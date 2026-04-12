/**
 * workflowPicker.js — Shared modal for triggering a workflow from a feature snapshot use case.
 *
 * Usage:
 *   import { showWorkflowPicker } from '../utils/workflowPicker.js';
 *   const runId = await showWorkflowPicker(tagId, ucNum, ucSummary, project);
 */

import { api } from './api.js';
import { toast } from './toast.js';

/**
 * Show a modal to pick a workflow and trigger it from a snapshot use case.
 * @param {string} tagId  - planner_tag UUID
 * @param {number} ucNum  - use_case_num
 * @param {string} ucSummary - use case summary text (shown as preview)
 * @param {string} project - project name
 * @returns {Promise<string|null>} run_id if triggered, null if cancelled
 */
export async function showWorkflowPicker(tagId, ucNum, ucSummary, project) {
  return new Promise(async (resolve) => {
    // Remove any existing picker
    document.getElementById('workflow-picker-overlay')?.remove();

    // Fetch templates + workflows
    let templates = {};
    let workflows = [];
    try {
      const data = await api.pipeline.templates(project);
      templates = data.templates || {};
      workflows = data.workflows || [];
    } catch (e) {
      console.warn('workflowPicker: failed to load templates', e);
    }

    if (!workflows.length) {
      toast('No workflows configured for this project', 'warning');
      resolve(null);
      return;
    }

    const overlay = document.createElement('div');
    overlay.id = 'workflow-picker-overlay';
    overlay.style.cssText =
      'position:fixed;inset:0;z-index:9500;display:flex;align-items:center;justify-content:center;' +
      'background:rgba(0,0,0,0.65);backdrop-filter:blur(4px)';

    const preview = (ucSummary || '').slice(0, 200);

    overlay.innerHTML = `
      <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
                  width:440px;max-width:95vw;padding:1.5rem;box-shadow:0 8px 32px rgba(0,0,0,0.4)">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem">
          <h3 style="margin:0;font-size:1rem">Run Workflow &mdash; Use Case ${ucNum}</h3>
          <button id="wfp-cancel-btn" style="background:none;border:none;color:var(--muted);font-size:1.2rem;
                  cursor:pointer;padding:0.2rem 0.4rem;line-height:1">&#10005;</button>
        </div>
        ${preview ? `
        <div style="font-size:0.78rem;color:var(--muted);background:var(--surface2);border-radius:var(--radius);
                    padding:0.6rem 0.75rem;margin-bottom:1rem;line-height:1.5;max-height:80px;overflow:hidden">
          ${preview}${ucSummary && ucSummary.length > 200 ? '&hellip;' : ''}
        </div>` : ''}
        <div style="margin-bottom:1rem">
          <label style="font-size:0.78rem;font-weight:600;color:var(--text);display:block;margin-bottom:0.5rem">
            Select workflow:
          </label>
          <div id="wfp-workflow-list" style="display:flex;flex-direction:column;gap:0.4rem;max-height:200px;overflow-y:auto">
            ${workflows.map((wf, i) => `
              <label style="display:flex;align-items:center;gap:0.5rem;padding:0.5rem 0.65rem;
                            border-radius:var(--radius);border:1px solid var(--border);cursor:pointer;
                            font-size:0.8rem;background:var(--surface2)">
                <input type="radio" name="wfp-wf" value="${wf.id}" ${i === 0 ? 'checked' : ''}
                       style="accent-color:var(--accent)">
                <span>${wf.name}</span>
                <span style="color:var(--muted);margin-left:auto;font-size:0.7rem">${wf.node_count} node${wf.node_count !== 1 ? 's' : ''}</span>
              </label>
            `).join('')}
          </div>
        </div>
        <div style="display:flex;justify-content:flex-end;gap:0.5rem">
          <button id="wfp-cancel2-btn" class="btn btn-ghost btn-sm">Cancel</button>
          <button id="wfp-run-btn" class="btn btn-primary btn-sm">&#9654; Run</button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    const _close = (result = null) => {
      overlay.remove();
      resolve(result);
    };

    overlay.querySelector('#wfp-cancel-btn').onclick = () => _close(null);
    overlay.querySelector('#wfp-cancel2-btn').onclick = () => _close(null);
    overlay.addEventListener('click', (e) => { if (e.target === overlay) _close(null); });

    overlay.querySelector('#wfp-run-btn').onclick = async () => {
      const checked = overlay.querySelector('input[name="wfp-wf"]:checked');
      if (!checked) return;
      const wfId = checked.value;
      const btn = overlay.querySelector('#wfp-run-btn');
      btn.disabled = true;
      btn.textContent = 'Starting\u2026';
      try {
        const result = await api.pipeline.runFromSnapshot(tagId, ucNum, project, wfId);
        toast(`Workflow started: ${result.workflow_name || wfId}`, 'success');
        _close(result.run_id);
        // Navigate to pipelines after short delay
        setTimeout(() => window._nav?.('workflow'), 1500);
      } catch (e) {
        toast(`Failed to start workflow: ${e.message}`, 'error');
        btn.disabled = false;
        btn.textContent = '\u25B6 Run';
      }
    };
  });
}
