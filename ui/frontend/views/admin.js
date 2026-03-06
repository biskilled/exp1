/**
 * Admin panel — user management table.
 * Only accessible to users with is_admin: true.
 */

import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { state } from '../stores/state.js';

export async function renderAdmin(container) {
  container.className = 'view active';
  container.style.cssText = 'display:flex;flex-direction:column;overflow:hidden;height:100%';

  container.innerHTML = `
    <div style="flex:1;display:flex;flex-direction:column;overflow:hidden">
      <div style="padding:1rem 1.25rem;border-bottom:1px solid var(--border);
                  display:flex;align-items:center;gap:0.75rem;flex-shrink:0">
        <span style="font-size:0.8rem;font-weight:600;color:var(--text)">Admin — User Management</span>
        <span style="font-size:0.65rem;color:var(--muted)">
          ${state.db_mode === 'postgresql' ? '🐘 PostgreSQL' : '📄 file store'}
        </span>
        <div style="flex:1"></div>
        <button class="btn btn-ghost btn-sm" onclick="window._adminRefresh()">↻ Refresh</button>
      </div>
      <div id="admin-body" style="flex:1;overflow-y:auto;padding:1rem 1.25rem"></div>
    </div>
  `;

  window._adminRefresh = () => _loadUsers();
  await _loadUsers();
}

async function _loadUsers() {
  const body = document.getElementById('admin-body');
  if (!body) return;
  body.innerHTML = '<div style="color:var(--muted);font-size:0.72rem">Loading…</div>';

  try {
    const data  = await api.adminListUsers();
    const users = data.users || [];

    if (!users.length) {
      body.innerHTML = '<div class="empty-state"><p>No users yet.</p></div>';
      return;
    }

    const myId = state.user?.id || '';

    body.innerHTML = `
      <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.75rem">
        ${users.length} user${users.length !== 1 ? 's' : ''} registered
      </div>
      <table style="width:100%;border-collapse:collapse;font-size:0.72rem">
        <thead>
          <tr style="text-align:left;border-bottom:2px solid var(--border)">
            <th style="padding:6px 8px;color:var(--muted);font-weight:500">Email</th>
            <th style="padding:6px 8px;color:var(--muted);font-weight:500">Role</th>
            <th style="padding:6px 8px;color:var(--muted);font-weight:500">Status</th>
            <th style="padding:6px 8px;color:var(--muted);font-weight:500">Created</th>
            <th style="padding:6px 8px;color:var(--muted);font-weight:500">Last login</th>
            <th style="padding:6px 8px;color:var(--muted);font-weight:500">API calls</th>
            <th style="padding:6px 8px;color:var(--muted);font-weight:500">Cost USD</th>
            <th style="padding:6px 8px;color:var(--muted);font-weight:500">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${users.map(u => _userRow(u, myId)).join('')}
        </tbody>
      </table>
    `;
  } catch (e) {
    body.innerHTML = `<div style="color:var(--red);font-size:0.72rem;padding:1rem">
      Error: ${_esc(e.message)}<br>
      <small style="color:var(--muted)">Make sure you are logged in as an admin user.</small>
    </div>`;
  }
}

function _userRow(u, myId) {
  const isMe    = u.id === myId;
  const isAdmin = u.is_admin;
  const active  = u.is_active !== false;
  const created = u.created_at?.slice(0, 10) || '—';
  const lastLogin = u.last_login?.slice(0, 16).replace('T', ' ') || '—';
  const usage   = u.usage || {};

  return `
    <tr style="border-bottom:1px solid var(--border);opacity:${active ? 1 : 0.5}"
        id="user-row-${u.id}">
      <td style="padding:8px">
        <span style="color:var(--text)">${_esc(u.email)}</span>
        ${isMe ? '<span style="font-size:0.6rem;color:var(--accent);margin-left:4px">(you)</span>' : ''}
      </td>
      <td style="padding:8px">
        <span style="padding:2px 8px;border-radius:10px;font-size:0.62rem;
               background:${isAdmin ? 'var(--accent)' : 'var(--surface2)'};
               color:${isAdmin ? '#fff' : 'var(--text2)'}">
          ${isAdmin ? 'admin' : 'user'}
        </span>
      </td>
      <td style="padding:8px">
        <span style="color:${active ? 'var(--green)' : 'var(--red)'}">
          ${active ? '● active' : '○ inactive'}
        </span>
      </td>
      <td style="padding:8px;color:var(--text2)">${created}</td>
      <td style="padding:8px;color:var(--text2)">${lastLogin}</td>
      <td style="padding:8px;color:var(--text2)">${usage.total_calls ?? 0}</td>
      <td style="padding:8px;color:var(--text2)">$${(usage.total_cost_usd ?? 0).toFixed(4)}</td>
      <td style="padding:8px">
        ${!isMe ? `
          <div style="display:flex;gap:4px">
            <button class="btn btn-ghost btn-sm"
              onclick="window._adminToggleAdmin('${u.id}', ${!isAdmin})"
              title="${isAdmin ? 'Remove admin' : 'Make admin'}">
              ${isAdmin ? '↓ user' : '↑ admin'}
            </button>
            <button class="btn btn-ghost btn-sm"
              style="color:${active ? 'var(--red)' : 'var(--green)'}"
              onclick="window._adminToggleActive('${u.id}', ${!active})">
              ${active ? 'Deactivate' : 'Reactivate'}
            </button>
          </div>
        ` : '<span style="color:var(--muted);font-size:0.62rem">—</span>'}
      </td>
    </tr>
  `;
}

window._adminToggleAdmin = async (userId, makeAdmin) => {
  try {
    await api.adminPatchUser(userId, { is_admin: makeAdmin });
    toast(`User ${makeAdmin ? 'promoted to admin' : 'set to user'}`, 'success');
    await _loadUsers();
  } catch (e) {
    toast(`Error: ${e.message}`, 'error');
  }
};

window._adminToggleActive = async (userId, activate) => {
  const verb = activate ? 'reactivate' : 'deactivate';
  if (!confirm(`${verb.charAt(0).toUpperCase() + verb.slice(1)} this user?`)) return;
  try {
    if (activate) {
      await api.adminPatchUser(userId, { is_active: true });
    } else {
      await api.adminDeleteUser(userId);
    }
    toast(`User ${verb}d`, 'success');
    await _loadUsers();
  } catch (e) {
    toast(`Error: ${e.message}`, 'error');
  }
};

function _esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
