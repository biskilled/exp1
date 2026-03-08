/**
 * entities.js — Features / Tasks / Bugs entity management view.
 *
 * Three-tab table view with create/edit modals following admin.js pattern.
 * Requires PostgreSQL on the backend (shows 503 message when unavailable).
 */

import { state } from '../stores/state.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';

const TABS = [
  { id: 'features', label: 'Features' },
  { id: 'tasks',    label: 'Tasks' },
  { id: 'bugs',     label: 'Bugs' },
];

let _activeTab = 'features';

// ── Main render ───────────────────────────────────────────────────────────────

export function renderEntities(container) {
  container.className = 'view active entities-view';
  const project = state.currentProject?.name || '';

  container.innerHTML = `
    <div class="entities-toolbar">
      <span style="font-size:0.85rem;font-weight:600">Entity Tracker</span>
      <div style="flex:1"></div>
      <button class="btn btn-primary btn-sm" id="ent-add-btn" onclick="window._entAdd()">+ Add</button>
    </div>
    <div class="entities-tabs" id="ent-tabs">
      ${TABS.map(t => `
        <div class="entities-tab ${_activeTab === t.id ? 'active' : ''}"
             onclick="window._entTab('${t.id}')">${t.label}</div>
      `).join('')}
    </div>
    <div style="flex:1;overflow-y:auto;padding:0.5rem" id="ent-body"></div>
  `;

  window._entTab = (tab) => {
    _activeTab = tab;
    document.querySelectorAll('.entities-tab').forEach(el => {
      el.classList.toggle('active', el.textContent.trim() === TABS.find(t => t.id === tab)?.label);
    });
    _loadTab(project);
  };
  window._entAdd = () => _showCreateModal(_activeTab, project);

  _loadTab(project);
}

// ── Tab loading ───────────────────────────────────────────────────────────────

async function _loadTab(project) {
  const body = document.getElementById('ent-body');
  if (!body) return;
  body.innerHTML = '<div style="padding:1rem;color:var(--muted)">Loading…</div>';

  try {
    if (_activeTab === 'features') {
      const { features } = await api.entities.listFeatures(project);
      _renderFeatures(body, features, project);
    } else if (_activeTab === 'tasks') {
      const { tasks } = await api.entities.listTasks(project);
      _renderTasks(body, tasks, project);
    } else if (_activeTab === 'bugs') {
      const { bugs } = await api.entities.listBugs(project);
      _renderBugs(body, bugs, project);
    }
  } catch (e) {
    body.innerHTML = `
      <div style="padding:1rem;color:var(--muted);text-align:center">
        <div style="font-size:1.5rem;margin-bottom:0.5rem">☁</div>
        <div>${e.message.includes('503') ? 'PostgreSQL required for entity tracking.' : e.message}</div>
        ${e.message.includes('503') ? '<div style="font-size:0.75rem;margin-top:0.5rem">Set DATABASE_URL to enable this feature.</div>' : ''}
      </div>`;
  }
}

// ── Features table ────────────────────────────────────────────────────────────

function _renderFeatures(container, features, project) {
  if (!features.length) {
    container.innerHTML = '<div style="padding:1rem;color:var(--muted);text-align:center">No features yet — click + Add</div>';
    return;
  }
  container.innerHTML = `
    <table class="entities-table">
      <thead>
        <tr>
          <th>Title</th><th>Status</th><th>Priority</th><th>Created</th><th></th>
        </tr>
      </thead>
      <tbody>
        ${features.map(f => `
          <tr>
            <td style="max-width:300px">
              <div style="font-weight:500;font-size:0.8rem">${_esc(f.title)}</div>
              ${f.description ? `<div style="color:var(--muted);font-size:0.7rem">${_esc(f.description.slice(0, 80))}</div>` : ''}
            </td>
            <td><span class="entities-badge status-${f.status}">${f.status}</span></td>
            <td><span class="entities-badge priority-${f.priority}">${f.priority}</span></td>
            <td style="color:var(--muted);font-size:0.7rem">${(f.created_at || '').slice(0, 10)}</td>
            <td>
              <button class="btn btn-ghost btn-sm" onclick="window._entEdit('feature','${f.id}')">Edit</button>
              <button class="btn btn-ghost btn-sm" style="color:var(--red)" onclick="window._entDelete('feature','${f.id}')">Del</button>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
  window._entEdit = (type, id) => _showEditModal(type, id, project);
  window._entDelete = (type, id) => _deleteEntity(type, id, project);
}

// ── Tasks table ───────────────────────────────────────────────────────────────

function _renderTasks(container, tasks, project) {
  if (!tasks.length) {
    container.innerHTML = '<div style="padding:1rem;color:var(--muted);text-align:center">No tasks yet — click + Add</div>';
    return;
  }
  container.innerHTML = `
    <table class="entities-table">
      <thead>
        <tr>
          <th>Title</th><th>Status</th><th>Priority</th><th>Assignee</th><th>Created</th><th></th>
        </tr>
      </thead>
      <tbody>
        ${tasks.map(t => `
          <tr>
            <td style="max-width:260px">
              <div style="font-weight:500;font-size:0.8rem">${_esc(t.title)}</div>
              ${t.description ? `<div style="color:var(--muted);font-size:0.7rem">${_esc(t.description.slice(0, 70))}</div>` : ''}
            </td>
            <td><span class="entities-badge status-${t.status}">${t.status}</span></td>
            <td><span class="entities-badge priority-${t.priority}">${t.priority}</span></td>
            <td style="font-size:0.75rem">${_esc(t.assignee || '—')}</td>
            <td style="color:var(--muted);font-size:0.7rem">${(t.created_at || '').slice(0, 10)}</td>
            <td>
              <button class="btn btn-ghost btn-sm" onclick="window._entEdit('task','${t.id}')">Edit</button>
              <button class="btn btn-ghost btn-sm" style="color:var(--red)" onclick="window._entDelete('task','${t.id}')">Del</button>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
  window._entEdit = (type, id) => _showEditModal(type, id, project);
  window._entDelete = (type, id) => _deleteEntity(type, id, project);
}

// ── Bugs table ────────────────────────────────────────────────────────────────

function _renderBugs(container, bugs, project) {
  if (!bugs.length) {
    container.innerHTML = '<div style="padding:1rem;color:var(--muted);text-align:center">No bugs reported — click + Add</div>';
    return;
  }
  container.innerHTML = `
    <table class="entities-table">
      <thead>
        <tr>
          <th>Title</th><th>Severity</th><th>Status</th><th>Created</th><th></th>
        </tr>
      </thead>
      <tbody>
        ${bugs.map(b => `
          <tr>
            <td style="max-width:300px">
              <div style="font-weight:500;font-size:0.8rem">${_esc(b.title)}</div>
              ${b.description ? `<div style="color:var(--muted);font-size:0.7rem">${_esc(b.description.slice(0, 70))}</div>` : ''}
            </td>
            <td><span class="entities-badge priority-${b.severity}">${b.severity}</span></td>
            <td><span class="entities-badge status-${b.status}">${b.status}</span></td>
            <td style="color:var(--muted);font-size:0.7rem">${(b.created_at || '').slice(0, 10)}</td>
            <td>
              <button class="btn btn-ghost btn-sm" onclick="window._entEdit('bug','${b.id}')">Edit</button>
              <button class="btn btn-ghost btn-sm" style="color:var(--red)" onclick="window._entDelete('bug','${b.id}')">Del</button>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;
  window._entEdit = (type, id) => _showEditModal(type, id, project);
  window._entDelete = (type, id) => _deleteEntity(type, id, project);
}

// ── Create modal ──────────────────────────────────────────────────────────────

function _showCreateModal(type, project) {
  const isFeature = type === 'features' || type === 'feature';
  const isTask = type === 'tasks' || type === 'task';
  const isBug = type === 'bugs' || type === 'bug';

  const typeLabel = isFeature ? 'Feature' : isTask ? 'Task' : 'Bug';

  const extraFields = isFeature ? `
    <label>Status</label>
    <select class="field-input" id="modal-ent-status">
      <option>proposed</option><option>active</option><option>done</option><option>cancelled</option>
    </select>
    <label>Priority</label>
    <select class="field-input" id="modal-ent-priority">
      <option>low</option><option selected>medium</option><option>high</option>
    </select>
  ` : isTask ? `
    <label>Status</label>
    <select class="field-input" id="modal-ent-status">
      <option selected>open</option><option>in_progress</option><option>done</option><option>cancelled</option>
    </select>
    <label>Priority</label>
    <select class="field-input" id="modal-ent-priority">
      <option>low</option><option selected>medium</option><option>high</option>
    </select>
    <label>Assignee</label>
    <input class="field-input" id="modal-ent-assignee" placeholder="optional" />
  ` : `
    <label>Severity</label>
    <select class="field-input" id="modal-ent-severity">
      <option>low</option><option selected>medium</option><option>high</option><option>critical</option>
    </select>
    <label>Status</label>
    <select class="field-input" id="modal-ent-status">
      <option selected>open</option><option>in_progress</option><option>closed</option>
    </select>
  `;

  const modal = _createModal(`
    <h3 style="margin-bottom:1rem;font-size:0.95rem">Add ${typeLabel}</h3>
    <div style="display:flex;flex-direction:column;gap:0.35rem">
      <label style="font-size:0.72rem;color:var(--muted)">Title *</label>
      <input class="field-input" id="modal-ent-title" placeholder="${typeLabel} title" />
      <label style="font-size:0.72rem;color:var(--muted)">Description</label>
      <textarea class="field-input" id="modal-ent-desc" rows="3" placeholder="Details…"></textarea>
      ${extraFields}
    </div>
    <div style="display:flex;gap:0.5rem;justify-content:flex-end;margin-top:1rem">
      <button class="btn btn-ghost btn-sm" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
      <button class="btn btn-primary btn-sm" id="modal-ent-save">Create</button>
    </div>
  `);

  modal.querySelector('#modal-ent-save').onclick = async () => {
    const title = modal.querySelector('#modal-ent-title')?.value.trim();
    if (!title) return toast('Title required', 'error');
    const desc = modal.querySelector('#modal-ent-desc')?.value || '';
    const status = modal.querySelector('#modal-ent-status')?.value || 'open';
    const priority = modal.querySelector('#modal-ent-priority')?.value || 'medium';
    const assignee = modal.querySelector('#modal-ent-assignee')?.value.trim() || null;
    const severity = modal.querySelector('#modal-ent-severity')?.value || 'medium';
    try {
      if (isFeature) {
        await api.entities.createFeature({ title, description: desc, status, priority, project });
      } else if (isTask) {
        await api.entities.createTask({ title, description: desc, status, priority, assignee, project });
      } else {
        await api.entities.createBug({ title, description: desc, status, severity, project });
      }
      modal.remove();
      toast('Created', 'success');
      _loadTab(project);
    } catch (e) {
      toast(`Failed: ${e.message}`, 'error');
    }
  };
}

// ── Edit modal ────────────────────────────────────────────────────────────────

async function _showEditModal(type, id, project) {
  // Fetch current entity
  try {
    let entity;
    if (type === 'feature') {
      const { features } = await api.entities.listFeatures(project);
      entity = features.find(f => f.id === id);
    } else if (type === 'task') {
      const { tasks } = await api.entities.listTasks(project);
      entity = tasks.find(t => t.id === id);
    } else {
      const { bugs } = await api.entities.listBugs(project);
      entity = bugs.find(b => b.id === id);
    }
    if (!entity) return toast('Not found', 'error');

    const typeLabel = type.charAt(0).toUpperCase() + type.slice(1);

    const modal = _createModal(`
      <h3 style="margin-bottom:1rem;font-size:0.95rem">Edit ${typeLabel}</h3>
      <div style="display:flex;flex-direction:column;gap:0.35rem">
        <label style="font-size:0.72rem;color:var(--muted)">Title</label>
        <input class="field-input" id="edit-ent-title" value="${_esc(entity.title || '')}" />
        <label style="font-size:0.72rem;color:var(--muted)">Description</label>
        <textarea class="field-input" id="edit-ent-desc" rows="3">${_esc(entity.description || '')}</textarea>
        <label style="font-size:0.72rem;color:var(--muted)">Status</label>
        <input class="field-input" id="edit-ent-status" value="${_esc(entity.status || '')}" />
        ${type !== 'bug' ? `
          <label style="font-size:0.72rem;color:var(--muted)">Priority</label>
          <select class="field-input" id="edit-ent-priority">
            ${['low','medium','high'].map(p => `<option ${entity.priority===p?'selected':''}>${p}</option>`).join('')}
          </select>
        ` : `
          <label style="font-size:0.72rem;color:var(--muted)">Severity</label>
          <select class="field-input" id="edit-ent-severity">
            ${['low','medium','high','critical'].map(s => `<option ${entity.severity===s?'selected':''}>${s}</option>`).join('')}
          </select>
        `}
      </div>
      <div style="display:flex;gap:0.5rem;justify-content:flex-end;margin-top:1rem">
        <button class="btn btn-ghost btn-sm" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
        <button class="btn btn-primary btn-sm" id="edit-ent-save">Save</button>
      </div>
    `);

    modal.querySelector('#edit-ent-save').onclick = async () => {
      const title = modal.querySelector('#edit-ent-title')?.value.trim();
      const desc = modal.querySelector('#edit-ent-desc')?.value || '';
      const status = modal.querySelector('#edit-ent-status')?.value.trim();
      const priority = modal.querySelector('#edit-ent-priority')?.value;
      const severity = modal.querySelector('#edit-ent-severity')?.value;
      try {
        const upd = { title, description: desc, status };
        if (priority) upd.priority = priority;
        if (severity) upd.severity = severity;
        if (type === 'feature') await api.entities.updateFeature(id, upd);
        else if (type === 'task') await api.entities.updateTask(id, upd);
        else await api.entities.updateBug(id, upd);
        modal.remove();
        toast('Saved', 'success');
        _loadTab(project);
      } catch (e) {
        toast(`Failed: ${e.message}`, 'error');
      }
    };
  } catch (e) {
    toast(`Load failed: ${e.message}`, 'error');
  }
}

// ── Delete ────────────────────────────────────────────────────────────────────

async function _deleteEntity(type, id, project) {
  if (!confirm(`Delete this ${type}?`)) return;
  try {
    if (type === 'feature') await api.entities.deleteFeature(id);
    else if (type === 'task') await api.entities.deleteTask(id);
    else await api.entities.deleteBug(id);
    toast('Deleted', 'success');
    _loadTab(project);
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _createModal(html) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.style.cssText = 'position:fixed;inset:0;z-index:9000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.5)';
  overlay.innerHTML = `
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);
                padding:1.5rem;min-width:360px;max-width:520px;width:90%;max-height:80vh;overflow-y:auto">
      ${html}
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
  return overlay;
}

function _esc(str) {
  return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
