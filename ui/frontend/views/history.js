/**
 * History view — JSONL chat history, commits, workflow run logs, entity tags.
 *
 * Tabs:
 *   Chat  |  Commits  |  Runs  |  Evals  |  Tags
 *
 * Commits tab:
 *   - If PostgreSQL available: loads from `commits` table with full metadata.
 *   - Fallback: reads commit_log.jsonl — all rows shown as untagged (red).
 *   - Inline edit: click Phase/Feature cell to edit; saves via PATCH /history/commits/{id}.
 *   - Sync button: imports commit_log.jsonl → DB.
 *   - Untagged rows (no phase): highlighted with red left border.
 *
 * Tags tab:
 *   Three-column layout:
 *     Left   — tag categories (feature, bug, component, doc_type, customer, phase)
 *              + create new category
 *     Middle — values for selected category + create new value
 *     Right  — events (prompts + commits) linked to selected value
 *              Each event row has "Add tag" chips for other values.
 */

import { state } from '../stores/state.js';
import { api } from '../utils/api.js';

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
    this.container = container;
    this.activeTab = "chat";
    this._render();
    this._loadTab("chat");
  }

  _render() {
    const tabs = ["chat", "commits", "runs", "evals", "tags"];
    this.container.innerHTML = `
      <div class="history-layout" style="display:flex;flex-direction:column;height:100%">
        <div class="tab-bar" style="display:flex;gap:4px;padding:8px 12px;border-bottom:1px solid var(--border);align-items:center">
          ${tabs.map(t =>
            `<button class="tab-btn" data-tab="${t}"
              style="padding:6px 14px;border-radius:6px;border:1px solid var(--border);cursor:pointer;background:${this.activeTab === t ? 'var(--accent)' : 'var(--surface)'}"
              onclick="window._historyView._loadTab('${t}')">
              ${t === 'tags' ? '⬡ Tags' : t.charAt(0).toUpperCase() + t.slice(1)}
            </button>`).join('')}
          <div style="flex:1"></div>
          <input id="history-search" placeholder="Search..."
            style="padding:4px 8px;border:1px solid var(--border);border-radius:4px;background:var(--surface);color:var(--text)" />
        </div>
        <div id="history-content" style="flex:1;overflow-y:auto;padding:12px;min-height:0"></div>
      </div>
    `;
    window._historyView = this;
    // Tags tab uses its own layout — skip search filter
    document.getElementById("history-search")?.addEventListener("input", (e) => {
      if (this.activeTab !== 'tags') this._filterContent(e.target.value);
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
    content.innerHTML = "<div style='padding:20px;color:var(--muted)'>Loading...</div>";

    try {
      if (tab === "chat")    await this._renderChat(content);
      else if (tab === "commits") await this._renderCommits(content);
      else if (tab === "runs")    await this._renderRuns(content);
      else if (tab === "evals")   await this._renderEvals(content);
      else if (tab === "tags")    await this._renderTags(content);
    } catch (e) {
      content.innerHTML = `<div style="color:red;padding:20px">Error: ${e.message}</div>`;
    }
  }

  async _renderChat(container) {
    const project = state.currentProject?.name || '';
    const res = await fetch(_histUrl('/history/chat?limit=100'));
    const data = await res.json();
    const entries = data.entries || [];

    // Load session tags to show active context
    let sessionTags = { phase: null, feature: null, bug_ref: null };
    try { sessionTags = await api.getSessionTags(project); } catch {}

    const untaggedCount = entries.filter(e => !e.phase && !e.feature).length;

    const tagsBar = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;padding:8px 10px;background:var(--surface);border-radius:6px;flex-wrap:wrap;font-size:12px">
        <span style="color:var(--muted);font-weight:600">Active tags:</span>
        ${this._tagChip('phase', sessionTags.phase, ['', 'discovery', 'development', 'prod'])}
        ${this._tagChip('feature', sessionTags.feature, null)}
        ${this._tagChip('bug_ref', sessionTags.bug_ref, null)}
        <div style="flex:1"></div>
        ${untaggedCount > 0
          ? `<span style="color:#e74c3c;font-size:11px;font-weight:600">${untaggedCount} untagged prompts</span>`
          : `<span style="color:green;font-size:11px">All prompts tagged ✓</span>`}
      </div>`;

    if (!entries.length) {
      container.innerHTML = tagsBar + "<div style='padding:20px;color:var(--muted)'>No chat history yet.</div>";
      return;
    }

    container.innerHTML = tagsBar + entries
      .map((e) => {
        const isUntagged = !e.phase && !e.feature;
        const borderColor = isUntagged ? '#e74c3c' : 'var(--border)';
        return `
        <div class="history-entry" style="border:1px solid ${borderColor};border-left:3px solid ${borderColor};border-radius:6px;padding:12px;margin-bottom:8px">
          <div style="display:flex;gap:8px;margin-bottom:6px;font-size:11px;color:var(--muted);flex-wrap:wrap;align-items:center">
            <span>${e.ts?.slice(0, 16) || ""}</span>
            <span style="color:var(--accent)">${e.provider || ""}</span>
            ${e.source === "claude_code" ? `<span style="background:var(--surface2);padding:1px 5px;border-radius:3px;font-size:10px">claude-code</span>` : ""}
            ${e.source === "ui" ? `<span style="background:var(--surface2);padding:1px 5px;border-radius:3px;font-size:10px">ui</span>` : ""}
            ${e.phase ? `<span style="background:rgba(74,144,226,.15);color:#4a90e2;padding:1px 5px;border-radius:3px">${e.phase}</span>` : ''}
            ${e.feature ? `<span style="background:rgba(39,174,96,.15);color:#27ae60;padding:1px 5px;border-radius:3px">#${e.feature}</span>` : ''}
            ${e.tag ? `<span style="color:orange">#${e.tag}</span>` : ""}
            ${isUntagged ? `<span style="color:#e74c3c;font-size:10px">⚠ untagged</span>` : ''}
          </div>
          <div style="font-weight:500;margin-bottom:4px">${this._escapeHtml(e.user_input?.slice(0, 150) || "")}</div>
          ${e.output ? `<div style="color:var(--muted);font-size:12px;margin-top:4px;border-left:2px solid var(--border);padding-left:8px">${this._escapeHtml(e.output.slice(0, 200))}${e.output.length > 200 ? "…" : ""}</div>` : ""}
        </div>`;
      })
      .join("");
  }

  _tagChip(field, value, options) {
    const label = field === 'bug_ref' ? 'Bug' : field.charAt(0).toUpperCase() + field.slice(1);
    if (options) {
      return `<label style="display:flex;align-items:center;gap:4px">
        <span style="color:var(--muted)">${label}:</span>
        <select onchange="window._historyView._saveSessionTag('${field}',this.value)"
          style="background:var(--surface);border:1px solid var(--border);border-radius:3px;padding:2px 6px;font-size:11px;color:${value ? 'var(--accent)' : 'var(--muted)'}">
          ${options.map(o => `<option value="${o}" ${value === o ? 'selected' : ''}>${o || '—'}</option>`).join('')}
        </select></label>`;
    }
    return `<label style="display:flex;align-items:center;gap:4px">
      <span style="color:var(--muted)">${label}:</span>
      <input type="text" value="${this._escapeHtml(value || '')}" placeholder="—"
        onblur="window._historyView._saveSessionTag('${field}',this.value)"
        onkeydown="if(event.key==='Enter')this.blur()"
        style="background:var(--surface);border:1px solid var(--border);border-radius:3px;padding:2px 6px;font-size:11px;width:90px;color:${value ? 'var(--accent)' : 'var(--muted)'}"/>
      </label>`;
  }

  async _saveSessionTag(field, value) {
    const project = state.currentProject?.name || '';
    try {
      let current = { phase: null, feature: null, bug_ref: null };
      try { current = await api.getSessionTags(project); } catch {}
      current[field] = value || null;
      await api.putSessionTags(project, current);
    } catch (e) {
      console.warn('Session tag save failed:', e.message);
    }
  }

  async _renderCommits(container) {
    const project = state.currentProject?.name || '';
    const data = await api.historyCommits(project, 100);
    const commits = data.commits || [];
    const fromDb = data.source === 'db';

    const untaggedCount = commits.filter(c => !c.phase).length;

    container.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;flex-wrap:wrap">
        <span style="font-size:13px;color:var(--muted)">${commits.length} commits</span>
        ${untaggedCount > 0 ? `<span style="font-size:12px;color:#e74c3c;font-weight:600">${untaggedCount} untagged</span>` : ''}
        ${fromDb
          ? `<span style="font-size:11px;color:green;background:rgba(39,174,96,.12);padding:2px 6px;border-radius:4px">live DB</span>`
          : `<span style="font-size:11px;color:orange;background:rgba(230,126,34,.12);padding:2px 6px;border-radius:4px">file fallback — no DB</span>`}
        <div style="flex:1"></div>
        <button id="commits-sync-btn" onclick="window._historyView._syncCommits()"
          style="padding:4px 12px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface);font-size:12px">
          ↻ Sync from log
        </button>
      </div>
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
            </tr>
          </thead>
          <tbody>
            ${commits.map((c, i) => this._commitRow(c, i)).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  _commitRow(c, i) {
    const untagged = !c.phase;
    const rowBorder = untagged ? 'border-left:3px solid #e74c3c' : 'border-left:3px solid transparent';
    const dateStr = c.committed_at ? c.committed_at.slice(0, 10) : '';
    const canEdit = !!c.id;
    const editAttr = canEdit ? 'contenteditable="true"' : '';
    const editStyle = canEdit ? 'cursor:text;min-width:60px' : 'color:var(--muted)';
    const PHASES = ['', 'discovery', 'development', 'prod'];

    return `
      <tr data-commit-id="${c.id || ''}" data-idx="${i}"
          style="border-bottom:1px solid var(--border);${rowBorder};transition:background .15s"
          onmouseenter="this.style.background='var(--surface)'"
          onmouseleave="this.style.background=''">
        <td style="padding:5px 8px;font-family:monospace;color:var(--accent)">${(c.commit_hash || '').slice(0, 8)}</td>
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
      </tr>
    `;
  }

  async _saveField(commitId, field, value) {
    if (!commitId) return;
    const project = state.currentProject?.name || '';
    try {
      await api.patchCommit(commitId, { [field]: value || null });
      // Refresh row background — untagged detection
      const row = document.querySelector(`tr[data-commit-id="${commitId}"]`);
      if (row) {
        const phaseSelect = row.querySelector('select');
        const hasPhase = phaseSelect ? phaseSelect.value !== '' : false;
        row.style.borderLeft = hasPhase ? '3px solid transparent' : '3px solid #e74c3c';
        if (phaseSelect) phaseSelect.style.color = hasPhase ? 'var(--text)' : '#e74c3c';
        // Update untagged count badge
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
      alert(`Synced ${res.imported} new commits.`);
      await this._loadTab('commits');
    } catch (e) {
      alert('Sync failed: ' + e.message);
    } finally {
      if (btn) { btn.textContent = '↻ Sync from log'; btn.disabled = false; }
    }
  }

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

  // ── Tags tab ─────────────────────────────────────────────────────────────────

  async _renderTags(container) {
    const project = state.currentProject?.name || '';

    container.style.padding = '0';
    container.style.overflow = 'hidden';
    container.style.display = 'flex';
    container.style.flexDirection = 'column';

    container.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border);flex-shrink:0">
        <span style="font-size:13px;font-weight:600">Entity Tags</span>
        <button id="tags-sync-btn" onclick="window._historyView._syncEvents()"
          style="padding:3px 10px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface);font-size:11px">
          ↻ Sync events
        </button>
        <div style="flex:1"></div>
        <span id="tags-status" style="font-size:11px;color:var(--muted)"></span>
      </div>
      <div style="display:flex;flex:1;min-height:0;overflow:hidden">
        <!-- Categories -->
        <div id="tags-cats" style="width:160px;flex-shrink:0;border-right:1px solid var(--border);overflow-y:auto;padding:8px 6px"></div>
        <!-- Values -->
        <div id="tags-vals" style="width:200px;flex-shrink:0;border-right:1px solid var(--border);overflow-y:auto;padding:8px 6px">
          <div style="color:var(--muted);font-size:12px;padding:8px">← Select a category</div>
        </div>
        <!-- Events -->
        <div id="tags-events" style="flex:1;overflow-y:auto;padding:8px 10px">
          <div style="color:var(--muted);font-size:12px;padding:8px">← Select a value to see linked events</div>
        </div>
      </div>
    `;

    // Load categories
    this._tagsState = { selectedCat: null, selectedVal: null, project };
    await this._loadCategories();
  }

  async _loadCategories() {
    const { project } = this._tagsState;
    const pane = document.getElementById('tags-cats');
    if (!pane) return;
    try {
      const data = await api.entities.listCategories(project);
      const cats = data.categories || [];
      pane.innerHTML = `
        <div style="font-size:10px;text-transform:uppercase;color:var(--muted);padding:2px 4px 6px;letter-spacing:.05em">Categories</div>
        ${cats.map(c => `
          <div class="tag-cat-row" data-id="${c.id}" data-name="${this._escapeHtml(c.name)}"
            onclick="window._historyView._selectCat(${c.id},'${this._escapeHtml(c.name)}')"
            style="display:flex;align-items:center;gap:6px;padding:6px 8px;border-radius:5px;cursor:pointer;margin-bottom:2px;
                   background:${this._tagsState.selectedCat === c.id ? 'var(--accent)' : 'transparent'}">
            <span style="color:${c.color};font-size:14px">${c.icon}</span>
            <span style="font-size:12px;flex:1">${this._escapeHtml(c.name)}</span>
            <span style="font-size:10px;color:var(--muted)">${c.value_count}</span>
          </div>`).join('')}
        <div style="margin-top:8px;padding:4px">
          <input id="new-cat-input" placeholder="New category…"
            style="width:100%;padding:4px 6px;border:1px dashed var(--border);border-radius:4px;background:transparent;color:var(--text);font-size:11px"
            onkeydown="if(event.key==='Enter')window._historyView._createCategory(this.value)" />
        </div>`;
    } catch (e) {
      pane.innerHTML = `<div style="color:red;font-size:11px;padding:8px">${this._escapeHtml(e.message)}</div>`;
    }
  }

  async _selectCat(catId, catName) {
    this._tagsState.selectedCat = catId;
    this._tagsState.selectedVal = null;
    // Highlight selected
    document.querySelectorAll('.tag-cat-row').forEach(r => {
      r.style.background = parseInt(r.dataset.id) === catId ? 'var(--accent)' : 'transparent';
    });
    await this._loadValues(catId, catName);
    // Clear events pane
    const ep = document.getElementById('tags-events');
    if (ep) ep.innerHTML = '<div style="color:var(--muted);font-size:12px;padding:8px">← Select a value</div>';
  }

  async _loadValues(catId, catName) {
    const { project } = this._tagsState;
    const pane = document.getElementById('tags-vals');
    if (!pane) return;
    pane.innerHTML = '<div style="color:var(--muted);font-size:11px;padding:8px">Loading…</div>';
    try {
      const data = await api.entities.listValues(project, catId);
      const vals = data.values || [];
      pane.innerHTML = `
        <div style="font-size:10px;text-transform:uppercase;color:var(--muted);padding:2px 4px 6px;letter-spacing:.05em">${this._escapeHtml(catName)}</div>
        ${vals.map(v => `
          <div class="tag-val-row" data-id="${v.id}"
            onclick="window._historyView._selectVal(${v.id},'${this._escapeHtml(v.name)}')"
            style="display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:5px;cursor:pointer;margin-bottom:2px;
                   background:${this._tagsState.selectedVal === v.id ? 'var(--accent)' : 'transparent'}">
            <span style="font-size:12px;flex:1">${this._escapeHtml(v.name)}</span>
            <span style="font-size:10px;color:var(--muted)">${v.event_count}</span>
            <button onclick="event.stopPropagation();window._historyView._deleteValue(${v.id})"
              style="border:none;background:none;cursor:pointer;color:var(--muted);font-size:10px;padding:0 2px">✕</button>
          </div>`).join('')}
        ${vals.length === 0 ? '<div style="color:var(--muted);font-size:11px;padding:4px 8px">No values yet</div>' : ''}
        <div style="margin-top:8px;padding:4px">
          <input id="new-val-input" placeholder="Add value…"
            style="width:100%;padding:4px 6px;border:1px dashed var(--border);border-radius:4px;background:transparent;color:var(--text);font-size:11px"
            onkeydown="if(event.key==='Enter')window._historyView._createValue(${catId},this.value)" />
        </div>`;
    } catch (e) {
      pane.innerHTML = `<div style="color:red;font-size:11px;padding:8px">${this._escapeHtml(e.message)}</div>`;
    }
  }

  async _selectVal(valId, valName) {
    this._tagsState.selectedVal = valId;
    document.querySelectorAll('.tag-val-row').forEach(r => {
      r.style.background = parseInt(r.dataset.id) === valId ? 'var(--accent)' : 'transparent';
    });
    await this._loadValueEvents(valId, valName);
  }

  async _loadValueEvents(valId, valName) {
    const { project } = this._tagsState;
    const pane = document.getElementById('tags-events');
    if (!pane) return;
    pane.innerHTML = '<div style="color:var(--muted);font-size:11px;padding:8px">Loading events…</div>';
    try {
      const data = await api.entities.valueEvents(valId, project);
      const events = data.events || [];
      const untagged = await api.entities.listEvents(project, { limit: 30 });
      const allEvents = untagged.events || [];

      pane.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
          <span style="font-size:13px;font-weight:600">${this._escapeHtml(valName)}</span>
          <span style="font-size:11px;color:var(--muted)">${events.length} events</span>
          <div style="flex:1"></div>
          <button onclick="window._historyView._showTagPicker(${valId},'${this._escapeHtml(valName)}')"
            style="padding:3px 10px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface);font-size:11px">
            + Tag event
          </button>
        </div>
        ${events.length === 0
          ? '<div style="color:var(--muted);font-size:12px;padding:8px">No events tagged with this value yet.<br>Click "+ Tag event" to link events.</div>'
          : events.map(e => this._eventRow(e, valId)).join('')}
      `;
    } catch (e) {
      pane.innerHTML = `<div style="color:red;font-size:11px;padding:8px">${this._escapeHtml(e.message)}</div>`;
    }
  }

  _eventRow(e, currentValId) {
    const isCommit = e.event_type === 'commit';
    const icon = isCommit ? '⑂' : '◉';
    const color = isCommit ? 'var(--accent)' : 'var(--text)';
    const date = (e.created_at || '').slice(0, 10);
    const tags = (e.tags || []).map(t =>
      `<span style="font-size:10px;padding:1px 5px;border-radius:3px;background:${t.color}22;color:${t.color};margin-right:3px"
        title="Remove tag" onclick="window._historyView._removeTag(${e.id},${t.value_id},${currentValId})"
        style="cursor:pointer">${t.icon||''}${t.value}</span>`
    ).join('');

    return `
      <div style="border:1px solid var(--border);border-radius:5px;padding:8px 10px;margin-bottom:6px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;font-size:11px">
          <span style="color:${color}">${icon} ${e.event_type}</span>
          <span style="color:var(--muted)">${date}</span>
          <span style="color:var(--muted);font-family:monospace">${(e.source_id||'').slice(0,8)}</span>
          <div style="flex:1"></div>
          <button onclick="window._historyView._removeTag(${e.id},${currentValId},${currentValId})"
            style="border:none;background:none;cursor:pointer;color:#e74c3c;font-size:10px">Remove</button>
        </div>
        <div style="font-size:12px;margin-bottom:4px">${this._escapeHtml((e.title||'').slice(0,120))}</div>
        ${tags ? `<div style="margin-top:4px">${tags}</div>` : ''}
      </div>`;
  }

  async _showTagPicker(valId, valName) {
    const { project } = this._tagsState;
    // Load recent untagged events
    const data = await api.entities.listEvents(project, { limit: 50 });
    const events = (data.events || []).filter(e => !(e.tags||[]).some(t => t.value_id === valId));

    const modal = document.createElement('div');
    modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;z-index:2000';
    modal.innerHTML = `
      <div style="background:var(--bg);border-radius:8px;padding:20px;width:560px;max-height:70vh;display:flex;flex-direction:column;overflow:hidden">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
          <strong>Tag events with: ${this._escapeHtml(valName)}</strong>
          <button onclick="this.closest('[style*=fixed]').remove()" style="border:none;background:none;cursor:pointer;font-size:16px">✕</button>
        </div>
        <input id="tag-picker-search" placeholder="Filter events…"
          style="padding:6px 8px;border:1px solid var(--border);border-radius:4px;margin-bottom:8px;background:var(--surface);color:var(--text)" />
        <div style="overflow-y:auto;flex:1">
          ${events.length === 0
            ? '<div style="color:var(--muted);padding:12px;text-align:center">All events already tagged</div>'
            : events.map(e => `
              <div class="picker-row" style="display:flex;align-items:center;gap:8px;padding:6px 8px;border-bottom:1px solid var(--border);cursor:pointer"
                onclick="window._historyView._tagEvent(${e.id},${valId},'${this._escapeHtml(valName)}',this)">
                <span style="font-size:11px;color:var(--accent);width:50px">${e.event_type}</span>
                <span style="font-size:11px;color:var(--muted);width:80px">${(e.created_at||'').slice(0,10)}</span>
                <span style="font-size:12px;flex:1">${this._escapeHtml((e.title||'').slice(0,100))}</span>
                <span style="font-size:11px;color:var(--muted)">+ Tag</span>
              </div>`).join('')}
        </div>
      </div>`;
    document.body.appendChild(modal);
    modal.querySelector('#tag-picker-search')?.addEventListener('input', ev => {
      const q = ev.target.value.toLowerCase();
      modal.querySelectorAll('.picker-row').forEach(r => {
        r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
      });
    });
  }

  async _tagEvent(eventId, valId, valName, rowEl) {
    try {
      await api.entities.addTag(eventId, valId);
      if (rowEl) { rowEl.style.background = 'rgba(39,174,96,.15)'; rowEl.style.pointerEvents = 'none'; rowEl.lastElementChild.textContent = '✓ Tagged'; }
      // Refresh events pane
      await this._loadValueEvents(valId, valName);
    } catch (e) {
      alert('Tag failed: ' + e.message);
    }
  }

  async _removeTag(eventId, valId, currentValId) {
    try {
      await api.entities.removeTag(eventId, valId);
      // Refresh events pane
      if (this._tagsState.selectedVal) {
        const valName = document.querySelector(`.tag-val-row[data-id="${currentValId}"]`)?.textContent?.trim() || '';
        await this._loadValueEvents(currentValId, valName);
      }
    } catch (e) {
      alert('Remove failed: ' + e.message);
    }
  }

  async _createCategory(name) {
    name = (name || '').trim();
    if (!name) return;
    const { project } = this._tagsState;
    const input = document.getElementById('new-cat-input');
    try {
      await api.entities.createCategory({ name, project });
      if (input) input.value = '';
      await this._loadCategories();
    } catch (e) { alert('Create failed: ' + e.message); }
  }

  async _createValue(catId, name) {
    name = (name || '').trim();
    if (!name) return;
    const { project } = this._tagsState;
    const input = document.getElementById('new-val-input');
    const catName = document.querySelector('.tag-cat-row[data-id="' + catId + '"] span:nth-child(2)')?.textContent || '';
    try {
      await api.entities.createValue({ category_id: catId, name, project });
      if (input) input.value = '';
      await this._loadValues(catId, catName);
    } catch (e) { alert('Create failed: ' + e.message); }
  }

  async _deleteValue(valId) {
    if (!confirm('Delete this value and all its event links?')) return;
    try {
      await api.entities.deleteValue(valId);
      const catId = this._tagsState.selectedCat;
      const catName = document.querySelector(`.tag-cat-row[data-id="${catId}"] span:nth-child(2)`)?.textContent || '';
      await this._loadValues(catId, catName);
      const ep = document.getElementById('tags-events');
      if (ep) ep.innerHTML = '<div style="color:var(--muted);font-size:12px;padding:8px">← Select a value</div>';
    } catch (e) { alert('Delete failed: ' + e.message); }
  }

  async _syncEvents() {
    const btn = document.getElementById('tags-sync-btn');
    const status = document.getElementById('tags-status');
    const { project } = this._tagsState;
    if (btn) { btn.textContent = 'Syncing…'; btn.disabled = true; }
    try {
      const res = await api.entities.syncEvents(project);
      const total = (res.imported?.prompt || 0) + (res.imported?.commit || 0);
      if (status) status.textContent = `✓ ${total} events synced`;
      await this._loadCategories();
    } catch (e) {
      if (status) status.textContent = 'Sync failed: ' + e.message;
    } finally {
      if (btn) { btn.textContent = '↻ Sync events'; btn.disabled = false; }
    }
  }

  // ── End Tags tab ──────────────────────────────────────────────────────────────

  _filterContent(query) {
    const entries = document.querySelectorAll(".history-entry, .run-entry");
    entries.forEach((el) => {
      el.style.display = el.textContent.toLowerCase().includes(query.toLowerCase()) ? "" : "none";
    });
  }

  _escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }
}
