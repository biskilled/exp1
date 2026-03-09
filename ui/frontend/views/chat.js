import { state, setState } from '../stores/state.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';

const PROVIDERS = [
  { id: 'claude',   label: 'Claude'   },
  { id: 'openai',   label: 'OpenAI'   },
  { id: 'deepseek', label: 'DeepSeek' },
  { id: 'gemini',   label: 'Gemini'   },
  { id: 'grok',     label: 'Grok'     },
];

let _sessionId   = null;
let _provider    = 'claude';
let _streaming   = false;
let _roleOptions = [];       // { path, name } — loaded when project is open
let _workflowOptions = [];   // workflow names — loaded when project is open
let _sessionCache = [];      // merged session list (ui + cli + workflow)

// Session tags — mandatory: phase
// Changing phase resets _sessionId → forces new session on next send
let _sessionTags = { phase: '' };

// Entity tags applied to current session via the + Tag picker
let _appliedEntities  = []; // [{value_id, category_name, name, color, icon}]
let _suggestedTags    = []; // [{name, category, is_new}] — LLM suggestions from /memory
let _pickerOpen       = false;
let _pickerType      = 'feature';
let _pickerValues    = []; // loaded for current picker type

const _ENTITY_TYPES = [
  { id: 'feature', icon: '⬡', color: '#27ae60' },
  { id: 'bug',     icon: '⚠', color: '#e74c3c' },
  { id: 'task',    icon: '✓', color: '#4a90e2' },
];

const PHASE_OPTIONS = [
  { value: '', label: '⚠ Phase (required)' },
  { value: 'discovery',    label: 'Discovery'    },
  { value: 'development',  label: 'Development'  },
  { value: 'testing',      label: 'Testing'      },
  { value: 'review',       label: 'Review'       },
  { value: 'production',   label: 'Production'   },
  { value: 'maintenance',  label: 'Maintenance'  },
  { value: 'bugfix',       label: 'Bug Fix'      },
];

export function renderChat(container) {
  _provider = state.currentProject?.default_provider || 'claude';

  container.className  = 'view active';
  container.style.cssText = 'display:flex;flex-direction:column;overflow:hidden;height:100%';

  const _savedPanelW = parseInt(localStorage.getItem('aicli_chat_sessions_w') || '190', 10);

  container.innerHTML = `
    <div style="display:flex;flex:1;overflow:hidden;min-height:0">

      <!-- Session sidebar -->
      <div id="chat-session-panel"
           style="width:${_savedPanelW}px;border-right:1px solid var(--border);background:var(--surface);
                  display:flex;flex-direction:column;flex-shrink:0;overflow:hidden">
        <div style="padding:0.6rem;border-bottom:1px solid var(--border)">
          <button class="btn btn-ghost btn-sm" style="width:100%;font-size:0.7rem"
            onclick="window._chatNew()">+ New Chat</button>
        </div>
        <div style="padding:0.35rem 0.6rem 0.15rem;font-size:0.55rem;color:var(--muted);
                    letter-spacing:2px;text-transform:uppercase">Sessions</div>
        <div id="chat-sessions" style="flex:1;overflow-y:auto;padding:0.15rem 0.4rem 0.5rem"></div>
      </div>

      <!-- Session panel resize handle -->
      <div id="chat-resize-handle"
           style="width:4px;cursor:col-resize;background:var(--border);flex-shrink:0"
           title="Drag to resize panel"></div>

      <!-- Main chat -->
      <div style="flex:1;display:flex;flex-direction:column;min-width:0;overflow:hidden">

        <!-- Provider / context bar -->
        <div style="display:flex;align-items:center;gap:0.75rem;padding:0.45rem 1rem;
                    border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0">
          <span style="font-size:0.62rem;color:var(--muted)">LLM:</span>
          <select id="chat-provider"
            style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.68rem;padding:0.2rem 0.5rem;
                   border-radius:var(--radius);cursor:pointer;outline:none">
            ${PROVIDERS.map(p => `
              <option value="${p.id}" ${p.id === _provider ? 'selected' : ''}>
                ${p.label}
              </option>`).join('')}
          </select>
          <span style="font-size:0.62rem;color:var(--muted)">Role:</span>
          <select id="chat-role"
            style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                   font-family:var(--font);font-size:0.68rem;padding:0.2rem 0.5rem;
                   border-radius:var(--radius);cursor:pointer;outline:none">
            <option value="">Default (CLAUDE.md)</option>
          </select>
          ${state.currentProject?.name ? `
            <span style="margin-left:auto;font-size:0.62rem;color:var(--muted)">
              <span style="color:var(--accent)">${state.currentProject.name}</span>
            </span>` : ''}
        </div>

        <!-- Session tag bar: phase (mandatory) + entity chips (optional) -->
        <div id="chat-tag-bar"
          style="display:flex;align-items:center;gap:0.45rem;padding:0.3rem 0.75rem;
                 border-bottom:1px solid var(--border);background:var(--surface2);flex-shrink:0;
                 flex-wrap:nowrap;min-height:2rem;overflow:hidden">
          <span style="font-size:0.55rem;color:var(--muted);letter-spacing:1px;text-transform:uppercase;white-space:nowrap;flex-shrink:0">Session:</span>

          <!-- Phase (mandatory) -->
          <select id="chat-phase-sel"
            style="background:var(--bg);border:1px solid var(--red,#e74c3c);color:var(--text);
                   font-family:var(--font);font-size:0.64rem;padding:0.15rem 0.35rem;
                   border-radius:var(--radius);cursor:pointer;outline:none;max-width:118px;flex-shrink:0"
            title="Mandatory: set a phase for this session">
            ${PHASE_OPTIONS.map(o => `<option value="${_esc(o.value)}">${_esc(o.label)}</option>`).join('')}
          </select>

          <!-- Applied entity chips (feature/bug/task) -->
          <div id="chat-entity-chips"
               style="display:flex;gap:0.25rem;flex-wrap:wrap;align-items:center;flex:1;min-width:0;overflow:hidden"></div>

          <!-- Add tag button -->
          <button id="chat-add-tag-btn"
            onclick="window._toggleEntityPicker()"
            style="background:var(--surface);border:1px solid var(--border);color:var(--text2);
                   font-family:var(--font);font-size:0.58rem;padding:0.12rem 0.4rem;
                   border-radius:var(--radius);cursor:pointer;white-space:nowrap;flex-shrink:0;outline:none"
            title="Tag this session with a feature, bug, or task">+ Tag</button>

          <span id="chat-tag-status"
                style="font-size:0.58rem;color:var(--red,#e74c3c);white-space:nowrap;flex-shrink:0">⚠ phase</span>
          <span style="font-size:0.58rem;color:var(--muted);cursor:pointer;white-space:nowrap;flex-shrink:0"
            onclick="window._chatNew()" title="Start new session">+ new</span>
        </div>

        <!-- Entity picker panel (shown when + Tag is clicked) -->
        <div id="chat-entity-picker"
          style="display:none;flex-direction:column;gap:0.4rem;padding:0.5rem 0.75rem;
                 border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0">
          <!-- Type tabs -->
          <div style="display:flex;gap:0.3rem;align-items:center">
            <span style="font-size:0.55rem;color:var(--muted);flex-shrink:0">Type:</span>
            ${_ENTITY_TYPES.map(t => `
              <button id="picker-tab-${t.id}" onclick="window._pickerSetType('${t.id}')"
                style="background:transparent;border:1px solid var(--border);color:var(--muted);
                       font-size:0.6rem;padding:0.1rem 0.4rem;border-radius:var(--radius);
                       cursor:pointer;font-family:var(--font);outline:none;transition:all 0.1s">
                ${t.icon} ${t.id}
              </button>`).join('')}
            <button onclick="window._closeEntityPicker()"
              style="margin-left:auto;background:none;border:none;color:var(--muted);
                     cursor:pointer;font-size:0.8rem;padding:0 0.25rem">✕</button>
          </div>
          <!-- Existing dropdown + New input + Save -->
          <div style="display:flex;gap:0.5rem;align-items:flex-end;flex-wrap:wrap">
            <div style="flex:1;min-width:140px">
              <div style="font-size:0.55rem;color:var(--muted);margin-bottom:0.12rem">Existing (open):</div>
              <select id="picker-existing-sel"
                style="width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);
                       font-family:var(--font);font-size:0.64rem;padding:0.18rem 0.4rem;
                       border-radius:var(--radius);outline:none">
                <option value="">Loading…</option>
              </select>
            </div>
            <div style="flex:1;min-width:140px">
              <div style="font-size:0.55rem;color:var(--muted);margin-bottom:0.12rem">Or create new:</div>
              <input id="picker-new-inp" type="text" placeholder="New name…"
                onkeydown="if(event.key==='Enter')window._saveEntityTag()"
                style="width:100%;background:var(--bg);border:1px solid var(--border);color:var(--text);
                       font-family:var(--font);font-size:0.64rem;padding:0.18rem 0.4rem;
                       border-radius:var(--radius);outline:none;box-sizing:border-box">
            </div>
            <button onclick="window._saveEntityTag()"
              style="background:var(--accent);border:none;color:#fff;font-family:var(--font);
                     font-size:0.64rem;padding:0.22rem 0.65rem;border-radius:var(--radius);
                     cursor:pointer;white-space:nowrap;outline:none;flex-shrink:0">Save</button>
          </div>
          <div id="picker-msg" style="font-size:0.6rem;color:var(--muted);min-height:0.8rem"></div>
        </div>

        <!-- Messages -->
        <div id="chat-messages"
          style="flex:1;overflow-y:auto;padding:1.25rem;display:flex;flex-direction:column;gap:1rem">
        </div>

        <!-- Input -->
        <div style="padding:0.75rem 1rem;border-top:1px solid var(--border);flex-shrink:0">
          <div style="position:relative">
            <div id="chat-cmd-popup-wrap"></div>
            <div id="chat-input-box"
              style="display:flex;align-items:flex-end;gap:0.75rem;background:var(--surface2);
                     border:1px solid var(--border);border-radius:var(--radius);
                     padding:0.6rem 0.75rem 0.6rem 1rem;transition:border-color 0.15s">
              <span style="color:var(--accent);font-size:0.85rem;margin-bottom:3px">❯</span>
              <textarea id="chat-input"
                style="flex:1;background:none;border:none;color:var(--text);font-family:var(--font);
                       font-size:0.8rem;line-height:1.6;resize:none;outline:none;max-height:140px;
                       user-select:text;-webkit-user-select:text"
                placeholder="Message… (/ for commands · Enter to send · Shift+Enter for newline)"
                rows="1"></textarea>
              <button id="chat-send-btn"
                style="background:var(--accent);border:none;color:#fff;width:28px;height:28px;
                       border-radius:6px;cursor:pointer;font-size:1rem;flex-shrink:0;
                       display:flex;align-items:center;justify-content:center;transition:opacity 0.15s"
                onclick="window._chatSend()">↑</button>
            </div>
          </div>
          <div style="margin-top:0.35rem;font-size:0.6rem;color:var(--muted)">
            / for commands · Enter to send · Shift+Enter for newline
          </div>
        </div>

      </div>
    </div>
  `;

  document.getElementById('chat-provider')?.addEventListener('change', e => {
    _provider = e.target.value;
  });

  document.getElementById('chat-role')?.addEventListener('change', async e => {
    const path = e.target.value;
    const proj = state.currentProject;
    if (!proj) return;
    if (!path) {
      // Reset to CLAUDE.md / project default
      const p = await api.getProject(proj.name).catch(() => proj);
      setState({ currentProject: { ...state.currentProject, system_prompt: p.claude_md || p.project_md || '' } });
    } else {
      try {
        const data = await api.readPrompt(path, proj.name);
        setState({ currentProject: { ...state.currentProject, system_prompt: data.content || '' } });
        toast(`Role: ${path}`, 'info');
      } catch (e) {
        toast(`Could not load role: ${e.message}`, 'error');
      }
    }
  });

  // ── Session tag bar listeners ────────────────────────────────────────────
  _setupTagBar();

  _setupInput();
  _initChatResize();
  _loadSessions();
  // Load roles+workflows first, then render welcome screen so buttons are populated
  _loadRolesAndWorkflows().then(() => _showWelcome());
}

function _setupTagBar() {
  const phaseSel = document.getElementById('chat-phase-sel');
  if (!phaseSel) return;

  phaseSel.value = _sessionTags.phase || '';
  _updateTagBarStatus();
  _renderEntityChips();

  phaseSel.addEventListener('change', () => {
    const newPhase = phaseSel.value;
    if (newPhase !== (_sessionTags.phase || '')) {
      _sessionTags = { phase: newPhase };
      _sessionId = null;       // force new session
      _appliedEntities = [];   // clear chips for new session
      _suggestedTags = [];     // clear suggestions on session reset
      _renderEntityChips();
    }
    _updateTagBarStatus();
    _loadSessions();
  });

  // Expose picker functions globally
  window._toggleEntityPicker = _toggleEntityPicker;
  window._closeEntityPicker  = _closeEntityPicker;
  window._pickerSetType      = _pickerSetType;
  window._saveEntityTag      = _saveEntityTag;
}

function _updateTagBarStatus() {
  const phaseSel = document.getElementById('chat-phase-sel');
  const status   = document.getElementById('chat-tag-status');
  if (!phaseSel || !status) return;

  const hasPhase = !!(_sessionTags.phase);
  // Update phase dropdown border color
  phaseSel.style.borderColor = hasPhase ? 'var(--border)' : 'var(--red,#e74c3c)';
  // Update status text
  if (hasPhase) {
    const label = PHASE_OPTIONS.find(o => o.value === _sessionTags.phase)?.label || _sessionTags.phase;
    status.style.color = 'var(--green,#27ae60)';
    status.textContent = `✓ ${label}`;
  } else {
    status.style.color = 'var(--red,#e74c3c)';
    status.textContent = '⚠ phase';
  }
}

// Restore tag bar to reflect a loaded session's tags
function _restoreTagBar(tags) {
  _sessionTags = { phase: (tags?.phase) || '' };
  _appliedEntities = [];  // chips not persisted — clear on session load
  const phaseSel = document.getElementById('chat-phase-sel');
  if (phaseSel) phaseSel.value = _sessionTags.phase;
  _updateTagBarStatus();
  _renderEntityChips();
}

// ── Entity picker ─────────────────────────────────────────────────────────────

function _toggleEntityPicker() {
  if (_pickerOpen) { _closeEntityPicker(); return; }
  const panel = document.getElementById('chat-entity-picker');
  if (!panel) return;
  _pickerOpen = true;
  panel.style.display = 'flex';
  _pickerSetType('feature');
}

function _closeEntityPicker() {
  const panel = document.getElementById('chat-entity-picker');
  if (panel) panel.style.display = 'none';
  _pickerOpen = false;
}

async function _pickerSetType(type) {
  _pickerType = type;
  // Update tab button styles
  _ENTITY_TYPES.forEach(t => {
    const btn = document.getElementById(`picker-tab-${t.id}`);
    if (!btn) return;
    btn.style.background   = t.id === type ? 'var(--accent)22' : 'transparent';
    btn.style.color        = t.id === type ? 'var(--accent)'   : 'var(--muted)';
    btn.style.borderColor  = t.id === type ? 'var(--accent)'   : 'var(--border)';
  });

  const sel = document.getElementById('picker-existing-sel');
  const msg = document.getElementById('picker-msg');
  if (sel) sel.innerHTML = '<option value="">Loading…</option>';
  if (msg) msg.textContent = '';

  const project = state.currentProject?.name;
  if (!project) { if (msg) msg.textContent = 'No project open'; return; }

  try {
    const data = await api.entities.listValues(project, null, { category_name: type, status: 'active' });
    _pickerValues = data.values || [];
    if (sel) {
      sel.innerHTML = '<option value="">-- select existing --</option>' +
        _pickerValues.map(v =>
          `<option value="${v.id}">${_esc(v.name)}${v.event_count ? ` (${v.event_count})` : ''}</option>`
        ).join('');
    }
    if (msg && !_pickerValues.length) msg.textContent = `No active ${type}s yet — create one below.`;
  } catch (e) {
    if (msg) msg.textContent = e.message;
  }
}

async function _saveEntityTag() {
  const msg     = document.getElementById('picker-msg');
  const sel     = document.getElementById('picker-existing-sel');
  const inp     = document.getElementById('picker-new-inp');
  const selVal  = sel?.value;
  const newName = inp?.value?.trim();
  const project = state.currentProject?.name;

  if (msg) msg.textContent = '';
  if (!project) { if (msg) msg.textContent = 'No project open'; return; }
  if (!selVal && !newName) { if (msg) msg.textContent = 'Select existing or type a new name'; return; }

  if (!_sessionId) {
    if (msg) msg.textContent = 'Send a message first to start a session — then tag it';
    return;
  }

  if (msg) msg.textContent = 'Saving…';

  try {
    let body, entityInfo;
    const typeInfo = _ENTITY_TYPES.find(t => t.id === _pickerType) || _ENTITY_TYPES[0];

    if (selVal) {
      const found = _pickerValues.find(v => String(v.id) === selVal);
      body       = { session_id: _sessionId, project, value_id: parseInt(selVal, 10) };
      entityInfo = { value_id: parseInt(selVal, 10), category_name: _pickerType,
                     name: found?.name || selVal, color: typeInfo.color, icon: typeInfo.icon };
    } else {
      body       = { session_id: _sessionId, project, category_name: _pickerType, value_name: newName };
      entityInfo = { value_id: null, category_name: _pickerType,
                     name: newName, color: typeInfo.color, icon: typeInfo.icon };
    }

    const result = await api.entities.sessionTag(body);
    entityInfo.value_id = entityInfo.value_id || result.value_id;
    _appliedEntities.push(entityInfo);
    _renderEntityChips();
    _closeEntityPicker();
    if (inp) inp.value = '';
    if (msg) msg.textContent = '';
    toast(`Tagged: ${_pickerType}/${entityInfo.name} (${result.events_tagged || 0} events)`, 'success');
  } catch (e) {
    if (msg) msg.textContent = e.message;
  }
}

function _renderEntityChips() {
  const container = document.getElementById('chat-entity-chips');
  if (!container) return;

  // Applied (user-confirmed) chips — blue style
  const appliedHtml = _appliedEntities.map(e => `
    <span class="entity-chip user-tag"
          style="display:inline-flex;align-items:center;gap:0.18rem;
                 background:${e.color}22;border:1px solid ${e.color}55;color:${e.color};
                 border-radius:10px;padding:0.08rem 0.38rem;font-size:0.56rem;white-space:nowrap"
          title="${_esc(e.category_name)}/${_esc(e.name)}">
      ${_esc(e.icon)} ${_esc(e.name)}
    </span>`).join('');

  // Suggested chips — amber dashed style, with Accept / Dismiss buttons
  const suggestedHtml = _suggestedTags.map((s, idx) => `
    <span class="entity-chip suggested-tag"
          style="display:inline-flex;align-items:center;gap:0.18rem;
                 background:#fffbe6;border:1px dashed #d4a017;color:#8a6500;
                 border-radius:10px;padding:0.08rem 0.38rem;font-size:0.56rem;white-space:nowrap;font-style:italic"
          title="LLM suggestion: ${_esc(s.category)}/${_esc(s.name)} — click ✓ to accept">
      ✦ ${_esc(s.name)}
      <button onclick="window._acceptSuggestedTag(${idx})"
        style="border:none;background:none;cursor:pointer;color:#27ae60;font-size:0.6rem;padding:0 1px;line-height:1"
        title="Accept tag">✓</button>
      <button onclick="window._dismissSuggestedTag(${idx})"
        style="border:none;background:none;cursor:pointer;color:#888;font-size:0.6rem;padding:0 1px;line-height:1"
        title="Dismiss">✕</button>
    </span>`).join('');

  container.innerHTML = appliedHtml + suggestedHtml;
}

window._acceptSuggestedTag = async (idx) => {
  const s = _suggestedTags[idx];
  if (!s) return;
  const project = state.currentProject?.name;
  if (!project || !_sessionId) {
    toast('Send a message first to start a session', 'error');
    return;
  }
  try {
    const result = await api.entities.sessionTag({
      session_id: _sessionId,
      project,
      category_name: s.category,
      value_name: s.name,
    });
    // Move from suggested → applied
    const typeInfo = _ENTITY_TYPES.find(t => t.id === s.category) || { color: '#9b7fcc', icon: '⬡' };
    _appliedEntities.push({
      value_id: result.value_id,
      category_name: s.category,
      name: s.name,
      color: typeInfo.color,
      icon: typeInfo.icon,
    });
    _suggestedTags = _suggestedTags.filter((_, i) => i !== idx);
    _renderEntityChips();
    toast(`Accepted tag: ${s.category}/${s.name}`, 'success');
  } catch (e) {
    toast(e.message, 'error');
  }
};

window._dismissSuggestedTag = (idx) => {
  _suggestedTags = _suggestedTags.filter((_, i) => i !== idx);
  _renderEntityChips();
};

// ── Commands autocomplete ─────────────────────────────────────────────────────

const COMMANDS = [
  { cmd: '/help',        args: '',                 desc: 'Show all available commands'                      },
  { cmd: '/memory',      args: '',                 desc: 'Refresh CLAUDE.md + CONTEXT.md → copy to code dir' },
  { cmd: '/role',        args: '[name]',           desc: 'Set system prompt role'                   },
  { cmd: '/workflow',    args: '[name]',           desc: 'List or run a workflow'                   },
  { cmd: '/switch',      args: '<provider>',       desc: 'Switch LLM (claude/openai/deepseek/gemini/grok)' },
  { cmd: '/compare',     args: '<prompt.md>',      desc: 'Run prompt on multiple LLMs side-by-side' },
  { cmd: '/project',     args: 'new|list|switch',  desc: 'Manage projects'                          },
  { cmd: '/tag',         args: '<name>',           desc: 'Tag this session'                         },
  { cmd: '/feature',     args: '<name>',           desc: 'Set feature context'                      },
  { cmd: '/search-tag',  args: '<tag>',            desc: 'Search history by tag'                    },
  { cmd: '/push',        args: '[branch]',          desc: 'Commit and push to git (optional: branch name)'  },
  { cmd: '/analytics',   args: '',                 desc: 'Show usage and cost stats'                },
  { cmd: '/history',     args: '',                 desc: 'Show last 20 commits'                     },
  { cmd: '/reload',      args: '',                 desc: 'Reload system prompt'                     },
  { cmd: '/clear',       args: '',                 desc: 'Clear conversation history'               },
];

let _cmdPopupIdx = -1;
let _cmdPopupVisible = false;

function _showCmdPopup(filter) {
  const wrap = document.getElementById('chat-cmd-popup-wrap');
  if (!wrap) return;

  // Build base commands list — annotate /role and /workflow with available names
  let allCmds = COMMANDS.map(c => {
    if (c.cmd === '/role' && _roleOptions.length)
      return { ...c, desc: `Roles: ${_roleOptions.map(r => r.name.replace('.md', '')).join(', ')}` };
    if (c.cmd === '/workflow' && _workflowOptions.length)
      return { ...c, desc: `Workflows: ${_workflowOptions.map(w => typeof w === 'string' ? w : w.name).join(', ')}` };
    return c;
  });

  // When typing /role → expand to individual role entries (concrete, no placeholder)
  if (filter.startsWith('/role') && filter !== '/role' || (filter === '/role' && _roleOptions.length)) {
    if (_roleOptions.length) {
      allCmds = allCmds.filter(c => c.cmd !== '/role');
      _roleOptions.forEach(r => {
        allCmds.push({ cmd: `/role ${r.name.replace('.md', '')}`, args: '', desc: r.path });
      });
    }
  }

  // When typing /workflow → expand to individual workflow entries
  if (filter.startsWith('/workflow') && filter !== '/workflow' || (filter === '/workflow' && _workflowOptions.length)) {
    if (_workflowOptions.length) {
      allCmds = allCmds.filter(c => c.cmd !== '/workflow');
      _workflowOptions.forEach(w => {
        const name = typeof w === 'string' ? w : w.name;
        const desc = (w.description) ? w.description : `Run workflow: ${name}`;
        allCmds.push({ cmd: `/workflow ${name}`, args: '', desc });
      });
    }
  }

  const matches = filter === '/'
    ? allCmds
    : allCmds.filter(c => c.cmd.startsWith(filter));

  if (!matches.length) { _hideCmdPopup(); return; }

  _cmdPopupVisible = true;
  _cmdPopupIdx = -1;

  wrap.innerHTML = `
    <div class="cmd-popup" id="cmd-popup">
      ${matches.map((c, i) => `
        <div class="cmd-popup-item" data-idx="${i}"
             onmousedown="window._cmdComplete('${_esc(c.cmd)}', ${!!c.args})"
             onmouseenter="window._cmdHover(${i})">
          <span class="cmd-popup-cmd">${_esc(c.cmd)}</span>
          ${c.args ? `<span class="cmd-popup-args">${_esc(c.args)}</span>` : ''}
          <span class="cmd-popup-desc">${_esc(c.desc)}</span>
        </div>
      `).join('')}
    </div>
  `;
  wrap._matches = matches;
}

function _hideCmdPopup() {
  _cmdPopupVisible = false;
  _cmdPopupIdx = -1;
  const wrap = document.getElementById('chat-cmd-popup-wrap');
  if (wrap) wrap.innerHTML = '';
}

window._cmdHover = (idx) => {
  _cmdPopupIdx = idx;
  _updateCmdSelection();
};

// isPlaceholder=true  → command has an arg to type (e.g. /switch <provider>): keep cmd + space
// isPlaceholder=false → concrete completion (e.g. /role architect, /memory): use full cmd
window._cmdComplete = (cmd, isPlaceholder = false) => {
  const input = document.getElementById('chat-input');
  if (!input) return;
  if (isPlaceholder) {
    const spaceIdx = cmd.indexOf(' ');
    input.value = (spaceIdx === -1 ? cmd : cmd.slice(0, spaceIdx)) + ' ';
  } else {
    input.value = cmd;
  }
  input.style.height = 'auto';
  _hideCmdPopup();
  input.focus();
};

function _updateCmdSelection() {
  document.querySelectorAll('#cmd-popup .cmd-popup-item').forEach((el, i) => {
    el.classList.toggle('selected', i === _cmdPopupIdx);
  });
}

// ── Input setup ───────────────────────────────────────────────────────────────

function _setupInput() {
  const input = document.getElementById('chat-input');
  const box   = document.getElementById('chat-input-box');
  if (!input) return;

  input.addEventListener('input', () => {
    input.style.height = 'auto';
    input.style.height = Math.min(input.scrollHeight, 140) + 'px';

    // Commands popup
    const val = input.value;
    if (val.startsWith('/') && !val.includes('\n') && !val.includes(' ')) {
      _showCmdPopup(val);
    } else {
      _hideCmdPopup();
    }
  });

  input.addEventListener('keydown', e => {
    if (_cmdPopupVisible) {
      const wrap = document.getElementById('chat-cmd-popup-wrap');
      const matches = wrap?._matches || [];

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        _cmdPopupIdx = Math.min(_cmdPopupIdx + 1, matches.length - 1);
        _updateCmdSelection();
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        _cmdPopupIdx = Math.max(_cmdPopupIdx - 1, 0);
        _updateCmdSelection();
        return;
      }
      if (e.key === 'Tab' || (e.key === 'Enter' && _cmdPopupIdx >= 0)) {
        e.preventDefault();
        const idx = _cmdPopupIdx >= 0 ? _cmdPopupIdx : 0;
        const c = matches[idx];
        if (c) window._cmdComplete(c.cmd, !!c.args);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        _hideCmdPopup();
        return;
      }
    }
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); window._chatSend(); }
  });

  input.addEventListener('focus', () => { if (box) box.style.borderColor = 'rgba(255,107,53,0.4)'; });
  input.addEventListener('blur',  () => {
    if (box) box.style.borderColor = 'var(--border)';
    // Delay hide so mousedown on popup item fires first
    setTimeout(_hideCmdPopup, 150);
  });
}

// ── Sessions sidebar ──────────────────────────────────────────────────────────

async function _loadSessions() {
  const container = document.getElementById('chat-sessions');
  if (!container) return;

  const projectName = state.currentProject?.name;
  const merged = [];

  // 1. UI sessions (have full message history loadable via chatSession)
  try {
    const uiData = await api.chatSessions();
    const list = Array.isArray(uiData) ? uiData : uiData.sessions || [];
    list.forEach(s => merged.push({
      id: s.id,
      title: s.title || s.id.slice(0, 14),
      source: 'ui',
      ts: s.updated_at || s.created_at || s.id,
      message_count: s.message_count || 0,
      phase: s.phase || null,
      feature: s.feature || null,
      bug_ref: s.bug_ref || null,
      tags: s.tags || {},
      entries: null,  // load on demand
    }));
  } catch { /* backend offline */ }

  // 2. Unified project history — claude_cli and workflow sources
  if (projectName) {
    try {
      const histData = await api.historyChat(projectName, 300);
      const bySession = new Map();
      for (const e of (histData.entries || [])) {
        const src = e.source || 'ui';
        if (src === 'ui') continue;  // already in UI sessions above
        const sid = e.session_id || ('hist_' + e.ts);
        if (!bySession.has(sid)) {
          bySession.set(sid, {
            id: sid,
            title: (e.user_input || '').slice(0, 60) || sid.slice(0, 14),
            source: src,
            ts: e.ts || '',
            message_count: 0,
            entries: [],
          });
        }
        const s = bySession.get(sid);
        s.message_count++;
        s.entries.push(e);
      }
      merged.push(...bySession.values());
    } catch { /* silent */ }
  }

  // Sort newest first (#1 = most recent)
  merged.sort((a, b) => (b.ts || '').localeCompare(a.ts || ''));
  _sessionCache = merged;

  if (!merged.length) {
    container.innerHTML = '<div style="font-size:0.65rem;color:var(--muted);padding:0.5rem 0.25rem">No sessions yet</div>';
    return;
  }

  container.innerHTML = merged.slice(0, 60).map((s, idx) => {
    const isActive  = s.id === _sessionId;
    const srcColor  = s.source === 'ui' ? 'var(--accent)' : s.source === 'claude_cli' ? 'var(--blue)' : 'var(--green)';
    const srcLabel  = s.source === 'ui' ? 'UI' : s.source === 'claude_cli' ? 'CLI' : 'WF';
    // Tag status — UI sessions show phase; missing phase = red
    const hasPhase  = !!(s.phase);
    const phaseTxt  = s.phase || null;
    const tagDot    = s.source === 'ui'
      ? (hasPhase
          ? `<span style="font-size:0.5rem;background:var(--accent)22;color:var(--accent);padding:0 0.22rem;border-radius:2px;flex-shrink:0">${_esc(phaseTxt)}</span>`
          : `<span style="font-size:0.5rem;color:#e74c3c;flex-shrink:0" title="Missing mandatory phase tag">⚠</span>`)
      : '';
    const featureTxt = s.feature ? `<span style="font-size:0.5rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:60px">#${_esc(s.feature)}</span>` : '';
    const borderL   = (s.source === 'ui' && !hasPhase) ? '2px solid #e74c3c' : (isActive ? '2px solid var(--accent)' : '2px solid transparent');
    return `
      <div onclick="window._chatLoadAny('${_esc(s.id)}')"
        style="padding:0.32rem 0.45rem;border-radius:var(--radius);cursor:pointer;
               border-left:${borderL};
               font-size:0.63rem;color:${isActive ? 'var(--text)' : 'var(--text2)'};
               background:${isActive ? 'var(--surface2)' : ''};
               transition:background 0.1s;margin-bottom:1px"
        title="${_esc(s.title)}"
        onmouseenter="this.style.background='var(--surface2)'"
        onmouseleave="this.style.background='${isActive ? 'var(--surface2)' : ''}'">
        <div style="display:flex;align-items:center;gap:0.3rem;margin-bottom:2px">
          <span style="font-size:0.52rem;color:var(--muted);flex-shrink:0">${idx + 1}.</span>
          <span style="font-size:0.5rem;color:${srcColor};background:${srcColor}1a;
                       padding:0 0.22rem;border-radius:2px;flex-shrink:0;letter-spacing:0.5px">${srcLabel}</span>
          ${tagDot}
          ${featureTxt}
        </div>
        <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(s.title)}</div>
      </div>`;
  }).join('');
}

// Load any session — UI sessions from store, CLI/WF sessions from history cache
window._chatLoadAny = async (id) => {
  const session = _sessionCache.find(s => s.id === id);
  if (!session) return;

  if (session.source === 'ui') {
    await window._chatLoad(id);
    return;
  }

  // History-only session (claude_cli or workflow): render entries read-only
  _sessionId = id;
  const msgs = document.getElementById('chat-messages');
  if (!msgs) return;
  msgs.innerHTML = '';
  if (!session.entries?.length) {
    _appendSystemMsg('No messages in this session.');
    return;
  }
  // Sort entries oldest-first so messages flow top→bottom chronologically
  const chronological = [...session.entries].sort((a, b) => (a.ts || '').localeCompare(b.ts || ''));
  for (const e of chronological) {
    if (e.user_input) _appendUserMsg(e.user_input);
    if (e.output) _appendAssistantMsg(e.output);
  }
  // Highlight active in sidebar
  document.querySelectorAll('#chat-sessions > div').forEach((el, i) => {
    const active = _sessionCache[i]?.id === id;
    el.style.background = active ? 'var(--surface2)' : '';
    el.style.color = active ? 'var(--text)' : 'var(--text2)';
  });
};

async function _loadRolesAndWorkflows() {
  const proj = state.currentProject?.name;
  if (!proj) return;
  try {
    const data = await api.listPrompts(proj);
    _roleOptions = (data.prompts || []).filter(p => p.path.startsWith('roles/'));
    // Populate role dropdown
    const sel = document.getElementById('chat-role');
    if (sel && _roleOptions.length) {
      _roleOptions.forEach(r => {
        const opt = document.createElement('option');
        opt.value = r.path;
        opt.textContent = r.name.replace('.md', '');
        sel.appendChild(opt);
      });
    }
  } catch { /* silent */ }

  try {
    const data = await api.listWorkflows(proj);
    // Keep full objects so popup can show descriptions
    _workflowOptions = data.workflows || [];
  } catch { /* silent */ }
}

window._chatNew = () => {
  _sessionId = null;
  _appliedEntities = [];
  _suggestedTags = [];
  _closeEntityPicker();
  const msgs = document.getElementById('chat-messages');
  if (msgs) msgs.innerHTML = '';
  _showWelcome();  // roles already loaded — show immediately
  _renderEntityChips();
  _loadSessions();
};

// ── Chat panel resize ─────────────────────────────────────────────────────────

function _initChatResize() {
  const handle = document.getElementById('chat-resize-handle');
  const panel  = document.getElementById('chat-session-panel');
  if (!handle || !panel) return;

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
    localStorage.setItem('aicli_chat_sessions_w', String(panel.offsetWidth));
  });
}

window._chatLoad = async (id) => {
  _sessionId = id;
  try {
    const session = await api.chatSession(id);
    const msgs = document.getElementById('chat-messages');
    if (!msgs) return;
    msgs.innerHTML = '';
    // Restore tags from session metadata so tag bar reflects this session
    const storedTags = session.metadata?.tags || {};
    _restoreTagBar(storedTags);
    for (const m of session.messages || []) {
      if (m.role === 'user')      _appendUserMsg(m.content);
      if (m.role === 'assistant') _appendAssistantMsg(m.content);
    }
    // Highlight active session in sidebar
    document.querySelectorAll('#chat-sessions > div').forEach((el, i) => {
      const active = _sessionCache[i]?.id === id;
      el.style.background = active ? 'var(--surface2)' : '';
    });
  } catch (e) {
    toast('Could not load session', 'error');
  }
};

// ── Send + SSE streaming ──────────────────────────────────────────────────────

window._chatSend = async () => {
  if (_streaming) return;
  const input = document.getElementById('chat-input');
  const message = input?.value?.trim();
  if (!message) return;

  // Handle /help — show all commands as a formatted message
  if (message === '/help') {
    input.value = '';
    input.style.height = 'auto';
    const roleNames = _roleOptions.map(r => r.name.replace('.md', '')).join(', ') || '(none loaded)';
    const wfNames   = _workflowOptions.map(w => typeof w === 'string' ? w : w.name).join(', ') || '(none loaded)';
    _appendSystemMsg(
      `## Available Commands\n\n` +
      `| Command | Description |\n` +
      `|---|---|\n` +
      `| \`/help\` | Show this help |\n` +
      `| \`/memory\` | Refresh CLAUDE.md + CONTEXT.md → copy to code dir |\n` +
      `| \`/role <name>\` | Set system prompt role · available: ${roleNames} |\n` +
      `| \`/workflow <name>\` | Run a workflow · available: ${wfNames} |\n` +
      `| \`/switch <provider>\` | Switch LLM: claude, openai, deepseek, gemini, grok |\n` +
      `| \`/compare <prompt.md>\` | Run prompt on multiple LLMs side-by-side |\n` +
      `| \`/project new\\|list\\|switch\` | Manage projects |\n` +
      `| \`/tag <name>\` | Tag this session |\n` +
      `| \`/feature <name>\` | Set feature context |\n` +
      `| \`/search-tag <tag>\` | Search history by tag |\n` +
      `| \`/push [branch]\` | Commit and push to git · e.g. \`/push master\` |\n` +
      `| \`/analytics\` | Show usage and cost stats |\n` +
      `| \`/history\` | Show last 20 commits |\n` +
      `| \`/reload\` | Reload system prompt |\n` +
      `| \`/clear\` | Clear conversation history |`
    );
    return;
  }

  // Handle /role command locally
  if (message.startsWith('/role ')) {
    const roleName = message.slice(6).trim();
    input.value = '';
    input.style.height = 'auto';
    const proj = state.currentProject?.name;
    if (!proj) { toast('No project open', 'error'); return; }
    const match = _roleOptions.find(r => r.name.replace('.md','') === roleName || r.path === roleName);
    if (match) {
      try {
        const data = await api.readPrompt(match.path, proj);
        setState({ currentProject: { ...state.currentProject, system_prompt: data.content || '' } });
        const sel = document.getElementById('chat-role');
        if (sel) sel.value = match.path;
        _appendSystemMsg(`Role set: **${match.name.replace('.md','')}**`);
      } catch (e) { toast(`Could not load role: ${e.message}`, 'error'); }
    } else {
      _appendSystemMsg(`Role not found: ${roleName}. Available: ${_roleOptions.map(r=>r.name.replace('.md','')).join(', ')}`);
    }
    return;
  }

  // Handle /memory — generate all memory files + get LLM tag suggestions
  if (message === '/memory') {
    input.value = '';
    input.style.height = 'auto';
    const proj = state.currentProject?.name;
    if (!proj) { toast('No project open', 'error'); return; }
    _appendSystemMsg('Generating memory files…');
    try {
      const result = await api.generateMemory(proj);
      // Load LLM-suggested tags into the tag bar
      if (result.suggested_tags?.length) {
        _suggestedTags = result.suggested_tags;
        _renderEntityChips();
      }
      // Refresh system prompt from freshly-written CONTEXT.md
      try {
        const ctxData = await api.getProjectContext(proj, false);
        const freshPrompt = ctxData.context || ctxData.claude_md || '';
        if (freshPrompt) setState({ currentProject: { ...state.currentProject, system_prompt: freshPrompt } });
      } catch { /* silent — don't fail if context fetch fails */ }

      const fileList = (result.generated || []).slice(0, 4).join(', ');
      const synthNote = result.synthesized ? ' *(LLM-synthesized)*' : '';
      _appendSystemMsg(`✓ **Memory files refreshed**${synthNote} → \`${fileList}\``);
      if (result.suggested_tags?.length) {
        _appendSystemMsg(`📎 **${result.suggested_tags.length}** tag suggestion${result.suggested_tags.length > 1 ? 's' : ''} shown in the tag bar above — accept or dismiss.`);
      }
    } catch (e) {
      _appendSystemMsg(`Error: ${e.message}`);
    }
    return;
  }

  // Handle /push [branch] — commit and push to git
  if (message === '/push' || message.startsWith('/push ')) {
    const branchArg = message.slice(5).trim();  // empty string if no branch given
    input.value = '';
    input.style.height = 'auto';
    const proj = state.currentProject?.name;
    if (!proj) { toast('No project open', 'error'); return; }
    _appendSystemMsg(`Committing and pushing${branchArg ? ` to **${branchArg}**` : ''}…`);
    try {
      const result = await api.gitCommitPush(proj, {
        message_hint: 'manual /push from chat',
        provider: _provider,
        branch: branchArg,
      });
      if (result.committed === false) {
        _appendSystemMsg('✓ **No changes** to commit — working tree is clean.');
      } else if (result.pushed) {
        const pullLine = result.pull_message ? `\n\n**Sync:** ${result.pull_message}` : '';
        _appendSystemMsg(
          `✓ **Pushed** \`${result.commit_hash}\` → \`${branchArg || 'default branch'}\`\n\n` +
          `**Message:** ${result.commit_message}\n\n` +
          `**Files:** ${(result.files || []).join(', ')}` + pullLine
        );
      } else {
        _appendSystemMsg(
          `✓ Committed \`${result.commit_hash}\` but **push failed:**\n\n` +
          `\`${result.push_error || 'Check credentials in Settings → Project → Git'}\``
        );
      }
    } catch (e) {
      _appendSystemMsg(`**Push failed:** ${e.message}`);
    }
    return;
  }

  // Handle /clear command locally
  if (message === '/clear') {
    input.value = '';
    input.style.height = 'auto';
    _sessionId = null;
    const msgs = document.getElementById('chat-messages');
    if (msgs) msgs.innerHTML = '';
    _showWelcome();
    return;
  }

  // Handle /switch command locally
  if (message.startsWith('/switch ') || message === '/switch') {
    const prov = message.slice(8).trim();
    input.value = '';
    input.style.height = 'auto';
    const sel = document.getElementById('chat-provider');
    if (PROVIDERS.find(p => p.id === prov)) {
      _provider = prov;
      if (sel) sel.value = prov;
      _appendSystemMsg(`Switched to **${prov}**`);
    } else {
      _appendSystemMsg(`Unknown provider: ${prov}. Options: ${PROVIDERS.map(p=>p.id).join(', ')}`);
    }
    return;
  }

  input.value = '';
  input.style.height = 'auto';
  document.querySelector('.chat-welcome')?.remove();

  _appendUserMsg(message);
  const { bubble, scrollInto } = _appendStreamBubble(_provider);
  _setStreaming(true);

  const system = state.currentProject?.system_prompt || '';
  // Warn if mandatory phase tag is not set
  if (!_sessionTags.phase) {
    _appendSystemMsg('⚠ **No phase tag set.** Select a phase above to categorize this session.');
  }

  try {
    const response = await api.chatStream(message, _provider, _sessionId, system, _sessionTags);

    // Session ID is in response header
    const sid = response.headers.get('X-Session-Id');
    if (sid) _sessionId = sid;

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer    = '';
    let fullText  = '';
    let eventTs   = null;   // captured from [EVENT:ts] SSE event

    outer: while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE messages are separated by \n\n
      const parts = buffer.split('\n\n');
      buffer = parts.pop(); // keep partial last chunk

      for (const part of parts) {
        // Each SSE event starts with "data: "; everything after it (including
        // embedded newlines from the content) belongs to that event.
        if (!part.startsWith('data: ')) continue;
        const data = part.slice(6);
        if (data === '[DONE]') break outer;
        if (data.startsWith('[ERROR]')) throw new Error(data.slice(8).trim() || 'Stream error');
        // Capture event timestamp for tag suggestion polling
        if (data.startsWith('[EVENT:')) { eventTs = data.slice(7); continue; }
        fullText += data;
        // Render markdown incrementally while streaming
        bubble.innerHTML = _renderMarkdown(fullText) + '<span style="opacity:0.3;animation:cursorBlink 1s infinite">▌</span>';
        scrollInto();
      }
    }

    // Remove streaming cursor, finalize
    bubble.innerHTML = _renderMarkdown(fullText);
    scrollInto();
    _loadSessions();

    // Poll for tag suggestions (backend needs ~2s to run Haiku)
    if (eventTs) {
      const capturedTs = eventTs;
      setTimeout(() => _pollTagSuggestions(capturedTs), 2500);
    }

    // Auto commit & push if enabled for this project
    const proj = state.currentProject;
    if (proj?.auto_commit_push && proj?.name) {
      _autoCommitPush(proj.name, message, fullText);
    }

  } catch (e) {
    bubble.innerHTML = `<span style="color:var(--red)">Error: ${_esc(e.message)}</span>`;
    toast(e.message, 'error');
  } finally {
    _setStreaming(false);
    input?.focus();
  }
};

async function _autoCommitPush(projectName, userMsg) {
  try {
    const result = await api.gitCommitPush(projectName, {
      message_hint: userMsg.slice(0, 200),
      provider:     _provider,
    });
    if (result.committed === false) return; // no changes — silent
    if (result.pushed) {
      _appendSystemMsg(`↑ **Auto-pushed** \`${result.commit_hash}\` — ${result.commit_message}`);
    } else {
      // Push failed — show in chat so user can see the error
      const err = result.push_error || 'Check Git credentials in Settings → Project → Git';
      _appendSystemMsg(`↑ Committed \`${result.commit_hash}\` but **push failed:** ${err}`);
    }
  } catch (e) {
    // Show error in chat (not just a toast) — common causes: code_dir not set, not a git repo
    _appendSystemMsg(`⚠ Auto-commit failed: ${e.message}\n\nCheck **Settings → Project** — make sure *Code directory* and *Git credentials* are configured.`);
  }
}

// ── Tag suggestion chips ──────────────────────────────────────────────────────

async function _pollTagSuggestions(sourceId) {
  try {
    const project = state.currentProject?.name || '';
    const d = await api.entities.getSuggestions(project, sourceId);
    const evt = d?.events?.[0];
    if (evt?.metadata?.tag_suggestions?.length) {
      _showTagSuggestions(evt);
    }
  } catch (_) {}
}

function _showTagSuggestions(evt) {
  const container = document.getElementById('chat-messages');
  if (!container) return;

  const suggs = (evt.metadata?.tag_suggestions || []);
  if (!suggs.length) return;

  const row = document.createElement('div');
  row.dataset.suggestionEventId = evt.id;
  row.style.cssText = [
    'display:flex;align-items:center;gap:0.4rem;flex-wrap:wrap',
    'padding:0.35rem 0.75rem;margin:0.15rem 0',
    'animation:msgIn 0.2s ease-out',
  ].join(';');

  // Label
  const label = document.createElement('span');
  label.style.cssText = 'font-size:0.6rem;color:var(--muted);white-space:nowrap';
  label.textContent = '📎 Tag:';
  row.appendChild(label);

  // One chip per suggestion
  suggs.forEach(s => {
    const chip = document.createElement('span');
    const isApplied = s.from_session === true;
    chip.style.cssText = [
      `background:${isApplied ? 'var(--accent)' : 'var(--surface2)'}`,
      `color:${isApplied ? '#fff' : 'var(--text)'}`,
      'border:1px solid var(--border)',
      'border-radius:12px',
      'padding:0.15rem 0.55rem',
      'font-size:0.62rem',
      'cursor:pointer',
      'transition:background 0.15s,opacity 0.15s',
      'user-select:none',
    ].join(';');
    chip.title = isApplied ? 'Applied from session tags' : 'Click to apply tag';
    chip.dataset.valueId = s.value_id;
    chip.dataset.applied = isApplied ? 'true' : 'false';
    chip.innerHTML = `${_esc(s.category)}/<strong>${_esc(s.name)}</strong>${isApplied ? ' ✓' : ' +'}`;

    if (!isApplied) {
      chip.addEventListener('click', async () => {
        if (chip.dataset.applied === 'true') return;
        try {
          await api.entities.addTag(evt.id, { entity_value_id: s.value_id, auto_tagged: false });
          chip.dataset.applied = 'true';
          chip.style.background = 'var(--accent)';
          chip.style.color = '#fff';
          chip.innerHTML = `${_esc(s.category)}/<strong>${_esc(s.name)}</strong> ✓`;
        } catch (e) {
          toast(e.message, 'error');
        }
      });
    }
    row.appendChild(chip);
  });

  // Apply-all button (only if there are non-session suggestions)
  const nonSession = suggs.filter(s => !s.from_session);
  if (nonSession.length > 1) {
    const applyAll = document.createElement('span');
    applyAll.style.cssText = 'font-size:0.6rem;color:var(--accent);cursor:pointer;white-space:nowrap;text-decoration:underline';
    applyAll.textContent = 'apply all';
    applyAll.addEventListener('click', async () => {
      for (const s of nonSession) {
        try {
          await api.entities.addTag(evt.id, { entity_value_id: s.value_id, auto_tagged: false });
        } catch (_) {}
      }
      // Refresh chips state
      row.querySelectorAll('span[data-value-id]').forEach(c => {
        c.dataset.applied = 'true';
        c.style.background = 'var(--accent)';
        c.style.color = '#fff';
      });
      applyAll.remove();
    });
    row.appendChild(applyAll);
  }

  // Dismiss button
  const dismiss = document.createElement('span');
  dismiss.style.cssText = 'font-size:0.7rem;color:var(--muted);cursor:pointer;margin-left:auto;padding:0 0.25rem';
  dismiss.title = 'Dismiss suggestions';
  dismiss.textContent = '✕';
  dismiss.addEventListener('click', async () => {
    row.remove();
    try { await api.entities.dismissSuggestions(evt.id); } catch (_) {}
  });
  row.appendChild(dismiss);

  container.appendChild(row);
  container.scrollTop = container.scrollHeight;
}

function _setStreaming(active) {
  _streaming = active;
  const btn = document.getElementById('chat-send-btn');
  if (!btn) return;
  btn.disabled      = active;
  btn.style.opacity = active ? '0.35' : '1';
  btn.textContent   = active ? '■' : '↑';
}

// ── Message rendering helpers ─────────────────────────────────────────────────

function _appendSystemMsg(md) {
  const container = document.getElementById('chat-messages');
  if (!container) return;
  const el = document.createElement('div');
  el.style.cssText = 'display:flex;justify-content:center;animation:msgIn 0.2s ease-out';
  el.innerHTML = `<div style="font-size:0.68rem;color:var(--muted);background:var(--surface2);
    border:1px solid var(--border);border-radius:20px;padding:0.25rem 0.85rem">
    ${_renderMarkdown(md)}</div>`;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
}

function _appendUserMsg(text) {
  const container = document.getElementById('chat-messages');
  if (!container) return;
  const el = document.createElement('div');
  el.style.cssText = 'display:flex;flex-direction:column;gap:0.3rem;align-items:flex-end;animation:msgIn 0.2s ease-out';
  el.innerHTML = `
    <div style="font-size:0.55rem;color:var(--muted);letter-spacing:1px;text-transform:uppercase">you</div>
    <div style="max-width:78%;background:var(--surface2);border:1px solid var(--border);
                border-radius:10px;padding:0.8rem 1rem;font-size:0.78rem;line-height:1.7;
                word-break:break-word;user-select:text;-webkit-user-select:text;
                white-space:pre-wrap">${_esc(text)}</div>`;
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
}

function _appendAssistantMsg(text) {
  const container = document.getElementById('chat-messages');
  if (!container) return;
  const el = document.createElement('div');
  el.style.cssText = 'display:flex;flex-direction:column;gap:0.3rem;align-items:flex-start;animation:msgIn 0.2s ease-out';
  const bubble = document.createElement('div');
  bubble.style.cssText = 'max-width:78%;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:0.8rem 1rem;font-size:0.78rem;line-height:1.7;word-break:break-word;user-select:text;-webkit-user-select:text';
  bubble.innerHTML = _renderMarkdown(text);
  el.innerHTML = '<div style="font-size:0.55rem;color:var(--muted);letter-spacing:1px;text-transform:uppercase">assistant</div>';
  el.appendChild(bubble);
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;
}

function _appendStreamBubble(provider) {
  const container = document.getElementById('chat-messages');
  const el = document.createElement('div');
  el.style.cssText = 'display:flex;flex-direction:column;gap:0.3rem;align-items:flex-start;animation:msgIn 0.2s ease-out';
  el.innerHTML = `<div style="font-size:0.55rem;color:var(--muted);letter-spacing:1px;text-transform:uppercase">${_esc(provider)}</div>`;

  const bubble = document.createElement('div');
  bubble.style.cssText = 'max-width:78%;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:0.8rem 1rem;font-size:0.78rem;line-height:1.7;word-break:break-word;user-select:text;-webkit-user-select:text';
  bubble.innerHTML = '<span style="opacity:0.3;animation:cursorBlink 1s infinite">▌</span>';

  el.appendChild(bubble);
  container.appendChild(el);
  container.scrollTop = container.scrollHeight;

  return {
    bubble,
    scrollInto: () => { container.scrollTop = container.scrollHeight; },
  };
}

// ── Welcome screen ────────────────────────────────────────────────────────────

function _showWelcome() {
  const container = document.getElementById('chat-messages');
  if (!container) return;
  const el = document.createElement('div');
  el.className  = 'chat-welcome';
  el.style.cssText = 'padding:1.5rem 2rem;max-width:720px;width:100%';
  const proj = state.currentProject;

  if (!proj) {
    el.innerHTML = `
      <div style="font-size:1.4rem;font-weight:800;color:var(--accent);margin-bottom:0.35rem">aicli Chat</div>
      <div style="font-size:0.68rem;color:var(--muted)">Open a project from the sidebar to start chatting with context.</div>`;
    container.appendChild(el);
    return;
  }

  const roleButtons = _roleOptions.length ? `
    <div style="margin-bottom:1.2rem">
      <div style="font-size:0.52rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:0.4rem">Roles</div>
      <div style="display:flex;flex-wrap:wrap;gap:0.3rem">
        <button onclick="window._quickRole('')"
          style="padding:0.22rem 0.55rem;font-size:0.63rem;background:var(--surface);border:1px solid var(--border);
                 border-radius:20px;cursor:pointer;color:var(--text2);transition:border-color 0.1s"
          onmouseenter="this.style.borderColor='var(--accent)'"
          onmouseleave="this.style.borderColor='var(--border)'">Default</button>
        ${_roleOptions.map(r => `
          <button onclick="window._quickRole('${_esc(r.path)}')"
            style="padding:0.22rem 0.55rem;font-size:0.63rem;background:var(--surface);border:1px solid var(--border);
                   border-radius:20px;cursor:pointer;color:var(--text2);transition:border-color 0.1s"
            onmouseenter="this.style.borderColor='var(--accent)'"
            onmouseleave="this.style.borderColor='var(--border)'">${_esc(r.name.replace('.md', ''))}</button>`).join('')}
      </div>
    </div>` : '';

  const wfButtons = _workflowOptions.length ? `
    <div style="margin-bottom:1.2rem">
      <div style="font-size:0.52rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:0.4rem">Workflows</div>
      <div style="display:flex;flex-wrap:wrap;gap:0.3rem">
        ${_workflowOptions.slice(0, 8).map(w => {
          const name = typeof w === 'string' ? w : w.name;
          return `<button onclick="document.getElementById('chat-input').value='/workflow ${_esc(name)}';document.getElementById('chat-input').focus()"
            style="padding:0.22rem 0.55rem;font-size:0.63rem;background:var(--surface);border:1px solid var(--border);
                   border-radius:20px;cursor:pointer;color:var(--text2);transition:border-color 0.1s"
            onmouseenter="this.style.borderColor='var(--accent)'"
            onmouseleave="this.style.borderColor='var(--border)'">⟳ ${_esc(name)}</button>`;
        }).join('')}
      </div>
    </div>` : '';

  // Store prompts in a global so onclick can reference by index (avoids quote escaping issues)
  window._chatWelcomePrompts = [
    'Explain the purpose, architecture and current state of this project.',
    'Based on the project context and recent history, what should I focus on next?',
    'Summarize the most recent changes and commits to this project.',
  ];
  const quickLabels = ['Explain this project', 'What should I work on?', 'Summarise recent changes'];

  el.innerHTML = `
    <div style="display:flex;align-items:baseline;gap:0.6rem;margin-bottom:0.2rem">
      <div style="font-size:0.9rem;font-weight:700;color:var(--text)">${_esc(proj.name)}</div>
      ${proj.system_prompt ? `<span style="font-size:0.58rem;color:var(--green)">✓ context loaded</span>` : ''}
    </div>
    <div style="font-size:0.62rem;color:var(--muted);margin-bottom:1.2rem">${_esc(proj.description || 'AI-assisted development workspace')}</div>
    ${roleButtons}
    ${wfButtons}
    <div>
      <div style="font-size:0.52rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-bottom:0.4rem">Quick start</div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:0.4rem">
        ${quickLabels.map((label, i) => `
          <div onclick="window._chatQuickPrompt(${i})"
            style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
                   padding:0.5rem 0.7rem;cursor:pointer;font-size:0.68rem;line-height:1.4;transition:border-color 0.1s"
            onmouseenter="this.style.borderColor='var(--accent)'"
            onmouseleave="this.style.borderColor='var(--border)'">${_esc(label)}</div>`).join('')}
      </div>
    </div>
  `;
  container.appendChild(el);
}

// Quick-fill chat input from welcome prompt index
window._chatQuickPrompt = (i) => {
  const prompt = (window._chatWelcomePrompts || [])[i];
  if (!prompt) return;
  const input = document.getElementById('chat-input');
  if (input) { input.value = prompt; input.focus(); }
};

// Quick-set role from welcome screen
window._quickRole = async (path) => {
  const proj = state.currentProject;
  if (!proj) return;
  const sel = document.getElementById('chat-role');
  if (!path) {
    // Reset to project default
    const p = await api.getProject(proj.name).catch(() => proj);
    setState({ currentProject: { ...state.currentProject, system_prompt: p.claude_md || p.project_md || '' } });
    if (sel) sel.value = '';
    toast('Role reset to default', 'info');
  } else {
    try {
      const data = await api.readPrompt(path, proj.name);
      setState({ currentProject: { ...state.currentProject, system_prompt: data.content || '' } });
      if (sel) sel.value = path;
      toast(`Role: ${path.split('/').pop().replace('.md', '')}`, 'info');
    } catch (e) { toast(`Could not load role: ${e.message}`, 'error'); }
  }
};

// ── Markdown renderer ─────────────────────────────────────────────────────────

function _renderMarkdown(text) {
  if (!text) return '';
  return text
    // Code blocks
    .replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) =>
      `<pre style="background:var(--bg);border:1px solid var(--border);border-radius:6px;padding:0.75rem;overflow-x:auto;margin:0.5rem 0"><code style="color:var(--green);font-size:0.72rem;white-space:pre">${_esc(code.trim())}</code></pre>`)
    // Inline code
    .replace(/`([^`\n]+)`/g, `<code style="background:var(--bg);border:1px solid var(--border);padding:0.1rem 0.3rem;border-radius:3px;font-size:0.75rem;color:var(--blue)">$1</code>`)
    // Headings
    .replace(/^### (.+)$/gm, '<h3 style="font-size:0.82rem;color:var(--accent);margin:0.6rem 0 0.2rem;font-family:var(--font-ui)">$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2 style="font-size:0.9rem;margin:0.75rem 0 0.3rem;font-family:var(--font-ui)">$1</h2>')
    .replace(/^# (.+)$/gm,   '<h1 style="font-size:1rem;margin:0.75rem 0 0.3rem;font-family:var(--font-ui)">$1</h1>')
    // Bold / italic
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,     '<em>$1</em>')
    // List items
    .replace(/^[-*] (.+)$/gm, '<li style="margin-left:1.2rem;margin-bottom:0.15rem">$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li style="margin-left:1.2rem;margin-bottom:0.15rem">$2</li>')
    // Paragraphs
    .replace(/\n\n+/g, '</p><p style="margin:0.5rem 0">')
    .replace(/\n/g, '<br>');
}

function _esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── CSS animations ────────────────────────────────────────────────────────────

const _style = document.createElement('style');
_style.textContent = `
  @keyframes msgIn        { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
  @keyframes cursorBlink  { 0%,49%{opacity:0.3} 50%,100%{opacity:0} }
`;
document.head.appendChild(_style);
