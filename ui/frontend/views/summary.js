import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { renderMd } from '../utils/markdown.js';

export async function renderSummary(container, projectName) {
  container.className = 'view active summary-view';
  container.innerHTML = `
    <div class="summary-toolbar">
      <span style="font-size:0.65rem;color:var(--muted);flex:1">
        ${projectName ? `PROJECT.md — ${projectName}` : 'No project open'}
      </span>
      <button class="btn btn-ghost btn-sm" id="summary-ctx-btn" title="Rebuild CONTEXT.md from PROJECT.md + history"
              onclick="window._summaryRefreshContext()">↺ Context</button>
      <button class="btn btn-ghost btn-sm" id="summary-edit-btn" onclick="window._summaryToggleEdit()">Edit</button>
      <button class="btn btn-primary btn-sm" id="summary-save-btn" disabled style="opacity:0.4" onclick="window._summarySave()">Save</button>
    </div>
    <div id="summary-body" class="summary-content">
      <div class="empty-state"><div class="empty-state-icon">📄</div><p>Loading…</p></div>
    </div>
  `;

  if (!projectName) {
    document.getElementById('summary-body').innerHTML =
      '<div class="empty-state"><div class="empty-state-icon">◫</div><p>No project open</p><p style="font-size:0.68rem;margin-top:0.3rem;color:var(--muted)">Open a project from the Projects view.</p></div>';
    return;
  }

  let _original = '';
  let _editMode = false;

  const editBtn = document.getElementById('summary-edit-btn');
  const saveBtn = document.getElementById('summary-save-btn');
  const body    = document.getElementById('summary-body');

  function _trackSave(textarea) {
    saveBtn.disabled = true;
    saveBtn.style.opacity = '0.4';
    textarea.addEventListener('input', () => {
      const changed = textarea.value !== _original;
      saveBtn.disabled = !changed;
      saveBtn.style.opacity = changed ? '1' : '0.4';
    });
    // Cmd+S / Ctrl+S
    textarea.addEventListener('keydown', e => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        if (!saveBtn.disabled) window._summarySave();
      }
    });
  }

  window._summaryToggleEdit = () => {
    _editMode = !_editMode;
    if (_editMode) {
      editBtn.textContent = 'Preview';
      body.className = '';
      body.style.cssText = 'flex:1;display:flex;flex-direction:column;overflow:hidden';
      const ta = document.createElement('textarea');
      ta.className = 'summary-textarea';
      ta.id = 'summary-textarea';
      ta.value = _original;
      body.innerHTML = '';
      body.appendChild(ta);
      _trackSave(ta);
      ta.focus();
    } else {
      editBtn.textContent = 'Edit';
      const ta = document.getElementById('summary-textarea');
      if (ta) _original = ta.value;
      body.className = 'summary-content';
      body.style.cssText = '';
      body.innerHTML = `<div class="summary-md">${renderMd(_original)}</div>`;
      saveBtn.disabled = true;
      saveBtn.style.opacity = '0.4';
    }
  };

  window._summaryRefreshContext = async () => {
    const btn = document.getElementById('summary-ctx-btn');
    if (btn) { btn.disabled = true; btn.textContent = '…'; }
    try {
      await api.getProjectContext(projectName, true);
      toast('CONTEXT.md rebuilt and saved', 'success');
    } catch (e) {
      toast(`Context refresh failed: ${e.message}`, 'error');
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '↺ Context'; }
    }
  };

  window._summarySave = async () => {
    const ta = document.getElementById('summary-textarea');
    if (!ta) return;
    const content = ta.value;
    try {
      await api.updateProjectSummary(projectName, content);
      _original = content;
      saveBtn.disabled = true;
      saveBtn.style.opacity = '0.4';
      toast('PROJECT.md saved', 'success');
    } catch (e) {
      toast(`Save failed: ${e.message}`, 'error');
    }
  };

  // Load PROJECT.md via dedicated summary endpoint
  try {
    const data = await api.getProjectSummary(projectName);
    _original = data.content || '';
    body.className = 'summary-content';
    body.innerHTML = `<div class="summary-md">${renderMd(_original)}</div>`;
  } catch {
    // File might not exist yet — show default template
    _original = `# ${projectName}\n\nProject description goes here.\n`;
    body.className = 'summary-content';
    body.innerHTML = `<div class="summary-md">${renderMd(_original)}</div>
      <p style="font-size:0.68rem;color:var(--muted);margin-top:1rem">
        No PROJECT.md found. Click <strong>Edit</strong> to create one.
      </p>`;
  }
}
