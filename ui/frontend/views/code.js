/**
 * code.js — Code browser: resizable file-tree and syntax-highlighted file viewer.
 *
 * Renders a two-panel code explorer for the project's configured code_dir, with a
 * resizable file tree on the left and a read-only syntax-highlighted viewer on the right;
 * supports directory selection via Electron's native dialog or manual path entry.
 * Rendered via: renderCode() called from main.js navigateTo().
 */

import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';

let _selectedFiles = new Set();  // paths of files checked for deletion
let _selectMode    = false;      // true when select/delete mode is active

export async function renderCode(container, projectName, project) {
  container.className = 'view active';
  container.style.cssText = 'display:flex;flex-direction:column;overflow:hidden;height:100%';

  const codeDir = project?.code_dir || '';
  const savedW  = parseInt(localStorage.getItem('ad_code_tree_w') || '200');

  container.innerHTML = `
    <div style="display:flex;flex-direction:column;overflow:hidden;height:100%">
      <div class="code-view-header">
        <span style="color:var(--muted)">Code folder:</span>
        <span id="code-dir-path"
              style="color:var(--text);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
          ${codeDir || '<span style="color:var(--muted)">Not configured</span>'}
        </span>
        <button class="btn btn-ghost btn-sm" onclick="window._changeCodeDir()">Change…</button>
      </div>

      <div style="flex:1;display:flex;overflow:hidden">
        <!-- Resizable file tree -->
        <div style="width:${savedW}px;flex:none;display:flex;flex-direction:column;overflow:hidden">
          <div id="code-tree-toolbar"
               style="padding:0.3rem 0.5rem;border-bottom:1px solid var(--border);
                      display:flex;align-items:center;gap:0.4rem;flex-shrink:0;font-size:0.65rem">
            <button id="code-select-btn" class="btn btn-ghost btn-sm"
                    style="font-size:0.62rem;padding:0.15rem 0.4rem"
                    onclick="window._toggleSelectMode()">☐ Select</button>
            <button id="code-delete-btn" class="btn btn-sm"
                    style="font-size:0.62rem;padding:0.15rem 0.4rem;display:none;
                           background:#dc2626;color:#fff;border:none;border-radius:4px;cursor:pointer"
                    onclick="window._deleteSelected()">🗑 Delete (0)</button>
          </div>
          <div class="code-file-tree" id="code-file-tree"
               style="flex:1;overflow-y:auto">
            <div style="padding:0.5rem 0.75rem;font-size:0.65rem;color:var(--muted)">Loading…</div>
          </div>
        </div>

        <!-- Drag handle -->
        <div id="code-resize-handle"
             style="width:4px;cursor:col-resize;background:var(--border);flex-shrink:0"
             title="Drag to resize panel"></div>

        <!-- File viewer -->
        <div class="code-viewer" id="code-viewer"
             style="flex:1;overflow:hidden;display:flex;flex-direction:column">
          <div style="color:var(--muted);font-size:0.72rem;padding:1.5rem;margin:auto">
            Select a file from the tree
          </div>
        </div>
      </div>
    </div>
  `;

  _initResizeHandle();

  window._changeCodeDir = async () => {
    let dir = null;
    if (window.electronAPI?.openDirectory) {
      dir = await window.electronAPI.openDirectory();
    } else {
      dir = prompt('Code folder path:', codeDir || '');
    }
    if (!dir || !projectName) return;
    try {
      await api.updateProjectConfig(projectName, { code_dir: dir });
      toast('Code folder updated — restart backend to apply', 'success');
      document.getElementById('code-dir-path').textContent = dir;
    } catch (e) {
      toast(`Error: ${e.message}`, 'error');
    }
  };

  await _loadFileTree();
}

// ── Drag-to-resize ─────────────────────────────────────────────────────────────

function _initResizeHandle() {
  const handle = document.getElementById('code-resize-handle');
  const tree   = document.getElementById('code-file-tree');
  if (!handle || !tree) return;

  let dragging = false, startX = 0, startW = 0;

  handle.addEventListener('mousedown', (e) => {
    dragging = true; startX = e.clientX; startW = tree.offsetWidth;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });
  handle.addEventListener('mouseover', () => { handle.style.background = 'var(--accent)'; });
  handle.addEventListener('mouseout',  () => { if (!dragging) handle.style.background = 'var(--border)'; });

  document.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    tree.style.width = `${Math.max(120, Math.min(600, startW + (e.clientX - startX)))}px`;
  });
  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    document.body.style.cursor = document.body.style.userSelect = '';
    handle.style.background = 'var(--border)';
    localStorage.setItem('ad_code_tree_w', String(tree.offsetWidth));
  });
}

// ── File tree ──────────────────────────────────────────────────────────────────

async function _loadFileTree() {
  const tree = document.getElementById('code-file-tree');
  if (!tree) return;
  try {
    const data = await api.getFiles(4);
    if (!data || data.name === '(no code_dir)') {
      tree.innerHTML = `<div class="empty-state" style="padding:1.25rem">
        <p style="font-size:0.68rem">No code folder configured.</p>
        <p style="font-size:0.62rem;color:var(--muted);margin-top:0.3rem">
          Click <strong>Change…</strong> to set the code directory.</p></div>`;
      return;
    }
    // Show children of root directly; skip wrapping root node
    const nodes = data.type === 'dir' ? (data.children || []) : [data];
    let counter = 0;
    tree.innerHTML = nodes.map(n => _renderNode(n, 0, () => counter++)).join('');
  } catch (e) {
    tree.innerHTML = `<div style="padding:0.75rem;font-size:0.68rem;color:var(--red)">${_esc(e.message)}</div>`;
  }
}

function _renderNode(node, depth, nextId) {
  if (!node) return '';
  const pad = depth * 12;

  if (node.type === 'dir') {
    const id       = `cd${nextId()}`;
    const children = (node.children || []).map(c => _renderNode(c, depth + 1, nextId)).join('');
    return `
      <div class="code-dir-row" style="padding-left:${pad}px"
           onclick="window._toggleCodeDir('${id}')">
        <span id="${id}-icon" style="display:inline-block;width:10px;font-size:0.58rem;
               color:var(--accent);transition:transform 0.15s">▸</span>
        <span>${_esc(node.name)}/</span>
      </div>
      <div id="${id}-ch" style="display:none">${children}</div>`;
  }

  const safePath = _esc(node.path);
  return `
    <div class="code-file-item" data-path="${safePath}"
         style="padding-left:${pad + 14}px;display:flex;align-items:center;gap:0.3rem"
         onclick="window._codeFileClick('${safePath}')">
      <input type="checkbox" class="code-file-cb" data-path="${safePath}"
             style="display:none;flex-shrink:0;cursor:pointer;accent-color:var(--accent)"
             onclick="event.stopPropagation();window._toggleFileSelect('${safePath}',this)">
      <span class="code-file-dot" style="font-size:0.55rem;color:var(--muted)">·</span>
      <span>${_esc(node.name)}</span>
    </div>`;
}

window._toggleCodeDir = (id) => {
  const ch   = document.getElementById(`${id}-ch`);
  const icon = document.getElementById(`${id}-icon`);
  if (!ch) return;
  const open = ch.style.display !== 'none';
  ch.style.display     = open ? 'none'  : 'block';
  icon.style.transform = open ? ''      : 'rotate(90deg)';
};

window._codeFileClick = (path) => {
  if (_selectMode) {
    const cb = document.querySelector(`.code-file-cb[data-path="${CSS.escape(path)}"]`);
    if (cb) { cb.checked = !cb.checked; window._toggleFileSelect(path, cb); }
  } else {
    window._viewCodeFile(path);
  }
};

window._toggleSelectMode = () => {
  _selectMode = !_selectMode;
  _selectedFiles.clear();
  const btn = document.getElementById('code-select-btn');
  const delBtn = document.getElementById('code-delete-btn');
  if (btn) btn.textContent = _selectMode ? '✕ Cancel' : '☐ Select';
  // Show/hide checkboxes
  document.querySelectorAll('.code-file-cb').forEach(cb => {
    cb.style.display = _selectMode ? 'inline-block' : 'none';
    cb.checked = false;
  });
  if (delBtn) { delBtn.style.display = 'none'; delBtn.textContent = '🗑 Delete (0)'; }
};

window._toggleFileSelect = (path, cb) => {
  if (cb.checked) _selectedFiles.add(path); else _selectedFiles.delete(path);
  const delBtn = document.getElementById('code-delete-btn');
  if (delBtn) {
    const n = _selectedFiles.size;
    delBtn.style.display = n > 0 ? 'inline-block' : 'none';
    delBtn.textContent = `🗑 Delete (${n})`;
  }
};

window._deleteSelected = async () => {
  if (!_selectedFiles.size) return;
  const paths = [..._selectedFiles];
  if (!confirm(`Delete ${paths.length} file${paths.length > 1 ? 's' : ''}?\n${paths.join('\n')}`)) return;
  try {
    const res = await api.deleteFiles(paths);
    const n = res.deleted?.length || 0;
    const errs = res.errors || [];
    if (errs.length) toast(`Deleted ${n}, ${errs.length} error(s): ${errs[0]}`, 'warning');
    else toast(`Deleted ${n} file${n > 1 ? 's' : ''}`, 'success');
    _selectMode = false;
    _selectedFiles.clear();
    await _loadFileTree();
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
};

// ── File viewer ────────────────────────────────────────────────────────────────

window._viewCodeFile = async (path) => {
  const viewer = document.getElementById('code-viewer');
  if (!viewer) return;

  document.querySelectorAll('.code-file-item').forEach(el =>
    el.classList.toggle('active', el.dataset.path === path)
  );

  viewer.innerHTML = '<div style="color:var(--muted);font-size:0.68rem;padding:1.5rem;margin:auto">Loading…</div>';

  try {
    const data    = await api.readFile(path);
    const content = data.content || '';
    const lines   = content.split('\n').length;
    const btnId   = `cp${Date.now()}`;

    viewer.innerHTML = `
      <div style="display:flex;align-items:center;gap:0.5rem;padding:0.4rem 0.75rem;
                  border-bottom:1px solid var(--border);flex-shrink:0;background:var(--surface)">
        <span style="font-size:0.65rem;color:var(--text2);flex:1;overflow:hidden;
                     text-overflow:ellipsis;white-space:nowrap">${_esc(path)}</span>
        <span style="font-size:0.6rem;color:var(--muted)">${lines} lines</span>
        <button class="btn btn-ghost btn-sm" id="${btnId}">Copy</button>
      </div>
      <div style="flex:1;overflow:auto">
        <pre style="padding:1rem;margin:0;font-family:var(--font);font-size:0.74rem;
                    line-height:1.7;white-space:pre;tab-size:2;color:var(--text)">${_esc(content)}</pre>
      </div>`;

    document.getElementById(btnId)?.addEventListener('click', function () {
      navigator.clipboard.writeText(content);
      this.textContent = 'Copied!';
      setTimeout(() => { this.textContent = 'Copy'; }, 1500);
    });

  } catch (e) {
    viewer.innerHTML = `<div style="padding:1rem;font-size:0.68rem;color:var(--red)">${_esc(e.message)}</div>`;
  }
};

function _esc(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
