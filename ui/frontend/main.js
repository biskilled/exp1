import { initLayout } from './utils/layout.js';
import { api, addRecentProject } from './utils/api.js';
import { state, setState } from './stores/state.js';
import { toast } from './utils/toast.js';
import { renderLogin, checkStoredAuth, logout } from './views/login.js';
import { renderHome } from './views/home.js';
import { renderSummary } from './views/summary.js';
import { renderChat } from './views/chat.js';
import { renderPrompts } from './views/prompts.js';
import { renderCode } from './views/code.js';
import { renderWorkflow } from './views/workflow.js';
import { renderSettings } from './views/settings.js';
import { renderAdmin } from './views/admin.js';
import { HistoryView } from './views/history.js';
import { closeWindow, minimizeWindow, maximizeWindow } from './utils/tauri.js';

function renderHistory(container) { new HistoryView(container); }

// ── Project nav tabs ───────────────────────────────────────────────────────────

const PROJECT_TABS = [
  { id: 'summary',  icon: '📄', label: 'Summary'  },
  { id: 'chat',     icon: '◉',  label: 'Chat'     },
  { id: 'prompts',  icon: '≡',  label: 'Prompts'  },
  { id: 'code',     icon: '</>',label: 'Code'     },
  { id: 'workflow', icon: '⟳',  label: 'Workflow' },
  { id: 'history',  icon: '⏱',  label: 'History'  },
  { id: 'settings', icon: '⚙',  label: 'Settings' },
];

// ── Boot ──────────────────────────────────────────────────────────────────────

async function boot() {
  initLayout();
  renderShell();

  // Restore sidebar state
  if (localStorage.getItem('aicli_sidebar_open') === '0')
    document.body.classList.add('sidebar-collapsed');

  // 1. Check backend health + whether auth is required
  let backendOk = false;
  try {
    const h = await api.health();
    backendOk = true;
    setState({
      backendOnline: true,
      requireAuth: h.require_auth || false,
    });
  } catch {
    setState({ backendOnline: false });
    updateStatusDot();
  }

  if (!backendOk) {
    await _continueToApp(null);
    return;
  }

  // 2. Auth gate
  if (state.requireAuth) {
    const { valid, token, user } = await checkStoredAuth(state.settings.backend_url);
    if (valid) {
      setState({ user });
      await _continueToApp(user);
    } else {
      renderLogin(
        document.getElementById('app'),
        state.settings.backend_url,
        async (token, user) => {
          setState({ user });
          renderShell();
          if (localStorage.getItem('aicli_sidebar_open') === '0')
            document.body.classList.add('sidebar-collapsed');
          await _continueToApp(user);
        }
      );
    }
    return;
  }

  await _continueToApp(null);
}

async function _continueToApp(user) {
  try {
    const data = await api.listProjects();
    setState({ projects: data.projects || [] });
  } catch (e) {
    console.warn('Could not load projects:', e.message);
  }

  updateStatusDot();
  renderSidebarContent();
  navigateTo('home');
}

// ── Shell ─────────────────────────────────────────────────────────────────────

function renderShell() {
  document.getElementById('app').innerHTML = `
    <div class="app-shell" id="shell">

      <div id="titlebar">
        <button class="titlebar-toggle" onclick="window._toggleSidebar()" title="Toggle sidebar">☰</button>
        <div class="titlebar-logo">
          <span class="titlebar-icon">⬡</span>
          <span class="titlebar-name">aicli</span>
        </div>
        <span class="titlebar-sep">·</span>
        <div class="titlebar-project" id="titlebar-project" onclick="window._nav('home')" title="Switch project">
          <span style="font-size:0.68rem;color:var(--muted)">No project open</span>
        </div>
        <div class="titlebar-spacer"></div>
        <div class="titlebar-controls">
          <div class="status-pill">
            <div class="status-dot" id="status-dot"></div>
            <span id="status-text" style="font-size:0.62rem">Connecting…</span>
          </div>
        </div>
      </div>

      <div id="sidebar">
        <nav class="sidebar-nav" id="sidebar-nav"></nav>
        <div class="sidebar-footer" id="sidebar-footer"></div>
      </div>

      <div id="content">
        <div id="views-container" style="flex:1;overflow:hidden;display:flex;flex-direction:column"></div>
      </div>

    </div>
    <div class="toast-container"></div>
  `;

  window._winClose  = closeWindow;
  window._winMin    = minimizeWindow;
  window._winMax    = maximizeWindow;
  window._logout    = () => { logout(); location.reload(); };

  window._toggleSidebar = () => {
    const collapsed = document.body.classList.toggle('sidebar-collapsed');
    localStorage.setItem('aicli_sidebar_open', collapsed ? '0' : '1');
  };
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

function renderSidebarContent() {
  renderSidebarNav();
  renderSidebarFooter();
}

function renderSidebarNav() {
  const nav = document.getElementById('sidebar-nav');
  if (!nav) return;

  const proj = state.currentProject;

  if (proj) {
    // Project is open — show project tabs + back to projects
    nav.innerHTML = `
      <div class="nav-project-label" title="${proj.name}">${proj.name}</div>
      <div class="nav-divider"></div>
      ${PROJECT_TABS.map(t => `
        <div class="nav-item ${state.activeView === t.id ? 'active' : ''}"
             id="nav-${t.id}"
             data-label="${t.label}"
             onclick="window._nav('${t.id}')">
          <span class="nav-icon">${t.icon}</span>
          <span class="nav-label">${t.label}</span>
        </div>
      `).join('')}
      <div class="nav-divider"></div>
      <div class="nav-item ${state.activeView === 'home' ? 'active' : ''}"
           id="nav-home"
           data-label="Projects"
           onclick="window._nav('home')">
        <span class="nav-icon">◫</span>
        <span class="nav-label">Projects</span>
      </div>
    `;
  } else {
    // No project open — global nav
    nav.innerHTML = `
      <div class="nav-item ${state.activeView === 'home' ? 'active' : ''}"
           id="nav-home"
           data-label="Projects"
           onclick="window._nav('home')">
        <span class="nav-icon">◫</span>
        <span class="nav-label">Projects</span>
      </div>
      <div class="nav-item ${state.activeView === 'workflow' ? 'active' : ''}"
           id="nav-workflow"
           data-label="Workflows"
           onclick="window._nav('workflow')">
        <span class="nav-icon">⟳</span>
        <span class="nav-label">Workflows</span>
      </div>
    `;
  }
}

function renderSidebarFooter() {
  const footer = document.getElementById('sidebar-footer');
  if (!footer) return;

  const u = state.user;

  if (u) {
    // Logged-in user
    const initials = (u.email || '?').slice(0, 2).toUpperCase();
    const isAdmin  = u.is_admin;
    footer.innerHTML = `
      <div class="sidebar-user">
        <div class="sidebar-user-avatar" title="${u.email}">${initials}</div>
        <div class="sidebar-user-info nav-label">
          <div class="sidebar-user-email">${u.email}</div>
          ${isAdmin ? '<div style="font-size:0.58rem;color:var(--accent)">admin</div>' : ''}
        </div>
        <div class="sidebar-user-actions nav-label">
          ${isAdmin ? `<button class="sidebar-user-btn" title="Admin panel" onclick="window._nav('admin')">👥</button>` : ''}
          <button class="sidebar-user-btn" title="Settings" onclick="window._nav('settings')">⚙</button>
          <button class="sidebar-user-btn" title="Sign out"  onclick="window._logout()">↩</button>
        </div>
      </div>
    `;
  } else {
    // Not logged in — show Sign in / Create account buttons (always, even local mode)
    footer.innerHTML = `
      <div class="sidebar-user" style="flex-direction:column;align-items:stretch;gap:0.4rem;padding:0.6rem 0.75rem">
        <button class="btn btn-primary btn-sm" style="width:100%"
                onclick="window._showLoginModal('login')">Sign in</button>
        <button class="btn btn-ghost btn-sm" style="width:100%"
                onclick="window._showLoginModal('register')">Create account</button>
        <div style="display:flex;justify-content:flex-end;margin-top:0.2rem">
          <button class="sidebar-user-btn nav-label" title="Settings" onclick="window._nav('settings')">⚙ Settings</button>
        </div>
      </div>
    `;
  }
}

// ── Login modal (opens over current view) ─────────────────────────────────────

window._showLoginModal = (initialMode = 'login') => {
  // Remove any existing modal
  document.getElementById('login-modal-overlay')?.remove();

  const overlay = document.createElement('div');
  overlay.id = 'login-modal-overlay';
  overlay.style.cssText =
    'position:fixed;inset:0;z-index:9000;display:flex;align-items:center;' +
    'justify-content:center;background:rgba(0,0,0,0.65);backdrop-filter:blur(4px)';

  // Close button (top-right corner)
  const closeBtn = document.createElement('button');
  closeBtn.innerHTML = '✕';
  closeBtn.title = 'Close';
  closeBtn.style.cssText =
    'position:absolute;top:1rem;right:1rem;z-index:9001;background:none;border:none;' +
    'color:var(--text2);font-size:1.1rem;cursor:pointer;width:32px;height:32px;' +
    'display:flex;align-items:center;justify-content:center;border-radius:50%;' +
    'transition:background 0.15s';
  closeBtn.onmouseenter = () => { closeBtn.style.background = 'rgba(255,255,255,0.1)'; };
  closeBtn.onmouseleave = () => { closeBtn.style.background = 'none'; };
  closeBtn.onclick = () => overlay.remove();
  overlay.appendChild(closeBtn);

  document.body.appendChild(overlay);

  // The renderLogin card goes inside the overlay
  import('./views/login.js').then(({ renderLogin }) => {
    renderLogin(overlay, state.settings.backend_url, (token, user) => {
      overlay.remove();
      localStorage.setItem('aicli_token', token);
      localStorage.setItem('aicli_user', JSON.stringify(user));
      setState({ user });
      renderSidebarFooter();
      toast(`Signed in as ${user.email}`, 'success');
    });

    // The login card is now inside overlay — patch its mode if register
    if (initialMode === 'register') {
      setTimeout(() => {
        document.getElementById('tab-register')?.click();
      }, 50);
    }
  });

  // Click outside the card to close
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) overlay.remove();
  });
};

function updateStatusDot() {
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-text');
  if (dot) dot.className = `status-dot ${state.backendOnline ? 'online' : ''}`;
  if (txt) txt.textContent = state.backendOnline ? 'Online' : 'Offline';
}

// ── Navigation ────────────────────────────────────────────────────────────────

window._nav = navigateTo;

export function navigateTo(viewId, opts = {}) {
  setState({ activeView: viewId });

  const container = document.getElementById('views-container');
  if (!container) return;
  container.innerHTML = '';
  const view = document.createElement('div');
  view.className = 'view active';
  // No inline style here — CSS classes (.view, .view.active, .<name>-view.active) fully
  // control layout.  Inline styles override CSS specificity and would prevent per-view
  // overrides such as the display:block + overflow-y:auto needed for settings/home scroll.
  container.appendChild(view);

  const proj = state.currentProject;

  switch (viewId) {
    case 'home':     renderHome(view);                         break;
    case 'summary':  renderSummary(view, proj?.name);         break;
    case 'chat':     renderChat(view);                        break;
    case 'prompts':  renderPrompts(view, proj?.name);         break;
    case 'code':     renderCode(view, proj?.name, proj);      break;
    case 'workflow': renderWorkflow(view);                    break;
    case 'history':  renderHistory(view);                       break;
    case 'settings': renderSettings(view);                    break;
    case 'admin':    renderAdmin(view);                       break;
    default:
      view.innerHTML = `<div class="empty-state"><p>View not found: ${viewId}</p></div>`;
  }

  renderSidebarNav();
}

// ── Open project (shared helper) ──────────────────────────────────────────────

export async function openProject(name) {
  try {
    const project = await api.getProject(name);
    await api.switchProject(name);
    // Use CONTEXT.md as system prompt if available (most current, includes history).
    // Fall back to CLAUDE.md (role definition + key decisions), then PROJECT.md.
    project.system_prompt = project.context_md || project.claude_md || project.project_md || '';
    setState({ currentProject: project });
    addRecentProject(name);

    // Update titlebar
    const tp = document.getElementById('titlebar-project');
    if (tp) tp.innerHTML = `<span style="font-size:0.75rem;color:var(--accent)">${name}</span><span class="caret">▾</span>`;

    navigateTo('summary');

    // Background context refresh — regenerates CLAUDE.md + CONTEXT.md, copies to code dir.
    // Runs after navigation so it doesn't block the UI opening.
    api.getProjectContext(name, true).then(data => {
      const fresh = data.context || data.claude_md || '';
      if (fresh && state.currentProject?.name === name) {
        setState({ currentProject: { ...state.currentProject, system_prompt: fresh } });
      }
    }).catch(() => {/* silent — don't block project open */});

  } catch (e) {
    toast(`Could not open project: ${e.message}`, 'error');
  }
}

window._openProject = openProject;

// ── Init ──────────────────────────────────────────────────────────────────────

boot();
