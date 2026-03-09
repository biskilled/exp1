/**
 * entities.js — Project Management: Features, Tasks, Bugs.
 *
 * Three-tab table view backed by entity_categories / entity_values.
 * Each tab loads api.entities.listValues filtered by category_name.
 * Users can create items, toggle status (active/done/archived), and delete.
 * event_count shows how many prompts/commits are tagged to each item.
 *
 * Requires PostgreSQL (shows 503 notice when unavailable).
 */

import { state } from '../stores/state.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';

const TABS = [
  { id: 'feature', label: 'Features', icon: '⬡', color: '#27ae60' },
  { id: 'task',    label: 'Tasks',    icon: '✓', color: '#4a90e2' },
  { id: 'bug',     label: 'Bugs',     icon: '⚠', color: '#e74c3c' },
  { id: 'tags',    label: 'Tags',     icon: '⬡', color: '#9b7fcc' },
];

// Tabs used in the "Create new" type selector (excludes the Tags management tab)
const PROJECT_TABS = TABS.filter(t => t.id !== 'tags');

let _activeTab    = 'feature';
let _catIds       = {};   // {name: id} — cached from listCategories
let _statusFilter = '';

// Tags sub-tab state
let _tagsState = { selectedCat: null, selectedVal: null, project: '' };

// ── Main render ───────────────────────────────────────────────────────────────

export function renderEntities(container) {
  _activeTab    = 'feature';
  _statusFilter = '';
  const project = state.currentProject?.name || '';

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- Header -->
      <div style="padding:0.75rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:1rem;flex-shrink:0">
        <span style="font-size:0.85rem;font-weight:700;color:var(--text)">Project Management</span>
        ${project ? `<span style="font-size:0.65rem;color:var(--accent)">${_esc(project)}</span>` : ''}
        <div style="margin-left:auto;display:flex;gap:0.5rem">
          <button class="btn btn-ghost btn-sm" onclick="window._projSync()" title="Import history + commits into event log">↻ Sync</button>
          <button class="btn btn-primary btn-sm" onclick="window._projCreateNew()">+ New</button>
        </div>
      </div>

      <!-- Tab bar + status filter -->
      <div style="display:flex;align-items:stretch;border-bottom:1px solid var(--border);
                  flex-shrink:0;background:var(--surface)">
        ${TABS.map(t => `
          <button id="proj-tab-${t.id}" onclick="window._projSetTab('${t.id}')"
            style="padding:0.55rem 1rem;font-size:0.72rem;border:none;cursor:pointer;
                   background:${t.id === 'feature' ? 'var(--bg)' : 'transparent'};
                   color:${t.id === 'feature' ? 'var(--text)' : 'var(--muted)'};
                   border-bottom:2px solid ${t.id === 'feature' ? 'var(--accent)' : 'transparent'};
                   font-family:var(--font);transition:all 0.15s;outline:none">
            ${t.icon} ${t.label}
          </button>`).join('')}
        <div style="margin-left:auto;padding:0.35rem 0.75rem;display:flex;align-items:center;gap:0.35rem">
          <span style="font-size:0.6rem;color:var(--muted)">Status:</span>
          <select id="proj-status-filter"
            onchange="window._projStatusFilter(this.value)"
            style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.65rem;padding:0.15rem 0.35rem;
                   border-radius:var(--radius);cursor:pointer;outline:none">
            <option value="">All</option>
            <option value="active">Active</option>
            <option value="done">Done</option>
            <option value="archived">Archived</option>
          </select>
        </div>
      </div>

      <!-- Content -->
      <div id="proj-content" style="flex:1;overflow-y:auto;padding:0.75rem 1.25rem">
        <div style="color:var(--muted);font-size:0.7rem;padding:1rem">Loading…</div>
      </div>

      <!-- Inline create form (hidden) -->
      <div id="proj-create-form"
           style="display:none;padding:0.6rem 1.25rem;border-top:1px solid var(--border);
                  background:var(--surface2);flex-shrink:0">
        <div style="display:flex;gap:0.5rem;align-items:flex-end;flex-wrap:wrap">
          <div>
            <div style="font-size:0.58rem;color:var(--muted);margin-bottom:0.12rem">Type</div>
            <select id="proj-create-type"
              style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                     font-family:var(--font);font-size:0.7rem;padding:0.25rem 0.5rem;
                     border-radius:var(--radius);outline:none">
              ${PROJECT_TABS.map(t => `<option value="${t.id}">${t.icon} ${t.label.replace(/s$/, '')}</option>`).join('')}
            </select>
          </div>
          <div style="flex:1;min-width:140px">
            <div style="font-size:0.58rem;color:var(--muted);margin-bottom:0.12rem">Name *</div>
            <input id="proj-create-name" type="text" placeholder="Name…"
              onkeydown="if(event.key==='Enter')window._projSaveNew()"
              style="width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);
                     font-family:var(--font);font-size:0.7rem;padding:0.25rem 0.5rem;
                     border-radius:var(--radius);outline:none;box-sizing:border-box">
          </div>
          <div style="flex:2;min-width:180px">
            <div style="font-size:0.58rem;color:var(--muted);margin-bottom:0.12rem">Description</div>
            <input id="proj-create-desc" type="text" placeholder="Optional description"
              onkeydown="if(event.key==='Enter')window._projSaveNew()"
              style="width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);
                     font-family:var(--font);font-size:0.7rem;padding:0.25rem 0.5rem;
                     border-radius:var(--radius);outline:none;box-sizing:border-box">
          </div>
          <button class="btn btn-primary btn-sm" onclick="window._projSaveNew()">Save</button>
          <button class="btn btn-ghost btn-sm" onclick="window._projCancelNew()">✕</button>
        </div>
      </div>

    </div>
  `;

  // Wire up window globals
  window._projSetTab      = _projSetTab;
  window._projStatusFilter = (v) => { _statusFilter = v; _projSetTab(_activeTab); };
  window._projSync        = _projSync;
  window._projCreateNew   = _projCreateNew;
  window._projSaveNew     = _projSaveNew;
  window._projCancelNew   = () => { document.getElementById('proj-create-form').style.display = 'none'; };
  window._projToggle      = _projToggleStatus;
  window._projDelete      = _projDelete;
  // Tags sub-tab globals
  window._tagsSelectCat   = _tagsSelectCat;
  window._tagsSelectVal   = _tagsSelectVal;
  window._tagsToggleStatus = _tagsToggleStatus;
  window._tagsCreateCategory = _tagsCreateCategory;
  window._tagsCreateValue = _tagsCreateValue;
  window._tagsDeleteValue = _tagsDeleteValue;
  window._tagsTagEvent    = _tagsTagEvent;
  window._tagsRemoveTag   = _tagsRemoveTag;
  window._tagsShowPicker  = _tagsShowPicker;
  window._tagsSyncEvents  = _tagsSyncEvents;

  if (!project) {
    document.getElementById('proj-content').innerHTML =
      '<div style="color:var(--muted);font-size:0.7rem;padding:3rem;text-align:center">No project open</div>';
    return;
  }

  _loadCategories(project).then(() => _projSetTab('feature'));
}

// ── Data loading ──────────────────────────────────────────────────────────────

async function _loadCategories(project) {
  try {
    const d = await api.entities.listCategories(project);
    _catIds = {};
    for (const c of d.categories || []) _catIds[c.name] = c.id;
  } catch { /* silent — categories may not exist yet */ }
}

async function _projSetTab(tabId) {
  _activeTab = tabId;
  const project = state.currentProject?.name || '';

  TABS.forEach(t => {
    const btn = document.getElementById(`proj-tab-${t.id}`);
    if (!btn) return;
    btn.style.background   = t.id === tabId ? 'var(--bg)' : 'transparent';
    btn.style.color        = t.id === tabId ? 'var(--text)' : 'var(--muted)';
    btn.style.borderBottom = `2px solid ${t.id === tabId ? 'var(--accent)' : 'transparent'}`;
  });

  // Show/hide status filter and new button based on active tab
  const filterEl = document.getElementById('proj-status-filter')?.parentElement;
  const newBtn   = document.querySelector('[onclick="window._projCreateNew()"]');
  const isTagsTab = tabId === 'tags';
  if (filterEl) filterEl.style.display = isTagsTab ? 'none' : '';
  if (newBtn)   newBtn.style.display   = isTagsTab ? 'none' : '';

  const content = document.getElementById('proj-content');
  if (!content) return;
  content.innerHTML = '<div style="color:var(--muted);font-size:0.7rem;padding:1rem">Loading…</div>';

  // Tags management tab — 3-column layout
  if (tabId === 'tags') {
    _tagsState = { selectedCat: null, selectedVal: null, project };
    await _renderTagsTab(content);
    return;
  }

  try {
    const opts = { category_name: tabId };
    if (_statusFilter) opts.status = _statusFilter;
    const d = await api.entities.listValues(project, null, opts);
    _renderValues(tabId, d.values || [], content);
  } catch (e) {
    const is503 = e.message.includes('503') || e.message.includes('PostgreSQL');
    content.innerHTML = `
      <div style="color:var(--muted);font-size:0.72rem;padding:3rem;text-align:center">
        <div style="font-size:2rem;margin-bottom:0.75rem">☁</div>
        ${is503
          ? 'PostgreSQL required for project management.<br><br><span style="font-size:0.65rem">Set DATABASE_URL in your environment to enable.</span>'
          : _esc(e.message)}
      </div>`;
  }
}

// ── Table rendering ───────────────────────────────────────────────────────────

function _renderValues(tabId, values, container) {
  const tab = TABS.find(t => t.id === tabId);
  if (!values.length) {
    container.innerHTML = `
      <div style="text-align:center;padding:3rem 1rem;color:var(--muted);font-size:0.72rem">
        <div style="font-size:2.5rem;margin-bottom:0.75rem">${tab?.icon || '•'}</div>
        No ${tab?.label || tabId} yet
        <br><br>
        <button class="btn btn-ghost btn-sm" onclick="window._projCreateNew()">+ Create first ${tabId}</button>
      </div>`;
    return;
  }

  const statusColors = { active: '#27ae60', done: '#888', archived: '#666', closed: '#888' };

  container.innerHTML = `
    <table style="width:100%;border-collapse:collapse;font-size:0.7rem">
      <thead>
        <tr style="border-bottom:2px solid var(--border)">
          <th style="text-align:left;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500">Name</th>
          <th style="text-align:left;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500;width:85px">Status</th>
          <th style="text-align:left;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500">Description</th>
          <th style="text-align:right;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500;width:56px" title="Prompts + commits tagged to this item">Events</th>
          <th style="text-align:center;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500;width:160px">Actions</th>
        </tr>
      </thead>
      <tbody>
        ${values.map(v => {
          const sc = statusColors[v.status] || '#888';
          return `
          <tr style="border-bottom:1px solid var(--border);transition:background 0.1s"
              onmouseenter="this.style.background='var(--surface2)'"
              onmouseleave="this.style.background=''">
            <td style="padding:0.45rem 0.5rem">
              <span style="color:${tab?.color || 'var(--accent)'}">${tab?.icon || '•'}</span>
              <span style="margin-left:0.3rem;color:var(--text);font-weight:500">${_esc(v.name)}</span>
            </td>
            <td style="padding:0.45rem 0.5rem">
              <span style="font-size:0.6rem;color:${sc};background:${sc}22;
                           padding:0.1rem 0.38rem;border-radius:10px;white-space:nowrap">
                ${_esc(v.status || 'active')}
              </span>
            </td>
            <td style="padding:0.45rem 0.5rem;color:var(--text2);font-size:0.65rem;
                       max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                title="${_esc(v.description || '')}">
              ${_esc(v.description || '—')}
            </td>
            <td style="padding:0.45rem 0.5rem;text-align:right;color:var(--muted)">${v.event_count || 0}</td>
            <td style="padding:0.45rem 0.5rem;text-align:center">
              <div style="display:flex;gap:0.25rem;justify-content:center">
                ${(v.status === 'active' || !v.status)
                  ? `<button onclick="window._projToggle(${v.id},'done')"
                       style="font-size:0.58rem;padding:0.1rem 0.38rem;background:var(--surface);
                              border:1px solid var(--border);border-radius:var(--radius);
                              cursor:pointer;color:var(--green);font-family:var(--font);outline:none"
                       title="Mark as done">✓ Done</button>`
                  : `<button onclick="window._projToggle(${v.id},'active')"
                       style="font-size:0.58rem;padding:0.1rem 0.38rem;background:var(--surface);
                              border:1px solid var(--border);border-radius:var(--radius);
                              cursor:pointer;color:var(--text2);font-family:var(--font);outline:none"
                       title="Reopen">↩ Open</button>`}
                <button onclick="window._projToggle(${v.id},'archived')"
                  style="font-size:0.58rem;padding:0.1rem 0.38rem;background:var(--surface);
                         border:1px solid var(--border);border-radius:var(--radius);
                         cursor:pointer;color:var(--muted);font-family:var(--font);outline:none"
                  title="Archive">⊘</button>
                <button onclick="window._projDelete(${v.id})"
                  style="font-size:0.58rem;padding:0.1rem 0.38rem;background:var(--surface);
                         border:1px solid var(--border);border-radius:var(--radius);
                         cursor:pointer;color:var(--red);font-family:var(--font);outline:none"
                  title="Delete">✕</button>
              </div>
            </td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>
  `;
}

// ── Actions ───────────────────────────────────────────────────────────────────

async function _projToggleStatus(valueId, newStatus) {
  try {
    await api.entities.patchValue(valueId, { status: newStatus });
    toast(`Status → ${newStatus}`, 'success');
    _projSetTab(_activeTab);
  } catch (e) { toast(e.message, 'error'); }
}

async function _projDelete(valueId) {
  if (!confirm('Delete this item? This cannot be undone.')) return;
  try {
    await api.entities.deleteValue(valueId);
    toast('Deleted', 'success');
    _projSetTab(_activeTab);
  } catch (e) { toast(e.message, 'error'); }
}

function _projCreateNew() {
  const form = document.getElementById('proj-create-form');
  if (!form) return;
  form.style.display = 'flex';
  const typeSelect = document.getElementById('proj-create-type');
  if (typeSelect) typeSelect.value = _activeTab;
  setTimeout(() => document.getElementById('proj-create-name')?.focus(), 0);
}

async function _projSaveNew() {
  const project = state.currentProject?.name || '';
  const type    = document.getElementById('proj-create-type')?.value;
  const name    = document.getElementById('proj-create-name')?.value?.trim();
  const desc    = document.getElementById('proj-create-desc')?.value?.trim() || '';
  if (!name) { toast('Name required', 'error'); return; }
  if (!type) { toast('Type required', 'error'); return; }

  // Ensure categories are loaded (idempotent re-load if _catIds is empty)
  if (!Object.keys(_catIds).length) await _loadCategories(project);

  const catId = _catIds[type];
  if (!catId) {
    toast(`Category '${type}' not initialized — try clicking ↻ Sync`, 'error');
    return;
  }

  try {
    await api.entities.createValue({ category_id: catId, name, description: desc, project });
    toast(`Created ${type}: ${name}`, 'success');
    document.getElementById('proj-create-form').style.display = 'none';
    document.getElementById('proj-create-name').value = '';
    document.getElementById('proj-create-desc').value = '';
    _projSetTab(type);
  } catch (e) { toast(e.message, 'error'); }
}

async function _projSync() {
  const project = state.currentProject?.name;
  if (!project) return;
  try {
    const r = await api.entities.syncEvents(project);
    toast(`Synced — ${r.imported?.prompt || 0} prompts, ${r.imported?.commit || 0} commits`, 'success');
    _projSetTab(_activeTab);  // refresh event_count
  } catch (e) { toast(e.message, 'error'); }
}

// ── Tags sub-tab ──────────────────────────────────────────────────────────────

async function _renderTagsTab(container) {
  container.style.padding = '0';
  container.style.overflow = 'hidden';
  container.style.display = 'flex';
  container.style.flexDirection = 'column';
  container.style.height = '100%';

  container.innerHTML = `
    <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--border);flex-shrink:0">
      <span style="font-size:0.75rem;font-weight:600">Tag Management</span>
      <button onclick="window._tagsSyncEvents()"
        style="padding:3px 10px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface);font-size:0.65rem">
        ↻ Sync events
      </button>
      <div style="flex:1"></div>
      <span id="tags-status-msg" style="font-size:0.62rem;color:var(--muted)"></span>
    </div>
    <div style="display:flex;flex:1;min-height:0;overflow:hidden">
      <!-- Categories -->
      <div id="tags-cats-pane" style="width:160px;flex-shrink:0;border-right:1px solid var(--border);overflow-y:auto;padding:8px 6px"></div>
      <!-- Values -->
      <div id="tags-vals-pane" style="width:220px;flex-shrink:0;border-right:1px solid var(--border);overflow-y:auto;padding:8px 6px">
        <div style="color:var(--muted);font-size:0.65rem;padding:8px">← Select a category</div>
      </div>
      <!-- Events -->
      <div id="tags-events-pane" style="flex:1;overflow-y:auto;padding:8px 10px">
        <div style="color:var(--muted);font-size:0.65rem;padding:8px">← Select a tag to see linked events</div>
      </div>
    </div>
  `;
  await _tagsLoadCategories();
}

async function _tagsLoadCategories() {
  const { project } = _tagsState;
  const pane = document.getElementById('tags-cats-pane');
  if (!pane) return;
  try {
    const data = await api.entities.listCategories(project);
    const cats = data.categories || [];
    pane.innerHTML = `
      <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);padding:2px 4px 6px;letter-spacing:.05em">Categories</div>
      ${cats.map(c => `
        <div class="tags-cat-row" data-id="${c.id}" data-name="${_esc(c.name)}"
          onclick="window._tagsSelectCat(${c.id},'${_esc(c.name)}')"
          style="display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:5px;cursor:pointer;margin-bottom:2px;
                 background:${_tagsState.selectedCat === c.id ? 'var(--accent)22' : 'transparent'};
                 border-left:2px solid ${_tagsState.selectedCat === c.id ? 'var(--accent)' : 'transparent'}">
          <span style="color:${c.color};font-size:0.85rem">${c.icon}</span>
          <span style="font-size:0.65rem;flex:1">${_esc(c.name)}</span>
          <span style="font-size:0.58rem;color:var(--muted)">${c.value_count}</span>
        </div>`).join('')}
      <div style="margin-top:8px;padding:4px">
        <input id="tags-new-cat" placeholder="New category…"
          style="width:100%;padding:3px 6px;border:1px dashed var(--border);border-radius:4px;
                 background:transparent;color:var(--text);font-size:0.62rem;box-sizing:border-box"
          onkeydown="if(event.key==='Enter')window._tagsCreateCategory(this.value)" />
      </div>`;
  } catch (e) {
    pane.innerHTML = `<div style="color:var(--red);font-size:0.62rem;padding:8px">${_esc(e.message)}</div>`;
  }
}

async function _tagsSelectCat(catId, catName) {
  _tagsState.selectedCat = catId;
  _tagsState.selectedVal = null;
  document.querySelectorAll('.tags-cat-row').forEach(r => {
    const sel = parseInt(r.dataset.id) === catId;
    r.style.background  = sel ? 'var(--accent)22' : 'transparent';
    r.style.borderLeft  = sel ? '2px solid var(--accent)' : '2px solid transparent';
  });
  await _tagsLoadValues(catId, catName);
  const ep = document.getElementById('tags-events-pane');
  if (ep) ep.innerHTML = '<div style="color:var(--muted);font-size:0.65rem;padding:8px">← Select a tag</div>';
}

async function _tagsLoadValues(catId, catName) {
  const { project } = _tagsState;
  const pane = document.getElementById('tags-vals-pane');
  if (!pane) return;
  pane.innerHTML = '<div style="color:var(--muted);font-size:0.62rem;padding:8px">Loading…</div>';
  try {
    const data = await api.entities.listValues(project, catId);
    const vals = data.values || [];
    const statusColors = { active: '#27ae60', archived: '#888', done: '#888' };
    pane.innerHTML = `
      <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);padding:2px 4px 6px;letter-spacing:.05em">${_esc(catName)}</div>
      ${vals.map(v => {
        const sc = statusColors[v.status] || '#888';
        const desc = (v.description || '').slice(0, 60);
        const date = (v.created_at || '').slice(0, 10);
        return `
        <div class="tags-val-row" data-id="${v.id}"
          onclick="window._tagsSelectVal(${v.id},'${_esc(v.name)}')"
          style="padding:6px 8px;border-radius:5px;cursor:pointer;margin-bottom:3px;
                 border:1px solid ${_tagsState.selectedVal === v.id ? 'var(--accent)' : 'var(--border)'};
                 background:${_tagsState.selectedVal === v.id ? 'var(--surface2)' : 'transparent'}">
          <div style="display:flex;align-items:center;gap:5px;margin-bottom:2px">
            <span style="font-size:0.65rem;font-weight:500;flex:1">${_esc(v.name)}</span>
            <span style="font-size:0.55rem;color:${sc};background:${sc}22;padding:0 4px;border-radius:8px;cursor:pointer"
              onclick="event.stopPropagation();window._tagsToggleStatus(${v.id},'${v.status}')"
              title="Toggle status">${_esc(v.status || 'active')}</span>
            <button onclick="event.stopPropagation();window._tagsDeleteValue(${v.id})"
              style="border:none;background:none;cursor:pointer;color:var(--muted);font-size:0.6rem;padding:0 2px">✕</button>
          </div>
          ${desc ? `<div style="font-size:0.58rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${_esc(v.description)}">${_esc(desc)}${v.description.length > 60 ? '…' : ''}</div>` : ''}
          <div style="font-size:0.55rem;color:var(--muted);margin-top:2px">${date} · ${v.event_count || 0} events</div>
        </div>`;
      }).join('')}
      ${vals.length === 0 ? '<div style="color:var(--muted);font-size:0.62rem;padding:4px 8px">No tags yet</div>' : ''}
      <div style="margin-top:8px;padding:4px">
        <input id="tags-new-val" placeholder="New tag…"
          style="width:100%;padding:3px 6px;border:1px dashed var(--border);border-radius:4px;
                 background:transparent;color:var(--text);font-size:0.62rem;box-sizing:border-box"
          onkeydown="if(event.key==='Enter')window._tagsCreateValue(${catId},this.value)" />
      </div>`;
  } catch (e) {
    pane.innerHTML = `<div style="color:var(--red);font-size:0.62rem;padding:8px">${_esc(e.message)}</div>`;
  }
}

async function _tagsSelectVal(valId, valName) {
  _tagsState.selectedVal = valId;
  document.querySelectorAll('.tags-val-row').forEach(r => {
    const sel = parseInt(r.dataset.id) === valId;
    r.style.border     = sel ? '1px solid var(--accent)' : '1px solid var(--border)';
    r.style.background = sel ? 'var(--surface2)' : 'transparent';
  });
  await _tagsLoadValueEvents(valId, valName);
}

async function _tagsLoadValueEvents(valId, valName) {
  const { project } = _tagsState;
  const pane = document.getElementById('tags-events-pane');
  if (!pane) return;
  pane.innerHTML = '<div style="color:var(--muted);font-size:0.62rem;padding:8px">Loading events…</div>';
  try {
    const data = await api.entities.valueEvents(valId, project);
    const events = data.events || [];
    pane.innerHTML = `
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
        <span style="font-size:0.75rem;font-weight:600">${_esc(valName)}</span>
        <span style="font-size:0.62rem;color:var(--muted)">${events.length} events</span>
        <div style="flex:1"></div>
        <button onclick="window._tagsShowPicker(${valId},'${_esc(valName)}')"
          style="padding:3px 10px;border:1px solid var(--border);border-radius:4px;cursor:pointer;background:var(--surface);font-size:0.62rem">
          + Tag event
        </button>
      </div>
      ${events.length === 0
        ? '<div style="color:var(--muted);font-size:0.65rem;padding:8px">No events tagged yet.<br>Click "+ Tag event" to link events.</div>'
        : events.map(e => {
            const isCommit = e.event_type === 'commit';
            const icon = isCommit ? '⑂' : '◉';
            const color = isCommit ? 'var(--accent)' : 'var(--text)';
            const date = (e.created_at || '').slice(0, 10);
            return `
            <div style="border:1px solid var(--border);border-radius:5px;padding:7px 10px;margin-bottom:5px">
              <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;font-size:0.6rem">
                <span style="color:${color}">${icon} ${e.event_type}</span>
                <span style="color:var(--muted)">${date}</span>
                <span style="color:var(--muted);font-family:monospace">${(e.source_id||'').slice(0,8)}</span>
                <div style="flex:1"></div>
                <button onclick="window._tagsRemoveTag(${e.id},${valId},'${_esc(valName)}')"
                  style="border:none;background:none;cursor:pointer;color:var(--red,#e74c3c);font-size:0.6rem">Remove</button>
              </div>
              <div style="font-size:0.65rem">${_esc((e.title||'').slice(0,120))}</div>
            </div>`;
          }).join('')}
    `;
  } catch (e) {
    pane.innerHTML = `<div style="color:var(--red);font-size:0.62rem;padding:8px">${_esc(e.message)}</div>`;
  }
}

async function _tagsToggleStatus(valId, currentStatus) {
  const newStatus = currentStatus === 'active' ? 'archived' : 'active';
  try {
    await api.entities.patchValue(valId, { status: newStatus });
    // Reload the values pane
    const catId = _tagsState.selectedCat;
    const catRow = document.querySelector(`.tags-cat-row[data-id="${catId}"]`);
    const catName = catRow?.dataset.name || '';
    await _tagsLoadValues(catId, catName);
  } catch (e) { toast(e.message, 'error'); }
}

async function _tagsCreateCategory(name) {
  name = (name || '').trim();
  if (!name) return;
  const { project } = _tagsState;
  try {
    await api.entities.createCategory({ name, project });
    document.getElementById('tags-new-cat').value = '';
    await _tagsLoadCategories();
  } catch (e) { toast('Create failed: ' + e.message, 'error'); }
}

async function _tagsCreateValue(catId, name) {
  name = (name || '').trim();
  if (!name) return;
  const { project } = _tagsState;
  const catRow = document.querySelector(`.tags-cat-row[data-id="${catId}"]`);
  const catName = catRow?.dataset.name || '';
  try {
    await api.entities.createValue({ category_id: catId, name, project });
    document.getElementById('tags-new-val').value = '';
    await _tagsLoadValues(catId, catName);
  } catch (e) { toast('Create failed: ' + e.message, 'error'); }
}

async function _tagsDeleteValue(valId) {
  if (!confirm('Delete this tag and all its event links?')) return;
  try {
    await api.entities.deleteValue(valId);
    const catId = _tagsState.selectedCat;
    const catRow = document.querySelector(`.tags-cat-row[data-id="${catId}"]`);
    const catName = catRow?.dataset.name || '';
    await _tagsLoadValues(catId, catName);
    const ep = document.getElementById('tags-events-pane');
    if (ep) ep.innerHTML = '<div style="color:var(--muted);font-size:0.65rem;padding:8px">← Select a tag</div>';
  } catch (e) { toast('Delete failed: ' + e.message, 'error'); }
}

async function _tagsShowPicker(valId, valName) {
  const { project } = _tagsState;
  const data = await api.entities.listEvents(project, { limit: 50 });
  const events = (data.events || []).filter(e => !(e.tags||[]).some(t => t.value_id === valId));

  const modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.6);display:flex;align-items:center;justify-content:center;z-index:2000';
  modal.innerHTML = `
    <div style="background:var(--bg);border-radius:8px;padding:20px;width:540px;max-height:70vh;display:flex;flex-direction:column;overflow:hidden">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <strong style="font-size:0.8rem">Tag events with: ${_esc(valName)}</strong>
        <button onclick="this.closest('[style*=fixed]').remove()" style="border:none;background:none;cursor:pointer;font-size:1rem">✕</button>
      </div>
      <input id="tags-picker-search" placeholder="Filter events…"
        style="padding:5px 8px;border:1px solid var(--border);border-radius:4px;margin-bottom:8px;
               background:var(--surface);color:var(--text);font-size:0.68rem" />
      <div style="overflow-y:auto;flex:1">
        ${events.length === 0
          ? '<div style="color:var(--muted);padding:12px;text-align:center;font-size:0.68rem">All events already tagged</div>'
          : events.map(e => `
            <div class="tags-picker-row"
              style="display:flex;align-items:center;gap:8px;padding:6px 8px;border-bottom:1px solid var(--border);cursor:pointer"
              onclick="window._tagsTagEvent(${e.id},${valId},'${_esc(valName)}',this)">
              <span style="font-size:0.6rem;color:var(--accent);width:50px">${e.event_type}</span>
              <span style="font-size:0.6rem;color:var(--muted);width:80px">${(e.created_at||'').slice(0,10)}</span>
              <span style="font-size:0.65rem;flex:1">${_esc((e.title||'').slice(0,100))}</span>
              <span style="font-size:0.6rem;color:var(--muted)">+ Tag</span>
            </div>`).join('')}
      </div>
    </div>`;
  document.body.appendChild(modal);
  modal.querySelector('#tags-picker-search')?.addEventListener('input', ev => {
    const q = ev.target.value.toLowerCase();
    modal.querySelectorAll('.tags-picker-row').forEach(r => {
      r.style.display = r.textContent.toLowerCase().includes(q) ? '' : 'none';
    });
  });
}

async function _tagsTagEvent(eventId, valId, valName, rowEl) {
  try {
    await api.entities.addTag(eventId, { entity_value_id: valId, auto_tagged: false });
    if (rowEl) {
      rowEl.style.background = 'rgba(39,174,96,.15)';
      rowEl.style.pointerEvents = 'none';
      rowEl.lastElementChild.textContent = '✓ Tagged';
    }
    await _tagsLoadValueEvents(valId, valName);
  } catch (e) { toast('Tag failed: ' + e.message, 'error'); }
}

async function _tagsRemoveTag(eventId, valId, valName) {
  try {
    await api.entities.removeTag(eventId, valId);
    await _tagsLoadValueEvents(valId, valName);
  } catch (e) { toast('Remove failed: ' + e.message, 'error'); }
}

async function _tagsSyncEvents() {
  const statusEl = document.getElementById('tags-status-msg');
  const { project } = _tagsState;
  if (statusEl) statusEl.textContent = 'Syncing…';
  try {
    const res = await api.entities.syncEvents(project);
    const total = (res.imported?.prompt || 0) + (res.imported?.commit || 0);
    if (statusEl) statusEl.textContent = `✓ ${total} events synced`;
    await _tagsLoadCategories();
  } catch (e) {
    if (statusEl) statusEl.textContent = 'Sync failed: ' + e.message;
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _esc(str) {
  return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
                          .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
