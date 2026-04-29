/**
 * pipeline.js — Pipeline & Role Execution (Dashboard tab)
 *
 * Single-column layout, always visible:
 *   1. Run form   — type (Pipeline | Role), selector, task, Run button
 *   2. Configure  — pipeline properties + stage table (collapsible)
 *   3. Progress   — stage dots + live log (appears when running)
 *   4. History    — last N runs (collapsible, show 10/20/50)
 */

import { api } from '../utils/api.js';

// ── Module state ──────────────────────────────────────────────────────────────

let _project     = null;
let _runType     = 'pipeline';   // 'pipeline' | 'role'
let _pipelines   = [];           // list from api.agentRoles.pipelinesConfig
let _roles       = [];           // list from api.agentRoles.list
let _selPipeline = null;         // full config object (from getPipelineConfig)
let _selRole     = null;         // role object
let _runId       = null;
let _pollTimer   = null;
let _histLimit   = 10;
let _configOpen  = false;
let _histOpen    = true;

export function destroyPipeline() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
}

// ── Entry ─────────────────────────────────────────────────────────────────────

export async function renderPipeline(container, project) {
  destroyPipeline();
  _project     = project;
  _runId       = null;
  _selPipeline = null;
  _selRole     = null;
  _configOpen  = false;
  _histOpen    = true;

  container.innerHTML = `
    <div id="pl-root" style="
      padding:1.25rem 1.5rem 2rem;
      max-width:860px;
      margin:0 auto;
      overflow-y:auto;
      height:100%;
      box-sizing:border-box">

      <!-- ① Run form -->
      <div id="pl-form" style="
        background:var(--surface2);
        border:1px solid var(--border);
        border-radius:var(--radius,6px);
        padding:1rem 1.1rem 0.85rem;
        margin-bottom:0.9rem">
        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.07em;color:var(--muted);margin-bottom:0.7rem">
          New Run
        </div>

        <!-- Run type tabs -->
        <div style="display:flex;gap:0;margin-bottom:0.85rem;
                    border:1px solid var(--border);border-radius:5px;width:fit-content;overflow:hidden">
          <button id="pl-tab-pipeline" onclick="window._plSetType('pipeline')"
            style="padding:0.3rem 0.85rem;font-size:0.78rem;border:none;cursor:pointer;
                   background:var(--accent);color:#fff">
            Pipeline
          </button>
          <button id="pl-tab-role" onclick="window._plSetType('role')"
            style="padding:0.3rem 0.85rem;font-size:0.78rem;border:none;cursor:pointer;
                   background:transparent;color:var(--muted)">
            Single Role
          </button>
        </div>

        <!-- Pipeline row -->
        <div id="pl-pipeline-row" style="display:flex;gap:0.75rem;align-items:flex-start;margin-bottom:0.7rem;flex-wrap:wrap">
          <div style="flex:0 0 220px">
            <label style="font-size:0.72rem;color:var(--muted);display:block;margin-bottom:0.25rem">Pipeline</label>
            <select id="pl-pipeline-sel"
              style="width:100%;background:var(--surface);border:1px solid var(--border);
                     border-radius:4px;padding:0.3rem 0.5rem;color:var(--text);font-size:0.82rem">
              <option value="">— loading —</option>
            </select>
          </div>
          <div id="pl-pipeline-meta" style="padding-top:1.3rem;font-size:0.75rem;color:var(--muted);flex:1;min-width:0"></div>
        </div>

        <!-- Role row (hidden by default) -->
        <div id="pl-role-row" style="display:none;gap:0.75rem;align-items:flex-start;margin-bottom:0.7rem;flex-wrap:wrap">
          <div style="flex:0 0 220px">
            <label style="font-size:0.72rem;color:var(--muted);display:block;margin-bottom:0.25rem">Role</label>
            <select id="pl-role-sel"
              style="width:100%;background:var(--surface);border:1px solid var(--border);
                     border-radius:4px;padding:0.3rem 0.5rem;color:var(--text);font-size:0.82rem">
              <option value="">— loading —</option>
            </select>
          </div>
          <div id="pl-role-meta" style="padding-top:1.3rem;font-size:0.75rem;color:var(--muted);flex:1;min-width:0"></div>
        </div>

        <!-- Task textarea -->
        <div style="margin-bottom:0.7rem">
          <label style="font-size:0.72rem;color:var(--muted);display:block;margin-bottom:0.25rem">Task</label>
          <textarea id="pl-task" rows="3"
            placeholder="Describe what you want the agent to do…"
            style="width:100%;box-sizing:border-box;background:var(--surface);
                   border:1px solid var(--border);border-radius:4px;padding:0.4rem 0.5rem;
                   color:var(--text);font-size:0.82rem;resize:vertical;font-family:inherit">
          </textarea>
        </div>

        <!-- Buttons -->
        <div style="display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap">
          <button id="pl-run-btn" class="btn btn-primary btn-sm"
            style="font-size:0.82rem;padding:0.35rem 1rem">
            ▶ Run Pipeline
          </button>
          <button id="pl-cancel-btn" class="btn btn-ghost btn-sm"
            style="font-size:0.82rem;display:none">
            ■ Cancel
          </button>
          <span id="pl-run-err" style="font-size:0.75rem;color:#e74c3c"></span>
        </div>
      </div>

      <!-- ② Configure (collapsible) -->
      <div id="pl-configure" style="
        border:1px solid var(--border);border-radius:var(--radius,6px);
        margin-bottom:0.9rem;overflow:hidden">
        <div id="pl-configure-hdr" style="
          display:flex;align-items:center;gap:0.5rem;
          padding:0.55rem 1rem;cursor:pointer;user-select:none;
          background:var(--surface2);font-size:0.8rem;font-weight:600">
          <span id="pl-cfg-arrow">▸</span>
          <span id="pl-cfg-title">Configure</span>
          <span id="pl-cfg-badge" style="margin-left:auto;font-size:0.68rem;color:var(--muted)"></span>
        </div>
        <div id="pl-configure-body" style="display:none;padding:0.9rem 1rem 1rem"></div>
      </div>

      <!-- ③ Progress (hidden until run starts) -->
      <div id="pl-progress" style="
        display:none;border:1px solid var(--border);border-radius:var(--radius,6px);
        padding:0.9rem 1rem 1rem;margin-bottom:0.9rem">
        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.07em;color:var(--muted);margin-bottom:0.6rem"
             id="pl-progress-title">Progress</div>
        <div id="pl-stage-dots"></div>
        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                    letter-spacing:0.07em;color:var(--muted);margin:0.6rem 0 0.3rem">Live Log</div>
        <div id="pl-log" style="
          font-family:monospace;font-size:0.7rem;line-height:1.5;
          background:var(--surface2);border:1px solid var(--border);
          border-radius:4px;padding:0.5rem;height:200px;overflow-y:auto;color:var(--text)">
        </div>
        <!-- Approval gate -->
        <div id="pl-approval" style="display:none;margin-top:0.75rem;
          border:2px solid #9b59b6;border-radius:6px;padding:0.75rem;
          background:rgba(155,89,182,0.06)">
          <div style="font-weight:600;color:#9b59b6;margin-bottom:0.35rem;font-size:0.82rem">
            Approval Required
          </div>
          <div id="pl-approval-msg" style="font-size:0.78rem;margin-bottom:0.4rem"></div>
          <div id="pl-approval-preview" style="font-family:monospace;font-size:0.7rem;
               background:var(--surface2);border-radius:4px;padding:0.4rem;
               max-height:100px;overflow-y:auto;margin-bottom:0.5rem;white-space:pre-wrap;word-break:break-word"></div>
          <textarea id="pl-approval-fb" rows="2" placeholder="Feedback (optional)…"
            style="width:100%;box-sizing:border-box;background:var(--surface2);border:1px solid var(--border);
                   border-radius:4px;padding:0.3rem;font-size:0.78rem;color:var(--text);resize:vertical;
                   margin-bottom:0.4rem;font-family:inherit"></textarea>
          <div style="display:flex;gap:0.5rem">
            <button id="pl-approve-btn" class="btn btn-primary btn-sm" style="font-size:0.78rem">✓ Approve</button>
            <button id="pl-reject-btn"  class="btn btn-ghost btn-sm"
                    style="font-size:0.78rem;color:#e74c3c;border-color:#e74c3c">✗ Reject</button>
          </div>
        </div>
      </div>

      <!-- ④ History -->
      <div id="pl-hist-wrap" style="border:1px solid var(--border);border-radius:var(--radius,6px);overflow:hidden">
        <div id="pl-hist-hdr" style="
          display:flex;align-items:center;gap:0.5rem;
          padding:0.55rem 1rem;cursor:pointer;user-select:none;
          background:var(--surface2);font-size:0.8rem;font-weight:600">
          <span id="pl-hist-arrow">▾</span>
          <span>History</span>
          <span style="margin-left:auto;display:flex;gap:0.25rem;align-items:center;font-size:0.72rem;color:var(--muted)">
            Show:
            <button class="btn btn-ghost" style="font-size:0.68rem;padding:0.05rem 0.3rem;min-height:0"
              onclick="event.stopPropagation();window._plHistLimit(10)">10</button>
            <button class="btn btn-ghost" style="font-size:0.68rem;padding:0.05rem 0.3rem;min-height:0"
              onclick="event.stopPropagation();window._plHistLimit(20)">20</button>
            <button class="btn btn-ghost" style="font-size:0.68rem;padding:0.05rem 0.3rem;min-height:0"
              onclick="event.stopPropagation();window._plHistLimit(50)">50</button>
          </span>
        </div>
        <div id="pl-hist-body" style="padding:0.75rem 1rem 1rem"></div>
      </div>
    </div>

    <style>
      #pl-root .pl-badge {
        font-size:0.6rem;padding:0.1rem 0.3rem;border-radius:3px;
        background:var(--surface3,rgba(128,128,128,.15));color:var(--muted)
      }
      #pl-root .pl-prop-row {
        display:flex;align-items:center;gap:0.75rem;padding:0.3rem 0;font-size:0.78rem
      }
      #pl-root .pl-prop-label { width:170px;flex-shrink:0;color:var(--muted);font-size:0.75rem }
      #pl-root .pl-dot {
        width:10px;height:10px;border-radius:50%;flex-shrink:0;border:2px solid var(--border)
      }
      #pl-root .pl-dot.done    { background:var(--green,#27ae60);border-color:var(--green,#27ae60) }
      #pl-root .pl-dot.running { background:var(--accent);border-color:var(--accent);animation:pl-pulse 1s infinite }
      #pl-root .pl-dot.error   { background:#e74c3c;border-color:#e74c3c }
      #pl-root .pl-dot.pending { background:transparent }
      @keyframes pl-pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
      #pl-root .pl-stage-grid {
        display:grid;grid-template-columns:100px 130px 170px 90px 1fr;
        gap:0.4rem;font-size:0.72rem;padding:0.3rem 0;border-bottom:1px solid var(--border);
        align-items:start
      }
      #pl-root .pl-stage-grid.hdr { font-weight:700;color:var(--muted) }
      #pl-root .pl-hist-row {
        display:grid;grid-template-columns:155px 65px 75px 65px 90px;
        gap:0.25rem;font-size:0.72rem;padding:0.3rem 0;border-bottom:1px solid var(--border)
      }
      #pl-root .pl-hist-row.hdr { font-weight:700;color:var(--muted) }
      #pl-root .pl-stars span { cursor:pointer;font-size:0.95rem }
      #pl-root .log-error { color:#e74c3c }
      #pl-root .log-warn  { color:#f39c12 }
    </style>
  `;

  // Wire up
  window._plSetType   = _setType;
  window._plHistLimit = (n) => { _histLimit = n; _loadHistory(); };

  document.getElementById('pl-configure-hdr').addEventListener('click', _toggleConfigure);
  document.getElementById('pl-hist-hdr').addEventListener('click', e => {
    if (e.target.tagName === 'BUTTON') return;
    _histOpen = !_histOpen;
    document.getElementById('pl-hist-body').style.display = _histOpen ? '' : 'none';
    document.getElementById('pl-hist-arrow').textContent  = _histOpen ? '▾' : '▸';
    if (_histOpen) _loadHistory();
  });
  document.getElementById('pl-run-btn').addEventListener('click', _startRun);
  document.getElementById('pl-cancel-btn').addEventListener('click', _cancelRun);
  document.getElementById('pl-approve-btn').addEventListener('click', () => _sendApproval(true));
  document.getElementById('pl-reject-btn').addEventListener('click',  () => _sendApproval(false));

  await Promise.all([_loadPipelines(), _loadRoles()]);
  _loadHistory();
}

// ── Data loading ──────────────────────────────────────────────────────────────

async function _loadPipelines() {
  try {
    const cfg = await api.agentRoles.pipelinesConfig(_project);
    _pipelines = (cfg.pipelines || []).filter(p => !p.error);
    const sel = document.getElementById('pl-pipeline-sel');
    if (!sel) return;
    if (!_pipelines.length) {
      sel.innerHTML = '<option value="">No activated pipelines</option>';
      return;
    }
    sel.innerHTML = _pipelines.map(p =>
      `<option value="${_esc(p.name)}">${_esc(p.name)}</option>`
    ).join('');
    sel.addEventListener('change', _onPipelineChange);
    _onPipelineChange();
  } catch (e) {
    const sel = document.getElementById('pl-pipeline-sel');
    if (sel) sel.innerHTML = `<option value="">Error: ${_esc(e.message)}</option>`;
  }
}

async function _loadRoles() {
  try {
    const data = await api.agentRoles.list(_project);
    _roles = (data || []).filter(r => r.activated !== false);
    const sel = document.getElementById('pl-role-sel');
    if (!sel) return;
    if (!_roles.length) {
      sel.innerHTML = '<option value="">No activated roles</option>';
      return;
    }
    sel.innerHTML = _roles.map(r =>
      `<option value="${_esc(r.name)}">${_esc(r.name)}</option>`
    ).join('');
    sel.addEventListener('change', _onRoleChange);
    _onRoleChange();
  } catch (e) {
    const sel = document.getElementById('pl-role-sel');
    if (sel) sel.innerHTML = `<option value="">Error: ${_esc(e.message)}</option>`;
  }
}

// ── Type selector ─────────────────────────────────────────────────────────────

function _setType(type) {
  _runType = type;
  const isPipeline = type === 'pipeline';

  document.getElementById('pl-pipeline-row').style.display = isPipeline ? 'flex' : 'none';
  document.getElementById('pl-role-row').style.display     = isPipeline ? 'none' : 'flex';

  const tabPl = document.getElementById('pl-tab-pipeline');
  const tabRo = document.getElementById('pl-tab-role');
  tabPl.style.background = isPipeline ? 'var(--accent)' : 'transparent';
  tabPl.style.color      = isPipeline ? '#fff' : 'var(--muted)';
  tabRo.style.background = isPipeline ? 'transparent' : 'var(--accent)';
  tabRo.style.color      = isPipeline ? 'var(--muted)' : '#fff';

  document.getElementById('pl-run-btn').textContent = isPipeline ? '▶ Run Pipeline' : '▶ Run Role';

  // Update configure panel
  if (isPipeline) {
    _onPipelineChange();
  } else {
    _onRoleChange();
    // Hide configure for role
    document.getElementById('pl-configure-body').style.display = 'none';
    document.getElementById('pl-cfg-arrow').textContent = '▸';
    document.getElementById('pl-cfg-title').textContent = 'Configure';
    document.getElementById('pl-cfg-badge').textContent = '';
    _configOpen = false;
  }
}

// ── Pipeline selection ────────────────────────────────────────────────────────

async function _onPipelineChange() {
  const sel  = document.getElementById('pl-pipeline-sel');
  const name = sel?.value;
  const meta = document.getElementById('pl-pipeline-meta');
  if (!name) return;

  const info = _pipelines.find(p => p.name === name);
  if (meta && info) {
    const roles = (info.required_roles || []).join(' → ');
    meta.innerHTML = `<span class="pl-badge">${(info.required_roles||[]).length} stages</span>
      <span style="margin-left:0.4rem">${_esc(roles)}</span>
      ${info.description ? `<div style="margin-top:0.2rem">${_esc(info.description.split('\n')[0])}</div>` : ''}`;
  }

  // Update configure badge
  document.getElementById('pl-cfg-title').textContent = `Configure · ${name}`;
  document.getElementById('pl-cfg-badge').textContent = '';

  // Load full config lazily when configure is open
  if (_configOpen) await _loadPipelineConfig(name);
}

async function _loadPipelineConfig(name) {
  const body = document.getElementById('pl-configure-body');
  if (!body) return;
  body.innerHTML = '<div style="color:var(--muted);font-size:0.78rem">Loading…</div>';
  try {
    _selPipeline = await api.agentRoles.getPipelineConfig(name, _project);
    _renderConfigure(_selPipeline);
  } catch (e) {
    body.innerHTML = `<div style="color:#e74c3c;font-size:0.78rem">Error: ${_esc(e.message)}</div>`;
  }
}

// ── Role selection ────────────────────────────────────────────────────────────

function _onRoleChange() {
  const sel  = document.getElementById('pl-role-sel');
  const name = sel?.value;
  const meta = document.getElementById('pl-role-meta');
  _selRole = _roles.find(r => r.name === name) || null;
  if (meta && _selRole) {
    const pm = [_selRole.provider, _selRole.model].filter(Boolean).join(' · ');
    const tmp = _selRole.temperature != null ? ` · temp ${_selRole.temperature}` : '';
    meta.textContent = pm + tmp;
  }
}

// ── Configure panel ───────────────────────────────────────────────────────────

async function _toggleConfigure() {
  if (_runType !== 'pipeline') return;
  _configOpen = !_configOpen;
  const body  = document.getElementById('pl-configure-body');
  const arrow = document.getElementById('pl-cfg-arrow');
  body.style.display = _configOpen ? '' : 'none';
  arrow.textContent  = _configOpen ? '▾' : '▸';

  if (_configOpen) {
    const name = document.getElementById('pl-pipeline-sel')?.value;
    if (name) await _loadPipelineConfig(name);
  }
}

function _renderConfigure(cfg) {
  const body = document.getElementById('pl-configure-body');
  if (!body) return;

  const stageKeys = (cfg.stages || []).map(s => s.key);
  const approvalOpts = ['<option value="">— none —</option>']
    .concat(stageKeys.map(k =>
      `<option value="${_esc(k)}" ${cfg.require_approval_after === k ? 'selected' : ''}>${_esc(k)}</option>`
    )).join('');

  body.innerHTML = `
    <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.06em;color:var(--muted);margin-bottom:0.5rem">Properties</div>

    <div class="pl-prop-row">
      <span class="pl-prop-label">Max rejection retries</span>
      <input id="cfg-retries" type="number" min="1" max="10" value="${cfg.max_rejection_retries ?? 2}"
        style="width:55px;background:var(--surface);border:1px solid var(--border);
               border-radius:4px;padding:0.2rem 0.35rem;color:var(--text);font-size:0.78rem">
      <span style="font-size:0.72rem;color:var(--muted)">reviewer rejections before pipeline stops</span>
    </div>
    <div class="pl-prop-row">
      <span class="pl-prop-label">Continue on failure</span>
      <label style="display:flex;align-items:center;gap:0.4rem;cursor:pointer">
        <input id="cfg-continue" type="checkbox" ${cfg.continue_on_failure ? 'checked' : ''}>
        <span style="font-size:0.78rem;color:var(--muted)">proceed to next stage if a stage errors</span>
      </label>
    </div>
    <div class="pl-prop-row">
      <span class="pl-prop-label">Save to memory</span>
      <label style="display:flex;align-items:center;gap:0.4rem;cursor:pointer">
        <input id="cfg-save-mem" type="checkbox" ${cfg.save_memory !== false ? 'checked' : ''}>
        <span style="font-size:0.78rem;color:var(--muted)">persist run output to project memory</span>
      </label>
    </div>
    <div class="pl-prop-row">
      <span class="pl-prop-label">Pause for approval after</span>
      <select id="cfg-approval"
        style="background:var(--surface);border:1px solid var(--border);border-radius:4px;
               padding:0.2rem 0.4rem;color:var(--text);font-size:0.78rem">
        ${approvalOpts}
      </select>
    </div>

    <div id="cfg-save-status" style="font-size:0.72rem;color:var(--muted);min-height:1rem;margin:0.2rem 0 0.75rem"></div>

    <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;
                letter-spacing:0.06em;color:var(--muted);margin-bottom:0.4rem">Stages</div>
    <div style="overflow-x:auto">
      <div class="pl-stage-grid hdr" style="padding-bottom:0.3rem">
        <span>Stage</span><span>Role</span><span>Provider · Model</span><span>Temperature</span><span>System Prompt</span>
      </div>
      ${(cfg.stages || []).map(_stageRow).join('') ||
        '<div style="color:var(--muted);font-size:0.75rem;padding:0.3rem 0">No stages</div>'}
    </div>
  `;

  // Auto-save on change
  const statusEl = document.getElementById('cfg-save-status');
  let saveTimer = null;
  const schedule = () => {
    statusEl.textContent = 'Unsaved…'; statusEl.style.color = 'var(--muted)';
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => _saveCfg(cfg.name, statusEl), 800);
  };
  ['cfg-retries','cfg-continue','cfg-save-mem','cfg-approval'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', schedule);
  });

  // System prompt expand toggles
  body.querySelectorAll('[data-sp]').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.sp;
      const prev = document.getElementById(`spp-${key}`);
      const full = document.getElementById(`spf-${key}`);
      if (!prev || !full) return;
      const open = full.style.display !== 'none';
      prev.style.display = open ? '' : 'none';
      full.style.display = open ? 'none' : '';
      btn.textContent    = open ? '▸' : '▾';
    });
  });
}

function _stageRow(s) {
  const pm   = [s.role_provider, s.role_model].filter(Boolean).join(' · ') || '—';
  const temp = s.role_temperature != null
    ? Number(s.role_temperature).toFixed(2)
    : (s.temperature_override != null ? `${s.temperature_override}↑` : '—');
  const sp     = (s.role_system_prompt || '').trim();
  const preview = _esc(sp.slice(0, 80).replace(/\n/g, ' ')) + (sp.length > 80 ? '…' : '');
  const key    = _esc(s.key);
  return `
    <div class="pl-stage-grid">
      <span style="font-family:monospace;font-weight:600">${_esc(s.key)}</span>
      <span>${_esc(s.role)}</span>
      <span style="font-family:monospace;font-size:0.7rem;color:var(--muted)">${_esc(pm)}</span>
      <span style="color:var(--muted)">${_esc(temp)}</span>
      <span style="font-size:0.7rem">
        ${sp ? `
          <span id="spp-${key}" style="color:var(--muted)">
            ${preview}
            <button data-sp="${key}" style="background:none;border:none;cursor:pointer;
              color:var(--accent);font-size:0.68rem;padding:0 0.15rem">▸</button>
          </span>
          <pre id="spf-${key}" style="display:none;margin:0.25rem 0 0;font-family:monospace;
            font-size:0.68rem;line-height:1.4;background:var(--surface2);border:1px solid var(--border);
            border-radius:3px;padding:0.4rem;white-space:pre-wrap;word-break:break-word;
            max-height:160px;overflow-y:auto">${_esc(sp)}</pre>
        ` : '<span style="color:var(--muted)">—</span>'}
      </span>
    </div>`;
}

async function _saveCfg(pipelineName, statusEl) {
  const body = {
    max_rejection_retries:  parseInt(document.getElementById('cfg-retries')?.value || '2', 10),
    continue_on_failure:    document.getElementById('cfg-continue')?.checked ?? false,
    save_memory:            document.getElementById('cfg-save-mem')?.checked ?? true,
    require_approval_after: document.getElementById('cfg-approval')?.value || null,
  };
  try {
    await api.agentRoles.patchPipeline(pipelineName, body, _project);
    statusEl.textContent = 'Saved'; statusEl.style.color = 'var(--green,#27ae60)';
    setTimeout(() => { statusEl.textContent = ''; statusEl.style.color = 'var(--muted)'; }, 2000);
  } catch (e) {
    statusEl.textContent = `Save error: ${e.message}`; statusEl.style.color = '#e74c3c';
  }
}

// ── Run execution ─────────────────────────────────────────────────────────────

async function _startRun() {
  const task = (document.getElementById('pl-task')?.value || '').trim();
  const errEl = document.getElementById('pl-run-err');
  if (!task) { errEl.textContent = 'Enter a task first.'; return; }
  errEl.textContent = '';

  document.getElementById('pl-run-btn').style.display    = 'none';
  document.getElementById('pl-cancel-btn').style.display = '';

  if (_runType === 'role') {
    await _startRoleRun(task);
  } else {
    await _startPipelineRun(task);
  }
}

async function _startPipelineRun(task) {
  const pipeline = document.getElementById('pl-pipeline-sel')?.value;
  if (!pipeline) {
    document.getElementById('pl-run-err').textContent = 'Select a pipeline first.';
    _resetRunUI(); return;
  }

  // Show progress
  document.getElementById('pl-progress').style.display = '';
  document.getElementById('pl-progress-title').textContent = `Running · ${pipeline}`;

  // Pre-fill stage dots from pipeline info
  const info = _pipelines.find(p => p.name === pipeline);
  const stageDefs = (info?.required_roles || []).map((r, i) => ({ key: `stage_${i}`, role: r }));
  _renderDots(stageDefs, []);
  _clearLog();

  try {
    const res = await api.agents.startPipelineRun({ pipeline, task, project: _project });
    _runId = res.run_id;
    _appendLog(`Run started: ${_runId}`);
    _startPolling();
  } catch (e) {
    document.getElementById('pl-run-err').textContent = `Error: ${e.message}`;
    _resetRunUI();
  }
}

async function _startRoleRun(task) {
  const roleName = document.getElementById('pl-role-sel')?.value;
  if (!roleName) {
    document.getElementById('pl-run-err').textContent = 'Select a role first.';
    _resetRunUI(); return;
  }

  document.getElementById('pl-progress').style.display = '';
  document.getElementById('pl-progress-title').textContent = `Running · ${roleName}`;
  document.getElementById('pl-stage-dots').innerHTML = '';
  _clearLog();
  _appendLog(`Running role: ${roleName}…`);

  try {
    const result = await api.agents.runAgent({ role: roleName, task, project: _project });
    _appendLog(`Status: ${result.status}`);
    _appendLog(`Cost: $${(result.cost_usd || 0).toFixed(4)} · Tokens: ${(result.input_tokens||0)+(result.output_tokens||0)}`);
    if (result.output) {
      _appendLog('--- Output ---');
      result.output.split('\n').slice(0, 30).forEach(l => _appendLog(l));
    }
    if (result.error) _appendLog(`Error: ${result.error}`, 'error');
    _resetRunUI(false);
    _loadHistory();
  } catch (e) {
    _appendLog(`Error: ${e.message}`, 'error');
    _resetRunUI(false);
  }
}

function _cancelRun() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
  _runId = null;
  _appendLog('Run cancelled by user.', 'warn');
  _resetRunUI(false);
}

function _startPolling() {
  if (_pollTimer) clearInterval(_pollTimer);
  _pollTimer = setInterval(async () => {
    if (!_runId) { clearInterval(_pollTimer); return; }
    try {
      const data = await api.agents.getPipelineRun(_runId);
      _updateProgress(data);
      const done = !['running','waiting_approval'].includes(data.status);
      if (done) {
        clearInterval(_pollTimer); _pollTimer = null;
        _onRunComplete(data);
      }
    } catch (e) { _appendLog(`Poll error: ${e.message}`, 'error'); }
  }, 1500);
}

function _updateProgress(data) {
  // Rebuild dots from actual stage rows
  _renderDots([], data.stages || []);

  // Stream new log lines
  const logEl = document.getElementById('pl-log');
  if (logEl) {
    for (const stage of (data.stages || [])) {
      for (const entry of (stage.log_lines || [])) {
        const key = `${stage.stage_key}:${entry.ts}`;
        if (!logEl._seen) logEl._seen = new Set();
        if (!logEl._seen.has(key)) {
          logEl._seen.add(key);
          _appendLog(`[${stage.stage_key}] ${entry.text}`, entry.level || 'info');
        }
      }
    }
  }

  // Approval gate
  const apEl = document.getElementById('pl-approval');
  if (data.status === 'waiting_approval') {
    apEl.style.display = '';
    const last = (data.stages || []).filter(s => s.status === 'done').at(-1);
    if (last) {
      document.getElementById('pl-approval-msg').textContent =
        `${last.stage_key} finished. Review before next stage continues.`;
      document.getElementById('pl-approval-preview').textContent = last.output_preview || '';
    }
  } else {
    apEl.style.display = 'none';
  }
}

function _onRunComplete(data) {
  const verdict = data.final_verdict || data.status;
  _appendLog(
    `Done · verdict: ${verdict} · cost $${(data.total_cost_usd||0).toFixed(4)} · ` +
    `${(data.total_input_tokens||0)+(data.total_output_tokens||0)} tokens`,
    data.status === 'error' ? 'error' : 'info',
  );
  document.getElementById('pl-progress-title').textContent =
    verdict === 'approved' ? '✓ Approved' :
    verdict === 'rejected' ? '✗ Rejected' :
    data.status === 'error' ? '✗ Error' : '✓ Done';
  _resetRunUI(false);
  _runId = null;
  _loadHistory();
}

function _resetRunUI(hideProgress = true) {
  document.getElementById('pl-run-btn').style.display    = '';
  document.getElementById('pl-cancel-btn').style.display = 'none';
  if (hideProgress) document.getElementById('pl-progress').style.display = 'none';
  document.getElementById('pl-approval').style.display = 'none';
}

async function _sendApproval(approved) {
  if (!_runId) return;
  const fb = document.getElementById('pl-approval-fb')?.value || '';
  try {
    await api.agents.approvePipelineRun(_runId, { approved, feedback: fb });
    document.getElementById('pl-approval').style.display = 'none';
  } catch (e) { _appendLog(`Approval error: ${e.message}`, 'error'); }
}

// ── Stage dots ────────────────────────────────────────────────────────────────

function _renderDots(defs, results) {
  const el = document.getElementById('pl-stage-dots');
  if (!el) return;

  // Build unified list — prefer results (have stage_key), fall back to defs
  const items = results.length ? results.map(r => ({
    key:      r.stage_key,
    role:     r.role_name || r.stage_key,
    status:   r.status || 'pending',
    dur:      r.duration_s,
    cost:     r.cost_usd,
    tok:      (r.input_tokens || 0) + (r.output_tokens || 0),
  })) : defs.map(d => ({ key: d.key, role: d.role, status: 'pending', dur: null, cost: null, tok: 0 }));

  el.innerHTML = `<div style="display:flex;flex-direction:column;gap:0.3rem;margin-bottom:0.6rem">` +
    items.map(s => {
      const dur  = s.dur  != null ? ` ${s.dur.toFixed(1)}s` : '';
      const cost = s.cost != null && s.cost > 0 ? ` $${Number(s.cost).toFixed(4)}` : '';
      const tok  = s.tok  > 0 ? ` ${_fmtNum(s.tok)} tok` : '';
      return `
        <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.78rem">
          <div class="pl-dot ${s.status}"></div>
          <span style="font-family:monospace;min-width:90px">${_esc(s.key)}</span>
          <span style="color:var(--muted);min-width:55px;font-size:0.7rem">[${_esc(s.status)}]</span>
          <span style="color:var(--muted);font-size:0.7rem">${_esc(s.role)}</span>
          ${dur  ? `<span style="color:var(--muted);font-size:0.68rem">${dur}</span>` : ''}
          ${cost ? `<span style="color:var(--accent);font-size:0.68rem">${cost}</span>` : ''}
          ${tok  ? `<span style="color:var(--muted);font-size:0.68rem">${tok}</span>` : ''}
        </div>`;
    }).join('') + '</div>';
}

// ── Log ───────────────────────────────────────────────────────────────────────

function _appendLog(text, level = 'info') {
  const el = document.getElementById('pl-log');
  if (!el) return;
  const ts  = new Date().toLocaleTimeString();
  const cls = level === 'error' ? 'log-error' : level === 'warn' ? 'log-warn' : '';
  el.insertAdjacentHTML('beforeend',
    `<div${cls ? ` class="${cls}"` : ''}>${ts} ${_esc(text)}</div>`);
  el.scrollTop = el.scrollHeight;
}

function _clearLog() {
  const el = document.getElementById('pl-log');
  if (el) { el.innerHTML = ''; el._seen = new Set(); }
}

// ── History ───────────────────────────────────────────────────────────────────

async function _loadHistory() {
  const el = document.getElementById('pl-hist-body');
  if (!el) return;

  const pipeline = _runType === 'pipeline' ? (document.getElementById('pl-pipeline-sel')?.value || null) : null;

  try {
    const data = await api.agents.listPipelineRuns(_project, pipeline, _histLimit);
    const runs = data.runs || [];
    if (!runs.length) {
      el.innerHTML = '<div style="color:var(--muted);font-size:0.78rem;padding:0.25rem 0">No runs yet for this pipeline.</div>';
      return;
    }
    el.innerHTML = `
      <div class="pl-hist-row hdr" style="padding-bottom:0.3rem">
        <span>Started</span><span>Duration</span><span>Tokens</span><span>Cost</span><span>Score</span>
      </div>
      ${runs.map(_histRow).join('')}
    `;
    el.querySelectorAll('.pl-stars span').forEach(star => {
      star.addEventListener('click', async () => {
        const row   = star.closest('[data-run-id]');
        const runId = row?.dataset.runId;
        if (!runId) return;
        try { await api.agents.scoreRun(runId, parseInt(star.dataset.s, 10)); _loadHistory(); }
        catch (_) {}
      });
    });
  } catch (e) {
    el.innerHTML = `<div style="color:#e74c3c;font-size:0.78rem">Error: ${e.message}</div>`;
  }
}

function _histRow(r) {
  const at   = r.started_at ? new Date(r.started_at).toLocaleString() : '—';
  const dur  = r.duration_s != null ? _fmtDur(r.duration_s) : '—';
  const tok  = (r.total_input_tokens||0) + (r.total_output_tokens||0);
  const cost = r.total_cost_usd != null ? `$${Number(r.total_cost_usd).toFixed(4)}` : '—';
  const sc   = r.score ?? null;
  const stars = [1,2,3,4,5].map(n =>
    `<span data-s="${n}" title="Rate ${n}"
      style="color:${sc != null && n <= sc ? '#f39c12' : 'var(--muted)'}">★</span>`
  ).join('');
  const vCol = r.final_verdict === 'approved' ? 'var(--green,#27ae60)'
    : r.final_verdict === 'rejected' ? '#e74c3c' : 'var(--muted)';

  return `
    <div class="pl-hist-row" data-run-id="${_esc(r.run_id)}">
      <span style="font-size:0.7rem;color:var(--muted)" title="${_esc(r.task||'')}">
        ${at}<br>
        <span style="color:${vCol}">${_esc(r.final_verdict || r.status || '—')}</span>
        · ${_esc(r.pipeline_name || '')}
      </span>
      <span>${dur}</span>
      <span>${_fmtNum(tok)}</span>
      <span style="color:var(--accent)">${cost}</span>
      <span class="pl-stars" style="display:flex;gap:0.05rem">${stars}</span>
    </div>
    <div style="font-size:0.68rem;color:var(--muted);padding:0 0 0.4rem;
                border-bottom:1px solid var(--border);line-height:1.4">
      ${_esc((r.task||'').slice(0,100))}
    </div>
  `;
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function _esc(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function _fmtNum(n) {
  if (n == null) return '—';
  return n >= 1000 ? (n/1000).toFixed(1)+'k' : String(n);
}
function _fmtDur(s) {
  if (s == null) return '—';
  const sec = Math.round(s);
  return sec < 60 ? `${sec}s` : `${Math.floor(sec/60)}m ${sec%60}s`;
}
