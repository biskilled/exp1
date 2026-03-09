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
];

let _activeTab    = 'feature';
let _catIds       = {};   // {name: id} — cached from listCategories
let _statusFilter = '';

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
              ${TABS.map(t => `<option value="${t.id}">${t.icon} ${t.label.replace(/s$/, '')}</option>`).join('')}
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

  const content = document.getElementById('proj-content');
  if (!content) return;
  content.innerHTML = '<div style="color:var(--muted);font-size:0.7rem;padding:1rem">Loading…</div>';

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

// ── Helpers ───────────────────────────────────────────────────────────────────

function _esc(str) {
  return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;')
                          .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
