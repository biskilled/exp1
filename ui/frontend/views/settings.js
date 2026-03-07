import { state, setState } from '../stores/state.js';
import { invoke } from '../utils/tauri.js';
import { api } from '../utils/api.js';
import { toast } from '../utils/toast.js';
import { BACKEND_URL } from '../utils/config.js';

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
          <div class="settings-nav-item" onclick="window._settingsSection('security')" id="snav-security">
            <span>🔐</span> Security
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
    security:  renderSecurity,
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

// ── API Keys ──────────────────────────────────────────────────────────────────

function renderApiKeys(content) {
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
