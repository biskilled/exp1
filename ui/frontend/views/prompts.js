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
let _activeFile          = '';
let _fileOrig            = '';
let _editMode            = false;
let _activeRole          = null;   // {id, name, provider, model, description, system_prompt, ...}
let _roles               = [];
let _project             = null;
let _isAdmin             = false;
let _systemRoles         = [];     // all available system roles loaded once at tab init
let _roleLinks           = {};     // {roleId: [{id, name, category, order_index, content}]}
let _activeSysRole       = null;   // system role being edited (admin panel)
let _toolsByCategory     = {};     // {category: [toolName, ...]} — populated by _loadRoleTools
let _mcpCatalog          = [];     // MCP entries from catalog — populated by _loadRoleTools
let _originalRoleSpecific = '';    // role-specific part of system_prompt when role was opened

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
  _activeFile      = '';
  _fileOrig        = '';
  _editMode        = false;
  _activeRole      = null;
  _activeSysRole   = null;
  _project         = projectName;
  _isAdmin         = false;
  _systemRoles     = [];
  _roleLinks       = {};
  _toolsByCategory = {};
  _mcpCatalog      = [];
  _msCloseAll();

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
          <div style="display:flex;gap:0.25rem;margin-left:auto">
            <button class="btn btn-ghost btn-sm" id="roles-reload-btn"
              style="padding:0.15rem 0.5rem;font-size:0.6rem" title="Reload all roles from YAML files">↺ Refresh</button>
            <button class="btn btn-ghost btn-sm" style="padding:0.15rem 0.4rem;font-size:0.65rem"
              onclick="window._rolesNew()" title="New agent role">+</button>
          </div>
        </div>
        <div id="roles-list-body" style="overflow-y:auto;flex:1;min-height:120px;border-bottom:1px solid var(--border)">
          <div style="padding:1rem;font-size:0.68rem;color:var(--muted)">Loading…</div>
        </div>

        <!-- System Roles section (bottom) -->
        <div id="sys-roles-section" style="display:flex;flex-shrink:0;flex-direction:column;max-height:35%">
          <div class="prompts-tree-header" style="flex-shrink:0">
            <span class="prompts-tree-label" style="font-size:0.62rem">System Roles</span>
            <div style="display:flex;gap:0.2rem;margin-left:auto">
              <button id="sys-roles-reset-btn" class="btn btn-ghost btn-sm"
                style="padding:0.12rem 0.35rem;font-size:0.55rem;display:none;color:var(--muted)"
                onclick="window._sysRolesResetDefaults()" title="Delete all system roles and re-seed defaults">Reset defaults</button>
              <button id="sys-roles-new-btn" class="btn btn-ghost btn-sm"
                style="padding:0.12rem 0.35rem;font-size:0.6rem;display:none"
                onclick="window._sysRolesNew()" title="New system role">+</button>
            </div>
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
  window._rolesNew               = _rolesNew;
  window._rolesSelect            = _rolesSelect;
  window._rolesDelete            = _rolesDelete;
  window._rolesSave              = _rolesSave;
  window._rolesExportYaml        = _rolesExportYaml;
  window._rolesEditYaml          = _rolesEditYaml;
  window._rolesProviderChange    = _rolesProviderChange;
  window._rolesRestoreDefault    = _rolesRestoreDefault;
  window._sysRolesNew            = _sysRolesNew;
  window._sysRolesSelect         = _sysRolesSelect;
  window._sysRolesSave           = _sysRolesSave;
  window._sysRolesDelete         = _sysRolesDelete;
  window._sysRolesAttach         = _sysRolesAttach;
  window._sysRolesDetach         = _sysRolesDetach;
  window._sysRolesResetDefaults  = _sysRolesResetDefaults;

  // Wire reload button (after HTML is set)
  const reloadBtn = document.getElementById('roles-reload-btn');
  if (reloadBtn) reloadBtn.addEventListener('click', () => _rolesReloadFromYaml(projectName));

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
    const sysSection    = document.getElementById('sys-roles-section');
    const sysNewBtn     = document.getElementById('sys-roles-new-btn');
    const sysResetBtn   = document.getElementById('sys-roles-reset-btn');
    if (sysSection)  sysSection.style.display  = 'flex';
    if (sysNewBtn)   sysNewBtn.style.display   = _isAdmin ? '' : 'none';
    if (sysResetBtn) sysResetBtn.style.display = _isAdmin ? '' : 'none';

    _renderRolesList();
    _renderSysRolesList();
  } catch (e) {
    body.innerHTML = `<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--red)">${_esc(e.message)}</div>`;
  }
}

// Provider color map for role list items
const _PROVIDER_COLORS = {
  claude:      '#a78bfa',  // purple
  openai:      '#34d399',  // green
  gemini:      '#fbbf24',  // amber
  deepseek:    '#60a5fa',  // blue
  grok:        '#f87171',  // red
  claude_sdk:  '#c4b5fd',  // light purple
  codex_sdk:   '#6ee7b7',  // light green
  ollama:      '#94a3b8',  // slate
};

function _renderRoleItem(r) {
  const isActive   = _activeRole?.id === r.id;
  const isExt      = r.has_template === false;
  const canRestore = r.has_template === true;
  const provColor  = _PROVIDER_COLORS[r.provider] || 'var(--muted)';

  const extBadge  = isExt
    ? `<span title="External role — no template, cannot restore"
             style="font-size:0.5rem;padding:0.1rem 0.3rem;border-radius:4px;
                    background:rgba(255,165,0,0.18);color:#f59e0b;font-weight:600;
                    letter-spacing:0.04em;flex-shrink:0">EXT</span>`
    : '';
  const restoreBtn = canRestore
    ? `<button onclick="event.stopPropagation();window._rolesRestoreDefault(${r.id},${JSON.stringify(_esc(r.name))})"
               title="Restore this role to template defaults"
               style="opacity:0;font-size:0.55rem;padding:0.1rem 0.3rem;border-radius:4px;
                      background:none;border:1px solid var(--border);color:var(--muted);
                      cursor:pointer;flex-shrink:0;line-height:1;transition:opacity 0.15s"
               class="role-reset-btn">reset</button>`
    : '';

  // Short model name: strip date suffixes like -20251001
  const modelShort = (r.model || '').replace(/-\d{8}$/, '').replace(/^claude-/, '').replace(/^gpt-/, '');

  return `
    <div onclick="window._rolesSelect(${r.id})"
         style="padding:0.45rem 0.75rem 0.4rem;cursor:pointer;border-bottom:1px solid var(--border);
                display:flex;align-items:center;gap:0.5rem;
                background:${isActive ? 'rgba(100,108,255,0.1)' : 'transparent'};
                border-left:3px solid ${isActive ? 'var(--accent)' : 'transparent'}"
         onmouseenter="this.style.background='${isActive ? 'rgba(100,108,255,0.1)' : 'var(--surface2)'}';this.querySelector('.role-reset-btn')&&(this.querySelector('.role-reset-btn').style.opacity='0.6')"
         onmouseleave="this.style.background='${isActive ? 'rgba(100,108,255,0.1)' : 'transparent'}';this.querySelector('.role-reset-btn')&&(this.querySelector('.role-reset-btn').style.opacity='0')">
      <div style="flex:1;min-width:0">
        <div style="font-size:0.72rem;font-weight:700;color:var(--text);
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
                    letter-spacing:-0.01em">${_esc(r.name)}</div>
        <div style="font-size:0.58rem;margin-top:0.1rem;display:flex;align-items:center;gap:0.3rem;overflow:hidden">
          <span style="color:${provColor};font-weight:500">${_esc(r.provider || '')}</span>
          ${modelShort ? `<span style="color:var(--muted)">·</span>
          <span style="color:rgba(255,255,255,0.45);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(modelShort)}</span>` : ''}
        </div>
      </div>
      ${extBadge}${restoreBtn}
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

async function _rolesReloadFromYaml(projectName) {
  const btn = document.getElementById('roles-reload-btn');
  if (btn) { btn.disabled = true; btn.textContent = '…'; }
  try {
    const data = await api.agentRoles.reloadFromYaml(projectName || 'aicli');
    toast(`Reloaded ${data.reloaded} role(s) from YAML`, 'success');
    await _loadRoles(projectName);
    // Re-open active role if still selected
    if (_activeRole) {
      const fresh = _roles.find(r => r.id === _activeRole.id);
      if (fresh) _rolesSelect(fresh.id);
    }
  } catch (e) {
    toast('Reload failed: ' + e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '↺'; }
  }
}

async function _rolesRestoreDefault(id, name) {
  if (!confirm(`Restore "${name}" to template defaults?\nAll your changes to this role will be lost.`)) return;
  try {
    const updated = await api.agentRoles.restoreDefault(id);
    const idx = _roles.findIndex(r => r.id === id);
    if (idx !== -1) _roles[idx] = { ..._roles[idx], ...updated };
    _renderRolesList();
    if (_activeRole?.id === id) {
      _activeRole = _roles[idx];
      _renderRoleEditor(_activeRole);
      _loadRoleTools(_activeRole);
    }
    toast(`"${name}" restored to defaults`, 'success');
  } catch (e) {
    toast('Restore failed: ' + e.message, 'error');
  }
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

// ── Multi-select dropdown widget ─────────────────────────────────────────────
// Each widget: _msHtml(id, items, selected) → HTML string
// Global handlers keep state purely in DOM (checked checkboxes + chip DOM).

function _msHtml(id, items, selectedValues, { label = '', placeholder = 'None selected', color = 'var(--accent)' } = {}) {
  const selSet = new Set(selectedValues);
  const chips  = selectedValues.map(v => {
    const item = items.find(i => i.value === v);
    return `<span style="display:inline-flex;align-items:center;gap:0.2rem;
                         padding:0.1rem 0.3rem 0.1rem 0.5rem;border-radius:10px;
                         background:rgba(100,108,255,0.18);color:var(--accent);
                         font-size:0.62rem;line-height:1.4;white-space:nowrap">
      ${_esc(item?.label || v)}
      <span onclick="event.stopPropagation();window._msRemove('${id}','${_esc(v)}')"
            style="cursor:pointer;opacity:0.7;font-size:0.75rem;padding:0 0.1rem">&times;</span>
    </span>`;
  }).join('');

  const listItems = items.map(item => `
    <label style="display:flex;align-items:flex-start;gap:0.5rem;padding:0.35rem 0.6rem;
                  cursor:pointer;border-bottom:1px solid rgba(255,255,255,0.04)"
           onmouseenter="this.style.background='var(--surface2)'"
           onmouseleave="this.style.background='transparent'">
      <input type="checkbox" value="${_esc(item.value)}" ${selSet.has(item.value) ? 'checked' : ''}
             data-ms="${id}"
             onchange="window._msSel('${id}','${_esc(item.value)}',this.checked)"
             style="width:13px;height:13px;accent-color:${item.color || color};cursor:pointer;flex-shrink:0;margin-top:2px">
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:0.4rem">
          <span style="font-size:0.68rem;color:${item.color || 'var(--text)'};font-weight:500">${_esc(item.label || item.value)}</span>
          ${item.tag ? `<span style="font-size:0.55rem;padding:0.05rem 0.3rem;border-radius:8px;
                                     background:var(--surface3);color:var(--muted)">${_esc(item.tag)}</span>` : ''}
        </div>
        ${item.subtitle ? `<div style="font-size:0.58rem;color:var(--muted);margin-top:0.1rem;line-height:1.4">${_esc(item.subtitle)}</div>` : ''}
      </div>
    </label>`).join('');

  return `
    <div style="position:relative" id="ms-root-${id}">
      ${label ? `<div style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.3rem">${label}</div>` : ''}
      <div onclick="window._msToggle('${id}')"
           style="display:flex;align-items:center;gap:0.35rem;flex-wrap:wrap;min-height:32px;
                  padding:0.3rem 0.5rem;background:var(--bg);border:1px solid var(--border);
                  border-radius:var(--radius);cursor:pointer;user-select:none">
        <div id="ms-chips-${id}" style="flex:1;display:flex;flex-wrap:wrap;gap:0.2rem;align-items:center;min-height:20px">
          ${chips || `<span style="font-size:0.65rem;color:var(--muted)">${_esc(placeholder)}</span>`}
        </div>
        <span style="color:var(--muted);font-size:0.65rem;flex-shrink:0">▾</span>
      </div>
      <div id="ms-drop-${id}"
           style="display:none;position:absolute;z-index:200;top:calc(100% + 3px);left:0;right:0;
                  background:var(--bg);border:1px solid var(--border);border-radius:6px;
                  box-shadow:0 10px 30px rgba(0,0,0,0.55);overflow:hidden">
        <div style="padding:0.35rem 0.5rem;border-bottom:1px solid var(--border)">
          <input id="ms-filter-${id}" type="search" placeholder="Filter…"
                 oninput="window._msFilter('${id}')"
                 onclick="event.stopPropagation()"
                 style="width:100%;box-sizing:border-box;background:transparent;border:none;
                        outline:none;color:var(--text);font-size:0.68rem;font-family:var(--font)">
        </div>
        <div id="ms-list-${id}" style="max-height:200px;overflow-y:auto">
          ${listItems || `<div style="padding:0.5rem;font-size:0.65rem;color:var(--muted)">No items</div>`}
        </div>
      </div>
    </div>`;
}

function _msCloseAll() {
  document.querySelectorAll('[id^="ms-drop-"]').forEach(el => { el.style.display = 'none'; });
}

function _msToggle(id) {
  const drop = document.getElementById(`ms-drop-${id}`);
  if (!drop) return;
  const isOpen = drop.style.display !== 'none';
  _msCloseAll();
  if (!isOpen) {
    drop.style.display = 'block';
    const filter = document.getElementById(`ms-filter-${id}`);
    if (filter) setTimeout(() => filter.focus(), 0);
    // Close on outside click
    setTimeout(() => {
      const handler = (e) => {
        const root = document.getElementById(`ms-root-${id}`);
        if (root && !root.contains(e.target)) {
          drop.style.display = 'none';
          document.removeEventListener('click', handler);
        }
      };
      document.addEventListener('click', handler);
    }, 0);
  }
}

function _msFilter(id) {
  const val  = (document.getElementById(`ms-filter-${id}`)?.value || '').toLowerCase();
  const list = document.getElementById(`ms-list-${id}`);
  if (!list) return;
  list.querySelectorAll('label').forEach(lbl => {
    const text = lbl.textContent.toLowerCase();
    lbl.style.display = text.includes(val) ? '' : 'none';
  });
}

function _msRemove(id, value) {
  // Uncheck the corresponding checkbox in the dropdown
  const cb = document.querySelector(`#ms-list-${id} input[value="${CSS.escape(value)}"]`);
  if (cb) { cb.checked = false; }
  _msRefreshChips(id);
}

function _msSel(id, value, checked) {
  void checked; // checkbox state already updated by browser
  _msRefreshChips(id);
}

function _msGetSelected(id) {
  return Array.from(document.querySelectorAll(`#ms-list-${id} input[type=checkbox]:checked`))
    .map(cb => cb.value);
}

function _msRefreshChips(id) {
  const chipsEl = document.getElementById(`ms-chips-${id}`);
  if (!chipsEl) return;
  const selected = _msGetSelected(id);
  if (!selected.length) {
    const placeholder = chipsEl.dataset.placeholder || 'None selected';
    chipsEl.innerHTML = `<span style="font-size:0.65rem;color:var(--muted)">${_esc(placeholder)}</span>`;
    return;
  }
  // Build label map from current dropdown: value → { label, tag, color }
  const meta = {};
  document.querySelectorAll(`#ms-list-${id} input[type=checkbox]`).forEach(cb => {
    const row   = cb.closest('label');
    const label = row?.querySelector('div > span:first-child')?.textContent?.trim() || cb.value;
    const tag   = row?.querySelector('span[style*="border-radius:8px"]')?.textContent?.trim() || '';
    const color = row?.querySelector('div > span:first-child')?.style?.color || 'var(--accent)';
    meta[cb.value] = { label, tag, color };
  });
  chipsEl.innerHTML = selected.map(v => {
    const { label, tag, color } = meta[v] || { label: v, tag: '', color: 'var(--accent)' };
    const display = tag ? `${label} (${tag})` : label;
    return `
      <span style="display:inline-flex;align-items:center;gap:0.2rem;
                   padding:0.1rem 0.3rem 0.1rem 0.5rem;border-radius:10px;
                   background:${color}22;color:${color};
                   font-size:0.62rem;line-height:1.4;white-space:nowrap;border:1px solid ${color}44">
        ${_esc(display)}
        <span onclick="event.stopPropagation();window._msRemove('${id}','${_esc(v)}')"
              style="cursor:pointer;opacity:0.7;font-size:0.75rem;padding:0 0.1rem">&times;</span>
      </span>`;
  }).join('');
}

// ── Tools + MCP loader ────────────────────────────────────────────────────────

async function _loadRoleTools(role) {
  const body = document.getElementById('role-tools-body');
  if (!body) return;

  body.innerHTML = `<div style="font-size:0.65rem;color:var(--muted)">Loading…</div>`;

  const providerData = _providers.find(p => p.id === role.provider) || {};
  const toolSupport  = providerData.tool_support || 'full';
  const isNative     = toolSupport === 'native';

  // Fetch tools and MCP catalog in parallel
  let allTools = [], mcps = _mcpCatalog;
  try {
    const fetches = [api.agentRoles.mcpCatalog(_project || 'aicli').catch(() => ({ mcps: [] }))];
    if (!isNative) fetches.unshift(api.agentRoles.availableTools().catch(() => ({ tools: [] })));
    const results = await Promise.all(fetches);
    if (!isNative) { allTools = results[0].tools || []; mcps = results[1]?.mcps || []; }
    else            { mcps = results[0].mcps || []; }
    _mcpCatalog = mcps;
  } catch (_) { /* use whatever was loaded */ }

  // Build tool items grouped by category
  _toolsByCategory = {};
  for (const t of allTools) {
    if (!_toolsByCategory[t.category]) _toolsByCategory[t.category] = [];
    _toolsByCategory[t.category].push(t.name);
  }

  // Parse role's current tools into builtin tool names and mcp names
  const roleMcpNames = (role.tools || []).filter(t => t.startsWith('mcp:')).map(t => t.slice(4));
  const roleBuiltin  = new Set((role.tools || []).filter(t => !t.startsWith('mcp:')));

  // Category colors
  const catColors = { git: '#e8834e', files: '#5b8af5', memory: '#9b7ef8', other: '#888' };

  // Tool multi-select items = one item per CATEGORY (not per tool)
  // A category is pre-selected if any of its tools are in roleBuiltin
  const catOrder     = ['git', 'files', 'memory', 'other'];
  const sortedCats   = [...catOrder.filter(c => _toolsByCategory[c]),
                        ...Object.keys(_toolsByCategory).filter(c => !catOrder.includes(c))];
  const selectedCats = sortedCats.filter(cat =>
    (_toolsByCategory[cat] || []).some(t => roleBuiltin.has(t))
  );
  const toolItems = sortedCats.map(cat => {
    const tools = _toolsByCategory[cat] || [];
    return {
      value:    cat,
      label:    cat,
      tag:      `${tools.length}`,
      subtitle: tools.join(' · '),
      color:    catColors[cat] || '#888',
    };
  });

  // MCP multi-select items — catalog + any unknown mcp: entries already in role.tools
  const catalogNames = new Set(mcps.map(m => m.name));
  const unknownMcps  = roleMcpNames.filter(n => !catalogNames.has(n)).map(n => ({ name: n, label: n }));
  const mcpItems     = [...mcps, ...unknownMcps].map(m => ({
    value:    m.name,
    label:    m.label || m.name,
    tag:      (m.tags || [])[0] || '',
    subtitle: m.description ? m.description.slice(0, 60) + (m.description.length > 60 ? '…' : '') : '',
  }));

  let html = '';

  if (isNative) {
    // Native providers: hide built-in tools, show info badge only
    html += `
      <div>
        <div style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.3rem">Built-in Tools</div>
        <div style="display:flex;align-items:center;gap:0.5rem;padding:0.45rem 0.65rem;
                    background:rgba(100,108,255,0.08);border:1px solid rgba(100,108,255,0.22);
                    border-radius:6px;font-size:0.67rem;color:rgba(255,255,255,0.65)">
          <span style="font-size:0.85rem">ℹ</span>
          <span>${_esc(providerData.tool_note || 'This provider uses its own native tools.')}</span>
        </div>
      </div>`;
  } else {
    const warning = toolSupport === 'limited'
      ? `<div style="margin-bottom:0.4rem;display:flex;align-items:center;gap:0.4rem;
                     padding:0.35rem 0.55rem;background:rgba(230,180,50,0.1);
                     border:1px solid rgba(230,180,50,0.3);border-radius:5px;
                     font-size:0.63rem;color:rgba(230,180,50,0.9)">
           ⚠ ${_esc(providerData.tool_note || 'Tool calling varies by model.')}
         </div>` : '';
    html += `<div>${warning}${_msHtml('tools', toolItems, selectedCats, {
      label:       'Built-in Tools',
      placeholder: 'No tool categories selected',
      color:       'var(--accent)',
    })}</div>`;
  }

  html += `<div>${_msHtml('mcps', mcpItems, roleMcpNames, {
    label:       'MCP Servers',
    placeholder: 'No MCP servers selected',
    color:       '#4ade80',
  })}</div>`;

  body.innerHTML = html;

  // Persist placeholder text for _msRefreshChips
  const toolChips = document.getElementById('ms-chips-tools');
  if (toolChips) toolChips.dataset.placeholder = 'No tool categories selected';
  const mcpChips = document.getElementById('ms-chips-mcps');
  if (mcpChips) mcpChips.dataset.placeholder = 'No MCP servers selected';

  // Register global handlers
  window._msToggle = _msToggle;
  window._msRemove = _msRemove;
  window._msSel    = _msSel;
  window._msFilter = _msFilter;
}

function _renderRoleSystemRolesSection(roleId) {
  const container = document.getElementById('role-sys-roles-list');
  if (!container) return;
  const links = _roleLinks[roleId] || [];

  // Update the BASE content preview regardless of admin state
  const preview    = document.getElementById('role-sys-roles-preview');
  const previewPre = document.getElementById('role-sys-roles-pre');
  if (preview && previewPre) {
    const combined = links.map(l => l.content || '').filter(Boolean).join('\n\n');
    if (combined.trim()) {
      preview.style.display = 'block';
      previewPre.textContent = combined;
    } else {
      preview.style.display = 'none';
    }
  }

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

  // Extract role-specific part (strip base preset divider if present)
  const _SP_DIVIDER = '\n\n---\n\n';
  const sp = role.system_prompt || '';
  const divIdx = sp.indexOf(_SP_DIVIDER);
  _originalRoleSpecific = divIdx !== -1 ? sp.slice(divIdx + _SP_DIVIDER.length) : sp;

  // Toolbar
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
        <input type="number" id="role-max-iterations" value="${role.max_iterations || 10}" min="1" max="100"
          style="width:60px;background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.72rem;
                 padding:0.3rem 0.4rem;border-radius:var(--radius);outline:none;text-align:center">
        <span style="font-size:0.62rem;color:var(--muted)">agent ReAct loop limit · pipeline stage overrides this</span>
      </div>

      <!-- Tools & MCP (multi-select dropdowns, loaded async by _loadRoleTools) -->
      <div id="role-tools-body" style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem">
        <div style="font-size:0.65rem;color:var(--muted)">Loading…</div>
      </div>

      <!-- System Roles (base prompt fragments prepended at runtime) -->
      <div id="role-sys-roles-section">
        <div style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em;margin-bottom:0.4rem">
          System Roles
          <span style="text-transform:none;font-weight:400;opacity:0.7">(shared base — prepended to role prompt)</span>
        </div>
        <div id="role-sys-roles-list" style="display:flex;flex-direction:column;gap:0.3rem">
          <div style="font-size:0.65rem;color:var(--muted)">Loading…</div>
        </div>
        <!-- Content preview — shown when system roles with content are attached -->
        <div id="role-sys-roles-preview" style="display:none;margin-top:0.5rem;
             border:1px solid var(--border);border-radius:var(--radius);background:var(--surface2);overflow:hidden">
          <div id="role-sys-roles-preview-toggle"
               style="display:flex;align-items:center;gap:0.5rem;padding:0.35rem 0.6rem;cursor:pointer"
               onclick="const pre=document.getElementById('role-sys-roles-pre');
                        pre.style.display=pre.style.display==='none'?'block':'none';
                        this.querySelector('.toggle-arrow').textContent=pre.style.display==='none'?'▸':'▾'">
            <span style="font-size:0.58rem;padding:0.08rem 0.35rem;border-radius:4px;
                         background:rgba(74,222,128,0.15);color:#4ade80;font-weight:600;letter-spacing:0.04em">BASE</span>
            <span style="font-size:0.62rem;color:var(--muted);flex:1">Combined system role content</span>
            <span class="toggle-arrow" style="font-size:0.6rem;color:var(--muted)">▸</span>
          </div>
          <pre id="role-sys-roles-pre"
               style="display:none;margin:0;padding:0.5rem 0.75rem;font-size:0.6rem;
                      color:var(--text2);line-height:1.5;border-top:1px solid var(--border);
                      overflow-x:auto;max-height:240px;overflow-y:auto;white-space:pre-wrap"></pre>
        </div>
      </div>

      <!-- Role-specific System Prompt -->
      <div style="flex:1;display:flex;flex-direction:column;gap:0.5rem">
        <div style="display:flex;align-items:center;justify-content:space-between">
          <label style="font-size:0.6rem;text-transform:uppercase;color:var(--muted);letter-spacing:.06em">
            Role-specific prompt</label>
          <button id="role-prompt-reset"
            style="font-size:0.58rem;padding:0.15rem 0.5rem;border-radius:4px;
                   background:none;border:1px solid var(--border);color:var(--muted);cursor:pointer"
            title="Reset to the value when this role was opened">↩ Reset to original</button>
        </div>
        <textarea id="role-system-prompt"
          style="width:100%;box-sizing:border-box;min-height:280px;resize:vertical;
                 background:var(--bg);border:1px solid var(--border);
                 color:var(--text);font-family:var(--font);font-size:0.72rem;
                 padding:0.5rem;border-radius:var(--radius);outline:none;line-height:1.55"
          placeholder="Role-specific instructions (output format, domain rules, JSON schema…)"></textarea>
      </div>

      <!-- Footer info -->
      <div style="font-size:0.6rem;color:var(--muted)">
        ID: ${role.id} · created: ${role.created_at ? new Date(role.created_at).toLocaleDateString() : '—'}
      </div>
    </div>
  `;

  // Set textarea to role-specific content only
  const ta = document.getElementById('role-system-prompt');
  if (ta) ta.value = _originalRoleSpecific;

  // Wire reset button
  const resetBtn = document.getElementById('role-prompt-reset');
  if (resetBtn) resetBtn.addEventListener('click', () => {
    const t = document.getElementById('role-system-prompt');
    if (t) { t.value = _originalRoleSpecific; toast('Prompt reset to original', 'success'); }
  });

  // Wire provider change
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
  // Expand selected categories → individual tool names
  const selectedCats = _msGetSelected('tools');
  const builtin = selectedCats.flatMap(cat => _toolsByCategory[cat] || []);
  const mcps    = _msGetSelected('mcps').map(v => `mcp:${v}`);
  return [...builtin, ...mcps];
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
  const maxIterations = parseInt(document.getElementById('role-max-iterations')?.value || '10', 10);

  // Reconstruct merged system_prompt: base (if any) + divider + role-specific
  const _DIVIDER    = '\n\n---\n\n';
  const baseContent = document.getElementById('role-base-content')?.value?.trimEnd() || '';
  const roleSpec    = document.getElementById('role-system-prompt')?.value || '';
  const systemPrompt  = baseContent ? baseContent + _DIVIDER + roleSpec : roleSpec;
  const tools         = _collectTools();
  if (!name) { toast('Name required', 'error'); return; }
  _rolesShowErrors([]);  // clear any previous errors
  try {
    const updated = await api.agentRoles.patch(id, {
      name, provider, model, description, system_prompt: systemPrompt,
      tools, max_iterations: maxIterations,
    }, _project || 'aicli');
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

// ── System Roles reset-to-defaults ────────────────────────────────────────────

async function _sysRolesResetDefaults() {
  if (!confirm(
    'Delete ALL system roles and re-seed the 3 canonical defaults?\n' +
    '(Coding — General · Design & Planning · Review & Quality)\n\n' +
    'Existing role attachments will be removed.'
  )) return;
  const btn = document.getElementById('sys-roles-reset-btn');
  if (btn) { btn.disabled = true; btn.textContent = '…'; }
  try {
    const result = await api.systemRoles.resetDefaults();
    toast(`Defaults restored: ${result.created} system roles created`, 'success');
    // Reload system roles list
    const sysData = await api.systemRoles.list().catch(() => ({ system_roles: [] }));
    _systemRoles = sysData.system_roles || [];
    _renderSysRolesList();
    // Re-render current role editor system roles section (attachments cleared)
    if (_activeRole) {
      _roleLinks[_activeRole.id] = [];
      _renderRoleSystemRolesSection(_activeRole.id);
    }
  } catch (e) {
    toast('Reset failed: ' + e.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = 'Reset defaults'; }
  }
}

function _rolesProviderChange(provider) {
  const datalist   = document.getElementById('role-model-list');
  const modelInput = document.getElementById('role-model');
  if (datalist) {
    const models = _providerModels(provider);
    datalist.innerHTML = models.map(m => `<option value="${_esc(m)}">`).join('');
    if (modelInput && models.length) modelInput.value = models[0];
  }
  // Reload tools/MCP dropdowns for the new provider
  if (_activeRole) {
    // Pass current selected tools so they survive the provider switch
    const currentTools = _collectTools();
    _loadRoleTools({ ..._activeRole, provider, tools: currentTools });
  }
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
