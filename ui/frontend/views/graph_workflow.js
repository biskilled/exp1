/**
 * graph_workflow.js — Horizontal CSS pipeline designer (v2).
 *
 * Replaces Cytoscape.js with a pure-CSS horizontal card-based layout.
 * Left sidebar: saved workflows + role library + IO type legend.
 * Center canvas: scrollable horizontal pipeline with connector arrows.
 * Right detail panel: full node config (slides in on node click).
 * Bottom run log: collapsible, approval panel overlay.
 */

import { state } from '../stores/state.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';

// ── IO type definitions ────────────────────────────────────────────────────────

const IO_TYPES = {
  prompt:   { color: '#9b7ef8', bg: 'rgba(155,126,248,0.15)', label: 'Prompt' },
  md:       { color: '#5b8ef0', bg: 'rgba(91,142,240,0.15)',  label: 'Markdown' },
  code:     { color: '#3ecf8e', bg: 'rgba(62,207,142,0.15)',  label: 'Code' },
  github:   { color: '#3ecf8e', bg: 'rgba(62,207,142,0.15)',  label: 'GitHub' },
  tests:    { color: '#f5a623', bg: 'rgba(245,166,35,0.15)',  label: 'Tests' },
  report:   { color: '#f5a623', bg: 'rgba(245,166,35,0.15)',  label: 'Report' },
  feedback: { color: '#e85d75', bg: 'rgba(232,93,117,0.15)', label: 'Feedback' },
  score:    { color: '#2dd4bf', bg: 'rgba(45,212,191,0.15)', label: 'Score' },
  json:     { color: '#2dd4bf', bg: 'rgba(45,212,191,0.15)', label: 'JSON' },
};

// ── Role presets ───────────────────────────────────────────────────────────────

const ROLE_PRESETS = {
  planner: {
    label: 'Planner', color: '#9b7ef8', badge: 'SDD', stateless: false,
    inputs:  [{ name: 'prompt',  type: 'prompt' }],
    outputs: [{ name: 'spec.md', type: 'md' }],
    success_criteria: 'reviewer_approved',
    role_prompt: 'You are a senior product manager. Produce a detailed spec document.',
  },
  developer: {
    label: 'Developer', color: '#3ecf8e', badge: 'DEV', stateless: false,
    inputs:  [{ name: 'spec.md', type: 'md' }],
    outputs: [{ name: 'code', type: 'code' }, { name: 'github_pr', type: 'github' }],
    success_criteria: 'tests_pass',
    role_prompt: 'You are a senior software engineer. Implement the spec.',
  },
  tester: {
    label: 'Tester', color: '#f5a623', badge: 'QA', stateless: false,
    inputs:  [{ name: 'code', type: 'code' }],
    outputs: [{ name: 'test_report.md', type: 'tests' }, { name: 'score', type: 'score' }],
    success_criteria: 'score >= 80',
    role_prompt: 'You are a QA engineer. Test the code and provide a score out of 100.',
  },
  reviewer_stateless: {
    label: 'Reviewer', color: '#2dd4bf', badge: '∅', stateless: true,
    inputs:  [{ name: 'code', type: 'code' }, { name: 'spec.md', type: 'md' }],
    outputs: [{ name: 'feedback.md', type: 'feedback' }, { name: 'approved', type: 'score' }],
    success_criteria: 'approved == true',
    role_prompt: 'You are a code reviewer. Review with fresh eyes (no history).',
  },
  reviewer_stateful: {
    label: 'Reviewer', color: '#e85d75', badge: '●', stateless: false,
    inputs:  [{ name: 'code', type: 'code' }, { name: 'prev_feedback', type: 'feedback' }],
    outputs: [{ name: 'feedback.md', type: 'feedback' }, { name: 'score', type: 'score' }],
    success_criteria: 'score >= 85',
    role_prompt: 'You are a stateful code reviewer. Track your feedback across iterations.',
  },
  custom: {
    label: 'Custom', color: '#6b7490', badge: 'NEW', stateless: false,
    inputs:  [{ name: 'input', type: 'prompt' }],
    outputs: [{ name: 'output', type: 'json' }],
    success_criteria: '',
    role_prompt: '',
  },
};

// ── Module state ───────────────────────────────────────────────────────────────

let _project = '';
let _currentWf = null;
let _selectedNodeId = null;
let _pollInterval = null;
let _currentRunId = null;
let _roles = [];

// ── Entry point ───────────────────────────────────────────────────────────────

export function renderGraphWorkflow(container) {
  container.className = 'view active gw-view';
  _project = state.currentProject?.name || '';

  if (_pollInterval) { clearInterval(_pollInterval); _pollInterval = null; }
  _currentWf = null;
  _selectedNodeId = null;

  container.innerHTML = `
    <style>
      .gw-view { display:flex; flex-direction:column; height:100%; overflow:hidden; }

      /* Layout */
      .gw-body2 { display:flex; flex:1; overflow:hidden; }
      .gw-sidebar2 { width:220px; min-width:180px; border-right:1px solid var(--border);
        overflow-y:auto; display:flex; flex-direction:column; gap:0; }
      .gw-main { flex:1; display:flex; flex-direction:column; overflow:hidden; }
      .gw-detail { width:320px; border-left:1px solid var(--border); overflow-y:auto;
        display:none; flex-direction:column; }
      .gw-detail.open { display:flex; }

      /* Sidebar */
      .gw-sb-section { border-bottom:1px solid var(--border); padding:0.5rem 0; }
      .gw-sb-label { font-size:0.65rem; font-weight:600; text-transform:uppercase;
        letter-spacing:0.05em; color:var(--muted); padding:0.25rem 0.75rem 0.1rem; }
      .gw-wf-item { padding:0.35rem 0.75rem; cursor:pointer; font-size:0.8rem;
        border-left:3px solid transparent; transition:background 0.1s; }
      .gw-wf-item:hover { background:var(--hover); }
      .gw-wf-item.active { border-left-color:var(--accent); background:var(--hover); font-weight:500; }
      .gw-role-card { display:flex; align-items:center; gap:0.4rem; padding:0.3rem 0.75rem;
        cursor:pointer; font-size:0.78rem; border-radius:0; transition:background 0.1s; }
      .gw-role-card:hover { background:var(--hover); }
      .gw-role-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
      .gw-role-badge { font-size:0.6rem; background:var(--border); border-radius:3px;
        padding:0.05rem 0.25rem; color:var(--muted); }
      .gw-io-legend { display:flex; flex-wrap:wrap; gap:0.25rem; padding:0.35rem 0.5rem; }
      .gw-io-pill { font-size:0.62rem; border-radius:8px; padding:0.1rem 0.4rem;
        font-weight:500; cursor:default; }

      /* Toolbar */
      .gw-toolbar2 { display:flex; align-items:center; gap:0.5rem; padding:0.5rem 0.75rem;
        border-bottom:1px solid var(--border); flex-shrink:0; }
      .gw-wf-name { font-size:0.85rem; font-weight:600; padding:0.25rem 0.5rem;
        border:1px solid transparent; border-radius:4px; background:transparent;
        color:var(--fg); min-width:120px; max-width:240px; }
      .gw-wf-name:focus { border-color:var(--accent); outline:none; background:var(--bg2); }

      /* Canvas area */
      .gw-canvas-area { flex:1; overflow:hidden; display:flex; flex-direction:column; }
      .gw-pipeline-scroll { flex:1; overflow-x:auto; overflow-y:auto; padding:2rem; }
      .gw-pipeline { display:flex; align-items:flex-start; gap:0; min-height:200px; }

      /* Node cards */
      .gw-node-card { width:180px; flex-shrink:0; border:2px solid var(--border);
        border-radius:8px; background:var(--bg1); cursor:pointer; transition:all 0.15s;
        position:relative; }
      .gw-node-card:hover { border-color:var(--accent); box-shadow:0 2px 8px rgba(0,0,0,0.1); }
      .gw-node-card.selected { border-color:var(--accent); box-shadow:0 0 0 3px rgba(100,108,255,0.2); }
      .gw-node-header { display:flex; align-items:center; gap:0.4rem; padding:0.5rem 0.6rem 0.35rem;
        border-bottom:1px solid var(--border); }
      .gw-node-dot { width:10px; height:10px; border-radius:50%; flex-shrink:0; }
      .gw-node-name { flex:1; font-size:0.78rem; font-weight:600; white-space:nowrap;
        overflow:hidden; text-overflow:ellipsis; }
      .gw-node-badge { font-size:0.58rem; padding:0.1rem 0.3rem; border-radius:3px;
        background:var(--border); color:var(--muted); flex-shrink:0; }
      .gw-node-del { display:none; position:absolute; top:4px; right:4px; background:none;
        border:none; color:var(--muted); cursor:pointer; font-size:0.7rem; padding:2px 4px; }
      .gw-node-card:hover .gw-node-del { display:block; }
      .gw-node-body { padding:0.4rem 0.6rem; }
      .gw-node-io-section { margin-bottom:0.3rem; }
      .gw-node-io-label { font-size:0.58rem; text-transform:uppercase; letter-spacing:0.04em;
        color:var(--muted); margin-bottom:0.15rem; }
      .gw-node-io-tags { display:flex; flex-wrap:wrap; gap:0.2rem; }
      .gw-node-footer { padding:0.3rem 0.6rem 0.4rem; border-top:1px solid var(--border);
        font-size:0.65rem; color:var(--muted); display:flex; justify-content:space-between; }
      .gw-stateless-badge { font-size:0.6rem; color:var(--muted); }
      .gw-node-status { position:absolute; bottom:4px; right:6px; width:8px; height:8px;
        border-radius:50%; }
      .gw-node-status.running  { background:#f5a623; animation:pulse 1s infinite; }
      .gw-node-status.done     { background:#3ecf8e; }
      .gw-node-status.error    { background:#e85d75; }
      @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

      /* Connectors */
      .gw-connector { display:flex; align-items:center; padding:0 0.2rem; flex-shrink:0;
        position:relative; }
      .gw-conn-line { width:32px; height:2px; background:var(--border); position:relative; }
      .gw-conn-line::after { content:'▶'; position:absolute; right:-6px; top:-7px;
        font-size:0.75rem; color:var(--border); }
      .gw-conn-label { position:absolute; top:-14px; left:50%; transform:translateX(-50%);
        font-size:0.6rem; color:var(--muted); white-space:nowrap; background:var(--bg1);
        padding:0 2px; }
      .gw-add-btn { width:36px; height:36px; border-radius:50%; border:2px dashed var(--border);
        background:none; color:var(--muted); cursor:pointer; font-size:1.1rem; display:flex;
        align-items:center; justify-content:center; margin:auto 0.5rem; transition:all 0.15s; }
      .gw-add-btn:hover { border-color:var(--accent); color:var(--accent); }

      /* Run log */
      .gw-log { border-top:1px solid var(--border); flex-shrink:0; max-height:220px;
        display:none; flex-direction:column; }
      .gw-log.open { display:flex; }
      .gw-log-hdr { display:flex; align-items:center; gap:0.5rem; padding:0.4rem 0.75rem;
        cursor:pointer; background:var(--bg2); font-size:0.78rem; font-weight:600; }
      .gw-log-body { overflow-y:auto; flex:1; font-size:0.75rem; padding:0.5rem 0.75rem; }
      .gw-log-entry { padding:0.2rem 0; border-bottom:1px solid var(--border); }
      .gw-log-entry:last-child { border:none; }

      /* Approval panel */
      .gw-approval { background:rgba(245,166,35,0.08); border:1px solid rgba(245,166,35,0.4);
        border-radius:6px; padding:0.75rem; margin-bottom:0.5rem; }
      .gw-approval h4 { margin:0 0 0.4rem; font-size:0.8rem; }
      .gw-approval pre { max-height:100px; overflow:auto; font-size:0.7rem;
        background:var(--bg2); border-radius:4px; padding:0.4rem; margin:0.4rem 0; }
      .gw-approval-btns { display:flex; gap:0.5rem; margin-top:0.5rem; }

      /* Detail panel */
      .gw-detail-hdr { display:flex; align-items:center; justify-content:space-between;
        padding:0.6rem 0.75rem; border-bottom:1px solid var(--border); font-weight:600;
        font-size:0.82rem; }
      .gw-detail-body { padding:0.75rem; overflow-y:auto; flex:1; }
      .gw-field { margin-bottom:0.75rem; }
      .gw-field label { display:block; font-size:0.72rem; font-weight:600; margin-bottom:0.25rem;
        color:var(--muted); text-transform:uppercase; letter-spacing:0.03em; }
      .gw-field input, .gw-field select, .gw-field textarea {
        width:100%; box-sizing:border-box; padding:0.3rem 0.5rem; border:1px solid var(--border);
        border-radius:4px; background:var(--bg1); color:var(--fg); font-size:0.8rem; }
      .gw-field textarea { resize:vertical; min-height:60px; }
      .gw-io-editor { display:flex; flex-direction:column; gap:0.3rem; }
      .gw-io-row { display:flex; align-items:center; gap:0.3rem; }
      .gw-io-row input { flex:1; }
      .gw-io-row select { width:90px; flex-shrink:0; }
      .gw-io-row button { padding:0.2rem 0.4rem; border:none; background:none;
        color:var(--muted); cursor:pointer; font-size:0.75rem; }
      .gw-add-io-btn { font-size:0.72rem; color:var(--accent); background:none; border:none;
        cursor:pointer; padding:0.15rem 0; }
      .gw-toggle-row { display:flex; align-items:center; justify-content:space-between; }
      .gw-detail-footer { padding:0.6rem 0.75rem; border-top:1px solid var(--border); }

      /* Empty state */
      .gw-empty { flex:1; display:flex; align-items:center; justify-content:center;
        flex-direction:column; gap:0.5rem; color:var(--muted); font-size:0.85rem; }
    </style>

    <div class="gw-toolbar2">
      <button class="btn btn-primary btn-sm" id="gw-new-btn" onclick="window._gwNew()">+ New Flow</button>
      <div id="gw-wf-name-wrap" style="display:none">
        <input class="gw-wf-name" id="gw-wf-name" placeholder="Flow name" onblur="window._gwSaveName(this.value)" />
      </div>
      <div style="flex:1"></div>
      <div id="gw-run-controls" style="display:none;display:none;gap:0.4rem;align-items:center" class="flex">
        <button class="btn btn-ghost btn-sm" id="gw-export-yaml-btn" onclick="window._gwExportYAML()">Export YAML</button>
        <button class="btn btn-ghost btn-sm" id="gw-export-lg-btn" onclick="window._gwExportLG()">Export LangGraph</button>
        <label class="btn btn-ghost btn-sm" style="cursor:pointer">
          Import YAML <input type="file" accept=".yaml,.yml" style="display:none" onchange="window._gwImportYAML(this)">
        </label>
        <button class="btn btn-primary btn-sm" onclick="window._gwStartRun()">▶ Run</button>
      </div>
    </div>

    <div class="gw-body2">
      <div class="gw-sidebar2">
        <div class="gw-sb-section">
          <div class="gw-sb-label">Saved Flows</div>
          <div id="gw-wf-list"><div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">Loading…</div></div>
        </div>
        <div class="gw-sb-section">
          <div class="gw-sb-label">Role Library</div>
          ${Object.entries(ROLE_PRESETS).map(([key, p]) => `
            <div class="gw-role-card" onclick="window._gwAddPreset('${key}')" title="Add to pipeline">
              <div class="gw-role-dot" style="background:${p.color}"></div>
              <span style="flex:1">${_esc(p.label)}</span>
              <span class="gw-role-badge">${_esc(p.badge)}</span>
            </div>
          `).join('')}
        </div>
        <div class="gw-sb-section">
          <div class="gw-sb-label">IO Types</div>
          <div class="gw-io-legend">
            ${Object.entries(IO_TYPES).map(([t, d]) => `
              <span class="gw-io-pill" style="background:${d.bg};color:${d.color}">${t}</span>
            `).join('')}
          </div>
        </div>
      </div>

      <div class="gw-main">
        <div class="gw-canvas-area">
          <div class="gw-pipeline-scroll" id="gw-pipeline-scroll">
            <div class="gw-empty" id="gw-empty-state">
              <div style="font-size:2rem">🔧</div>
              <div>Select a flow or create a new one</div>
              <div style="font-size:0.75rem">Then drag roles from the sidebar to build your pipeline</div>
            </div>
            <div class="gw-pipeline" id="gw-pipeline" style="display:none"></div>
          </div>
          <div class="gw-log" id="gw-log">
            <div class="gw-log-hdr" onclick="window._gwToggleLog()">
              <span>Run Log</span>
              <span id="gw-log-status" style="font-size:0.72rem;color:var(--muted)"></span>
              <div style="flex:1"></div>
              <button id="gw-cancel-btn" class="btn btn-ghost btn-sm"
                style="display:none;color:var(--red);font-size:0.7rem"
                onclick="event.stopPropagation();window._gwCancelRun()">✕ Cancel</button>
              <span id="gw-log-toggle">▼</span>
            </div>
            <div id="gw-approval-wrap" style="display:none;padding:0.5rem 0.75rem 0"></div>
            <div class="gw-log-body" id="gw-log-body"></div>
          </div>
        </div>
      </div>

      <div class="gw-detail" id="gw-detail">
        <div class="gw-detail-hdr">
          <span id="gw-detail-title">Node Config</span>
          <button class="btn btn-ghost btn-sm" onclick="window._gwCloseDetail()">✕</button>
        </div>
        <div class="gw-detail-body" id="gw-detail-body"></div>
        <div class="gw-detail-footer">
          <button class="btn btn-primary btn-sm" style="width:100%" onclick="window._gwSaveNode()">Save Changes</button>
        </div>
      </div>
    </div>
  `;

  // Register globals
  window._gwNew         = () => _newWorkflow();
  window._gwSaveName    = (v) => _saveWorkflowName(v);
  window._gwAddPreset   = (key) => _addFromPreset(key);
  window._gwStartRun    = () => _startRun();
  window._gwCancelRun   = () => _cancelRun();
  window._gwToggleLog   = _toggleLog;
  window._gwCloseDetail = _closeDetail;
  window._gwSaveNode    = _saveNodeFromForm;
  window._gwExportYAML  = _exportYAML;
  window._gwExportLG    = _exportLangGraph;
  window._gwImportYAML  = _importYAML;

  _loadList();
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function _ioTag(io) {
  const def = IO_TYPES[io.type] || { color: '#888', bg: 'rgba(136,136,136,0.15)' };
  return `<span class="gw-io-pill" style="background:${def.bg};color:${def.color}" title="${_esc(io.name)}">${_esc(io.name)}</span>`;
}

function _download(filename, text) {
  const a = document.createElement('a');
  a.href = 'data:text/plain;charset=utf-8,' + encodeURIComponent(text);
  a.download = filename;
  a.click();
}

// ── Sidebar workflow list ─────────────────────────────────────────────────────

async function _loadList() {
  const el = document.getElementById('gw-wf-list');
  if (!el) return;
  try {
    const { workflows } = await api.graphWorkflows.list(_project || '');
    if (!workflows.length) {
      el.innerHTML = '<div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">No flows yet</div>';
      return;
    }
    el.innerHTML = workflows.map(wf => `
      <div class="gw-wf-item ${_currentWf?.id === wf.id ? 'active' : ''}"
           onclick="window._gwOpenWf('${wf.id}')">
        ${_esc(wf.name)}
      </div>
    `).join('');
    window._gwOpenWf = _openWorkflow;
  } catch (e) {
    el.innerHTML = `<div style="padding:0.4rem 0.75rem;color:var(--red);font-size:0.75rem">${_esc(e.message)}</div>`;
  }
}

// ── Workflow open / create ────────────────────────────────────────────────────

async function _openWorkflow(id) {
  try {
    const wf = await api.graphWorkflows.get(id);
    _currentWf = wf;
    _showWorkflow(wf);
    _loadList(); // refresh active highlight
  } catch (e) {
    toast(`Failed to load flow: ${e.message}`, 'error');
  }
}

function _showWorkflow(wf) {
  const nameEl = document.getElementById('gw-wf-name');
  const nameWrap = document.getElementById('gw-wf-name-wrap');
  const runControls = document.getElementById('gw-run-controls');
  if (nameEl) nameEl.value = wf.name;
  if (nameWrap) nameWrap.style.display = '';
  if (runControls) runControls.style.display = 'flex';
  _renderPipeline(wf);
}

async function _newWorkflow() {
  const name = prompt('Flow name:', 'My Pipeline');
  if (!name) return;
  try {
    const wf = await api.graphWorkflows.create({ name, project: _project, max_iterations: 5 });
    _currentWf = wf;
    _showWorkflow(wf);
    _loadList();
  } catch (e) {
    toast(`Could not create flow: ${e.message}`, 'error');
  }
}

async function _saveWorkflowName(value) {
  if (!_currentWf || !value) return;
  try {
    await api.graphWorkflows.update(_currentWf.id, { name: value });
    _currentWf.name = value;
    _loadList();
  } catch (e) {
    toast(`Save failed: ${e.message}`, 'error');
  }
}

// ── Pipeline rendering ─────────────────────────────────────────────────────────

function _renderPipeline(wf) {
  const empty = document.getElementById('gw-empty-state');
  const pipeline = document.getElementById('gw-pipeline');
  if (!pipeline) return;

  if (empty) empty.style.display = 'none';
  pipeline.style.display = 'flex';

  const nodes = wf.nodes || [];
  const edges = wf.edges || [];

  // Build edge map source→target for connectors
  const edgeMap = new Map(); // source_node_id → [edge, ...]
  for (const e of edges) {
    if (!edgeMap.has(e.source_node_id)) edgeMap.set(e.source_node_id, []);
    edgeMap.get(e.source_node_id).push(e);
  }

  let html = '';
  nodes.forEach((n, i) => {
    html += _renderNodeCard(n);
    if (i < nodes.length - 1) {
      const outEdges = edgeMap.get(n.id) || [];
      const label = outEdges[0]?.label || '';
      html += `
        <div class="gw-connector">
          <div class="gw-conn-line">
            ${label ? `<div class="gw-conn-label">${_esc(label)}</div>` : ''}
          </div>
        </div>
      `;
    }
  });

  // Add button at end
  html += `
    <div style="display:flex;align-items:center;padding-left:${nodes.length ? '0.5rem' : '0'}">
      <button class="gw-add-btn" onclick="window._gwShowAddMenu(event)" title="Add node">+</button>
    </div>
  `;

  pipeline.innerHTML = html;

  // Attach click handlers
  pipeline.querySelectorAll('.gw-node-card').forEach(card => {
    const nodeId = card.dataset.nodeId;
    card.addEventListener('click', (e) => {
      if (e.target.closest('.gw-node-del')) return;
      _selectNode(nodeId);
    });
  });

  window._gwShowAddMenu = (evt) => {
    evt.stopPropagation();
    _showAddMenu(evt);
  };
  window._gwDeleteNode = (nodeId, evt) => {
    evt && evt.stopPropagation();
    _deleteNode(nodeId);
  };
}

function _renderNodeCard(node) {
  const preset = Object.values(ROLE_PRESETS).find(p => p.label === node.name) || ROLE_PRESETS.custom;
  const dotColor = preset.color;
  const badge = node.stateless ? '∅' : (preset.badge || 'DEV');
  const inputs = node.inputs || [];
  const outputs = node.outputs || [];
  const criteria = node.success_criteria || '';
  const isSelected = node.id === _selectedNodeId;

  return `
    <div class="gw-node-card ${isSelected ? 'selected' : ''}" data-node-id="${node.id}">
      <button class="gw-node-del" onclick="window._gwDeleteNode('${node.id}', event)">✕</button>
      <div class="gw-node-header">
        <div class="gw-node-dot" style="background:${dotColor}"></div>
        <div class="gw-node-name">${_esc(node.name)}</div>
        <div class="gw-node-badge">${_esc(badge)}</div>
      </div>
      <div class="gw-node-body">
        ${inputs.length ? `
          <div class="gw-node-io-section">
            <div class="gw-node-io-label">In</div>
            <div class="gw-node-io-tags">${inputs.map(_ioTag).join('')}</div>
          </div>
        ` : ''}
        ${outputs.length ? `
          <div class="gw-node-io-section">
            <div class="gw-node-io-label">Out</div>
            <div class="gw-node-io-tags">${outputs.map(_ioTag).join('')}</div>
          </div>
        ` : ''}
        ${!inputs.length && !outputs.length ? '<div style="color:var(--muted);font-size:0.72rem">No IO configured</div>' : ''}
      </div>
      <div class="gw-node-footer">
        <span>${_esc(criteria.slice(0, 24))}${criteria.length > 24 ? '…' : ''}</span>
        ${node.stateless ? '<span class="gw-stateless-badge">stateless</span>' : ''}
      </div>
      <div class="gw-node-status" id="status-${node.id}" style="display:none"></div>
    </div>
  `;
}

// ── Node selection + detail panel ─────────────────────────────────────────────

function _selectNode(nodeId) {
  _selectedNodeId = nodeId;
  const node = _currentWf?.nodes?.find(n => n.id === nodeId);
  if (!node) return;

  // Update selection border
  document.querySelectorAll('.gw-node-card').forEach(c => {
    c.classList.toggle('selected', c.dataset.nodeId === nodeId);
  });

  _renderDetailPanel(node);
  const detail = document.getElementById('gw-detail');
  if (detail) detail.classList.add('open');
}

function _closeDetail() {
  _selectedNodeId = null;
  document.querySelectorAll('.gw-node-card').forEach(c => c.classList.remove('selected'));
  const detail = document.getElementById('gw-detail');
  if (detail) detail.classList.remove('open');
}

function _renderDetailPanel(node) {
  const title = document.getElementById('gw-detail-title');
  const body = document.getElementById('gw-detail-body');
  if (!body) return;
  if (title) title.textContent = node.name;

  const ioTypeOptions = Object.keys(IO_TYPES).map(t => `<option value="${t}">${t}</option>`).join('');
  const providerOptions = ['claude','openai','deepseek','gemini','grok'].map(p =>
    `<option value="${p}" ${node.provider===p?'selected':''}>${p}</option>`
  ).join('');

  const inputsHtml = (node.inputs || []).map((io, i) => `
    <div class="gw-io-row" data-io-idx="${i}" data-io-type="input">
      <input value="${_esc(io.name)}" placeholder="name" data-io-name />
      <select data-io-type-sel>${ioTypeOptions.replace(`value="${io.type}"`,`value="${io.type}" selected`)}</select>
      <button onclick="this.closest('.gw-io-row').remove()">−</button>
    </div>
  `).join('');

  const outputsHtml = (node.outputs || []).map((io, i) => `
    <div class="gw-io-row" data-io-idx="${i}" data-io-type="output">
      <input value="${_esc(io.name)}" placeholder="name" data-io-name />
      <select data-io-type-sel>${ioTypeOptions.replace(`value="${io.type}"`,`value="${io.type}" selected`)}</select>
      <button onclick="this.closest('.gw-io-row').remove()">−</button>
    </div>
  `).join('');

  const criteriaOptions = ['','reviewer_approved','tests_pass','score >= 80','score >= 85','approved == true'].map(v =>
    `<option value="${v}" ${node.success_criteria===v?'selected':''}>${v||'—'}</option>`
  ).join('');

  body.innerHTML = `
    <div class="gw-field">
      <label>Name</label>
      <input id="dn-name" value="${_esc(node.name)}" />
    </div>
    <div class="gw-field">
      <label>Provider</label>
      <select id="dn-provider">${providerOptions}</select>
    </div>
    <div class="gw-field">
      <label>Model (optional)</label>
      <input id="dn-model" value="${_esc(node.model||'')}" placeholder="leave blank for default" />
    </div>
    <div class="gw-field">
      <label>System Prompt</label>
      <textarea id="dn-prompt" rows="5">${_esc(node.role_prompt||'')}</textarea>
    </div>
    <div class="gw-field">
      <label>Inputs</label>
      <div class="gw-io-editor" id="dn-inputs">${inputsHtml}</div>
      <button class="gw-add-io-btn" onclick="window._gwAddIO('input')">+ Add input</button>
    </div>
    <div class="gw-field">
      <label>Outputs</label>
      <div class="gw-io-editor" id="dn-outputs">${outputsHtml}</div>
      <button class="gw-add-io-btn" onclick="window._gwAddIO('output')">+ Add output</button>
    </div>
    <div class="gw-field">
      <label>Success Criteria</label>
      <select id="dn-criteria">${criteriaOptions}</select>
    </div>
    <div class="gw-field">
      <label>Retry Config (JSON)</label>
      <input id="dn-retry" value="${_esc(JSON.stringify(node.retry_config||{}))}" />
    </div>
    <div class="gw-field">
      <div class="gw-toggle-row">
        <label style="margin:0">Stateless (fresh context each run)</label>
        <input type="checkbox" id="dn-stateless" ${node.stateless?'checked':''} />
      </div>
    </div>
    <div class="gw-field">
      <div class="gw-toggle-row">
        <label style="margin:0">Require Approval</label>
        <input type="checkbox" id="dn-approval" ${node.require_approval?'checked':''} />
      </div>
    </div>
  `;

  window._gwAddIO = (type) => _addIORow(type);
}

function _addIORow(type) {
  const containerId = type === 'input' ? 'dn-inputs' : 'dn-outputs';
  const container = document.getElementById(containerId);
  if (!container) return;
  const ioTypeOptions = Object.keys(IO_TYPES).map(t => `<option value="${t}">${t}</option>`).join('');
  const row = document.createElement('div');
  row.className = 'gw-io-row';
  row.innerHTML = `
    <input value="" placeholder="name" data-io-name />
    <select data-io-type-sel>${ioTypeOptions}</select>
    <button onclick="this.closest('.gw-io-row').remove()">−</button>
  `;
  container.appendChild(row);
}

function _readIORows(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return [];
  return Array.from(container.querySelectorAll('.gw-io-row')).map(row => ({
    name: (row.querySelector('[data-io-name]')?.value || '').trim(),
    type: row.querySelector('[data-io-type-sel]')?.value || 'prompt',
  })).filter(io => io.name);
}

async function _saveNodeFromForm() {
  if (!_selectedNodeId || !_currentWf) return;
  let retryConfig = {};
  try { retryConfig = JSON.parse(document.getElementById('dn-retry')?.value || '{}'); } catch {}

  const data = {
    name:             document.getElementById('dn-name')?.value || '',
    provider:         document.getElementById('dn-provider')?.value || 'claude',
    model:            document.getElementById('dn-model')?.value || '',
    role_prompt:      document.getElementById('dn-prompt')?.value || '',
    success_criteria: document.getElementById('dn-criteria')?.value || '',
    stateless:        document.getElementById('dn-stateless')?.checked || false,
    require_approval: document.getElementById('dn-approval')?.checked || false,
    retry_config:     retryConfig,
    inputs:           _readIORows('dn-inputs'),
    outputs:          _readIORows('dn-outputs'),
  };

  try {
    await api.graphWorkflows.updateNode(_currentWf.id, _selectedNodeId, data);
    // Refresh workflow and re-render
    const wf = await api.graphWorkflows.get(_currentWf.id);
    _currentWf = wf;
    _renderPipeline(wf);
    // Re-select to keep detail open
    _selectNode(_selectedNodeId);
    toast('Node saved', 'success');
  } catch (e) {
    toast(`Save failed: ${e.message}`, 'error');
  }
}

// ── Add node ──────────────────────────────────────────────────────────────────

function _showAddMenu(evt) {
  // Simple: show a popup with preset choices
  const existing = document.getElementById('_gw-add-menu');
  if (existing) { existing.remove(); return; }

  const menu = document.createElement('div');
  menu.id = '_gw-add-menu';
  menu.style.cssText = `position:fixed;z-index:1000;background:var(--bg1);border:1px solid var(--border);
    border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,0.15);padding:0.25rem 0;min-width:140px;
    left:${evt.clientX}px;top:${evt.clientY}px`;

  Object.entries(ROLE_PRESETS).forEach(([key, p]) => {
    const item = document.createElement('div');
    item.style.cssText = 'padding:0.35rem 0.75rem;cursor:pointer;font-size:0.8rem;display:flex;align-items:center;gap:0.4rem';
    item.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:${p.color};display:inline-block"></span>${_esc(p.label)}`;
    item.onmouseenter = () => item.style.background = 'var(--hover)';
    item.onmouseleave = () => item.style.background = '';
    item.onclick = () => { menu.remove(); _addFromPreset(key); };
    menu.appendChild(item);
  });

  document.body.appendChild(menu);
  setTimeout(() => document.addEventListener('click', function h() {
    menu.remove(); document.removeEventListener('click', h);
  }), 0);
}

async function _addFromPreset(presetKey) {
  if (!_currentWf) {
    toast('Open or create a flow first', 'error');
    return;
  }
  const preset = ROLE_PRESETS[presetKey] || ROLE_PRESETS.custom;
  const nodeCount = (_currentWf.nodes || []).length;

  try {
    const node = await api.graphWorkflows.createNode(_currentWf.id, {
      name: preset.label,
      provider: 'claude',
      role_prompt: preset.role_prompt || '',
      stateless: preset.stateless,
      success_criteria: preset.success_criteria || '',
      inputs: preset.inputs || [],
      outputs: preset.outputs || [],
      position_x: 100 + nodeCount * 200,
      position_y: 150,
    });

    // Auto-connect to last node
    const existingNodes = _currentWf.nodes || [];
    if (existingNodes.length > 0) {
      const lastNode = existingNodes[existingNodes.length - 1];
      try {
        await api.graphWorkflows.createEdge(_currentWf.id, {
          source_node_id: lastNode.id,
          target_node_id: node.id,
        });
      } catch {}
    }

    const wf = await api.graphWorkflows.get(_currentWf.id);
    _currentWf = wf;
    _renderPipeline(wf);
  } catch (e) {
    toast(`Failed to add node: ${e.message}`, 'error');
  }
}

async function _deleteNode(nodeId) {
  if (!_currentWf) return;
  if (!confirm('Delete this node?')) return;
  try {
    await api.graphWorkflows.deleteNode(_currentWf.id, nodeId);
    if (_selectedNodeId === nodeId) _closeDetail();
    const wf = await api.graphWorkflows.get(_currentWf.id);
    _currentWf = wf;
    _renderPipeline(wf);
  } catch (e) {
    toast(`Delete failed: ${e.message}`, 'error');
  }
}

// ── Run ───────────────────────────────────────────────────────────────────────

async function _startRun() {
  if (!_currentWf) return;
  const userInput = prompt('Pipeline input (user prompt):', '');
  if (userInput === null) return;

  try {
    const { run_id } = await api.graphWorkflows.startRun(_currentWf.id, {
      user_input: userInput,
      project: _project,
    });
    _currentRunId = run_id;
    _openLog();
    _pollRun(run_id);
    document.getElementById('gw-cancel-btn').style.display = '';
  } catch (e) {
    toast(`Run failed: ${e.message}`, 'error');
  }
}

function _openLog() {
  const log = document.getElementById('gw-log');
  const toggle = document.getElementById('gw-log-toggle');
  if (log) { log.classList.add('open'); }
  if (toggle) toggle.textContent = '▼';
}

function _toggleLog() {
  const log = document.getElementById('gw-log');
  const toggle = document.getElementById('gw-log-toggle');
  if (!log) return;
  const open = log.querySelector('.gw-log-body').style.display !== 'none';
  log.querySelector('.gw-log-body').style.display = open ? 'none' : '';
  if (toggle) toggle.textContent = open ? '▶' : '▼';
}

function _pollRun(runId) {
  if (_pollInterval) clearInterval(_pollInterval);
  _pollInterval = setInterval(async () => {
    try {
      const run = await api.graphWorkflows.getRun(runId);
      _updateRunLog(run);
      if (['done','error','stopped','cancelled'].includes(run.status)) {
        clearInterval(_pollInterval); _pollInterval = null;
        document.getElementById('gw-cancel-btn').style.display = 'none';
      }
      if (run.status === 'waiting_approval') {
        clearInterval(_pollInterval); _pollInterval = null;
        _showApprovalPanel(run);
      }
    } catch {
      clearInterval(_pollInterval); _pollInterval = null;
    }
  }, 2000);
}

function _updateRunLog(run) {
  const statusEl = document.getElementById('gw-log-status');
  const bodyEl = document.getElementById('gw-log-body');
  if (statusEl) statusEl.textContent = run.status;

  // Update node status indicators
  (run.node_results || []).forEach(nr => {
    const statusDot = document.getElementById(`status-${nr.node_id}`);
    if (statusDot) {
      statusDot.style.display = '';
      statusDot.className = `gw-node-status ${nr.status}`;
    }
  });

  if (!bodyEl) return;
  const entries = (run.node_results || []).map(nr => `
    <div class="gw-log-entry">
      <span style="font-weight:600">${_esc(nr.node_name)}</span>
      <span style="color:var(--muted);margin-left:0.4rem">[${nr.status}]</span>
      <span style="margin-left:0.4rem;color:var(--muted);font-size:0.7rem">$${nr.cost_usd?.toFixed(4)||'0'}</span>
      ${nr.output ? `<div style="color:var(--muted);font-size:0.72rem;margin-top:0.15rem;white-space:pre-wrap;max-height:80px;overflow:auto">${_esc(nr.output.slice(0, 300))}</div>` : ''}
    </div>
  `).join('');
  bodyEl.innerHTML = entries || '<div style="color:var(--muted)">Waiting for results…</div>';
}

function _showApprovalPanel(run) {
  const wrap = document.getElementById('gw-approval-wrap');
  if (!wrap) return;
  const waiting = run.context?._waiting || {};
  wrap.style.display = '';
  wrap.innerHTML = `
    <div class="gw-approval">
      <h4>⏸ Approval Required: ${_esc(waiting.node_name || 'Node')}</h4>
      <div style="font-size:0.75rem;color:var(--muted)">${_esc(waiting.approval_msg || 'Review output and approve or reject.')}</div>
      ${waiting.output ? `<pre>${_esc(String(waiting.output).slice(0, 400))}</pre>` : ''}
      <div class="gw-approval-btns">
        <button class="btn btn-primary btn-sm" onclick="window._gwDecide(true, false)">✓ Approve</button>
        <button class="btn btn-ghost btn-sm" onclick="window._gwDecide(true, true)">↩ Retry</button>
        <button class="btn btn-ghost btn-sm" style="color:var(--red)" onclick="window._gwDecide(false, false)">✕ Stop</button>
      </div>
    </div>
  `;
  window._gwDecide = async (approved, retry) => {
    try {
      await api.graphWorkflows.decide(_currentRunId, { approved, retry });
      wrap.innerHTML = '';
      wrap.style.display = 'none';
      _pollRun(_currentRunId);
    } catch (e) {
      toast(`Decision failed: ${e.message}`, 'error');
    }
  };
}

async function _cancelRun() {
  if (!_currentRunId) return;
  try {
    await api.graphWorkflows.cancelRun(_currentRunId);
    if (_pollInterval) { clearInterval(_pollInterval); _pollInterval = null; }
    document.getElementById('gw-cancel-btn').style.display = 'none';
    const s = document.getElementById('gw-log-status');
    if (s) s.textContent = 'cancelled';
  } catch (e) {
    toast(`Cancel failed: ${e.message}`, 'error');
  }
}

// ── Export / Import ───────────────────────────────────────────────────────────

async function _exportYAML() {
  if (!_currentWf) return;
  try {
    const yaml = await api.graphWorkflows.exportYAML(_currentWf.id);
    const safe = (_currentWf.name || 'workflow').toLowerCase().replace(/[^a-z0-9_-]/g, '_');
    _download(`${safe}_graph.yaml`, yaml);
  } catch (e) {
    toast(`Export failed: ${e.message}`, 'error');
  }
}

async function _exportLangGraph() {
  if (!_currentWf) return;
  try {
    const py = await api.graphWorkflows.exportLangGraph(_currentWf.id);
    const safe = (_currentWf.name || 'workflow').toLowerCase().replace(/[^a-z0-9_-]/g, '_');
    _download(`${safe}_langgraph.py`, py);
  } catch (e) {
    toast(`Export failed: ${e.message}`, 'error');
  }
}

async function _importYAML(input) {
  const file = input.files?.[0];
  if (!file) return;
  const text = await file.text();
  try {
    const wf = await api.graphWorkflows.importYAML(_project, text);
    _currentWf = wf;
    _showWorkflow(wf);
    _loadList();
    toast('Workflow imported', 'success');
  } catch (e) {
    toast(`Import failed: ${e.message}`, 'error');
  }
  input.value = '';
}
