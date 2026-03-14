/**
 * History view — JSONL chat history, commits, workflow run logs.
 *
 * Tabs:
 *   Chat  |  Commits  |  Runs  |  Evals
 *
 * Data loading strategy:
 *   - Loaded ONCE per project; cached in this._histData / this._commitData.
 *   - Re-used on repeated tab clicks (no re-fetch until project changes).
 *   - Pagination: _PAGE_SIZE entries per page; filter applies to FULL dataset.
 *
 * Commits tab:
 *   - If PostgreSQL available: loads from `commits` table with full metadata.
 *   - Fallback: reads commit_log.jsonl — all rows shown as untagged (red).
 *   - Inline edit: click Phase/Feature cell to edit; saves via PATCH /history/commits/{id}.
 *   - Sync button: imports commit_log.jsonl → DB.
 *   - Untagged rows (no phase): highlighted with red left border.
 *   - prompt_source_id: shown as a small "⊙ HH:MM" indicator per commit.
 *
 * Tags management has moved to the Planner tab (entities.js → Tags sub-tab).
 */

import { state } from '../stores/state.js';
import { api } from '../utils/api.js';

const _PAGE_SIZE = 100;

// Build a history API URL, injecting the current project as a query param.
function _histUrl(path) {
  const base = (state.settings?.backend_url || 'http://localhost:8000').replace(/\/$/, '');
  const project = state.currentProject?.name;
  const sep = path.includes('?') ? '&' : '?';
  const proj = project ? `${sep}project=${encodeURIComponent(project)}` : '';
  return `${base}${path}${proj}`;
}

export class HistoryView {
  constructor(container) {
    this.container    = container;
    this.activeTab    = "chat";

    // Cache — keyed by project; invalidated on project switch
    this._cachedProject = null;
    this._histData      = null;   // { entries: [...], total: N }
    this._commitData    = null;   // { commits: [...], source, total }
    this._tagCache      = null;
    this._tagCacheMap   = {};
    this._chatGhBase    = '';
    this._ghBase        = '';

    // Pagination + filter state
    this._histPage      = 1;
    this._commitPage    = 1;
    this._histFilter    = { source: '', phase: '', query: '' };
    this._commitFilter  = { query: '' };

    this._render();
    this._loadTab("chat");
  }

  _render() {
    const tabs = ["chat", "commits", "runs", "evals"];
    this.container.innerHTML = `
      <div class="history-layout" style="display:flex;flex-direction:column;height:100%">
        <div class="tab-bar" style="display:flex;gap:4px;padding:8px 12px;border-bottom:1px solid var(--border);align-items:center">
          ${tabs.map(t =>
            `<button class="tab-btn" data-tab="${t}"
              style="padding:6px 14px;border-radius:6px;border:1px solid var(--border);cursor:pointer;background:${this.activeTab === t ? 'var(--accent)' : 'var(--surface)'}"
              onclick="window._historyView._loadTab('${t}')">
              ${t.charAt(0).toUpperCase() + t.slice(1)}
            </button>`).join('')}
          <div style="flex:1"></div>
          <input id="history-search" placeholder="Search all…"
            style="padding:4px 8px;border:1px solid var(--border);border-radius:4px;background:var(--surface);color:var(--text)" />
        </div>
        <div id="history-content" style="flex:1;overflow-y:auto;padding:12px;min-height:0"></div>
      </div>
    `;
    window._historyView = this;
    document.getElementById("history-search")?.addEventListener("input", (e) => {
      this._filterContent(e.target.value);
    });
  }

  async _loadTab(tab) {
    this.activeTab = tab;
    // Update tab styles
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.style.background = btn.dataset.tab === tab ? "var(--accent)" : "var(--surface)";
    });

    const content = document.getElementById("history-content");
    if (!content) return;

    // Invalidate cache on project switch
    const project = state.currentProject?.name || '';
    if (project !== this._cachedProject) {
      this._cachedProject = project;
      this._histData      = null;
      this._commitData    = null;
      this._tagCache      = null;
      this._tagCacheMap   = {};
    }

    // Re-render from cache without re-fetching (fast tab switching)
    if (tab === "chat" && this._histData) {
      this._renderChatContainer(content);
      return;
    }
    if (tab === "commits" && this._commitData) {
      this._renderCommitsContainer(content);
      return;
    }

    content.innerHTML = "<div style='padding:20px;color:var(--muted)'>Loading…</div>";
    try {
      if (tab === "chat")         await this._renderChat(content);
      else if (tab === "commits") await this._renderCommits(content);
      else if (tab === "runs")    await this._renderRuns(content);
      else if (tab === "evals")   await this._renderEvals(content);
    } catch (e) {
      content.innerHTML = `<div style="color:red;padding:20px">Error: ${e.message}</div>`;
    }
  }

  // ── Chat tab ──────────────────────────────────────────────────────────────

  async _renderChat(container) {
    const project = state.currentProject?.name || '';

    // Load all data in parallel (limit=0 → backend returns all entries, noise filtered)
    const [histRes, commitsData, catsRes, cfgData] = await Promise.all([
      fetch(_histUrl('/history/chat')).then(r => r.json()),
      api.historyCommits(project, 2000).catch(() => ({ commits: [] })),
      api.entities.listCategories(project).catch(() => ({ categories: [] })),
      api.getProjectConfig(project).catch(() => ({})),
    ]);

    this._histData   = histRes;
    this._commitData = commitsData;
    this._histPage   = 1;

    await this._buildTagCache(project, catsRes.categories || []);

    // Build GitHub base URL
    let ghBase = (cfgData.github_repo || '').replace(/\.git$/, '').replace(/\/$/, '');
    if (ghBase.startsWith('git@')) ghBase = ghBase.replace(/^git@([^:]+):/, 'https://$1/');
    this._chatGhBase = ghBase;

    this._renderChatContainer(container);
  }

  _renderChatContainer(container) {
    const entries       = this._histData?.entries || [];
    const total         = entries.length;
    const untaggedCount = entries.filter(e => !e.phase && !e.feature).length;

    container.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;padding:8px 10px;
                  background:var(--surface);border-radius:6px;flex-wrap:wrap;font-size:12px">
        <span style="color:var(--muted);font-weight:600">Filter:</span>
        <select id="hist-filter-source" onchange="window._historyView._applyFilter()"
          style="background:var(--bg);border:1px solid var(--border);border-radius:3px;
                 padding:2px 6px;font-size:11px;color:var(--text)">
          <option value="">All sources</option>
          <option value="claude_cli">Claude CLI</option>
          <option value="ui">UI</option>
          <option value="workflow">Workflow</option>
        </select>
        <select id="hist-filter-phase" onchange="window._historyView._applyFilter()"
          style="background:var(--bg);border:1px solid var(--border);border-radius:3px;
                 padding:2px 6px;font-size:11px;color:var(--text)">
          <option value="">All phases</option>
          <option value="discovery">Discovery</option>
          <option value="development">Development</option>
          <option value="prod">Prod</option>
        </select>
        <span style="color:var(--muted);font-size:11px">${total} entries total</span>
        <div style="flex:1"></div>
        ${untaggedCount > 0
          ? `<span style="color:#e74c3c;font-size:11px;font-weight:600">${untaggedCount} untagged</span>`
          : `<span style="color:green;font-size:11px">All tagged ✓</span>`}
      </div>
      <div id="hist-chat-groups"></div>
      <div id="hist-page-bar"></div>`;

    // Restore previous filter values
    const srcEl = document.getElementById('hist-filter-source');
    const phEl  = document.getElementById('hist-filter-phase');
    if (srcEl && this._histFilter.source) srcEl.value = this._histFilter.source;
    if (phEl  && this._histFilter.phase)  phEl.value  = this._histFilter.phase;
    const searchEl = document.getElementById('history-search');
    if (searchEl && this._histFilter.query) searchEl.value = this._histFilter.query;

    this._applyFilter();
  }

  _applyFilter() {
    const srcFilter   = document.getElementById('hist-filter-source')?.value  || '';
    const phaseFilter = document.getElementById('hist-filter-phase')?.value   || '';
    const query       = document.getElementById('history-search')?.value      || '';

    this._histFilter = { source: srcFilter, phase: phaseFilter, query };
    this._histPage   = 1;  // reset to page 1 on filter change

    const wrapper = document.getElementById('hist-chat-groups');
    if (wrapper) this._renderChatGroups(wrapper);
  }

  _renderChatGroups(wrapper) {
    if (!wrapper) return;
    const { source: srcFilter, phase: phaseFilter, query } = this._histFilter;

    let entries = this._histData?.entries || [];
    if (srcFilter)   entries = entries.filter(e => (e.source || 'ui') === srcFilter);
    if (phaseFilter) entries = entries.filter(e => e.phase === phaseFilter);
    if (query) {
      const q = query.toLowerCase();
      entries = entries.filter(e =>
        (e.user_input || '').toLowerCase().includes(q) ||
        (e.output     || '').toLowerCase().includes(q));
    }

    const totalFiltered = entries.length;
    if (!totalFiltered) {
      wrapper.innerHTML = "<div style='padding:20px;color:var(--muted)'>No entries match the current filter.</div>";
      this._renderPageBar(totalFiltered);
      return;
    }

    // Paginate
    const start       = (this._histPage - 1) * _PAGE_SIZE;
    const pageEntries = entries.slice(start, start + _PAGE_SIZE);

    // Build session_id → commits map (from cached commit data)
    const commitsBySession = {};
    for (const c of (this._commitData?.commits || [])) {
      if (c.session_id) {
        if (!commitsBySession[c.session_id]) commitsBySession[c.session_id] = [];
        commitsBySession[c.session_id].push(c);
      }
    }

    // Group consecutive entries by session_id
    const groups = [];
    for (const e of pageEntries) {
      const last = groups[groups.length - 1];
      if (last && last.session_id === e.session_id) last.entries.push(e);
      else groups.push({ session_id: e.session_id, entries: [e] });
    }

    const ghBase = this._chatGhBase || '';
    wrapper.innerHTML = groups.map(group => {
      const sid = group.session_id || '';
      const commits = sid ? (commitsBySession[sid] || []) : [];

      const commitStrip = commits.length ? `
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;
                    padding:5px 8px;background:var(--surface2);border-radius:4px;margin-bottom:6px;font-size:11px">
          <span style="color:var(--muted);font-weight:600;white-space:nowrap">⑂ ${commits.length} commit${commits.length > 1 ? 's' : ''}:</span>
          ${commits.map(c => {
            const hash  = (c.commit_hash || '').slice(0, 8);
            const msg   = (c.commit_msg  || '').slice(0, 60);
            const date  = (c.committed_at || '').slice(0, 10);
            const pRef  = c.prompt_source_id
              ? ` <span title="Triggered by prompt at ${c.prompt_source_id}" style="color:var(--muted);font-size:9px">⊙${c.prompt_source_id.slice(11,16)}</span>`
              : '';
            return ghBase && c.commit_hash
              ? `<span style="white-space:nowrap"><a href="${ghBase}/commit/${this._escapeHtml(c.commit_hash)}" target="_blank"
                    style="font-family:monospace;color:var(--accent);text-decoration:none"
                    title="${this._escapeHtml(msg)} · ${date}">${hash} ↗</a>${pRef}</span>`
              : `<span style="white-space:nowrap"><span style="font-family:monospace;color:var(--accent)"
                       title="${this._escapeHtml(msg)} · ${date}">${hash}</span>${pRef}</span>`;
          }).join('')}
        </div>` : '';

      const entriesHtml = group.entries.map((e, idx) => {
        const isUntagged = !e.phase && !e.feature;
        const borderColor = isUntagged ? '#e74c3c' : 'var(--border)';
        const entryId     = `hist-entry-${(sid || 'ns').slice(0, 8)}-${start + idx}`;
        const tagAnchorId = `hist-tag-${entryId}`;
        const sourceId    = e.ts || '';

        const outputHtml = e.output
          ? `<div style="margin-top:6px">
              <div style="font-size:11px;color:var(--muted);font-weight:600;margin-bottom:2px">Response:</div>
              <div id="${entryId}-resp"
                style="color:var(--muted);font-size:12px;border-left:2px solid var(--border);
                       padding-left:8px;white-space:pre-wrap;word-break:break-word;
                       max-height:120px;overflow:hidden;transition:max-height 0.2s">
                ${this._escapeHtml(e.output)}
              </div>
              ${e.output.length > 200
                ? `<span style="font-size:11px;color:var(--accent);cursor:pointer;user-select:none"
                    onclick="const el=document.getElementById('${entryId}-resp');
                             el.style.maxHeight=el.style.maxHeight==='none'?'120px':'none';
                             this.textContent=el.style.maxHeight==='none'?'▲ collapse':'▼ expand'">▼ expand</span>`
                : ''}
            </div>`
          : '';

        return `
        <div class="history-entry" style="border:1px solid ${borderColor};border-left:3px solid ${borderColor};
                    border-radius:6px;padding:10px 12px;margin-bottom:6px">
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;font-size:11px">
            <span>${e.ts?.slice(0, 16) || ""}</span>
            <span style="color:var(--accent)">${e.provider || ""}</span>
            <span style="background:var(--surface2);padding:1px 5px;border-radius:3px;font-size:10px">${e.source || "ui"}</span>
            ${e.phase ? `<span style="background:rgba(74,144,226,.15);color:#4a90e2;padding:1px 5px;border-radius:3px">${e.phase}</span>` : ''}
            ${e.feature ? `<span style="background:rgba(39,174,96,.15);color:#27ae60;padding:1px 5px;border-radius:3px">#${e.feature}</span>` : ''}
            ${e.bug_ref ? `<span style="background:rgba(231,76,60,.12);color:#e74c3c;padding:1px 5px;border-radius:3px">🐛${e.bug_ref}</span>` : ''}
            ${isUntagged ? `<span style="color:#e74c3c;font-size:10px">⚠ untagged</span>` : ''}
            <span id="${tagAnchorId}" style="margin-left:auto;position:relative;display:flex;align-items:center;gap:4px">
              <button onclick="window._historyView._openEntryTagPicker('${this._escapeHtml(sourceId)}','${tagAnchorId}')"
                style="font-size:10px;padding:1px 6px;border:1px solid var(--border);border-radius:3px;
                       cursor:pointer;background:var(--surface);color:var(--muted);white-space:nowrap">
                ⬡ Tag
              </button>
            </span>
          </div>
          <div style="font-size:11px;color:var(--muted);font-weight:600;margin-bottom:2px">Prompt:</div>
          <div style="font-weight:500;margin-bottom:4px;white-space:pre-wrap;word-break:break-word">${this._escapeHtml(e.user_input || "")}</div>
          ${outputHtml}
        </div>`;
      }).join('');

      return `
        <div style="border:1px solid var(--border);border-radius:8px;padding:10px;margin-bottom:10px">
          ${sid ? `<div style="font-size:10px;color:var(--muted);margin-bottom:6px;font-family:monospace">session: ${sid.slice(0,16)}…</div>` : ''}
          ${commitStrip}
          ${entriesHtml}
        </div>`;
    }).join('');

    this._renderPageBar(totalFiltered);
  }

  // ── Pagination ─────────────────────────────────────────────────────────────

  _renderPageBar(total) {
    const bar  = document.getElementById('hist-page-bar');
    if (!bar) return;
    const page       = this._histPage;
    const totalPages = Math.ceil(total / _PAGE_SIZE);
    if (totalPages <= 1) { bar.innerHTML = ''; return; }
    bar.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;padding:10px;justify-content:center;font-size:12px">
        <button onclick="window._historyView._changePage(-1)"
          style="padding:3px 10px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface)"
          ${page <= 1 ? 'disabled style="opacity:.4"' : ''}>◀ Prev</button>
        <span style="color:var(--muted)">Page ${page} of ${totalPages} · ${total} entries</span>
        <button onclick="window._historyView._changePage(1)"
          style="padding:3px 10px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface)"
          ${page >= totalPages ? 'disabled style="opacity:.4"' : ''}>Next ▶</button>
      </div>`;
  }

  _changePage(delta) {
    this._histPage = Math.max(1, this._histPage + delta);
    const wrapper = document.getElementById('hist-chat-groups');
    if (wrapper) this._renderChatGroups(wrapper);
    document.getElementById('history-content')?.scrollTo(0, 0);
  }

  // ── Tag picker (shared by chat + commits) ─────────────────────────────────

  async _buildTagCache(project, categories) {
    this._tagCache    = [];
    this._tagCacheMap = {};
    const allCats = categories.length ? categories : ((await api.entities.listCategories(project).catch(() => ({ categories: [] }))).categories || []);
    for (const cat of allCats) {
      const vals = ((await api.entities.listValues(project, cat.id, { status: 'active' }).catch(() => ({ values: [] }))).values || []);
      if (vals.length) this._tagCache.push({ cat, values: vals });
      for (const v of vals) {
        this._tagCacheMap[v.id] = { color: cat.color || '#4a90e2', name: v.name, catName: cat.name, icon: cat.icon || '⬡' };
      }
    }
  }

  // Shared picker — opens instantly using cached tag data (no API calls)
  _openEntryTagPicker(sourceId, anchorId) {
    document.querySelectorAll('.entry-tag-picker').forEach(el => el.remove());
    const anchor = document.getElementById(anchorId);
    if (!anchor) return;

    const groups = this._tagCache || [];
    const picker = document.createElement('div');
    picker.className = 'entry-tag-picker';
    picker.style.cssText = [
      'position:absolute;right:0;top:100%;z-index:200;background:var(--bg)',
      'border:1px solid var(--border);border-radius:6px;padding:6px',
      'min-width:180px;max-height:260px;overflow-y:auto;box-shadow:0 4px 12px rgba(0,0,0,.2)',
    ].join(';');

    if (!groups.length) {
      picker.innerHTML = `<div style="font-size:11px;color:var(--muted);padding:4px 8px">No tags available.<br>Create tags in Planner.</div>`;
    } else {
      const filterId = `etag-filter-${Date.now()}`;
      picker.innerHTML = `
        <input id="${filterId}" placeholder="Filter tags…" oninput="window._historyView._filterTagPicker('${filterId}')"
          style="width:100%;box-sizing:border-box;margin-bottom:4px;padding:3px 6px;border:1px solid var(--border);
                 border-radius:3px;background:var(--surface);color:var(--text);font-size:11px"/>
        <div id="etag-groups">
          ${groups.map(({ cat, values }) => `
            <div class="etag-group">
              <div style="font-size:10px;color:var(--muted);font-weight:600;padding:2px 4px;
                          text-transform:uppercase;letter-spacing:.5px">
                ${this._escapeHtml(cat.icon || '')} ${this._escapeHtml(cat.name)}
              </div>
              ${values.map(v => `
                <div class="etag-item" data-catname="${this._escapeHtml(cat.name)}"
                  onclick="window._historyView._tagEntryWith('${this._escapeHtml(sourceId)}',${v.id},'${anchorId}')"
                  style="padding:3px 10px;cursor:pointer;border-radius:3px;font-size:12px;color:${this._escapeHtml(cat.color || 'var(--text)')}"
                  onmouseenter="this.style.background='var(--surface)'" onmouseleave="this.style.background=''">
                  ${this._escapeHtml(v.name)}
                </div>`).join('')}
            </div>`).join('')}
        </div>`;
    }

    anchor.appendChild(picker);
    picker.querySelector('input')?.focus();

    // Close on outside click
    setTimeout(() => {
      document.addEventListener('click', function _close(ev) {
        if (!picker.contains(ev.target) && ev.target !== anchor) {
          picker.remove();
          document.removeEventListener('click', _close);
        }
      });
    }, 10);
  }

  _filterTagPicker(filterId) {
    const q = document.getElementById(filterId)?.value?.toLowerCase() || '';
    document.querySelectorAll('.etag-item').forEach(item => {
      const match = !q || item.textContent.toLowerCase().includes(q) || item.dataset.catname?.toLowerCase().includes(q);
      item.style.display = match ? '' : 'none';
    });
    document.querySelectorAll('.etag-group').forEach(g => {
      const anyVisible = [...g.querySelectorAll('.etag-item')].some(i => i.style.display !== 'none');
      g.style.display = anyVisible ? '' : 'none';
    });
  }

  async _tagEntryWith(sourceId, valueId, anchorId) {
    const project = state.currentProject?.name || '';
    document.querySelectorAll('.entry-tag-picker').forEach(el => el.remove());
    const anchor = document.getElementById(anchorId);
    const info   = this._tagCacheMap?.[valueId] || {};
    const color  = info.color || '#4a90e2';

    // Optimistic chip
    if (anchor) {
      const chip = document.createElement('span');
      chip.style.cssText = `font-size:10px;background:${color}22;color:${color};border:1px solid ${color}55;padding:1px 5px;border-radius:3px;white-space:nowrap`;
      chip.textContent = `${info.icon || '⬡'} ${info.name || 'tagged'}`;
      anchor.appendChild(chip);
    }

    try {
      await api.entities.tagBySourceId({ source_id: sourceId, entity_value_id: valueId, project });
    } catch (e) {
      console.warn('Tag entry failed:', e.message);
      // Show error indicator
      if (anchor) {
        const err = document.createElement('span');
        err.style.cssText = 'font-size:10px;color:#e74c3c;margin-left:4px';
        err.textContent = '✕ ' + e.message;
        anchor.appendChild(err);
      }
    }
  }

  // ── Commits tab ───────────────────────────────────────────────────────────

  async _renderCommits(container) {
    const project = state.currentProject?.name || '';
    const [data, cfgData, catsRes] = await Promise.all([
      api.historyCommits(project, 2000),
      api.getProjectConfig(project).catch(() => ({})),
      this._tagCache ? Promise.resolve(null) : api.entities.listCategories(project).catch(() => ({ categories: [] })),
    ]);
    if (catsRes) await this._buildTagCache(project, catsRes.categories || []);

    this._commitData = data;
    this._commitPage = 1;

    let ghBase = (cfgData.github_repo || '').replace(/\/$/, '').replace(/\.git$/, '');
    if (ghBase.startsWith('git@')) ghBase = ghBase.replace(/^git@([^:]+):/, 'https://$1/');
    this._ghBase = ghBase;

    this._renderCommitsContainer(container);
  }

  _renderCommitsContainer(container) {
    const commits    = this._commitData?.commits || [];
    const fromDb     = this._commitData?.source === 'db';
    const untaggedCount = commits.filter(c => !c.phase).length;

    const headerBar = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;flex-wrap:wrap">
        <span style="font-size:13px;color:var(--muted)">${commits.length} commit${commits.length !== 1 ? 's' : ''} total</span>
        ${untaggedCount > 0 ? `<span style="font-size:12px;color:#e74c3c;font-weight:600">${untaggedCount} untagged</span>` : ''}
        ${fromDb
          ? `<span style="font-size:11px;color:green;background:rgba(39,174,96,.12);padding:2px 6px;border-radius:4px">live DB</span>`
          : `<span style="font-size:11px;color:orange;background:rgba(230,126,34,.12);padding:2px 6px;border-radius:4px">file fallback — no DB</span>`}
        <div style="flex:1"></div>
        <button id="commits-sync-btn" onclick="window._historyView._syncCommits()"
          style="padding:4px 12px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface);font-size:12px">
          ↻ Sync Commits
        </button>
      </div>`;

    if (!commits.length) {
      container.innerHTML = headerBar + `
        <div style="padding:2rem;text-align:center;color:var(--muted);font-size:13px">
          <div style="font-size:2rem;margin-bottom:0.5rem">⑂</div>
          No commits loaded yet.<br>
          <span style="font-size:12px">Click <strong>↻ Sync Commits</strong> above to import from <code>commit_log.jsonl</code>.</span>
        </div>`;
      return;
    }

    // Paginate
    const start        = (this._commitPage - 1) * _PAGE_SIZE;
    const pageCommits  = commits.slice(start, start + _PAGE_SIZE);
    const totalPages   = Math.ceil(commits.length / _PAGE_SIZE);

    const pageBar = totalPages > 1 ? `
      <div style="display:flex;align-items:center;gap:8px;padding:8px;justify-content:center;font-size:12px">
        <button onclick="window._historyView._changeCommitPage(-1)"
          style="padding:3px 10px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface)"
          ${this._commitPage <= 1 ? 'disabled' : ''}>◀ Prev</button>
        <span style="color:var(--muted)">Page ${this._commitPage} of ${totalPages}</span>
        <button onclick="window._historyView._changeCommitPage(1)"
          style="padding:3px 10px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface)"
          ${this._commitPage >= totalPages ? 'disabled' : ''}>Next ▶</button>
      </div>` : '';

    container.innerHTML = headerBar + `
      <div style="overflow-x:auto">
        <table id="commits-table" style="width:100%;border-collapse:collapse;font-size:12px">
          <thead>
            <tr style="background:var(--surface);font-size:11px;text-transform:uppercase;color:var(--muted)">
              <th style="padding:6px 8px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap">Hash</th>
              <th style="padding:6px 8px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap">Date</th>
              <th style="padding:6px 8px;text-align:left;border-bottom:1px solid var(--border)">Phase</th>
              <th style="padding:6px 8px;text-align:left;border-bottom:1px solid var(--border)">Feature</th>
              <th style="padding:6px 8px;text-align:left;border-bottom:1px solid var(--border)">Bug</th>
              <th style="padding:6px 8px;text-align:left;border-bottom:1px solid var(--border)">Message</th>
              <th style="padding:6px 8px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap">Source</th>
              <th style="padding:6px 8px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap">Prompt</th>
              <th style="padding:6px 8px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap">Tags</th>
            </tr>
          </thead>
          <tbody>
            ${pageCommits.map((c, i) => this._commitRow(c, start + i)).join('')}
          </tbody>
        </table>
      </div>
      ${pageBar}
    `;
  }

  _changeCommitPage(delta) {
    const commits    = this._commitData?.commits || [];
    const totalPages = Math.ceil(commits.length / _PAGE_SIZE);
    this._commitPage = Math.max(1, Math.min(totalPages, this._commitPage + delta));
    const container  = document.getElementById('history-content');
    if (container) this._renderCommitsContainer(container);
    container?.scrollTo(0, 0);
  }

  _commitRow(c, i) {
    const untagged  = !c.phase;
    const rowBorder = untagged ? 'border-left:3px solid #e74c3c' : 'border-left:3px solid transparent';
    const dateStr   = c.committed_at ? c.committed_at.slice(0, 10) : '';
    const canEdit   = !!c.id;
    const editAttr  = canEdit ? 'contenteditable="true"' : '';
    const editStyle = canEdit ? 'cursor:text;min-width:60px' : 'color:var(--muted)';
    const PHASES    = ['', 'discovery', 'development', 'prod'];

    const ghBase   = this._ghBase || '';
    const hashFull = c.commit_hash || '';
    const hashShort = hashFull.slice(0, 8);
    const hashEl   = ghBase && hashFull
      ? `<a href="${ghBase}/commit/${hashFull}" target="_blank"
            style="font-family:monospace;color:var(--accent);text-decoration:none"
            title="Open commit in GitHub">${hashShort} ↗</a>`
      : `<span style="font-family:monospace;color:var(--accent)">${hashShort}</span>`;

    // Show linked prompt timestamp (HH:MM from ISO timestamp)
    const promptCell = c.prompt_source_id
      ? `<span title="Triggered by prompt at ${this._escapeHtml(c.prompt_source_id)}"
               style="font-family:monospace;font-size:11px;color:var(--accent)">
           ⊙ ${c.prompt_source_id.slice(11, 16)}
         </span>`
      : `<span style="color:var(--muted);font-size:11px">—</span>`;

    return `
      <tr data-commit-id="${c.id || ''}" data-idx="${i}"
          style="border-bottom:1px solid var(--border);${rowBorder};transition:background .15s"
          onmouseenter="this.style.background='var(--surface)'"
          onmouseleave="this.style.background=''">
        <td style="padding:5px 8px">${hashEl}</td>
        <td style="padding:5px 8px;color:var(--muted);white-space:nowrap">${dateStr}</td>
        <td style="padding:5px 4px">
          ${canEdit
            ? `<select onchange="window._historyView._saveField(${c.id},'phase',this.value)"
                style="background:var(--surface);border:1px solid var(--border);border-radius:3px;padding:2px 4px;font-size:11px;color:${untagged ? '#e74c3c' : 'var(--text)'}">
                ${PHASES.map(ph => `<option value="${ph}" ${c.phase === ph ? 'selected' : ''}>${ph || '—'}</option>`).join('')}
               </select>`
            : `<span style="color:${untagged ? '#e74c3c' : 'var(--muted)'}">—</span>`}
        </td>
        <td style="padding:5px 4px">
          <span class="commit-editable" data-id="${c.id || ''}" data-field="feature"
            ${editAttr} style="${editStyle};display:inline-block;padding:1px 4px;border-radius:3px"
            onblur="window._historyView._onEditBlur(this)"
            onkeydown="if(event.key==='Enter'){event.preventDefault();this.blur()}">
            ${this._escapeHtml(c.feature || '')}
          </span>
        </td>
        <td style="padding:5px 4px">
          <span class="commit-editable" data-id="${c.id || ''}" data-field="bug_ref"
            ${editAttr} style="${editStyle};display:inline-block;padding:1px 4px;border-radius:3px"
            onblur="window._historyView._onEditBlur(this)"
            onkeydown="if(event.key==='Enter'){event.preventDefault();this.blur()}">
            ${this._escapeHtml(c.bug_ref || '')}
          </span>
        </td>
        <td style="padding:5px 8px;max-width:340px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
            title="${this._escapeHtml(c.commit_msg || '')}">
          ${this._escapeHtml(c.commit_msg || '')}
        </td>
        <td style="padding:5px 8px;color:var(--muted);font-size:11px">${c.source || ''}</td>
        <td style="padding:5px 8px">${promptCell}</td>
        <td style="padding:5px 4px">
          <span id="ctag-${hashFull.slice(0,8) || i}" style="position:relative;display:flex;align-items:center;gap:4px">
            <button onclick="window._historyView._openEntryTagPicker('${this._escapeHtml(hashFull)}','ctag-${hashFull.slice(0,8) || i}')"
              style="font-size:10px;padding:1px 6px;border:1px solid var(--border);border-radius:3px;
                     cursor:pointer;background:var(--surface);color:var(--muted);white-space:nowrap">
              ⬡ Tag
            </button>
          </span>
        </td>
      </tr>
    `;
  }

  async _saveField(commitId, field, value) {
    if (!commitId) return;
    try {
      await api.patchCommit(commitId, { [field]: value || null });
      const row = document.querySelector(`tr[data-commit-id="${commitId}"]`);
      if (row) {
        const phaseSelect = row.querySelector('select');
        const hasPhase = phaseSelect ? phaseSelect.value !== '' : false;
        row.style.borderLeft = hasPhase ? '3px solid transparent' : '3px solid #e74c3c';
        if (phaseSelect) phaseSelect.style.color = hasPhase ? 'var(--text)' : '#e74c3c';
        this._refreshUntaggedCount();
      }
    } catch (e) {
      console.warn('Commit patch failed:', e.message);
    }
  }

  async _onEditBlur(el) {
    const commitId = el.dataset.id;
    const field = el.dataset.field;
    if (!commitId || !field) return;
    const value = el.textContent.trim();
    try {
      await api.patchCommit(parseInt(commitId), { [field]: value || null });
    } catch (e) {
      console.warn('Commit patch failed:', e.message);
    }
  }

  _refreshUntaggedCount() {
    const rows = document.querySelectorAll('#commits-table tbody tr');
    let untagged = 0;
    rows.forEach(r => {
      if (r.style.borderLeft.includes('#e74c3c')) untagged++;
    });
    const badge = document.querySelector('#history-content span[style*="e74c3c"]');
    if (badge) badge.textContent = untagged > 0 ? `${untagged} untagged` : '';
  }

  async _syncCommits() {
    const btn = document.getElementById('commits-sync-btn');
    if (btn) { btn.textContent = 'Syncing…'; btn.disabled = true; }
    const project = state.currentProject?.name || '';
    try {
      const res = await api.syncCommits(project);
      // Invalidate commit cache so next render re-fetches
      this._commitData = null;
      alert(`Synced ${res.imported} new commits.`);
      await this._loadTab('commits');
    } catch (e) {
      alert('Sync failed: ' + e.message);
    } finally {
      if (btn) { btn.textContent = '↻ Sync Commits'; btn.disabled = false; }
    }
  }

  // ── Runs tab ───────────────────────────────────────────────────────────────

  async _renderRuns(container) {
    const res = await fetch(_histUrl('/history/runs?limit=20'));
    const data = await res.json();
    const runs = data.runs || [];

    if (!runs.length) {
      container.innerHTML = "<div style='padding:20px;color:var(--muted)'>No workflow runs yet.</div>";
      return;
    }

    container.innerHTML = runs
      .map(
        (r) => `
        <div class="run-entry" style="border:1px solid var(--border);border-radius:6px;padding:12px;margin-bottom:10px;cursor:pointer"
          onclick="window._historyView._showRunDetail('${r.file}')">
          <div style="display:flex;gap:12px;align-items:center">
            <strong>${r.workflow || r.file}</strong>
            <span style="color:var(--muted);font-size:12px">${r.started_at?.slice(0, 16) || ""}</span>
            <span>${r.steps || 0} steps</span>
            <span style="color:green">$${(r.total_cost_usd || 0).toFixed(5)}</span>
            <span style="color:var(--muted)">${r.duration_secs || 0}s</span>
          </div>
        </div>
      `
      )
      .join("");
  }

  async _showRunDetail(filename) {
    const res = await fetch(_histUrl(`/history/runs/${filename}`));
    const run = await res.json();

    const modal = document.createElement("div");
    modal.style.cssText =
      "position:fixed;inset:0;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;z-index:1000";
    modal.innerHTML = `
      <div style="background:var(--bg);border-radius:8px;padding:24px;max-width:700px;width:90%;max-height:80vh;overflow-y:auto">
        <div style="display:flex;justify-content:space-between;margin-bottom:16px">
          <strong>Run: ${run.workflow}</strong>
          <button onclick="this.closest('div[style*=fixed]').remove()">✕</button>
        </div>
        <pre style="font-size:12px;background:var(--surface);padding:12px;border-radius:4px;overflow-x:auto">${JSON.stringify(run, null, 2)}</pre>
      </div>
    `;
    document.body.appendChild(modal);
  }

  // ── Evals tab ──────────────────────────────────────────────────────────────

  async _renderEvals(container) {
    const res = await fetch(_histUrl('/history/evals'));
    const data = await res.json();
    const evals = data.evals || [];

    if (!evals.length) {
      container.innerHTML =
        "<div style='padding:20px;color:var(--muted)'>No prompt evaluations yet. Use /compare in the CLI.</div>";
      return;
    }

    container.innerHTML = evals
      .map(
        (e) => `
        <div style="border:1px solid var(--border);border-radius:6px;padding:12px;margin-bottom:10px">
          <div style="display:flex;gap:8px;margin-bottom:8px">
            <span style="color:var(--muted);font-size:12px">${e.ts?.slice(0, 16) || ""}</span>
            <span style="color:var(--accent)">${e.prompt_file || ""}</span>
            <span style="color:green">Winner: ${e.winner || "(none)"}</span>
          </div>
          <div style="font-size:12px;color:var(--muted)">Providers: ${(e.providers || []).join(", ")}</div>
          ${e.notes ? `<div style="margin-top:4px;font-size:12px">${this._escapeHtml(e.notes)}</div>` : ""}
        </div>
      `
      )
      .join("");
  }

  // ── Global search (redirects to full-dataset filter) ─────────────────────

  _filterContent(query) {
    if (this.activeTab === 'chat') {
      this._histFilter.query = query;
      this._histPage = 1;
      const wrapper = document.getElementById('hist-chat-groups');
      if (wrapper) this._renderChatGroups(wrapper);
    }
    // For other tabs (runs/evals) fall back to DOM filter
    else {
      const entries = document.querySelectorAll(".history-entry, .run-entry");
      entries.forEach((el) => {
        el.style.display = el.textContent.toLowerCase().includes(query.toLowerCase()) ? "" : "none";
      });
    }
  }

  _escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
}
