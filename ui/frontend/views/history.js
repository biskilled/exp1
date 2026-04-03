/**
 * history.js — Project history: chat log, commits, workflow runs, and evals.
 *
 * Renders a four-tab view (Chat, Commits, Runs, Evals) backed by paginated JSONL history
 * and the PostgreSQL commits/runs tables; data is loaded once per project and cached
 * in-memory with per-entry entity tagging support via the shared tagCache.
 * Rendered via: new HistoryView(container).render() called from main.js navigateTo().
 */

import { state } from '../stores/state.js';
import { api } from '../utils/api.js';

const _PAGE_SIZE = 100;

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

    // Cache — invalidated on project switch or ↻ Refresh
    this._cachedProject = null;
    this._histData      = null;   // { entries, total, filtered }
    this._commitData    = null;   // { commits, source }
    this._tagCache      = null;   // [{cat, values}] from planner_tags grouped by category
    this._tagCacheMap   = {};     // "cat:name" → {color, label}
    this._entryTags     = {};     // sourceId → string[] (e.g. ["phase:discovery","feature:auth"])
    this._chatGhBase    = '';
    this._ghBase        = '';

    // Pagination + filter state
    this._histPage      = 1;
    this._commitPage    = 1;
    this._histFilter    = { source: '', phase: '', query: '' };
    this._commitFilter  = { phase: '' };

    this._render();
    this._loadTab("chat");
  }

  _render() {
    const tabs = ["chat", "commits", "runs", "evals"];
    this.container.innerHTML = `
      <div class="history-layout" style="display:flex;flex-direction:column;height:100%">
        <div class="tab-bar" style="display:flex;gap:4px;padding:6px 10px;border-bottom:1px solid var(--border);align-items:center;flex-wrap:wrap">
          ${tabs.map(t =>
            `<button class="tab-btn" data-tab="${t}"
              style="padding:5px 12px;border-radius:6px;border:1px solid var(--border);cursor:pointer;background:${this.activeTab === t ? 'var(--accent)' : 'var(--surface)'};font-size:12px"
              onclick="window._historyView._loadTab('${t}')">
              ${t.charAt(0).toUpperCase() + t.slice(1)}
            </button>`).join('')}
          <div style="flex:1"></div>
          <!-- Pagination controls — updated by _renderPageBars() -->
          <div id="hist-nav-bar" style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted)"></div>
          <input id="history-search" placeholder="Search…"
            style="padding:3px 7px;border:1px solid var(--border);border-radius:4px;background:var(--surface);color:var(--text);width:130px;font-size:12px;margin-left:6px" />
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
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.style.background = btn.dataset.tab === tab ? "var(--accent)" : "var(--surface)";
    });

    const content = document.getElementById("history-content");
    if (!content) return;

    // Invalidate cache on project switch
    const project = state.currentProject?.name || '';
    if (project !== this._cachedProject) {
      this._cachedProject = project;
      this._histData    = null;
      this._commitData  = null;
      this._tagCache    = null;
      this._tagCacheMap = {};
      this._entryTags   = {};
    }

    // Re-render from cache (fast tab switching — no fetch)
    if (tab === "chat" && this._histData) {
      this._renderChatContainer(content);
      return;
    }
    if (tab === "commits" && this._commitData) {
      this._renderCommitsContainer(content);
      return;
    }

    // Clear nav bar when switching away from chat
    if (tab !== 'chat') {
      const nav = document.getElementById('hist-nav-bar');
      if (nav) nav.innerHTML = '';
    }

    content.innerHTML = `<div style='padding:20px;color:var(--muted);display:flex;align-items:center;gap:8px'>
      <span id="hist-loading-spinner" style="display:inline-block;animation:spin 1s linear infinite">⟳</span>
      <span id="hist-loading-msg">Loading…</span>
    </div>`;
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

  _setLoadingMsg(msg) {
    const el = document.getElementById('hist-loading-msg');
    if (el) el.textContent = msg;
  }

  async _renderChat(container) {
    const project = state.currentProject?.name || '';

    // Step 1: fetch history (newest 500) + config in parallel
    this._setLoadingMsg('Fetching history entries…');
    const _ts = Date.now();
    const [histRes, cfgData] = await Promise.all([
      fetch(_histUrl(`/history/chat?limit=500&_t=${_ts}`)).then(r => r.json()),
      api.getProjectConfig(project).catch(() => ({})),
    ]);

    const total = histRes.total || 0;
    this._histData = histRes;
    this._histPage = 1;

    let ghBase = (cfgData.github_repo || '').replace(/\.git$/, '').replace(/\/$/, '');
    if (ghBase.startsWith('git@')) ghBase = ghBase.replace(/^git@([^:]+):/, 'https://$1/');
    this._chatGhBase = ghBase;

    // Step 2: build tag cache from planner_tags
    this._setLoadingMsg(`Building tag index (${total} entries)…`);
    await this._buildTagCache(project);

    // Step 3: render immediately so user sees data
    this._renderChatContainer(container);

    // Step 4: load source tags in background (non-blocking — chips appear after render)
    api.entities.getSourceTags(project).then(sourceTags => {
      for (const [sid, tagArr] of Object.entries(sourceTags || {})) {
        if (!this._entryTags[sid]) this._entryTags[sid] = tagArr;
      }
    }).catch(() => {});

    // Step 5: pre-load commits in background for the Commits tab (lazy)
    if (!this._commitData) {
      api.historyCommits(project, 500).then(d => {
        this._commitData = d;
      }).catch(() => { this._commitData = { commits: [] }; });
    }
  }

  _renderChatContainer(container) {
    const entries    = this._histData?.entries  || [];
    const serverTotal = this._histData?.total   || entries.length;
    const filtered   = this._histData?.filtered || 0;
    const hasMore    = this._histData?.has_more  || false;
    const untagged   = entries.filter(e => !e.tags?.some(t => t.startsWith('phase:'))).length;

    container.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;padding:5px 8px;
                  background:var(--surface);border-radius:6px;flex-wrap:wrap;font-size:11px">
        <select id="hist-filter-source" onchange="window._historyView._applyFilter()"
          style="background:var(--bg);border:1px solid var(--border);border-radius:3px;padding:2px 5px;font-size:11px;color:var(--text)">
          <option value="">All sources</option>
          <option value="claude_cli">Claude CLI</option>
          <option value="ui">UI</option>
          <option value="workflow">Workflow</option>
        </select>
        <select id="hist-filter-phase" onchange="window._historyView._applyFilter()"
          style="background:var(--bg);border:1px solid var(--border);border-radius:3px;padding:2px 5px;font-size:11px;color:var(--text)">
          <option value="">All phases</option>
          <option value="discovery">Discovery</option>
          <option value="development">Development</option>
          <option value="testing">Testing</option>
          <option value="review">Review</option>
          <option value="production">Production</option>
          <option value="maintenance">Maintenance</option>
          <option value="bugfix">Bug Fix</option>
        </select>
        ${filtered > 0 ? `<span style="color:var(--muted)">${filtered} noise hidden</span>` : ''}
        ${hasMore ? `<span style="color:var(--muted)">showing ${entries.length} of ${serverTotal}</span>
          <button onclick="window._historyView._loadMore()"
            style="padding:2px 7px;border:1px solid var(--accent);border-radius:3px;cursor:pointer;
                   background:var(--surface);font-size:11px;color:var(--accent)">Load all</button>` : ''}
        <div style="flex:1"></div>
        ${untagged > 0 ? `<span style="color:#e74c3c;font-weight:600">${untagged} untagged</span>` : `<span style="color:green">All tagged ✓</span>`}
        <button onclick="window._historyView._refreshHistory()"
          style="padding:2px 7px;border:1px solid var(--border);border-radius:3px;cursor:pointer;background:var(--surface);font-size:11px;color:var(--muted)"
          title="Reload from server">↻</button>
      </div>
      <div id="hist-chat-groups"></div>`;

    // Restore filter state (default = All phases, no auto-populate)
    const srcEl = document.getElementById('hist-filter-source');
    const phEl  = document.getElementById('hist-filter-phase');
    if (srcEl && this._histFilter.source) srcEl.value = this._histFilter.source;
    if (phEl  && this._histFilter.phase)  phEl.value  = this._histFilter.phase;
    const searchEl = document.getElementById('history-search');
    if (searchEl && this._histFilter.query) searchEl.value = this._histFilter.query;

    this._applyFilter();
  }

  async _refreshHistory() {
    this._histData   = null;
    this._commitData = null;
    this._entryTags  = {};
    const content = document.getElementById("history-content");
    if (content) {
      content.innerHTML = `<div style='padding:20px;color:var(--muted);display:flex;align-items:center;gap:8px'>
        <span style="display:inline-block;animation:spin 1s linear infinite">⟳</span>
        <span id="hist-loading-msg">Reloading…</span>
      </div>`;
      await this._renderChat(content);
    }
  }

  async _loadMore() {
    const project = state.currentProject?.name || '';
    const current = this._histData?.entries || [];
    const _ts = Date.now();
    const content = document.getElementById('history-content');
    // Load all entries (no limit)
    if (content) {
      const btn = content.querySelector('button[onclick*="_loadMore"]');
      if (btn) { btn.disabled = true; btn.textContent = '…'; }
    }
    try {
      const res = await fetch(_histUrl(`/history/chat?limit=0&_t=${_ts}`)).then(r => r.json());
      this._histData = res;
      this._histPage = 1;
      this._renderChatContainer(content);
    } catch (e) {
      if (content) {
        const btn = content.querySelector('button[onclick*="_loadMore"]');
        if (btn) { btn.disabled = false; btn.textContent = 'Load all'; }
      }
    }
  }

  _applyFilter() {
    const srcFilter   = document.getElementById('hist-filter-source')?.value || '';
    const phaseFilter = document.getElementById('hist-filter-phase')?.value  || '';
    const query       = document.getElementById('history-search')?.value     || '';
    this._histFilter = { source: srcFilter, phase: phaseFilter, query };
    this._histPage   = 1;
    const wrapper = document.getElementById('hist-chat-groups');
    if (wrapper) this._renderChatGroups(wrapper);
  }

  _renderChatGroups(wrapper) {
    if (!wrapper) return;
    const { source: srcFilter, phase: phaseFilter, query } = this._histFilter;

    let entries = this._histData?.entries || [];
    if (srcFilter)   entries = entries.filter(e => (e.source || 'ui') === srcFilter);
    if (phaseFilter) entries = entries.filter(e => e.tags?.includes('phase:' + phaseFilter));
    if (query) {
      const q = query.toLowerCase();
      entries = entries.filter(e =>
        (e.user_input || '').toLowerCase().includes(q) ||
        (e.output     || '').toLowerCase().includes(q));
    }

    const totalFiltered = entries.length;
    if (!totalFiltered) {
      wrapper.innerHTML = "<div style='padding:20px;color:var(--muted)'>No entries match the current filter.</div>";
      this._renderPageBars(0, 0);
      return;
    }

    const start       = (this._histPage - 1) * _PAGE_SIZE;
    const pageEntries = entries.slice(start, start + _PAGE_SIZE);

    // Build prompt_source_id → commits map (per-prompt); fallback session map for unlinked commits
    const commitsByPrompt   = {};
    const commitsBySessionUnlinked = {};
    for (const c of (this._commitData?.commits || [])) {
      if (c.prompt_source_id) {
        if (!commitsByPrompt[c.prompt_source_id]) commitsByPrompt[c.prompt_source_id] = [];
        commitsByPrompt[c.prompt_source_id].push(c);
      } else if (c.session_id) {
        if (!commitsBySessionUnlinked[c.session_id]) commitsBySessionUnlinked[c.session_id] = [];
        commitsBySessionUnlinked[c.session_id].push(c);
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

      // Fallback strip: commits in this session with no prompt_source_id
      const unlinked = sid ? (commitsBySessionUnlinked[sid] || []) : [];
      const commitStrip = unlinked.length ? `
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;
                    padding:5px 8px;background:var(--surface2);border-radius:4px;margin-bottom:6px;font-size:11px">
          <span style="color:var(--muted);font-weight:600;white-space:nowrap">⑂ ${unlinked.length} unlinked:</span>
          ${unlinked.map(c => {
            const hash = (c.commit_hash || '').slice(0, 8);
            const msg  = (c.commit_msg  || '').slice(0, 60);
            const date = (c.committed_at || '').slice(0, 10);
            return ghBase && c.commit_hash
              ? `<a href="${ghBase}/commit/${this._escapeHtml(c.commit_hash)}" target="_blank"
                    style="font-family:monospace;color:var(--accent);text-decoration:none;white-space:nowrap"
                    title="${this._escapeHtml(msg)} · ${date}">${hash} ↗</a>`
              : `<span style="font-family:monospace;color:var(--accent);white-space:nowrap"
                       title="${this._escapeHtml(msg)} · ${date}">${hash}</span>`;
          }).join('')}
        </div>` : '';

      const entriesHtml = group.entries.map((e, idx) => {
        const isUntagged  = !e.tags?.some(t => t.startsWith('phase:'));
        const borderColor = isUntagged ? '#e74c3c' : 'var(--border)';
        const entryId     = `he-${(sid || 'ns').slice(0, 6)}-${start + idx}`;
        const anchorId    = `ha-${entryId}`;
        const sourceId    = e.ts || '';

        // Pre-existing tag chips from DB (string array)
        const existing = this._entryTags[sourceId] || [];
        const existingChips = existing.map(tag => {
          const color = this._tagColor(tag);
          return `<span data-tag="${this._escapeHtml(tag)}"
                 style="font-size:10px;background:${color}22;color:${color};border:1px solid ${color}55;padding:1px 4px;border-radius:3px;white-space:nowrap;display:inline-flex;align-items:center;gap:2px">
             ${this._escapeHtml(tag)}
             <button onclick="event.stopPropagation();window._historyView._removeTag('${this._escapeHtml(sourceId)}','${this._escapeHtml(tag)}','${anchorId}')"
               style="border:none;background:none;cursor:pointer;color:${color};font-size:9px;padding:0 1px;line-height:1;opacity:.7"
               title="Remove tag">✕</button>
           </span>`;
        }).join('');

        const outputHtml = e.output
          ? `<div style="margin-top:6px">
              <div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px">Response</div>
              <div id="${entryId}-resp"
                style="color:var(--muted);font-size:12px;border-left:2px solid var(--border);
                       padding-left:8px;white-space:pre-wrap;word-break:break-word;
                       max-height:100px;overflow:hidden;transition:max-height 0.2s">
                ${this._escapeHtml(e.output)}
              </div>
              ${e.output.length > 200
                ? `<span style="font-size:11px;color:var(--accent);cursor:pointer;user-select:none"
                    onclick="const el=document.getElementById('${entryId}-resp');
                             el.style.maxHeight=el.style.maxHeight==='none'?'100px':'none';
                             this.textContent=el.style.maxHeight==='none'?'▲ collapse':'▼ expand'">▼ expand</span>`
                : ''}
            </div>`
          : '';

        // Per-prompt linked commits (commits where prompt_source_id === this entry's ts)
        const linkedCommits = commitsByPrompt[sourceId] || [];
        const commitRow = linkedCommits.length ? `
          <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap;
                      margin-top:6px;padding:3px 6px;background:var(--surface2);
                      border-radius:3px;border-left:2px solid var(--accent);font-size:10px">
            <span style="color:var(--muted);font-weight:600;white-space:nowrap">⑂</span>
            ${linkedCommits.map(c => {
              const hash = (c.commit_hash || '').slice(0, 8);
              const msg  = (c.commit_msg  || '').slice(0, 70);
              const date = (c.committed_at || '').slice(0, 10);
              return ghBase && c.commit_hash
                ? `<a href="${ghBase}/commit/${this._escapeHtml(c.commit_hash)}" target="_blank"
                      style="font-family:monospace;color:var(--accent);text-decoration:none;white-space:nowrap"
                      title="${this._escapeHtml(msg)} · ${date}">${hash} ↗</a>`
                : `<span style="font-family:monospace;color:var(--accent);white-space:nowrap"
                         title="${this._escapeHtml(msg)} · ${date}">${hash}</span>`;
            }).join('')}
          </div>` : '';

        return `
        <div class="history-entry" data-ts="${this._escapeHtml(e.ts || '')}"
             style="border:1px solid ${borderColor};border-left:3px solid ${borderColor};
                    border-radius:6px;padding:8px 10px;margin-bottom:5px">
          <div style="display:flex;align-items:center;gap:5px;flex-wrap:wrap;margin-bottom:5px;font-size:11px">
            <span style="color:var(--muted)">${e.ts?.slice(0, 16) || ''}</span>
            <span style="color:var(--accent)">${e.provider || ''}</span>
            <span style="background:var(--surface2);padding:1px 5px;border-radius:3px;font-size:10px">${e.source || 'ui'}</span>
            ${(e.tags||[]).filter(t=>t.startsWith('phase:')).map(t=>`<span style="background:rgba(74,144,226,.15);color:#4a90e2;padding:1px 5px;border-radius:3px">${this._escapeHtml(t.slice(6))}</span>`).join('')}
            ${isUntagged ? `<span style="color:#e74c3c;font-size:10px">⚠ untagged</span>` : ''}
            <span id="${anchorId}" style="margin-left:auto;display:inline-flex;align-items:center;gap:4px;flex-wrap:wrap;position:relative">
              ${existingChips}
              <button onclick="window._historyView._openEntryTagPicker('${this._escapeHtml(sourceId)}','${anchorId}')"
                style="font-size:10px;padding:1px 6px;border:1px solid var(--border);border-radius:3px;
                       cursor:pointer;background:var(--surface);color:var(--muted);white-space:nowrap">
                + Tag
              </button>
            </span>
          </div>
          <div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin-bottom:2px">Prompt</div>
          <div style="font-weight:500;margin-bottom:4px;white-space:pre-wrap;word-break:break-word;font-size:13px">${this._escapeHtml(e.user_input || '')}</div>
          ${outputHtml}
          ${commitRow}
        </div>`;
      }).join('');

      return `
        <div style="border:1px solid var(--border);border-radius:8px;padding:8px;margin-bottom:8px">
          ${sid ? `<div style="font-size:10px;color:var(--muted);margin-bottom:4px;font-family:monospace">session: ${sid.slice(0,20)}…</div>` : ''}
          ${commitStrip}
          ${entriesHtml}
        </div>`;
    }).join('');

    this._renderPageBars(totalFiltered, start);
  }

  // ── Pagination ─────────────────────────────────────────────────────────────

  _renderPageBars(total, start) {
    const nav = document.getElementById('hist-nav-bar');
    if (!nav) return;

    const page       = this._histPage;
    const totalPages = Math.ceil(total / _PAGE_SIZE);
    const end        = Math.min(start + _PAGE_SIZE, total);

    const btnStyle = 'padding:2px 8px;border:1px solid var(--border);border-radius:3px;background:var(--surface);font-size:11px';
    const atFirst = page <= 1;
    const atLast  = page >= totalPages;
    nav.innerHTML = `
      <button onclick="window._historyView._changePage(-1)"
        style="${btnStyle};cursor:${atFirst ? 'default' : 'pointer'};opacity:${atFirst ? '.35' : '1'}"
        ${atFirst ? 'disabled' : ''}>◀</button>
      <span style="color:var(--text);white-space:nowrap;font-size:11px">${start + 1}–${end} / ${total}</span>
      <button onclick="window._historyView._changePage(1)"
        style="${btnStyle};cursor:${atLast ? 'default' : 'pointer'};opacity:${atLast ? '.35' : '1'}"
        ${atLast ? 'disabled' : ''}>▶</button>`;
  }

  _changePage(delta) {
    this._histPage = Math.max(1, this._histPage + delta);
    const wrapper = document.getElementById('hist-chat-groups');
    if (wrapper) this._renderChatGroups(wrapper);
    document.getElementById('history-content')?.scrollTo(0, 0);
  }

  // ── Tag picker (shared by chat entries + commits) ─────────────────────────

  async _buildTagCache(project, _categories) {
    this._tagCache    = [];
    this._tagCacheMap = {};
    try {
      const res = await api.tags.list(project);
      const tags = res.tags || res || [];
      // Group by category_name for picker display
      const groups = {};
      for (const t of tags) {
        const catName = t.category_name || 'other';
        const color   = t.color || '#4a90e2';
        const tagStr  = `${catName}:${t.name}`;
        if (!groups[catName]) groups[catName] = { cat: { name: catName, color }, values: [] };
        groups[catName].values.push({ name: t.name, tagStr });
        this._tagCacheMap[tagStr] = { color, label: tagStr };
      }
      this._tagCache = Object.values(groups);
    } catch (_) {}
  }

  _openEntryTagPicker(sourceId, anchorId) {
    document.querySelectorAll('.entry-tag-picker').forEach(el => el.remove());
    const anchor = document.getElementById(anchorId);
    if (!anchor) return;

    const groups  = this._tagCache || [];
    const picker  = document.createElement('div');
    picker.className = 'entry-tag-picker';
    picker.style.cssText = 'position:absolute;right:0;top:100%;z-index:300;background:var(--bg);' +
      'border:1px solid var(--border);border-radius:6px;padding:6px;min-width:180px;' +
      'max-height:260px;overflow-y:auto;box-shadow:0 4px 16px rgba(0,0,0,.25)';

    if (!groups.length) {
      picker.innerHTML = `<div style="font-size:11px;color:var(--muted);padding:4px 8px">No tags.<br>Create tags in Planner.</div>`;
    } else {
      const fid = `etf-${Date.now()}`;
      picker.innerHTML = `
        <input id="${fid}" placeholder="Filter…" oninput="window._historyView._filterTagPicker('${fid}')"
          style="width:100%;box-sizing:border-box;margin-bottom:4px;padding:3px 6px;border:1px solid var(--border);
                 border-radius:3px;background:var(--surface);color:var(--text);font-size:11px"/>
        <div id="etag-groups">
          ${groups.map(({ cat, values }) => `
            <div class="etag-group">
              <div style="font-size:10px;color:var(--muted);font-weight:600;padding:2px 4px;text-transform:uppercase;letter-spacing:.5px">
                ${this._escapeHtml(cat.name)}
              </div>
              ${values.map(v => `
                <div class="etag-item" data-catname="${this._escapeHtml(cat.name)}"
                  onclick="window._historyView._tagEntryWith('${this._escapeHtml(sourceId)}','${this._escapeHtml(v.tagStr)}','${anchorId}')"
                  style="padding:3px 10px;cursor:pointer;border-radius:3px;font-size:12px;color:${this._escapeHtml(cat.color || 'var(--text)')}"
                  onmouseenter="this.style.background='var(--surface)'" onmouseleave="this.style.background=''">
                  ${this._escapeHtml(v.name)}
                </div>`).join('')}
            </div>`).join('')}
        </div>`;
    }

    anchor.appendChild(picker);
    picker.querySelector('input')?.focus();

    setTimeout(() => {
      document.addEventListener('click', function _close(ev) {
        if (!picker.contains(ev.target) && !anchor.contains(ev.target)) {
          picker.remove();
          document.removeEventListener('click', _close);
        }
      });
    }, 10);
  }

  _filterTagPicker(fid) {
    const q = document.getElementById(fid)?.value?.toLowerCase() || '';
    document.querySelectorAll('.etag-item').forEach(item => {
      item.style.display = (!q || item.textContent.toLowerCase().includes(q) ||
        (item.dataset.catname || '').toLowerCase().includes(q)) ? '' : 'none';
    });
    document.querySelectorAll('.etag-group').forEach(g => {
      g.style.display = [...g.querySelectorAll('.etag-item')].some(i => i.style.display !== 'none') ? '' : 'none';
    });
  }

  async _tagEntryWith(sourceId, tagStr, anchorId) {
    const project = state.currentProject?.name || '';
    document.querySelectorAll('.entry-tag-picker').forEach(el => el.remove());
    const anchor = document.getElementById(anchorId);
    const color  = this._tagColor(tagStr);

    // Track in _entryTags so it survives re-renders
    if (!this._entryTags[sourceId]) this._entryTags[sourceId] = [];
    if (!this._entryTags[sourceId].includes(tagStr)) {
      this._entryTags[sourceId].push(tagStr);
    }

    // Render chip into anchor immediately
    if (anchor) {
      const chip = document.createElement('span');
      chip.dataset.tag = tagStr;
      chip.style.cssText = `font-size:10px;background:${color}22;color:${color};border:1px solid ${color}55;padding:1px 4px;border-radius:3px;white-space:nowrap;display:inline-flex;align-items:center;gap:2px`;
      chip.appendChild(document.createTextNode(tagStr));
      const rmBtn = document.createElement('button');
      rmBtn.textContent = '✕';
      rmBtn.title = 'Remove tag';
      rmBtn.style.cssText = `border:none;background:none;cursor:pointer;color:${color};font-size:9px;padding:0 1px;line-height:1;opacity:.7`;
      rmBtn.addEventListener('click', (ev) => { ev.stopPropagation(); window._historyView._removeTag(sourceId, tagStr, anchorId); });
      chip.appendChild(rmBtn);
      const firstBtn = anchor.querySelector('button:not([title="Remove tag"])');
      if (firstBtn) anchor.insertBefore(chip, firstBtn);
      else anchor.appendChild(chip);
    }

    try {
      await api.entities.tagBySourceId({ source_id: sourceId, tag: tagStr, project });
    } catch (e) {
      console.warn('Tag entry failed:', e.message);
      if (anchor) {
        const err = document.createElement('span');
        err.style.cssText = 'font-size:10px;color:#e74c3c';
        err.textContent = '✕ ' + e.message;
        anchor.appendChild(err);
      }
    }
  }

  // ── Commits tab ───────────────────────────────────────────────────────────

  async _renderCommits(container) {
    const project = state.currentProject?.name || '';
    const [data, cfgData, sourceTags] = await Promise.all([
      api.historyCommits(project, 2000),
      api.getProjectConfig(project).catch(() => ({})),
      api.entities.getSourceTags(project).catch(() => ({})),
    ]);
    if (!this._tagCache) await this._buildTagCache(project);

    // Load commit tags into _entryTags (same dict as prompt tags — keyed by source_id = commit_hash)
    for (const [sid, tagArr] of Object.entries(sourceTags || {})) {
      if (!this._entryTags[sid]) this._entryTags[sid] = tagArr;
    }

    this._commitData = data;
    this._commitPage = 1;

    let ghBase = (cfgData.github_repo || '').replace(/\/$/, '').replace(/\.git$/, '');
    if (ghBase.startsWith('git@')) ghBase = ghBase.replace(/^git@([^:]+):/, 'https://$1/');
    this._ghBase = ghBase;

    this._renderCommitsContainer(container);
  }

  _renderCommitsContainer(container) {
    const allCommits = this._commitData?.commits || [];
    const fromDb     = this._commitData?.source === 'db';

    // Apply phase filter (no auto-populate — default is "All phases")
    const phaseFilter = this._commitFilter.phase || '';
    const commits = phaseFilter ? allCommits.filter(c => c.tags?.includes('phase:' + phaseFilter)) : allCommits;
    const untagged = allCommits.filter(c => !c.tags?.some(t => t.startsWith('phase:'))).length;

    const PHASES = [
      ['', 'All phases'], ['discovery', 'Discovery'], ['development', 'Development'],
      ['testing', 'Testing'], ['review', 'Review'], ['production', 'Production'],
      ['maintenance', 'Maintenance'], ['bugfix', 'Bug Fix'],
    ];
    const phaseSelectHtml = `
      <select id="commit-filter-phase" onchange="window._historyView._applyCommitFilter()"
        style="background:var(--bg);border:1px solid var(--border);border-radius:3px;padding:2px 5px;font-size:11px;color:var(--text)">
        ${PHASES.map(([v, l]) => `<option value="${v}" ${phaseFilter === v ? 'selected' : ''}>${l}</option>`).join('')}
      </select>`;

    const totalPages  = Math.ceil(commits.length / _PAGE_SIZE) || 1;
    const start       = (this._commitPage - 1) * _PAGE_SIZE;
    const end         = Math.min(start + _PAGE_SIZE, commits.length);
    const pageCommits = commits.slice(start, end);

    // Update top-right nav bar (same style as chat pagination)
    const nav = document.getElementById('hist-nav-bar');
    if (nav) {
      const btnStyle = 'padding:2px 8px;border:1px solid var(--border);border-radius:3px;background:var(--surface);font-size:11px';
      const atFirst = this._commitPage <= 1;
      const atLast  = this._commitPage >= totalPages;
      nav.innerHTML = `
        <button onclick="window._historyView._changeCommitPage(-1)"
          style="${btnStyle};cursor:${atFirst ? 'default' : 'pointer'};opacity:${atFirst ? '.35' : '1'}"
          ${atFirst ? 'disabled' : ''}>◀</button>
        <span style="color:var(--text);white-space:nowrap;font-size:11px">${start + 1}–${end} / ${commits.length}</span>
        <button onclick="window._historyView._changeCommitPage(1)"
          style="${btnStyle};cursor:${atLast ? 'default' : 'pointer'};opacity:${atLast ? '.35' : '1'}"
          ${atLast ? 'disabled' : ''}>▶</button>`;
    }

    // Shared header bar (always rendered — filter persists even with 0 results)
    const headerBar = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;flex-wrap:wrap">
        ${phaseSelectHtml}
        <span style="font-size:13px;color:var(--muted)">
          ${phaseFilter ? `${commits.length} / ${allCommits.length}` : allCommits.length} commit${allCommits.length !== 1 ? 's' : ''}
          ${untagged > 0 ? `· <span style="color:#e74c3c;font-weight:600">${untagged} untagged</span>` : ''}
        </span>
        ${fromDb ? `<span style="font-size:11px;color:green;background:rgba(39,174,96,.12);padding:2px 6px;border-radius:4px">live DB</span>`
                 : `<span style="font-size:11px;color:orange;background:rgba(230,126,34,.12);padding:2px 6px;border-radius:4px">file fallback</span>`}
        <div style="flex:1"></div>
        <button id="commits-sync-btn" onclick="window._historyView._syncCommits()"
          style="padding:4px 12px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface);font-size:12px">
          ↻ Sync Commits
        </button>
      </div>`;

    if (!commits.length) {
      container.innerHTML = headerBar + `
        <div style="padding:2rem;text-align:center;color:var(--muted);font-size:13px">
          <div style="font-size:2rem;margin-bottom:.5rem">⑂</div>
          ${phaseFilter ? `No commits with phase <strong>${phaseFilter}</strong>.`
                        : 'No commits yet. Click <strong>↻ Sync Commits</strong> to import.'}
        </div>`;
      return;
    }

    container.innerHTML = headerBar + `
      <div style="overflow-x:auto">
        <table id="commits-table" style="width:100%;border-collapse:collapse;font-size:12px">
          <thead>
            <tr style="background:var(--surface);font-size:10px;text-transform:uppercase;color:var(--muted)">
              <th style="padding:5px 6px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap">Hash</th>
              <th style="padding:5px 6px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap">Date</th>
              <th style="padding:5px 6px;text-align:left;border-bottom:1px solid var(--border)">Phase</th>
              <th style="padding:5px 6px;text-align:left;border-bottom:1px solid var(--border)">Tags ⬡</th>
              <th style="padding:5px 6px;text-align:left;border-bottom:1px solid var(--border)">Message</th>
              <th style="padding:5px 6px;text-align:left;border-bottom:1px solid var(--border);white-space:nowrap">Prompt ↗</th>
            </tr>
          </thead>
          <tbody>
            ${pageCommits.map((c, i) => this._commitRow(c, start + i)).join('')}
          </tbody>
        </table>
      </div>`;
  }

  _applyCommitFilter() {
    const phEl = document.getElementById('commit-filter-phase');
    this._commitFilter.phase = phEl?.value || '';
    this._commitPage = 1;
    const container = document.getElementById('history-content');
    if (container) this._renderCommitsContainer(container);
  }

  _changeCommitPage(delta) {
    const allCommits = this._commitData?.commits || [];
    const phaseFilter = this._commitFilter.phase || '';
    const commits = phaseFilter ? allCommits.filter(c => c.tags?.includes('phase:' + phaseFilter)) : allCommits;
    const totalPages = Math.ceil(commits.length / _PAGE_SIZE);
    this._commitPage = Math.max(1, Math.min(totalPages, this._commitPage + delta));
    const container  = document.getElementById('history-content');
    if (container) this._renderCommitsContainer(container);
    container?.scrollTo(0, 0);
  }

  _commitRow(c, i) {
    const untagged   = !c.tags?.some(t => t.startsWith('phase:'));
    const rowBorder  = untagged ? 'border-left:3px solid #e74c3c' : 'border-left:3px solid transparent';
    const dateStr    = c.committed_at ? c.committed_at.slice(0, 10) : '';
    const ghBase     = this._ghBase || '';
    const hashFull   = c.commit_hash || '';
    const hashShort  = hashFull.slice(0, 8);
    const anchorId   = `ca-${hashShort}`;

    const hashEl = ghBase && hashFull
      ? `<a href="${ghBase}/commit/${hashFull}" target="_blank"
            style="font-family:monospace;color:var(--accent);text-decoration:none">${hashShort} ↗</a>`
      : `<span style="font-family:monospace;color:var(--accent)">${hashShort}</span>`;

    // Prompt cell — clickable ⊙ HH:MM to jump to Chat tab at that entry
    const promptCell = c.prompt_source_id
      ? `<button onclick="window._historyView._jumpToPrompt('${this._escapeHtml(c.prompt_source_id)}')"
           title="Jump to prompt at ${this._escapeHtml(c.prompt_source_id)}"
           style="font-family:monospace;font-size:11px;color:var(--accent);cursor:pointer;
                  background:none;border:none;padding:0;text-decoration:underline dotted">
           ⊙ ${c.prompt_source_id.slice(11, 16)}
         </button>`
      : `<span style="color:var(--muted);font-size:11px">—</span>`;

    // Tag chips from _entryTags keyed by commit_hash (string[])
    const existing      = this._entryTags[hashFull] || [];
    const existingChips = existing.map(tag => {
      const color = this._tagColor(tag);
      return `<span data-tag="${this._escapeHtml(tag)}"
             style="font-size:10px;background:${color}22;color:${color};border:1px solid ${color}55;padding:1px 4px;border-radius:3px;white-space:nowrap;display:inline-flex;align-items:center;gap:2px">
         ${this._escapeHtml(tag)}
         <button onclick="event.stopPropagation();window._historyView._removeTag('${this._escapeHtml(hashFull)}','${this._escapeHtml(tag)}','${anchorId}')"
           style="border:none;background:none;cursor:pointer;color:${color};font-size:9px;padding:0 1px;line-height:1;opacity:.7"
           title="Remove tag">✕</button>
       </span>`;
    }).join('');

    return `
      <tr data-commit-id="${c.id || ''}" data-hash="${this._escapeHtml(hashFull)}"
          style="border-bottom:1px solid var(--border);${rowBorder};transition:background .15s"
          onmouseenter="this.style.background='var(--surface)'"
          onmouseleave="this.style.background=''">
        <td style="padding:4px 6px">${hashEl}</td>
        <td style="padding:4px 6px;color:var(--muted);white-space:nowrap">${dateStr}</td>
        <td style="padding:4px 4px">
          <span style="font-size:11px;color:${untagged ? '#e74c3c' : 'var(--muted)'}">
            ${(c.tags||[]).find(t=>t.startsWith('phase:'))?.slice(6) || '—'}
          </span>
        </td>
        <td style="padding:4px 6px">
          <span id="${anchorId}" style="display:inline-flex;align-items:center;gap:4px;flex-wrap:wrap;position:relative">
            ${existingChips}
            <button onclick="window._historyView._openEntryTagPicker('${this._escapeHtml(hashFull)}','${anchorId}')"
              style="font-size:10px;padding:1px 6px;border:1px solid var(--border);border-radius:3px;
                     cursor:pointer;background:var(--surface);color:var(--muted);white-space:nowrap">
              + Tag
            </button>
          </span>
        </td>
        <td style="padding:4px 6px;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
            title="${this._escapeHtml(c.commit_msg || '')}">
          ${this._escapeHtml(c.commit_msg || '')}
        </td>
        <td style="padding:4px 6px;white-space:nowrap">${promptCell}</td>
      </tr>
    `;
  }

  async _saveField(commitId, field, value) {
    // Phase is now read-only in the Commits table — set phase in Chat and it propagates.
    // Method retained for any future commit field patching.
    if (!commitId) return;
    try {
      await api.patchCommit(commitId, { [field]: value || null });
    } catch (e) {
      console.warn('Commit patch failed:', e.message);
    }
  }

  // ── Jump to prompt from commit ─────────────────────────────────────────────

  async _jumpToPrompt(promptSourceId) {
    if (!promptSourceId) return;

    // Ensure history data is loaded
    const content = document.getElementById('history-content');
    if (!content) return;

    if (!this._histData) {
      content.innerHTML = "<div style='padding:20px;color:var(--muted)'>Loading…</div>";
      await this._renderChat(content);
    }

    // Find which page the entry is on and navigate there
    const entries = this._histData?.entries || [];
    const filter  = this._histFilter || {};
    let filtered  = [...entries];
    if (filter.source)  filtered = filtered.filter(e => (e.source || 'ui') === filter.source);
    if (filter.phase)   filtered = filtered.filter(e => e.tags?.includes('phase:' + filter.phase));
    const idx = filtered.findIndex(e => e.ts === promptSourceId);
    if (idx >= 0) {
      this._histPage = Math.floor(idx / _PAGE_SIZE) + 1;
    }

    // Switch to chat tab and render
    this.activeTab = 'chat';
    document.querySelectorAll('.tab-btn').forEach(btn => {
      btn.style.background = btn.dataset.tab === 'chat' ? 'var(--accent)' : 'var(--surface)';
    });
    this._renderChatContainer(content);

    // Scroll to + highlight the entry after render
    setTimeout(() => {
      const el = content.querySelector(`.history-entry[data-ts="${CSS.escape(promptSourceId)}"]`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.style.outline = '2px solid var(--accent)';
        setTimeout(() => { el.style.outline = ''; }, 2500);
      }
    }, 120);
  }

  // ── Tag removal ────────────────────────────────────────────────────────────

  async _removeTag(sourceId, tagStr, anchorId) {
    const project = state.currentProject?.name || '';

    // Remove from in-memory state immediately (optimistic)
    if (this._entryTags[sourceId]) {
      this._entryTags[sourceId] = this._entryTags[sourceId].filter(t => t !== tagStr);
    }

    // Remove chip from DOM
    const anchor = document.getElementById(anchorId);
    if (anchor) {
      const chip = anchor.querySelector(`[data-tag="${CSS.escape(tagStr)}"]`);
      if (chip) chip.remove();
    }

    // Persist to backend
    try {
      await api.entities.untagBySourceId(sourceId, tagStr, project);
    } catch (e) {
      console.warn('Remove tag failed:', e.message);
      // Re-fetch tags on failure so state stays consistent
      try {
        const fresh = await api.entities.getSourceTags(project);
        for (const [sid, tagArr] of Object.entries(fresh || {})) {
          this._entryTags[sid] = tagArr;
        }
      } catch (_) {}
    }
  }

  _refreshUntaggedCount() {
    const rows = document.querySelectorAll('#commits-table tbody tr');
    let untagged = 0;
    rows.forEach(r => { if (r.style.borderLeft.includes('#e74c3c')) untagged++; });
    // update the counter badge in header if present
    const badge = document.querySelector('#history-content [style*="e74c3c"]');
    if (badge && badge.tagName === 'SPAN') badge.textContent = untagged > 0 ? `${untagged} untagged` : '';
  }

  async _syncCommits() {
    const btn = document.getElementById('commits-sync-btn');
    if (btn) { btn.textContent = 'Syncing…'; btn.disabled = true; }
    const project = state.currentProject?.name || '';
    try {
      const res = await api.syncCommits(project);
      this._commitData = null;   // invalidate cache
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
    container.innerHTML = '<div style="padding:16px;color:var(--muted)">Loading runs…</div>';
    try {
      const res  = await fetch(_histUrl('/history/runs?limit=50'));
      const data = await res.json();
      const runs = data.runs || [];

      if (!runs.length) {
        container.innerHTML = "<div style='padding:20px;color:var(--muted)'>No workflow runs yet.</div>";
        return;
      }

      const STATUS_COLORS = {
        done: '#3ecf8e', error: '#e85d75', running: '#f5a623',
        stopped: '#888', cancelled: '#888', waiting_approval: '#9b7ef8',
      };

      const escH = s => String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

      container.innerHTML = runs.map(r => {
        const statusColor = STATUS_COLORS[r.status] || 'var(--muted)';
        const ts = (r.started_at || '').slice(0, 16).replace('T', ' ');
        const dur = r.duration_secs ? `${r.duration_secs}s` : '';
        const cost = r.total_cost_usd > 0 ? `$${Number(r.total_cost_usd).toFixed(4)}` : '';
        const input = (r.user_input || '').slice(0, 80);
        // If the run has an ID (DB run), clicking opens it in the Pipelines tab
        const clickHandler = r.id && /^[0-9a-f-]{36}$/.test(r.id)
          ? `onclick="window._historyView._openRunInPipelines('${escH(r.id)}')"`
          : `onclick="window._historyView._showRunDetail('${escH(r.file)}')"`;
        return `
          <div class="run-entry" style="border:1px solid var(--border);border-radius:6px;
               padding:10px 14px;margin-bottom:8px;cursor:pointer;
               transition:background 0.12s" onmouseover="this.style.background='var(--bg2)'"
               onmouseout="this.style.background=''" ${clickHandler}>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
              <span style="width:8px;height:8px;border-radius:50%;background:${statusColor};flex-shrink:0;display:inline-block"></span>
              <strong style="font-size:0.82rem">${escH(r.workflow || r.file)}</strong>
              <span style="color:${statusColor};font-size:0.72rem">${escH(r.status || '')}</span>
              <span style="color:var(--muted);font-size:0.72rem;margin-left:auto">${escH(ts)}</span>
              ${r.steps ? `<span style="color:var(--muted);font-size:0.72rem">${r.steps} steps</span>` : ''}
              ${dur ? `<span style="color:var(--muted);font-size:0.72rem">${escH(dur)}</span>` : ''}
              ${cost ? `<span style="color:#3ecf8e;font-size:0.72rem">${escH(cost)}</span>` : ''}
            </div>
            ${input ? `<div style="font-size:0.72rem;color:var(--muted);margin-top:4px;
                            overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escH(input)}</div>` : ''}
            ${r.error ? `<div style="font-size:0.72rem;color:#e85d75;margin-top:4px">${escH(r.error.slice(0,100))}</div>` : ''}
          </div>`;
      }).join('');
    } catch (e) {
      container.innerHTML = `<div style='padding:20px;color:var(--red)'>Could not load runs: ${e.message}</div>`;
    }
  }

  _openRunInPipelines(runId) {
    // Set pending run to auto-open when Pipelines tab renders
    window._pendingRunOpen = runId;
    // Navigate to Pipelines tab (renderGraphWorkflow will pick up _pendingRunOpen)
    if (window.navigateTo) {
      window.navigateTo('workflow');
    }
  }

  async _showRunDetail(filename) {
    try {
      const res = await fetch(_histUrl(`/history/runs/${filename}`));
      const run = await res.json();
      const modal = document.createElement('div');
      modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.7);display:flex;align-items:center;justify-content:center;z-index:1000';
      modal.innerHTML = `
        <div style="background:var(--bg);border-radius:8px;padding:24px;max-width:700px;width:90%;max-height:80vh;overflow-y:auto">
          <div style="display:flex;justify-content:space-between;margin-bottom:16px">
            <strong>Run: ${run.workflow}</strong>
            <button onclick="this.closest('div[style*=fixed]').remove()">✕</button>
          </div>
          <pre style="font-size:12px;background:var(--surface);padding:12px;border-radius:4px;overflow-x:auto">${JSON.stringify(run, null, 2)}</pre>
        </div>`;
      document.body.appendChild(modal);
    } catch (e) {
      alert(`Could not load run detail: ${e.message}`);
    }
  }

  // ── Evals tab ──────────────────────────────────────────────────────────────

  async _renderEvals(container) {
    const res  = await fetch(_histUrl('/history/evals'));
    const data = await res.json();
    const evals = data.evals || [];

    if (!evals.length) {
      container.innerHTML = "<div style='padding:20px;color:var(--muted)'>No prompt evaluations yet.</div>";
      return;
    }
    container.innerHTML = evals.map(e => `
      <div style="border:1px solid var(--border);border-radius:6px;padding:12px;margin-bottom:10px">
        <div style="display:flex;gap:8px;margin-bottom:8px">
          <span style="color:var(--muted);font-size:12px">${e.ts?.slice(0, 16) || ''}</span>
          <span style="color:var(--accent)">${e.prompt_file || ''}</span>
          <span style="color:green">Winner: ${e.winner || '(none)'}</span>
        </div>
        <div style="font-size:12px;color:var(--muted)">Providers: ${(e.providers || []).join(', ')}</div>
        ${e.notes ? `<div style="margin-top:4px;font-size:12px">${this._escapeHtml(e.notes)}</div>` : ''}
      </div>`).join('');
  }

  // ── Global search ─────────────────────────────────────────────────────────

  _filterContent(query) {
    if (this.activeTab === 'chat') {
      this._histFilter.query = query;
      this._histPage = 1;
      const wrapper = document.getElementById('hist-chat-groups');
      if (wrapper) this._renderChatGroups(wrapper);
    } else {
      // DOM filter for runs/evals (not cached)
      const entries = document.querySelectorAll('.history-entry, .run-entry');
      entries.forEach(el => {
        el.style.display = el.textContent.toLowerCase().includes(query.toLowerCase()) ? '' : 'none';
      });
    }
  }

  _tagColor(tagStr) {
    const prefix = (tagStr || '').split(':')[0];
    const MAP = { phase: '#3b82f6', feature: '#22c55e', bug: '#ef4444' };
    return MAP[prefix] || '#4a90e2';
  }

  _escapeHtml(text) {
    return String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
}
