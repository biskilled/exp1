/**
 * prompts.js — Roles tab: DB-backed agent role editor and workspace prompt file browser.
 *
 * Two-panel layout: left sidebar lists Agent Roles (DB) and Prompt Files (workspace markdown);
 * right panel shows the selected role form (system prompt, provider, model, IO schema) or
 * file editor with live markdown preview and save/delete actions.
 * Rendered via: renderPrompts() called from main.js navigateTo().
 */
import { api }      from '../utils/api.js';
import { toast }    from '../utils/toast.js';
import { renderMd } from '../utils/markdown.js';

// ── State ─────────────────────────────────────────────────────────────────────
let _activeFile    = '';
let _fileOrig      = '';
let _editMode      = false;
let _activeRole    = null;   // {id, name, provider, model, description, system_prompt, ...}
let _roles         = [];
let _project       = null;
let _isAdmin       = false;
let _systemRoles   = [];     // all available system roles loaded once at tab init
let _roleLinks     = {};     // {roleId: [{id, name, category, order_index}]}
let _activeSysRole = null;   // system role being edited (admin panel)

function _promptModal(title, label, placeholder = '') {
  return new Promise(resolve => {
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;z-index:9000;background:rgba(0,0,0,0.72);backdrop-filter:blur(2px);display:flex;align-items:center;justify-content:center';
    const box = document.createElement('div');
    box.style.cssText = 'background:#1e2130;border:1px solid rgba(255,255,255,0.14);border-radius:10px;padding:1.5rem;min-width:320px;box-shadow:0 24px 64px rgba(0,0,0,0.7)';
    box.innerHTML = `
      <div style="font-size:0.95rem;font-weight:700;margin-bottom:0.75rem;color:#fff">${title}</div>
      <label style="display:block;font-size:0.7rem;color:rgba(255,255,255,0.5);margin-bottom:0.3rem;text-transform:uppercase;letter-spacing:0.05em">${label}</label>
      <input id="_pm-input" type="text" value="" placeholder="${placeholder}"
        style="width:100%;box-sizing:border-box;padding:0.5rem 0.6rem;border:1px solid rgba(255,255,255,0.18);border-radius:6px;background:rgba(255,255,255,0.07);color:#fff;font-size:0.84rem;outline:none">
      <div style="display:flex;justify-content:flex-end;gap:0.5rem;margin-top:1rem;padding-top:0.75rem;border-top:1px solid rgba(255,255,255,0.08)">
        <button id="_pm-cancel" class="btn btn-ghost btn-sm">Cancel</button>
        <button id="_pm-ok" class="btn btn-primary btn-sm">Create</button>
      </div>`;
    overlay.appendChild(box);
    document.body.appendChild(overlay);
    const inp = box.querySelector('#_pm-input');
    setTimeout(() => { inp.focus(); inp.select(); }, 0);
    const close = v => { overlay.remove(); resolve(v); };
    box.querySelector('#_pm-cancel').onclick = () => close(null);
    box.querySelector('#_pm-ok').onclick = () => close(inp.value);
    box.addEventListener('keydown', e => {
      if (e.key === 'Enter') close(inp.value);
      if (e.key === 'Escape') close(null);
    });
    overlay.onclick = e => { if (e.target === overlay) close(null); };
  });
}

// Providers loaded from /agent-roles/providers (backed by backend/prompts/providers.yaml).
// Fallback used only if the API call fails on first load.
let _providers = [];
const _PROVIDERS_FALLBACK = [
  { id: 'claude',   label: 'Claude API',    models: ['claude-sonnet-4-6', 'claude-haiku-4-5-20251001', 'claude-opus-4-6'] },
  { id: 'openai',   label: 'OpenAI API',    models: ['gpt-4o', 'gpt-4o-mini'] },
  { id: 'deepseek', label: 'DeepSeek Cloud',models: ['deepseek-chat', 'deepseek-coder'] },
  { id: 'gemini',   label: 'Gemini API',    models: ['gemini-1.5-pro', 'gemini-1.5-flash'] },
  { id: 'grok',     label: 'Grok API',      models: ['grok-2-latest'] },
];

async function _loadProviders() {
  try {
    const data = await api.agentRoles.providers();
    if (data?.providers?.length) _providers = data.providers;
  } catch (_) { /* use fallback */ }
  if (!_providers.length) _providers = _PROVIDERS_FALLBACK;
}

function _providerModels(providerId) {
  const p = _providers.find(x => x.id === providerId);
  return p?.models || [];
}

// ── Entry point ───────────────────────────────────────────────────────────────

export async function renderPrompts(container, projectName) {
  _activeFile    = '';
  _fileOrig      = '';
  _editMode      = false;
  _activeRole    = null;
  _activeSysRole = null;
  _project       = projectName;
  _isAdmin       = false;
  _systemRoles   = [];
  _roleLinks     = {};

  const savedW = parseInt(localStorage.getItem('aicli_prompts_tree_w') || '220', 10);

  container.className  = 'view active';
  container.style.cssText = 'display:flex;flex-direction:column;overflow:hidden;height:100%';

  container.innerHTML = `
    <div class="prompts-view" style="flex:1;overflow:hidden">
      <!-- Left panel -->
      <div class="prompts-tree" id="prompts-tree-panel" style="width:${savedW}px;display:flex;flex-direction:column">

        <!-- Agent Roles section (top, takes most space) -->
        <div class="prompts-tree-header" style="flex-shrink:0">
          <span class="prompts-tree-label">Agent Roles</span>
          <button class="btn btn-ghost btn-sm" style="padding:0.15rem 0.4rem;font-size:0.65rem"
            onclick="window._rolesNew()" title="New agent role">+</button>
        </div>
        <div id="roles-list-body" style="overflow-y:auto;flex:1;min-height:120px;border-bottom:1px solid var(--border)">
          <div style="padding:1rem;font-size:0.68rem;color:var(--muted)">Loading…</div>
        </div>

        <!-- System Roles section (bottom) -->
        <div id="sys-roles-section" style="display:flex;flex-shrink:0;flex-direction:column;max-height:35%">
          <div class="prompts-tree-header" style="flex-shrink:0">
            <span class="prompts-tree-label" style="font-size:0.62rem">System Roles</span>
            <button id="sys-roles-new-btn" class="btn btn-ghost btn-sm"
              style="padding:0.12rem 0.35rem;font-size:0.6rem;display:none"
              onclick="window._sysRolesNew()" title="New system role">+</button>
          </div>
          <div id="sys-roles-list-body" style="overflow-y:auto;flex:1">
            <div style="padding:1rem;font-size:0.68rem;color:var(--muted)">Loading…</div>
          </div>
        </div>

      </div>

      <!-- Resize handle -->
      <div id="prompts-resize-handle"
           style="width:4px;cursor:col-resize;background:var(--border);flex-shrink:0"
           title="Drag to resize"></div>

      <!-- Right panel -->
      <div class="prompts-editor-area">
        <div class="prompts-editor-toolbar" id="prompts-toolbar">
          <span class="prompts-editor-path" id="prompts-path">Select a role or file</span>
        </div>
        <div id="prompts-editor-body"
          style="flex:1;display:flex;align-items:center;justify-content:center;
                 color:var(--muted);font-size:0.72rem">
          <span>Select a role or file from the left panel</span>
        </div>
      </div>
    </div>
  `;

  // Wire globals
  window._rolesNew            = _rolesNew;
  window._rolesSelect         = _rolesSelect;
  window._rolesDelete         = _rolesDelete;
  window._rolesSave           = _rolesSave;
  window._rolesExportYaml     = _rolesExportYaml;
  window._rolesEditYaml       = _rolesEditYaml;
  window._rolesProviderChange = _rolesProviderChange;
  window._sysRolesNew         = _sysRolesNew;
  window._sysRolesSelect      = _sysRolesSelect;
  window._sysRolesSave        = _sysRolesSave;
  window._sysRolesDelete      = _sysRolesDelete;
  window._sysRolesAttach      = _sysRolesAttach;
  window._sysRolesDetach      = _sysRolesDetach;

  _initPromptsResize();

  if (!projectName) {
    document.getElementById('roles-list-body').innerHTML =
      '<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--muted)">No project open</div>';
    return;
  }

  await _loadRoles(projectName);
}

// ── Agent Roles (DB) ──────────────────────────────────────────────────────────

async function _loadRoles(projectName) {
  const body = document.getElementById('roles-list-body');
  if (!body) return;
  try {
    const [rolesData, sysData] = await Promise.all([
      api.agentRoles.list(projectName || '_global'),
      api.systemRoles.list().catch(() => ({ system_roles: [], is_admin: false })),
      _loadProviders(),
    ]);
    _roles       = rolesData.roles || rolesData || [];
    _isAdmin     = rolesData.is_admin || sysData.is_admin || false;
    _systemRoles = sysData.system_roles || [];

    // Always show system roles section; gate write controls via _isAdmin
    const sysSection   = document.getElementById('sys-roles-section');
    const sysNewBtn    = document.getElementById('sys-roles-new-btn');
    if (sysSection) sysSection.style.display = 'flex';
    if (sysNewBtn)  sysNewBtn.style.display  = _isAdmin ? '' : 'none';

    _renderRolesList();
    _renderSysRolesList();
  } catch (e) {
    body.innerHTML = `<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--red)">${_esc(e.message)}</div>`;
  }
}

function _renderRoleItem(r) {
  const isActive = _activeRole?.id === r.id;
  return `
    <div onclick="window._rolesSelect(${r.id})"
         style="padding:0.4rem 0.75rem;cursor:pointer;border-bottom:1px solid var(--border);
                display:flex;align-items:center;gap:0.5rem;
                background:${isActive ? 'rgba(100,108,255,0.1)' : 'transparent'};
                border-left:2px solid ${isActive ? 'var(--accent)' : 'transparent'}"
         onmouseenter="this.style.background='${isActive ? 'rgba(100,108,255,0.1)' : 'var(--surface2)'}'"
         onmouseleave="this.style.background='${isActive ? 'rgba(100,108,255,0.1)' : 'transparent'}'">
      <div style="flex:1;min-width:0">
        <div style="font-size:0.7rem;font-weight:500;color:var(--text);
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(r.name)}</div>
        <div style="font-size:0.55rem;color:var(--muted)">${_esc(r.provider || '')} ${r.model ? '· ' + _esc(r.model) : ''}</div>
      </div>
    </div>`;
}

function _renderRolesList() {
  const body = document.getElementById('roles-list-body');
  if (!body) return;
  if (!_roles.length) {
    body.innerHTML = `<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--muted)">
      No roles yet — click <strong>+</strong> to create one</div>`;
    return;
  }
  body.innerHTML = _roles.map(_renderRoleItem).join('');
}

async function _rolesNew() {
  const name = await _promptModal('New Agent Role', 'Role name (e.g. "Senior Developer"):', 'My Role');
  if (!name?.trim()) return;
  try {
    const r = await api.agentRoles.create({
      name: name.trim(), provider: 'anthropic',
      model: 'claude-haiku-4-5-20251001', description: '', system_prompt: '',
      project: _project || '_global',
    });
    _roles.push(r);
    _renderRolesList();
    _rolesSelect(r.id);
    toast(`Role "${name}" created`, 'success');
  } catch (e) { toast('Create failed: ' + e.message, 'error'); }
}

async function _rolesSelect(id) {
  _activeFile    = '';
  _activeSysRole = null;
  const role = _roles.find(r => r.id === id);
  if (!role) return;
  _activeRole = role;
  _renderRolesList();
  _renderRoleEditor(role);
  const pathEl = document.getElementById('prompts-path');
  if (pathEl) pathEl.textContent = `Role: ${role.name}`;

  // Load available tools and render checkboxes
  _loadRoleTools(role);

  // Load linked system roles
  try {
    const data = await api.systemRoles.listLinks(id);
    _roleLinks[id] = data.links || [];
  } catch (_) {
    _roleLinks[id] = [];
  }
  _renderRoleSystemRolesSection(id);
}

async function _loadRoleTools(role) {
  const grid = document.getElementById('role-tools-grid');
  if (!grid) return;
  let allTools = [];
  try {
    const data = await api.agentRoles.availableTools();
    allTools = data.tools || [];
  } catch (_) {
    grid.innerHTML = '<div style="font-size:0.65rem;color:var(--muted)">Tools unavailable</div>';
    return;
  }
  const enabled = new Set(role.tools || []);
  const byCategory = {};
  for (const t of allTools) {
    if (!byCategory[t.category]) byCategory[t.category] = [];
    byCategory[t.category].push(t);
  }
  const catColors = { git: '#e8834e', file: '#5b8af5', memory: '#9b7ef8', work_items: '#4ec9a6', other: '#888' };
  let html = '';
  for (const [cat, tools] of Object.entries(byCategory)) {
    const col = catColors[cat] || '#888';
    html += tools.map(t => `
      <label style="display:flex;align-items:center;gap:0.35rem;cursor:pointer;
                    padding:0.2rem 0.4rem;border-radius:4px;border:1px solid var(--border);
                    background:var(--surface2);font-size:0.65rem;color:var(--text)">
        <input type="checkbox" value="${t.name}" ${enabled.has(t.name) ? 'checked' : ''}
          style="width:12px;height:12px;accent-color:${col};cursor:pointer">
        <span style="color:${col};font-size:0.55rem;font-weight:600;text-transform:uppercase">${cat}</span>
        <span>${t.name}</span>
      </label>`).join('');
  }
  grid.innerHTML = html || '<div style="font-size:0.65rem;color:var(--muted)">No tools registered</div>';
}

function _renderRoleSystemRolesSection(roleId) {
  const container = document.getElementById('role-sys-roles-list');
  if (!container) return;
  const links = _roleLinks[roleId] || [];

  if (!_isAdmin) {
    // Read-only: name chips
    if (!links.length) {
      container.innerHTML = `<div style="font-size:0.65rem;color:var(--muted)">No system roles attached</div>`;
      return;
    }
    container.innerHTML = links.map(l => `
      <span style="display:inline-flex;align-items:center;gap:0.3rem;
                   background:var(--surface2);border:1px solid var(--border);
                   border-radius:var(--radius);padding:0.2rem 0.5rem;
                   font-size:0.65rem;color:var(--text)">
        ${_esc(l.name)}
        <span style="font-size:0.55rem;opacity:0.6">[${_esc(l.category)}]</span>
      </span>
    `).join('');
    return;
  }

  // Admin: ordered list with remove + add dropdown
  const attachedIds = new Set(links.map(l => l.id));
  const available   = _systemRoles.filter(sr => !attachedIds.has(sr.id));

  let html = '';
  if (links.length) {
    html += links.map(l => `
      <div style="display:flex;align-items:center;gap:0.5rem;
                  background:var(--surface2);border:1px solid var(--border);
                  border-radius:var(--radius);padding:0.3rem 0.6rem;
                  font-size:0.68rem">
        <span style="color:var(--muted);cursor:default" title="Drag to reorder">⠿</span>
        <span style="flex:1;color:var(--text)">${_esc(l.name)}</span>
        <span style="font-size:0.55rem;padding:0.1rem 0.35rem;background:var(--surface3);
                     border-radius:3px;color:var(--muted)">${_esc(l.category)}</span>
        <button onclick="window._sysRolesDetach(${roleId},${l.id})"
          style="background:none;border:none;cursor:pointer;color:var(--muted);
                 font-size:0.8rem;padding:0 0.2rem;line-height:1" title="Remove">×</button>
      </div>
    `).join('');
  } else {
    html += `<div style="font-size:0.65rem;color:var(--muted)">No system roles attached</div>`;
  }

  if (available.length) {
    html += `
      <div style="display:flex;gap:0.4rem;margin-top:0.3rem">
        <select id="sys-role-add-select"
          style="flex:1;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.65rem;
                 padding:0.25rem 0.4rem;border-radius:var(--radius);outline:none">
          <option value="">─ add a system role ─</option>
          ${available.map(sr => `<option value="${sr.id}">${_esc(sr.name)} [${_esc(sr.category)}]</option>`).join('')}
        </select>
        <button class="btn btn-ghost btn-sm" onclick="window._sysRolesAttach(${roleId})"
          style="font-size:0.62rem;white-space:nowrap">Add</button>
      </div>
    `;
  }

  container.innerHTML = html;
}

function _renderRoleEditor(role) {
  const body    = document.getElementById('prompts-editor-body');
  const toolbar = document.getElementById('prompts-toolbar');
  if (!body) return;

  // Toolbar — use event listeners to avoid onclick attribute quoting issues
  if (toolbar) {
    toolbar.innerHTML = `
      <span class="prompts-editor-path" id="prompts-path">Role: ${_esc(role.name)}</span>
      <button id="roles-delete-btn" class="btn btn-ghost btn-sm" style="color:var(--red);border-color:var(--red);font-size:0.62rem">Delete</button>
      <button id="roles-edit-yaml-btn" class="btn btn-ghost btn-sm" style="font-size:0.62rem">Edit YAML</button>
      <button id="roles-export-yaml-btn" class="btn btn-ghost btn-sm" style="font-size:0.62rem">↓ YAML</button>
      <button id="roles-save-btn" class="btn btn-primary btn-sm">Save</button>
    `;
    toolbar.querySelector('#roles-delete-btn').addEventListener('click', () => _rolesDelete(role.id));
    toolbar.querySelector('#roles-edit-yaml-btn').addEventListener('click', () => _rolesEditYaml(role));
    toolbar.querySelector('#roles-export-yaml-btn').addEventListener('click', () => _rolesExportYaml(role.id, role.name));
    toolbar.querySelector('#roles-save-btn').addEventListener('click', () => _rolesSave(role.id));
  }

  // Provider options from loaded providers list
  const providerOpts = _providers.map(p =>
    `<option value="${_esc(p.id)}" ${role.provider === p.id ? 'selected' : ''}>${_esc(p.label || p.id)}</option>`
  ).join('');

  const modelsForProvider = _providerModels(role.provider)
    .concat(role.model && !_providerModels(role.provider).includes(role.model) ? [role.model] : []);

  body.style.cssText = 'flex:1;overflow-y:auto;padding:1.5rem';
  body.innerHTML = `
    <div style="max-width:700px;display:flex;flex-direction:column;gap:1rem">

      <!-- Name + Provider + Model row -->
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.75rem">
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Name</label>
          <input id="role-name" value="${_esc(role.name)}"
            style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
        </div>
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Provider</label>
          <select id="role-provider"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
            ${providerOpts}
          </select>
        </div>
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Model</label>
          <input id="role-model" value="${_esc(role.model || '')}" list="role-model-list"
            style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
          <datalist id="role-model-list">
            ${modelsForProvider.map(m => `<option value="${_esc(m)}">`).join('')}
          </datalist>
        </div>
      </div>

      <!-- Description -->
      <div>
        <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Description</label>
        <input id="role-description" value="${_esc(role.description || '')}" placeholder="Short description of this role's purpose…"
          style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                 border-radius:var(--radius);outline:none">
      </div>

      <!-- Max Iterations -->
      <div style="display:flex;align-items:center;gap:0.5rem">
        <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;white-space:nowrap">Max iterations</label>
        <input type="number" id="role-max-iterations" value="${role.max_iterations || 10}" min="1" max="50"
          style="width:60px;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.72rem;
                 padding:0.3rem 0.4rem;border-radius:var(--radius);outline:none;text-align:center">
        <span style="font-size:0.62rem;color:var(--muted)">(pipeline loop limit)</span>
      </div>

      <!-- Built-in Tools -->
      <div>
        <div style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.4rem">
          Tools <span style="text-transform:none;font-weight:400;opacity:0.7">(built-in tools available in agentic loop)</span>
        </div>
        <div id="role-tools-grid" style="display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:0.25rem">
          <div style="font-size:0.65rem;color:var(--muted)">Loading tools…</div>
        </div>
      </div>

      <!-- MCP Tools -->
      <div>
        <div style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.25rem">
          MCP Tools <span style="text-transform:none;font-weight:400;opacity:0.7">(one per line: <code>server_name</code> or <code>server_name/tool_name</code>)</span>
        </div>
        <textarea id="role-mcp-tools" rows="3"
          style="width:100%;box-sizing:border-box;resize:vertical;background:var(--bg);
                 border:1px solid var(--border);color:var(--text);font-family:var(--font);
                 font-size:0.68rem;padding:0.4rem 0.5rem;border-radius:var(--radius);outline:none;
                 line-height:1.6"
          placeholder="filesystem&#10;github/create_issue&#10;my_mcp_server/run_query">${_esc(_mcpToolsToText(role.tools || []))}</textarea>
        <div style="font-size:0.58rem;color:var(--muted);margin-top:0.2rem">
          Stored as <code>mcp:{entry}</code> in the tools list. MCP server must be configured in <code>.claude/mcp.json</code>.
        </div>
      </div>

      <!-- System Roles (prepended fragments) -->
      <div id="role-sys-roles-section">
        <div style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.4rem">
          System Roles <span style="text-transform:none;font-weight:400;opacity:0.7">(prepended to prompt)</span>
        </div>
        <div id="role-sys-roles-list" style="display:flex;flex-direction:column;gap:0.3rem">
          <div style="font-size:0.65rem;color:var(--muted)">Loading…</div>
        </div>
      </div>

      <!-- System Prompt -->
      <div style="flex:1">
        <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">System Prompt</label>
        <textarea id="role-system-prompt"
          style="width:100%;box-sizing:border-box;min-height:320px;resize:vertical;
                 background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.72rem;
                 padding:0.5rem;border-radius:var(--radius);outline:none;
                 line-height:1.55"
          placeholder="You are a senior software architect…">${_esc(role.system_prompt || '')}</textarea>
      </div>

      <!-- Tags / extra info -->
      <div style="font-size:0.6rem;color:var(--muted)">
        ID: ${role.id} · created: ${role.created_at ? new Date(role.created_at).toLocaleDateString() : '—'}
      </div>
    </div>
  `;

  // Wire provider change after innerHTML is set (safe — no onclick in HTML)
  const providerSel = document.getElementById('role-provider');
  if (providerSel) providerSel.addEventListener('change', e => _rolesProviderChange(e.target.value));
}

// ── MCP tools helpers ─────────────────────────────────────────────────────────

/** Extract mcp: entries from the tools array and return as newline-separated text */
function _mcpToolsToText(tools) {
  return tools.filter(t => t.startsWith('mcp:')).map(t => t.slice(4)).join('\n');
}

/** Parse the MCP textarea into mcp: prefixed strings */
function _mcpToolsFromText(text) {
  return text.split('\n').map(l => l.trim()).filter(Boolean).map(l => `mcp:${l}`);
}

function _collectTools() {
  const builtin = Array.from(document.querySelectorAll('#role-tools-grid input[type=checkbox]'))
    .filter(c => c.checked).map(c => c.value);
  const mcpText = document.getElementById('role-mcp-tools')?.value || '';
  return [...builtin, ..._mcpToolsFromText(mcpText)];
}

async function _rolesExportYaml(id, name) {
  try {
    const yaml = await api.agentRoles.exportYaml(id);
    const blob = new Blob([yaml], { type: 'text/yaml' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href     = url;
    a.download = `${(name||'role').toLowerCase().replace(/\s+/g,'_')}.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) { toast('Export failed: ' + e.message, 'error'); }
}

// ── Inline YAML editor ────────────────────────────────────────────────────────

let _yamlValidateTimer = null;

async function _rolesEditYaml(role) {
  const body    = document.getElementById('prompts-editor-body');
  const toolbar = document.getElementById('prompts-toolbar');
  if (!body) return;

  // Load current YAML from backend (export-yaml returns the canonical serialisation)
  let initialYaml = '';
  try {
    initialYaml = await api.agentRoles.exportYaml(role.id);
  } catch (_) {
    // Fallback: build minimal YAML from in-memory role
    initialYaml = [
      `name: ${role.name}`,
      `description: ${role.description || ''}`,
      `provider: ${role.provider || 'claude'}`,
      `model: ${role.model || ''}`,
      `max_iterations: ${role.max_iterations || 10}`,
      `auto_commit: ${role.auto_commit || false}`,
      `tools: []`,
      `system_prompt: |`,
      (role.system_prompt || '').split('\n').map(l => `  ${l}`).join('\n'),
    ].join('\n');
  }

  // Toolbar for YAML mode
  if (toolbar) {
    toolbar.innerHTML = `
      <span class="prompts-editor-path" id="prompts-path">Role (YAML): ${_esc(role.name)}</span>
      <span id="yaml-validation-status" style="font-size:0.65rem;color:var(--muted)">—</span>
      <button id="yaml-back-btn" class="btn btn-ghost btn-sm" style="font-size:0.62rem">← Form</button>
      <button id="yaml-save-btn" class="btn btn-primary btn-sm">Save YAML</button>
    `;
    toolbar.querySelector('#yaml-back-btn').addEventListener('click', () => _renderRoleEditor(role));
    toolbar.querySelector('#yaml-save-btn').addEventListener('click', () => _rolesSaveYaml(role));
  }

  body.style.cssText = 'flex:1;overflow-y:auto;padding:1.5rem';
  body.innerHTML = `
    <div style="max-width:700px;display:flex;flex-direction:column;gap:0.75rem;height:100%">
      <div id="yaml-errors" style="display:none;background:rgba(220,53,69,0.12);border:1px solid rgba(220,53,69,0.4);
           border-radius:6px;padding:0.6rem 0.8rem;font-size:0.7rem;color:#f08080"></div>
      <textarea id="role-yaml-editor"
        style="flex:1;width:100%;box-sizing:border-box;min-height:480px;resize:vertical;
               background:#0d1117;border:1px solid var(--border);color:#e6edf3;
               font-family:'Fira Code','Cascadia Code',monospace;font-size:0.75rem;
               padding:0.75rem;border-radius:var(--radius);outline:none;line-height:1.6;
               tab-size:2"
        spellcheck="false">${_esc(initialYaml)}</textarea>
      <div style="font-size:0.6rem;color:var(--muted)">
        Tip: YAML is validated against the backend schema on every keystroke (debounced 600ms).
        Save writes directly to the database via <code>POST /agent-roles/sync-yaml</code>.
      </div>
    </div>
  `;

  // Wire live validation
  const editor = document.getElementById('role-yaml-editor');
  if (editor) {
    editor.addEventListener('input', () => {
      clearTimeout(_yamlValidateTimer);
      _setYamlStatus('validating…', 'var(--muted)');
      _yamlValidateTimer = setTimeout(() => _validateYamlLive(editor.value), 600);
    });
    // Initial validation
    setTimeout(() => _validateYamlLive(initialYaml), 200);
  }
}

function _setYamlStatus(text, color) {
  const el = document.getElementById('yaml-validation-status');
  if (el) { el.textContent = text; el.style.color = color; }
}

async function _validateYamlLive(yamlText) {
  const errBox = document.getElementById('yaml-errors');
  if (!errBox) return;
  try {
    const res = await api.agentRoles.validateYaml({ yaml_content: yamlText, project: _project || '_global' });
    if (res.valid) {
      errBox.style.display = 'none';
      _setYamlStatus(`✓ valid  (${res.name || '?'})`, '#4ade80');
    } else {
      _showYamlErrors(res.errors || ['Validation failed']);
      _setYamlStatus(`✗ ${res.errors?.length || 1} error(s)`, '#f08080');
    }
  } catch (e) {
    // Try to extract a YAML parse error with line/col info
    let msg = e.message || 'Validation error';
    try {
      const body = JSON.parse(msg.match(/\{.*\}/s)?.[0] || '{}');
      const errs = body.errors || body.detail?.errors || [body.detail] || [];
      if (errs.length) { _showYamlErrors(errs); _setYamlStatus(`✗ ${errs.length} error(s)`, '#f08080'); return; }
    } catch (_) {}
    _showYamlErrors([msg]);
    _setYamlStatus('✗ error', '#f08080');
  }
}

function _showYamlErrors(errors) {
  const errBox = document.getElementById('yaml-errors');
  if (!errBox) return;
  errBox.style.display = 'block';
  errBox.innerHTML =
    '<div style="font-weight:600;margin-bottom:0.3rem">YAML errors:</div>' +
    errors.map(e => {
      // Extract line:col from PyYAML error format "line X column Y"
      const loc = e.match(/line (\d+)(?:.*?column (\d+))?/i);
      const badge = loc
        ? `<span style="font-size:0.6rem;background:rgba(240,128,128,0.2);padding:0.05rem 0.3rem;border-radius:3px;margin-right:0.3rem">line ${loc[1]}${loc[2] ? ':' + loc[2] : ''}</span>`
        : '';
      return `<div style="margin-top:0.15rem">${badge}${_esc(String(e))}</div>`;
    }).join('');
}

async function _rolesSaveYaml(role) {
  const editor = document.getElementById('role-yaml-editor');
  if (!editor) return;
  const yamlText = editor.value;
  _setYamlStatus('saving…', 'var(--muted)');
  try {
    await api.agentRoles.syncYaml({ yaml_content: yamlText, project: _project || '_global' });
    _setYamlStatus('✓ saved', '#4ade80');
    toast('Role saved from YAML', 'success');
    // Reload roles list and re-render the form view with fresh data
    await _loadRoles(_project);
    const updated = _roles.find(r => r.id === role.id) || _activeRole;
    if (updated) _renderRoleEditor(updated);
  } catch (e) {
    let errs = [];
    try {
      const body = JSON.parse(e.message.match(/\{.*\}/s)?.[0] || '{}');
      errs = body.errors || body.detail?.errors || [];
    } catch (_) {}
    if (errs.length) {
      _showYamlErrors(errs);
      _setYamlStatus(`✗ ${errs.length} error(s)`, '#f08080');
    } else {
      _setYamlStatus('✗ save failed', '#f08080');
      toast('Save failed: ' + e.message, 'error');
    }
  }
}

async function _rolesSave(id) {
  const name          = document.getElementById('role-name')?.value?.trim();
  const provider      = document.getElementById('role-provider')?.value;
  const model         = document.getElementById('role-model')?.value?.trim();
  const description   = document.getElementById('role-description')?.value?.trim();
  const systemPrompt  = document.getElementById('role-system-prompt')?.value;
  const maxIterations = parseInt(document.getElementById('role-max-iterations')?.value || '10', 10);
  const tools         = _collectTools();
  if (!name) { toast('Name required', 'error'); return; }
  _rolesShowErrors([]);  // clear any previous errors
  try {
    const updated = await api.agentRoles.patch(id, {
      name, provider, model, description, system_prompt: systemPrompt,
      tools, max_iterations: maxIterations,
    });
    const idx = _roles.findIndex(r => r.id === id);
    if (idx !== -1) _roles[idx] = { ..._roles[idx], ...updated,
      name, provider, model, description, system_prompt: systemPrompt,
      tools, max_iterations: maxIterations };
    _activeRole = _roles[idx] || _activeRole;
    _renderRolesList();
    toast('Role saved', 'success');
  } catch (e) {
    let errs = [];
    try {
      const body = JSON.parse(e.message.match(/\{.*\}/s)?.[0] || '{}');
      errs = body.errors || body.detail?.errors || [];
    } catch (_) {}
    if (errs.length) {
      _rolesShowErrors(errs);
    } else {
      toast('Save failed: ' + e.message, 'error');
    }
  }
}

function _rolesShowErrors(errors) {
  let box = document.getElementById('role-validation-errors');
  if (!errors.length) {
    if (box) box.remove();
    return;
  }
  if (!box) {
    box = document.createElement('div');
    box.id = 'role-validation-errors';
    box.style.cssText = [
      'background:rgba(220,53,69,0.12)',
      'border:1px solid rgba(220,53,69,0.4)',
      'border-radius:6px',
      'padding:0.6rem 0.8rem',
      'margin-bottom:0.75rem',
      'font-size:0.7rem',
      'color:#f08080',
    ].join(';');
    const form = document.querySelector('#prompts-editor-body > div');
    if (form) form.prepend(box);
  }
  box.innerHTML =
    '<div style="font-weight:600;margin-bottom:0.3rem">Validation errors — role not saved:</div>' +
    errors.map(e => `<div>• ${e}</div>`).join('');
}

async function _rolesDelete(id) {
  if (!confirm('Delete this role? Pipeline steps using it will fall back to inline prompts.')) return;
  try {
    await api.agentRoles.delete(id);
    _roles = _roles.filter(r => r.id !== id);
    _activeRole = null;
    _renderRolesList();
    const body = document.getElementById('prompts-editor-body');
    if (body) body.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;
      height:100%;color:var(--muted);font-size:0.72rem">Role deleted</div>`;
    const toolbar = document.getElementById('prompts-toolbar');
    if (toolbar) toolbar.innerHTML = `<span class="prompts-editor-path" id="prompts-path">Select a role or file</span>`;
    toast('Role deleted', 'success');
  } catch (e) { toast('Delete failed: ' + e.message, 'error'); }
}

function _rolesProviderChange(provider) {
  const datalist = document.getElementById('role-model-list');
  const modelInput = document.getElementById('role-model');
  if (!datalist) return;
  const models = _providerModels(provider);
  datalist.innerHTML = models.map(m => `<option value="${_esc(m)}">`).join('');
  // Auto-select the first model for the new provider
  if (modelInput && models.length) modelInput.value = models[0];
}

// ── System Roles (admin panel) ────────────────────────────────────────────────

function _renderSysRolesList() {
  const body = document.getElementById('sys-roles-list-body');
  if (!body) return;
  if (!_systemRoles.length) {
    body.innerHTML = `<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--muted)">
      ${_isAdmin
        ? 'No system roles yet — click <strong>+</strong> to create one'
        : 'No system roles configured'
      }</div>`;
    return;
  }
  const CATEGORY_COLORS = { quality: '#4a90e2', security: '#e25c4a', output: '#4ae29b', review: '#e2b44a', general: '#999' };
  body.innerHTML = _systemRoles.map(sr => `
    <div onclick="window._sysRolesSelect(${sr.id})"
         style="padding:0.35rem 0.75rem;cursor:pointer;border-bottom:1px solid var(--border);
                display:flex;align-items:center;gap:0.45rem;
                background:${_activeSysRole?.id === sr.id ? 'var(--accent)18' : 'transparent'};
                border-left:2px solid ${_activeSysRole?.id === sr.id ? 'var(--accent)' : 'transparent'}"
         onmouseenter="if(${_activeSysRole?.id !== sr.id})this.style.background='var(--surface2)'"
         onmouseleave="if(${_activeSysRole?.id !== sr.id})this.style.background='transparent'">
      <span style="width:6px;height:6px;border-radius:50%;flex-shrink:0;
                   background:${CATEGORY_COLORS[sr.category] || '#999'}"></span>
      <div style="flex:1;min-width:0">
        <div style="font-size:0.68rem;font-weight:500;color:var(--text);
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(sr.name)}</div>
        <div style="font-size:0.55rem;color:var(--muted)">${_esc(sr.category)}</div>
      </div>
    </div>
  `).join('');
}

function _sysRolesSelect(id) {
  _activeFile = '';
  _activeRole = null;
  const sr = _systemRoles.find(s => s.id === id);
  if (!sr) return;
  _activeSysRole = sr;
  _renderSysRolesList();
  _renderSysRoleEditor(sr);
  const pathEl = document.getElementById('prompts-path');
  if (pathEl) pathEl.textContent = `System Role: ${sr.name}`;
}

function _renderSysRoleEditor(sr) {
  const body    = document.getElementById('prompts-editor-body');
  const toolbar = document.getElementById('prompts-toolbar');
  if (!body) return;

  if (toolbar) toolbar.innerHTML = `
    <span class="prompts-editor-path" id="prompts-path">System Role: ${_esc(sr.name)}</span>
    <button class="btn btn-ghost btn-sm" style="color:var(--red);border-color:var(--red);font-size:0.62rem"
      onclick="window._sysRolesDelete(${sr.id})">Delete</button>
    <button class="btn btn-primary btn-sm" onclick="window._sysRolesSave(${sr.id})">Save</button>
  `;

  const CATEGORIES = ['quality', 'security', 'output', 'review', 'general'];
  body.style.cssText = 'flex:1;overflow-y:auto;padding:1.5rem';
  body.innerHTML = `
    <div style="max-width:700px;display:flex;flex-direction:column;gap:1rem">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem">
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Name</label>
          <input id="sysrole-name" value="${_esc(sr.name)}"
            style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
        </div>
        <div>
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Category</label>
          <select id="sysrole-category"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
            ${CATEGORIES.map(c => `<option value="${c}" ${sr.category === c ? 'selected' : ''}>${c}</option>`).join('')}
          </select>
        </div>
      </div>
      <div>
        <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Description</label>
        <input id="sysrole-description" value="${_esc(sr.description || '')}" placeholder="Short description…"
          style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                 border-radius:var(--radius);outline:none">
      </div>
      <div style="flex:1">
        <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;display:block;margin-bottom:0.25rem">Content (prepended as Markdown)</label>
        <textarea id="sysrole-content"
          style="width:100%;box-sizing:border-box;min-height:300px;resize:vertical;
                 background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.72rem;
                 padding:0.5rem;border-radius:var(--radius);outline:none;line-height:1.55"
          placeholder="## Coding Standards\n- …">${_esc(sr.content || '')}</textarea>
      </div>
      <div style="font-size:0.6rem;color:var(--muted)">
        ID: ${sr.id} · category: ${_esc(sr.category)} · created: ${sr.created_at ? new Date(sr.created_at).toLocaleDateString() : '—'}
      </div>
    </div>
  `;
}

async function _sysRolesNew() {
  const name = await _promptModal('New System Role', 'System role name (e.g. "coding_standards"):', 'my_standards');
  if (!name?.trim()) return;
  try {
    const sr = await api.systemRoles.create({ name: name.trim(), category: 'general', description: '', content: '' });
    _systemRoles.push(sr);
    _renderSysRolesList();
    _sysRolesSelect(sr.id);
    toast(`System role "${name}" created`, 'success');
  } catch (e) { toast('Create failed: ' + e.message, 'error'); }
}

async function _sysRolesSave(id) {
  const name        = document.getElementById('sysrole-name')?.value?.trim();
  const category    = document.getElementById('sysrole-category')?.value;
  const description = document.getElementById('sysrole-description')?.value?.trim();
  const content     = document.getElementById('sysrole-content')?.value;
  if (!name) { toast('Name required', 'error'); return; }
  try {
    const updated = await api.systemRoles.patch(id, { name, category, description, content });
    const idx = _systemRoles.findIndex(s => s.id === id);
    if (idx !== -1) _systemRoles[idx] = { ..._systemRoles[idx], ...updated };
    _activeSysRole = _systemRoles[idx] || _activeSysRole;
    _renderSysRolesList();
    toast('System role saved', 'success');
  } catch (e) { toast('Save failed: ' + e.message, 'error'); }
}

async function _sysRolesDelete(id) {
  if (!confirm('Delete this system role? Roles using it will no longer have it prepended.')) return;
  try {
    await api.systemRoles.delete(id);
    _systemRoles = _systemRoles.filter(s => s.id !== id);
    _activeSysRole = null;
    _renderSysRolesList();
    const body    = document.getElementById('prompts-editor-body');
    const toolbar = document.getElementById('prompts-toolbar');
    if (body) body.innerHTML = `<div style="display:flex;align-items:center;justify-content:center;
      height:100%;color:var(--muted);font-size:0.72rem">System role deleted</div>`;
    if (toolbar) toolbar.innerHTML = `<span class="prompts-editor-path" id="prompts-path">Select a role or file</span>`;
    toast('System role deleted', 'success');
  } catch (e) { toast('Delete failed: ' + e.message, 'error'); }
}

async function _sysRolesAttach(roleId) {
  const sel = document.getElementById('sys-role-add-select');
  const systemRoleId = parseInt(sel?.value || '0');
  if (!systemRoleId) { toast('Select a system role to add', 'error'); return; }
  const orderIndex = (_roleLinks[roleId] || []).length;
  try {
    await api.systemRoles.attach(roleId, { system_role_id: systemRoleId, order_index: orderIndex });
    const data = await api.systemRoles.listLinks(roleId);
    _roleLinks[roleId] = data.links || [];
    _renderRoleSystemRolesSection(roleId);
    toast('System role attached', 'success');
  } catch (e) { toast('Attach failed: ' + e.message, 'error'); }
}

async function _sysRolesDetach(roleId, systemRoleId) {
  try {
    await api.systemRoles.detach(roleId, systemRoleId);
    _roleLinks[roleId] = (_roleLinks[roleId] || []).filter(l => l.id !== systemRoleId);
    _renderRoleSystemRolesSection(roleId);
    toast('System role removed', 'success');
  } catch (e) { toast('Remove failed: ' + e.message, 'error'); }
}

// ── File browser (existing prompt files) ─────────────────────────────────────

async function _promptsNew() {
  const name = prompt('File name (e.g. assistant.md):');
  if (!name) return;
  try {
    await api.writePrompt(name, '', _project);
    toast(`Created ${name}`, 'success');
    await _loadTree(_project);
    await _openFile(name, _project);
  } catch (e) { toast(`Error: ${e.message}`, 'error'); }
}

async function _promptsSave() {
  const ta = document.getElementById('prompts-textarea');
  if (!ta || !_activeFile) return;
  try {
    await api.writePrompt(_activeFile, ta.value, _project);
    _fileOrig = ta.value;
    _setSaveBtn(false);
    toast('Saved', 'success');
  } catch (e) { toast(`Save failed: ${e.message}`, 'error'); }
}

function _promptsToggleMode() {
  _editMode = !_editMode;
  _renderEditorArea(_activeFile, _project);
}

async function _loadTree(projectName) {
  const body = document.getElementById('prompts-tree-body');
  if (!body) return;
  try {
    const data  = await api.listPrompts(projectName);
    const files = data.files || data.prompts || [];
    if (!files.length) {
      body.innerHTML = '<div class="empty-state" style="padding:1.5rem"><p style="font-size:0.68rem">No prompt files</p></div>';
      return;
    }
    const tree = _buildTree(files);
    body.innerHTML = _renderTree(tree);
    if (_activeFile) {
      document.querySelectorAll('.tree-file').forEach(el =>
        el.classList.toggle('active', el.dataset.path === _activeFile)
      );
    }
  } catch (e) {
    body.innerHTML = `<div class="empty-state" style="padding:1rem">
      <p style="color:var(--red);font-size:0.68rem">${_esc(e.message)}</p></div>`;
  }
}

function _buildTree(files) {
  const root = {};
  for (const f of files) {
    const parts = (typeof f === 'string' ? f : f.path || f.name).split('/');
    let node = root;
    for (let i = 0; i < parts.length - 1; i++) {
      const dir = parts[i];
      if (!node[dir]) node[dir] = { _files: [] };
      node = node[dir];
    }
    if (!node._files) node._files = [];
    node._files.push(typeof f === 'string' ? f : (f.path || f.name));
  }
  return root;
}

function _renderTree(node, prefix = '') {
  let html = '';
  const dirs  = Object.keys(node).filter(k => k !== '_files').sort();
  const files = (node._files || []).sort();
  for (const dir of dirs) {
    const id = _slugify(prefix ? `${prefix}/${dir}` : dir);
    html += `
      <div class="tree-folder" id="folder-${id}">
        <div class="tree-folder-row" onclick="window._toggleFolder('${id}')">
          <span class="tree-folder-icon">▶</span>
          <span>${_esc(dir)}/</span>
        </div>
        <div id="folder-children-${id}" style="display:none">
          ${_renderTree(node[dir], prefix ? `${prefix}/${dir}` : dir)}
        </div>
      </div>`;
  }
  for (const file of files) {
    const fname = file.split('/').pop();
    const isMd  = fname.endsWith('.md');
    html += `
      <div class="tree-file ${file === _activeFile ? 'active' : ''}"
           data-path="${_esc(file)}"
           onclick="window._openPromptFile('${_esc(file)}')">
        <span style="font-size:0.6rem;color:${isMd ? 'var(--blue)' : 'var(--muted)'}">
          ${isMd ? 'M↓' : '≡'}
        </span>
        <span>${_esc(fname)}</span>
      </div>`;
  }
  return html;
}

async function _openFile(path, projectName) {
  _activeRole = null;
  _activeFile = path;
  _editMode   = false;
  document.querySelectorAll('.tree-file').forEach(el =>
    el.classList.toggle('active', el.dataset.path === path)
  );
  const pathEl = document.getElementById('prompts-path');
  if (pathEl) pathEl.textContent = path;
  const bodyEl = document.getElementById('prompts-editor-body');
  if (!bodyEl) return;
  bodyEl.innerHTML = '<div style="padding:1rem;font-size:0.68rem;color:var(--muted)">Loading…</div>';
  bodyEl.style.cssText = '';
  try {
    const data = await api.readPrompt(path, projectName);
    _fileOrig = data.content || '';
    _renderEditorArea(path, projectName);
  } catch (e) {
    bodyEl.innerHTML = `<div style="padding:1rem;font-size:0.68rem;color:var(--red)">${_esc(e.message)}</div>`;
  }
}

function _renderEditorArea(path, projectName) {
  const bodyEl  = document.getElementById('prompts-editor-body');
  const toolbar = document.getElementById('prompts-toolbar');
  if (!bodyEl || !toolbar) return;
  const isMd = (path || '').endsWith('.md');
  toolbar.innerHTML = `
    <span class="prompts-editor-path" id="prompts-path">${_esc(path)}</span>
    ${isMd ? `
      <div style="display:flex;gap:2px;background:var(--surface2);padding:2px;border-radius:var(--radius)">
        <button style="padding:0.2rem 0.55rem;border-radius:5px;border:none;cursor:pointer;
                       font-size:0.65rem;font-family:var(--font);
                       background:${!_editMode ? 'var(--surface3)' : 'transparent'};
                       color:${!_editMode ? 'var(--text)' : 'var(--text2)'}"
                onclick="window._promptsToggleMode()">Preview</button>
        <button style="padding:0.2rem 0.55rem;border-radius:5px;border:none;cursor:pointer;
                       font-size:0.65rem;font-family:var(--font);
                       background:${_editMode ? 'var(--surface3)' : 'transparent'};
                       color:${_editMode ? 'var(--text)' : 'var(--text2)'}"
                onclick="window._promptsToggleMode()">Edit</button>
      </div>` : ''}
    <button class="btn btn-primary btn-sm" id="prompts-save-btn"
      disabled style="opacity:0.4" onclick="window._promptsSave()">Save</button>
  `;
  if (_editMode || !isMd) {
    bodyEl.style.cssText = 'flex:1;display:flex;flex-direction:column;overflow:hidden';
    bodyEl.innerHTML = '';
    const ta = document.createElement('textarea');
    ta.className = 'prompts-textarea';
    ta.id = 'prompts-textarea';
    ta.value = _fileOrig;
    bodyEl.appendChild(ta);
    _setSaveBtn(false);
    ta.addEventListener('input', () => _setSaveBtn(ta.value !== _fileOrig));
    ta.addEventListener('keydown', e => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        const btn = document.getElementById('prompts-save-btn');
        if (btn && !btn.disabled) window._promptsSave();
      }
    });
    ta.focus();
  } else {
    bodyEl.style.cssText = 'flex:1;overflow-y:auto';
    bodyEl.innerHTML = `<div class="prompt-md-view" style="padding:1.5rem 2rem">${renderMd(_fileOrig)}</div>`;
  }
}

// ── Resize handle ─────────────────────────────────────────────────────────────

function _initPromptsResize() {
  const handle = document.getElementById('prompts-resize-handle');
  const panel  = document.getElementById('prompts-tree-panel');
  if (!handle || !panel) return;
  let dragging = false, startX = 0, startW = 0;
  handle.addEventListener('mousedown', e => {
    dragging = true; startX = e.clientX; startW = panel.offsetWidth;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });
  handle.addEventListener('mouseover', () => { handle.style.background = 'var(--accent)'; });
  handle.addEventListener('mouseout',  () => { if (!dragging) handle.style.background = 'var(--border)'; });
  document.addEventListener('mousemove', e => {
    if (!dragging) return;
    panel.style.width = `${Math.max(150, Math.min(500, startW + (e.clientX - startX)))}px`;
  });
  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    document.body.style.cursor = document.body.style.userSelect = '';
    handle.style.background = 'var(--border)';
    localStorage.setItem('aicli_prompts_tree_w', String(panel.offsetWidth));
  });
}

// ── Utils ─────────────────────────────────────────────────────────────────────

function _setSaveBtn(enabled) {
  const btn = document.getElementById('prompts-save-btn');
  if (!btn) return;
  btn.disabled = !enabled;
  btn.style.opacity = enabled ? '1' : '0.4';
}

function _esc(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function _slugify(s) { return s.replace(/[^a-zA-Z0-9]/g, '_'); }
