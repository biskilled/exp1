/**
 * settings.js — Application and project settings view.
 *
 * Renders a sidebar-nav settings panel with sections for Project, API Keys, Models,
 * Backend, Billing, Security, and Agent Roles; persists changes to the backend and
 * updates local state for the active project.
 * Rendered via: renderSettings() called from main.js navigateTo().
 */

import { state, setState } from '../stores/state.js';
import { invoke } from '../utils/tauri.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { BACKEND_URL } from '../utils/config.js';
// updateBalanceChip accessed via window._updateBalance (set by main.js to avoid circular import)

const LLM_CONFIG = [
  { id: 'claude',   label: 'Claude',   color: 'var(--claude)',   placeholder: 'sk-ant-api03-...',    models: ['claude-opus-4-6', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001'] },
  { id: 'openai',   label: 'OpenAI',   color: 'var(--openai)',   placeholder: 'sk-...',               models: ['gpt-4o', 'gpt-4o-mini', 'o3-mini', 'o3'] },
  { id: 'deepseek', label: 'DeepSeek', color: 'var(--deepseek)', placeholder: 'sk-...',               models: ['deepseek-chat', 'deepseek-reasoner'] },
  { id: 'gemini',   label: 'Gemini',   color: 'var(--gemini)',   placeholder: 'AIza...',              models: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-2.0-flash'] },
  { id: 'grok',     label: 'Grok',     color: 'var(--grok)',     placeholder: 'xai-...',              models: ['grok-3', 'grok-3-fast'] },
];

export function renderSettings(container) {
  container.className = 'view active settings-view';

  container.innerHTML = `
    <div style="max-width:900px">
      <div style="font-family:var(--font-ui);font-size:1.4rem;font-weight:800;letter-spacing:-1px;margin-bottom:0.3rem">Settings</div>
      <div style="font-size:0.68rem;color:var(--text2);margin-bottom:1.5rem">API keys are encrypted with AES-256-GCM using your master password.</div>

      <div class="settings-sections">
        <div class="settings-nav">
          ${state.currentProject ? `
          <div class="settings-nav-item active" onclick="window._settingsSection('project')" id="snav-project">
            <span>◫</span> Project
          </div>` : ''}
          <div class="settings-nav-item ${!state.currentProject ? 'active' : ''}" onclick="window._settingsSection('apikeys')" id="snav-apikeys">
            <span>🔑</span> API Keys
          </div>
          <div class="settings-nav-item" onclick="window._settingsSection('models')" id="snav-models">
            <span>◉</span> Models
          </div>
          <div class="settings-nav-item" onclick="window._settingsSection('backend')" id="snav-backend">
            <span>⚡</span> Backend
          </div>
          <div class="settings-nav-item" onclick="window._settingsSection('billing')" id="snav-billing">
            <span>💳</span> Billing
          </div>
          <div class="settings-nav-item" onclick="window._settingsSection('security')" id="snav-security">
            <span>🔐</span> Security
          </div>
          <div class="settings-nav-item" onclick="window._settingsSection('roles')" id="snav-roles">
            <span>◉</span> Roles &amp; Pipelines
          </div>
          <div class="settings-nav-item" onclick="window._settingsSection('updates')" id="snav-updates">
            <span>⟳</span> Updates
          </div>
        </div>

        <div id="settings-content"></div>
      </div>
    </div>
  `;

  const defaultSection = state.currentProject ? 'project' : 'apikeys';
  renderSettingsSection(defaultSection);

  window._settingsSection = (section) => {
    setState({ activeSettingsSection: section });
    document.querySelectorAll('.settings-nav-item').forEach(el => {
      el.classList.toggle('active', el.id === `snav-${section}`);
    });
    renderSettingsSection(section);
  };
}

function renderSettingsSection(section) {
  const content = document.getElementById('settings-content');
  if (!content) return;

  const sections = {
    project:   renderProjectSettings,
    apikeys:   renderApiKeys,
    models:    renderModels,
    workspace: renderWorkspace,
    backend:   renderBackend,
    billing:   renderBilling,
    security:  renderSecurity,
    roles:     renderAgentRoles,
    updates:   (c) => _renderUpdateSection(c),
  };

  (sections[section] || renderApiKeys)(content);
}

// ── Project Settings ──────────────────────────────────────────────────────────

async function renderProjectSettings(content) {
  const proj = state.currentProject;
  if (!proj) {
    content.innerHTML = '<div class="empty-state"><p>No project open.</p></div>';
    return;
  }

  content.innerHTML = `<div style="color:var(--muted);font-size:0.72rem">Loading project config…</div>`;

  let cfg = {};
  try { cfg = await api.getProjectConfig(proj.name); } catch { cfg = proj; }

  content.innerHTML = `
    <div>
      <div class="settings-section-title">Project: ${proj.name}</div>
      <div class="settings-section-desc">Per-project configuration stored in project.yaml.</div>

      <div class="field-group">
        <div class="field-label">Description</div>
        <input class="field-input" id="proj-description" value="${_esc(cfg.description || '')}" placeholder="Short project description" />
      </div>

      <div class="field-group">
        <div class="field-label">Default LLM Provider</div>
        <select class="field-select" id="proj-provider">
          ${['claude','openai','deepseek','gemini','grok'].map(p =>
            `<option value="${p}" ${cfg.default_provider === p ? 'selected' : ''}>${p}</option>`
          ).join('')}
        </select>
      </div>

      <div class="field-group">
        <div class="field-label">Code Directory</div>
        <div style="display:flex;gap:8px">
          <input class="field-input" id="proj-codedir" value="${_esc(cfg.code_dir || '')}"
            placeholder="/path/to/your/code" style="flex:1" />
          <button class="btn btn-ghost" onclick="window._browseProjCodeDir()">Browse</button>
        </div>
        <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem">Used in Code view and for file injection into workflows.</div>
      </div>

      <div class="field-group">
        <label style="display:flex;align-items:center;gap:0.6rem;cursor:pointer;font-size:0.75rem">
          <input type="checkbox" id="proj-autocommit" ${cfg.auto_commit_push ? 'checked' : ''}
            style="width:15px;height:15px;accent-color:var(--accent);cursor:pointer" />
          <span>Auto commit &amp; push after every chat response</span>
        </label>
        <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem;margin-left:1.5rem">
          When enabled, changed files in Code Directory are auto-committed (LLM generates the message) and pushed after each AI response.
        </div>
      </div>

      <div style="margin-top:1.25rem;display:flex;gap:0.75rem">
        <button class="btn btn-primary" onclick="window._saveProjSettings()">Save Project Config</button>
      </div>
      <div id="proj-save-status" style="font-size:0.68rem;margin-top:0.5rem;color:var(--muted)"></div>

      <!-- Git Setup section -->
      <div style="margin-top:2rem;padding-top:1.5rem;border-top:1px solid var(--border)">
        <div class="settings-section-title" style="font-size:0.85rem">Git Setup</div>
        <div class="settings-section-desc">
          Connect your project to GitHub. Credentials stored in <code>_system/.git_token</code> — never committed.
        </div>
        <div id="git-status-line" style="font-size:0.68rem;color:var(--muted);margin-bottom:1rem">
          Checking git status…
        </div>

        <!-- Repository URL -->
        <div class="field-group">
          <div class="field-label">GitHub Repository URL</div>
          <div style="display:flex;gap:8px;flex-wrap:wrap">
            <input class="field-input" id="git-repo-url" value="${_esc(cfg.github_repo || '')}"
              placeholder="https://github.com/you/repo.git" style="flex:1;min-width:200px" />
            <button class="btn btn-ghost btn-sm" onclick="window._showCreateRepo()" id="git-create-btn">
              + Create on GitHub
            </button>
          </div>
          <!-- Inline create-repo form -->
          <div id="git-create-form" style="display:none;margin-top:0.6rem;padding:0.75rem;
               border-radius:var(--radius);background:var(--surface2);border:1px solid var(--border)">
            <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.5rem">
              Creates a new GitHub repository using your stored Browser Login token.
            </div>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
              <input class="field-input" id="new-repo-name" placeholder="repo-name" style="width:180px" />
              <label style="display:flex;align-items:center;gap:0.4rem;font-size:0.75rem;cursor:pointer">
                <input type="checkbox" id="new-repo-private" checked style="accent-color:var(--accent)" /> Private
              </label>
              <button class="btn btn-primary btn-sm" onclick="window._createRepoOnGitHub()">Create &amp; Connect</button>
              <button class="btn btn-ghost btn-sm" onclick="window._showCreateRepo(false)">Cancel</button>
            </div>
            <span id="git-create-status" style="font-size:0.68rem;color:var(--muted);display:block;margin-top:0.4rem"></span>
          </div>
          <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem">
            HTTPS format: <code>https://github.com/user/repo.git</code> · used for <code>/push</code> and auto-commit
          </div>
        </div>

        <!-- Default push branch -->
        <div class="field-group">
          <div class="field-label">Default Push Branch</div>
          <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
            <input class="field-input" id="git-branch" list="branch-suggestions"
              value="${_esc(cfg.git_branch || '')}" placeholder="main"
              style="width:160px" />
            <datalist id="branch-suggestions"></datalist>
            <button class="btn btn-ghost btn-sm" onclick="window._fetchBranches()" id="fetch-branches-btn">
              ↺ Fetch remote
            </button>
          </div>
          <div id="branches-hint" style="font-size:0.62rem;color:var(--muted);margin-top:0.2rem">
            Click ↺ Fetch remote to list branches from GitHub.
          </div>
        </div>

        <!-- Authentication -->
        <div style="margin-top:0.75rem">
          <div style="font-size:0.78rem;font-weight:600;color:var(--text);margin-bottom:0.5rem">Authentication</div>
          <div style="display:flex;gap:0;margin-bottom:0.75rem;border-bottom:1px solid var(--border)">
            <button id="git-tab-oauth" onclick="window._gitTab('oauth')"
              style="padding:0.4rem 0.85rem;border:none;border-bottom:2px solid var(--accent);
                     background:none;cursor:pointer;color:var(--text);font-size:0.75rem;font-weight:600">
              🌐 Browser Login
            </button>
            <button id="git-tab-pat" onclick="window._gitTab('pat')"
              style="padding:0.4rem 0.85rem;border:none;border-bottom:2px solid transparent;
                     background:none;cursor:pointer;color:var(--text2);font-size:0.75rem">
              🔑 PAT Token
            </button>
          </div>

          <!-- OAuth Device Flow panel -->
          <div id="git-panel-oauth">
            <div class="field-group">
              <div class="field-label">GitHub App Client ID</div>
              <input class="field-input" id="git-client-id" value="${_esc(cfg.github_client_id || '')}"
                placeholder="Ov23Li…" style="width:280px" />
              <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem">
                github.com → Settings → Developer settings → OAuth Apps → New OAuth App.
                Set any Homepage &amp; Callback URL to <code>http://localhost</code>. Enable <strong>Device Flow</strong> in the app settings. Copy the <strong>Client ID</strong>.
              </div>
            </div>
            <div id="git-device-box" style="display:none;margin:0.6rem 0;padding:0.85rem;
                 border-radius:var(--radius);background:var(--surface2);border:1px solid var(--border)">
              <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.4rem">
                1. Open this URL (may open automatically):
              </div>
              <a id="git-verify-url" href="#" target="_blank"
                style="font-size:0.82rem;color:var(--accent);font-weight:600;display:block;margin-bottom:0.6rem">
                github.com/login/device
              </a>
              <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.3rem">2. Enter this code:</div>
              <div id="git-user-code"
                style="font-family:monospace;font-size:1.5rem;letter-spacing:0.25em;
                       color:var(--accent);font-weight:700;margin-bottom:0.6rem">—</div>
              <div id="git-device-status" style="font-size:0.72rem;color:var(--muted)">Waiting for authorization…</div>
            </div>
            <div style="display:flex;gap:0.75rem;margin-top:0.75rem;align-items:center">
              <button class="btn btn-primary btn-sm" id="git-oauth-btn" onclick="window._startDeviceFlow()">
                Login with GitHub
              </button>
              <span id="git-oauth-status" style="font-size:0.68rem;color:var(--muted)"></span>
            </div>
          </div>

          <!-- PAT Token panel -->
          <div id="git-panel-pat" style="display:none">
            <div class="field-group">
              <div class="field-label">Git Username</div>
              <input class="field-input" id="git-username" value="${_esc(cfg.git_username || '')}"
                placeholder="your-github-username" style="width:240px" />
            </div>
            <div class="field-group">
              <div class="field-label">Git Email</div>
              <input class="field-input" id="git-email" value="${_esc(cfg.git_email || '')}"
                placeholder="you@example.com" style="width:240px" />
            </div>
            <div class="field-group">
              <div class="field-label">Personal Access Token</div>
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <input class="field-input" type="password" id="git-token"
                  placeholder="ghp_xxxxxxxxxxxx" style="flex:1;min-width:160px" />
                <button class="btn btn-ghost btn-sm" onclick="window._toggleGitToken()">👁</button>
                <a class="btn btn-ghost btn-sm"
                  href="https://github.com/settings/tokens/new?scopes=repo&description=aicli-desktop"
                  target="_blank">Open GitHub ↗</a>
              </div>
              <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem">
                GitHub → Settings → Developer settings → Personal access tokens → Generate new token → select <strong>repo</strong> scope
              </div>
            </div>
            <button class="btn btn-primary btn-sm" style="margin-top:0.5rem"
              onclick="window._saveGitCredentials()">Save &amp; Setup Git</button>
          </div>
        </div>

        <!-- Setup actions -->
        <div style="margin-top:1rem;padding-top:0.75rem;border-top:1px solid var(--border)">
          <div style="display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap">
            <button class="btn btn-ghost btn-sm" onclick="window._setupGit()">⚙ Setup Git</button>
            <button class="btn btn-ghost btn-sm" onclick="window._gitPull()" id="git-pull-btn">↓ Pull</button>
            <button class="btn btn-ghost btn-sm" onclick="window._gitPushAll()" id="git-push-btn">↑ Push</button>
            <button class="btn btn-ghost btn-sm" onclick="window._testGitConnection()" id="git-test-btn">⚡ Test Connection</button>
          </div>
          <!-- Error / status display — selectable text + copy button -->
          <div id="git-status-box" style="display:none;margin-top:0.5rem;padding:0.5rem 0.65rem;
               border-radius:var(--radius);background:var(--surface2);border:1px solid var(--border);
               font-size:0.72rem;line-height:1.5;position:relative">
            <span id="git-cred-status" style="user-select:text;cursor:text;white-space:pre-wrap;word-break:break-all"></span>
            <button onclick="window._copyGitStatus()" title="Copy to clipboard"
              style="position:absolute;top:0.3rem;right:0.3rem;background:none;border:none;
                     cursor:pointer;font-size:0.75rem;color:var(--text2);padding:2px 5px;
                     border-radius:3px;opacity:0.7" onmouseenter="this.style.opacity='1'"
              onmouseleave="this.style.opacity='0.7'">📋</button>
          </div>
          <div style="font-size:0.62rem;color:var(--muted);margin-top:0.4rem">
            Setup Git — init &amp; connect · Pull — sync from remote · Push — force-upload all files (replaces remote history) · Test — verify connection
          </div>
        </div>

        <!-- Setup Guide (collapsible) -->
        <div style="margin-top:1.25rem">
          <button class="btn btn-ghost btn-sm" onclick="window._toggleGitHelp()" id="git-help-btn"
            style="font-size:0.72rem;color:var(--text2)">
            ℹ How to set up git — step-by-step guide ▾
          </button>
          <div id="git-help-panel" style="display:none;margin-top:0.75rem;padding:1rem;
               border-radius:var(--radius);background:var(--surface2);border:1px solid var(--border);
               font-size:0.72rem;line-height:1.7;color:var(--text2)">
            <div style="font-weight:700;color:var(--text);margin-bottom:0.4rem">Step 1 — Install Git</div>
            <div>• <strong>Windows:</strong> Download <a href="https://gitforwindows.org" target="_blank" style="color:var(--accent)">Git for Windows</a> and run the installer with defaults. Tick "Git Bash" to get a terminal.</div>
            <div>• <strong>Mac:</strong> Run <code>xcode-select --install</code> in Terminal, or <code>brew install git</code> with <a href="https://brew.sh" target="_blank" style="color:var(--accent)">Homebrew</a>.</div>
            <div>• <strong>Linux:</strong> <code>sudo apt install git</code></div>
            <div style="margin-top:0.75rem;font-weight:700;color:var(--text);margin-bottom:0.4rem">Step 2 — GitHub account &amp; repo</div>
            <div>Sign up at <a href="https://github.com" target="_blank" style="color:var(--accent)">github.com</a>. Create a repo manually and paste its URL above, or use <strong>+ Create on GitHub</strong> (requires Browser Login first).</div>
            <div style="margin-top:0.75rem;font-weight:700;color:var(--text);margin-bottom:0.4rem">Option A — Browser Login (recommended)</div>
            <div>1. github.com → avatar → Settings → Developer settings → OAuth Apps → <strong>New OAuth App</strong></div>
            <div>2. Any name, Homepage URL: <code>http://localhost</code>, Callback URL: <code>http://localhost</code> → Register</div>
            <div>3. In the OAuth App page, scroll down → enable <strong>Device Flow</strong> → Update application</div>
            <div>4. Copy the <strong>Client ID</strong> (NOT the secret) → paste above → click <strong>Login with GitHub</strong></div>
            <div style="margin-top:0.75rem;font-weight:700;color:var(--text);margin-bottom:0.4rem">Option B — PAT Token</div>
            <div>1. github.com → avatar → Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token</div>
            <div>2. Set a name, expiry, select <strong>repo</strong> scope → Generate. Copy the token (starts <code>ghp_</code>).</div>
            <div>3. Switch to PAT Token tab, fill username + email + token → Save &amp; Setup Git</div>
            <div style="margin-top:0.75rem;font-weight:700;color:var(--text);margin-bottom:0.4rem">Troubleshooting</div>
            <div>• <strong>400 on Login:</strong> Device Flow not enabled on your OAuth App — go to the app settings and check "Enable Device Flow".</div>
            <div>• <strong>Push 403:</strong> Token missing <code>repo</code> scope or expired — regenerate it.</div>
            <div>• <strong>Remote not found:</strong> Set GitHub Repo URL above and click ⚙ Setup Git.</div>
            <div>• <strong>No git repo error:</strong> Enter the repo URL, tick "Initial commit", click ⚙ Setup Git.</div>
          </div>
        </div>
      </div>
    </div>
  `;

  window._browseProjCodeDir = async () => {
    if (window.electronAPI) {
      const dir = await window.electronAPI.openDirectory();
      if (dir) document.getElementById('proj-codedir').value = dir;
    }
  };

  window._fetchBranches = async () => {
    const btn  = document.getElementById('fetch-branches-btn');
    const hint = document.getElementById('branches-hint');
    if (btn) { btn.disabled = true; btn.textContent = 'Fetching…'; }
    try {
      const data = await api.gitBranches(proj.name);
      const all = [...new Set([...(data.remote_branches || []), ...(data.local_branches || [])])].filter(Boolean);
      const dl = document.getElementById('branch-suggestions');
      if (dl) dl.innerHTML = all.map(b => `<option value="${b}">`).join('');
      if (hint) {
        if (all.length) {
          hint.innerHTML = `Branches: ` + all.map(b =>
            `<span onclick="document.getElementById('git-branch').value='${b}'"
              style="cursor:pointer;text-decoration:underline;margin-right:8px;color:var(--text2)">${b}</span>`
          ).join('');
          hint.style.color = 'var(--text2)';
        } else {
          hint.textContent = data.is_git_repo
            ? 'No remote branches found — check Repo URL and credentials, then click ⚙ Setup Git.'
            : 'Not a git repo — enter the Repo URL and click ⚙ Setup Git first.';
          hint.style.color = 'var(--muted)';
        }
      }
      // Auto-fill branch input if empty and remote has a default
      const bi = document.getElementById('git-branch');
      if (bi && !bi.value && data.default_branch) bi.value = data.default_branch;
    } catch (e) {
      if (hint) { hint.textContent = `Could not fetch branches: ${e.message}`; hint.style.color = 'var(--red)'; }
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '↺ Fetch remote'; }
    }
  };

  window._saveProjSettings = async () => {
    const updates = {
      description:      document.getElementById('proj-description').value,
      default_provider: document.getElementById('proj-provider').value,
      code_dir:         document.getElementById('proj-codedir').value,
      auto_commit_push: document.getElementById('proj-autocommit').checked,
    };
    const statusEl = document.getElementById('proj-save-status');
    try {
      await api.updateProjectConfig(proj.name, updates);
      setState({ currentProject: { ...state.currentProject, ...updates } });
      if (statusEl) { statusEl.textContent = '✓ Project config saved'; statusEl.style.color = 'var(--green)'; }
      toast('Project config saved', 'success');
    } catch (e) {
      if (statusEl) { statusEl.textContent = `✕ ${e.message}`; statusEl.style.color = 'var(--red)'; }
      toast(`Save failed: ${e.message}`, 'error');
    }
  };

  // Load git status
  api.gitStatus(proj.name).then(s => {
    const el = document.getElementById('git-status-line');
    if (!el) return;
    if (!s.is_git_repo) {
      el.textContent = '⚠ Not a git repo — fill in credentials and click "Save & Setup Git"';
      el.style.color = 'var(--accent)';
    } else {
      const cred = s.has_credentials ? '✓ credentials stored' : '⚠ no credentials';
      el.innerHTML = `✓ Git repo on branch <strong>${s.branch || 'main'}</strong> · ${s.changed_count} changed file(s) · ${cred}`;
      el.style.color = s.has_credentials ? 'var(--green)' : 'var(--accent)';
      if (s.git_username) {
        const u = document.getElementById('git-username');
        if (u && !u.value) u.value = s.git_username;
      }
    }
  }).catch(() => {});

  // ── Git status helpers ───────────────────────────────────────────────────────
  function _setGitStatus(text, color) {
    const box = document.getElementById('git-status-box');
    const el  = document.getElementById('git-cred-status');
    if (!el || !box) return;
    el.textContent  = text;
    el.style.color  = color || 'var(--text)';
    box.style.display = text ? '' : 'none';
    box.style.borderColor = color === 'var(--red)' ? 'rgba(255,80,80,0.3)'
                          : color === 'var(--green)' ? 'rgba(80,200,120,0.3)'
                          : 'var(--border)';
  }

  window._copyGitStatus = () => {
    const el = document.getElementById('git-cred-status');
    if (!el) return;
    navigator.clipboard.writeText(el.textContent).then(() => {
      const btn = el.parentElement?.querySelector('button');
      if (btn) { btn.textContent = '✓'; setTimeout(() => { btn.textContent = '📋'; }, 1500); }
    }).catch(() => {});
  };

  window._toggleGitToken = () => {
    const inp = document.getElementById('git-token');
    if (inp) inp.type = inp.type === 'password' ? 'text' : 'password';
  };

  window._gitTab = (method) => {
    const isOauth = method === 'oauth';
    const tabO = document.getElementById('git-tab-oauth');
    const tabP = document.getElementById('git-tab-pat');
    const panO = document.getElementById('git-panel-oauth');
    const panP = document.getElementById('git-panel-pat');
    if (tabO) { tabO.style.borderBottomColor = isOauth ? 'var(--accent)' : 'transparent'; tabO.style.color = isOauth ? 'var(--text)' : 'var(--text2)'; tabO.style.fontWeight = isOauth ? '600' : 'normal'; }
    if (tabP) { tabP.style.borderBottomColor = isOauth ? 'transparent' : 'var(--accent)'; tabP.style.color = isOauth ? 'var(--text2)' : 'var(--text)'; tabP.style.fontWeight = isOauth ? 'normal' : '600'; }
    if (panO) panO.style.display = isOauth ? '' : 'none';
    if (panP) panP.style.display = isOauth ? 'none' : '';
  };

  let _devicePollTimer = null;

  window._startDeviceFlow = async () => {
    const clientId  = document.getElementById('git-client-id')?.value.trim();
    if (!clientId) { toast('Enter your GitHub App Client ID first', 'error'); return; }
    // Persist client_id immediately so it survives page reloads
    api.updateProjectConfig(proj.name, { github_client_id: clientId }).catch(() => {});
    const btn       = document.getElementById('git-oauth-btn');
    const statusEl  = document.getElementById('git-oauth-status');
    const deviceBox = document.getElementById('git-device-box');
    if (btn) { btn.disabled = true; btn.textContent = 'Starting…'; }
    if (statusEl) { statusEl.textContent = ''; }
    if (_devicePollTimer) { clearTimeout(_devicePollTimer); _devicePollTimer = null; }

    const doPoll = (deviceCode, interval, expiresAt) => {
      _devicePollTimer = setTimeout(async () => {
        const devStatus = document.getElementById('git-device-status');
        const sEl       = document.getElementById('git-oauth-status');
        if (Date.now() > expiresAt) {
          if (devStatus) { devStatus.textContent = 'Code expired — click Login again.'; devStatus.style.color = 'var(--accent)'; }
          return;
        }
        try {
          const poll = await api.gitOauthDevicePoll({ client_id: clientId, device_code: deviceCode, project_name: proj.name });
          if (poll.status === 'authorized') {
            if (devStatus) { devStatus.textContent = `✓ Authorized as @${poll.username}`; devStatus.style.color = 'var(--green)'; }
            if (sEl) { sEl.textContent = `✓ Signed in as @${poll.username}`; sEl.style.color = 'var(--green)'; }
            toast(`GitHub connected as @${poll.username}`, 'success');
            // Connect the remote with the new token
            window._setupGit?.();
            return;
          }
          let next = interval;
          if (poll.status === 'slow_down') next = (poll.interval || 10) * 1000;
          if (poll.status === 'denied')  { if (devStatus) { devStatus.textContent = 'Access denied.'; devStatus.style.color = 'var(--red)'; } return; }
          if (poll.status === 'expired') { if (devStatus) { devStatus.textContent = 'Code expired — click Login again.'; devStatus.style.color = 'var(--accent)'; } return; }
          doPoll(deviceCode, next, expiresAt);
        } catch { doPoll(deviceCode, interval, expiresAt); }
      }, interval);
    };

    try {
      const data = await api.gitOauthDeviceStart({ client_id: clientId });
      if (deviceBox) deviceBox.style.display = '';
      const urlEl     = document.getElementById('git-verify-url');
      const codeEl    = document.getElementById('git-user-code');
      const devStatus = document.getElementById('git-device-status');
      if (urlEl) { urlEl.href = data.verification_uri; urlEl.textContent = data.verification_uri; }
      if (codeEl) codeEl.textContent = data.user_code || '—';
      if (devStatus) { devStatus.textContent = 'Waiting for you to authorize in browser…'; devStatus.style.color = 'var(--muted)'; }
      if (data.verification_uri) window.open(data.verification_uri, '_blank');
      if (btn) { btn.disabled = false; btn.textContent = 'Restart'; }
      doPoll(data.device_code, (data.interval || 5) * 1000, Date.now() + (data.expires_in || 900) * 1000);
    } catch (e) {
      if (btn) { btn.disabled = false; btn.textContent = 'Login with GitHub'; }
      if (statusEl) { statusEl.textContent = `Error: ${e.message}`; statusEl.style.color = 'var(--red)'; }
      toast(`OAuth error: ${e.message}`, 'error');
    }
  };

  window._toggleGitHelp = () => {
    const panel   = document.getElementById('git-help-panel');
    const helpBtn = document.getElementById('git-help-btn');
    if (!panel) return;
    const nowOpen = panel.style.display !== 'none';
    panel.style.display = nowOpen ? 'none' : '';
    if (helpBtn) helpBtn.textContent = helpBtn.textContent.replace(nowOpen ? '▴' : '▾', nowOpen ? '▾' : '▴');
  };

  window._saveGitCredentials = async () => {
    const username = document.getElementById('git-username').value.trim();
    const email    = document.getElementById('git-email').value.trim();
    const token    = document.getElementById('git-token').value.trim();
    if (!token) { toast('Enter a Personal Access Token', 'error'); return; }
    _setGitStatus('Setting up…', 'var(--muted)');
    try {
      const result = await api.gitSetup(proj.name, {
        git_username:  username,
        git_email:     email,
        git_token:     token,
        github_repo:   document.getElementById('git-repo-url')?.value.trim() || '',
        git_branch:    document.getElementById('git-branch')?.value.trim() || '',
        init_if_needed: true,
        initial_commit: true,
      });
      _setGitStatus('✓ ' + result.actions.join('\n'), 'var(--green)');
      toast('Git configured', 'success');
      const s = await api.gitStatus(proj.name);
      const el = document.getElementById('git-status-line');
      if (el && s.is_git_repo) {
        el.innerHTML = `✓ Git repo on branch <strong>${s.branch || 'main'}</strong> · credentials stored`;
        el.style.color = 'var(--green)';
      }
      window._fetchBranches?.();
    } catch (e) {
      _setGitStatus(`✕ ${e.message}`, 'var(--red)');
      toast(`Git setup failed: ${e.message}`, 'error');
    }
  };

  window._setupGit = async () => {
    const repoUrl  = document.getElementById('git-repo-url')?.value.trim() || '';
    const branch   = document.getElementById('git-branch')?.value.trim() || '';
    const clientId = document.getElementById('git-client-id')?.value.trim() || '';
    _setGitStatus('Setting up…', 'var(--muted)');
    try {
      const result = await api.gitSetup(proj.name, {
        github_repo:      repoUrl,
        git_branch:       branch,
        github_client_id: clientId,
        init_if_needed:   true,
        initial_commit:   true,
      });
      _setGitStatus('✓ ' + result.actions.join('\n'), 'var(--green)');
      toast('Git configured', 'success');
      api.gitStatus(proj.name).then(s => {
        const el = document.getElementById('git-status-line');
        if (!el) return;
        if (s.is_git_repo) {
          const cred = s.has_credentials ? '✓ credentials stored' : '⚠ no credentials';
          el.innerHTML = `✓ Git repo · branch <strong>${s.branch || 'main'}</strong> · ${s.changed_count} changed · ${cred}`;
          el.style.color = s.has_credentials ? 'var(--green)' : 'var(--accent)';
        }
      }).catch(() => {});
      window._fetchBranches?.();
    } catch (e) {
      _setGitStatus(`✕ ${e.message}`, 'var(--red)');
      toast(`Setup failed: ${e.message}`, 'error');
    }
  };

  window._testGitConnection = async () => {
    const btn = document.getElementById('git-test-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Testing…'; }
    _setGitStatus('', '');
    try {
      const result = await api.gitTestConnection(proj.name);
      if (result.ok) {
        const branches = result.branches?.length ? result.branches.join(', ') : '(no remote branches yet)';
        _setGitStatus(`✓ Connected\nBranches: ${branches}`, 'var(--green)');
        toast('Git connection OK', 'success');
      } else {
        _setGitStatus(`✕ ${result.error}`, 'var(--red)');
        toast(`Connection failed: ${result.error}`, 'error');
      }
    } catch (e) {
      _setGitStatus(`✕ ${e.message}`, 'var(--red)');
      toast(`Test error: ${e.message}`, 'error');
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '⚡ Test Connection'; }
    }
  };

  window._gitPull = async () => {
    const btn = document.getElementById('git-pull-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Pulling…'; }
    _setGitStatus('', '');
    try {
      const result = await api.gitPull(proj.name);
      if (result.ok) {
        _setGitStatus(`↓ ${result.message}`, 'var(--green)');
        toast(result.message, 'success');
      } else {
        _setGitStatus(`✕ ${result.error}`, 'var(--red)');
        toast(`Pull failed: ${result.error}`, 'error');
      }
    } catch (e) {
      _setGitStatus(`✕ ${e.message}`, 'var(--red)');
      toast(`Pull error: ${e.message}`, 'error');
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '↓ Pull'; }
    }
  };

  window._gitPushAll = async () => {
    const btn = document.getElementById('git-push-btn');
    if (btn) { btn.disabled = true; btn.textContent = 'Pushing…'; }
    _setGitStatus('Pushing — rewriting history to remove any secrets…', 'var(--muted)');
    try {
      const result = await api.gitPushAll(proj.name);
      if (result.ok) {
        const parts = [`↑ Pushed to remote (clean history)`];
        if (result.staged_count) parts.push(`${result.staged_count} file(s) committed`);
        _setGitStatus(parts.join('\n'), 'var(--green)');
        toast(parts[0], 'success');
      } else {
        const err = result.error || result.push_error || 'Push failed';
        _setGitStatus(`✕ ${err}`, 'var(--red)');
        toast(`Push failed: ${err}`, 'error');
      }
    } catch (e) {
      _setGitStatus(`✕ ${e.message}`, 'var(--red)');
      toast(`Push error: ${e.message}`, 'error');
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = '↑ Push'; }
    }
  };

  window._showCreateRepo = (show = true) => {
    const form = document.getElementById('git-create-form');
    if (form) form.style.display = show ? '' : 'none';
    const btn = document.getElementById('git-create-btn');
    if (btn) btn.textContent = show ? '− Cancel' : '+ Create on GitHub';
  };

  window._createRepoOnGitHub = async () => {
    const repoName  = document.getElementById('new-repo-name')?.value.trim();
    const isPrivate = document.getElementById('new-repo-private')?.checked ?? true;
    const statusEl  = document.getElementById('git-create-status');
    if (!repoName) { toast('Enter a repository name', 'error'); return; }
    if (statusEl) { statusEl.textContent = 'Creating…'; statusEl.style.color = 'var(--muted)'; }
    try {
      const result = await api.gitOauthCreateRepo({
        project_name: proj.name,
        repo_name:    repoName,
        private:      isPrivate,
      });
      // Fill the URL field with the new repo URL
      const urlEl = document.getElementById('git-repo-url');
      if (urlEl) urlEl.value = result.clone_url;
      if (statusEl) { statusEl.textContent = `✓ Created: ${result.html_url}`; statusEl.style.color = 'var(--green)'; }
      toast(`Repo created: ${result.html_url}`, 'success');
      window._showCreateRepo(false);
      // Refresh status and branches
      window._fetchBranches?.();
      api.gitStatus(proj.name).then(s => {
        const el = document.getElementById('git-status-line');
        if (el && s.is_git_repo) { el.innerHTML = `✓ Git repo · credentials stored`; el.style.color = 'var(--green)'; }
      }).catch(() => {});
    } catch (e) {
      if (statusEl) { statusEl.textContent = `✕ ${e.message}`; statusEl.style.color = 'var(--red)'; }
      toast(`Create repo failed: ${e.message}`, 'error');
    }
  };
}

function _esc(s) {
  return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Updates ───────────────────────────────────────────────────────────────────

async function _renderUpdateSection(content) {
  const isAdmin = state.user?.is_admin || state.user?.role === 'admin';
  const currentVersion = state.ui_version || 'unknown';

  content.innerHTML = `
    <div style="max-width:580px">
      <div class="settings-section-title">Updates</div>
      <div class="settings-section-desc">Check for new versions of AgentDesk from your server's update manifest.</div>

      <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);
                  padding:1rem 1.25rem;margin-bottom:1.25rem">
        <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.25rem;text-transform:uppercase;letter-spacing:0.05em">Installed Version</div>
        <div style="font-size:1.3rem;font-weight:700;color:var(--text);font-family:monospace">${_esc(currentVersion)}</div>
      </div>

      <div style="display:flex;gap:0.75rem;align-items:center;margin-bottom:1rem">
        <button class="btn btn-primary" id="update-check-btn" onclick="window._checkForUpdates()">Check for Updates</button>
        <div id="update-check-status" style="font-size:0.68rem;color:var(--muted)"></div>
      </div>

      <div id="update-result"></div>

      ${isAdmin ? `
      <div style="margin-top:2rem;padding-top:1.5rem;border-top:1px solid var(--border)">
        <div style="font-size:0.78rem;font-weight:600;margin-bottom:0.5rem">Edit Update Manifest (Admin)</div>
        <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.75rem">
          Write to <code>workspace/_system/update.json</code> — all connected clients will see this when they check for updates.
        </div>
        <textarea id="update-manifest-editor" rows="12"
          style="width:100%;box-sizing:border-box;font-family:monospace;font-size:0.72rem;
                 background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);
                 color:var(--text);padding:0.65rem;resize:vertical"
          placeholder='{"version":"2.1.0","release_notes":"...","download":{"mac":"...","win":"...","linux":"..."}}'
        ></textarea>
        <div style="display:flex;gap:0.5rem;margin-top:0.5rem">
          <button class="btn btn-primary btn-sm" onclick="window._saveUpdateManifest()">Save Manifest</button>
          <button class="btn btn-ghost btn-sm" onclick="window._loadManifestIntoEditor()">↺ Reload from Server</button>
        </div>
        <div id="manifest-save-status" style="font-size:0.65rem;color:var(--muted);margin-top:0.35rem"></div>
      </div>` : ''}
    </div>
  `;

  // Load current manifest into editor if admin
  if (isAdmin) {
    window._loadManifestIntoEditor = async () => {
      const ed = document.getElementById('update-manifest-editor');
      if (!ed) return;
      try {
        const m = await api.system.updateManifest();
        ed.value = JSON.stringify(m, null, 2);
      } catch (e) {
        ed.value = '';
      }
    };
    window._loadManifestIntoEditor();

    window._saveUpdateManifest = async () => {
      const ed = document.getElementById('update-manifest-editor');
      const statusEl = document.getElementById('manifest-save-status');
      if (!ed) return;
      let body;
      try { body = JSON.parse(ed.value); } catch {
        if (statusEl) { statusEl.textContent = '✕ Invalid JSON'; statusEl.style.color = 'var(--red)'; }
        return;
      }
      try {
        await api.system.saveManifest(body);
        if (statusEl) { statusEl.textContent = '✓ Manifest saved'; statusEl.style.color = 'var(--green)'; }
      } catch (e) {
        if (statusEl) { statusEl.textContent = `✕ ${e.message}`; statusEl.style.color = 'var(--red)'; }
      }
    };
  }

  window._checkForUpdates = async () => {
    const btn = document.getElementById('update-check-btn');
    const statusEl = document.getElementById('update-check-status');
    const resultEl = document.getElementById('update-result');
    if (btn) { btn.disabled = true; btn.textContent = 'Checking…'; }
    if (statusEl) statusEl.textContent = '';
    if (resultEl) resultEl.innerHTML = '';

    try {
      const manifest = await api.system.updateManifest();

      if (!manifest || !manifest.version) {
        if (statusEl) { statusEl.textContent = 'No update manifest available on this server.'; }
        if (resultEl) resultEl.innerHTML = `
          <div style="font-size:0.72rem;color:var(--muted);padding:0.75rem;background:var(--surface2);
                      border:1px solid var(--border);border-radius:var(--radius)">
            No update information is available. Ask your administrator to publish an update manifest.
          </div>`;
        return;
      }

      const isNewer = manifest.version !== currentVersion && manifest.version > currentVersion;
      setState({ update_available: isNewer ? manifest : null });

      if (!isNewer) {
        if (statusEl) { statusEl.textContent = `✓ You are up to date (${manifest.version})`; statusEl.style.color = 'var(--green)'; }
        if (resultEl) resultEl.innerHTML = `
          <div style="font-size:0.72rem;color:var(--green);padding:0.75rem;background:rgba(34,197,94,.07);
                      border:1px solid rgba(34,197,94,.25);border-radius:var(--radius)">
            ✓ AgentDesk ${_esc(currentVersion)} is the latest version.
          </div>`;
        return;
      }

      // Update available
      const dl = manifest.download || {};
      const platform = navigator.platform?.toLowerCase() || '';
      const suggestedKey = platform.includes('win') ? 'win' : platform.includes('mac') || platform.includes('mac') ? 'mac' : 'linux';

      if (resultEl) resultEl.innerHTML = `
        <div style="padding:1rem;background:rgba(255,107,53,.07);border:1px solid rgba(255,107,53,.3);
                    border-radius:var(--radius)">
          <div style="font-size:0.85rem;font-weight:700;color:var(--accent);margin-bottom:0.3rem">
            Update available: ${_esc(manifest.version)}
          </div>
          ${manifest.release_notes ? `
          <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.85rem;white-space:pre-wrap">${_esc(manifest.release_notes)}</div>` : ''}
          <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
            ${dl.mac    ? `<button class="btn btn-primary btn-sm" onclick="window.open('${_esc(dl.mac)}','_blank')"   style="${suggestedKey==='mac'?'outline:2px solid var(--accent)':''}">↓ macOS</button>` : ''}
            ${dl.win    ? `<button class="btn btn-primary btn-sm" onclick="window.open('${_esc(dl.win)}','_blank')"   style="${suggestedKey==='win'?'outline:2px solid var(--accent)':''}">↓ Windows</button>` : ''}
            ${dl.linux  ? `<button class="btn btn-primary btn-sm" onclick="window.open('${_esc(dl.linux)}','_blank')" style="${suggestedKey==='linux'?'outline:2px solid var(--accent)':''}">↓ Linux</button>` : ''}
          </div>
          ${manifest.config?.default_models ? `
          <div style="margin-top:0.85rem;padding-top:0.75rem;border-top:1px solid var(--border)">
            <div style="font-size:0.68rem;color:var(--muted);margin-bottom:0.4rem">
              This update includes recommended model settings:
            </div>
            <button class="btn btn-ghost btn-sm" onclick="window._applyManifestConfig(${JSON.stringify(JSON.stringify(manifest.config))})">
              Apply Recommended Config
            </button>
          </div>` : ''}
        </div>
      `;

      window._applyManifestConfig = (configJson) => {
        try {
          const cfg = JSON.parse(configJson);
          if (cfg.default_models) {
            setState({ settings: { ...state.settings, default_models: { ...state.settings.default_models, ...cfg.default_models } } });
            import('../utils/toast.js').then(({ toast }) => toast('Model config applied', 'success'));
          }
        } catch { /* ignore */ }
      };

    } catch (e) {
      if (statusEl) { statusEl.textContent = `Error: ${e.message}`; statusEl.style.color = 'var(--red)'; }
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = 'Check for Updates'; }
    }
  };
}

// ── Billing ───────────────────────────────────────────────────────────────────

async function renderBilling(content) {
  const isAdmin = state.user?.is_admin || state.user?.role === 'admin';
  content.innerHTML = '<div style="color:var(--muted);font-size:0.72rem">Loading billing info…</div>';

  try {
    const b = await api.billingBalance();
    const role = b.role || 'free';
    const balance = b.balance_usd ?? 0;
    const freeLimit = b.free_tier_limit_usd;
    const freeUsed = b.free_tier_used_usd ?? 0;

    // Balance display
    let balanceHtml;
    if (role === 'admin') {
      balanceHtml = `<div style="font-size:1.5rem;font-weight:700;color:var(--accent)">Admin</div>
        <div style="font-size:0.65rem;color:var(--muted);margin-top:0.25rem">Admin accounts have unlimited access</div>`;
    } else if (role === 'free') {
      const pct = freeLimit ? Math.min(100, (freeUsed / freeLimit) * 100) : 0;
      balanceHtml = `
        <div style="font-size:1.2rem;font-weight:700;color:var(--text)">Free Tier</div>
        <div style="font-size:0.72rem;color:var(--text2);margin-top:0.2rem">$${freeUsed.toFixed(4)} used of $${freeLimit?.toFixed(2)} limit</div>
        <div style="margin-top:0.5rem;background:var(--surface2);border-radius:4px;height:6px;overflow:hidden">
          <div style="width:${pct}%;height:100%;background:${pct>90?'var(--red)':pct>70?'var(--accent)':'var(--green)'}"></div>
        </div>
        <div style="font-size:0.62rem;color:var(--muted);margin-top:0.25rem">
          Free models: ${(b.free_tier_models||[]).join(', ') || 'none'}
        </div>`;
    } else {
      balanceHtml = `
        <div style="font-size:1.5rem;font-weight:700;color:${balance>=1?'var(--green)':balance>=0.1?'var(--accent)':'var(--red)'}">
          $${balance.toFixed(4)}
        </div>
        <div style="font-size:0.65rem;color:var(--muted);margin-top:0.25rem">Available balance</div>`;
    }

    content.innerHTML = `
      <div style="max-width:580px">
        <div class="settings-section-title">Billing &amp; Balance</div>

        <!-- Balance card -->
        <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);
                    padding:1rem 1.25rem;margin-bottom:1.5rem">
          <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:0.05em">Current Balance</div>
          ${balanceHtml}
          ${!isAdmin ? `
          <div style="margin-top:1rem">
            <button onclick="window._billingAddPayment()"
              style="padding:0.45rem 1rem;background:var(--surface);border:1px solid var(--border);
                     border-radius:6px;color:var(--text2);font-size:0.75rem;cursor:pointer">
              + Add Payment (Coming Soon)
            </button>
          </div>` : ''}
        </div>

        ${!isAdmin ? `
        <!-- Apply coupon -->
        <div style="margin-bottom:1.5rem">
          <div style="font-size:0.78rem;font-weight:600;margin-bottom:0.6rem">Apply Coupon Code</div>
          <div style="display:flex;gap:0.5rem">
            <input id="billing-coupon" placeholder="Enter coupon code" style="flex:1;
              background:var(--bg);border:1px solid var(--border);border-radius:6px;
              color:var(--text);font-size:0.82rem;padding:0.45rem 0.65rem" />
            <button onclick="window._applyCoupon()"
              style="padding:0.45rem 1rem;background:var(--accent);border:none;border-radius:6px;
                     color:#fff;font-size:0.8rem;font-weight:600;cursor:pointer">Apply</button>
          </div>
          <div id="coupon-status" style="font-size:0.65rem;margin-top:0.35rem;color:var(--muted)"></div>
        </div>
        ` : `
        <!-- Admin note -->
        <div style="background:rgba(255,107,53,0.07);border:1px solid rgba(255,107,53,0.2);
                    border-radius:var(--radius);padding:0.75rem 1rem;margin-bottom:1.5rem;font-size:0.72rem;color:var(--text2)">
          💡 Manage API keys, pricing, coupons, and user credits in the
          <a href="#" onclick="window._nav('admin');return false" style="color:var(--accent)">Admin Panel</a>.
        </div>
        `}

        <!-- Transaction history -->
        <div>
          <div style="font-size:0.78rem;font-weight:600;margin-bottom:0.6rem">Transaction History</div>
          <div id="billing-history-body">
            <div style="color:var(--muted);font-size:0.72rem">Loading…</div>
          </div>
        </div>
      </div>
    `;

    window._billingAddPayment = async () => {
      try {
        const r = await api.billingAddPayment();
        toast(r.message, 'info');
      } catch (e) { toast(e.message, 'error'); }
    };

    window._applyCoupon = async () => {
      const code = document.getElementById('billing-coupon')?.value.trim();
      const statusEl = document.getElementById('coupon-status');
      if (!code) { if (statusEl) { statusEl.textContent = 'Enter a coupon code'; statusEl.style.color = 'var(--red)'; } return; }
      try {
        const r = await api.billingApplyCoupon(code);
        if (statusEl) { statusEl.textContent = `✓ ${r.message}`; statusEl.style.color = 'var(--green)'; }
        toast(r.message, 'success');
        document.getElementById('billing-coupon').value = '';
        window._updateBalance?.().catch(() => {});
        // Refresh billing section
        await renderBilling(content);
      } catch (e) {
        if (statusEl) { statusEl.textContent = `✕ ${e.message}`; statusEl.style.color = 'var(--red)'; }
        toast(e.message, 'error');
      }
    };

    // Load transaction history
    const histBody = document.getElementById('billing-history-body');
    try {
      const h = await api.billingHistory();
      const txs = (h.transactions || []).slice().reverse();
      if (!txs.length) {
        if (histBody) histBody.innerHTML = '<div style="color:var(--muted);font-size:0.72rem">No transactions yet.</div>';
      } else {
        if (histBody) histBody.innerHTML = `
          <table style="width:100%;border-collapse:collapse;font-size:0.72rem">
            <thead>
              <tr style="border-bottom:1px solid var(--border);color:var(--muted)">
                <th style="text-align:left;padding:0.3rem 0.4rem;font-weight:500">Date</th>
                <th style="text-align:left;padding:0.3rem 0.4rem;font-weight:500">Type</th>
                <th style="text-align:right;padding:0.3rem 0.4rem;font-weight:500">Amount</th>
                <th style="text-align:left;padding:0.3rem 0.4rem;font-weight:500">Description</th>
              </tr>
            </thead>
            <tbody>
              ${txs.map(tx => {
                const isCredit = tx.type?.includes('credit');
                const amt = tx.amount_usd || 0;
                const ts = tx.ts ? new Date(tx.ts).toLocaleDateString() : '';
                return `
                  <tr style="border-bottom:1px solid var(--border)">
                    <td style="padding:0.35rem 0.4rem;color:var(--muted)">${ts}</td>
                    <td style="padding:0.35rem 0.4rem">${tx.type || ''}</td>
                    <td style="padding:0.35rem 0.4rem;text-align:right;color:${isCredit?'var(--green)':'var(--text2)'}">
                      ${isCredit?'+':'−'}$${amt.toFixed(4)}
                    </td>
                    <td style="padding:0.35rem 0.4rem;color:var(--text2)">${tx.description||''}</td>
                  </tr>`;
              }).join('')}
            </tbody>
          </table>
        `;
      }
    } catch {
      if (histBody) histBody.innerHTML = '<div style="color:var(--muted);font-size:0.72rem">Could not load history.</div>';
    }

  } catch (e) {
    content.innerHTML = `<div style="color:var(--red);font-size:0.75rem">Could not load billing: ${e.message}</div>`;
  }
}


// ── API Keys ──────────────────────────────────────────────────────────────────

function renderApiKeys(content) {
  const isAdmin = state.user?.is_admin || state.user?.role === 'admin';

  // Admins: show note to use Admin Panel
  if (isAdmin) {
    content.innerHTML = `
      <div>
        <div class="settings-section-title">API Keys</div>
        <div class="settings-section-desc">As an admin, API keys are managed server-side in the Admin Panel.</div>
        <div style="background:rgba(255,107,53,0.07);border:1px solid rgba(255,107,53,0.2);
                    border-radius:var(--radius);padding:0.75rem 1rem;margin-top:0.75rem;font-size:0.75rem;color:var(--text2)">
          💡 Go to the <a href="#" onclick="window._nav('admin');return false" style="color:var(--accent)">Admin Panel → API Keys</a>
          to set server-side API keys for all users.
        </div>
      </div>
    `;
    return;
  }

  content.innerHTML = `
    <div>
      <div class="settings-section-title">API Keys</div>
      <div class="settings-section-desc">Keys are encrypted at rest with AES-256-GCM. They are never sent anywhere except the respective LLM API.</div>

      <div class="lock-banner">
        <span class="lock-icon">🔐</span>
        <div>
          <div style="font-weight:700;font-size:0.72rem;margin-bottom:0.15rem">Encrypted Storage</div>
          <div>All API keys are stored in an encrypted file on your local machine. Enter your master password to save changes.</div>
        </div>
      </div>

      <div class="api-key-grid">
        ${LLM_CONFIG.map(llm => `
          <div class="api-key-row">
            <div class="api-key-label">
              <div class="llm-color-dot" style="background:${llm.color}"></div>
              <span>${llm.label}</span>
            </div>
            <div class="key-input-wrap">
              <input
                class="key-input"
                type="password"
                id="key-${llm.id}"
                placeholder="${llm.placeholder}"
                value="${state.settings.api_keys?.[llm.id] || ''}"
                oninput="window._onKeyChange('${llm.id}', this.value)"
              />
              <span class="key-toggle" onclick="window._toggleKeyVisible('${llm.id}')">👁</span>
            </div>
            <div class="key-status ${state.settings.api_keys?.[llm.id] ? 'set' : ''}" id="kstatus-${llm.id}"></div>
          </div>
        `).join('')}
      </div>

      <div class="password-section">
        <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.75rem">
          Enter your master password to save. If this is your first time, this becomes your password.
        </div>
        <div style="display:flex;gap:0.75rem;align-items:center">
          <div class="key-input-wrap" style="flex:1">
            <input class="key-input" type="password" id="save-pwd" placeholder="Master password..." />
            <span class="key-toggle" onclick="window._togglePwdVisible()">👁</span>
          </div>
          <button class="btn btn-primary" onclick="window._saveKeys()">Save Encrypted</button>
        </div>
        <div id="save-status" style="font-size:0.68rem;margin-top:0.5rem;color:var(--muted)"></div>
      </div>
    </div>
  `;

  // Local draft of keys
  window._keyDraft = { ...(state.settings.api_keys || {}) };

  window._onKeyChange = (id, val) => {
    window._keyDraft[id] = val;
    const status = document.getElementById(`kstatus-${id}`);
    if (status) status.className = `key-status ${val ? 'set' : ''}`;
  };

  window._toggleKeyVisible = (id) => {
    const input = document.getElementById(`key-${id}`);
    if (input) input.type = input.type === 'password' ? 'text' : 'password';
  };

  window._togglePwdVisible = () => {
    const input = document.getElementById('save-pwd');
    if (input) input.type = input.type === 'password' ? 'text' : 'password';
  };

  window._saveKeys = async () => {
    const pwd = document.getElementById('save-pwd').value;
    if (!pwd) { toast('Enter your master password', 'error'); return; }

    const newSettings = {
      ...state.settings,
      api_keys: window._keyDraft,
    };

    const statusEl = document.getElementById('save-status');
    try {
      await invoke('save_settings', { settings: newSettings, password: pwd });
      setState({ settings: newSettings, masterPassword: pwd });
      if (statusEl) statusEl.textContent = '✓ Settings saved and encrypted';
      if (statusEl) statusEl.style.color = 'var(--green)';
      toast('API keys saved (encrypted)', 'success');

      // Export env file for the Python backend
      await exportEnvFile(newSettings.api_keys, newSettings.backend_url);
    } catch (e) {
      if (statusEl) statusEl.textContent = `✕ ${e}`;
      if (statusEl) statusEl.style.color = 'var(--red)';
      toast(`Save failed: ${e}`, 'error');
    }
  };
}

async function exportEnvFile(keys, backendUrl) {
  // Generate .env for the Python backend
  const envContent = `# Generated by AgentDesk — do not edit manually
ANTHROPIC_API_KEY=${keys.claude || ''}
OPENAI_API_KEY=${keys.openai || ''}
DEEPSEEK_API_KEY=${keys.deepseek || ''}
GEMINI_API_KEY=${keys.gemini || ''}
GROK_API_KEY=${keys.grok || ''}
BACKEND_URL=${backendUrl || 'http://localhost:8000'}
`;
  try {
    await invoke('write_linked_file', { path: '../backend/.env', content: envContent });
  } catch { /* backend may not exist */ }
}

// ── Workspace ────────────────────────────────────────────────────────────────

async function renderWorkspace(content) {
  const API = (state.settings?.backend_url || 'http://localhost:8000').replace(/\/$/, '');
  let configData = {};
  let projectsData = { projects: [], active: '' };

  try {
    const [cfgRes, projRes] = await Promise.all([
      fetch(`${API}/config/`),
      fetch(`${API}/projects/`),
    ]);
    configData = await cfgRes.json();
    projectsData = await projRes.json();
  } catch { /* backend may not be running */ }

  content.innerHTML = `
    <div>
      <div class="settings-section-title">Workspace Settings</div>
      <div class="settings-section-desc">Configure workspace directory and active project.</div>

      <div class="field-group" style="margin-top:1rem">
        <div class="field-label">Workspace Directory</div>
        <div style="display:flex;gap:8px">
          <input class="field-input" id="ws-dir" value="${configData.workspace_dir || ''}"
            placeholder="/path/to/workspace" style="flex:1" />
          <button class="btn btn-ghost" onclick="window._browseWorkspaceDir()">Browse</button>
        </div>
      </div>

      <div class="field-group">
        <div class="field-label">Active Project</div>
        <select class="field-select" id="ws-project" onchange="window._switchProject(this.value)">
          ${(projectsData.projects || []).map(p =>
            `<option value="${p.name}" ${p.name === projectsData.active ? 'selected' : ''}>${p.name}${p.active ? ' ← active' : ''}</option>`
          ).join('')}
        </select>
      </div>

      <div class="field-group">
        <div class="field-label">Code Directory</div>
        <input class="field-input" id="ws-codedir" value="${configData.code_dir || ''}"
          placeholder="/path/to/your/code" />
      </div>

      <div style="margin-top:1rem;display:flex;gap:8px">
        <button class="btn btn-primary" onclick="window._saveWorkspaceSettings()">Save</button>
        <button class="btn btn-ghost" onclick="window._newProject()">New Project...</button>
      </div>

      <div style="margin-top:2rem">
        <div class="field-label">Provider Availability</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
          ${Object.entries(configData.providers_available || {}).map(([p, ok]) =>
            `<span style="padding:4px 10px;border-radius:12px;font-size:12px;background:${ok ? 'var(--green)' : 'var(--surface)'};color:${ok ? '#000' : 'var(--muted)'}">${p} ${ok ? '✓' : '✗'}</span>`
          ).join('')}
        </div>
      </div>
    </div>
  `;

  window._browseWorkspaceDir = async () => {
    if (window.electronAPI) {
      const dir = await window.electronAPI.openDirectory();
      if (dir) document.getElementById('ws-dir').value = dir;
    }
  };

  window._switchProject = async (name) => {
    await fetch(`${API}/projects/switch/${name}`, { method: 'POST' });
    toast(`Switched to project: ${name}`, 'success');
  };

  window._saveWorkspaceSettings = () => {
    toast('Workspace settings saved (restart backend to apply directory changes)', 'info');
  };

  window._newProject = async () => {
    const name = prompt('New project name:');
    if (!name) return;
    const template = prompt('Template (blank, python_api, quant_notebook, ui_app):', 'blank');
    try {
      const res = await fetch(`${API}/projects/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, template: template || 'blank' }),
      });
      const data = await res.json();
      if (data.created) {
        toast(`Project created: ${name}`, 'success');
        renderWorkspace(content);
      } else {
        toast(data.detail || 'Failed to create project', 'error');
      }
    } catch (e) {
      toast(`Error: ${e.message}`, 'error');
    }
  };
}

// ── Models ────────────────────────────────────────────────────────────────────

function renderModels(content) {
  content.innerHTML = `
    <div>
      <div class="settings-section-title">Default Models</div>
      <div class="settings-section-desc">Select the default model for each LLM provider used in agent workflows.</div>

      <div style="display:flex;flex-direction:column;gap:0.75rem">
        ${LLM_CONFIG.map(llm => `
          <div style="display:grid;grid-template-columns:120px 1fr;gap:0.75rem;align-items:center">
            <div style="display:flex;align-items:center;gap:0.5rem;font-size:0.75rem">
              <div style="width:8px;height:8px;border-radius:50%;background:${llm.color}"></div>
              ${llm.label}
            </div>
            <select class="field-select" onchange="window._setModel('${llm.id}',this.value)">
              ${llm.models.map(m => `
                <option value="${m}" ${state.settings.default_models?.[llm.id]===m?'selected':''}>${m}</option>
              `).join('')}
            </select>
          </div>
        `).join('')}
      </div>

      <div style="margin-top:1.25rem">
        <button class="btn btn-primary" onclick="window._saveModels()">Save Model Settings</button>
      </div>
    </div>
  `;

  window._modelDraft = { ...(state.settings.default_models || {}) };

  window._setModel = (id, val) => { window._modelDraft[id] = val; };

  window._saveModels = async () => {
    const pwd = state.masterPassword;
    if (!pwd) { toast('Unlock settings first (enter master password in API Keys tab)', 'error'); return; }
    const newSettings = { ...state.settings, default_models: window._modelDraft };
    await invoke('save_settings', { settings: newSettings, password: pwd });
    setState({ settings: newSettings });
    toast('Model settings saved', 'success');
  };
}

// ── Backend ───────────────────────────────────────────────────────────────────

function renderBackend(content) {
  content.innerHTML = `
    <div>
      <div class="settings-section-title">Backend Connection</div>
      <div class="settings-section-desc">Configure the Python FastAPI backend URL. The backend handles LLM calls, vector store, and chat history.</div>

      <div class="field-group">
        <div class="field-label">Backend URL</div>
        <input class="field-input" id="backend-url" value="${state.settings.backend_url || 'http://localhost:8000'}" placeholder="http://localhost:8000" />
      </div>

      <div style="display:flex;gap:0.75rem;align-items:center;margin-top:1rem">
        <button class="btn btn-ghost" onclick="window._testBackend()">Test Connection</button>
        <button class="btn btn-primary" onclick="window._saveBackendUrl()">Save</button>
        <div id="backend-status" style="font-size:0.68rem;color:var(--muted)"></div>
      </div>

      <div style="margin-top:2rem">
        <div style="font-size:0.72rem;color:var(--text2);margin-bottom:0.75rem">Backend quick-start:</div>
        <pre style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:1rem;font-size:0.7rem;color:var(--green);line-height:1.7">cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000</pre>
      </div>
    </div>
  `;

  window._testBackend = async () => {
    const url = document.getElementById('backend-url').value;
    const statusEl = document.getElementById('backend-status');
    try {
      const r = await fetch(`${url}/health`);
      const data = await r.json();
      statusEl.textContent = `✓ Online — v${data.version}`;
      statusEl.style.color = 'var(--green)';
      setState({ backendOnline: true });
      const dot = document.getElementById('status-dot');
      if (dot) { dot.className = 'status-dot online'; }
    } catch {
      statusEl.textContent = '✕ Cannot connect';
      statusEl.style.color = 'var(--red)';
      setState({ backendOnline: false });
    }
  };

  window._saveBackendUrl = async () => {
    const url = document.getElementById('backend-url').value;
    const pwd = state.masterPassword;
    const newSettings = { ...state.settings, backend_url: url };
    if (pwd) {
      await invoke('save_settings', { settings: newSettings, password: pwd });
    }
    setState({ settings: newSettings });
    toast('Backend URL saved', 'success');
  };
}

// ── Security ──────────────────────────────────────────────────────────────────

function renderSecurity(content) {
  content.innerHTML = `
    <div>
      <div class="settings-section-title">Security</div>
      <div class="settings-section-desc">Manage your master password and encryption settings.</div>

      <div style="background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:1rem;margin-bottom:1.5rem">
        <div style="font-size:0.72rem;font-weight:700;margin-bottom:0.5rem">Encryption Details</div>
        <div style="font-size:0.68rem;color:var(--text2);line-height:1.8">
          <div>Algorithm: <span style="color:var(--blue)">AES-256-GCM</span></div>
          <div>Key derivation: <span style="color:var(--blue)">SHA-256 with per-file salt</span></div>
          <div>Storage: <span style="color:var(--blue)">Local encrypted file</span></div>
          <div>Keys never leave: <span style="color:var(--green)">Your machine</span></div>
        </div>
      </div>

      <div style="margin-bottom:1.5rem">
        <div style="font-size:0.78rem;font-weight:700;margin-bottom:0.75rem">Change Master Password</div>
        <div class="field-group">
          <div class="field-label">Current password</div>
          <input class="field-input" type="password" id="sec-current" placeholder="Current master password" />
        </div>
        <div class="field-group">
          <div class="field-label">New password</div>
          <input class="field-input" type="password" id="sec-new" placeholder="New master password" />
        </div>
        <div class="field-group">
          <div class="field-label">Confirm new password</div>
          <input class="field-input" type="password" id="sec-confirm" placeholder="Confirm new password" />
        </div>
        <button class="btn btn-primary" onclick="window._changePassword()">Change Password</button>
      </div>

      <div style="padding-top:1.5rem;border-top:1px solid var(--border)">
        <div style="font-size:0.78rem;font-weight:700;color:var(--red);margin-bottom:0.5rem">Danger Zone</div>
        <div style="font-size:0.68rem;color:var(--text2);margin-bottom:0.75rem">This will permanently delete all encrypted settings and API keys.</div>
        <button class="btn btn-danger" onclick="window._clearSettings()">Clear All Settings</button>
      </div>
    </div>
  `;

  window._changePassword = async () => {
    const current = document.getElementById('sec-current').value;
    const newPwd   = document.getElementById('sec-new').value;
    const confirm  = document.getElementById('sec-confirm').value;

    if (!current || !newPwd) { toast('Fill in all fields', 'error'); return; }
    if (newPwd !== confirm)  { toast('Passwords do not match', 'error'); return; }

    try {
      // Verify old password by loading
      const settings = await invoke('load_settings', { password: current });
      // Re-save with new password
      await invoke('save_settings', { settings, password: newPwd });
      setState({ masterPassword: newPwd });
      toast('Password changed', 'success');
    } catch (e) { toast(`Error: ${e}`, 'error'); }
  };

  window._clearSettings = async () => {
    if (!confirm('This will delete all API keys and settings. Are you sure?')) return;
    try {
      await invoke('save_settings', {
        settings: {
          api_keys: {},
          default_models: { claude: 'claude-sonnet-4-6', deepseek: 'deepseek-chat', gemini: 'gemini-1.5-flash', grok: 'grok-3', openai: 'gpt-4o' },
          ui: { theme: 'dark', font_size: 13, sidebar_width: 220 },
          backend_url: BACKEND_URL,
        },
        password: 'default',
      });
      toast('Settings cleared', 'info');
    } catch (e) { toast(`Error: ${e}`, 'error'); }
  };
}

// ── Agent Roles ───────────────────────────────────────────────────────────────

function _jwtIsAdmin() {
  try {
    const tok = localStorage.getItem('ad_token');
    if (!tok) return false;
    const b64 = tok.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
    const payload = JSON.parse(atob(b64));
    return payload.is_admin === true || payload.role === 'admin';
  } catch { return false; }
}

// Module-level provider cache for the roles edit form (populated on first load)
let _settingsProviders = [];

function _settingsProviderModels(providerId) {
  const p = _settingsProviders.find(x => x.id === providerId);
  return p?.models || [];
}

async function renderAgentRoles(content) {
  const isAdmin = _jwtIsAdmin();
  content.innerHTML = `<div style="color:var(--muted);font-size:0.72rem">Loading…</div>`;

  let roles = [], adminFlag = false, pipelines = [];
  try {
    const [rolesData, plData, provData] = await Promise.all([
      api.agentRoles.list('_global', true),   // show_deactivated=true so settings sees all
      api.agentRoles.pipelinesConfig().catch(() => ({ pipelines: [] })),
      api.agentRoles.providers().catch(() => ({ providers: [] })),
    ]);
    if (provData?.providers?.length) _settingsProviders = provData.providers;
    roles     = rolesData.roles || [];
    adminFlag = rolesData.is_admin || isAdmin;
    pipelines = plData.pipelines || [];
  } catch (e) {
    content.innerHTML = `<div style="color:var(--red);font-size:0.72rem">Error: ${_esc(e.message)}</div>`;
    return;
  }

  content.innerHTML = `
    <div>
      <!-- ── Roles section ── -->
      <div class="settings-section-title">Roles &amp; Pipelines</div>
      <div class="settings-section-desc">
        Manage reusable LLM personas and pipeline templates.
        Deactivated roles and pipelines are hidden from pickers.
        ${adminFlag ? 'As admin you can edit system prompts and manage activation.' : ''}
      </div>

      <div style="font-size:0.72rem;font-weight:700;margin:1rem 0 0.4rem;color:var(--text)">Agent Roles</div>

      ${adminFlag ? `
      <div style="margin-bottom:0.75rem">
        <button class="btn btn-primary btn-sm" onclick="window._rolesShowCreate()">+ New Role</button>
      </div>
      <div id="roles-create-form" style="display:none;margin-bottom:1rem;padding:0.75rem;
           background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius)">
        <div style="font-size:0.72rem;font-weight:600;margin-bottom:0.5rem">New Role</div>
        <div class="field-group"><div class="field-label">Name</div>
          <input class="field-input" id="nr-name" placeholder="e.g. Data Engineer" /></div>
        <div class="field-group"><div class="field-label">Description (shown to all users)</div>
          <input class="field-input" id="nr-desc" placeholder="Short description of what this role does" /></div>
        <div class="field-group"><div class="field-label">Provider</div>
          <select class="field-input" id="nr-provider">
            ${['claude','openai','deepseek','gemini','grok'].map(p => `<option value="${p}">${p}</option>`).join('')}
          </select></div>
        <div class="field-group"><div class="field-label">Model (blank = default)</div>
          <input class="field-input" id="nr-model" placeholder="" /></div>
        <div class="field-group"><div class="field-label">System Prompt</div>
          <textarea class="field-input" id="nr-prompt" rows="5"
            style="font-family:var(--font);font-size:0.72rem;resize:vertical"
            placeholder="You are a…"></textarea></div>
        <div style="display:flex;gap:0.5rem;margin-top:0.5rem">
          <button class="btn btn-primary btn-sm" onclick="window._rolesSaveCreate()">Create</button>
          <button class="btn btn-ghost btn-sm" onclick="window._rolesHideCreate()">Cancel</button>
        </div>
      </div>` : ''}

      <div id="roles-list">
        ${roles.length === 0
          ? '<div style="color:var(--muted);font-size:0.72rem;padding:1rem">No roles found.</div>'
          : roles.map(r => _renderRoleRow(r, adminFlag)).join('')}
      </div>

      <!-- ── Pipelines section ── -->
      <div style="font-size:0.72rem;font-weight:700;margin:1.5rem 0 0.4rem;color:var(--text)">Pipelines</div>
      <div style="font-size:0.67rem;color:var(--muted);margin-bottom:0.75rem">
        Activate pipelines to make them available in workflow pickers.
        A pipeline can only be activated when all its required roles are also activated.
      </div>

      <div id="pipelines-list">
        ${pipelines.length === 0
          ? '<div style="color:var(--muted);font-size:0.72rem;padding:0.5rem">No pipelines found.</div>'
          : `<table style="width:100%;border-collapse:collapse;font-size:0.68rem">
              <thead>
                <tr style="border-bottom:1px solid var(--border);color:var(--muted)">
                  <th style="text-align:left;padding:0.35rem 0.5rem;font-weight:600">Name</th>
                  <th style="text-align:left;padding:0.35rem 0.5rem;font-weight:600">Required Roles</th>
                  <th style="text-align:center;padding:0.35rem 0.5rem;font-weight:600;width:70px">Activated</th>
                  <th style="text-align:center;padding:0.35rem 0.5rem;font-weight:600;width:70px" title="Show in Use Case Run menu">Use Case</th>
                  <th style="text-align:center;padding:0.35rem 0.5rem;font-weight:600;width:55px" title="Show in Item Run menu">Item</th>
                </tr>
              </thead>
              <tbody>
                ${pipelines.map(pl => _renderPipelineRow(pl, adminFlag)).join('')}
              </tbody>
            </table>`}
      </div>
    </div>
  `;

  // ── Wire create form ──
  window._rolesShowCreate = () => {
    document.getElementById('roles-create-form').style.display = '';
  };
  window._rolesHideCreate = () => {
    document.getElementById('roles-create-form').style.display = 'none';
  };
  window._rolesSaveCreate = async () => {
    const name   = document.getElementById('nr-name')?.value.trim();
    const desc   = document.getElementById('nr-desc')?.value.trim() || '';
    const prov   = document.getElementById('nr-provider')?.value || 'claude';
    const model  = document.getElementById('nr-model')?.value.trim() || '';
    const prompt = document.getElementById('nr-prompt')?.value || '';
    if (!name) { toast('Name required', 'error'); return; }
    try {
      await api.agentRoles.create({ name, description: desc, provider: prov, model, system_prompt: prompt });
      toast(`Role "${name}" created`, 'success');
      renderAgentRoles(content);
    } catch (e) { toast('Create failed: ' + e.message, 'error'); }
  };

  // ── Wire role actions ──
  window._rolesDelete = async (id, name) => {
    if (!confirm(`Delete role "${name}"?`)) return;
    try {
      await api.agentRoles.delete(id);
      toast('Role deleted', 'success');
      renderAgentRoles(content);
    } catch (e) { toast('Delete failed: ' + e.message, 'error'); }
  };
  window._rolesToggleEdit = (id) => {
    const el = document.getElementById(`role-edit-${id}`);
    if (el) el.style.display = el.style.display === 'none' ? '' : 'none';
  };
  window._rolesSaveEdit = async (id) => {
    const desc    = document.getElementById(`re-desc-${id}`)?.value.trim() || '';
    const prov    = document.getElementById(`re-prov-${id}`)?.value || 'claude';
    const model   = document.getElementById(`re-model-${id}`)?.value || '';
    const prompt  = document.getElementById(`re-prompt-${id}`)?.value || '';
    const note    = document.getElementById(`re-note-${id}`)?.value.trim() || '';
    const tempRaw = document.getElementById(`re-temp-${id}`)?.value;
    const temperature = tempRaw != null ? parseFloat(tempRaw) : null;
    try {
      await api.agentRoles.patch(id, { description: desc, provider: prov, model, system_prompt: prompt, note, temperature });
      toast('Role saved — new version created', 'success');
      renderAgentRoles(content);
    } catch (e) { toast('Update failed: ' + e.message, 'error'); }
  };
  window._rolesResetToBase = async (id) => {
    if (!confirm('Reset this role to its saved base snapshot? Current changes will be lost.')) return;
    try {
      await api.agentRoles.resetToBase(id);
      toast('Role reset to base', 'success');
      renderAgentRoles(content);
    } catch (e) { toast('Reset failed: ' + e.message, 'error'); }
  };
  window._rolesProviderChange = (id) => {
    const prov   = document.getElementById(`re-prov-${id}`)?.value;
    const modelSel = document.getElementById(`re-model-${id}`);
    if (!prov || !modelSel) return;
    const models = _settingsProviderModels(prov);
    const currentVal = modelSel.value;
    // Re-populate options; keep current if it's in the new list
    modelSel.innerHTML = models.map(m =>
      `<option value="${_esc(m)}" ${m === currentVal ? 'selected' : ''}>${_esc(m)}</option>`
    ).join('') + (models.length === 0 ? '<option value="">— no preset models —</option>' : '');
    // If current model isn't in list, select first
    if (models.length && !models.includes(currentVal)) modelSel.value = models[0];
  };
  window._rolesShowVersions = async (id, name) => {
    const el = document.getElementById(`role-versions-${id}`);
    if (!el) return;
    if (el.style.display !== 'none') { el.style.display = 'none'; return; }
    el.innerHTML = '<div style="color:var(--muted);font-size:0.65rem;padding:0.5rem">Loading…</div>';
    el.style.display = '';
    try {
      const data = await api.agentRoles.versions(id);
      const vers = data.versions || [];
      if (!vers.length) { el.innerHTML = '<div style="color:var(--muted);font-size:0.65rem;padding:0.5rem">No version history.</div>'; return; }
      el.innerHTML = vers.map(v => `
        <div style="border-bottom:1px solid var(--border);padding:0.4rem 0;font-size:0.65rem">
          <div style="display:flex;align-items:center;gap:0.5rem">
            <span style="color:var(--muted)">${(v.changed_at||'').slice(0,16)}</span>
            <span style="color:var(--text2)">${_esc(v.changed_by||'?')}</span>
            ${v.note ? `<span style="color:var(--muted);font-style:italic">${_esc(v.note)}</span>` : ''}
            <button onclick="window._rolesRestore(${id},${v.id},'${_esc(name)}')"
              style="margin-left:auto;font-size:0.6rem;padding:0.1rem 0.4rem;background:var(--surface2);
                     border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                     color:var(--text2);font-family:var(--font)">Restore</button>
          </div>
          <div style="color:var(--muted);font-size:0.62rem;margin-top:0.2rem;
                      white-space:pre-wrap;max-height:60px;overflow:hidden;font-family:monospace">${_esc((v.system_prompt||'').slice(0,200))}</div>
        </div>`).join('');
    } catch (e) { el.innerHTML = `<div style="color:var(--red);font-size:0.65rem;padding:0.5rem">${_esc(e.message)}</div>`; }
  };
  window._rolesRestore = async (roleId, versionId, name) => {
    if (!confirm(`Restore role "${name}" to this version?`)) return;
    try {
      await api.agentRoles.restore(roleId, versionId);
      toast('Role restored', 'success');
      renderAgentRoles(content);
    } catch (e) { toast('Restore failed: ' + e.message, 'error'); }
  };

  // ── In-place toggle handlers — update the affected element only, no full re-render ──
  window._toggleRoleActivated = async (id, val) => {
    const card = document.getElementById(`role-card-${id}`);
    try {
      await api.agentRoles.patch(id, { activated: val });
      toast(val ? 'Role activated' : 'Role deactivated', 'success');
      if (card) card.style.opacity = val ? '1' : '0.55';
    } catch (e) {
      toast('Update failed: ' + e.message, 'error');
      // Revert checkbox to previous state
      const cb = card?.querySelector('input[type=checkbox]');
      if (cb) cb.checked = !val;
    }
  };

  window._togglePipelineActivated = async (name, val) => {
    const row = document.getElementById(`pl-row-${name.replace(/\W+/g, '_')}`);
    try {
      await api.agentRoles.patchPipeline(name, { activated: val });
      toast(val ? `Pipeline "${name}" activated` : `Pipeline "${name}" deactivated`, 'success');
      if (row) row.style.opacity = val ? '1' : '0.6';
      window._invalidatePipelineCache?.();
    } catch (e) {
      toast(e.message, 'error');
      // Revert checkbox
      const cb = row?.querySelector('td:nth-child(3) input[type=checkbox]');
      if (cb) cb.checked = !val;
    }
  };

  window._togglePipelineMode = async (name, field, val) => {
    // Browser already toggled the checkbox — just PATCH and handle errors
    const row = document.getElementById(`pl-row-${name.replace(/\W+/g, '_')}`);
    try {
      await api.agentRoles.patchPipeline(name, { [field]: val });
      const label = field === 'mode_use_case' ? 'Use Case' : 'Item';
      toast(`Pipeline "${name}" — ${label} mode ${val ? 'on' : 'off'}`, 'success');
      window._invalidatePipelineCache?.();
    } catch (e) {
      toast(e.message, 'error');
      // Revert the checkbox — col 4 = Use Case, col 5 = Item
      const colIdx = field === 'mode_use_case' ? 4 : 5;
      const cb = row?.querySelector(`td:nth-child(${colIdx}) input[type=checkbox]`);
      if (cb) cb.checked = !val;
    }
  };
}

function _renderRoleRow(r, isAdmin) {
  const PROVIDER_COLORS = { claude: '#e67e22', openai: '#27ae60', deepseek: '#2980b9', gemini: '#16a085', grok: '#8e44ad' };
  const col = PROVIDER_COLORS[r.provider] || '#888';
  const activated = r.activated !== false;
  const rowOpacity = activated ? '1' : '0.55';
  return `
    <div id="role-card-${r.id}" style="border:1px solid var(--border);border-radius:var(--radius);margin-bottom:0.5rem;
                background:var(--surface);opacity:${rowOpacity}">
      <div style="display:flex;align-items:center;gap:0.75rem;padding:0.6rem 0.75rem">
        <span style="font-size:0.75rem;font-weight:600;color:var(--text);flex:1">${_esc(r.name)}</span>
        <span style="font-size:0.6rem;color:#fff;background:${col};padding:0.1rem 0.45rem;
                     border-radius:8px;white-space:nowrap">${_esc(r.provider)}${r.model ? ' · '+_esc(r.model.split('-').slice(0,3).join('-')) : ''}</span>
        ${isAdmin ? `
          <label title="Activated — show this role in pickers"
            style="display:flex;align-items:center;gap:0.25rem;font-size:0.6rem;color:var(--muted);cursor:pointer;user-select:none">
            <input type="checkbox" ${activated ? 'checked' : ''}
              onchange="window._toggleRoleActivated(${r.id}, this.checked)"
              style="cursor:pointer" />
            On
          </label>
          <button onclick="window._rolesToggleEdit(${r.id})"
            style="font-size:0.6rem;padding:0.15rem 0.45rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font)">Edit</button>
          <button onclick="window._rolesShowVersions(${r.id},'${_esc(r.name)}')"
            style="font-size:0.6rem;padding:0.15rem 0.45rem;background:var(--surface2);
                   border:1px solid var(--border);border-radius:var(--radius);cursor:pointer;
                   color:var(--text2);font-family:var(--font)">History</button>
          <button onclick="window._rolesDelete(${r.id},'${_esc(r.name)}')"
            style="font-size:0.6rem;padding:0.15rem 0.45rem;background:none;
                   border:1px solid var(--red,#e74c3c);border-radius:var(--radius);cursor:pointer;
                   color:var(--red,#e74c3c);font-family:var(--font)">✕</button>` : ''}
      </div>
      <div style="padding:0 0.75rem 0.5rem;font-size:0.67rem;color:var(--muted)">${_esc(r.description)}</div>

      ${isAdmin ? `
      <!-- Edit form (hidden by default) -->
      <div id="role-edit-${r.id}" style="display:none;border-top:1px solid var(--border);
           padding:0.75rem;background:var(--surface2)">

        <!-- Form header: note + link to full editor -->
        <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.6rem;font-size:0.6rem;color:var(--muted)">
          <span>Each save creates a new version. Use History to restore older versions.</span>
          <a href="#" onclick="window._nav('prompts');return false"
            style="margin-left:auto;color:var(--accent);text-decoration:none;white-space:nowrap"
            title="Open full role editor in the Roles tab">Open in Roles editor →</a>
        </div>

        <div class="field-group">
          <div class="field-label" style="font-size:0.6rem">Description</div>
          <input class="field-input" id="re-desc-${r.id}" value="${_esc(r.description)}" /></div>

        <!-- Provider + Model row -->
        <div style="display:flex;gap:0.5rem">
          <div class="field-group" style="flex:1">
            <div class="field-label" style="font-size:0.6rem">Provider</div>
            <select class="field-input" id="re-prov-${r.id}"
              onchange="window._rolesProviderChange(${r.id})">
              ${(() => {
                const provs = _settingsProviders.length
                  ? _settingsProviders
                  : [{id:'claude',label:'Claude'},{id:'openai',label:'OpenAI'},{id:'deepseek',label:'DeepSeek'},{id:'gemini',label:'Gemini'},{id:'grok',label:'Grok'}];
                return provs.map(p =>
                  `<option value="${_esc(p.id)}" ${r.provider===p.id?'selected':''}>${_esc(p.label||p.id)}</option>`
                ).join('');
              })()}
            </select>
          </div>
          <div class="field-group" style="flex:1">
            <div class="field-label" style="font-size:0.6rem">Model</div>
            <select class="field-input" id="re-model-${r.id}">
              ${(() => {
                const models = _settingsProviderModels(r.provider);
                const cur = r.model || '';
                const opts = [...new Set([...(cur ? [cur] : []), ...models])];
                if (!opts.length) return `<option value="${_esc(cur)}">${_esc(cur) || '— default —'}</option>`;
                return opts.map(m => `<option value="${_esc(m)}" ${m===cur?'selected':''}>${_esc(m)}</option>`).join('');
              })()}
            </select>
          </div>
        </div>

        <!-- Temperature -->
        <div class="field-group">
          <div class="field-label" style="font-size:0.6rem">
            Temperature
            <span id="re-temp-val-${r.id}" style="margin-left:0.4rem;color:var(--accent);font-weight:600">
              ${r.temperature != null ? parseFloat(r.temperature).toFixed(2) : '0.30'}
            </span>
            <span style="color:var(--muted);font-weight:400;margin-left:0.4rem">(0 = precise · 1 = creative)</span>
          </div>
          <input type="range" id="re-temp-${r.id}" min="0" max="1" step="0.05"
            value="${r.temperature != null ? r.temperature : 0.3}"
            oninput="document.getElementById('re-temp-val-${r.id}').textContent=parseFloat(this.value).toFixed(2)"
            style="width:100%;accent-color:var(--accent)" />
        </div>

        <!-- System Prompt -->
        <div class="field-group">
          <div class="field-label" style="font-size:0.6rem">System Prompt</div>
          <textarea class="field-input" id="re-prompt-${r.id}" rows="6"
            style="font-family:monospace;font-size:0.68rem;resize:vertical">${_esc(r.system_prompt||'')}</textarea></div>

        <!-- Change note -->
        <div class="field-group">
          <div class="field-label" style="font-size:0.6rem">Change note (optional — recorded in version history)</div>
          <input class="field-input" id="re-note-${r.id}" placeholder="What changed and why?" /></div>

        <!-- Action buttons -->
        <div style="display:flex;gap:0.5rem;margin-top:0.25rem;align-items:center">
          <button class="btn btn-primary btn-sm" onclick="window._rolesSaveEdit(${r.id})">Save version</button>
          <button class="btn btn-ghost btn-sm" onclick="window._rolesToggleEdit(${r.id})">Cancel</button>
          ${r.has_snapshot ? `
          <button class="btn btn-ghost btn-sm" onclick="window._rolesResetToBase(${r.id})"
            style="margin-left:auto;color:var(--amber,#f59e0b);border-color:var(--amber,#f59e0b)"
            title="Restore role to the saved base snapshot">↩ Reset to base</button>` : ''}
        </div>
      </div>
      <!-- Version history panel -->
      <div id="role-versions-${r.id}" style="display:none;border-top:1px solid var(--border);
           padding:0.5rem 0.75rem;background:var(--bg);max-height:180px;overflow-y:auto"></div>
      ` : ''}
    </div>
  `;
}

function _renderPipelineRow(pl, isAdmin) {
  const activated   = pl.activated !== false;
  const eligible    = pl.eligible !== false;
  const missing     = pl.missing_roles || [];
  const modeUC      = pl.mode_use_case !== false;
  const modeItem    = pl.mode_item     !== false;

  const rolesHtml = (pl.required_roles || []).length === 0
    ? '<span style="color:var(--muted);font-style:italic">none</span>'
    : (pl.required_roles || []).map(r => `<span style="display:inline-block;background:var(--surface2);
        border:1px solid var(--border);border-radius:3px;padding:0.05rem 0.3rem;
        font-size:0.6rem;margin:0.05rem">${_esc(r)}</span>`).join(' ');

  let checkboxHtml;
  if (!isAdmin) {
    checkboxHtml = `<input type="checkbox" ${activated ? 'checked' : ''} disabled />`;
  } else if (!eligible && !activated) {
    const tip = missing.length ? `Activate roles first: ${missing.join(', ')}` : 'Required roles not activated';
    checkboxHtml = `<input type="checkbox" disabled title="${_esc(tip)}" />
      <span style="font-size:0.58rem;color:var(--amber,#f59e0b)" title="${_esc(tip)}">⚠</span>`;
  } else {
    checkboxHtml = `<input type="checkbox" ${activated ? 'checked' : ''}
      onchange="window._togglePipelineActivated('${_esc(pl.name)}', this.checked)" />`;
  }

  const _modeBox = (field, val) => isAdmin
    ? `<input type="checkbox" ${val ? 'checked' : ''}
         onchange="window._togglePipelineMode('${_esc(pl.name)}', '${field}', this.checked)" />`
    : `<input type="checkbox" ${val ? 'checked' : ''} disabled />`;

  return `
    <tr id="pl-row-${pl.name.replace(/\W+/g, '_')}" style="border-bottom:1px solid var(--border);opacity:${activated ? '1' : '0.6'}">
      <td style="padding:0.4rem 0.5rem;font-weight:600;color:var(--text)">${_esc(pl.name)}</td>
      <td style="padding:0.4rem 0.5rem;color:var(--muted)">${rolesHtml}</td>
      <td style="padding:0.4rem 0.5rem;text-align:center">
        <label style="display:inline-flex;align-items:center;gap:0.25rem;cursor:${isAdmin ? 'pointer' : 'default'}">
          ${checkboxHtml}
        </label>
      </td>
      <td style="padding:0.4rem 0.5rem;text-align:center">
        <label style="display:inline-flex;align-items:center;justify-content:center;cursor:${isAdmin ? 'pointer' : 'default'}">
          ${_modeBox('mode_use_case', modeUC)}
        </label>
      </td>
      <td style="padding:0.4rem 0.5rem;text-align:center">
        <label style="display:inline-flex;align-items:center;justify-content:center;cursor:${isAdmin ? 'pointer' : 'default'}">
          ${_modeBox('mode_item', modeItem)}
        </label>
      </td>
    </tr>
  `;
}
