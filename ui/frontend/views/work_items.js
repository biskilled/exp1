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

let _project        = '';
let _polling        = null;
let _stats          = {};
let _mrrCounts      = {};    // pending mrr event counts from /classify-status
let _allItems       = [];    // all loaded items
let _filter         = '';    // wi_type filter
let _dragItemId     = null;  // item id being dragged
let _insertBeforeId = null;  // insert-before card id during within-UC reorder
let _dragOverItemId = null;  // item card being hovered over during drag (for link/merge)
let _classifyPoller = null;  // interval polling after background classify
let _tab            = 'backlog';  // 'backlog' | 'use_cases'
let _ucItems        = [];         // loaded by _loadUseCases()
let _ucHideDone     = new Set();  // UC IDs where completed children are hidden
let _ucCacheProject = '';         // project name when cache was populated
let _ucCacheData    = null;       // cached _ucItems (skip network on re-entry)
let _lastUndo       = null;       // { label, undoFn, reloadFn } — set by _setUndoAction

// ── UC pipeline run state ─────────────────────────────────────────────────────
let _ucPipeNamesUC   = null;  // cached pipeline names for use_case mode
let _ucPipeNamesItem = null;  // cached pipeline names for item mode
let _ucPollTimer  = null;   // polling interval for active run
let _ucRunCtx     = null;   // { mode, ucId, itemId, panelId }
const _UC_DROP_ID = 'uc-pipe-body-drop';  // body-level pipeline dropdown (avoids overflow:hidden clipping)

// ── Type config ──────────────────────────────────────────────────────────────

const _TYPE = {
  use_case:    { icon: '◻',  label: 'Use Case',    color: '#06b6d4', cls: 'wi-type-uc'  },
  feature:     { icon: '⚡', label: 'Feature',     color: '#22c55e', cls: 'wi-type-feat' },
  bug:         { icon: '🐛', label: 'Bug',         color: '#ef4444', cls: 'wi-type-bug'  },
  task:        { icon: '✓',  label: 'Task',        color: '#3b82f6', cls: 'wi-type-task' },
  policy:      { icon: '⚑', label: 'Policy',      color: '#8b5cf6', cls: 'wi-type-pol'  },
  requirement: { icon: '◎',  label: 'Requirement', color: '#f59e0b', cls: 'wi-type-req'  },
};

// After m079 user_status is TEXT ('open'|'pending'|'in-progress'|'review'|'blocked'|'done').
// score_status is still a legacy numeric 0-9 field. Use _isDone() / _statusNum() everywhere.
function _isDone(item) {
  if (item.user_status != null) return item.user_status === 'done';
  return (item.score_status ?? 0) >= 5;
}

// Map text user_status → numeric bucket so existing sort/compare logic keeps working.
function _statusNum(item) {
  const us = item.user_status;
  if (us === 'done')        return 9;
  if (us === 'review')      return 4;
  if (us === 'in-progress') return 3;
  if (us === 'blocked')     return 3;
  if (us === 'pending')     return 2;
  if (us === 'open')        return 1;
  if (us != null)           return 1;   // unknown text → treat as open
  return item.score_status ?? 0;        // numeric fallback
}

function _itemStatus(item) {
  if (_isDone(item))      return { label: 'Done',        cls: 'wi-s-done' };
  const n = _statusNum(item);
  if (n === 0)            return { label: 'Not Started', cls: 'wi-s-req'  };
  if (n === 2)            return { label: 'Pending',     cls: 'wi-s-req'  };
  if (n >= 3 && n < 9)   return { label: item.user_status === 'review' ? 'Review' : 'In Progress', cls: 'wi-s-wip' };
  return                         { label: 'Open',        cls: 'wi-s-req'  };
}

function _typeMeta(t) {
  return _TYPE[t] || { icon: '?', label: t, color: '#6b7280', cls: '' };
}

function _esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Lifecycle ─────────────────────────────────────────────────────────────────

export function destroyWorkItems() {
  if (_polling)        { clearInterval(_polling);        _polling        = null; }
  if (_classifyPoller) { clearInterval(_classifyPoller); _classifyPoller = null; }
}

export async function renderWorkItems(container, projectName) {
  destroyWorkItems();
  _project = projectName || state.currentProject?.name || '';
  _tab     = 'backlog';
  _ucItems = [];

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- ── Toolbar ── -->
      <div style="padding:0.65rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.75rem;flex-shrink:0;flex-wrap:wrap">
        <div id="wi-classify-row" style="display:flex;align-items:center;gap:0.5rem">
          <button id="wi-classify-btn" class="btn btn-ghost btn-sm" title="Classify pending mirror rows via LLM">
            ↻ Classify
          </button>
          <label style="display:flex;align-items:center;gap:0.3rem;font-size:0.75rem;color:var(--muted)" title="Max use cases to generate (8 = default)">
            Max UCs:
            <input id="wi-max-uc" type="number" min="1" max="50" value="8"
                   style="width:52px;padding:2px 5px;border:1px solid var(--border);border-radius:4px;
                          background:var(--surface);color:var(--text);font-size:0.75rem;text-align:center"
                   title="Max use cases for classification (default: 8)">
          </label>
        </div>
        <div id="wi-filter-chips" style="display:flex;gap:0.3rem;flex-wrap:wrap"></div>
        <span id="wi-status" style="font-size:0.72rem;color:var(--muted)"></span>
        <span style="flex:1"></span>
        <span id="wi-hook-badge" style="display:none;font-size:0.72rem;padding:0.2rem 0.55rem;
              border-radius:10px;background:#7c3aed22;color:#c084fc;border:1px solid #7c3aed44;
              cursor:default" title="No Claude Code prompts received recently — hook may be offline"></span>
        <button id="wi-undo-btn" class="btn btn-ghost btn-sm" disabled
                style="opacity:0.4" title="Nothing to undo">↩ Undo</button>
        <button id="wi-refresh-btn" class="btn btn-ghost btn-sm" title="Reload work items">⟳ Refresh</button>
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

    ${_sharedStyles()}
  `;

  _setupEvents(container);
  _updateUndoBtn();
  await _loadAll();
  _checkHookHealth();
}

// ── Shared CSS (injected by both Work Items and Use Cases views) ───────────────
function _sharedStyles() { return `<style>
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

      /* file hotspot badge */
      .wi-hotspot-badge {
        font-size:0.6rem;font-weight:700;padding:1px 5px;border-radius:6px;
        background:#fde68a;color:#92400e;white-space:nowrap;cursor:default;
      }

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

      /* done card — subtle green tint, no strikethrough */
      .wi-card-done { border-left:3px solid #22c55e !important }
      .wi-name-done { color:var(--text2) }

      /* priority rank badge */
      .wi-rank-badge {
        font-size:0.6rem;font-weight:800;color:var(--muted);font-family:monospace;
        background:var(--surface3);padding:1px 5px;border-radius:4px;
        min-width:22px;text-align:center;flex-shrink:0;
      }
      .wi-rank-done { color:#16a34a;background:#dcfce7 }

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
      /* insert-position indicator when reordering within a UC */
      .wi-card.wi-insert-above {
        border-top:2px solid var(--accent) !important;
      }
      /* item-as-parent drop target (drag onto card to set parent) */
      .wi-card.wi-parent-target {
        outline:2px solid #f59e0b;outline-offset:-2px;
        background:rgba(245,158,11,.07);
        cursor:crosshair !important;
      }
      /* item-over-item target: shows link/merge choice popover */
      .wi-card.wi-item-target {
        outline:2px solid var(--accent);outline-offset:-2px;
        background:rgba(6,182,212,.07);
        cursor:copy !important;
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

      /* Tab buttons — pill group on the right */
      .wi-tab-btn {
        padding:0.3rem 0.85rem;font-size:0.8rem;font-weight:600;
        border:none;background:var(--surface2);color:var(--muted);cursor:pointer;
        transition:background 0.15s,color 0.15s;
      }
      .wi-tab-btn.active { background:var(--accent,#06b6d4);color:#fff; }
      .wi-tab-btn:hover:not(.active) { background:var(--surface3);color:var(--text); }

      /* Use Cases tab — UC card */
      .wi-uc-card { margin-bottom:1.25rem;border:1px solid var(--border);border-radius:var(--radius);overflow:hidden; }
      .wi-uc-card-header {
        display:flex;align-items:center;gap:0.5rem;padding:0.55rem 0.9rem;
        background:var(--surface2);cursor:pointer;user-select:none;flex-wrap:wrap;
      }
      .wi-uc-card-header:hover { background:var(--surface3) }
      .wi-uc-card-body { border-top:1px solid var(--border) }
      .wi-uc-card-body.collapsed { display:none }
      .wi-uc-dates {
        padding:0.3rem 0.9rem;font-size:0.67rem;color:var(--muted);
        background:var(--surface);border-bottom:1px solid var(--border);
        display:flex;gap:1rem;flex-wrap:wrap;align-items:center;
      }
      .wi-uc-event-chips { display:flex;gap:0.4rem;flex-wrap:wrap;align-items:center }
      .wi-uc-event-chip {
        background:var(--surface3);padding:1px 6px;border-radius:6px;
        font-size:0.65rem;color:var(--muted);
      }
    </style>`; }

async function _checkHookHealth() {
  if (!_project) return;
  try {
    const h = await api.wi.hookHealth(_project);
    const badge = document.getElementById('wi-hook-badge');
    if (!badge) return;
    if (h.warning === 'hook_stale') {
      const hrs = h.hours_since != null ? `${h.hours_since}h ago` : 'never';
      badge.textContent = `⚠ Hook offline (last prompt: ${hrs})`;
      badge.style.display = '';
      badge.title = 'No Claude Code prompts received recently. Check that the UserPromptSubmit hook is installed and the backend is running on localhost:8000.';
    } else if (h.warning === 'no_prompts_ever') {
      badge.textContent = '⚠ Hook: no prompts received yet';
      badge.style.display = '';
    } else {
      badge.style.display = 'none';
    }
  } catch (_) {
    // silently ignore — badge stays hidden
  }
}

// ── Event wiring ──────────────────────────────────────────────────────────────

function _setupEvents(container) {
  // Refresh button
  container.querySelector('#wi-refresh-btn')?.addEventListener('click', async () => {
    await _reloadCurrent();
    toast('Refreshed', 'info');
  });

  // Undo button
  container.querySelector('#wi-undo-btn')?.addEventListener('click', async () => {
    if (!_lastUndo) return;
    const { undoFn, reloadFn } = _lastUndo;
    _clearUndo();
    try {
      const r = await undoFn();
      if (r && r.error) { toast(`Undo failed: ${r.error}`, 'error'); return; }
      toast('Action undone', 'success');
      await reloadFn();
    } catch (err) { toast(`Undo failed: ${err.message}`, 'error'); }
  });

  // Classify button (Work Items view only)
  container.querySelector('#wi-classify-btn')?.addEventListener('click', async (e) => {
    const btn = e.currentTarget;
    if (btn.disabled) return;
    const maxUc = parseInt(container.querySelector('#wi-max-uc')?.value || '8', 10);
    btn.disabled = true; btn.textContent = '⏳ Classifying…';

    // Stop any previous poller
    if (_classifyPoller) { clearInterval(_classifyPoller); _classifyPoller = null; }

    try {
      // Always run as background — classify takes several minutes (N groups × ~35s each)
      await api.wi.classify(_project, maxUc, /* bg= */ true);
      toast(`Classification started (max ${maxUc} use cases) — auto-refreshing when done…`, 'info');
      _startClassifyPoller(btn);
    } catch (err) {
      toast(`Classify failed: ${err.message}`, 'error');
      btn.disabled = false; btn.textContent = '↻ Classify';
    }
  });

  // Filter chips (Work Items view only)
  container.querySelector('#wi-filter-chips')?.addEventListener('click', (e) => {
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
        await _reloadCurrent();
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
        await _reloadCurrent();
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
        await _reloadCurrent();
      } catch (err) { toast(`Approve all failed: ${err.message}`, 'error'); apAllBtn.disabled = false; }
      return;
    }

    // Edit MD
    const mdBtn = e.target.closest('[data-action="edit-md"]');
    if (mdBtn) {
      e.stopPropagation();
      const id   = mdBtn.dataset.id;
      const item = _allItems.find(i => i.id === id)
                || _ucItems.find(i => i.id === id);
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

    // Copy item
    const copyBtn = e.target.closest('[data-action="copy-item"]');
    if (copyBtn) {
      e.stopPropagation();
      const id   = copyBtn.dataset.id;
      const item = _findInUcItems(id) || _allItems.find(i => i.id === id);
      if (!item) return;
      const lines = [
        `## ${item.name}`,
        `Type: ${item.wi_type}  |  ID: ${item.wi_id || 'pending'}`,
      ];
      if (item.summary)   lines.push(`\n### Summary\n${item.summary}`);
      if (item.deliveries) lines.push(`\n### Deliveries\n${item.deliveries}`);
      const text = lines.join('\n');
      try {
        await navigator.clipboard.writeText(text);
        toast('Copied to clipboard', 'success');
      } catch (_) {
        // Fallback for environments without clipboard API
        const ta = Object.assign(document.createElement('textarea'),
          { value: text, style: 'position:fixed;opacity:0' });
        document.body.appendChild(ta); ta.select();
        document.execCommand('copy'); ta.remove();
        toast('Copied to clipboard', 'success');
      }
      return;
    }

    // AI Summarise — auto-apply, save old summary to MD log
    const sumBtn = e.target.closest('[data-action="summarise"]');
    if (sumBtn) {
      e.stopPropagation();
      sumBtn.disabled = true; sumBtn.textContent = '⏳…';
      const ucId = sumBtn.dataset.ucId;
      try {
        const uc = _ucItems.find(u => u.id === ucId);
        const result = await api.wi.summarise(_project, ucId);
        // Save old summary to MD log (best-effort, don't block apply)
        if (uc?.summary) {
          _appendSummaryToMdLog(ucId, uc.summary).catch(() => {});
        }
        // Auto-apply the generated version
        await api.wi.versions.apply(_project, ucId, result.version_id);
        toast(`Summary updated (${result.in_progress_count} open, ${result.completed_count} done)`, 'success');
        await _loadUseCases();
      } catch (err) { toast(`Summarise failed: ${err.message}`, 'error'); }
      finally { sumBtn.disabled = false; sumBtn.textContent = '⟳ Summarise'; }
      return;
    }

    // Toggle done/completed items visibility per UC
    const toggleDone = e.target.closest('[data-action="toggle-done"]');
    if (toggleDone) {
      e.stopPropagation();
      const ucId = toggleDone.dataset.ucId;
      if (_ucHideDone.has(ucId)) _ucHideDone.delete(ucId);
      else _ucHideDone.add(ucId);
      _renderUseCases();
      return;
    }

    // Complete use case
    const completeBtn = e.target.closest('[data-action="complete-uc"]');
    if (completeBtn) {
      e.stopPropagation();
      const ucId = completeBtn.dataset.id;
      const uc   = _ucItems.find(u => u.id === ucId);
      const name = uc?.name || 'this use case';
      if (!confirm(`Mark "${name}" as completed?\n\nAll items must be done. The use case will move to the Completed tab.`)) return;
      completeBtn.disabled = true;
      try {
        const r = await api.wi.complete(_project, ucId);
        if (r.error) {
          const detail = r.incomplete?.length
            ? `\n\nStill open:\n• ${r.incomplete.slice(0, 5).join('\n• ')}`
            : '';
          toast(`Cannot complete: ${r.error}${detail}`, 'error');
          completeBtn.disabled = false;
          return;
        }
        toast(`✓ "${name}" completed and moved to Completed tab`, 'success');
        await _loadUseCases();
      } catch (err) {
        toast(`Failed: ${err.message}`, 'error');
        completeBtn.disabled = false;
      }
      return;
    }

    // Re-parent item
    const parentBtn = e.target.closest('[data-action="parent-pop"]');
    if (parentBtn) {
      e.stopPropagation();
      _showParentPopover(parentBtn, parentBtn.dataset.id, parentBtn.dataset.ucId);
      return;
    }

    // Due date popover
    const duePop = e.target.closest('[data-action="due-pop"]');
    if (duePop) {
      e.stopPropagation();
      const card   = duePop.closest('[data-item-id]');
      const itemId = card?.dataset.itemId || duePop.dataset.itemId;
      const item   = _findInUcItems(itemId)
                  || _ucItems.find(u => u.id === itemId)
                  || _allItems.find(i => i.id === itemId);
      if (item) _showDueDatePopover(duePop, item);
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

// ── Reload helpers ────────────────────────────────────────────────────────────

async function _reloadCurrent() {
  if (_tab === 'use_cases') await _loadUseCases();
  else await _loadAll();
}

// ── Classify poller ───────────────────────────────────────────────────────────
// Polls /classify-status every 4 s (server-authoritative running flag).
// Done when running=false AND we have already seen it running at least once.

function _startClassifyPoller(btn) {
  let seenRunning = false;
  const startMs   = Date.now();
  const MAX_MS    = 25 * 60 * 1000; // 25-minute safety cap

  async function _finish(timedOut = false) {
    clearInterval(_classifyPoller); _classifyPoller = null;
    btn.disabled = false; btn.textContent = '↻ Classify';
    await _loadAll();
    if (timedOut) {
      toast('Classify timed out — check backend logs', 'error');
    } else {
      const pending = (await api.wi.stats(_project)).pending ?? 0;
      if (pending === 0 && seenRunning) {
        toast('Classification complete — no new items (all events already classified?)', 'info');
      } else if (pending > 0) {
        toast(`Classification complete — ${pending} items pending review`, 'success');
      } else {
        toast('Classification finished', 'info');
      }
    }
  }

  _classifyPoller = setInterval(async () => {
    try {
      const elapsed = Date.now() - startMs;
      if (elapsed > MAX_MS) { await _finish(true); return; }

      const status  = await api.wi.classifyStatus(_project);
      const running = status.running ?? false;

      if (running) {
        seenRunning = true;
        // Show pending mrr count so user sees progress
        const total = status.pending_total ?? 0;
        if (total > 0) btn.textContent = `⏳ ${total} unclassified…`;
        return;
      }

      // running=false:
      // Wait up to 15 s in case we started polling before the backend set the flag.
      if (!seenRunning && elapsed < 15_000) return;

      // Done (or never ran — e.g. no pending events)
      await _finish();
    } catch (_) { /* network blip — keep polling */ }
  }, 4_000);
}

// ── MD editor panel ────────────────────────────────────────────────────────

let _mdPanel = null;

async function _openMdPanel(item) {
  // Regenerate (and write) the MD file on disk, then navigate to Documents.
  // Documents API paths are relative to documents/ — no "documents/" prefix.
  const slug = (item.name || item.id).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60);
  const filePath = `use_cases/${slug}.md`;
  if (!window._nav) return;
  toast('Generating MD file…', 'info');
  try {
    await api.wi.md.refresh(_project, item.id);
  } catch (_) { /* non-fatal — navigate anyway, file may already exist */ }
  window._nav('documents', { openFile: filePath, project: _project, itemId: item.id });
}

// ── Summary log helper ────────────────────────────────────────────────────────

async function _appendSummaryToMdLog(ucId, oldSummary) {
  if (!oldSummary) return;

  // Compute file path (must match Python _use_case_slug: re.sub(r'[^a-z0-9]+','-',name).strip('-')[:60])
  const uc = _ucItems.find(u => u.id === ucId);
  if (!uc?.name) return;
  const slug     = uc.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '').slice(0, 60);
  const filePath = `use_cases/${slug}.md`;   // relative to documents/

  const mdData = await api.wi.md.get(_project, ucId).catch(() => null);
  if (!mdData?.content) return;

  const now = new Date();
  const ts = `${String(now.getFullYear()).slice(2)}/${String(now.getMonth()+1).padStart(2,'0')}/${String(now.getDate()).padStart(2,'0')}-${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
  const logEntry = `${ts} summary: ${oldSummary.replace(/\n/g, ' ')}`;

  let content = mdData.content;
  const LOG_HEADER = '## Summary Log';
  const logIdx = content.indexOf(LOG_HEADER);

  if (logIdx === -1) {
    content = content.trimEnd() + `\n\n${LOG_HEADER}\n${logEntry}\n`;
  } else {
    const afterHeader = content.slice(logIdx + LOG_HEADER.length);
    const nextSection = afterHeader.search(/\n##\s/);
    const newLogContent = `\n${logEntry}\n`;
    if (nextSection === -1) {
      content = content.slice(0, logIdx + LOG_HEADER.length) + newLogContent;
    } else {
      content = content.slice(0, logIdx + LOG_HEADER.length) + newLogContent + afterHeader.slice(nextSection);
    }
  }

  await api.documents.save(filePath, content, _project);
}

// ── Status options ────────────────────────────────────────────────────────────

const _STATUS_OPTIONS = [
  { score: 0, label: 'Not Started', cls: 'wi-s-req'  },
  { score: 2, label: 'In Progress', cls: 'wi-s-wip'  },
  { score: 5, label: 'Done',        cls: 'wi-s-done' },
];

// ── Rename popover ────────────────────────────────────────────────────────────

function _showRenamePopover(anchorEl, itemId, currentName, isUC) {
  if (_closePop(anchorEl)) return;

  // For UC rename: offer all existing UC names as quick picks
  const existingNames = isUC
    ? [...new Set(
        [..._allItems, ..._ucItems]
          .filter(i => i.wi_type === 'use_case' && i.name)
          .map(i => i.name)
      )]
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
      await _reloadCurrent();
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
  if (_closePop(anchorEl)) return;

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
        await api.wi.update(_project, itemId, { user_status: newScore });
        const item = _allItems.find(i => i.id === itemId);
        if (item) item.user_status = newScore;
        await _reloadCurrent();
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
  if (_closePop(anchorEl)) return;
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
        await _reloadCurrent();
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
    await _reloadCurrent();
  });
  wrap.querySelector('#wi-sum-cancel').addEventListener('click', () => {
    wrap.innerHTML = prev;
  });
}

// ── Popover helper ────────────────────────────────────────────────────────────

/**
 * Remove any open popover. If it was anchored to `anchorEl`, returns true
 * (caller should bail — same button toggled it closed). Otherwise returns false.
 */
function _closePop(anchorEl) {
  const existing = document.querySelector('.wi-wi-pop');
  if (!existing) return false;
  const sameAnchor = existing._popAnchor === anchorEl;
  existing.remove();
  return sameAnchor;
}

function _popupAt(el, anchor) {
  el._popAnchor = anchor; // store so _closePop can detect same-button re-click
  el.style.cssText += ';position:fixed;z-index:900;min-width:220px;padding:0.65rem;' +
    'background:var(--surface2);border:1px solid var(--border);' +
    'border-radius:var(--radius);box-shadow:0 6px 24px rgba(0,0,0,.4)';
  const rect = anchor.getBoundingClientRect();
  el.style.top  = (rect.bottom + 6) + 'px';
  el.style.left = Math.min(rect.left, window.innerWidth - 260) + 'px';
  document.body.appendChild(el);
}

// ── Drag-and-drop ─────────────────────────────────────────────────────────────

function _clearDragIndicators(listEl) {
  listEl.querySelectorAll('.wi-insert-above').forEach(el => el.classList.remove('wi-insert-above'));
  listEl.querySelectorAll('.wi-drag-over').forEach(el => el.classList.remove('wi-drag-over'));
  listEl.querySelectorAll('.wi-parent-target').forEach(el => el.classList.remove('wi-parent-target'));
  listEl.querySelectorAll('.wi-item-target').forEach(el => el.classList.remove('wi-item-target'));
  _dragOverItemId = null;
}

/**
 * Register an undoable action and enable the toolbar Undo button.
 * undoFn must return a promise resolving to { error? } or truthy on success.
 */
function _setUndoAction(label, undoFn, reloadFn) {
  _lastUndo = { label, undoFn, reloadFn };
  _updateUndoBtn();
}

function _clearUndo() {
  _lastUndo = null;
  _updateUndoBtn();
}

function _updateUndoBtn() {
  const btn = document.getElementById('wi-undo-btn');
  if (!btn) return;
  if (_lastUndo) {
    btn.disabled = false;
    btn.title    = `Undo: ${_lastUndo.label}`;
    btn.style.opacity = '1';
  } else {
    btn.disabled = true;
    btn.title    = 'Nothing to undo';
    btn.style.opacity = '0.4';
  }
}

/**
 * Show a small popover at position (x, y) offering two options:
 *   ↓ Make child  — reparent draggedId under targetId
 *   ⊕ Merge       — combine summaries, soft-delete draggedId
 *
 * reloadFn is called after a successful action.
 */
function _showLinkMergePopover(x, y, draggedId, targetId, reloadFn) {
  document.querySelectorAll('.wi-link-merge-pop').forEach(p => p.remove());

  // Type validation — same type required for both actions
  const allFlat = [..._allItems, ..._ucItems.flatMap(u => u.children || [])];
  const draggedItem = allFlat.find(i => i.id === draggedId);
  const targetItem  = allFlat.find(i => i.id === targetId);
  if (draggedItem && targetItem && draggedItem.wi_type !== targetItem.wi_type) {
    toast(`Cannot link: items must be the same type (${draggedItem.wi_type} ≠ ${targetItem.wi_type})`, 'error');
    return;
  }

  // Capture original parent before any action (for Make-child undo)
  const originalParentId = draggedItem?.wi_parent_id ?? null;

  const pop = document.createElement('div');
  pop.className = 'wi-link-merge-pop';
  pop.style.cssText = `position:fixed;z-index:950;padding:0.4rem;
    background:var(--surface2);border:1px solid var(--accent);
    border-radius:var(--radius);box-shadow:0 6px 24px rgba(0,0,0,.45);
    display:flex;flex-direction:column;gap:0.25rem;min-width:160px`;
  pop.style.left = Math.min(x, window.innerWidth - 180) + 'px';
  pop.style.top  = Math.min(y, window.innerHeight - 90) + 'px';

  pop.innerHTML = `
    <div style="font-size:0.65rem;color:var(--muted);font-weight:700;padding:0.1rem 0.3rem 0.3rem">
      DROP ACTION</div>
    <button id="wi-lm-child" style="text-align:left;padding:0.35rem 0.6rem;
      background:transparent;border:1px solid var(--border);border-radius:4px;
      color:var(--text);cursor:pointer;font-size:0.82rem">
      ↓ Make child</button>
    <button id="wi-lm-merge" style="text-align:left;padding:0.35rem 0.6rem;
      background:transparent;border:1px solid var(--border);border-radius:4px;
      color:var(--text);cursor:pointer;font-size:0.82rem">
      ⊕ Merge into target</button>
    <button id="wi-lm-cancel" style="text-align:left;padding:0.25rem 0.6rem;
      background:transparent;border:none;color:var(--muted);cursor:pointer;font-size:0.75rem">
      Cancel</button>
  `;
  document.body.appendChild(pop);

  const _close = () => pop.remove();

  pop.querySelector('#wi-lm-child').addEventListener('click', async () => {
    _close();
    try {
      const r = await api.wi.update(_project, draggedId, { wi_parent_id: targetId });
      if (r.error) { toast(`Error: ${r.error}`, 'error'); return; }
      await reloadFn();
      _setUndoAction('Item linked as child', () =>
        api.wi.update(_project, draggedId, { wi_parent_id: originalParentId || null }),
        reloadFn
      );
    } catch (err) { toast(`Link failed: ${err.message}`, 'error'); }
  });

  pop.querySelector('#wi-lm-merge').addEventListener('click', async () => {
    _close();
    if (!confirm('Merge: source summary will be appended to target, source will be soft-deleted. You can undo to restore the source. Continue?')) return;
    try {
      const r = await api.wi.merge(_project, targetId, draggedId);
      if (r.error) { toast(`Error: ${r.error}`, 'error'); return; }
      await reloadFn();
      _setUndoAction('Items merged', () => api.wi.unmerge(_project, draggedId), reloadFn);
    } catch (err) { toast(`Merge failed: ${err.message}`, 'error'); }
  });

  pop.querySelector('#wi-lm-cancel').addEventListener('click', _close);

  // Auto-dismiss on outside click
  setTimeout(() => {
    document.addEventListener('click', e => {
      if (!pop.contains(e.target)) _close();
    }, { once: true });
  }, 100);
}

function _attachDragListeners(reloadFn = _loadAll) {
  const listEl = document.getElementById('wi-list');
  if (!listEl) return;

  // ── Card drag start/end ───────────────────────────────────────────────────
  listEl.querySelectorAll('.wi-card[draggable="true"]').forEach(card => {
    card.addEventListener('dragstart', (e) => {
      _dragItemId = card.dataset.itemId;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', _dragItemId);
      setTimeout(() => card.classList.add('wi-dragging'), 0);
    });
    card.addEventListener('dragend', () => {
      card.classList.remove('wi-dragging');
      _clearDragIndicators(listEl);
      _dragItemId     = null;
      _insertBeforeId = null;
    });
  });

  // ── Drop zone: dragover tracks insert position, drop performs action ──────
  listEl.querySelectorAll('.wi-drop-zone').forEach(zone => {
    zone.addEventListener('dragover', (e) => {
      if (!_dragItemId) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';

      // Highlight only this zone
      listEl.querySelectorAll('.wi-drag-over').forEach(el => { if (el !== zone) el.classList.remove('wi-drag-over'); });
      zone.classList.add('wi-drag-over');

      // Detect if hovering directly over a sibling card → link/merge mode
      const hoverEl  = document.elementFromPoint(e.clientX, e.clientY);
      const hoverCard = hoverEl?.closest('.wi-card[data-item-id]');
      const hoverId  = hoverCard?.dataset.itemId;
      const isHoverTarget = hoverId && hoverId !== _dragItemId;

      // Clear old item-target highlights, then set new one if applicable
      listEl.querySelectorAll('.wi-item-target').forEach(el => el.classList.remove('wi-item-target'));
      _dragOverItemId = null;

      if (isHoverTarget) {
        // Hovering over a specific card → highlight for link/merge
        hoverCard.classList.add('wi-item-target');
        _dragOverItemId = hoverId;
        // Don't show insert-above indicator when in link/merge mode
        listEl.querySelectorAll('.wi-insert-above').forEach(el => el.classList.remove('wi-insert-above'));
        _insertBeforeId = null;
      } else {
        // Compute insert position within zone for same-UC reorder
        const cards = [...zone.querySelectorAll('.wi-card')].filter(c => c.dataset.itemId !== _dragItemId);
        listEl.querySelectorAll('.wi-insert-above').forEach(el => el.classList.remove('wi-insert-above'));
        _insertBeforeId = null;
        for (const c of cards) {
          const rect = c.getBoundingClientRect();
          if (e.clientY < rect.top + rect.height / 2) {
            c.classList.add('wi-insert-above');
            _insertBeforeId = c.dataset.itemId;
            break;
          }
        }
      }
    });

    zone.addEventListener('dragleave', (e) => {
      if (!zone.contains(e.relatedTarget)) {
        zone.classList.remove('wi-drag-over');
        zone.querySelectorAll('.wi-insert-above').forEach(el => el.classList.remove('wi-insert-above'));
        listEl.querySelectorAll('.wi-item-target').forEach(el => el.classList.remove('wi-item-target'));
        _dragOverItemId = null;
      }
    });

    zone.addEventListener('drop', async (e) => {
      e.preventDefault();
      e.stopPropagation();

      const targetUcId   = zone.dataset.ucId;
      const itemId       = _dragItemId;
      const insertBefore = _insertBeforeId;
      const overItemId   = _dragOverItemId;

      _clearDragIndicators(listEl);
      _dragItemId     = null;
      _insertBeforeId = null;
      _dragOverItemId = null;

      if (!targetUcId || !itemId || targetUcId === '__none__') return;

      // If dropped directly onto another item card → show link/merge popover
      if (overItemId) {
        _showLinkMergePopover(e.clientX, e.clientY, itemId, overItemId, reloadFn);
        return;
      }

      const draggedItem = _allItems.find(i => i.id === itemId);
      if (!draggedItem) return;

      const isSameUC = draggedItem.wi_parent_id === targetUcId;

      if (!isSameUC) {
        // Cross-UC move
        try {
          await api.wi.update(_project, itemId, { wi_parent_id: targetUcId });
          toast('Moved to use case', 'success');
          await reloadFn();
        } catch (err) { toast(`Move failed: ${err.message}`, 'error'); }
        return;
      }

      // ── Same UC: reorder ──────────────────────────────────────────────────
      // Get current display order (same sort as _renderList)
      const siblings = _allItems
        .filter(i => i.wi_parent_id === targetUcId)
        .sort((a, b) => {
          const aDone = _isDone(a) ? 1 : 0;
          const bDone = _isDone(b) ? 1 : 0;
          if (aDone !== bDone) return aDone - bDone;
          return (b.user_importance ?? b.score_importance ?? 0) -
                 (a.user_importance ?? a.score_importance ?? 0);
        });

      const withoutDragged = siblings.filter(s => s.id !== itemId);
      const insertIdx = insertBefore
        ? withoutDragged.findIndex(s => s.id === insertBefore)
        : withoutDragged.length;

      if (insertIdx < 0) return;

      // Build new order with dragged item inserted
      const newOrder = [...withoutDragged];
      newOrder.splice(insertIdx, 0, draggedItem);

      // Assign user_importance: top item = N (highest), bottom item = 1
      const N = newOrder.length;
      const updates = newOrder.map((s, idx) => ({ id: s.id, user_importance: N - idx }));

      try {
        await api.wi.reorder(_project, updates);
        await reloadFn();
      } catch (err) { toast(`Reorder failed: ${err.message}`, 'error'); }
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
    await _reloadCurrent();
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
    const [statsData, listData, mrrData] = await Promise.all([
      api.wi.stats(_project).catch(() => ({})),
      api.wi.list(_project).catch(() => ({ items: [] })),
      api.wi.classifyStatus(_project).catch(() => ({})),
    ]);
    _stats    = statsData || {};
    _mrrCounts = mrrData || {};
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

// ── Use Cases tab ─────────────────────────────────────────────────────────────

async function _loadUseCases() {
  if (!_project) return;
  _setStatus('Loading use cases…');
  try {
    const [data, mrrData, statsData] = await Promise.all([
      api.wi.useCases(_project).catch(() => ({ use_cases: [] })),
      api.wi.classifyStatus(_project).catch(() => ({})),
      api.wi.stats(_project).catch(() => ({})),
    ]);
    _ucItems   = data.use_cases || [];
    _mrrCounts = mrrData || {};
    _stats     = statsData || {};
    // Persist in cache so re-entering the tab skips the network call
    _ucCacheProject = _project;
    _ucCacheData    = _ucItems;
    _renderStats();
    _renderUseCases();
    _setStatus('');
  } catch (e) {
    _setStatus(`Error: ${e.message}`);
    const el = document.getElementById('wi-list');
    if (el) el.innerHTML =
      `<div style="color:var(--muted);text-align:center;padding:2rem">${_esc(e.message)}</div>`;
  }
}

function _groupUcItems(children) {
  const TYPE_ORDER = ['bug', 'feature', 'task', 'policy', 'requirement', 'use_case'];
  const inProgress = children.filter(c => !_isDone(c));
  const completed  = children.filter(c =>  _isDone(c));
  function sortByTypeThenPriority(items) {
    return [...items].sort((a, b) => {
      const ta = TYPE_ORDER.indexOf(a.wi_type), tb = TYPE_ORDER.indexOf(b.wi_type);
      if (ta !== tb) return ta - tb;
      return (b.user_importance ?? b.score_importance ?? 0) -
             (a.user_importance ?? a.score_importance ?? 0);
    });
  }
  return {
    inProgress: sortByTypeThenPriority(inProgress),
    completed:  sortByTypeThenPriority(completed),
  };
}

function _renderUseCases() {
  const el = document.getElementById('wi-list');
  if (!el) return;

  // Exclude completed use cases — they live in the Completed tab
  const activeUcs = _ucItems.filter(uc => !uc.completed_at);

  if (!activeUcs.length) {
    el.innerHTML = `<div style="color:var(--muted);text-align:center;padding:3rem;font-size:0.82rem">
      No active use cases.<br>Approve use cases in the <strong>Work Items</strong> tab first.<br>
      ${_ucItems.length > activeUcs.length ? `<span style="color:#22c55e">✓ ${_ucItems.length - activeUcs.length} completed — see Completed tab.</span>` : ''}
    </div>`;
    return;
  }

  const fmt = (iso) => iso ? iso.slice(0, 10) : '—';

  let html = '';
  for (const uc of activeUcs) {
    const s = uc.stats;
    const evChips = [
      s.total_prompts  ? `${s.total_prompts} prompts`   : '',
      s.total_commits  ? `${s.total_commits} commits`   : '',
      s.total_messages ? `${s.total_messages} messages` : '',
    ].filter(Boolean).join(' · ');

    const pendingDot = s.pending_children > 0
      ? `<span style="color:#f59e0b;font-weight:700">●</span> ${s.pending_children} pending` : '';

    const ucId = `uc-card-${uc.id.replace(/-/g, '')}`;

    // Group children by in-progress vs completed
    const { inProgress, completed } = _groupUcItems(uc.children || []);

    // Render grouped sections
    let childrenHtml = '';
    if (!uc.children.length) {
      childrenHtml = `<div style="padding:0.4rem 0;color:var(--muted);font-size:0.78rem;font-style:italic">No items yet</div>`;
    } else {
      // Group in-progress by type
      const ipTypes = ['bug', 'feature', 'task', 'policy', 'requirement'];
      const ipByType = {};
      for (const t of ipTypes) ipByType[t] = inProgress.filter(c => c.wi_type === t && (c.depth ?? 0) === 0);

      let ipHtml = '';
      for (const t of ipTypes) {
        const group = ipByType[t];
        if (!group.length) continue;
        const meta = _typeMeta(t);
        ipHtml += `<div style="font-size:0.69rem;font-weight:600;color:var(--muted);text-transform:uppercase;
                               letter-spacing:0.05em;margin:0.45rem 0 0.2rem">${meta.icon} ${meta.label}s (${group.length})</div>`;
        for (const c of group) {
          ipHtml += _renderUcItem(c, c.depth ?? 0);
          // Render sub-items (depth > 0) that have this item as parent
          const subs = inProgress.filter(s => s.wi_parent_id === c.id && (s.depth ?? 0) > 0);
          for (const sub of subs) ipHtml += _renderUcItem(sub, sub.depth ?? 1);
        }
      }

      let doneHtml = '';
      for (const c of completed.filter(c => (c.depth ?? 0) === 0)) {
        doneHtml += _renderUcItem(c, 0);
        const subs = completed.filter(s => s.wi_parent_id === c.id && (s.depth ?? 0) > 0);
        for (const sub of subs) doneHtml += _renderUcItem(sub, sub.depth ?? 1);
      }

      const hideDone = _ucHideDone.has(uc.id);
      childrenHtml = `
        ${inProgress.length ? `
          <div style="font-size:0.72rem;font-weight:700;color:var(--text);
                      border-bottom:1px solid var(--border);padding-bottom:0.25rem;margin-bottom:0.4rem">
            ── In Progress (${inProgress.length}) ──────────────────
          </div>
          ${ipHtml}
        ` : ''}
        ${completed.length ? `
          <div id="done-section-${uc.id}" style="${hideDone ? 'display:none' : ''}">
            <div style="font-size:0.72rem;font-weight:700;color:var(--muted);
                        border-bottom:1px solid var(--border);padding-bottom:0.25rem;
                        margin:0.6rem 0 0.4rem">
              ── Completed (${completed.length}) ──────────────────
            </div>
            ${doneHtml}
          </div>
        ` : ''}
      `;
    }

    html += `
      <div class="wi-uc-card" id="${ucId}">
        <div class="wi-uc-card-header" data-uc-expand="${uc.id}">
          <span class="wi-uc-arrow" style="font-size:0.65rem;color:var(--muted)">▼</span>
          <span class="wi-uc-label">◻ USE CASE</span>
          <span class="wi-id">${_esc(uc.wi_id)}</span>
          <span class="wi-name">${_esc(uc.name || uc.id)}</span>
          <button class="wi-edit-arrow" data-action="rename-pop"
                  data-id="${uc.id}" data-current-name="${_esc(uc.name || '')}" data-is-uc="true"
                  title="Rename use case">▾</button>
          ${_openDaysBadge(uc.approved_at)}
          <span style="flex:1"></span>
          ${uc.due_date
            ? _dueBadge(uc.due_date, uc.start_date)
            : `<button class="wi-edit-link" data-action="due-pop" data-item-id="${uc.id}"
                       style="font-size:0.72rem;opacity:0.6" title="Set due date for this use case">📅 Due date</button>`
          }
          <button class="wi-btn wi-btn-ghost" data-action="edit-md"
                  data-id="${uc.id}" data-name="${_esc(uc.name)}" title="Open Markdown in Documents">✎ MD</button>
          <div style="position:relative;display:inline-flex" id="uc-run-wrap-${uc.id}">
            <button class="btn btn-ghost btn-sm" style="font-size:0.65rem;padding:0.2rem 0.4rem;
                    border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface2)"
                    onclick="event.stopPropagation();window._ucRunMenu('${uc.id}','uc',this)">▶ Run ▾</button>
            <div id="uc-run-drop-${uc.id}" style="display:none;position:absolute;top:100%;right:0;
                 background:var(--bg);border:1px solid var(--border);border-radius:6px;
                 min-width:180px;z-index:200;box-shadow:0 4px 12px rgba(0,0,0,.15)"></div>
          </div>
          <button class="wi-btn wi-btn-approve" style="font-size:0.7rem;opacity:0.85"
                  data-action="complete-uc" data-id="${uc.id}"
                  title="Mark use case as completed (all items must be done)">✓ Complete</button>
        </div>
        <div class="wi-uc-card-body" id="body-${uc.id}">
          <div class="wi-uc-dates">
            <span>Created: ${fmt(uc.created_at)}</span>
            <span>Approved: ${fmt(uc.approved_at)}${uc.approved_at ? ` · <strong>${_daysAgo(uc.approved_at)}d open</strong>` : ''}</span>
            <span>Updated: ${fmt(uc.updated_at)}</span>
            <span style="flex:1"></span>
            ${evChips ? `<div class="wi-uc-event-chips">
              ${evChips.split(' · ').map(c => `<span class="wi-uc-event-chip">${c}</span>`).join('')}
            </div>` : ''}
            <span style="font-size:0.67rem;color:var(--muted)">
              ${s.total_children} item${s.total_children !== 1 ? 's' : ''}
              (${s.approved_children} approved${s.pending_children ? `, ${pendingDot}` : ''})
            </span>
          </div>

          <!-- Summary -->
          <div class="wi-uc-summary wi-summary-wrap" style="padding:0.55rem 0.9rem;border-bottom:1px solid var(--border)">
            ${uc.summary
              ? `<div style="font-size:0.79rem;color:var(--text2);line-height:1.5;border-left:3px solid var(--accent);padding-left:0.5rem">${_esc(uc.summary)}</div>`
              : `<span style="color:var(--muted);font-style:italic;font-size:0.77rem">No summary</span>`
            }
            <button class="wi-edit-link" data-action="edit-summary"
                    data-id="${uc.id}" data-summary="${_esc(uc.summary || '')}">✎ Edit summary</button>
          </div>

          <!-- Toolbar: Summarise + toggle done -->
          <div style="display:flex;gap:0.5rem;padding:0.4rem 0.9rem;border-bottom:1px solid var(--border);align-items:center">
            <button class="wi-btn wi-btn-ghost" data-action="summarise" data-uc-id="${uc.id}"
                    style="font-size:0.72rem" title="AI rewrite summary based on current items (auto-applies)">⟳ Summarise</button>
            ${completed.length ? `
              <button class="wi-btn wi-btn-ghost" data-action="toggle-done" data-uc-id="${uc.id}"
                      style="font-size:0.72rem" title="Toggle completed items">
                ${_ucHideDone.has(uc.id) ? '👁 Show Done' : '🙈 Hide Done'}
              </button>
            ` : ''}
          </div>

          <!-- Children grouped -->
          <div class="wi-uc-children wi-drop-zone" data-uc-id="${uc.id}" style="padding:0.4rem 0.9rem 0.3rem;border-bottom:1px solid var(--border)">
            ${childrenHtml}
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
              <button class="wi-btn wi-btn-ghost"
                      onclick="document.getElementById('wi-add-form-${uc.id}').classList.remove('visible')">Cancel</button>
            </div>
          </div>
          <button class="wi-btn wi-btn-ghost" style="margin:0.4rem 0.9rem;font-size:0.72rem"
                  data-action="add-item" data-uc-id="${uc.id}">+ Add Item</button>
        </div>
      </div>
    `;
  }

  el.innerHTML = html;

  // Wire collapse for UC card headers
  el.querySelectorAll('[data-uc-expand]').forEach(hdr => {
    hdr.addEventListener('click', (e) => {
      if (e.target.closest('[data-action]') || e.target.closest('button')) return;
      const ucId = hdr.dataset.ucExpand;
      const body = document.getElementById(`body-${ucId}`);
      if (!body) return;
      body.classList.toggle('collapsed');
      const arrow = hdr.querySelector('.wi-uc-arrow');
      if (arrow) arrow.textContent = body.classList.contains('collapsed') ? '▶' : '▼';
    });
  });

  _attachDragListeners(_reloadCurrent);
}

function _renderUcChildRow(c, rank) {
  return _renderUcItem(c, 0);
}

function _renderUcItem(item, depth = 0) {
  const meta      = _typeMeta(item.wi_type);
  const isPending = !item.wi_id || item.wi_id.startsWith('AI');
  const st        = _itemStatus(item);
  const isDone    = st.cls === 'wi-s-done';
  const indent    = depth > 0 ? `margin-left:${depth * 1.5}rem;` : '';

  return `
    <div class="wi-card${isDone ? ' wi-card-done' : ''}"
         draggable="true" style="${indent}margin-bottom:0.35rem" data-item-id="${item.id}">
      <div class="wi-card-header" title="Click to expand">
        <span class="wi-type-badge ${meta.cls}">${meta.icon} ${meta.label}</span>
        <button class="wi-edit-arrow" data-action="type-pop"
                data-id="${item.id}" data-type="${item.wi_type}" title="Change type">▾</button>
        <span class="wi-name${isDone ? ' wi-name-done' : ''}">${isDone ? '✓ ' : ''}${_esc(item.name || '(unnamed)')}</span>
        <button class="wi-edit-arrow" data-action="rename-pop"
                data-id="${item.id}" data-current-name="${_esc(item.name || '')}" data-is-uc="false"
                title="Rename">▾</button>
        <span class="wi-status-badge ${st.cls}">${st.label}</span>
        <button class="wi-edit-arrow" data-action="status-pop"
                data-id="${item.id}" data-score="${_statusNum(item)}"
                title="Change status">▾</button>
        ${isPending
          ? `<span class="wi-pending">${_esc(item.wi_id || 'pending')}</span>
             ${_waitingBadge(item.created_at)}`
          : `<span class="wi-id">${_esc(item.wi_id)}</span>`
        }
        ${_hotspotBadge(item._hotspot_files)}
        ${_dueBadge(item.due_date, item.start_date)}
        <div class="wi-actions">
          <button class="wi-edit-arrow" data-action="parent-pop"
                  data-id="${item.id}" data-uc-id="${item._uc_id || ''}"
                  title="Change parent">⇑</button>
          <button class="wi-btn wi-btn-ghost" data-action="copy-item"
                  data-id="${item.id}" title="Copy text to clipboard" style="font-size:0.75rem;padding:0.1rem 0.35rem">⎘</button>
          <div style="position:relative;display:inline-flex">
            <button title="Run pipeline on this item"
                    onclick="event.stopPropagation();window._ucRunMenu('${item.id}','item',this,'${item._uc_id || ''}')"
                    style="font-size:0.6rem;padding:0.1rem 0.28rem;border:1px solid var(--border);
                           border-radius:3px;cursor:pointer;background:var(--surface2)">▶</button>
            <div id="uc-run-drop-${item.id}" style="display:none;position:absolute;bottom:100%;right:0;
                 background:var(--bg);border:1px solid var(--border);border-radius:6px;
                 min-width:160px;z-index:300;box-shadow:0 4px 12px rgba(0,0,0,.2)"></div>
          </div>
          <span class="wi-arrow" style="font-size:0.65rem;color:var(--muted)">▼</span>
          ${isPending ? `
            <button class="wi-btn wi-btn-approve" data-action="approve" data-id="${item.id}" title="Approve">✓</button>
            <button class="wi-btn wi-btn-reject"  data-action="reject"  data-id="${item.id}" title="Reject">✗</button>
          ` : ''}
        </div>
      </div>
      <div class="wi-card-body collapsed">
        <div class="wi-summary-wrap">
          ${item.summary
            ? `<div class="wi-summary">${_esc(item.summary)}</div>`
            : `<span style="color:var(--muted);font-style:italic;font-size:0.77rem">No summary yet</span>`
          }
          <button class="wi-edit-link" data-action="edit-summary"
                  data-id="${item.id}" data-summary="${_esc(item.summary || '')}">✎ Edit summary</button>
        </div>
        <div class="wi-scores" style="margin-top:0.35rem">
          <span>Importance: ${_scorePips(item.score_importance, '#3b82f6')}</span>
          <span>Completion: ${_scorePips(item.score_status, '#22c55e')}</span>
        </div>
        <div style="margin-top:0.4rem;font-size:0.75rem;display:flex;align-items:center;gap:0.5rem">
          ${item.due_date
            ? `<span style="color:var(--muted)">📅 ${item.start_date || '—'} → ${item.due_date}</span>
               <button class="wi-edit-link" data-action="due-pop" data-item-id="${item.id}">✎</button>`
            : `<button class="wi-edit-link" data-action="due-pop" data-item-id="${item.id}">📅 Set due date</button>`
          }
        </div>
        ${item._hotspot_files && item._hotspot_files.length ? `
          <div style="margin-top:0.4rem;font-size:0.72rem;color:#92400e;background:#fef3c7;border-radius:4px;padding:0.3rem 0.5rem">
            🔥 <strong>Code alerts:</strong>
            ${item._hotspot_files.map(h =>
              `<span title="commits:${h.commit_count} bugs:${h.bug_commit_count} lines:${h.current_lines} score:${h.hotspot_score}">${_esc(h.file_path)}</span>`
            ).join(', ')}
          </div>
        ` : ''}
        ${item.deliveries ? `<div class="wi-deliveries" style="margin-top:0.4rem">✓ ${_esc(item.deliveries)}</div>` : ''}
      </div>
    </div>
  `;
}

// ── Age / waiting helpers ──────────────────────────────────────────────────────

/** Returns whole days elapsed since an ISO date string, or null if no date. */
function _daysAgo(isoDate) {
  if (!isoDate) return null;
  return Math.max(0, Math.floor((Date.now() - new Date(isoDate)) / 86400000));
}

/** Orange/red badge shown on pending items: "⏳ 5d waiting" */
function _waitingBadge(createdAt) {
  const d = _daysAgo(createdAt);
  if (d === null) return '';
  const color = d > 7 ? '#ef4444' : d > 3 ? '#f59e0b' : '#9ca3af';
  return `<span title="Waiting for approval · created ${createdAt ? createdAt.slice(0,10) : '?'}"
    style="font-size:0.65rem;color:${color};white-space:nowrap;padding:1px 5px;
    background:${color}18;border-radius:3px;border:1px solid ${color}44;line-height:1.6">⏳ ${d}d waiting</span>`;
}

// ── UC / item pipeline run menu + panel ───────────────────────────────────────

window._ucRunMenu = async (targetId, mode, triggerEl, ucId = '') => {
  // If dropdown already open, toggle it closed
  const existing = document.getElementById(_UC_DROP_ID);
  if (existing) { existing.remove(); return; }

  // Load pipeline names once per mode (cached separately for use_case vs item)
  const apiMode = mode === 'uc' ? 'use_case' : 'item';
  if (apiMode === 'use_case' && !_ucPipeNamesUC) {
    try {
      const pipes = await api.agents.listPipelines('use_case');
      _ucPipeNamesUC = pipes.map(p => p.name);
      if (!_ucPipeNamesUC.length) _ucPipeNamesUC = ['standard'];
    } catch (e) { _ucPipeNamesUC = ['standard']; }
  } else if (apiMode === 'item' && !_ucPipeNamesItem) {
    try {
      const pipes = await api.agents.listPipelines('item');
      _ucPipeNamesItem = pipes.map(p => p.name);
      if (!_ucPipeNamesItem.length) _ucPipeNamesItem = ['standard'];
    } catch (e) { _ucPipeNamesItem = ['standard']; }
  }
  const pipeNames = apiMode === 'use_case' ? _ucPipeNamesUC : _ucPipeNamesItem;

  // Build a body-level fixed dropdown to avoid overflow:hidden clipping on .wi-uc-card
  const rect = triggerEl.getBoundingClientRect();
  const drop = document.createElement('div');
  drop.id = _UC_DROP_ID;
  drop.style.cssText = `
    position:fixed;top:${rect.bottom + 4}px;left:${rect.left}px;
    background:var(--bg);border:1px solid var(--border);border-radius:6px;
    min-width:160px;z-index:10000;box-shadow:0 4px 12px rgba(0,0,0,.25);
  `;
  drop.innerHTML = pipeNames.map(name =>
    `<div onclick="document.getElementById('${_UC_DROP_ID}')?.remove();window._ucStartRun('${_esc(name)}','${_esc(targetId)}','${_esc(mode)}','${_esc(ucId)}')"
          style="padding:0.4rem 0.8rem;font-size:0.78rem;cursor:pointer;border-bottom:1px solid var(--border);
                 color:var(--text)"
          onmouseover="this.style.background='var(--bg2)'" onmouseout="this.style.background=''">
      ${_esc(name)}
    </div>`
  ).join('');

  document.body.appendChild(drop);

  // Close on outside click
  setTimeout(() => {
    const handler = (e) => {
      const d = document.getElementById(_UC_DROP_ID);
      if (d && !d.contains(e.target) && e.target !== triggerEl) {
        d.remove();
        document.removeEventListener('click', handler);
      }
    };
    document.addEventListener('click', handler);
  }, 0);
};

window._ucStartRun = async (pipeName, targetId, mode, ucId) => {
  if (!_project) { return; }

  let task = '';
  let linked_uc_id = null;
  let linked_item_id = null;
  let source = 'direct';
  let contextLabel = '';

  try {
    if (mode === 'uc') {
      const ucData  = _ucItems.find(u => u.id === targetId);
      const name    = ucData?.name || targetId;
      const wiId    = ucData?.wi_id  || '';
      const summary = ucData?.summary || '';
      const ac      = ucData?.acceptance_criteria || '';
      const impl    = ucData?.implementation_plan || '';
      const children = ucData?.children || [];
      const openItems = children.filter(c => !['done'].includes(c.user_status));
      const doneItems = children.filter(c =>  ['done'].includes(c.user_status));
      const itemLines = openItems.map(it =>
        `- [${it.wi_type}] ${it.wi_id || 'pending'} ${it.name}` +
        (it.user_status ? ` (${it.user_status}, score=${it.score_status || 0}/5)` : '') +
        (it.summary ? `\n  Summary: ${it.summary.slice(0, 250)}` : '') +
        (it.acceptance_criteria ? `\n  AC: ${it.acceptance_criteria.slice(0, 200)}` : '')
      ).join('\n');
      const doneLines = doneItems.slice(0,10).map(it =>
        `- ✓ [${it.wi_type}] ${it.wi_id || ''} ${it.name}`
      ).join('\n');
      task = [
        `RUN PIPELINE ON USE CASE: ${name}${wiId ? ' [' + wiId + ']' : ''}`,
        summary ? `SUMMARY:\n${summary}` : '',
        ac      ? `ACCEPTANCE CRITERIA:\n${ac}` : '',
        impl    ? `IMPLEMENTATION PLAN:\n${impl.slice(0, 600)}` : '',
        `\nOPEN ITEMS (${openItems.length}):`,
        itemLines || '(none)',
        doneItems.length ? `\nCOMPLETED ITEMS (${doneItems.length}):\n${doneLines}` : '',
      ].filter(Boolean).join('\n');
      linked_uc_id = targetId;
      source = 'use_case';
      contextLabel = name;
    } else {
      // mode === 'item'
      const ucData   = _ucItems.find(u => u.id === ucId);
      const allItems = (ucData?.children || []);
      const item     = allItems.find(it => it.id === targetId) ||
                       _allItems.find(it => it.id === targetId);
      const itemName = item?.name || targetId;
      const itemWiId = item?.wi_id || '';
      task = [
        `RUN PIPELINE ON ITEM: ${itemName}${itemWiId ? ' [' + itemWiId + ']' : ''}`,
        `TYPE: ${item?.wi_type || 'unknown'} | STATUS: ${item?.user_status || 'open'} | SCORE: ${item?.score_status || 0}/5`,
        item?.summary ? `SUMMARY:\n${item.summary}` : '',
        item?.acceptance_criteria ? `ACCEPTANCE CRITERIA:\n${item.acceptance_criteria}` : '',
        ucData ? `\nPARENT USE CASE: ${ucData.name}${ucData.wi_id ? ' [' + ucData.wi_id + ']' : ''}` : '',
        ucData?.summary ? `UC SUMMARY:\n${ucData.summary.slice(0, 400)}` : '',
      ].filter(Boolean).join('\n');
      linked_item_id = targetId;
      linked_uc_id   = ucId || null;
      source = 'item';
      contextLabel = itemName;
    }

    // Start the run
    const res = await api.agents.startPipelineRun({
      pipeline: pipeName, task, project: _project,
      source, linked_uc_id, linked_item_id,
    });

    _ucRunCtx = { mode, ucId: linked_uc_id, itemId: linked_item_id, runId: res.run_id };

    // Open fixed right-side drawer
    _ucOpenPanel(res.run_id, pipeName, contextLabel);
  } catch (e) {
    toast(`Failed to start pipeline run: ${e.message}`, 'error');
  }
};

// Fixed panel uses stable IDs — only one panel exists at a time
const _PANEL_ID        = 'uc-run-panel';
const _PANEL_DOT_ID    = 'uc-panel-dot';
const _PANEL_STAGES_ID = 'uc-panel-stages';
const _PANEL_LOG_ID    = 'uc-panel-log';
const _PANEL_VERDICT_ID= 'uc-panel-verdict';
const _PANEL_TITLE_ID  = 'uc-panel-title';

function _ucOpenPanel(runId, pipeName, contextLabel) {
  // Remove any existing panel
  const existing = document.getElementById(_PANEL_ID);
  if (existing) existing.remove();
  if (_ucPollTimer) { clearInterval(_ucPollTimer); _ucPollTimer = null; }

  const label = contextLabel
    ? `${_esc(pipeName)} — ${_esc(contextLabel.slice(0, 30))}`
    : _esc(pipeName);

  const panel = document.createElement('div');
  panel.id = _PANEL_ID;
  panel.style.cssText = `
    position:fixed; right:0; top:0; height:100vh; width:420px; z-index:9999;
    background:var(--bg); border-left:2px solid var(--accent);
    display:flex; flex-direction:column; padding:1rem 1.1rem;
    box-shadow:-6px 0 24px rgba(0,0,0,.25); overflow:hidden;
  `;
  panel.innerHTML = `
    <!-- Header -->
    <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.7rem;flex-shrink:0">
      <span id="${_PANEL_DOT_ID}"
            style="width:10px;height:10px;border-radius:50%;background:#f5a623;flex-shrink:0"></span>
      <span id="${_PANEL_TITLE_ID}"
            style="font-size:0.82rem;font-weight:700;flex:1;overflow:hidden;text-overflow:ellipsis;
                   white-space:nowrap">${label}</span>
      <button onclick="window._ucClosePanel()"
              style="font-size:0.75rem;padding:2px 8px;border:1px solid var(--border);
                     border-radius:4px;cursor:pointer;background:transparent;flex-shrink:0">✕</button>
    </div>

    <!-- Stages (scrollable) -->
    <div id="${_PANEL_STAGES_ID}"
         style="flex:1;overflow-y:auto;font-size:0.78rem;padding-right:0.25rem"></div>

    <!-- Log (compact, collapsed) -->
    <details style="flex-shrink:0;margin-top:0.5rem">
      <summary style="font-size:0.68rem;color:var(--muted);font-weight:600;letter-spacing:.04em;
                      text-transform:uppercase;cursor:pointer;padding:0.3rem 0;
                      border-top:1px solid var(--border)">Execution Log</summary>
      <div id="${_PANEL_LOG_ID}"
           style="font-family:monospace;font-size:0.7rem;color:var(--muted);
                  max-height:100px;overflow-y:auto;white-space:pre-wrap;line-height:1.5;
                  margin-top:0.25rem">Starting…</div>
    </details>

    <!-- Verdict / approval gate -->
    <div id="${_PANEL_VERDICT_ID}"
         style="display:none;margin-top:0.5rem;flex-shrink:0"></div>
  `;
  document.body.appendChild(panel);

  _ucPollRun(runId);
}

window._ucClosePanel = () => {
  const panel = document.getElementById(_PANEL_ID);
  if (panel) panel.remove();
  if (_ucPollTimer) { clearInterval(_ucPollTimer); _ucPollTimer = null; }
};

function _ucPollRun(runId) {
  if (_ucPollTimer) clearInterval(_ucPollTimer);
  const STATUS_COLORS = { done: '#3ecf8e', error: '#e85d75', running: '#f5a623', waiting_approval: '#9b7ef8' };
  const STAGE_ICONS   = { done: '●', running: '⟳', error: '✗', pending: '○' };

  const poll = async () => {
    try {
      const data = await api.agents.getPipelineRun(runId);
      const dot      = document.getElementById(_PANEL_DOT_ID);
      const stagesEl = document.getElementById(_PANEL_STAGES_ID);
      const logEl    = document.getElementById(_PANEL_LOG_ID);
      const verdEl   = document.getElementById(_PANEL_VERDICT_ID);

      if (!dot) return; // panel was closed

      dot.style.background = STATUS_COLORS[data.status] || '#f5a623';

      if (stagesEl && data.stages) {
        stagesEl.innerHTML = data.stages.map(s => {
          const icon  = STAGE_ICONS[s.status] || '○';
          const color = s.status === 'done'    ? '#3ecf8e'
                      : s.status === 'error'   ? '#e85d75'
                      : s.status === 'running' ? '#f5a623'
                      : 'var(--muted)';
          const dur   = s.duration_s != null ? `${s.duration_s.toFixed(1)}s` : '';
          const cost  = s.cost_usd > 0 ? `$${Number(s.cost_usd).toFixed(3)}` : '';
          const toks  = s.input_tokens ? `${Math.round((s.input_tokens + s.output_tokens) / 1000)}k tok` : '';
          const detId = `stage-det-${s.id}`;
          const hasDetails = s.status === 'done' || s.status === 'error';

          // Build detail section
          let detailHtml = '';
          if (hasDetails) {
            // Input summary
            let inputHtml = '';
            const snap = s.input_snapshot;
            if (snap) {
              const inputLines = [];
              if (snap.role) inputLines.push(`From: ${snap.role}`);
              if (snap.summary) inputLines.push(snap.summary.slice(0, 120));
              if (snap.work_items?.length) inputLines.push(`${snap.work_items.length} work items`);
              if (snap.verdict) inputLines.push(`Verdict: ${snap.verdict}`);
              if (snap.issues?.length) inputLines.push(`Issues: ${snap.issues.slice(0,2).join('; ').slice(0,100)}`);
              if (snap.raw_output) inputLines.push(snap.raw_output.slice(0, 150));
              if (inputLines.length) {
                inputHtml = `<div style="margin-bottom:0.35rem;color:var(--muted)">
                  <span style="font-weight:600;font-size:0.65rem;letter-spacing:.04em;text-transform:uppercase">Input</span>
                  <div style="margin-top:0.2rem;color:var(--text);font-size:0.7rem;line-height:1.4">${inputLines.map(l => _esc(l)).join('<br>')}</div>
                </div>`;
              }
            }

            // Steps / tool calls
            let stepsHtml = '';
            const steps = s.steps_json;
            if (steps?.length) {
              const stepLines = steps.map(st => {
                const tool = st.tool || '?';
                // Pick most meaningful arg
                const args = st.args || {};
                const mainArg = args.file_path || args.path || args.pattern || args.command || args.query || '';
                const argStr = mainArg ? `(${String(mainArg).slice(0, 50)})` : '';
                // Short observation
                const obs = (st.observation || '').slice(0, 80).replace(/\n/g, ' ');
                return `<div style="display:flex;gap:0.3rem;align-items:baseline;padding:0.1rem 0">
                  <span style="color:var(--accent);font-weight:600;min-width:4px">${st.step}.</span>
                  <span style="color:#a78bfa;white-space:nowrap">${_esc(tool)}</span>
                  <span style="color:var(--muted);font-size:0.67rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(argStr)}</span>
                  ${obs ? `<span style="color:var(--muted);font-size:0.67rem;margin-left:auto;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:110px" title="${_esc(obs)}">→ ${_esc(obs.slice(0,40))}</span>` : ''}
                </div>`;
              });
              stepsHtml = `<div style="margin-bottom:0.35rem">
                <span style="font-weight:600;font-size:0.65rem;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)">${steps.length} Steps</span>
                <div style="margin-top:0.25rem;font-size:0.7rem;font-family:monospace;border-left:2px solid var(--border);padding-left:0.4rem">${stepLines.join('')}</div>
              </div>`;
            }

            // Output summary
            let outputHtml = '';
            const so = s.structured_out;
            if (so) {
              const outLines = [];
              if (so.summary) outLines.push(so.summary.slice(0, 200));
              if (so.verdict) outLines.push(`Verdict: ${so.verdict}`);
              if (so.issues?.length) outLines.push(`Issues: ${so.issues.slice(0,3).join('; ').slice(0,150)}`);
              if (so.suggested_fixes?.length) outLines.push(`Fixes: ${so.suggested_fixes.slice(0,2).join('; ').slice(0,120)}`);
              if (so.files_changed?.length) outLines.push(`Files: ${so.files_changed.slice(0,5).join(', ')}`);
              if (so.commit_hash) outLines.push(`Commit: ${so.commit_hash.slice(0,8)}`);
              if (so.work_items?.length) outLines.push(`Work items assessed: ${so.work_items.length}`);
              if (outLines.length) {
                outputHtml = `<div style="margin-bottom:0.35rem">
                  <span style="font-weight:600;font-size:0.65rem;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)">Output</span>
                  <div style="margin-top:0.2rem;color:var(--text);font-size:0.7rem;line-height:1.4">${outLines.map(l => _esc(l)).join('<br>')}</div>
                </div>`;
              }
            } else if (s.output_preview) {
              // Strip leading "Thought:" lines to show cleaner text
              const cleaned = s.output_preview.replace(/^(Thought:.*?\n)+/m, '').trim().slice(0, 300);
              if (cleaned) {
                outputHtml = `<div style="margin-bottom:0.35rem">
                  <span style="font-weight:600;font-size:0.65rem;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)">Output</span>
                  <div style="margin-top:0.2rem;color:var(--text);font-size:0.7rem;line-height:1.4;font-style:italic">${_esc(cleaned)}</div>
                </div>`;
              }
            }

            detailHtml = `<div id="${detId}"
                style="display:none;margin-top:0.35rem;padding:0.45rem 0.55rem;
                       background:var(--surface2);border-radius:4px;border-left:3px solid ${color};
                       font-size:0.72rem;overflow:hidden">
              ${inputHtml}${stepsHtml}${outputHtml}
            </div>`;
          }

          return `<div style="border-bottom:1px solid var(--border);padding:0.3rem 0">
            <div style="display:flex;align-items:center;gap:0.35rem;color:${color};
                        ${hasDetails ? 'cursor:pointer' : ''}"
                 ${hasDetails ? `onclick="const d=document.getElementById('${detId}');if(d)d.style.display=d.style.display==='none'?'block':'none'"` : ''}>
              <span style="font-size:0.85rem;flex-shrink:0">${icon}</span>
              <span style="font-weight:600">${_esc(s.stage_key)}</span>
              <span style="font-size:0.7rem;color:var(--muted)">${_esc(s.role_name || '')}</span>
              <span style="font-size:0.68rem;color:var(--muted);margin-left:auto;white-space:nowrap">${_esc(dur)} ${_esc(toks)} ${_esc(cost)}</span>
              ${hasDetails ? `<span style="font-size:0.65rem;color:var(--muted)" title="Click to expand">▸</span>` : ''}
            </div>
            ${detailHtml}
          </div>`;
        }).join('');
      }

      if (logEl && data.stages) {
        const lines = [];
        for (const s of data.stages) {
          if (s.log_lines?.length) lines.push(...s.log_lines.slice(-3).map(l => l.text || ''));
        }
        logEl.textContent = lines.slice(-10).join('\n') || 'Running…';
        logEl.scrollTop = logEl.scrollHeight;
      }

      if (data.status === 'waiting_approval' && verdEl) {
        verdEl.style.display = 'block';
        verdEl.style.background = '#9b7ef822';
        verdEl.style.color = '#9b7ef8';
        verdEl.innerHTML = `Waiting for approval
          <div style="display:flex;gap:0.5rem;margin-top:0.5rem;justify-content:center">
            <button onclick="api.agents.approvePipelineRun('${runId}',{approved:true}).catch(()=>{})"
                    style="padding:0.25rem 0.8rem;border-radius:4px;background:#3ecf8e22;color:#3ecf8e;
                           border:1px solid #3ecf8e;cursor:pointer;font-size:0.75rem">Approve</button>
            <button onclick="api.agents.approvePipelineRun('${runId}',{approved:false}).catch(()=>{})"
                    style="padding:0.25rem 0.8rem;border-radius:4px;background:#e85d7522;color:#e85d75;
                           border:1px solid #e85d75;cursor:pointer;font-size:0.75rem">Reject</button>
          </div>`;
      }

      if (data.status === 'done' || data.status === 'error') {
        clearInterval(_ucPollTimer);
        _ucPollTimer = null;
        const verdict = data.final_verdict || data.status;
        const vColor  = verdict === 'approved' ? '#3ecf8e'
                      : verdict === 'error'    ? '#e85d75'
                      : verdict === 'rejected' ? '#f59e0b' : '#3ecf8e';
        dot.style.background = vColor;

        // Build the completion / apply UI in the verdict zone
        if (verdEl) {
          const isLinked  = data.linked_uc_id || data.linked_item_id;
          const lastDone  = [...(data.stages || [])].filter(s => s.status === 'done').pop();
          const suggested = (lastDone?.output_preview || '').slice(0, 300).trim();
          const applyTarget = data.linked_item_id ? 'Item' : 'Use Case';
          const sid = `_ps_${runId.replace(/-/g,'')}`; // summary textarea id (safe)

          // Auto-score from backend: approved=5, needs_changes=3, rejected=1, error=0
          const autoScore = typeof data.score === 'number' ? data.score : 0;

          // Render score dots: filled up to autoScore, empty after
          const scoreDots = [1,2,3,4,5].map(n =>
            `<span style="font-size:0.85rem;color:${n <= autoScore ? vColor : 'var(--border)'}">${n <= autoScore ? '●' : '○'}</span>`
          ).join('');

          // Score buttons — pre-highlight up to autoScore
          const scoreBtns = [1,2,3,4,5].map(n => {
            const active = n <= autoScore;
            return `<button data-sn="${n}" onclick="window._ucScoreSet(this,'${sid}')"
              style="width:22px;height:22px;border-radius:50%;cursor:pointer;font-size:0.62rem;
                     border:1px solid ${active ? vColor : 'var(--border)'};
                     background:${active ? vColor + '33' : 'var(--surface2)'};
                     color:${active ? vColor : 'var(--muted)'}">${n}</button>`;
          }).join('');

          verdEl.style.cssText = 'display:block;margin-top:0.5rem;flex-shrink:0';
          verdEl.innerHTML = `
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;
                        padding:0.4rem 0.55rem;background:${vColor}18;border-radius:4px;border:1px solid ${vColor}44">
              <span style="font-size:0.75rem;font-weight:700;color:${vColor}">${verdict.toUpperCase()}</span>
              <span style="display:flex;gap:1px;align-items:center" title="${autoScore}/5">${scoreDots}</span>
              <span style="font-size:0.68rem;font-weight:600;color:${vColor}">${autoScore}/5</span>
              ${data.duration_s ? `<span style="font-size:0.65rem;color:var(--muted);margin-left:auto">${data.duration_s.toFixed(0)}s · $${(data.total_cost_usd||0).toFixed(3)}</span>` : ''}
            </div>
            ${data.error ? `<div style="font-size:0.65rem;color:#e85d75;margin-bottom:0.4rem;word-break:break-word">${_esc(data.error.slice(0, 120))}</div>` : ''}
            ${isLinked ? `
              <div style="font-size:0.68rem;color:var(--muted);margin-bottom:0.25rem">
                Summary to apply (1-2 sentences):
              </div>
              <textarea id="${sid}"
                style="width:100%;min-height:64px;font-size:0.7rem;padding:0.4rem;box-sizing:border-box;
                       border:1px solid var(--border);border-radius:4px;resize:vertical;
                       background:var(--surface2);color:var(--text);font-family:inherit"
                placeholder="Write a brief summary of what was done…">${_esc(suggested.slice(0, 200))}</textarea>
              <div style="display:flex;align-items:center;gap:0.35rem;margin-top:0.4rem;flex-wrap:wrap">
                <span style="font-size:0.68rem;color:var(--muted)">Score:</span>
                ${scoreBtns}
                <span id="${sid}_score" data-v="${autoScore}"
                      style="font-size:0.68rem;color:var(--muted)">${autoScore > 0 ? autoScore+'/5' : ''}</span>
                <button onclick="window._ucApplyRun('${runId}','${sid}')"
                  style="margin-left:auto;padding:0.25rem 0.7rem;border-radius:4px;font-size:0.72rem;
                         font-weight:600;cursor:pointer;background:#3ecf8e;color:#fff;border:none">
                  Apply to ${_esc(applyTarget)}
                </button>
              </div>
            ` : `<div style="font-size:0.7rem;color:var(--muted)">Run complete — no linked item.</div>`}
          `;
        }
      }
    } catch (_e) {
      // silent poll error — keep trying
    }
  };

  _ucPollTimer = setInterval(poll, 1500);
  poll(); // immediate first poll
}

// ── Panel apply helpers ───────────────────────────────────────────────────────

window._ucScoreSet = (btn, sid) => {
  const score = parseInt(btn.dataset.sn, 10);
  const scoreEl = document.getElementById(`${sid}_score`);
  if (scoreEl) { scoreEl.dataset.v = score; scoreEl.textContent = `${score}/5`; }
  // Highlight all buttons up to selected score
  btn.closest('div').querySelectorAll('[data-sn]').forEach(b => {
    const active = parseInt(b.dataset.sn, 10) <= score;
    b.style.background    = active ? '#3ecf8e33' : 'var(--surface2)';
    b.style.borderColor   = active ? '#3ecf8e'   : 'var(--border)';
    b.style.color         = active ? '#3ecf8e'   : 'var(--muted)';
  });
};

window._ucApplyRun = async (runId, sid) => {
  const summary = document.getElementById(sid)?.value?.trim() || '';
  if (!summary) { toast('Please write a summary before applying', 'error'); return; }
  const score = parseInt(document.getElementById(`${sid}_score`)?.dataset.v || '0', 10) || null;
  try {
    await api.agents.applyPipelineRun(runId, { summary, score });
    toast('Summary applied to item/use case', 'success');
    // Invalidate UC cache so next visit shows updated summary
    _ucCacheData = null;
    _ucClosePanel();
    setTimeout(() => _loadUseCases().catch(() => {}), 300);
  } catch (e) {
    toast('Apply failed: ' + e.message, 'error');
  }
};

/** Neutral badge shown on approved use cases: "📂 12d open" */
function _openDaysBadge(approvedAt) {
  const d = _daysAgo(approvedAt);
  if (d === null) return '';
  const color = d > 30 ? '#ef4444' : d > 14 ? '#f59e0b' : '#6b7280';
  return `<span title="Open since ${approvedAt ? approvedAt.slice(0,10) : '?'}"
    style="font-size:0.65rem;color:${color};white-space:nowrap;padding:1px 5px;
    background:${color}18;border-radius:3px;border:1px solid ${color}44;line-height:1.6">📂 ${d}d open</span>`;
}

// ── Due date helpers ──────────────────────────────────────────────────────────

function _dueBadge(dueDate, startDate) {
  if (!dueDate) return '';
  const today = new Date(); today.setHours(0,0,0,0);
  const due   = new Date(dueDate + 'T00:00:00');
  const days  = Math.round((due - today) / 86400000);
  let color, label;
  if (days < 0)      { color = '#ef4444'; label = `${Math.abs(days)}d overdue`; }
  else if (days === 0){ color = '#f97316'; label = 'due today'; }
  else if (days <= 3) { color = '#f59e0b'; label = `${days}d left`; }
  else                { color = '#22c55e'; label = dueDate.slice(5); }
  const title = `Due: ${dueDate}${startDate ? ' | Start: ' + startDate : ''}`;
  return `<span class="wi-due-badge"
    style="background:${color}22;color:${color};border:1px solid ${color}44;
    border-radius:4px;padding:1px 6px;font-size:0.67rem;cursor:pointer;white-space:nowrap"
    data-action="due-pop" title="${_esc(title)}">📅 ${label}</span>`;
}

function _showDueDatePopover(anchorEl, item) {
  if (_closePop(anchorEl)) return;
  const today = new Date().toISOString().slice(0, 10);
  const isUC  = item.wi_type === 'use_case';
  const kids  = isUC ? (item.children || []).filter(c => !_isDone(c)) : [];
  const pop = document.createElement('div');
  pop.className = 'wi-wi-pop';
  pop.style.width = '260px';
  pop.innerHTML = `
    <div class="wi-wi-pop-label">Set due date${kids.length ? ` · ${kids.length} children will be capped` : ''}</div>
    <div style="display:flex;gap:0.4rem;align-items:center;margin-bottom:0.45rem">
      <input id="wi-due-days" type="number" min="1" max="730" placeholder="days"
             style="width:64px;padding:3px 5px;border:1px solid var(--border);border-radius:4px;
                    background:var(--surface);color:var(--text);font-size:0.8rem">
      <span style="color:var(--muted);font-size:0.72rem">days from today, or pick:</span>
    </div>
    <input id="wi-due-date" type="date" value="${item.due_date || ''}"
           style="width:100%;box-sizing:border-box;padding:4px 8px;
                  border:1px solid var(--accent);border-radius:4px;
                  background:var(--surface);color:var(--text);font-size:0.82rem">
    ${item.start_date ? `<div style="font-size:0.68rem;color:var(--muted);margin-top:0.3rem">
      ⚑ Start: ${item.start_date} — will reset to today on save</div>` : ''}
    <div style="display:flex;gap:0.4rem;margin-top:0.5rem">
      <button id="wi-due-ok" class="wi-btn wi-btn-approve" style="flex:1">Set</button>
      ${item.due_date ? `<button id="wi-due-clear" class="wi-btn wi-btn-ghost" title="Remove due date">✕ Clear</button>` : ''}
      <button id="wi-due-cancel" class="wi-btn wi-btn-ghost">Cancel</button>
    </div>
  `;
  _popupAt(pop, anchorEl);

  const daysInp = pop.querySelector('#wi-due-days');
  const dateInp = pop.querySelector('#wi-due-date');

  daysInp.addEventListener('input', () => {
    const d = parseInt(daysInp.value, 10);
    if (d > 0) {
      const t = new Date(); t.setDate(t.getDate() + d);
      dateInp.value = t.toISOString().slice(0, 10);
    }
  });
  dateInp.addEventListener('input', () => {
    if (dateInp.value) {
      const diff = Math.round((new Date(dateInp.value + 'T00:00:00') - new Date(today + 'T00:00:00')) / 86400000);
      daysInp.value = diff > 0 ? diff : '';
    }
  });

  const _close = () => pop.remove();

  const _apply = async (newDue) => {
    _close();
    if (item.start_date && newDue) {
      if (!confirm(`Setting due date will reset start date to today (${today}).\nContinue?`)) return;
    }
    try {
      const r = await api.wi.update(_project, item.id, { due_date: newDue || null });
      if (r.error) { toast(`Error: ${r.error}`, 'error'); return; }
      toast(r.cascaded_children
        ? `Due date set — ${r.cascaded_children} children updated`
        : 'Due date updated', 'success');
      await _reloadCurrent();
    } catch (err) { toast(`Failed: ${err.message}`, 'error'); }
  };

  pop.querySelector('#wi-due-ok').addEventListener('click', () => _apply(dateInp.value));
  pop.querySelector('#wi-due-clear')?.addEventListener('click', () => _apply(null));
  pop.querySelector('#wi-due-cancel').addEventListener('click', _close);
  dateInp.addEventListener('keydown', e => {
    if (e.key === 'Enter') _apply(dateInp.value);
    if (e.key === 'Escape') _close();
  });
  setTimeout(() => {
    document.addEventListener('click', e => { if (!pop.contains(e.target)) pop.remove(); }, { once: true });
  }, 150);
}

// ── Stats bar ─────────────────────────────────────────────────────────────────

function _renderStats() {
  const el = document.getElementById('wi-stats-bar');
  if (!el) return;

  // Pending mrr counts (unclassified events in mirror tables)
  const mrr = _mrrCounts || {};
  const mrrPills = mrr.pending_total > 0 ? [
    { label: 'Unclassified',
      val: `${mrr.pending_total} (${mrr.pending_prompts || 0}P / ${mrr.pending_commits || 0}C / ${mrr.pending_messages || 0}M / ${mrr.pending_items || 0}I)`,
      color: '#f97316',
      title: `${mrr.pending_prompts || 0} prompts, ${mrr.pending_commits || 0} commits, ${mrr.pending_messages || 0} messages, ${mrr.pending_items || 0} items not yet classified` },
  ] : [];

  if (_tab === 'use_cases') {
    const totalUcs      = _ucItems.length;
    const totalItems    = _ucItems.reduce((s, u) => s + u.stats.total_children, 0);
    const approvedItems = _ucItems.reduce((s, u) => s + u.stats.approved_children, 0);
    const pendingItems  = _ucItems.reduce((s, u) => s + u.stats.pending_children, 0);
    const totalEvents   = _ucItems.reduce((s, u) => s + u.stats.total_events, 0);
    // No mrrPills in use_cases tab — all items here are classified
    const pills = [
      { label: 'Use Cases', val: totalUcs,      color: '#06b6d4' },
      { label: 'Items',     val: totalItems,    color: '#22c55e' },
      { label: 'Approved',  val: approvedItems, color: '#22c55e' },
      { label: 'Pending',   val: pendingItems,  color: '#f59e0b' },
      { label: 'Events',    val: totalEvents,   color: '#8b5cf6' },
      ...(_stats.overdue > 0 ? [{ label: 'Overdue', val: _stats.overdue, color: '#ef4444' }] : []),
    ];
    el.innerHTML = pills.map(p => `
      <div class="wi-stats-pill"${p.title ? ` title="${_esc(p.title)}"` : ''}>
        <div class="wi-stats-dot" style="background:${p.color}"></div>
        <span style="color:var(--muted)">${p.label}:</span>
        <strong style="color:var(--text)">${p.val}</strong>
      </div>
    `).join('');
    return;
  }

  const s = _stats;
  const pills = [
    ...mrrPills,
    { label: 'Pending',      val: s.pending      || 0, color: '#f59e0b' },
    { label: 'Approved',     val: s.approved     || 0, color: '#22c55e' },
    { label: 'Rejected',     val: s.rejected     || 0, color: '#6b7280' },
    { label: 'Bugs',         val: s.bugs         || 0, color: '#ef4444' },
    { label: 'Features',     val: s.features     || 0, color: '#22c55e' },
    { label: 'Tasks',        val: s.tasks        || 0, color: '#3b82f6' },
    { label: 'Policies',     val: s.policies     || 0, color: '#8b5cf6' },
    { label: 'Requirements', val: s.requirements || 0, color: '#f59e0b' },
    ...(s.overdue > 0 ? [{ label: 'Overdue', val: s.overdue, color: '#ef4444' }] : []),
  ];
  el.innerHTML = pills.map(p => `
    <div class="wi-stats-pill"${p.title ? ` title="${_esc(p.title)}"` : ''}>
      <div class="wi-stats-dot" style="background:${p.color}"></div>
      <span style="color:var(--muted)">${p.label}:</span>
      <strong style="color:var(--text)">${p.val}</strong>
    </div>
  `).join('');
}

// ── Use Case helpers ──────────────────────────────────────────────────────────

function _findInUcItems(id) {
  for (const uc of _ucItems) {
    if (uc.id === id) return uc;
    const found = (uc.children || []).find(c => c.id === id);
    if (found) return found;
  }
  return null;
}

function _getDescendants(itemId, allItems) {
  const result = new Set();
  const queue  = [itemId];
  while (queue.length) {
    const cur = queue.shift();
    const children = allItems.filter(i => i.wi_parent_id === cur);
    for (const c of children) {
      if (!result.has(c.id)) { result.add(c.id); queue.push(c.id); }
    }
  }
  return result;
}

function _openSummarisePanel(ucId, draftResult) {
  document.getElementById('wi-md-panel')?.remove();
  const panel = document.createElement('div');
  panel.id = 'wi-md-panel';
  panel.style.cssText = `position:fixed;top:0;right:0;width:420px;height:100vh;
    background:var(--bg2);border-left:1px solid var(--border);z-index:200;
    display:flex;flex-direction:column;overflow:hidden;box-shadow:-4px 0 20px rgba(0,0,0,0.3)`;

  const { new_summary, in_progress_count, completed_count, snapshot } = draftResult;

  const ipItems = snapshot.slice(0, in_progress_count);
  const doneItems = snapshot.slice(in_progress_count);

  function itemLine(s) {
    const meta = _typeMeta(s.wi_type || 'task');
    return `<div style="padding:0.2rem 0;font-size:0.77rem">
      ${meta.icon} ${_esc(s.name || '(unnamed)')}
      ${s.wi_id ? `<span style="color:var(--muted);font-size:0.7rem"> ${s.wi_id}</span>` : ''}
    </div>`;
  }

  panel.innerHTML = `
    <div style="padding:0.7rem 1rem;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:0.5rem">
      <strong style="font-size:0.85rem;flex:1">AI Draft Summary</strong>
      <button id="wi-sum-apply" class="wi-btn wi-btn-approve" style="font-size:0.75rem">✓ Apply</button>
      <button id="wi-sum-discard" class="wi-btn wi-btn-ghost" style="font-size:0.75rem">✗ Discard</button>
      <button id="wi-md-close" style="background:none;border:none;cursor:pointer;color:var(--muted);font-size:1rem">✕</button>
    </div>
    <div style="flex:1;overflow-y:auto;padding:0.8rem 1rem">
      <div style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;margin-bottom:0.3rem">New Summary</div>
      <div style="font-size:0.8rem;color:var(--text2);line-height:1.5;border-left:3px solid var(--accent);
                  padding-left:0.5rem;margin-bottom:1rem">${_esc(new_summary)}</div>
      ${ipItems.length ? `
        <div style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;margin-bottom:0.3rem">
          In Progress (${ipItems.length})
        </div>
        <div style="margin-bottom:0.8rem">${ipItems.map(itemLine).join('')}</div>
      ` : ''}
      ${doneItems.length ? `
        <div style="font-size:0.72rem;font-weight:700;color:var(--muted);text-transform:uppercase;margin-bottom:0.3rem">
          Completed (${doneItems.length})
        </div>
        <div>${doneItems.map(itemLine).join('')}</div>
      ` : ''}
    </div>
  `;

  document.body.appendChild(panel);

  panel.querySelector('#wi-md-close').onclick    = () => panel.remove();
  panel.querySelector('#wi-sum-discard').onclick  = () => panel.remove();
  panel.querySelector('#wi-sum-apply').onclick    = async () => {
    try {
      await api.wi.versions.apply(_project, ucId, draftResult.version_id);
      toast('Version applied', 'success');
      panel.remove();
      await _loadUseCases();
    } catch (err) { toast(`Apply failed: ${err.message}`, 'error'); }
  };
}

function _openVersionPanel(uc) {
  document.getElementById('wi-md-panel')?.remove();
  const panel = document.createElement('div');
  panel.id = 'wi-md-panel';
  panel.style.cssText = `position:fixed;top:0;right:0;width:420px;height:100vh;
    background:var(--bg2);border-left:1px solid var(--border);z-index:200;
    display:flex;flex-direction:column;overflow:hidden;box-shadow:-4px 0 20px rgba(0,0,0,0.3)`;

  panel.innerHTML = `
    <div style="padding:0.7rem 1rem;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:0.5rem">
      <strong style="font-size:0.85rem;flex:1">Versions — ${_esc(uc.name)}</strong>
      <button id="wi-ver-save" class="wi-btn wi-btn-ghost" style="font-size:0.75rem">+ Save current</button>
      <button id="wi-md-close" style="background:none;border:none;cursor:pointer;color:var(--muted);font-size:1rem">✕</button>
    </div>
    <div id="wi-ver-list" style="flex:1;overflow-y:auto;padding:0.6rem 1rem">
      <div style="color:var(--muted);font-size:0.8rem">Loading…</div>
    </div>
  `;
  document.body.appendChild(panel);

  panel.querySelector('#wi-md-close').onclick = () => panel.remove();

  async function loadVersions() {
    const listEl = panel.querySelector('#wi-ver-list');
    try {
      const data = await api.wi.versions.list(_project, uc.id);
      const versions = data.versions || [];
      if (!versions.length) {
        listEl.innerHTML = `<div style="color:var(--muted);font-size:0.8rem">No versions yet.</div>`;
        return;
      }
      listEl.innerHTML = versions.map(v => {
        const statusColor = v.status === 'draft' ? '#f59e0b' : v.status === 'active' ? '#22c55e' : '#6b7280';
        const dt = v.created_at ? v.created_at.slice(0, 16).replace('T', ' ') : '';
        return `
          <div style="border:1px solid var(--border);border-radius:6px;padding:0.6rem 0.8rem;margin-bottom:0.5rem">
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.25rem">
              <strong style="font-size:0.82rem">v${v.version_num}</strong>
              <span style="font-size:0.68rem;color:${statusColor};font-weight:600;text-transform:uppercase">${v.status}</span>
              <span style="font-size:0.7rem;color:var(--muted);flex:1">by ${_esc(v.created_by)}</span>
              <span style="font-size:0.7rem;color:var(--muted)">${dt}</span>
            </div>
            <div style="font-size:0.75rem;color:var(--text2);margin-bottom:0.35rem">
              ${v.item_count} items${v.summary ? ' · ' + _esc(v.summary.slice(0, 80)) + (v.summary.length > 80 ? '…' : '') : ''}
            </div>
            <button class="wi-btn wi-btn-ghost wi-ver-apply" data-vid="${v.id}"
                    style="font-size:0.72rem">Apply</button>
          </div>
        `;
      }).join('');

      listEl.querySelectorAll('.wi-ver-apply').forEach(btn => {
        btn.onclick = async () => {
          btn.disabled = true; btn.textContent = '…';
          try {
            await api.wi.versions.apply(_project, uc.id, btn.dataset.vid);
            toast('Version applied', 'success');
            panel.remove();
            await _loadUseCases();
          } catch (err) { toast(`Apply failed: ${err.message}`, 'error'); btn.disabled = false; btn.textContent = 'Apply'; }
        };
      });
    } catch (err) {
      listEl.innerHTML = `<div style="color:#ef4444;font-size:0.8rem">Error: ${_esc(err.message)}</div>`;
    }
  }

  panel.querySelector('#wi-ver-save').onclick = async () => {
    try {
      await api.wi.versions.create(_project, uc.id);
      toast('Version saved', 'success');
      await loadVersions();
    } catch (err) { toast(`Save failed: ${err.message}`, 'error'); }
  };

  loadVersions();
}

function _showParentPopover(anchorEl, itemId, ucId) {
  document.querySelectorAll('.wi-popover').forEach(p => p.remove());

  const uc       = _ucItems.find(u => u.id === ucId);
  const allItems = uc ? (uc.children || []) : [];
  const desc     = _getDescendants(itemId, allItems);
  const candidates = allItems.filter(i => i.id !== itemId && !desc.has(i.id));

  const TYPE_COLORS = {
    bug:         { bg: '#fee2e2', text: '#dc2626' },
    feature:     { bg: '#dcfce7', text: '#16a34a' },
    task:        { bg: '#dbeafe', text: '#1d4ed8' },
    policy:      { bg: '#ede9fe', text: '#7c3aed' },
    requirement: { bg: '#fef3c7', text: '#b45309' },
    use_case:    { bg: '#cffafe', text: '#0e7490' },
  };

  const pop = document.createElement('div');
  pop.className = 'wi-popover';
  pop.style.cssText = `position:fixed;background:var(--surface);border:1px solid var(--border);
    border-radius:8px;padding:0.4rem;min-width:240px;z-index:300;
    box-shadow:0 6px 24px rgba(0,0,0,0.35);max-height:300px;overflow-y:auto`;

  const rect = anchorEl.getBoundingClientRect();
  pop.style.top  = `${rect.bottom + 4}px`;
  pop.style.left = `${Math.min(rect.left, window.innerWidth - 260)}px`;

  function optionEl(label, value, type) {
    const col = type ? TYPE_COLORS[type] : null;
    const d = document.createElement('div');
    d.style.cssText = `padding:0.32rem 0.6rem;cursor:pointer;border-radius:5px;font-size:0.79rem;
      margin-bottom:2px;
      background:${col ? col.bg : 'var(--surface2)'};
      color:${col ? col.text : 'var(--text)'}`;
    d.innerHTML = label;
    d.onmouseenter = () => d.style.opacity = '0.75';
    d.onmouseleave = () => d.style.opacity = '1';
    d.onclick = async () => {
      pop.remove();
      try {
        await api.wi.update(_project, itemId, { wi_parent_id: value });
        await _loadUseCases();
      } catch (err) { toast(`Re-parent failed: ${err.message}`, 'error'); }
    };
    return d;
  }

  // Header label
  const lbl = document.createElement('div');
  lbl.style.cssText = 'font-size:0.68rem;font-weight:700;color:var(--muted);text-transform:uppercase;padding:0.2rem 0.5rem 0.4rem;letter-spacing:0.04em';
  lbl.textContent = 'Move item under…';
  pop.appendChild(lbl);

  if (ucId) pop.appendChild(optionEl('↑ &nbsp;Direct child of use case', ucId, 'use_case'));
  for (const c of candidates) {
    const depth  = c.depth ?? 0;
    const indent = depth > 0 ? `<span style="opacity:0.4">${'&nbsp;&nbsp;'.repeat(depth)}└ </span>` : '';
    const meta   = _typeMeta(c.wi_type);
    const idBadge = c.wi_id ? `<span style="opacity:0.5;font-size:0.68rem;margin-left:0.3rem">${c.wi_id}</span>` : '';
    pop.appendChild(optionEl(`${indent}${meta.icon} ${_esc(c.name)}${idBadge}`, c.id, c.wi_type));
  }

  document.body.appendChild(pop);
  const close = (ev) => { if (!pop.contains(ev.target)) { pop.remove(); document.removeEventListener('mousedown', close); } };
  setTimeout(() => document.addEventListener('mousedown', close), 0);
}

// ── Filter chips ──────────────────────────────────────────────────────────────

function _renderFilterChips() {
  const el = document.getElementById('wi-filter-chips');
  if (!el) return;
  // use_case is excluded — items are always shown grouped under UCs
  const types = ['bug', 'feature', 'task', 'policy', 'requirement'];
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

  // Work Items tab: show only pending (AI*) use cases — approved ones live in Use Cases tab
  const allUcIds = new Set(_allItems.filter(i => i.wi_type === 'use_case' || i.item_level === 3).map(u => u.id));
  const useCases = _allItems.filter(i =>
    (i.wi_type === 'use_case' || i.item_level === 3) &&
    (!i.wi_id || i.wi_id.startsWith('AI'))
  );

  // Apply type filter to children only; UC headers are always preserved
  const allChildren = _allItems.filter(i => i.wi_parent_id && allUcIds.has(i.wi_parent_id));
  const children    = _filter ? allChildren.filter(c => c.wi_type === _filter) : allChildren;
  // When filter active, only show UCs that have at least one matching child
  const visibleUcIds = _filter ? new Set(children.map(c => c.wi_parent_id).filter(Boolean)) : allUcIds;
  const visibleUCs  = _filter ? useCases.filter(u => visibleUcIds.has(u.id)) : useCases;

  // Direct UC children IDs
  const childIds  = new Set(allChildren.map(c => c.id));
  // Sub-items: children of non-UC items (depth 1+); rendered indented below their parent
  const allSubItems  = _allItems.filter(i => i.wi_parent_id && childIds.has(i.wi_parent_id) && !allUcIds.has(i.id));
  const subItemIds   = new Set(allSubItems.map(s => s.id));
  // Orphans: not UC, not direct child, not sub-item
  const orphans   = _allItems.filter(i => !allUcIds.has(i.id) && !childIds.has(i.id) && !subItemIds.has(i.id));
  const visibleOrphans = _filter ? orphans.filter(o => o.wi_type === _filter) : orphans;

  if (!visibleUCs.length && !visibleOrphans.length) {
    const mrrTotal = (_mrrCounts.pending_prompts || 0) + (_mrrCounts.pending_commits || 0);
    el.innerHTML = `
      <div style="color:var(--muted);text-align:center;padding:3rem 2rem;font-size:0.85rem;max-width:480px;margin:0 auto">
        ${_filter
          ? `<div>No <strong>${_filter}</strong> items pending approval.</div>`
          : `<div style="font-size:1.1rem;margin-bottom:0.75rem">No pending items</div>
             <div style="font-size:0.82rem;line-height:1.6">
               Approved use cases are in the <strong>Use Cases</strong> tab →<br><br>
               ${mrrTotal > 0
                 ? `Click <button onclick="document.getElementById('wi-classify-btn').click()"
                          style="padding:4px 12px;border:1px solid var(--accent);border-radius:5px;
                                 background:var(--accent);color:#fff;cursor:pointer;font-size:0.82rem">
                      ↻ Classify
                    </button>
                    to generate AI-suggested use cases from
                    <strong>${_mrrCounts.pending_prompts||0} prompts</strong> +
                    <strong>${_mrrCounts.pending_commits||0} commits</strong>.`
                 : 'All events have been classified.'
               }
             </div>`
        }
      </div>`;
    return;
  }

  let html = '';

  // Render use_case groups with their (filtered) children
  for (const uc of visibleUCs) {
    // Sort: done items last, then by user_importance DESC
    const ucChildren = children
      .filter(c => c.wi_parent_id === uc.id)
      .sort((a, b) => {
        const aDone = _isDone(a) ? 1 : 0;
        const bDone = _isDone(b) ? 1 : 0;
        if (aDone !== bDone) return aDone - bDone; // done items last
        return (b.user_importance ?? b.score_importance ?? 0) -
               (a.user_importance ?? a.score_importance ?? 0); // higher importance first
      });
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
            ${ucChildren.length ? ucChildren.map((c, idx) => {
                const subs = allSubItems.filter(s => s.wi_parent_id === c.id);
                const subHtml = subs.map(s =>
                  `<div style="margin-left:1.4rem;border-left:2px solid var(--border)">${_renderItemCard(s)}</div>`
                ).join('');
                return _renderItemCard(c, idx + 1) + subHtml;
              }).join('') : `
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
  if (visibleOrphans.length) {
    html += `
      <div class="wi-orphan-zone">
        <div class="wi-orphan-zone-label">
          ⚠ ${visibleOrphans.length} unlinked item${visibleOrphans.length !== 1 ? 's' : ''} — drag to a use case above
        </div>
        <div class="wi-drop-zone" data-uc-id="__none__" style="min-height:0">
          ${visibleOrphans.map(i => _renderItemCard(i)).join('')}
        </div>
      </div>
    `;
  }

  el.innerHTML = html || `<div style="color:var(--muted);text-align:center;padding:3rem">No items match the current filter.</div>`;
  _attachDragListeners();
}

function _renderItemCard(item, rank) {
  const meta = _typeMeta(item.wi_type);
  const isPending = !item.wi_id || item.wi_id.startsWith('AI');
  const st = _itemStatus(item);
  const isDone = st.cls === 'wi-s-done';
  const mrr = item.mrr_ids || {};
  const mrrChips = [
    mrr.prompts?.length  ? `<span class="wi-mrr-chip">Prompts: ${mrr.prompts.length}</span>`   : '',
    mrr.commits?.length  ? `<span class="wi-mrr-chip">Commits: ${mrr.commits.length}</span>`   : '',
    mrr.messages?.length ? `<span class="wi-mrr-chip">Messages: ${mrr.messages.length}</span>` : '',
    mrr.items?.length    ? `<span class="wi-mrr-chip">Items: ${mrr.items.length}</span>`        : '',
  ].filter(Boolean).join('');

  return `
    <div class="wi-card${isDone ? ' wi-card-done' : ''}" draggable="true" data-item-id="${item.id}">
      <div class="wi-card-header" title="Click header to expand">

        <!-- Priority rank -->
        ${rank != null ? `<span class="wi-rank-badge${isDone ? ' wi-rank-done' : ''}" title="Priority #${rank}">#${rank}</span>` : ''}

        <!-- Type badge + ▾ button to change type -->
        <span class="wi-type-badge ${meta.cls}">${meta.icon} ${meta.label}</span>
        <button class="wi-edit-arrow" data-action="type-pop"
                data-id="${item.id}" data-type="${item.wi_type}"
                title="Change type">▾</button>

        <!-- Name + ▾ to rename -->
        <span class="wi-name${isDone ? ' wi-name-done' : ''}">${isDone ? '✓ ' : ''}${_esc(item.name || '(unnamed)')}</span>
        <button class="wi-edit-arrow" data-action="rename-pop"
                data-id="${item.id}" data-current-name="${_esc(item.name || '')}" data-is-uc="false"
                title="Rename item">▾</button>

        <!-- Status badge + ▾ button to change status -->
        <span class="wi-status-badge ${st.cls}">${st.label}</span>
        <button class="wi-edit-arrow" data-action="status-pop"
                data-id="${item.id}" data-score="${_statusNum(item)}"
                title="Change status">▾</button>

        <!-- ID + waiting badge for pending items -->
        ${isPending
          ? `<span class="wi-pending">${_esc(item.wi_id || 'pending')}</span>
             ${_waitingBadge(item.created_at)}`
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
        <!-- AI scores (read-only indicators from classification) -->
        <div class="wi-scores" style="margin-top:0.35rem">
          <span title="AI importance score (0–5)">Importance: ${_scorePips(item.score_importance, '#3b82f6')}</span>
          <span title="AI completion score (0–5)">Completion: ${_scorePips(item.score_status, '#22c55e')}</span>
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

function _hotspotBadge(hotspots) {
  if (!hotspots || !hotspots.length) return '';
  const top = hotspots[0];
  const tip = hotspots.map(h =>
    `${h.file_path} (commits:${h.commit_count} bugs:${h.bug_commit_count} lines:${h.current_lines})`
  ).join('\n');
  return `<span class="wi-hotspot-badge" title="${tip}">🔥 ${hotspots.length} hotspot${hotspots.length > 1 ? 's' : ''}</span>`;
}

// ── Use Cases standalone view (separate sidebar entry) ────────────────────────

export function destroyUseCases() {
  if (_classifyPoller) { clearInterval(_classifyPoller); _classifyPoller = null; }
  if (_mdPanel)        { _mdPanel.remove(); _mdPanel = null; }
}

export async function renderUseCases(container, projectName) {
  destroyUseCases();
  _project = projectName || state.currentProject?.name || '';
  _tab     = 'use_cases';

  // Use cached data when re-entering the same project — renders instantly, no network call
  const hasFreshCache = _ucCacheData !== null && _ucCacheData.length > 0 && _ucCacheProject === _project;
  if (hasFreshCache) {
    _ucItems = _ucCacheData;
  } else {
    _ucItems = [];
  }

  const loadingPlaceholder = hasFreshCache ? '' : `
    <div style="color:var(--muted);text-align:center;padding:3rem;font-size:0.82rem">
      Loading use cases…
    </div>`;

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- ── Toolbar ── -->
      <div style="padding:0.65rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.75rem;flex-shrink:0">
        <strong style="font-size:0.9rem;color:var(--text)">◻ Use Cases</strong>
        <span style="color:var(--muted);font-size:0.78rem">Approved use cases and their items</span>
        <span style="flex:1"></span>
        <span id="wi-status" style="font-size:0.72rem;color:var(--muted)"></span>
        <span id="wi-hook-badge" style="display:none;font-size:0.72rem;padding:0.2rem 0.55rem;
              border-radius:10px;background:#7c3aed22;color:#c084fc;border:1px solid #7c3aed44;
              cursor:default" title="No prompts received recently"></span>
        <button id="wi-undo-btn" class="btn btn-ghost btn-sm" disabled
                style="opacity:0.4" title="Nothing to undo">↩ Undo</button>
        <button id="wi-refresh-btn" class="btn btn-ghost btn-sm" title="Reload use cases">⟳ Refresh</button>
      </div>

      <!-- ── Stats bar ── -->
      <div id="wi-stats-bar" style="padding:0.55rem 1.25rem;background:var(--surface);
                border-bottom:1px solid var(--border);flex-shrink:0;
                display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap">
        <span style="color:var(--muted);font-size:0.72rem">${hasFreshCache ? '' : 'Loading…'}</span>
      </div>

      <!-- ── List ── -->
      <div id="wi-list" style="flex:1;overflow-y:auto;padding:1rem 1.25rem">
        ${loadingPlaceholder}
      </div>
    </div>

    ${_sharedStyles()}
  `;

  _setupEvents(container);
  _updateUndoBtn();

  if (hasFreshCache) {
    // Render immediately from cache; stats + list appear with no network wait
    _renderStats();
    _renderUseCases();
  } else {
    await _loadUseCases();
  }
  _checkHookHealth();
}

// Allow settings.js to invalidate the pipeline name caches after mode/activation changes
window._invalidatePipelineCache = () => {
  _ucPipeNamesUC   = null;
  _ucPipeNamesItem = null;
};

// ── Completed Use Cases view ───────────────────────────────────────────────

export async function renderCompleted(container, projectName) {
  const proj = projectName || state.currentProject?.name || '';
  container.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">
      <div style="padding:0.65rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.75rem;flex-shrink:0">
        <strong style="font-size:0.9rem;color:var(--text)">✓ Completed</strong>
        <span style="color:var(--muted);font-size:0.78rem">Completed use cases</span>
        <span style="flex:1"></span>
        <button id="completed-refresh" class="btn btn-ghost btn-sm" title="Refresh">⟳</button>
      </div>
      <div id="completed-list" style="flex:1;overflow-y:auto;padding:1rem 1.25rem">
        <div style="color:var(--muted);text-align:center;padding:3rem">Loading…</div>
      </div>
    </div>
    ${_sharedStyles()}
  `;

  document.getElementById('completed-refresh')?.addEventListener('click', () => _loadCompleted());

  async function _loadCompleted() {
    const listEl = document.getElementById('completed-list');
    if (!listEl) return;
    try {
      const data = await api.wi.completed(proj);
      const ucs  = data.use_cases || [];

      if (!ucs.length) {
        listEl.innerHTML = `<div style="color:var(--muted);text-align:center;padding:3rem;font-size:0.82rem">
          No completed use cases yet.<br>
          <span style="font-size:0.75rem">Complete a use case from the <strong>Use Cases</strong> tab when all its items are done.</span>
        </div>`;
        return;
      }

      let html = '';
      for (const uc of ucs) {
        const startDate  = uc.start_date   ? uc.start_date.slice(0,10)   : '—';
        const doneDate   = uc.completed_at ? uc.completed_at.slice(0,10) : '—';
        const totalDays  = uc.total_days != null ? `${uc.total_days}d` : '—';

        html += `
          <div style="background:var(--surface);border:1px solid var(--border);border-left:3px solid #22c55e;
                      border-radius:var(--radius);margin-bottom:0.75rem;overflow:hidden"
               data-uc-id="${uc.id}">
            <div style="display:flex;align-items:center;gap:0.5rem;padding:0.55rem 0.9rem;
                        border-bottom:1px solid var(--border)">
              <span style="font-size:0.6rem;font-weight:700;color:#22c55e;letter-spacing:0.05em;
                           background:#22c55e18;border:1px solid #22c55e33;border-radius:3px;
                           padding:1px 5px">✓ DONE</span>
              <span style="font-size:0.72rem;color:var(--muted);font-family:monospace">${_esc(uc.wi_id || '')}</span>
              <span style="font-weight:600;font-size:0.85rem;color:var(--text)">${_esc(uc.name || '')}</span>
              <span style="flex:1"></span>
              <span style="font-size:0.7rem;color:var(--muted);display:flex;gap:1rem;align-items:center">
                <span title="Start date">⚑ ${startDate}</span>
                <span title="Completed date">✓ ${doneDate}</span>
                <span title="Total days" style="font-weight:600;color:var(--text)">⏱ ${totalDays}</span>
              </span>
              ${uc.md_path ? `<button class="wi-btn wi-btn-ghost" style="font-size:0.72rem"
                      data-action="view-md" data-path="${_esc(uc.md_path)}" data-id="${uc.id}">📋 MD</button>` : ''}
              <button class="wi-btn wi-btn-ghost" style="font-size:0.72rem"
                      data-action="reopen-uc" data-id="${uc.id}" title="Move back to Use Cases">↩ Reopen</button>
            </div>
            ${uc.summary ? `
              <div style="padding:0.5rem 0.9rem;font-size:0.79rem;color:var(--text2);line-height:1.5">
                ${_esc(uc.summary)}
              </div>` : ''}
          </div>`;
      }
      listEl.innerHTML = html;

      listEl.querySelectorAll('[data-action="reopen-uc"]').forEach(btn => {
        btn.addEventListener('click', async () => {
          const ucId = btn.dataset.id;
          btn.disabled = true;
          try {
            const r = await api.wi.reopen(proj, ucId);
            if (r.error) { toast(`Error: ${r.error}`, 'error'); btn.disabled = false; return; }
            toast('Use case reopened — now visible in Use Cases tab', 'success');
            _loadCompleted();
          } catch (err) { toast(`Failed: ${err.message}`, 'error'); btn.disabled = false; }
        });
      });

      listEl.querySelectorAll('[data-action="view-md"]').forEach(btn => {
        btn.addEventListener('click', () => {
          if (window._nav) window._nav('documents', { openFile: btn.dataset.path });
        });
      });

    } catch (err) {
      const listEl = document.getElementById('completed-list');
      if (listEl) listEl.innerHTML = `<div style="color:var(--muted);text-align:center;padding:2rem">Error: ${_esc(err.message)}</div>`;
    }
  }

  await _loadCompleted();
}
