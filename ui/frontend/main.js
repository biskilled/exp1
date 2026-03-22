import { initLayout } from './utils/layout.js';
import { api, addRecentProject, getRecentProjects } from './utils/api.js';
import { renderAdmin as _renderAdminView } from './views/admin.js';
import { state, setState } from './stores/state.js';
import { toast } from './utils/toast.js';
import { renderLogin, checkStoredAuth, logout } from './views/login.js';
import { renderHome } from './views/home.js';
import { renderSummary } from './views/summary.js';
import { renderChat } from './views/chat.js';
import { renderPrompts } from './views/prompts.js';
import { renderCode } from './views/code.js';
import { renderDocuments } from './views/documents.js';
import { renderGraphWorkflow, destroyGraphWorkflow } from './views/graph_workflow.js';
import { renderSettings } from './views/settings.js';
import { HistoryView } from './views/history.js';
import { renderEntities } from './views/entities.js';
import { loadTagCache } from './utils/tagCache.js';
import { closeWindow, minimizeWindow, maximizeWindow } from './utils/tauri.js';

// ── History singleton — reused across tab switches, recreated on project change ─
let _historyViewInstance = null;
let _historyViewProject  = null;

function renderHistory(container) {
  const proj = state.currentProject?.name || null;
  if (_historyViewInstance && _historyViewProject === proj) {
    // Reuse existing instance: just re-attach its DOM to the container
    container.innerHTML = '';
    // The HistoryView writes into `container`, so we only need to re-call
    // _render() + restore the current tab without re-fetching data.
    _historyViewInstance.container = container;
    _historyViewInstance._render();
    _historyViewInstance._loadTab(_historyViewInstance.activeTab || 'chat');
    return;
  }
  // New project or first open — create fresh
  _historyViewProject  = proj;
  _historyViewInstance = new HistoryView(container);
}

// ── Project nav tabs ───────────────────────────────────────────────────────────

const PROJECT_TABS = [
  { id: 'summary',  icon: '📄', label: 'Summary'  },
  { id: 'chat',     icon: '◉',  label: 'Chat'     },
  { id: 'planner',  icon: '◎',  label: 'Planner'  },
  { id: 'prompts',  icon: '≡',  label: 'Roles'    },
  { id: 'code',      icon: '</>',label: 'Code'      },
  { id: 'documents', icon: '📋', label: 'Documents' },
  { id: 'workflow',  icon: '◈',  label: 'Pipelines' },
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

  // 1. Check backend health — retry up to 8× (1.5 s apart) so the UI waits
  //    for the backend process to finish starting rather than immediately
  //    showing "No projects" because the first request was refused.
  let backendOk = false;
  for (let attempt = 0; attempt < 8; attempt++) {
    try {
      const h = await api.health();
      backendOk = true;
      setState({ backendOnline: true, requireAuth: h.require_auth || false });
      break;
    } catch {
      if (attempt < 7) {
        // Show "Connecting…" with attempt count so the user sees progress
        const st = document.getElementById('status-text');
        if (st) st.textContent = `Connecting… (${attempt + 1})`;
        await new Promise(r => setTimeout(r, 1500));
      } else {
        setState({ backendOnline: false });
        updateStatusDot();
      }
    }
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
  updateStatusDot();
  renderSidebarContent();
  navigateTo('home');  // render immediately (may be empty)

  // Await project list — ensures home re-render happens before auto-restore
  let projects = [];
  try {
    const data = await api.listProjects();
    projects = data.projects || [];
    setState({ projects });
    renderSidebarContent();
    // Force home page re-render with loaded projects
    if (state.activeView === 'home') {
      const vc = document.getElementById('views-container');
      const view = vc?.querySelector('.view.active') || vc?.querySelector('.view');
      if (view) renderHome(view);
    }
  } catch (e) {
    console.warn('Could not load projects:', e.message);
  }

  // Auto-restore last open project
  if (projects.length) {
    const recent = getRecentProjects();
    const allNames = projects.map(p => p.name);
    const lastProject = recent.find(n => allNames.includes(n));
    if (lastProject) {
      _markProjectRestoring(lastProject);
      setTimeout(() => openProject(lastProject).catch(() => {}), 200);
    }
  }

  if (state.backendOnline && state.user?.email) {
    updateBalanceChip().catch(() => {});
  }
}

function _markProjectRestoring(name) {
  // Add a subtle "Restoring…" indicator on the home page card while loading
  requestAnimationFrame(() => {
    const cards = document.querySelectorAll('[data-project-name]');
    cards.forEach(el => {
      if (el.dataset.projectName === name) {
        el.style.borderColor = 'var(--accent)';
        const badge = document.createElement('span');
        badge.id = 'restore-badge';
        badge.style.cssText = 'font-size:0.6rem;color:var(--accent);margin-left:auto';
        badge.textContent = '↺ restoring…';
        el.querySelector('div')?.appendChild(badge);
      }
    });
  });
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
          <div style="display:none;align-items:center;gap:0.3rem" id="balance-chip-wrap">
            <div id="balance-chip" onclick="window._updateBalance()" title="Click to refresh balance"
              style="font-size:0.65rem;padding:0.2rem 0.5rem;border-radius:var(--radius);
                     background:var(--surface2);cursor:pointer;user-select:none"></div>
            <button id="balance-refresh-btn" onclick="window._updateBalance()" title="Refresh balance"
              style="background:none;border:none;color:var(--muted);cursor:pointer;
                     font-size:0.72rem;padding:2px 3px;line-height:1;transition:opacity 0.2s">↺</button>
          </div>
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
           data-label="Pipelines"
           onclick="window._nav('workflow')">
        <span class="nav-icon">◈</span>
        <span class="nav-label">Pipelines</span>
      </div>
    `;
  }
}

function renderSidebarFooter() {
  const footer = document.getElementById('sidebar-footer');
  if (!footer) return;

  const u = state.user;

  if (u) {
    const initials = (u.email || '?').slice(0, 2).toUpperCase();
    const role     = u.role || (u.is_admin ? 'admin' : 'free');
    const isAdmin  = role === 'admin';
    const roleColors = { admin: 'var(--accent)', paid: 'var(--green)', free: 'var(--muted)' };
    const roleColor  = roleColors[role] || 'var(--muted)';
    footer.innerHTML = `
      <div class="sidebar-user">
        <div class="sidebar-user-avatar" title="${u.email}">${initials}</div>
        <div class="sidebar-user-info nav-label">
          <div class="sidebar-user-email" style="font-size:0.72rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${u.email}</div>
          <div style="font-size:0.58rem;color:${roleColor};text-transform:uppercase;letter-spacing:0.04em;margin-top:1px">${role}</div>
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
  document.getElementById('login-modal-overlay')?.remove();

  const overlay = document.createElement('div');
  overlay.id = 'login-modal-overlay';
  overlay.style.cssText =
    'position:fixed;inset:0;z-index:9000;display:flex;align-items:center;' +
    'justify-content:center;background:rgba(0,0,0,0.65);backdrop-filter:blur(4px)';
  document.body.appendChild(overlay);

  const _close = () => overlay.remove();

  // renderLogin now owns the close button inside the card via onClose param
  import('./views/login.js').then(({ renderLogin }) => {
    renderLogin(overlay, state.settings.backend_url, (token, user) => {
      overlay.remove();
      localStorage.setItem('aicli_token', token);
      localStorage.setItem('aicli_user', JSON.stringify(user));
      setState({ user });
      renderSidebarFooter();
      toast(`Signed in as ${user.email}`, 'success');
      updateBalanceChip().then(() => renderSidebarFooter()).catch(() => {});
    }, _close);

    if (initialMode === 'register') {
      setTimeout(() => document.getElementById('tab-register')?.click(), 50);
    }
  });

  // Click outside the card also closes
  overlay.addEventListener('click', (e) => { if (e.target === overlay) _close(); });
};

function updateStatusDot() {
  const dot = document.getElementById('status-dot');
  const txt = document.getElementById('status-text');
  if (dot) dot.className = `status-dot ${state.backendOnline ? 'online' : ''}`;
  if (txt) txt.textContent = state.backendOnline ? 'Online' : 'Offline';
}

export async function updateBalanceChip() {
  const chip = document.getElementById('balance-chip');
  const wrap = document.getElementById('balance-chip-wrap');
  const refreshBtn = document.getElementById('balance-refresh-btn');
  if (!chip || !wrap) return;

  // Show loading state
  chip.style.opacity = '0.5';
  if (refreshBtn) { refreshBtn.style.opacity = '0.3'; refreshBtn.style.pointerEvents = 'none'; }

  const _set = (text, color, bg, title) => {
    chip.innerHTML = `${text} <span style="opacity:0.45;font-size:0.6em">↺</span>`;
    chip.style.color = color;
    chip.style.background = bg || 'var(--surface2)';
    chip.style.opacity = '1';
    chip.title = title || 'Click to refresh';
    wrap.style.display = 'flex';
  };

  try {
    const b = await api.billingBalance();
    setState({ balanceInfo: b });
    const role = b.role || 'free';

    if (role === 'admin') {
      // Placeholder while fetching platform stats + provider balances
      _set('Admin', 'var(--accent)', 'rgba(255,107,53,0.12)', 'Click to refresh');

      Promise.all([
        api.adminGetStats(),
        api.adminGetProviderBalances().catch(() => ({})),
      ]).then(([stats, provBals]) => {
        setState({ platformStats: stats });
        const total   = stats.total_added_usd   ?? 0;
        const charged = stats.total_charged_usd ?? 0;
        // Compute total remaining API provider budget
        const tracked = stats.by_provider || {};
        let apiRemaining = null;
        Object.entries(provBals).forEach(([prov, bal]) => {
          if (bal?.balance_usd != null) {
            const spent = tracked[prov]?.real_cost_usd || 0;
            if (apiRemaining === null) apiRemaining = 0;
            apiRemaining += Math.max(0, bal.balance_usd - spent);
          }
        });
        const apiPart = apiRemaining !== null
          ? ` | API: $${apiRemaining.toFixed(2)}`
          : '';
        const apiColor = apiRemaining === null ? 'var(--muted)'
          : apiRemaining >= 5 ? 'var(--green)' : apiRemaining >= 1 ? 'var(--accent)' : 'var(--red)';
        _set(
          `Credits: $${total.toFixed(2)} · Used: $${charged.toFixed(2)}<span style="color:${apiColor}">${apiPart}</span>`,
          'var(--accent)', 'rgba(255,107,53,0.12)',
          'Platform credits (user wallets) + API provider remaining budget. Click to refresh.',
        );
        renderSidebarFooter();
      }).catch(() => {
        _set('Admin ↺', 'var(--accent)', 'rgba(255,107,53,0.12)', 'Click to refresh');
      });

    } else if (role === 'free') {
      const used  = b.free_tier_used_usd ?? 0;
      const limit = b.free_tier_limit_usd ?? 5;
      _set(`Free · $${used.toFixed(2)} / $${limit.toFixed(2)}`, 'var(--text2)', 'var(--surface2)',
           'Free tier usage. Click to refresh.');

    } else {
      const bal = b.balance_usd ?? 0;
      const color = bal >= 1 ? 'var(--green)' : bal >= 0.1 ? 'var(--accent)' : 'var(--red)';
      _set(`$${bal.toFixed(2)}`, color, 'var(--surface2)', 'Your platform credit balance. Click to refresh.');
    }

    if (state.user?.email) {
      setState({ user: { ...state.user, role, balance_usd: b.balance_usd } });
      renderSidebarFooter();
    }

  } catch {
    if (wrap) wrap.style.display = 'none';
  } finally {
    if (refreshBtn) { refreshBtn.style.opacity = '1'; refreshBtn.style.pointerEvents = ''; }
  }
}

window._updateBalance = updateBalanceChip;

// ── Navigation ────────────────────────────────────────────────────────────────

window._nav = navigateTo;

export function navigateTo(viewId, opts = {}) {
  setState({ activeView: viewId });

  // Clean up any running intervals from the pipeline view before tearing down its DOM.
  destroyGraphWorkflow();

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
    case 'home':
      renderHome(view);
      // Refresh on every home visit (user may have added projects from CLI)
      api.listProjects().then(d => {
        const fresh = d.projects || [];
        setState({ projects: fresh });
        renderSidebarContent();
        renderHome(view);  // always re-render
      }).catch(() => {});
      break;
    case 'summary':  renderSummary(view, proj?.name);         break;
    case 'chat':     renderChat(view);                        break;
    case 'planner':  renderEntities(view);                    break;
    case 'prompts':  renderPrompts(view, proj?.name);         break;
    case 'code':      renderCode(view, proj?.name, proj);           break;
    case 'documents': renderDocuments(view, proj?.name);            break;
    case 'workflow':  renderGraphWorkflow(view);                     break;
    case 'history':  renderHistory(view);                     break;
    case 'settings': renderSettings(view);                    break;
    case 'admin':    _renderAdminView(view);                  break;
    default:
      view.innerHTML = `<div class="empty-state"><p>View not found: ${viewId}</p></div>`;
  }

  renderSidebarNav();
}

// ── Open project (shared helper) ──────────────────────────────────────────────

export async function openProject(name) {
  // Show "opening…" in the titlebar immediately — visible during DB cold-start
  const tp = document.getElementById('titlebar-project');
  if (tp) tp.innerHTML = `<span style="font-size:0.75rem;color:var(--muted)">Opening ${name}…</span>`;

  try {
    const project = await api.getProject(name);
    await api.switchProject(name);
    // Use CONTEXT.md as system prompt if available (most current, includes history).
    // Fall back to CLAUDE.md (role definition + key decisions), then PROJECT.md.
    project.system_prompt = project.context_md || project.claude_md || project.project_md || '';
    setState({ currentProject: project });
    addRecentProject(name);
    // Pre-warm tag cache so chat picker + planner have zero-latency data
    loadTagCache(name).catch(() => {});

    // Update titlebar — clear the "Opening…" state
    if (tp) tp.innerHTML = `<span style="font-size:0.75rem;color:var(--accent)">${name}</span><span class="caret">▾</span>`;

    navigateTo('summary');

    // Memory health check — show amber banner if too many prompts since last /memory
    api.getMemoryStatus(name).then(s => {
      if (s.needs_memory) _showMemoryBanner(s, name);
    }).catch(() => {});

    // Background context refresh — regenerates CLAUDE.md + CONTEXT.md, copies to code dir.
    // Runs after navigation so it doesn't block the UI opening.
    // Throttled to once per 30 minutes per project (sessionStorage TTL).
    const CTX_TTL = 30 * 60 * 1000;
    const ctxKey  = `ctx_refresh_${name}`;
    const lastCtx = parseInt(sessionStorage.getItem(ctxKey) || '0', 10);
    if (Date.now() - lastCtx > CTX_TTL) {
      sessionStorage.setItem(ctxKey, String(Date.now()));
      api.getProjectContext(name, true).then(data => {
        const fresh = data.context || data.claude_md || '';
        if (fresh && state.currentProject?.name === name) {
          setState({ currentProject: { ...state.currentProject, system_prompt: fresh } });
        }
      }).catch(() => {/* silent — don't block project open */});
    }

  } catch (e) {
    // Reset titlebar on failure
    const tpErr = document.getElementById('titlebar-project');
    if (tpErr) tpErr.innerHTML = `<span style="font-size:0.75rem;color:var(--muted)">No project</span><span class="caret">▾</span>`;
    toast(`Could not open project: ${e.message}`, 'error');
  }
}

// ── Memory health banner ──────────────────────────────────────────────────────

function _showMemoryBanner(status, projectName) {
  const key = `memory-banner-dismissed-${projectName}`;
  if (sessionStorage.getItem(key)) return;

  // Remove any existing banner
  document.getElementById('memory-health-banner')?.remove();

  const n = status.prompts_since_last_memory || 0;
  const days = status.days_since_last_memory;
  const ageStr = days != null ? ` (${days} day${days !== 1 ? 's' : ''} ago)` : '';

  const banner = document.createElement('div');
  banner.id = 'memory-health-banner';
  banner.style.cssText = [
    'display:flex;align-items:center;gap:0.75rem;padding:0.5rem 1rem',
    'background:#fff3cd;border-bottom:1px solid #ffc107;font-size:0.72rem;',
    'color:#856404;flex-shrink:0;z-index:10',
  ].join(';');
  banner.innerHTML = `
    <span style="font-size:0.95rem">⚠</span>
    <span style="flex:1">
      <strong>${n} new prompts</strong> since last /memory${ageStr}.
      Refresh AI context files to keep Claude, Cursor and Copilot in sync.
    </span>
    <button id="memory-banner-run"
      style="background:#ffc107;border:none;color:#000;font-size:0.65rem;
             padding:0.2rem 0.6rem;border-radius:4px;cursor:pointer;font-family:inherit;
             font-weight:600;white-space:nowrap">
      Run /memory
    </button>
    <button id="memory-banner-dismiss"
      style="background:none;border:none;color:#856404;font-size:0.9rem;
             cursor:pointer;padding:0;line-height:1;flex-shrink:0">✕</button>
  `;

  // Insert before main content
  const main = document.getElementById('main-content');
  if (main) main.prepend(banner);

  document.getElementById('memory-banner-run')?.addEventListener('click', async () => {
    const btn = document.getElementById('memory-banner-run');
    if (btn) { btn.disabled = true; btn.textContent = '…'; }
    try {
      await api.generateMemory(projectName);
      banner.remove();
      sessionStorage.setItem(key, '1');
      toast('Memory files refreshed', 'success');
    } catch (e) {
      toast(`/memory failed: ${e.message}`, 'error');
      if (btn) { btn.disabled = false; btn.textContent = 'Run /memory'; }
    }
  });

  document.getElementById('memory-banner-dismiss')?.addEventListener('click', () => {
    banner.remove();
    sessionStorage.setItem(key, '1');
  });
}

window._openProject = openProject;

// ── Init ──────────────────────────────────────────────────────────────────────

boot();
