/**
 * backlog.js — Backlog tab view.
 *
 * GROUP sections (one per use-case cluster) show:
 *   - Header: slug, counts, date, [Approve all] [Reject all]
 *   - Body: summary text, requirements paragraph, deliveries table (sorted
 *     completed-first, up to 7), then expandable item rows
 *
 * Commit items are informational-only — already committed, nothing to approve.
 * Prompt items have classify/status dropdowns and a remove button.
 */

import { api }  from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { state } from '../stores/state.js';

let _project      = '';
let _polling      = null;
let _allSlugs     = [];          // all known slugs
let _fileSlugs    = new Set();   // slugs that have a use_cases/*.md file
let _groupSlugs   = new Set();   // slugs only in backlog groups (NEW)
let _plannerTags  = [];          // planner tags for tag picker
let _undoStack    = [];          // [{label, fn}] — undo stack (last 10 ops)

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
        <button id="bl-export-btn" class="btn btn-ghost btn-sm"
                title="Export commit analysis report to workspace/logs/">
          📊 Export
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
        display:flex;align-items:center;gap:0.6rem;flex-wrap:wrap;
        padding:0.65rem 1rem;
        background:var(--surface2);
        border-bottom:1px solid var(--border);
        cursor:pointer;user-select:none;
      }
      .bl-group-header:hover { background:var(--surface3); }
      .bl-group-slug {
        font-size:0.92rem;font-weight:800;color:var(--text);
        letter-spacing:-.01em;
      }
      .bl-group-meta {
        font-size:0.69rem;color:var(--muted);
        display:flex;align-items:center;gap:0.45rem;flex-wrap:wrap;
      }
      .bl-group-counts {
        font-size:0.67rem;color:var(--muted);
        background:var(--surface3);padding:1px 7px;border-radius:8px;
      }
      .bl-group-arrow { font-size:0.7rem;color:var(--muted);margin-left:0 }
      .bl-group-body { padding:0.75rem 1rem }
      .bl-group-body.collapsed { display:none }

      /* ── Approve/Reject in header ── */
      .bl-approve-all-btn, .bl-reject-all-btn {
        border:none;border-radius:4px;padding:3px 11px;cursor:pointer;
        font-size:0.74rem;font-weight:700;transition:opacity .15s;flex-shrink:0;
      }
      .bl-approve-all-btn { background:#16a34a;color:#fff }
      .bl-reject-all-btn  { background:#dc2626;color:#fff }
      .bl-approve-all-btn:hover { opacity:.85 }
      .bl-reject-all-btn:hover  { opacity:.85 }
      .bl-approve-all-btn:disabled, .bl-reject-all-btn:disabled {
        opacity:.35;cursor:not-allowed;
      }
      /* hide approve/reject for commit-only groups */
      .bl-commits-only .bl-approve-all-btn,
      .bl-commits-only .bl-reject-all-btn { display:none }

      /* ── Tag chips ── */
      .bl-tags-row { display:flex;flex-wrap:wrap;gap:0.3rem;margin-bottom:0.55rem;align-items:center }
      .bl-chip {
        font-size:0.67rem;padding:2px 7px;border-radius:10px;font-weight:600;
        display:inline-flex;align-items:center;gap:3px;
      }
      .bl-chip-user     { background:#f3f4f6;color:#374151;border:1px solid #d1d5db }
      .bl-chip-existing { background:#dbeafe;color:#1d4ed8 }
      .bl-chip-new      { background:#fef9c3;color:#854d0e }
      .bl-chip-type-new { background:#fce7f3;color:#9d174d;font-size:0.61rem;padding:1px 5px }
      .bl-chip-remove {
        background:none;border:none;cursor:pointer;padding:0;margin-left:2px;
        color:inherit;opacity:.55;font-size:0.75rem;line-height:1;
      }
      .bl-chip-remove:hover { opacity:1 }
      .bl-tag-add-btn {
        font-size:0.67rem;padding:2px 7px;border-radius:10px;font-weight:600;
        background:none;border:1px dashed #9ca3af;color:var(--muted);cursor:pointer;
      }
      .bl-tag-add-btn:hover { border-color:var(--accent);color:var(--accent) }
      .bl-tag-input-wrap { display:flex;align-items:center;gap:4px }
      .bl-tag-input {
        font-size:0.67rem;padding:2px 6px;border-radius:8px;
        border:1px solid var(--accent);outline:none;background:var(--surface);
        color:var(--text);width:130px;
      }

      /* ── Group summary ── */
      .bl-group-summary {
        font-size:0.81rem;color:var(--text2);line-height:1.55;
        margin-bottom:0.6rem;padding:0.45rem 0.7rem;
        background:var(--surface3);border-radius:calc(var(--radius) - 2px);
        border-left:3px solid var(--accent);
      }

      /* ── Requirements block ── */
      .bl-group-reqs {
        font-size:0.78rem;color:var(--text2);line-height:1.5;
        margin-bottom:0.65rem;
      }
      .bl-group-reqs-label {
        font-size:0.65rem;font-weight:800;color:var(--muted);
        text-transform:uppercase;letter-spacing:.07em;margin-bottom:0.2rem;
      }

      /* ── Deliveries table ── */
      .bl-deliveries-section { margin-bottom:0.75rem }
      .bl-deliveries-label {
        font-size:0.65rem;font-weight:800;color:var(--muted);
        text-transform:uppercase;letter-spacing:.07em;margin-bottom:0.3rem;
      }
      .bl-deliveries-table {
        width:100%;border-collapse:collapse;font-size:0.76rem;
      }
      .bl-deliveries-table td {
        padding:3px 6px;vertical-align:middle;
        border-bottom:1px solid var(--border);
      }
      .bl-deliveries-table tr:last-child td { border-bottom:none }
      .bl-delivery-icon { font-size:0.8rem;width:20px;text-align:center }
      .bl-delivery-type {
        font-size:0.62rem;padding:1px 5px;border-radius:6px;font-weight:700;
        white-space:nowrap;
      }
      .bl-delivery-type-feature { background:#dcfce7;color:#16a34a }
      .bl-delivery-type-bug     { background:#fee2e2;color:#dc2626 }
      .bl-delivery-type-task    { background:#dbeafe;color:#1d4ed8 }
      .bl-delivery-type-use_case{ background:#cffafe;color:#0e7490 }
      .bl-delivery-score {
        font-size:0.62rem;color:var(--muted);background:var(--surface3);
        padding:1px 5px;border-radius:6px;white-space:nowrap;
      }
      .bl-delivery-desc {
        color:var(--text);flex:1;
        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:340px;
      }
      .bl-delivery-status-done { color:#16a34a }
      .bl-delivery-status-prog { color:#c2410c }
      .bl-delivery-remove {
        background:none;border:none;cursor:pointer;padding:0 2px;
        color:var(--muted);font-size:0.75rem;opacity:.5;
      }
      .bl-delivery-remove:hover { opacity:1;color:#dc2626 }

      /* ── Items divider ── */
      .bl-items-divider {
        font-size:0.65rem;font-weight:800;color:var(--muted);
        text-transform:uppercase;letter-spacing:.06em;
        margin:0.5rem 0 0.35rem;
        border-top:1px solid var(--border);padding-top:0.45rem;
        display:flex;align-items:center;gap:0.4rem;
      }

      /* ── Source type label ── */
      .bl-src-section { margin-bottom:0.4rem }
      .bl-src-label {
        font-size:0.62rem;font-weight:800;color:var(--muted);
        text-transform:uppercase;letter-spacing:.08em;margin-bottom:0.25rem;
      }

      /* ── Item card ── */
      .bl-entry {
        border:1px solid var(--border);
        border-radius:calc(var(--radius) - 2px);
        background:var(--surface);
        margin-bottom:0.35rem;
        overflow:hidden;
      }
      .bl-entry-header {
        display:flex;align-items:center;gap:0.45rem;flex-wrap:wrap;
        padding:0.4rem 0.7rem;
        background:var(--surface2);
        cursor:pointer;user-select:none;
      }
      .bl-entry-header:hover { background:var(--surface3); }
      .bl-ref { font-family:var(--font);font-size:0.68rem;font-weight:700;color:var(--accent);min-width:65px }
      .bl-summary {
        flex:1;font-size:0.79rem;color:var(--text);
        white-space:nowrap;overflow:hidden;text-overflow:ellipsis;min-width:0;
      }
      .bl-ai-score {
        font-size:0.62rem;color:var(--muted);background:var(--surface3);
        padding:1px 5px;border-radius:7px;flex-shrink:0;
      }

      /* ── Item controls (prompts only) ── */
      .bl-item-select {
        font-size:0.69rem;border:1px solid var(--border);border-radius:4px;
        background:var(--surface);color:var(--text);padding:1px 3px;
        cursor:pointer;flex-shrink:0;
      }
      .bl-item-select:focus { outline:none;border-color:var(--accent) }
      .bl-remove-btn {
        border:none;border-radius:4px;padding:1px 6px;cursor:pointer;
        font-size:0.75rem;font-weight:700;background:transparent;color:var(--muted);
        transition:color .15s,background .15s;flex-shrink:0;
      }
      .bl-remove-btn:hover { background:#fee2e2;color:#dc2626 }

      /* ── Commit item badge ── */
      .bl-commit-badge {
        font-size:0.62rem;padding:1px 6px;border-radius:7px;font-weight:700;
        background:#f0fdf4;color:#16a34a;border:1px solid #86efac;flex-shrink:0;
      }

      /* ── Item body ── */
      .bl-body {
        padding:0.45rem 0.7rem;
        font-size:0.76rem;color:var(--text2);line-height:1.5;
        display:none;border-top:1px solid var(--border);
      }
      .bl-body.open { display:block }
      .bl-body-label {
        font-size:0.63rem;font-weight:700;color:var(--muted);
        text-transform:uppercase;letter-spacing:.06em;margin-bottom:0.12rem;
      }
      .bl-body-text { color:var(--text);font-size:0.77rem;line-height:1.5;margin-bottom:0.3rem }

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

      /* ── Undo panel ── */
      .bl-undo-panel {
        position:fixed;bottom:1rem;right:1rem;width:300px;
        background:#1e293b;border:1px solid #334155;border-radius:8px;
        z-index:9999;box-shadow:0 4px 20px rgba(0,0,0,.4);
      }
      .bl-undo-panel-hdr {
        display:flex;justify-content:space-between;align-items:center;
        padding:0.4rem 0.75rem;font-size:0.72rem;color:#94a3b8;
        border-bottom:1px solid #334155;
      }
      .bl-undo-row {
        display:flex;align-items:center;gap:0.5rem;padding:0.35rem 0.75rem;
        border-bottom:1px solid #283040;font-size:0.78rem;color:#cbd5e1;
      }
      .bl-undo-row:last-child { border-bottom:none }
      .bl-undo-row-btn {
        background:#334155;border:none;color:#f8fafc;border-radius:4px;
        padding:1px 6px;cursor:pointer;font-size:0.78rem;flex-shrink:0;
      }
      .bl-undo-row-btn:hover { background:#475569 }
      .bl-undo-clear-btn { background:none;border:none;color:#64748b;cursor:pointer;font-size:1rem }

      /* ── Use case open items section ── */
      .bl-uc-section { margin-top:0.75rem;padding-top:0.75rem;border-top:1px solid #2d3748 }
      .bl-uc-section-title {
        font-size:0.7rem;color:#64748b;text-transform:uppercase;
        letter-spacing:.07em;margin-bottom:0.4rem;
      }
      .bl-uc-badges { display:flex;gap:0.5rem;margin-bottom:0.4rem;flex-wrap:wrap }
      .bl-uc-badge {
        font-size:0.72rem;padding:2px 8px;border-radius:10px;
        background:#1e3347;color:#60a5fa;
      }
      .bl-uc-badge.empty { background:#1e293b;color:#475569 }
      .bl-uc-item-row {
        display:flex;align-items:flex-start;gap:0.4rem;
        padding:0.2rem 0;font-size:0.77rem;color:#cbd5e1;
      }
      .bl-uc-item-score { color:#f59e0b;font-size:0.68rem;flex-shrink:0;min-width:2.8rem }
      .bl-uc-item-body { flex:1;min-width:0 }
      .bl-uc-item-desc { line-height:1.35 }
      .bl-uc-item-ref { font-size:0.67rem;color:#475569 }
      .bl-uc-item-remove {
        background:none;border:none;color:#475569;cursor:pointer;
        padding:0 3px;flex-shrink:0;line-height:1;
      }
      .bl-uc-item-remove:hover { color:#ef4444 }

      /* ── Requirements bullets ── */
      .bl-req-row {
        display:flex;align-items:baseline;gap:5px;padding:2px 0;
      }
      .bl-req-bullet { color:var(--muted);flex-shrink:0 }
      .bl-req-text   { flex:1;font-size:0.78rem;color:var(--text) }
      .bl-req-remove {
        border:none;background:transparent;color:var(--muted);
        font-size:0.68rem;cursor:pointer;padding:0 2px;opacity:.4;flex-shrink:0;
      }
      .bl-req-remove:hover { color:#dc2626;opacity:1 }

      /* ── Code stats bar ── */
      .bl-code-stats-bar { margin-bottom:0.4rem }
      .bl-stats-row { display:flex;flex-wrap:wrap;align-items:center;gap:0.3rem }
      .bl-stat-chip {
        font-size:0.64rem;padding:1px 6px;border-radius:8px;
        background:var(--surface3);color:var(--muted);border:1px solid var(--border);
      }
      .bl-stat-added   { background:#f0fdf4;color:#16a34a;border-color:#86efac }
      .bl-stat-removed { background:#fef2f2;color:#dc2626;border-color:#fca5a5 }
      .bl-stats-files  { font-size:0.68rem;color:var(--muted) }
      .bl-stats-files summary { cursor:pointer;user-select:none }
      .bl-stats-file-row { display:flex;align-items:center;gap:4px;padding:1px 4px }
      .bl-stats-file-path { flex:1;font-family:monospace;font-size:0.68rem;color:var(--text2) }

      /* ── Overlay dropdown ── */
      .bl-overlay {
        position:fixed;z-index:9999;
        background:var(--surface);border:1px solid var(--border);
        border-radius:var(--radius);box-shadow:0 4px 16px rgba(0,0,0,.18);
        min-width:200px;max-width:320px;overflow:hidden;
      }
      .bl-overlay-input {
        display:block;width:100%;box-sizing:border-box;
        font-size:0.8rem;padding:0.45rem 0.65rem;
        border:none;border-bottom:1px solid var(--border);
        background:var(--surface);color:var(--text);outline:none;
      }
      .bl-overlay-list { max-height:220px;overflow-y:auto }
      .bl-overlay-item {
        padding:5px 12px;font-size:0.78rem;cursor:pointer;color:var(--text);
      }
      .bl-overlay-item:hover, .bl-overlay-item.active { background:var(--surface2) }
      .bl-overlay-cat {
        padding:4px 10px 2px;font-size:0.62rem;font-weight:700;
        color:var(--muted);text-transform:uppercase;letter-spacing:.06em;
        border-top:1px solid var(--border);
      }

      /* ── Slug combobox ── */
      .bl-slug-wrap { display:inline-flex;align-items:center;gap:0.3rem;cursor:pointer }
      .bl-slug-edit-btn {
        border:none;background:transparent;color:var(--muted);font-size:0.65rem;
        cursor:pointer;padding:0 2px;opacity:0;transition:opacity .15s;line-height:1;
      }
      .bl-group-header:hover .bl-slug-edit-btn { opacity:1 }

      /* ── Summary inline edit ── */
      .bl-summary-wrap { position:relative }
      .bl-summary-edit-btn {
        position:absolute;top:4px;right:6px;
        border:none;background:transparent;color:var(--muted);font-size:0.65rem;
        cursor:pointer;padding:0 2px;opacity:0;transition:opacity .15s;
      }
      .bl-summary-wrap:hover .bl-summary-edit-btn { opacity:1 }
      .bl-summary-textarea {
        width:100%;box-sizing:border-box;
        font-size:0.81rem;line-height:1.55;
        border:1px solid var(--accent);border-radius:calc(var(--radius) - 2px);
        padding:0.4rem 0.65rem;background:var(--surface);color:var(--text);
        resize:vertical;min-height:60px;
      }
    </style>
  `;

  document.getElementById('bl-sync-btn').onclick = _onSync;
  document.getElementById('bl-export-btn').onclick = async () => {
    const btn = document.getElementById('bl-export-btn');
    btn.disabled = true; btn.textContent = '⏳ Exporting…';
    try {
      const r = await api.backlog.exportCommitAnalysis(_project);
      toast(`Report saved: ${r.file} (${r.linked_commits} linked, ${r.standalone_commits} standalone commits)`, 'success');
    } catch (e) { toast(`Export failed: ${e.message}`, 'error'); }
    finally { btn.disabled = false; btn.textContent = '📊 Export'; }
  };

  await _loadAll();
  _polling = setInterval(_loadStats, 30_000);
}

// ── Loaders ───────────────────────────────────────────────────────────────────

async function _loadAll() {
  await Promise.all([_loadStats(), _loadEntries(), _loadSlugs(), _loadPlannerTags()]);
}

async function _loadSlugs() {
  if (!_project) return;
  try {
    const data = await api.backlog.listSlugs(_project);
    _allSlugs = data.slugs || [];
    _fileSlugs = new Set(data.file_slugs || []);
    _groupSlugs = new Set(data.group_slugs || []);
  } catch { /* non-critical */ }
}

async function _loadPlannerTags() {
  if (!_project) return;
  try {
    const data = await api.backlog.listPlannerTags(_project);
    _plannerTags = Array.isArray(data) ? data : (data.tags || []);
  } catch { /* non-critical */ }
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

function _flatToGroups(entries) {
  if (!entries.length) return [];
  return [{ slug: 'backlog', slug_type: 'existing', date: '', source: 'auto',
            approve: ' ', user_tags: [], ai_existing_tags: [], ai_new_tags: [],
            summary: '', requirements: [], deliveries: [], items: entries }];
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

async function _onSlugChange(oldSlug, newSlug, slugWrapEl) {
  if (!newSlug || newSlug === oldSlug) return;
  try {
    await api.backlog.patchGroup(_project, oldSlug, { new_slug: newSlug });
    // Update the wrap element's data attribute and visible text
    slugWrapEl.dataset.slug = newSlug;
    const textEl = slugWrapEl.querySelector('.bl-slug-text');
    if (textEl) textEl.textContent = newSlug;
    // Add new slug to datalist
    if (!_allSlugs.includes(newSlug)) {
      _allSlugs.push(newSlug);
      _updateSlugsDatalist();
    }
    toast(`Renamed → ${newSlug}`, 'success');
  } catch (e) {
    toast(`Rename failed: ${e.message}`, 'error');
  }
}

async function _onSummaryEdit(slug, newText, summaryEl) {
  try {
    await api.backlog.patchGroup(_project, slug, { summary: newText });
    // Update the displayed summary text
    const textNode = summaryEl.querySelector('.bl-summary-text');
    if (textNode) textNode.textContent = newText;
    toast('Summary updated', 'success');
  } catch (e) {
    toast(`Summary update failed: ${e.message}`, 'error');
  }
}

function _pushUndo(label, undoFn) {
  _undoStack.unshift({ label, fn: undoFn });
  if (_undoStack.length > 5) _undoStack.pop();
  _renderUndoPanel();
}

function _renderUndoPanel() {
  let panel = document.getElementById('bl-undo-panel');
  if (!_undoStack.length) {
    if (panel) panel.remove();
    return;
  }
  if (!panel) {
    panel = document.createElement('div');
    panel.id = 'bl-undo-panel';
    panel.className = 'bl-undo-panel';
    document.body.appendChild(panel);
  }
  panel.innerHTML = `
    <div class="bl-undo-panel-hdr">
      <span>Undo history</span>
      <button class="bl-undo-clear-btn" title="Clear all">×</button>
    </div>
    ${_undoStack.map((op, i) => `
      <div class="bl-undo-row">
        <button class="bl-undo-row-btn" data-idx="${i}">↩</button>
        <span>${_esc(op.label)}</span>
      </div>`).join('')}`;
  panel.querySelector('.bl-undo-clear-btn').addEventListener('click', () => {
    _undoStack.length = 0;
    panel.remove();
  });
  panel.querySelectorAll('.bl-undo-row-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const i = parseInt(btn.dataset.idx, 10);
      const op = _undoStack.splice(i, 1)[0];
      if (op) op.fn();
      _renderUndoPanel();
    });
  });
}

async function _onDeliveryRemove(slug, index, desc, rowEl) {
  try {
    await api.backlog.patchGroup(_project, slug, { remove_delivery_index: index });
    if (rowEl) rowEl.remove();
    _pushUndo(`Removed delivery: ${desc.slice(0,40)}`, async () => {
      await api.backlog.patchGroup(_project, slug, { restore_delivery: desc });
      await _loadEntries();
    });
  } catch (e) { toast(`Could not remove delivery: ${e.message}`, 'error'); }
}

async function _onAiNewTagRemove(slug, index, tagLabel, chipEl) {
  try {
    await api.backlog.patchGroup(_project, slug, { remove_ai_new_tag_index: index });
    if (chipEl) chipEl.remove();
    _pushUndo(`Dismissed tag: ${tagLabel}`, async () => {
      await api.backlog.patchGroup(_project, slug, { restore_ai_new_tag: tagLabel });
      await _loadEntries();
    });
  } catch (e) { toast(`Could not remove tag suggestion: ${e.message}`, 'error'); }
}

async function _onRequirementRemove(slug, index, text, rowEl) {
  try {
    await api.backlog.patchGroup(_project, slug, { remove_requirement_index: index });
    if (rowEl) rowEl.remove();
    _pushUndo(`Removed requirement`, async () => {
      await api.backlog.patchGroup(_project, slug, { add_requirement: text });
      await _loadEntries();
    });
  } catch (e) { toast(`Could not remove requirement: ${e.message}`, 'error'); }
}

async function _onTagsUpdate(slug, newTags, tagsRowEl, previousTags) {
  const prev = previousTags || [];
  try {
    await api.backlog.patchGroup(_project, slug, { user_tags: newTags });
    // Rebuild user-tag chips in-place
    tagsRowEl.querySelectorAll('.bl-chip-user').forEach(c => c.remove());
    const addBtn = tagsRowEl.querySelector('.bl-tag-add-btn');
    newTags.forEach((t, i) => {
      const chip = document.createElement('span');
      chip.className = 'bl-chip bl-chip-user';
      chip.innerHTML = `🏷 ${_esc(t)}<button class="bl-chip-remove" data-tag-idx="${i}" title="Remove tag">&times;</button>`;
      chip.querySelector('.bl-chip-remove').addEventListener('click', e => {
        e.stopPropagation();
        const updated = [...newTags]; updated.splice(i, 1);
        _onTagsUpdate(slug, updated, tagsRowEl, newTags);
      });
      tagsRowEl.insertBefore(chip, addBtn);
    });
    if (prev.join(',') !== newTags.join(',')) {
      _pushUndo('Tag change', async () => {
        await _onTagsUpdate(slug, prev, tagsRowEl, newTags);
      });
    }
    toast('Tags updated', 'success');
  } catch (e) { toast(`Tag update failed: ${e.message}`, 'error'); }
}

// ── Overlay helpers ────────────────────────────────────────────────────────────

/**
 * Show a slug-picker overlay anchored to `anchorEl`.
 * Displays all known slugs in a scrollable list + a free-text input at top.
 * Calls onConfirm(slug) when the user picks or types a value.
 */
function _showSlugPicker(currentSlug, anchorEl, onConfirm) {
  _closeOverlay();
  const overlay = document.createElement('div');
  overlay.id = 'bl-overlay';
  overlay.className = 'bl-overlay';

  const inp = document.createElement('input');
  inp.type = 'text';
  inp.value = currentSlug;
  inp.className = 'bl-overlay-input';
  inp.placeholder = 'Type a name or choose below…';

  const list = document.createElement('div');
  list.className = 'bl-overlay-list';

  const renderList = (filter = '') => {
    const f = filter.toLowerCase();
    const existing = _allSlugs.filter(s => _fileSlugs.has(s) && (!f || s.includes(f)));
    const newOnes  = _allSlugs.filter(s => !_fileSlugs.has(s) && (!f || s.includes(f)));
    let html = '';
    if (existing.length) {
      html += `<div class="bl-overlay-cat">Existing use cases</div>`;
      html += existing.map(s =>
        `<div class="bl-overlay-item${s === currentSlug ? ' active' : ''}" data-val="${_esc(s)}">${_esc(s)}</div>`
      ).join('');
    }
    if (newOnes.length) {
      html += `<div class="bl-overlay-cat" style="color:#854d0e">New (pending)</div>`;
      html += newOnes.map(s =>
        `<div class="bl-overlay-item bl-overlay-item-new${s === currentSlug ? ' active' : ''}" data-val="${_esc(s)}"><span style="color:#854d0e;font-size:0.6rem;font-weight:700;margin-right:4px">NEW:</span>${_esc(s)}</div>`
      ).join('');
    }
    if (!html) html = `<div style="padding:6px 10px;color:var(--muted);font-size:0.76rem">No use cases yet — type a name above</div>`;
    list.innerHTML = html;
    list.querySelectorAll('.bl-overlay-item').forEach(it => {
      it.addEventListener('mousedown', e => {
        e.preventDefault();
        _closeOverlay();
        onConfirm(it.dataset.val);
      });
    });
  };
  renderList();

  inp.addEventListener('input', () => renderList(inp.value));
  inp.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); const v = inp.value.trim(); _closeOverlay(); if (v) onConfirm(v); }
    if (e.key === 'Escape') _closeOverlay();
  });
  inp.addEventListener('blur', () => setTimeout(_closeOverlay, 150));

  overlay.appendChild(inp);
  overlay.appendChild(list);
  document.body.appendChild(overlay);

  const rect = anchorEl.getBoundingClientRect();
  overlay.style.top  = `${rect.bottom + window.scrollY + 4}px`;
  overlay.style.left = `${rect.left + window.scrollX}px`;
  inp.focus(); inp.select();
}

/**
 * Show a tag-picker overlay anchored to `anchorEl`.
 * Shows planner tags grouped by category + free-text fallback.
 * Calls onConfirm(tagStr) with "category:name" format.
 */
function _showTagPicker(anchorEl, onConfirm) {
  _closeOverlay();
  const overlay = document.createElement('div');
  overlay.id = 'bl-overlay';
  overlay.className = 'bl-overlay';

  const inp = document.createElement('input');
  inp.type = 'text';
  inp.className = 'bl-overlay-input';
  inp.placeholder = 'Search or type phase:dev, feature:auth…';

  const list = document.createElement('div');
  list.className = 'bl-overlay-list';

  const renderTagList = (filter = '') => {
    const f = filter.toLowerCase();
    // Group planner tags by category
    const byCategory = {};
    for (const t of _plannerTags) {
      const cat = t.category_name || 'tag';
      const label = `${cat}:${t.name}`;
      if (!f || label.includes(f)) {
        (byCategory[cat] = byCategory[cat] || []).push(t);
      }
    }
    const sections = Object.entries(byCategory).map(([cat, tags]) => `
      <div class="bl-overlay-cat">${_esc(cat)}</div>
      ${tags.map(t => `<div class="bl-overlay-item" data-val="${_esc(cat)}:${_esc(t.name)}">${_esc(t.name)}</div>`).join('')}
    `).join('');
    list.innerHTML = sections || `<div style="padding:6px 10px;color:var(--muted);font-size:0.76rem">No tags found — press Enter to create</div>`;
    list.querySelectorAll('.bl-overlay-item').forEach(it => {
      it.addEventListener('mousedown', e => {
        e.preventDefault();
        _closeOverlay();
        onConfirm(it.dataset.val);
      });
    });
  };
  renderTagList();

  inp.addEventListener('input', () => renderTagList(inp.value));
  inp.addEventListener('keydown', e => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const val = inp.value.trim();
      _closeOverlay();
      if (val) onConfirm(val);
    }
    if (e.key === 'Escape') _closeOverlay();
  });
  inp.addEventListener('blur', () => setTimeout(_closeOverlay, 150));

  overlay.appendChild(inp);
  overlay.appendChild(list);
  document.body.appendChild(overlay);

  const rect = anchorEl.getBoundingClientRect();
  overlay.style.top  = `${rect.bottom + window.scrollY + 4}px`;
  overlay.style.left = `${rect.left  + window.scrollX}px`;
  inp.focus();
}

function _closeOverlay() {
  const el = document.getElementById('bl-overlay');
  if (el) el.remove();
}

async function _loadGroupCodeStats(slug, idx) {
  const el = document.getElementById(`bl-stats-${idx}`);
  if (!el) return;
  try {
    const s = await api.backlog.codeStats(_project, slug);
    if (!s.linked_commits && !s.files_changed) { el.innerHTML = ''; return; }
    const chips = [
      s.linked_commits ? `<span class="bl-stat-chip">🔗 ${s.linked_commits} commit${s.linked_commits !== 1 ? 's' : ''}</span>` : '',
      s.files_changed  ? `<span class="bl-stat-chip">📄 ${s.files_changed} file${s.files_changed !== 1 ? 's' : ''}</span>` : '',
      s.rows_added     ? `<span class="bl-stat-chip bl-stat-added">+${s.rows_added} lines</span>` : '',
      s.rows_removed   ? `<span class="bl-stat-chip bl-stat-removed">-${s.rows_removed} lines</span>` : '',
    ].filter(Boolean).join('');
    const topFiles = s.top_files && s.top_files.length
      ? `<details class="bl-stats-files"><summary style="font-size:0.67rem;color:var(--muted);cursor:pointer">Top files ▾</summary>${
          s.top_files.map(f => `<div class="bl-stats-file-row">
            <span class="bl-stats-file-path">${_esc(f.path.split('/').slice(-2).join('/'))}</span>
            <span class="bl-stat-chip bl-stat-added" style="font-size:0.6rem">+${f.added}</span>
            <span class="bl-stat-chip bl-stat-removed" style="font-size:0.6rem">-${f.removed}</span>
          </div>`).join('')}</details>` : '';
    el.innerHTML = `<div class="bl-stats-row">${chips}${topFiles}</div>`;

    // Also update the header count badge to show commit count
    const grpEl = document.getElementById(`bl-grp-${idx}`);
    if (grpEl && s.linked_commits > 0) {
      const countsBadge = grpEl.querySelector('.bl-group-counts');
      if (countsBadge && !countsBadge.textContent.includes('commit')) {
        countsBadge.textContent += ` · 🔗${s.linked_commits}`;
      }
    }
  } catch { el.innerHTML = ''; }
}

// ── Use case item loaders ──────────────────────────────────────────────────────

async function _loadUseCaseItems(slug, containerEl) {
  if (!containerEl) return;
  try {
    const data = await api.backlog.listUseCaseItems(_project, slug);
    const openItems = data.open_items || [];
    const openBugs  = data.open_bugs  || [];
    if (!openItems.length && !openBugs.length) { containerEl.innerHTML = ''; return; }

    const itemRow = (item, section) => `
      <div class="bl-uc-item-row" data-ref="${_esc(item.ref_id)}" data-section="${_esc(section)}">
        <span class="bl-uc-item-score">AI:${item.ai_score ?? '?'}</span>
        <div class="bl-uc-item-body">
          <div class="bl-uc-item-desc">${_esc(item.desc)}</div>
          ${item.ref_id ? `<div class="bl-uc-item-ref">${_esc(item.ref_id)}</div>` : ''}
        </div>
        <button class="bl-uc-item-remove" title="Remove from use case">✕</button>
      </div>`;

    containerEl.innerHTML = `
      <div class="bl-uc-section">
        <div class="bl-uc-section-title">── Use case open items ──────────────────────────</div>
        <div class="bl-uc-badges">
          <span class="bl-uc-badge${!openItems.length ? ' empty' : ''}">● Open Items (${openItems.length})</span>
          <span class="bl-uc-badge${!openBugs.length ? ' empty' : ''}">● Open Bugs (${openBugs.length})</span>
        </div>
        ${openItems.map(it => itemRow(it, 'Open Items')).join('')}
        ${openBugs.map(it => itemRow(it, 'Open Bugs')).join('')}
      </div>`;

    containerEl.querySelectorAll('.bl-uc-item-remove').forEach(btn => {
      const row     = btn.closest('.bl-uc-item-row');
      const refId   = row.dataset.ref;
      const section = row.dataset.section;
      btn.addEventListener('click', () => _onUseCaseItemRemove(slug, refId, section, row, containerEl));
    });
  } catch { containerEl.innerHTML = ''; }
}

async function _onUseCaseItemRemove(slug, refId, section, rowEl, containerEl) {
  try {
    const resp = await api.backlog.deleteUseCaseItem(_project, { slug, ref_id: refId });
    rowEl.remove();
    const restoredSection = resp.section || section;
    const deletedText     = resp.deleted_text;
    _pushUndo(`Removed from ${slug}: ${refId}`, async () => {
      await api.backlog.restoreUseCaseItem(_project, { slug, section: restoredSection, text: deletedText });
      await _loadUseCaseItems(slug, containerEl);
    });
  } catch (e) { toast(`Could not remove item: ${e.message}`, 'error'); }
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
          <div class="bl-stat"><div class="bl-stat-n ${pending > 0 ? 'warn' : 'ok'}">${pending}</div><div class="bl-stat-lbl">open</div></div>
          <div class="bl-stat"><div class="bl-stat-n">${processed}</div><div class="bl-stat-lbl">done</div></div>
          <div class="bl-stat"><div class="bl-stat-n">${batches}</div><div class="bl-stat-lbl">×${cnt}</div></div>
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

  groups.forEach((grp, gi) => {
    const grpEl = document.getElementById(`bl-grp-${gi}`);
    if (!grpEl) return;

    // Group collapse toggle
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

    // Group-level approve/reject (skip for commits-only groups)
    const apAllBtn = grpEl.querySelector('.bl-approve-all-btn');
    const rjAllBtn = grpEl.querySelector('.bl-reject-all-btn');
    if (apAllBtn) apAllBtn.addEventListener('click', () => _onGroupApprove(grp.slug));
    if (rjAllBtn) rjAllBtn.addEventListener('click', () => _onGroupReject(grp.slug));

    // Slug rename — edit button inside .bl-slug-wrap → shows overlay dropdown
    const slugWrap = grpEl.querySelector('.bl-slug-wrap');
    const slugEditBtn = grpEl.querySelector('.bl-slug-edit-btn');
    if (slugWrap && slugEditBtn) {
      slugEditBtn.addEventListener('click', e => {
        e.stopPropagation();
        const currentSlug = slugWrap.dataset.slug || grp.slug;
        _showSlugPicker(currentSlug, slugWrap, async newSlug => {
          await _onSlugChange(currentSlug, newSlug, slugWrap);
        });
      });
    }

    // Summary inline edit
    const sumWrap = grpEl.querySelector('.bl-summary-wrap');
    const sumEditBtn = grpEl.querySelector('.bl-summary-edit-btn');
    if (sumWrap && sumEditBtn) {
      sumEditBtn.addEventListener('click', e => {
        e.stopPropagation();
        const currentText = sumWrap.querySelector('.bl-summary-text')?.textContent || '';
        const currentSlug = slugWrap?.dataset.slug || grp.slug;
        const ta = document.createElement('textarea');
        ta.value = currentText;
        ta.className = 'bl-summary-textarea';
        sumWrap.style.display = 'none';
        sumWrap.parentNode.insertBefore(ta, sumWrap.nextSibling);
        ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length);
        const save = async () => {
          const newText = ta.value.trim();
          ta.remove();
          sumWrap.style.display = '';
          if (newText !== currentText) {
            await _onSummaryEdit(currentSlug, newText, sumWrap);
          }
        };
        ta.addEventListener('blur', save);
        ta.addEventListener('keydown', e2 => {
          if (e2.key === 'Escape') { ta.remove(); sumWrap.style.display = ''; }
        });
      });
    }

    // Delivery remove buttons (synthesized themes)
    grpEl.querySelectorAll('.bl-delivery-remove').forEach(btn => {
      const idx   = parseInt(btn.dataset.deliveryIdx, 10);
      const dSlug = btn.dataset.deliverySlug || grp.slug;
      const desc  = btn.closest('tr')?.querySelector('.bl-delivery-desc')?.textContent || '';
      btn.addEventListener('click', e => {
        e.stopPropagation();
        _onDeliveryRemove(dSlug, idx, desc, btn.closest('tr'));
      });
    });

    // Tag chips — remove user tag
    const tagsRow = grpEl.querySelector('.bl-tags-row');
    if (tagsRow) {
      // User tag remove
      tagsRow.querySelectorAll('[data-tag-idx]').forEach(btn => {
        btn.addEventListener('click', e => {
          e.stopPropagation();
          const idx     = parseInt(btn.dataset.tagIdx, 10);
          const updated = [...(grp.user_tags || [])];
          updated.splice(idx, 1);
          _onTagsUpdate(grp.slug, updated, tagsRow, grp.user_tags || []);
        });
      });

      // AI-new tag (yellow) remove
      tagsRow.querySelectorAll('[data-ai-new-idx]').forEach(btn => {
        btn.addEventListener('click', e => {
          e.stopPropagation();
          const idx      = parseInt(btn.dataset.aiNewIdx, 10);
          const tagLabel = btn.closest('span')?.textContent?.replace('×','').trim() || '';
          _onAiNewTagRemove(grp.slug, idx, tagLabel, btn.closest('span'));
        });
      });

      // + tag button → tag picker overlay
      const addBtn = tagsRow.querySelector('.bl-tag-add-btn');
      if (addBtn) {
        addBtn.addEventListener('click', e => {
          e.stopPropagation();
          _showTagPicker(addBtn, async val => {
            if (val) {
              const newTags = [...(grp.user_tags || []), val];
              await _onTagsUpdate(grp.slug, newTags, tagsRow, grp.user_tags || []);
            }
          });
        });
      }
    }

    // Requirements remove buttons
    grpEl.querySelectorAll('.bl-req-remove').forEach(btn => {
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const idx  = parseInt(btn.dataset.reqIdx, 10);
        const text = btn.closest('.bl-req-row')?.querySelector('.bl-req-text')?.textContent || '';
        _onRequirementRemove(grp.slug, idx, text, btn.closest('.bl-req-row'));
      });
    });

    // Load code stats for this group (non-blocking)
    _loadGroupCodeStats(grp.slug, gi);

    // Load use case open items for groups that have a file (non-blocking)
    if (_fileSlugs.has(grp.slug)) {
      const ucEl = document.getElementById(`bl-uc-${grp.slug}`);
      if (ucEl) _loadUseCaseItems(grp.slug, ucEl);
    }

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

      // Commit items are informational only — no controls
      if (item.src_label === 'COMMITS') return;

      const clsSel = card.querySelector('.bl-classify-select');
      const stSel  = card.querySelector('.bl-status-select');
      const rmBtn  = card.querySelector('.bl-remove-btn');
      if (clsSel) clsSel.addEventListener('change', () => _onClassifyChange(item.ref_id, clsSel.value));
      if (stSel)  stSel.addEventListener('change',  () => _onStatusChange(item.ref_id, stSel.value));
      if (rmBtn)  rmBtn.addEventListener('click',   () => _onRemove(item.ref_id, card));
    });
  });
}

// ── Group HTML ────────────────────────────────────────────────────────────────

function _groupHtml(grp, idx = 0) {
  const grpId    = `bl-grp-${idx}`;
  const slug     = grp.slug      || 'unknown';
  const slugType = grp.slug_type || 'existing';
  const date     = grp.date      || '';
  const items    = grp.items     || [];

  // Detect commits-only group (no approve/reject needed)
  const isCommitsGroup = items.length > 0 && items.every(it => it.src_label === 'COMMITS');

  // Counts by source
  const cnts = { PROMPTS: 0, COMMITS: 0, MESSAGES: 0, ITEMS: 0 };
  for (const it of items) cnts[it.src_label || 'PROMPTS'] = (cnts[it.src_label || 'PROMPTS'] || 0) + 1;
  const countParts = Object.entries(cnts).filter(([,v]) => v > 0)
    .map(([k,v]) => `${v} ${k.toLowerCase()}`);
  const countStr = countParts.join(' · ') || '0 events';

  // Tags
  const userTags   = grp.user_tags        || [];
  const aiExisting = grp.ai_existing_tags || [];
  const aiNew      = grp.ai_new_tags      || [];
  const tagChips = `
    <div class="bl-tags-row" data-tags-slug="${_esc(slug)}">
      ${userTags.map((t,i) => `<span class="bl-chip bl-chip-user">🏷 ${_esc(t)}<button class="bl-chip-remove" data-tag-idx="${i}" title="Remove tag">×</button></span>`).join('')}
      ${aiExisting.map(t => `<span class="bl-chip bl-chip-existing">● ${_esc(t.category)}:${_esc(t.name)}</span>`).join('')}
      ${aiNew.map((t,i) => `<span class="bl-chip bl-chip-new">✦ ${_esc(t.category)}:${_esc(t.name)}<button class="bl-chip-remove" data-ai-new-idx="${i}" title="Dismiss suggestion">×</button></span>`).join('')}
      <button class="bl-tag-add-btn" title="Add tag">+ tag</button>
    </div>`;

  // Summary paragraph — with inline edit button
  const summaryHtml = grp.summary ? `
    <div class="bl-summary-wrap">
      <div class="bl-group-summary">
        <span class="bl-summary-text">${_esc(grp.summary)}</span>
      </div>
      <button class="bl-summary-edit-btn" title="Edit summary">✎</button>
    </div>` : '';

  // Requirements block — each bullet has a remove button
  const reqs = grp.requirements || [];
  const reqsHtml = reqs.length ? `
    <div class="bl-group-reqs">
      <div class="bl-group-reqs-label">Requirements</div>
      ${reqs.map((r, i) => `<div class="bl-req-row">
        <span class="bl-req-bullet">•</span>
        <span class="bl-req-text">${_esc(r)}</span>
        <button class="bl-req-remove" data-req-idx="${i}" title="Remove">✕</button>
      </div>`).join('')}
    </div>` : '';

  // Deliveries table (items sorted: completed first, in-progress last, max 7)
  const deliveries = grp.deliveries || [];
  const deliveriesHtml = _deliveriesTable(deliveries, items, slug);

  // Items section grouped by source type
  const bySource = { PROMPTS: [], COMMITS: [], MESSAGES: [], ITEMS: [] };
  for (const it of items) bySource[it.src_label || 'PROMPTS'].push(it);

  const itemsBodyHtml = Object.entries(bySource)
    .filter(([,arr]) => arr.length > 0)
    .map(([src, arr]) => `
      <div class="bl-src-section">
        <div class="bl-src-label">${src}</div>
        ${arr.map(it => _itemHtml(it)).join('')}
      </div>`)
    .join('');

  const itemsDivider = items.length ? `
    <div class="bl-items-divider">Items (${items.length})</div>` : '';

  return `
    <div class="bl-group${isCommitsGroup ? ' bl-commits-only' : ''}" id="${grpId}">
      <div class="bl-group-header">
        <div style="flex:1;min-width:0;display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
          <span class="bl-slug-wrap" data-slug="${_esc(slug)}">
            <span class="bl-group-slug bl-slug-text">${_esc(slug)}</span>
            <button class="bl-slug-edit-btn" title="Change use case">✎</button>
          </span>
          ${slugType === 'new' ? '<span class="bl-chip bl-chip-type-new">NEW</span>' : ''}
          <span class="bl-group-counts">${countStr}</span>
          <span class="bl-group-meta">${date}</span>
        </div>
        ${!isCommitsGroup ? `
          <button class="bl-approve-all-btn" title="Approve all → merge into use case">✓ Approve</button>
          <button class="bl-reject-all-btn"  title="Reject all">✗ Reject</button>` : ''}
        <span class="bl-group-arrow">▼</span>
      </div>
      <div class="bl-group-body">
        ${tagChips}
        <div class="bl-code-stats-bar" id="bl-stats-${idx}"></div>
        ${summaryHtml}
        ${reqsHtml}
        ${deliveriesHtml}
        ${itemsDivider}
        ${itemsBodyHtml || '<div style="color:var(--muted);font-size:0.77rem;padding:0.4rem 0">No items</div>'}
        <div id="bl-uc-${_esc(slug)}"></div>
      </div>
    </div>`;
}

/**
 * Build the deliveries table.
 *
 * Priority:
 *   1. grp.deliveries — LLM-synthesised group deliveries (3-5 thematic items).
 *      Each has {classify, status, ai_score, event_count, desc}.
 *   2. items fallback — one row per event, sorted completed-first.
 *
 * Max 7 rows shown.
 */
function _deliveriesTable(deliveries, items, slug) {
  let rows = [];
  let isSynthesised = false;

  if (deliveries && deliveries.length) {
    rows = deliveries.map(d => ({
      classify:    d.classify    || 'task',
      status:      d.status      || 'in-progress',
      ai_score:    d.ai_score    ?? 0,
      event_count: d.event_count ?? 1,
      desc:        d.desc        || '',
    }));
    isSynthesised = true;
  } else if (items && items.length) {
    rows = items.map(it => ({
      classify:    it.classify || 'task',
      status:      it.status   || 'in-progress',
      ai_score:    it.ai_score ?? 0,
      event_count: 1,
      desc:        it.summary  || '',
    }));
    const done = rows.filter(r => r.status === 'completed').sort((a,b) => b.ai_score - a.ai_score);
    const prog = rows.filter(r => r.status !== 'completed').sort((a,b) => b.ai_score - a.ai_score);
    rows = [...done, ...prog];
  }

  if (!rows.length) return '';

  const tableRows = rows.slice(0, 7).map((r, i) => {
    const isDone   = r.status === 'completed';
    const icon     = isDone ? '✓' : '⏳';
    const iconCls  = isDone ? 'bl-delivery-status-done' : 'bl-delivery-status-prog';
    const typeCls  = `bl-delivery-type bl-delivery-type-${r.classify}`;
    const cntBadge = (isSynthesised && r.event_count > 1)
      ? `<span class="bl-delivery-score" style="margin-left:3px" title="${r.event_count} events">${r.event_count}×</span>`
      : '';
    const removeBtn = isSynthesised
      ? `<button class="bl-delivery-remove" data-delivery-idx="${i}" data-delivery-slug="${_esc(slug)}" title="Remove this theme">✕</button>`
      : '';
    return `
      <tr>
        <td class="bl-delivery-icon ${iconCls}">${icon}</td>
        <td><span class="${typeCls}">${_esc(r.classify)}</span></td>
        <td><span class="bl-delivery-score">AI:${r.ai_score}</span>${cntBadge}</td>
        <td class="bl-delivery-desc" title="${_esc(r.desc)}">${_esc(r.desc)}</td>
        <td>${removeBtn}</td>
      </tr>`;
  }).join('');

  const total = isSynthesised ? rows.length : items.length;
  const label = isSynthesised
    ? `Deliveries — ${rows.length} theme${rows.length !== 1 ? 's' : ''}`
    : `Items (${Math.min(rows.length, 7)}${rows.length > 7 ? ' of ' + total : ''})`;

  return `
    <div class="bl-deliveries-section">
      <div class="bl-deliveries-label">${label}</div>
      <table class="bl-deliveries-table">${tableRows}</table>
    </div>`;
}

// ── Item HTML ─────────────────────────────────────────────────────────────────

function _itemHtml(item) {
  const isCommit = item.src_label === 'COMMITS';
  const classify = item.classify || 'task';
  const status   = item.status   || 'in-progress';
  const aiScore  = item.ai_score ?? '';
  const refId    = item.ref_id   || '';
  const summary  = item.summary  || '';

  // Body content
  const reqs = item.requirements || '';
  const devs = Array.isArray(item.deliveries)
    ? item.deliveries.join('; ')
    : (item.deliveries || '');
  const hasBody = reqs || devs;

  const bodyHtml = hasBody ? `
    <div class="bl-body">
      ${reqs ? `<div class="bl-body-label">Requirements</div>
        <div class="bl-body-text">${_esc(reqs)}</div>` : ''}
      ${devs ? `<div class="bl-body-label">Changes</div>
        <div class="bl-body-text">${_esc(devs)}</div>` : ''}
    </div>` : '';

  if (isCommit) {
    // Commit item: informational only — no dropdowns, no remove
    return `
      <div class="bl-entry" id="bl-card-${refId}">
        <div class="bl-entry-header">
          <span class="bl-ref">${_esc(refId)}</span>
          <span class="bl-commit-badge">committed</span>
          ${aiScore !== '' ? `<span class="bl-ai-score">AI:${aiScore}</span>` : ''}
          <span class="bl-summary" title="${_esc(summary)}">${_esc(summary)}</span>
        </div>
        ${bodyHtml}
      </div>`;
  }

  // Prompt / message / item: full controls
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
