/**
 * pipeline.js — Pipeline Execution UI
 *
 * Layout:
 *   Left panel (220px): Activated pipelines + activated roles
 *   Right panel:
 *     Section 1 (Properties) — always visible, top
 *     Section 2 (Execution)  — collapsible, middle
 *     Section 3 (History)    — toggleable, bottom
 */

import { api } from '../utils/api.js';

// ── State ─────────────────────────────────────────────────────────────────────

let _project       = null;
let _selected      = null;   // { type: 'pipeline'|'role', name, data }
let _runId         = null;
let _pollTimer     = null;
let _histLimit     = 10;
let _histVisible   = false;
let _execVisible   = true;

export function destroyPipeline() {
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }
}

// ── Entry ─────────────────────────────────────────────────────────────────────

export async function renderPipeline(container, project) {
  destroyPipeline();
  _project     = project;
  _selected    = null;
  _runId       = null;
  _histVisible = false;
  _execVisible = true;

  container.innerHTML = `
    <div id="pl-root" style="display:flex;height:100%;overflow:hidden">
      <!-- Left panel -->
      <div id="pl-left" style="
        width:220px;min-width:160px;flex-shrink:0;
        border-right:1px solid var(--border);
        display:flex;flex-direction:column;overflow:hidden">
        <div style="padding:0.7rem 0.75rem 0.4rem;font-size:0.65rem;font-weight:700;
                    text-transform:uppercase;letter-spacing:0.07em;color:var(--muted)">
          Pipelines
        </div>
        <div id="pl-pipelines-list" style="overflow-y:auto;flex:0 0 auto;max-height:50%">
          <div style="padding:0 0.75rem;color:var(--muted);font-size:0.75rem">Loading…</div>
        </div>
        <div style="padding:0.6rem 0.75rem 0.4rem;font-size:0.65rem;font-weight:700;
                    text-transform:uppercase;letter-spacing:0.07em;color:var(--muted);
                    border-top:1px solid var(--border);margin-top:0.25rem">
          Roles
        </div>
        <div id="pl-roles-list" style="overflow-y:auto;flex:1">
          <div style="padding:0 0.75rem;color:var(--muted);font-size:0.75rem">Loading…</div>
        </div>
      </div>

      <!-- Right panel -->
      <div id="pl-right" style="flex:1;overflow-y:auto;display:flex;flex-direction:column;min-width:0">
        <div id="pl-props"  style="flex-shrink:0;padding:1rem 1.25rem 0.75rem"></div>
        <div id="pl-exec"   style="flex-shrink:0;border-top:1px solid var(--border)"></div>
        <div id="pl-hist"   style="flex-shrink:0;border-top:1px solid var(--border)"></div>
      </div>
    </div>

    <style>
      .pl-item {
        padding:0.35rem 0.75rem;cursor:pointer;font-size:0.78rem;
        display:flex;align-items:center;gap:0.4rem;
        border-left:2px solid transparent;
        transition:background 0.1s;
      }
      .pl-item:hover { background:var(--surface2) }
      .pl-item.active {
        background:var(--surface2);
        border-left-color:var(--accent);
        font-weight:600;
      }
      .pl-badge {
        margin-left:auto;font-size:0.6rem;padding:0.1rem 0.3rem;
        border-radius:3px;background:var(--surface3,rgba(128,128,128,.15));
        color:var(--muted);white-space:nowrap;flex-shrink:0
      }
      .pl-prop-row {
        display:flex;align-items:center;gap:0.75rem;
        padding:0.3rem 0;font-size:0.78rem
      }
      .pl-prop-label {
        width:180px;flex-shrink:0;color:var(--muted);font-size:0.75rem
      }
      .pl-stage-row {
        display:grid;grid-template-columns:110px 130px 70px 140px 1fr;
        gap:0.4rem;font-size:0.72rem;padding:0.3rem 0;
        border-bottom:1px solid var(--border);align-items:start
      }
      .pl-stage-row.header { font-weight:700;color:var(--muted) }
      .pl-log {
        font-family:monospace;font-size:0.7rem;line-height:1.5;
        background:var(--surface2);border:1px solid var(--border);
        border-radius:4px;padding:0.5rem;height:220px;overflow-y:auto;
        color:var(--text)
      }
      .pl-log .log-error { color:#e74c3c }
      .pl-log .log-warn  { color:#f39c12 }
      .pl-stage-dots { display:flex;flex-direction:column;gap:0.35rem;margin:0.75rem 0 }
      .pl-dot-row {
        display:flex;align-items:center;gap:0.6rem;font-size:0.78rem
      }
      .pl-dot {
        width:10px;height:10px;border-radius:50%;flex-shrink:0;
        border:2px solid var(--border)
      }
      .pl-dot.done    { background:var(--green,#27ae60);border-color:var(--green,#27ae60) }
      .pl-dot.running { background:var(--accent);border-color:var(--accent);animation:pl-pulse 1s infinite }
      .pl-dot.error   { background:#e74c3c;border-color:#e74c3c }
      .pl-dot.pending { background:transparent }
      @keyframes pl-pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
      .pl-approval {
        border:2px solid #9b59b6;border-radius:6px;padding:0.75rem;
        margin:0.75rem 0;background:rgba(155,89,182,0.06)
      }
      .pl-hist-row {
        display:grid;grid-template-columns:160px 70px 80px 70px 80px;
        gap:0.25rem;font-size:0.72rem;padding:0.3rem 0;
        border-bottom:1px solid var(--border)
      }
      .pl-hist-row.header { font-weight:700;color:var(--muted) }
      .pl-stars span { cursor:pointer;font-size:1rem }
      .pl-stars span:hover { opacity:0.7 }
      .pl-section-hdr {
        display:flex;align-items:center;gap:0.5rem;
        padding:0.6rem 1.25rem;cursor:pointer;user-select:none;
        font-size:0.8rem;font-weight:600
      }
      .pl-section-hdr:hover { background:var(--surface2) }
    </style>
  `;

  _renderEmpty();
  await Promise.all([_loadPipelines(), _loadRoles()]);
}

// ── Left panel loaders ────────────────────────────────────────────────────────

async function _loadPipelines() {
  const el = document.getElementById('pl-pipelines-list');
  if (!el) return;
  try {
    const cfg = await api.agentRoles.pipelinesConfig(_project);
    const pipes = (cfg.pipelines || []).filter(p => p.activated && !p.error);
    if (!pipes.length) {
      el.innerHTML = '<div style="padding:0 0.75rem;color:var(--muted);font-size:0.72rem">No activated pipelines</div>';
      return;
    }
    el.innerHTML = pipes.map(p => `
      <div class="pl-item" data-type="pipeline" data-name="${_esc(p.name)}">
        <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">${_esc(p.name)}</span>
        <span class="pl-badge">${p.required_roles?.length || 0} stages</span>
      </div>
    `).join('');
    el.querySelectorAll('.pl-item').forEach(item => {
      item.addEventListener('click', () => _selectPipeline(item.dataset.name));
    });
  } catch (e) {
    el.innerHTML = `<div style="padding:0 0.75rem;color:#e74c3c;font-size:0.72rem">Error: ${e.message}</div>`;
  }
}

async function _loadRoles() {
  const el = document.getElementById('pl-roles-list');
  if (!el) return;
  try {
    const roles = await api.agentRoles.list(_project);
    const activated = (roles || []).filter(r => r.activated !== false);
    if (!activated.length) {
      el.innerHTML = '<div style="padding:0 0.75rem;color:var(--muted);font-size:0.72rem">No activated roles</div>';
      return;
    }
    el.innerHTML = activated.map(r => `
      <div class="pl-item" data-type="role" data-name="${_esc(r.name)}">
        <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">${_esc(r.name)}</span>
        <span class="pl-badge" style="text-transform:capitalize">${r.provider || 'claude'}</span>
      </div>
    `).join('');
    el.querySelectorAll('.pl-item').forEach(item => {
      item.addEventListener('click', () => _selectRole(item.dataset.name));
    });
  } catch (e) {
    el.innerHTML = `<div style="padding:0 0.75rem;color:#e74c3c;font-size:0.72rem">Error: ${e.message}</div>`;
  }
}

// ── Selection ─────────────────────────────────────────────────────────────────

async function _selectPipeline(name) {
  _markActive('pipeline', name);
  _runId = null;
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }

  const propsEl = document.getElementById('pl-props');
  propsEl.innerHTML = '<div style="color:var(--muted);font-size:0.8rem">Loading pipeline config…</div>';

  try {
    const cfg = await api.agentRoles.getPipelineConfig(name, _project);
    _selected = { type: 'pipeline', name, data: cfg };
    _renderPipelineProps(cfg);
    _renderExecSection(cfg);
    _renderHistSection();
  } catch (e) {
    propsEl.innerHTML = `<div style="color:#e74c3c;font-size:0.8rem">Error loading config: ${e.message}</div>`;
  }
}

async function _selectRole(name) {
  _markActive('role', name);
  _runId = null;
  if (_pollTimer) { clearInterval(_pollTimer); _pollTimer = null; }

  const propsEl = document.getElementById('pl-props');
  propsEl.innerHTML = '<div style="color:var(--muted);font-size:0.8rem">Loading role…</div>';

  document.getElementById('pl-exec').innerHTML = '';
  document.getElementById('pl-hist').innerHTML = '';

  try {
    const roles = await api.agentRoles.list(_project);
    const role  = (roles || []).find(r => r.name === name);
    _selected = { type: 'role', name, data: role };
    _renderRoleProps(role || { name });
  } catch (e) {
    propsEl.innerHTML = `<div style="color:#e74c3c;font-size:0.8rem">Error loading role: ${e.message}</div>`;
  }
}

function _markActive(type, name) {
  document.querySelectorAll('#pl-left .pl-item').forEach(el => {
    el.classList.toggle('active', el.dataset.type === type && el.dataset.name === name);
  });
}

function _renderEmpty() {
  document.getElementById('pl-props').innerHTML =
    '<div style="padding:2rem;color:var(--muted);font-size:0.85rem">Select a pipeline or role from the left panel.</div>';
  document.getElementById('pl-exec').innerHTML = '';
  document.getElementById('pl-hist').innerHTML = '';
}

// ── Section 1: Pipeline properties ───────────────────────────────────────────

function _renderPipelineProps(cfg) {
  const el = document.getElementById('pl-props');

  const stageKeys = (cfg.stages || []).map(s => s.key);
  const approvalOptions = ['<option value="">— none —</option>']
    .concat(stageKeys.map(k =>
      `<option value="${_esc(k)}" ${cfg.require_approval_after === k ? 'selected' : ''}>${_esc(k)}</option>`
    )).join('');

  el.innerHTML = `
    <div style="margin-bottom:1rem">
      <div style="display:flex;align-items:baseline;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.3rem">
        <span style="font-size:1rem;font-weight:700">${_esc(cfg.name)}</span>
        <span style="font-size:0.7rem;color:var(--muted);font-family:monospace">v${_esc(cfg.version)}</span>
        <span class="pl-badge">${(cfg.stages||[]).length} stages</span>
      </div>
      ${cfg.description ? `<div style="font-size:0.78rem;color:var(--muted);margin-bottom:0.75rem">${_esc(cfg.description)}</div>` : ''}
    </div>

    <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;
                color:var(--muted);margin-bottom:0.5rem">Properties</div>

    <div class="pl-prop-row">
      <span class="pl-prop-label">Max rejection retries</span>
      <input id="prop-max-retries" type="number" min="1" max="10"
             value="${cfg.max_rejection_retries ?? 2}"
             style="width:60px;background:var(--surface2);border:1px solid var(--border);
                    border-radius:4px;padding:0.2rem 0.4rem;color:var(--text);font-size:0.78rem">
      <span style="font-size:0.72rem;color:var(--muted)">times reviewer can reject before pipeline stops</span>
    </div>
    <div class="pl-prop-row">
      <span class="pl-prop-label">Continue on failure</span>
      <label style="display:flex;align-items:center;gap:0.4rem;cursor:pointer">
        <input id="prop-continue" type="checkbox" ${cfg.continue_on_failure ? 'checked' : ''}>
        <span style="font-size:0.78rem;color:var(--muted)">proceed to next stage even if a stage errors</span>
      </label>
    </div>
    <div class="pl-prop-row">
      <span class="pl-prop-label">Save to memory</span>
      <label style="display:flex;align-items:center;gap:0.4rem;cursor:pointer">
        <input id="prop-save-memory" type="checkbox" ${cfg.save_memory !== false ? 'checked' : ''}>
        <span style="font-size:0.78rem;color:var(--muted)">persist run output to project memory</span>
      </label>
    </div>
    <div class="pl-prop-row">
      <span class="pl-prop-label">Require approval after</span>
      <select id="prop-approval" style="background:var(--surface2);border:1px solid var(--border);
              border-radius:4px;padding:0.2rem 0.4rem;color:var(--text);font-size:0.78rem">
        ${approvalOptions}
      </select>
      <span style="font-size:0.72rem;color:var(--muted)">pause for human review before next stage</span>
    </div>

    <div id="pl-save-status" style="font-size:0.72rem;color:var(--muted);min-height:1rem;margin:0.25rem 0"></div>

    <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;
                color:var(--muted);margin:0.85rem 0 0.4rem">Stages</div>
    <div style="overflow-x:auto">
      <div class="pl-stage-row header" style="padding-bottom:0.4rem">
        <span>Stage</span><span>Role</span><span>Provider · Model</span><span>Temperature</span><span>System Prompt</span>
      </div>
      ${(cfg.stages || []).map(s => _renderStageRow(s)).join('') ||
        '<div style="color:var(--muted);font-size:0.75rem;padding:0.3rem 0">No stages defined</div>'}
    </div>
  `;

  // Auto-save on any property change
  const saveStatus = document.getElementById('pl-save-status');
  let _saveTimer = null;
  const _scheduleSave = () => {
    saveStatus.textContent = 'Unsaved changes…';
    saveStatus.style.color = 'var(--muted)';
    clearTimeout(_saveTimer);
    _saveTimer = setTimeout(() => _savePipelineProps(cfg.name, saveStatus), 800);
  };
  ['prop-max-retries','prop-continue','prop-save-memory','prop-approval'].forEach(id => {
    const inp = document.getElementById(id);
    if (inp) inp.addEventListener('change', _scheduleSave);
  });

  // System prompt expand/collapse
  el.querySelectorAll('[data-sp-toggle]').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.dataset.spToggle;
      const preview = document.getElementById(`sp-preview-${key}`);
      const full    = document.getElementById(`sp-full-${key}`);
      if (preview && full) {
        const expanded = full.style.display !== 'none';
        preview.style.display = expanded ? '' : 'none';
        full.style.display    = expanded ? 'none' : '';
        btn.textContent       = expanded ? '▸' : '▾';
      }
    });
  });
}

function _renderStageRow(s) {
  const provModel = [s.role_provider, s.role_model].filter(Boolean).join(' · ') || '—';
  const temp = s.role_temperature != null
    ? Number(s.role_temperature).toFixed(2)
    : (s.temperature_override != null ? `${s.temperature_override} (override)` : 'default');

  const sp = (s.role_system_prompt || '').trim();
  const spPreview = sp.slice(0, 90).replace(/\n/g, ' ') + (sp.length > 90 ? '…' : '');
  const spFull    = _esc(sp);
  const key       = _esc(s.key);

  return `
    <div class="pl-stage-row">
      <span style="font-family:monospace;font-weight:600">${_esc(s.key)}</span>
      <span>
        <span style="color:var(--text)">${_esc(s.role)}</span>
      </span>
      <span style="font-size:0.7rem;color:var(--muted);font-family:monospace">${_esc(provModel)}</span>
      <span style="font-size:0.7rem;color:var(--muted)">${_esc(temp)}</span>
      <span style="font-size:0.7rem">
        ${sp ? `
          <span id="sp-preview-${key}" style="color:var(--muted)">
            ${_esc(spPreview)}
            <button data-sp-toggle="${key}"
                    style="background:none;border:none;cursor:pointer;color:var(--accent);
                           font-size:0.68rem;padding:0 0.2rem">▸</button>
          </span>
          <pre id="sp-full-${key}" style="display:none;margin:0.3rem 0 0;
               font-family:monospace;font-size:0.68rem;line-height:1.45;
               background:var(--surface2);border:1px solid var(--border);
               border-radius:3px;padding:0.4rem;white-space:pre-wrap;
               word-break:break-word;max-height:180px;overflow-y:auto">${spFull}</pre>
        ` : '<span style="color:var(--muted)">—</span>'}
      </span>
    </div>
  `;
}

async function _savePipelineProps(pipelineName, statusEl) {
  const maxRetries = parseInt(document.getElementById('prop-max-retries')?.value || '2', 10);
  const continueOn = document.getElementById('prop-continue')?.checked ?? false;
  const saveMem    = document.getElementById('prop-save-memory')?.checked ?? true;
  const approval   = document.getElementById('prop-approval')?.value || null;

  const body = {
    max_rejection_retries:  maxRetries,
    continue_on_failure:    continueOn,
    save_memory:            saveMem,
    require_approval_after: approval || null,
  };

  try {
    await api.agentRoles.patchPipeline(pipelineName, body, _project);
    if (statusEl) { statusEl.textContent = 'Saved'; statusEl.style.color = 'var(--green,#27ae60)'; }
    setTimeout(() => { if (statusEl) { statusEl.textContent = ''; statusEl.style.color = 'var(--muted)'; } }, 2000);
  } catch (e) {
    if (statusEl) { statusEl.textContent = `Save error: ${e.message}`; statusEl.style.color = '#e74c3c'; }
  }
}

// ── Section 1: Role properties ─────────────────────────────────────────────

function _renderRoleProps(role) {
  const el = document.getElementById('pl-props');
  const sp = role.system_prompt || '';
  el.innerHTML = `
    <div style="margin-bottom:1rem">
      <div style="display:flex;align-items:baseline;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.3rem">
        <span style="font-size:1rem;font-weight:700">${_esc(role.name)}</span>
        ${role.provider ? `<span class="pl-badge" style="text-transform:capitalize">${_esc(role.provider)}${role.model ? ' · ' + _esc(role.model) : ''}</span>` : ''}
      </div>
      ${role.description ? `<div style="font-size:0.78rem;color:var(--muted);margin-bottom:0.75rem">${_esc(role.description)}</div>` : ''}
    </div>

    ${sp ? `
    <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;
                color:var(--muted);margin-bottom:0.4rem">System Prompt</div>
    <pre style="font-family:monospace;font-size:0.7rem;line-height:1.5;
                background:var(--surface2);border:1px solid var(--border);
                border-radius:4px;padding:0.6rem;max-height:200px;overflow-y:auto;
                white-space:pre-wrap;word-break:break-word;color:var(--text)">${_esc(sp)}</pre>
    ` : ''}

    <div style="margin-top:0.75rem">
      <a href="#" onclick="window._nav && window._nav('prompts');return false"
         style="font-size:0.78rem;color:var(--accent)">Open in Roles editor →</a>
    </div>
  `;
}

// ── Section 2: Execution ──────────────────────────────────────────────────────

function _renderExecSection(cfg) {
  const el = document.getElementById('pl-exec');
  _execVisible = true;
  el.innerHTML = `
    <div class="pl-section-hdr" id="pl-exec-hdr">
      <span id="pl-exec-arrow">▼</span>
      <span id="pl-exec-title">New Run</span>
    </div>
    <div id="pl-exec-body" style="padding:0 1.25rem 1rem">
      <!-- Input mode -->
      <div style="display:flex;gap:1.25rem;align-items:center;margin-bottom:0.6rem;font-size:0.78rem">
        <label style="display:flex;align-items:center;gap:0.35rem;cursor:pointer">
          <input type="radio" name="pl-input-mode" value="prompt" checked> Prompt
        </label>
        <label style="display:flex;align-items:center;gap:0.35rem;cursor:pointer">
          <input type="radio" name="pl-input-mode" value="file"> File
        </label>
      </div>

      <!-- Prompt input -->
      <div id="pl-input-prompt">
        <textarea id="pl-task-input" rows="4"
          placeholder="Describe the task for this pipeline run…"
          style="width:100%;box-sizing:border-box;background:var(--surface2);
                 border:1px solid var(--border);border-radius:4px;padding:0.5rem;
                 color:var(--text);font-size:0.8rem;resize:vertical;font-family:inherit">
        </textarea>
      </div>

      <!-- File input -->
      <div id="pl-input-file" style="display:none">
        <div style="margin-bottom:0.4rem;font-size:0.75rem;color:var(--muted)">Pick from project docs:</div>
        <select id="pl-doc-select" style="width:100%;background:var(--surface2);border:1px solid var(--border);
                border-radius:4px;padding:0.35rem 0.5rem;color:var(--text);font-size:0.78rem;margin-bottom:0.5rem">
          <option value="">— loading docs… —</option>
        </select>
        <div style="margin-bottom:0.4rem;font-size:0.75rem;color:var(--muted)">Or upload a file:</div>
        <input id="pl-file-upload" type="file" style="font-size:0.78rem">
        <div id="pl-file-name" style="font-size:0.72rem;color:var(--muted);margin-top:0.3rem"></div>
      </div>

      <!-- Run button -->
      <div style="display:flex;gap:0.75rem;align-items:center;margin-top:0.6rem">
        <button id="pl-run-btn" class="btn btn-primary btn-sm"
                style="font-size:0.78rem;padding:0.3rem 0.8rem">▶ Run</button>
        <button id="pl-cancel-btn" class="btn btn-ghost btn-sm"
                style="font-size:0.78rem;display:none">■ Cancel</button>
        <span id="pl-run-error" style="font-size:0.75rem;color:#e74c3c"></span>
      </div>

      <!-- Progress -->
      <div id="pl-progress" style="display:none;margin-top:1rem">
        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;
                    color:var(--muted);margin-bottom:0.4rem">Progress</div>
        <div id="pl-stage-dots" class="pl-stage-dots"></div>
        <div id="pl-rejection-counter" style="font-size:0.72rem;color:var(--muted)"></div>

        <div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;
                    color:var(--muted);margin:0.6rem 0 0.3rem">Live Log</div>
        <div id="pl-log" class="pl-log"></div>

        <!-- Approval gate -->
        <div id="pl-approval-gate" style="display:none" class="pl-approval">
          <div style="font-weight:600;font-size:0.82rem;margin-bottom:0.4rem;color:#9b59b6">
            Approval Required
          </div>
          <div id="pl-approval-msg" style="font-size:0.78rem;color:var(--text);margin-bottom:0.5rem"></div>
          <div id="pl-approval-preview" style="font-family:monospace;font-size:0.7rem;
               background:var(--surface3,rgba(128,128,128,.1));border-radius:4px;padding:0.5rem;
               max-height:120px;overflow-y:auto;margin-bottom:0.6rem;white-space:pre-wrap;
               word-break:break-word"></div>
          <textarea id="pl-approval-feedback" rows="2" placeholder="Feedback (optional)…"
            style="width:100%;box-sizing:border-box;background:var(--surface2);
                   border:1px solid var(--border);border-radius:4px;padding:0.35rem;
                   color:var(--text);font-size:0.78rem;margin-bottom:0.5rem;resize:vertical"></textarea>
          <div style="display:flex;gap:0.5rem">
            <button id="pl-approve-btn" class="btn btn-primary btn-sm" style="font-size:0.78rem">
              ✓ Approve and continue
            </button>
            <button id="pl-reject-btn" class="btn btn-ghost btn-sm"
                    style="font-size:0.78rem;color:#e74c3c;border-color:#e74c3c">
              ✗ Reject
            </button>
          </div>
        </div>
      </div>
    </div>
  `;

  // Toggle collapse
  document.getElementById('pl-exec-hdr').addEventListener('click', () => {
    _execVisible = !_execVisible;
    document.getElementById('pl-exec-body').style.display = _execVisible ? '' : 'none';
    document.getElementById('pl-exec-arrow').textContent  = _execVisible ? '▼' : '▶';
  });

  // Input mode toggle
  document.querySelectorAll('input[name="pl-input-mode"]').forEach(r => {
    r.addEventListener('change', () => {
      const isFile = r.value === 'file' && r.checked;
      document.getElementById('pl-input-prompt').style.display = isFile ? 'none' : '';
      document.getElementById('pl-input-file').style.display   = isFile ? '' : 'none';
      if (isFile) _loadDocs();
    });
  });

  // File upload label
  document.getElementById('pl-file-upload')?.addEventListener('change', e => {
    const f = e.target.files?.[0];
    document.getElementById('pl-file-name').textContent = f ? `Selected: ${f.name}` : '';
  });

  // Run button
  document.getElementById('pl-run-btn').addEventListener('click', () => _startRun(cfg));

  // Approval buttons
  document.getElementById('pl-approve-btn')?.addEventListener('click', () => _sendApproval(true));
  document.getElementById('pl-reject-btn')?.addEventListener('click',  () => _sendApproval(false));
}

async function _loadDocs() {
  const sel = document.getElementById('pl-doc-select');
  if (!sel) return;
  try {
    const docs = await api.documents.list(_project);
    sel.innerHTML = '<option value="">— select a document —</option>' +
      (docs || []).map(d => `<option value="${_esc(d.path)}">${_esc(d.path)}</option>`).join('');
  } catch (_) {
    sel.innerHTML = '<option value="">— could not load docs —</option>';
  }
}

async function _startRun(cfg) {
  const mode = document.querySelector('input[name="pl-input-mode"]:checked')?.value || 'prompt';
  let task = '';
  let inputFiles = [];

  if (mode === 'file') {
    const docSel = document.getElementById('pl-doc-select');
    const fileEl = document.getElementById('pl-file-upload');
    if (docSel?.value) {
      task = `Process document: ${docSel.value}`;
      inputFiles = [{ path: docSel.value }];
    } else if (fileEl?.files?.[0]) {
      task = `Process uploaded file: ${fileEl.files[0].name}`;
      inputFiles = [{ name: fileEl.files[0].name }];
    }
  } else {
    task = (document.getElementById('pl-task-input')?.value || '').trim();
  }

  if (!task) {
    const errEl = document.getElementById('pl-run-error');
    if (errEl) { errEl.textContent = 'Please enter a task or select a file.'; }
    return;
  }

  document.getElementById('pl-run-error').textContent = '';
  document.getElementById('pl-run-btn').style.display    = 'none';
  document.getElementById('pl-cancel-btn').style.display = '';
  document.getElementById('pl-exec-title').textContent   = 'Running…';
  document.getElementById('pl-progress').style.display   = '';

  // Pre-populate stage dots
  _renderStageDots(cfg.stages || [], []);
  _clearLog();

  try {
    const res = await api.agents.startPipelineRun({
      pipeline: cfg.name,
      task,
      project:  _project,
      input_files: inputFiles,
    });
    _runId = res.run_id;
    _appendLog(`Run started: ${_runId}`, 'info');
    _startPolling(cfg);
  } catch (e) {
    document.getElementById('pl-run-error').textContent = `Error: ${e.message}`;
    _resetRunUI();
  }
}

function _startPolling(cfg) {
  if (_pollTimer) clearInterval(_pollTimer);
  _pollTimer = setInterval(async () => {
    if (!_runId) { clearInterval(_pollTimer); return; }
    try {
      const data = await api.agents.getPipelineRun(_runId);
      _updateProgress(cfg, data);
      if (['done','error','rejected','approved'].includes(data.status) && data.status !== 'running' && data.status !== 'waiting_approval') {
        clearInterval(_pollTimer);
        _pollTimer = null;
        _onRunComplete(data);
      }
    } catch (e) {
      _appendLog(`Poll error: ${e.message}`, 'error');
    }
  }, 1500);
}

function _updateProgress(cfg, data) {
  _renderStageDots(cfg.stages || [], data.stages || []);

  // Log new lines from stages
  const logEl = document.getElementById('pl-log');
  if (logEl) {
    for (const stage of (data.stages || [])) {
      for (const entry of (stage.log_lines || [])) {
        const key = `${stage.stage_key}:${entry.ts}`;
        if (!logEl.dataset.seen) logEl.dataset.seen = '';
        if (!logEl.dataset.seen.includes(key)) {
          logEl.dataset.seen += key + '|';
          _appendLog(`[${stage.stage_key}] ${entry.text}`, entry.level || 'info');
        }
      }
    }
  }

  // Approval gate
  const approvalEl = document.getElementById('pl-approval-gate');
  if (data.status === 'waiting_approval' && approvalEl) {
    approvalEl.style.display = '';
    const lastDoneStage = (data.stages || []).filter(s => s.status === 'done').at(-1);
    const msgEl = document.getElementById('pl-approval-msg');
    if (msgEl && lastDoneStage) {
      msgEl.textContent = `${lastDoneStage.stage_key} stage complete. Review output before next stage continues.`;
    }
    const previewEl = document.getElementById('pl-approval-preview');
    if (previewEl && lastDoneStage?.output_preview) {
      previewEl.textContent = lastDoneStage.output_preview;
    }
    document.getElementById('pl-exec-title').textContent = 'Waiting for Approval…';
  } else if (approvalEl) {
    approvalEl.style.display = 'none';
  }

  // Title update
  if (data.status === 'running') {
    document.getElementById('pl-exec-title').textContent = 'Running…';
  }
}

function _onRunComplete(data) {
  _appendLog(
    `Run complete. Verdict: ${data.final_verdict || data.status}. ` +
    `Cost: $${(data.total_cost_usd || 0).toFixed(4)}. ` +
    `Tokens: ${(data.total_input_tokens || 0) + (data.total_output_tokens || 0)}`,
    data.status === 'error' ? 'error' : 'info',
  );

  const title = data.final_verdict === 'approved' ? '✓ Approved'
    : data.final_verdict === 'rejected' ? '✗ Rejected'
    : data.status === 'error' ? '✗ Error'
    : '✓ Done';
  document.getElementById('pl-exec-title').textContent = title;

  _resetRunUI(false);
  _runId = null;

  // Reload history section
  if (_selected?.type === 'pipeline') _renderHistSection();
}

function _resetRunUI(hideProgress = true) {
  document.getElementById('pl-run-btn').style.display    = '';
  document.getElementById('pl-cancel-btn').style.display = 'none';
  if (hideProgress) document.getElementById('pl-progress').style.display = 'none';
  document.getElementById('pl-approval-gate').style.display = 'none';
}

async function _sendApproval(approved) {
  if (!_runId) return;
  const feedback = document.getElementById('pl-approval-feedback')?.value || '';
  try {
    await api.agents.approvePipelineRun(_runId, { approved, feedback });
    document.getElementById('pl-approval-gate').style.display = 'none';
  } catch (e) {
    _appendLog(`Approval error: ${e.message}`, 'error');
  }
}

// ── Stage dots ────────────────────────────────────────────────────────────────

function _renderStageDots(stageDefs, stageResults) {
  const el = document.getElementById('pl-stage-dots');
  if (!el) return;

  const resultMap = {};
  for (const sr of stageResults) resultMap[sr.stage_key] = sr;

  el.innerHTML = stageDefs.map(s => {
    const sr  = resultMap[s.key] || {};
    const st  = sr.status || 'pending';
    const dur = sr.duration_s != null ? `${sr.duration_s.toFixed(1)}s` : '';
    const cost = sr.cost_usd != null ? `$${Number(sr.cost_usd).toFixed(4)}` : '';
    const tok  = (sr.input_tokens || 0) + (sr.output_tokens || 0);
    const tokStr = tok > 0 ? `${_fmtNum(tok)} tok` : '';
    return `
      <div class="pl-dot-row">
        <div class="pl-dot ${st}" title="${st}"></div>
        <span style="font-family:monospace;font-size:0.76rem;min-width:80px">${_esc(s.key)}</span>
        <span style="font-size:0.7rem;color:var(--muted);min-width:60px">[${st}]</span>
        ${dur    ? `<span style="font-size:0.7rem;color:var(--muted)">${dur}</span>` : ''}
        ${cost   ? `<span style="font-size:0.7rem;color:var(--accent)">${cost}</span>` : ''}
        ${tokStr ? `<span style="font-size:0.7rem;color:var(--muted)">${tokStr}</span>` : ''}
      </div>
    `;
  }).join('');
}

function _appendLog(text, level = 'info') {
  const el = document.getElementById('pl-log');
  if (!el) return;
  const ts  = new Date().toLocaleTimeString();
  const cls = level === 'error' ? 'log-error' : level === 'warn' ? 'log-warn' : '';
  el.insertAdjacentHTML('beforeend', `<div class="${cls}">${ts} ${_esc(text)}</div>`);
  el.scrollTop = el.scrollHeight;
}

function _clearLog() {
  const el = document.getElementById('pl-log');
  if (el) { el.innerHTML = ''; el.dataset.seen = ''; }
}

// ── Section 3: History ────────────────────────────────────────────────────────

function _renderHistSection() {
  const el = document.getElementById('pl-hist');
  if (!el || !_selected) return;

  el.innerHTML = `
    <div class="pl-section-hdr" id="pl-hist-hdr">
      <span id="pl-hist-arrow">${_histVisible ? '▾' : '▸'}</span>
      <span>History</span>
      <span style="margin-left:auto;font-size:0.72rem;color:var(--muted)">
        Show:
        <button class="btn btn-ghost btn-xs" style="font-size:0.7rem;padding:0.05rem 0.3rem" onclick="window._plHistLimit(10)">10</button>
        <button class="btn btn-ghost btn-xs" style="font-size:0.7rem;padding:0.05rem 0.3rem" onclick="window._plHistLimit(20)">20</button>
        <button class="btn btn-ghost btn-xs" style="font-size:0.7rem;padding:0.05rem 0.3rem" onclick="window._plHistLimit(50)">50</button>
      </span>
    </div>
    <div id="pl-hist-body" style="display:${_histVisible ? '' : 'none'};padding:0 1.25rem 1rem">
      <div style="color:var(--muted);font-size:0.78rem">Loading…</div>
    </div>
  `;

  document.getElementById('pl-hist-hdr').addEventListener('click', e => {
    if (e.target.tagName === 'BUTTON') return;
    _histVisible = !_histVisible;
    document.getElementById('pl-hist-body').style.display = _histVisible ? '' : 'none';
    document.getElementById('pl-hist-arrow').textContent  = _histVisible ? '▾' : '▸';
    if (_histVisible) _loadHistory();
  });

  window._plHistLimit = (n) => { _histLimit = n; _loadHistory(); };

  if (_histVisible) _loadHistory();
}

async function _loadHistory() {
  const el = document.getElementById('pl-hist-body');
  if (!el || !_selected) return;

  const pipelineName = _selected.type === 'pipeline' ? _selected.name : null;
  if (!pipelineName) { el.innerHTML = '<div style="color:var(--muted);font-size:0.78rem">Select a pipeline to see run history.</div>'; return; }

  try {
    const data = await api.agents.listPipelineRuns(_project, pipelineName, _histLimit);
    const runs = data.runs || [];
    if (!runs.length) {
      el.innerHTML = '<div style="color:var(--muted);font-size:0.78rem">No runs yet.</div>';
      return;
    }
    el.innerHTML = `
      <div class="pl-hist-row header">
        <span>Run At</span><span>Duration</span><span>Tokens</span><span>Cost</span><span>Score</span>
      </div>
      ${runs.map(r => _renderHistRow(r)).join('')}
    `;
    // Bind star clicks
    el.querySelectorAll('.pl-stars span').forEach(star => {
      star.addEventListener('click', async () => {
        const runId = star.closest('[data-run-id]')?.dataset.runId;
        const score = parseInt(star.dataset.score, 10);
        if (!runId) return;
        try {
          await api.agents.scoreRun(runId, score);
          _loadHistory();
        } catch (e) {
          console.warn('score error', e);
        }
      });
    });
  } catch (e) {
    el.innerHTML = `<div style="color:#e74c3c;font-size:0.78rem">Error: ${e.message}</div>`;
  }
}

function _renderHistRow(r) {
  const startedAt = r.started_at ? new Date(r.started_at).toLocaleString() : '—';
  const dur = r.duration_s != null ? _fmtDur(r.duration_s) : '—';
  const tok  = (r.total_input_tokens || 0) + (r.total_output_tokens || 0);
  const cost = r.total_cost_usd != null ? `$${Number(r.total_cost_usd).toFixed(4)}` : '—';
  const score = r.score ?? null;
  const stars = [1,2,3,4,5].map(n =>
    `<span data-score="${n}" title="Rate ${n}" style="color:${score != null && n <= score ? '#f39c12' : 'var(--muted)'}">★</span>`
  ).join('');

  return `
    <div class="pl-hist-row" data-run-id="${r.run_id}">
      <span style="font-size:0.7rem;color:var(--muted)">${startedAt}</span>
      <span>${dur}</span>
      <span>${_fmtNum(tok)}</span>
      <span style="color:var(--accent)">${cost}</span>
      <span class="pl-stars" style="display:flex;gap:0.1rem">${stars}</span>
    </div>
    <div style="font-size:0.7rem;color:var(--muted);padding:0.1rem 0 0.5rem;
                border-bottom:1px solid var(--border)">
      Verdict: <strong>${r.final_verdict || r.status || '—'}</strong>
      &nbsp;|&nbsp; Task: ${_esc((r.task || '').slice(0, 80))}
      &nbsp;|&nbsp;
      <a href="#" onclick="window._nav && window._nav('workflow');return false"
         style="color:var(--accent);font-size:0.7rem">Open in History →</a>
    </div>
  `;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function _fmtNum(n) {
  if (n == null) return '—';
  return n >= 1000 ? (n / 1000).toFixed(1) + 'k' : String(n);
}

function _fmtDur(secs) {
  if (secs == null) return '—';
  const s = Math.round(secs);
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}
