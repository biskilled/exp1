/**
 * entities.js — Planner: tag hierarchy manager.
 *
 * Layout (top → bottom):
 *   1. Toolbar
 *   2. Use-case filter bar  — "All" + one chip per use-case tag
 *   3. Category bar         — task | feature | bug (primary tabs)
 *                             + other categories in a secondary group (filter only)
 *   4. Tag tree             — indented rows, drag-handle for parent/child reparenting
 *   5. Slide-in drawer      — edit name / status / description for the selected tag
 */

import { state } from '../stores/state.js';
import { api }   from '../utils/api.js';
import { toast } from '../utils/toast.js';

// ── Module state ───────────────────────────────────────────────────────────────

let _project   = '';
let _allCats   = [];        // all loaded categories
let _catId     = null;      // active category filter
let _ucTagId   = null;      // active use-case filter (null = All)
let _ucSlug    = null;      // slug of active use case (for file_ref filtering)
let _tags      = [];        // flat list from API for current category
let _drawer    = null;      // currently-open tag object
let _dragging  = null;      // id of tag being dragged

// Categories treated as "primary tabs" (always shown first, bold)
const PRIMARY_CATS = new Set(['task', 'feature', 'bug']);
// Category that acts as the use-case dimension (not shown in category tabs)
const UC_CAT_NAME  = 'use_case';

// ── Public ────────────────────────────────────────────────────────────────────

export function renderEntities(container) {
  _project  = state.currentProject?.name || '';
  _catId    = null;
  _ucTagId  = null;
  _ucSlug   = null;
  _drawer   = null;
  _dragging = null;

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- Toolbar -->
      <div style="padding:0.6rem 1.1rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.6rem;flex-shrink:0">
        <span style="font-size:0.85rem;font-weight:700;color:var(--text)">Planner</span>
        ${_project ? `<span style="font-size:0.65rem;color:var(--accent)">${_esc(_project)}</span>` : ''}
        <span style="flex:1"></span>
        <span id="pl-status" style="font-size:0.7rem;color:var(--muted)"></span>
      </div>

      <!-- Use-case filter bar -->
      <div id="pl-uc-bar"
           style="padding:5px 1.1rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:5px;flex-wrap:wrap;flex-shrink:0;
                  background:var(--surface)">
        <span style="font-size:0.6rem;color:var(--muted);text-transform:uppercase;
                     letter-spacing:.05em;margin-right:3px;flex-shrink:0">Use case</span>
        <div id="pl-uc-chips" style="display:flex;flex-wrap:wrap;gap:4px;align-items:center">
          <span style="font-size:0.7rem;color:var(--muted)">Loading…</span>
        </div>
      </div>

      <!-- Category bar -->
      <div id="pl-cat-bar"
           style="padding:5px 1.1rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:4px;flex-wrap:wrap;flex-shrink:0">
        <div id="pl-primary-tabs" style="display:flex;gap:4px;align-items:center"></div>
        <div id="pl-secondary-tabs"
             style="display:flex;gap:4px;align-items:center;margin-left:10px;
                    padding-left:10px;border-left:1px solid var(--border)44"></div>
        <span style="flex:1"></span>
        <button id="pl-new-cat-btn" class="pl-add-btn" style="font-size:0.65rem;padding:3px 8px">
          + Category
        </button>
      </div>

      <!-- Main area: tag tree + drawer -->
      <div style="flex:1;display:flex;min-height:0;overflow:hidden">

        <!-- Drop zone for root-level (remove parent) — invisible strip -->
        <div id="pl-root-drop"
             style="display:none;position:absolute;bottom:0;left:0;right:280px;
                    height:40px;z-index:10;background:var(--accent)22;
                    font-size:0.7rem;color:var(--accent);display:flex;
                    align-items:center;justify-content:center;border-top:2px dashed var(--accent)">
          Drop here to make root-level
        </div>

        <!-- Tag tree -->
        <div id="pl-tag-pane"
             style="flex:1;overflow-y:auto;padding:0.6rem 0.9rem 4rem;min-width:0">
          <div style="color:var(--muted);font-size:0.75rem;padding:3rem;text-align:center">
            ← Select a category
          </div>
        </div>

        <!-- Slide-in detail drawer -->
        <div id="pl-drawer"
             style="width:0;overflow:hidden;border-left:0 solid var(--border);
                    flex-shrink:0;transition:width .2s ease,border-width .2s;
                    background:var(--surface)">
          <div id="pl-drawer-inner"
               style="width:275px;box-sizing:border-box;overflow-y:auto;
                      padding:1rem;flex-shrink:0"></div>
        </div>

      </div>
    </div>

    <style>
      /* ── Category / use-case chips ── */
      .pl-cat-tab {
        padding:3px 11px;border-radius:14px;border:1px solid var(--border);
        background:transparent;cursor:pointer;font-family:var(--font);
        font-size:0.72rem;color:var(--text);transition:background .12s,color .12s;
        white-space:nowrap;
      }
      .pl-cat-tab:hover { background:var(--surface2) }
      .pl-cat-tab.active {
        background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600;
      }
      .pl-cat-tab.primary { font-weight:600 }
      .pl-cat-tab.secondary { font-size:0.68rem;opacity:.85 }

      .pl-uc-chip {
        padding:2px 10px;border-radius:12px;border:1px solid var(--border);
        background:transparent;cursor:pointer;font-family:var(--font);
        font-size:0.68rem;color:var(--text);transition:background .12s,color .12s;
        white-space:nowrap;
      }
      .pl-uc-chip:hover { background:var(--surface2) }
      .pl-uc-chip.active {
        background:var(--accent)22;color:var(--accent);border-color:var(--accent)55;font-weight:600;
      }

      /* ── Tag tree ── */
      .pl-tree-row {
        display:flex;align-items:center;padding:5px 4px;border-radius:5px;
        cursor:pointer;transition:background .1s;font-size:0.78rem;
        border-bottom:1px solid var(--border)22;user-select:none;
      }
      .pl-tree-row:hover { background:var(--surface2) }
      .pl-tree-row.selected { background:var(--accent)14 }
      .pl-tree-row.drag-over { background:var(--accent)30;outline:2px dashed var(--accent) }
      .pl-tree-row.dragging  { opacity:.4 }

      .pl-drag-handle {
        cursor:grab;color:var(--muted);font-size:0.75rem;padding:0 5px;
        flex-shrink:0;opacity:.5;
      }
      .pl-drag-handle:active { cursor:grabbing }

      .pl-tree-indent { display:inline-block;flex-shrink:0 }
      .pl-tree-toggle {
        width:16px;flex-shrink:0;text-align:center;cursor:pointer;
        font-size:0.7rem;color:var(--muted);
      }
      .pl-tag-name {
        flex:1;font-weight:600;color:var(--text);
        overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;
      }
      .pl-tag-desc {
        color:var(--muted);font-size:0.7rem;margin-left:6px;
        overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
        max-width:160px;flex-shrink:0;
      }
      .pl-status-badge {
        font-size:0.6rem;padding:1px 6px;border-radius:9px;font-weight:600;
        text-transform:uppercase;white-space:nowrap;flex-shrink:0;margin-left:6px;
      }
      .st-open     { background:#dbeafe44;color:#3b82f6 }
      .st-active   { background:#dcfce7;color:#16a34a }
      .st-done     { background:#f3f4f666;color:#9ca3af }
      .st-archived { background:#f3f4f633;color:#d1d5db }

      .pl-file-dot {
        width:6px;height:6px;border-radius:50%;background:var(--accent);
        flex-shrink:0;margin-left:6px;title:attr(title);
      }

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

      /* ── Misc ── */
      .pl-add-btn {
        display:flex;align-items:center;gap:3px;padding:4px 9px;
        border:1px dashed var(--border);border-radius:4px;
        background:transparent;color:var(--muted);font-family:var(--font);
        font-size:0.72rem;cursor:pointer;transition:color .12s,border-color .12s;
      }
      .pl-add-btn:hover { color:var(--accent);border-color:var(--accent) }
    </style>
  `;

  // Wire global event handlers
  window._plSelectCat = _selectCat;
  window._plSelectUC  = _selectUC;
  window._plCloseDrawer = () => _closeDrawer(true);
  document.getElementById('pl-new-cat-btn')?.addEventListener('click', _promptNewCat);

  _loadAll();
}

export function destroyEntities() {
  _drawer   = null;
  _dragging = null;
}

// ── Bootstrap: load categories + use cases in parallel ────────────────────────

async function _loadAll() {
  try {
    const data = await api.entities.listCategories(_project);
    _allCats = data.categories || [];
    _renderCategoryBar();
    await _loadUseCases();
  } catch (e) {
    document.getElementById('pl-primary-tabs').innerHTML =
      `<span style="font-size:0.7rem;color:var(--muted)">Error: ${_esc(e.message)}</span>`;
  }
}

// ── Use-case bar ───────────────────────────────────────────────────────────────

async function _loadUseCases() {
  const bar = document.getElementById('pl-uc-chips');
  if (!bar) return;

  // Find the use_case category
  const ucCat = _allCats.find(c => c.name?.toLowerCase() === UC_CAT_NAME);
  if (!ucCat) {
    bar.innerHTML = `<span style="font-size:0.68rem;color:var(--muted)">No use cases yet</span>`;
    return;
  }

  try {
    const data = await api.entities.listValues(_project, ucCat.id);
    const ucs  = (data.values || []).filter(t => t.status !== 'archived');

    const all  = `<button class="pl-uc-chip ${_ucTagId === null ? 'active' : ''}"
                          onclick="window._plSelectUC(null, null)">All</button>`;
    const chips = ucs.map(u => `
      <button class="pl-uc-chip ${_ucTagId === u.id ? 'active' : ''}"
              onclick="window._plSelectUC(${_esc(JSON.stringify(u.id))}, ${_esc(JSON.stringify(u.name))})">
        ${_esc(u.name)}
      </button>`).join('');
    bar.innerHTML = all + chips;
  } catch (e) {
    bar.innerHTML = `<span style="font-size:0.68rem;color:var(--muted)">—</span>`;
  }
}

function _selectUC(tagId, tagName) {
  _ucTagId = tagId;
  _ucSlug  = tagName;
  // Re-render chips
  document.querySelectorAll('.pl-uc-chip').forEach(c => {
    const isAll = c.textContent.trim() === 'All';
    c.classList.toggle('active', tagId === null ? isAll : c.textContent.trim() === tagName);
  });
  if (_catId) _loadTags();
}

// ── Category bar ───────────────────────────────────────────────────────────────

function _renderCategoryBar() {
  const primary   = document.getElementById('pl-primary-tabs');
  const secondary = document.getElementById('pl-secondary-tabs');
  if (!primary || !secondary) return;

  const primCats = _allCats.filter(c =>
    PRIMARY_CATS.has(c.name?.toLowerCase()) &&
    c.name?.toLowerCase() !== UC_CAT_NAME
  );
  const secCats  = _allCats.filter(c =>
    !PRIMARY_CATS.has(c.name?.toLowerCase()) &&
    c.name?.toLowerCase() !== UC_CAT_NAME
  );

  primary.innerHTML = primCats.map(c => `
    <button class="pl-cat-tab primary ${_catId === c.id ? 'active' : ''}"
            onclick="window._plSelectCat(${c.id}, ${_esc(JSON.stringify(c.name))}, ${_esc(JSON.stringify(c.color||'#4a90e2'))})">
      ${_esc(c.name)}
      <span style="font-size:0.6rem;opacity:.7;margin-left:3px">${c.value_count ?? 0}</span>
    </button>`).join('');

  if (secCats.length) {
    secondary.innerHTML = secCats.map(c => `
      <button class="pl-cat-tab secondary ${_catId === c.id ? 'active' : ''}"
              onclick="window._plSelectCat(${c.id}, ${_esc(JSON.stringify(c.name))}, ${_esc(JSON.stringify(c.color||'#4a90e2'))})">
        ${_esc(c.name)}
        <span style="font-size:0.58rem;opacity:.7;margin-left:2px">${c.value_count ?? 0}</span>
      </button>`).join('');
    secondary.parentElement.style.display = 'flex';
  } else {
    secondary.parentElement.style.display = 'none';
  }

  // Auto-select first primary cat if none selected
  if (!_catId && primCats.length) {
    const first = primCats[0];
    _catId = first.id;
    _selectCat(first.id, first.name, first.color || '#4a90e2');
  }
}

function _selectCat(catId, catName, catColor) {
  _catId = catId;
  _closeDrawer(false);
  // Highlight tabs
  document.querySelectorAll('.pl-cat-tab').forEach(b => {
    b.classList.toggle('active', String(b.dataset?.catid || '') === String(catId) ||
      b.onclick?.toString().includes(`(${catId},`));
  });
  _loadTags();
}

// ── Tag tree loading & rendering ───────────────────────────────────────────────

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
    visible = _tags.filter(t =>
      t.file_ref && t.file_ref.toLowerCase().includes(_ucSlug.toLowerCase().replace(/\s+/g, '-'))
    );
  }

  if (!visible.length) {
    const cat = _allCats.find(c => c.id === _catId);
    pane.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:flex-start;gap:0.8rem;padding:1.5rem 0.2rem">
        <div style="color:var(--muted);font-size:0.78rem">
          No tags in <strong>${_esc(cat?.name || '')}</strong>${_ucSlug ? ` for use case <em>${_esc(_ucSlug)}</em>` : ''}.
        </div>
        <button class="pl-add-btn" id="pl-new-tag-btn">+ New tag</button>
      </div>`;
    document.getElementById('pl-new-tag-btn')?.addEventListener('click', _promptNewTag);
    return;
  }

  // Build tree
  const tree = _buildTree(visible);
  const html = _treeHtml(tree, 0);

  pane.innerHTML = `
    <div id="pl-tree-root"
         style="padding-bottom:0.5rem"
         ondragover="event.preventDefault()"
         ondrop="window._plDropRoot(event)">
      ${html}
    </div>
    <div style="padding:0.5rem 0.2rem">
      <button class="pl-add-btn" id="pl-new-tag-btn">+ New tag</button>
    </div>`;

  // Wire row events
  visible.forEach(t => _wireRow(t));
  document.getElementById('pl-new-tag-btn')?.addEventListener('click', _promptNewTag);

  window._plDropRoot = async (e) => {
    e.preventDefault();
    if (!_dragging) return;
    try {
      await api.entities.patchValue(_dragging, { parent_id: null });
      _dragging = null;
      await _loadTags();
    } catch (err) { toast('Reparent failed: ' + err.message, 'error'); }
  };
}

function _buildTree(flat) {
  const map  = Object.fromEntries(flat.map(t => [t.id, { ...t, _children: [] }]));
  const roots = [];
  flat.forEach(t => {
    if (t.parent_id && map[t.parent_id]) map[t.parent_id]._children.push(map[t.id]);
    else                                  roots.push(map[t.id]);
  });
  return roots;
}

function _treeHtml(nodes, depth) {
  return nodes.map(t => {
    const indent  = depth * 18;
    const st      = t.status || 'open';
    const stCls   = { open: 'st-open', active: 'st-active', done: 'st-done', archived: 'st-archived' }[st] || 'st-open';
    const hasKids = t._children?.length > 0;
    const toggle  = hasKids
      ? `<span class="pl-tree-toggle">▾</span>`
      : `<span class="pl-tree-toggle" style="opacity:0">▸</span>`;
    const fileDot = t.file_ref
      ? `<span class="pl-file-dot" title="${_esc(t.file_ref)}"></span>`
      : '';

    const childrenHtml = hasKids
      ? `<div id="plc-${t.id}">${_treeHtml(t._children, depth + 1)}</div>`
      : '';

    return `
      <div id="plrow-${t.id}" class="pl-tree-row ${_drawer?.id === t.id ? 'selected' : ''}"
           draggable="true" data-id="${t.id}" data-depth="${depth}">
        <span class="pl-drag-handle" title="Drag to reparent">⠿</span>
        <span class="pl-tree-indent" style="width:${indent}px"></span>
        ${toggle}
        <span class="pl-tag-name">${_esc(t.name)}</span>
        <span class="pl-status-badge ${stCls}">${st}</span>
        ${t.description ? `<span class="pl-tag-desc">${_esc(t.description)}</span>` : ''}
        ${fileDot}
      </div>
      ${childrenHtml}`;
  }).join('');
}

function _wireRow(t) {
  const el = document.getElementById(`plrow-${t.id}`);
  if (!el) return;

  // Click → open drawer
  el.addEventListener('click', (e) => {
    if (e.target.classList.contains('pl-tree-toggle')) {
      // Toggle children visibility
      const kids = document.getElementById(`plc-${t.id}`);
      if (kids) kids.style.display = kids.style.display === 'none' ? '' : 'none';
    } else {
      _openDrawer(t);
    }
  });

  // Drag & drop
  el.addEventListener('dragstart', (e) => {
    _dragging = t.id;
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', t.id);
    el.classList.add('dragging');
  });
  el.addEventListener('dragend', () => {
    el.classList.remove('dragging');
    document.querySelectorAll('.pl-tree-row.drag-over').forEach(r => r.classList.remove('drag-over'));
  });
  el.addEventListener('dragover', (e) => {
    if (_dragging === t.id) return;
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    document.querySelectorAll('.pl-tree-row.drag-over').forEach(r => r.classList.remove('drag-over'));
    el.classList.add('drag-over');
  });
  el.addEventListener('dragleave', () => el.classList.remove('drag-over'));
  el.addEventListener('drop', async (e) => {
    e.preventDefault();
    e.stopPropagation();
    el.classList.remove('drag-over');
    if (!_dragging || _dragging === t.id) return;
    // Prevent dropping onto own descendant
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

/** Returns true if candidateId is an ancestor of targetId in the current _tags list. */
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

// ── Drawer ─────────────────────────────────────────────────────────────────────

function _openDrawer(tag) {
  _drawer = tag;
  document.querySelectorAll('.pl-tree-row').forEach(r => r.classList.remove('selected'));
  document.getElementById(`plrow-${tag.id}`)?.classList.add('selected');

  const inner = document.getElementById('pl-drawer-inner');
  if (!inner) return;

  const st      = tag.status || 'open';
  const fileRef = tag.file_ref || '';
  const catName = _allCats.find(c => c.id === _catId)?.name || '';

  // Build parent selector options
  const parentOpts = [{ id: '', name: '— none (root) —' }]
    .concat(_tags.filter(t => t.id !== tag.id && !_isDescendant(tag.id, t.id)))
    .map(t => `<option value="${_esc(t.id)}" ${(tag.parent_id || '') === t.id ? 'selected' : ''}>${_esc(t.name || t.id)}</option>`)
    .join('');

  inner.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
      <span style="font-size:0.65rem;font-weight:700;color:var(--muted);text-transform:uppercase;
                   letter-spacing:.05em">${_esc(catName)}</span>
      <button onclick="window._plCloseDrawer()"
              style="border:none;background:none;cursor:pointer;font-size:1.1rem;
                     color:var(--muted);padding:0;line-height:1">×</button>
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
      <label class="pl-drawer-label">Parent</label>
      <select id="pld-parent" class="pl-drawer-input">${parentOpts}</select>
    </div>

    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Description</label>
      <textarea id="pld-desc" class="pl-drawer-input">${_esc(tag.description || '')}</textarea>
    </div>

    ${fileRef ? `
    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Use Case File</label>
      <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
        <span style="font-size:0.7rem;color:var(--accent)">📄 ${_esc(fileRef)}</span>
        <button id="pld-view-uc" style="font-size:0.68rem;background:none;border:none;
                cursor:pointer;color:var(--accent);text-decoration:underline;padding:0">Preview ↗</button>
      </div>
    </div>` : `
    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Use Case File</label>
      <span style="font-size:0.7rem;color:var(--muted)">Linked when backlog entry is processed.</span>
    </div>`}

    <div style="margin-bottom:0.8rem">
      <div style="font-size:0.62rem;color:var(--muted)">
        Created: ${tag.created_at ? _fmtDate(tag.created_at) : '—'}
      </div>
    </div>

    <div style="display:flex;gap:0.5rem">
      <button id="pld-save" class="btn btn-primary btn-sm" style="flex:1">Save</button>
      <button id="pld-delete" class="btn btn-ghost btn-sm"
              style="color:var(--red,#dc2626)">Delete</button>
    </div>

    <div id="pld-uc-preview"
         style="display:none;margin-top:1rem;padding:0.65rem;
                background:var(--surface2);border-radius:4px;border:1px solid var(--border)">
      <div style="font-size:0.6rem;font-weight:700;color:var(--muted);margin-bottom:0.4rem">
        USE CASE PREVIEW
      </div>
      <div id="pld-uc-content"
           style="font-size:0.7rem;color:var(--text2);line-height:1.5;
                  white-space:pre-wrap;max-height:260px;overflow-y:auto"></div>
    </div>
  `;

  document.getElementById('pld-save')?.addEventListener('click',   () => _saveDrawer(tag.id));
  document.getElementById('pld-delete')?.addEventListener('click', () => _deleteTag(tag));
  document.getElementById('pld-view-uc')?.addEventListener('click', () => _previewUseCase(fileRef));

  const drawer = document.getElementById('pl-drawer');
  if (drawer) { drawer.style.width = '275px'; drawer.style.borderLeftWidth = '1px'; }
}

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
      name, status, description: desc,
      parent_id: parentId || null,
    });
    toast('Saved', 'success');
    const idx = _tags.findIndex(t => t.id === tagId);
    if (idx >= 0) {
      _tags[idx] = { ..._tags[idx], name, status, description: desc, parent_id: parentId || null };
      _drawer = _tags[idx];
    }
    _renderTree();
    document.getElementById(`plrow-${tagId}`)?.classList.add('selected');
    _loadAll(); // refresh category counts
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
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
}

async function _promptNewTag() {
  const name = prompt('New tag name:');
  if (!name?.trim()) return;
  try {
    await api.entities.createValue({
      name:          name.trim(),
      category_id:   _catId,
      project:       _project,
      status:        'open',
    });
    toast(`"${name.trim()}" created`, 'success');
    await _loadTags();
    _loadAll();
  } catch (e) {
    toast(`Failed: ${e.message}`, 'error');
  }
}

async function _promptNewCat() {
  const name = prompt('New category name:');
  if (!name?.trim()) return;
  try {
    await api.entities.createCategory({ name: name.trim(), color: '#4a90e2', icon: '⬡' });
    toast(`Category "${name.trim()}" created`, 'success');
    await _loadAll();
  } catch (e) {
    toast(`Failed: ${e.message}`, 'error');
  }
}

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
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function _fmtDate(iso) {
  try {
    return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: '2-digit' });
  } catch { return iso; }
}
