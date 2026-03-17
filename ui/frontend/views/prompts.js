/**
 * prompts.js — "Roles" tab: manage DB-backed agent roles + workspace prompt files.
 *
 * Left panel has two sections:
 *   1. Agent Roles (DB) — create/edit/delete named roles with system prompts, model, provider
 *   2. Prompt Files — file-browser for workspace prompt markdown files (legacy/custom)
 *
 * Right panel shows the selected role form or file editor.
 */
import { api }      from '../utils/api.js';
import { toast }    from '../utils/toast.js';
import { renderMd } from '../utils/markdown.js';

// ── State ─────────────────────────────────────────────────────────────────────
let _activeFile = '';
let _fileOrig   = '';
let _editMode   = false;
let _activeRole = null;   // {id, name, provider, model, description, system_prompt, ...}
let _roles      = [];
let _project    = null;

const PROVIDERS = ['anthropic', 'openai', 'deepseek', 'gemini', 'xai', 'ollama'];
const MODELS    = {
  anthropic: ['claude-sonnet-4-6', 'claude-haiku-4-5-20251001', 'claude-opus-4-6'],
  openai:    ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo'],
  deepseek:  ['deepseek-chat', 'deepseek-coder'],
  gemini:    ['gemini-1.5-pro', 'gemini-1.5-flash'],
  xai:       ['grok-2-latest', 'grok-vision-beta'],
  ollama:    ['llama3', 'mistral', 'codellama'],
};

// ── Entry point ───────────────────────────────────────────────────────────────

export async function renderPrompts(container, projectName) {
  _activeFile = '';
  _fileOrig   = '';
  _editMode   = false;
  _activeRole = null;
  _project    = projectName;

  const savedW = parseInt(localStorage.getItem('aicli_prompts_tree_w') || '220', 10);

  container.className  = 'view active';
  container.style.cssText = 'display:flex;flex-direction:column;overflow:hidden;height:100%';

  container.innerHTML = `
    <div class="prompts-view" style="flex:1;overflow:hidden">
      <!-- Left panel -->
      <div class="prompts-tree" id="prompts-tree-panel" style="width:${savedW}px;display:flex;flex-direction:column">

        <!-- Agent Roles section -->
        <div class="prompts-tree-header" style="flex-shrink:0">
          <span class="prompts-tree-label">Agent Roles</span>
          <button class="btn btn-ghost btn-sm" style="padding:0.15rem 0.4rem;font-size:0.65rem"
            onclick="window._rolesNew()" title="New role">+</button>
        </div>
        <div id="roles-list-body" style="overflow-y:auto;max-height:40%;flex-shrink:0;border-bottom:1px solid var(--border)">
          <div style="padding:1rem;font-size:0.68rem;color:var(--muted)">Loading…</div>
        </div>

        <!-- Prompt Files section -->
        <div class="prompts-tree-header" style="flex-shrink:0;border-top:none">
          <span class="prompts-tree-label" style="font-size:0.6rem">Prompt Files</span>
          <button class="btn btn-ghost btn-sm" style="padding:0.12rem 0.35rem;font-size:0.6rem"
            onclick="window._promptsNew()" title="New file">+</button>
        </div>
        <div class="prompts-tree-body" id="prompts-tree-body" style="flex:1;overflow-y:auto">
          <div class="empty-state" style="padding:1.5rem">
            <p style="font-size:0.68rem">Loading…</p>
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
  window._rolesNew         = _rolesNew;
  window._rolesSelect      = _rolesSelect;
  window._rolesDelete      = _rolesDelete;
  window._rolesSave        = _rolesSave;
  window._rolesProviderChange = _rolesProviderChange;
  window._promptsNew       = _promptsNew;
  window._promptsSave      = _promptsSave;
  window._promptsToggleMode = _promptsToggleMode;
  window._openPromptFile   = (p) => { _activeRole = null; _openFile(p, projectName); };
  window._toggleFolder     = (id) => {
    const ch = document.getElementById(`folder-children-${id}`);
    const fo = document.getElementById(`folder-${id}`);
    if (!ch || !fo) return;
    const open = ch.style.display !== 'none';
    ch.style.display = open ? 'none' : 'block';
    fo.classList.toggle('open', !open);
  };

  _initPromptsResize();

  if (!projectName) {
    document.getElementById('prompts-tree-body').innerHTML =
      '<div class="empty-state" style="padding:1.5rem"><p>No project open</p></div>';
    document.getElementById('roles-list-body').innerHTML =
      '<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--muted)">No project open</div>';
    return;
  }

  // Load both in parallel
  await Promise.all([_loadRoles(projectName), _loadTree(projectName)]);
}

// ── Agent Roles (DB) ──────────────────────────────────────────────────────────

async function _loadRoles(projectName) {
  const body = document.getElementById('roles-list-body');
  if (!body) return;
  try {
    const data = await api.agentRoles.list(projectName || '_global');
    _roles = data.roles || data || [];
    _renderRolesList();
  } catch (e) {
    body.innerHTML = `<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--red)">${_esc(e.message)}</div>`;
  }
}

function _renderRolesList() {
  const body = document.getElementById('roles-list-body');
  if (!body) return;
  if (!_roles.length) {
    body.innerHTML = `<div style="padding:0.75rem 1rem;font-size:0.68rem;color:var(--muted)">
      No roles yet — click <strong>+</strong> to create one</div>`;
    return;
  }
  body.innerHTML = _roles.map(r => `
    <div onclick="window._rolesSelect(${r.id})"
         style="padding:0.4rem 0.75rem;cursor:pointer;border-bottom:1px solid var(--border);
                display:flex;align-items:center;gap:0.5rem;
                background:${_activeRole?.id === r.id ? 'var(--accent)18' : 'transparent'};
                border-left:2px solid ${_activeRole?.id === r.id ? 'var(--accent)' : 'transparent'}"
         onmouseenter="if(!${_activeRole?.id === r.id})this.style.background='var(--surface2)'"
         onmouseleave="if(!${_activeRole?.id === r.id})this.style.background='${_activeRole?.id === r.id ? 'var(--accent)18' : 'transparent'}'">
      <span style="font-size:0.62rem;color:var(--muted);flex-shrink:0">≡</span>
      <div style="flex:1;min-width:0">
        <div style="font-size:0.7rem;font-weight:500;color:var(--text);
                    overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(r.name)}</div>
        <div style="font-size:0.55rem;color:var(--muted)">${_esc(r.provider || '')} ${r.model ? '· ' + _esc(r.model) : ''}</div>
      </div>
    </div>
  `).join('');
}

async function _rolesNew() {
  const name = prompt('Role name (e.g. "Senior Developer"):');
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

function _rolesSelect(id) {
  _activeFile = '';
  const role = _roles.find(r => r.id === id);
  if (!role) return;
  _activeRole = role;
  _renderRolesList();
  _renderRoleEditor(role);
  const pathEl = document.getElementById('prompts-path');
  if (pathEl) pathEl.textContent = `Role: ${role.name}`;
}

function _renderRoleEditor(role) {
  const body    = document.getElementById('prompts-editor-body');
  const toolbar = document.getElementById('prompts-toolbar');
  if (!body) return;

  if (toolbar) toolbar.innerHTML = `
    <span class="prompts-editor-path" id="prompts-path">Role: ${_esc(role.name)}</span>
    <button class="btn btn-ghost btn-sm" style="color:var(--red);border-color:var(--red);font-size:0.62rem"
      onclick="window._rolesDelete(${role.id})">Delete</button>
    <button class="btn btn-primary btn-sm" id="roles-save-btn"
      onclick="window._rolesSave(${role.id})">Save</button>
  `;

  const modelsForProvider = (MODELS[role.provider] || []).concat(role.model && !(MODELS[role.provider]||[]).includes(role.model) ? [role.model] : []);

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
          <select id="role-provider" onchange="window._rolesProviderChange(this.value)"
            style="width:100%;background:var(--bg);border:1px solid var(--border);
                   color:var(--text);font-family:var(--font);font-size:0.72rem;padding:0.35rem 0.5rem;
                   border-radius:var(--radius);outline:none">
            ${PROVIDERS.map(p => `<option value="${p}" ${role.provider === p ? 'selected' : ''}>${p}</option>`).join('')}
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
}

async function _rolesSave(id) {
  const name         = document.getElementById('role-name')?.value?.trim();
  const provider     = document.getElementById('role-provider')?.value;
  const model        = document.getElementById('role-model')?.value?.trim();
  const description  = document.getElementById('role-description')?.value?.trim();
  const systemPrompt = document.getElementById('role-system-prompt')?.value;
  if (!name) { toast('Name required', 'error'); return; }
  try {
    const updated = await api.agentRoles.patch(id, { name, provider, model, description, system_prompt: systemPrompt });
    const idx = _roles.findIndex(r => r.id === id);
    if (idx !== -1) _roles[idx] = { ..._roles[idx], ...updated, name, provider, model, description, system_prompt: systemPrompt };
    _activeRole = _roles[idx] || _activeRole;
    _renderRolesList();
    toast('Role saved', 'success');
  } catch (e) { toast('Save failed: ' + e.message, 'error'); }
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
  if (!datalist) return;
  datalist.innerHTML = (MODELS[provider] || []).map(m => `<option value="${_esc(m)}">`).join('');
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
