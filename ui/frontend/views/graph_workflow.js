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

// Role library: loaded from DB on tab open, used for sidebar + add-node menu
// _roles[] is populated in _loadList() alongside workflows

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

  // Guard: must have a project open
  if (!_project) {
    container.innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
                  height:100%;gap:1rem;color:var(--muted);text-align:center;padding:2rem">
        <div style="font-size:2.5rem">◈</div>
        <div style="font-size:1rem;font-weight:600;color:var(--fg)">No project open</div>
        <div style="font-size:0.82rem">Open a project first, then come back to Pipelines to create and run workflows.</div>
      </div>`;
    return;
  }

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
      .gw-node-card { width:210px; flex-shrink:0; border:2px solid var(--border);
        border-radius:8px; background:var(--bg1); cursor:pointer; transition:all 0.15s; }
      .gw-node-card:hover { border-color:var(--accent); box-shadow:0 2px 12px rgba(0,0,0,0.18); }
      .gw-node-card.selected { border-color:var(--accent); box-shadow:0 0 0 3px rgba(100,108,255,0.25); }
      .gw-node-header { display:flex; align-items:center; gap:0.35rem; padding:0.45rem 0.6rem;
        border-bottom:1px solid var(--border); }
      .gw-node-dot { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
      .gw-node-name { flex:1; font-size:0.78rem; font-weight:600; white-space:nowrap;
        overflow:hidden; text-overflow:ellipsis; }
      .gw-node-badge { font-size:0.57rem; padding:0.1rem 0.28rem; border-radius:3px;
        background:var(--border); color:var(--muted); flex-shrink:0; }
      .gw-node-del { background:rgba(232,93,117,0.12); border:1px solid rgba(232,93,117,0.3);
        border-radius:4px; color:#e85d75; cursor:pointer; font-size:0.68rem; font-weight:700;
        padding:1px 5px; line-height:1.4; flex-shrink:0; opacity:0; transition:opacity 0.15s; }
      .gw-node-card:hover .gw-node-del { opacity:1; }
      .gw-node-del:hover { background:rgba(232,93,117,0.25) !important; }
      .gw-node-body { padding:0.45rem 0.6rem; display:flex; flex-direction:column; gap:0.3rem; }
      .gw-node-row { display:flex; align-items:baseline; gap:0.3rem; }
      .gw-node-row-lbl { font-size:0.58rem; text-transform:uppercase; letter-spacing:0.04em;
        color:var(--muted); flex-shrink:0; width:28px; }
      .gw-node-row-val { font-size:0.7rem; color:var(--fg); overflow:hidden;
        text-overflow:ellipsis; white-space:nowrap; }
      .gw-node-row-val.muted { color:var(--muted); font-style:italic; }
      .gw-node-cfg-badges { display:flex; flex-wrap:wrap; gap:0.2rem; padding-top:0.1rem; }
      .gw-cfg-badge { font-size:0.58rem; padding:0.1rem 0.35rem; border-radius:10px;
        background:var(--border); color:var(--muted); }
      .gw-cfg-stateless { background:rgba(45,212,191,0.18); color:#2dd4bf; }
      .gw-cfg-warn      { background:rgba(245,166,35,0.18);  color:#f5a623; }
      .gw-cfg-approval  { background:rgba(155,126,248,0.18); color:#9b7ef8; }
      .gw-node-footer { padding:0.3rem 0.6rem 0.4rem; border-top:1px solid var(--border);
        font-size:0.63rem; color:var(--muted); display:flex; align-items:center; gap:0.4rem; }
      .gw-node-status { width:7px; height:7px; border-radius:50%; flex-shrink:0; display:none; }
      .gw-node-status.running  { background:#f5a623; animation:pulse 1s infinite; display:inline-block; }
      .gw-node-status.done     { background:#3ecf8e; display:inline-block; }
      .gw-node-status.error    { background:#e85d75; display:inline-block; }
      @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

      /* Inline modal */
      .gw-modal-overlay { position:fixed;inset:0;z-index:9000;
        background:rgba(0,0,0,0.72);backdrop-filter:blur(2px);
        display:flex;align-items:center;justify-content:center; }
      .gw-modal-box { background:#1e2130;border:1px solid rgba(255,255,255,0.14);border-radius:10px;
        padding:1.5rem;min-width:340px;max-width:500px;width:92%;
        box-shadow:0 24px 64px rgba(0,0,0,0.7); }
      .gw-modal-title { font-size:0.95rem;font-weight:700;margin-bottom:1rem;color:#fff; }
      .gw-modal-desc { font-size:0.8rem;color:rgba(255,255,255,0.5);margin:-0.5rem 0 0.9rem; }
      .gw-modal-field { margin-bottom:0.75rem; }
      .gw-modal-field label { display:block;font-size:0.7rem;color:rgba(255,255,255,0.5);
        margin-bottom:0.3rem;text-transform:uppercase;letter-spacing:0.05em;font-weight:600; }
      .gw-modal-field input, .gw-modal-field textarea {
        width:100%;box-sizing:border-box;padding:0.5rem 0.6rem;
        border:1px solid rgba(255,255,255,0.18);border-radius:6px;
        background:rgba(255,255,255,0.07);color:#fff;font-size:0.84rem; }
      .gw-modal-field input:focus, .gw-modal-field textarea:focus {
        outline:none;border-color:var(--accent);background:rgba(255,255,255,0.1); }
      .gw-modal-field textarea { resize:vertical; font-family:inherit; }
      .gw-modal-footer { display:flex;justify-content:flex-end;gap:0.5rem;margin-top:1rem;
        padding-top:0.75rem;border-top:1px solid rgba(255,255,255,0.08); }

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
      <button class="btn btn-primary btn-sm" id="gw-new-btn" onclick="window._gwNew()">+ New Pipeline</button>
      <button class="btn btn-ghost btn-sm" onclick="window._gwFromTemplate(event)" title="Create from template">From Template ▾</button>
      <div id="gw-wf-name-wrap" style="display:none">
        <input class="gw-wf-name" id="gw-wf-name" placeholder="Flow name" onblur="window._gwSaveName(this.value)" />
      </div>
      <div style="flex:1"></div>
      <div id="gw-run-controls" style="display:none;gap:0.4rem;align-items:center" class="flex">
        <button class="btn btn-ghost btn-sm" onclick="window._gwExportYAML()">Export YAML</button>
        <label class="btn btn-ghost btn-sm" style="cursor:pointer">
          Import YAML <input type="file" accept=".yaml,.yml" style="display:none" onchange="window._gwImportYAML(this)">
        </label>
        <button class="btn btn-primary btn-sm" onclick="window._gwStartRun()">▶ Run</button>
      </div>
    </div>

    <div class="gw-body2">
      <div class="gw-sidebar2">
        <div class="gw-sb-section">
          <div class="gw-sb-label">Saved Pipelines</div>
          <div id="gw-wf-list"><div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">Loading…</div></div>
        </div>
        <div class="gw-sb-section">
          <div class="gw-sb-label">Role Library</div>
          <div id="gw-role-library"><div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">Loading…</div></div>
        </div>
      </div>

      <div class="gw-main">
        <div class="gw-canvas-area">
          <div class="gw-pipeline-scroll" id="gw-pipeline-scroll">
            <div class="gw-empty" id="gw-empty-state">
              <div style="font-size:2rem">◈</div>
              <div style="font-weight:600">Select a pipeline or create a new one</div>
              <div style="font-size:0.78rem">Use <b>From Template</b> to instantly create a PM→Dev→Reviewer pipeline</div>
              <div style="font-size:0.78rem">or click a role in the sidebar to add it to the pipeline</div>
              <div style="margin-top:0.5rem;display:flex;gap:0.5rem">
                <button class="btn btn-primary btn-sm" onclick="window._gwNew()">+ New Pipeline</button>
                <button class="btn btn-ghost btn-sm" onclick="window._gwFromTemplate(event)">From Template ▾</button>
              </div>
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
  window._gwFromTemplate = (evt) => _showTemplateMenu(evt);
  window._gwStartRun    = () => _startRun();
  window._gwCancelRun   = () => _cancelRun();
  window._gwToggleLog   = _toggleLog;
  window._gwCloseDetail = _closeDetail;
  window._gwSaveNode    = _saveNodeFromForm;
  window._gwExportYAML  = _exportYAML;
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

/**
 * Inline modal that replaces native prompt()/confirm() which can be blocked in Electron.
 * @param {object} opts
 * @param {string}   opts.title
 * @param {Array}    opts.fields  — [{id, label, type?, placeholder?, value?, rows?}]
 * @param {string}   opts.confirmLabel
 * @param {boolean}  opts.danger  — red confirm button
 * @returns {Promise<object|null>} — resolves with {fieldId: value} map, or null if cancelled
 */
function _gwModal({ title, fields = [], confirmLabel = 'OK', danger = false }) {
  return new Promise(resolve => {
    const overlay = document.createElement('div');
    overlay.className = 'gw-modal-overlay';

    const box = document.createElement('div');
    box.className = 'gw-modal-box';

    let html = `<div class="gw-modal-title">${_esc(title)}</div>`;
    fields.forEach(f => {
      html += `<div class="gw-modal-field">`;
      if (f.label) html += `<label>${_esc(f.label)}</label>`;
      if (f.rows) {
        html += `<textarea id="_gm-${f.id}" rows="${f.rows}" placeholder="${_esc(f.placeholder || '')}">${_esc(f.value || '')}</textarea>`;
      } else {
        html += `<input id="_gm-${f.id}" type="${f.type || 'text'}" value="${_esc(f.value || '')}" placeholder="${_esc(f.placeholder || '')}" />`;
      }
      html += `</div>`;
    });
    html += `<div class="gw-modal-footer">
      <button id="_gm-cancel" class="btn btn-ghost btn-sm">Cancel</button>
      <button id="_gm-ok" class="btn ${danger ? 'btn-danger' : 'btn-primary'} btn-sm">${_esc(confirmLabel)}</button>
    </div>`;
    box.innerHTML = html;
    overlay.appendChild(box);
    document.body.appendChild(overlay);

    const firstInput = box.querySelector('input,textarea');
    if (firstInput) setTimeout(() => { firstInput.focus(); firstInput.select?.(); }, 0);

    const close = result => { overlay.remove(); resolve(result); };

    box.querySelector('#_gm-cancel').onclick = () => close(null);
    box.querySelector('#_gm-ok').onclick = () => {
      const result = {};
      fields.forEach(f => { result[f.id] = box.querySelector(`#_gm-${f.id}`)?.value ?? ''; });
      close(result);
    };
    box.addEventListener('keydown', e => {
      if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') { e.preventDefault(); box.querySelector('#_gm-ok').click(); }
      if (e.key === 'Escape') close(null);
    });
    overlay.onclick = e => { if (e.target === overlay) close(null); };
  });
}

// ── Sidebar workflow list ─────────────────────────────────────────────────────

async function _loadList() {
  const el = document.getElementById('gw-wf-list');
  if (!el) return;

  // Load workflows + roles in parallel
  const [wfResult, roleResult] = await Promise.allSettled([
    api.graphWorkflows.list(_project || ''),
    api.agentRoles.list(_project || '_global'),
  ]);

  // Populate role library sidebar
  if (roleResult.status === 'fulfilled') {
    _roles = roleResult.value.roles || [];
    _renderRoleLibrary();
  }

  if (wfResult.status === 'rejected') {
    el.innerHTML = `<div style="padding:0.4rem 0.75rem;color:var(--red);font-size:0.75rem">${_esc(wfResult.reason?.message || 'Error')}</div>`;
    return;
  }

  const { workflows } = wfResult.value;
  if (!workflows.length) {
    el.innerHTML = '<div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">No flows yet — use "From Template" to start</div>';
    return;
  }
  el.innerHTML = workflows.map(wf => {
    const isWiPipeline = wf.name === '_work_item_pipeline';
    const label = isWiPipeline ? '⚙ Work Item Pipeline' : _esc(wf.name);
    const note  = isWiPipeline
      ? '<div style="font-size:0.65rem;color:var(--accent)">Triggered from Planner ▶ Run</div>'
      : (wf.description ? `<div style="font-size:0.65rem;color:var(--muted)">${_esc(wf.description.slice(0,40))}</div>` : '');
    return `
      <div class="gw-wf-item ${_currentWf?.id === wf.id ? 'active' : ''}"
           onclick="window._gwOpenWf('${wf.id}')">
        <div style="font-size:0.8rem">${label}</div>
        ${note}
      </div>
    `;
  }).join('');
  window._gwOpenWf = _openWorkflow;
}

function _renderRoleLibrary() {
  const lib = document.getElementById('gw-role-library');
  if (!lib) return;
  if (!_roles.length) {
    lib.innerHTML = '<div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">No roles — create them in the Roles tab</div>';
    return;
  }
  // Role type → color mapping
  const TYPE_COLORS = {
    agent: '#3ecf8e', system_designer: '#9b7ef8', reviewer: '#2dd4bf',
  };
  lib.innerHTML = _roles.map(r => {
    const color = TYPE_COLORS[r.role_type || 'agent'] || '#6b7490';
    const badge = r.role_type === 'system_designer' ? 'SYS'
                : r.role_type === 'reviewer' ? 'REV' : 'AGT';
    return `
      <div class="gw-role-card" onclick="window._gwAddFromRole(${r.id})" title="${_esc(r.description||r.name)}">
        <div class="gw-role-dot" style="background:${color}"></div>
        <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(r.name)}</span>
        <span class="gw-role-badge">${badge}</span>
      </div>
    `;
  }).join('');
  window._gwAddFromRole = _addFromRole;
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
  if (!_project) { toast('Open a project first', 'error'); return; }
  const result = await _gwModal({
    title: 'New Pipeline',
    fields: [
      { id: 'name', label: 'Name', placeholder: 'My Pipeline', value: 'My Pipeline' },
      { id: 'desc', label: 'Description (optional)', placeholder: '' },
    ],
    confirmLabel: 'Create',
  });
  if (!result || !result.name.trim()) return;
  try {
    const wf = await api.graphWorkflows.create({
      name: result.name.trim(),
      description: result.desc.trim(),
      project: _project,
      max_iterations: 5,
    });
    _currentWf = wf;
    _showWorkflow(wf);
    _loadList();
  } catch (e) {
    toast(`Could not create pipeline: ${e.message}`, 'error');
  }
}

// ── Template menu ─────────────────────────────────────────────────────────────

const PIPELINE_TEMPLATES = [
  {
    key: 'pm_dev_reviewer',
    label: 'PM → Dev → Reviewer',
    description: 'Standard feature pipeline with approval gate',
    nodes: [
      { name: 'Product Manager', stateless: false,
        inputs: [{name:'prompt',type:'prompt'}], outputs: [{name:'spec.md',type:'md'}],
        role_prompt: 'You are a senior product manager. Produce a detailed spec document.' },
      { name: 'Developer', stateless: false,
        inputs: [{name:'spec.md',type:'md'}], outputs: [{name:'code',type:'code'}],
        role_prompt: 'You are a senior software engineer. Implement the spec.' },
      { name: 'Reviewer', stateless: true,
        inputs: [{name:'code',type:'code'},{name:'spec.md',type:'md'}],
        outputs: [{name:'feedback.md',type:'feedback'},{name:'approved',type:'score'}],
        role_prompt: 'You are a code reviewer. Review with fresh eyes.' },
    ],
    edges: [{ from: 0, to: 1 }, { from: 1, to: 2 }],
  },
  {
    key: 'pm_arch_dev_reviewer',
    label: 'PM → Architect → Dev → Reviewer',
    description: 'Full 4-agent work item pipeline (same as Planner ▶ Run)',
    nodes: [
      { name: 'Product Manager', stateless: false,
        inputs: [{name:'prompt',type:'prompt'}], outputs: [{name:'spec.md',type:'md'}],
        role_prompt: 'You are a senior product manager. Produce a detailed spec document.' },
      { name: 'Architect', stateless: false,
        inputs: [{name:'spec.md',type:'md'}], outputs: [{name:'arch.md',type:'md'}],
        role_prompt: 'You are a Senior Architect. Write a technical implementation plan.' },
      { name: 'Developer', stateless: false,
        inputs: [{name:'arch.md',type:'md'}], outputs: [{name:'code',type:'code'}],
        role_prompt: 'You are a senior software engineer. Implement the architecture plan.' },
      { name: 'Reviewer', stateless: true,
        inputs: [{name:'code',type:'code'}], outputs: [{name:'score',type:'score'}],
        role_prompt: 'You are a code reviewer. Score the code 1-10.' },
    ],
    edges: [{ from: 0, to: 1 }, { from: 1, to: 2 }, { from: 2, to: 3 }],
  },
  {
    key: 'dev_tester',
    label: 'Dev → Tester',
    description: 'Simple code generation + test scoring',
    nodes: [
      { name: 'Developer', stateless: false,
        inputs: [{name:'prompt',type:'prompt'}], outputs: [{name:'code',type:'code'}],
        role_prompt: 'You are a senior software engineer. Write the code.' },
      { name: 'Tester', stateless: false,
        inputs: [{name:'code',type:'code'}], outputs: [{name:'score',type:'score'}],
        role_prompt: 'You are a QA engineer. Test the code and provide a score out of 100.' },
    ],
    edges: [{ from: 0, to: 1 }],
  },
];

function _showTemplateMenu(evt) {
  const existing = document.getElementById('_gw-tmpl-menu');
  if (existing) { existing.remove(); return; }

  const btn = evt?.currentTarget || evt?.target;
  const rect = btn?.getBoundingClientRect?.() || { left: 100, bottom: 50 };

  const menu = document.createElement('div');
  menu.id = '_gw-tmpl-menu';
  menu.style.cssText = `position:fixed;z-index:2000;background:var(--bg1);border:1px solid var(--border);
    border-radius:6px;box-shadow:0 4px 20px rgba(0,0,0,0.18);padding:0.4rem 0;min-width:260px;
    left:${rect.left}px;top:${(rect.bottom || 50) + 4}px`;

  PIPELINE_TEMPLATES.forEach(tmpl => {
    const item = document.createElement('div');
    item.style.cssText = 'padding:0.5rem 0.85rem;cursor:pointer;';
    item.innerHTML = `
      <div style="font-size:0.82rem;font-weight:600">${_esc(tmpl.label)}</div>
      <div style="font-size:0.7rem;color:var(--muted)">${_esc(tmpl.description)}</div>
    `;
    item.onmouseenter = () => item.style.background = 'var(--hover)';
    item.onmouseleave = () => item.style.background = '';
    item.onclick = () => { menu.remove(); _createFromTemplate(tmpl); };
    menu.appendChild(item);
  });

  document.body.appendChild(menu);
  setTimeout(() => document.addEventListener('click', function h() {
    menu.remove(); document.removeEventListener('click', h);
  }), 0);
}

async function _createFromTemplate(tmpl) {
  if (!_project) { toast('Open a project first', 'error'); return; }
  try {
    // 1. Create workflow
    const wf = await api.graphWorkflows.create({
      name: tmpl.label,
      description: tmpl.description,
      project: _project,
      max_iterations: 5,
    });

    // 2. Create nodes and track IDs
    const nodeIds = [];
    for (let i = 0; i < tmpl.nodes.length; i++) {
      const n = tmpl.nodes[i];
      const created = await api.graphWorkflows.createNode(wf.id, {
        name:             n.name,
        provider:         'claude',
        role_prompt:      n.role_prompt || '',
        stateless:        n.stateless || false,
        success_criteria: n.success_criteria || '',
        inputs:           n.inputs  || [],
        outputs:          n.outputs || [],
        order_index:      i,
        max_retry:        3,
        position_x:       100 + i * 220,
        position_y:       150,
      });
      nodeIds.push(created.id);
    }

    // 3. Create edges
    for (const e of tmpl.edges) {
      if (nodeIds[e.from] && nodeIds[e.to]) {
        await api.graphWorkflows.createEdge(wf.id, {
          source_node_id: nodeIds[e.from],
          target_node_id: nodeIds[e.to],
          condition:       e.condition || null,
          label:           e.label    || '',
        });
      }
    }

    // 4. Open it
    const full = await api.graphWorkflows.get(wf.id);
    _currentWf = full;
    _showWorkflow(full);
    _loadList();
    toast(`Created "${tmpl.label}"`, 'success');
  } catch (e) {
    toast(`Template failed: ${e.message}`, 'error');
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
  const TYPE_COLORS = { agent: '#3ecf8e', system_designer: '#9b7ef8', reviewer: '#2dd4bf' };
  const matchedRole = _roles.find(r => r.id === node.role_id || r.name === node.name);
  const roleType = matchedRole?.role_type || 'agent';
  const dotColor = TYPE_COLORS[roleType] || '#6b7490';
  const badge = roleType === 'system_designer' ? 'SYS' : roleType === 'reviewer' ? 'REV' : 'AGT';
  const isSelected = node.id === _selectedNodeId;

  // Provider + model row
  const modelLabel = node.model ? `${node.provider} / ${node.model}` : (node.provider || 'claude');

  // IO rows (names only — no type colour needed on card)
  const inputs  = (node.inputs  || []).map(io => _esc(io.name)).filter(Boolean);
  const outputs = (node.outputs || []).map(io => _esc(io.name)).filter(Boolean);

  // Config badges
  const cfgBadges = [];
  if (node.stateless)        cfgBadges.push(`<span class="gw-cfg-badge gw-cfg-stateless" title="Runs with fresh context each time">stateless</span>`);
  if ((node.max_retry ?? 3) !== 3) cfgBadges.push(`<span class="gw-cfg-badge" title="Max retry attempts">retry:${node.max_retry}</span>`);
  if (node.continue_on_fail) cfgBadges.push(`<span class="gw-cfg-badge gw-cfg-warn" title="Pipeline continues even if this node fails">cont.fail</span>`);
  if (node.require_approval) cfgBadges.push(`<span class="gw-cfg-badge gw-cfg-approval" title="Requires human approval before next node">approval</span>`);

  const criteria = node.success_criteria || '';

  return `
    <div class="gw-node-card ${isSelected ? 'selected' : ''}" data-node-id="${node.id}">
      <div class="gw-node-header">
        <div class="gw-node-dot" style="background:${dotColor}"></div>
        <div class="gw-node-name">${_esc(node.name)}</div>
        <div class="gw-node-badge">${_esc(badge)}</div>
        <button class="gw-node-del" onclick="window._gwDeleteNode('${node.id}', event)" title="Delete node">✕</button>
      </div>
      <div class="gw-node-body">
        <div class="gw-node-row">
          <span class="gw-node-row-lbl">model</span>
          <span class="gw-node-row-val">${_esc(modelLabel)}</span>
        </div>
        ${inputs.length ? `
        <div class="gw-node-row">
          <span class="gw-node-row-lbl">in</span>
          <span class="gw-node-row-val" title="${inputs.join(', ')}">${inputs.join(', ')}</span>
        </div>` : ''}
        ${outputs.length ? `
        <div class="gw-node-row">
          <span class="gw-node-row-lbl">out</span>
          <span class="gw-node-row-val" title="${outputs.join(', ')}">${outputs.join(', ')}</span>
        </div>` : ''}
        <div class="gw-node-row">
          <span class="gw-node-row-lbl">retry</span>
          <span class="gw-node-row-val">${node.max_retry ?? 3}</span>
        </div>
        ${cfgBadges.length ? `<div class="gw-node-cfg-badges">${cfgBadges.join('')}</div>` : ''}
      </div>
      ${criteria ? `
      <div class="gw-node-footer">
        <div class="gw-node-status" id="status-${node.id}"></div>
        <span title="Success criteria">${_esc(criteria.slice(0, 30))}${criteria.length > 30 ? '…' : ''}</span>
      </div>` : `
      <div class="gw-node-footer" style="padding-top:0.2rem;padding-bottom:0.25rem">
        <div class="gw-node-status" id="status-${node.id}"></div>
      </div>`}
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
      <label>Max Retry</label>
      <input type="number" id="dn-max-retry" value="${node.max_retry ?? 3}" min="1" max="10" />
    </div>
    <div class="gw-field">
      <div class="gw-toggle-row">
        <label style="margin:0">Stateless (fresh context each run)</label>
        <input type="checkbox" id="dn-stateless" ${node.stateless?'checked':''} />
      </div>
    </div>
    <div class="gw-field">
      <div class="gw-toggle-row">
        <label style="margin:0">Continue on Fail</label>
        <input type="checkbox" id="dn-continue-fail" ${node.continue_on_fail?'checked':''} />
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
    continue_on_fail: document.getElementById('dn-continue-fail')?.checked || false,
    require_approval: document.getElementById('dn-approval')?.checked || false,
    max_retry:        parseInt(document.getElementById('dn-max-retry')?.value || '3', 10),
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
  const existing = document.getElementById('_gw-add-menu');
  if (existing) { existing.remove(); return; }

  const menu = document.createElement('div');
  menu.id = '_gw-add-menu';
  menu.style.cssText = `position:fixed;z-index:1000;background:var(--bg1);border:1px solid var(--border);
    border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,0.15);padding:0.25rem 0;min-width:180px;
    left:${evt.clientX}px;top:${evt.clientY}px`;

  const TYPE_COLORS = { agent: '#3ecf8e', system_designer: '#9b7ef8', reviewer: '#2dd4bf' };
  const rolesToShow = _roles.length ? _roles : [{ id: null, name: 'Custom Node', role_type: 'agent' }];

  rolesToShow.forEach(r => {
    const color = TYPE_COLORS[r.role_type || 'agent'] || '#6b7490';
    const item = document.createElement('div');
    item.style.cssText = 'padding:0.35rem 0.75rem;cursor:pointer;font-size:0.8rem;display:flex;align-items:center;gap:0.4rem';
    item.innerHTML = `<span style="width:8px;height:8px;border-radius:50%;background:${color};display:inline-block;flex-shrink:0"></span>${_esc(r.name)}`;
    item.onmouseenter = () => item.style.background = 'var(--hover)';
    item.onmouseleave = () => item.style.background = '';
    item.onclick = () => { menu.remove(); r.id ? _addFromRole(r.id) : _addBlankNode(); };
    menu.appendChild(item);
  });

  document.body.appendChild(menu);
  setTimeout(() => document.addEventListener('click', function h() {
    menu.remove(); document.removeEventListener('click', h);
  }), 0);
}

async function _addFromRole(roleId) {
  if (!_currentWf) { toast('Open or create a flow first', 'error'); return; }
  const role = _roles.find(r => r.id === roleId);
  if (!role) return;
  const nodeCount = (_currentWf.nodes || []).length;
  try {
    const node = await api.graphWorkflows.createNode(_currentWf.id, {
      name:             role.name,
      provider:         role.provider || 'claude',
      model:            role.model || '',
      role_id:          role.id,
      stateless:        false,
      inputs:           role.inputs  || [],
      outputs:          role.outputs || [],
      order_index:      nodeCount,
      position_x:       100 + nodeCount * 200,
      position_y:       150,
    });
    await _autoConnectNode(node);
    const wf = await api.graphWorkflows.get(_currentWf.id);
    _currentWf = wf;
    _renderPipeline(wf);
  } catch (e) {
    toast(`Failed to add node: ${e.message}`, 'error');
  }
}

async function _addBlankNode() {
  if (!_currentWf) { toast('Open or create a flow first', 'error'); return; }
  const nodeCount = (_currentWf.nodes || []).length;
  try {
    const node = await api.graphWorkflows.createNode(_currentWf.id, {
      name: 'New Node', provider: 'claude', order_index: nodeCount,
      position_x: 100 + nodeCount * 200, position_y: 150,
    });
    await _autoConnectNode(node);
    const wf = await api.graphWorkflows.get(_currentWf.id);
    _currentWf = wf;
    _renderPipeline(wf);
  } catch (e) {
    toast(`Failed to add node: ${e.message}`, 'error');
  }
}

async function _addFromPreset(presetKey) {
  // Legacy — just add a blank node now that we use live DB roles
  return _addBlankNode();
}

async function _autoConnectNode(node) {
  const existingNodes = _currentWf.nodes || [];
  if (existingNodes.length > 0) {
    const lastNode = existingNodes[existingNodes.length - 1];
    try {
      await api.graphWorkflows.createEdge(_currentWf.id, {
        source_node_id: lastNode.id,
        target_node_id: node.id,
      });
    } catch (_) {}
  }
}


async function _deleteNode(nodeId) {
  if (!_currentWf) return;
  const node = _currentWf.nodes?.find(n => n.id === nodeId);
  const result = await _gwModal({
    title: `Delete "${node?.name || 'node'}"?`,
    fields: [],
    confirmLabel: 'Delete',
    danger: true,
  });
  if (!result) return;
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
  const result = await _gwModal({
    title: `Run: ${_currentWf.name}`,
    fields: [{ id: 'input', label: 'Task / Prompt', placeholder: 'Describe the task for this pipeline…', rows: 4 }],
    confirmLabel: '▶ Run',
  });
  if (!result || !result.input.trim()) return;
  const userInput = result.input.trim();

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
  if (statusEl) {
    const statusColors = { done: '#3ecf8e', error: '#e85d75', running: '#f5a623', stopped: '#888' };
    const c = statusColors[run.status] || 'var(--muted)';
    statusEl.innerHTML = `<span style="color:${c}">${run.status}</span>`;
    if (run.total_cost_usd > 0) {
      statusEl.innerHTML += ` <span style="color:var(--muted);font-size:0.7rem">$${Number(run.total_cost_usd).toFixed(4)}</span>`;
    }
  }

  // Update node status indicators on cards
  (run.node_results || []).forEach(nr => {
    const statusDot = document.getElementById(`status-${nr.node_id}`);
    if (statusDot) {
      statusDot.style.display = '';
      statusDot.className = `gw-node-status ${nr.status}`;
    }
  });

  if (!bodyEl) return;

  // Show "where results go" info when done
  let doneMsg = '';
  if (run.status === 'done') {
    doneMsg = `
      <div style="background:rgba(62,207,142,0.1);border:1px solid rgba(62,207,142,0.3);border-radius:6px;
                  padding:0.6rem 0.75rem;margin-bottom:0.5rem;font-size:0.76rem">
        <b>✓ Pipeline complete.</b> Results are saved in:
        <ul style="margin:0.25rem 0 0;padding-left:1.2rem">
          <li><b>Run context</b> — poll again or check the run log above</li>
          <li><b>Documents tab</b> — <code>workspace/${_esc(_project)}/documents/</code></li>
          ${_currentWf?.name === '_work_item_pipeline'
            ? '<li><b>Planner tab</b> — open the work item to see updated Acceptance Criteria &amp; Implementation Plan</li>'
            : ''}
        </ul>
      </div>`;
  }

  const entries = (run.node_results || []).map(nr => {
    const statusColor = nr.status === 'done' ? '#3ecf8e' : nr.status === 'error' ? '#e85d75' : '#f5a623';
    return `
      <div class="gw-log-entry">
        <div style="display:flex;align-items:center;gap:0.5rem">
          <span style="font-weight:600;font-size:0.8rem">${_esc(nr.node_name)}</span>
          <span style="color:${statusColor};font-size:0.72rem">${nr.status}</span>
          <span style="color:var(--muted);font-size:0.7rem;margin-left:auto">$${nr.cost_usd?.toFixed(4)||'0.0000'}</span>
        </div>
        ${nr.output ? `<div style="color:var(--muted);font-size:0.72rem;margin-top:0.2rem;
          white-space:pre-wrap;max-height:80px;overflow:auto;background:var(--bg2);
          border-radius:4px;padding:0.3rem 0.4rem">${_esc(nr.output.slice(0, 400))}</div>` : ''}
      </div>
    `;
  }).join('');

  bodyEl.innerHTML = doneMsg + (entries || '<div style="color:var(--muted);padding:0.25rem 0">Waiting for results…</div>');
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
