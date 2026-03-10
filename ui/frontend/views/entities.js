/**
 * entities.js — Planner: Unified Tag Manager.
 *
 * 2-pane layout: left pane = category list (160px), right pane = tag table.
 * All project items (features, tasks, bugs, etc.) are entity_values in different
 * categories — no separate tabs needed. Status cycles active→done→archived.
 *
 * Requires PostgreSQL (shows 503 notice when unavailable).
 */

import { state } from '../stores/state.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';

let _plannerState = { selectedCat: null, selectedCatName: '', project: '' };

// ── Main render ───────────────────────────────────────────────────────────────

export function renderEntities(container) {
  const project = state.currentProject?.name || '';
  _plannerState = { selectedCat: null, selectedCatName: '', project };

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- Header -->
      <div style="padding:0.75rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:1rem;flex-shrink:0">
        <span style="font-size:0.85rem;font-weight:700;color:var(--text)">Tag Management</span>
        ${project ? `<span style="font-size:0.65rem;color:var(--accent)">${_esc(project)}</span>` : ''}
        <button class="btn btn-ghost btn-sm" style="margin-left:auto"
          onclick="window._plannerSync()" title="Sync events + reload">↻ Sync</button>
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

        <!-- Right pane: tag table -->
        <div id="planner-tags-pane" style="flex:1;overflow-y:auto;padding:0.75rem 1rem">
          <div style="color:var(--muted);font-size:0.7rem;padding:3rem;text-align:center">
            ← Select a category
          </div>
        </div>

      </div>
    </div>
  `;

  // Wire window globals
  window._plannerSelectCat    = _plannerSelectCat;
  window._plannerCycleStatus  = _plannerCycleStatus;
  window._plannerSaveDesc     = _plannerSaveDesc;
  window._plannerSaveDue      = _plannerSaveDue;
  window._plannerDeleteVal    = _plannerDeleteVal;
  window._plannerArchiveVal   = _plannerArchiveVal;
  window._plannerSaveNewTag   = _plannerSaveNewTag;
  window._plannerCancelNewTag = _plannerCancelNewTag;
  window._plannerSync         = _plannerSync;
  window._plannerNewCat       = _plannerNewCat;

  if (!project) {
    document.getElementById('planner-tags-pane').innerHTML =
      '<div style="color:var(--muted);font-size:0.7rem;padding:3rem;text-align:center">No project open</div>';
    return;
  }

  _loadCategories();
}

// ── Categories ────────────────────────────────────────────────────────────────

async function _loadCategories() {
  const { project } = _plannerState;
  const list = document.getElementById('planner-cat-list');
  if (!list) return;
  list.innerHTML = '<div style="color:var(--muted);font-size:0.62rem;padding:8px 10px">Loading…</div>';
  try {
    const data = await api.entities.listCategories(project);
    const cats  = data.categories || [];
    if (!cats.length) {
      list.innerHTML = '<div style="color:var(--muted);font-size:0.62rem;padding:8px 10px">No categories yet</div>';
      return;
    }
    list.innerHTML = cats.map(c => `
      <div class="planner-cat-row" data-id="${c.id}" data-name="${_esc(c.name)}"
           data-color="${_esc(c.color)}" data-icon="${_esc(c.icon)}"
           onclick="window._plannerSelectCat(${c.id},'${_esc(c.name)}')"
           style="display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:5px;
                  cursor:pointer;margin-bottom:2px;transition:background 0.1s;
                  background:${_plannerState.selectedCat === c.id ? 'var(--accent)22' : 'transparent'};
                  border-left:2px solid ${_plannerState.selectedCat === c.id ? 'var(--accent)' : 'transparent'}">
        <span style="color:${c.color};font-size:0.85rem">${c.icon}</span>
        <span style="font-size:0.65rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(c.name)}</span>
        <span style="font-size:0.55rem;color:var(--muted);flex-shrink:0">${c.value_count}</span>
      </div>`).join('');
  } catch (e) {
    list.innerHTML = `<div style="color:var(--red,#e74c3c);font-size:0.62rem;padding:8px 10px">${_esc(e.message)}</div>`;
  }
}

async function _plannerSelectCat(catId, catName) {
  _plannerState.selectedCat = catId;
  _plannerState.selectedCatName = catName;
  document.querySelectorAll('.planner-cat-row').forEach(r => {
    const sel = parseInt(r.dataset.id) === catId;
    r.style.background = sel ? 'var(--accent)22' : 'transparent';
    r.style.borderLeft = sel ? '2px solid var(--accent)' : '2px solid transparent';
  });
  await _loadTagTable(catId, catName);
}

async function _plannerNewCat(name) {
  name = (name || '').trim();
  if (!name) return;
  const { project } = _plannerState;
  const inp = document.getElementById('planner-new-cat-inp');
  try {
    await api.entities.createCategory({ name, project });
    if (inp) inp.value = '';
    await _loadCategories();
  } catch (e) { toast('Create failed: ' + e.message, 'error'); }
}

// ── Tag table ─────────────────────────────────────────────────────────────────

async function _loadTagTable(catId, catName) {
  const pane = document.getElementById('planner-tags-pane');
  if (!pane) return;
  const { project } = _plannerState;

  const catRow   = document.querySelector(`.planner-cat-row[data-id="${catId}"]`);
  const catColor = catRow?.dataset.color || 'var(--accent)';
  const catIcon  = catRow?.dataset.icon  || '⬡';

  pane.innerHTML = '<div style="color:var(--muted);font-size:0.7rem;padding:1rem">Loading…</div>';
  try {
    const data = await api.entities.listValues(project, catId);
    _renderTagTable(pane, catId, catName, catColor, catIcon, data.values || []);
  } catch (e) {
    const is503 = e.message.includes('503') || e.message.includes('PostgreSQL');
    pane.innerHTML = `
      <div style="color:var(--muted);font-size:0.72rem;padding:3rem;text-align:center">
        <div style="font-size:2rem;margin-bottom:0.75rem">☁</div>
        ${is503
          ? 'PostgreSQL required for tag management.<br><br><span style="font-size:0.65rem">Set DATABASE_URL in your environment to enable.</span>'
          : _esc(e.message)}
      </div>`;
  }
}

function _renderTagTable(pane, catId, catName, catColor, catIcon, vals) {
  const STATUS_CYCLE  = { active: 'done', done: 'archived', archived: 'active' };
  const STATUS_COLORS = { active: '#27ae60', done: '#888', archived: '#666' };

  pane.innerHTML = `
    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem">
      <span style="font-size:0.8rem;color:${catColor}">${catIcon}</span>
      <span style="font-size:0.78rem;font-weight:600;color:var(--text)">${_esc(catName)}</span>
      <button onclick="window._plannerShowNewTag()"
        style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
               padding:0.2rem 0.55rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none;margin-left:auto">+ New Tag</button>
    </div>

    <!-- New tag inline row (hidden) -->
    <div id="planner-new-tag-row"
         style="display:none;gap:0.4rem;align-items:center;margin-bottom:0.5rem;
                padding:0.4rem 0.5rem;background:var(--surface2);
                border:1px solid var(--border);border-radius:var(--radius)">
      <input id="planner-new-tag-inp" placeholder="Tag name…" type="text"
        onkeydown="if(event.key==='Enter')window._plannerSaveNewTag(${catId});if(event.key==='Escape')window._plannerCancelNewTag()"
        style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
               font-family:var(--font);font-size:0.68rem;padding:0.22rem 0.45rem;
               border-radius:var(--radius);outline:none" />
      <button onclick="window._plannerSaveNewTag(${catId})"
        style="background:var(--accent);border:none;color:#fff;font-size:0.62rem;
               padding:0.22rem 0.55rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none">Save</button>
      <button onclick="window._plannerCancelNewTag()"
        style="background:none;border:1px solid var(--border);color:var(--muted);font-size:0.62rem;
               padding:0.22rem 0.45rem;border-radius:var(--radius);cursor:pointer;
               font-family:var(--font);outline:none">✕</button>
    </div>

    ${vals.length === 0 ? `
      <div style="text-align:center;padding:3rem 1rem;color:var(--muted);font-size:0.72rem">
        <div style="font-size:2rem;margin-bottom:0.75rem">${catIcon}</div>
        No tags in <strong>${_esc(catName)}</strong> yet
      </div>` : `
    <table style="width:100%;border-collapse:collapse;font-size:0.7rem">
      <thead>
        <tr style="border-bottom:2px solid var(--border)">
          <th style="text-align:left;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500">Name</th>
          <th style="text-align:left;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500;width:80px">Status</th>
          <th style="text-align:left;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500">Description</th>
          <th style="text-align:left;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500;width:125px">Due Date</th>
          <th style="text-align:left;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500;width:80px">Created</th>
          <th style="text-align:right;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500;width:52px">Events</th>
          <th style="text-align:center;padding:0.4rem 0.5rem;color:var(--muted);font-weight:500;width:64px">Actions</th>
        </tr>
      </thead>
      <tbody>
        ${vals.map(v => {
          const sc   = STATUS_COLORS[v.status] || '#888';
          const next = STATUS_CYCLE[v.status]  || 'active';
          const desc    = v.description || '';
          const due     = v.due_date    || '';
          const created = (v.created_at || '').slice(0, 10);
          return `
          <tr style="border-bottom:1px solid var(--border);transition:background 0.1s"
              onmouseenter="this.style.background='var(--surface2)'"
              onmouseleave="this.style.background=''">
            <td style="padding:0.45rem 0.5rem;color:var(--text);font-weight:500">${_esc(v.name)}</td>
            <td style="padding:0.45rem 0.5rem">
              <span onclick="window._plannerCycleStatus(${v.id},'${next}')"
                style="font-size:0.6rem;color:${sc};background:${sc}22;
                       padding:0.1rem 0.38rem;border-radius:10px;white-space:nowrap;
                       cursor:pointer;user-select:none"
                title="Click to cycle: active→done→archived">${_esc(v.status || 'active')}</span>
            </td>
            <td style="padding:0.45rem 0.5rem;max-width:180px">
              <span contenteditable="true"
                onblur="window._plannerSaveDesc(${v.id},this.textContent)"
                onfocus="this.style.borderBottomColor='var(--accent)'"
                style="display:inline-block;color:var(--text2);font-size:0.65rem;outline:none;
                       cursor:text;min-width:20px;border-bottom:1px dashed transparent;
                       transition:border-color 0.15s"
                title="Click to edit description">${_esc(desc || '—')}</span>
            </td>
            <td style="padding:0.45rem 0.5rem">
              <input type="date" value="${_esc(due)}"
                onchange="window._plannerSaveDue(${v.id},this.value)"
                style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                       font-family:var(--font);font-size:0.62rem;padding:0.1rem 0.25rem;
                       border-radius:var(--radius);outline:none;max-width:115px" />
            </td>
            <td style="padding:0.45rem 0.5rem;color:var(--muted);font-size:0.62rem;white-space:nowrap">${created}</td>
            <td style="padding:0.45rem 0.5rem;text-align:right;color:var(--muted)">${v.event_count || 0}</td>
            <td style="padding:0.45rem 0.5rem;text-align:center">
              <div style="display:flex;gap:0.2rem;justify-content:center">
                <button onclick="window._plannerArchiveVal(${v.id})"
                  style="font-size:0.58rem;padding:0.1rem 0.3rem;background:var(--surface);
                         border:1px solid var(--border);border-radius:var(--radius);
                         cursor:pointer;color:var(--muted);font-family:var(--font);outline:none"
                  title="Archive">⊘</button>
                <button onclick="window._plannerDeleteVal(${v.id})"
                  style="font-size:0.58rem;padding:0.1rem 0.3rem;background:var(--surface);
                         border:1px solid var(--border);border-radius:var(--radius);
                         cursor:pointer;color:var(--red,#e74c3c);font-family:var(--font);outline:none"
                  title="Delete">✕</button>
              </div>
            </td>
          </tr>`;
        }).join('')}
      </tbody>
    </table>`}
  `;

  // Wire the "New Tag" show button (defined inline so catId is in scope)
  window._plannerShowNewTag = () => {
    const row = document.getElementById('planner-new-tag-row');
    if (!row) return;
    row.style.display = 'flex';
    setTimeout(() => document.getElementById('planner-new-tag-inp')?.focus(), 0);
  };
}

// ── Tag actions ───────────────────────────────────────────────────────────────

async function _plannerCycleStatus(valId, nextStatus) {
  try {
    await api.entities.patchValue(valId, { status: nextStatus });
    const { selectedCat, selectedCatName } = _plannerState;
    if (selectedCat) await _loadTagTable(selectedCat, selectedCatName);
  } catch (e) { toast(e.message, 'error'); }
}

async function _plannerSaveDesc(valId, rawText) {
  const desc = (rawText || '').trim();
  try {
    await api.entities.patchValue(valId, { description: desc === '—' ? '' : desc });
  } catch (e) { toast('Save failed: ' + e.message, 'error'); }
}

async function _plannerSaveDue(valId, dateStr) {
  try {
    await api.entities.patchValue(valId, { due_date: dateStr || '' });
    toast('Due date saved', 'success');
  } catch (e) { toast('Save failed: ' + e.message, 'error'); }
}

async function _plannerArchiveVal(valId) {
  try {
    await api.entities.patchValue(valId, { status: 'archived' });
    toast('Archived', 'success');
    const { selectedCat, selectedCatName } = _plannerState;
    if (selectedCat) await _loadTagTable(selectedCat, selectedCatName);
  } catch (e) { toast(e.message, 'error'); }
}

async function _plannerDeleteVal(valId) {
  if (!confirm('Delete this tag and all its event links?')) return;
  try {
    await api.entities.deleteValue(valId);
    toast('Deleted', 'success');
    const { selectedCat, selectedCatName } = _plannerState;
    if (selectedCat) await _loadTagTable(selectedCat, selectedCatName);
    await _loadCategories();
  } catch (e) { toast(e.message, 'error'); }
}

async function _plannerSaveNewTag(catId) {
  const inp  = document.getElementById('planner-new-tag-inp');
  const name = (inp?.value || '').trim();
  if (!name) { toast('Name required', 'error'); return; }
  const { project, selectedCatName } = _plannerState;
  try {
    await api.entities.createValue({ category_id: catId, name, project });
    if (inp) inp.value = '';
    _plannerCancelNewTag();
    await _loadTagTable(catId, selectedCatName);
    await _loadCategories();
  } catch (e) { toast('Create failed: ' + e.message, 'error'); }
}

function _plannerCancelNewTag() {
  const row = document.getElementById('planner-new-tag-row');
  if (row) row.style.display = 'none';
  const inp = document.getElementById('planner-new-tag-inp');
  if (inp) inp.value = '';
}

async function _plannerSync() {
  const { project, selectedCat, selectedCatName } = _plannerState;
  if (!project) return;
  try {
    const r = await api.entities.syncEvents(project);
    toast(`Synced — ${r.imported?.prompt || 0} prompts, ${r.imported?.commit || 0} commits`, 'success');
    if (selectedCat) await _loadTagTable(selectedCat, selectedCatName);
    await _loadCategories();
  } catch (e) { toast(e.message, 'error'); }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _esc(str) {
  return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
                          .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
