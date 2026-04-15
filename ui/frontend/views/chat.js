/**
 * chat.js — Multi-provider AI chat view.
 *
 * Renders the main chat interface with session management, provider/model selection,
 * phase tagging, entity tag picker, streaming message display, and slash-command support
 * (including /memory, /run, and /help). Entry point is renderChat().
 * Rendered via: renderChat() called from main.js navigateTo().
 */

import { state, setState } from '../stores/state.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { getCacheCategories, getCacheValues, addCachedValue } from '../utils/tagCache.js';

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
let _appliedEntities  = []; // [{value_id, category_name, name, color, icon}] — confirmed (saved to session)
let _pendingEntities  = []; // same shape — selected but not yet saved
let _suggestedTags    = []; // [{name, category, is_new}] — LLM suggestions from /memory
let _pickerOpen        = false;

// Fallback color/icon for known category names (used in _acceptSuggestedTag)
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
  // Reset per-navigation state so stale session from a previous visit doesn't persist
  _sessionId      = null;
  _appliedEntities = [];
  _pendingEntities = [];

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
                 flex-wrap:wrap;min-height:2rem">
          <span style="font-size:0.55rem;color:var(--muted);letter-spacing:1px;text-transform:uppercase;white-space:nowrap;flex-shrink:0">Phase:</span>

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

          <!-- Session ID badge (last 5 chars; click = copy full ID) -->
          <span id="chat-session-id-badge" style="display:none;font-family:monospace;font-size:0.52rem;
               color:var(--accent);background:var(--surface);border:1px solid var(--border);
               padding:1px 6px;border-radius:3px;cursor:pointer;white-space:nowrap;flex-shrink:0;
               user-select:none" title="Click to copy full session ID"></span>

          <!-- Add tag button -->
          <button id="chat-add-tag-btn"
            onclick="window._toggleEntityPicker()"
            style="background:var(--surface);border:1px solid var(--border);color:var(--text2);
                   font-family:var(--font);font-size:0.58rem;padding:0.12rem 0.4rem;
                   border-radius:var(--radius);cursor:pointer;white-space:nowrap;flex-shrink:0;outline:none"
            title="Tag this session with a feature, bug, or task">+ Tag</button>

          <!-- Save tags button — always visible, disabled when nothing pending -->
          <button id="chat-save-tags-btn"
            onclick="window._saveEntitiesToSession()"
            disabled
            style="font-family:var(--font);font-size:0.58rem;padding:0.12rem 0.5rem;
                   border-radius:var(--radius);cursor:not-allowed;white-space:nowrap;flex-shrink:0;
                   outline:none;background:var(--surface);border:1px solid var(--border);
                   color:var(--muted);transition:all 0.15s"
            title="Save selected tags to this session">💾 Save</button>

          <span id="chat-tag-status"
                style="font-size:0.58rem;color:var(--red,#e74c3c);white-space:nowrap;flex-shrink:0">⚠ phase</span>
          <span style="font-size:0.58rem;color:var(--muted);cursor:pointer;white-space:nowrap;flex-shrink:0"
            onclick="window._chatNew()" title="Start new session">+ new</span>
        </div>

        <!-- AI Suggestions banner — only shown after /memory returns suggestions -->
        <div id="chat-ai-suggestions" style="display:none"></div>

        <!-- Entity picker panel (shown when + Tag is clicked) — grouped listbox -->
        <div id="chat-entity-picker"
          style="display:none;flex-direction:column;max-height:280px;
                 border-bottom:1px solid var(--border);background:var(--surface);flex-shrink:0">
          <!-- Filter row -->
          <div style="display:flex;align-items:center;gap:0.4rem;padding:0.35rem 0.75rem;
                      border-bottom:1px solid var(--border);flex-shrink:0">
            <input id="picker-filter-inp" type="text" placeholder="🔍 Filter tags…"
              autocomplete="off"
              oninput="window._pickerFilter(this.value)"
              style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
                     font-family:var(--font);font-size:0.68rem;padding:0.2rem 0.4rem;
                     border-radius:var(--radius);outline:none" />
            <button onclick="window._closeEntityPicker()"
              style="background:none;border:none;color:var(--muted);cursor:pointer;
                     font-size:0.8rem;padding:0 0.25rem;flex-shrink:0;line-height:1">✕</button>
          </div>
          <!-- Grouped tag list -->
          <div id="picker-groups-list"
               style="flex:1;overflow-y:auto;padding:0.2rem 0;min-height:60px"></div>
          <!-- Add new section -->
          <div style="border-top:1px solid var(--border);padding:0.3rem 0.75rem;flex-shrink:0;
                      display:flex;align-items:center;gap:0.4rem">
            <span style="font-size:0.6rem;color:var(--muted);white-space:nowrap;flex-shrink:0">+ Add:</span>
            <select id="picker-add-cat"
              style="background:var(--bg);border:1px solid var(--border);color:var(--text);
                     font-family:var(--font);font-size:0.62rem;padding:0.15rem 0.3rem;
                     border-radius:var(--radius);outline:none;max-width:115px;flex-shrink:0">
              <option value="">Category…</option>
            </select>
            <input id="picker-add-name" type="text" placeholder="Tag name"
              onkeydown="if(event.key==='Enter')window._pickerSaveNew()"
              style="flex:1;background:var(--bg);border:1px solid var(--border);color:var(--text);
                     font-family:var(--font);font-size:0.62rem;padding:0.15rem 0.3rem;
                     border-radius:var(--radius);outline:none;min-width:0" />
            <button onclick="window._pickerSaveNew()"
              style="background:var(--accent);border:none;color:#fff;font-size:0.6rem;
                     padding:0.2rem 0.5rem;border-radius:var(--radius);cursor:pointer;
                     font-family:var(--font);outline:none;white-space:nowrap;flex-shrink:0">Save</button>
          </div>
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

  // Restore last persisted phase for this project from DB
  (async () => {
    const project = state.currentProject?.name;
    if (!project) return;
    try {
      const tags = await api.getSessionTags(project);
      if (tags?.phase && !_sessionTags.phase) {
        _sessionTags = { phase: tags.phase };
        const phaseSel = document.getElementById('chat-phase-sel');
        if (phaseSel) phaseSel.value = tags.phase;
        window.__currentPhase = tags.phase;
        _updateTagBarStatus();
      }
    } catch { /* DB unavailable — silent */ }
  })();

  _setupInput();
  _initChatResize();
  _loadSessions();
  // Auto-refresh session list every 30s (picks up new CLI prompts without full page reload)
  if (_sessRefreshTimer) clearInterval(_sessRefreshTimer);
  _sessRefreshTimer = setInterval(() => {
    if (!document.getElementById('chat-sessions')) { clearInterval(_sessRefreshTimer); _sessRefreshTimer = null; return; }
    _loadSessions({ force: true });
  }, 30000);
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
    _sessionTags = { ..._sessionTags, phase: newPhase };
    window.__currentPhase = newPhase;
    _updateTagBarStatus();
    _updateSaveButton();

    // Persist phase globally (restored on next app load)
    const project = state.currentProject?.name;
    if (project) api.putSessionTags(project, { phase: newPhase || null }).catch(() => {});

    // If a session is already loaded, update its metadata in-place
    // patchSessionTags works for both UI sessions (session file) and CLI sessions (session_phases.json)
    if (_sessionId) {
      api.patchSessionTags(_sessionId, { phase: newPhase || null }, project)
        .then(() => _loadSessions())
        .catch(() => _loadSessions());
    } else {
      _loadSessions();
    }
  });

  // Expose picker functions globally
  window._toggleEntityPicker    = _toggleEntityPicker;
  window._closeEntityPicker     = _closeEntityPicker;
  window._pickerFilter          = _pickerFilter;
  window._pickerSaveNew         = _pickerSaveNew;
  window._applyTagDirect        = _applyTagDirect;
  window._saveEntitiesToSession = _saveEntitiesToSession;
  window._removePendingTag      = _removePendingTag;
  window._removeAppliedTag      = _removeAppliedTag;
}

function _updateSaveButton() {
  const btn = document.getElementById('chat-save-tags-btn');
  if (!btn) return;
  const hasPending = _pendingEntities.length > 0;
  btn.disabled = !hasPending;
  if (hasPending) {
    btn.style.cursor  = 'pointer';
    btn.style.background = 'var(--accent)';
    btn.style.color   = '#fff';
    btn.style.border  = '1px solid var(--accent)';
    btn.title = `Save ${_pendingEntities.length} pending tag(s) to session`;
    btn.textContent = `💾 Save (${_pendingEntities.length})`;
  } else {
    btn.style.cursor  = 'not-allowed';
    btn.style.background = 'var(--surface)';
    btn.style.color   = 'var(--muted)';
    btn.style.border  = '1px solid var(--border)';
    btn.title = 'No pending tags';
    btn.textContent = '💾 Save';
  }
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
  _pendingEntities = [];
  _suggestedTags = [];    // suggestions are per-session — clear when switching
  const phaseSel = document.getElementById('chat-phase-sel');
  if (phaseSel) phaseSel.value = _sessionTags.phase;
  _updateTagBarStatus();
  _updateSaveButton();
  _renderEntityChips();
  _renderSuggestionsBar();
}

// ── Entity picker ─────────────────────────────────────────────────────────────

function _toggleEntityPicker() {
  if (_pickerOpen) { _closeEntityPicker(); return; }
  const panel = document.getElementById('chat-entity-picker');
  if (!panel) return;
  _pickerOpen = true;
  panel.style.display = 'flex';
  _loadPickerGroups();
}

function _closeEntityPicker() {
  const panel = document.getElementById('chat-entity-picker');
  if (panel) panel.style.display = 'none';
  _pickerOpen = false;
}

/** Open the grouped listbox picker — uses tag cache (zero DB calls). */
function _loadPickerGroups() {
  const cats   = getCacheCategories();
  // Populate "+ Add" category select
  const addSel = document.getElementById('picker-add-cat');
  if (addSel) {
    addSel.innerHTML = '<option value="">Category…</option>' +
      cats.map(c => `<option value="${c.id}">${_esc(c.icon)} ${_esc(c.name)}</option>`).join('');
  }
  // Reset filter + name inputs
  const filterInp = document.getElementById('picker-filter-inp');
  if (filterInp) { filterInp.value = ''; setTimeout(() => filterInp.focus(), 0); }
  const nameInp = document.getElementById('picker-add-name');
  if (nameInp) nameInp.value = '';
  _renderPickerGroups('');
}

/** Render all categories + their active tags into the grouped list. */
function _renderPickerGroups(q) {
  const list = document.getElementById('picker-groups-list');
  if (!list) return;
  const cats  = getCacheCategories();
  const query = (q || '').toLowerCase().trim();
  let html = '';
  for (const cat of cats) {
    const vals    = getCacheValues(cat.id).filter(v => !v.status || v.status === 'active');
    const matched = query ? vals.filter(v => v.name.toLowerCase().includes(query)) : vals;
    if (!matched.length) continue;
    html += `
      <div class="picker-group">
        <div style="padding:0.18rem 0.75rem;font-size:0.57rem;font-weight:600;
                    color:${cat.color};text-transform:uppercase;letter-spacing:0.04em">
          ${_esc(cat.icon)} ${_esc(cat.name)}
        </div>
        ${matched.map(v => `
          <div onmousedown="event.preventDefault();window._applyTagDirect(${v.id},'${_esc(v.name)}',${cat.id},'${_esc(cat.name)}','${_esc(cat.icon)}','${_esc(cat.color)}')"
               style="padding:0.22rem 0.75rem 0.22rem 1.6rem;cursor:pointer;font-size:0.68rem;
                      display:flex;align-items:center;justify-content:space-between;gap:6px"
               onmouseenter="this.style.background='var(--surface2)'"
               onmouseleave="this.style.background='transparent'">
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(v.name)}</span>
            ${v.event_count ? `<span style="font-size:0.55rem;color:var(--muted);flex-shrink:0">${v.event_count}</span>` : ''}
          </div>`).join('')}
      </div>`;
  }
  list.innerHTML = html || `
    <div style="padding:1rem;text-align:center;font-size:0.65rem;color:var(--muted)">
      ${query ? 'No matching tags' : 'No tags yet — add one below'}
    </div>`;
}

function _pickerFilter(q) {
  _renderPickerGroups(q);
}

/** Save a brand-new tag from the "+ Add" section in the picker. */
function _pickerSaveNew() {
  const catSel  = document.getElementById('picker-add-cat');
  const nameInp = document.getElementById('picker-add-name');
  const catId   = catSel?.value;
  const name    = (nameInp?.value || '').trim();
  if (!catId) { toast('Select a category', 'error'); return; }
  if (!name)  { toast('Enter a tag name', 'error'); return; }
  const cat = getCacheCategories().find(c => String(c.id) === String(catId)) || {};
  const catName = cat.name  || '';
  const icon    = cat.icon  || '⬡';
  const color   = cat.color || '#4a90e2';
  const exists = _pendingEntities.some(e => e.name === name && e.category_name === catName) ||
                 _appliedEntities.some(e => e.name === name && e.category_name === catName);
  if (!exists) {
    _pendingEntities.push({ value_id: null, category_name: catName, name, color, icon, is_new: true });
    _renderEntityChips();
    _updateSaveButton();
  }
  if (nameInp) nameInp.value = '';
  _closeEntityPicker();
}

// Legacy helper — routes through pending flow
function _applyTagDirect(valueId, valueName, catId, catName, icon, color) {
  const exists = _pendingEntities.some(e => e.value_id === valueId) ||
                 _appliedEntities.some(e => e.value_id === valueId);
  if (!exists) {
    _pendingEntities.push({ value_id: valueId, category_name: catName, name: valueName, color, icon });
    _renderEntityChips();
    _updateSaveButton();
  }
  _closeEntityPicker();
}


/** Remove a pending tag by index. */
function _removePendingTag(idx) {
  _pendingEntities.splice(idx, 1);
  _renderEntityChips();
  _updateSaveButton();
}

async function _removeAppliedTag(idx) {
  const e = _appliedEntities[idx];
  if (!e) return;

  // Optimistic: remove from UI immediately
  _appliedEntities.splice(idx, 1);
  _renderEntityChips();

  // Persist removal to backend (removes from all events in this session)
  const project = state.currentProject?.name || '';
  if (_sessionId && e.value_id) {
    try {
      await api.entities.untagSession(_sessionId, e.value_id, project);
    } catch (err) {
      console.warn('Remove applied tag failed:', err.message);
      // Restore on failure
      _appliedEntities.splice(idx, 0, e);
      _renderEntityChips();
    }
  }
}

/** Save all pending tags to the current session (or queue them for auto-apply on first send). */
async function _saveEntitiesToSession() {
  if (!_pendingEntities.length) return;
  const project = state.currentProject?.name;
  if (!project) { toast('No project open', 'error'); return; }

  if (!_sessionId) {
    // No session yet — toast to inform user, tags will auto-apply on first send
    toast(`${_pendingEntities.length} tag(s) queued — will be saved when you send your first message`, 'info');
    return;
  }

  const btn = document.getElementById('chat-save-tags-btn');
  if (btn) btn.textContent = '💾 Saving…';

  const toApply = [..._pendingEntities];
  let saved = 0;
  for (const e of toApply) {
    try {
      const body = e.value_id
        ? { session_id: _sessionId, project, value_id: e.value_id }
        : { session_id: _sessionId, project, category_name: e.category_name, value_name: e.name };
      const result = await api.entities.sessionTag(body);
      const resolvedId = result.value_id || e.value_id;
      // Add to cache if brand new
      if (e.is_new && resolvedId) {
        addCachedValue(
          getCacheCategories().find(c => c.name === e.category_name)?.id,
          { id: resolvedId, name: e.name, status: 'active', event_count: result.events_tagged || 0 },
        );
      }
      _appliedEntities.push({ ...e, value_id: resolvedId });
      saved++;
    } catch (err) {
      toast(`Tag "${e.name}" error: ${err.message}`, 'error');
    }
  }
  _pendingEntities = [];
  _renderEntityChips();
  _updateSaveButton();
  if (saved) toast(`${saved} tag(s) saved to session`, 'success');
}

function _renderEntityChips() {
  const container = document.getElementById('chat-entity-chips');
  if (!container) return;

  // Confirmed chips — solid colored style, with ✕ to remove
  const appliedHtml = _appliedEntities.map((e, idx) => `
    <span class="entity-chip user-tag"
          style="display:inline-flex;align-items:center;gap:0.18rem;
                 background:${e.color}22;border:1px solid ${e.color}55;color:${e.color};
                 border-radius:10px;padding:0.08rem 0.38rem;font-size:0.56rem;white-space:nowrap"
          title="Saved · ${_esc(e.category_name)}/${_esc(e.name)}">
      ${_esc(e.icon)} ${_esc(e.name)}
      <button onclick="window._removeAppliedTag(${idx})"
        style="border:none;background:none;cursor:pointer;color:${e.color};font-size:0.6rem;padding:0 1px;line-height:1;opacity:.7"
        title="Remove tag">✕</button>
    </span>`).join('');

  // Pending chips — lighter border, ✕ to remove
  const pendingHtml = _pendingEntities.map((e, idx) => `
    <span class="entity-chip pending-tag"
          style="display:inline-flex;align-items:center;gap:0.18rem;
                 background:${e.color}11;border:1px dashed ${e.color}88;color:${e.color};
                 border-radius:10px;padding:0.08rem 0.38rem;font-size:0.56rem;white-space:nowrap;
                 opacity:0.82"
          title="Pending · ${_esc(e.category_name)}/${_esc(e.name)} — click 💾 Save to apply">
      ${_esc(e.icon)} ${_esc(e.name)}
      <button onclick="window._removePendingTag(${idx})"
        style="border:none;background:none;cursor:pointer;color:${e.color};font-size:0.6rem;padding:0 1px;line-height:1"
        title="Remove">✕</button>
    </span>`).join('');

  container.innerHTML = appliedHtml + pendingHtml;
}

/** Renders the dedicated AI suggestions banner below the tag bar. */
function _renderSuggestionsBar() {
  const bar = document.getElementById('chat-ai-suggestions');
  if (!bar) return;
  if (!_suggestedTags.length) { bar.style.display = 'none'; return; }

  const project      = state.currentProject?.name || '';
  const sessionShort = _sessionId ? _sessionId.slice(0, 8) + '…' : 'new session';

  const chipsHtml = _suggestedTags.map((s, idx) => {
    const cat      = getCacheCategories().find(c => c.name === s.category);
    const typeInfo = cat || _ENTITY_TYPES.find(t => t.id === s.category) || { color: '#9b7fcc', icon: '⬡' };
    return `
      <span style="display:inline-flex;align-items:center;gap:0.3rem;
                   background:${typeInfo.color}18;border:1px solid ${typeInfo.color}55;
                   border-radius:6px;padding:0.2rem 0.5rem;font-size:0.62rem;white-space:nowrap">
        <span style="color:${typeInfo.color}">${_esc(typeInfo.icon)}</span>
        <span style="color:var(--muted);font-size:0.55rem">${_esc(s.category)}</span>
        <strong style="color:var(--text)">${_esc(s.name)}</strong>
        <button onclick="window._acceptSuggestedTag(${idx})"
          style="border:1px solid #27ae60;background:#27ae6018;cursor:pointer;color:#27ae60;
                 font-size:0.58rem;padding:0.06rem 0.35rem;border-radius:4px;line-height:1.2;
                 font-family:var(--font);white-space:nowrap">✓ Accept</button>
        <button onclick="window._dismissSuggestedTag(${idx})"
          style="border:none;background:none;cursor:pointer;color:var(--muted);
                 font-size:0.65rem;padding:0 2px;line-height:1"
          title="Dismiss">✕</button>
      </span>`;
  }).join('');

  bar.style.display = 'block';
  bar.innerHTML = `
    <div style="display:flex;align-items:flex-start;gap:0.5rem;flex-wrap:wrap;
                padding:0.5rem 0.75rem;border-bottom:2px solid #d4a017;
                background:linear-gradient(to right,#fffbe6,#fff9d6)">
      <div style="flex:1;min-width:0">
        <div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.3rem;flex-wrap:wrap">
          <span style="font-size:0.62rem;font-weight:700;color:#8a6500">🤖 AI Tag Suggestions</span>
          <span style="font-size:0.55rem;color:#b08000;background:#d4a01722;border:1px solid #d4a01744;
                       border-radius:4px;padding:0.05rem 0.3rem">
            session: <code style="font-size:0.55rem">${_esc(sessionShort)}</code>
            ${project ? ` · ${_esc(project)}` : ''}
          </span>
          <span style="font-size:0.55rem;color:#b08000;font-style:italic">
            Based on your recent history — click ✓ Accept to apply
          </span>
        </div>
        <div style="display:flex;gap:0.35rem;flex-wrap:wrap;align-items:center">${chipsHtml}</div>
      </div>
      <button onclick="window._dismissAllSuggestions()"
        style="border:none;background:none;cursor:pointer;color:#b08000;font-size:0.6rem;
               padding:0;line-height:1;white-space:nowrap;flex-shrink:0;align-self:flex-start"
        title="Dismiss all suggestions">Dismiss all</button>
    </div>`;
}

window._acceptSuggestedTag = async (idx) => {
  const s = _suggestedTags[idx];
  if (!s) return;
  // Resolve color/icon from cache categories or fallback
  const cat      = getCacheCategories().find(c => c.name === s.category);
  const typeInfo = cat || _ENTITY_TYPES.find(t => t.id === s.category) || { color: '#9b7fcc', icon: '⬡' };
  _pendingEntities.push({
    value_id: null, category_name: s.category, name: s.name,
    color: typeInfo.color, icon: typeInfo.icon, is_new: !cat,
  });
  _suggestedTags = _suggestedTags.filter((_, i) => i !== idx);
  _renderSuggestionsBar();
  _renderEntityChips();
  // Auto-save immediately if we already have a session; otherwise pending tags
  // are saved automatically when the first message is sent (_saveEntitiesToSession
  // is called in the send handler after the session ID is returned).
  if (_sessionId) {
    await _saveEntitiesToSession();
  } else {
    _updateSaveButton();
  }
};

window._dismissSuggestedTag = (idx) => {
  _suggestedTags = _suggestedTags.filter((_, i) => i !== idx);
  _renderSuggestionsBar();
};

window._dismissAllSuggestions = () => {
  _suggestedTags = [];
  _renderSuggestionsBar();
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
  { cmd: '/pipeline',   args: '[status]',          desc: 'Show pipeline health dashboard'           },
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

/** Render session list from _sessionCache into #chat-sessions container. */
function _renderSessionList(container) {
  if (!container) return;
  if (!_sessionCache.length) {
    container.innerHTML = '<div style="font-size:0.65rem;color:var(--muted);padding:0.5rem 0.25rem">No sessions yet</div>';
    return;
  }
  container.innerHTML = _sessionCache.slice(0, 60).map((s) => {
    const isActive  = s.id === _sessionId;
    const srcColor  = s.source === 'ui' ? 'var(--accent)' : s.source === 'claude_cli' ? 'var(--blue)' : 'var(--green)';
    const srcLabel  = s.source === 'ui' ? 'UI' : s.source === 'claude_cli' ? 'CLI' : 'WF';
    const hasPhase  = !!(s.phase);
    const phaseTxt  = s.phase || null;
    const tagDot    = hasPhase
      ? `<span style="font-size:0.5rem;background:var(--accent)22;color:var(--accent);padding:0 0.22rem;border-radius:2px;flex-shrink:0">${_esc(phaseTxt)}</span>`
      : `<span style="font-size:0.5rem;color:#e74c3c;flex-shrink:0" title="Missing phase">⚠</span>`;
    const featureTxt = s.feature ? `<span style="font-size:0.5rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:60px">#${_esc(s.feature)}</span>` : '';
    const borderL   = !hasPhase ? '2px solid #e74c3c' : (isActive ? '2px solid var(--accent)' : '2px solid transparent');
    const sid5      = s.id ? s.id.slice(-5) : '?????';
    return `
      <div onclick="window._chatLoadAny('${_esc(s.id)}')"
        style="padding:0.32rem 0.45rem;border-radius:var(--radius);cursor:pointer;
               border-left:${borderL};font-size:0.63rem;
               color:${isActive ? 'var(--text)' : 'var(--text2)'};
               background:${isActive ? 'var(--surface2)' : ''};
               transition:background 0.1s;margin-bottom:1px"
        title="${_esc(s.id)}"
        onmouseenter="this.style.background='var(--surface2)'"
        onmouseleave="this.style.background='${isActive ? 'var(--surface2)' : ''}'">
        <div style="display:flex;align-items:center;gap:0.3rem;margin-bottom:2px">
          <span style="font-size:0.5rem;color:${srcColor};background:${srcColor}1a;
                       padding:0 0.22rem;border-radius:2px;flex-shrink:0;letter-spacing:0.5px">${srcLabel}</span>
          ${tagDot}
          ${featureTxt}
          <span style="margin-left:auto;font-family:monospace;font-size:0.48rem;color:var(--accent);flex-shrink:0">(${_esc(sid5)})</span>
        </div>
        <div style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:0.6rem">${_esc(s.title)}</div>
      </div>`;
  }).join('');
}

async function _loadSessions(opts = {}) {
  const container = document.getElementById('chat-sessions');
  if (!container) return;

  const projectName = state.currentProject?.name;

  // Pre-set session ID from runtime state so the very first render shows the right session.
  // This is synchronous — no network call needed (loaded when project was opened).
  if (!_sessionId) {
    const lastKnown = state.currentProject?.dev_runtime_state?.last_session_id;
    if (lastKnown) _sessionId = lastKnown;
  }

  // ── 1. Quick render from localStorage cache (avoids blank sidebar on load) ──
  const cacheKey  = _sessCacheKey(projectName || '_');
  const fromCache = !opts.force && !_sessionCache.length;
  if (fromCache) {
    try {
      const raw = localStorage.getItem(cacheKey);
      if (raw) {
        const cached = JSON.parse(raw);
        _sessionCache = cached;
        _renderSessionList(container);
      }
    } catch { /* corrupt cache — ignore */ }
  }

  // ── 2. Find the latest timestamp we already have (for delta hint to server) ──
  const latestTs = _sessionCache.reduce((best, s) => s.ts > best ? s.ts : best, '');

  const merged = [];

  // ── 3. UI sessions ──────────────────────────────────────────────────────────
  try {
    const uiData = await api.chatSessions();
    const list = Array.isArray(uiData) ? uiData : uiData.sessions || [];
    list.forEach(s => merged.push({
      id: s.id,
      title: s.title || s.id.slice(0, 14),
      source: 'ui',
      ts: s.created_at || s.id,
      message_count: s.message_count || 0,
      phase: s.phase || null,
      feature: s.feature || null,
      bug_ref: s.bug_ref || null,
      tags: s.tags || {},
      entries: null,  // load on demand
    }));
  } catch { /* backend offline */ }

  // ── 4. CLI / workflow sessions from history ─────────────────────────────────
  if (projectName) {
    try {
      const histData = await api.historyChat(projectName, 300);
      const bySession = new Map();
      // Preserve existing entries for sessions already in cache (avoid re-fetching)
      for (const s of _sessionCache) {
        if (s.entries?.length) bySession.set(s.id, { ...s });
      }
      for (const e of (histData.entries || [])) {
        const src = e.source || 'ui';
        if (src === 'ui') continue;
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
        if (!s.entries) s.entries = [];
        s.message_count = (s.message_count || 0) + 1;
        s.entries.push(e);
        if (!s.phase) {
          const entryPhase = (e.tags || []).find(t => t.startsWith('phase:'))?.split(':')[1];
          if (entryPhase) { s.phase = entryPhase; s.tags = { ...(s.tags || {}), phase: entryPhase }; }
        }
      }
      merged.push(...bySession.values());
    } catch { /* silent */ }
  }

  // ── 5. Phase overrides ──────────────────────────────────────────────────────
  if (projectName) {
    try {
      const phases = await api.getSessionPhases(projectName);
      for (const s of merged) {
        const override = phases[s.id];
        if (override?.phase) { s.phase = override.phase; s.tags = { ...(s.tags || {}), phase: override.phase }; }
      }
    } catch { /* silent */ }
  }

  // Sort newest first
  merged.sort((a, b) => (b.ts || '').localeCompare(a.ts || ''));
  _sessionCache = merged;

  // Save to localStorage (without entries — keep it small)
  try {
    const toCache = merged.slice(0, 60).map(s => ({ ...s, entries: null }));
    localStorage.setItem(cacheKey, JSON.stringify(toCache));
  } catch { /* quota exceeded — ignore */ }

  // After full fetch: if _sessionId isn't in the new list, fall back to newest session.
  if (_sessionId && !merged.find(s => s.id === _sessionId)) {
    _sessionId = merged[0]?.id || null;
  } else if (!_sessionId && merged.length) {
    _sessionId = merged[0].id;
  }

  _renderSessionList(container);
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
  _chatTagCache = null;  // reset per-message tag cache
  // Restore phase for this session (from cache tags populated in _loadSessions)
  _restoreTagBar(session.tags || {});
  const msgs = document.getElementById('chat-messages');
  if (!msgs) return;
  msgs.innerHTML = '';
  _updateSessionIdBadge(id);
  if (!session.entries?.length) {
    _appendSystemMsg('No messages in this session.');
    return;
  }
  // Sort entries oldest-first so messages flow top→bottom chronologically
  const _NOISE = ['<task-notification>', '<tool-use-id>', '<task-id>', '<parameter>'];
  const chronological = [...session.entries].sort((a, b) => (a.ts || '').localeCompare(b.ts || ''));
  for (const e of chronological) {
    const inp = e.user_input || '';
    // Skip internal Claude Code tool noise entries
    if (_NOISE.some(p => inp.startsWith(p))) continue;
    if (inp) _appendUserMsg(inp, { ts: e.created_at || e.ts, tags: e.tags || [], sourceId: e.ts });
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
  _pendingEntities = [];
  _suggestedTags = [];
  _chatTagCache = null;
  _updateSessionIdBadge(null);
  _closeEntityPicker();
  const msgs = document.getElementById('chat-messages');
  if (msgs) msgs.innerHTML = '';
  _showWelcome();  // roles already loaded — show immediately
  _renderEntityChips();
  _renderSuggestionsBar();
  _updateSaveButton();
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

/** Fetch commits for this session and show a footer section in the messages area. */
async function _renderSessionCommits(msgsContainer, sessionId, project) {
  // Remove stale commits footer if any
  const old = document.getElementById('session-commits-footer');
  if (old) old.remove();
  if (!sessionId) return;
  try {
    const data = await api.getSessionCommits(sessionId, project);
    const commits = data.commits || [];
    if (!commits.length) return;
    const ghBase = (data.github_repo || '').replace(/\/$/, '');
    const rows = commits.map(c => {
      const hash  = (c.commit_hash || '').slice(0, 8);
      const date  = (c.committed_at || '').slice(0, 16).replace('T', ' ');
      const msg   = (c.commit_msg || '').slice(0, 80);
      const hashEl = ghBase
        ? `<a href="${ghBase}/commit/${_esc(c.commit_hash)}" target="_blank"
              style="font-family:monospace;color:var(--accent);text-decoration:none"
              title="Open in GitHub">${hash} ↗</a>`
        : `<span style="font-family:monospace;color:var(--accent)">${hash}</span>`;
      return `<div style="display:flex;gap:0.6rem;align-items:baseline;padding:0.18rem 0;
                          border-bottom:1px solid var(--border);font-size:0.62rem">
        ${hashEl}
        <span style="color:var(--muted);white-space:nowrap">${_esc(date)}</span>
        <span style="color:var(--text2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">${_esc(msg)}</span>
        ${c.feature ? `<span style="color:#27ae60;white-space:nowrap;font-size:0.55rem">#${_esc(c.feature)}</span>` : ''}
      </div>`;
    }).join('');
    const footer = document.createElement('div');
    footer.id = 'session-commits-footer';
    footer.style.cssText = 'margin:1rem 0.75rem 0.5rem;border:1px solid var(--border);border-radius:6px;overflow:hidden';
    footer.innerHTML = `
      <div style="display:flex;align-items:center;gap:0.5rem;padding:0.35rem 0.6rem;
                  background:var(--surface2);border-bottom:1px solid var(--border)">
        <span style="font-size:0.6rem;font-weight:700;color:var(--muted);letter-spacing:1px;text-transform:uppercase">
          ⑂ ${commits.length} Commit${commits.length !== 1 ? 's' : ''} in this session
        </span>
        ${ghBase ? `<a href="${ghBase}/commits" target="_blank"
            style="font-size:0.55rem;color:var(--accent);text-decoration:none;margin-left:auto">
            View on GitHub ↗</a>` : ''}
      </div>
      <div style="padding:0.3rem 0.6rem 0.2rem">${rows}</div>`;
    msgsContainer.appendChild(footer);
  } catch { /* silent — no commits or no backend */ }
}

window._chatLoad = async (id) => {
  _sessionId = id;
  _chatTagCache = null;  // reset per-message tag cache for fresh session
  try {
    const session = await api.chatSession(id);
    const msgs = document.getElementById('chat-messages');
    if (!msgs) return;
    msgs.innerHTML = '';
    // Restore phase/session tags — prefer session metadata, fall back to session cache
    // (cache is populated from list_sessions which also reads metadata.tags)
    const storedTags = session.metadata?.tags || {};
    const cacheTags  = _sessionCache.find(s => s.id === id)?.tags || {};
    const effectiveTags = Object.keys(storedTags).length ? storedTags : cacheTags;
    _restoreTagBar(effectiveTags);
    // Update session ID badge in tag bar
    _updateSessionIdBadge(id);
    for (const m of session.messages || []) {
      if (m.role === 'user')      _appendUserMsg(m.content);
      if (m.role === 'assistant') _appendAssistantMsg(m.content);
    }
    // Reload confirmed entity tags from DB (they live in event_tags, not session metadata)
    const project = state.currentProject?.name;
    try {
      const tagData = await api.entities.getEntitySessionTags(id, project);
      _appliedEntities = (tagData.tags || []).map(t => ({
        value_id:      t.id,
        category_name: t.category_name,
        name:          t.name,
        color:         t.color,
        icon:          t.icon,
      }));
      _renderEntityChips();
      _updateSaveButton();
    } catch { /* DB unavailable — silent */ }
    // Load commits associated with this session
    _renderSessionCommits(msgs, id, project);
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
      `| \`/clear\` | Clear conversation history |\n` +
      `| \`/pipeline [status]\` | Show pipeline health dashboard |`
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
      // Load LLM-suggested tags into the dedicated suggestions banner
      if (result.suggested_tags?.length) {
        _suggestedTags = result.suggested_tags;
        _renderSuggestionsBar();
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
        _appendSystemMsg(`📎 **${result.suggested_tags.length}** AI tag suggestion${result.suggested_tags.length > 1 ? 's' : ''} appeared above the chat — review and accept or dismiss.`);
      } else if (result.suggestions_note) {
        _appendSystemMsg(`ℹ️ No tag suggestions: *${result.suggestions_note}* — check backend logs for detail.`);
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

  // Handle /pipeline [status] — show pipeline health as formatted message
  if (message === '/pipeline' || message === '/pipeline status') {
    input.value = '';
    input.style.height = 'auto';
    const proj = state.currentProject?.name;
    if (!proj) { toast('No project open', 'error'); return; }
    _appendSystemMsg('Fetching pipeline status…');
    try {
      const data = await api.pipeline.status(proj);
      const last24h = data?.last_24h || {};
      const pending = data?.pending || {};
      const pipelines = ['commit_embed','commit_store','commit_code_extract','session_summary','tag_match','work_item_embed'];
      const labels    = { commit_embed:'commit_embed', commit_store:'commit_store',
                          commit_code_extract:'commit_code', session_summary:'session_summary',
                          tag_match:'tag_match', work_item_embed:'wi_embed' };
      let table = `## Pipeline Health — last 24h\n\n`;
      table += `| Pipeline | OK | Errors | Skipped | Last Run |\n`;
      table += `|---|---|---|---|---|\n`;
      for (const key of pipelines) {
        const s = last24h[key] || { ok: 0, error: 0, skipped: 0, last_run: null };
        const lastRun = s.last_run ? new Date(s.last_run).toLocaleTimeString() : '—';
        table += `| \`${labels[key]}\` | ${s.ok} | ${s.error} | ${s.skipped} | ${lastRun} |\n`;
      }
      const pendingLines = [];
      if (pending.commits_not_embedded > 0) pendingLines.push(`- ${pending.commits_not_embedded} commit(s) not embedded`);
      if (pending.work_items_unmatched > 0) pendingLines.push(`- ${pending.work_items_unmatched} work item(s) unmatched`);
      if (pendingLines.length) table += `\n**Pending:**\n${pendingLines.join('\n')}`;
      _appendSystemMsg(table);
      // Also navigate to the Pipeline tab
      window._nav('pipeline');
    } catch (e) {
      _appendSystemMsg(`**Pipeline status error:** ${e.message}`);
    }
    return;
  }

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
    if (sid) {
      _sessionId = sid;
      // Auto-apply any tags that were queued before the session existed
      if (_pendingEntities.length) _saveEntitiesToSession();
    }

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

function _appendUserMsg(text, opts = {}) {
  // opts: { ts, tags, sourceId }
  const container = document.getElementById('chat-messages');
  if (!container) return;
  const el = document.createElement('div');
  el.style.cssText = 'display:flex;flex-direction:column;gap:0.25rem;align-items:flex-end;animation:msgIn 0.2s ease-out';

  const tsStr   = opts.ts ? _fmtTs(opts.ts) : '';
  const sid     = opts.sourceId || '';
  const tags    = opts.tags || [];

  // Tag chips (phase/feature/bug/source etc.)
  const chipHtml = tags.map(t => {
    const col = _tagColor(t);
    return `<span style="font-size:0.5rem;background:${col}22;color:${col};border:1px solid ${col}44;padding:1px 4px;border-radius:3px;white-space:nowrap">${_esc(t)}</span>`;
  }).join('');

  // + Tag button (only for CLI entries that have a sourceId for tagBySourceId)
  const tagBtnHtml = sid
    ? `<button onclick="window._chatMsgTagPicker('${_esc(sid)}',this)"
         style="font-size:0.5rem;padding:1px 5px;border:1.5px solid var(--accent);border-radius:3px;
                cursor:pointer;background:var(--surface);color:var(--accent);white-space:nowrap;font-weight:600">
         ＋ Tag
       </button>`
    : '';

  el.innerHTML = `
    <div style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;justify-content:flex-end">
      <span style="font-size:0.55rem;color:#27ae60;font-weight:600;letter-spacing:.5px">YOU${tsStr ? ' — ' + _esc(tsStr) : ''}</span>
    </div>
    <div class="chat-msg-chips" data-sid="${_esc(sid)}"
         style="display:flex;align-items:center;gap:4px;flex-wrap:wrap;justify-content:flex-end;min-height:${(chipHtml || tagBtnHtml) ? '16px' : '0'}">
      ${chipHtml}
      ${tagBtnHtml}
    </div>
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

/** Format ISO timestamp → YY/MM/DD-HH:MM (local time). */
function _fmtTs(ts) {
  if (!ts) return '';
  const d = new Date(ts);
  if (isNaN(d.getTime())) return '';
  const YY  = String(d.getFullYear()).slice(2);
  const MM  = String(d.getMonth() + 1).padStart(2, '0');
  const DD  = String(d.getDate()).padStart(2, '0');
  const HH  = String(d.getHours()).padStart(2, '0');
  const min = String(d.getMinutes()).padStart(2, '0');
  return `${YY}/${MM}/${DD}-${HH}:${min}`;
}

/** Tag color by prefix (phase/feature/bug/source/task). */
function _tagColor(tagStr) {
  const prefix = (tagStr || '').split(':')[0];
  const MAP = { phase: '#3b82f6', feature: '#22c55e', bug: '#ef4444', source: '#a78bfa', task: '#f59e0b' };
  return MAP[prefix] || '#4a90e2';
}

/** Render a session ID + phase banner at the top of the messages container. */
function _renderSessionHeader(sessionId, phase) {
  const msgs = document.getElementById('chat-messages');
  if (!msgs || !sessionId) return;
  document.querySelectorAll('.chat-session-hdr').forEach(el => el.remove());
  const hdr = document.createElement('div');
  hdr.className = 'chat-session-hdr';
  hdr.style.cssText = 'display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:5px 10px;' +
    'background:var(--surface2);border-radius:6px;margin-bottom:10px;border-left:3px solid var(--accent);' +
    'font-size:0.6rem;position:sticky;top:0;z-index:10';
  hdr.innerHTML =
    `<span style="color:var(--muted);text-transform:uppercase;letter-spacing:.5px;white-space:nowrap">Session</span>` +
    `<span style="font-family:monospace;color:var(--accent);user-select:all;word-break:break-all;flex:1">${_esc(sessionId)}</span>` +
    `<button onclick="navigator.clipboard.writeText('${_esc(sessionId)}').then(()=>{this.textContent='✓';setTimeout(()=>this.textContent='⎘',1200)})"
       style="font-size:0.5rem;padding:1px 5px;border:1px solid var(--border);border-radius:3px;cursor:pointer;background:var(--surface);color:var(--muted);white-space:nowrap;flex-shrink:0">⎘</button>` +
    (phase ? `<span style="background:rgba(59,130,246,.15);color:#3b82f6;padding:1px 5px;border-radius:3px;flex-shrink:0">${_esc(phase)}</span>` : '');
  msgs.insertBefore(hdr, msgs.firstChild);
}

/** Per-message tag cache — loaded once per session open. */
let _chatTagCache    = null;  // [{cat, values}] or null = not loaded yet
let _sessRefreshTimer = null; // auto-refresh interval for session sidebar

const _sessCacheKey = (proj) => `aicli_sess_v1_${proj}`;

/** Update session ID badge in tag bar — shows last 5 chars; click = copy full ID. */
function _updateSessionIdBadge(id) {
  const badge = document.getElementById('chat-session-id-badge');
  if (!badge) return;
  if (!id) { badge.style.display = 'none'; badge.dataset.fullId = ''; return; }
  badge.dataset.fullId = id;
  badge.textContent    = `(${id.slice(-5)})`;
  badge.title          = `Session: ${id}\n(click to copy)`;
  badge.style.display  = '';
  badge.onclick = () => navigator.clipboard.writeText(id).then(() => {
    badge.textContent = '✓ copied';
    setTimeout(() => { badge.textContent = `(${id.slice(-5)})`; }, 1400);
  });
}

/** Load + flatten planner_tags into _chatTagCache. */
async function _ensureChatTagCache() {
  if (_chatTagCache !== null) return;
  const project = state.currentProject?.name;
  if (!project) { _chatTagCache = []; return; }
  try {
    const res  = await api.tags.list(project);
    const flat = [];
    const flatten = items => { for (const t of (items||[])) { flat.push(t); if (t.children?.length) flatten(t.children); } };
    flatten(Array.isArray(res) ? res : (res.tags || []));
    const groups = {};
    for (const t of flat) {
      const cat = t.category_name || 'other';
      if (!groups[cat]) groups[cat] = { cat: { name: cat, color: t.color || '#4a90e2', id: t.category_id }, values: [] };
      groups[cat].values.push({ name: t.name, tagStr: `${cat}:${t.name}` });
    }
    _chatTagCache = Object.values(groups);
  } catch { _chatTagCache = []; }
}

/** Open a mini per-message tag picker anchored to buttonEl (for CLI sessions). */
window._chatMsgTagPicker = async (sourceId, buttonEl) => {
  // Remove any existing pickers
  document.querySelectorAll('.chat-msg-tag-picker').forEach(el => el.remove());
  await _ensureChatTagCache();
  const project = state.currentProject?.name || '';

  const picker = document.createElement('div');
  picker.className = 'chat-msg-tag-picker';
  picker.style.cssText = 'position:absolute;right:0;top:100%;z-index:400;background:var(--bg);' +
    'border:1px solid var(--border);border-radius:6px;padding:5px;min-width:170px;' +
    'max-height:220px;overflow-y:auto;box-shadow:0 4px 16px rgba(0,0,0,.3)';

  const groups = _chatTagCache || [];
  picker.innerHTML = `<div style="font-size:0.55rem;color:var(--muted);padding:2px 4px;margin-bottom:3px">Add tag to this prompt:</div>` +
    (groups.length
      ? groups.map(({ cat, values }) =>
          `<div style="font-size:0.5rem;color:var(--muted);padding:1px 4px;text-transform:uppercase;letter-spacing:.5px;margin-top:4px">${_esc(cat.name)}</div>` +
          values.map(v =>
            `<div onclick="window._chatMsgTagApply('${_esc(sourceId)}','${_esc(v.tagStr)}',this)"
               style="padding:2px 8px;cursor:pointer;border-radius:3px;font-size:0.65rem;color:${_esc(cat.color || 'var(--text)')}"
               onmouseenter="this.style.background='var(--surface)'" onmouseleave="this.style.background=''">
               ${_esc(v.name)}
             </div>`
          ).join('')
        ).join('')
      : `<div style="font-size:0.6rem;color:var(--muted);padding:4px 8px">No tags available.</div>`
    );

  const wrap = buttonEl.closest('[style*="position:relative"]') || buttonEl.parentElement;
  wrap.style.position = 'relative';
  wrap.appendChild(picker);
  setTimeout(() => {
    document.addEventListener('click', function _close(ev) {
      if (!picker.contains(ev.target) && ev.target !== buttonEl) {
        picker.remove(); document.removeEventListener('click', _close);
      }
    });
  }, 10);
};

/** Apply a tag string to a prompt via tagBySourceId; update the chips div. */
window._chatMsgTagApply = async (sourceId, tagStr, triggerEl) => {
  document.querySelectorAll('.chat-msg-tag-picker').forEach(el => el.remove());
  const project = state.currentProject?.name || '';
  const col = _tagColor(tagStr);
  // Find the chips container for this sourceId
  const chipsDiv = document.querySelector(`.chat-msg-chips[data-sid="${CSS.escape(sourceId)}"]`);
  if (chipsDiv) {
    const chip = document.createElement('span');
    chip.style.cssText = `font-size:0.55rem;background:${col}22;color:${col};border:1px solid ${col}44;padding:1px 4px;border-radius:3px;white-space:nowrap`;
    chip.textContent = tagStr;
    chipsDiv.insertBefore(chip, chipsDiv.querySelector('button'));
  }
  try {
    await api.entities.tagBySourceId({ source_id: sourceId, tag: tagStr, project });
  } catch (e) { console.warn('tag prompt failed:', e.message); }
};

// ── CSS animations ────────────────────────────────────────────────────────────

const _style = document.createElement('style');
_style.textContent = `
  @keyframes msgIn        { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
  @keyframes cursorBlink  { 0%,49%{opacity:0.3} 50%,100%{opacity:0} }
`;
document.head.appendChild(_style);
