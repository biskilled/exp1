import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { renderMd } from '../utils/markdown.js';

let _original   = '';
let _activePath = '';
let _editMode   = false;

export async function renderPrompts(container, projectName) {
  _original   = '';
  _activePath = '';
  _editMode   = false;

  container.className = 'view active';
  container.style.cssText = 'display:flex;flex-direction:column;overflow:hidden;height:100%';

  const _savedTreeW = parseInt(localStorage.getItem('aicli_prompts_tree_w') || '200', 10);

  container.innerHTML = `
    <div class="prompts-view" style="flex:1;overflow:hidden">
      <!-- File tree -->
      <div class="prompts-tree" id="prompts-tree-panel" style="width:${_savedTreeW}px">
        <div class="prompts-tree-header">
          <span class="prompts-tree-label">Prompts</span>
          <button class="btn btn-ghost btn-sm" style="padding:0.15rem 0.4rem;font-size:0.65rem"
            onclick="window._promptsNew()" title="New file">+</button>
        </div>
        <div class="prompts-tree-body" id="prompts-tree-body">
          <div class="empty-state" style="padding:1.5rem">
            <p style="font-size:0.68rem">Loading…</p>
          </div>
        </div>
      </div>

      <!-- Tree resize handle -->
      <div id="prompts-resize-handle"
           style="width:4px;cursor:col-resize;background:var(--border);flex-shrink:0"
           title="Drag to resize panel"></div>

      <!-- Editor / viewer -->
      <div class="prompts-editor-area">
        <div class="prompts-editor-toolbar" id="prompts-toolbar">
          <span class="prompts-editor-path" id="prompts-path">Select a file to edit</span>
          <!-- mode toggle + save injected here when file is open -->
        </div>
        <div id="prompts-editor-body"
          style="flex:1;display:flex;align-items:center;justify-content:center;
                 color:var(--muted);font-size:0.72rem">
          <span>Select a file from the tree</span>
        </div>
      </div>
    </div>
  `;

  window._promptsNew = async () => {
    const name = prompt('File name (e.g. roles/assistant.md):');
    if (!name) return;
    try {
      await api.writePrompt(name, '', projectName);
      toast(`Created ${name}`, 'success');
      await _loadTree(projectName);
      await _openFile(name, projectName);
    } catch (e) {
      toast(`Error: ${e.message}`, 'error');
    }
  };

  window._promptsSave = async () => {
    const ta = document.getElementById('prompts-textarea');
    if (!ta || !_activePath) return;
    try {
      await api.writePrompt(_activePath, ta.value, projectName);
      _original = ta.value;
      _setSaveBtn(false);
      toast('Saved', 'success');
    } catch (e) {
      toast(`Save failed: ${e.message}`, 'error');
    }
  };

  window._promptsToggleMode = () => {
    _editMode = !_editMode;
    _renderEditorArea(_activePath, projectName);
  };

  _initPromptsResize();

  if (!projectName) {
    document.getElementById('prompts-tree-body').innerHTML =
      '<div class="empty-state" style="padding:1.5rem"><p>No project open</p></div>';
    return;
  }

  await _loadTree(projectName);
}

// ── Tree panel resize ─────────────────────────────────────────────────────────

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
    panel.style.width = `${Math.max(120, Math.min(500, startW + (e.clientX - startX)))}px`;
  });
  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    document.body.style.cursor = document.body.style.userSelect = '';
    handle.style.background = 'var(--border)';
    localStorage.setItem('aicli_prompts_tree_w', String(panel.offsetWidth));
  });
}

// ── File tree ─────────────────────────────────────────────────────────────────

async function _loadTree(projectName) {
  const body = document.getElementById('prompts-tree-body');
  if (!body) return;

  try {
    const data = await api.listPrompts(projectName);
    const files = data.files || data.prompts || [];

    if (!files.length) {
      body.innerHTML = '<div class="empty-state" style="padding:1.5rem"><p style="font-size:0.68rem">No prompt files yet</p></div>';
      return;
    }

    const tree = _buildTree(files);
    body.innerHTML = _renderTree(tree);

    if (_activePath) {
      document.querySelectorAll('.tree-file').forEach(el =>
        el.classList.toggle('active', el.dataset.path === _activePath)
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
      <div class="tree-file ${file === _activePath ? 'active' : ''}"
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

window._toggleFolder = (id) => {
  const ch     = document.getElementById(`folder-children-${id}`);
  const folder = document.getElementById(`folder-${id}`);
  if (!ch || !folder) return;
  const open = ch.style.display !== 'none';
  ch.style.display = open ? 'none' : 'block';
  folder.classList.toggle('open', !open);
};

window._openPromptFile = async (path) => {
  const { state } = await import('../stores/state.js');
  const projectName = state.currentProject?.name;
  if (!projectName) return;
  await _openFile(path, projectName);
};

async function _openFile(path, projectName) {
  _activePath = path;
  _editMode   = false;   // reset to view mode on new file

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
    _original = data.content || '';
    _renderEditorArea(path, projectName);
  } catch (e) {
    bodyEl.innerHTML = `<div style="padding:1rem;font-size:0.68rem;color:var(--red)">${_esc(e.message)}</div>`;
  }
}

// ── Editor area (called when mode toggles) ────────────────────────────────────

function _renderEditorArea(path, projectName) {
  const bodyEl   = document.getElementById('prompts-editor-body');
  const toolbar  = document.getElementById('prompts-toolbar');
  if (!bodyEl || !toolbar) return;

  const isMd = (path || '').endsWith('.md');

  // Toolbar
  _updateToolbar(toolbar, path, isMd);

  if (_editMode || !isMd) {
    // ── Raw editor ──
    bodyEl.style.cssText = 'flex:1;display:flex;flex-direction:column;overflow:hidden';
    bodyEl.innerHTML = '';

    const ta = document.createElement('textarea');
    ta.className = 'prompts-textarea';
    ta.id = 'prompts-textarea';
    ta.value = _original;
    bodyEl.appendChild(ta);

    _setSaveBtn(false);

    ta.addEventListener('input', () => {
      _setSaveBtn(ta.value !== _original);
    });
    ta.addEventListener('keydown', e => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        const btn = document.getElementById('prompts-save-btn');
        if (btn && !btn.disabled) window._promptsSave();
      }
    });
    ta.focus();

  } else {
    // ── Markdown preview ──
    bodyEl.style.cssText = 'flex:1;overflow-y:auto';
    bodyEl.innerHTML = `<div class="prompt-md-view" style="padding:1.5rem 2rem">${renderMd(_original)}</div>`;
  }
}

function _updateToolbar(toolbar, path, isMd) {
  const pathEl = document.getElementById('prompts-path');
  const currentPath = pathEl?.textContent || path;

  // Keep path span, rebuild buttons
  toolbar.innerHTML = `
    <span class="prompts-editor-path" id="prompts-path">${_esc(currentPath)}</span>
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
      </div>
    ` : ''}
    <button class="btn btn-primary btn-sm" id="prompts-save-btn"
      disabled style="opacity:0.4" onclick="window._promptsSave()">Save</button>
  `;
}

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

function _slugify(s) {
  return s.replace(/[^a-zA-Z0-9]/g, '_');
}
