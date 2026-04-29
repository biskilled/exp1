/**
 * mcp.js — MCP Catalog standalone view.
 *
 * Renders the full MCP catalog as a main nav view: cards for each server,
 * active/inactive state, activate/deactivate modals, add/edit catalog entries.
 * Navigating to "Used in roles" chips calls window._nav('prompts').
 */
import { api }   from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { state } from '../stores/state.js';

function _esc(s) {
  if (!s) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Entry point ───────────────────────────────────────────────────────────────

export async function renderMcpCatalog(container, project) {
  const proj = project || state.currentProject?.name || 'aicli';

  container.innerHTML = `
    <div style="padding:1.5rem;max-width:1100px">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:1.5rem;flex-wrap:wrap;gap:0.75rem">
        <div>
          <div style="font-size:1.1rem;font-weight:700;color:var(--text);margin-bottom:0.2rem">MCP Catalog</div>
          <div style="font-size:0.7rem;color:var(--muted)">
            Activate MCP servers for <strong>${_esc(proj)}</strong>.
            Active servers are written to <code>.mcp.json</code> in the project code directory.
          </div>
        </div>
        <button class="btn btn-primary btn-sm" onclick="window._mcpAddModal()">+ Add MCP</button>
      </div>
      <div id="mcp-cards-grid"
           style="display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:0.85rem">
        <div style="color:var(--muted);font-size:0.72rem">Loading…</div>
      </div>
    </div>
  `;

  _loadMcpCatalog(container, proj);
}

async function _loadMcpCatalog(container, proj) {
  let catalog = [], activeServers = new Set();
  try {
    const [catData, activeData] = await Promise.all([
      api.agentRoles.mcpCatalog(proj),
      api.agentRoles.mcpActive(proj).catch(() => ({ servers: [] })),
    ]);
    catalog       = catData.mcps || [];
    activeServers = new Set(activeData.servers || []);
  } catch (e) {
    const grid = container.querySelector('#mcp-cards-grid');
    if (grid) grid.innerHTML = `<div style="color:var(--red);font-size:0.72rem">${_esc(e.message)}</div>`;
    return;
  }

  // Wire globals — re-registered each load so closures stay fresh
  window._mcpActivate   = (name) => _mcpActivateModal(name, catalog, proj, container);
  window._mcpDeactivate = async (name) => {
    if (!confirm(`Deactivate MCP server "${name}"?`)) return;
    try {
      await api.agentRoles.mcpDeactivate(proj, name);
      toast(`MCP "${name}" deactivated`, 'success');
      _loadMcpCatalog(container, proj);
    } catch (e) { toast('Deactivate failed: ' + e.message, 'error'); }
  };
  window._mcpEditModal = (name) => _mcpEditModal(name, catalog, proj, container);
  window._mcpAddModal  = ()     => _mcpEditModal(null,  catalog, proj, container);

  _renderCards(container, catalog, activeServers, proj);
}

// ── Cards grid ────────────────────────────────────────────────────────────────

function _renderCards(container, catalog, activeServers, proj) {
  const grid = container.querySelector('#mcp-cards-grid');
  if (!grid) return;

  if (!catalog.length) {
    grid.innerHTML = `<div style="color:var(--muted);font-size:0.72rem">
      No MCPs in catalog — click <strong>+ Add MCP</strong> to add one.</div>`;
    return;
  }

  grid.innerHTML = catalog.map(mcp => {
    const isActive = activeServers.has(mcp.name);
    const accentCol = isActive ? '#4ade80' : 'rgba(255,255,255,0.2)';
    const tags = (mcp.tags || []).map(t =>
      `<span style="display:inline-block;padding:0.1rem 0.35rem;border-radius:10px;
                    font-size:0.55rem;background:var(--surface3);color:var(--muted);
                    margin:0.1rem 0.1rem 0">${_esc(t)}</span>`
    ).join('');
    return `
      <div style="border:1px solid var(--border);border-radius:8px;background:var(--surface);
                  padding:0.85rem;display:flex;flex-direction:column;gap:0.45rem;
                  border-top:2px solid ${isActive ? '#4ade80' : 'var(--border)'}">
        <div style="display:flex;align-items:center;gap:0.5rem">
          <span style="width:8px;height:8px;border-radius:50%;background:${accentCol};flex-shrink:0"></span>
          <span style="font-size:0.8rem;font-weight:600;color:var(--text);
                       flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                title="${_esc(mcp.label || mcp.name)}">${_esc(mcp.label || mcp.name)}</span>
          ${isActive ? `<span style="font-size:0.52rem;font-weight:700;color:#4ade80;
                                     text-transform:uppercase;letter-spacing:0.07em;flex-shrink:0">ACTIVE</span>` : ''}
        </div>
        <div style="font-size:0.65rem;color:var(--muted);line-height:1.5;flex:1">${_esc(mcp.description || '')}</div>
        <div>${tags}</div>
        <div id="mcp-usage-${_esc(mcp.name)}" style="font-size:0.6rem;color:var(--muted);min-height:1rem">
          <span style="opacity:0.4">checking roles…</span>
        </div>
        <div style="display:flex;gap:0.4rem;margin-top:0.15rem">
          <button class="btn btn-ghost btn-sm" style="font-size:0.6rem"
                  onclick="window._mcpEditModal('${_esc(mcp.name)}')">Edit</button>
          ${isActive
            ? `<button class="btn btn-ghost btn-sm"
                       style="font-size:0.6rem;color:var(--red);border-color:var(--red)"
                       onclick="window._mcpDeactivate('${_esc(mcp.name)}')">Deactivate</button>`
            : `<button class="btn btn-primary btn-sm" style="font-size:0.6rem"
                       onclick="window._mcpActivate('${_esc(mcp.name)}')">Activate</button>`
          }
        </div>
      </div>`;
  }).join('');

  // Async-load role usage per card
  catalog.forEach(mcp => {
    api.agentRoles.mcpUsage(proj, mcp.name).then(data => {
      const el = grid.querySelector(`#mcp-usage-${CSS.escape(mcp.name)}`);
      if (!el) return;
      const roles = data.roles || [];
      if (!roles.length) { el.innerHTML = ''; return; }
      el.innerHTML = `<span style="opacity:0.55">Used in: </span>` +
        roles.map(r =>
          `<span onclick="window._nav('prompts')"
                 style="display:inline-block;padding:0.1rem 0.35rem;border-radius:8px;
                        font-size:0.6rem;background:rgba(100,108,255,0.15);
                        color:var(--accent);cursor:pointer;margin:0.05rem"
                 title="Go to Roles">${_esc(r.name)}</span>`
        ).join('');
    }).catch(() => {
      const el = grid.querySelector(`#mcp-usage-${CSS.escape(mcp.name)}`);
      if (el) el.innerHTML = '';
    });
  });
}

// ── Activate modal ────────────────────────────────────────────────────────────

function _mcpActivateModal(name, catalog, proj, container) {
  const mcp = catalog.find(m => m.name === name);
  if (!mcp) return;
  const defaultCmd  = (mcp.install || '').split(' ')[0] || 'npx';
  const defaultArgs = (mcp.install || '').split(' ').slice(1).join(' ');

  const overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;z-index:9000;background:rgba(0,0,0,0.72);backdrop-filter:blur(2px);display:flex;align-items:center;justify-content:center';
  overlay.innerHTML = `
    <div style="background:#1e2130;border:1px solid rgba(255,255,255,0.14);border-radius:10px;
                padding:1.5rem;min-width:340px;max-width:480px;box-shadow:0 24px 64px rgba(0,0,0,0.7)">
      <div style="font-size:0.95rem;font-weight:700;margin-bottom:0.15rem;color:#fff">Activate: ${_esc(mcp.label || mcp.name)}</div>
      <div style="font-size:0.65rem;color:rgba(255,255,255,0.4);margin-bottom:1rem">${_esc(mcp.description || '')}</div>

      <label style="display:block;font-size:0.63rem;color:rgba(255,255,255,0.5);margin-bottom:0.2rem;text-transform:uppercase;letter-spacing:0.05em">Command</label>
      <input id="_mcp-cmd" value="${_esc(defaultCmd)}" placeholder="npx"
        style="width:100%;box-sizing:border-box;padding:0.45rem 0.6rem;border:1px solid rgba(255,255,255,0.18);
               border-radius:6px;background:rgba(255,255,255,0.06);color:#fff;font-size:0.82rem;outline:none;margin-bottom:0.75rem">

      <label style="display:block;font-size:0.63rem;color:rgba(255,255,255,0.5);margin-bottom:0.2rem;text-transform:uppercase;letter-spacing:0.05em">Args (space-separated)</label>
      <input id="_mcp-args" value="${_esc(defaultArgs)}"
        style="width:100%;box-sizing:border-box;padding:0.45rem 0.6rem;border:1px solid rgba(255,255,255,0.18);
               border-radius:6px;background:rgba(255,255,255,0.06);color:#fff;font-size:0.82rem;outline:none;margin-bottom:0.75rem">

      <div style="font-size:0.6rem;color:rgba(255,255,255,0.3);margin-bottom:1rem">
        Hint: <code style="opacity:0.8">${_esc(mcp.install || '')}</code>
      </div>
      <div style="display:flex;justify-content:flex-end;gap:0.5rem;padding-top:0.75rem;border-top:1px solid rgba(255,255,255,0.08)">
        <button id="_mcp-cancel" class="btn btn-ghost btn-sm">Cancel</button>
        <button id="_mcp-ok"     class="btn btn-primary btn-sm">Activate</button>
      </div>
    </div>`;

  document.body.appendChild(overlay);
  const close = () => overlay.remove();
  overlay.querySelector('#_mcp-cancel').onclick = close;
  overlay.onclick = e => { if (e.target === overlay) close(); };
  overlay.querySelector('#_mcp-ok').onclick = async () => {
    const command = overlay.querySelector('#_mcp-cmd').value.trim();
    const argsRaw = overlay.querySelector('#_mcp-args').value.trim();
    const args    = argsRaw ? argsRaw.split(/\s+/) : [];
    if (!command) { toast('Command is required', 'error'); return; }
    try {
      await api.agentRoles.mcpActivate(proj, { name, command, args });
      toast(`MCP "${name}" activated`, 'success');
      close();
      _loadMcpCatalog(container, proj);
    } catch (e) { toast('Activate failed: ' + e.message, 'error'); }
  };
}

// ── Add / Edit modal ──────────────────────────────────────────────────────────

function _mcpEditModal(existingName, catalog, proj, container) {
  const mcp = existingName ? catalog.find(m => m.name === existingName) : null;

  const overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;z-index:9000;background:rgba(0,0,0,0.72);backdrop-filter:blur(2px);display:flex;align-items:center;justify-content:center';
  overlay.innerHTML = `
    <div style="background:#1e2130;border:1px solid rgba(255,255,255,0.14);border-radius:10px;
                padding:1.5rem;min-width:380px;max-width:520px;box-shadow:0 24px 64px rgba(0,0,0,0.7);
                max-height:90vh;overflow-y:auto">
      <div style="font-size:0.95rem;font-weight:700;margin-bottom:1rem;color:#fff">${mcp ? 'Edit MCP' : 'Add MCP'}</div>
      ${[
        ['name',         'Name (unique id)',        mcp?.name        || '', 'e.g. my-server'       ],
        ['label',        'Label',                   mcp?.label       || '', 'Display name'          ],
        ['description',  'Description',             mcp?.description || '', 'What this MCP does'    ],
        ['url',          'URL / Docs',              mcp?.url         || '', 'https://...'           ],
        ['install',      'Install command',         mcp?.install     || '', 'npx @org/mcp-server'   ],
        ['tags',         'Tags (comma-separated)',  (mcp?.tags          || []).join(', '), 'e.g. aws, cloud'  ],
        ['project_types','Project types (comma-sep)',(mcp?.project_types || []).join(', '), 'e.g. backend, devops'],
      ].map(([id, lbl, val, ph]) => `
        <label style="display:block;font-size:0.63rem;color:rgba(255,255,255,0.5);margin-bottom:0.2rem;
                       text-transform:uppercase;letter-spacing:0.05em">${lbl}</label>
        <input id="_mcp-edit-${id}" value="${_esc(val)}" placeholder="${_esc(ph)}"
          style="width:100%;box-sizing:border-box;padding:0.4rem 0.55rem;
                 border:1px solid rgba(255,255,255,0.18);border-radius:6px;
                 background:rgba(255,255,255,0.06);color:#fff;font-size:0.78rem;
                 outline:none;margin-bottom:0.7rem">`
      ).join('')}
      <label style="display:block;font-size:0.63rem;color:rgba(255,255,255,0.5);margin-bottom:0.2rem;
                     text-transform:uppercase;letter-spacing:0.05em">Type</label>
      <select id="_mcp-edit-type"
        style="width:100%;padding:0.4rem 0.55rem;border:1px solid rgba(255,255,255,0.18);
               border-radius:6px;background:#1e2130;color:#fff;font-size:0.78rem;
               outline:none;margin-bottom:1rem">
        <option value="stdio" ${(mcp?.type||'stdio')==='stdio'?'selected':''}>stdio</option>
        <option value="http"  ${mcp?.type==='http'?'selected':''}>http</option>
      </select>
      <div style="display:flex;justify-content:flex-end;gap:0.5rem;padding-top:0.75rem;border-top:1px solid rgba(255,255,255,0.08)">
        <button id="_mcp-edit-cancel" class="btn btn-ghost btn-sm">Cancel</button>
        <button id="_mcp-edit-save"   class="btn btn-primary btn-sm">Save</button>
      </div>
    </div>`;

  document.body.appendChild(overlay);
  const close = () => overlay.remove();
  overlay.querySelector('#_mcp-edit-cancel').onclick = close;
  overlay.onclick = e => { if (e.target === overlay) close(); };

  overlay.querySelector('#_mcp-edit-save').onclick = async () => {
    const get   = id => overlay.querySelector(`#_mcp-edit-${id}`)?.value?.trim() || '';
    const entry = {
      name:          get('name'),
      label:         get('label'),
      description:   get('description'),
      url:           get('url'),
      install:       get('install'),
      type:          overlay.querySelector('#_mcp-edit-type')?.value || 'stdio',
      tags:          get('tags').split(',').map(s => s.trim()).filter(Boolean),
      project_types: get('project_types').split(',').map(s => s.trim()).filter(Boolean),
    };
    if (!entry.name) { toast('Name is required', 'error'); return; }
    const updated = existingName
      ? catalog.map(m => m.name === existingName ? entry : m)
      : [...catalog, entry];
    try {
      await api.agentRoles.mcpCatalogSave(proj, { mcps: updated });
      toast(existingName ? 'MCP updated' : 'MCP added', 'success');
      close();
      _loadMcpCatalog(container, proj);
    } catch (e) { toast('Save failed: ' + e.message, 'error'); }
  };
}
