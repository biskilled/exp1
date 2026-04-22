/**
 * work_items.js — Work Items tab view (replaces backlog.js).
 *
 * Displays DB-first work items (mem_work_items table) in a hierarchical view:
 *
 *   USE CASE group (level=3) — [Approve All] [Reject All]
 *     ├─ 🐛 BU pending  Login 500 error              [▼] [✓] [✗] [edit]
 *     ├─ ⚡ FE pending  JWT refresh flow             [▼] [✓] [✗]
 *     └─ ✓ TA pending  Update deps                  [▼] [✓] [✗]
 *
 *   ⚑ POLICY (level=2, no parent)  No raw SQL       [▼] [✓] [✗]
 *
 * API: api.wi (defined in utils/api.js)
 */

import { api }  from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { state } from '../stores/state.js';

let _project   = '';
let _polling   = null;
let _stats     = {};
let _allItems  = [];    // all loaded items
let _filter    = '';    // wi_type filter
let _dragItemId = null; // item id being dragged

// ── Type config ──────────────────────────────────────────────────────────────

const _TYPE = {
  use_case:    { icon: '◻',  label: 'Use Case',    color: '#06b6d4', cls: 'wi-type-uc'  },
  feature:     { icon: '⚡', label: 'Feature',     color: '#22c55e', cls: 'wi-type-feat' },
  bug:         { icon: '🐛', label: 'Bug',         color: '#ef4444', cls: 'wi-type-bug'  },
  task:        { icon: '✓',  label: 'Task',        color: '#3b82f6', cls: 'wi-type-task' },
  policy:      { icon: '⚑', label: 'Policy',      color: '#8b5cf6', cls: 'wi-type-pol'  },
  requirement: { icon: '◎',  label: 'Requirement', color: '#f59e0b', cls: 'wi-type-req'  },
};

function _itemStatus(item) {
  const s = item.score_status || 0;
  if (s === 0) return { label: 'Not Started', cls: 'wi-s-req'  };
  if (s >= 5)  return { label: 'Done',        cls: 'wi-s-done' };
  return              { label: 'In Progress', cls: 'wi-s-wip'  };
}

function _typeMeta(t) {
  return _TYPE[t] || { icon: '?', label: t, color: '#6b7280', cls: '' };
}

function _esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

export function destroyWorkItems() {
  if (_polling) { clearInterval(_polling); _polling = null; }
}

export async function renderWorkItems(container, projectName) {
  destroyWorkItems();
  _project = projectName || state.currentProject?.name || '';

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- ── Toolbar ── -->
      <div style="padding:0.65rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.75rem;flex-shrink:0;flex-wrap:wrap">
        <span style="font-size:0.88rem;font-weight:700;color:var(--text)">Work Items</span>
        <button id="wi-classify-btn" class="btn btn-ghost btn-sm" title="Classify pending mirror rows via LLM">
          ↻ Classify
        </button>
        <span style="flex:1"></span>
        <!-- Type filter chips -->
        <div id="wi-filter-chips" style="display:flex;gap:0.3rem;flex-wrap:wrap"></div>
        <span id="wi-status" style="font-size:0.72rem;color:var(--muted)"></span>
      </div>

      <!-- ── Stats bar ── -->
      <div id="wi-stats-bar" style="padding:0.55rem 1.25rem;background:var(--surface);
                border-bottom:1px solid var(--border);flex-shrink:0;
                display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap">
        <span style="color:var(--muted);font-size:0.72rem">Loading…</span>
      </div>

      <!-- ── List ── -->
      <div id="wi-list" style="flex:1;overflow-y:auto;padding:1rem 1.25rem">
        <div style="color:var(--muted);text-align:center;padding:3rem;font-size:0.82rem">
          Loading work items…
        </div>
      </div>
    </div>

    <style>
      .wi-card {
        border:1px solid var(--border);border-radius:var(--radius);
        background:var(--surface);margin-bottom:0.75rem;overflow:hidden;
      }
      .wi-card-header {
        display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;
        padding:0.55rem 0.9rem;background:var(--surface2);
        border-bottom:1px solid var(--border);
        cursor:pointer;user-select:none;
      }
      .wi-card-header:hover { background:var(--surface3) }
      .wi-card-body { padding:0.65rem 0.9rem }
      .wi-card-body.collapsed { display:none }

      .wi-type-badge {
        font-size:0.67rem;font-weight:700;padding:2px 7px;border-radius:8px;white-space:nowrap;
      }
      .wi-type-uc   { background:#cffafe;color:#0e7490 }
      .wi-type-feat { background:#dcfce7;color:#16a34a }
      .wi-type-bug  { background:#fee2e2;color:#dc2626 }
      .wi-type-task { background:#dbeafe;color:#1d4ed8 }
      .wi-type-pol  { background:#ede9fe;color:#7c3aed }
      .wi-type-req  { background:#fef3c7;color:#b45309 }

      .wi-status-badge {
        font-size:0.62rem;font-weight:700;padding:1px 6px;border-radius:6px;white-space:nowrap;
      }
      .wi-s-req  { background:#fef3c7;color:#b45309 }
      .wi-s-wip  { background:#dbeafe;color:#1d4ed8 }
      .wi-s-done { background:#dcfce7;color:#16a34a }

      .wi-md-panel {
        position:fixed;top:0;right:0;width:520px;height:100vh;z-index:900;
        background:var(--surface);border-left:1px solid var(--border);
        display:flex;flex-direction:column;box-shadow:-4px 0 24px rgba(0,0,0,.25);
      }
      .wi-md-panel-header {
        padding:0.65rem 1rem;border-bottom:1px solid var(--border);
        display:flex;align-items:center;gap:0.5rem;flex-shrink:0;background:var(--surface2);
      }
      .wi-md-textarea {
        flex:1;resize:none;border:none;outline:none;padding:1rem;
        background:var(--surface);color:var(--text);font-family:monospace;
        font-size:0.8rem;line-height:1.6;
      }
      .wi-add-form {
        padding:0.65rem 0.9rem;border-top:1px solid var(--border);
        background:var(--surface2);display:none;flex-direction:column;gap:0.4rem;
      }
      .wi-add-form.visible { display:flex }
      .wi-add-form input, .wi-add-form select, .wi-add-form textarea {
        background:var(--surface);border:1px solid var(--border);border-radius:4px;
        padding:4px 8px;color:var(--text);font-size:0.8rem;
      }
      .wi-add-form textarea { resize:vertical;min-height:50px }

      .wi-name { font-size:0.88rem;font-weight:700;color:var(--text);flex:1;min-width:120px }
      .wi-id   { font-size:0.65rem;color:var(--muted);background:var(--surface3);
                 padding:1px 6px;border-radius:6px;font-family:monospace }
      .wi-pending { color:#f59e0b;font-size:0.62rem;font-weight:700;text-transform:uppercase }

      .wi-actions { display:flex;gap:0.3rem;margin-left:auto }
      .wi-btn {
        border:none;border-radius:4px;padding:3px 9px;cursor:pointer;
        font-size:0.72rem;font-weight:700;transition:opacity .15s;
      }
      .wi-btn:disabled { opacity:.35;cursor:not-allowed }
      .wi-btn-approve { background:#16a34a;color:#fff }
      .wi-btn-reject  { background:#dc2626;color:#fff }
      .wi-btn-approve:hover:not(:disabled) { opacity:.85 }
      .wi-btn-reject:hover:not(:disabled)  { opacity:.85 }
      .wi-btn-ghost {
        background:var(--surface3);color:var(--muted);border:1px solid var(--border);
      }
      .wi-btn-ghost:hover { background:var(--surface4,#334155);color:var(--text) }

      .wi-summary {
        font-size:0.79rem;color:var(--text2);line-height:1.5;margin-bottom:0.5rem;
        padding:0.35rem 0.6rem;background:var(--surface3);border-radius:4px;
        border-left:3px solid var(--accent);
      }
      .wi-deliveries {
        font-size:0.77rem;color:var(--text2);margin-bottom:0.4rem;
        padding:0.3rem 0.6rem;background:var(--surface);border:1px solid var(--border);
        border-radius:4px;border-left:3px solid #22c55e;
      }
      .wi-scores {
        display:flex;gap:0.75rem;font-size:0.68rem;color:var(--muted);margin-bottom:0.4rem;
      }
      .wi-score-bar {
        display:inline-flex;gap:2px;align-items:center;
      }
      .wi-score-pip {
        width:8px;height:8px;border-radius:2px;background:var(--border);
      }
      .wi-score-pip.filled { background:var(--accent) }

      .wi-mrr-counts {
        font-size:0.67rem;color:var(--muted);display:flex;gap:0.6rem;flex-wrap:wrap;
      }
      .wi-mrr-chip {
        background:var(--surface3);padding:1px 6px;border-radius:6px;
      }

      .wi-uc-group { margin-bottom:1.25rem }
      .wi-uc-header {
        display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0.9rem;
        background:var(--surface2);border:1px solid var(--border);
        border-radius:var(--radius) var(--radius) 0 0;
        cursor:pointer;user-select:none;
      }
      .wi-uc-header:hover { background:var(--surface3) }
      .wi-uc-label {
        font-size:0.75rem;font-weight:800;text-transform:uppercase;
        letter-spacing:.05em;color:var(--accent);
      }
      .wi-uc-body {
        border:1px solid var(--border);border-top:none;
        border-radius:0 0 var(--radius) var(--radius);
        overflow:hidden;
      }
      .wi-uc-body.collapsed { display:none }
      .wi-uc-summary {
        padding:0.55rem 0.9rem;font-size:0.79rem;color:var(--text2);line-height:1.5;
        border-bottom:1px solid var(--border);background:var(--surface);
        border-left:3px solid var(--accent);
      }
      .wi-uc-children {
        overflow:hidden;
        padding-left:1rem;
        border-left:3px solid var(--border);
        margin-left:0.5rem;
      }
      .wi-uc-children .wi-card { margin-bottom:0.5rem }
      .wi-uc-children .wi-card:last-child { margin-bottom:0 }

      /* drag-and-drop */
      .wi-card[draggable="true"] { cursor:grab }
      .wi-card[draggable="true"]:active { cursor:grabbing }
      .wi-card.wi-dragging { opacity:.4;pointer-events:none }
      .wi-drop-zone {
        min-height:2.5rem;transition:background .15s,border .15s;
      }
      .wi-drop-zone.wi-drag-over {
        background:rgba(var(--accent-rgb,6,182,212),.08);
        outline:2px dashed var(--accent);outline-offset:-2px;
      }
      .wi-orphan-zone {
        margin-bottom:1.25rem;padding:0.65rem 0.9rem;
        border:2px dashed #f59e0b;border-radius:var(--radius);
        background:rgba(245,158,11,.05);
      }
      .wi-orphan-zone-label {
        font-size:0.72rem;font-weight:700;color:#f59e0b;margin-bottom:0.5rem;
        display:flex;align-items:center;gap:0.4rem;
      }

      /* inline rename */
      .wi-rename-input {
        background:var(--surface);border:1px solid var(--accent);border-radius:4px;
        padding:2px 6px;color:var(--text);font-size:0.88rem;font-weight:700;
        min-width:140px;max-width:300px;flex:1;outline:none;
      }
      .wi-rename-btn {
        background:none;border:none;cursor:pointer;font-size:0.75rem;
        color:var(--muted);padding:1px 3px;opacity:.6;line-height:1;
      }
      .wi-rename-btn:hover { opacity:1;color:var(--accent) }

      /* status badge — display only, ▾ button is the trigger */
      .wi-status-badge {
        font-size:0.62rem;font-weight:700;padding:1px 6px;border-radius:6px;
        white-space:nowrap;cursor:default;user-select:none;
      }

      /* UC MRR totals */
      .wi-uc-mrr {
        font-size:0.65rem;color:var(--muted);display:flex;gap:0.4rem;flex-wrap:wrap;align-items:center;
      }
      .wi-uc-mrr-chip {
        background:var(--surface3);padding:1px 5px;border-radius:5px;
      }

      .wi-filter-chip {
        font-size:0.67rem;padding:2px 8px;border-radius:10px;cursor:pointer;
        border:1px solid var(--border);background:var(--surface2);color:var(--muted);
        transition:all .15s;font-weight:600;
      }
      .wi-filter-chip.active { border-color:var(--accent);color:var(--accent);background:var(--surface3) }
      .wi-filter-chip:hover  { border-color:var(--accent);color:var(--accent) }

      .wi-stats-pill {
        font-size:0.71rem;display:flex;align-items:center;gap:0.3rem;
      }
      .wi-stats-dot { width:8px;height:8px;border-radius:50% }

      /* shared popover */
      .wi-wi-pop {
        position:fixed;z-index:900;min-width:200px;padding:0.65rem;
        background:var(--surface2);border:1px solid var(--border);
        border-radius:var(--radius);box-shadow:0 6px 24px rgba(0,0,0,.4);
      }
      .wi-wi-pop select, .wi-wi-pop input {
        width:100%;box-sizing:border-box;background:var(--surface);
        border:1px solid var(--border);border-radius:4px;
        padding:4px 8px;color:var(--text);font-size:0.8rem;
      }
      .wi-wi-pop input:focus { border-color:var(--accent);outline:none }
      .wi-wi-pop-label { font-size:0.68rem;color:var(--muted);font-weight:700;margin-bottom:0.4rem }

      /* inline edit controls */
      .wi-edit-arrow {
        background:var(--surface3);border:1px solid var(--border);border-radius:3px;
        cursor:pointer;color:var(--text2);
        font-size:0.7rem;padding:1px 5px;line-height:1.4;
        flex-shrink:0;font-weight:700;
      }
      .wi-edit-arrow:hover {
        background:var(--accent,#06b6d4);color:#fff;border-color:var(--accent,#06b6d4);
      }
      .wi-edit-link {
        background:none;border:none;cursor:pointer;font-size:0.67rem;
        color:var(--muted);padding:2px 0;text-decoration:underline;display:block;margin-top:0.25rem;
      }
      .wi-edit-link:hover { color:var(--accent) }
      .wi-summary-editor {
        width:100%;box-sizing:border-box;min-height:70px;resize:vertical;
        background:var(--surface);border:1px solid var(--accent);border-radius:4px;
        padding:6px 8px;color:var(--text);font-size:0.8rem;line-height:1.5;outline:none;
        display:block;margin-bottom:0.35rem;
      }
    </style>
  `;

  _setupEvents(container);
  await _loadAll();
}

// ── Event wiring ──────────────────────────────────────────────────────────────

function _setupEvents(container) {
  // Classify button
  container.querySelector('#wi-classify-btn').addEventListener('click', async (e) => {
    const btn = e.currentTarget;
    btn.disabled = true; btn.textContent = '⏳ Classifying…';
    try {
      const r = await api.wi.classify(_project);
      toast(
        r.classified > 0
          ? `Classified ${r.classified} items from ${r.events_in || 0} events`
          : (r.message || 'No pending events to classify'),
        r.classified > 0 ? 'success' : 'info',
      );
      await _loadAll();
    } catch (e) {
      toast(`Classify failed: ${e.message}`, 'error');
    } finally {
      btn.disabled = false; btn.textContent = '↻ Classify';
    }
  });

  // Filter chips
  container.querySelector('#wi-filter-chips').addEventListener('click', (e) => {
    const chip = e.target.closest('.wi-filter-chip');
    if (!chip) return;
    const type = chip.dataset.type;
    _filter = (_filter === type) ? '' : type;
    container.querySelectorAll('.wi-filter-chip').forEach(c => {
      c.classList.toggle('active', c.dataset.type === _filter);
    });
    _renderList();
  });

  // List-level delegation (approve/reject/expand)
  container.querySelector('#wi-list').addEventListener('click', async (e) => {
    // Approve single
    const apBtn = e.target.closest('[data-action="approve"]');
    if (apBtn) {
      e.stopPropagation();
      const id = apBtn.dataset.id;
      apBtn.disabled = true;
      try {
        const r = await api.wi.approve(_project, id);
        toast(`✓ Approved → ${r.wi_id}`, 'success');
        await _loadAll();
      } catch (err) { toast(`Approve failed: ${err.message}`, 'error'); apBtn.disabled = false; }
      return;
    }

    // Reject single
    const rejBtn = e.target.closest('[data-action="reject"]');
    if (rejBtn) {
      e.stopPropagation();
      const id = rejBtn.dataset.id;
      rejBtn.disabled = true;
      try {
        const r = await api.wi.reject(_project, id);
        toast(`✗ Rejected (${r.wi_id})`, 'info');
        await _loadAll();
      } catch (err) { toast(`Reject failed: ${err.message}`, 'error'); rejBtn.disabled = false; }
      return;
    }

    // Approve all under use_case group
    const apAllBtn = e.target.closest('[data-action="approve-all"]');
    if (apAllBtn) {
      e.stopPropagation();
      const parentId = apAllBtn.dataset.parentId;
      apAllBtn.disabled = true;
      try {
        const r = await api.wi.approveAll(_project, parentId);
        toast(`✓ Approved ${r.approved} items`, 'success');
        await _loadAll();
      } catch (err) { toast(`Approve all failed: ${err.message}`, 'error'); apAllBtn.disabled = false; }
      return;
    }

    // Edit MD
    const mdBtn = e.target.closest('[data-action="edit-md"]');
    if (mdBtn) {
      e.stopPropagation();
      const id   = mdBtn.dataset.id;
      const name = mdBtn.dataset.name;
      const item = _allItems.find(i => i.id === id);
      if (item) _openMdPanel(item);
      return;
    }

    // Add item to use_case
    const addBtn = e.target.closest('[data-action="add-item"]');
    if (addBtn) {
      e.stopPropagation();
      const ucId = addBtn.dataset.ucId;
      _toggleAddForm(ucId);
      return;
    }

    // Submit add-item form
    const submitAdd = e.target.closest('[data-action="submit-add"]');
    if (submitAdd) {
      e.stopPropagation();
      const ucId = submitAdd.dataset.ucId;
      await _submitAddForm(ucId);
      return;
    }

    // ── Edit actions MUST be checked before expand/collapse ──────────────────
    // (edit buttons live inside card/uc headers, so they'd trigger expand otherwise)
    const actionEl = e.target.closest('[data-action="rename-pop"],[data-action="status-pop"],[data-action="type-pop"],[data-action="edit-summary"]');
    if (actionEl) {
      e.stopPropagation();
      const action = actionEl.dataset.action;
      const id     = actionEl.dataset.id;
      if      (action === 'rename-pop')   _showRenamePopover(actionEl, id, actionEl.dataset.currentName, actionEl.dataset.isUc === 'true');
      else if (action === 'status-pop')   _showStatusPopover(actionEl, id, parseInt(actionEl.dataset.score || '0', 10));
      else if (action === 'type-pop')     _showTypePopover(actionEl, id, actionEl.dataset.type);
      else if (action === 'edit-summary') _startSummaryEdit(actionEl, id, actionEl.dataset.summary);
      return;
    }

    // Expand/collapse card body — only when clicking the header itself (not edit buttons)
    const header = e.target.closest('.wi-card-header');
    if (header && !e.target.closest('[data-action]') && !e.target.closest('button')) {
      const body = header.nextElementSibling;
      if (body?.classList.contains('wi-card-body')) {
        body.classList.toggle('collapsed');
        const arrow = header.querySelector('.wi-arrow');
        if (arrow) arrow.textContent = body.classList.contains('collapsed') ? '▶' : '▼';
      }
      return;
    }

    // Expand/collapse use case body
    const ucHeader = e.target.closest('.wi-uc-header');
    if (ucHeader && !e.target.closest('[data-action]') && !e.target.closest('button')) {
      const body = ucHeader.nextElementSibling;
      if (body?.classList.contains('wi-uc-body')) {
        body.classList.toggle('collapsed');
        const arrow = ucHeader.querySelector('.wi-uc-arrow');
        if (arrow) arrow.textContent = body.classList.contains('collapsed') ? '▶' : '▼';
      }
    }
  });
}

// ── MD editor panel ────────────────────────────────────────────────────────

let _mdPanel = null;

function _openMdPanel(item) {
  // Close existing
  if (_mdPanel) _mdPanel.remove();

  const meta = _typeMeta(item.wi_type);
  const panel = document.createElement('div');
  panel.className = 'wi-md-panel';
  panel.innerHTML = `
    <div class="wi-md-panel-header">
      <span>${meta.icon} ${_esc(item.name)}</span>
      ${item.wi_id ? `<span class="wi-id">${_esc(item.wi_id)}</span>` : ''}
      <span style="flex:1"></span>
      <button class="wi-btn wi-btn-ghost" id="wi-md-refresh" style="margin-right:0.25rem">↻ Refresh</button>
      <button class="wi-btn wi-btn-approve" id="wi-md-save" style="margin-right:0.25rem">Save</button>
      <button class="wi-btn wi-btn-ghost" id="wi-md-close">✕</button>
    </div>
    <textarea class="wi-md-textarea" id="wi-md-content" placeholder="Loading…"></textarea>
  `;
  document.body.appendChild(panel);
  _mdPanel = panel;

  const textarea = panel.querySelector('#wi-md-content');

  // Load content
  api.wi.md.get(_project, item.id).then(r => {
    textarea.value = r.content || '';
  }).catch(err => {
    textarea.value = `Error: ${err.message}`;
  });

  panel.querySelector('#wi-md-close').addEventListener('click', () => {
    panel.remove(); _mdPanel = null;
  });

  panel.querySelector('#wi-md-refresh').addEventListener('click', async (e) => {
    e.currentTarget.disabled = true;
    try {
      const r = await api.wi.md.refresh(_project, item.id);
      textarea.value = r.content || '';
      toast('Refreshed from DB', 'info');
    } catch (err) { toast(`Refresh failed: ${err.message}`, 'error'); }
    finally { e.currentTarget.disabled = false; }
  });

  panel.querySelector('#wi-md-save').addEventListener('click', async (e) => {
    e.currentTarget.disabled = true;
    try {
      const r = await api.wi.md.save(_project, item.id, textarea.value);
      toast(`Saved (${r.updated || 0} updated, ${r.embedded || 0} embedded)`, 'success');
    } catch (err) { toast(`Save failed: ${err.message}`, 'error'); }
    finally { e.currentTarget.disabled = false; }
  });
}

// ── Status options ────────────────────────────────────────────────────────────

const _STATUS_OPTIONS = [
  { score: 0, label: 'Not Started', cls: 'wi-s-req'  },
  { score: 2, label: 'In Progress', cls: 'wi-s-wip'  },
  { score: 5, label: 'Done',        cls: 'wi-s-done' },
];

// ── Rename popover ────────────────────────────────────────────────────────────

function _showRenamePopover(anchorEl, itemId, currentName, isUC) {
  document.querySelector('.wi-wi-pop')?.remove();

  // For UC rename: offer all existing UC names as quick picks
  const existingNames = isUC
    ? [...new Set(_allItems.filter(i => i.wi_type === 'use_case' && i.name).map(i => i.name))]
    : [];

  const pop = document.createElement('div');
  pop.className = 'wi-wi-pop';
  pop.innerHTML = `
    <div style="font-size:0.7rem;color:var(--muted);font-weight:700;margin-bottom:0.45rem">
      ${isUC ? 'Rename use case' : 'Rename item'}
    </div>
    ${existingNames.length ? `
      <select id="wi-rpop-sel"
              style="width:100%;margin-bottom:0.4rem;background:var(--surface);border:1px solid var(--border);
                     border-radius:4px;padding:4px 6px;color:var(--text);font-size:0.8rem">
        <option value="">── pick existing ──</option>
        ${existingNames.map(n => `<option value="${_esc(n)}"${n===currentName?' selected':''}>${_esc(n)}</option>`).join('')}
        <option value="__new__">+ New name…</option>
      </select>
    ` : ''}
    <input id="wi-rpop-inp" value="${_esc(currentName)}"
           placeholder="${isUC ? 'Use case name…' : 'Item name…'}"
           style="width:100%;box-sizing:border-box;background:var(--surface);border:1px solid var(--accent);
                  border-radius:4px;padding:4px 8px;color:var(--text);font-size:0.82rem;outline:none">
    <div style="display:flex;gap:0.4rem;margin-top:0.5rem">
      <button id="wi-rpop-ok" class="wi-btn wi-btn-approve" style="flex:1">Rename</button>
      <button id="wi-rpop-cancel" class="wi-btn wi-btn-ghost">✕</button>
    </div>
  `;
  _popupAt(pop, anchorEl);

  const inp = pop.querySelector('#wi-rpop-inp');
  const sel = pop.querySelector('#wi-rpop-sel');
  inp.focus(); inp.select();

  if (sel) {
    sel.addEventListener('change', () => {
      if (sel.value && sel.value !== '__new__') inp.value = sel.value;
      if (sel.value === '__new__') inp.value = '';
      inp.focus();
    });
  }

  const _close = () => pop.remove();
  const _confirm = async () => {
    const newName = inp.value.trim();
    _close();
    if (!newName || newName === currentName) return;
    try {
      await api.wi.update(_project, itemId, { name: newName });
      toast(`Renamed → ${newName}`, 'success');
      await _loadAll();
    } catch (err) { toast(`Rename failed: ${err.message}`, 'error'); }
  };

  pop.querySelector('#wi-rpop-ok').addEventListener('click', _confirm);
  pop.querySelector('#wi-rpop-cancel').addEventListener('click', _close);
  inp.addEventListener('keydown', e => {
    if (e.key === 'Enter')  { e.preventDefault(); _confirm(); }
    if (e.key === 'Escape') _close();
  });
  setTimeout(() => {
    document.addEventListener('click', e => { if (!pop.contains(e.target)) pop.remove(); }, { once: true });
  }, 150);
}

// ── Status popover ────────────────────────────────────────────────────────────

function _showStatusPopover(anchorEl, itemId, currentScore) {
  document.querySelector('.wi-wi-pop')?.remove();

  const pop = document.createElement('div');
  pop.className = 'wi-wi-pop';
  pop.style.width = '140px';
  pop.innerHTML = _STATUS_OPTIONS.map(s => `
    <button class="wi-btn ${s.score === currentScore ? 'wi-btn-approve' : 'wi-btn-ghost'}"
            data-score="${s.score}"
            style="width:100%;margin-bottom:2px;text-align:left;justify-content:flex-start">
      ${s.label}
    </button>
  `).join('');
  _popupAt(pop, anchorEl);

  pop.querySelectorAll('[data-score]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const newScore = parseInt(btn.dataset.score, 10);
      pop.remove();
      try {
        await api.wi.update(_project, itemId, { score_status: newScore });
        const opt = _STATUS_OPTIONS.find(s => s.score === newScore) || _STATUS_OPTIONS[0];
        const badge = document.querySelector(`.wi-status-badge[data-item-id="${itemId}"]`);
        if (badge) {
          badge.textContent = opt.label;
          badge.className   = `wi-status-badge ${opt.cls}`;
          badge.dataset.scoreStatus = String(newScore);
        }
        const item = _allItems.find(i => i.id === itemId);
        if (item) item.score_status = newScore;
      } catch (err) { toast(`Status update failed: ${err.message}`, 'error'); }
    });
  });
  setTimeout(() => {
    document.addEventListener('click', e => { if (!pop.contains(e.target)) pop.remove(); }, { once: true });
  }, 150);
}

// ── Type popover ─────────────────────────────────────────────────────────────

const _ITEM_TYPES = ['feature', 'bug', 'task', 'policy', 'requirement'];

function _showTypePopover(anchorEl, itemId, currentType) {
  document.querySelector('.wi-wi-pop')?.remove();
  const pop = document.createElement('div');
  pop.className = 'wi-wi-pop';
  pop.style.width = '165px';
  pop.innerHTML = `<div class="wi-wi-pop-label">Change type</div>` +
    _ITEM_TYPES.map(t => {
      const m = _typeMeta(t);
      return `<button class="wi-btn ${t === currentType ? 'wi-btn-approve' : 'wi-btn-ghost'}"
                      data-type="${t}"
                      style="width:100%;margin-bottom:2px;text-align:left">
                ${m.icon} ${m.label}
              </button>`;
    }).join('');
  _popupAt(pop, anchorEl);
  pop.querySelectorAll('[data-type]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const newType = btn.dataset.type;
      pop.remove();
      try {
        await api.wi.update(_project, itemId, { wi_type: newType });
        toast(`Type → ${newType}`, 'success');
        await _loadAll();
      } catch (err) { toast(`Type update failed: ${err.message}`, 'error'); }
    });
  });
  setTimeout(() => {
    document.addEventListener('click', e => { if (!pop.contains(e.target)) pop.remove(); }, { once: true });
  }, 150);
}

// ── Inline summary edit ────────────────────────────────────────────────────────

function _startSummaryEdit(triggerEl, itemId, currentSummary) {
  // Find the .wi-summary-wrap that contains this trigger
  const wrap = triggerEl.closest('.wi-summary-wrap');
  if (!wrap) return;

  const prev = wrap.innerHTML;
  wrap.innerHTML = `
    <textarea class="wi-summary-editor">${_esc(currentSummary)}</textarea>
    <div style="display:flex;gap:0.4rem">
      <button class="wi-btn wi-btn-approve" id="wi-sum-save">Save</button>
      <button class="wi-btn wi-btn-ghost"   id="wi-sum-cancel">Cancel</button>
    </div>
  `;
  const ta = wrap.querySelector('.wi-summary-editor');
  ta.focus();
  // Move cursor to end
  ta.selectionStart = ta.selectionEnd = ta.value.length;

  wrap.querySelector('#wi-sum-save').addEventListener('click', async () => {
    const newSummary = ta.value.trim();
    try {
      await api.wi.update(_project, itemId, { summary: newSummary });
      toast('Summary saved', 'success');
    } catch (err) { toast(`Save failed: ${err.message}`, 'error'); }
    await _loadAll();
  });
  wrap.querySelector('#wi-sum-cancel').addEventListener('click', () => {
    wrap.innerHTML = prev;
  });
}

// ── Popover helper ────────────────────────────────────────────────────────────

function _popupAt(el, anchor) {
  el.style.cssText += ';position:fixed;z-index:900;min-width:220px;padding:0.65rem;' +
    'background:var(--surface2);border:1px solid var(--border);' +
    'border-radius:var(--radius);box-shadow:0 6px 24px rgba(0,0,0,.4)';
  const rect = anchor.getBoundingClientRect();
  el.style.top  = (rect.bottom + 6) + 'px';
  el.style.left = Math.min(rect.left, window.innerWidth - 260) + 'px';
  document.body.appendChild(el);
}

// ── Drag-and-drop ─────────────────────────────────────────────────────────────

function _attachDragListeners() {
  const listEl = document.getElementById('wi-list');
  if (!listEl) return;

  listEl.querySelectorAll('.wi-card[draggable="true"]').forEach(card => {
    card.addEventListener('dragstart', (e) => {
      _dragItemId = card.dataset.itemId;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', _dragItemId);
      // Delay to let the drag image render before hiding
      setTimeout(() => card.classList.add('wi-dragging'), 0);
    });
    card.addEventListener('dragend', () => {
      card.classList.remove('wi-dragging');
      listEl.querySelectorAll('.wi-drag-over').forEach(el => el.classList.remove('wi-drag-over'));
      _dragItemId = null;
    });
  });

  listEl.querySelectorAll('.wi-drop-zone').forEach(zone => {
    zone.addEventListener('dragover', (e) => {
      if (!_dragItemId) return;
      e.preventDefault();
      e.stopPropagation();
      e.dataTransfer.dropEffect = 'move';
      listEl.querySelectorAll('.wi-drag-over').forEach(el => { if (el !== zone) el.classList.remove('wi-drag-over'); });
      zone.classList.add('wi-drag-over');
    });
    zone.addEventListener('dragleave', (e) => {
      if (!zone.contains(e.relatedTarget)) zone.classList.remove('wi-drag-over');
    });
    zone.addEventListener('drop', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      zone.classList.remove('wi-drag-over');
      const targetUcId = zone.dataset.ucId;
      const itemId     = _dragItemId;
      _dragItemId = null;
      if (!targetUcId || !itemId || targetUcId === '__none__') return;
      try {
        await api.wi.update(_project, itemId, { wi_parent_id: targetUcId });
        toast('Moved to use case', 'success');
        await _loadAll();
      } catch (err) { toast(`Move failed: ${err.message}`, 'error'); }
    });
  });
}

// ── Add-item form ──────────────────────────────────────────────────────────

function _toggleAddForm(ucId) {
  const form = document.getElementById(`wi-add-form-${ucId}`);
  if (!form) return;
  form.classList.toggle('visible');
}

async function _submitAddForm(ucId) {
  const nameEl    = document.getElementById(`wi-add-name-${ucId}`);
  const typeEl    = document.getElementById(`wi-add-type-${ucId}`);
  const summaryEl = document.getElementById(`wi-add-summary-${ucId}`);
  if (!nameEl || !typeEl) return;

  const name    = nameEl.value.trim();
  const wi_type = typeEl.value;
  const summary = summaryEl?.value.trim() || '';
  if (!name) { toast('Name is required', 'error'); return; }

  const btn = document.querySelector(`[data-action="submit-add"][data-uc-id="${ucId}"]`);
  if (btn) btn.disabled = true;
  try {
    await api.wi.create(_project, { name, wi_type, summary, wi_parent_id: ucId });
    toast(`Added: ${name}`, 'success');
    await _loadAll();
  } catch (err) {
    toast(`Add failed: ${err.message}`, 'error');
    if (btn) btn.disabled = false;
  }
}

// ── Data load ─────────────────────────────────────────────────────────────────

async function _loadAll() {
  if (!_project) return;
  _setStatus('Loading…');
  try {
    const [statsData, listData] = await Promise.all([
      api.wi.stats(_project),
      api.wi.list(_project),
    ]);
    _stats    = statsData || {};
    _allItems = (listData.items || []);
    _renderStats();
    _renderFilterChips();
    _renderList();
    _setStatus('');
  } catch (e) {
    _setStatus(`Error: ${e.message}`);
    document.getElementById('wi-list').innerHTML =
      `<div style="color:var(--muted);text-align:center;padding:2rem">${_esc(e.message)}</div>`;
  }
}

function _setStatus(msg) {
  const el = document.getElementById('wi-status');
  if (el) el.textContent = msg;
}

// ── Stats bar ─────────────────────────────────────────────────────────────────

function _renderStats() {
  const el = document.getElementById('wi-stats-bar');
  if (!el) return;
  const s = _stats;
  const pills = [
    { label: 'Pending',      val: s.pending      || 0, color: '#f59e0b' },
    { label: 'Approved',     val: s.approved     || 0, color: '#22c55e' },
    { label: 'Rejected',     val: s.rejected     || 0, color: '#6b7280' },
    { label: 'Bugs',         val: s.bugs         || 0, color: '#ef4444' },
    { label: 'Features',     val: s.features     || 0, color: '#22c55e' },
    { label: 'Tasks',        val: s.tasks        || 0, color: '#3b82f6' },
    { label: 'Policies',     val: s.policies     || 0, color: '#8b5cf6' },
    { label: 'Requirements', val: s.requirements || 0, color: '#f59e0b' },
  ];
  el.innerHTML = pills.map(p => `
    <div class="wi-stats-pill">
      <div class="wi-stats-dot" style="background:${p.color}"></div>
      <span style="color:var(--muted)">${p.label}:</span>
      <strong style="color:var(--text)">${p.val}</strong>
    </div>
  `).join('');
}

// ── Filter chips ──────────────────────────────────────────────────────────────

function _renderFilterChips() {
  const el = document.getElementById('wi-filter-chips');
  if (!el) return;
  const types = ['bug', 'feature', 'task', 'policy', 'requirement', 'use_case'];
  el.innerHTML = types.map(t => {
    const m = _typeMeta(t);
    return `<button class="wi-filter-chip${_filter === t ? ' active' : ''}" data-type="${t}"
               title="Filter by ${m.label}">
              ${m.icon} ${m.label}
            </button>`;
  }).join('');
}

// ── Main list render ──────────────────────────────────────────────────────────

function _renderList() {
  const el = document.getElementById('wi-list');
  if (!el) return;

  let items = _allItems;
  if (_filter) items = items.filter(i => i.wi_type === _filter);

  if (!items.length) {
    el.innerHTML = `<div style="color:var(--muted);text-align:center;padding:3rem;font-size:0.82rem">
      No work items${_filter ? ` of type "${_filter}"` : ''}.
      ${!_allItems.length ? '<br>Run <strong>Classify</strong> to process pending events.' : ''}
    </div>`;
    return;
  }

  // Separate use_case groups (level=3) from standalone items
  const useCases  = items.filter(i => i.wi_type === 'use_case' || i.item_level === 3);
  const ucIds     = new Set(useCases.map(u => u.id));
  const children  = items.filter(i => i.wi_parent_id && ucIds.has(i.wi_parent_id));
  const childIds  = new Set(children.map(c => c.id));
  const orphans   = items.filter(i => !ucIds.has(i.id) && !childIds.has(i.id));

  let html = '';

  // Render use_case groups with their children
  for (const uc of useCases) {
    const ucChildren = children.filter(c => c.wi_parent_id === uc.id);
    const ucIsPending = !uc.wi_id || uc.wi_id.startsWith('AI');
    const pendingChildren = ucChildren.filter(c => !c.wi_id || c.wi_id.startsWith('AI'));

    // Compute UC-level MRR totals (sum across all children)
    let totalPrompts = 0, totalCommits = 0, totalMessages = 0, totalItems = 0;
    for (const c of ucChildren) {
      const m = c.mrr_ids || {};
      totalPrompts  += (m.prompts?.length  || 0);
      totalCommits  += (m.commits?.length  || 0);
      totalMessages += (m.messages?.length || 0);
      totalItems    += (m.items?.length    || 0);
    }
    const ucMrrChips = [
      totalPrompts  ? `<span class="wi-uc-mrr-chip">Prompts: ${totalPrompts}</span>`   : '',
      totalCommits  ? `<span class="wi-uc-mrr-chip">Commits: ${totalCommits}</span>`   : '',
      totalMessages ? `<span class="wi-uc-mrr-chip">Messages: ${totalMessages}</span>` : '',
      totalItems    ? `<span class="wi-uc-mrr-chip">Items: ${totalItems}</span>`        : '',
    ].filter(Boolean).join('');

    html += `
      <div class="wi-uc-group">
        <div class="wi-uc-header">
          <span class="wi-uc-arrow" style="font-size:0.65rem;color:var(--muted)">▼</span>
          <span class="wi-uc-label">◻ USE CASE</span>
          <span class="wi-name">${_esc(uc.name || uc.id)}</span>
          <button class="wi-edit-arrow" data-action="rename-pop"
                  data-id="${uc.id}" data-current-name="${_esc(uc.name || '')}" data-is-uc="true"
                  title="Rename use case">▾</button>
          <span style="font-size:0.7rem;color:var(--muted)">${ucChildren.length} item${ucChildren.length !== 1 ? 's' : ''}</span>
          ${ucMrrChips ? `<div class="wi-uc-mrr">${ucMrrChips}</div>` : ''}
          ${ucIsPending
            ? `<span class="wi-pending">${_esc(uc.wi_id || 'pending')}</span>`
            : `<span class="wi-id">${_esc(uc.wi_id)}</span>`
          }
          ${ucIsPending ? `
            <button class="wi-btn wi-btn-approve" data-action="approve" data-id="${uc.id}"
                    title="Approve use case and all its items (${pendingChildren.length})">
              ✓ Approve + ${pendingChildren.length} item${pendingChildren.length !== 1 ? 's' : ''}
            </button>
            <button class="wi-btn wi-btn-reject"  data-action="reject"  data-id="${uc.id}" title="Reject use case">✗</button>
          ` : `
            <button class="wi-btn wi-btn-ghost" data-action="edit-md" data-id="${uc.id}" data-name="${_esc(uc.name)}" title="Edit MD file">✎ MD</button>
            ${pendingChildren.length > 0 ? `
              <button class="wi-btn wi-btn-approve" data-action="approve-all" data-parent-id="${uc.id}"
                      title="Approve remaining ${pendingChildren.length} items">
                ✓ ${pendingChildren.length} pending
              </button>
            ` : ''}
          `}
        </div>
        <div class="wi-uc-body">
          <div class="wi-uc-summary wi-summary-wrap" style="padding:0.55rem 0.9rem;border-bottom:1px solid var(--border)">
            ${uc.summary
              ? `<div style="font-size:0.79rem;color:var(--text2);line-height:1.5;border-left:3px solid var(--accent);padding-left:0.5rem">${_esc(uc.summary)}</div>`
              : `<span style="color:var(--muted);font-style:italic;font-size:0.77rem">No summary yet</span>`
            }
            <button class="wi-edit-link" data-action="edit-summary"
                    data-id="${uc.id}" data-summary="${_esc(uc.summary || '')}">✎ Edit summary</button>
          </div>
          <div class="wi-uc-children wi-drop-zone" data-uc-id="${uc.id}">
            ${ucChildren.length ? ucChildren.map(c => _renderItemCard(c)).join('') : `
              <div style="padding:0.75rem 0.9rem;color:var(--muted);font-size:0.78rem;font-style:italic">
                Drop items here or use + Add Item
              </div>
            `}
          </div>
          <!-- Add Item form -->
          <div class="wi-add-form" id="wi-add-form-${uc.id}">
            <div style="display:flex;gap:0.5rem;align-items:center">
              <input  id="wi-add-name-${uc.id}"    placeholder="Item name" style="flex:1">
              <select id="wi-add-type-${uc.id}">
                <option value="feature">⚡ Feature</option>
                <option value="bug">🐛 Bug</option>
                <option value="task">✓ Task</option>
                <option value="policy">⚑ Policy</option>
                <option value="requirement" selected>◎ Requirement</option>
              </select>
            </div>
            <textarea id="wi-add-summary-${uc.id}" placeholder="Summary (optional)"></textarea>
            <div style="display:flex;gap:0.5rem">
              <button class="wi-btn wi-btn-approve" data-action="submit-add" data-uc-id="${uc.id}">Add</button>
              <button class="wi-btn wi-btn-ghost" onclick="document.getElementById('wi-add-form-${uc.id}').classList.remove('visible')">Cancel</button>
            </div>
          </div>
          <button class="wi-btn wi-btn-ghost" style="margin:0.4rem 0.9rem;font-size:0.72rem"
                  data-action="add-item" data-uc-id="${uc.id}">+ Add Item</button>
        </div>
      </div>
    `;
  }

  // Render orphaned items — shown in a warning zone; must be dragged to a UC
  if (orphans.length) {
    html += `
      <div class="wi-orphan-zone">
        <div class="wi-orphan-zone-label">
          ⚠ ${orphans.length} unlinked item${orphans.length !== 1 ? 's' : ''} — drag to a use case above
        </div>
        <div class="wi-drop-zone" data-uc-id="__none__" style="min-height:0">
          ${orphans.map(i => _renderItemCard(i)).join('')}
        </div>
      </div>
    `;
  }

  el.innerHTML = html || `<div style="color:var(--muted);text-align:center;padding:3rem">No items match the current filter.</div>`;
  _attachDragListeners();
}

function _renderItemCard(item) {
  const meta = _typeMeta(item.wi_type);
  const isPending = !item.wi_id || item.wi_id.startsWith('AI');
  const mrr = item.mrr_ids || {};
  const mrrChips = [
    mrr.prompts?.length  ? `<span class="wi-mrr-chip">Prompts: ${mrr.prompts.length}</span>`   : '',
    mrr.commits?.length  ? `<span class="wi-mrr-chip">Commits: ${mrr.commits.length}</span>`   : '',
    mrr.messages?.length ? `<span class="wi-mrr-chip">Messages: ${mrr.messages.length}</span>` : '',
    mrr.items?.length    ? `<span class="wi-mrr-chip">Items: ${mrr.items.length}</span>`        : '',
  ].filter(Boolean).join('');

  const st = _itemStatus(item);
  return `
    <div class="wi-card" draggable="true" data-item-id="${item.id}">
      <div class="wi-card-header" title="Click header to expand">

        <!-- Type badge + ▾ button to change type -->
        <span class="wi-type-badge ${meta.cls}">${meta.icon} ${meta.label}</span>
        <button class="wi-edit-arrow" data-action="type-pop"
                data-id="${item.id}" data-type="${item.wi_type}"
                title="Change type">▾</button>

        <!-- Name + ▾ to rename -->
        <span class="wi-name">${_esc(item.name || '(unnamed)')}</span>
        <button class="wi-edit-arrow" data-action="rename-pop"
                data-id="${item.id}" data-current-name="${_esc(item.name || '')}" data-is-uc="false"
                title="Rename item">▾</button>

        <!-- Status badge + ▾ button to change status -->
        <span class="wi-status-badge ${st.cls}">${st.label}</span>
        <button class="wi-edit-arrow" data-action="status-pop"
                data-id="${item.id}" data-score="${item.score_status || 0}"
                title="Change status">▾</button>

        <!-- ID -->
        ${isPending
          ? `<span class="wi-pending">${_esc(item.wi_id || 'pending')}</span>`
          : `<span class="wi-id">${_esc(item.wi_id)}</span>`
        }

        <div class="wi-actions">
          <span class="wi-arrow" style="font-size:0.65rem;color:var(--muted)">▼</span>
          ${isPending ? `<button class="wi-btn wi-btn-reject" data-action="reject" data-id="${item.id}" title="Reject">✗</button>` : ''}
        </div>
      </div>

      <div class="wi-card-body collapsed">
        <!-- Summary with inline edit -->
        <div class="wi-summary-wrap">
          ${item.summary
            ? `<div class="wi-summary">${_esc(item.summary)}</div>`
            : `<span style="color:var(--muted);font-style:italic;font-size:0.77rem">No summary yet</span>`
          }
          <button class="wi-edit-link" data-action="edit-summary"
                  data-id="${item.id}" data-summary="${_esc(item.summary || '')}">✎ Edit summary</button>
        </div>
        ${item.deliveries ? `<div class="wi-deliveries" style="margin-top:0.4rem">✓ ${_esc(item.deliveries)}</div>` : ''}
        ${mrrChips ? `<div class="wi-mrr-counts" style="margin-top:0.4rem">${mrrChips}</div>` : ''}
        ${item.wi_parent_wi_id ? `<div style="font-size:0.65rem;color:var(--muted);margin-top:0.3rem">Parent: <code>${_esc(item.wi_parent_wi_id)}</code></div>` : ''}
      </div>
    </div>
  `;
}

function _scorePips(score, color) {
  const n = Math.min(5, Math.max(0, score || 0));
  return `<span class="wi-score-bar">` +
    Array.from({length:5}, (_,i) =>
      `<span class="wi-score-pip${i < n ? ' filled' : ''}" style="${i < n ? `background:${color}` : ''}"></span>`
    ).join('') +
    `</span> <span style="font-size:0.65rem;color:var(--muted)">${n}/5</span>`;
}
