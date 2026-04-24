/**
 * summary.js — Project summary: PROJECT.md viewer and memory dashboard.
 *
 * Renders the active project's PROJECT.md with toggle between rendered markdown and
 * raw edit mode, alongside cards for Memory Health, Project Facts, and LLM-synthesized
 * memory digest; supports context rebuild and inline save via Cmd+S.
 * Rendered via: renderSummary() called from main.js navigateTo().
 */

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

  // ── Project Facts card (rendered above Memory Health) ────────────────────────
  let _factsCardEl = null;
  async function _renderFactsCard() {
    try {
      const data = await api.wi.facts(projectName);
      const facts = data.facts || [];
      if (!facts.length) { _factsCardEl.innerHTML = ''; return; }
      const rows = facts.map(f =>
        `<tr>
          <td style="padding:0.18rem 0.6rem 0.18rem 0;font-weight:500;white-space:nowrap;
                     font-size:0.67rem;color:var(--text)">${f.fact_key}</td>
          <td style="padding:0.18rem 0;font-size:0.67rem;color:var(--text2)">${f.fact_value}</td>
         </tr>`
      ).join('');
      const updatedAt = facts[0]?.valid_from?.slice(0, 10) || '';
      _factsCardEl.innerHTML = `
        <div style="border:1px solid var(--border);border-radius:8px;background:var(--surface);
                    padding:0.65rem 1rem;font-size:0.72rem">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem">
            <span style="font-size:0.95rem">📌</span>
            <strong style="font-size:0.75rem">Project Facts</strong>
            ${updatedAt ? `<span style="margin-left:auto;color:var(--muted);font-size:0.62rem">updated: ${updatedAt}</span>` : ''}
          </div>
          <table style="border-collapse:collapse;width:100%">${rows}</table>
        </div>
      `;
    } catch {
      _factsCardEl.innerHTML = '';  // hide if endpoint unavailable
    }
  }

  // ── Memory Health card (rendered above PROJECT.md) ───────────────────────────
  let _memCardEl = null;
  async function _renderMemoryCard() {
    try {
      const s = await api.getMemoryStatus(projectName);
      const needs = s.needs_memory;
      const n     = s.prompts_since_last_memory || 0;
      const total = s.total_prompts || 0;
      const days  = s.days_since_last_memory;
      const last  = s.last_memory_run
        ? s.last_memory_run.slice(0, 10) + (days != null ? ` (${days}d ago)` : '')
        : 'Never';
      const border = needs ? '#ffc107' : '#27ae60';
      const bg     = needs ? '#fff8e1' : '#f0faf4';
      const icon   = needs ? '⚠️' : '✅';

      _memCardEl.innerHTML = `
        <div style="border:1px solid ${border};border-radius:8px;background:${bg};
                    padding:0.75rem 1rem;font-size:0.72rem;color:var(--text)">
          <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem">
            <span style="font-size:1rem">${icon}</span>
            <strong style="font-size:0.78rem">Memory Health</strong>
            <span style="margin-left:auto;color:var(--muted);font-size:0.65rem">
              Last run: ${last}
            </span>
          </div>
          <div style="display:flex;align-items:center;gap:1rem">
            <span>New prompts: <strong>${n}</strong>${needs ? ` ⚠ (threshold: ${s.threshold})` : ` / ${s.threshold}`}</span>
            <span style="color:var(--muted)">Total: ${total}</span>
            ${needs ? `<button id="summary-run-memory"
              style="margin-left:auto;background:#ffc107;border:none;color:#000;font-size:0.62rem;
                     padding:0.2rem 0.65rem;border-radius:4px;cursor:pointer;font-family:inherit;
                     font-weight:600">Run /memory Now</button>` : ''}
          </div>
        </div>
      `;

      document.getElementById('summary-run-memory')?.addEventListener('click', async () => {
        const btn = document.getElementById('summary-run-memory');
        if (btn) { btn.disabled = true; btn.textContent = '…'; }
        try {
          await api.generateMemory(projectName);
          toast('/memory completed — memory files refreshed', 'success');
          await _renderMemoryCard();
        } catch (e) {
          toast(`/memory failed: ${e.message}`, 'error');
          if (btn) { btn.disabled = false; btn.textContent = 'Run /memory Now'; }
        }
      });
    } catch {
      _memCardEl.innerHTML = '';  // hide if endpoint unavailable
    }
  }

  // ── Build the card placeholder elements (rendered into body before md) ──────
  _factsCardEl = document.createElement('div');
  _factsCardEl.id = 'summary-facts-card';
  _factsCardEl.style.cssText = 'margin:0.75rem 0 0.4rem 0;';

  _memCardEl = document.createElement('div');
  _memCardEl.id = 'summary-memory-card';
  _memCardEl.style.cssText = 'margin:0.75rem 0;';
  // Show a lightweight skeleton so layout doesn't jump
  _memCardEl.innerHTML = `
    <div style="border:1px solid var(--border);border-radius:8px;background:var(--surface);
                padding:0.65rem 1rem;font-size:0.72rem;color:var(--muted);
                display:flex;align-items:center;gap:0.5rem">
      <span style="font-size:0.85rem">⏳</span> Checking memory health…
    </div>`;

  const mdDiv = document.createElement('div');

  // ── Step 1: fetch PROJECT.md and render immediately ──────────────────────────
  try {
    const data = await api.getProjectSummary(projectName);
    _original = data.content || '';
    mdDiv.className = 'summary-md';
    mdDiv.innerHTML = renderMd(_original);
  } catch {
    _original = `# ${projectName}\n\nProject description goes here.\n`;
    mdDiv.innerHTML = `<div class="summary-md">${renderMd(_original)}</div>
      <p style="font-size:0.68rem;color:var(--muted);margin-top:1rem">
        No PROJECT.md found. Click <strong>Edit</strong> to create one.
      </p>`;
  }

  // Render skeleton + markdown immediately — user sees content at once
  body.className = 'summary-content';
  body.innerHTML = '';
  body.appendChild(_factsCardEl);
  body.appendChild(_memCardEl);
  body.appendChild(mdDiv);

  // ── Step 2: load cards in background (don't block initial render) ────────────
  _renderFactsCard().catch(() => {});
  _renderMemoryCard().catch(() => {});
}
