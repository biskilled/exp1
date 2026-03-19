/**
 * documents.js — Two-pane document browser for workspace/documents/.
 *
 * Left panel: collapsible folder tree.
 * Right panel: file viewer with inline edit and delete.
 * Auto-saved outputs from graph workflow nodes and work-item pipeline stages
 * appear here automatically.
 */

import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';

const TREE_W_KEY = 'aicli_docs_tree_w';

let _project = '';
let _selectedPath = '';

export async function renderDocuments(container, projectName) {
  _project = projectName || '';
  _selectedPath = '';

  container.className = 'view active';
  container.style.cssText = 'display:flex;flex-direction:column;overflow:hidden;height:100%';

  const savedW = parseInt(localStorage.getItem(TREE_W_KEY) || '220');

  container.innerHTML = `
    <div style="display:flex;overflow:hidden;height:100%">
      <!-- Left: file tree -->
      <div id="doc-tree"
           style="width:${savedW}px;flex:none;overflow-y:auto;border-right:1px solid var(--border);
                  display:flex;flex-direction:column">
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:0.5rem 0.75rem;border-bottom:1px solid var(--border)">
          <span style="font-size:0.68rem;color:var(--muted);font-weight:600">documents/</span>
          <button class="btn btn-ghost btn-sm" id="doc-new-btn"
                  style="font-size:0.65rem;padding:0.15rem 0.4rem">+ New</button>
        </div>
        <div id="doc-tree-body" style="flex:1;overflow-y:auto;padding:0.25rem 0">
          <div style="padding:0.75rem;font-size:0.68rem;color:var(--muted)">Loading…</div>
        </div>
      </div>

      <!-- Resize handle -->
      <div id="doc-resize-handle"
           style="width:4px;cursor:col-resize;background:var(--border);flex-shrink:0"
           title="Drag to resize"></div>

      <!-- Right: viewer -->
      <div id="doc-viewer"
           style="flex:1;overflow:hidden;display:flex;flex-direction:column">
        <div style="color:var(--muted);font-size:0.72rem;padding:1.5rem;margin:auto">
          Select a file from the tree
        </div>
      </div>
    </div>
  `;

  _initResizeHandle();
  document.getElementById('doc-new-btn').addEventListener('click', _newDoc);
  await _loadDocs();
}

// ── Resize handle ──────────────────────────────────────────────────────────────

function _initResizeHandle() {
  const handle = document.getElementById('doc-resize-handle');
  const tree   = document.getElementById('doc-tree');
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
    tree.style.width = `${Math.max(160, Math.min(500, startW + (e.clientX - startX)))}px`;
  });
  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    document.body.style.cursor = document.body.style.userSelect = '';
    handle.style.background = 'var(--border)';
    localStorage.setItem(TREE_W_KEY, String(tree.offsetWidth));
  });
}

// ── Tree loading ───────────────────────────────────────────────────────────────

async function _loadDocs() {
  const body = document.getElementById('doc-tree-body');
  if (!body) return;
  try {
    const data = await api.documents.list(_project);
    const flat = data.documents || [];
    if (flat.length === 0) {
      body.innerHTML = `<div style="padding:0.75rem;font-size:0.68rem;color:var(--muted)">No documents yet.</div>`;
      return;
    }
    const tree = _buildTree(flat);
    body.innerHTML = _renderTree(tree, 0);
    _attachTreeEvents(body);
  } catch (e) {
    body.innerHTML = `<div style="padding:0.75rem;font-size:0.68rem;color:var(--red)">${_esc(e.message)}</div>`;
  }
}

// ── Tree building ──────────────────────────────────────────────────────────────

function _buildTree(flat) {
  // flat: [{path: "features/auth/pm_design.md", name, size}]
  // returns {children: {name: node}}
  const root = { name: '', path: '', children: {}, isDir: true };
  for (const item of flat) {
    const parts = item.path.split('/');
    let cur = root;
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (!cur.children[part]) {
        const isDir = i < parts.length - 1;
        const nodePath = parts.slice(0, i + 1).join('/');
        cur.children[part] = { name: part, path: nodePath, isDir, children: {}, size: item.size };
      }
      cur = cur.children[part];
    }
  }
  return root;
}

function _renderTree(node, depth) {
  const pad = depth * 14;
  let html = '';
  const sorted = Object.values(node.children).sort((a, b) => {
    // Dirs first, then files, alphabetical within each group
    if (a.isDir !== b.isDir) return a.isDir ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
  for (const child of sorted) {
    if (child.isDir) {
      const id = `ddir-${child.path.replace(/[^a-z0-9]/gi, '_')}`;
      html += `
        <div class="doc-dir-row" data-dir-id="${id}"
             style="padding:0.3rem 0.5rem 0.3rem ${pad + 8}px;cursor:pointer;
                    font-size:0.7rem;color:var(--muted);display:flex;align-items:center;gap:0.35rem;
                    user-select:none"
             onclick="window._docToggleDir('${id}')">
          <span id="${id}-arrow" style="font-size:0.6rem">▶</span>
          <span>${_esc(child.name)}/</span>
        </div>
        <div id="${id}-children" style="display:none">
          ${_renderTree(child, depth + 1)}
        </div>`;
    } else {
      const isSel = child.path === _selectedPath;
      html += `
        <div class="doc-file-row" data-path="${_esc(child.path)}"
             style="padding:0.3rem 0.5rem 0.3rem ${pad + 8}px;cursor:pointer;
                    font-size:0.7rem;border-radius:3px;
                    ${isSel ? 'background:var(--accent-dim,rgba(99,102,241,.15));color:var(--accent)' : 'color:var(--text)'}">
          ${_esc(child.name)}
        </div>`;
    }
  }
  return html;
}

function _attachTreeEvents(body) {
  body.querySelectorAll('.doc-file-row').forEach(row => {
    row.addEventListener('click', () => _docSelect(row.dataset.path));
  });
}

window._docToggleDir = (id) => {
  const children = document.getElementById(`${id}-children`);
  const arrow    = document.getElementById(`${id}-arrow`);
  if (!children) return;
  const open = children.style.display === 'none';
  children.style.display = open ? '' : 'none';
  if (arrow) arrow.textContent = open ? '▼' : '▶';
};

// ── File viewer ────────────────────────────────────────────────────────────────

async function _docSelect(path) {
  _selectedPath = path;
  // Highlight selected
  document.querySelectorAll('.doc-file-row').forEach(r => {
    const sel = r.dataset.path === path;
    r.style.background = sel ? 'var(--accent-dim,rgba(99,102,241,.15))' : '';
    r.style.color       = sel ? 'var(--accent)' : 'var(--text)';
  });

  const viewer = document.getElementById('doc-viewer');
  if (!viewer) return;
  viewer.innerHTML = `<div style="padding:1rem;font-size:0.7rem;color:var(--muted)">Loading…</div>`;
  try {
    const data = await api.documents.read(path, _project);
    _renderViewer(path, data.content || '');
  } catch (e) {
    viewer.innerHTML = `<div style="padding:1rem;font-size:0.7rem;color:var(--red)">${_esc(e.message)}</div>`;
  }
}

function _renderViewer(path, content) {
  const viewer = document.getElementById('doc-viewer');
  if (!viewer) return;
  viewer.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:0.5rem 0.75rem;border-bottom:1px solid var(--border);flex-shrink:0">
      <span style="font-size:0.68rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
        ${_esc(path)}
      </span>
      <div style="display:flex;gap:0.4rem;flex-shrink:0">
        <button class="btn btn-ghost btn-sm" id="doc-edit-btn"
                style="font-size:0.65rem;padding:0.15rem 0.5rem">Edit</button>
        <button class="btn btn-ghost btn-sm" id="doc-delete-btn"
                style="font-size:0.65rem;padding:0.15rem 0.5rem;color:var(--red)">Delete</button>
      </div>
    </div>
    <pre id="doc-content-pre"
         style="flex:1;overflow:auto;margin:0;padding:1rem;font-size:0.72rem;
                line-height:1.55;white-space:pre-wrap;word-break:break-word">${_esc(content)}</pre>
  `;
  document.getElementById('doc-edit-btn').addEventListener('click', () => _editDoc(path, content));
  document.getElementById('doc-delete-btn').addEventListener('click', () => _deleteDoc(path));
}

function _editDoc(path, content) {
  const viewer = document.getElementById('doc-viewer');
  if (!viewer) return;
  viewer.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:0.5rem 0.75rem;border-bottom:1px solid var(--border);flex-shrink:0">
      <span style="font-size:0.68rem;color:var(--muted)">${_esc(path)}</span>
      <div style="display:flex;gap:0.4rem">
        <button class="btn btn-sm btn-primary" id="doc-save-btn"
                style="font-size:0.65rem;padding:0.15rem 0.5rem">Save</button>
        <button class="btn btn-ghost btn-sm" id="doc-cancel-btn"
                style="font-size:0.65rem;padding:0.15rem 0.5rem">Cancel</button>
      </div>
    </div>
    <textarea id="doc-edit-area"
              style="flex:1;resize:none;border:none;outline:none;padding:1rem;
                     font-size:0.72rem;line-height:1.55;background:var(--bg);color:var(--text);
                     font-family:var(--font-mono,monospace)">${_esc(content)}</textarea>
  `;
  document.getElementById('doc-save-btn').addEventListener('click', async () => {
    const newContent = document.getElementById('doc-edit-area')?.value ?? '';
    await _saveDoc(path, newContent);
  });
  document.getElementById('doc-cancel-btn').addEventListener('click', () => _renderViewer(path, content));
}

async function _saveDoc(path, content) {
  try {
    await api.documents.save(path, content, _project);
    toast('Saved', 'success');
    _renderViewer(path, content);
  } catch (e) {
    toast(`Save failed: ${e.message}`, 'error');
  }
}

async function _deleteDoc(path) {
  if (!confirm(`Delete "${path}"?`)) return;
  try {
    await api.documents.delete(path, _project);
    toast('Deleted', 'success');
    _selectedPath = '';
    document.getElementById('doc-viewer').innerHTML = `
      <div style="color:var(--muted);font-size:0.72rem;padding:1.5rem;margin:auto">
        Select a file from the tree
      </div>`;
    await _loadDocs();
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
}

async function _newDoc() {
  const filename = prompt('New document path (e.g. notes/design.md):');
  if (!filename?.trim()) return;
  const path = filename.trim().replace(/^\/+/, '');
  try {
    await api.documents.save(path, '', _project);
    toast('Created', 'success');
    await _loadDocs();
    await _docSelect(path);
  } catch (e) {
    toast(`Could not create: ${e.message}`, 'error');
  }
}

// ── Utility ────────────────────────────────────────────────────────────────────

function _esc(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
