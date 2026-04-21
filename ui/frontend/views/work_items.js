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

// ── Type config ──────────────────────────────────────────────────────────────

const _TYPE = {
  use_case: { icon: '◻',  label: 'Use Case',  color: '#06b6d4', cls: 'wi-type-uc'   },
  feature:  { icon: '⚡', label: 'Feature',   color: '#22c55e', cls: 'wi-type-feat' },
  bug:      { icon: '🐛', label: 'Bug',       color: '#ef4444', cls: 'wi-type-bug'  },
  task:     { icon: '✓',  label: 'Task',      color: '#3b82f6', cls: 'wi-type-task' },
  policy:   { icon: '⚑', label: 'Policy',    color: '#8b5cf6', cls: 'wi-type-pol'  },
};

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
      }
      .wi-uc-label {
        font-size:0.75rem;font-weight:800;text-transform:uppercase;
        letter-spacing:.05em;color:var(--accent);
      }
      .wi-uc-children {
        border:1px solid var(--border);border-top:none;
        border-radius:0 0 var(--radius) var(--radius);
        overflow:hidden;
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

    // Expand/collapse card body
    const header = e.target.closest('.wi-card-header');
    if (header) {
      const body = header.nextElementSibling;
      if (body?.classList.contains('wi-card-body')) {
        body.classList.toggle('collapsed');
        const arrow = header.querySelector('.wi-arrow');
        if (arrow) arrow.textContent = body.classList.contains('collapsed') ? '▶' : '▼';
      }
    }
  });
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
    { label: 'Pending',  val: s.pending  || 0, color: '#f59e0b' },
    { label: 'Approved', val: s.approved || 0, color: '#22c55e' },
    { label: 'Rejected', val: s.rejected || 0, color: '#6b7280' },
    { label: 'Bugs',     val: s.bugs     || 0, color: '#ef4444' },
    { label: 'Features', val: s.features || 0, color: '#22c55e' },
    { label: 'Tasks',    val: s.tasks    || 0, color: '#3b82f6' },
    { label: 'Policies', val: s.policies || 0, color: '#8b5cf6' },
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
  const types = ['bug', 'feature', 'task', 'policy', 'use_case'];
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
    const pendingChildren = ucChildren.filter(c => !c.wi_id);
    html += `
      <div class="wi-uc-group">
        <div class="wi-uc-header">
          <span class="wi-uc-label">◻ Use Case</span>
          <span style="font-size:0.85rem;font-weight:700;color:var(--text);flex:1">${_esc(uc.name || uc.id)}</span>
          ${uc.wi_id ? `<span class="wi-id">${_esc(uc.wi_id)}</span>` : '<span class="wi-pending">pending</span>'}
          ${!uc.wi_id ? `
            <button class="wi-btn wi-btn-approve" data-action="approve" data-id="${uc.id}" title="Approve use case">✓</button>
            <button class="wi-btn wi-btn-reject"  data-action="reject"  data-id="${uc.id}" title="Reject">✗</button>
          ` : ''}
          ${pendingChildren.length > 0 ? `
            <button class="wi-btn wi-btn-approve" data-action="approve-all" data-parent-id="${uc.id}" title="Approve all children">✓ All (${pendingChildren.length})</button>
          ` : ''}
        </div>
        <div class="wi-uc-children">
          ${ucChildren.length ? ucChildren.map(c => _renderItemCard(c)).join('') : `
            <div style="padding:0.75rem 0.9rem;color:var(--muted);font-size:0.78rem">No child items</div>
          `}
        </div>
      </div>
    `;
  }

  // Render orphaned items (no parent use_case)
  if (orphans.length) {
    html += orphans.map(i => _renderItemCard(i)).join('');
  }

  el.innerHTML = html || `<div style="color:var(--muted);text-align:center;padding:3rem">No items match the current filter.</div>`;
}

function _renderItemCard(item) {
  const meta = _typeMeta(item.wi_type);
  const isPending = !item.wi_id;
  const mrr = item.mrr_ids || {};
  const mrrCounts = [
    mrr.prompts?.length  ? `P:${mrr.prompts.length}`   : null,
    mrr.commits?.length  ? `C:${mrr.commits.length}`   : null,
    mrr.messages?.length ? `M:${mrr.messages.length}`  : null,
    mrr.items?.length    ? `I:${mrr.items.length}`      : null,
  ].filter(Boolean);

  return `
    <div class="wi-card">
      <div class="wi-card-header" title="Click to expand">
        <span class="wi-type-badge ${meta.cls}">${meta.icon} ${meta.label}</span>
        <span class="wi-name">${_esc(item.name || '(unnamed)')}</span>
        ${item.wi_id
          ? `<span class="wi-id">${_esc(item.wi_id)}</span>`
          : `<span class="wi-pending">pending</span>`
        }
        <div class="wi-actions">
          <span class="wi-arrow" style="font-size:0.65rem;color:var(--muted)">▼</span>
          ${isPending ? `
            <button class="wi-btn wi-btn-approve" data-action="approve" data-id="${item.id}" title="Approve">✓</button>
            <button class="wi-btn wi-btn-reject"  data-action="reject"  data-id="${item.id}" title="Reject">✗</button>
          ` : ''}
        </div>
      </div>
      <div class="wi-card-body collapsed">
        ${item.summary ? `<div class="wi-summary">${_esc(item.summary)}</div>` : ''}
        ${item.deliveries ? `<div class="wi-deliveries">✓ ${_esc(item.deliveries)}</div>` : ''}
        <div class="wi-scores">
          <div>Importance: ${_scorePips(item.score_importance, '#f59e0b')}</div>
          <div>Status: ${_scorePips(item.score_status, '#22c55e')}</div>
          ${item.delivery_type ? `<div style="color:var(--muted)">${_esc(item.delivery_type)}</div>` : ''}
        </div>
        ${mrrCounts.length ? `
          <div class="wi-mrr-counts">
            ${mrrCounts.map(c => `<span class="wi-mrr-chip">${c}</span>`).join('')}
          </div>
        ` : ''}
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
