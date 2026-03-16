/**
 * graph_workflow.js — Multi-agent workflow editor (Cytoscape.js).
 *
 * Sidebar: Graph Flows (PostgreSQL) + YAML Workflows (file-based).
 * Node config: role selector from prompts/roles/, approval toggle, output schema.
 * Edge config: condition type (always / score_gte / score_lt / needs_approval).
 * Run log: real-time polling + approval panel when run.status==='waiting_approval'.
 * Templates: Web Dev, Trading Algo, AWS Design pipelines.
 */

import { state } from '../stores/state.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';

// ── Constants ─────────────────────────────────────────────────────────────────

const PROVIDER_COLORS = {
  claude: 'var(--claude)', openai: 'var(--openai)', deepseek: 'var(--deepseek)',
  gemini: 'var(--gemini)', grok: 'var(--grok)',
};
const PROVIDER_BG = {
  claude: '#fff3ee', openai: '#e6f7f0', deepseek: '#e6f4fb',
  gemini: '#e6f9ee', grok: '#fdf6e3',
};

const TEMPLATES = [
  {
    id: 'web_dev',
    name: 'Web Dev Pipeline',
    description: 'PM → Architect → Developer → Reviewer → QA',
    nodes: [
      { name: 'Product Manager', provider: 'openai',    role_file: 'roles/product_manager.md', position_x: 80,  position_y: 150 },
      { name: 'Architect',       provider: 'claude',    role_file: 'roles/architect.md',       position_x: 260, position_y: 150 },
      { name: 'Developer',       provider: 'deepseek',  role_file: 'roles/developer.md',       position_x: 440, position_y: 150 },
      { name: 'Reviewer',        provider: 'claude',    role_file: 'roles/reviewer.md',        position_x: 620, position_y: 150, require_approval: true, approval_msg: 'Review complete. Approve to proceed to QA?' },
      { name: 'QA Engineer',     provider: 'openai',    role_file: 'roles/qa.md',              position_x: 800, position_y: 150 },
    ],
    edges: [
      { from: 0, to: 1 },
      { from: 1, to: 2 },
      { from: 2, to: 3 },
      { from: 3, to: 4, condition: { field: 'score', op: 'gte', value: 7 }, label: 'score≥7' },
      { from: 3, to: 2, condition: { field: 'score', op: 'lt',  value: 7 }, label: 'rework'  },
    ],
  },
  {
    id: 'trading',
    name: 'Trading Algo Pipeline',
    description: 'Strategist → Algo Dev → Backtester → Risk Review',
    nodes: [
      { name: 'Strategist',    provider: 'claude',   role_file: 'roles/product_manager.md', position_x: 80,  position_y: 150 },
      { name: 'Algo Dev',      provider: 'deepseek', role_file: 'roles/developer.md',       position_x: 280, position_y: 150 },
      { name: 'Backtester',    provider: 'claude',   role_file: 'roles/qa.md',              position_x: 480, position_y: 150 },
      { name: 'Risk Reviewer', provider: 'openai',   role_file: 'roles/reviewer.md',        position_x: 680, position_y: 150, require_approval: true, approval_msg: 'Backtesting complete. Approve strategy for deployment?' },
    ],
    edges: [
      { from: 0, to: 1 },
      { from: 1, to: 2 },
      { from: 2, to: 3, condition: { field: 'score', op: 'gte', value: 6 }, label: 'score≥6' },
      { from: 2, to: 1, condition: { field: 'score', op: 'lt',  value: 6 }, label: 'rework'  },
    ],
  },
  {
    id: 'aws',
    name: 'AWS Architecture Review',
    description: 'Requirements → Architect → Infra Dev → Security Review',
    nodes: [
      { name: 'Requirements',   provider: 'openai',   role_file: 'roles/product_manager.md', position_x: 80,  position_y: 150 },
      { name: 'Architect',      provider: 'claude',   role_file: 'roles/architect.md',       position_x: 260, position_y: 150 },
      { name: 'Infra Developer',provider: 'deepseek', role_file: 'roles/developer.md',       position_x: 440, position_y: 150 },
      { name: 'Security Review',provider: 'claude',   role_file: 'roles/security.md',        position_x: 620, position_y: 150, require_approval: true, approval_msg: 'Security review done. Approve for deployment?' },
    ],
    edges: [
      { from: 0, to: 1 },
      { from: 1, to: 2 },
      { from: 2, to: 3 },
    ],
  },
];

// ── Module state ──────────────────────────────────────────────────────────────

let _cy = null;
let _currentWf = null;
let _connectMode = false;
let _connectSourceId = null;
let _pollInterval = null;
let _currentRunId = null;
let _roles = [];       // cached DB agent roles [{id, name, description, provider, model}]
let _rolesIsAdmin = false;  // whether current user can see system_prompt

// ── Main render ───────────────────────────────────────────────────────────────

export function renderGraphWorkflow(container) {
  container.className = 'view active gw-view';
  const projectName = state.currentProject?.name;

  // Stop any running poll from previous view
  if (_pollInterval) { clearInterval(_pollInterval); _pollInterval = null; }
  _currentWf = null;
  _cy = null;

  container.innerHTML = `
    <div class="gw-toolbar">
      <button class="btn btn-primary btn-sm" onclick="window._gwNewWorkflow()">+ New Flow</button>
      <button class="btn btn-ghost btn-sm" onclick="window._gwFromTemplate()">From Template</button>
      <div style="flex:1"></div>
      <button class="btn btn-ghost btn-sm" id="gw-add-node-btn" onclick="window._gwAddNode()" style="display:none">+ Node</button>
      <button class="btn btn-ghost btn-sm" id="gw-run-btn" onclick="window._gwStartRun()" style="display:none">▶ Run</button>
      <button class="btn btn-ghost btn-sm" id="gw-layout-btn" onclick="window._gwRelayout()" style="display:none">⟳ Layout</button>
    </div>
    <div class="gw-body">
      <div class="gw-sidebar" id="gw-sidebar">
        <div class="gw-sidebar-section">
          <div class="nav-section-label" style="padding:0.4rem 0.75rem 0.2rem">Graph Flows</div>
          <div id="gw-list"></div>
        </div>
        <div class="gw-sidebar-section" style="border-top:1px solid var(--border);padding-top:0.25rem;margin-top:0.25rem">
          <div class="nav-section-label" style="padding:0.4rem 0.75rem 0.2rem">YAML Workflows</div>
          <div id="gw-yaml-list"></div>
        </div>
      </div>
      <div class="gw-canvas-wrap" id="gw-canvas-wrap">
        <div id="cy-container" style="flex:1;height:100%;min-height:300px"></div>
        <div class="gw-log-panel" id="gw-log-panel" style="display:none">
          <div class="gw-log-header" onclick="window._gwToggleLog()">
            <span>Run Log</span>
            <span id="gw-log-status" style="margin-left:0.5rem;font-size:0.75rem;color:var(--muted)"></span>
            <button class="btn btn-ghost btn-sm" id="gw-cancel-btn"
                    style="display:none;margin-left:0.5rem;font-size:0.7rem;color:var(--red)"
                    onclick="event.stopPropagation();window._gwCancelRun()">✕ Cancel</button>
            <span class="gw-log-toggle">▲</span>
          </div>
          <div id="gw-approval-panel" style="display:none;border-bottom:1px solid var(--border)"></div>
          <div class="gw-log-body" id="gw-log-body"></div>
        </div>
      </div>
      <div class="gw-config-panel" id="gw-config-panel" style="display:none">
        <div class="gw-config-header">
          <span id="gw-config-title">Config</span>
          <button class="btn btn-ghost btn-sm" onclick="window._gwCloseConfig()">✕</button>
        </div>
        <div id="gw-config-body" style="overflow-y:auto;flex:1"></div>
      </div>
    </div>
  `;

  window._gwNewWorkflow   = () => _showNewWorkflowModal(projectName);
  window._gwFromTemplate  = () => _showTemplateModal(projectName);
  window._gwAddNode       = () => _addNodeAtCenter();
  window._gwStartRun      = () => _startRun(projectName);
  window._gwCancelRun     = () => _cancelRun();
  window._gwRelayout      = () => _cy?.layout({ name: 'dagre', rankDir: 'LR', nodeSep: 60, rankSep: 120 }).run();
  window._gwToggleLog     = _toggleLog;
  window._gwCloseConfig   = _closeConfig;
  window._gwOpenWf        = _openWorkflow;

  _loadRoles(projectName);
  _loadList(projectName);
  _loadYamlList(projectName);
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

async function _loadList(project) {
  const el = document.getElementById('gw-list');
  if (!el) return;
  el.innerHTML = '<div class="gw-sidebar-loading">Loading…</div>';
  try {
    const { workflows } = await api.graphWorkflows.list(project || '');
    if (!workflows.length) {
      el.innerHTML = '<div class="gw-sidebar-empty">No flows yet</div>';
      return;
    }
    el.innerHTML = workflows.map(wf => `
      <div class="gw-list-item ${_currentWf?.id === wf.id ? 'active' : ''}"
           onclick="window._gwOpenWf('${wf.id}')">
        <div style="font-weight:500;font-size:0.8rem">${_esc(wf.name)}</div>
        <div style="color:var(--muted);font-size:0.7rem">${_esc(wf.description || '')}</div>
      </div>
    `).join('');
  } catch (e) {
    el.innerHTML = `<div class="gw-sidebar-empty" style="color:var(--red)">${_esc(e.message)}</div>`;
  }
}

async function _loadYamlList(project) {
  const el = document.getElementById('gw-yaml-list');
  if (!el) return;
  el.innerHTML = '<div class="gw-sidebar-loading">Loading…</div>';
  try {
    const data = await api.listWorkflows(project || '');
    const workflows = data.workflows || data || [];
    if (!workflows.length) {
      el.innerHTML = '<div class="gw-sidebar-empty">No YAML workflows</div>';
      return;
    }
    el.innerHTML = workflows.map(wf => {
      const name = typeof wf === 'string' ? wf : (wf.name || wf.id || String(wf));
      return `<div class="gw-list-item" onclick="window._nav && window._nav('yaml-workflow')"
                   title="Open in YAML editor">
        <div style="font-size:0.8rem">⌨ ${_esc(name)}</div>
      </div>`;
    }).join('');
  } catch {
    el.innerHTML = '<div class="gw-sidebar-empty">—</div>';
  }
}

async function _loadRoles(project) {
  try {
    const data = await api.agentRoles.list(project || '_global');
    _roles = data.roles || [];
    _rolesIsAdmin = data.is_admin || false;
  } catch {
    _roles = [];
    _rolesIsAdmin = false;
  }
}

async function _openWorkflow(id) {
  try {
    const wf = await api.graphWorkflows.get(id);
    _currentWf = wf;
    _showToolbarButtons();
    _renderCanvas(wf);
    _loadList(state.currentProject?.name);
  } catch (e) {
    toast(`Failed to load flow: ${e.message}`, 'error');
  }
}

function _showToolbarButtons() {
  ['gw-run-btn', 'gw-layout-btn', 'gw-add-node-btn'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = '';
  });
}

// ── Canvas ────────────────────────────────────────────────────────────────────

function _renderCanvas(wf) {
  const container = document.getElementById('cy-container');
  if (!container) return;
  if (_cy) { _cy.destroy(); _cy = null; }

  const elements = [];
  (wf.nodes || []).forEach(n => {
    elements.push({
      group: 'nodes',
      data: { id: n.id, label: n.name, provider: n.provider, nodeData: n },
      position: { x: n.position_x || 100, y: n.position_y || 100 },
    });
  });
  (wf.edges || []).forEach(e => {
    elements.push({
      group: 'edges',
      data: { id: e.id, source: e.source_node_id, target: e.target_node_id, label: e.label || '', condition: e.condition },
    });
  });

  _cy = window.cytoscape({
    container, elements,
    style: _cytoscapeStyle(),
    layout: elements.filter(e => e.group === 'nodes').length
      ? { name: 'preset' }
      : { name: 'dagre', rankDir: 'LR', nodeSep: 60, rankSep: 120 },
    minZoom: 0.25, maxZoom: 3,
  });

  _cy.on('tap', 'node', evt => {
    const node = evt.target;
    if (_connectMode && _connectSourceId) {
      _createEdge(_connectSourceId, node.id());
      _exitConnectMode();
    } else {
      _openNodeConfig(node.data('nodeData'));
    }
  });

  _cy.on('tap', 'edge', evt => _openEdgeConfig(evt.target.data()));

  _cy.on('tap', evt => {
    if (evt.target === _cy) _exitConnectMode();
  });

  _cy.on('dragfree', 'node', evt => {
    const node = evt.target;
    const pos = node.position();
    api.graphWorkflows.updateNode(_currentWf.id, node.id(), { position_x: pos.x, position_y: pos.y }).catch(() => {});
    const nd = node.data('nodeData');
    if (nd) { nd.position_x = pos.x; nd.position_y = pos.y; }
  });

  _cy.on('dbltap', evt => {
    if (evt.target === _cy) _addNodeAt(evt.position.x, evt.position.y);
  });
}

function _cytoscapeStyle() {
  return [
    {
      selector: 'node',
      style: {
        label: 'data(label)',
        'text-valign': 'center', 'text-halign': 'center',
        'font-size': '11px', 'font-family': 'JetBrains Mono, monospace',
        width: '130px', height: '55px', shape: 'round-rectangle',
        'background-color': ele => PROVIDER_BG[ele.data('provider')] || '#f0f4f8',
        'border-color': ele => PROVIDER_COLORS[ele.data('provider')] || '#888',
        'border-width': '2px', color: '#1a1a2e',
        'text-wrap': 'wrap', 'text-max-width': '120px', padding: '8px',
      },
    },
    { selector: 'node[status="running"]',          style: { 'border-width': '3px', 'border-color': 'var(--accent)', 'border-style': 'dashed' } },
    { selector: 'node[status="waiting_approval"]', style: { 'border-width': '3px', 'border-color': '#f59e0b', 'border-style': 'solid', 'background-color': '#fffbeb' } },
    { selector: 'node[status="done"]',             style: { 'border-width': '3px', 'border-color': 'var(--green)' } },
    { selector: 'node[status="error"]',            style: { 'border-width': '3px', 'border-color': 'var(--red)' } },
    { selector: 'node.connect-source',             style: { 'border-width': '4px', 'border-color': 'var(--accent)' } },
    {
      selector: 'edge',
      style: {
        'curve-style': 'bezier', 'target-arrow-shape': 'triangle',
        'target-arrow-color': 'var(--muted)', 'line-color': 'var(--border)',
        width: 2, label: 'data(label)', 'font-size': '9px', color: 'var(--muted)',
        'text-background-color': 'var(--bg)', 'text-background-opacity': 1,
        'text-background-padding': '2px',
      },
    },
    { selector: 'edge[?condition]', style: { 'line-style': 'dashed', 'line-color': 'var(--accent)' } },
  ];
}

// ── Node config panel ─────────────────────────────────────────────────────────

function _openNodeConfig(nodeData) {
  const panel = document.getElementById('gw-config-panel');
  const title = document.getElementById('gw-config-title');
  const body  = document.getElementById('gw-config-body');
  if (!panel) return;
  panel.style.display = '';
  title.textContent = 'Node: ' + (nodeData?.name || 'New');

  const n = nodeData || {};
  // role_id takes priority; fall back to role_file for legacy nodes
  const hasDbRole   = !!n.role_id;
  const hasFileRole = !hasDbRole && !!n.role_file;

  // Build role dropdown options from DB roles
  const PROV_COL = { claude: '#e67e22', openai: '#27ae60', deepseek: '#2980b9', gemini: '#16a085', grok: '#8e44ad' };
  const roleOpts = _roles.map(r => {
    const sel = hasDbRole && String(n.role_id) === String(r.id);
    return `<option value="${r.id}" ${sel ? 'selected' : ''}
      data-provider="${_esc(r.provider)}" data-model="${_esc(r.model || '')}"
      title="${_esc(r.description)}">${_esc(r.name)} [${_esc(r.provider)}]</option>`;
  }).join('');

  // Find currently selected role for description display
  const selRole = hasDbRole ? _roles.find(r => String(r.id) === String(n.role_id)) : null;

  body.innerHTML = `
    <div class="gw-config-form">
      <label>Name</label>
      <input class="field-input" id="cfg-name" value="${_esc(n.name || '')}" />

      <label>Agent Role <span style="font-size:0.6rem;color:var(--muted)">(prompt loaded from role library)</span></label>
      <select class="field-input" id="cfg-role-select" onchange="window._gwOnRoleChange(this.value)">
        <option value="" ${!hasDbRole ? 'selected' : ''}>— inline / custom prompt —</option>
        ${roleOpts}
      </select>
      <div id="cfg-role-desc" style="font-size:0.62rem;color:var(--muted);margin-top:0.15rem;min-height:0.9rem">
        ${selRole ? _esc(selRole.description) : ''}
      </div>

      <label>Provider <span style="font-size:0.6rem;color:var(--muted)">(role default used when blank)</span></label>
      <select class="field-input" id="cfg-provider">
        ${['claude','openai','deepseek','gemini','grok'].map(p =>
          `<option value="${p}" ${n.provider === p ? 'selected' : ''}>${p}</option>`
        ).join('')}
      </select>

      <label>Model (blank = provider default)</label>
      <input class="field-input" id="cfg-model" value="${_esc(n.model || '')}" />

      <div id="cfg-prompt-wrap" style="${hasDbRole ? 'display:none' : ''}">
        <label>Inline system prompt ${hasFileRole ? `<span style="font-size:0.6rem;color:var(--muted)">(from ${_esc(n.role_file)})</span>` : ''}</label>
        <textarea class="field-input" id="cfg-role-prompt" rows="5" style="font-size:0.72rem;font-family:monospace">${_esc(n.role_prompt || '')}</textarea>
      </div>

      ${_rolesIsAdmin ? `
      <div id="cfg-role-prompt-preview"
           style="font-size:0.62rem;color:var(--muted);background:var(--surface2);
                  border:1px solid var(--border);border-radius:var(--radius);padding:0.4rem 0.5rem;
                  font-family:monospace;white-space:pre-wrap;max-height:80px;overflow:hidden;cursor:pointer;
                  ${selRole ? '' : 'display:none'}"
           title="Click to view full prompt"
           onclick="this.style.maxHeight=this.style.maxHeight==='none'?'80px':'none'">
        ${selRole ? _esc((selRole.system_prompt||'').slice(0,300)) + ((selRole.system_prompt||'').length>300?'…':'') : ''}
      </div>` : ''}


      <label style="display:flex;align-items:center;gap:0.4rem;margin-top:0.35rem">
        <input type="checkbox" id="cfg-inject" ${n.inject_context !== false ? 'checked' : ''} />
        Inject context from previous nodes
      </label>

      <label style="display:flex;align-items:center;gap:0.4rem;margin-top:0.35rem">
        <input type="checkbox" id="cfg-approval" ${n.require_approval ? 'checked' : ''}
               onchange="window._gwOnApprovalToggle(this.checked)" />
        Pause for user approval
      </label>

      <div id="cfg-approval-wrap" style="${n.require_approval ? '' : 'display:none'}">
        <label>Message shown to user</label>
        <input class="field-input" id="cfg-approval-msg" value="${_esc(n.approval_msg || '')}"
               placeholder="Review and approve to continue?" />
      </div>

      <div style="display:flex;gap:0.5rem;margin-top:0.75rem;flex-wrap:wrap">
        <button class="btn btn-primary btn-sm" onclick="window._gwSaveNode('${n.id || ''}')">Save</button>
        <button class="btn btn-ghost btn-sm" onclick="window._gwConnectFrom('${n.id || ''}')">Connect →</button>
        ${n.id ? `<button class="btn btn-ghost btn-sm" style="color:var(--red)" onclick="window._gwDeleteNode('${n.id}')">Delete</button>` : ''}
      </div>
    </div>
  `;

  window._gwOnRoleChange = (val) => {
    const wrap = document.getElementById('cfg-prompt-wrap');
    if (wrap) wrap.style.display = val ? 'none' : '';
    const descEl = document.getElementById('cfg-role-desc');
    const previewEl = document.getElementById('cfg-role-prompt-preview');
    if (val) {
      const role = _roles.find(r => String(r.id) === String(val));
      if (role) {
        if (descEl) descEl.textContent = role.description || '';
        // Auto-populate provider/model from role defaults
        const provEl = document.getElementById('cfg-provider');
        const modEl  = document.getElementById('cfg-model');
        if (provEl && role.provider) provEl.value = role.provider;
        if (modEl)  modEl.value = role.model || '';
        // Update admin prompt preview
        if (previewEl) {
          const txt = role.system_prompt || '';
          previewEl.textContent = txt.slice(0, 300) + (txt.length > 300 ? '…' : '');
          previewEl.style.display = '';
        }
      }
    } else {
      if (descEl) descEl.textContent = '';
      if (previewEl) previewEl.style.display = 'none';
    }
  };
  window._gwOnApprovalToggle = (checked) => {
    const wrap = document.getElementById('cfg-approval-wrap');
    if (wrap) wrap.style.display = checked ? '' : 'none';
  };
  window._gwSaveNode    = (nodeId) => _saveNodeConfig(nodeId, nodeData);
  window._gwConnectFrom = (nodeId) => _enterConnectMode(nodeId);
  window._gwDeleteNode  = (nodeId) => _deleteNode(nodeId);
}

async function _saveNodeConfig(nodeId, existingData) {
  if (!_currentWf) return;
  const name          = document.getElementById('cfg-name')?.value.trim() || '';
  const provider      = document.getElementById('cfg-provider')?.value || 'claude';
  const model         = document.getElementById('cfg-model')?.value.trim() || '';
  const roleIdRaw     = document.getElementById('cfg-role-select')?.value || '';
  const roleId        = roleIdRaw ? parseInt(roleIdRaw, 10) : null;
  const rolePrompt    = roleId ? '' : (document.getElementById('cfg-role-prompt')?.value || '');
  const injectContext = document.getElementById('cfg-inject')?.checked !== false;
  const reqApproval   = document.getElementById('cfg-approval')?.checked || false;
  const approvalMsg   = document.getElementById('cfg-approval-msg')?.value.trim() || '';

  const body = {
    name, provider, model,
    role_id: roleId,
    role_file: null,
    role_prompt: rolePrompt,
    inject_context: injectContext,
    require_approval: reqApproval,
    approval_msg: approvalMsg,
  };

  try {
    if (nodeId) {
      await api.graphWorkflows.updateNode(_currentWf.id, nodeId, body);
      const cyNode = _cy?.getElementById(nodeId);
      if (cyNode) {
        cyNode.data('label', name);
        cyNode.data('provider', provider);
        const nd = cyNode.data('nodeData');
        if (nd) Object.assign(nd, body);
      }
    } else {
      const node = await api.graphWorkflows.createNode(_currentWf.id, body);
      _cy?.add({ group: 'nodes', data: { id: node.id, label: node.name, provider: node.provider, nodeData: node }, position: { x: 200, y: 200 } });
      if (_currentWf.nodes) _currentWf.nodes.push(node);
    }
    toast('Saved', 'success');
  } catch (e) {
    toast(`Save failed: ${e.message}`, 'error');
  }
}

async function _deleteNode(nodeId) {
  if (!_currentWf || !confirm('Delete this node and its edges?')) return;
  try {
    await api.graphWorkflows.deleteNode(_currentWf.id, nodeId);
    _cy?.getElementById(nodeId).remove();
    if (_currentWf.nodes) _currentWf.nodes = _currentWf.nodes.filter(n => n.id !== nodeId);
    _closeConfig();
    toast('Node deleted', 'success');
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
}

// ── Edge config panel ─────────────────────────────────────────────────────────

function _openEdgeConfig(edgeData) {
  const panel = document.getElementById('gw-config-panel');
  const title = document.getElementById('gw-config-title');
  const body  = document.getElementById('gw-config-body');
  if (!panel) return;
  panel.style.display = '';
  title.textContent = 'Edge Config';

  const cond = edgeData.condition || {};
  // Determine condition type for UI
  let condType = 'always';
  if (cond.op === 'gte' || cond.op === 'gt')      condType = 'score_gte';
  else if (cond.op === 'lt' || cond.op === 'lte') condType = 'score_lt';

  const threshold = cond.value ?? '';
  const field     = cond.field || 'score';

  body.innerHTML = `
    <div class="gw-config-form">
      <label>Label</label>
      <input class="field-input" id="cfg-edge-label" value="${_esc(edgeData.label || '')}" />

      <label>Condition</label>
      <select class="field-input" id="cfg-cond-type" onchange="window._gwOnCondChange(this.value)">
        <option value="always"    ${condType === 'always'    ? 'selected' : ''}>Always proceed</option>
        <option value="score_gte" ${condType === 'score_gte' ? 'selected' : ''}>Score ≥ threshold</option>
        <option value="score_lt"  ${condType === 'score_lt'  ? 'selected' : ''}>Score &lt; threshold (rework)</option>
      </select>

      <div id="cfg-cond-threshold-wrap" style="${condType === 'always' ? 'display:none' : ''}">
        <label>Output field</label>
        <input class="field-input" id="cfg-cond-field" value="${_esc(field)}" placeholder="score" />
        <label>Threshold value</label>
        <input class="field-input" id="cfg-cond-value" type="number" value="${_esc(String(threshold))}" placeholder="7" />
      </div>

      <div style="display:flex;gap:0.5rem;margin-top:0.75rem">
        <button class="btn btn-primary btn-sm" onclick="window._gwSaveEdge('${edgeData.id}')">Save</button>
        <button class="btn btn-ghost btn-sm" style="color:var(--red)" onclick="window._gwDeleteEdge('${edgeData.id}')">Delete</button>
      </div>
    </div>
  `;

  window._gwOnCondChange = (val) => {
    const wrap = document.getElementById('cfg-cond-threshold-wrap');
    if (wrap) wrap.style.display = val === 'always' ? 'none' : '';
  };
  window._gwSaveEdge   = (edgeId) => _saveEdgeConfig(edgeId);
  window._gwDeleteEdge = (edgeId) => _deleteEdge(edgeId);
}

async function _saveEdgeConfig(edgeId) {
  if (!_currentWf) return;
  const label     = document.getElementById('cfg-edge-label')?.value.trim() || '';
  const condType  = document.getElementById('cfg-cond-type')?.value || 'always';
  const fieldVal  = document.getElementById('cfg-cond-field')?.value.trim() || 'score';
  const threshold = parseFloat(document.getElementById('cfg-cond-value')?.value || '0');

  let condition = null;
  if (condType === 'score_gte') condition = { field: fieldVal, op: 'gte', value: threshold };
  if (condType === 'score_lt')  condition = { field: fieldVal, op: 'lt',  value: threshold };

  try {
    await api.graphWorkflows.updateEdge(_currentWf.id, edgeId, { label, condition });
    const cyEdge = _cy?.getElementById(edgeId);
    if (cyEdge) { cyEdge.data('label', label); cyEdge.data('condition', condition); }
    toast('Edge updated', 'success');
    _closeConfig();
  } catch (e) {
    toast(`Update failed: ${e.message}`, 'error');
  }
}

async function _deleteEdge(edgeId) {
  if (!_currentWf || !confirm('Delete this edge?')) return;
  try {
    await api.graphWorkflows.deleteEdge(_currentWf.id, edgeId);
    _cy?.getElementById(edgeId).remove();
    if (_currentWf.edges) _currentWf.edges = _currentWf.edges.filter(e => e.id !== edgeId);
    _closeConfig();
    toast('Edge deleted', 'success');
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
}

function _closeConfig() {
  const panel = document.getElementById('gw-config-panel');
  if (panel) panel.style.display = 'none';
}

// ── Connect mode ──────────────────────────────────────────────────────────────

function _enterConnectMode(sourceId) {
  _connectMode = true;
  _connectSourceId = sourceId;
  _closeConfig();
  const cyNode = _cy?.getElementById(sourceId);
  if (cyNode) cyNode.addClass('connect-source');
  toast('Click target node to connect', 'info');
}

function _exitConnectMode() {
  if (_connectSourceId) {
    const cyNode = _cy?.getElementById(_connectSourceId);
    if (cyNode) cyNode.removeClass('connect-source');
  }
  _connectMode = false;
  _connectSourceId = null;
}

async function _createEdge(sourceId, targetId) {
  if (!_currentWf) return;
  try {
    const edge = await api.graphWorkflows.createEdge(_currentWf.id, {
      source_node_id: sourceId,
      target_node_id: targetId,
    });
    _cy?.add({ group: 'edges', data: { id: edge.id, source: sourceId, target: targetId, label: '', condition: null } });
    if (_currentWf.edges) _currentWf.edges.push(edge);
  } catch (e) {
    toast(`Connect failed: ${e.message}`, 'error');
  }
}

// ── Node add helpers ──────────────────────────────────────────────────────────

async function _addNodeAt(x, y) {
  if (!_currentWf) return;
  const name = prompt('Agent name (e.g. "QA Engineer"):');
  if (!name) return;
  try {
    const node = await api.graphWorkflows.createNode(_currentWf.id, { name, position_x: x, position_y: y });
    _cy?.add({ group: 'nodes', data: { id: node.id, label: node.name, provider: node.provider, nodeData: node }, position: { x, y } });
    if (_currentWf.nodes) _currentWf.nodes.push(node);
    _openNodeConfig(node);
  } catch (e) {
    toast(`Add node failed: ${e.message}`, 'error');
  }
}

function _addNodeAtCenter() {
  if (!_currentWf) return;
  const ext = _cy?.extent();
  const x = ext ? (ext.x1 + ext.x2) / 2 : 300;
  const y = ext ? (ext.y1 + ext.y2) / 2 : 200;
  _addNodeAt(x, y);
}

// ── Run workflow ──────────────────────────────────────────────────────────────

async function _startRun(project) {
  if (!_currentWf) return;
  if (!(_currentWf.nodes || []).length) {
    toast('Add at least one node before running', 'error');
    return;
  }

  const userInput = prompt('Task / user input for this run (describes what agents should work on):') || '';

  try {
    const { run_id } = await api.graphWorkflows.startRun(_currentWf.id, {
      user_input: userInput,
      project: project || '',
    });
    _currentRunId = run_id;
    _showLog();
    _pollRun(run_id);
  } catch (e) {
    toast(`Run failed: ${e.message}`, 'error');
  }
}

async function _cancelRun() {
  if (!_currentRunId) return;
  try {
    await api.graphWorkflows.cancel(_currentRunId);
    if (_pollInterval) { clearInterval(_pollInterval); _pollInterval = null; }
    document.getElementById('gw-log-status').textContent = ' — cancelled';
    const cancelBtn = document.getElementById('gw-cancel-btn');
    if (cancelBtn) cancelBtn.style.display = 'none';
    toast('Run cancelled', 'info');
  } catch (e) {
    toast(`Cancel failed: ${e.message}`, 'error');
  }
}

function _showLog() {
  const panel  = document.getElementById('gw-log-panel');
  const body   = document.getElementById('gw-log-body');
  const status = document.getElementById('gw-log-status');
  const cancel = document.getElementById('gw-cancel-btn');
  if (!panel) return;
  panel.style.display = '';
  if (body)   body.innerHTML = '<div class="gw-log-entry">Starting run…</div>';
  if (status) status.textContent = ' — running';
  if (cancel) cancel.style.display = '';
}

function _toggleLog() {
  const body   = document.getElementById('gw-log-body');
  const toggle = document.querySelector('.gw-log-toggle');
  if (!body) return;
  const hidden = body.style.display === 'none';
  body.style.display = hidden ? '' : 'none';
  if (toggle) toggle.textContent = hidden ? '▲' : '▼';
}

function _pollRun(runId) {
  if (_pollInterval) clearInterval(_pollInterval);

  _pollInterval = setInterval(async () => {
    try {
      const run = await api.graphWorkflows.getRun(runId);
      _updateCanvasNodeStatuses(run);
      _updateRunLog(run);

      if (run.status === 'waiting_approval') {
        _showApprovalPanel(run);
      } else {
        const ap = document.getElementById('gw-approval-panel');
        if (ap) ap.style.display = 'none';
      }

      if (run.status !== 'running' && run.status !== 'waiting_approval') {
        clearInterval(_pollInterval);
        _pollInterval = null;
        const status = document.getElementById('gw-log-status');
        const cancel = document.getElementById('gw-cancel-btn');
        if (status) status.textContent = run.status === 'done'
          ? ` — done ($${Number(run.total_cost_usd || 0).toFixed(4)})`
          : ` — ${run.status}`;
        if (cancel) cancel.style.display = 'none';
      }
    } catch {
      clearInterval(_pollInterval);
      _pollInterval = null;
    }
  }, 2000);
}

function _updateCanvasNodeStatuses(run) {
  (run.node_results || []).forEach(nr => {
    const cyNode = _cy?.getElementById(nr.node_id);
    if (cyNode) cyNode.data('status', nr.status);
  });
}

function _updateRunLog(run) {
  const body = document.getElementById('gw-log-body');
  if (!body) return;
  const results = run.node_results || [];
  if (!results.length) {
    body.innerHTML = '<div style="padding:0.5rem;color:var(--muted);font-size:0.8rem">Waiting for first node to start…</div>';
    return;
  }
  body.innerHTML = results.map(nr => `
    <div class="gw-log-entry gw-log-${nr.status}">
      <div class="gw-log-node-header">
        <strong>${_esc(nr.node_name)}</strong>
        <span class="gw-log-badge gw-log-badge-${nr.status}">${nr.status}</span>
        ${nr.iteration > 0 ? `<span style="font-size:0.65rem;color:var(--muted)">iter ${nr.iteration}</span>` : ''}
        <span style="color:var(--muted);font-size:0.7rem;margin-left:auto">$${Number(nr.cost_usd || 0).toFixed(4)}</span>
      </div>
      ${nr.output ? `<pre class="gw-log-output">${_esc(nr.output.slice(0, 600))}${nr.output.length > 600 ? '\n…' : ''}</pre>` : ''}
    </div>
  `).join('');
}

function _showApprovalPanel(run) {
  const panel = document.getElementById('gw-approval-panel');
  if (!panel) return;
  panel.style.display = '';

  const waiting = run.context?._waiting || {};
  const nodeName  = _esc(waiting.node_name || 'Node');
  const msg       = _esc(waiting.approval_msg || 'Review the output and choose how to continue.');
  const output    = _esc((waiting.output || '').slice(0, 400));
  const successors = waiting.successors || [];

  // Build successor node names from _currentWf
  const nodeMap = {};
  (_currentWf?.nodes || []).forEach(n => { nodeMap[n.id] = n.name; });

  const goToOpts = successors.length > 1
    ? `<select id="ap-goto-select" class="field-input" style="font-size:0.75rem;padding:0.2rem">
        ${successors.map(nid => `<option value="${_esc(nid)}">${_esc(nodeMap[nid] || nid)}</option>`).join('')}
       </select>`
    : '';

  panel.innerHTML = `
    <div style="padding:0.75rem;background:rgba(245,158,11,0.08);border-bottom:1px solid #f59e0b">
      <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.4rem">
        <span style="font-size:1rem">⏸</span>
        <strong style="font-size:0.8rem">Waiting — ${nodeName}</strong>
      </div>
      <div style="color:var(--muted);font-size:0.75rem;margin-bottom:0.4rem">${msg}</div>
      ${output ? `<pre style="font-size:0.72rem;background:var(--bg);border:1px solid var(--border);border-radius:4px;padding:0.4rem;max-height:100px;overflow-y:auto;margin-bottom:0.5rem">${output}</pre>` : ''}
      <div style="display:flex;gap:0.4rem;flex-wrap:wrap;align-items:center">
        <button class="btn btn-primary btn-sm" style="font-size:0.75rem" onclick="window._gwDecide('approve')">✓ Continue</button>
        ${goToOpts}
        ${successors.length > 1 ? `<button class="btn btn-ghost btn-sm" style="font-size:0.75rem" onclick="window._gwDecide('goto')">→ Go to</button>` : ''}
        <button class="btn btn-ghost btn-sm" style="font-size:0.75rem" onclick="window._gwDecide('retry')">↺ Retry</button>
        <button class="btn btn-ghost btn-sm" style="font-size:0.75rem;color:var(--red)" onclick="window._gwDecide('stop')">✗ Stop</button>
      </div>
    </div>
  `;

  window._gwDecide = async (action) => {
    let body = {};
    if (action === 'approve') {
      body = { approved: true };
    } else if (action === 'goto') {
      const sel = document.getElementById('ap-goto-select');
      const nextNodeId = sel?.value || (successors[0] || null);
      body = { approved: true, next_node_id: nextNodeId };
    } else if (action === 'retry') {
      body = { approved: false, retry: true };
    } else {
      body = { approved: false };
    }

    try {
      await api.graphWorkflows.makeDecision(_currentRunId, body);
      panel.style.display = 'none';
      // Resume polling (might have stopped)
      if (!_pollInterval && _currentRunId) {
        document.getElementById('gw-cancel-btn').style.display = '';
        _pollRun(_currentRunId);
      }
    } catch (e) {
      toast(`Decision failed: ${e.message}`, 'error');
    }
  };
}

// ── New workflow modal ────────────────────────────────────────────────────────

function _showNewWorkflowModal(project) {
  const modal = _createModal(`
    <h3 style="margin-bottom:1rem;font-size:0.95rem">New Graph Flow</h3>
    <label style="font-size:0.75rem;color:var(--muted)">Name</label>
    <input class="field-input" id="modal-wf-name" style="margin-bottom:0.75rem" placeholder="e.g. Web Dev Pipeline" autofocus />
    <label style="font-size:0.75rem;color:var(--muted)">Description</label>
    <input class="field-input" id="modal-wf-desc" style="margin-bottom:0.75rem" placeholder="What does this flow do?" />
    <label style="font-size:0.75rem;color:var(--muted)">Max iterations</label>
    <input class="field-input" id="modal-wf-iter" type="number" value="5" style="margin-bottom:1rem" min="1" max="20" />
    <div style="display:flex;gap:0.5rem;justify-content:flex-end">
      <button class="btn btn-ghost btn-sm" id="modal-cancel">Cancel</button>
      <button class="btn btn-primary btn-sm" id="modal-create">Create</button>
    </div>
  `);

  modal.querySelector('#modal-cancel').onclick = () => modal.remove();
  modal.querySelector('#modal-create').onclick = async () => {
    const name = modal.querySelector('#modal-wf-name').value.trim();
    if (!name) { toast('Name required', 'error'); return; }
    const desc = modal.querySelector('#modal-wf-desc').value.trim();
    const maxIter = parseInt(modal.querySelector('#modal-wf-iter').value || '5', 10);
    try {
      const wf = await api.graphWorkflows.create({ name, description: desc, project: project || '', max_iterations: maxIter });
      modal.remove();
      _currentWf = { ...wf, nodes: [], edges: [] };
      _showToolbarButtons();
      _renderCanvas(_currentWf);
      await _loadList(project);
      toast('Flow created — double-click canvas or click "+ Node" to add agents', 'success');
    } catch (e) {
      toast(`Create failed: ${e.message}`, 'error');
    }
  };
}

// ── Template modal ────────────────────────────────────────────────────────────

function _showTemplateModal(project) {
  const modal = _createModal(`
    <h3 style="margin-bottom:0.75rem;font-size:0.95rem">New Flow from Template</h3>
    <p style="font-size:0.75rem;color:var(--muted);margin-bottom:0.75rem">
      Templates create a pre-configured flow with agents and edges.<br>
      Edit role files in the Prompts tab to customise each agent.
    </p>
    <div id="template-list" style="display:flex;flex-direction:column;gap:0.5rem;margin-bottom:1rem">
      ${TEMPLATES.map(t => `
        <label class="gw-template-option" style="display:flex;gap:0.75rem;align-items:flex-start;padding:0.6rem;border:1px solid var(--border);border-radius:var(--radius);cursor:pointer">
          <input type="radio" name="tpl" value="${t.id}" style="margin-top:3px" />
          <div>
            <div style="font-weight:600;font-size:0.8rem">${_esc(t.name)}</div>
            <div style="color:var(--muted);font-size:0.72rem">${_esc(t.description)}</div>
          </div>
        </label>
      `).join('')}
    </div>
    <div style="display:flex;gap:0.5rem;justify-content:flex-end">
      <button class="btn btn-ghost btn-sm" id="tpl-cancel">Cancel</button>
      <button class="btn btn-primary btn-sm" id="tpl-create">Create</button>
    </div>
  `);

  // Select first by default
  const firstRadio = modal.querySelector('input[type=radio]');
  if (firstRadio) firstRadio.checked = true;

  modal.querySelector('#tpl-cancel').onclick = () => modal.remove();
  modal.querySelector('#tpl-create').onclick = async () => {
    const selected = modal.querySelector('input[name=tpl]:checked');
    if (!selected) { toast('Select a template', 'error'); return; }
    const tpl = TEMPLATES.find(t => t.id === selected.value);
    if (!tpl) return;
    modal.remove();
    await _applyTemplate(tpl, project);
  };
}

async function _applyTemplate(tpl, project) {
  toast(`Creating "${tpl.name}"…`, 'info');
  try {
    // 1. Create workflow
    const wf = await api.graphWorkflows.create({
      name: tpl.name, description: tpl.description, project: project || '', max_iterations: 5,
    });

    // 2. Create nodes in order, collect IDs
    const nodeIds = [];
    for (const nSpec of tpl.nodes) {
      const node = await api.graphWorkflows.createNode(wf.id, {
        name: nSpec.name, provider: nSpec.provider,
        role_file: nSpec.role_file || null,
        role_prompt: nSpec.role_prompt || '',
        inject_context: true,
        position_x: nSpec.position_x || 100,
        position_y: nSpec.position_y || 150,
        require_approval: nSpec.require_approval || false,
        approval_msg: nSpec.approval_msg || '',
      });
      nodeIds.push(node.id);
    }

    // 3. Create edges using index-based references
    for (const eSpec of tpl.edges) {
      const sourceId = nodeIds[eSpec.from];
      const targetId = nodeIds[eSpec.to];
      if (!sourceId || !targetId) continue;
      await api.graphWorkflows.createEdge(wf.id, {
        source_node_id: sourceId,
        target_node_id: targetId,
        condition: eSpec.condition || null,
        label: eSpec.label || '',
      });
    }

    // 4. Load full workflow and render
    const full = await api.graphWorkflows.get(wf.id);
    _currentWf = full;
    _showToolbarButtons();
    _renderCanvas(full);
    _cy?.layout({ name: 'preset' }).run();
    await _loadList(project);
    toast(`"${tpl.name}" created with ${nodeIds.length} agents`, 'success');
  } catch (e) {
    toast(`Template failed: ${e.message}`, 'error');
  }
}

// ── Modal helper ──────────────────────────────────────────────────────────────

function _createModal(innerHTML) {
  const overlay = document.createElement('div');
  overlay.style.cssText = 'position:fixed;inset:0;z-index:9000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.45)';
  overlay.innerHTML = `
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:1.5rem;min-width:340px;max-width:520px;width:92%;max-height:80vh;overflow-y:auto">
      ${innerHTML}
    </div>
  `;
  // Click overlay background to close
  overlay.addEventListener('click', evt => { if (evt.target === overlay) overlay.remove(); });
  document.body.appendChild(overlay);
  return overlay;
}

// ── Utility ───────────────────────────────────────────────────────────────────

function _esc(str) {
  return String(str ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
