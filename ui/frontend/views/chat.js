import { state, setState } from '../stores/state.js';
import { api, loadApiKeys } from '../utils/api.js';
import { toast } from '../utils/toast.js';

const PROVIDERS = [
  { id: 'claude',   label: 'Claude'   },
  { id: 'openai',   label: 'OpenAI'   },
  { id: 'deepseek', label: 'DeepSeek' },
  { id: 'gemini',   label: 'Gemini'   },
  { id: 'grok',     label: 'Grok'     },
];

let _sessionId = null;
let _provider  = 'claude';
let _streaming = false;
let _roleOptions = [];       // { path, name } — loaded when project is open
let _workflowOptions = [];   // workflow names — loaded when project is open

export function renderChat(container) {
  _provider = state.currentProject?.default_provider || 'claude';

  container.className  = 'view active';
  container.style.cssText = 'display:flex;flex-direction:column;overflow:hidden;height:100%';

  const apiKeys = loadApiKeys();

  container.innerHTML = `
    <div style="display:flex;flex:1;overflow:hidden;min-height:0">

      <!-- Session sidebar -->
      <div style="width:190px;border-right:1px solid var(--border);background:var(--surface);
                  display:flex;flex-direction:column;flex-shrink:0;overflow:hidden">
        <div style="padding:0.6rem;border-bottom:1px solid var(--border)">
          <button class="btn btn-ghost btn-sm" style="width:100%;font-size:0.7rem"
            onclick="window._chatNew()">+ New Chat</button>
        </div>
        <div style="padding:0.35rem 0.6rem 0.15rem;font-size:0.55rem;color:var(--muted);
                    letter-spacing:2px;text-transform:uppercase">Sessions</div>
        <div id="chat-sessions" style="flex:1;overflow-y:auto;padding:0.15rem 0.4rem 0.5rem"></div>
      </div>

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
                ${p.label}${!apiKeys[p.id] ? ' ⚠' : ''}
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

  _setupInput();
  _loadSessions();
  _loadRolesAndWorkflows();
  _showWelcome();
}

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
  try {
    const sessions = await api.chatSessions();
    const list = Array.isArray(sessions) ? sessions : sessions.sessions || [];
    if (!list.length) {
      container.innerHTML = '<div style="font-size:0.65rem;color:var(--muted);padding:0.5rem 0.25rem">No sessions yet</div>';
      return;
    }
    container.innerHTML = list.slice(0, 30).map(s => `
      <div onclick="window._chatLoad('${s.id}')"
        style="padding:0.4rem 0.5rem;border-radius:var(--radius);cursor:pointer;
               font-size:0.65rem;color:var(--text2);overflow:hidden;text-overflow:ellipsis;
               white-space:nowrap;transition:background 0.1s;margin-bottom:1px"
        title="${_esc(s.title || s.id)}"
        onmouseenter="this.style.background='var(--surface2)'"
        onmouseleave="this.style.background='${s.id === _sessionId ? 'var(--surface2)' : ''}'">
        ${_esc(s.title || s.id.slice(0, 14))}
      </div>`).join('');
  } catch {
    // backend offline — silent
  }
}

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
  const msgs = document.getElementById('chat-messages');
  if (msgs) msgs.innerHTML = '';
  _showWelcome();
  _loadSessions();
};

window._chatLoad = async (id) => {
  _sessionId = id;
  try {
    const session = await api.chatSession(id);
    const msgs = document.getElementById('chat-messages');
    if (!msgs) return;
    msgs.innerHTML = '';
    for (const m of session.messages || []) {
      if (m.role === 'user')      _appendUserMsg(m.content);
      if (m.role === 'assistant') _appendAssistantMsg(m.content);
    }
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

  // Handle /memory — refresh CLAUDE.md + CONTEXT.md and copy to code dir
  if (message === '/memory') {
    input.value = '';
    input.style.height = 'auto';
    const proj = state.currentProject?.name;
    if (!proj) { toast('No project open', 'error'); return; }
    _appendSystemMsg('Refreshing CLAUDE.md + CONTEXT.md…');
    try {
      const data = await api.getProjectContext(proj, true);
      // Update system prompt to freshest context
      const freshPrompt = data.context || data.claude_md || '';
      if (freshPrompt) setState({ currentProject: { ...state.currentProject, system_prompt: freshPrompt } });
      _appendSystemMsg('✓ **CLAUDE.md** + **CONTEXT.md** refreshed — copied to code directory');
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

  try {
    const response = await api.chatStream(message, _provider, _sessionId, system);

    // Session ID is in response header
    const sid = response.headers.get('X-Session-Id');
    if (sid) _sessionId = sid;

    const reader  = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer   = '';
    let fullText = '';

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

async function _autoCommitPush(projectName, userMsg, aiResponse) {
  try {
    const result = await api.gitCommitPush(projectName, {
      message_hint: userMsg.slice(0, 200),
      provider: _provider,
    });
    if (result.committed === false) return; // no changes — silent
    if (result.pushed) {
      toast(`Auto-committed & pushed: ${result.commit_message}`, 'success');
    } else {
      toast(`Auto-committed (push failed: ${result.push_error || 'check credentials in Settings'})`, 'error');
    }
  } catch (e) {
    toast(`Auto-commit failed: ${e.message}`, 'error');
  }
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
  el.style.cssText = 'text-align:center;padding:3rem 2rem;margin:auto;max-width:600px;width:100%';
  const proj = state.currentProject;
  const hasSystem = !!(proj?.system_prompt);
  el.innerHTML = `
    <div style="font-family:var(--font-ui);font-size:1.6rem;font-weight:800;letter-spacing:-1px;color:var(--accent);margin-bottom:0.4rem">aicli Chat</div>
    <div style="font-size:0.68rem;color:var(--muted);margin-bottom:0.75rem">Multi-LLM · SSE Streaming · Per-project context</div>
    ${hasSystem ? `<div style="font-size:0.65rem;color:var(--green);margin-bottom:1.25rem;display:flex;align-items:center;gap:0.4rem;justify-content:center">
      <span>✓</span> System prompt loaded from <strong>${proj.name}</strong> — use Role selector to switch
    </div>` : `<div style="font-size:0.65rem;color:var(--muted);margin-bottom:1.25rem">
      No project open — chat without context. Open a project for roles &amp; prompts.
    </div>`}
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:0.5rem">
      ${['Ask a question', 'Write code', 'Review code', 'Explain concept', 'Debug error', 'Summarise text'].map(s => `
        <div onclick="document.getElementById('chat-input').value='${s}: ';document.getElementById('chat-input').focus()"
          style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
                 padding:0.6rem 0.75rem;cursor:pointer;font-size:0.7rem;text-align:left;transition:border-color 0.1s"
          onmouseenter="this.style.borderColor='var(--accent)'"
          onmouseleave="this.style.borderColor='var(--border)'">
          ${s}
        </div>`).join('')}
    </div>
  `;
  container.appendChild(el);
}

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
