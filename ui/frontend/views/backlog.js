/**
 * backlog.js — Backlog tab view.
 *
 * Renders GROUP sections (one per use-case cluster) each containing
 * source-event items (PROMPTS / COMMITS / MESSAGES / ITEMS).
 *
 * Actions:
 *   ↻ Sync    — POST /sync-backlog?mode=full
 *   ▶ Process — POST /work-items/sync
 *   ✓ / ✗    — PATCH /backlog/{ref_id} per item
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
        <button id="bl-process-btn" class="btn btn-outline btn-sm" style="display:none"
                title="Merge approved items into use_cases/*.md and planner_tags">
          ▶ Process approved (<span id="bl-approved-count">0</span>)
        </button>
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
      .bl-date { font-size:0.67rem;color:var(--muted);min-width:78px }
      .bl-summary { flex:1;font-size:0.8rem;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0 }
      .bl-classify {
        font-size:0.63rem;padding:1px 6px;border-radius:8px;font-weight:700;
        text-transform:uppercase;letter-spacing:.04em;flex-shrink:0;
      }
      .bl-classify-feature { background:#dcfce7;color:#16a34a }
      .bl-classify-bug     { background:#fee2e2;color:#dc2626 }
      .bl-classify-task    { background:#dbeafe;color:#1d4ed8 }
      .bl-classify-use_case{ background:#cffafe;color:#0e7490 }
      .bl-status {
        font-size:0.63rem;padding:1px 6px;border-radius:8px;font-weight:600;
        flex-shrink:0;
      }
      .bl-status-completed   { background:#f0fdf4;color:#16a34a;border:1px solid #86efac }
      .bl-status-in-progress { background:#fff7ed;color:#c2410c;border:1px solid #fdba74 }
      .bl-ai-score {
        font-size:0.63rem;color:var(--muted);background:var(--surface3);
        padding:1px 6px;border-radius:8px;flex-shrink:0;
      }
      .bl-approve-btn, .bl-reject-btn {
        border:none;border-radius:4px;padding:2px 8px;cursor:pointer;
        font-size:0.72rem;font-weight:700;transition:opacity .15s;flex-shrink:0;
      }
      .bl-approve-btn { background:#16a34a;color:#fff }
      .bl-reject-btn  { background:#dc2626;color:#fff }
      .bl-approve-btn:hover { opacity:.85 }
      .bl-reject-btn:hover  { opacity:.85 }
      .bl-approved { border-color:#16a34a!important;background:#f0fdf4 }
      .bl-rejected { border-color:#dc2626!important;background:#fef2f2;opacity:.65 }

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

  document.getElementById('bl-sync-btn').onclick    = _onSync;
  document.getElementById('bl-process-btn').onclick = _onProcess;

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
    // Support both old flat format and new group format
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

async function _onProcess() {
  const btn = document.getElementById('bl-process-btn');
  _setStatus('Processing…');
  btn.disabled = true;
  try {
    const r = await api.backlog.runWorkItems(_project);
    const msg = [
      r.approved  ? `${r.approved} approved`  : '',
      r.rejected  ? `${r.rejected} rejected`  : '',
      r.pending   ? `${r.pending} pending`    : '',
      r.use_cases_updated?.length ? `${r.use_cases_updated.length} use cases updated` : '',
    ].filter(Boolean).join(' · ');
    toast(msg || 'Done', 'success');
    await _loadAll();
  } catch (e) {
    toast(`Process failed: ${e.message}`, 'error');
  } finally {
    btn.disabled = false;
    _setStatus('');
  }
}

async function _onApprove(refId, card) {
  try {
    await api.backlog.patch(_project, refId, { approve: '+' });
    card.classList.remove('bl-rejected');
    card.classList.add('bl-approved');
    _updateItemButtons(card, '+');
    _refreshApproveCount();
  } catch (e) {
    toast(`Could not approve ${refId}: ${e.message}`, 'error');
  }
}

async function _onReject(refId, card) {
  try {
    await api.backlog.patch(_project, refId, { approve: '-' });
    card.classList.remove('bl-approved');
    card.classList.add('bl-rejected');
    _updateItemButtons(card, '-');
    _refreshApproveCount();
  } catch (e) {
    toast(`Could not reject ${refId}: ${e.message}`, 'error');
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

  // Count approved items
  let totalApproved = 0;
  for (const grp of groups) {
    for (const item of grp.items || []) {
      if (item.approve === '+' || item.approve === 'x') totalApproved++;
    }
  }
  const processBtn    = document.getElementById('bl-process-btn');
  const approvedCount = document.getElementById('bl-approved-count');
  if (processBtn) {
    processBtn.style.display = totalApproved > 0 ? '' : 'none';
    if (approvedCount) approvedCount.textContent = totalApproved;
  }

  el.innerHTML = groups.map((grp, gi) => _groupHtml(grp, gi)).join('');

  // Bind group toggle + item events
  groups.forEach((grp, gi) => {
    const grpId  = `bl-grp-${gi}`;
    const grpEl  = document.getElementById(grpId);
    if (!grpEl) return;

    const hdr  = grpEl.querySelector('.bl-group-header');
    const body = grpEl.querySelector('.bl-group-body');
    const arrow = grpEl.querySelector('.bl-group-arrow');
    if (hdr && body) {
      hdr.addEventListener('click', e => {
        if (e.target.closest('button')) return;
        const collapsed = body.classList.toggle('collapsed');
        if (arrow) arrow.textContent = collapsed ? '▶' : '▼';
      });
    }

    (grp.items || []).forEach(item => {
      const card = document.getElementById(`bl-card-${item.ref_id}`);
      if (!card) return;

      const ih = card.querySelector('.bl-entry-header');
      const ib = card.querySelector('.bl-body');
      if (ih && ib) {
        ih.addEventListener('click', e => {
          if (e.target.closest('button')) return;
          ib.classList.toggle('open');
        });
      }

      const apBtn = card.querySelector('.bl-approve-btn');
      const rjBtn = card.querySelector('.bl-reject-btn');
      if (apBtn) apBtn.addEventListener('click', () => _onApprove(item.ref_id, card));
      if (rjBtn) rjBtn.addEventListener('click', () => _onReject(item.ref_id, card));
    });
  });
}

function _groupHtml(grp, idx = 0) {
  const grpId    = `bl-grp-${idx}`;
  const slug     = grp.slug     || 'unknown';
  const slugType = grp.slug_type || 'existing';
  const date     = grp.date     || '';
  const items    = grp.items    || [];

  // Counts
  const cnts = { PROMPTS: 0, COMMITS: 0, MESSAGES: 0, ITEMS: 0 };
  for (const it of items) cnts[it.src_label || 'PROMPTS'] = (cnts[it.src_label || 'PROMPTS'] || 0) + 1;
  const countParts = Object.entries(cnts).filter(([,v]) => v > 0).map(([k,v]) => `${v} ${k.toLowerCase()}`);
  const countStr = countParts.join(' · ') || '0 events';

  // Approved / rejected counts
  const approvedItems = items.filter(i => i.approve === '+' || i.approve === 'x').length;
  const rejectedItems = items.filter(i => i.approve === '-').length;
  const pendingItems  = items.length - approvedItems - rejectedItems;

  // Tags
  const userTags     = grp.user_tags       || [];
  const aiExisting   = grp.ai_existing_tags|| [];
  const aiNew        = grp.ai_new_tags     || [];
  const hasAnyTags   = userTags.length || aiExisting.length || aiNew.length;

  const tagChips = hasAnyTags ? `
    <div class="bl-tags-row">
      ${userTags.map(t => `<span class="bl-chip bl-chip-user">🏷 ${_esc(t)}</span>`).join('')}
      ${aiExisting.map(t => `<span class="bl-chip bl-chip-existing">● ${_esc(t.category)}:${_esc(t.name)}</span>`).join('')}
      ${aiNew.map(t => `<span class="bl-chip bl-chip-new">✦ ${_esc(t.category)}:${_esc(t.name)}</span>`).join('')}
    </div>` : '';

  // Progress bar counts
  const statusLine = `
    <span style="font-size:0.67rem;color:var(--muted)">
      ${pendingItems > 0  ? `<span style="color:#f59e0b">⬤ ${pendingItems} pending</span>` : ''}
      ${approvedItems > 0 ? `<span style="color:#16a34a;margin-left:0.4rem">✓ ${approvedItems} approved</span>` : ''}
      ${rejectedItems > 0 ? `<span style="color:#dc2626;margin-left:0.4rem">✗ ${rejectedItems} rejected</span>` : ''}
    </span>`;

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

  return `
    <div class="bl-group" id="${grpId}">
      <div class="bl-group-header">
        <div style="flex:1;min-width:0">
          <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
            <span class="bl-group-slug">${_esc(slug)}</span>
            ${slugType === 'new' ? '<span class="bl-chip bl-chip-type-new">NEW</span>' : ''}
            <span class="bl-group-counts">${countStr}</span>
            <span class="bl-group-meta">${date}</span>
            ${statusLine}
          </div>
        </div>
        <span class="bl-group-arrow">▼</span>
      </div>
      <div class="bl-group-body">
        ${tagChips}
        ${itemsHtml || '<div style="color:var(--muted);font-size:0.78rem;padding:0.5rem 0">No items</div>'}
      </div>
    </div>`;
}

// Needed because _renderGroups passes idx but _groupHtml receives grp+idx
// Wrap to use array index:
const _origGroupHtml = _groupHtml;

function _itemHtml(item) {
  const ap       = item.approve || ' ';
  const classify = item.classify || 'task';
  const status   = item.status   || '';
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

  const approvedStyle = (ap === '+' || ap === 'x') ? 'style="opacity:.4;pointer-events:none"' : '';
  const rejectStyle   = ap === '-' ? 'style="opacity:.4;pointer-events:none"' : '';
  const cardCls       = ap === 'x' || ap === '+' ? 'bl-approved' : ap === '-' ? 'bl-rejected' : '';

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
    <div class="bl-entry ${cardCls}" id="bl-card-${refId}">
      <div class="bl-entry-header">
        <span class="bl-ref">${_esc(refId)}</span>
        ${classify ? `<span class="bl-classify ${classifyCls}">${classify}</span>` : ''}
        ${status   ? `<span class="bl-status ${statusCls}">${status}</span>` : ''}
        ${aiScore !== '' ? `<span class="bl-ai-score">AI:${aiScore}</span>` : ''}
        <span class="bl-summary" title="${_esc(summary)}">${_esc(summary)}</span>
        <button class="bl-approve-btn" ${approvedStyle} title="Approve — merge into use case on Process">✓</button>
        <button class="bl-reject-btn"  ${rejectStyle}   title="Reject — move to REJECTED section">✗</button>
      </div>
      ${bodyHtml}
    </div>`;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _refreshApproveCount() {
  let total = 0;
  document.querySelectorAll('.bl-entry.bl-approved').forEach(() => total++);
  const processBtn    = document.getElementById('bl-process-btn');
  const approvedCount = document.getElementById('bl-approved-count');
  if (processBtn) processBtn.style.display = total > 0 ? '' : 'none';
  if (approvedCount) approvedCount.textContent = total;
}

function _updateItemButtons(card, val) {
  const apBtn = card.querySelector('.bl-approve-btn');
  const rjBtn = card.querySelector('.bl-reject-btn');
  if (apBtn) { apBtn.style.opacity = (val === '+' || val === 'x') ? '.4' : '1'; apBtn.style.pointerEvents = (val === '+' || val === 'x') ? 'none' : ''; }
  if (rjBtn) { rjBtn.style.opacity = val === '-' ? '.4' : '1'; rjBtn.style.pointerEvents = val === '-' ? 'none' : ''; }
}

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
