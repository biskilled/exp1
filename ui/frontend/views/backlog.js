/**
 * backlog.js — Backlog tab view.
 *
 * Renders GROUP sections (one per use-case cluster) each containing
 * source-event items (PROMPTS / COMMITS / MESSAGES / ITEMS).
 *
 * Actions:
 *   ↻ Sync          — POST /sync-backlog?mode=full
 *   ✓ Approve all   — POST /backlog/approve-group {slug, approve:"x"}
 *   ✗ Reject all    — POST /backlog/approve-group {slug, approve:"-"}
 *   classify select — PATCH /backlog/{ref_id} {classify}
 *   status select   — PATCH /backlog/{ref_id} {status}
 *   ✕ remove        — DELETE /backlog/{ref_id}
 */

import { api }  from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { state } from '../stores/state.js';

let _project = '';
let _polling  = null;

export function destroyBacklog() {
  if (_polling) { clearInterval(_polling); _polling = null; }
}

export async function renderBacklog(container, projectName) {
  destroyBacklog();
  _project = projectName || state.currentProject?.name || '';

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- ── Toolbar ── -->
      <div style="padding:0.65rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.75rem;flex-shrink:0;flex-wrap:wrap">
        <span style="font-size:0.88rem;font-weight:700;color:var(--text);margin-right:0.25rem">Backlog</span>
        <button id="bl-sync-btn" class="btn btn-ghost btn-sm"
                title="Run full digest — all pending rows grouped into use-case clusters">
          ↻ Sync
        </button>
        <span style="flex:1"></span>
        <span id="bl-status" style="font-size:0.72rem;color:var(--muted)"></span>
      </div>

      <!-- ── Counters bar ── -->
      <div id="bl-counters" style="padding:0.65rem 1.25rem;background:var(--surface);
                border-bottom:1px solid var(--border);flex-shrink:0">
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem" id="bl-counter-grid">
          ${_skeletonCounters()}
        </div>
      </div>

      <!-- ── Groups ── -->
      <div id="bl-entries" style="flex:1;overflow-y:auto;padding:1rem 1.25rem">
        <div style="color:var(--muted);text-align:center;padding:3rem;font-size:0.82rem">
          Loading backlog…
        </div>
      </div>
    </div>

    <style>
      /* ── Group card ── */
      .bl-group {
        border:1px solid var(--border);
        border-radius:var(--radius);
        background:var(--surface);
        margin-bottom:1rem;
        overflow:hidden;
      }
      .bl-group-header {
        display:flex;align-items:flex-start;gap:0.6rem;flex-wrap:wrap;
        padding:0.7rem 1rem;
        background:var(--surface2);
        border-bottom:1px solid var(--border);
        cursor:pointer;user-select:none;
      }
      .bl-group-header:hover { background:var(--surface3); }
      .bl-group-slug {
        font-size:0.95rem;font-weight:800;color:var(--text);
        letter-spacing:-.01em;
      }
      .bl-group-meta {
        font-size:0.7rem;color:var(--muted);display:flex;
        align-items:center;gap:0.5rem;flex-wrap:wrap;flex:1;
      }
      .bl-group-counts {
        font-size:0.68rem;color:var(--muted);
        background:var(--surface3);padding:1px 7px;border-radius:8px;
      }
      .bl-group-arrow { font-size:0.7rem;color:var(--muted);margin-left:auto;align-self:center }
      .bl-group-body { padding:0.75rem 1rem }
      .bl-group-body.collapsed { display:none }

      /* ── Group summary/completed/actions sections ── */
      .bl-group-summary {
        font-size:0.82rem;color:var(--text2);line-height:1.55;
        margin-bottom:0.75rem;padding:0.5rem 0.75rem;
        background:var(--surface3);border-radius:calc(var(--radius) - 2px);
        border-left:3px solid var(--accent);
      }
      .bl-group-section { margin-bottom:0.75rem }
      .bl-group-section-title {
        font-size:0.68rem;font-weight:800;color:var(--muted);
        text-transform:uppercase;letter-spacing:.07em;
        margin-bottom:0.3rem;display:flex;align-items:center;gap:0.4rem;
      }
      .bl-completed-list, .bl-actions-list {
        list-style:none;margin:0;padding:0;
        display:flex;flex-direction:column;gap:0.2rem;
      }
      .bl-completed-list li, .bl-actions-list li {
        font-size:0.78rem;color:var(--text);
        padding:0.15rem 0;display:flex;align-items:flex-start;gap:0.4rem;
      }
      .bl-completed-list li::before { content:"•";color:#16a34a;flex-shrink:0 }
      .bl-actions-list li::before   { content:"•";color:var(--accent);flex-shrink:0 }
      .bl-action-badge {
        font-size:0.62rem;padding:1px 5px;border-radius:6px;font-weight:700;
        flex-shrink:0;
      }
      .bl-action-badge-feature { background:#dcfce7;color:#16a34a }
      .bl-action-badge-bug     { background:#fee2e2;color:#dc2626 }
      .bl-action-badge-task    { background:#dbeafe;color:#1d4ed8 }

      /* ── Group footer ── */
      .bl-group-footer {
        display:flex;justify-content:flex-end;gap:0.5rem;
        padding:0.65rem 1rem;
        border-top:1px solid var(--border);
        background:var(--surface2);
      }
      .bl-approve-all-btn, .bl-reject-all-btn {
        border:none;border-radius:4px;padding:4px 14px;cursor:pointer;
        font-size:0.78rem;font-weight:700;transition:opacity .15s;
      }
      .bl-approve-all-btn { background:#16a34a;color:#fff }
      .bl-reject-all-btn  { background:#dc2626;color:#fff }
      .bl-approve-all-btn:hover { opacity:.85 }
      .bl-reject-all-btn:hover  { opacity:.85 }
      .bl-approve-all-btn:disabled, .bl-reject-all-btn:disabled { opacity:.4;cursor:not-allowed }

      /* ── Tag chips ── */
      .bl-tags-row { display:flex;flex-wrap:wrap;gap:0.3rem;margin-bottom:0.6rem }
      .bl-chip {
        font-size:0.68rem;padding:2px 8px;border-radius:10px;font-weight:600;
        display:inline-flex;align-items:center;gap:3px;
      }
      .bl-chip-user     { background:#f3f4f6;color:#374151;border:1px solid #d1d5db }
      .bl-chip-existing { background:#dbeafe;color:#1d4ed8 }
      .bl-chip-new      { background:#fef9c3;color:#854d0e }
      .bl-chip-type-new { background:#fce7f3;color:#9d174d;font-size:0.62rem;padding:1px 5px }

      /* ── Source type section ── */
      .bl-src-section { margin-bottom:0.5rem }
      .bl-src-label {
        font-size:0.63rem;font-weight:800;color:var(--muted);
        text-transform:uppercase;letter-spacing:.08em;
        margin-bottom:0.3rem;
      }

      /* ── Item card ── */
      .bl-entry {
        border:1px solid var(--border);
        border-radius:calc(var(--radius) - 2px);
        background:var(--surface);
        margin-bottom:0.4rem;
        overflow:hidden;
      }
      .bl-entry-header {
        display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;
        padding:0.45rem 0.75rem;
        background:var(--surface2);
        cursor:pointer;user-select:none;
      }
      .bl-entry-header:hover { background:var(--surface3); }
      .bl-ref  { font-family:var(--font);font-size:0.7rem;font-weight:700;color:var(--accent);min-width:68px }
      .bl-summary { flex:1;font-size:0.8rem;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0 }
      .bl-classify-badge {
        font-size:0.63rem;padding:1px 6px;border-radius:8px;font-weight:700;
        text-transform:uppercase;letter-spacing:.04em;flex-shrink:0;
      }
      .bl-classify-feature { background:#dcfce7;color:#16a34a }
      .bl-classify-bug     { background:#fee2e2;color:#dc2626 }
      .bl-classify-task    { background:#dbeafe;color:#1d4ed8 }
      .bl-classify-use_case{ background:#cffafe;color:#0e7490 }
      .bl-status-badge {
        font-size:0.63rem;padding:1px 6px;border-radius:8px;font-weight:600;
        flex-shrink:0;
      }
      .bl-status-completed   { background:#f0fdf4;color:#16a34a;border:1px solid #86efac }
      .bl-status-in-progress { background:#fff7ed;color:#c2410c;border:1px solid #fdba74 }
      .bl-ai-score {
        font-size:0.63rem;color:var(--muted);background:var(--surface3);
        padding:1px 6px;border-radius:8px;flex-shrink:0;
      }

      /* ── Item inline controls ── */
      .bl-item-select {
        font-size:0.7rem;border:1px solid var(--border);border-radius:4px;
        background:var(--surface);color:var(--text);padding:1px 4px;
        cursor:pointer;flex-shrink:0;
      }
      .bl-item-select:focus { outline:none;border-color:var(--accent) }
      .bl-remove-btn {
        border:none;border-radius:4px;padding:1px 7px;cursor:pointer;
        font-size:0.78rem;font-weight:700;background:transparent;color:var(--muted);
        transition:color .15s,background .15s;flex-shrink:0;
      }
      .bl-remove-btn:hover { background:#fee2e2;color:#dc2626 }

      /* ── Item body ── */
      .bl-body {
        padding:0.5rem 0.75rem;
        font-size:0.77rem;
        color:var(--text2);
        line-height:1.55;
        display:none;
        border-top:1px solid var(--border);
      }
      .bl-body.open { display:block }
      .bl-body-row { margin-bottom:0.35rem }
      .bl-body-label {
        font-size:0.64rem;font-weight:700;color:var(--muted);
        text-transform:uppercase;letter-spacing:.06em;
        margin-bottom:0.15rem;
      }
      .bl-body-text { color:var(--text);font-size:0.78rem;line-height:1.5 }

      /* ── Counters ── */
      .bl-counter-card {
        background:var(--surface2);border-radius:var(--radius);
        padding:0.55rem 0.85rem;border:1px solid var(--border);
      }
      .bl-counter-label { font-size:0.68rem;color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.05em }
      .bl-counter-row   { display:flex;gap:1rem;margin-top:0.3rem;flex-wrap:wrap }
      .bl-stat          { display:flex;flex-direction:column;align-items:center }
      .bl-stat-n        { font-size:1.05rem;font-weight:700;color:var(--text);line-height:1 }
      .bl-stat-lbl      { font-size:0.62rem;color:var(--muted);margin-top:2px }
      .bl-stat-n.warn   { color:var(--accent) }
      .bl-stat-n.ok     { color:#16a34a }
      .bl-empty { text-align:center;padding:3rem;color:var(--muted);font-size:0.82rem }
    </style>
  `;

  document.getElementById('bl-sync-btn').onclick = _onSync;

  await _loadAll();
  _polling = setInterval(_loadStats, 30_000);
}

// ── Loaders ───────────────────────────────────────────────────────────────────

async function _loadAll() {
  await Promise.all([_loadStats(), _loadEntries()]);
}

async function _loadStats() {
  if (!_project) return;
  try {
    const data = await api.backlog.stats(_project);
    _renderCounters(data);
  } catch (e) {
    const g = document.getElementById('bl-counter-grid');
    if (g) g.innerHTML = `<div style="grid-column:1/-1;color:var(--muted);font-size:0.78rem">Stats unavailable: ${e.message}</div>`;
  }
}

async function _loadEntries() {
  if (!_project) return;
  const el = document.getElementById('bl-entries');
  try {
    const data = await api.backlog.entries(_project);
    const entries = data.entries || [];
    if (entries.length && entries[0]?.items !== undefined) {
      _renderGroups(entries);
    } else {
      _renderGroups(_flatToGroups(entries));
    }
  } catch (e) {
    if (el) el.innerHTML = `<div class="bl-empty">Could not load backlog: ${e.message}</div>`;
  }
}

/** Wrap old flat entry list into a single synthetic group for backward compat. */
function _flatToGroups(entries) {
  if (!entries.length) return [];
  return [{ slug: 'backlog', slug_type: 'existing', date: '', source: 'auto',
            approve: ' ', user_tags: [], ai_existing_tags: [], ai_new_tags: [],
            summary: '', completed: [], action_items: [],
            items: entries }];
}

// ── Actions ───────────────────────────────────────────────────────────────────

async function _onSync() {
  const btn = document.getElementById('bl-sync-btn');
  _setStatus('Syncing…');
  btn.disabled = true;
  try {
    const r = await api.backlog.syncBacklog(_project, 'full');
    const total = r.appended || 0;
    toast(total > 0 ? `Synced — ${total} items in ${r.groups || 0} groups` : 'No new rows to process', 'success');
    await _loadAll();
  } catch (e) {
    toast(`Sync failed: ${e.message}`, 'error');
  } finally {
    btn.disabled = false;
    _setStatus('');
  }
}

async function _onGroupApprove(slug) {
  _setStatus('Approving…');
  try {
    const r = await api.backlog.approveGroup(_project, slug, 'x');
    toast(`✓ Approved ${r.processed || 0} items → merged into use case`, 'success');
    await _loadAll();
  } catch (e) {
    toast(`Approve failed: ${e.message}`, 'error');
  } finally {
    _setStatus('');
  }
}

async function _onGroupReject(slug) {
  _setStatus('Rejecting…');
  try {
    const r = await api.backlog.approveGroup(_project, slug, '-');
    toast(`✗ Rejected ${r.rejected || 0} items`, 'info');
    await _loadAll();
  } catch (e) {
    toast(`Reject failed: ${e.message}`, 'error');
  } finally {
    _setStatus('');
  }
}

async function _onClassifyChange(refId, val) {
  try {
    await api.backlog.patch(_project, refId, { classify: val });
  } catch (e) {
    toast(`Could not update classify for ${refId}: ${e.message}`, 'error');
  }
}

async function _onStatusChange(refId, val) {
  try {
    await api.backlog.patch(_project, refId, { status: val });
  } catch (e) {
    toast(`Could not update status for ${refId}: ${e.message}`, 'error');
  }
}

async function _onRemove(refId, itemEl) {
  try {
    await api.backlog.deleteEntry(_project, refId);
    itemEl.remove();
  } catch (e) {
    toast(`Could not remove ${refId}: ${e.message}`, 'error');
  }
}

// ── Renderers ─────────────────────────────────────────────────────────────────

function _renderCounters(data) {
  const grid = document.getElementById('bl-counter-grid');
  if (!grid) return;
  const sources = ['prompts', 'commits', 'messages', 'items'];
  const icons   = { prompts: '💬', commits: '⌥', messages: '✉', items: '📋' };
  const labels  = { prompts: 'Prompts', commits: 'Commits', messages: 'Messages', items: 'Items' };
  grid.innerHTML = sources.map(src => {
    const s = data.by_source?.[src] || {};
    const pending   = s.pending   ?? 0;
    const processed = s.processed ?? 0;
    const cnt       = s.cnt       ?? 5;
    const batches   = s.batches   ?? 0;
    return `
      <div class="bl-counter-card">
        <div class="bl-counter-label">${icons[src]} ${labels[src]}</div>
        <div class="bl-counter-row">
          <div class="bl-stat">
            <div class="bl-stat-n ${pending > 0 ? 'warn' : 'ok'}">${pending}</div>
            <div class="bl-stat-lbl">open</div>
          </div>
          <div class="bl-stat">
            <div class="bl-stat-n">${processed}</div>
            <div class="bl-stat-lbl">done</div>
          </div>
          <div class="bl-stat">
            <div class="bl-stat-n">${batches}</div>
            <div class="bl-stat-lbl">×${cnt}</div>
          </div>
        </div>
      </div>`;
  }).join('');
}

function _renderGroups(groups) {
  const el = document.getElementById('bl-entries');
  if (!el) return;

  if (!groups.length) {
    el.innerHTML = `
      <div class="bl-empty">
        <div style="font-size:2rem;margin-bottom:0.5rem">📭</div>
        <div>Backlog is empty.</div>
        <div style="margin-top:0.4rem;font-size:0.75rem">
          Click <strong>↻ Sync</strong> to flush pending rows from the database.
        </div>
      </div>`;
    return;
  }

  el.innerHTML = groups.map((grp, gi) => _groupHtml(grp, gi)).join('');

  // Bind group toggle + item events
  groups.forEach((grp, gi) => {
    const grpId = `bl-grp-${gi}`;
    const grpEl = document.getElementById(grpId);
    if (!grpEl) return;

    const hdr   = grpEl.querySelector('.bl-group-header');
    const body  = grpEl.querySelector('.bl-group-body');
    const arrow = grpEl.querySelector('.bl-group-arrow');
    if (hdr && body) {
      hdr.addEventListener('click', e => {
        if (e.target.closest('button')) return;
        const collapsed = body.classList.toggle('collapsed');
        if (arrow) arrow.textContent = collapsed ? '▶' : '▼';
      });
    }

    // Group-level approve/reject buttons
    const apAllBtn = grpEl.querySelector('.bl-approve-all-btn');
    const rjAllBtn = grpEl.querySelector('.bl-reject-all-btn');
    if (apAllBtn) apAllBtn.addEventListener('click', () => _onGroupApprove(grp.slug));
    if (rjAllBtn) rjAllBtn.addEventListener('click', () => _onGroupReject(grp.slug));

    // Per-item controls
    (grp.items || []).forEach(item => {
      const card = document.getElementById(`bl-card-${item.ref_id}`);
      if (!card) return;

      const ih = card.querySelector('.bl-entry-header');
      const ib = card.querySelector('.bl-body');
      if (ih && ib) {
        ih.addEventListener('click', e => {
          if (e.target.closest('select') || e.target.closest('button')) return;
          ib.classList.toggle('open');
        });
      }

      const clsSel = card.querySelector('.bl-classify-select');
      const stSel  = card.querySelector('.bl-status-select');
      const rmBtn  = card.querySelector('.bl-remove-btn');

      if (clsSel) clsSel.addEventListener('change', () => _onClassifyChange(item.ref_id, clsSel.value));
      if (stSel)  stSel.addEventListener('change',  () => _onStatusChange(item.ref_id, stSel.value));
      if (rmBtn)  rmBtn.addEventListener('click',   () => _onRemove(item.ref_id, card));
    });
  });
}

function _groupHtml(grp, idx = 0) {
  const grpId    = `bl-grp-${idx}`;
  const slug     = grp.slug      || 'unknown';
  const slugType = grp.slug_type || 'existing';
  const date     = grp.date      || '';
  const items    = grp.items     || [];

  // Counts
  const cnts = { PROMPTS: 0, COMMITS: 0, MESSAGES: 0, ITEMS: 0 };
  for (const it of items) cnts[it.src_label || 'PROMPTS'] = (cnts[it.src_label || 'PROMPTS'] || 0) + 1;
  const countParts = Object.entries(cnts).filter(([,v]) => v > 0).map(([k,v]) => `${v} ${k.toLowerCase()}`);
  const countStr = countParts.join(' · ') || '0 events';

  // Tags
  const userTags   = grp.user_tags        || [];
  const aiExisting = grp.ai_existing_tags || [];
  const aiNew      = grp.ai_new_tags      || [];
  const hasAnyTags = userTags.length || aiExisting.length || aiNew.length;

  const tagChips = hasAnyTags ? `
    <div class="bl-tags-row">
      ${userTags.map(t => `<span class="bl-chip bl-chip-user">🏷 ${_esc(t)}</span>`).join('')}
      ${aiExisting.map(t => `<span class="bl-chip bl-chip-existing">● ${_esc(t.category)}:${_esc(t.name)}</span>`).join('')}
      ${aiNew.map(t => `<span class="bl-chip bl-chip-new">✦ ${_esc(t.category)}:${_esc(t.name)}</span>`).join('')}
    </div>` : '';

  // Summary paragraph
  const summaryHtml = grp.summary ? `
    <div class="bl-group-summary">${_esc(grp.summary)}</div>` : '';

  // Completed section
  const completed = grp.completed || [];
  const completedHtml = completed.length ? `
    <div class="bl-group-section">
      <div class="bl-group-section-title">✓ Completed</div>
      <ul class="bl-completed-list">
        ${completed.map(d => `<li>${_esc(d)}</li>`).join('')}
      </ul>
    </div>` : '';

  // Action items section
  const actionItems = grp.action_items || [];
  const actionsHtml = actionItems.length ? `
    <div class="bl-group-section">
      <div class="bl-group-section-title">⚡ Action items</div>
      <ul class="bl-actions-list">
        ${actionItems.map(a => {
          const cls = a.classify || 'task';
          const badgeCls = `bl-action-badge bl-action-badge-${cls}`;
          return `<li><span class="${badgeCls}">${_esc(cls)}</span>${_esc(a.desc || '')}</li>`;
        }).join('')}
      </ul>
    </div>` : '';

  // Group items by source type
  const bySource = { PROMPTS: [], COMMITS: [], MESSAGES: [], ITEMS: [] };
  for (const it of items) bySource[it.src_label || 'PROMPTS'].push(it);

  const itemsHtml = Object.entries(bySource)
    .filter(([,arr]) => arr.length > 0)
    .map(([src, arr]) => `
      <div class="bl-src-section">
        <div class="bl-src-label">${src}</div>
        ${arr.map(it => _itemHtml(it)).join('')}
      </div>`)
    .join('');

  const itemsDivider = items.length ? `
    <div style="font-size:0.68rem;font-weight:700;color:var(--muted);text-transform:uppercase;
                letter-spacing:.06em;margin:0.6rem 0 0.4rem;border-top:1px solid var(--border);
                padding-top:0.5rem">
      Items (${items.length})
    </div>` : '';

  return `
    <div class="bl-group" id="${grpId}">
      <div class="bl-group-header">
        <div style="flex:1;min-width:0">
          <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
            <span class="bl-group-slug">${_esc(slug)}</span>
            ${slugType === 'new' ? '<span class="bl-chip bl-chip-type-new">NEW</span>' : ''}
            <span class="bl-group-counts">${countStr}</span>
            <span class="bl-group-meta">${date}</span>
          </div>
        </div>
        <span class="bl-group-arrow">▼</span>
      </div>
      <div class="bl-group-body">
        ${tagChips}
        ${summaryHtml}
        ${completedHtml}
        ${actionsHtml}
        ${itemsDivider}
        ${itemsHtml || '<div style="color:var(--muted);font-size:0.78rem;padding:0.5rem 0">No items</div>'}
      </div>
      <div class="bl-group-footer">
        <button class="bl-approve-all-btn" title="Approve all items in this group → merge into use case file">✓ Approve all</button>
        <button class="bl-reject-all-btn"  title="Reject all items in this group">✗ Reject all</button>
      </div>
    </div>`;
}

function _itemHtml(item) {
  const classify = item.classify || 'task';
  const status   = item.status   || 'in-progress';
  const aiScore  = item.ai_score ?? '';
  const refId    = item.ref_id   || '';
  const summary  = item.summary  || '';

  const classifyCls = {
    feature:  'bl-classify-feature',
    bug:      'bl-classify-bug',
    task:     'bl-classify-task',
    use_case: 'bl-classify-use_case',
  }[classify] || 'bl-classify-task';

  const statusCls = status === 'completed' ? 'bl-status-completed' : 'bl-status-in-progress';

  // Body content
  const reqs = item.requirements || '';
  const devs = item.deliveries   || '';
  const hasBody = reqs || devs;

  const bodyHtml = hasBody ? `
    <div class="bl-body">
      ${reqs ? `<div class="bl-body-row">
        <div class="bl-body-label">Requirements</div>
        <div class="bl-body-text">${_esc(reqs)}</div>
      </div>` : ''}
      ${devs ? `<div class="bl-body-row">
        <div class="bl-body-label">Deliveries</div>
        <div class="bl-body-text">${_esc(devs)}</div>
      </div>` : ''}
    </div>` : '';

  return `
    <div class="bl-entry" id="bl-card-${refId}">
      <div class="bl-entry-header">
        <span class="bl-ref">${_esc(refId)}</span>
        <select class="bl-item-select bl-classify-select" title="Classify">
          ${['feature','task','bug','use_case'].map(v =>
            `<option value="${v}"${v === classify ? ' selected' : ''}>${v}</option>`
          ).join('')}
        </select>
        <select class="bl-item-select bl-status-select" title="Status">
          ${['in-progress','completed'].map(v =>
            `<option value="${v}"${v === status ? ' selected' : ''}>${v}</option>`
          ).join('')}
        </select>
        ${aiScore !== '' ? `<span class="bl-ai-score">AI:${aiScore}</span>` : ''}
        <span class="bl-summary" title="${_esc(summary)}">${_esc(summary)}</span>
        <button class="bl-remove-btn" title="Remove this item from backlog">✕</button>
      </div>
      ${bodyHtml}
    </div>`;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _setStatus(msg) {
  const el = document.getElementById('bl-status');
  if (el) el.textContent = msg;
}

function _skeletonCounters() {
  return Array(4).fill(0).map(() =>
    `<div class="bl-counter-card" style="height:72px;background:var(--surface3);border-radius:var(--radius)"></div>`
  ).join('');
}

function _esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
