/**
 * entities.js — Planner: Unified Tag Manager.
 *
 * 2-pane layout: left = category list (160px), right = tag table.
 * Reads from the shared tagCache — zero DB calls on navigation. Mutations
 * update the cache synchronously (instant UI feedback) then fire the DB
 * call in the background.
 *
 * Requires PostgreSQL (shows 503 notice when unavailable).
 */

import { state } from '../stores/state.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';
import {
  loadTagCache, isCacheLoaded, getCacheProject,
  getCacheCategories, getCacheValues,
  getCacheRoots, getCacheChildren, getCacheDescendants, hasChildren,
  addCachedValue, updateCachedValue, removeCachedValue, addCachedCategory,
} from '../utils/tagCache.js';

let _plannerState = {
  selectedCat:      null,
  selectedCatName:  '',
  selectedCatColor: '',
  selectedCatIcon:  '',
  project:          '',
};

// ── Main render ───────────────────────────────────────────────────────────────

export function renderEntities(container) {
  const project = state.currentProject?.name || '';
  _plannerState = { selectedCat: null, selectedCatName: '', selectedCatColor: '', selectedCatIcon: '', project };

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- Header -->
      <div style="padding:0.75rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:1rem;flex-shrink:0">
        <span style="font-size:0.85rem;font-weight:700;color:var(--text)">Tag Management</span>
        ${project ? `<span style="font-size:0.65rem;color:var(--accent)">${_esc(project)}</span>` : ''}
        <button class="btn btn-ghost btn-sm" style="margin-left:auto"
          onclick="window._plannerSync()" title="Sync events + reload cache">↻ Sync</button>
      </div>

      <!-- 2-pane body -->
      <div style="display:flex;flex:1;min-height:0;overflow:hidden">

        <!-- Left pane: category list -->
        <div id="planner-cats-pane"
             style="width:160px;flex-shrink:0;border-right:1px solid var(--border);
                    overflow:hidden;display:flex;flex-direction:column">
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      padding:8px 10px 4px;letter-spacing:.05em;flex-shrink:0">Categories</div>
          <div id="planner-cat-list" style="flex:1;overflow-y:auto;padding:0 4px"></div>
          <div style="padding:6px 8px;border-top:1px solid var(--border);flex-shrink:0">
            <input id="planner-new-cat-inp" placeholder="+ New category…"
              style="width:100%;padding:3px 6px;border:1px dashed var(--border);border-radius:4px;
                     background:transparent;color:var(--text);font-size:0.62rem;
                     box-sizing:border-box;outline:none;font-family:var(--font)"
              onkeydown="if(event.key==='Enter')window._plannerNewCat(this.value)" />
          </div>
        </div>

        <!-- Right area: table + detail drawer -->
        <div style="flex:1;display:flex;min-height:0;overflow:hidden">

          <!-- Tag table -->
          <div id="planner-tags-pane" style="flex:1;overflow-y:auto;padding:0.75rem 1rem">
            <div style="color:var(--muted);font-size:0.7rem;padding:3rem;text-align:center">
              ← Select a category
            </div>
          </div>

          <!-- Detail drawer (closed by default) -->
          <div id="planner-drawer"
               style="width:0;overflow:hidden;border-left:0 solid var(--border);
                      flex-shrink:0;transition:width 0.22s ease,border-width 0.22s;
                      background:var(--surface);display:flex">
            <div id="planner-drawer-inner"
                 style="width:290px;overflow-y:auto;flex-shrink:0;box-sizing:border-box"></div>
          </div>

        </div>

      </div>
    </div>
  `;

  // Wire window globals
  window._plannerSelectCat        = _plannerSelectCat;
  window._plannerDeleteVal        = _plannerDeleteVal;
  window._plannerSaveNewTag       = _plannerSaveNewTag;
  window._plannerCancelNewTag     = _plannerCancelNewTag;
  window._plannerSync             = _plannerSync;
  window._plannerNewCat           = _plannerNewCat;
  window._plannerAddChild         = _plannerAddChild;
  window._plannerToggleExpand     = _plannerToggleExpand;
  window._plannerOpenDrawer       = _plannerOpenDrawer;
  window._plannerCloseDrawer      = _plannerCloseDrawer;
  window._plannerDrawerSetStatus  = _plannerDrawerSetStatus;
  window._plannerDrawerSaveRemarks = _plannerDrawerSaveRemarks;
  window._plannerDrawerSaveDue    = _plannerDrawerSaveDue;
  window._plannerDrawerAddChild   = _plannerDrawerAddChild;
  window._plannerCycleLifecycle   = _plannerCycleLifecycle;
  window._plannerDrawerAddLink    = _plannerDrawerAddLink;
  window._plannerDrawerRemoveLink = _plannerDrawerRemoveLink;

  if (!project) {
    document.getElementById('planner-tags-pane').innerHTML =
      '<div style="color:var(--muted);font-size:0.7rem;padding:3rem;text-align:center">No project open</div>';
    return;
  }

  _initPlanner(project);
}

// ── Init: use cache if warm, otherwise load ──────────────────────────────────

async function _initPlanner(project) {
  if (!isCacheLoaded() || getCacheProject() !== project) {
    document.getElementById('planner-cat-list').innerHTML =
      '<div style="color:var(--muted);font-size:0.62rem;padding:8px 10px">Loading…</div>';
    await loadTagCache(project);
  }
  _renderCategoryList();
}

// ── Category list ─────────────────────────────────────────────────────────────

function _renderCategoryList() {
  const list = document.getElementById('planner-cat-list');
  if (!list) return;
  const cats = getCacheCategories();
  if (!cats.length) {
    list.innerHTML = '<div style="color:var(--muted);font-size:0.62rem;padding:8px 10px">No categories yet</div>';
    return;
  }
  list.innerHTML = cats.map(c => `
    <div class="planner-cat-row" data-id="${c.id}"
         onclick="window._plannerSelectCat(${c.id},'${_esc(c.name)}')"
         style="display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:5px;
                cursor:pointer;margin-bottom:2px;transition:background 0.1s;
                background:${_plannerState.selectedCat === c.id ? 'var(--accent)22' : 'transparent'};
                border-left:2px solid ${_plannerState.selectedCat === c.id ? 'var(--accent)' : 'transparent'}">
      <span style="color:${c.color};font-size:0.85rem">${c.icon}</span>
      <span style="font-size:0.65rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(c.name)}</span>
      <span style="font-size:0.55rem;color:var(--muted);flex-shrink:0">${c.value_count ?? getCacheValues(c.id).length}</span>
    </div>`).join('');
}

async function _plannerSelectCat(catId, catName) {
  _plannerState.selectedCat = catId;
  _plannerState.selectedCatName = catName;
  const cat = getCacheCategories().find(c => c.id === catId) || {};
  _plannerState.selectedCatColor = cat.color || 'var(--accent)';
  _plannerState.selectedCatIcon  = cat.icon  || '⬡';

  // Update active style in left pane
  document.querySelectorAll('.planner-cat-row').forEach(r => {
    const sel = parseInt(r.dataset.id) === catId;
    r.style.background = sel ? 'var(--accent)22' : 'transparent';
    r.style.borderLeft = sel ? '2px solid var(--accent)' : '2px solid transparent';
  });

  _renderTagTableFromCache();
}

// ── Work item categories ──────────────────────────────────────────────────────

const _WORK_ITEM_CATEGORIES = new Set(['feature', 'bug', 'task']);

function _isWorkItemCat(name) {
  return _WORK_ITEM_CATEGORIES.has((name || '').toLowerCase());
}

// ── Lifecycle badge helpers ───────────────────────────────────────────────────

const _LIFECYCLE_ORDER = ['idea', 'design', 'development', 'testing', 'review', 'done'];
const _LIFECYCLE_COLORS = {
  idea:        '#95a5a6',
  design:      '#8e44ad',
  development: '#2980b9',
  testing:     '#e67e22',
  review:      '#16a085',
  done:        '#27ae60',
};

function _lifecycleBadge(lc, valId) {
  const label = lc || 'idea';
  const color = _LIFECYCLE_COLORS[label] || '#95a5a6';
  return `<span onclick="event.stopPropagation();window._plannerCycleLifecycle(${valId},'${label}')"
                title="Click to advance lifecycle"
                style="font-size:0.58rem;color:#fff;background:${color};padding:0.1rem 0.4rem;
                       border-radius:10px;white-space:nowrap;cursor:pointer;user-select:none">
            ${label}
          </span>`;
}

function _plannerCycleLifecycle(valId, current) {
  const idx  = _LIFECYCLE_ORDER.indexOf(current);
  const next = _LIFECYCLE_ORDER[(idx + 1) % _LIFECYCLE_ORDER.length];
  updateCachedValue(valId, { lifecycle_status: next });
  _renderTagTableFromCache();
  if (_drawerValId === valId) _renderDrawer();
  api.entities.patchValue(valId, { lifecycle_status: next })
    .catch(e => toast('Lifecycle sync error: ' + e.message, 'error'));
}

// ── Tag table ─────────────────────────────────────────────────────────────────

// Which parent rows are collapsed (set of value IDs whose children are hidden)
const _collapsed = new Set();

function _renderTagTableFromCache() {
  const { selectedCat, selectedCatName, selectedCatColor, selectedCatIcon } = _plannerState;
  const pane = document.getElementById('planner-tags-pane');
  if (!pane || !selectedCat) return;
  _renderTagTable(pane, selectedCat, selectedCatName, selectedCatColor, selectedCatIcon);
}

// ── Work item table (for feature/bug/task categories) ─────────────────────────

// Collapse state for work item tree (mirroring _collapsed for regular tags)
const _wiCollapsed = new Set();
// Current items cache (id → wi object) for the open category
let _wiItemsCache = {};

async function _renderWorkItemTable(pane, catName, catColor, catIcon, project) {
  pane.innerHTML = `
    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem">
      <span style="font-size:0.8rem;color:${catColor}">${catIcon}</span>
      <span style="font-size:0.78rem;font-weight:600;color:var(--text)">${_esc(catName)}</span>
      <button onclick="window._plannerShowNewWorkItem('${_esc(catName)}', null)"
        style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
               padding:0.2rem 0.55rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none;margin-left:auto">+ New</button>
    </div>
    <div id="wi-table-body" style="color:var(--muted);font-size:0.7rem;padding:1rem;text-align:center">
      Loading…
    </div>
  `;

  // Wire globals up front so they're always available
  window._plannerShowNewWorkItem = async (cn, parentId) => {
    const label = parentId ? `New child ${cn} name:` : `New ${cn} name:`;
    const name = prompt(label);
    if (!name) return;
    try {
      await api.workItems.create(project, { category_name: cn, name, parent_id: parentId || null });
      _renderWorkItemTable(pane, catName, catColor, catIcon, project);
    } catch (e) { toast('Create failed: ' + e.message, 'error'); }
  };
  window._wiToggleCollapse = (id) => {
    if (_wiCollapsed.has(id)) _wiCollapsed.delete(id); else _wiCollapsed.add(id);
    const tb = document.getElementById('wi-table-body');
    if (tb) tb.innerHTML = _wiRenderRows(_wiItemsCache, catName, catColor, catIcon, project);
  };
  window._wiRunPipeline = async (id, proj) => {
    const btn = document.querySelector(`[data-wi-run-btn="${id}"]`);
    if (btn) { btn.disabled = true; btn.textContent = '…'; }
    try {
      const res = await api.workItems.runPipeline(id, proj);
      const runId = res.run_id ? String(res.run_id) : null;
      if (runId) {
        // Navigate to Pipelines tab and open the run progress panel
        window._pendingRunOpen = runId;
        window._nav('workflow');
        // Poll until graph_workflow.js has registered _gwOpenRun (max 4s)
        let t = 0;
        const iv = setInterval(() => {
          t += 200;
          if (window._gwOpenRun) {
            clearInterval(iv);
            window._gwOpenRun(runId);
            window._pendingRunOpen = null;
          } else if (t >= 4000) {
            clearInterval(iv);
          }
        }, 200);
      } else {
        toast('Pipeline started — check Pipelines tab for progress', 'success', 5000);
      }
      setTimeout(() => _renderWorkItemTable(pane, catName, catColor, catIcon, project), 5000);
    } catch (e) {
      toast('Pipeline error: ' + e.message, 'error');
      if (btn) { btn.disabled = false; btn.textContent = '▶'; }
    }
  };
  window._plannerOpenWorkItemDrawer = (id, cn, proj) => _openWorkItemDrawer(id, cn, proj, pane, catColor, catIcon);

  try {
    const data = await api.workItems.list(project, catName);
    const items = data.work_items || [];

    // Build lookup + tree
    _wiItemsCache = {};
    items.forEach(wi => { _wiItemsCache[wi.id] = wi; });

    const tableBody = document.getElementById('wi-table-body');
    if (!tableBody) return;

    if (!items.length) {
      tableBody.innerHTML = `<div style="text-align:center;padding:3rem 1rem;color:var(--muted)">
        <div style="font-size:2rem;margin-bottom:0.75rem">${catIcon}</div>
        No ${catName}s yet — click <strong>+ New</strong> to create one.
      </div>`;
      return;
    }

    tableBody.innerHTML = _wiRenderRows(_wiItemsCache, catName, catColor, catIcon, project);
  } catch (e) {
    const tb = document.getElementById('wi-table-body');
    if (tb) tb.textContent = `Error loading ${catName}s: ${e.message}`;
  }
}

function _wiRenderRows(byId, catName, catColor, catIcon, project) {
  // Build roots + children map
  const children = {};  // parent_id → [wi]
  const roots = [];
  Object.values(byId).forEach(wi => {
    if (wi.parent_id && byId[wi.parent_id]) {
      (children[wi.parent_id] = children[wi.parent_id] || []).push(wi);
    } else {
      roots.push(wi);
    }
  });

  const agentBadge = (s) => {
    if (!s) return '';
    const col = s === 'done' ? '#27ae60' : s === 'failed' ? '#e74c3c' : s.startsWith('running') ? '#e67e22' : '#888';
    return `<span style="font-size:0.55rem;color:#fff;background:${col};
                         padding:0.1rem 0.35rem;border-radius:8px;white-space:nowrap">${_esc(s)}</span>`;
  };

  function rowsForNode(wi, depth) {
    const lc     = wi.lifecycle_status || 'idea';
    const lcCol  = _LIFECYCLE_COLORS[lc] || '#888';
    const sc     = wi.status === 'active' ? '#27ae60' : wi.status === 'done' ? '#4a90e2' : '#888';
    const kids   = children[wi.id] || [];
    const hasKids   = kids.length > 0;
    const expanded  = !_wiCollapsed.has(wi.id);
    const indent    = depth * 18;
    const acPreview = wi.acceptance_criteria
      ? wi.acceptance_criteria.replace(/\n/g, ' ').slice(0, 55) + (wi.acceptance_criteria.length > 55 ? '…' : '')
      : '—';
    const isRunning = (wi.agent_status || '').startsWith('running');

    const toggleBtn = hasKids
      ? `<span onclick="event.stopPropagation();window._wiToggleCollapse('${wi.id}')"
               style="cursor:pointer;color:var(--muted);margin-right:3px;display:inline-block;
                      width:14px;text-align:center;font-size:0.72rem;user-select:none;flex-shrink:0"
               title="${expanded ? 'Collapse' : 'Expand'}">${expanded ? '▾' : '▸'}</span>`
      : `<span style="display:inline-block;width:14px;margin-right:3px;flex-shrink:0"></span>`;

    const seqBadge = wi.seq_num
      ? `<span style="font-size:0.52rem;color:var(--muted);background:var(--surface2);
                      border:1px solid var(--border);padding:0.05rem 0.28rem;
                      border-radius:6px;white-space:nowrap;margin-right:4px;flex-shrink:0"
               title="Seq #${wi.seq_num}">#${wi.seq_num}</span>`
      : '';

    let html = `
      <tr style="border-bottom:1px solid var(--border);cursor:pointer;transition:background 0.1s"
          data-wi-id="${wi.id}"
          onclick="window._plannerOpenWorkItemDrawer('${_esc(wi.id)}','${_esc(catName)}','${_esc(project)}')"
          onmouseenter="this.style.background='var(--surface2)'"
          onmouseleave="this.style.background=''">
        <td style="padding:0.5rem 0.5rem 0.5rem ${0.5 + indent / 16}rem;
                   color:var(--text);font-weight:${depth === 0 ? '500' : '400'}">
          <div style="display:flex;align-items:center">
            ${toggleBtn}
            ${seqBadge}
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                  title="${_esc(wi.name)}">${_esc(wi.name)}</span>
          </div>
        </td>
        <td style="padding:0.5rem 0.4rem;white-space:nowrap" onclick="event.stopPropagation()">
          <span onclick="window._wiCycleLifecycle('${wi.id}','${lc}')"
                title="Click to advance"
                style="font-size:0.58rem;color:#fff;background:${lcCol};
                       padding:0.1rem 0.4rem;border-radius:10px;white-space:nowrap;
                       cursor:pointer;user-select:none">${lc}</span>
        </td>
        <td style="padding:0.5rem 0.4rem;white-space:nowrap">
          <span style="font-size:0.6rem;color:${sc};background:${sc}22;
                       padding:0.12rem 0.4rem;border-radius:10px">${_esc(wi.status || 'active')}</span>
        </td>
        <td style="padding:0.5rem 0.4rem;color:var(--muted);font-size:0.65rem;
                   max-width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
            title="${_esc(wi.acceptance_criteria || '')}">${_esc(acPreview)}</td>
        <td style="padding:0.5rem 0.4rem" onclick="event.stopPropagation()">
          ${agentBadge(wi.agent_status)}
        </td>
        <td style="padding:0.5rem 0.4rem;color:var(--muted);font-size:0.65rem">
          ${wi.due_date ? wi.due_date.slice(0, 10) : '—'}
        </td>
        <td style="padding:0.5rem 0.4rem;white-space:nowrap;text-align:right"
            onclick="event.stopPropagation()">
          <button title="Add child ${catName}"
            onclick="window._plannerShowNewWorkItem('${_esc(catName)}','${_esc(wi.id)}')"
            style="font-size:0.6rem;padding:0.13rem 0.35rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font);outline:none;margin-right:3px">+▸</button>
        </td>
      </tr>`;

    if (hasKids && expanded) {
      html += kids.map(child => rowsForNode(child, depth + 1)).join('');
    }
    return html;
  }

  return `
    <table style="width:100%;border-collapse:collapse;font-size:0.72rem">
      <thead>
        <tr style="border-bottom:2px solid var(--border)">
          <th style="text-align:left;padding:0.35rem 0.5rem;color:var(--muted);font-weight:500">Name</th>
          <th style="text-align:left;padding:0.35rem 0.4rem;color:var(--muted);font-weight:500;width:80px">Lifecycle</th>
          <th style="text-align:left;padding:0.35rem 0.4rem;color:var(--muted);font-weight:500;width:65px">Status</th>
          <th style="text-align:left;padding:0.35rem 0.4rem;color:var(--muted);font-weight:500;max-width:110px">Criteria</th>
          <th style="text-align:left;padding:0.35rem 0.4rem;color:var(--muted);font-weight:500;width:70px">Agent</th>
          <th style="text-align:left;padding:0.35rem 0.4rem;color:var(--muted);font-weight:500;width:78px">Due</th>
          <th style="width:80px"></th>
        </tr>
      </thead>
      <tbody>
        ${roots.map(wi => rowsForNode(wi, 0)).join('')}
      </tbody>
    </table>`;
}

// Lifecycle cycling for work items (inline, mirrors _plannerCycleLifecycle)
window._wiCycleLifecycle = (id, current) => {
  const idx  = _LIFECYCLE_ORDER.indexOf(current);
  const next = _LIFECYCLE_ORDER[(idx + 1) % _LIFECYCLE_ORDER.length];
  if (_wiItemsCache[id]) _wiItemsCache[id].lifecycle_status = next;
  const tb = document.getElementById('wi-table-body');
  const { selectedCatName: catName, selectedCatColor: catColor, selectedCatIcon: catIcon, project } = _plannerState;
  if (tb) tb.innerHTML = _wiRenderRows(_wiItemsCache, catName, catColor, catIcon, project);
  api.workItems.patch(id, _plannerState.project, { lifecycle_status: next })
    .catch(e => toast('Lifecycle sync error: ' + e.message, 'error'));
};

async function _openWorkItemDrawer(id, catName, project, pane, catColor, catIcon) {
  const drawer = document.getElementById('planner-drawer');
  const inner  = document.getElementById('planner-drawer-inner');
  if (!drawer || !inner) return;
  drawer.style.width = '300px';
  drawer.style.borderLeftWidth = '1px';

  inner.innerHTML = `<div style="padding:1rem;color:var(--muted);font-size:0.72rem">Loading…</div>`;

  try {
    const data = await api.workItems.list(project, catName);
    const wi   = (data.work_items || []).find(w => w.id === id);
    if (!wi) { inner.innerHTML = '<div style="padding:1rem;color:var(--muted)">Not found</div>'; return; }

    const lc_col = _LIFECYCLE_COLORS[wi.lifecycle_status || 'idea'] || '#888';
    const drawerSeqBadge = wi.seq_num
      ? `<span style="font-size:0.55rem;color:var(--muted);background:var(--surface2);
                       border:1px solid var(--border);padding:0.1rem 0.35rem;
                       border-radius:6px;white-space:nowrap;cursor:default"
              title="Reference this item as #${wi.seq_num}">#${wi.seq_num}</span>`
      : '';
    inner.innerHTML = `
      <div style="padding:0.9rem 1rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.5rem">
        ${drawerSeqBadge}
        <strong style="font-size:0.75rem;flex:1;overflow:hidden;text-overflow:ellipsis">${_esc(wi.name)}</strong>
        <button onclick="window._plannerCloseDrawer()"
          style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:1rem">✕</button>
      </div>

      <div style="padding:0.85rem 1rem;display:flex;flex-direction:column;gap:0.85rem">

        <!-- Lifecycle badge -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Lifecycle</div>
          <span style="font-size:0.65rem;color:#fff;background:${lc_col};
                       padding:0.15rem 0.5rem;border-radius:10px">${wi.lifecycle_status || 'idea'}</span>
        </div>

        <!-- Description -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Description</div>
          <textarea id="wi-desc-ta" rows="3"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.68rem;
                   padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                   resize:vertical;box-sizing:border-box;line-height:1.5"
            onblur="api.workItems.patch('${id}','${project}',{description:this.value}).catch(e=>toast(e.message,'error'))"
          >${_esc(wi.description || '')}</textarea>
        </div>

        <!-- Acceptance Criteria -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Acceptance Criteria</div>
          <textarea id="wi-ac-ta" rows="5"
            placeholder="- [ ] Criteria 1&#10;- [ ] Criteria 2"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                   resize:vertical;box-sizing:border-box;line-height:1.5"
            onblur="api.workItems.patch('${id}','${project}',{acceptance_criteria:this.value}).catch(e=>toast(e.message,'error'))"
          >${_esc(wi.acceptance_criteria || '')}</textarea>
        </div>

        <!-- Implementation Plan -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Implementation Plan</div>
          <textarea id="wi-impl-ta" rows="5"
            placeholder="1. Step one&#10;2. Step two"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                   resize:vertical;box-sizing:border-box;line-height:1.5"
            onblur="api.workItems.patch('${id}','${project}',{implementation_plan:this.value}).catch(e=>toast(e.message,'error'))"
          >${_esc(wi.implementation_plan || '')}</textarea>
        </div>

        <!-- Due date -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Due Date</div>
          <input type="date" value="${_esc(wi.due_date ? wi.due_date.slice(0,10) : '')}"
            onchange="api.workItems.patch('${id}','${project}',{due_date:this.value||null}).catch(e=>toast(e.message,'error'))"
            style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.68rem;padding:0.25rem 0.4rem;
                   border-radius:var(--radius);outline:none;width:100%;box-sizing:border-box" />
        </div>

        <!-- Agent status -->
        ${wi.agent_status ? `
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Agent Status</div>
          <div style="font-size:0.68rem;color:var(--text2)">${_esc(wi.agent_status)}</div>
        </div>` : ''}

        <!-- Parent item link -->
        ${wi.parent_id && _wiItemsCache[wi.parent_id] ? `
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Parent</div>
          <span style="font-size:0.68rem;color:var(--accent);cursor:pointer"
                onclick="window._plannerOpenWorkItemDrawer('${wi.parent_id}','${_esc(catName)}','${_esc(project)}')"
          >${_esc((_wiItemsCache[wi.parent_id] || {}).name || '')}</span>
        </div>` : ''}

        <!-- Run Pipeline -->
        <div style="border-top:1px solid var(--border);padding-top:0.75rem">
          <button id="wi-drawer-run-btn"
            onclick="window._wiRunPipeline('${id}','${project}')"
            style="background:var(--accent);border:none;color:#fff;font-size:0.68rem;
                   padding:0.3rem 0.75rem;border-radius:var(--radius);cursor:pointer;
                   font-family:var(--font);outline:none;width:100%">▶ Run Pipeline</button>
          <div style="font-size:0.58rem;color:var(--muted);margin-top:0.35rem;line-height:1.4">
            PM → Architect → Developer → Reviewer
            ${wi.agent_run_id ? `· <a href="#" onclick="
              window._pendingRunOpen='${wi.agent_run_id}';window._nav('workflow');
              let _rt=0,_ri=setInterval(()=>{_rt+=200;if(window._gwOpenRun){clearInterval(_ri);window._gwOpenRun('${wi.agent_run_id}');window._pendingRunOpen=null;}else if(_rt>=4000)clearInterval(_ri);},200);return false"
              style="color:var(--accent);text-decoration:none">View last run →</a>` : ''}
          </div>
        </div>

        <!-- Delete -->
        <div style="border-top:1px solid var(--border);padding-top:0.75rem">
          <button onclick="window._wiDelete('${id}','${project}')"
            style="background:none;border:1px solid var(--red,#e74c3c);color:var(--red,#e74c3c);
                   font-size:0.62rem;padding:0.22rem 0.6rem;border-radius:var(--radius);
                   cursor:pointer;font-family:var(--font);outline:none">Delete ✕</button>
        </div>

      </div>
    `;

    window._wiDelete = async (wid, proj) => {
      if (!confirm('Delete this work item?')) return;
      try {
        await api.workItems.delete(wid, proj);
        _plannerCloseDrawer();
        _renderWorkItemTable(pane, catName, catColor, catIcon, project);
      } catch (e) { toast('Delete failed: ' + e.message, 'error'); }
    };
  } catch (e) {
    inner.innerHTML = `<div style="padding:1rem;color:#e74c3c;font-size:0.72rem">Error: ${_esc(e.message)}</div>`;
  }
}

function _renderTagTable(pane, catId, catName, catColor, catIcon) {
  const STATUS_COLORS = { active: '#27ae60', done: '#4a90e2', archived: '#888' };
  const roots = getCacheRoots(catId);

  // Recursively build table rows for a node and its visible children
  function _rowsForNode(v, depth) {
    const sc       = STATUS_COLORS[v.status] || '#888';
    const archived = v.status === 'archived';
    const kids     = getCacheChildren(v.id);
    const hasKids  = kids.length > 0;
    const expanded = !_collapsed.has(v.id);
    const indent   = depth * 20;

    const toggleBtn = hasKids
      ? `<span onclick="window._plannerToggleExpand(${v.id})"
               style="cursor:pointer;color:var(--muted);margin-right:3px;display:inline-block;
                      width:14px;text-align:center;font-size:0.72rem;user-select:none;flex-shrink:0"
               title="${expanded ? 'Collapse' : 'Expand'}">${expanded ? '▾' : '▸'}</span>`
      : `<span style="display:inline-block;width:14px;margin-right:3px;flex-shrink:0"></span>`;

    let html = `
      <tr style="border-bottom:1px solid var(--border);opacity:${archived ? '0.45' : '1'};
                 transition:background 0.1s;cursor:pointer"
          data-val-id="${v.id}"
          onclick="window._plannerOpenDrawer(${catId},${v.id})"
          onmouseenter="this.style.background='var(--surface2)'"
          onmouseleave="this.style.background=''">
        <td style="padding:0.5rem 0.5rem 0.5rem ${0.5 + indent/16}rem;
                   color:var(--text);font-weight:${depth===0?'500':'400'}">
          <div style="display:flex;align-items:center">
            ${toggleBtn}
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(v.name)}</span>
          </div>
        </td>
        <td style="padding:0.5rem 0.4rem;white-space:nowrap" onclick="event.stopPropagation()">
          ${_lifecycleBadge(v.lifecycle_status, v.id)}
        </td>
        <td style="padding:0.5rem 0.5rem;white-space:nowrap" onclick="event.stopPropagation()">
          <span style="font-size:0.6rem;color:${sc};background:${sc}22;
                       padding:0.12rem 0.4rem;border-radius:10px;white-space:nowrap;user-select:none">
            ${_esc(v.status || 'active')}
          </span>
        </td>
        <td style="padding:0.5rem 0.4rem;text-align:right;white-space:nowrap" onclick="event.stopPropagation()">
          <button onclick="window._plannerAddChild(${catId},${v.id})"
            style="font-size:0.6rem;padding:0.13rem 0.35rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font);outline:none;margin-right:3px"
            title="Add child tag">+▸</button>
          ${_isWorkItemCat(catName) ? `<button
            onclick="event.stopPropagation();window._plannerOpenDrawer(${catId},${v.id});
                     setTimeout(()=>window._plannerDrawerRunPipeline('${_esc(catName)}','${_esc(v.name)}','${_esc(_plannerState.project)}'),200)"
            style="font-size:0.6rem;padding:0.13rem 0.35rem;background:var(--accent)18;
                   border:1px solid var(--accent);border-radius:var(--radius);cursor:pointer;
                   color:var(--accent);font-family:var(--font);outline:none;margin-right:3px"
            title="Run AI Pipeline">▶</button>` : ''}
          <button onclick="window._plannerOpenDrawer(${catId},${v.id})"
            style="font-size:0.85rem;padding:0.15rem 0.45rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);
                   cursor:pointer;color:var(--text2);font-family:var(--font);outline:none;
                   transition:background 0.12s,color 0.12s;line-height:1"
            onmouseenter="this.style.background='var(--accent)';this.style.color='#fff'"
            onmouseleave="this.style.background='var(--surface2)';this.style.color='var(--text2)'"
            title="Open details">⋯</button>
        </td>
      </tr>`;

    if (hasKids && expanded) {
      html += kids.map(child => _rowsForNode(child, depth + 1)).join('');
    }
    return html;
  }

  pane.innerHTML = `
    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem">
      <span style="font-size:0.8rem;color:${catColor}">${catIcon}</span>
      <span style="font-size:0.78rem;font-weight:600;color:var(--text)">${_esc(catName)}</span>
      <button onclick="window._plannerShowNewTag(${catId})"
        style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
               padding:0.2rem 0.55rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none;margin-left:auto">+ New Tag</button>
    </div>

    <!-- New tag inline row (hidden) -->
    <div id="planner-new-tag-row"
         style="display:none;gap:0.4rem;align-items:center;margin-bottom:0.5rem;
                padding:0.4rem 0.5rem;background:var(--surface2);
                border:1px solid var(--border);border-radius:var(--radius)">
      <span id="planner-new-tag-label" style="font-size:0.6rem;color:var(--muted);white-space:nowrap;flex-shrink:0"></span>
      <input id="planner-new-tag-inp" placeholder="Tag name…" type="text"
        onkeydown="if(event.key==='Enter')window._plannerSaveNewTag();if(event.key==='Escape')window._plannerCancelNewTag()"
        style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
               font-family:var(--font);font-size:0.68rem;padding:0.22rem 0.45rem;
               border-radius:var(--radius);outline:none" />
      <button onclick="window._plannerSaveNewTag()"
        style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
               padding:0.22rem 0.55rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none">Save</button>
      <button onclick="window._plannerCancelNewTag()"
        style="background:none;border:1px solid var(--border);color:var(--muted);font-size:0.62rem;
               padding:0.22rem 0.45rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none">✕</button>
    </div>

    ${roots.length === 0 ? `
      <div style="text-align:center;padding:3rem 1rem;color:var(--muted);font-size:0.72rem">
        <div style="font-size:2rem;margin-bottom:0.75rem">${catIcon}</div>
        No tags in <strong>${_esc(catName)}</strong> yet — click <strong>+ New Tag</strong>
      </div>` : `
    <table style="width:100%;border-collapse:collapse;font-size:0.72rem">
      <thead>
        <tr style="border-bottom:2px solid var(--border)">
          <th style="text-align:left;padding:0.35rem 0.5rem;color:var(--muted);font-weight:500">Name</th>
          <th style="text-align:left;padding:0.35rem 0.4rem;color:var(--muted);font-weight:500;width:90px">Lifecycle</th>
          <th style="text-align:left;padding:0.35rem 0.5rem;color:var(--muted);font-weight:500;width:75px">Status</th>
          <th style="width:${_isWorkItemCat(catName) ? '108' : '80'}px"></th>
        </tr>
      </thead>
      <tbody>
        ${roots.map(v => _rowsForNode(v, 0)).join('')}
      </tbody>
    </table>`}
  `;

  window._plannerShowNewTag = (catId, parentId = null) => {
    const row   = document.getElementById('planner-new-tag-row');
    const label = document.getElementById('planner-new-tag-label');
    if (row) {
      row.style.display   = 'flex';
      row.dataset.catId    = catId;
      row.dataset.parentId = parentId ?? '';
    }
    if (label) label.textContent = parentId ? 'Child tag:' : 'New root tag:';
    setTimeout(() => document.getElementById('planner-new-tag-inp')?.focus(), 0);
  };
}

// ── Mutations — update cache sync, fire DB in background ─────────────────────

// Track which val is open in the drawer
let _drawerValId  = null;
let _drawerCatId  = null;

function _plannerOpenDrawer(catId, valId) {
  _drawerValId = valId;
  _drawerCatId = catId;

  const drawer = document.getElementById('planner-drawer');
  if (drawer) {
    drawer.style.width = '300px';
    drawer.style.borderLeftWidth = '1px';
  }
  _renderDrawer();
  // Async: load value links + pipeline status after drawer renders
  _loadDrawerLinks(valId);
  const { selectedCatName, project } = _plannerState;
  if (_isWorkItemCat(selectedCatName)) {
    const v = getCacheValues(catId).find(x => x.id === valId);
    if (v) _loadDrawerPipeline(selectedCatName, v.name, project);
  }
}

function _plannerCloseDrawer() {
  const drawer = document.getElementById('planner-drawer');
  if (drawer) { drawer.style.width = '0'; drawer.style.borderLeftWidth = '0'; }
  _drawerValId = null;
  _drawerCatId = null;
}

function _renderDrawer() {
  const inner = document.getElementById('planner-drawer-inner');
  if (!inner || !_drawerValId) return;

  const catId = _drawerCatId;
  const all   = getCacheValues(catId);
  const v     = all.find(x => x.id === _drawerValId);
  if (!v) { _plannerCloseDrawer(); return; }

  const STATUS_COLORS = { active: '#27ae60', done: '#4a90e2', archived: '#888' };
  const STATUS_LABELS = { active: '● Active', done: '✓ Done', archived: '⊘ Archived' };

  // Build parent path string
  const byId  = Object.fromEntries(all.map(x => [String(x.id), x]));
  const parts = [];
  let cur = v;
  while (cur) { parts.unshift(cur.name); cur = cur.parent_id ? byId[String(cur.parent_id)] : null; }
  const fullPath = parts.join(' / ');

  const due     = v.due_date    || '';
  const created = (v.created_at || '').slice(0, 10);
  const desc    = v.description || '';

  const btnStyle = (s) => {
    const active = v.status === s;
    const col    = STATUS_COLORS[s] || '#888';
    return `background:${active ? col : 'var(--surface2)'};color:${active ? '#fff' : 'var(--text2)'};
            border:1px solid ${active ? col : 'var(--border)'};font-size:0.62rem;
            padding:0.22rem 0.55rem;border-radius:var(--radius);cursor:pointer;
            font-family:var(--font);outline:none;transition:all 0.12s;white-space:nowrap`;
  };

  inner.innerHTML = `
    <div style="padding:0.9rem 1rem;border-bottom:1px solid var(--border);
                display:flex;align-items:flex-start;gap:0.5rem">
      <div style="flex:1;min-width:0">
        <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.15rem;
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
             title="${_esc(fullPath)}">${_esc(fullPath)}</div>
      </div>
      <button onclick="window._plannerCloseDrawer()"
        style="background:none;border:none;color:var(--muted);cursor:pointer;
               font-size:1rem;padding:0;line-height:1;flex-shrink:0">✕</button>
    </div>

    <div style="padding:0.85rem 1rem;display:flex;flex-direction:column;gap:0.9rem">

      <!-- Status -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Status</div>
        <div style="display:flex;gap:5px;flex-wrap:wrap">
          ${['active','done','archived'].map(s => `
            <button style="${btnStyle(s)}"
              onclick="window._plannerDrawerSetStatus(${v.id},'${s}')">
              ${STATUS_LABELS[s]}
            </button>`).join('')}
        </div>
      </div>

      <!-- Lifecycle -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Lifecycle</div>
        <div style="display:flex;gap:5px;flex-wrap:wrap">
          ${_LIFECYCLE_ORDER.map(lc => {
            const col = _LIFECYCLE_COLORS[lc] || '#888';
            const active = (v.lifecycle_status || 'idea') === lc;
            return `<button
              onclick="window._plannerCycleLifecycle(${v.id},'${(v.lifecycle_status || 'idea')}')"
              style="font-size:0.6rem;padding:0.18rem 0.5rem;border-radius:10px;cursor:pointer;
                     font-family:var(--font);outline:none;white-space:nowrap;border:1px solid ${col};
                     background:${active ? col : 'transparent'};color:${active ? '#fff' : col};
                     transition:all 0.12s"
              title="Advance lifecycle">${lc}</button>`;
          }).join('')}
        </div>
      </div>

      <!-- Remarks -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Remarks / Description</div>
        <textarea id="drawer-desc-ta" rows="3"
          onblur="window._plannerDrawerSaveRemarks(${v.id},this.value)"
          style="width:100%;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.68rem;
                 padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                 resize:vertical;box-sizing:border-box;line-height:1.5">${_esc(desc)}</textarea>
      </div>

      <!-- Due date -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Due Date</div>
        <input type="date" value="${_esc(due)}"
          onchange="window._plannerDrawerSaveDue(${v.id},this.value)"
          style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                 font-family:var(--font);font-size:0.68rem;padding:0.25rem 0.4rem;
                 border-radius:var(--radius);outline:none;width:100%;box-sizing:border-box" />
      </div>

      <!-- Dependencies (Blocks) -->
      <div id="drawer-links-section">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Dependencies (Blocks)</div>
        <div id="drawer-links-chips" style="display:flex;flex-wrap:wrap;gap:5px;margin-bottom:0.4rem">
          <span style="font-size:0.62rem;color:var(--muted)">Loading…</span>
        </div>
        <div style="display:flex;gap:5px;align-items:center">
          <input id="drawer-link-inp" type="text" placeholder="Value name to block…"
            list="drawer-link-datalist"
            style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.65rem;padding:0.2rem 0.4rem;
                   border-radius:var(--radius);outline:none" />
          <datalist id="drawer-link-datalist">
            ${getCacheValues(catId).map(vv => `<option value="${_esc(vv.name)}"></option>`).join('')}
          </datalist>
          <button onclick="window._plannerDrawerAddLink(${v.id},${catId})"
            style="background:var(--accent);border:none;color:#fff;font-size:0.6rem;
                   padding:0.2rem 0.5rem;border-radius:var(--radius);cursor:pointer;
                   font-family:var(--font);outline:none;white-space:nowrap">+ Link</button>
        </div>
        <div id="drawer-link-msg" style="font-size:0.6rem;color:var(--muted);margin-top:0.2rem;min-height:0.8rem"></div>
      </div>

      <!-- Meta -->
      <div style="display:flex;gap:1.5rem">
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.2rem">Created</div>
          <div style="font-size:0.68rem;color:var(--text2)">${created || '—'}</div>
        </div>
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.2rem">Events</div>
          <div style="font-size:0.68rem;color:var(--text2)">${v.event_count || 0}</div>
        </div>
      </div>

      <!-- AI Pipeline (feature/bug/task only) -->
      ${_isWorkItemCat(_plannerState.selectedCatName) ? `
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">AI Pipeline</div>
        <div id="drawer-pipeline-content">
          <span style="font-size:0.62rem;color:var(--muted)">Checking…</span>
        </div>
      </div>` : ''}

      <!-- Add sub-tag -->
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Add Sub-tag</div>
        <div style="display:flex;gap:5px">
          <input id="drawer-child-inp" type="text" placeholder="Sub-tag name…"
            onkeydown="if(event.key==='Enter')window._plannerDrawerAddChild(${catId},${v.id})"
            style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.68rem;padding:0.22rem 0.45rem;
                   border-radius:var(--radius);outline:none" />
          <button onclick="window._plannerDrawerAddChild(${catId},${v.id})"
            style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
                   padding:0.22rem 0.55rem;border-radius:var(--radius);cursor:pointer;
                   font-family:var(--font);outline:none;white-space:nowrap">+ Add</button>
        </div>
        <div id="drawer-child-msg" style="font-size:0.6rem;color:var(--muted);margin-top:0.25rem;min-height:0.9rem"></div>
      </div>

      <!-- Danger zone -->
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <button onclick="window._plannerDeleteVal(${v.id})"
          style="background:none;border:1px solid var(--red,#e74c3c);color:var(--red,#e74c3c);
                 font-size:0.62rem;padding:0.22rem 0.6rem;border-radius:var(--radius);
                 cursor:pointer;font-family:var(--font);outline:none;
                 transition:background 0.12s,color 0.12s"
          onmouseenter="this.style.background='var(--red,#e74c3c)';this.style.color='#fff'"
          onmouseleave="this.style.background='none';this.style.color='var(--red,#e74c3c)'">
          Delete tag ✕
        </button>
      </div>

    </div>
  `;
}

function _plannerDrawerSetStatus(valId, status) {
  updateCachedValue(valId, { status });
  _renderTagTableFromCache();
  _renderCategoryList();
  _renderDrawer();  // refresh button states
  api.entities.patchValue(valId, { status })
    .catch(e => toast('Sync error: ' + e.message, 'error'));
}

function _plannerDrawerSaveRemarks(valId, text) {
  const desc = (text || '').trim();
  updateCachedValue(valId, { description: desc });
  api.entities.patchValue(valId, { description: desc })
    .catch(e => toast('Sync error: ' + e.message, 'error'));
}

function _plannerDrawerSaveDue(valId, dateStr) {
  updateCachedValue(valId, { due_date: dateStr || null });
  api.entities.patchValue(valId, { due_date: dateStr || '' })
    .catch(e => toast('Sync error: ' + e.message, 'error'));
}

async function _plannerDrawerAddChild(catId, parentId) {
  const inp = document.getElementById('drawer-child-inp');
  const msg = document.getElementById('drawer-child-msg');
  const name = (inp?.value || '').trim();
  if (!name) { if (msg) msg.textContent = 'Enter a name'; return; }
  const { project } = _plannerState;
  if (msg) msg.textContent = 'Saving…';
  try {
    const result = await api.entities.createValue({ category_id: catId, name, project, parent_id: parentId });
    addCachedValue(catId, {
      id: result.id, category_id: catId, name, description: '',
      status: 'active', event_count: 0, due_date: null, parent_id: parentId,
      created_at: new Date().toISOString(),
    });
    _collapsed.delete(parentId);  // auto-expand parent
    if (inp) inp.value = '';
    if (msg) msg.textContent = `✓ "${name}" added`;
    _renderTagTableFromCache();
    _renderCategoryList();
  } catch (e) {
    if (msg) msg.textContent = e.message;
  }
}

// ── Pipeline drawer helpers (feature / bug / task categories) ─────────────────

async function _loadDrawerPipeline(catName, valName, project) {
  const el = document.getElementById('drawer-pipeline-content');
  if (!el) return;
  try {
    const data = await api.workItems.list({ project, category: catName, name: valName });
    const wi   = (data.work_items || []).find(w => w.name === valName);
    const runBtn = `<button id="drawer-run-pipeline-btn"
      onclick="window._plannerDrawerRunPipeline('${_esc(catName)}','${_esc(valName)}','${_esc(project)}')"
      style="font-size:0.62rem;padding:0.2rem 0.55rem;background:var(--accent);border:none;
             color:#fff;border-radius:var(--radius);cursor:pointer;font-family:var(--font);
             outline:none;white-space:nowrap">▶ Run Pipeline</button>`;

    if (!wi) {
      el.innerHTML = `<div style="display:flex;gap:6px;align-items:center">
        ${runBtn}
        <span style="font-size:0.6rem;color:var(--muted)">No run yet</span>
      </div>`;
      return;
    }
    const statusBadge = wi.agent_status
      ? `<span style="font-size:0.55rem;padding:0.1rem 0.4rem;border-radius:8px;color:#fff;
                      background:${wi.agent_status==='done'?'#27ae60':wi.agent_status==='failed'?'#e74c3c':'#e67e22'}">
           ${_esc(wi.agent_status)}</span>` : '';
    const acSection = wi.acceptance_criteria
      ? `<div style="margin-top:0.5rem">
           <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.25rem">Acceptance Criteria</div>
           <div style="font-size:0.65rem;color:var(--text2);line-height:1.5;white-space:pre-wrap;
                       max-height:100px;overflow-y:auto;background:var(--surface2);
                       padding:0.35rem 0.5rem;border-radius:var(--radius)">${_esc(wi.acceptance_criteria)}</div>
         </div>` : '';
    const planSection = wi.implementation_plan
      ? `<div style="margin-top:0.5rem">
           <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.25rem">Implementation Plan</div>
           <div style="font-size:0.65rem;color:var(--text2);line-height:1.5;white-space:pre-wrap;
                       max-height:100px;overflow-y:auto;background:var(--surface2);
                       padding:0.35rem 0.5rem;border-radius:var(--radius)">${_esc(wi.implementation_plan)}</div>
         </div>` : '';
    el.innerHTML = `<div style="display:flex;gap:6px;align-items:center;margin-bottom:0.35rem">
      ${runBtn} ${statusBadge}
    </div>${acSection}${planSection}`;
  } catch (e) {
    if (el) el.innerHTML = `<span style="font-size:0.6rem;color:var(--red)">${_esc(e.message)}</span>`;
  }
}

window._plannerDrawerRunPipeline = async (catName, valName, project) => {
  const btn = document.getElementById('drawer-run-pipeline-btn');
  if (btn) { btn.disabled = true; btn.textContent = '…'; }
  try {
    // Find or create the work_item linked to this entity_value by name
    let data = await api.workItems.list({ project, category: catName, name: valName });
    let wi   = (data.work_items || []).find(w => w.name === valName);
    if (!wi) {
      wi = await api.workItems.create(project, { category_name: catName, name: valName });
    }
    const res = await api.workItems.runPipeline(wi.id, project);
    const runId = res.run_id ? String(res.run_id) : null;
    if (runId) {
      window._pendingRunOpen = runId;
      window._nav('workflow');
      let _rt = 0;
      const _ri = setInterval(() => {
        _rt += 200;
        if (window._gwOpenRun) {
          clearInterval(_ri);
          window._gwOpenRun(runId);
          window._pendingRunOpen = null;
        } else if (_rt >= 4000) {
          clearInterval(_ri);
        }
      }, 200);
    } else {
      toast('Pipeline started — check Pipelines tab for progress', 'success', 5000);
    }
    setTimeout(() => _loadDrawerPipeline(catName, valName, project), 5000);
  } catch (e) {
    toast('Pipeline error: ' + e.message, 'error');
    if (btn) { btn.disabled = false; btn.textContent = '▶ Run Pipeline'; }
  }
};

async function _plannerDeleteVal(valId) {
  if (!confirm('Delete this tag (and all its children + event links)?')) return;
  getCacheDescendants(valId).forEach(d => removeCachedValue(d.id));
  removeCachedValue(valId);
  _collapsed.delete(valId);
  _plannerCloseDrawer();
  _renderTagTableFromCache();
  _renderCategoryList();
  api.entities.deleteValue(valId)
    .catch(e => toast('Delete sync error: ' + e.message, 'error'));
}

async function _plannerSaveNewTag() {
  const inp     = document.getElementById('planner-new-tag-inp');
  const row     = document.getElementById('planner-new-tag-row');
  const name    = (inp?.value || '').trim();
  if (!name) { toast('Name required', 'error'); return; }
  const catId   = row ? parseInt(row.dataset.catId, 10) : _plannerState.selectedCat;
  const parentId = row?.dataset.parentId ? parseInt(row.dataset.parentId, 10) : null;
  const { project } = _plannerState;
  try {
    const result = await api.entities.createValue({ category_id: catId, name, project, parent_id: parentId });
    addCachedValue(catId, {
      id: result.id, category_id: catId, name, description: '',
      status: 'active', event_count: 0, due_date: null, parent_id: parentId,
      created_at: new Date().toISOString(),
    });
    if (inp) inp.value = '';
    // Auto-expand the parent so the new child is visible
    if (parentId) _collapsed.delete(parentId);
    _plannerCancelNewTag();
    _renderTagTableFromCache();
    _renderCategoryList();
  } catch (e) { toast('Create failed: ' + e.message, 'error'); }
}

function _plannerCancelNewTag() {
  const row = document.getElementById('planner-new-tag-row');
  if (row) row.style.display = 'none';
  const inp = document.getElementById('planner-new-tag-inp');
  if (inp) inp.value = '';
}

/** Open the new-tag inline form pre-configured to add a child under parentId. */
function _plannerAddChild(catId, parentId) {
  const row   = document.getElementById('planner-new-tag-row');
  const label = document.getElementById('planner-new-tag-label');
  const inp   = document.getElementById('planner-new-tag-inp');
  const parentVal = getCacheValues(catId).find(v => v.id === parentId);
  if (row) {
    row.style.display = 'flex';
    row.dataset.catId    = catId;
    row.dataset.parentId = parentId;
  }
  if (label) label.textContent = `Child of "${parentVal?.name ?? parentId}":`;
  if (inp)   inp.value = '';
  setTimeout(() => inp?.focus(), 0);
}

/** Toggle expand/collapse for a node's children. */
function _plannerToggleExpand(valId) {
  if (_collapsed.has(valId)) _collapsed.delete(valId);
  else _collapsed.add(valId);
  _renderTagTableFromCache();
}

async function _plannerNewCat(name) {
  name = (name || '').trim();
  if (!name) return;
  const { project } = _plannerState;
  const inp = document.getElementById('planner-new-cat-inp');
  try {
    const result = await api.entities.createCategory({ name, project });
    addCachedCategory({ id: result.id, name, color: '#4a90e2', icon: '⬡' });
    if (inp) inp.value = '';
    _renderCategoryList();
  } catch (e) { toast('Create failed: ' + e.message, 'error'); }
}

async function _plannerSync() {
  const { project, selectedCat, selectedCatName } = _plannerState;
  if (!project) return;
  try {
    const r = await api.entities.syncEvents(project);
    toast(`Synced — ${r.imported?.prompt || 0} prompts, ${r.imported?.commit || 0} commits`, 'success');
    // Reload cache to get updated event_counts
    await loadTagCache(project, true);
    _renderCategoryList();
    if (selectedCat) _renderTagTableFromCache();
  } catch (e) { toast(e.message, 'error'); }
}

// ── Value-link helpers ────────────────────────────────────────────────────────

async function _loadDrawerLinks(valId) {
  const chipsEl = document.getElementById('drawer-links-chips');
  if (!chipsEl) return;
  try {
    const data = await api.entities.getValueLinks(valId);
    _renderLinkChips(valId, data.outgoing || []);
  } catch {
    if (chipsEl) chipsEl.innerHTML = '<span style="font-size:0.62rem;color:var(--muted)">—</span>';
  }
}

function _renderLinkChips(fromValId, links) {
  const chipsEl = document.getElementById('drawer-links-chips');
  if (!chipsEl) return;
  if (!links.length) {
    chipsEl.innerHTML = '<span style="font-size:0.62rem;color:var(--muted)">None</span>';
    return;
  }
  chipsEl.innerHTML = links.map(lk => `
    <span style="display:inline-flex;align-items:center;gap:3px;font-size:0.62rem;
                 background:${lk.color || 'var(--accent)'}22;color:${lk.color || 'var(--accent)'};
                 border:1px solid ${lk.color || 'var(--accent)'}44;
                 padding:0.1rem 0.35rem;border-radius:10px">
      ${_esc(lk.name)}
      <span onclick="window._plannerDrawerRemoveLink(${fromValId},${lk.to_value_id})"
            style="cursor:pointer;color:var(--muted);font-size:0.75rem;margin-left:1px">×</span>
    </span>`).join('');
}

async function _plannerDrawerAddLink(fromValId, catId) {
  const inp = document.getElementById('drawer-link-inp');
  const msg = document.getElementById('drawer-link-msg');
  const name = (inp?.value || '').trim();
  if (!name) { if (msg) msg.textContent = 'Enter a value name'; return; }
  const allVals = getCacheValues(catId);
  const target = allVals.find(v => v.name === name && v.id !== fromValId);
  if (!target) { if (msg) msg.textContent = `"${name}" not found in this category`; return; }
  if (msg) msg.textContent = 'Linking…';
  try {
    await api.entities.createValueLink(fromValId, { to_value_id: target.id, link_type: 'blocks' });
    if (inp) inp.value = '';
    if (msg) msg.textContent = '✓ Linked';
    await _loadDrawerLinks(fromValId);
  } catch (e) {
    if (msg) msg.textContent = e.message;
  }
}

async function _plannerDrawerRemoveLink(fromValId, toValId) {
  try {
    await api.entities.deleteValueLink(fromValId, toValId);
    await _loadDrawerLinks(fromValId);
  } catch (e) {
    toast('Remove link failed: ' + e.message, 'error');
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _esc(str) {
  return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
                          .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
