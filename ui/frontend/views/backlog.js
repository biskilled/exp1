/**
 * backlog.js — Backlog tab view.
 *
 * Shows all entries from documents/backlog.md with per-section approve/reject
 * controls. A counter bar at the top shows unprocessed vs processed row counts
 * per source type with batch estimates.
 *
 * Actions:
 *   ↻ Sync    — POST /sync-backlog (flush pending rows → backlog.md)
 *   ▶ Process — POST /work-items/sync (approve entries → use_cases/*.md + planner_tags)
 *   ✓ / ✗    — PATCH /backlog/{ref_id} to approve or reject individual entries
 */

import { api }   from '../utils/api.js';
import { toast }  from '../utils/toast.js';
import { state }  from '../stores/state.js';

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

        <button id="bl-sync-btn" class="btn btn-ghost btn-sm" title="Flush pending mirror rows → backlog.md">
          ↻ Sync
        </button>
        <button id="bl-process-btn" class="btn btn-primary btn-sm" title="Process approved entries → use_cases/ + planner_tags">
          ▶ Process approved
        </button>
        <button id="bl-refresh-btn" class="btn btn-ghost btn-sm" title="Reload entries from backlog.md">
          ⟳ Reload
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

      <!-- ── Entries ── -->
      <div id="bl-entries" style="flex:1;overflow-y:auto;padding:1rem 1.25rem">
        <div style="color:var(--muted);text-align:center;padding:3rem;font-size:0.82rem">
          Loading backlog…
        </div>
      </div>
    </div>

    <style>
      .bl-entry {
        border:1px solid var(--border);
        border-radius:var(--radius);
        background:var(--surface);
        margin-bottom:0.65rem;
        overflow:hidden;
      }
      .bl-entry-header {
        display:flex;
        align-items:center;
        gap:0.6rem;
        padding:0.55rem 0.85rem;
        border-bottom:1px solid var(--border);
        background:var(--surface2);
        cursor:pointer;
        user-select:none;
      }
      .bl-entry-header:hover { background:var(--surface3); }
      .bl-ref  { font-family:var(--font);font-size:0.72rem;font-weight:700;color:var(--accent);min-width:72px }
      .bl-date { font-size:0.7rem;color:var(--muted);min-width:80px }
      .bl-summary { flex:1;font-size:0.8rem;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis }
      .bl-classify {
        font-size:0.65rem;padding:1px 6px;border-radius:10px;font-weight:600;
        text-transform:uppercase;letter-spacing:.04em;
      }
      .bl-classify-feature { background:#dcfce7;color:#16a34a }
      .bl-classify-bug     { background:#fee2e2;color:#dc2626 }
      .bl-classify-task    { background:#dbeafe;color:#1d4ed8 }
      .bl-classify-use_case{ background:#cffafe;color:#0e7490 }
      .bl-approve-btn, .bl-reject-btn {
        border:none;border-radius:4px;padding:2px 9px;cursor:pointer;
        font-size:0.75rem;font-weight:700;transition:opacity .15s;
      }
      .bl-approve-btn { background:#16a34a;color:#fff }
      .bl-reject-btn  { background:#dc2626;color:#fff }
      .bl-approve-btn:hover { opacity:.85 }
      .bl-reject-btn:hover  { opacity:.85 }
      .bl-approved { border-color:#16a34a!important;background:#f0fdf4 }
      .bl-rejected { border-color:#dc2626!important;background:#fef2f2;opacity:.6 }
      .bl-body {
        padding:0.65rem 0.85rem;
        font-size:0.78rem;
        color:var(--text2);
        line-height:1.55;
        display:none;
      }
      .bl-body.open { display:block }
      .bl-section-label {
        font-size:0.67rem;font-weight:700;color:var(--muted);
        text-transform:uppercase;letter-spacing:.06em;margin-bottom:0.25rem;margin-top:0.5rem;
      }
      .bl-pill-row { display:flex;flex-wrap:wrap;gap:0.3rem;margin-bottom:0.25rem }
      .bl-pill {
        font-size:0.7rem;padding:2px 7px;border-radius:10px;
        background:var(--surface3);color:var(--text2);
      }
      .bl-ai-match {
        font-size:0.72rem;color:var(--blue);background:#eff6ff;
        border-radius:4px;padding:2px 7px;display:inline-block;margin-top:0.2rem;
      }
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
      .bl-empty {
        text-align:center;padding:3rem;color:var(--muted);font-size:0.82rem;
      }
      .bl-tag-chip {
        font-size:0.68rem;padding:1px 6px;border-radius:8px;
        background:#e0f2fe;color:#0369a1;font-weight:600;
      }
    </style>
  `;

  // ── Event handlers ────────────────────────────────────────────────────────

  document.getElementById('bl-sync-btn').onclick    = _onSync;
  document.getElementById('bl-process-btn').onclick = _onProcess;
  document.getElementById('bl-refresh-btn').onclick = _loadAll;

  // Initial load
  await _loadAll();

  // Auto-refresh counters every 30s
  _polling = setInterval(_loadStats, 30_000);
}

// ── Loaders ──────────────────────────────────────────────────────────────────

async function _loadAll() {
  await Promise.all([_loadStats(), _loadEntries()]);
}

async function _loadStats() {
  if (!_project) return;
  try {
    const data = await api.backlog.stats(_project);
    _renderCounters(data);
  } catch (e) {
    document.getElementById('bl-counter-grid').innerHTML =
      `<div style="grid-column:1/-1;color:var(--muted);font-size:0.78rem">Stats unavailable: ${e.message}</div>`;
  }
}

async function _loadEntries() {
  if (!_project) return;
  const el = document.getElementById('bl-entries');
  try {
    const data = await api.backlog.entries(_project);
    _renderEntries(data.entries || []);
  } catch (e) {
    el.innerHTML = `<div class="bl-empty">Could not load backlog: ${e.message}</div>`;
  }
}

// ── Actions ───────────────────────────────────────────────────────────────────

async function _onSync() {
  const btn = document.getElementById('bl-sync-btn');
  _setStatus('Syncing…');
  btn.disabled = true;
  try {
    const r = await api.backlog.syncBacklog(_project);
    const total = r.appended || 0;
    toast(total > 0 ? `Synced — ${total} new entries added` : 'No new rows to process', 'success');
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
      r.approved  ? `${r.approved} approved`   : '',
      r.rejected  ? `${r.rejected} rejected`   : '',
      r.pending   ? `${r.pending} pending`     : '',
      (r.use_cases_updated?.length) ? `${r.use_cases_updated.length} use cases updated` : '',
      (r.tags_created?.length)      ? `${r.tags_created.length} planner tags created`  : '',
    ].filter(Boolean).join(' · ');
    toast(msg || 'No approved entries to process', 'success');
    await _loadAll();
  } catch (e) {
    toast(`Process failed: ${e.message}`, 'error');
  } finally {
    btn.disabled = false;
    _setStatus('');
  }
}

async function _onApprove(refId, entryEl) {
  try {
    await api.backlog.patch(_project, refId, { approve: 'x' });
    entryEl.classList.remove('bl-rejected');
    entryEl.classList.add('bl-approved');
    _updateApproveButtons(entryEl, 'x');
  } catch (e) {
    toast(`Could not approve ${refId}: ${e.message}`, 'error');
  }
}

async function _onReject(refId, entryEl) {
  try {
    await api.backlog.patch(_project, refId, { approve: '-' });
    entryEl.classList.remove('bl-approved');
    entryEl.classList.add('bl-rejected');
    _updateApproveButtons(entryEl, '-');
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
    const batches   = s.batches   ?? 0;
    const cnt       = s.cnt       ?? 5;

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
            <div class="bl-stat-lbl">processed</div>
          </div>
          <div class="bl-stat">
            <div class="bl-stat-n">${batches}</div>
            <div class="bl-stat-lbl">batches×${cnt}</div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function _renderEntries(entries) {
  const el = document.getElementById('bl-entries');
  if (!el) return;

  const pending   = entries.filter(e => e.approve === ' ' || !e.approve);
  const approved  = entries.filter(e => e.approve === 'x');
  const rejected  = entries.filter(e => e.approve === '-');

  if (!entries.length) {
    el.innerHTML = `
      <div class="bl-empty">
        <div style="font-size:2rem;margin-bottom:0.5rem">📭</div>
        <div>Backlog is empty.</div>
        <div style="margin-top:0.4rem;font-size:0.75rem">
          Click <strong>↻ Sync</strong> to flush pending rows from the database into backlog.md.
        </div>
      </div>`;
    return;
  }

  const sections = [
    { label: `Pending (${pending.length})`,   items: pending,  cls: '' },
    { label: `Approved (${approved.length})`, items: approved, cls: 'bl-approved' },
    { label: `Rejected (${rejected.length})`, items: rejected, cls: 'bl-rejected' },
  ];

  el.innerHTML = sections
    .filter(s => s.items.length > 0)
    .map(s => `
      <div style="margin-bottom:1.25rem">
        <div style="font-size:0.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;
                    letter-spacing:.07em;margin-bottom:0.5rem;padding-bottom:0.3rem;
                    border-bottom:1px solid var(--border)">${s.label}</div>
        ${s.items.map(e => _entryHtml(e, s.cls)).join('')}
      </div>
    `).join('');

  // Bind approve/reject buttons
  entries.forEach(entry => {
    const card = document.getElementById(`bl-card-${entry.ref_id}`);
    if (!card) return;

    // Toggle body on header click
    const header = card.querySelector('.bl-entry-header');
    const body   = card.querySelector('.bl-body');
    if (header && body) {
      header.addEventListener('click', e => {
        if (e.target.closest('button')) return;
        body.classList.toggle('open');
      });
    }

    const approveBtn = card.querySelector('.bl-approve-btn');
    const rejectBtn  = card.querySelector('.bl-reject-btn');
    if (approveBtn) approveBtn.addEventListener('click', () => _onApprove(entry.ref_id, card));
    if (rejectBtn)  rejectBtn.addEventListener('click',  () => _onReject(entry.ref_id, card));
  });
}

function _entryHtml(entry, extraCls = '') {
  const ap       = entry.approve || ' ';
  const classify = entry.classify || '';
  const matchSlug = entry.match_slug || '';
  const matchType = entry.match_type || 'none';

  const classifyClass = {
    feature:  'bl-classify-feature',
    bug:      'bl-classify-bug',
    task:     'bl-classify-task',
    use_case: 'bl-classify-use_case',
  }[classify] || 'bl-classify-task';

  const approveActive = ap === 'x' ? 'style="opacity:.4;pointer-events:none"' : '';
  const rejectActive  = ap === '-' ? 'style="opacity:.4;pointer-events:none"' : '';

  // Parse raw markdown body for display
  const raw    = entry.raw || '';
  const reqM   = raw.match(/\*\*Requirements:\*\*\s*([^\n]+)/);
  const reqTxt = reqM ? reqM[1].trim() : '';

  // Action items lines: "- [ ] ..."
  const aiLines = (raw.match(/- \[ \] .+/g) || []).slice(0, 3);

  const matchChip = (matchType !== 'none' && matchSlug)
    ? `<span class="bl-ai-match">→ ${matchType === 'new' ? '✦ new: ' : ''}${matchSlug}</span>`
    : '';

  const tagChip = entry.tag
    ? `<span class="bl-tag-chip">🏷 ${entry.tag}</span>`
    : '';

  return `
    <div class="bl-entry ${extraCls}" id="bl-card-${entry.ref_id}">
      <div class="bl-entry-header">
        <span class="bl-ref">${entry.ref_id}</span>
        <span class="bl-date">${entry.date || ''}</span>
        <span class="bl-summary" title="${_esc(entry.summary || '')}">${_esc(entry.summary || '')}</span>
        ${classify ? `<span class="bl-classify ${classifyClass}">${classify}</span>` : ''}
        ${tagChip}
        <button class="bl-approve-btn" ${approveActive} title="Approve — will be merged into use case on next Process">✓</button>
        <button class="bl-reject-btn"  ${rejectActive}  title="Reject — will be archived">✗</button>
      </div>
      ${(reqTxt || aiLines.length || matchChip) ? `
      <div class="bl-body">
        ${reqTxt ? `<div class="bl-section-label">Requirements</div>
          <div style="margin-bottom:0.4rem;color:var(--text)">${_esc(reqTxt)}</div>` : ''}
        ${aiLines.length ? `<div class="bl-section-label">Action items</div>
          <ul style="margin:0 0 0.4rem;padding-left:1.2rem">
            ${aiLines.map(l => `<li>${_esc(l.replace('- [ ] ', ''))}</li>`).join('')}
          </ul>` : ''}
        ${matchChip}
      </div>` : ''}
    </div>
  `;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _updateApproveButtons(card, val) {
  const approveBtn = card.querySelector('.bl-approve-btn');
  const rejectBtn  = card.querySelector('.bl-reject-btn');
  if (approveBtn) approveBtn.style.opacity = val === 'x' ? '.4' : '1';
  if (approveBtn) approveBtn.style.pointerEvents = val === 'x' ? 'none' : '';
  if (rejectBtn)  rejectBtn.style.opacity  = val === '-' ? '.4' : '1';
  if (rejectBtn)  rejectBtn.style.pointerEvents = val === '-' ? 'none' : '';
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
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
