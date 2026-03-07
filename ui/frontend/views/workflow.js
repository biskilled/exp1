import { state, setState } from '../stores/state.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { highlightYaml, validateYaml } from '../utils/markdown.js';

// ── Sample YAML ────────────────────────────────────────────────────────────────

const SAMPLE_YAML = `name: my_workflow
description: "Describe what this workflow does"
max_iterations: 1
steps:
  - name: design
    provider: claude
    prompt: prompts/01_design.md
    inject_files: [PROJECT.md]
  - name: review
    provider: deepseek
    prompt: prompts/02_review.md
    inject_previous_output: true
`;

const PROVIDER_COLORS = {
  claude:   'var(--claude)',
  openai:   'var(--openai)',
  deepseek: 'var(--deepseek)',
  gemini:   'var(--gemini)',
  grok:     'var(--grok)',
};

// ── Main render ───────────────────────────────────────────────────────────────

export function renderWorkflow(container) {
  container.className = 'view active workflow-view';
  const projectName = state.currentProject?.name;

  container.innerHTML = `
    <div class="workflow-toolbar">
      <button class="btn btn-primary btn-sm" onclick="window._newWorkflow()">+ New Workflow</button>
      <div style="flex:1"></div>
      <div class="wf-mode-tabs" id="wf-mode-tabs">
        <div class="wf-mode-tab active" onclick="window._wfMode('yaml')">⌨ YAML</div>
        <div class="wf-mode-tab" onclick="window._wfMode('steps')">≡ Steps</div>
        <div class="wf-mode-tab" onclick="window._wfMode('visual')">⬡ Visual</div>
      </div>
    </div>
    <div class="workflow-body">
      <div class="workflow-sidebar" id="wf-sidebar-panel">
        <div style="padding:0.5rem 0.5rem 0.25rem">
          <div class="nav-section-label">Workflows</div>
        </div>
        <div id="wf-list"></div>
      </div>
      <!-- Sidebar resize handle -->
      <div id="wf-resize-handle"
           style="width:4px;cursor:col-resize;background:var(--border);flex-shrink:0"
           title="Drag to resize panel"></div>
      <div class="workflow-canvas-area" id="wf-canvas-area"></div>
    </div>
  `;

  setState({ workflowMode: 'yaml' });

  window._wfMode = (mode) => {
    setState({ workflowMode: mode });
    document.querySelectorAll('.wf-mode-tab').forEach(el => {
      const labels = { yaml: 'YAML', steps: 'Steps', visual: 'Visual' };
      el.classList.toggle('active', el.textContent.includes(labels[mode]));
    });
    if (state.currentWorkflow) renderWorkflowCanvas();
  };

  window._newWorkflow = () => _showNewWorkflowModal(projectName);

  _loadWorkflowList(projectName);
  renderWorkflowEmpty();
  _initWfResize();
}

// ── Sidebar resize ─────────────────────────────────────────────────────────────

function _initWfResize() {
  const handle = document.getElementById('wf-resize-handle');
  const panel  = document.getElementById('wf-sidebar-panel');
  if (!handle || !panel) return;

  // Restore saved width
  const saved = localStorage.getItem('aicli_wf_sidebar_w');
  if (saved) panel.style.width = saved + 'px';

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
    panel.style.width = `${Math.max(120, Math.min(400, startW + (e.clientX - startX)))}px`;
  });
  document.addEventListener('mouseup', () => {
    if (!dragging) return;
    dragging = false;
    document.body.style.cursor = document.body.style.userSelect = '';
    handle.style.background = 'var(--border)';
    localStorage.setItem('aicli_wf_sidebar_w', String(panel.offsetWidth));
  });
}

// ── Workflow list ─────────────────────────────────────────────────────────────

async function _loadWorkflowList(projectName) {
  const list = document.getElementById('wf-list');
  if (!list) return;

  if (!projectName) {
    list.innerHTML = '<div class="empty-state" style="padding:1rem"><p style="font-size:0.68rem">No project open</p></div>';
    return;
  }

  try {
    const data = await api.listWorkflows(projectName);
    const workflows = data.workflows || data.files || [];

    if (!workflows.length) {
      list.innerHTML = '<div class="empty-state" style="padding:1rem"><p style="font-size:0.68rem">No workflows yet</p></div>';
      return;
    }

    list.innerHTML = workflows.map(w => {
      const name = typeof w === 'string' ? w : w.name;
      return `
        <div class="wf-list-item ${state.currentWorkflow?.name === name ? 'active' : ''}"
             onclick="window._selectWorkflow('${_esc(name)}')">
          <span>⟳</span>
          <span style="flex:1;overflow:hidden;text-overflow:ellipsis">${_esc(name)}</span>
        </div>
      `;
    }).join('');
  } catch (e) {
    list.innerHTML = `<div style="padding:0.75rem;font-size:0.65rem;color:var(--red)">${_esc(e.message)}</div>`;
  }

  window._selectWorkflow = async (name) => {
    const projectName = state.currentProject?.name;
    if (!projectName) return;
    try {
      const data = await api.readWorkflow(projectName, name);
      const yaml = data.yaml || data.content || '';
      setState({ currentWorkflow: { name, yaml } });
      document.querySelectorAll('.wf-list-item').forEach(el =>
        el.classList.toggle('active', el.textContent.trim().startsWith(name))
      );
      renderWorkflowCanvas();
    } catch (e) {
      toast(`Could not load workflow: ${e.message}`, 'error');
    }
  };
}

// ── Empty state ───────────────────────────────────────────────────────────────

function renderWorkflowEmpty() {
  const area = document.getElementById('wf-canvas-area');
  if (!area) return;
  area.innerHTML = `
    <div class="empty-state" style="height:100%">
      <div class="empty-state-icon">⟳</div>
      <p>Select a workflow or create a new one</p>
      <button class="btn btn-primary btn-sm" onclick="window._newWorkflow()">+ New Workflow</button>
    </div>
  `;
}

// ── Canvas dispatch ───────────────────────────────────────────────────────────

function renderWorkflowCanvas() {
  const area = document.getElementById('wf-canvas-area');
  if (!area || !state.currentWorkflow) return;

  const mode = state.workflowMode || 'yaml';
  if (mode === 'visual') _renderVisualCanvas(area);
  else if (mode === 'steps') _renderStepsList(area);
  else _renderYamlEditor(area);
}

// ── YAML editor mode — split pane with live syntax highlight + validation ──────

function _renderYamlEditor(area) {
  const wf   = state.currentWorkflow;
  const yaml = wf?.yaml || SAMPLE_YAML;

  area.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">

      <!-- Toolbar -->
      <div style="display:flex;align-items:center;gap:0.5rem;padding:0.45rem 0.75rem;
                  border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0">
        <span style="font-size:0.68rem;color:var(--text2);flex:1">${_esc(wf?.name || 'untitled')}.yaml</span>
        <span id="wf-yaml-status" style="font-size:0.62rem"></span>
        <button class="btn btn-primary btn-sm" id="wf-save-btn"
          disabled style="opacity:0.4" onclick="window._saveWorkflowYaml()">Save</button>
      </div>

      <!-- Error banner (hidden by default) -->
      <div id="wf-yaml-error" style="display:none;padding:0.45rem 1rem;
           background:rgba(239,68,68,0.08);border-bottom:1px solid rgba(239,68,68,0.25);
           font-size:0.68rem;color:var(--red);flex-shrink:0"></div>

      <!-- Split pane: textarea | highlighted preview -->
      <div style="flex:1;display:flex;overflow:hidden;min-height:0">

        <!-- Left: editable textarea -->
        <textarea class="yaml-editor" id="yaml-editor" spellcheck="false"
          style="flex:1;border-right:1px solid var(--border)"
          >${_esc(yaml)}</textarea>

        <!-- Right: syntax-highlighted mirror -->
        <div id="yaml-preview-pane"
          style="flex:1;overflow:auto;background:var(--bg);padding:1rem;
                 font-family:var(--font);font-size:0.75rem;line-height:1.7;
                 white-space:pre;tab-size:2;user-select:text;-webkit-user-select:text"></div>
      </div>

      <!-- Node flow -->
      <div id="wf-node-flow"></div>
    </div>
  `;

  const ta      = document.getElementById('yaml-editor');
  const preview = document.getElementById('yaml-preview-pane');
  const errorEl = document.getElementById('wf-yaml-error');
  const saveBtn = document.getElementById('wf-save-btn');
  const statusEl = document.getElementById('wf-yaml-status');
  let _original  = yaml;

  function _refresh(text) {
    // Syntax highlight
    preview.innerHTML = highlightYaml(text);

    // Validate
    const result = validateYaml(text);
    if (result.ok) {
      errorEl.style.display = 'none';
      statusEl.textContent  = '✓ valid';
      statusEl.style.color  = 'var(--green)';
    } else {
      errorEl.style.display = 'block';
      errorEl.innerHTML =
        `<strong>Line ${result.line}:</strong> ${_esc(result.message)}`;
      statusEl.textContent = `✗ line ${result.line}`;
      statusEl.style.color = 'var(--red)';
    }

    // Node flow
    _renderNodeFlow(text);
  }

  // Initial render
  _refresh(yaml);

  ta.addEventListener('input', () => {
    const changed = ta.value !== _original;
    saveBtn.disabled = !changed;
    saveBtn.style.opacity = changed ? '1' : '0.4';
    _refresh(ta.value);
  });

  // Sync scroll between textarea and preview
  ta.addEventListener('scroll', () => {
    const ratio = ta.scrollTop / (ta.scrollHeight - ta.clientHeight || 1);
    preview.scrollTop = ratio * (preview.scrollHeight - preview.clientHeight);
  });

  window._saveWorkflowYaml = async () => {
    const projectName = state.currentProject?.name;
    const wfName      = state.currentWorkflow?.name;
    if (!projectName || !wfName) { toast('No project/workflow selected', 'error'); return; }

    const result = validateYaml(ta.value);
    if (!result.ok) {
      toast(`Cannot save — YAML error on line ${result.line}: ${result.message}`, 'error');
      return;
    }

    try {
      await api.writeWorkflow(projectName, wfName, ta.value);
      _original = ta.value;
      state.currentWorkflow.yaml = ta.value;
      saveBtn.disabled = true;
      saveBtn.style.opacity = '0.4';
      toast('Workflow saved', 'success');
    } catch (e) {
      toast(`Save failed: ${e.message}`, 'error');
    }
  };
}

// ── Node flow visualization ───────────────────────────────────────────────────

function _renderNodeFlow(yamlText) {
  const container = document.getElementById('wf-node-flow');
  if (!container) return;

  try {
    const steps = _parseYamlSteps(yamlText);
    if (!steps.length) { container.innerHTML = ''; return; }

    const nodes = steps.map((s, i) => {
      const provider = s.provider || 'claude';
      const color = PROVIDER_COLORS[provider] || 'var(--muted)';
      const arrow = i < steps.length - 1 ? '<div class="wf-flow-arrow">──▶</div>' : '';
      return `
        <div class="wf-flow-node">
          <div class="wf-flow-box" style="border-color:${color}">
            <div class="wf-flow-name">${_esc(s.name || `step${i+1}`)}</div>
            <div class="wf-flow-badge" style="background:${color};margin-top:0.25rem">${_esc(provider)}</div>
          </div>
        </div>
        ${arrow}
      `;
    }).join('');

    container.className = 'wf-node-flow';
    container.innerHTML = nodes;
  } catch (e) {
    container.className = 'wf-parse-error';
    container.innerHTML = `⚠ YAML parse error: ${_esc(e.message)}`;
  }
}

// Minimal YAML step parser (no lib dependency)
function _parseYamlSteps(yamlText) {
  const steps = [];
  let inSteps = false;
  let currentStep = null;

  for (const line of yamlText.split('\n')) {
    if (/^steps\s*:/.test(line)) { inSteps = true; continue; }
    if (!inSteps) continue;
    if (/^\S/.test(line) && !/^steps\s*:/.test(line)) { inSteps = false; continue; }

    // New step item
    const stepMatch = line.match(/^  - (?:name\s*:\s*(.+))?/);
    if (stepMatch) {
      if (currentStep) steps.push(currentStep);
      currentStep = { name: stepMatch[1]?.trim().replace(/^['"]|['"]$/g, '') || '' };
      continue;
    }

    if (!currentStep) continue;

    const kv = line.match(/^\s+(\w+)\s*:\s*(.+)/);
    if (kv) {
      const key = kv[1].trim();
      const val = kv[2].trim().replace(/^['"]|['"]$/g, '');
      currentStep[key] = val;
    }
  }
  if (currentStep) steps.push(currentStep);
  return steps;
}

// ── Steps list mode ────────────────────────────────────────────────────────────

function _renderStepsList(area) {
  const wf = state.currentWorkflow;
  let steps = [];
  try { steps = _parseYamlSteps(wf?.yaml || ''); } catch {}

  area.innerHTML = `
    <div style="display:flex;flex-direction:column;height:100%;overflow:hidden">
      <div style="padding:0.75rem;border-bottom:1px solid var(--border);font-size:0.68rem;color:var(--text2)">
        ${steps.length} step${steps.length !== 1 ? 's' : ''} — edit in YAML mode to modify
      </div>
      <div class="wf-steps-list">
        ${!steps.length ? `
          <div class="empty-state"><p>No steps. Switch to YAML mode to add steps.</p></div>
        ` : steps.map((step, i) => {
          const provider = step.provider || 'claude';
          const color = PROVIDER_COLORS[provider] || 'var(--muted)';
          return `
            <div class="wf-step-item">
              <div class="wf-step-num" style="color:${color};border-color:${color}">${i+1}</div>
              <div class="wf-step-content">
                <div class="wf-step-name">${_esc(step.name || `step${i+1}`)}
                  <span style="font-size:0.6rem;color:${color}">[${_esc(provider)}]</span>
                </div>
                <div class="wf-step-desc">
                  ${step.prompt ? `prompt: ${_esc(step.prompt)}` : ''}
                  ${step.inject_files ? ` · inject: ${_esc(step.inject_files)}` : ''}
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
}

// ── Visual canvas (simplified) ────────────────────────────────────────────────

function _renderVisualCanvas(area) {
  const wf = state.currentWorkflow;
  let steps = [];
  try { steps = _parseYamlSteps(wf?.yaml || ''); } catch {}

  area.innerHTML = `
    <div class="wf-canvas">
      <svg class="wf-connections"></svg>
      ${steps.map((step, i) => {
        const provider = step.provider || 'claude';
        const color = PROVIDER_COLORS[provider] || 'var(--muted)';
        const x = 80 + i * 200;
        const y = 120;
        return `
          <div class="wf-node" style="left:${x}px;top:${y}px;--node-color:${color}">
            <div class="wf-node-header">
              <span class="wf-node-icon" style="color:${color}">◉</span>
              <span class="wf-node-title">${_esc(step.name || `step${i+1}`)}</span>
            </div>
            <div class="wf-node-body">
              <div style="color:${color};font-size:0.6rem">${_esc(provider)}</div>
              ${step.prompt ? `<div style="font-size:0.6rem;opacity:0.7">${_esc(step.prompt.slice(0,40))}</div>` : ''}
            </div>
          </div>
        `;
      }).join('')}
      ${steps.length === 0 ? `<div class="empty-state" style="height:100%"><p>Switch to YAML mode to add steps</p></div>` : ''}
    </div>
  `;
}

// ── New workflow modal ────────────────────────────────────────────────────────

function _showNewWorkflowModal(projectName) {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay open';
  overlay.innerHTML = `
    <div class="modal" style="min-width:480px">
      <div class="modal-title">New Workflow</div>
      <div class="modal-subtitle">Workflows orchestrate multiple LLM steps, defined as YAML.</div>
      <div class="field-group">
        <div class="field-label">Workflow name <span style="color:var(--red)">*</span></div>
        <input class="field-input" id="wf-new-name" placeholder="code_review" autofocus />
      </div>
      <div class="modal-footer">
        <button class="btn btn-ghost" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
        <button class="btn btn-primary" onclick="window._createWorkflow()">Create</button>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });

  window._createWorkflow = async () => {
    const name = document.getElementById('wf-new-name').value.trim().replace(/\s+/g, '_');
    if (!name) { toast('Workflow name required', 'error'); return; }
    if (!projectName) { toast('No project open', 'error'); return; }

    try {
      await api.writeWorkflow(projectName, name, SAMPLE_YAML.replace('my_workflow', name));
      toast(`Workflow "${name}" created`, 'success');
      overlay.remove();
      setState({ currentWorkflow: { name, yaml: SAMPLE_YAML.replace('my_workflow', name) } });
      await _loadWorkflowList(projectName);
      renderWorkflowCanvas();
    } catch (e) {
      toast(`Error: ${e.message}`, 'error');
    }
  };
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _esc(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
