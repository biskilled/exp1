/**
 * entities.js — Planner: Unified Tag Manager.
 *
 * Two-pane layout (category list left, tag table right) for creating and managing entity
 * values (features, bugs, tasks, etc.) with lifecycle status, due dates, nested tags, and
 * dependency links; uses tagCache for zero-latency navigation and lazy DB writes.
 * Rendered via: renderEntities() called from main.js navigateTo().
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
  aiSubtypeFilter:  null,   // filter for AI section sub-rows
};

// ── Main render ───────────────────────────────────────────────────────────────

export function renderEntities(container) {
  const project = state.currentProject?.name || '';
  _plannerState = { selectedCat: null, selectedCatName: '', selectedCatColor: '', selectedCatIcon: '', project, aiSubtypeFilter: null };

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- Header -->
      <div style="padding:0.75rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:1rem;flex-shrink:0">
        <span style="font-size:0.85rem;font-weight:700;color:var(--text)">Tag Management</span>
        ${project ? `<span style="font-size:0.65rem;color:var(--accent)">${_esc(project)}</span>` : ''}
        <button class="btn btn-ghost btn-sm" style="margin-left:auto"
          onclick="window._plannerSync()" title="Sync events + reload cache">↻ Sync</button>
        <button class="btn btn-ghost btn-sm"
          onclick="window._plannerMigrateAiTags()"
          title="Move AI-auto-created tags from bug/feature/task into AI Suggestions">⇢ Fix AI tags</button>
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

      <!-- Bottom panel: Work Items (always visible) -->
    <div id="planner-wi-panel"
         style="height:210px;flex-shrink:0;display:flex;flex-direction:column;
                background:var(--surface)">
      <!-- Resize handle -->
      <div id="wi-panel-resizer"
           style="height:5px;background:var(--border);cursor:ns-resize;flex-shrink:0;
                  display:flex;align-items:center;justify-content:center;
                  border-top:1px solid var(--border);transition:background 0.1s"
           onmousedown="window._wiPanelResizeStart(event)"
           onmouseenter="this.style.background='var(--accent)44'"
           onmouseleave="this.style.background='var(--border)'">
        <div style="width:32px;height:2px;background:var(--muted);border-radius:2px;opacity:.5"></div>
      </div>
      <!-- Panel header -->
      <div style="display:flex;align-items:center;gap:0.5rem;padding:3px 10px;
                  border-bottom:1px solid var(--border);flex-shrink:0;
                  background:var(--surface2)">
        <span style="font-size:0.6rem;font-weight:700;color:var(--text);letter-spacing:.03em">⬡ WORK ITEMS</span>
        <span id="wi-panel-count" style="font-size:0.55rem;color:var(--muted)"></span>
        <span style="flex:1"></span>
        <button id="wi-panel-add-btn"
          style="background:var(--accent);border:none;color:#fff;font-size:0.57rem;
                 padding:0.13rem 0.42rem;border-radius:var(--radius);cursor:pointer;
                 font-family:var(--font);outline:none">+ New</button>
      </div>
      <!-- Panel list (also a drop zone for unlinking) -->
      <div id="wi-panel-list" style="flex:1;overflow-y:auto;overflow-x:hidden"
           ondragover="window._wiPanelDragOver(event)"
           ondragleave="window._wiPanelDragLeave(event)"
           ondrop="window._wiPanelDrop(event)">
        <div style="padding:0.5rem 1rem;font-size:0.65rem;color:var(--muted)">Loading…</div>
      </div>
    </div>

  </div>
  `;

  // Wire window globals
  window._plannerSelectCat        = _plannerSelectCat;

  window._plannerMigrateAiTags    = _plannerMigrateAiTags;
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
  window._plannerDrawerAddLink    = _plannerDrawerAddLink;
  window._plannerDrawerRemoveLink = _plannerDrawerRemoveLink;
  window._plannerGenerateSnapshot = _plannerGenerateSnapshot;
  window._plannerDrawerMerge      = _plannerDrawerMerge;

  window._plannerRunPlan = async (tagId, tagName, catName, project) => {
    const btn = document.getElementById('drawer-planner-btn');
    const docSpan = document.getElementById('drawer-planner-doc');
    if (btn) { btn.disabled = true; btn.textContent = '…'; }
    try {
      const r = await api.tags.plan(tagId, project);
      toast(`Planner done · ${r.work_items_updated} items synced`, 'success');
      if (docSpan) docSpan.innerHTML =
        `<a href="#" onclick="event.preventDefault();window._plannerOpenDoc('${_esc(r.doc_path)}','${_esc(project)}')"
           style="color:var(--accent);text-decoration:underline">&#128196; ${_esc(r.doc_path)}</a>`;
      setTimeout(() => window._plannerOpenDrawer && window._plannerOpenDrawer(
        getCacheCategories().find(c => c.name === catName)?.id, tagId), 300);
    } catch (e) { toast('Planner error: ' + e.message, 'error'); }
    finally { if (btn) { btn.disabled = false; btn.textContent = '&#9641; Run Planner'; } }
  };

  window._plannerOpenDoc = (docPath, project) => {
    const nav = document.querySelector('[data-view="documents"]');
    if (nav) nav.click();
    setTimeout(() => window._documentsOpenFile?.(docPath, project), 250);
  };
  window._plannerOpenWorkItemDrawer = (id, cat, proj) => _openWorkItemDrawer(id, cat, proj, null, '#4a90e2', '📋');

  window._extractWorkItemCode = async (id, project) => {
    const btn = document.getElementById(`wi-extract-btn-${id}`);
    const statusEl = document.getElementById(`wi-extract-status-${id}`);
    if (btn) { btn.disabled = true; btn.textContent = '…'; }
    try {
      const r = await api.workItems.extract(id, project);
      const agg = r.aggregated || {};
      const msg = `${agg.commit_count || 0} commits · ${(agg.all_files || []).length} files`;
      toast(`Extracted · ${msg}`, 'success');
      if (statusEl) statusEl.textContent = msg;
      // Refresh ai_tags display
      const aiTagsEl = document.getElementById(`wi-ai-tags-${id}`);
      if (aiTagsEl) {
        const cs = r.code_summary || {};
        const tc = r.test_coverage || {};
        const parts = [];
        if (cs.key_classes?.length)  parts.push(`Classes: ${cs.key_classes.join(', ')}`);
        if (cs.key_methods?.length)  parts.push(`Methods: ${cs.key_methods.join(', ')}`);
        if (tc.missing?.length)      parts.push(`<span style="color:#e67e22">Missing tests: ${tc.missing.join(', ')}</span>`);
        if (parts.length) {
          aiTagsEl.innerHTML = `<div style="font-size:0.52rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:0.2rem;color:var(--muted)">Code Intelligence</div>`
            + parts.map(p => `<div style="font-size:0.6rem;color:var(--muted)">${p}</div>`).join('');
        }
      }
    } catch (e) { toast('Extract error: ' + e.message, 'error'); }
    finally { if (btn) { btn.disabled = false; btn.textContent = '&#11041; Extract Code'; } }
  };

  window._wiBotDragStart = (e, id, name, cat) => {
    _dragWiData = { id, ai_name: name, ai_category: cat };
    e.dataTransfer.effectAllowed = 'link';
    e.dataTransfer.setData('text/plain', id);
    e.currentTarget.style.opacity = '0.5';
  };
  window._wiBotDragEnd = (e) => {
    if (e && e.currentTarget) e.currentTarget.style.opacity = '';
    _dragWiData = null;
    document.querySelectorAll('[data-tag-id]').forEach(r => { r.style.background = ''; r.style.outline = ''; });
    const h = document.getElementById('planner-dnd-hint');
    if (h) h.style.display = 'none';
  };
  window._wiBotItemDragOver = (e, el) => {
    const targetId = el.dataset.wiId;
    if (!_dragWiData || !targetId || targetId === _dragWiData.id) return;
    e.preventDefault();
    e.stopPropagation();
    el.style.outline = '2px solid var(--accent)';
    const h = document.getElementById('planner-dnd-hint');
    if (h) { h.style.display = 'block'; h.textContent = `⊕ Merge with "${_esc(el.dataset.wiName || '')}"`;
             h.style.left = (e.clientX+16)+'px'; h.style.top = (e.clientY+12)+'px'; }
  };
  window._wiBotItemDragLeave = (e, el) => { el.style.outline = ''; };
  window._wiBotItemDrop = async (e, targetId, proj) => {
    e.preventDefault();
    e.stopPropagation();
    const el = e.currentTarget;
    el.style.outline = '';
    if (!_dragWiData || !targetId || targetId === _dragWiData.id) return;
    const sourceId = _dragWiData.id;
    const sourceName = _dragWiData.ai_name;
    _dragWiData = null;
    try {
      await api.workItems.merge(sourceId, targetId, proj);
      toast(`Merged "${sourceName}" ⊕ merged`, 'success');
      _loadWiPanel(proj);
    } catch(err) { toast('Merge failed: ' + err.message, 'error'); }
  };
  window._wiUnlink = async (id, proj) => {
    try {
      await api.workItems.patch(id, proj, { tag_id: '' });
      toast('Unlinked', 'success');
      _loadWiPanel(proj);
      const { selectedCatName } = _plannerState;
      if (selectedCatName && _isWorkItemCat(selectedCatName)) {
        _loadTagLinkedWorkItems(proj, selectedCatName).catch(() => {});
      } else {
        _renderTagTableFromCache();
      }
    } catch(err) { toast('Unlink failed: ' + err.message, 'error'); }
  };
  window._wiPanelNewItem = () => {
    const { project } = _plannerState;
    const cat = prompt('Category (bug/feature/task):');
    if (!cat) return;
    const name = prompt('Work item name:');
    if (!name) return;
    api.workItems.create(project, { ai_category: cat.toLowerCase(), ai_name: name })
      .then(() => { toast(`Created "${name}"`, 'success'); _loadWiPanel(project); })
      .catch(err => toast(err.message, 'error'));
  };
  document.getElementById('wi-panel-add-btn')?.addEventListener('click', window._wiPanelNewItem);

  // Resize handle: drag up = taller, drag down = shorter
  window._wiPanelResizeStart = (e) => {
    e.preventDefault();
    const panel = document.getElementById('planner-wi-panel');
    if (!panel) return;
    const startY = e.clientY;
    const startH = panel.offsetHeight;
    const resizer = document.getElementById('wi-panel-resizer');
    if (resizer) resizer.style.background = 'var(--accent)66';
    const onMove = (ev) => {
      const delta = startY - ev.clientY;  // drag up = positive = taller
      panel.style.height = Math.max(60, Math.min(520, startH + delta)) + 'px';
    };
    const onUp = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      if (resizer) resizer.style.background = '';
    };
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  };

  // Drag from sub-row in top pane back to bottom panel (to unlink)
  window._wiSubRowDragStart = (e, id, name, cat) => {
    _dragWiData = { id, ai_name: name, ai_category: cat };
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', id);
  };

  // Bottom panel drop zone (accept work items dragged from top → unlink)
  window._wiPanelDragOver = (e) => {
    if (_dragWiData) {
      e.preventDefault();
      e.dataTransfer.dropEffect = 'move';
      const list = document.getElementById('wi-panel-list');
      if (list) list.style.outline = '2px dashed var(--accent)';
    }
  };
  window._wiPanelDragLeave = (e) => {
    const list = document.getElementById('wi-panel-list');
    if (list && !list.contains(e.relatedTarget)) list.style.outline = '';
  };
  window._wiPanelDrop = async (e) => {
    e.preventDefault();
    const list = document.getElementById('wi-panel-list');
    if (list) list.style.outline = '';
    if (!_dragWiData) return;
    const wi = { ..._dragWiData };
    _dragWiData = null;
    const proj = _plannerState.project;
    try {
      await api.workItems.patch(wi.id, proj, { tag_id: '' });
      toast(`Unlinked "${wi.ai_name}"`, 'success');
      _loadWiPanel(proj);
      _loadTagLinkedWorkItems(proj).catch(() => {});
    } catch(err) { toast('Unlink failed: ' + err.message, 'error'); }
  };

  if (!project) {
    document.getElementById('planner-tags-pane').innerHTML =
      '<div style="color:var(--muted);font-size:0.7rem;padding:3rem;text-align:center">No project open</div>';
    return;
  }

  _initPlanner(project);
}

// ── Init: use cache if warm, otherwise load ──────────────────────────────────

async function _initPlanner(project) {
  const cats0 = getCacheCategories();
  // Force reload if: not loaded, wrong project, has fallback null-IDs,
  // or values are empty for all categories that claim to have items (stale fallback load).
  const hasFallback  = cats0.some(c => c.id === null);
  const hasStaleVals = isCacheLoaded() && cats0.length > 0 &&
    cats0.every(c => (c.value_count || 0) > 0 && getCacheValues(c.id).length === 0);

  if (!isCacheLoaded() || getCacheProject() !== project || hasFallback || hasStaleVals) {
    document.getElementById('planner-cat-list').innerHTML =
      '<div style="color:var(--muted);font-size:0.62rem;padding:8px 10px">Loading…</div>';
    await loadTagCache(project, true);
  }
  _renderCategoryList();
  // Auto-select first pipeline category (feature/bug/task), else first overall
  const cats = getCacheCategories();
  if (!_plannerState.selectedCat && cats.length > 0) {
    const first = cats.find(c => _isWorkItemCat(c.name) && c.id != null) || cats.find(c => c.id != null);
    if (first) await _plannerSelectCat(first.id, first.name);
  }
  // Load persistent work items bottom panel
  _loadWiPanel(project);
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

  const pipeline  = cats.filter(c => _isWorkItemCat(c.name));
  const tags      = cats.filter(c => !_isWorkItemCat(c.name) && c.name !== 'ai_suggestion');

  const isSel = (id) => _plannerState.selectedCat === id;
  const catRow = c => `
    <div class="planner-cat-row" data-id="${c.id}" data-cat-name="${_esc(c.name)}"
         onclick="window._plannerSelectCat(${c.id},'${_esc(c.name)}')"
         ondragover="window._plannerCatDragOver(event,${c.id},'${_esc(c.name)}')"
         ondragleave="window._plannerCatDragLeave(event)"
         ondrop="window._plannerCatDrop(event,${c.id},'${_esc(c.name)}')"
         style="display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:5px;
                cursor:pointer;margin-bottom:2px;transition:background 0.1s;
                background:${isSel(c.id) ? 'var(--accent)22' : 'transparent'};
                border-left:2px solid ${isSel(c.id) ? 'var(--accent)' : 'transparent'}">
      <span style="color:${c.color};font-size:0.85rem">${c.icon}</span>
      <span style="font-size:0.65rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(c.name)}</span>
      <span style="font-size:0.55rem;color:var(--muted);flex-shrink:0">${getCacheValues(c.id).length}</span>
    </div>`;

  const divider = tags.length ? `
    <div style="font-size:0.5rem;text-transform:uppercase;letter-spacing:.1em;
                color:var(--muted);padding:8px 8px 3px;margin-top:4px;
                border-top:1px solid var(--border)">Tags</div>` : '';

  list.innerHTML = pipeline.map(catRow).join('') + divider + tags.map(catRow).join('');
}

async function _plannerSelectCat(catId, catName) {
  _plannerState.aiSubtypeFilter = null;

  // Fallback categories have null IDs — reload cache and resolve real ID by name
  if (catId === null || catId === undefined) {
    const pane = document.getElementById('planner-tags-pane');
    if (pane) pane.innerHTML = '<div style="color:var(--muted);font-size:0.7rem;padding:16px">Loading…</div>';
    await loadTagCache(_plannerState.project, true);
    const real = getCacheCategories().find(c => c.name === catName && c.id != null);
    if (real) return _plannerSelectCat(real.id, real.name);
    if (pane) pane.innerHTML = '<div style="color:var(--muted);font-size:0.7rem;padding:16px">Database not ready yet — try again shortly</div>';
    return;
  }
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

// ── Work Items bottom panel ────────────────────────────────────────────────────

let _dragWiData = null;   // { id, ai_name, ai_category } — set while dragging a work item
let _wiPanelItems = {};   // id → wi object, cache for bottom panel

async function _loadWiPanel(project) {
  const list = document.getElementById('wi-panel-list');
  if (!list) return;
  try {
    const data = await api.workItems.unlinked(project);
    const items = data.items || [];
    _wiPanelItems = {};
    items.forEach(wi => { _wiPanelItems[wi.id] = wi; });
    _renderWiPanel(items, project);
    const cnt = document.getElementById('wi-panel-count');
    if (cnt) cnt.textContent = items.length ? `(${items.length} unlinked)` : '(all linked ✓)';
  } catch(e) {
    if (list) list.innerHTML = '<div style="padding:0.5rem 1rem;font-size:0.65rem;color:var(--muted)">Could not load work items</div>';
  }
}

function _renderWiPanel(items, project) {
  const list = document.getElementById('wi-panel-list');
  if (!list) return;
  if (!items.length) {
    list.innerHTML = '<div style="padding:0.5rem 1rem;font-size:0.65rem;color:var(--muted)">No work items yet — click + New to create one</div>';
    return;
  }

  const CAT_ICON  = { feature: '✨', bug: '🐛', task: '📋' };
  const STATUS_C  = { active: '#27ae60', in_progress: '#e67e22', done: '#4a90e2', paused: '#888' };

  // Sort state for bottom panel (separate from the category-pane sort)
  if (!window._wiPanelSort) window._wiPanelSort = { field: 'updated_at', dir: 'desc' };
  const { field, dir } = window._wiPanelSort;
  const mul = dir === 'asc' ? 1 : -1;
  const sorted = [...items].sort((a, b) => {
    if (field === 'prompt_count')  return mul * ((a.prompt_count||0)  - (b.prompt_count||0));
    if (field === 'commit_count')  return mul * ((a.commit_count||0)  - (b.commit_count||0));
    return mul * (new Date(a.updated_at||a.created_at||0) - new Date(b.updated_at||b.created_at||0));
  });

  function fmtDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    const yy = String(d.getFullYear()).slice(2);
    const mo = String(d.getMonth()+1).padStart(2,'0');
    const dd = String(d.getDate()).padStart(2,'0');
    const hh = String(d.getHours()).padStart(2,'0');
    const mn = String(d.getMinutes()).padStart(2,'0');
    return `${yy}/${mo}/${dd}-${hh}:${mn}`;
  }

  function hdr(f, label) {
    const active = window._wiPanelSort.field === f;
    const arrow  = active ? (window._wiPanelSort.dir === 'asc' ? '↑' : '↓') : '↕';
    return `<th onclick="window._wiPanelResort('${f}')"
      style="text-align:right;padding:5px 10px;cursor:pointer;user-select:none;white-space:nowrap;
             font-size:0.68rem;font-weight:600;letter-spacing:.03em;text-transform:uppercase;
             color:${active?'var(--accent)':'var(--muted)'};background:var(--surface2);
             border-bottom:2px solid ${active?'var(--accent)':'var(--border)'};border-left:1px solid var(--border);
             position:sticky;top:0;z-index:1">
      ${label}&nbsp;<span style="opacity:${active?1:.35};font-size:0.62rem">${arrow}</span>
    </th>`;
  }

  window._wiPanelResort = (f) => {
    if (window._wiPanelSort.field === f) {
      window._wiPanelSort.dir = window._wiPanelSort.dir === 'asc' ? 'desc' : 'asc';
    } else {
      window._wiPanelSort.field = f;
      window._wiPanelSort.dir = 'desc';
    }
    _renderWiPanel(Object.values(_wiPanelItems), project);
  };

  window._wiPanelDelete = async (id, proj) => {
    if (!confirm('Remove this work item?')) return;
    try {
      await api.workItems.delete(id, proj);
      delete _wiPanelItems[id];
      const remaining = Object.values(_wiPanelItems);
      _renderWiPanel(remaining, proj);
      const cnt = document.getElementById('wi-panel-count');
      if (cnt) cnt.textContent = remaining.length ? `(${remaining.length} unlinked)` : '(all linked ✓)';
    } catch(e) { toast('Delete failed: ' + e.message, 'error'); }
  };

  window._wiPanelApproveTag = async (id, proj) => {
    const wi = _wiPanelItems[id];
    if (!wi || !wi.ai_tag_id) return;
    try {
      await api.workItems.patch(id, proj, { tag_id: wi.ai_tag_id });
      delete _wiPanelItems[id];  // now linked → remove from unlinked panel
      const remaining = Object.values(_wiPanelItems);
      _renderWiPanel(remaining, proj);
      const cnt = document.getElementById('wi-panel-count');
      if (cnt) cnt.textContent = remaining.length ? `(${remaining.length} unlinked)` : '(all linked ✓)';
      toast(`Linked to "${wi.ai_tag_name}"`, 'success');
    } catch(e) { toast('Approve failed: ' + e.message, 'error'); }
  };

  window._wiPanelRemoveTag = async (id, proj) => {
    try {
      await api.workItems.patch(id, proj, { ai_tag_id: '', ai_tags: {} });
      if (_wiPanelItems[id]) {
        _wiPanelItems[id].ai_tag_id = null;
        _wiPanelItems[id].ai_tag_name = null;
        _wiPanelItems[id].ai_tag_category = null;
        _wiPanelItems[id].ai_tag_color = null;
        _wiPanelItems[id].ai_tags = {};
      }
      _renderWiPanel(Object.values(_wiPanelItems), proj);
    } catch(e) { toast('Remove failed: ' + e.message, 'error'); }
  };

  window._wiPanelCreateTag = async (id, tagName, categoryName, proj) => {
    const catLabel = categoryName || 'task';
    if (!confirm(`Create new ${catLabel} tag "${tagName}" and link this work item?`)) return;
    try {
      // Resolve category id from name
      const cats = await api.tags.categories.list(proj);
      const catObj = cats.find(c => c.name === catLabel) || cats.find(c => c.name === 'task') || cats[0];
      const newTag = await api.tags.create({ name: tagName, project: proj, category_id: catObj?.id });
      await api.workItems.patch(id, proj, { tag_id: newTag.id });
      delete _wiPanelItems[id];
      const remaining = Object.values(_wiPanelItems);
      _renderWiPanel(remaining, proj);
      const cnt = document.getElementById('wi-panel-count');
      if (cnt) cnt.textContent = remaining.length ? `(${remaining.length} unlinked)` : '(all linked ✓)';
      toast(`Created ${catLabel} tag "${tagName}" and linked`, 'success');
    } catch(e) { toast('Create failed: ' + e.message, 'error'); }
  };

  const LBL_BASE = 'font-size:0.58rem;font-weight:600;flex-shrink:0;padding:1px 5px;border-radius:3px;letter-spacing:.02em;white-space:nowrap';
  const LBL_AI_E = LBL_BASE + ';color:#27ae60;border:1px solid #27ae6066;background:#27ae6012';   // green — exists
  const LBL_AI_N = LBL_BASE + ';color:#e74c3c;border:1px solid #e74c3c66;background:#e74c3c12';   // red — new
  const LBL_USER = LBL_BASE + ';color:#4a90e2;border:1px solid #4a90e266;background:#4a90e212';   // blue — user

  const rows = sorted.map(wi => {
    const icon = CAT_ICON[wi.ai_category] || '📋';
    const sc   = STATUS_C[wi.status_user] || '#888';
    const desc = (wi.ai_desc || '').replace(/\n/g,' ').trim();
    // AI(EXISTS) — matched to an existing planner tag
    const aiTagColor = wi.ai_tag_color || '#27ae60';
    const aiTagLabel = wi.ai_tag_name
      ? (wi.ai_tag_category ? wi.ai_tag_category + ':' + wi.ai_tag_name : wi.ai_tag_name)
      : '';
    // AI(NEW) — stored in ai_tags.suggested_new + suggested_category
    const aiNew = (wi.ai_tags && wi.ai_tags.suggested_new) ? wi.ai_tags.suggested_new : '';
    const aiNewCat = (wi.ai_tags && wi.ai_tags.suggested_category) ? wi.ai_tags.suggested_category : 'task';
    const aiNewLabel = aiNew ? (aiNewCat + ':' + aiNew) : '';
    const userTagsList = Array.isArray(wi.user_tags) ? wi.user_tags : [];

    // AI row — always shown; show EXISTS first, then NEW if no exists match
    let aiRow;
    if (aiTagLabel) {
      aiRow = `<div style="display:flex;align-items:center;gap:4px;margin-top:3px;flex-wrap:wrap">
        <span style="${LBL_AI_E}">AI(EXISTS)</span>
        <span style="font-size:0.65rem;font-weight:500;padding:1px 6px;border-radius:4px;
                     color:${aiTagColor};border:1px solid ${aiTagColor};background:${aiTagColor}1a;
                     white-space:nowrap">${_esc(aiTagLabel)}</span>
        <button onclick="event.stopPropagation();window._wiPanelApproveTag('${_esc(wi.id)}','${_esc(project)}')"
          title="Link to this tag" style="background:none;border:1px solid #27ae60;color:#27ae60;
                 cursor:pointer;font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">✓</button>
        <button onclick="event.stopPropagation();window._wiPanelRemoveTag('${_esc(wi.id)}','${_esc(project)}')"
          title="Dismiss" style="background:none;border:1px solid #e74c3c;color:#e74c3c;cursor:pointer;
                 font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">×</button>
      </div>`;
    } else if (aiNew) {
      aiRow = `<div style="display:flex;align-items:center;gap:4px;margin-top:3px;flex-wrap:wrap">
        <span style="${LBL_AI_N}">AI(NEW)</span>
        <span style="font-size:0.65rem;font-weight:500;padding:1px 6px;border-radius:4px;
                     color:#e74c3c;border:1px solid #e74c3c;background:#e74c3c1a;
                     white-space:nowrap">${_esc(aiNewLabel)}</span>
        <button onclick="event.stopPropagation();window._wiPanelCreateTag('${_esc(wi.id)}','${_esc(aiNew)}','${_esc(aiNewCat)}','${_esc(project)}')"
          title="Create this tag" style="background:none;border:1px solid #e74c3c;color:#e74c3c;
                 cursor:pointer;font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">✓</button>
        <button onclick="event.stopPropagation();window._wiPanelRemoveTag('${_esc(wi.id)}','${_esc(project)}')"
          title="Dismiss" style="background:none;border:1px solid #888;color:#888;cursor:pointer;
                 font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">×</button>
      </div>`;
    } else {
      aiRow = `<div style="display:flex;align-items:center;gap:4px;margin-top:3px">
        <span style="${LBL_AI_E}">AI(EXISTS)</span>
        <span style="font-size:0.62rem;color:var(--muted);opacity:.5">—</span>
      </div>`;
    }

    // User row — always shown
    const userRow = userTagsList.length
      ? `<div style="display:flex;align-items:center;flex-wrap:wrap;gap:3px;margin-top:2px">
           <span style="${LBL_USER}">USER</span>
           ${userTagsList.map(t =>
             `<span style="font-size:0.62rem;color:#4a90e2;border:1px solid #4a90e266;background:#4a90e212;
                           padding:1px 5px;border-radius:4px;white-space:nowrap">${_esc(t)}</span>`
           ).join('')}
         </div>`
      : `<div style="display:flex;align-items:center;gap:4px;margin-top:2px">
           <span style="${LBL_USER}">USER</span>
           <span style="font-size:0.62rem;color:var(--muted);opacity:.5">—</span>
         </div>`;

    return `<tr draggable="true"
        data-wi-id="${_esc(wi.id)}"
        data-wi-name="${_esc(wi.ai_name)}"
        ondragstart="window._wiBotDragStart(event,'${_esc(wi.id)}','${_esc(wi.ai_name)}','${_esc(wi.ai_category)}')"
        ondragend="window._wiBotDragEnd(event)"
        onclick="window._plannerOpenWorkItemDrawer('${_esc(wi.id)}','${_esc(wi.ai_category)}','${_esc(project)}')"
        style="border-bottom:1px solid var(--border);cursor:pointer;transition:background 0.1s"
        onmouseenter="this.style.background='var(--surface2)'"
        onmouseleave="this.style.background=''">
      <td style="padding:4px 8px 6px 12px;min-width:0;overflow:hidden">
        <div style="display:flex;align-items:center;gap:4px;min-width:0">
          <button title="Delete this item"
            onclick="event.stopPropagation();window._wiPanelDelete('${_esc(wi.id)}','${_esc(project)}')"
            style="background:none;border:1px solid #e74c3c;color:#e74c3c;cursor:pointer;font-size:0.6rem;
                   font-weight:700;padding:1px 5px;border-radius:4px;line-height:1.5;flex-shrink:0">×</button>
          <span style="flex-shrink:0;font-size:0.78rem">${icon}</span>
          ${wi.seq_num ? `<span style="font-size:0.58rem;color:var(--muted);flex-shrink:0">#${wi.seq_num}</span>` : ''}
          <span style="font-size:0.72rem;color:var(--text);overflow:hidden;text-overflow:ellipsis;
                       white-space:nowrap;flex:1;min-width:0" title="${_esc(wi.ai_name)}">${_esc(wi.ai_name)}</span>
          <span style="font-size:0.56rem;color:${sc};background:${sc}1a;
                       padding:0 0.3rem;border-radius:6px;flex-shrink:0;white-space:nowrap">${wi.status_user||'active'}</span>
        </div>
        ${desc ? `<div style="font-size:0.63rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;
                              white-space:nowrap;margin-top:1px" title="${_esc(desc)}">${_esc(desc)}</div>` : ''}
        ${aiRow}
        ${userRow}
      </td>
      <td style="padding:4px 10px;text-align:right;white-space:nowrap;font-size:0.72rem;vertical-align:top;
                 color:var(--text2);font-variant-numeric:tabular-nums;
                 border-left:1px solid var(--border)">${wi.prompt_count||0}</td>
      <td style="padding:4px 10px;text-align:right;white-space:nowrap;font-size:0.72rem;vertical-align:top;
                 color:var(--text2);font-variant-numeric:tabular-nums;
                 border-left:1px solid var(--border)">${wi.commit_count||0}</td>
      <td style="padding:4px 10px 4px 6px;text-align:right;white-space:nowrap;font-size:0.66rem;vertical-align:top;
                 color:var(--muted);font-variant-numeric:tabular-nums;font-family:monospace;
                 border-left:1px solid var(--border)">${fmtDate(wi.updated_at||wi.created_at)}</td>
    </tr>`;
  }).join('');

  list.innerHTML = `
    <table style="width:100%;border-collapse:collapse;table-layout:fixed">
      <colgroup><col><col style="width:58px"><col style="width:58px"><col style="width:112px"></colgroup>
      <thead><tr>
        <th style="text-align:left;padding:5px 8px 5px 12px;font-size:0.68rem;font-weight:600;
                   letter-spacing:.03em;text-transform:uppercase;
                   color:var(--muted);background:var(--surface2);
                   border-bottom:2px solid var(--border);position:sticky;top:0;z-index:1">Name</th>
        ${hdr('prompt_count','Prompts')}
        ${hdr('commit_count','Commits')}
        ${hdr('updated_at','Updated')}
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

/** Load work items linked to tags in the current category, inject as sub-rows. */
async function _loadTagLinkedWorkItems(project, catName) {
  try {
    // Fetch all linked work items (no ai_category filter — a 'task' work item can be linked
    // to a 'feature' tag; we rely on the DOM tr[data-tag-id] selector to scope to current view)
    const data = await api.workItems.list({ project });
    const linked = (data.work_items || []).filter(w => w.tag_id && !w.merged_into);
    // Always clear existing sub-rows first — tags that lost all linked items would otherwise
    // keep stale sub-rows (the per-tag cleanup below only runs for tags that still have items)
    document.querySelectorAll('.wi-sub-row').forEach(r => r.remove());
    if (!linked.length) return;
    const CAT_ICON = { feature: '✨', bug: '🐛', task: '📋' };
    const STATUS_UC = { active: '#27ae60', in_progress: '#e67e22', done: '#4a90e2', paused: '#888' };
    // Group by tag_id
    const byTag = {};
    linked.forEach(w => { (byTag[w.tag_id] = byTag[w.tag_id] || []).push(w); });
    Object.entries(byTag).forEach(([tagId, wis]) => {
      const tagRow = document.querySelector(`tr[data-tag-id="${CSS.escape(tagId)}"]`);
      if (!tagRow) return;
      // Insert sub-rows (in reverse so first item ends up first)
      [...wis].reverse().forEach(wi => {
        const sc = STATUS_UC[wi.status_user] || '#888';
        const icon = CAT_ICON[wi.ai_category] || '📋';
        const tr = document.createElement('tr');
        tr.className = 'wi-sub-row';
        tr.dataset.wiId = wi.id;
        tr.dataset.parentTagId = tagId;
        tr.draggable = true;
        tr.style.cssText = 'cursor:grab;user-select:none;transition:background 0.1s';
        tr.innerHTML = `
          <td colspan="3" style="padding:2px 8px 2px 26px;border-bottom:1px solid var(--border);
                                  background:var(--accent)07">
            <div style="display:flex;align-items:center;gap:4px">
              <span style="font-size:0.7rem;flex-shrink:0">${icon}</span>
              <span style="font-size:0.63rem;color:var(--text);flex:1;overflow:hidden;
                           text-overflow:ellipsis;white-space:nowrap"
                    title="${_esc(wi.ai_desc||'')}">${_esc(wi.ai_name)}</span>
              <span style="font-size:0.52rem;color:${sc};background:${sc}22;
                           padding:0.02rem 0.25rem;border-radius:8px;flex-shrink:0">${wi.status_user||'active'}</span>
              <button title="Unlink — move back to Work Items"
                onclick="event.stopPropagation();window._wiUnlink('${_esc(wi.id)}','${_esc(project)}')"
                style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:0.75rem;
                       padding:0 3px;line-height:1;flex-shrink:0;opacity:.6"
                onmouseenter="this.style.opacity=1" onmouseleave="this.style.opacity=.6">↓</button>
            </div>
          </td>`;
        tr.addEventListener('mouseenter', () => tr.style.background = 'var(--accent)12');
        tr.addEventListener('mouseleave', () => tr.style.background = '');
        tr.addEventListener('click', (e) => {
          if (e.target.closest('button')) return;
          window._plannerOpenWorkItemDrawer(wi.id, wi.ai_category, project);
        });
        tr.addEventListener('dragstart', (e) => {
          _dragWiData = { id: wi.id, ai_name: wi.ai_name, ai_category: wi.ai_category };
          e.dataTransfer.effectAllowed = 'move';
          e.dataTransfer.setData('text/plain', wi.id);
          tr.style.opacity = '0.45';
        });
        tr.addEventListener('dragend', () => {
          tr.style.opacity = '';
          _dragWiData = null;
        });
        tagRow.parentNode.insertBefore(tr, tagRow.nextSibling);
      });
    });
  } catch(e) { /* non-critical */ }
}

// ── Old Work Items panel (kept for reference, no longer rendered in top pane) ─

async function _renderWorkItemsPane(pane, project) {
  pane.innerHTML = '<div style="color:var(--muted);font-size:0.7rem;padding:1rem">Loading…</div>';
  try {
    const [unlinkedRes, tagsTree] = await Promise.all([
      api.workItems.unlinked(project),
      api.tags.list(project),
    ]);
    const items = unlinkedRes.items || [];
    const allTags = (tagsTree.tags || []).filter(t => ['feature','bug','task'].includes((t.category_name||'').toLowerCase()));

    const CAT_ICON = { feature: '✨', bug: '🐛', task: '📋' };
    const statusColor = (s) => s === 'active' ? '#27ae60' : '#888';

    const itemRows = items.length
      ? items.map(wi => {
          const hintBadge = wi.ai_tag_name
            ? `<span style="font-size:10px;color:var(--muted);border:1px solid var(--border);
                            padding:1px 5px;border-radius:3px;opacity:.7;margin-left:4px">✦ ${_esc(wi.ai_tag_name)}</span>`
            : '';
          return `<div draggable="true"
                       data-wi-id="${_esc(wi.id)}"
                       data-wi-name="${_esc(wi.ai_name)}"
                       data-wi-cat="${_esc(wi.ai_category)}"
                       ondragstart="window._wiItemDragStart(event,'${_esc(wi.id)}','${_esc(wi.ai_name)}','${_esc(wi.ai_category)}')"
                       style="display:flex;align-items:center;gap:6px;padding:5px 8px;
                              border-bottom:1px solid var(--border);cursor:grab;user-select:none">
                    <span style="font-size:0.75rem">${CAT_ICON[wi.ai_category] || '📋'}</span>
                    <span style="font-size:0.68rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                          title="${_esc(wi.ai_desc || '')}">${_esc(wi.ai_name)}</span>
                    ${hintBadge}
                    <span style="font-size:0.6rem;color:var(--muted);flex-shrink:0">[drag to link ↓]</span>
                  </div>`;
        }).join('')
      : '<div style="padding:8px 10px;font-size:0.65rem;color:var(--muted)">No unlinked work items</div>';

    const byCategory = {};
    allTags.forEach(t => {
      const c = (t.category_name || 'other').toLowerCase();
      (byCategory[c] = byCategory[c] || []).push(t);
    });

    const tagDropZones = Object.entries(byCategory).map(([cat, tagList]) => `
      <div style="margin-top:4px">
        <div style="font-size:0.55rem;text-transform:uppercase;letter-spacing:.08em;
                    color:var(--muted);padding:6px 8px 3px">${CAT_ICON[cat]||'⬡'} ${_esc(cat)}s</div>
        ${tagList.map(t => `
          <div data-tag-id="${_esc(t.id)}" data-tag-name="${_esc(t.name)}"
               ondragover="event.preventDefault();this.style.background='var(--accent)22'"
               ondragleave="this.style.background=''"
               ondrop="window._wiItemDrop(event,'${_esc(t.id)}','${_esc(project)}')"
               style="padding:5px 8px 5px 20px;border-bottom:1px solid var(--border);
                      font-size:0.66rem;color:var(--text2);transition:background 0.1s;cursor:default">
            ${_esc(t.name)}
          </div>`).join('')}
      </div>`).join('');

    pane.innerHTML = `
      <div style="display:flex;flex-direction:column;height:100%">
        <div style="font-size:0.55rem;text-transform:uppercase;letter-spacing:.08em;
                    color:var(--muted);padding:8px 10px 4px;border-bottom:1px solid var(--border);
                    display:flex;align-items:center;gap:6px">
          ⬡ UNLINKED WORK ITEMS
          <span style="font-size:0.65rem;font-weight:600;color:var(--text);margin-left:2px">${items.length}</span>
        </div>
        <div style="flex:0 0 auto;max-height:240px;overflow-y:auto;border-bottom:2px solid var(--border)">
          ${itemRows}
        </div>
        <div style="font-size:0.55rem;text-transform:uppercase;letter-spacing:.08em;
                    color:var(--muted);padding:8px 10px 4px">
          ─── LINK TO TAG ───
        </div>
        <div style="flex:1;overflow-y:auto">
          ${tagDropZones || '<div style="padding:8px 10px;font-size:0.65rem;color:var(--muted)">No feature/bug/task tags yet</div>'}
        </div>
      </div>`;

    window._wiItemDragStart = (event, id, ai_name, ai_category) => {
      _dragWiData = { id, ai_name, ai_category };
      event.dataTransfer.effectAllowed = 'link';
    };
    window._wiItemDrop = async (event, tagId, proj) => {
      event.preventDefault();
      event.currentTarget.style.background = '';
      if (!_dragWiData) return;
      try {
        await api.workItems.patch(_dragWiData.id, proj, { tag_id: tagId });
        _dragWiData = null;
        // Refresh panel and unlinked count
        _renderWorkItemsPane(pane, proj);
        const el = document.getElementById('wi-unlinked-count');
        api.workItems.unlinked(proj).then(d => { if (el) el.textContent = d.total > 0 ? d.total : ''; }).catch(()=>{});
      } catch(e) { toast('Link failed: ' + e.message, 'error'); }
    };
  } catch(e) {
    pane.innerHTML = `<div style="padding:1rem;color:#e74c3c;font-size:0.72rem">Error: ${_esc(e.message)}</div>`;
  }
}

// ── Work item categories ──────────────────────────────────────────────────────

const _WORK_ITEM_CATEGORIES = new Set(['feature', 'bug', 'task']);

function _isWorkItemCat(name) {
  return _WORK_ITEM_CATEGORIES.has((name || '').toLowerCase());
}

// ── Tag table ─────────────────────────────────────────────────────────────────

// Which parent rows are collapsed (set of value IDs whose children are hidden)
const _collapsed = new Set();

let _dragTag        = null;   // { id, name, category_id, category_name } of dragged tag
let _dragWi         = null;   // { id, name, catName } of dragged work item
let _dragOverRow    = null;   // currently highlighted <tr> DOM element
let _dragZone       = null;   // 'top' | 'mid' | 'bot'
let _dragOverTagRow = null;   // single tag row highlighted during work-item drag

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
// Sort state for work items table
let _wiSort = { field: 'updated_at', dir: 'desc' };

async function _renderWorkItemTable(pane, catName, catColor, catIcon, project) {
  pane.innerHTML = `
    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem">
      <span style="font-size:0.8rem;color:${catColor}">${catIcon}</span>
      <span style="font-size:0.78rem;font-weight:600;color:var(--text)">${_esc(catName)}</span>
      <button onclick="window._plannerShowNewWorkItem('${_esc(catName)}')"
        style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
               padding:0.2rem 0.55rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none;margin-left:auto">+ New</button>
    </div>
    <div id="wi-table-body" style="color:var(--muted);font-size:0.7rem;padding:1rem;text-align:center">
      Loading…
    </div>
  `;

  // Wire globals up front so they're always available
  window._plannerShowNewWorkItem = async (cn) => {
    const name = prompt(`New ${cn} name:`);
    if (!name) return;
    try {
      await api.workItems.create(project, { ai_category: cn, ai_name: name });
      _renderWorkItemTable(pane, catName, catColor, catIcon, project);
    } catch (e) { toast('Create failed: ' + e.message, 'error'); }
  };
  window._plannerOpenWorkItemDrawer = (id, cn, proj) => _openWorkItemDrawer(id, cn, proj, pane, catColor, catIcon);
  window._wiResort = (field) => {
    if (_wiSort.field === field) {
      _wiSort.dir = _wiSort.dir === 'asc' ? 'desc' : 'asc';
    } else {
      _wiSort.field = field;
      _wiSort.dir = 'desc';
    }
    const tb = document.getElementById('wi-table-body');
    if (tb) _wiSetTableBody(tb, _wiItemsCache, catName, catColor, catIcon, project);
  };

  try {
    const data = await api.workItems.list(project, catName);
    const items = data.work_items || [];

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

    _wiSetTableBody(tableBody, _wiItemsCache, catName, catColor, catIcon, project);
  } catch (e) {
    const tb = document.getElementById('wi-table-body');
    if (tb) tb.textContent = `Error loading ${catName}s: ${e.message}`;
  }
}

/** Render work item rows into tableBody and attach DnD listeners. */
function _wiSetTableBody(tableBody, byId, catName, catColor, catIcon, project) {
  if (!tableBody) return;
  tableBody.innerHTML = _wiRenderRows(byId, catName, catColor, catIcon, project);
  _attachWorkItemDnd(tableBody, catName, project);
}

function _wiRenderRows(byId, catName, catColor, catIcon, project) {
  const rows = Object.values(byId);

  // Sort rows client-side
  const { field, dir } = _wiSort;
  const mul = dir === 'asc' ? 1 : -1;
  rows.sort((a, b) => {
    if (field === 'prompt_count')  return mul * ((a.prompt_count||0)  - (b.prompt_count||0));
    if (field === 'commit_count')  return mul * ((a.commit_count||0)  - (b.commit_count||0));
    // default: updated_at / created_at
    return mul * (new Date(a.updated_at||a.created_at||0) - new Date(b.updated_at||b.created_at||0));
  });

  // Date → yymmddhhmm (local time)
  function fmtDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    const yy = String(d.getFullYear()).slice(2);
    const mo = String(d.getMonth()+1).padStart(2,'0');
    const dd = String(d.getDate()).padStart(2,'0');
    const hh = String(d.getHours()).padStart(2,'0');
    const mn = String(d.getMinutes()).padStart(2,'0');
    return `${yy}${mo}${dd}${hh}${mn}`;
  }

  // Sortable column header
  function hdr(f, label, align='right') {
    const active = _wiSort.field === f;
    const arrow  = active ? (_wiSort.dir === 'asc' ? ' ↑' : ' ↓') : '';
    return `<th onclick="window._wiResort('${f}')"
      style="text-align:${align};padding:0.35rem 0.5rem;white-space:nowrap;cursor:pointer;
             user-select:none;font-size:0.68rem;font-weight:${active?'600':'400'};
             color:${active?'var(--text)':'var(--muted)'};border-bottom:2px solid var(--border)">
      ${label}${arrow}
    </th>`;
  }

  const STATUS_C = {active:'#27ae60', in_progress:'#e67e22', done:'#4a90e2', paused:'#888'};

  function rowFor(wi) {
    const su  = wi.status_user || 'active';
    const sc  = STATUS_C[su] || '#888';
    const desc = (wi.ai_desc||'').replace(/\n/g,' ');
    const descClip = desc.length > 90 ? desc.slice(0,90)+'…' : desc;
    const date = fmtDate(wi.updated_at || wi.created_at);
    const linked = wi.tag_id
      ? `<span style="font-size:0.5rem;color:var(--accent);margin-left:4px">✓</span>`
      : (wi.ai_tag_id ? `<span style="font-size:0.5rem;color:var(--muted);margin-left:4px">✦</span>` : '');

    return `
      <tr draggable="true" data-wi-id="${wi.id}" data-wi-name="${_esc(wi.ai_name)}"
          style="border-bottom:1px solid var(--border);cursor:pointer;transition:background 0.1s"
          onclick="window._plannerOpenWorkItemDrawer('${_esc(wi.id)}','${_esc(catName)}','${_esc(project)}')"
          onmouseenter="this.style.background='var(--surface2)'"
          onmouseleave="this.style.background=''">
        <td style="padding:0.42rem 0.5rem;min-width:0">
          <div style="display:flex;align-items:baseline;gap:0.35rem">
            ${wi.seq_num ? `<span style="font-size:0.5rem;color:var(--muted);flex-shrink:0;white-space:nowrap">#${wi.seq_num}</span>` : ''}
            <span style="font-size:0.7rem;font-weight:500;color:var(--text);
                         overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                  title="${_esc(wi.ai_name)}">${_esc(wi.ai_name)}</span>
            <span style="font-size:0.5rem;color:${sc};background:${sc}22;
                         padding:0 0.3rem;border-radius:8px;flex-shrink:0;white-space:nowrap">${su}</span>
            ${linked}
          </div>
          ${descClip ? `<div style="font-size:0.6rem;color:var(--muted);margin-top:0.08rem;
                                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                             title="${_esc(desc)}">${_esc(descClip)}</div>` : ''}
        </td>
        <td style="padding:0.42rem 0.5rem;text-align:right;white-space:nowrap;
                   font-size:0.65rem;color:var(--text2);font-variant-numeric:tabular-nums;
                   width:58px">${wi.prompt_count||0}</td>
        <td style="padding:0.42rem 0.5rem;text-align:right;white-space:nowrap;
                   font-size:0.65rem;color:var(--text2);font-variant-numeric:tabular-nums;
                   width:58px">${wi.commit_count||0}</td>
        <td style="padding:0.42rem 0.5rem;text-align:right;white-space:nowrap;
                   font-size:0.6rem;color:var(--muted);font-variant-numeric:tabular-nums;
                   font-family:monospace;width:82px">${date}</td>
      </tr>`;
  }

  return `
    <table style="width:100%;border-collapse:collapse;font-size:0.72rem;table-layout:fixed">
      <colgroup>
        <col><col style="width:58px"><col style="width:58px"><col style="width:82px">
      </colgroup>
      <thead>
        <tr>
          <th style="text-align:left;padding:0.35rem 0.5rem;color:var(--muted);font-weight:400;
                     font-size:0.68rem;border-bottom:2px solid var(--border)">Name / Description</th>
          ${hdr('prompt_count','Prompts')}
          ${hdr('commit_count','Commits')}
          ${hdr('updated_at','Updated')}
        </tr>
      </thead>
      <tbody>${rows.map(rowFor).join('')}</tbody>
    </table>`;
}

async function _openWorkItemDrawer(id, catName, project, pane, catColor, catIcon) {
  const drawer = document.getElementById('planner-drawer');
  const inner  = document.getElementById('planner-drawer-inner');
  if (!drawer || !inner) return;
  drawer.style.width = '300px';
  drawer.style.borderLeftWidth = '1px';

  inner.innerHTML = `<div style="padding:1rem;color:var(--muted);font-size:0.72rem">Loading…</div>`;

  try {
    // Fetch the specific work item directly (avoids limit issues with large lists)
    const [wi, sibData] = await Promise.all([
      api.workItems.get(id, project),
      api.workItems.list({ project, limit: 200 }),
    ]);
    if (!wi || wi.error) { inner.innerHTML = '<div style="padding:1rem;color:var(--muted)">Not found</div>'; return; }
    // Siblings = other non-done work items in the same context (same tag, or both unlinked)
    const siblings = (sibData.work_items || []).filter(w =>
      w.id !== id && w.status_user !== 'done' &&
      (wi.tag_id ? w.tag_id === wi.tag_id : !w.tag_id)
    );

    const drawerSeqBadge = wi.seq_num
      ? `<span style="font-size:0.55rem;color:var(--muted);background:var(--surface2);
                       border:1px solid var(--border);padding:0.1rem 0.35rem;
                       border-radius:6px;white-space:nowrap;cursor:default"
              title="Reference #${wi.seq_num}">#${wi.seq_num}</span>`
      : '';
    const linkedTagBadge = wi.tag_id
      ? `<span style="font-size:0.58rem;color:var(--accent);background:var(--accent)18;
                      padding:0.1rem 0.35rem;border-radius:8px">linked ✓</span>`
      : (wi.ai_tag_id
          ? `<span style="font-size:0.58rem;color:var(--muted);border:1px solid var(--border);
                          padding:0.1rem 0.35rem;border-radius:8px;opacity:.7">✦ suggested</span>`
          : '');
    inner.innerHTML = `
      <div style="padding:0.9rem 1rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.5rem">
        ${drawerSeqBadge}
        <strong style="font-size:0.75rem;flex:1;overflow:hidden;text-overflow:ellipsis">${_esc(wi.ai_name)}</strong>
        ${linkedTagBadge}
        <button onclick="window._plannerCloseDrawer()"
          style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:1rem">✕</button>
      </div>

      <div style="padding:0.85rem 1rem;display:flex;flex-direction:column;gap:0.85rem">

        <!-- Status row: user dropdown + AI badge -->
        <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
          <div style="display:flex;flex-direction:column;gap:0.2rem">
            <div style="font-size:0.52rem;text-transform:uppercase;color:var(--muted);
                        letter-spacing:.06em">Your Status</div>
            <select
              style="background:var(--surface2);border:1px solid var(--border);
                     color:var(--text);font-size:0.65rem;padding:0.2rem 0.4rem;
                     border-radius:var(--radius);font-family:var(--font);cursor:pointer"
              onchange="api.workItems.patch('${id}','${project}',{status_user:this.value}).catch(e=>toast(e.message,'error'))">
              ${['active','in_progress','paused','done'].map(s =>
                `<option value="${s}"${wi.status_user===s?' selected':''}>${s}</option>`).join('')}
            </select>
          </div>
          <div style="display:flex;flex-direction:column;gap:0.2rem">
            <div style="font-size:0.52rem;text-transform:uppercase;color:var(--muted);
                        letter-spacing:.06em">AI Status</div>
            <span style="font-size:0.62rem;padding:0.18rem 0.5rem;border-radius:10px;
                         color:${{active:'#27ae60',in_progress:'#e67e22',done:'#4a90e2',paused:'#888'}[wi.status_ai]||'#888'};
                         background:${{active:'#27ae60',in_progress:'#e67e22',done:'#4a90e2',paused:'#888'}[wi.status_ai]||'#888'}22;
                         border:1px solid currentColor;opacity:.8" title="AI-suggested status based on progress">
              ${_esc(wi.status_ai || 'active')}
            </span>
          </div>
        </div>

        <!-- Stats row -->
        <div style="display:flex;gap:0.6rem;flex-wrap:wrap;font-size:0.6rem;color:var(--muted)">
          <span>&#128172; <span id="wi-stat-prompts-${id}">${wi.prompt_count||0} prompts</span></span>
          <span>&#9741; ${wi.event_count||0} events</span>
          <span id="wi-stat-words-${id}">~… words</span>
          <span>&#8859; ${wi.commit_count||0} commits</span>
          <span id="wi-stat-files-${id}"></span>
        </div>

        <!-- Extract Code button -->
        <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
          <button id="wi-extract-btn-${id}"
            onclick="window._extractWorkItemCode('${id}','${project}')"
            style="font-size:0.62rem;padding:0.22rem 0.6rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font);outline:none">
            &#11041; Extract Code
          </button>
          <span id="wi-extract-status-${id}" style="font-size:0.57rem;color:var(--muted)"></span>
        </div>

        <!-- ai_tags display (populated after extract) -->
        ${wi.ai_tags && wi.ai_tags.code_summary ? `
        <div id="wi-ai-tags-${id}" style="font-size:0.6rem;color:var(--muted)">
          <div style="font-size:0.52rem;text-transform:uppercase;letter-spacing:.06em;margin-bottom:0.2rem">Code Intelligence</div>
          ${wi.ai_tags.code_summary.key_classes?.length ? `<div>Classes: ${_esc(wi.ai_tags.code_summary.key_classes.join(', '))}</div>` : ''}
          ${wi.ai_tags.code_summary.key_methods?.length ? `<div>Methods: ${_esc(wi.ai_tags.code_summary.key_methods.join(', '))}</div>` : ''}
          ${wi.ai_tags.test_coverage?.missing?.length ? `<div style="color:#e67e22">Missing tests: ${_esc(wi.ai_tags.test_coverage.missing.join(', '))}</div>` : ''}
        </div>` : `<div id="wi-ai-tags-${id}"></div>`}

        <!-- Start date -->
        <div>
          <div style="font-size:0.52rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.2rem">Start Date</div>
          <input type="date"
            value="${wi.start_date ? wi.start_date.slice(0,10) : ''}"
            style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.65rem;padding:0.2rem 0.4rem;
                   border-radius:var(--radius);outline:none"
            onchange="api.workItems.patch('${id}','${project}',{start_date:this.value||''})
                        .catch(e=>toast(e.message,'error'))" />
        </div>

        <!-- Description -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Description</div>
          <textarea rows="3"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.68rem;
                   padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                   resize:vertical;box-sizing:border-box;line-height:1.5"
            onblur="api.workItems.patch('${id}','${project}',{ai_desc:this.value}).catch(e=>toast(e.message,'error'))"
          >${_esc(wi.ai_desc || '')}</textarea>
        </div>

        <!-- Requirements -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Requirements</div>
          <textarea rows="3"
            placeholder="Describe requirements…"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                   resize:vertical;box-sizing:border-box;line-height:1.5"
            onblur="api.workItems.patch('${id}','${project}',{requirements:this.value}).catch(e=>toast(e.message,'error'))"
          >${_esc(wi.requirements || '')}</textarea>
        </div>

        <!-- Acceptance Criteria -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Acceptance Criteria</div>
          <textarea rows="4"
            placeholder="- [ ] Criteria 1&#10;- [ ] Criteria 2"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                   resize:vertical;box-sizing:border-box;line-height:1.5"
            onblur="api.workItems.patch('${id}','${project}',{acceptance_criteria:this.value}).catch(e=>toast(e.message,'error'))"
          >${_esc(wi.acceptance_criteria || '')}</textarea>
        </div>

        <!-- Action Items -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Action Items</div>
          <textarea rows="4"
            placeholder="1. Step one&#10;2. Step two"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                   resize:vertical;box-sizing:border-box;line-height:1.5"
            onblur="api.workItems.patch('${id}','${project}',{action_items:this.value}).catch(e=>toast(e.message,'error'))"
          >${_esc(wi.action_items || '')}</textarea>
        </div>

        ${wi.summary ? `
        <!-- AI Summary (read-only) -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">AI Progress Summary</div>
          <div style="font-size:0.65rem;color:var(--text2);line-height:1.5;
                      background:var(--surface2);padding:0.35rem 0.45rem;
                      border-radius:var(--radius)">${_esc(wi.summary)}</div>
        </div>` : ''}

        ${wi.code_summary ? `
        <!-- Code Summary (read-only) -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Code Summary</div>
          <div style="font-size:0.65rem;color:var(--text2);line-height:1.5;font-family:monospace;
                      background:var(--surface2);padding:0.35rem 0.45rem;
                      border-radius:var(--radius);white-space:pre-wrap">${_esc(wi.code_summary)}</div>
        </div>` : ''}

        <!-- Linked Commits (loaded async) -->
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Commits</div>
          <div id="wi-commits-${id}" style="font-size:0.65rem;color:var(--muted)">Loading…</div>
        </div>

        <!-- Merge into (only if siblings exist and this item is not itself a merged result) -->
        ${siblings.length && !wi.merge_count ? `
        <div>
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Merge Into…</div>
          <div style="display:flex;gap:5px">
            <select id="wi-merge-sel-${id}"
              style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
                     font-family:var(--font);font-size:0.65rem;padding:0.22rem 0.45rem;
                     border-radius:var(--radius);outline:none;min-width:0">
              <option value="">— select work item —</option>
              ${siblings.map(s => `<option value="${_esc(s.id)}">${_esc(s.ai_name)}</option>`).join('')}
            </select>
            <button onclick="window._wiMergeInto('${id}','${project}')"
              style="background:var(--surface2);border:1px solid var(--border);color:var(--text2);
                     font-size:0.6rem;padding:0.22rem 0.55rem;border-radius:var(--radius);
                     cursor:pointer;font-family:var(--font);outline:none;white-space:nowrap">⊕ Merge</button>
          </div>
          <div id="wi-merge-msg-${id}" style="font-size:0.6rem;color:var(--muted);margin-top:0.2rem;min-height:0.8rem"></div>
        </div>` : ''}

        <!-- Delete / Dismerge -->
        <div style="border-top:1px solid var(--border);padding-top:0.75rem;display:flex;gap:0.5rem;flex-wrap:wrap">
          ${wi.merge_count > 0 ? `
          <button onclick="window._wiDismerge('${id}','${project}')"
            title="Restore the ${wi.merge_count} original item(s) and remove this merged result"
            style="background:none;border:1px solid var(--accent);color:var(--accent);
                   font-size:0.62rem;padding:0.22rem 0.6rem;border-radius:var(--radius);
                   cursor:pointer;font-family:var(--font);outline:none">⊕ Dismerge (restore ${wi.merge_count})</button>
          ` : ''}
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
        _loadWiPanel(proj);
      } catch (e) { toast('Delete failed: ' + e.message, 'error'); }
    };

    window._wiDismerge = async (wid, proj) => {
      if (!confirm('Restore the original items and remove this merged result?')) return;
      try {
        const r = await api.workItems.dismerge(wid, proj);
        toast(`Dismerged — ${r.restored.length} item(s) restored`, 'success');
        _plannerCloseDrawer();
        _loadWiPanel(proj);
        _loadTagLinkedWorkItems(proj).catch(() => {});
      } catch (e) { toast('Dismerge failed: ' + e.message, 'error'); }
    };

    window._wiMergeInto = async (fromId, proj) => {
      const sel = document.getElementById(`wi-merge-sel-${fromId}`);
      const msg = document.getElementById(`wi-merge-msg-${fromId}`);
      const targetId = sel?.value;
      if (!targetId) { if (msg) msg.textContent = 'Select a work item first.'; return; }
      if (!confirm('Merge these two work items into a new combined item?')) return;
      try {
        if (msg) msg.textContent = 'Merging…';
        await api.workItems.merge(fromId, targetId, proj);
        toast('⊕ Merged — new combined item created', 'success');
        _plannerCloseDrawer();
        _loadWiPanel(proj);
        _loadTagLinkedWorkItems(proj).catch(() => {});
      } catch (e) {
        if (msg) msg.textContent = 'Error: ' + e.message;
        toast('Merge failed: ' + e.message, 'error');
      }
    };

    // Load commits async
    api.workItems.commits(id, project).then(d => {
      const el = document.getElementById(`wi-commits-${id}`);
      if (!el) return;
      const commits = (d && d.commits) || [];
      if (!commits.length) { el.textContent = 'No linked commits'; return; }
      el.innerHTML = commits.map(c => `
        <div style="padding:0.25rem 0;border-bottom:1px solid var(--border)">
          <div style="color:var(--text);font-weight:500">${_esc((c.commit_msg||'').slice(0,60))}${(c.commit_msg||'').length>60?'…':''}</div>
          ${c.summary ? `<div style="color:var(--muted);font-size:0.58rem;margin-top:0.15rem">${_esc(c.summary.slice(0,80))}</div>` : ''}
          <div style="color:var(--muted);font-size:0.55rem;margin-top:0.1rem">${c.commit_hash ? c.commit_hash.slice(0,8) : ''} · ${c.committed_at ? c.committed_at.slice(0,10) : ''}</div>
        </div>`).join('');

      // Parse file stats from commits
      const allFiles = {};
      let totalAdded = 0, totalRemoved = 0;
      commits.forEach(c => {
        if (!c.diff_summary) return;
        const ins = (c.diff_summary.match(/(\d+) insertions?\(\+\)/)||[])[1];
        const del = (c.diff_summary.match(/(\d+) deletions?\(-\)/)||[])[1];
        if (ins) totalAdded += parseInt(ins);
        if (del) totalRemoved += parseInt(del);
        c.diff_summary.split('\n').forEach(line => {
          const m = line.match(/^\s*(.+?)\s*\|\s*\d+/);
          if (m) allFiles[m[1].trim()] = true;
        });
      });
      const nFiles = Object.keys(allFiles).length;
      const filesEl = document.getElementById(`wi-stat-files-${id}`);
      if (filesEl && nFiles > 0)
        filesEl.textContent = `&#128193; ${nFiles} files · +${totalAdded}/-${totalRemoved}`;
      if (nFiles > 0) {
        const listHtml = Object.keys(allFiles).map(f =>
          `<div style="font-size:0.57rem;color:var(--muted)">${_esc(f)}</div>`).join('');
        el.insertAdjacentHTML('beforeend',
          `<details style="margin-top:4px"><summary style="font-size:0.58rem;
             color:var(--muted);cursor:pointer">Files (${nFiles})</summary>${listHtml}</details>`);
      }

      // Load interactions for word count
      api.workItems.interactions(id, project, 100).then(data => {
        const total = (data?.interactions||[]).reduce(
          (s, i) => s + (i.prompt||'').length + (i.response||'').length, 0);
        const wordEl = document.getElementById(`wi-stat-words-${id}`);
        if (wordEl) wordEl.textContent = `~${Math.round(total/5).toLocaleString()} words`;
      }).catch(() => {});
    }).catch(() => {
      const el = document.getElementById(`wi-commits-${id}`);
      if (el) el.textContent = 'No linked commits';
    });

  } catch (e) {
    inner.innerHTML = `<div style="padding:1rem;color:#e74c3c;font-size:0.72rem">Error: ${_esc(e.message)}</div>`;
  }
}

function _renderTagTable(pane, catId, catName, catColor, catIcon) {
  const STATUS_COLORS = { active: '#27ae60', done: '#4a90e2', archived: '#888' };
  const isAiSug = catName === 'ai_suggestion';

  // For ai_suggestion category, optionally filter by subtype prefix
  let roots = getCacheRoots(catId);
  if (isAiSug && _plannerState.aiSubtypeFilter) {
    const prefix = `[suggested: ${_plannerState.aiSubtypeFilter}]`;
    roots = roots.filter(v => (v.description || '').toLowerCase().startsWith(prefix));
  }

  // Recursively build table rows for a node and its visible children
  function _rowsForNode(v, depth) {
    const sc       = STATUS_COLORS[v.status] || '#888';
    const archived = v.status === 'archived';
    const kids     = getCacheChildren(v.id);
    const hasKids  = kids.length > 0;
    const expanded = !_collapsed.has(v.id);
    const indent   = depth * 20;

    const toggleBtn = hasKids
      ? `<span onclick="window._plannerToggleExpand('${v.id}')"
               style="cursor:pointer;color:var(--muted);margin-right:3px;display:inline-block;
                      width:14px;text-align:center;font-size:0.72rem;user-select:none;flex-shrink:0"
               title="${expanded ? 'Collapse' : 'Expand'}">${expanded ? '▾' : '▸'}</span>`
      : `<span style="display:inline-block;width:14px;margin-right:3px;flex-shrink:0"></span>`;

    let html = `
      <tr style="border-bottom:1px solid var(--border);opacity:${archived ? '0.45' : '1'};
                 transition:background 0.1s;cursor:grab;user-select:none"
          data-val-id="${v.id}" data-tag-id="${v.id}" data-tag-name="${_esc(v.name)}"
          data-cat-id="${catId}" data-cat-name="${_esc(catName)}"
          draggable="true"
          onclick="window._plannerOpenDrawer(${catId},'${v.id}')"
          onmouseenter="this.style.background='var(--surface2)'"
          onmouseleave="this.style.background=''">
        <td style="padding:0.5rem 0.5rem 0.5rem ${0.5 + indent/16}rem;
                   color:var(--text);font-weight:${depth===0?'500':'400'}">
          <div style="display:flex;align-items:center">
            ${toggleBtn}
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(v.name)}</span>
          </div>
        </td>
        <td style="padding:0.5rem 0.5rem;white-space:nowrap" onclick="event.stopPropagation()">
          <span style="font-size:0.6rem;color:${sc};background:${sc}22;
                       padding:0.12rem 0.4rem;border-radius:10px;white-space:nowrap;user-select:none">
            ${_esc(v.status || 'active')}
          </span>
        </td>
        <td style="padding:0.5rem 0.4rem;text-align:right;white-space:nowrap" onclick="event.stopPropagation()">
          <button onclick="window._plannerAddChild(${catId},'${v.id}')"
            style="font-size:0.6rem;padding:0.13rem 0.35rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font);outline:none;margin-right:3px"
            title="Add child tag">+▸</button>
          ${_isWorkItemCat(catName) ? `<button
            onclick="event.stopPropagation();window._plannerOpenDrawer(${catId},'${v.id}');
                     setTimeout(()=>window._plannerDrawerRunPipeline('${_esc(catName)}','${_esc(v.name)}','${_esc(_plannerState.project)}'),200)"
            style="font-size:0.6rem;padding:0.13rem 0.35rem;background:var(--accent)18;
                   border:1px solid var(--accent);border-radius:var(--radius);cursor:pointer;
                   color:var(--accent);font-family:var(--font);outline:none;margin-right:3px"
            title="Run AI Pipeline">▶</button>` : ''}
          <button onclick="window._plannerOpenDrawer(${catId},'${v.id}')"
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
      <span style="font-size:0.78rem;font-weight:600;color:var(--text)">
        ${isAiSug && _plannerState.aiSubtypeFilter ? `AI → ${_plannerState.aiSubtypeFilter}` : _esc(catName)}
      </span>
      ${isAiSug ? '' : `<button onclick="window._plannerShowNewTag(${catId})"
        style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
               padding:0.2rem 0.55rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none;margin-left:auto">+ New Tag</button>`}
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
          <th style="text-align:left;padding:0.35rem 0.5rem;color:var(--muted);font-weight:500;width:75px">Status</th>
          <th style="width:80px"></th>
        </tr>
      </thead>
      <tbody>
        ${roots.map(v => _rowsForNode(v, 0)).join('')}
      </tbody>
    </table>`}
  `;

  _attachTagTableDnd(pane, catName);

  // For work item categories (bug/feature/task), inject linked work items as sub-rows
  if (_isWorkItemCat(catName)) {
    const { project } = _plannerState;
    if (project) _loadTagLinkedWorkItems(project, catName).catch(() => {});
  }

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

  const STATUS_COLORS = { open: '#888', active: '#27ae60', done: '#4a90e2', archived: '#666' };
  const STATUS_LABELS = { open: '○ Open', active: '● Active', done: '✓ Done', archived: '⊘ Archived' };

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
          ${['open','active','done','archived'].map(s => `
            <button style="${btnStyle(s)}"
              onclick="window._plannerDrawerSetStatus('${v.id}','${s}')">
              ${STATUS_LABELS[s]}
            </button>`).join('')}
        </div>
      </div>

      <!-- Short Description -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.3rem">Description</div>
        <textarea id="tag-short-desc-ta" rows="2"
          style="width:100%;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.68rem;
                 padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                 resize:vertical;box-sizing:border-box;line-height:1.5"
          onblur="api.tags.update('${v.id}', {short_desc: this.value}).catch(e=>toast(e.message,'error'))"
        >${_esc(v.description || '')}</textarea>
      </div>

      <!-- Requirements -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.3rem">Requirements</div>
        <textarea id="tag-req-ta" rows="3"
          style="width:100%;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.65rem;
                 padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                 resize:vertical;box-sizing:border-box;line-height:1.5"
          onblur="api.tags.update('${v.id}', {requirements: this.value}).catch(e=>toast(e.message,'error'))"
        >${_esc(v.requirements || '')}</textarea>
      </div>

      <!-- Acceptance Criteria -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.3rem">Acceptance Criteria</div>
        <textarea id="tag-ac-ta" rows="3"
          style="width:100%;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.65rem;
                 padding:0.35rem 0.45rem;border-radius:var(--radius);outline:none;
                 resize:vertical;box-sizing:border-box;line-height:1.5"
          onblur="api.tags.update('${v.id}', {acceptance_criteria: this.value}).catch(e=>toast(e.message,'error'))"
        >${_esc(v.acceptance_criteria || '')}</textarea>
      </div>

      <!-- Priority + Due Date row -->
      <div style="display:flex;gap:0.6rem">
        <div style="flex:1">
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Priority</div>
          <select
            onchange="api.tags.update('${v.id}', {priority: parseInt(this.value)}).catch(e=>toast(e.message,'error'))"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.22rem 0.4rem;border-radius:var(--radius);outline:none">
            ${[1,2,3,4,5].map(p => `<option value="${p}" ${(v.priority||3)===p?'selected':''}>${p === 1 ? '1 Critical' : p === 2 ? '2 High' : p === 3 ? '3 Normal' : p === 4 ? '4 Low' : '5 Minimal'}</option>`).join('')}
          </select>
        </div>
        <div style="flex:1">
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      letter-spacing:.06em;margin-bottom:0.3rem">Due Date</div>
          <input type="date" value="${_esc(v.due_date ? v.due_date.slice(0,10) : '')}"
            onchange="api.tags.update('${v.id}', {due_date: this.value || null}).catch(e=>toast(e.message,'error'))"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.65rem;
                   padding:0.22rem 0.4rem;border-radius:var(--radius);outline:none;
                   box-sizing:border-box" />
        </div>
      </div>

      <!-- Remarks -->
      <div>
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Remarks / Description</div>
        <textarea id="drawer-desc-ta" rows="3"
          onblur="window._plannerDrawerSaveRemarks('${v.id}',this.value)"
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
          onchange="window._plannerDrawerSaveDue('${v.id}',this.value)"
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
          <button onclick="window._plannerDrawerAddLink('${v.id}',${catId})"
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

      <!-- Planner -->
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Planner</div>
        <div style="display:flex;gap:5px;align-items:center;flex-wrap:wrap">
          <button id="drawer-planner-btn"
            onclick="window._plannerRunPlan('${v.id}','${_esc(v.name)}','${_esc(v.category_name || _plannerState.selectedCatName)}','${_esc(_plannerState.project)}')"
            style="font-size:0.62rem;padding:0.22rem 0.6rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font);outline:none;white-space:nowrap">
            &#9641; Run Planner
          </button>
          <span id="drawer-planner-doc" style="font-size:0.57rem;color:var(--muted)"></span>
        </div>
      </div>

      <!-- Snapshot -->
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Memory Snapshot</div>
        <div style="display:flex;gap:5px;align-items:center">
          <button id="drawer-snapshot-btn"
            onclick="window._plannerGenerateSnapshot('${_esc(v.name)}','${_esc(_plannerState.project)}')"
            style="font-size:0.62rem;padding:0.22rem 0.6rem;background:var(--accent)18;
                   border:1px solid var(--accent);border-radius:var(--radius);cursor:pointer;
                   color:var(--accent);font-family:var(--font);outline:none;white-space:nowrap">
            ◈ Generate Snapshot
          </button>
          <span id="drawer-snapshot-msg" style="font-size:0.58rem;color:var(--muted)"></span>
        </div>
      </div>

      <!-- Add sub-tag -->
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                    letter-spacing:.06em;margin-bottom:0.35rem">Add Sub-tag</div>
        <div style="display:flex;gap:5px">
          <input id="drawer-child-inp" type="text" placeholder="Sub-tag name…"
            onkeydown="if(event.key==='Enter')window._plannerDrawerAddChild(${catId},'${v.id}')"
            style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.68rem;padding:0.22rem 0.45rem;
                   border-radius:var(--radius);outline:none" />
          <button onclick="window._plannerDrawerAddChild(${catId},'${v.id}')"
            style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
                   padding:0.22rem 0.55rem;border-radius:var(--radius);cursor:pointer;
                   font-family:var(--font);outline:none;white-space:nowrap">+ Add</button>
        </div>
        <div id="drawer-child-msg" style="font-size:0.6rem;color:var(--muted);margin-top:0.25rem;min-height:0.9rem"></div>
      </div>

      <!-- Danger zone -->
      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
        <button onclick="window._plannerDeleteVal('${v.id}')"
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

async function _plannerGenerateSnapshot(tagName, project) {
  const btn = document.getElementById('drawer-snapshot-btn');
  const msg = document.getElementById('drawer-snapshot-msg');
  if (!btn || !project) return;
  btn.disabled = true;
  btn.textContent = '… Generating';
  if (msg) msg.textContent = '';
  try {
    const res = await fetch(
      (window._serverUrl || 'http://localhost:8000') + `/projects/${encodeURIComponent(project)}/snapshot/${encodeURIComponent(tagName)}`,
      { method: 'POST', headers: { 'Content-Type': 'application/json', ...(window._authHeaders ? window._authHeaders() : {}) } }
    );
    if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || res.statusText); }
    if (msg) { msg.textContent = '✓ Snapshot ready'; msg.style.color = 'var(--green, #27ae60)'; }
    toast('Snapshot generated for "' + tagName + '"', 'success');
  } catch (e) {
    if (msg) { msg.textContent = '✗ ' + e.message; msg.style.color = 'var(--red, #e74c3c)'; }
    toast('Snapshot error: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '◈ Generate Snapshot';
  }
}

async function _plannerDrawerMerge(fromName, project) {
  const inp = document.getElementById('drawer-merge-inp');
  const msg = document.getElementById('drawer-merge-msg');
  const intoName = (inp?.value || '').trim();
  if (!intoName) { if (msg) msg.textContent = 'Enter target tag name'; return; }
  if (!confirm(`Merge "${fromName}" into "${intoName}"? This moves all sources to the target and marks ${fromName} as merged.`)) return;
  if (msg) msg.textContent = '…';
  try {
    await api.tags.merge({ project, from_name: fromName, into_name: intoName });
    toast(`Merged "${fromName}" → "${intoName}"`, 'success');
    await _plannerSync();
  } catch (e) {
    if (msg) msg.textContent = '✗ ' + e.message;
    toast('Merge error: ' + e.message, 'error');
  }
}

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
  const parentId = row?.dataset.parentId || null;  // UUID string or null
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
    _loadWiPanel(project);
  } catch (e) { toast(e.message, 'error'); }
}

async function _plannerMigrateAiTags() {
  const { project } = _plannerState;
  if (!project) return;
  try {
    const r = await api.tags.migrateToAiSuggestions(project);
    const n = r.moved || 0;
    if (n > 0) {
      toast(`Moved ${n} auto-created tag${n !== 1 ? 's' : ''} to AI Suggestions`, 'success');
      await loadTagCache(project, true);
      _renderCategoryList();
      _renderTagTableFromCache();
    } else {
      toast('No AI-auto-created tags found to migrate', 'info');
    }
  } catch (e) { toast('Migration failed: ' + e.message, 'error'); }
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
      <span onclick="window._plannerDrawerRemoveLink('${fromValId}','${lk.to_value_id}')"
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

// ── Drag-and-Drop ─────────────────────────────────────────────────────────────

function _dndGetZone(e, row) {
  const rect = row.getBoundingClientRect();
  const relY  = (e.clientY - rect.top) / rect.height;
  return relY < 0.28 ? 'top' : relY > 0.72 ? 'bot' : 'mid';
}

function _dndHighlight(row, zone) {
  _dndClearHighlight();
  _dragOverRow = row;  _dragZone = zone;
  if (zone === 'top')       row.style.borderTop    = '2px solid var(--accent)';
  else if (zone === 'bot')  row.style.borderBottom = '2px solid var(--accent)';
  else { row.style.background = 'rgba(255,165,0,0.08)'; row.style.outline = '1px dashed rgba(255,165,0,0.5)'; }
  const hint = document.getElementById('planner-dnd-hint');
  if (hint) {
    hint.textContent = zone === 'top' ? '↑ Make parent' : zone === 'mid' ? '⊕ Merge' : '↓ Make child';
    hint.style.color = zone === 'mid' ? '#e67e22' : 'var(--accent)';
  }
}

function _dndClearHighlight() {
  if (_dragOverRow) {
    _dragOverRow.style.borderTop = _dragOverRow.style.borderBottom = '';
    _dragOverRow.style.background = _dragOverRow.style.outline = '';
    _dragOverRow = null;
  }
  _dragZone = null;
  const h = document.getElementById('planner-dnd-hint');
  if (h) h.style.display = 'none';
}

async function _dndExecuteDrop(zone, drag, target) {
  const project = _plannerState.project;
  const catId   = _plannerState.selectedCat;

  // Cycle guard for reparent operations
  if (zone !== 'mid') {
    const dragDescs   = getCacheDescendants(drag.id)   || [];
    const targetDescs = getCacheDescendants(target.id) || [];
    if (zone === 'bot' && dragDescs.some(d => d.id === target.id))
      { toast('Cannot make a descendant a parent', 'error'); return; }
    if (zone === 'top' && targetDescs.some(d => d.id === drag.id))
      { toast('Cannot create circular hierarchy', 'error'); return; }
  }

  if (zone === 'mid') {
    if (!confirm(`Merge "${drag.name}" into "${target.name}"?\n\n"${drag.name}" will be archived and all its history remapped to "${target.name}". This cannot be undone.`)) return;
    await api.tags.merge({ project, from_name: drag.name, into_name: target.name });
    toast(`Merged "${drag.name}" → "${target.name}"`, 'success');
  } else if (zone === 'bot') {
    await api.tags.update(drag.id, { parent_id: target.id });
    toast(`"${drag.name}" is now a child of "${target.name}"`, 'success');
  } else {
    await api.tags.update(target.id, { parent_id: drag.id });
    toast(`"${target.name}" is now a child of "${drag.name}"`, 'success');
  }

  await loadTagCache(project, true);
  _renderTagTableFromCache();
  _renderCategoryList();
}

async function _dndExecuteWiDrop(zone, drag, target, project) {
  if (zone === 'mid') { toast('Merge is not supported for work items', 'error'); return; }
  // Cycle guard
  const dragKids   = Object.values(_wiItemsCache).filter(w => w.parent_id === drag.id).map(w => w.id);
  const allDescs   = new Set();
  const stack = [...dragKids];
  while (stack.length) { const n = stack.pop(); allDescs.add(n); Object.values(_wiItemsCache).filter(w => w.parent_id === n).forEach(w => stack.push(w.id)); }
  if (zone === 'bot' && allDescs.has(target.id)) { toast('Cannot make a descendant a parent', 'error'); return; }
  if (zone === 'top') {
    const tDescs = new Set();
    const ts = [target.id];
    while (ts.length) { const n = ts.pop(); tDescs.add(n); Object.values(_wiItemsCache).filter(w => w.parent_id === n).forEach(w => ts.push(w.id)); }
    if (tDescs.has(drag.id)) { toast('Cannot create circular hierarchy', 'error'); return; }
  }
  if (zone === 'bot') {
    await api.workItems.patch(drag.id, project, { parent_id: target.id });
    if (_wiItemsCache[drag.id]) _wiItemsCache[drag.id].parent_id = target.id;
    toast(`"${drag.name}" is now a child of "${target.name}"`, 'success');
  } else {
    await api.workItems.patch(target.id, project, { parent_id: drag.id });
    if (_wiItemsCache[target.id]) _wiItemsCache[target.id].parent_id = drag.id;
    toast(`"${target.name}" is now a child of "${drag.name}"`, 'success');
  }
  const tb = document.getElementById('wi-table-body');
  const { selectedCatColor: catColor, selectedCatIcon: catIcon, selectedCatName: catName } = _plannerState;
  _wiSetTableBody(tb, _wiItemsCache, catName, catColor, catIcon, project);
}

/** Attach drag-and-drop listeners to a rendered work-item tbody. */
function _attachWorkItemDnd(tableBody, catName, project) {
  _ensureDndHint();
  tableBody.querySelectorAll('tr[data-wi-id]').forEach(tr => {
    tr.addEventListener('dragstart', function(e) {
      _dragWi = { id: this.dataset.wiId, name: this.dataset.wiName, catName };
      _dragTag = null;
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', this.dataset.wiId);
      this.style.opacity = '0.45';
    });
    tr.addEventListener('dragend', function() {
      this.style.opacity = '';
      _dndClearHighlight();
      _dragWi = null;
    });
  });

  tableBody.addEventListener('dragover', function(e) {
    const row = e.target.closest('tr[data-wi-id]');
    if (!row || !_dragWi) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const zone = _dndGetZone(e, row);
    if (row !== _dragOverRow || zone !== _dragZone) _dndHighlight(row, zone);
    const h = document.getElementById('planner-dnd-hint');
    if (h) { h.style.display = 'block'; h.style.left = (e.clientX + 16) + 'px'; h.style.top = (e.clientY + 12) + 'px'; }
  });

  tableBody.addEventListener('dragleave', function(e) {
    if (!this.contains(e.relatedTarget)) _dndClearHighlight();
  });

  tableBody.addEventListener('drop', function(e) {
    e.preventDefault();
    const row = e.target.closest('tr[data-wi-id]');
    if (!row || !_dragWi || !_dragZone) { _dndClearHighlight(); return; }
    const zone = _dragZone;
    const target = { id: row.dataset.wiId, name: row.dataset.wiName };
    _dndClearHighlight();
    if (target.id === _dragWi.id) return;
    const drag = { ..._dragWi };
    _dndExecuteWiDrop(zone, drag, target, project).catch(err => toast(err.message, 'error'));
  });
}

function _ensureDndHint() {
  if (document.getElementById('planner-dnd-hint')) return;
  const h = document.createElement('div');
  h.id = 'planner-dnd-hint';
  h.style.cssText = 'position:fixed;pointer-events:none;z-index:9999;display:none;font-size:0.62rem;' +
    'background:var(--surface2);border:1px solid var(--border);padding:0.2rem 0.5rem;' +
    'border-radius:var(--radius);white-space:nowrap;font-family:var(--font)';
  document.body.appendChild(h);
}

/** Attach drag-and-drop listeners to table rows and tbody after innerHTML is set. */
function _attachTagTableDnd(pane, catName) {
  _ensureDndHint();

  // dragstart / dragend — on each draggable <tr>
  pane.querySelectorAll('tr[data-tag-id]').forEach(tr => {
    tr.addEventListener('dragstart', function(e) {
      const ds = this.dataset;
      _dragTag = { id: ds.tagId, name: ds.tagName, category_id: Number(ds.catId), category_name: ds.catName };
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', ds.tagId);
      this.style.opacity = '0.45';
    });
    tr.addEventListener('dragend', function() {
      this.style.opacity = '';
      _dndClearHighlight();
      _dragTag = null;
    });
  });

  // dragover / dragleave / drop — delegated to <tbody> so every pixel in the row responds
  const tbody = pane.querySelector('tbody');
  if (!tbody) return;

  tbody.addEventListener('dragover', function(e) {
    const row = e.target.closest('tr[data-tag-id]');
    if (!row) return;
    if (_dragWiData) {
      // Work item → tag: link work item to this tag
      e.preventDefault();
      e.dataTransfer.dropEffect = 'link';
      // Clear previous highlighted row before highlighting new one
      if (_dragOverTagRow && _dragOverTagRow !== row) {
        _dragOverTagRow.style.background = '';
        _dragOverTagRow.style.outline = '';
      }
      _dragOverTagRow = row;
      row.style.background = 'var(--accent)22';
      row.style.outline = '2px solid var(--accent)';
      _ensureDndHint();
      const h = document.getElementById('planner-dnd-hint');
      if (h) { h.style.display = 'block';
               h.textContent = `→ Link to "${row.dataset.tagName || ''}"`;
               h.style.color = 'var(--accent)';
               h.style.left = (e.clientX + 16) + 'px'; h.style.top = (e.clientY + 12) + 'px'; }
      return;
    }
    if (!_dragTag) return;
    if (_dragTag.category_name !== row.dataset.catName) { e.dataTransfer.dropEffect = 'none'; return; }
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    const zone = _dndGetZone(e, row);
    if (row !== _dragOverRow || zone !== _dragZone) _dndHighlight(row, zone);
    const h = document.getElementById('planner-dnd-hint');
    if (h) { h.style.display = 'block'; h.style.left = (e.clientX + 16) + 'px'; h.style.top = (e.clientY + 12) + 'px'; }
  });

  tbody.addEventListener('dragleave', function(e) {
    if (!this.contains(e.relatedTarget)) {
      _dndClearHighlight();
      if (_dragOverTagRow) { _dragOverTagRow.style.background = ''; _dragOverTagRow.style.outline = ''; _dragOverTagRow = null; }
      const h = document.getElementById('planner-dnd-hint');
      if (h) h.style.display = 'none';
    }
  });

  tbody.addEventListener('drop', function(e) {
    e.preventDefault();
    const row = e.target.closest('tr[data-tag-id]');
    if (!row) { _dndClearHighlight(); return; }
    row.style.background = '';
    row.style.outline = '';
    const h = document.getElementById('planner-dnd-hint');
    if (h) h.style.display = 'none';
    if (_dragWiData) {
      // Link work item to this tag
      const tagId   = row.dataset.tagId;
      const tagName = row.dataset.tagName;
      const catName = row.dataset.catName;
      const wi = { ..._dragWiData };
      _dragWiData = null;
      if (_dragOverTagRow) { _dragOverTagRow.style.background = ''; _dragOverTagRow.style.outline = ''; _dragOverTagRow = null; }
      const h = document.getElementById('planner-dnd-hint');
      if (h) h.style.display = 'none';
      const proj = _plannerState.project;
      // Optimistic: immediately remove from lower panel
      const _wiRow = document.querySelector(`#wi-panel-list [data-wi-id="${CSS.escape(wi.id)}"]`);
      if (_wiRow) {
        _wiRow.remove();
        const _cnt = document.getElementById('wi-panel-count');
        const _rem = document.querySelectorAll('#wi-panel-list [data-wi-id]').length;
        if (_cnt) _cnt.textContent = _rem ? `(${_rem} unlinked)` : '(all linked ✓)';
      }
      api.workItems.patch(wi.id, proj, { tag_id: tagId })
        .then(() => {
          toast(`Linked "${wi.ai_name}" → "${tagName}"`, 'success');
          _loadWiPanel(proj);
          // Inject sub-rows directly (no full re-render needed)
          if (catName) _loadTagLinkedWorkItems(proj, catName).catch(() => {});
        })
        .catch(err => { toast(err.message, 'error'); _loadWiPanel(proj); });
      return;
    }
    if (!_dragTag || !_dragZone) { _dndClearHighlight(); return; }
    const zone = _dragZone;
    const target = { id: row.dataset.tagId, name: row.dataset.tagName,
                     category_id: Number(row.dataset.catId), category_name: row.dataset.catName };
    _dndClearHighlight();
    if (target.id === _dragTag.id) return;
    _dndExecuteDrop(zone, { ..._dragTag }, target).catch(err => toast(err.message, 'error'));
  });
}

window._plannerCatDragOver = function(e, catId, catName) {
  if (!_dragTag || _dragTag.category_name !== 'ai_suggestion' || catName === 'ai_suggestion') return;
  e.preventDefault();
  e.dataTransfer.dropEffect = 'move';
  const el = e.target.closest('.planner-cat-row');
  if (el) { el.style.background = 'var(--accent)22'; el.style.outline = '1px solid var(--accent)'; }
  const h = document.getElementById('planner-dnd-hint');
  if (h) { h.style.display = 'block'; h.textContent = `→ Move to ${catName}`; h.style.color = 'var(--accent)';
           h.style.left = (e.clientX+16)+'px'; h.style.top = (e.clientY+12)+'px'; }
};

window._plannerCatDragLeave = function(e) {
  const el = e.target.closest('.planner-cat-row');
  if (el && !el.contains(e.relatedTarget)) {
    el.style.background = el.style.outline = '';
    const h = document.getElementById('planner-dnd-hint');
    if (h) h.style.display = 'none';
  }
};

window._plannerCatDrop = async function(e, catId, catName) {
  e.preventDefault();
  const el = e.target.closest('.planner-cat-row');
  if (el) el.style.background = el.style.outline = '';
  const h = document.getElementById('planner-dnd-hint');
  if (h) h.style.display = 'none';
  if (!_dragTag || _dragTag.category_name !== 'ai_suggestion' || catName === 'ai_suggestion') return;
  const dragCopy = { ..._dragTag };
  _dragTag = null;
  await api.tags.update(dragCopy.id, { category_id: catId });
  toast(`"${dragCopy.name}" moved to "${catName}"`, 'success');
  await loadTagCache(_plannerState.project, true);
  _renderCategoryList();
  _renderTagTableFromCache();
};

// ── Helpers ───────────────────────────────────────────────────────────────────

window._wiShowLinkedTags = async (wiId, project) => {
  try {
    const rels = await api.tags.relations.listForWorkItem(project, wiId);
    if (!rels || !rels.length) { toast('No linked tags', 'info'); return; }
    const names = rels.map(r => `${r.tag_name || r.tag_id} (${r.relation || r.related_approved || 'linked'})`).join('\n');
    alert(`Linked tags:\n${names}`);
  } catch (e) { toast('Error loading tags: ' + e.message, 'error'); }
};

function _esc(str) {
  return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
                          .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
