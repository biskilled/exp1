/**
 * graph_workflow.js — Cytoscape.js-based graph workflow editor.
 *
 * Structure mirrors workflow.js: sidebar list + canvas area + toolbar.
 * Nodes represent LLM roles; edges represent data flow with optional conditions.
 * Node positions are persisted to the backend on drag.
 * A collapsible run log shows node outputs as they complete (polling).
 */

import { state } from '../stores/state.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';

const PROVIDER_COLORS = {
  claude:   'var(--claude)',
  openai:   'var(--openai)',
  deepseek: 'var(--deepseek)',
  gemini:   'var(--gemini)',
  grok:     'var(--grok)',
};

const PROVIDER_BG = {
  claude:   '#fff3ee',
  openai:   '#e6f7f0',
  deepseek: '#e6f4fb',
  gemini:   '#e6f9ee',
  grok:     '#fdf6e3',
};

let _cy = null;          // Cytoscape instance
let _currentWf = null;   // loaded workflow object
let _connectMode = false; // edge-creation mode
let _connectSourceId = null;
let _pollInterval = null;

// ── Main render ───────────────────────────────────────────────────────────────

export function renderGraphWorkflow(container) {
  container.className = 'view active gw-view';
  const projectName = state.currentProject?.name;

  container.innerHTML = `
    <div class="gw-toolbar">
      <button class="btn btn-primary btn-sm" onclick="window._gwNewWorkflow()">+ New Flow</button>
      <div style="flex:1"></div>
      <button class="btn btn-ghost btn-sm" id="gw-run-btn" onclick="window._gwStartRun()" style="display:none">▶ Run</button>
      <button class="btn btn-ghost btn-sm" id="gw-layout-btn" onclick="window._gwRelayout()" style="display:none">⟳ Layout</button>
    </div>
    <div class="gw-body">
      <div class="gw-sidebar" id="gw-sidebar">
        <div style="padding:0.5rem 0.5rem 0.25rem">
          <div class="nav-section-label">Flows</div>
        </div>
        <div id="gw-list"></div>
      </div>
      <div class="gw-canvas-wrap" id="gw-canvas-wrap">
        <div id="cy-container" style="flex:1;height:100%;min-height:300px"></div>
        <div class="gw-log-panel" id="gw-log-panel" style="display:none">
          <div class="gw-log-header" onclick="window._gwToggleLog()">
            <span>Run Log</span><span id="gw-log-status"></span><span class="gw-log-toggle">▲</span>
          </div>
          <div class="gw-log-body" id="gw-log-body"></div>
        </div>
      </div>
      <div class="gw-config-panel" id="gw-config-panel" style="display:none">
        <div class="gw-config-header">
          <span id="gw-config-title">Node Config</span>
          <button class="btn btn-ghost btn-sm" onclick="window._gwCloseConfig()">✕</button>
        </div>
        <div id="gw-config-body"></div>
      </div>
    </div>
  `;

  window._gwNewWorkflow = () => _showNewWorkflowModal(projectName);
  window._gwStartRun = () => _startRun(projectName);
  window._gwRelayout = () => _cy?.layout({ name: 'dagre', rankDir: 'LR', nodeSep: 60, rankSep: 100 }).run();
  window._gwToggleLog = _toggleLog;
  window._gwCloseConfig = _closeConfig;

  _loadList(projectName);
}

// ── Workflow list ─────────────────────────────────────────────────────────────

async function _loadList(project) {
  const el = document.getElementById('gw-list');
  if (!el) return;
  el.innerHTML = '<div style="padding:0.5rem;color:var(--muted);font-size:0.75rem">Loading…</div>';
  try {
    const { workflows } = await api.graphWorkflows.list(project || '');
    if (!workflows.length) {
      el.innerHTML = '<div style="padding:0.5rem;color:var(--muted);font-size:0.75rem">No flows yet</div>';
      return;
    }
    el.innerHTML = workflows.map(wf => `
      <div class="gw-list-item ${_currentWf?.id === wf.id ? 'active' : ''}"
           onclick="window._gwOpenWf('${wf.id}')">
        <div style="font-weight:500;font-size:0.8rem">${_esc(wf.name)}</div>
        <div style="color:var(--muted);font-size:0.7rem">${_esc(wf.description || '')}</div>
      </div>
    `).join('');
    workflows.forEach(wf => {
      window[`_gwOpenWf`] = _openWorkflow;
    });
  } catch (e) {
    el.innerHTML = `<div style="padding:0.5rem;color:var(--red);font-size:0.75rem">${e.message}</div>`;
  }
}

window._gwOpenWf = _openWorkflow;

async function _openWorkflow(id) {
  try {
    const wf = await api.graphWorkflows.get(id);
    _currentWf = wf;
    document.getElementById('gw-run-btn').style.display = '';
    document.getElementById('gw-layout-btn').style.display = '';
    _renderCanvas(wf);
    _loadList(state.currentProject?.name);
  } catch (e) {
    toast(`Failed to load workflow: ${e.message}`, 'error');
  }
}

// ── Cytoscape canvas ──────────────────────────────────────────────────────────

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
      data: {
        id: e.id,
        source: e.source_node_id,
        target: e.target_node_id,
        label: e.label || '',
        condition: e.condition,
      },
    });
  });

  _cy = window.cytoscape({
    container,
    elements,
    style: _cytoscapeStyle(),
    layout: elements.filter(e => e.group === 'nodes').length
      ? { name: 'preset' }
      : { name: 'dagre', rankDir: 'LR', nodeSep: 60, rankSep: 100 },
    minZoom: 0.3,
    maxZoom: 3,
  });

  // Node tap → open config panel (or edge-connect mode)
  _cy.on('tap', 'node', evt => {
    const node = evt.target;
    if (_connectMode && _connectSourceId) {
      _createEdge(_connectSourceId, node.id());
      _exitConnectMode();
    } else {
      _openNodeConfig(node.data('nodeData'));
    }
  });

  // Edge tap → open edge config
  _cy.on('tap', 'edge', evt => {
    _openEdgeConfig(evt.target.data());
  });

  // Tap canvas background → cancel connect mode / close config
  _cy.on('tap', evt => {
    if (evt.target === _cy) {
      _exitConnectMode();
    }
  });

  // Drag end → persist position
  _cy.on('dragfree', 'node', evt => {
    const node = evt.target;
    const pos = node.position();
    const nodeData = node.data('nodeData');
    api.graphWorkflows.updateNode(_currentWf.id, node.id(), {
      position_x: pos.x,
      position_y: pos.y,
    }).catch(() => {});
    if (nodeData) {
      nodeData.position_x = pos.x;
      nodeData.position_y = pos.y;
    }
  });

  // Double-tap canvas → add node
  _cy.on('dbltap', evt => {
    if (evt.target === _cy) {
      const pos = evt.position;
      _addNodeAt(pos.x, pos.y);
    }
  });
}

function _cytoscapeStyle() {
  return [
    {
      selector: 'node',
      style: {
        'label': 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '11px',
        'font-family': 'JetBrains Mono, monospace',
        'width': '120px',
        'height': '50px',
        'shape': 'round-rectangle',
        'background-color': ele => PROVIDER_BG[ele.data('provider')] || '#f0f0f0',
        'border-color': ele => PROVIDER_COLORS[ele.data('provider')] || '#888',
        'border-width': '2px',
        'color': '#1a1a2e',
        'text-wrap': 'wrap',
        'text-max-width': '110px',
        'padding': '8px',
      },
    },
    {
      selector: 'node[status="running"]',
      style: { 'border-width': '3px', 'border-color': 'var(--accent)', 'border-style': 'dashed' },
    },
    {
      selector: 'node[status="done"]',
      style: { 'border-width': '3px', 'border-color': 'var(--green)' },
    },
    {
      selector: 'node[status="error"]',
      style: { 'border-width': '3px', 'border-color': 'var(--red)' },
    },
    {
      selector: 'node.connect-source',
      style: { 'border-width': '4px', 'border-color': 'var(--accent)' },
    },
    {
      selector: 'edge',
      style: {
        'curve-style': 'bezier',
        'target-arrow-shape': 'triangle',
        'target-arrow-color': 'var(--muted)',
        'line-color': 'var(--border)',
        'width': 2,
        'label': 'data(label)',
        'font-size': '9px',
        'color': 'var(--muted)',
        'text-background-color': 'var(--bg)',
        'text-background-opacity': 1,
        'text-background-padding': '2px',
      },
    },
    {
      selector: 'edge[?condition]',
      style: { 'line-style': 'dashed', 'line-color': 'var(--accent)' },
    },
  ];
}

// ── Node config panel ─────────────────────────────────────────────────────────

function _openNodeConfig(nodeData) {
  const panel = document.getElementById('gw-config-panel');
  const title = document.getElementById('gw-config-title');
  const body = document.getElementById('gw-config-body');
  if (!panel) return;
  panel.style.display = '';
  title.textContent = 'Node: ' + (nodeData?.name || 'New');

  const n = nodeData || {};
  body.innerHTML = `
    <div class="gw-config-form">
      <label>Name</label>
      <input class="field-input" id="cfg-name" value="${_esc(n.name || '')}" />

      <label>Provider</label>
      <select class="field-input" id="cfg-provider">
        ${['claude','openai','deepseek','gemini','grok'].map(p =>
          `<option value="${p}" ${n.provider === p ? 'selected' : ''}>${p}</option>`
        ).join('')}
      </select>

      <label>Model (blank = default)</label>
      <input class="field-input" id="cfg-model" value="${_esc(n.model || '')}" />

      <label>Role file (e.g. roles/architect.md)</label>
      <input class="field-input" id="cfg-role-file" value="${_esc(n.role_file || '')}" />

      <label>Inline role prompt</label>
      <textarea class="field-input" id="cfg-role-prompt" rows="4">${_esc(n.role_prompt || '')}</textarea>

      <label>Inject context from previous nodes</label>
      <select class="field-input" id="cfg-inject">
        <option value="true" ${n.inject_context !== false ? 'selected' : ''}>Yes</option>
        <option value="false" ${n.inject_context === false ? 'selected' : ''}>No</option>
      </select>

      <div style="display:flex;gap:0.5rem;margin-top:0.75rem;flex-wrap:wrap">
        <button class="btn btn-primary btn-sm" onclick="window._gwSaveNode('${n.id || ''}')">Save</button>
        <button class="btn btn-ghost btn-sm" onclick="window._gwConnectFrom('${n.id || ''}')">Connect →</button>
        ${n.id ? `<button class="btn btn-ghost btn-sm" style="color:var(--red)" onclick="window._gwDeleteNode('${n.id}')">Delete</button>` : ''}
      </div>
    </div>
  `;

  window._gwSaveNode = (nodeId) => _saveNodeConfig(nodeId, nodeData);
  window._gwConnectFrom = (nodeId) => _enterConnectMode(nodeId);
  window._gwDeleteNode = (nodeId) => _deleteNode(nodeId);
}

function _openEdgeConfig(edgeData) {
  const panel = document.getElementById('gw-config-panel');
  const title = document.getElementById('gw-config-title');
  const body = document.getElementById('gw-config-body');
  if (!panel) return;
  panel.style.display = '';
  title.textContent = 'Edge Config';

  const cond = edgeData.condition || {};
  body.innerHTML = `
    <div class="gw-config-form">
      <label>Label</label>
      <input class="field-input" id="cfg-edge-label" value="${_esc(edgeData.label || '')}" />

      <label>Condition (optional)</label>
      <div style="display:grid;grid-template-columns:1fr 80px 1fr;gap:0.25rem">
        <input class="field-input" id="cfg-cond-field" placeholder="field" value="${_esc(cond.field || '')}" />
        <select class="field-input" id="cfg-cond-op">
          ${['eq','neq','gte','gt','lt','lte','contains'].map(op =>
            `<option ${cond.op === op ? 'selected' : ''}>${op}</option>`
          ).join('')}
        </select>
        <input class="field-input" id="cfg-cond-value" placeholder="value" value="${_esc(String(cond.value ?? ''))}" />
      </div>
      <div style="display:flex;gap:0.5rem;margin-top:0.75rem">
        <button class="btn btn-primary btn-sm" onclick="window._gwSaveEdge('${edgeData.id}')">Save</button>
        <button class="btn btn-ghost btn-sm" style="color:var(--red)" onclick="window._gwDeleteEdge('${edgeData.id}')">Delete</button>
      </div>
    </div>
  `;

  window._gwSaveEdge = (edgeId) => _saveEdgeConfig(edgeId);
  window._gwDeleteEdge = (edgeId) => _deleteEdge(edgeId);
}

function _closeConfig() {
  const panel = document.getElementById('gw-config-panel');
  if (panel) panel.style.display = 'none';
}

// ── Node operations ───────────────────────────────────────────────────────────

async function _addNodeAt(x, y) {
  if (!_currentWf) return;
  const name = prompt('Node name:');
  if (!name) return;
  try {
    const node = await api.graphWorkflows.createNode(_currentWf.id, {
      name, position_x: x, position_y: y,
    });
    _cy.add({ group: 'nodes', data: { id: node.id, label: node.name, provider: node.provider, nodeData: node }, position: { x, y } });
    _currentWf.nodes = (_currentWf.nodes || []).concat(node);
    _openNodeConfig(node);
  } catch (e) {
    toast(`Add node failed: ${e.message}`, 'error');
  }
}

async function _saveNodeConfig(nodeId, existingData) {
  if (!_currentWf) return;
  const name = document.getElementById('cfg-name')?.value.trim() || '';
  const provider = document.getElementById('cfg-provider')?.value || 'claude';
  const model = document.getElementById('cfg-model')?.value.trim() || '';
  const roleFile = document.getElementById('cfg-role-file')?.value.trim() || null;
  const rolePrompt = document.getElementById('cfg-role-prompt')?.value || '';
  const injectContext = document.getElementById('cfg-inject')?.value !== 'false';

  const body = { name, provider, model, role_file: roleFile || null, role_prompt: rolePrompt, inject_context: injectContext };

  try {
    if (nodeId) {
      await api.graphWorkflows.updateNode(_currentWf.id, nodeId, body);
      // Update canvas node label + provider color
      const cyNode = _cy.getElementById(nodeId);
      if (cyNode) {
        cyNode.data('label', name);
        cyNode.data('provider', provider);
        if (cyNode.data('nodeData')) Object.assign(cyNode.data('nodeData'), body);
      }
    } else {
      const node = await api.graphWorkflows.createNode(_currentWf.id, body);
      _cy.add({ group: 'nodes', data: { id: node.id, label: node.name, provider: node.provider, nodeData: node }, position: { x: 200, y: 200 } });
      _currentWf.nodes = (_currentWf.nodes || []).concat(node);
    }
    toast('Saved', 'success');
  } catch (e) {
    toast(`Save failed: ${e.message}`, 'error');
  }
}

async function _deleteNode(nodeId) {
  if (!_currentWf || !confirm('Delete node?')) return;
  try {
    await api.graphWorkflows.deleteNode(_currentWf.id, nodeId);
    _cy.getElementById(nodeId).remove();
    _currentWf.nodes = (_currentWf.nodes || []).filter(n => n.id !== nodeId);
    _closeConfig();
    toast('Deleted', 'success');
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
}

// ── Edge operations ───────────────────────────────────────────────────────────

function _enterConnectMode(sourceId) {
  _connectMode = true;
  _connectSourceId = sourceId;
  _closeConfig();
  const cyNode = _cy.getElementById(sourceId);
  if (cyNode) cyNode.addClass('connect-source');
  toast('Click target node to connect', 'info');
}

function _exitConnectMode() {
  if (_connectSourceId) {
    const cyNode = _cy.getElementById(_connectSourceId);
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
    _cy.add({ group: 'edges', data: { id: edge.id, source: sourceId, target: targetId, label: '', condition: null } });
    _currentWf.edges = (_currentWf.edges || []).concat(edge);
  } catch (e) {
    toast(`Connect failed: ${e.message}`, 'error');
  }
}

async function _saveEdgeConfig(edgeId) {
  if (!_currentWf) return;
  const label = document.getElementById('cfg-edge-label')?.value.trim() || '';
  const field = document.getElementById('cfg-cond-field')?.value.trim();
  const op = document.getElementById('cfg-cond-op')?.value;
  const rawVal = document.getElementById('cfg-cond-value')?.value.trim();
  const condition = field ? { field, op, value: isNaN(rawVal) ? rawVal : Number(rawVal) } : null;

  try {
    await api.graphWorkflows.updateEdge(_currentWf.id, edgeId, { label, condition });
    const cyEdge = _cy.getElementById(edgeId);
    if (cyEdge) { cyEdge.data('label', label); cyEdge.data('condition', condition); }
    toast('Edge updated', 'success');
    _closeConfig();
  } catch (e) {
    toast(`Update failed: ${e.message}`, 'error');
  }
}

async function _deleteEdge(edgeId) {
  if (!_currentWf || !confirm('Delete edge?')) return;
  try {
    await api.graphWorkflows.deleteEdge(_currentWf.id, edgeId);
    _cy.getElementById(edgeId).remove();
    _currentWf.edges = (_currentWf.edges || []).filter(e => e.id !== edgeId);
    _closeConfig();
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
}

// ── Run workflow ──────────────────────────────────────────────────────────────

async function _startRun(project) {
  if (!_currentWf) return;
  const userInput = prompt('User input for this run (optional):') || '';

  try {
    const { run_id } = await api.graphWorkflows.startRun(_currentWf.id, {
      user_input: userInput,
      project: project || '',
    });
    _showLog(run_id);
    _pollRun(run_id);
  } catch (e) {
    toast(`Run failed: ${e.message}`, 'error');
  }
}

function _showLog(runId) {
  const panel = document.getElementById('gw-log-panel');
  const body = document.getElementById('gw-log-body');
  if (!panel || !body) return;
  panel.style.display = '';
  body.innerHTML = '<div class="gw-log-entry">Starting run…</div>';
  document.getElementById('gw-log-status').textContent = ' — running';
}

function _toggleLog() {
  const body = document.getElementById('gw-log-body');
  const toggle = document.querySelector('.gw-log-toggle');
  if (!body) return;
  const hidden = body.style.display === 'none';
  body.style.display = hidden ? '' : 'none';
  if (toggle) toggle.textContent = hidden ? '▲' : '▼';
}

function _pollRun(runId) {
  if (_pollInterval) clearInterval(_pollInterval);
  let lastResultCount = 0;

  _pollInterval = setInterval(async () => {
    try {
      const run = await api.graphWorkflows.getRun(runId);
      _updateRunLog(run);

      // Update node statuses on canvas
      (run.node_results || []).slice(lastResultCount).forEach(nr => {
        const cyNode = _cy?.getElementById(nr.node_id);
        if (cyNode) cyNode.data('status', nr.status);
      });
      lastResultCount = (run.node_results || []).length;

      if (run.status !== 'running') {
        clearInterval(_pollInterval);
        _pollInterval = null;
        document.getElementById('gw-log-status').textContent =
          run.status === 'done' ? ` — done ($${run.total_cost_usd?.toFixed(4)})` : ` — ${run.status}`;
      }
    } catch (e) {
      clearInterval(_pollInterval);
    }
  }, 2000);
}

function _updateRunLog(run) {
  const body = document.getElementById('gw-log-body');
  if (!body) return;
  const results = run.node_results || [];
  body.innerHTML = results.map(nr => `
    <div class="gw-log-entry gw-log-${nr.status}">
      <div class="gw-log-node-header">
        <strong>${_esc(nr.node_name)}</strong>
        <span class="gw-log-badge gw-log-badge-${nr.status}">${nr.status}</span>
        <span style="color:var(--muted);font-size:0.7rem">$${Number(nr.cost_usd || 0).toFixed(4)}</span>
      </div>
      ${nr.output ? `<pre class="gw-log-output">${_esc(nr.output.slice(0, 500))}${nr.output.length > 500 ? '…' : ''}</pre>` : ''}
    </div>
  `).join('') || '<div style="padding:0.5rem;color:var(--muted)">Waiting for results…</div>';
}

// ── New workflow modal ────────────────────────────────────────────────────────

function _showNewWorkflowModal(project) {
  const modal = document.createElement('div');
  modal.style.cssText = 'position:fixed;inset:0;z-index:9000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.5)';
  modal.innerHTML = `
    <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:1.5rem;min-width:320px;max-width:480px;width:90%">
      <h3 style="margin-bottom:1rem;font-size:0.95rem">New Graph Flow</h3>
      <label style="font-size:0.75rem;color:var(--muted)">Name</label>
      <input class="field-input" id="modal-wf-name" style="margin-bottom:0.75rem" placeholder="e.g. Trading Algo Pipeline" />
      <label style="font-size:0.75rem;color:var(--muted)">Description</label>
      <input class="field-input" id="modal-wf-desc" style="margin-bottom:1rem" placeholder="What does this flow do?" />
      <div style="display:flex;gap:0.5rem;justify-content:flex-end">
        <button class="btn btn-ghost btn-sm" onclick="this.closest('[style]').remove()">Cancel</button>
        <button class="btn btn-primary btn-sm" id="modal-wf-create">Create</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  modal.querySelector('#modal-wf-create').onclick = async () => {
    const name = modal.querySelector('#modal-wf-name').value.trim();
    if (!name) return toast('Name required', 'error');
    const desc = modal.querySelector('#modal-wf-desc').value.trim();
    try {
      const wf = await api.graphWorkflows.create({ name, description: desc, project: project || '' });
      modal.remove();
      _currentWf = wf;
      _currentWf.nodes = [];
      _currentWf.edges = [];
      _renderCanvas(_currentWf);
      document.getElementById('gw-run-btn').style.display = '';
      document.getElementById('gw-layout-btn').style.display = '';
      await _loadList(project);
      toast('Flow created — double-click canvas to add nodes', 'success');
    } catch (e) {
      toast(`Create failed: ${e.message}`, 'error');
    }
  };
}

// ── Utility ───────────────────────────────────────────────────────────────────

function _esc(str) {
  return String(str ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
