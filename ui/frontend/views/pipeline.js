/**
 * pipeline.js — Pipeline & Role Execution (Dashboard tab)
 *
 * Layout:
 *   Left panel (220px fixed): activated pipelines + activated roles
 *   Right panel (scrollable): 3 sections
 *     ① Config   — always visible; pipeline nodes + global props | role info + prompt
 *     ② Execute  — collapsible; input form + live progress + approval gate
 *     ③ History  — collapsible; last N run results with stats
 */

import { api } from '../utils/api.js';

// ── Module state ───────────────────────────────────────────────────────────────

let _project    = null;
let _selType    = null;     // 'pipeline' | 'role'
let _selName    = null;
let _selConfig  = null;     // full pipeline config (from getPipelineConfig)
let _selRole    = null;     // role object (from list)
let _pipelines  = [];
let _roles      = [];
let _runId      = null;
let _pollTimer  = null;
let _histLimit  = 10;
let _execOpen   = false;
let _histOpen   = true;

export function destroyPipeline() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
}

// ── Entry ──────────────────────────────────────────────────────────────────────

export async function renderPipeline(container, project) {
  destroyPipeline();
  _project   = project;
  _selType   = null;
  _selName   = null;
  _selConfig = null;
  _selRole   = null;
  _runId     = null;
  _histLimit = 10;
  _execOpen  = false;
  _histOpen  = true;

  container.innerHTML = `
    <div id="pl-shell" style="
      display:flex;height:100%;overflow:hidden;
      font-size:0.82rem;color:var(--text)">

      <!-- Left panel -->
      <div id="pl-left" style="
        width:220px;flex-shrink:0;
        border-right:1px solid var(--border);
        overflow-y:auto;display:flex;flex-direction:column">
        <div style="padding:0.6rem 0.75rem 0.3rem;font-size:0.65rem;font-weight:700;
                    text-transform:uppercase;letter-spacing:0.08em;color:var(--muted)">
          Pipelines
        </div>
        <div id="pl-left-pipelines"></div>
        <div style="padding:0.6rem 0.75rem 0.3rem;margin-top:0.25rem;
                    font-size:0.65rem;font-weight:700;
                    text-transform:uppercase;letter-spacing:0.08em;color:var(--muted)">
          Roles
        </div>
        <div id="pl-left-roles"></div>
      </div>

      <!-- Right panel -->
      <div id="pl-right" style="flex:1;overflow-y:auto;padding:1.1rem 1.4rem 2rem">

        <!-- placeholder -->
        <div id="pl-placeholder" style="
          display:flex;align-items:center;justify-content:center;
          height:60%;color:var(--muted);font-size:0.85rem;flex-direction:column;gap:0.5rem">
          <div style="font-size:1.6rem;opacity:.35">◫</div>
          <div>Select a pipeline or role from the left panel</div>
        </div>

        <!-- ① Config -->
        <div id="pl-config" style="display:none;margin-bottom:0.9rem"></div>

        <!-- ② Execute -->
        <div id="pl-exec-wrap" style="display:none;
          border:1px solid var(--border);border-radius:var(--radius,6px);
          margin-bottom:0.9rem;overflow:hidden">
          <div id="pl-exec-hdr" style="
            display:flex;align-items:center;gap:0.45rem;
            padding:0.5rem 0.9rem;cursor:pointer;user-select:none;
            background:var(--surface2);font-size:0.8rem;font-weight:600">
            <span id="pl-exec-arrow">▸</span>
            <span id="pl-exec-title">Execute</span>
            <span id="pl-exec-badge" style="margin-left:auto;font-size:0.68rem;color:var(--muted)"></span>
          </div>
          <div id="pl-exec-body" style="display:none;padding:0.85rem 1rem 1rem"></div>
        </div>

        <!-- ③ History -->
        <div id="pl-hist-wrap" style="display:none;
          border:1px solid var(--border);border-radius:var(--radius,6px);overflow:hidden">
          <div id="pl-hist-hdr" style="
            display:flex;align-items:center;gap:0.45rem;
            padding:0.5rem 0.9rem;cursor:pointer;user-select:none;
            background:var(--surface2);font-size:0.8rem;font-weight:600">
            <span id="pl-hist-arrow">▾</span>
            <span>History</span>
            <span style="margin-left:auto;display:flex;gap:0.2rem;align-items:center;
                         font-size:0.7rem;color:var(--muted)">
              Show:
              <button class="btn btn-ghost" style="font-size:0.65rem;padding:0.05rem 0.28rem;min-height:0"
                onclick="event.stopPropagation();window._plHist(10)">10</button>
              <button class="btn btn-ghost" style="font-size:0.65rem;padding:0.05rem 0.28rem;min-height:0"
                onclick="event.stopPropagation();window._plHist(20)">20</button>
              <button class="btn btn-ghost" style="font-size:0.65rem;padding:0.05rem 0.28rem;min-height:0"
                onclick="event.stopPropagation();window._plHist(50)">50</button>
            </span>
          </div>
          <div id="pl-hist-body" style="padding:0.75rem 1rem 1rem"></div>
        </div>

      </div>
    </div>

    <style>
      #pl-shell .pl-left-item {
        display:flex;align-items:center;justify-content:space-between;
        padding:0.42rem 0.75rem;cursor:pointer;font-size:0.78rem;
        border-left:2px solid transparent;transition:background .12s
      }
      #pl-shell .pl-left-item:hover { background:var(--surface2) }
      #pl-shell .pl-left-item.active {
        background:var(--surface2);border-left-color:var(--accent);
        color:var(--accent);font-weight:600
      }
      #pl-shell .pl-badge {
        font-size:0.6rem;padding:0.08rem 0.28rem;border-radius:3px;
        background:var(--surface3,rgba(128,128,128,.15));color:var(--muted);
        flex-shrink:0
      }
      #pl-shell .pl-prop-row {
        display:flex;align-items:center;gap:0.75rem;padding:0.28rem 0;font-size:0.78rem
      }
      #pl-shell .pl-prop-label {
        width:160px;flex-shrink:0;color:var(--muted);font-size:0.74rem
      }
      #pl-shell .pl-dot {
        width:9px;height:9px;border-radius:50%;flex-shrink:0;
        border:2px solid var(--border)
      }
      #pl-shell .pl-dot.done    { background:var(--green,#27ae60);border-color:var(--green,#27ae60) }
      #pl-shell .pl-dot.running {
        background:var(--accent);border-color:var(--accent);
        animation:pl-pulse 1s infinite
      }
      #pl-shell .pl-dot.waiting_approval { background:#9b59b6;border-color:#9b59b6 }
      #pl-shell .pl-dot.error   { background:#e74c3c;border-color:#e74c3c }
      #pl-shell .pl-dot.pending { background:transparent }
      @keyframes pl-pulse { 0%,100%{opacity:1} 50%{opacity:.35} }
      #pl-shell .pl-node-grid {
        display:grid;
        grid-template-columns:100px 140px 180px 65px 1fr;
        gap:0.35rem;font-size:0.72rem;padding:0.28rem 0;
        border-bottom:1px solid var(--border);align-items:start
      }
      #pl-shell .pl-node-grid.hdr {
        font-weight:700;color:var(--muted);padding-bottom:0.35rem
      }
      #pl-shell .pl-hist-row {
        font-size:0.72rem;padding:0.3rem 0;
        border-bottom:1px solid var(--border)
      }
      #pl-shell .pl-stars span { cursor:pointer;font-size:0.9rem }
      #pl-shell .log-error { color:#e74c3c }
      #pl-shell .log-warn  { color:#f39c12 }
      #pl-shell .log-info  { color:var(--text) }
    </style>
  `;

  // Wire global handlers
  window._plHist   = n => { _histLimit = n; _loadHistory(); };
  window._plTogSP  = _toggleSysPrompt;
  window._plNavRole = name => { if (window._nav) window._nav('prompts', { role: name }); };

  document.getElementById('pl-exec-hdr').addEventListener('click', _toggleExec);
  document.getElementById('pl-hist-hdr').addEventListener('click', e => {
    if (e.target.tagName === 'BUTTON') return;
    _histOpen = !_histOpen;
    document.getElementById('pl-hist-body').style.display = _histOpen ? '' : 'none';
    document.getElementById('pl-hist-arrow').textContent  = _histOpen ? '▾' : '▸';
    if (_histOpen) _loadHistory();
  });

  await Promise.all([_loadPipelines(), _loadRoles()]);
}

// ── Left panel loaders ─────────────────────────────────────────────────────────

async function _loadPipelines() {
  try {
    const cfg = await api.agentRoles.pipelinesConfig(_project);
    _pipelines = (cfg.pipelines || []).filter(p => p.activated && !p.error);
    const el = document.getElementById('pl-left-pipelines');
    if (!el) return;
    if (!_pipelines.length) {
      el.innerHTML = '<div style="padding:0.3rem 0.75rem;font-size:0.72rem;color:var(--muted)">No activated pipelines</div>';
      return;
    }
    el.innerHTML = _pipelines.map(p => `
      <div class="pl-left-item" data-type="pipeline" data-name="${_esc(p.name)}"
           onclick="window._plSel('pipeline','${_esc(p.name)}')">
        <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-right:0.3rem">
          ${_esc(p.name)}
        </span>
        <span class="pl-badge">${(p.required_roles||[]).length}</span>
      </div>`).join('');
  } catch (e) {
    const el = document.getElementById('pl-left-pipelines');
    if (el) el.innerHTML = `<div style="padding:0.3rem 0.75rem;font-size:0.72rem;color:#e74c3c">${_esc(e.message)}</div>`;
  }
}

async function _loadRoles() {
  try {
    const data = await api.agentRoles.list(_project);
    const arr  = Array.isArray(data) ? data : (data?.roles || []);
    _roles = arr.filter(r => r.activated && r.name !== 'internal_project_fact');
    const el = document.getElementById('pl-left-roles');
    if (!el) return;
    if (!_roles.length) {
      el.innerHTML = '<div style="padding:0.3rem 0.75rem;font-size:0.72rem;color:var(--muted)">No activated roles</div>';
      return;
    }
    el.innerHTML = _roles.map(r => `
      <div class="pl-left-item" data-type="role" data-name="${_esc(r.name)}"
           onclick="window._plSel('role','${_esc(r.name)}')">
        <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-right:0.3rem">
          ${_esc(r.name)}
        </span>
        <span class="pl-badge" style="font-size:0.55rem">${_esc((r.provider||'').slice(0,6))}</span>
      </div>`).join('');
  } catch (e) {
    const el = document.getElementById('pl-left-roles');
    if (el) el.innerHTML = `<div style="padding:0.3rem 0.75rem;font-size:0.72rem;color:#e74c3c">${_esc(e.message)}</div>`;
  }
}

// ── Selection ──────────────────────────────────────────────────────────────────

window._plSel = async (type, name) => {
  _selType = type;
  _selName = name;
  _runId   = null;
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }

  // Highlight left item
  document.querySelectorAll('#pl-shell .pl-left-item').forEach(el => {
    el.classList.toggle('active',
      el.dataset.type === type && el.dataset.name === name);
  });

  // Show sections, hide placeholder
  document.getElementById('pl-placeholder').style.display  = 'none';
  document.getElementById('pl-config').style.display       = '';
  document.getElementById('pl-exec-wrap').style.display    = '';
  document.getElementById('pl-hist-wrap').style.display    = '';

  // Reset execute section
  _execOpen = false;
  document.getElementById('pl-exec-body').style.display  = 'none';
  document.getElementById('pl-exec-arrow').textContent   = '▸';
  document.getElementById('pl-exec-title').textContent   = type === 'pipeline' ? `Execute · ${name}` : `Execute · ${name}`;
  document.getElementById('pl-exec-badge').textContent   = '';

  // Load config + history
  if (type === 'pipeline') {
    await _loadPipelineConfig(name);
  } else {
    _renderRoleConfig(name);
  }
  _histOpen = true;
  document.getElementById('pl-hist-body').style.display  = '';
  document.getElementById('pl-hist-arrow').textContent   = '▾';
  _loadHistory();
};

// ── Pipeline config ────────────────────────────────────────────────────────────

async function _loadPipelineConfig(name) {
  const configEl = document.getElementById('pl-config');
  if (!configEl) return;
  configEl.innerHTML = '<div style="color:var(--muted);font-size:0.78rem;padding:0.5rem 0">Loading pipeline config…</div>';
  try {
    _selConfig = await api.agentRoles.getPipelineConfig(name, _project);
    _renderPipelineConfig(_selConfig);
  } catch (e) {
    configEl.innerHTML = `<div style="color:#e74c3c;font-size:0.78rem">Error loading config: ${_esc(e.message)}</div>`;
  }
}

function _renderPipelineConfig(cfg) {
  const configEl = document.getElementById('pl-config');
  if (!configEl) return;

  const stageKeys = (cfg.stages || []).map(s => s.key);
  const approvalOpts = ['<option value="">— none —</option>']
    .concat(stageKeys.map(k =>
      `<option value="${_esc(k)}" ${cfg.require_approval_after === k ? 'selected' : ''}>${_esc(k)}</option>`
    )).join('');

  const tempVal  = cfg.default_temperature != null ? cfg.default_temperature : '';
  const retries  = cfg.max_rejection_retries ?? 2;

  configEl.innerHTML = `
    <div style="background:var(--surface2);border:1px solid var(--border);
                border-radius:var(--radius,6px);padding:1rem 1.1rem 0.9rem;margin-bottom:0.9rem">

      <!-- Header -->
      <div style="display:flex;align-items:baseline;gap:0.6rem;margin-bottom:0.25rem;flex-wrap:wrap">
        <span style="font-size:1rem;font-weight:700">${_esc(cfg.name)}</span>
        <span class="pl-badge">v${_esc(cfg.version||'1.0')}</span>
        <span class="pl-badge">${(cfg.stages||[]).length} stages</span>
      </div>
      ${cfg.description ? `<div style="font-size:0.75rem;color:var(--muted);margin-bottom:0.75rem;line-height:1.5">${_esc(cfg.description.split('\n')[0])}</div>` : ''}

      <!-- Global Properties -->
      <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;
                  color:var(--muted);margin:0.65rem 0 0.45rem">Global Properties</div>

      <div class="pl-prop-row">
        <span class="pl-prop-label">Max rejection retries</span>
        <input id="cfg-retries" type="number" min="1" max="10" value="${retries}"
          style="width:50px;background:var(--surface);border:1px solid var(--border);
                 border-radius:4px;padding:0.2rem 0.3rem;color:var(--text);font-size:0.78rem;text-align:center">
        <span style="font-size:0.7rem;color:var(--muted)">reviewer rejections before pipeline stops</span>
      </div>

      <div class="pl-prop-row">
        <span class="pl-prop-label">Global temperature</span>
        <input id="cfg-temp" type="number" min="0" max="1" step="0.05"
          value="${tempVal}"
          placeholder="role default"
          style="width:72px;background:var(--surface);border:1px solid var(--border);
                 border-radius:4px;padding:0.2rem 0.3rem;color:var(--text);font-size:0.78rem">
        <span style="font-size:0.7rem;color:var(--muted)">0–1, blank = use each role's default</span>
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
                 padding:0.2rem 0.35rem;color:var(--text);font-size:0.78rem">
          ${approvalOpts}
        </select>
      </div>

      <div id="cfg-save-status" style="font-size:0.7rem;color:var(--muted);min-height:1rem;margin:0.2rem 0 0.7rem"></div>

      <!-- Nodes -->
      <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;
                  color:var(--muted);margin-bottom:0.4rem">Nodes</div>
      <div style="overflow-x:auto">
        <div class="pl-node-grid hdr">
          <span>Stage</span><span>Role</span><span>Provider · Model</span>
          <span>Temp</span><span>System Prompt</span>
        </div>
        ${(cfg.stages || []).map(_nodeRow).join('') ||
          '<div style="color:var(--muted);font-size:0.75rem;padding:0.3rem 0">No stages defined</div>'}
      </div>
    </div>
  `;

  // Auto-save on change with 800ms debounce
  const statusEl = document.getElementById('cfg-save-status');
  let saveTimer  = null;
  const schedule = () => {
    statusEl.textContent = 'Unsaved…'; statusEl.style.color = 'var(--muted)';
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => _saveCfg(cfg.name, statusEl), 800);
  };
  ['cfg-retries','cfg-temp','cfg-continue','cfg-save-mem','cfg-approval'].forEach(id => {
    document.getElementById(id)?.addEventListener('change', schedule);
  });

  // System prompt expand toggles (event delegation)
  configEl.addEventListener('click', e => {
    const btn = e.target.closest('[data-sp-toggle]');
    if (!btn) return;
    const key = btn.dataset.spToggle;
    _toggleSysPrompt(key);
  });
}

function _nodeRow(s) {
  const pm   = [s.role_provider, s.role_model].filter(Boolean).join(' · ') || '—';
  const temp = s.role_temperature != null
    ? Number(s.role_temperature).toFixed(2)
    : (s.temperature_override != null ? `${s.temperature_override}↑` : '—');
  const sp      = (s.role_system_prompt || '').trim();
  const preview = _esc(sp.slice(0, 80).replace(/\n/g, ' ')) + (sp.length > 80 ? '…' : '');
  const key     = s.key;
  return `
    <div class="pl-node-grid">
      <span style="font-family:monospace;font-weight:600;word-break:break-all">${_esc(key)}</span>
      <span>
        ${_esc(s.role)}
        <button onclick="window._plNavRole('${_esc(s.role)}')"
          style="background:none;border:none;cursor:pointer;color:var(--accent);
                 font-size:0.62rem;padding:0 0.1rem;opacity:.75" title="Open in Roles editor">↗</button>
      </span>
      <span style="font-family:monospace;font-size:0.68rem;color:var(--muted);word-break:break-all">${_esc(pm)}</span>
      <span style="color:var(--muted)">${_esc(temp)}</span>
      <span style="font-size:0.68rem">
        ${sp ? `
          <span id="spp-${_esc(key)}">${preview}
            <button data-sp-toggle="${_esc(key)}"
              style="background:none;border:none;cursor:pointer;color:var(--accent);
                     font-size:0.62rem;padding:0 0.1rem">▸</button>
          </span>
          <pre id="spf-${_esc(key)}" style="display:none;margin:0.2rem 0 0;
            font-family:monospace;font-size:0.65rem;line-height:1.4;
            background:var(--surface2);border:1px solid var(--border);border-radius:3px;
            padding:0.35rem;white-space:pre-wrap;word-break:break-word;
            max-height:140px;overflow-y:auto">${_esc(sp)}</pre>
        ` : '<span style="color:var(--muted)">—</span>'}
      </span>
    </div>`;
}

function _toggleSysPrompt(key) {
  const prev = document.getElementById(`spp-${key}`);
  const full = document.getElementById(`spf-${key}`);
  if (!prev || !full) return;
  const open = full.style.display !== 'none';
  prev.style.display = open ? '' : 'none';
  full.style.display = open ? 'none' : '';
  const btn = prev.querySelector('[data-sp-toggle]');
  if (btn) btn.textContent = open ? '▸' : '▾';
}

async function _saveCfg(pipelineName, statusEl) {
  const tempRaw = document.getElementById('cfg-temp')?.value;
  const body = {
    max_rejection_retries:  parseInt(document.getElementById('cfg-retries')?.value || '2', 10),
    continue_on_failure:    document.getElementById('cfg-continue')?.checked ?? false,
    save_memory:            document.getElementById('cfg-save-mem')?.checked ?? true,
    require_approval_after: document.getElementById('cfg-approval')?.value || null,
    default_temperature:    tempRaw !== '' && tempRaw != null ? parseFloat(tempRaw) : null,
  };
  try {
    await api.agentRoles.patchPipeline(pipelineName, body, _project);
    statusEl.textContent = 'Saved ✓'; statusEl.style.color = 'var(--green,#27ae60)';
    setTimeout(() => { statusEl.textContent = ''; }, 2500);
  } catch (e) {
    statusEl.textContent = `Save error: ${e.message}`; statusEl.style.color = '#e74c3c';
  }
}

// ── Role config ────────────────────────────────────────────────────────────────

function _renderRoleConfig(name) {
  const configEl = document.getElementById('pl-config');
  if (!configEl) return;

  _selRole   = _roles.find(r => r.name === name) || null;
  const role = _selRole;
  if (!role) { configEl.innerHTML = `<div style="color:#e74c3c">Role not found: ${_esc(name)}</div>`; return; }

  const pm   = [role.provider, role.model].filter(Boolean).join(' · ');
  const temp = role.temperature != null ? `temp ${role.temperature}` : '';
  const sp   = (role.system_prompt || '').trim();

  configEl.innerHTML = `
    <div style="background:var(--surface2);border:1px solid var(--border);
                border-radius:var(--radius,6px);padding:1rem 1.1rem 0.9rem;margin-bottom:0.9rem">

      <div style="display:flex;align-items:baseline;gap:0.5rem;margin-bottom:0.2rem;flex-wrap:wrap">
        <span style="font-size:1rem;font-weight:700">${_esc(role.name)}</span>
        ${pm ? `<span class="pl-badge">${_esc(pm)}</span>` : ''}
        ${temp ? `<span class="pl-badge">${_esc(temp)}</span>` : ''}
        ${role.max_iterations ? `<span class="pl-badge">max ${role.max_iterations} steps</span>` : ''}
      </div>

      ${role.description ? `
        <div style="font-size:0.75rem;color:var(--muted);margin-bottom:0.6rem;line-height:1.5">
          ${_esc(role.description)}
        </div>` : ''}

      <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.07em;
                  color:var(--muted);margin-bottom:0.35rem">System Prompt</div>
      ${sp ? `
        <pre style="font-family:monospace;font-size:0.7rem;line-height:1.4;
          background:var(--surface);border:1px solid var(--border);border-radius:4px;
          padding:0.5rem;white-space:pre-wrap;word-break:break-word;
          max-height:180px;overflow-y:auto;margin:0 0 0.65rem">${_esc(sp)}</pre>
      ` : `<div style="color:var(--muted);font-size:0.75rem;margin-bottom:0.65rem">No system prompt</div>`}

      <button onclick="window._plNavRole('${_esc(role.name)}')"
        class="btn btn-ghost btn-sm" style="font-size:0.75rem">
        Open in Roles editor ↗
      </button>
    </div>
  `;
}

// ── Execute section ────────────────────────────────────────────────────────────

function _toggleExec() {
  if (!_selType) return;
  _execOpen = !_execOpen;
  document.getElementById('pl-exec-body').style.display = _execOpen ? '' : 'none';
  document.getElementById('pl-exec-arrow').textContent  = _execOpen ? '▾' : '▸';
  if (_execOpen) _renderExecBody();
}

function _renderExecBody() {
  const body = document.getElementById('pl-exec-body');
  if (!body || body.querySelector('#pl-task')) return; // already rendered

  body.innerHTML = `
    <!-- Input mode -->
    <div style="display:flex;gap:0.5rem;margin-bottom:0.65rem;font-size:0.78rem">
      <label style="display:flex;align-items:center;gap:0.3rem;cursor:pointer">
        <input type="radio" name="pl-input-mode" value="prompt" checked
               onchange="window._plInputMode('prompt')"> Prompt
      </label>
      <label style="display:flex;align-items:center;gap:0.3rem;cursor:pointer">
        <input type="radio" name="pl-input-mode" value="file"
               onchange="window._plInputMode('file')"> Document / File
      </label>
    </div>

    <!-- Prompt input -->
    <div id="pl-prompt-area" style="margin-bottom:0.65rem">
      <textarea id="pl-task" rows="4"
        placeholder="Describe the task you want the agent to solve…"
        style="width:100%;box-sizing:border-box;background:var(--surface);
               border:1px solid var(--border);border-radius:4px;padding:0.4rem 0.5rem;
               color:var(--text);font-size:0.82rem;resize:vertical;font-family:inherit">
      </textarea>
    </div>

    <!-- File input (hidden by default) -->
    <div id="pl-file-area" style="display:none;margin-bottom:0.65rem">
      <div style="font-size:0.72rem;color:var(--muted);margin-bottom:0.3rem">
        Select from project documents or upload a file
      </div>
      <div style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center;margin-bottom:0.4rem">
        <select id="pl-doc-sel"
          style="flex:1;min-width:160px;background:var(--surface);border:1px solid var(--border);
                 border-radius:4px;padding:0.28rem 0.4rem;color:var(--text);font-size:0.78rem">
          <option value="">— pick a project document —</option>
        </select>
        <label class="btn btn-ghost btn-sm" style="cursor:pointer;font-size:0.75rem">
          Upload file
          <input id="pl-file-upload" type="file" style="display:none" onchange="window._plFileUp(this)">
        </label>
      </div>
      <div id="pl-file-label" style="font-size:0.7rem;color:var(--muted)"></div>
      <textarea id="pl-file-task" rows="2" placeholder="Additional instructions (optional)…"
        style="width:100%;box-sizing:border-box;margin-top:0.4rem;background:var(--surface);
               border:1px solid var(--border);border-radius:4px;padding:0.3rem 0.4rem;
               color:var(--text);font-size:0.78rem;resize:vertical;font-family:inherit">
      </textarea>
    </div>

    <!-- Action buttons -->
    <div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;margin-bottom:0.65rem">
      <button id="pl-run-btn" class="btn btn-primary btn-sm"
        style="font-size:0.8rem;padding:0.35rem 1rem"
        onclick="window._plRun()">
        ▶ ${_selType === 'pipeline' ? 'Run Pipeline' : 'Run Role'}
      </button>
      <button id="pl-cancel-btn" class="btn btn-ghost btn-sm"
        style="font-size:0.8rem;display:none"
        onclick="window._plCancel()">
        ■ Cancel
      </button>
      <span id="pl-run-err" style="font-size:0.74rem;color:#e74c3c"></span>
    </div>

    <!-- Progress (hidden until run starts) -->
    <div id="pl-progress" style="display:none">
      <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;
                  letter-spacing:0.07em;color:var(--muted);margin-bottom:0.4rem"
           id="pl-progress-title">Progress</div>

      <!-- Stage dots -->
      <div id="pl-stage-dots" style="margin-bottom:0.5rem"></div>

      <!-- Live Log -->
      <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;
                  letter-spacing:0.07em;color:var(--muted);margin-bottom:0.25rem">Live Log</div>
      <div id="pl-log" style="
        font-family:monospace;font-size:0.7rem;line-height:1.5;
        background:var(--surface);border:1px solid var(--border);
        border-radius:4px;padding:0.45rem 0.5rem;
        height:200px;overflow-y:auto;color:var(--text)"></div>

      <!-- Approval gate -->
      <div id="pl-approval" style="display:none;margin-top:0.65rem;
        border:2px solid #9b59b6;border-radius:6px;padding:0.7rem;
        background:rgba(155,89,182,0.06)">
        <div style="font-weight:700;color:#9b59b6;margin-bottom:0.3rem;font-size:0.8rem">
          ⏸ Approval Required
        </div>
        <div id="pl-approval-msg" style="font-size:0.76rem;color:var(--muted);margin-bottom:0.35rem"></div>
        <div id="pl-approval-preview" style="font-family:monospace;font-size:0.68rem;
             background:var(--surface2);border-radius:4px;padding:0.35rem;
             max-height:90px;overflow-y:auto;margin-bottom:0.45rem;
             white-space:pre-wrap;word-break:break-word;color:var(--text)"></div>
        <textarea id="pl-approval-fb" rows="2" placeholder="Feedback (optional)…"
          style="width:100%;box-sizing:border-box;background:var(--surface2);
                 border:1px solid var(--border);border-radius:4px;padding:0.28rem 0.35rem;
                 font-size:0.76rem;color:var(--text);resize:vertical;margin-bottom:0.35rem;
                 font-family:inherit"></textarea>
        <div style="display:flex;gap:0.4rem">
          <button class="btn btn-primary btn-sm" style="font-size:0.76rem"
            onclick="window._plApprove(true)">✓ Approve &amp; continue</button>
          <button class="btn btn-ghost btn-sm"
            style="font-size:0.76rem;color:#e74c3c;border-color:#e74c3c"
            onclick="window._plApprove(false)">✗ Reject</button>
        </div>
      </div>

      <!-- Final result -->
      <div id="pl-result" style="display:none;margin-top:0.65rem;
        border:1px solid var(--border);border-radius:6px;padding:0.6rem 0.75rem;
        background:var(--surface2);font-size:0.78rem"></div>
    </div>
  `;

  window._plInputMode = mode => {
    document.getElementById('pl-prompt-area').style.display = mode === 'prompt' ? '' : 'none';
    document.getElementById('pl-file-area').style.display   = mode === 'file'   ? '' : 'none';
  };
  window._plFileUp = inp => {
    const f = inp.files?.[0];
    document.getElementById('pl-file-label').textContent = f ? `Selected: ${f.name}` : '';
  };
  window._plRun    = _startRun;
  window._plCancel = _cancelRun;
  window._plApprove = _sendApproval;

  // Load document list for file picker
  _loadDocList();
}

async function _loadDocList() {
  const sel = document.getElementById('pl-doc-sel');
  if (!sel) return;
  try {
    // Try project documents endpoint
    const data = await api.projects?.listDocuments?.(_project) || null;
    const docs = data?.documents || [];
    if (docs.length) {
      sel.innerHTML = '<option value="">— pick a project document —</option>' +
        docs.map(d => `<option value="${_esc(d.path||d.name)}">${_esc(d.name||d.path)}</option>`).join('');
    }
  } catch (_) { /* no documents endpoint — file upload only */ }
}

// ── Run execution ──────────────────────────────────────────────────────────────

async function _startRun() {
  const errEl = document.getElementById('pl-run-err');
  errEl.textContent = '';

  const mode = document.querySelector('[name="pl-input-mode"]:checked')?.value || 'prompt';
  let task = '';
  if (mode === 'prompt') {
    task = (document.getElementById('pl-task')?.value || '').trim();
    if (!task) { errEl.textContent = 'Enter a task first.'; return; }
  } else {
    const docPath = document.getElementById('pl-doc-sel')?.value;
    const fileInp = document.getElementById('pl-file-upload');
    const extra   = (document.getElementById('pl-file-task')?.value || '').trim();
    if (!docPath && !fileInp?.files?.length) {
      errEl.textContent = 'Select a document or upload a file.'; return;
    }
    task = docPath ? `[file: ${docPath}]` : `[file: ${fileInp.files[0].name}]`;
    if (extra) task += `\n${extra}`;
  }

  document.getElementById('pl-run-btn').style.display    = 'none';
  document.getElementById('pl-cancel-btn').style.display = '';
  document.getElementById('pl-progress').style.display   = '';
  document.getElementById('pl-result').style.display     = 'none';
  document.getElementById('pl-approval').style.display   = 'none';
  _clearLog();

  if (_selType === 'role') {
    await _startRoleRun(task);
  } else {
    await _startPipelineRun(task);
  }
}

async function _startPipelineRun(task) {
  const pipeline = _selName;
  document.getElementById('pl-exec-title').textContent = `Running · ${pipeline}`;

  // Pre-fill dots from YAML stage list
  const defs = (_selConfig?.stages || []).map(s => ({ key: s.key, role: s.role, status: 'pending' }));
  _renderDots(defs);
  _appendLog(`Starting pipeline: ${pipeline}`);

  try {
    const res = await api.agents.startPipelineRun({ pipeline, task, project: _project });
    _runId = res.run_id;
    _appendLog(`Run ID: ${_runId}`);
    _startPolling();
  } catch (e) {
    _appendLog(`Error: ${e.message}`, 'error');
    _resetRunUI(false);
  }
}

async function _startRoleRun(task) {
  const role = _selName;
  document.getElementById('pl-exec-title').textContent = `Running · ${role}`;
  document.getElementById('pl-stage-dots').innerHTML   = '';
  _appendLog(`Running role: ${role}…`);

  try {
    const result = await api.agents.runAgent({ role, task, project: _project });
    _appendLog(`Status: ${result.status || 'done'}`);
    const tok = (result.input_tokens||0) + (result.output_tokens||0);
    _appendLog(`Cost: $${(result.cost_usd||0).toFixed(4)} · Tokens: ${tok}`);

    // Show each ReAct step
    if (result.steps?.length) {
      result.steps.slice(0, 20).forEach((step, i) => {
        if (step.thought) _appendLog(`Step ${i+1} Thought: ${step.thought.slice(0,120)}…`);
        if (step.action)  _appendLog(`  Action: ${step.action}`);
      });
    }
    if (result.output) {
      _appendLog('── Output ──');
      result.output.split('\n').slice(0, 40).forEach(l => _appendLog(l));
    }
    if (result.error) _appendLog(`Error: ${result.error}`, 'error');

    document.getElementById('pl-exec-title').textContent = result.status === 'done' ? '✓ Done' : `✓ ${result.status}`;
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
  _appendLog('Cancelled.', 'warn');
  _resetRunUI(false);
  document.getElementById('pl-exec-title').textContent = `Execute · ${_selName}`;
}

function _startPolling() {
  if (_pollTimer) clearInterval(_pollTimer);
  _pollTimer = setInterval(async () => {
    if (!_runId) { clearInterval(_pollTimer); return; }
    try {
      const data = await api.agents.getPipelineRun(_runId);
      _updateProgress(data);
      if (!['running','waiting_approval'].includes(data.status)) {
        clearInterval(_pollTimer); _pollTimer = null;
        _onRunDone(data);
      }
    } catch (e) { _appendLog(`Poll error: ${e.message}`, 'error'); }
  }, 1500);
}

function _updateProgress(data) {
  _renderDots(data.stages || []);

  // Stream new log lines (dedup by stage+ts)
  const logEl = document.getElementById('pl-log');
  if (logEl) {
    if (!logEl._seen) logEl._seen = new Set();
    for (const stage of (data.stages || [])) {
      for (const entry of (stage.log_lines || [])) {
        const key = `${stage.stage_key}:${entry.ts}`;
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
        `Stage "${last.stage_key}" finished. Review output before the next stage runs.`;
      document.getElementById('pl-approval-preview').textContent = last.output_preview || '';
    }
  } else {
    if (apEl) apEl.style.display = 'none';
  }
}

function _onRunDone(data) {
  const verdict = data.final_verdict || data.status;
  const tok   = (data.total_input_tokens||0) + (data.total_output_tokens||0);
  const cost  = `$${(data.total_cost_usd||0).toFixed(4)}`;
  const dur   = data.duration_s != null ? _fmtDur(data.duration_s) : '—';

  _appendLog(
    `✓ Complete — verdict: ${verdict} | duration: ${dur} | cost: ${cost} | tokens: ${_fmtNum(tok)}`,
    data.status === 'error' ? 'error' : 'info',
  );

  document.getElementById('pl-exec-title').textContent =
    verdict === 'approved' ? '✓ Approved' :
    verdict === 'rejected' ? '✗ Rejected' :
    data.status === 'error' ? '✗ Error' : '✓ Done';

  // Score summary
  const score = data.score;
  const resEl = document.getElementById('pl-result');
  if (resEl) {
    const verdictColor = verdict === 'approved' ? 'var(--green,#27ae60)'
      : verdict === 'rejected' ? '#e74c3c' : 'var(--muted)';
    resEl.style.display = '';
    resEl.innerHTML = `
      <div style="display:flex;flex-wrap:wrap;gap:0.75rem;align-items:center">
        <span style="font-weight:700;color:${verdictColor}">${_esc(verdict)}</span>
        <span style="color:var(--muted)">${dur}</span>
        <span style="color:var(--accent)">${cost}</span>
        <span style="color:var(--muted)">${_fmtNum(tok)} tokens</span>
        <span id="pl-run-score" style="display:flex;gap:0.05rem">
          ${[1,2,3,4,5].map(n => `
            <span data-sc="${n}" title="Rate ${n}"
              style="cursor:pointer;font-size:1rem;color:${score != null && n <= score ? '#f39c12' : 'var(--muted)'}">★</span>`
          ).join('')}
        </span>
      </div>
    `;
    resEl.querySelectorAll('[data-sc]').forEach(star => {
      star.addEventListener('click', async () => {
        try {
          await api.agents.scoreRun(_runId, parseInt(star.dataset.sc, 10));
          _loadHistory();
          // Refresh stars
          resEl.querySelectorAll('[data-sc]').forEach(s => {
            s.style.color = parseInt(s.dataset.sc) <= parseInt(star.dataset.sc) ? '#f39c12' : 'var(--muted)';
          });
        } catch (_) {}
      });
    });
  }

  _resetRunUI(false);
  _runId = null;
  _loadHistory();
}

function _resetRunUI(hideProgress = true) {
  document.getElementById('pl-run-btn').style.display    = '';
  document.getElementById('pl-cancel-btn').style.display = 'none';
  if (hideProgress && document.getElementById('pl-progress'))
    document.getElementById('pl-progress').style.display = 'none';
}

async function _sendApproval(approved) {
  if (!_runId) return;
  const fb = document.getElementById('pl-approval-fb')?.value || '';
  try {
    await api.agents.approvePipelineRun(_runId, { approved, feedback: fb });
    document.getElementById('pl-approval').style.display = 'none';
    _appendLog(approved ? 'Approved — continuing…' : 'Rejected — stopping pipeline.', approved ? 'info' : 'warn');
  } catch (e) { _appendLog(`Approval error: ${e.message}`, 'error'); }
}

// ── Stage dots ─────────────────────────────────────────────────────────────────

function _renderDots(stages) {
  const el = document.getElementById('pl-stage-dots');
  if (!el) return;
  el.innerHTML = stages.map(s => {
    const dur  = s.duration_s  != null ? ` ${Number(s.duration_s).toFixed(1)}s` : '';
    const cost = s.cost_usd    != null && s.cost_usd > 0
      ? ` $${Number(s.cost_usd).toFixed(4)}` : '';
    const tok  = ((s.input_tokens||0) + (s.output_tokens||0)) > 0
      ? ` ${_fmtNum((s.input_tokens||0)+(s.output_tokens||0))} tok` : '';
    const st   = s.status || 'pending';
    return `
      <div style="display:flex;align-items:center;gap:0.45rem;padding:0.18rem 0;font-size:0.76rem">
        <div class="pl-dot ${_esc(st)}"></div>
        <span style="font-family:monospace;min-width:100px;font-weight:600">${_esc(s.stage_key||s.key||'')}</span>
        <span style="color:var(--muted);font-size:0.68rem;min-width:70px">${_esc(s.role_name||s.role||'')}</span>
        <span style="font-size:0.68rem;min-width:75px;color:${_statusColor(st)}">[${_esc(st)}]</span>
        ${dur  ? `<span style="color:var(--muted);font-size:0.68rem">${dur}</span>` : ''}
        ${cost ? `<span style="color:var(--accent);font-size:0.68rem">${cost}</span>` : ''}
        ${tok  ? `<span style="color:var(--muted);font-size:0.68rem">${tok}</span>` : ''}
      </div>`;
  }).join('');
}

function _statusColor(st) {
  return st === 'done'             ? 'var(--green,#27ae60)'
    : st === 'running'             ? 'var(--accent)'
    : st === 'error'               ? '#e74c3c'
    : st === 'waiting_approval'    ? '#9b59b6'
    : 'var(--muted)';
}

// ── Log ────────────────────────────────────────────────────────────────────────

function _appendLog(text, level = 'info') {
  const el = document.getElementById('pl-log');
  if (!el) return;
  const ts  = new Date().toLocaleTimeString();
  const cls = level === 'error' ? ' class="log-error"'
            : level === 'warn'  ? ' class="log-warn"' : '';
  el.insertAdjacentHTML('beforeend',
    `<div${cls}>${ts}  ${_esc(String(text))}</div>`);
  el.scrollTop = el.scrollHeight;
}

function _clearLog() {
  const el = document.getElementById('pl-log');
  if (el) { el.innerHTML = ''; el._seen = new Set(); }
}

// ── History section ────────────────────────────────────────────────────────────

async function _loadHistory() {
  const el = document.getElementById('pl-hist-body');
  if (!el) return;
  el.innerHTML = '<div style="color:var(--muted);font-size:0.75rem">Loading…</div>';

  const pipeline = _selType === 'pipeline' ? _selName : null;

  try {
    const data = await api.agents.listPipelineRuns(_project, pipeline, _histLimit);
    const runs = data.runs || [];
    if (!runs.length) {
      el.innerHTML = '<div style="color:var(--muted);font-size:0.75rem;padding:0.25rem 0">No runs yet.</div>';
      return;
    }

    el.innerHTML = `
      <div style="overflow-x:auto">
        <div style="display:grid;grid-template-columns:150px 90px 70px 70px 90px 80px;
                    gap:0.25rem;font-size:0.68rem;font-weight:700;color:var(--muted);
                    padding-bottom:0.3rem;border-bottom:1px solid var(--border);min-width:560px">
          <span>Date &amp; Pipeline</span>
          <span>Duration / Nodes</span>
          <span>Tokens</span>
          <span>Cost</span>
          <span>Verdict</span>
          <span>Score</span>
        </div>
        ${runs.map(_histRow).join('')}
      </div>
    `;

    el.querySelectorAll('.pl-stars span').forEach(star => {
      star.addEventListener('click', async () => {
        const row = star.closest('[data-run-id]');
        if (!row) return;
        try {
          await api.agents.scoreRun(row.dataset.runId, parseInt(star.dataset.s, 10));
          _loadHistory();
        } catch (_) {}
      });
    });
  } catch (e) {
    el.innerHTML = `<div style="color:#e74c3c;font-size:0.75rem">${_esc(e.message)}</div>`;
  }
}

function _histRow(r) {
  const at     = r.started_at ? new Date(r.started_at) : null;
  const dateStr = at ? at.toLocaleDateString('en-GB', { day:'2-digit', month:'2-digit', year:'2-digit' })
                      + ' ' + at.toLocaleTimeString([], { hour:'2-digit', minute:'2-digit' }) : '—';
  const dur    = r.duration_s != null ? _fmtDur(r.duration_s) : '—';
  const tok    = (r.total_input_tokens||0) + (r.total_output_tokens||0);
  const cost   = r.total_cost_usd != null ? `$${Number(r.total_cost_usd).toFixed(4)}` : '—';
  const sc     = r.score ?? null;
  const verdict = r.final_verdict || r.status || '—';
  const vColor = verdict === 'approved' ? 'var(--green,#27ae60)'
    : verdict === 'rejected' ? '#e74c3c' : 'var(--muted)';
  const stars = [1,2,3,4,5].map(n =>
    `<span data-s="${n}" style="color:${sc != null && n <= sc ? '#f39c12' : 'var(--muted)'}">★</span>`
  ).join('');

  // Stage breakdown (node durations)
  const stageSummary = (r.stages || []).map(s => {
    const d = s.duration_s != null ? `${Number(s.duration_s).toFixed(0)}s` : '…';
    const col = _statusColor(s.status || 'pending');
    return `<span style="color:${col};font-size:0.6rem">${_esc(s.stage_key||'')} ${d}</span>`;
  }).join(' | ');

  return `
    <div class="pl-hist-row" data-run-id="${_esc(r.run_id)}" style="
      display:grid;grid-template-columns:150px 90px 70px 70px 90px 80px;
      gap:0.25rem;align-items:start;min-width:560px">
      <span>
        <div style="font-size:0.7rem;color:var(--muted)">${dateStr}</div>
        <div style="font-size:0.65rem;color:var(--muted)">${_esc(r.pipeline_name||'')}</div>
        <div style="font-size:0.65rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;
                    white-space:nowrap" title="${_esc(r.task||'')}">${_esc((r.task||'').slice(0,35))}</div>
      </span>
      <span>
        <div style="font-size:0.7rem">${dur}</div>
        <div style="font-size:0.62rem;display:flex;flex-direction:column;gap:0.05rem">${stageSummary}</div>
      </span>
      <span style="font-size:0.7rem">${_fmtNum(tok)}</span>
      <span style="font-size:0.7rem;color:var(--accent)">${cost}</span>
      <span style="font-size:0.7rem;color:${vColor};font-weight:600">${_esc(verdict)}</span>
      <span class="pl-stars" style="display:flex;gap:0.02rem;font-size:0.82rem">${stars}</span>
    </div>
  `;
}

// ── Utilities ──────────────────────────────────────────────────────────────────

function _esc(s) {
  return String(s ?? '')
    .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
function _fmtNum(n) {
  if (n == null || n === 0) return '—';
  return n >= 1000 ? (n/1000).toFixed(1)+'k' : String(n);
}
function _fmtDur(s) {
  if (s == null) return '—';
  const sec = Math.round(s);
  return sec < 60 ? `${sec}s` : `${Math.floor(sec/60)}m ${sec%60}s`;
}
