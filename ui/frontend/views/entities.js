/**
 * entities.js — Planner: tag hierarchy manager.
 *
 * Layout:
 *   ┌──────────────────────────────────────────────┐
 *   │ Use-case filter bar  [All] [auth] [billing]… │  ← top
 *   ├────────────┬─────────────────────────────────┤
 *   │ Category   │  Tag tree          │  Drawer    │
 *   │ sidebar    │  (nested, d&d)     │  (edit)    │
 *   │ task       │                    │            │
 *   │ feature    │                    │            │
 *   │ bug        │                    │            │
 *   │ ─────────  │                    │            │
 *   │ component  │                    │            │
 *   │ decision   │                    │            │
 *   └────────────┴─────────────────────────────────┘
 */

import { state } from '../stores/state.js';
import { api }   from '../utils/api.js';
import { toast } from '../utils/toast.js';

// ── Module state ───────────────────────────────────────────────────────────────

let _project   = '';
let _allCats   = [];      // [{id, name, color, value_count}]
let _catId     = null;    // active category id
let _catName   = '';
let _ucTagId   = null;    // active use-case filter (null = All)
let _ucSlug    = null;    // name of active use case
let _tags      = [];      // flat list of planner_tags for _catId
let _drawer    = null;    // currently-open tag object
let _dragging  = null;    // id of tag being dragged
let _collapsed = new Set(); // set of tag ids with collapsed children

const PRIMARY_CATS = ['task', 'feature', 'bug'];
const UC_CAT_NAME  = 'use_case';

// ── Public ────────────────────────────────────────────────────────────────────

export function renderEntities(container) {
  _project   = state.currentProject?.name || '';
  _catId     = null;
  _catName   = '';
  _ucTagId   = null;
  _ucSlug    = null;
  _drawer    = null;
  _dragging  = null;
  _collapsed = new Set();

  container.innerHTML = `
    <div id="pl-root" style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- Use-case filter bar (top) -->
      <div id="pl-uc-bar"
           style="padding:5px 1rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:5px;flex-wrap:wrap;flex-shrink:0;
                  background:var(--surface)">
        <span style="font-size:0.6rem;color:var(--muted);text-transform:uppercase;
                     letter-spacing:.06em;flex-shrink:0;margin-right:2px">Use case</span>
        <div id="pl-uc-chips" style="display:flex;flex-wrap:wrap;gap:4px;align-items:center">
          <span style="font-size:0.68rem;color:var(--muted)">Loading…</span>
        </div>
      </div>

      <!-- Body: sidebar + tree + drawer -->
      <div style="flex:1;display:flex;min-height:0;overflow:hidden">

        <!-- Category sidebar (left) -->
        <div id="pl-sidebar"
             style="width:138px;flex-shrink:0;border-right:1px solid var(--border);
                    overflow-y:auto;padding:0.5rem 0;background:var(--surface)">
          <div id="pl-cat-list" style="display:flex;flex-direction:column;gap:1px"></div>
          <div style="padding:0.5rem 0.7rem;margin-top:0.4rem;
                      border-top:1px solid var(--border)33">
            <button id="pl-new-cat-btn" class="pl-add-btn" style="width:100%;justify-content:center">
              + Category
            </button>
          </div>
        </div>

        <!-- Tag tree pane -->
        <div id="pl-tree-pane"
             style="flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0">

          <!-- Pane toolbar -->
          <div id="pl-tree-toolbar"
               style="padding:5px 0.8rem;border-bottom:1px solid var(--border);
                      display:flex;align-items:center;gap:0.5rem;flex-shrink:0">
            <span id="pl-tree-title"
                  style="font-size:0.75rem;font-weight:700;color:var(--text)">
              Select a category
            </span>
            <span style="flex:1"></span>
            <button id="pl-new-tag-btn" class="pl-add-btn" style="display:none">+ New</button>
          </div>

          <!-- Scrollable tree -->
          <div id="pl-tag-pane"
               style="flex:1;overflow-y:auto;padding:0.4rem 0.6rem 4rem">
            <div style="color:var(--muted);font-size:0.75rem;padding:3rem;text-align:center">
              ← Select a category
            </div>
          </div>
        </div>

        <!-- Slide-in drawer -->
        <div id="pl-drawer"
             style="width:0;overflow:hidden;border-left:0 solid var(--border);
                    flex-shrink:0;transition:width .2s ease,border-width .2s;
                    background:var(--surface)">
          <div id="pl-drawer-inner"
               style="width:290px;box-sizing:border-box;overflow-y:auto;
                      padding:1rem;height:100%"></div>
        </div>

      </div>
    </div>

    <style>
      /* ── Sidebar category items ── */
      .pl-cat-item {
        display:flex;align-items:center;gap:6px;padding:6px 10px;
        cursor:pointer;font-size:0.75rem;color:var(--text);
        border-left:3px solid transparent;transition:background .1s,border-color .1s;
        user-select:none;
      }
      .pl-cat-item:hover { background:var(--surface2) }
      .pl-cat-item.active {
        background:var(--accent)14;border-left-color:var(--accent);
        font-weight:700;color:var(--accent);
      }
      .pl-cat-count {
        margin-left:auto;font-size:0.6rem;color:var(--muted);
        background:var(--surface2);border-radius:9px;padding:1px 5px;
      }
      .pl-cat-divider {
        height:1px;background:var(--border)44;margin:5px 8px;
      }
      .pl-cat-section-label {
        font-size:0.58rem;text-transform:uppercase;letter-spacing:.07em;
        color:var(--muted);padding:4px 10px 2px;
      }

      /* ── Use-case chips ── */
      .pl-uc-chip {
        padding:2px 10px;border-radius:12px;border:1px solid var(--border);
        background:transparent;cursor:pointer;font-family:var(--font);
        font-size:0.68rem;color:var(--text);transition:background .12s,color .12s;
        white-space:nowrap;
      }
      .pl-uc-chip:hover { background:var(--surface2) }
      .pl-uc-chip.active {
        background:var(--accent)22;color:var(--accent);
        border-color:var(--accent)66;font-weight:600;
      }

      /* ── Tag tree rows ── */
      .pl-tree-row {
        display:flex;align-items:center;padding:5px 4px;border-radius:5px;
        cursor:pointer;transition:background .1s;font-size:0.78rem;
        border-bottom:1px solid var(--border)22;user-select:none;
      }
      .pl-tree-row:hover { background:var(--surface2) }
      .pl-tree-row:hover .pl-row-actions { opacity:1 }
      .pl-tree-row.selected { background:var(--accent)14 }
      .pl-tree-row.drag-over { background:var(--accent)30;outline:2px dashed var(--accent) }
      .pl-tree-row.dragging  { opacity:.35 }

      .pl-drag-handle {
        cursor:grab;color:var(--muted);font-size:0.75rem;padding:0 4px;
        flex-shrink:0;opacity:.4;
      }
      .pl-drag-handle:active { cursor:grabbing }
      .pl-tree-indent { display:inline-block;flex-shrink:0 }
      .pl-tree-toggle {
        width:14px;flex-shrink:0;text-align:center;cursor:pointer;
        font-size:0.65rem;color:var(--muted);
      }
      .pl-tag-name {
        flex:1;font-weight:600;color:var(--text);
        overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;
      }
      .pl-tag-desc {
        color:var(--muted);font-size:0.68rem;margin-left:5px;
        overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
        max-width:140px;flex-shrink:0;
      }
      .pl-status-badge {
        font-size:0.58rem;padding:1px 5px;border-radius:9px;font-weight:600;
        text-transform:uppercase;white-space:nowrap;flex-shrink:0;margin-left:5px;
      }
      .st-open     { background:#dbeafe44;color:#3b82f6 }
      .st-active   { background:#dcfce7;color:#16a34a }
      .st-done     { background:#f3f4f666;color:#9ca3af }
      .st-archived { background:#f3f4f633;color:#d1d5db }

      .pl-file-dot {
        width:5px;height:5px;border-radius:50%;background:var(--accent);
        flex-shrink:0;margin-left:5px;cursor:default;
      }
      .pl-row-actions {
        display:flex;gap:2px;flex-shrink:0;margin-left:4px;opacity:0;transition:opacity .1s;
      }
      .pl-row-btn {
        border:none;background:none;cursor:pointer;padding:1px 4px;border-radius:3px;
        font-size:0.68rem;color:var(--muted);line-height:1;
        transition:background .1s,color .1s;
      }
      .pl-row-btn:hover { background:var(--surface2);color:var(--accent) }

      /* ── Drawer ── */
      .pl-drawer-field { margin-bottom:0.8rem }
      .pl-drawer-label {
        font-size:0.6rem;font-weight:700;color:var(--muted);
        text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;display:block;
      }
      .pl-drawer-input {
        width:100%;box-sizing:border-box;padding:5px 8px;
        border:1px solid var(--border);border-radius:4px;
        background:var(--surface2);color:var(--text);font-family:var(--font);
        font-size:0.78rem;outline:none;transition:border-color .15s;
      }
      .pl-drawer-input:focus { border-color:var(--accent) }
      textarea.pl-drawer-input { resize:vertical;min-height:52px;line-height:1.45 }
      select.pl-drawer-input   { cursor:pointer }

      /* ── Dependency tags ── */
      .pl-dep-chip {
        display:inline-flex;align-items:center;gap:4px;padding:2px 7px;
        border-radius:10px;background:var(--surface2);border:1px solid var(--border);
        font-size:0.68rem;color:var(--text);margin:2px;
      }
      .pl-dep-remove {
        border:none;background:none;cursor:pointer;color:var(--muted);
        font-size:0.8rem;padding:0;line-height:1;
      }
      .pl-dep-remove:hover { color:var(--red,#dc2626) }

      /* ── Misc ── */
      .pl-add-btn {
        display:flex;align-items:center;gap:3px;padding:4px 8px;
        border:1px dashed var(--border);border-radius:4px;
        background:transparent;color:var(--muted);font-family:var(--font);
        font-size:0.7rem;cursor:pointer;transition:color .12s,border-color .12s;
      }
      .pl-add-btn:hover { color:var(--accent);border-color:var(--accent) }

      .pl-section-sep {
        font-size:0.58rem;text-transform:uppercase;letter-spacing:.07em;
        color:var(--muted);padding:6px 4px 2px;
      }
    </style>
  `;

  // Wire globals
  window._plSelectCat = _selectCat;
  window._plSelectUC  = _selectUC;
  window._plCloseDrawer = () => _closeDrawer(true);
  window._plAddChild   = _promptAddChild;
  window._plDropRoot   = _dropRoot;
  document.getElementById('pl-new-cat-btn')?.addEventListener('click', _promptNewCat);
  document.getElementById('pl-new-tag-btn')?.addEventListener('click', () => _promptNewTag(null));

  _loadAll();
}

export function destroyEntities() {
  _drawer   = null;
  _dragging = null;
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────

async function _loadAll() {
  try {
    const data = await api.entities.listCategories(_project);
    _allCats = data.categories || [];
    _renderSidebar();
    _loadUseCases();
  } catch (e) {
    document.getElementById('pl-cat-list').innerHTML =
      `<div style="font-size:0.7rem;color:var(--muted);padding:0.5rem 0.8rem">Error: ${_esc(e.message)}</div>`;
  }
}

// ── Use-case bar ───────────────────────────────────────────────────────────────

async function _loadUseCases() {
  const bar = document.getElementById('pl-uc-chips');
  if (!bar) return;
  const ucCat = _allCats.find(c => c.name?.toLowerCase() === UC_CAT_NAME);
  if (!ucCat) {
    bar.innerHTML = `<span style="font-size:0.68rem;color:var(--muted)">No use cases yet</span>`;
    return;
  }
  try {
    const data = await api.entities.listValues(_project, ucCat.id);
    const ucs  = (data.values || []).filter(t => t.status !== 'archived');
    bar.innerHTML =
      `<button class="pl-uc-chip ${_ucTagId === null ? 'active' : ''}"
               onclick="window._plSelectUC(null,null)">All</button>` +
      ucs.map(u =>
        `<button class="pl-uc-chip ${_ucTagId === u.id ? 'active' : ''}"
                 onclick="window._plSelectUC(${_esc(JSON.stringify(u.id))},${_esc(JSON.stringify(u.name))})">
           ${_esc(u.name)}
         </button>`
      ).join('');
  } catch {
    bar.innerHTML = `<span style="font-size:0.68rem;color:var(--muted)">—</span>`;
  }
}

function _selectUC(tagId, tagName) {
  _ucTagId = tagId;
  _ucSlug  = tagName;
  document.querySelectorAll('.pl-uc-chip').forEach(c => {
    c.classList.toggle('active', tagId === null
      ? c.textContent.trim() === 'All'
      : c.textContent.trim() === tagName);
  });
  if (_catId) _loadTags();
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

function _renderSidebar() {
  const list = document.getElementById('pl-cat-list');
  if (!list) return;

  const primary   = _allCats.filter(c => PRIMARY_CATS.includes(c.name?.toLowerCase()));
  const secondary = _allCats.filter(c =>
    !PRIMARY_CATS.includes(c.name?.toLowerCase()) &&
    c.name?.toLowerCase() !== UC_CAT_NAME
  );

  let html = '';
  primary.forEach(c => { html += _catItemHtml(c); });
  if (secondary.length) {
    html += `<div class="pl-cat-divider"></div>
             <div class="pl-cat-section-label">More</div>`;
    secondary.forEach(c => { html += _catItemHtml(c); });
  }
  list.innerHTML = html;

  // Auto-select first primary cat
  if (!_catId) {
    const first = primary[0] || _allCats[0];
    if (first) _selectCat(first.id, first.name, first.color || '#4a90e2');
  }
}

function _catItemHtml(c) {
  const active = _catId === c.id;
  return `<div class="pl-cat-item ${active ? 'active' : ''}"
               data-catid="${c.id}"
               onclick="window._plSelectCat(${c.id}, ${_esc(JSON.stringify(c.name))}, ${_esc(JSON.stringify(c.color || '#4a90e2'))})">
    <span style="width:8px;height:8px;border-radius:50%;background:${_esc(c.color||'#4a90e2')};
                 flex-shrink:0;display:inline-block"></span>
    <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">
      ${_esc(c.name)}
    </span>
    <span class="pl-cat-count">${c.value_count ?? 0}</span>
  </div>`;
}

function _selectCat(catId, catName, catColor) {
  _catId   = catId;
  _catName = catName;
  _closeDrawer(false);

  document.querySelectorAll('.pl-cat-item').forEach(el => {
    el.classList.toggle('active', Number(el.dataset.catid) === catId || el.dataset.catid === String(catId));
  });

  const title = document.getElementById('pl-tree-title');
  if (title) title.textContent = catName;
  const btn = document.getElementById('pl-new-tag-btn');
  if (btn) btn.style.display = '';

  _loadTags();
}

// ── Tag tree ──────────────────────────────────────────────────────────────────

async function _loadTags() {
  const pane = document.getElementById('pl-tag-pane');
  if (!pane || !_catId) return;
  pane.innerHTML = `<div style="color:var(--muted);font-size:0.72rem;padding:2rem;text-align:center">Loading…</div>`;
  try {
    const data = await api.entities.listValues(_project, _catId);
    _tags = data.values || [];
    _renderTree();
  } catch (e) {
    pane.innerHTML = `<div style="color:var(--muted);font-size:0.72rem;padding:2rem">Error: ${_esc(e.message)}</div>`;
  }
}

function _renderTree() {
  const pane = document.getElementById('pl-tag-pane');
  if (!pane) return;

  // Filter by use case if one is selected
  let visible = _tags;
  if (_ucSlug) {
    const slug = _ucSlug.toLowerCase().replace(/\s+/g, '-');
    visible = _tags.filter(t => t.file_ref && t.file_ref.toLowerCase().includes(slug));
  }

  if (!visible.length) {
    pane.innerHTML = `
      <div style="color:var(--muted);font-size:0.78rem;padding:1.5rem 0.4rem">
        No tags in <strong>${_esc(_catName)}</strong>${_ucSlug ? ` for use case <em>${_esc(_ucSlug)}</em>` : ''}.
      </div>`;
    return;
  }

  const tree = _buildTree(visible);
  pane.innerHTML = `
    <div id="pl-tree-root"
         ondragover="event.preventDefault()"
         ondrop="window._plDropRoot(event)">
      ${_treeHtml(tree, 0)}
    </div>`;

  visible.forEach(t => _wireRow(t));
}

function _buildTree(flat) {
  const map   = Object.fromEntries(flat.map(t => [t.id, { ...t, _children: [] }]));
  const roots = [];
  flat.forEach(t => {
    if (t.parent_id && map[t.parent_id]) map[t.parent_id]._children.push(map[t.id]);
    else                                  roots.push(map[t.id]);
  });
  return roots;
}

function _treeHtml(nodes, depth) {
  return nodes.map(t => {
    const indent   = depth * 20;
    const st       = t.status || 'open';
    const stCls    = { open:'st-open', active:'st-active', done:'st-done', archived:'st-archived' }[st] || 'st-open';
    const hasKids  = t._children?.length > 0;
    const isCol    = _collapsed.has(t.id);
    const toggle   = hasKids
      ? `<span class="pl-tree-toggle" data-toggle="${t.id}">${isCol ? '▸' : '▾'}</span>`
      : `<span class="pl-tree-toggle" style="opacity:0">▸</span>`;
    const fileDot  = t.file_ref
      ? `<span class="pl-file-dot" title="${_esc(t.file_ref)}"></span>` : '';
    const isSelected = _drawer?.id === t.id;

    const childrenHtml = hasKids
      ? `<div id="plc-${t.id}" style="${isCol ? 'display:none' : ''}">${_treeHtml(t._children, depth + 1)}</div>`
      : '';

    return `
      <div id="plrow-${t.id}" class="pl-tree-row ${isSelected ? 'selected' : ''}"
           draggable="true" data-id="${t.id}">
        <span class="pl-drag-handle" title="Drag to reparent">⠿</span>
        <span class="pl-tree-indent" style="width:${indent}px"></span>
        ${toggle}
        <span class="pl-tag-name">${_esc(t.name)}</span>
        <span class="pl-status-badge ${stCls}">${st}</span>
        ${t.description ? `<span class="pl-tag-desc" title="${_esc(t.description)}">${_esc(t.description)}</span>` : ''}
        ${fileDot}
        <span class="pl-row-actions">
          <button class="pl-row-btn" title="Add child under this tag"
                  onclick="event.stopPropagation();window._plAddChild(${_esc(JSON.stringify(t.id))},${_esc(JSON.stringify(t.name))})">+ child</button>
        </span>
      </div>
      ${childrenHtml}`;
  }).join('');
}

function _wireRow(t) {
  const el = document.getElementById(`plrow-${t.id}`);
  if (!el) return;

  el.addEventListener('click', e => {
    const toggle = e.target.closest('[data-toggle]');
    if (toggle) {
      const kids = document.getElementById(`plc-${t.id}`);
      if (kids) {
        const closing = kids.style.display !== 'none';
        kids.style.display = closing ? 'none' : '';
        if (closing) _collapsed.add(t.id); else _collapsed.delete(t.id);
        toggle.textContent = closing ? '▸' : '▾';
      }
      return;
    }
    if (!e.target.classList.contains('pl-row-btn')) _openDrawer(t);
  });

  el.addEventListener('dragstart', e => {
    _dragging = t.id;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', t.id);
    el.classList.add('dragging');
  });
  el.addEventListener('dragend', () => {
    el.classList.remove('dragging');
    document.querySelectorAll('.pl-tree-row.drag-over').forEach(r => r.classList.remove('drag-over'));
  });
  el.addEventListener('dragover', e => {
    if (_dragging === t.id) return;
    e.preventDefault();
    e.stopPropagation();
    document.querySelectorAll('.pl-tree-row.drag-over').forEach(r => r.classList.remove('drag-over'));
    el.classList.add('drag-over');
  });
  el.addEventListener('dragleave', () => el.classList.remove('drag-over'));
  el.addEventListener('drop', async e => {
    e.preventDefault();
    e.stopPropagation();
    el.classList.remove('drag-over');
    if (!_dragging || _dragging === t.id) return;
    if (_isDescendant(_dragging, t.id)) {
      toast('Cannot move a tag into its own child', 'error');
      return;
    }
    try {
      await api.entities.patchValue(_dragging, { parent_id: t.id });
      _dragging = null;
      await _loadTags();
    } catch (err) { toast('Reparent failed: ' + err.message, 'error'); }
  });
}

async function _dropRoot(e) {
  e.preventDefault();
  if (!_dragging) return;
  try {
    await api.entities.patchValue(_dragging, { parent_id: null });
    _dragging = null;
    await _loadTags();
  } catch (err) { toast('Move failed: ' + err.message, 'error'); }
}

function _isDescendant(ancestorId, targetId) {
  const map = Object.fromEntries(_tags.map(t => [t.id, t]));
  let cur = map[targetId];
  const seen = new Set();
  while (cur?.parent_id) {
    if (seen.has(cur.id)) break;
    seen.add(cur.id);
    if (cur.parent_id === ancestorId) return true;
    cur = map[cur.parent_id];
  }
  return false;
}

// ── Drawer ────────────────────────────────────────────────────────────────────

async function _openDrawer(tag) {
  _drawer = tag;
  document.querySelectorAll('.pl-tree-row').forEach(r => r.classList.remove('selected'));
  document.getElementById(`plrow-${tag.id}`)?.classList.add('selected');

  const inner = document.getElementById('pl-drawer-inner');
  if (!inner) return;

  _showDrawerSkeleton(inner, tag);
  _openDrawerSlide();

  // Load dependencies in parallel
  let deps = { depends_on: [], required_by: [] };
  try { deps = await api.entities.getValueLinks(tag.id, _project); } catch { /* ignore */ }
  _renderDrawerContent(inner, tag, deps);
}

function _openDrawerSlide() {
  const drawer = document.getElementById('pl-drawer');
  if (drawer) { drawer.style.width = '290px'; drawer.style.borderLeftWidth = '1px'; }
}

function _showDrawerSkeleton(inner, tag) {
  inner.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.8rem">
      <span style="font-size:0.65rem;font-weight:700;color:var(--muted);text-transform:uppercase">${_esc(_catName)}</span>
      <button onclick="window._plCloseDrawer()"
              style="border:none;background:none;cursor:pointer;font-size:1.1rem;color:var(--muted);padding:0;line-height:1">×</button>
    </div>
    <div style="font-size:0.85rem;font-weight:700;color:var(--text);margin-bottom:1rem">${_esc(tag.name)}</div>
    <div style="color:var(--muted);font-size:0.72rem">Loading…</div>`;
}

function _renderDrawerContent(inner, tag, deps) {
  const st = tag.status || 'open';

  // Parent selector — exclude self and descendants
  const parentOpts = [{ id: '', name: '— none (root level) —' }]
    .concat(_tags.filter(t => t.id !== tag.id && !_isDescendant(tag.id, t.id)))
    .map(t => `<option value="${_esc(t.id)}" ${(tag.parent_id || '') === t.id ? 'selected' : ''}>${_esc(t.name || '—')}</option>`)
    .join('');

  // Available tags for dependency picker (all categories, same project)
  const depsHtml = _depsHtml(deps.depends_on, tag.id);
  const reqByHtml = deps.required_by.length
    ? deps.required_by.map(d =>
        `<span class="pl-dep-chip" style="opacity:.75">${_esc(d.category)} / ${_esc(d.name)}</span>`
      ).join('')
    : `<span style="font-size:0.7rem;color:var(--muted)">None</span>`;

  const fileRef = tag.file_ref || '';

  inner.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.8rem">
      <span style="font-size:0.65rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.05em">${_esc(_catName)}</span>
      <button onclick="window._plCloseDrawer()"
              style="border:none;background:none;cursor:pointer;font-size:1.1rem;color:var(--muted);padding:0;line-height:1">×</button>
    </div>

    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Name</label>
      <input id="pld-name" class="pl-drawer-input" value="${_esc(tag.name)}" />
    </div>

    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Status</label>
      <select id="pld-status" class="pl-drawer-input">
        ${['open','active','done','archived'].map(s =>
          `<option value="${s}" ${s === st ? 'selected' : ''}>${s}</option>`
        ).join('')}
      </select>
    </div>

    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Parent (hierarchy)</label>
      <select id="pld-parent" class="pl-drawer-input">${parentOpts}</select>
    </div>

    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Description</label>
      <textarea id="pld-desc" class="pl-drawer-input">${_esc(tag.description || '')}</textarea>
    </div>

    <!-- Dependencies -->
    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Depends on</label>
      <div id="pld-dep-chips" style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:5px">${depsHtml}</div>
      <div style="display:flex;gap:4px;align-items:center">
        <select id="pld-dep-pick" class="pl-drawer-input" style="flex:1">
          <option value="">— add dependency —</option>
        </select>
        <button id="pld-dep-add" class="pl-add-btn" style="white-space:nowrap">+ Add</button>
      </div>
    </div>

    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Required by</label>
      <div style="display:flex;flex-wrap:wrap;gap:3px">${reqByHtml}</div>
    </div>

    ${fileRef ? `
    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Use Case File</label>
      <div style="display:flex;align-items:center;gap:6px">
        <span style="font-size:0.7rem;color:var(--accent);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(fileRef)}</span>
        <button id="pld-view-uc" style="font-size:0.65rem;background:none;border:none;
                cursor:pointer;color:var(--accent);text-decoration:underline;padding:0;flex-shrink:0">Preview</button>
      </div>
    </div>` : ''}

    <div style="font-size:0.62rem;color:var(--muted);margin-bottom:0.8rem">
      Created: ${tag.created_at ? _fmtDate(tag.created_at) : '—'}
    </div>

    <div style="display:flex;gap:0.5rem">
      <button id="pld-save" class="btn btn-primary btn-sm" style="flex:1">Save</button>
      <button id="pld-delete" class="btn btn-ghost btn-sm" style="color:var(--red,#dc2626)">Delete</button>
    </div>

    <div id="pld-uc-preview"
         style="display:none;margin-top:1rem;padding:0.65rem;
                background:var(--surface2);border-radius:4px;border:1px solid var(--border)">
      <div style="font-size:0.6rem;font-weight:700;color:var(--muted);margin-bottom:0.4rem">USE CASE FILE</div>
      <div id="pld-uc-content"
           style="font-size:0.68rem;color:var(--text2);line-height:1.5;
                  white-space:pre-wrap;max-height:240px;overflow-y:auto"></div>
    </div>
  `;

  // Wire events
  document.getElementById('pld-save')?.addEventListener('click',   () => _saveDrawer(tag.id));
  document.getElementById('pld-delete')?.addEventListener('click', () => _deleteTag(tag));
  document.getElementById('pld-view-uc')?.addEventListener('click', () => _previewUseCase(fileRef));
  document.getElementById('pld-dep-add')?.addEventListener('click', () => _addDep(tag.id));

  // Load all tags for dependency picker
  _loadDepPicker(tag.id, deps.depends_on);
}

function _depsHtml(deps, tagId) {
  if (!deps.length) return `<span style="font-size:0.7rem;color:var(--muted)">None</span>`;
  return deps.map(d =>
    `<span class="pl-dep-chip">
       ${_esc(d.category)} / ${_esc(d.name)}
       <button class="pl-dep-remove" title="Remove dependency"
               onclick="window._plRemoveDep(${_esc(JSON.stringify(tagId))},${_esc(JSON.stringify(d.id))})">×</button>
     </span>`
  ).join('');
}

async function _loadDepPicker(tagId, existingDeps) {
  const sel = document.getElementById('pld-dep-pick');
  if (!sel) return;
  try {
    // Load all values across all categories for this project
    const data = await api.entities.allValues(_project);
    // allValues returns {by_category: {catId: [{...}]}}
    const byCat = data.by_category || {};
    sel.innerHTML = `<option value="">— add dependency —</option>` +
      Object.entries(byCat)
        .filter(([, tags]) => tags.length)
        .map(([, tags]) => {
          const catName = tags[0].category_name || 'other';
          const filtered = tags.filter(t => t.id !== tagId && !existingDeps.some(d => d.id === t.id));
          if (!filtered.length) return '';
          return `<optgroup label="${_esc(catName)}">` +
            filtered.map(t => `<option value="${_esc(t.id)}">${_esc(t.name)}</option>`).join('') +
            `</optgroup>`;
        }).join('');
  } catch { /* leave as is */ }
}

async function _addDep(tagId) {
  const sel = document.getElementById('pld-dep-pick');
  const depId = sel?.value;
  if (!depId) { toast('Select a tag to depend on', 'error'); return; }
  try {
    await api.entities.createValueLink(tagId, { depends_on: depId });
    toast('Dependency added', 'success');
    // Reload drawer
    const tag = _tags.find(t => t.id === tagId);
    if (tag) await _openDrawer(tag);
  } catch (e) { toast('Failed: ' + e.message, 'error'); }
}

window._plRemoveDep = async (tagId, depId) => {
  try {
    await api.entities.deleteValueLink(tagId, depId);
    toast('Dependency removed', 'success');
    const tag = _tags.find(t => t.id === tagId);
    if (tag) await _openDrawer(tag);
  } catch (e) { toast('Failed: ' + e.message, 'error'); }
};

function _closeDrawer(reload = false) {
  _drawer = null;
  const drawer = document.getElementById('pl-drawer');
  if (drawer) { drawer.style.width = '0'; drawer.style.borderLeftWidth = '0'; }
  document.querySelectorAll('.pl-tree-row').forEach(r => r.classList.remove('selected'));
  if (reload) _loadTags();
}

async function _saveDrawer(tagId) {
  const name     = document.getElementById('pld-name')?.value?.trim();
  const status   = document.getElementById('pld-status')?.value;
  const desc     = document.getElementById('pld-desc')?.value?.trim();
  const parentId = document.getElementById('pld-parent')?.value || null;
  if (!name) { toast('Name is required', 'error'); return; }

  const btn = document.getElementById('pld-save');
  if (btn) btn.disabled = true;
  try {
    await api.entities.patchValue(tagId, {
      name, status, description: desc, parent_id: parentId || null,
    });
    toast('Saved', 'success');
    const idx = _tags.findIndex(t => t.id === tagId);
    if (idx >= 0) {
      _tags[idx] = { ..._tags[idx], name, status, description: desc, parent_id: parentId || null };
      _drawer = _tags[idx];
    }
    _renderTree();
    document.getElementById(`plrow-${tagId}`)?.classList.add('selected');
    _loadAll();
  } catch (e) {
    toast(`Save failed: ${e.message}`, 'error');
  } finally {
    if (btn) btn.disabled = false;
  }
}

async function _deleteTag(tag) {
  if (!confirm(`Delete "${tag.name}"? This cannot be undone.`)) return;
  try {
    await api.entities.deleteValue(tag.id);
    toast(`"${tag.name}" deleted`, 'success');
    _closeDrawer(false);
    _tags = _tags.filter(t => t.id !== tag.id);
    _renderTree();
    _loadAll();
  } catch (e) { toast(`Delete failed: ${e.message}`, 'error'); }
}

// ── Create dialogs ────────────────────────────────────────────────────────────

async function _promptNewTag(parentId) {
  const parentName = parentId ? _tags.find(t => t.id === parentId)?.name : null;
  const name = prompt(parentName ? `New tag under "${parentName}":` : 'New tag name:');
  if (!name?.trim()) return;
  try {
    await api.entities.createValue({
      name: name.trim(), category_id: _catId, project: _project,
      status: 'open', parent_id: parentId || undefined,
    });
    toast(`"${name.trim()}" created`, 'success');
    await _loadTags();
    _loadAll();
  } catch (e) { toast(`Failed: ${e.message}`, 'error'); }
}

async function _promptAddChild(parentId, parentName) {
  const name = prompt(`New child tag under "${parentName}":`);
  if (!name?.trim()) return;
  try {
    await api.entities.createValue({
      name: name.trim(), category_id: _catId, project: _project,
      status: 'open', parent_id: parentId,
    });
    toast(`"${name.trim()}" created`, 'success');
    _collapsed.delete(parentId); // expand parent
    await _loadTags();
    _loadAll();
  } catch (e) { toast(`Failed: ${e.message}`, 'error'); }
}

async function _promptNewCat() {
  const name = prompt('New category name:');
  if (!name?.trim()) return;
  try {
    await api.entities.createCategory({ name: name.trim(), color: '#4a90e2', icon: '⬡' });
    toast(`Category "${name.trim()}" created`, 'success');
    await _loadAll();
  } catch (e) { toast(`Failed: ${e.message}`, 'error'); }
}

// ── Use case preview ──────────────────────────────────────────────────────────

async function _previewUseCase(fileRef) {
  const panel   = document.getElementById('pld-uc-preview');
  const content = document.getElementById('pld-uc-content');
  if (!panel || !content) return;
  panel.style.display = 'block';
  content.textContent = 'Loading…';
  try {
    const data = await api.backlog.getUseCaseSection(_project, fileRef);
    content.textContent = (data.content || '').slice(0, 2000);
  } catch (e) {
    content.textContent = `Could not load: ${e.message}`;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _esc(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function _fmtDate(iso) {
  try {
    return new Date(iso).toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'2-digit' });
  } catch { return iso; }
}
