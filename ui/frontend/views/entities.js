/**
 * entities.js — Planner: tag hierarchy manager.
 *
 * Simple two-pane layout: category list (left) + tag table (right).
 * Tags are created by the backlog pipeline and link to use case files
 * via the `file_ref` field. Users can rename, re-status, and delete tags.
 *
 * No work items, no requirements, no acceptance criteria — all managed
 * through the use case .md files in the Backlog tab.
 */

import { state }  from '../stores/state.js';
import { api }    from '../utils/api.js';
import { toast }  from '../utils/toast.js';

// ── Module state ──────────────────────────────────────────────────────────────

let _project  = '';
let _catId    = null;
let _catName  = '';
let _catColor = '#4a90e2';
let _tags     = [];        // currently shown tags
let _drawer   = null;      // open tag object or null

// ── Public ────────────────────────────────────────────────────────────────────

export function renderEntities(container) {
  _project  = state.currentProject?.name || '';
  _catId    = null;
  _catName  = '';
  _drawer   = null;

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- Toolbar -->
      <div style="padding:0.65rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.75rem;flex-shrink:0">
        <span style="font-size:0.88rem;font-weight:700;color:var(--text)">Planner</span>
        ${_project ? `<span style="font-size:0.65rem;color:var(--accent)">${_esc(_project)}</span>` : ''}
        <span style="flex:1"></span>
        <span id="pl-status" style="font-size:0.72rem;color:var(--muted)"></span>
      </div>

      <!-- Two-pane body -->
      <div style="display:flex;flex:1;min-height:0;overflow:hidden">

        <!-- Left: category list -->
        <div style="width:155px;flex-shrink:0;border-right:1px solid var(--border);
                    display:flex;flex-direction:column;overflow:hidden">
          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
                      padding:8px 10px 4px;letter-spacing:.05em;flex-shrink:0">Categories</div>
          <div id="pl-cat-list" style="flex:1;overflow-y:auto;padding:0 4px 4px"></div>
          <div style="padding:6px 8px;border-top:1px solid var(--border);flex-shrink:0">
            <input id="pl-new-cat" placeholder="+ New category…"
              style="width:100%;padding:3px 6px;border:1px dashed var(--border);
                     border-radius:4px;background:transparent;color:var(--text);
                     font-size:0.62rem;box-sizing:border-box;outline:none;font-family:var(--font)"
              onkeydown="if(event.key==='Enter')window._plAddCat(this)" />
          </div>
        </div>

        <!-- Right: tag table + slide-in drawer -->
        <div style="flex:1;display:flex;min-height:0;overflow:hidden">

          <!-- Tag table -->
          <div id="pl-tag-pane" style="flex:1;overflow-y:auto;padding:0.75rem 1rem;min-width:0">
            <div style="color:var(--muted);font-size:0.72rem;padding:3rem;text-align:center">
              ← Select a category
            </div>
          </div>

          <!-- Detail drawer (hidden until a tag is selected) -->
          <div id="pl-drawer"
               style="width:0;overflow:hidden;border-left:0 solid var(--border);
                      flex-shrink:0;transition:width .22s ease,border-width .22s;
                      background:var(--surface)">
            <div id="pl-drawer-inner"
                 style="width:270px;box-sizing:border-box;overflow-y:auto;padding:1rem;flex-shrink:0"></div>
          </div>

        </div>
      </div>
    </div>

    <style>
      .pl-cat-btn {
        display:flex;align-items:center;gap:5px;width:100%;padding:5px 8px;
        border:none;border-radius:4px;background:transparent;cursor:pointer;
        text-align:left;font-size:0.72rem;color:var(--text);font-family:var(--font);
        transition:background .12s;
      }
      .pl-cat-btn:hover { background:var(--surface2) }
      .pl-cat-btn.active { background:var(--accent)22;color:var(--accent);font-weight:600 }
      .pl-cat-count {
        margin-left:auto;font-size:0.6rem;color:var(--muted);
        background:var(--surface3);border-radius:8px;padding:0 5px;min-width:16px;text-align:center;
      }
      .pl-tag-table { width:100%;border-collapse:collapse;font-size:0.78rem }
      .pl-tag-table th {
        font-size:0.62rem;font-weight:700;color:var(--muted);text-transform:uppercase;
        letter-spacing:.05em;padding:0 8px 6px;text-align:left;
        border-bottom:1px solid var(--border);
      }
      .pl-tag-row { cursor:pointer;transition:background .1s }
      .pl-tag-row:hover td { background:var(--surface2) }
      .pl-tag-row.selected td { background:var(--accent)11 }
      .pl-tag-row td { padding:7px 8px;border-bottom:1px solid var(--border)44;vertical-align:middle }
      .pl-tag-name { font-weight:600;color:var(--text);max-width:180px;
        overflow:hidden;text-overflow:ellipsis;white-space:nowrap }
      .pl-tag-desc { color:var(--muted);font-size:0.72rem;max-width:220px;
        overflow:hidden;text-overflow:ellipsis;white-space:nowrap }
      .pl-status-badge {
        font-size:0.62rem;padding:1px 7px;border-radius:10px;font-weight:600;
        text-transform:uppercase;letter-spacing:.04em;white-space:nowrap;
      }
      .st-open     { background:#dbeafe;color:#1d4ed8 }
      .st-active   { background:#dcfce7;color:#16a34a }
      .st-done     { background:#f3f4f6;color:#6b7280 }
      .st-archived { background:#f3f4f6;color:#9ca3af }
      .pl-file-link {
        font-size:0.68rem;color:var(--accent);cursor:pointer;
        background:none;border:none;padding:0;font-family:var(--font);
        text-decoration:underline;
      }
      .pl-drawer-field { margin-bottom:0.85rem }
      .pl-drawer-label {
        font-size:0.62rem;font-weight:700;color:var(--muted);
        text-transform:uppercase;letter-spacing:.05em;margin-bottom:3px;display:block;
      }
      .pl-drawer-input {
        width:100%;box-sizing:border-box;padding:5px 8px;
        border:1px solid var(--border);border-radius:4px;
        background:var(--surface2);color:var(--text);font-family:var(--font);
        font-size:0.78rem;outline:none;transition:border-color .15s;
      }
      .pl-drawer-input:focus { border-color:var(--accent) }
      textarea.pl-drawer-input { resize:vertical;min-height:56px;line-height:1.45 }
      select.pl-drawer-input { cursor:pointer }
      .pl-drawer-meta {
        font-size:0.65rem;color:var(--muted);margin-bottom:0.25rem;
      }
      .pl-add-btn {
        display:flex;align-items:center;gap:4px;padding:5px 10px;
        border:1px dashed var(--border);border-radius:4px;
        background:transparent;color:var(--muted);font-family:var(--font);
        font-size:0.72rem;cursor:pointer;transition:color .12s,border-color .12s;
      }
      .pl-add-btn:hover { color:var(--accent);border-color:var(--accent) }
    </style>
  `;

  window._plAddCat   = _addCat;
  window._plSelectCat = _selectCat;

  _loadCats();
}

export function destroyEntities() {
  _drawer = null;
}

// ── Categories ────────────────────────────────────────────────────────────────

async function _loadCats() {
  const el = document.getElementById('pl-cat-list');
  if (!el) return;
  try {
    const data = await api.entities.listCategories(_project);
    const cats  = data.categories || [];
    el.innerHTML = cats.length
      ? cats.map(c => `
          <button class="pl-cat-btn ${c.id === _catId ? 'active' : ''}"
                  data-catid="${c.id}"
                  onclick="window._plSelectCat(${c.id}, ${_esc(JSON.stringify(c.name))}, ${_esc(JSON.stringify(c.color || '#4a90e2'))})">
            <span style="color:${_esc(c.color||'#888')}">${_esc(c.icon||'⬡')}</span>
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(c.name)}</span>
            <span class="pl-cat-count">${c.value_count ?? 0}</span>
          </button>`).join('')
      : `<div style="font-size:0.7rem;color:var(--muted);padding:8px 10px">No categories</div>`;
  } catch (e) {
    el.innerHTML = `<div style="font-size:0.7rem;color:var(--muted);padding:8px 10px">Error: ${e.message}</div>`;
  }
}

async function _addCat(inp) {
  const name = (inp.value || '').trim();
  if (!name) return;
  try {
    await api.entities.createCategory({ name, color: '#4a90e2', icon: '⬡' });
    inp.value = '';
    await _loadCats();
    toast(`Category "${name}" created`, 'success');
  } catch (e) {
    toast(`Failed: ${e.message}`, 'error');
  }
}

function _selectCat(catId, catName, catColor) {
  _catId    = catId;
  _catName  = catName;
  _catColor = catColor;
  _closeDrawer(false);
  // Highlight active category button
  document.querySelectorAll('.pl-cat-btn').forEach(b => {
    b.classList.toggle('active', String(b.dataset.catid) === String(catId));
  });
  _loadTags();
}

// ── Tags ──────────────────────────────────────────────────────────────────────

async function _loadTags() {
  const pane = document.getElementById('pl-tag-pane');
  if (!pane || !_catId) return;
  pane.innerHTML = `<div style="color:var(--muted);font-size:0.72rem;padding:2rem;text-align:center">Loading…</div>`;
  try {
    const data = await api.entities.listValues(_project, _catId);
    _tags = data.values || [];
    _renderTags();
  } catch (e) {
    pane.innerHTML = `<div style="color:var(--muted);font-size:0.72rem;padding:2rem">Error: ${e.message}</div>`;
  }
}

function _renderTags() {
  const pane = document.getElementById('pl-tag-pane');
  if (!pane) return;

  if (!_tags.length) {
    pane.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:flex-start;gap:1rem;padding:1.5rem 0">
        <div style="color:var(--muted);font-size:0.78rem">
          No tags in <strong>${_esc(_catName)}</strong> yet.
          Tags are created automatically when backlog entries are processed.
        </div>
        ${_newTagButton()}
      </div>`;
    document.getElementById('pl-new-tag-btn')?.addEventListener('click', _promptNewTag);
    return;
  }

  pane.innerHTML = `
    <table class="pl-tag-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Status</th>
          <th style="min-width:80px">Description</th>
          <th>Use Case</th>
          <th style="min-width:90px">Updated</th>
        </tr>
      </thead>
      <tbody>
        ${_tags.map(t => _tagRowHtml(t)).join('')}
      </tbody>
    </table>
    <div style="margin-top:1rem">
      ${_newTagButton()}
    </div>`;

  _tags.forEach(t => {
    document.getElementById(`plrow-${t.id}`)?.addEventListener('click', () => _openDrawer(t));
  });
  document.getElementById('pl-new-tag-btn')?.addEventListener('click', _promptNewTag);
}

function _tagRowHtml(t) {
  const st     = t.status || 'open';
  const stCls  = { open: 'st-open', active: 'st-active', done: 'st-done', archived: 'st-archived' }[st] || 'st-open';
  const isOpen = _drawer?.id === t.id;
  const updated = t.updated_at ? _fmtDate(t.updated_at) : (t.created_at ? _fmtDate(t.created_at) : '—');
  const fileIcon = t.file_ref ? `<span style="color:var(--accent);font-size:0.8rem" title="${_esc(t.file_ref)}">📄</span>` : '—';
  return `
    <tr class="pl-tag-row ${isOpen ? 'selected' : ''}" id="plrow-${t.id}">
      <td class="pl-tag-name" title="${_esc(t.name)}">${_esc(t.name)}</td>
      <td><span class="pl-status-badge ${stCls}">${st}</span></td>
      <td class="pl-tag-desc">${_esc(t.description || '')}</td>
      <td style="text-align:center">${fileIcon}</td>
      <td style="font-size:0.68rem;color:var(--muted)">${updated}</td>
    </tr>`;
}

function _newTagButton() {
  return `<button class="pl-add-btn" id="pl-new-tag-btn">+ New tag in ${_esc(_catName)}</button>`;
}

// ── Drawer ────────────────────────────────────────────────────────────────────

function _openDrawer(tag) {
  _drawer = tag;

  // Highlight row
  document.querySelectorAll('.pl-tag-row').forEach(r => r.classList.remove('selected'));
  document.getElementById(`plrow-${tag.id}`)?.classList.add('selected');

  // Build drawer content
  const inner = document.getElementById('pl-drawer-inner');
  if (!inner) return;

  const st = tag.status || 'open';
  const fileRef = tag.file_ref || '';

  inner.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
      <span style="font-size:0.7rem;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.05em">
        ${_esc(_catName)}
      </span>
      <button onclick="window._plCloseDrawer()"
              style="border:none;background:none;cursor:pointer;font-size:1rem;color:var(--muted);padding:0">×</button>
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
      <label class="pl-drawer-label">Description</label>
      <textarea id="pld-desc" class="pl-drawer-input">${_esc(tag.description || '')}</textarea>
    </div>

    ${fileRef ? `
    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Use Case File</label>
      <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
        <span style="font-size:0.72rem;color:var(--accent);font-family:var(--font)">📄 ${_esc(fileRef)}</span>
        <button class="pl-file-link" id="pld-view-uc" title="Preview use case file">Preview ↗</button>
      </div>
    </div>` : `
    <div class="pl-drawer-field">
      <label class="pl-drawer-label">Use Case File</label>
      <span style="font-size:0.72rem;color:var(--muted)">No file linked yet — assigned when backlog entry is processed.</span>
    </div>`}

    <div style="margin-bottom:1rem">
      <div class="pl-drawer-meta">Created: ${tag.created_at ? _fmtDate(tag.created_at) : '—'}</div>
    </div>

    <div style="display:flex;gap:0.5rem">
      <button id="pld-save" class="btn btn-primary btn-sm" style="flex:1">Save</button>
      <button id="pld-delete" class="btn btn-ghost btn-sm" style="color:var(--red,#dc2626)">Delete</button>
    </div>

    <!-- Use case preview panel -->
    <div id="pld-uc-preview" style="display:none;margin-top:1rem;padding:0.75rem;
         background:var(--surface2);border-radius:4px;border:1px solid var(--border)">
      <div style="font-size:0.62rem;font-weight:700;color:var(--muted);margin-bottom:0.5rem">USE CASE PREVIEW</div>
      <div id="pld-uc-content" style="font-size:0.72rem;color:var(--text2);line-height:1.5;
           white-space:pre-wrap;max-height:280px;overflow-y:auto"></div>
    </div>
  `;

  // Wire buttons
  document.getElementById('pld-save')?.addEventListener('click', () => _saveDrawer(tag.id));
  document.getElementById('pld-delete')?.addEventListener('click', () => _deleteTag(tag));
  document.getElementById('pld-view-uc')?.addEventListener('click', () => _previewUseCase(fileRef));
  window._plCloseDrawer = () => _closeDrawer(true);

  // Animate open
  const drawer = document.getElementById('pl-drawer');
  if (drawer) {
    drawer.style.width = '270px';
    drawer.style.borderLeftWidth = '1px';
  }
}

function _closeDrawer(reload = false) {
  _drawer = null;
  const drawer = document.getElementById('pl-drawer');
  if (drawer) {
    drawer.style.width = '0';
    drawer.style.borderLeftWidth = '0';
  }
  document.querySelectorAll('.pl-tag-row').forEach(r => r.classList.remove('selected'));
  if (reload) _loadTags();
}

async function _saveDrawer(tagId) {
  const name   = document.getElementById('pld-name')?.value?.trim();
  const status = document.getElementById('pld-status')?.value;
  const desc   = document.getElementById('pld-desc')?.value?.trim();
  if (!name) { toast('Name is required', 'error'); return; }

  const btn = document.getElementById('pld-save');
  if (btn) btn.disabled = true;
  try {
    await api.entities.patchValue(tagId, { name, status, description: desc });
    toast('Saved', 'success');
    // Update local copy and re-render table row
    const idx = _tags.findIndex(t => t.id === tagId);
    if (idx >= 0) {
      _tags[idx] = { ..._tags[idx], name, status, description: desc };
      _drawer = _tags[idx];
    }
    _renderTags();
    // Re-highlight
    document.getElementById(`plrow-${tagId}`)?.classList.add('selected');
    await _loadCats(); // refresh counts
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
    _renderTags();
    await _loadCats();
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
}

async function _promptNewTag() {
  const name = prompt(`New tag name in "${_catName}":`);
  if (!name?.trim()) return;
  try {
    await api.entities.createValue({
      name:          name.trim(),
      category_id:   _catId,
      category_name: _catName,
      project:       _project,
      status:        'open',
    });
    toast(`"${name.trim()}" created`, 'success');
    await _loadTags();
    await _loadCats();
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
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function _fmtDate(iso) {
  try {
    return new Date(iso).toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'2-digit' });
  } catch { return iso; }
}
