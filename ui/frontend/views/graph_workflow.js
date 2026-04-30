/**
 * graph_workflow.js — Horizontal CSS pipeline designer (v2).
 *
 * Renders a pure-CSS card-based pipeline builder with a left sidebar (saved workflows,
 * role library, IO type legend), a scrollable horizontal canvas of connected agent nodes,
 * a slide-in node config panel, and a collapsible live run log with approval-gate overlay.
 * Rendered via: renderGraphWorkflow() called from main.js navigateTo().
 */

import { state } from '../stores/state.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { renderMd } from '../utils/markdown.js';

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
let _runStartTime = null;       // Date — when current run started
let _timerInterval = null;      // setInterval handle for live clock
let _approvalChatHistory = [];  // [{role, content}] — chat within current approval gate

// Cache for sidebar data — loaded once per project, refreshed on mutation
let _listCache = null;  // { workflows, roles, recentRuns, project } or null

// Run log accumulator — live text log entries for current run
let _runLog = [];  // [{node, msg, ts}]
let _prevNodeStatuses = {};  // {node_name: status} — track transitions for log entries

// Approval panel state
let _approvalBaselineOutput = '';   // original output when approval panel opened
let _approvalEditMode = false;      // whether edit textarea is active
let _currentApprovalNodeName = null; // node name currently shown in approval panel

// ── Entry point ───────────────────────────────────────────────────────────────

export function renderGraphWorkflow(container) {
  container.className = 'view active gw-view';
  const prevProject = _project;
  _project = state.currentProject?.name || '';
  if (prevProject !== _project) _listCache = null;  // invalidate on project switch

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
      .gw-pipeline-scroll { flex-shrink:0; overflow-x:auto; overflow-y:hidden;
        padding:1.5rem 2rem; max-height:260px; min-height:120px; }
      .gw-pipeline { display:flex; align-items:flex-start; gap:0; min-height:160px; }

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

      /* Run progress panel (directly below nodes, fills remaining canvas space) */
      .gw-run-panel { border-top:1px solid var(--border); display:none;
        flex-direction:column; overflow:hidden; flex:1; min-height:0; }
      .gw-run-panel.open { display:flex; }
      .gw-rp-hdr { padding:0.45rem 0.75rem; border-bottom:1px solid var(--border); flex-shrink:0;
        display:flex; align-items:center; gap:0.75rem; }
      .gw-rp-wf-name { font-size:0.78rem; font-weight:700; white-space:nowrap; overflow:hidden;
        text-overflow:ellipsis; max-width:180px; }
      .gw-rp-meta { display:flex; align-items:center; gap:0.5rem;
        font-size:0.72rem; color:var(--muted); }
      .gw-rp-status-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
      .gw-rp-status-dot.running { background:#f5a623; animation:pulse 1s infinite; }
      .gw-rp-status-dot.done    { background:#3ecf8e; }
      .gw-rp-status-dot.error   { background:#e85d75; }
      .gw-rp-status-dot.stopped, .gw-rp-status-dot.cancelled { background:var(--muted); }
      .gw-rp-actions { display:flex; gap:0.4rem; align-items:center; }
      /* Timeline: horizontal cards in bottom panel */
      .gw-rp-timeline { padding:0.5rem 0.75rem; display:flex; flex-direction:row;
        gap:0.5rem; align-items:flex-start; flex-wrap:nowrap; overflow-x:auto; }
      .gw-rp-step { min-width:160px; max-width:220px; flex-shrink:0; border-radius:6px;
        border:2px solid var(--border); padding:0.45rem 0.55rem; transition:background 0.1s; }
      .gw-rp-step.pending  { border-color:var(--border); opacity:0.5; }
      .gw-rp-step.running  { border-color:#f5a623; background:rgba(245,166,35,0.06); }
      .gw-rp-step.done     { border-color:#3ecf8e; }
      .gw-rp-step.error    { border-color:#e85d75; background:rgba(232,93,117,0.06); }
      .gw-rp-step.skipped  { border-color:var(--muted); opacity:0.5; }
      .gw-rp-step-hdr { display:flex; align-items:center; gap:0.35rem; }
      .gw-rp-step-dot { width:7px; height:7px; border-radius:50%; flex-shrink:0;
        background:var(--border); }
      .gw-rp-step.pending .gw-rp-step-dot  { background:var(--border); }
      .gw-rp-step.running .gw-rp-step-dot  { background:#f5a623; animation:pulse 1s infinite; }
      .gw-rp-step.done    .gw-rp-step-dot  { background:#3ecf8e; }
      .gw-rp-step.error   .gw-rp-step-dot  { background:#e85d75; }
      .gw-rp-step-name { font-size:0.75rem; font-weight:600; flex:1;
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .gw-rp-step-meta { font-size:0.63rem; color:var(--muted); margin-top:0.2rem; }
      .gw-rp-step-out { font-size:0.65rem; color:var(--muted); margin-top:0.3rem;
        line-height:1.4; max-height:52px; overflow:hidden;
        background:var(--bg2); border-radius:4px; padding:0.2rem 0.35rem;
        white-space:pre-wrap; word-break:break-word; }
      .gw-rp-deliverables { flex-shrink:0; overflow-y:auto; padding:0.5rem 0.6rem; }
      .gw-rp-del-title { font-size:0.68rem; font-weight:700; text-transform:uppercase;
        letter-spacing:0.05em; color:var(--muted); margin-bottom:0.4rem; }
      .gw-rp-del-file { font-size:0.72rem; padding:0.2rem 0; display:flex;
        align-items:center; gap:0.35rem; color:var(--fg); cursor:default; }
      .gw-rp-del-file span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
      .gw-rp-history { border-top:1px solid var(--border); }
      .gw-rp-hist-item { display:flex; align-items:center; gap:0.4rem;
        padding:0.3rem 0.75rem; font-size:0.75rem; cursor:pointer; }
      .gw-rp-hist-item:hover { background:var(--hover); }

      /* Recent runs sidebar section */
      .gw-run-row { display:flex; align-items:center; gap:0.4rem; padding:0.3rem 0.75rem;
        cursor:pointer; font-size:0.75rem; }
      .gw-run-row:hover { background:var(--hover); }
      .gw-run-dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; }

      /* Inline pipeline panels (above/below canvas) */
      .gw-props-bar { background:var(--bg2); flex-shrink:0; border-bottom:1px solid var(--border); }
      .gw-exec-bar  { flex-shrink:0; display:flex; flex-direction:column; overflow:hidden; max-height:50%; }
      .gw-hist-bar  { flex-shrink:0; display:flex; flex-direction:column; overflow:hidden; max-height:35%;
                      border-top:1px solid var(--border); }
      .gw-canvas-area { flex:1; min-height:0; overflow:hidden; display:flex; flex-direction:column; }
    </style>

    <div class="gw-toolbar2">
      <button class="btn btn-primary btn-sm" id="gw-new-btn" onclick="window._gwNew()">+ New Pipeline</button>
      <button class="btn btn-ghost btn-sm" onclick="window._gwFromTemplate(event)" title="Create from template">From Template ▾</button>
      <button class="btn btn-ghost btn-sm" id="gw-react-btn" onclick="window._gwOpenReActRunner()" title="Run a YAML-defined ReAct pipeline (PM → Architect → Developer → Reviewer)">▶ ReAct Run</button>
      <span id="gw-props-btn" style="display:none"></span>
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
        <div class="gw-sb-section">
          <div class="gw-sb-label">Recent Runs</div>
          <div id="gw-recent-runs"><div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">Loading…</div></div>
        </div>
      </div>

      <div class="gw-main">
        <div id="gw-props-bar" class="gw-props-bar" style="display:none"></div>
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
          <div id="gw-exec-bar" class="gw-exec-bar" style="display:none"></div>
          <!-- Run progress panel (directly below nodes, fills remaining canvas space) -->
          <div class="gw-run-panel" id="gw-run-panel">
            <div class="gw-rp-hdr">
              <div style="display:flex;align-items:center;gap:0.75rem;flex:1;min-width:0">
                <div class="gw-rp-wf-name" id="gw-rp-wf-name">Pipeline</div>
                <div class="gw-rp-meta" style="flex-wrap:nowrap">
                  <div class="gw-rp-status-dot running" id="gw-rp-dot"></div>
                  <span id="gw-rp-status">running</span>
                  <span id="gw-rp-timer" style="font-variant-numeric:tabular-nums">0s</span>
                  <span id="gw-rp-nodes">0/0</span>
                  <span id="gw-rp-cost">$0.0000</span>
                </div>
              </div>
              <div class="gw-rp-actions" style="margin-top:0;flex-shrink:0">
                <button class="btn btn-ghost btn-sm" id="gw-rp-stop"
                  style="color:var(--red);font-size:0.72rem" onclick="window._gwCancelRun()">■ Stop</button>
                <button class="btn btn-ghost btn-sm" style="font-size:0.72rem"
                  onclick="window._gwCloseRunPanel()">✕ Close</button>
              </div>
            </div>
            <!-- Approval panel shown here when waiting -->
            <div id="gw-approval-wrap" style="display:none;padding:0.5rem 0.75rem 0;flex-shrink:0"></div>
            <div style="flex:1;overflow-y:auto;display:flex;flex-direction:column;">
              <!-- Status cards row -->
              <div class="gw-rp-timeline" id="gw-rp-timeline"></div>
              <!-- Full-width text log -->
              <div id="gw-run-log" style="flex:1;overflow-y:auto;padding:0.5rem 0.75rem;
                   font-family:var(--font-mono,monospace);font-size:0.72rem;line-height:1.6;
                   border-top:1px solid var(--border);min-height:80px"></div>
              <!-- Deliverables (shown on completion) -->
              <div class="gw-rp-deliverables" id="gw-rp-deliverables" style="display:none;border-top:1px solid var(--border)"></div>
            </div>
            <!-- Legacy log body (hidden, kept for backward compat) -->
            <div id="gw-log" style="display:none">
              <div class="gw-log-body" id="gw-log-body"></div>
            </div>
          </div>
        </div>
        <div id="gw-hist-bar" class="gw-hist-bar" style="display:none"></div>
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
  window._gwNew          = () => _newWorkflow();
  window._gwSaveName     = (v) => _saveWorkflowName(v);
  window._gwAddPreset    = (key) => _addFromPreset(key);
  window._gwFromTemplate = (evt) => _showTemplateMenu(evt);
  window._gwStartRun     = () => _startRun();
  window._gwCancelRun    = () => _cancelRun();
  window._gwToggleLog    = _toggleLog;
  window._gwCloseDetail  = _closeDetail;
  window._gwSaveNode     = _saveNodeFromForm;
  window._gwExportYAML   = _exportYAML;
  window._gwImportYAML   = _importYAML;
  window._gwCloseRunPanel = _closeRunPanel;
  window._gwOpenRun      = (runId) => _openRunById(runId);
  window._gwOpenReActRunner = () => openReActRunner();
  window._gwShowProps       = () => _showPipelineProps();

  _loadList().then(() => {
    // If navigation came from a pipeline trigger (entities.js), auto-open that run
    if (window._pendingRunOpen) {
      const rid = window._pendingRunOpen;
      window._pendingRunOpen = null;
      _openRunById(rid);
    }
  });
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

  // Render from cache immediately if available for this project
  if (_listCache && _listCache.project === _project) {
    _applyListData(_listCache.workflows, _listCache.roles, _listCache.recentRuns);
    // Refresh in background (fire and forget)
    _refreshListInBackground();
    return;
  }

  // No cache — show loading and fetch
  el.innerHTML = '<div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">Loading…</div>';
  await _refreshListInBackground();
}

async function _refreshListInBackground() {
  try {
    const [wfResult, roleResult, runsResult] = await Promise.allSettled([
      api.graphWorkflows.list(_project || ''),
      api.agentRoles.list(_project || '_global'),
      api.graphWorkflows.recentRuns(_project || '', 15),
    ]);

    const workflows = wfResult.status === 'fulfilled' ? (wfResult.value.workflows || []) : null;
    const roles = roleResult.status === 'fulfilled' ? (roleResult.value.roles || []) : null;
    const recentRuns = runsResult.status === 'fulfilled' ? (runsResult.value.runs || []) : [];

    if (workflows !== null) {
      _listCache = { project: _project, workflows, roles: roles || _roles, recentRuns };
      _applyListData(workflows, roles, recentRuns);
    }
  } catch (_) {}
}

function _applyListData(workflows, roles, recentRuns) {
  const el = document.getElementById('gw-wf-list');
  if (!el) return;

  if (roles) {
    _roles = roles;
    _renderRoleLibrary();
  }
  _renderRecentRuns(recentRuns);

  if (!workflows || !workflows.length) {
    el.innerHTML = '<div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">No flows yet — use "From Template" to start</div>';
    return;
  }
  el.innerHTML = workflows.map(wf => {
    const isWiPipeline = wf.name === '_work_item_pipeline';
    const label = isWiPipeline ? '⚙ Work Item Pipeline' : _esc(wf.name);
    const note = wf.description
      ? `<div style="font-size:0.65rem;color:var(--muted)">${_esc((isWiPipeline ? 'Auto-pipeline from Planner' : wf.description).slice(0,40))}</div>`
      : '';
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
  const pipelineRoles = _roles;
  if (!pipelineRoles.length) {
    lib.innerHTML = '<div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">No roles — create them in the Roles tab</div>';
    return;
  }
  // Role type → color mapping
  const TYPE_COLORS = {
    agent: '#3ecf8e', system_designer: '#9b7ef8', reviewer: '#2dd4bf',
  };
  lib.innerHTML = pipelineRoles.map(r => {
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

// ── Recent runs sidebar ───────────────────────────────────────────────────────

function _renderRecentRuns(runs) {
  const el = document.getElementById('gw-recent-runs');
  if (!el) return;
  if (!runs.length) {
    el.innerHTML = '<div style="padding:0.4rem 0.75rem;color:var(--muted);font-size:0.75rem">No runs yet</div>';
    return;
  }
  const STATUS_COLORS = { done: '#3ecf8e', error: '#e85d75', running: '#f5a623',
                           stopped: '#888', cancelled: '#888', waiting_approval: '#9b7ef8' };
  el.innerHTML = runs.slice(0, 12).map(r => {
    const color = STATUS_COLORS[r.status] || 'var(--muted)';
    const dur = r.started_at ? _fmtDurIso(r.started_at, r.finished_at) : '';
    const cost = r.total_cost_usd > 0 ? ` · $${Number(r.total_cost_usd).toFixed(3)}` : '';
    const rawName = r.workflow_name === '_work_item_pipeline' ? 'Work Item Pipeline' : (r.workflow_name || 'Pipeline');
    const label = rawName.slice(0, 22);
    const input  = (r.user_input || '').slice(0, 30);
    return `
      <div class="gw-run-row" onclick="window._gwOpenRun('${r.id}')" title="${_esc(r.user_input||'')}">
        <div class="gw-run-dot" style="background:${color}"></div>
        <div style="flex:1;min-width:0">
          <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-weight:500">${_esc(label)}</div>
          ${input ? `<div style="font-size:0.65rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(input)}</div>` : ''}
        </div>
        <div style="font-size:0.65rem;color:var(--muted);white-space:nowrap;flex-shrink:0">${dur}${cost}</div>
      </div>`;
  }).join('');
}

// ── Duration helpers ──────────────────────────────────────────────────────────

function _fmtDurIso(startIso, endIso) {
  if (!startIso) return '';
  const start = new Date(startIso).getTime();
  const end   = endIso ? new Date(endIso).getTime() : Date.now();
  return _fmtDurMs(end - start);
}

function _fmtDurMs(ms) {
  if (ms < 0) ms = 0;
  const s = Math.floor(ms / 1000);
  if (s < 60) return `${s}s`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ${s % 60}s`;
  return `${Math.floor(m / 60)}h ${m % 60}m`;
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
  const propsBtn = document.getElementById('gw-props-btn');
  const displayName = wf.name === '_work_item_pipeline' ? 'Work Item Pipeline' : wf.name;
  if (nameEl) nameEl.value = displayName;
  if (nameWrap) nameWrap.style.display = '';
  if (runControls) runControls.style.display = 'flex';
  if (propsBtn) propsBtn.style.display = '';
  _renderPipeline(wf);
  // Auto-open properties panel when a workflow is first selected
  _showPipelineProps();
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
    _listCache = null;
    _loadList();
  } catch (e) {
    toast(`Could not create pipeline: ${e.message}`, 'error');
  }
}

// ── Template menu ─────────────────────────────────────────────────────────────

// PIPELINE_TEMPLATES loaded dynamically from GET /agents/pipelines
// (see _loadPipelineTemplates()). Fallback for offline mode:
const _FALLBACK_TEMPLATES = [
  {
    key: 'standard', label: 'PM → Architect → Dev → Reviewer',
    description: 'Full 4-agent work item pipeline',
    nodes: [
      { name: 'Product Manager', stateless: false,
        inputs: [{name:'prompt',type:'prompt'}], outputs: [{name:'spec.md',type:'md'}], role_prompt: '' },
      { name: 'Sr. Architect', stateless: false,
        inputs: [{name:'spec.md',type:'md'}], outputs: [{name:'arch.md',type:'md'}], role_prompt: '' },
      { name: 'Web Developer', stateless: false,
        inputs: [{name:'arch.md',type:'md'}], outputs: [{name:'code',type:'code'}], role_prompt: '' },
      { name: 'Code Reviewer', stateless: true,
        inputs: [{name:'code',type:'code'}], outputs: [{name:'score',type:'score'}], role_prompt: '' },
    ],
    edges: [{ from: 0, to: 1 }, { from: 1, to: 2 }, { from: 2, to: 3 }],
  },
];
let _pipelineTemplates = null;

async function _loadPipelineTemplates() {
  if (_pipelineTemplates) return _pipelineTemplates;
  try {
    const pipelines = await api.listPipelines();
    _pipelineTemplates = pipelines.map(p => ({
      key:         p.name,
      label:       p.name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
      description: (p.description || '').split('\n')[0].trim(),
      nodes: (p.stages || []).map((s, i) => ({
        name:       s.role || s.key,
        stateless:  s.key === 'reviewer',
        inputs:     i === 0 ? [{name:'prompt',type:'prompt'}] : [{name:'input',type:'md'}],
        outputs:    [{name: s.result_field || 'output', type: i === (p.stages.length - 1) ? 'score' : 'md'}],
        role_prompt: '',
      })),
      edges: (p.stages || []).slice(0, -1).map((_, i) => ({ from: i, to: i + 1 })),
    }));
  } catch {
    _pipelineTemplates = _FALLBACK_TEMPLATES;
  }
  return _pipelineTemplates;
}

async function _showTemplateMenu(evt) {
  const existing = document.getElementById('_gw-tmpl-menu');
  if (existing) { existing.remove(); return; }

  const btn = evt?.currentTarget || evt?.target;
  const rect = btn?.getBoundingClientRect?.() || { left: 100, bottom: 50 };

  const menu = document.createElement('div');
  menu.id = '_gw-tmpl-menu';
  menu.style.cssText = `position:fixed;z-index:2000;background:var(--bg1);border:1px solid var(--border);
    border-radius:6px;box-shadow:0 4px 20px rgba(0,0,0,0.18);padding:0.4rem 0;min-width:260px;
    left:${rect.left}px;top:${(rect.bottom || 50) + 4}px`;
  menu.innerHTML = `<div style="padding:0.5rem 0.85rem;color:var(--muted);font-size:0.75rem">Loading…</div>`;
  document.body.appendChild(menu);

  const templates = await _loadPipelineTemplates();
  menu.innerHTML = '';
  templates.forEach(tmpl => {
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
  // Don't save the display-only alias back to the DB
  if (_currentWf.name === '_work_item_pipeline') return;
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

  // Provider / model / temperature row
  const providerLabel = node.provider || 'claude';
  const modelPart     = node.model ? ` / ${node.model}` : '';
  const tempPart      = node.temperature != null ? ` · t${node.temperature}` : '';
  const modelLabel    = `${providerLabel}${modelPart}${tempPart}`;

  // Acceptance criteria preview
  const criteria = node.acceptance_criteria || node.success_criteria || '';

  // Config badges (only non-default values shown)
  const cfgBadges = [];
  if (node.stateless)            cfgBadges.push(`<span class="gw-cfg-badge gw-cfg-stateless" title="Fresh context each run">stateless</span>`);
  if ((node.max_retry ?? 3) > 1) cfgBadges.push(`<span class="gw-cfg-badge" title="Max retries">retry:${node.max_retry ?? 3}</span>`);
  if (node.continue_on_fail)     cfgBadges.push(`<span class="gw-cfg-badge gw-cfg-warn"     title="Continue even if this node fails">cont.fail</span>`);
  if (node.require_approval)     cfgBadges.push(`<span class="gw-cfg-badge gw-cfg-approval" title="Human approval required">approval</span>`);

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
          <span class="gw-node-row-lbl">LLM</span>
          <span class="gw-node-row-val">${_esc(modelLabel)}</span>
        </div>
        ${criteria ? `
        <div style="margin-top:0.3rem;font-size:0.68rem;color:var(--muted);line-height:1.35;
                    display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden"
             title="${_esc(criteria)}">✓ ${_esc(criteria.slice(0, 70))}${criteria.length > 70 ? '…' : ''}</div>
        ` : `<div style="font-size:0.68rem;color:var(--muted);font-style:italic">click to configure</div>`}
        ${cfgBadges.length ? `<div class="gw-node-cfg-badges" style="margin-top:0.3rem">${cfgBadges.join('')}</div>` : ''}
      </div>
      <div class="gw-node-footer">
        <div class="gw-node-status" id="status-${node.id}"></div>
      </div>
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

// ── Pipeline Properties / Execute / History panel ─────────────────────────────

let _gwPollTimer   = null;   // async pipeline run poll
let _gwRunId       = null;   // current async run id
let _gwHistLimit   = 10;
let _gwPanelMode   = null;   // 'node' | 'pipeline'
let _gwPpFileData  = null;   // { type: 'doc'|'upload', path?: str, file?: File } or null
let _gwPpDocsCache = null;   // cached [{name, path}] from api.documents.list

function _showPipelineProps() {
  if (!_currentWf) return;
  _gwPanelMode   = 'pipeline';
  _selectedNodeId = null;
  _gwPpFileData  = null;
  _gwPpDocsCache = null;  // refresh docs list each time a pipeline is loaded
  document.querySelectorAll('.gw-node-card').forEach(c => c.classList.remove('selected'));

  // Close right detail panel — pipeline props are now inline bars
  const detail = document.getElementById('gw-detail');
  if (detail) detail.classList.remove('open');

  const propsBar = document.getElementById('gw-props-bar');
  const execBar  = document.getElementById('gw-exec-bar');
  const histBar  = document.getElementById('gw-hist-bar');
  if (!propsBar || !execBar || !histBar) return;

  propsBar.style.display = '';
  execBar.style.display  = '';
  histBar.style.display  = '';

  // ── ① Properties bar (compact row above canvas) ──────────────────────
  propsBar.innerHTML = `
    <div style="padding:0.4rem 0.75rem;display:flex;flex-wrap:wrap;gap:0.4rem 1rem;align-items:center">
      <div style="font-size:0.65rem;font-weight:700;color:var(--muted);text-transform:uppercase;
                  letter-spacing:0.05em;flex-shrink:0">Properties</div>

      <div style="display:flex;align-items:center;gap:0.3rem;flex-shrink:0">
        <label style="font-size:0.65rem;color:var(--muted)">Max retries</label>
        <input id="pp-retries" type="number" min="1" max="10"
          value="${_currentWf.max_rejection_retries ?? _currentWf.max_iterations ?? 3}"
          style="width:44px;font-size:0.72rem;padding:0.1rem 0.3rem;border:1px solid var(--border);
                 border-radius:3px;background:var(--bg1);color:var(--fg);text-align:center">
      </div>

      <div style="display:flex;align-items:center;gap:0.3rem;flex-shrink:0">
        <label style="font-size:0.65rem;color:var(--muted)">Temp</label>
        <input id="pp-temp" type="number" min="0" max="1" step="0.05"
          value="${_currentWf.default_temperature ?? ''}"
          placeholder="default"
          style="width:58px;font-size:0.72rem;padding:0.1rem 0.3rem;border:1px solid var(--border);
                 border-radius:3px;background:var(--bg1);color:var(--fg)">
      </div>

      <label style="display:flex;align-items:center;gap:0.25rem;font-size:0.65rem;cursor:pointer;flex-shrink:0">
        <input type="checkbox" id="pp-continue" ${_currentWf.continue_on_failure ? 'checked' : ''}>
        Continue on fail
      </label>

      <label style="display:flex;align-items:center;gap:0.25rem;font-size:0.65rem;cursor:pointer;flex-shrink:0">
        <input type="checkbox" id="pp-savemem" ${_currentWf.save_memory !== false ? 'checked' : ''}>
        Save memory
      </label>

      <span id="pp-save-status" style="font-size:0.65rem;color:var(--muted)"></span>
    </div>
  `;

  // Auto-save when properties change
  let saveTimer = null;
  const schedSave = () => {
    const s = document.getElementById('pp-save-status');
    if (s) { s.textContent = 'Unsaved…'; s.style.color = 'var(--muted)'; }
    clearTimeout(saveTimer);
    saveTimer = setTimeout(_gwSavePipelineProps, 800);
  };
  ['pp-retries','pp-temp','pp-continue','pp-savemem'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', schedSave);
  });

  // ── ② Execution bar (below canvas) ───────────────────────────────────
  execBar.innerHTML = `
    <div style="display:flex;align-items:center;padding:0.4rem 0.75rem;
                background:var(--bg2);border-bottom:1px solid var(--border);flex-shrink:0">
      <span style="font-size:0.72rem;font-weight:600;flex:1">Execute</span>
    </div>
    <div id="gw-exec-body" style="padding:0.6rem 0.75rem;display:flex;flex-direction:column;
                                   gap:0.45rem;overflow-y:auto">

      <!-- Input mode toggle -->
      <div style="display:flex;align-items:center;gap:0.75rem">
        <span style="font-size:0.65rem;font-weight:600;color:var(--muted);text-transform:uppercase;
                     letter-spacing:0.04em">Input</span>
        <label style="display:flex;align-items:center;gap:0.2rem;font-size:0.72rem;cursor:pointer">
          <input type="radio" name="pp-input-mode" value="prompt" checked
            onchange="window._gwPpModeSwitch('prompt')"> Prompt
        </label>
        <label style="display:flex;align-items:center;gap:0.2rem;font-size:0.72rem;cursor:pointer">
          <input type="radio" name="pp-input-mode" value="file"
            onchange="window._gwPpModeSwitch('file')"> File
        </label>
      </div>

      <!-- Prompt section -->
      <div id="pp-prompt-section">
        <textarea id="pp-task" rows="3"
          placeholder="Describe what you want the pipeline to do…"
          style="width:100%;box-sizing:border-box;font-size:0.78rem;resize:vertical;
                 background:var(--bg1);border:1px solid var(--border);border-radius:4px;
                 padding:0.3rem 0.45rem;color:var(--fg);font-family:inherit"
          oninput="window._gwPpValidate()"></textarea>
      </div>

      <!-- File section (hidden initially) -->
      <div id="pp-file-section" style="display:none;flex-direction:column;gap:0.35rem">
        <div style="font-size:0.65rem;color:var(--muted);font-weight:500">Project document or local file:</div>

        <!-- Searchable doc combobox -->
        <div style="position:relative">
          <input type="text" id="pp-doc-search"
            placeholder="Search documents…"
            autocomplete="off"
            style="width:100%;box-sizing:border-box;padding:0.3rem 0.4rem;font-size:0.76rem;
                   background:var(--bg1);border:1px solid var(--border);border-radius:4px;color:var(--fg)"
            oninput="window._gwPpDocSearch(this.value)"
            onfocus="window._gwPpDocSearch(this.value)"
            onblur="setTimeout(() => { const l=document.getElementById('pp-doc-list'); if(l) l.style.display='none'; }, 150)">
          <input type="hidden" id="pp-doc-select" value="">
          <div id="pp-doc-list"
            style="display:none;position:absolute;top:100%;left:0;right:0;z-index:200;
                   background:var(--bg1);border:1px solid var(--border);border-radius:0 0 4px 4px;
                   max-height:140px;overflow-y:auto;box-shadow:0 4px 12px rgba(0,0,0,0.18)"></div>
        </div>

        <div style="text-align:center;font-size:0.62rem;color:var(--muted)">— or —</div>

        <!-- Local file upload -->
        <label class="btn btn-ghost btn-sm"
          style="cursor:pointer;font-size:0.72rem;width:100%;box-sizing:border-box;text-align:center">
          Upload local file…
          <input type="file" id="pp-file-input" style="display:none"
            onchange="window._gwPpFileSelect(this)">
        </label>
        <div id="pp-file-name" style="font-size:0.65rem;color:var(--muted)"></div>
      </div>

      <!-- Optional extra prompt when in file mode -->
      <div id="pp-file-prompt-wrap" style="display:none">
        <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.2rem">Additional instructions (optional):</div>
        <textarea id="pp-file-task" rows="2"
          placeholder="e.g. Summarise, Review for errors, Extract requirements…"
          style="width:100%;box-sizing:border-box;font-size:0.76rem;resize:vertical;
                 background:var(--bg1);border:1px solid var(--border);border-radius:4px;
                 padding:0.25rem 0.4rem;color:var(--fg);font-family:inherit"></textarea>
      </div>

      <div style="display:flex;gap:0.4rem;flex-wrap:wrap;align-items:center">
        <button id="pp-run-btn" class="btn btn-primary btn-sm"
          style="font-size:0.76rem;opacity:0.4" disabled onclick="window._gwPpRun()">▶ Run Pipeline</button>
        <button id="pp-cancel-btn" class="btn btn-ghost btn-sm"
          style="font-size:0.76rem;display:none" onclick="window._gwPpCancel()">■ Cancel</button>
        <div id="pp-run-err" style="font-size:0.72rem;color:#e74c3c"></div>
      </div>

      <!-- Stage progress (shown when run started) -->
      <div id="pp-progress" style="display:none">
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.06em;color:var(--muted);margin-bottom:0.25rem">Progress</div>
        <div id="pp-dots" style="margin-bottom:0.35rem;font-size:0.72rem"></div>
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.06em;color:var(--muted);margin-bottom:0.15rem">Log</div>
        <div id="pp-log" style="font-family:var(--font-mono,monospace);font-size:0.65rem;
             line-height:1.4;background:var(--bg1);border:1px solid var(--border);border-radius:4px;
             padding:0.3rem 0.4rem;height:110px;overflow-y:auto"></div>
      </div>

      <!-- Approval gate -->
      <div id="pp-approval" style="display:none;border:2px solid #9b59b6;border-radius:6px;
           padding:0.5rem;background:rgba(155,89,182,0.06)">
        <div style="font-weight:700;color:#9b59b6;font-size:0.76rem;margin-bottom:0.2rem">⏸ Approval Required</div>
        <div id="pp-apv-msg" style="font-size:0.7rem;color:var(--muted);margin-bottom:0.2rem"></div>
        <textarea id="pp-apv-fb" rows="2" placeholder="Feedback (optional)…"
          style="width:100%;box-sizing:border-box;background:var(--bg1);border:1px solid var(--border);
                 border-radius:4px;padding:0.25rem;font-size:0.72rem;resize:vertical;margin-bottom:0.25rem;font-family:inherit"></textarea>
        <div style="display:flex;gap:0.3rem">
          <button class="btn btn-primary btn-sm" style="font-size:0.7rem;flex:1"
            onclick="window._gwPpApprove(true)">✓ Approve</button>
          <button class="btn btn-ghost btn-sm" style="font-size:0.7rem;flex:1;color:#e74c3c;border-color:#e74c3c"
            onclick="window._gwPpApprove(false)">✗ Reject</button>
        </div>
      </div>
    </div>
  `;

  // ── ③ History bar (toggle at bottom) ─────────────────────────────────
  histBar.innerHTML = `
    <div style="display:flex;align-items:center;justify-content:space-between;
                padding:0.4rem 0.75rem;cursor:pointer;background:var(--bg2);flex-shrink:0"
         onclick="window._gwToggleHist()">
      <span style="font-size:0.72rem;font-weight:600" id="gw-hist-toggle-lbl">▸ History</span>
      <span style="display:flex;gap:0.2rem">
        ${[10,20,50].map(n =>
          `<button class="btn btn-ghost" style="font-size:0.6rem;padding:0.02rem 0.22rem;min-height:0"
             onclick="event.stopPropagation();window._gwPpHistLimit(${n})">${n}</button>`
        ).join('')}
      </span>
    </div>
    <div id="gw-hist-body" style="display:none;overflow-y:auto;flex:1;padding:0.4rem 0.75rem">
      <div id="pp-hist"></div>
    </div>
  `;

  window._gwPpRun       = _gwPpRun;
  window._gwPpCancel    = _gwPpCancel;
  window._gwPpApprove   = _gwPpApprove;
  window._gwPpHistLimit = n => { _gwHistLimit = n; _gwLoadHistory(); };
  window._gwPpModeSwitch = (mode) => {
    const ps = document.getElementById('pp-prompt-section');
    const fs = document.getElementById('pp-file-section');
    const fp = document.getElementById('pp-file-prompt-wrap');
    if (ps) ps.style.display = mode === 'prompt' ? '' : 'none';
    if (fs) fs.style.display = mode === 'file'   ? 'flex' : 'none';
    if (fp) fp.style.display = mode === 'file'   ? '' : 'none';
    if (mode === 'file') _gwPpLoadDocs();
    _gwPpValidate();
  };
  window._gwPpFileSelect = (input) => {
    const fn  = document.getElementById('pp-file-name');
    const src = document.getElementById('pp-doc-search');
    const sel = document.getElementById('pp-doc-select');
    const f   = input.files?.[0];
    if (fn)  fn.textContent = f ? `📄 ${f.name}` : '';
    if (src) src.value = '';   // clear doc search when file chosen
    if (sel) sel.value = '';
    _gwPpFileData = f ? { type: 'upload', file: f } : null;
    _gwPpValidate();
  };
  window._gwPpDocSearch  = _gwPpDocSearch;
  window._gwPpValidate   = _gwPpValidate;
  window._gwPpDocPick    = (path, label) => {
    const sel = document.getElementById('pp-doc-select');
    const src = document.getElementById('pp-doc-search');
    const fn  = document.getElementById('pp-file-name');
    const lst = document.getElementById('pp-doc-list');
    const fi  = document.getElementById('pp-file-input');
    if (sel) sel.value = path;
    if (src) src.value = label;
    if (fn)  fn.textContent = '';
    if (lst) lst.style.display = 'none';
    if (fi)  fi.value = '';   // clear file upload
    _gwPpFileData = null;
    _gwPpValidate();
  };
  window._gwToggleHist  = () => {
    const body = document.getElementById('gw-hist-body');
    const lbl  = document.getElementById('gw-hist-toggle-lbl');
    if (!body) return;
    const open = body.style.display !== 'none';
    body.style.display = open ? 'none' : '';
    if (lbl) lbl.textContent = open ? '▸ History' : '▾ History';
    if (!open) _gwLoadHistory();
  };

  _gwLoadHistory();
}

async function _gwPpLoadDocs() {
  if (_gwPpDocsCache) { _gwPpDocSearch(''); return; }
  const src = document.getElementById('pp-doc-search');
  if (src) src.placeholder = 'Loading…';
  try {
    const data = await api.documents.list(_project);
    const raw  = Array.isArray(data) ? data : (data?.documents || data?.files || []);
    _gwPpDocsCache = raw.map(d => ({
      name: d.name || d.filename || String(d.path || d).split('/').pop() || String(d),
      path: d.path || d.name || String(d),
    }));
  } catch (_) {
    _gwPpDocsCache = [];
  }
  if (src) src.placeholder = 'Search documents…';
  _gwPpDocSearch('');
}

function _gwPpDocSearch(q) {
  const lst = document.getElementById('pp-doc-list');
  if (!lst || !_gwPpDocsCache) return;
  const query = (q || '').toLowerCase();
  const matches = query
    ? _gwPpDocsCache.filter(d => d.name.toLowerCase().includes(query) || d.path.toLowerCase().includes(query))
    : _gwPpDocsCache;

  if (!matches.length) {
    lst.style.display = 'none'; return;
  }
  lst.style.display = '';
  lst.innerHTML = matches.slice(0, 30).map(d => `
    <div style="padding:0.3rem 0.55rem;cursor:pointer;font-size:0.75rem;white-space:nowrap;
                overflow:hidden;text-overflow:ellipsis"
         onmouseenter="this.style.background='var(--hover)'"
         onmouseleave="this.style.background=''"
         onmousedown="event.preventDefault();window._gwPpDocPick(${JSON.stringify(d.path)},${JSON.stringify(d.name)})">
      📄 ${_esc(d.name)}
      ${d.path !== d.name ? `<span style="font-size:0.62rem;color:var(--muted)">${_esc(d.path)}</span>` : ''}
    </div>`).join('');
}

function _gwPpValidate() {
  const btn = document.getElementById('pp-run-btn');
  if (!btn) return;
  const mode = document.querySelector('input[name="pp-input-mode"]:checked')?.value || 'prompt';
  let ready = false;
  if (mode === 'prompt') {
    ready = (document.getElementById('pp-task')?.value || '').trim().length > 0;
  } else {
    ready = !!(document.getElementById('pp-doc-select')?.value || _gwPpFileData);
  }
  btn.disabled = !ready;
  btn.style.opacity = ready ? '' : '0.4';
}

async function _gwSavePipelineProps() {
  const statusEl = document.getElementById('pp-save-status');
  if (!_currentWf || !statusEl) return;
  const tempRaw = document.getElementById('pp-temp')?.value;
  const body = {
    max_rejection_retries: parseInt(document.getElementById('pp-retries')?.value || '3', 10),
    continue_on_failure:   document.getElementById('pp-continue')?.checked ?? false,
    save_memory:           document.getElementById('pp-savemem')?.checked ?? true,
    default_temperature:   tempRaw !== '' && tempRaw != null ? parseFloat(tempRaw) : null,
  };
  try {
    // Try YAML pipeline PATCH first, fall back silently for custom workflows
    await api.agentRoles.patchPipeline(_currentWf.name, body, _project);
    statusEl.textContent = 'Saved ✓'; statusEl.style.color = 'var(--green,#3ecf8e)';
    setTimeout(() => { if (statusEl) statusEl.textContent = ''; }, 2500);
  } catch (_) {
    // Custom workflow — properties not stored server-side yet
    statusEl.textContent = '(properties not saved for custom workflows)';
    statusEl.style.color = 'var(--muted)';
  }
}

async function _gwPpRun() {
  const mode = document.querySelector('input[name="pp-input-mode"]:checked')?.value || 'prompt';
  let task = '';
  let inputFiles = [];

  const extraInstructions = (document.getElementById('pp-file-task')?.value || '').trim();

  if (mode === 'file') {
    const docPath = document.getElementById('pp-doc-select')?.value;
    if (docPath) {
      // Load doc content from project documents
      try {
        const data = await api.documents.read(docPath, _project);
        const content = data?.content || data?.text || '';
        task = [content || `Document: ${docPath}`, extraInstructions].filter(Boolean).join('\n\n');
        inputFiles = [{ type: 'doc', path: docPath }];
      } catch (_) {
        task = [`Process document: ${docPath}`, extraInstructions].filter(Boolean).join('\n\n');
        inputFiles = [{ type: 'doc', path: docPath }];
      }
    } else if (_gwPpFileData?.file) {
      // Read uploaded file content client-side
      try {
        const content = await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = e => resolve(e.target.result);
          reader.onerror = reject;
          reader.readAsText(_gwPpFileData.file);
        });
        task = [content, extraInstructions].filter(Boolean).join('\n\n');
        inputFiles = [{ type: 'upload', name: _gwPpFileData.file.name }];
      } catch (_) {
        document.getElementById('pp-run-err').textContent = 'Failed to read file.';
        return;
      }
    } else {
      document.getElementById('pp-run-err').textContent = 'Select a document or upload a file.';
      return;
    }
  } else {
    task = (document.getElementById('pp-task')?.value || '').trim();
    if (!task) { document.getElementById('pp-run-err').textContent = 'Enter a task first.'; return; }
  }

  document.getElementById('pp-run-err').textContent = '';
  document.getElementById('pp-run-btn').style.display    = 'none';
  document.getElementById('pp-cancel-btn').style.display = '';
  document.getElementById('pp-progress').style.display   = '';
  document.getElementById('pp-approval').style.display   = 'none';
  _gwPpClearLog();

  // Try as a YAML pipeline run (async)
  try {
    const payload = { pipeline: _currentWf.name, task, project: _project };
    if (inputFiles.length) payload.input_files = inputFiles;
    const res = await api.agents.startPipelineRun(payload);
    _gwRunId = res.run_id;
    _gwPpLog(`Run started: ${_gwRunId}`);
    _gwStartPoll();
  } catch (_) {
    // Fall back to the existing graph workflow run (opens the bottom run panel)
    _gwRunId = null;
    document.getElementById('pp-run-btn').style.display    = '';
    document.getElementById('pp-cancel-btn').style.display = 'none';
    document.getElementById('pp-progress').style.display   = 'none';
    window._gwStartRun?.();
  }
}

function _gwPpCancel() {
  if (_gwPollTimer) { clearInterval(_gwPollTimer); _gwPollTimer = null; }
  _gwRunId = null;
  _gwPpLog('Cancelled.', 'warn');
  document.getElementById('pp-run-btn').style.display    = '';
  document.getElementById('pp-cancel-btn').style.display = 'none';
}

function _gwStartPoll() {
  if (_gwPollTimer) clearInterval(_gwPollTimer);
  _gwPollTimer = setInterval(async () => {
    if (!_gwRunId) { clearInterval(_gwPollTimer); return; }
    try {
      const data = await api.agents.getPipelineRun(_gwRunId);
      _gwPpUpdateProgress(data);
      if (!['running','waiting_approval'].includes(data.status)) {
        clearInterval(_gwPollTimer); _gwPollTimer = null;
        _gwPpOnDone(data);
      }
    } catch (e) { _gwPpLog(`Poll error: ${e.message}`, 'error'); }
  }, 1500);
}

function _gwPpUpdateProgress(data) {
  // Stage dots
  const dotsEl = document.getElementById('pp-dots');
  if (dotsEl) {
    const STATUS_CLR = { done:'#3ecf8e', running:'#f5a623', error:'#e85d75',
                         waiting_approval:'#9b7ef8', pending:'var(--muted)' };
    dotsEl.innerHTML = (data.stages || []).map(s => {
      const dur = s.duration_s != null ? ` ${Number(s.duration_s).toFixed(0)}s` : '';
      const cost = s.cost_usd > 0 ? ` $${Number(s.cost_usd).toFixed(4)}` : '';
      return `<div style="display:flex;align-items:center;gap:0.3rem;padding:0.1rem 0">
        <div style="width:7px;height:7px;border-radius:50%;flex-shrink:0;background:${STATUS_CLR[s.status]||'var(--muted)'}"></div>
        <span style="font-family:monospace;font-size:0.65rem;min-width:80px">${s.stage_key||''}</span>
        <span style="font-size:0.62rem;color:var(--muted)">${s.role_name||''}</span>
        <span style="font-size:0.62rem;color:var(--muted)">${dur}${cost}</span>
      </div>`;
    }).join('');
  }

  // Log lines (dedup)
  const logEl = document.getElementById('pp-log');
  if (logEl) {
    if (!logEl._seen) logEl._seen = new Set();
    for (const stage of (data.stages || [])) {
      for (const entry of (stage.log_lines || [])) {
        const key = `${stage.stage_key}:${entry.ts}`;
        if (!logEl._seen.has(key)) {
          logEl._seen.add(key);
          _gwPpLog(`[${stage.stage_key}] ${entry.text}`, entry.level);
        }
      }
    }
  }

  // Approval gate
  const apEl = document.getElementById('pp-approval');
  if (data.status === 'waiting_approval' && apEl) {
    apEl.style.display = '';
    const last = (data.stages || []).filter(s => s.status === 'done').at(-1);
    if (last) document.getElementById('pp-apv-msg').textContent =
      `Stage "${last.stage_key}" done. Approve to continue.`;
  } else if (apEl) {
    apEl.style.display = 'none';
  }
}

function _gwPpOnDone(data) {
  const verdict = data.final_verdict || data.status;
  _gwPpLog(`Done — ${verdict} | $${(data.total_cost_usd||0).toFixed(4)} | ${(data.total_input_tokens||0)+(data.total_output_tokens||0)} tok`);
  document.getElementById('pp-run-btn').style.display    = '';
  document.getElementById('pp-cancel-btn').style.display = 'none';
  _gwRunId = null;
  _gwLoadHistory();
}

async function _gwPpApprove(approved) {
  if (!_gwRunId) return;
  const fb = document.getElementById('pp-apv-fb')?.value || '';
  try {
    await api.agents.approvePipelineRun(_gwRunId, { approved, feedback: fb });
    document.getElementById('pp-approval').style.display = 'none';
  } catch (e) { _gwPpLog(`Approval error: ${e.message}`, 'error'); }
}

function _gwPpLog(text, level = 'info') {
  const el = document.getElementById('pp-log');
  if (!el) return;
  const ts  = new Date().toLocaleTimeString();
  const col = level === 'error' ? '#e85d75' : level === 'warn' ? '#f5a623' : 'inherit';
  el.insertAdjacentHTML('beforeend',
    `<div style="color:${col}">${ts}  ${String(text).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>`);
  el.scrollTop = el.scrollHeight;
}

function _gwPpClearLog() {
  const el = document.getElementById('pp-log');
  if (el) { el.innerHTML = ''; el._seen = new Set(); }
}

async function _gwLoadHistory() {
  const el = document.getElementById('pp-hist');
  if (!el) return;
  el.innerHTML = '<div style="color:var(--muted);font-size:0.7rem">Loading…</div>';
  try {
    const data = await api.agents.listPipelineRuns(_project, _currentWf?.name, _gwHistLimit);
    const runs = data.runs || [];
    if (!runs.length) {
      el.innerHTML = '<div style="color:var(--muted);font-size:0.7rem">No runs yet.</div>';
      return;
    }
    const STATUS_CLR = { approved:'var(--green,#3ecf8e)', rejected:'#e85d75', done:'var(--muted)', error:'#e85d75' };
    el.innerHTML = runs.map(r => {
      const at  = r.started_at ? new Date(r.started_at).toLocaleString() : '—';
      const dur = r.duration_s != null ? _gwFmtDur(r.duration_s) : '—';
      const tok = (r.total_input_tokens||0) + (r.total_output_tokens||0);
      const cost = r.total_cost_usd != null ? `$${Number(r.total_cost_usd).toFixed(4)}` : '—';
      const v   = r.final_verdict || r.status || '—';
      const sc  = r.score ?? null;
      const stars = [1,2,3,4,5].map(n =>
        `<span data-run="${r.run_id}" data-s="${n}"
          style="cursor:pointer;color:${sc != null && n <= sc ? '#f5a623' : 'var(--muted)'};font-size:0.8rem">★</span>`
      ).join('');
      return `
        <div style="padding:0.3rem 0;border-bottom:1px solid var(--border);font-size:0.68rem">
          <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:0.2rem">
            <span style="color:var(--muted)">${at}</span>
            <span style="color:${STATUS_CLR[v]||'var(--muted)'};font-weight:600">${v}</span>
          </div>
          <div style="display:flex;gap:0.5rem;color:var(--muted);flex-wrap:wrap;margin-top:0.15rem">
            <span>${dur}</span>
            <span>${tok >= 1000 ? (tok/1000).toFixed(1)+'k' : tok} tok</span>
            <span style="color:var(--accent)">${cost}</span>
          </div>
          <div style="display:flex;gap:0.05rem;margin-top:0.15rem">${stars}</div>
          ${r.task ? `<div style="color:var(--muted);margin-top:0.1rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${r.task}">${r.task.slice(0,50)}</div>` : ''}
        </div>`;
    }).join('');

    // Star click handlers
    el.querySelectorAll('[data-s]').forEach(star => {
      star.addEventListener('click', async () => {
        try {
          await api.agents.scoreRun(star.dataset.run, parseInt(star.dataset.s, 10));
          _gwLoadHistory();
        } catch (_) {}
      });
    });
  } catch (e) {
    el.innerHTML = `<div style="color:#e85d75;font-size:0.7rem">${e.message}</div>`;
  }
}

function _gwFmtDur(s) {
  const sec = Math.round(s || 0);
  return sec < 60 ? `${sec}s` : `${Math.floor(sec/60)}m ${sec%60}s`;
}

// ── Close detail panel (node config) ─────────────────────────────────────────

function _closeDetail() {
  _selectedNodeId = null;
  _gwPanelMode = null;
  document.querySelectorAll('.gw-node-card').forEach(c => c.classList.remove('selected'));
  const detail = document.getElementById('gw-detail');
  if (detail) detail.classList.remove('open');
  const footer = document.querySelector('.gw-detail-footer');
  if (footer) footer.style.display = '';
}

function _renderDetailPanel(node) {
  _gwPanelMode = 'node';
  const title  = document.getElementById('gw-detail-title');
  const body   = document.getElementById('gw-detail-body');
  const footer = document.querySelector('.gw-detail-footer');
  if (!body) return;
  if (title)  title.textContent    = node.name;
  if (footer) footer.style.display = '';

  // Match node to a loaded role for system prompt display
  const matchedRole = _roles.find(r => r.id === node.role_id || r.name === node.name);
  const roleName    = matchedRole?.name || node.name;
  const systemPrompt = node.role_prompt || matchedRole?.system_prompt || '(no system prompt configured for this role)';

  const isAdmin = !!(state.user?.is_admin || state.user?.role === 'admin');

  const providerOptions = ['claude','openai','deepseek','gemini','grok'].map(p =>
    `<option value="${p}" ${node.provider===p?'selected':''}>${p}</option>`
  ).join('');

  // Context flow: show prior node names + stored role props
  const nodeIndex = _currentWf?.nodes?.findIndex(n => n.id === node.id) ?? -1;
  const priorNodes = nodeIndex > 0 ? _currentWf.nodes.slice(0, nodeIndex) : [];
  const priorChips = priorNodes.map(n =>
    `<span style="background:var(--bg1);border:1px solid var(--border);border-radius:3px;
              padding:0.05rem 0.3rem;font-size:0.65rem">${_esc(n.name)}</span>`
  ).join(' → ');
  const propTags = [
    `<span style="background:rgba(100,108,255,0.12);border-radius:3px;padding:0.05rem 0.3rem;font-size:0.65rem">
       ${_esc(node.provider || 'claude')}</span>`,
    node.model ? `<span style="background:rgba(100,108,255,0.12);border-radius:3px;padding:0.05rem 0.3rem;font-size:0.65rem">
       ${_esc(node.model)}</span>` : '',
    node.temperature != null ? `<span style="background:rgba(100,108,255,0.12);border-radius:3px;padding:0.05rem 0.3rem;font-size:0.65rem">
       temp ${node.temperature}</span>` : '',
  ].filter(Boolean).join(' ');

  const acceptanceCriteria = node.acceptance_criteria || node.success_criteria || '';

  body.innerHTML = `
    <div class="gw-field">
      <label>Name (Role Name)</label>
      <input id="dn-name" value="${_esc(node.name)}" />
    </div>

    <div style="display:flex;gap:0.5rem">
      <div class="gw-field" style="flex:1">
        <label>Provider</label>
        <select id="dn-provider">${providerOptions}</select>
      </div>
      <div class="gw-field" style="width:58px">
        <label>Temp</label>
        <input type="number" id="dn-temp"
          value="${node.temperature ?? ''}" min="0" max="1" step="0.05"
          placeholder="—"
          style="width:100%;text-align:center" />
      </div>
    </div>

    <div class="gw-field">
      <label>Model <span style="font-weight:400;color:var(--muted)">(leave blank for role default)</span></label>
      <input id="dn-model" value="${_esc(node.model||'')}" placeholder="e.g. claude-sonnet-4-6" />
    </div>

    <!-- Context flow -->
    <div style="background:rgba(100,108,255,0.07);border:1px solid rgba(100,108,255,0.2);
                border-radius:6px;padding:0.5rem 0.65rem;margin-bottom:0.75rem;">
      <div style="font-size:0.65rem;font-weight:700;color:var(--fg);margin-bottom:0.3rem">Context flow</div>
      <div style="font-size:0.68rem;color:var(--muted);line-height:1.6">
        ${priorChips ? `${priorChips} → <b>${_esc(node.name)}</b><br>
        Outputs from prior nodes are injected before this node's prompt.` :
        `<b>${_esc(node.name)}</b> is the first node — receives the user's task as input.`}
      </div>
      ${propTags ? `<div style="margin-top:0.35rem;display:flex;gap:0.2rem;flex-wrap:wrap">${propTags}</div>` : ''}
    </div>

    <!-- System Prompt (read-only) -->
    <div class="gw-field">
      <label style="display:flex;align-items:center;justify-content:space-between">
        <span>System Prompt</span>
        ${isAdmin
          ? `<a href="#" style="font-size:0.65rem;color:var(--accent);text-decoration:none"
               onclick="event.preventDefault();window._nav('prompts')">Edit in Roles →</a>`
          : `<span style="font-size:0.65rem;color:var(--muted)">role: ${_esc(roleName)}</span>`}
      </label>
      <pre style="margin:0;font-size:0.67rem;line-height:1.45;background:var(--bg2);
                  border:1px solid var(--border);border-radius:4px;padding:0.4rem 0.5rem;
                  max-height:130px;overflow-y:auto;white-space:pre-wrap;word-break:break-word;
                  color:var(--muted);font-family:var(--font-mono,monospace)">${_esc(systemPrompt)}</pre>
    </div>

    <!-- Acceptance Criteria -->
    <div class="gw-field">
      <label>Acceptance Criteria</label>
      <textarea id="dn-criteria" rows="3"
        placeholder="Describe what 'done' looks like for this stage. The pipeline will use this to verify completion.
e.g. All acceptance criteria from spec are addressed. No regressions. Tests pass."
        style="font-size:0.76rem;font-family:inherit">${_esc(acceptanceCriteria)}</textarea>
    </div>

    <div class="gw-field">
      <label>Max Retry</label>
      <input type="number" id="dn-max-retry" value="${node.max_retry ?? 3}" min="1" max="10" style="width:70px" />
    </div>

    <div class="gw-field">
      <div class="gw-toggle-row">
        <label style="margin:0">Stateless <span style="font-weight:400;color:var(--muted)">(fresh context each run)</span></label>
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

  const tempRaw = document.getElementById('dn-temp')?.value;
  const data = {
    name:                document.getElementById('dn-name')?.value || '',
    provider:            document.getElementById('dn-provider')?.value || 'claude',
    model:               document.getElementById('dn-model')?.value || '',
    temperature:         tempRaw !== '' && tempRaw != null ? parseFloat(tempRaw) : null,
    acceptance_criteria: document.getElementById('dn-criteria')?.value || '',
    success_criteria:    document.getElementById('dn-criteria')?.value || '',  // compat
    stateless:           document.getElementById('dn-stateless')?.checked || false,
    continue_on_fail:    document.getElementById('dn-continue-fail')?.checked || false,
    require_approval:    document.getElementById('dn-approval')?.checked || false,
    max_retry:           parseInt(document.getElementById('dn-max-retry')?.value || '3', 10),
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
    _listCache = null;
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
    _runStartTime = new Date();
    _openRunPanel(_currentWf.name, _currentWf.nodes || []);
    _pollRun(run_id);
  } catch (e) {
    toast(`Run failed: ${e.message}`, 'error');
  }
}

function _openLog() {
  const log = document.getElementById('gw-log');
  if (log) log.classList.add('open');
}

function _toggleLog() {
  const log = document.getElementById('gw-log');
  const toggle = document.getElementById('gw-log-toggle');
  if (!log) return;
  const body = log.querySelector('.gw-log-body');
  const open = body?.style.display !== 'none';
  if (body) body.style.display = open ? 'none' : '';
  if (toggle) toggle.textContent = open ? '▶' : '▼';
}

// ── Run progress panel ────────────────────────────────────────────────────────

function _openRunPanel(wfName, nodes) {
  // Show run panel (bottom of canvas — detail panel can remain open)
  const panel = document.getElementById('gw-run-panel');
  if (panel) panel.classList.add('open');

  // Set workflow name
  const nameEl = document.getElementById('gw-rp-wf-name');
  if (nameEl) nameEl.textContent = wfName || 'Pipeline';

  // Reset run log state
  _runLog = [];
  _prevNodeStatuses = {};
  _renderRunLog();

  // Build pending timeline from nodes
  _renderRunTimeline(nodes.map(n => ({ node_name: n.name, node_id: n.id, status: 'pending' })), null);

  // Start live timer
  if (_timerInterval) clearInterval(_timerInterval);
  _timerInterval = setInterval(() => {
    const timerEl = document.getElementById('gw-rp-timer');
    if (timerEl && _runStartTime) {
      timerEl.textContent = _fmtDurMs(Date.now() - _runStartTime.getTime());
    }
  }, 1000);
}

function _closeRunPanel() {
  const panel = document.getElementById('gw-run-panel');
  if (panel) panel.classList.remove('open');
  if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null; }
}

function _pollRun(runId) {
  if (_pollInterval) clearInterval(_pollInterval);
  _pollInterval = setInterval(async () => {
    try {
      const run = await api.graphWorkflows.getRun(runId);
      _updateRunPanel(run);
      const terminal = ['done','error','stopped','cancelled'];
      if (terminal.includes(run.status)) {
        clearInterval(_pollInterval); _pollInterval = null;
        if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null; }
        _onRunComplete(run);
      }
      if (run.status === 'waiting_approval') {
        const newNodeName = run.context?._waiting?.node_name;
        // Only stop polling + show panel when we have a NEW approval gate
        // (different node from what was just approved). This prevents the
        // brief window where the DB still shows waiting_approval for the
        // node we just approved before the backend flips it to 'running'.
        if (newNodeName && newNodeName !== _currentApprovalNodeName) {
          clearInterval(_pollInterval); _pollInterval = null;
          if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null; }
          _showApprovalPanel(run);
        }
      }
    } catch {
      clearInterval(_pollInterval); _pollInterval = null;
    }
  }, 1000);
}

function _updateRunPanel(run) {
  const STATUS_COLORS = { done:'#3ecf8e', error:'#e85d75', running:'#f5a623',
                           stopped:'#888', cancelled:'#888', waiting_approval:'#9b7ef8' };

  // Update header meta
  const dot    = document.getElementById('gw-rp-dot');
  const status = document.getElementById('gw-rp-status');
  const cost   = document.getElementById('gw-rp-cost');
  const nodes  = document.getElementById('gw-rp-nodes');
  const stop   = document.getElementById('gw-rp-stop');

  if (dot)    { dot.className = `gw-rp-status-dot ${run.status}`; }
  if (status) { status.textContent = run.status.replace('_', ' '); status.style.color = STATUS_COLORS[run.status] || 'var(--muted)'; }
  if (cost)   cost.textContent = `$${Number(run.total_cost_usd || 0).toFixed(4)}`;

  const doneCount = (run.node_results || []).filter(nr => nr.status === 'done').length;
  const totalNodes = _currentWf?.nodes?.length || (run.node_results || []).length;
  if (nodes) nodes.textContent = `${doneCount}/${totalNodes}`;

  // Hide stop button when terminal
  if (stop && ['done','error','stopped','cancelled'].includes(run.status)) stop.style.display = 'none';

  // Build merged node list: pipeline order + results
  const pipelineNodes = _currentWf?.nodes || [];
  const resultsByName = {};
  for (const nr of (run.node_results || [])) {
    // Keep latest result per node name (last retry)
    resultsByName[nr.node_name] = nr;
  }

  const steps = pipelineNodes.length
    ? pipelineNodes.map(n => {
        const r = resultsByName[n.name];
        return r ? { ...r, node_id: n.id }
                 : { node_name: n.name, node_id: n.id,
                     status: n.name === run.current_node ? 'running' : 'pending' };
      })
    : run.node_results || [];

  _renderRunTimeline(steps, run.current_node);

  // Generate log entries for newly-changed node statuses
  for (const nr of (run.node_results || [])) {
    const prev = _prevNodeStatuses[nr.node_name];
    if (prev !== nr.status) {
      _prevNodeStatuses[nr.node_name] = nr.status;
      if (nr.status === 'running') {
        _appendRunLog(nr.node_name, 'Processing…');
      } else if (nr.status === 'done') {
        const dur = nr.started_at ? ` (${_fmtDurIso(nr.started_at, nr.finished_at)})` : '';
        const cost = nr.cost_usd > 0 ? `, $${Number(nr.cost_usd).toFixed(4)}` : '';
        _appendRunLog(nr.node_name, `✓ Done${dur}${cost}`);
      } else if (nr.status === 'error') {
        _appendRunLog(nr.node_name, `✗ Error: ${nr.output?.slice(0, 100) || 'unknown'}`);
      }
    }
  }
  // Log when current_node changes (running but no result yet)
  if (run.current_node && run.current_node !== _prevNodeStatuses['__current__']) {
    _prevNodeStatuses['__current__'] = run.current_node;
    if (!run.node_results?.find(nr => nr.node_name === run.current_node && nr.status === 'running')) {
      _appendRunLog(run.current_node, 'Processing…');
    }
  }

  // Update node card status dots on canvas
  for (const nr of (run.node_results || [])) {
    const dot2 = document.getElementById(`status-${nr.node_id}`);
    if (dot2) dot2.className = `gw-node-status ${nr.status}`;
  }
  // Mark current running node on canvas
  if (run.current_node && pipelineNodes.length) {
    const currentNode = pipelineNodes.find(n => n.name === run.current_node);
    if (currentNode) {
      const dot2 = document.getElementById(`status-${currentNode.id}`);
      if (dot2) dot2.className = 'gw-node-status running';
    }
  }
}

function _renderRunTimeline(steps, currentNodeName) {
  const tl = document.getElementById('gw-rp-timeline');
  if (!tl) return;
  tl.innerHTML = steps.map(nr => {
    let stepStatus = nr.status || 'pending';
    if (stepStatus === 'pending' && nr.node_name === currentNodeName) stepStatus = 'running';

    const dur  = nr.started_at ? _fmtDurIso(nr.started_at, nr.finished_at) : '';
    const cost = nr.cost_usd > 0 ? `$${Number(nr.cost_usd).toFixed(4)}` : '';
    const meta = [dur, cost].filter(Boolean).join(' · ');

    const icon = stepStatus === 'done' ? '✓' : stepStatus === 'error' ? '✗'
               : stepStatus === 'running' ? '⟳' : stepStatus === 'skipped' ? '⤳' : '○';

    const outputPreview = nr.output
      ? `<div class="gw-rp-step-out">${renderMd(nr.output.slice(0, 500))}</div>` : '';

    return `
      <div class="gw-rp-step ${stepStatus}">
        <div class="gw-rp-step-hdr">
          <div class="gw-rp-step-dot"></div>
          <span class="gw-rp-step-name">${icon} ${_esc(nr.node_name)}</span>
        </div>
        ${meta ? `<div class="gw-rp-step-meta">${_esc(meta)}</div>` : ''}
        ${outputPreview}
      </div>`;
  }).join('');
}

// ── Run log (full-width text log below timeline cards) ─────────────────────────

function _appendRunLog(nodeName, msg) {
  const ts = new Date().toLocaleTimeString('en', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  _runLog.push({ node: nodeName, msg, ts });
  _renderRunLog();
}

function _renderRunLog() {
  const el = document.getElementById('gw-run-log');
  if (!el) return;
  if (!_runLog.length) {
    el.innerHTML = '<span style="color:var(--muted)">Waiting for pipeline to start…</span>';
    return;
  }
  el.innerHTML = _runLog.map(e => {
    const nodeColor = _getNodeColor(e.node);
    return `<div style="margin-bottom:0.1rem">
      <span style="color:${nodeColor};font-weight:600">${_esc(e.node)}:</span>
      <span style="color:var(--muted);font-size:0.65rem;margin:0 0.35rem">${e.ts}</span>
      <span>${_esc(e.msg)}</span>
    </div>`;
  }).join('');
  el.scrollTop = el.scrollHeight;
}

function _getNodeColor(nodeName) {
  // Map node name to a color based on a stable hash
  const colors = ['#9b7ef8', '#3ecf8e', '#f5a623', '#2dd4bf', '#e85d75', '#5b8ef0'];
  let hash = 0;
  for (const c of (nodeName || '')) hash = (hash * 31 + c.charCodeAt(0)) & 0xffff;
  return colors[hash % colors.length];
}

async function _onRunComplete(run) {
  // Final timer update
  const timerEl = document.getElementById('gw-rp-timer');
  if (timerEl && run.started_at) {
    timerEl.textContent = _fmtDurIso(run.started_at, run.finished_at || new Date().toISOString());
  }

  // Show error if any
  if (run.status === 'error' && run.error) {
    const tl = document.getElementById('gw-rp-timeline');
    if (tl) tl.insertAdjacentHTML('beforeend', `
      <div style="margin:0.5rem 0.75rem;padding:0.5rem;background:rgba(232,93,117,0.1);
           border:1px solid rgba(232,93,117,0.3);border-radius:6px;font-size:0.72rem;color:#e85d75">
        ✗ ${_esc(run.error)}
      </div>`);
  }

  // Load deliverables
  if (run.status === 'done' && _currentRunId) {
    try {
      const { files, directory } = await api.graphWorkflows.deliverables(_currentRunId);
      _renderDeliverables(files, directory, run);
    } catch (_) {}
  }

  // Refresh sidebar run history (background — no loading flash)
  _listCache = null;
  _refreshListInBackground();
}

function _renderDeliverables(files, directory, run) {
  const el = document.getElementById('gw-rp-deliverables');
  if (!el) return;
  el.style.display = '';

  const isWorkItem = _currentWf?.name === '_work_item_pipeline';
  const savedNote = isWorkItem
    ? `<div style="font-size:0.72rem;color:#3ecf8e;margin-top:0.4rem">✓ Work item updated in Planner — open it to view AC &amp; implementation plan</div>`
    : '';

  const ctx = run?.context || {};
  // Build a summary of each node output for display
  const nodeOutputs = (_currentWf?.nodes || []).map(n => {
    const output = ctx[n.name];
    if (!output || typeof output !== 'string') return '';
    const preview = output.slice(0, 600);
    return `
      <details style="margin:0.35rem 0" open>
        <summary style="cursor:pointer;font-size:0.72rem;font-weight:600;color:var(--fg);
                        padding:0.25rem 0;list-style:none;display:flex;align-items:center;gap:0.4rem">
          <span style="color:#3ecf8e">✓</span> ${_esc(n.name)}
        </summary>
        <div class="md-prose" style="font-size:0.71rem;line-height:1.5;
             margin:0.25rem 0 0.35rem 0.75rem;padding:0.4rem 0.5rem;
             background:var(--bg2);border-radius:4px;border-left:2px solid var(--accent)">
          ${renderMd(preview)}${output.length > 600 ? '<p style="color:var(--muted)">…</p>' : ''}
        </div>
      </details>`;
  }).filter(Boolean).join('');

  el.innerHTML = `
    <div style="padding:0.5rem 0.75rem">
      <div style="font-size:0.72rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;
                  color:var(--muted);margin-bottom:0.4rem">
        ✓ Pipeline Complete
      </div>
      ${nodeOutputs}
      ${files.length > 0 ? `
        <div style="margin-top:0.5rem;padding-top:0.4rem;border-top:1px solid var(--border)">
          <div style="font-size:0.65rem;font-weight:600;color:var(--muted);margin-bottom:0.25rem">SAVED FILES</div>
          ${files.map(f => `
            <div style="display:flex;align-items:center;gap:0.35rem;font-size:0.71rem;padding:0.15rem 0" title="${_esc(f.path)}">
              📄 <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(f.name)}</span>
              <span style="color:var(--muted)">${(f.size/1024).toFixed(1)}k</span>
            </div>`).join('')}
          <div style="font-size:0.63rem;color:var(--muted);margin-top:0.3rem">📁 ${_esc(directory)}</div>
        </div>` : ''}
      ${savedNote}
    </div>
  `;
}

async function _openRunById(runId) {
  if (!runId || !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(String(runId))) {
    return; // not a valid UUID — skip silently
  }
  try {
    const run = await api.graphWorkflows.getRun(runId);
    _currentRunId = runId;
    _runStartTime = run.started_at ? new Date(run.started_at) : new Date();

    // Find matching workflow to get node order
    if (run.workflow_id && (!_currentWf || _currentWf.id !== run.workflow_id)) {
      try {
        _currentWf = await api.graphWorkflows.get(run.workflow_id);
        _showWorkflow(_currentWf);
      } catch (_) {}
    }

    const wfName = run.workflow_name === '_work_item_pipeline' ? 'Work Item Pipeline'
                 : (run.workflow_name || _currentWf?.name || 'Pipeline');
    _openRunPanel(wfName, _currentWf?.nodes || []);

    // Restore timer: live for running, static for completed
    if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null; }
    const timerEl = document.getElementById('gw-rp-timer');
    if (run.status === 'running') {
      // Client-side live timer from actual start
      _timerInterval = setInterval(() => {
        const t = document.getElementById('gw-rp-timer');
        if (t && _runStartTime) t.textContent = _fmtDurMs(Date.now() - _runStartTime.getTime());
      }, 1000);
    } else if (timerEl && run.started_at) {
      timerEl.textContent = _fmtDurIso(run.started_at, run.finished_at);
    }

    _updateRunPanel(run);

    if (run.status === 'done') {
      _onRunComplete(run);
    } else if (run.status === 'running' || run.status === 'waiting_approval') {
      _pollRun(runId);
    }
  } catch (e) {
    toast(`Could not load run: ${e.message}`, 'error');
  }
}

function _showApprovalPanel(run) {
  const wrap = document.getElementById('gw-approval-wrap');
  if (!wrap) return;

  // Reset chat history and approval state for this gate
  _approvalChatHistory = [];
  _approvalBaselineOutput = run.context?._waiting?.output || '';
  _approvalEditMode = false;
  _currentApprovalNodeName = run.context?._waiting?.node_name || null;

  const waiting = run.context?._waiting || {};
  const nextLabel = waiting.next_node ? ` → ${_esc(waiting.next_node)}` : '';

  // Expand wrap to fill remaining run-panel space; hide timeline while approval is shown
  wrap.style.cssText = 'display:flex;flex-direction:column;flex:1;min-height:0;overflow:hidden;padding:0.5rem 0.75rem;';
  const timelineWrap = document.getElementById('gw-rp-timeline')?.parentElement;
  if (timelineWrap) timelineWrap.style.display = 'none';

  wrap.innerHTML = `
    <!-- header row: title + action buttons -->
    <div style="display:flex;align-items:center;gap:0.6rem;flex-shrink:0;margin-bottom:0.3rem">
      <span style="font-size:0.82rem;font-weight:700;flex:1">
        ⏸ ${_esc(waiting.node_name || 'Node')}${nextLabel}
      </span>
      <button class="btn btn-primary btn-sm" onclick="window._gwDecide(true,false)">✓ Approve</button>
      <button class="btn btn-ghost btn-sm" onclick="window._gwDecide(true,true)">↩ Retry</button>
      <button class="btn btn-ghost btn-sm" style="color:var(--red)" onclick="window._gwDecide(false,false)">✕ Stop</button>
    </div>
    <div style="font-size:0.71rem;color:var(--muted);flex-shrink:0;margin-bottom:0.4rem">
      ${_esc(waiting.approval_msg || 'Review output and approve or reject.')}
    </div>
    <!-- 2-pane: current output (left) + chat (right) -->
    <div style="display:flex;flex:1;gap:0.75rem;min-height:0;overflow:hidden">
      <!-- Left: current output (updates after each chat reply) -->
      <div style="flex:1;display:flex;flex-direction:column;min-width:0">
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;
                    color:var(--muted);margin-bottom:0.25rem;flex-shrink:0;display:flex;align-items:center;gap:0.5rem">
          Current Output
          <button id="gw-ap-edit-toggle" onclick="window._gwToggleEditMode()"
            style="font-size:0.6rem;padding:0.1rem 0.4rem;background:var(--surface2);border:1px solid var(--border);
                   border-radius:3px;cursor:pointer;color:var(--text2,var(--muted));font-family:var(--font)">
            ✏ Edit
          </button>
          <span id="gw-ap-processing" style="display:none;font-size:0.65rem;color:#f5a623">⟳ Processing…</span>
        </div>
        <div id="gw-ap-output" class="md-prose" data-raw-content="${_esc(waiting.output || '')}"
             style="flex:1;overflow-y:auto;background:var(--bg2);border-radius:5px;
             padding:0.5rem 0.65rem;font-size:0.72rem;line-height:1.55;
             border:1px solid var(--border)">${renderMd(waiting.output || '*(no output)*')}</div>
      </div>
      <!-- Right: chat pane -->
      <div style="width:320px;flex-shrink:0;display:flex;flex-direction:column;min-height:0">
        <div style="font-size:0.62rem;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;
                    color:var(--muted);margin-bottom:0.25rem;flex-shrink:0">Refine with Chat</div>
        <div id="gw-ap-msgs" style="flex:1;overflow-y:auto;display:flex;flex-direction:column;
             gap:0.35rem;padding:0.4rem;background:var(--bg2);
             border:1px solid var(--border);border-bottom:none;border-radius:5px 5px 0 0;min-height:60px">
          <div id="gw-ap-hint" style="font-size:0.72rem;color:var(--muted);text-align:center;padding:0.5rem 0;margin:auto 0">
            Ask the agent to change anything. Once satisfied, click Approve.
          </div>
        </div>
        <div style="display:flex;gap:0.35rem;flex-shrink:0;border:1px solid var(--border);
                    border-radius:0 0 5px 5px;padding:0.35rem;background:var(--bg2)">
          <textarea id="gw-ap-input" placeholder="Request changes… (Ctrl+Enter to send)" rows="2"
            style="flex:1;resize:none;padding:0.35rem 0.45rem;border:1px solid var(--border);
                   border-radius:4px;background:var(--bg1);color:var(--fg);font-size:0.78rem;
                   font-family:inherit;line-height:1.4;min-height:48px;max-height:100px"></textarea>
          <button id="gw-ap-send" class="btn btn-primary btn-sm"
            style="align-self:flex-end;padding:0.3rem 0.65rem;font-size:0.75rem"
            onclick="window._gwApprovalSend()">Send</button>
        </div>
      </div>
    </div>
  `;

  // Ctrl/Cmd+Enter shortcut
  const inp = document.getElementById('gw-ap-input');
  if (inp) {
    inp.addEventListener('keydown', e => {
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); window._gwApprovalSend(); }
    });
    setTimeout(() => inp.focus(), 80);
  }

  window._gwDecide = async (approved, retry) => {
    try {
      await api.graphWorkflows.decide(_currentRunId, { approved, retry });
      // Restore timeline
      const tl = document.getElementById('gw-rp-timeline')?.parentElement;
      if (tl) tl.style.display = '';
      wrap.innerHTML = '';
      wrap.style.cssText = 'display:none;padding:0.5rem 0.75rem 0;flex-shrink:0';
      _approvalChatHistory = [];
      _pollRun(_currentRunId);
    } catch (e) {
      toast(`Decision failed: ${e.message}`, 'error');
    }
  };

  window._gwApprovalSend = async () => {
    const input = document.getElementById('gw-ap-input');
    const msg = input?.value?.trim();
    if (!msg || !_currentRunId) return;

    input.value = '';
    input.disabled = true;
    const sendBtn = document.getElementById('gw-ap-send');
    if (sendBtn) sendBtn.disabled = true;
    const processingEl = document.getElementById('gw-ap-processing');
    if (processingEl) processingEl.style.display = '';

    const priorHistory = [..._approvalChatHistory];
    _approvalChatHistory.push({ role: 'user', content: msg });
    _renderApprovalMessages();

    try {
      const { reply } = await api.graphWorkflows.approvalChat(_currentRunId, {
        message: msg,
        history: priorHistory,
      });
      _approvalChatHistory.push({ role: 'assistant', content: reply });
      _renderApprovalMessages();
      // Update the output pane with the latest full document, showing diff vs baseline
      const outEl = document.getElementById('gw-ap-output');
      if (outEl && outEl.tagName !== 'TEXTAREA') {
        outEl.dataset.rawContent = reply;
        outEl.innerHTML = _renderApprovalDiff(_approvalBaselineOutput, reply);
      } else if (outEl?.tagName === 'TEXTAREA') {
        outEl.value = reply;
      }
      // Keep _approvalBaselineOutput as the original — so all changes remain highlighted
    } catch (e) {
      toast(`Chat failed: ${e.message}`, 'error');
      _approvalChatHistory.pop();
      _renderApprovalMessages();
    } finally {
      if (input) input.disabled = false;
      if (sendBtn) sendBtn.disabled = false;
      if (processingEl) processingEl.style.display = 'none';
      if (input) input.focus();
    }
  };
}

function _renderApprovalDiff(baseline, current) {
  if (!baseline || baseline === current) return renderMd(current);

  // Simple line-level diff: highlight lines in current that are not in baseline
  const baseLines = baseline.split('\n');
  const currLines = current.split('\n');
  const baseSet = new Set(baseLines);

  let html = '';
  for (const line of currLines) {
    if (!baseSet.has(line) && line.trim()) {
      // New or changed line — highlight with green left border
      html += `<div style="background:rgba(62,207,142,0.15);display:block;border-left:3px solid #3ecf8e;padding-left:0.4rem;margin:1px 0">${renderMd(line)}</div>`;
    } else {
      html += renderMd(line + '\n');
    }
  }
  return html || renderMd(current);
}

window._gwToggleEditMode = () => {
  const outEl = document.getElementById('gw-ap-output');
  const toggle = document.getElementById('gw-ap-edit-toggle');
  if (!outEl) return;
  _approvalEditMode = !_approvalEditMode;
  if (_approvalEditMode) {
    // Get raw markdown from data attribute or use baseline
    const rawMd = outEl.dataset.rawContent || _approvalBaselineOutput;
    const ta = document.createElement('textarea');
    ta.id = 'gw-ap-output';
    ta.value = rawMd;
    ta.style.cssText = 'flex:1;overflow-y:auto;background:var(--bg2);border-radius:5px;padding:0.5rem 0.65rem;font-size:0.72rem;line-height:1.55;resize:none;border:2px solid var(--accent);color:var(--fg);font-family:var(--font-mono,"Menlo",monospace);width:100%;box-sizing:border-box;min-height:200px';
    outEl.replaceWith(ta);
    if (toggle) toggle.textContent = '👁 Preview';
  } else {
    const ta = document.getElementById('gw-ap-output');
    const content = ta?.value || '';
    const div = document.createElement('div');
    div.id = 'gw-ap-output';
    div.className = 'md-prose';
    div.dataset.rawContent = content;
    div.style.cssText = 'flex:1;overflow-y:auto;background:var(--bg2);border-radius:5px;padding:0.5rem 0.65rem;font-size:0.72rem;line-height:1.55;border:1px solid var(--border)';
    div.innerHTML = _renderApprovalDiff(_approvalBaselineOutput, content);
    ta?.replaceWith(div);
    if (toggle) toggle.textContent = '✏ Edit';
    // Save the edited content back through approval chat if changed
    if (content !== _approvalBaselineOutput && _currentRunId) {
      api.graphWorkflows.approvalChat(_currentRunId, {
        message: `Please use exactly this revised content as the new output (direct edit by user):\n\n${content}`,
        history: [],
      }).then(r => {
        _approvalChatHistory.push({ role: 'user', content: '(direct edit)' });
        _approvalChatHistory.push({ role: 'assistant', content: r.reply });
        _renderApprovalMessages();
        // Update output pane with diff vs original baseline
        const outUpdated = document.getElementById('gw-ap-output');
        if (outUpdated && outUpdated.tagName !== 'TEXTAREA') {
          outUpdated.dataset.rawContent = r.reply;
          outUpdated.innerHTML = _renderApprovalDiff(_approvalBaselineOutput, r.reply);
        }
      }).catch(() => {});
    }
  }
};

function _renderApprovalMessages() {
  const el = document.getElementById('gw-ap-msgs');
  if (!el) return;

  const hint = document.getElementById('gw-ap-hint');

  if (!_approvalChatHistory.length) {
    if (hint) hint.style.display = '';
    el.querySelectorAll('.gw-ap-msg').forEach(m => m.remove());
    return;
  }
  if (hint) hint.style.display = 'none';

  // Rebuild message list (keep hint element in DOM, replace message divs)
  el.querySelectorAll('.gw-ap-msg').forEach(m => m.remove());

  for (const m of _approvalChatHistory) {
    const isUser = m.role === 'user';
    const preview = m.content.length > 400 ? m.content.slice(0, 400) + '…' : m.content;
    const div = document.createElement('div');
    div.className = 'gw-ap-msg';
    div.style.cssText = `display:flex;flex-direction:column;align-items:${isUser ? 'flex-end' : 'flex-start'}`;
    div.innerHTML = `
      <div style="max-width:92%;padding:0.3rem 0.5rem;border-radius:7px;font-size:0.71rem;
           line-height:1.45;word-break:break-word;white-space:pre-wrap;
           background:${isUser ? 'rgba(100,108,255,0.18)' : 'var(--bg1)'};
           border:1px solid ${isUser ? 'rgba(100,108,255,0.35)' : 'var(--border)'}">
        ${_esc(preview)}
      </div>
      <div style="font-size:0.6rem;color:var(--muted);margin-top:0.1rem;padding:0 0.2rem">
        ${isUser ? 'you' : 'agent'}
      </div>`;
    el.appendChild(div);
  }
  el.scrollTop = el.scrollHeight;
}

async function _cancelRun() {
  if (!_currentRunId) return;
  try {
    await api.graphWorkflows.cancelRun(_currentRunId);
    if (_pollInterval)  { clearInterval(_pollInterval);  _pollInterval  = null; }
    if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null; }
    const dot = document.getElementById('gw-rp-dot');
    const st  = document.getElementById('gw-rp-status');
    const stop = document.getElementById('gw-rp-stop');
    if (dot)  dot.className = 'gw-rp-status-dot cancelled';
    if (st)   { st.textContent = 'cancelled'; st.style.color = '#888'; }
    if (stop) stop.style.display = 'none';
    _listCache = null;
    _refreshListInBackground(); // refresh run history
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

// ── Cleanup ───────────────────────────────────────────────────────────────────

/**
 * Stop all running intervals owned by this module.
 * Must be called by the router (navigateTo) before switching away from this view
 * to prevent orphaned setInterval handles from continuing to fire.
 */
export function destroyGraphWorkflow() {
  if (_pollInterval)  { clearInterval(_pollInterval);  _pollInterval  = null; }
  if (_timerInterval) { clearInterval(_timerInterval); _timerInterval = null; }
}

// ── ReAct Pipeline Runner ─────────────────────────────────────────────────────
// Renders a modal / full-screen overlay for running YAML-defined ReAct pipelines
// (PM → Architect → Developer → Reviewer).  Accessible via the ▶ Run Pipeline button.

let _reactPipelines = [];   // loaded once per session from GET /agents/pipelines

/** Open the ReAct pipeline runner overlay. */
export async function openReActRunner(container) {
  // Build overlay if not already present
  let overlay = document.getElementById('react-runner-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'react-runner-overlay';
    overlay.style.cssText = `
      position:fixed;inset:0;z-index:2000;background:rgba(0,0,0,0.65);
      display:flex;align-items:flex-start;justify-content:center;
      padding:3rem 1rem;overflow-y:auto;
    `;
    overlay.innerHTML = `
      <div style="background:var(--bg);border:1px solid var(--border);border-radius:10px;
                  width:100%;max-width:820px;display:flex;flex-direction:column;gap:0">
        <!-- Header -->
        <div style="display:flex;align-items:center;justify-content:space-between;
                    padding:1rem 1.25rem;border-bottom:1px solid var(--border)">
          <div style="font-weight:700;font-size:1rem;letter-spacing:0.01em">
            ▶ Run ReAct Pipeline
          </div>
          <button id="rr-close" style="background:none;border:none;cursor:pointer;
            color:var(--muted);font-size:1.2rem;padding:0.2rem 0.5rem">✕</button>
        </div>

        <!-- Pipeline selector + task input -->
        <div style="padding:1.25rem;display:flex;flex-direction:column;gap:1rem">
          <div style="display:flex;gap:0.75rem;align-items:flex-end">
            <div style="flex:0 0 200px">
              <label style="font-size:0.75rem;color:var(--muted);display:block;margin-bottom:0.35rem">Pipeline</label>
              <select id="rr-pipeline-select" style="width:100%;background:var(--bg-2);
                border:1px solid var(--border);border-radius:5px;padding:0.4rem 0.6rem;
                color:var(--fg);font-size:0.85rem">
                <option value="">Loading…</option>
              </select>
            </div>
            <div style="flex:1">
              <label style="font-size:0.75rem;color:var(--muted);display:block;margin-bottom:0.35rem">Task</label>
              <input id="rr-task-input" type="text" placeholder="Describe what the pipeline should do…"
                style="width:100%;box-sizing:border-box;background:var(--bg-2);
                  border:1px solid var(--border);border-radius:5px;padding:0.4rem 0.7rem;
                  color:var(--fg);font-size:0.85rem" />
            </div>
            <button id="rr-run-btn" style="padding:0.4rem 1.1rem;background:var(--accent);
              color:#fff;border:none;border-radius:5px;cursor:pointer;font-size:0.85rem;
              white-space:nowrap">▶ Run</button>
          </div>
          <div id="rr-pipeline-desc" style="font-size:0.78rem;color:var(--muted);min-height:1em"></div>
        </div>

        <!-- Results area -->
        <div id="rr-results" style="border-top:1px solid var(--border);display:none;
          padding:0;max-height:60vh;overflow-y:auto"></div>
      </div>
    `;
    document.body.appendChild(overlay);

    document.getElementById('rr-close').onclick = () => overlay.remove();
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });
    document.getElementById('rr-run-btn').onclick = _rrRun;

    // Load pipelines
    try {
      _reactPipelines = await api.agents.listPipelines();
    } catch (_) { _reactPipelines = []; }

    const sel = document.getElementById('rr-pipeline-select');
    sel.innerHTML = _reactPipelines.length
      ? _reactPipelines.map(p =>
          `<option value="${p.name}">${p.name} — ${(p.stages || []).map(s => s.role).join(' → ')}</option>`
        ).join('')
      : '<option value="">No pipelines found</option>';
    sel.onchange = _rrUpdateDesc;
    _rrUpdateDesc();
  } else {
    overlay.style.display = 'flex';
  }
}

function _rrUpdateDesc() {
  const sel   = document.getElementById('rr-pipeline-select');
  const desc  = document.getElementById('rr-pipeline-desc');
  const found = _reactPipelines.find(p => p.name === sel?.value);
  if (found) {
    desc.textContent = found.description
      || `${(found.stages || []).length} stages · max ${found.max_rejection_retries ?? 2} rejection retries`;
  } else {
    desc.textContent = '';
  }
}

async function _rrRun() {
  const pipeline = document.getElementById('rr-pipeline-select')?.value;
  const task     = document.getElementById('rr-task-input')?.value?.trim();
  const btn      = document.getElementById('rr-run-btn');
  const results  = document.getElementById('rr-results');

  if (!pipeline || !task) {
    alert('Select a pipeline and enter a task description.');
    return;
  }

  btn.disabled = true;
  btn.textContent = '⏳ Running…';
  results.style.display = 'block';
  results.innerHTML = `
    <div style="padding:1.25rem;color:var(--muted);font-size:0.85rem;text-align:center">
      Running pipeline — this may take a few minutes…
    </div>`;

  try {
    const result = await api.agents.runPipeline({
      pipeline,
      task,
      project: _project || 'aicli',
    });
    _rrRenderResult(result);
  } catch (err) {
    results.innerHTML = `
      <div style="padding:1.25rem;color:#e85d75;font-size:0.85rem">
        ✗ Pipeline failed: ${err.message}
      </div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = '▶ Run';
  }
}

function _rrRenderResult(result) {
  const results = document.getElementById('rr-results');
  const verdict = result.final_verdict || 'unknown';
  const verdictColor = verdict === 'approved' ? '#3ecf8e'
    : verdict === 'rejected' ? '#e85d75'
    : verdict === 'error'    ? '#e85d75'
    : '#f5a623';

  const stagesHtml = Object.entries(result.stage_details || {}).map(([key, stage]) => {
    const stepsHtml = (stage.steps || []).map(step => `
      <div style="margin-bottom:0.6rem">
        <div style="font-size:0.75rem;font-weight:600;color:var(--muted)">Step ${step.step}</div>
        ${step.thought ? `<div style="font-size:0.8rem;color:var(--fg);opacity:0.9;margin-top:0.2rem">
          <span style="color:#9b7ef8;font-weight:600">Thought:</span> ${_esc(step.thought)}</div>` : ''}
        ${step.action  ? `<div style="font-size:0.8rem;margin-top:0.15rem">
          <span style="color:#5b8ef0;font-weight:600">Action:</span>
          <code style="background:var(--bg-2);padding:0.1rem 0.3rem;border-radius:3px;font-size:0.78rem">${_esc(step.action)}</code>
          ${step.args ? `<span style="color:var(--muted);font-size:0.75rem"> ${JSON.stringify(step.args)}</span>` : ''}
          </div>` : ''}
        ${step.observation ? `<div style="font-size:0.78rem;color:var(--muted);margin-top:0.15rem;
          max-height:4em;overflow:hidden;text-overflow:ellipsis">
          <span style="color:#3ecf8e;font-weight:600">Obs:</span> ${_esc(step.observation.slice(0, 300))}
          </div>` : ''}
        ${step.guard_fired ? `<div style="font-size:0.72rem;color:#f5a623">⚠ Hallucination guard fired</div>` : ''}
      </div>
    `).join('');

    const collapsed = stage.steps?.length > 3;
    const stepsId = `rr-steps-${key}`;
    return `
      <div style="border-bottom:1px solid var(--border)">
        <div style="padding:0.75rem 1.25rem;display:flex;align-items:center;gap:0.75rem;
          cursor:pointer;user-select:none" onclick="
            const el=document.getElementById('${stepsId}');
            el.style.display=el.style.display==='none'?'block':'none'">
          <span style="font-weight:600;font-size:0.85rem">${_esc(stage.role)}</span>
          <span style="font-size:0.75rem;color:var(--muted)">${key}</span>
          ${stage.attempt > 1 ? `<span style="font-size:0.72rem;color:#f5a623">retry #${stage.attempt}</span>` : ''}
          <span style="font-size:0.75rem;color:${stage.status === 'done' ? '#3ecf8e' : '#e85d75'};margin-left:auto">
            ${stage.status} · ${stage.steps?.length ?? 0} steps
          </span>
          <span style="font-size:0.75rem;color:var(--muted)">${collapsed ? '▼ expand' : '▲'}</span>
        </div>
        <div id="${stepsId}" style="display:${collapsed ? 'none' : 'block'};
          padding:0 1.25rem 0.75rem;border-top:1px solid var(--border);background:var(--bg-2)">
          ${stepsHtml || '<div style="color:var(--muted);font-size:0.8rem">No steps recorded.</div>'}
        </div>
      </div>
    `;
  }).join('');

  results.innerHTML = `
    <!-- Summary bar -->
    <div style="padding:0.75rem 1.25rem;background:var(--bg-2);display:flex;
      align-items:center;gap:1rem;flex-wrap:wrap;border-bottom:1px solid var(--border)">
      <span style="font-weight:700;color:${verdictColor};font-size:0.9rem">
        ${verdict.toUpperCase()}
      </span>
      <span style="color:var(--muted);font-size:0.8rem">${result.total_stages ?? 0} stages</span>
      <span style="color:var(--muted);font-size:0.8rem">${result.total_steps ?? 0} steps</span>
      <span style="color:var(--muted);font-size:0.8rem">$${(result.total_cost_usd ?? 0).toFixed(4)}</span>
      <span style="color:var(--muted);font-size:0.8rem">${(result.duration_s ?? 0).toFixed(1)}s</span>
    </div>
    <!-- Stage traces -->
    ${stagesHtml}
    <!-- Structured output of last stage -->
    ${result.last_handoff ? `
      <div style="padding:0.75rem 1.25rem;border-top:1px solid var(--border)">
        <div style="font-size:0.75rem;color:var(--muted);margin-bottom:0.4rem">Final structured output</div>
        <pre style="font-size:0.75rem;background:var(--bg-2);border-radius:5px;
          padding:0.6rem;overflow:auto;max-height:12rem;margin:0">${_esc(JSON.stringify(result.last_handoff, null, 2))}</pre>
      </div>` : ''}
  `;
}

