import { state } from '../stores/state.js';
import { api, getRecentProjects } from '../utils/api.js';
import { toast } from '../utils/toast.js';

export function renderHome(container) {
  container.className = 'view active';
  container.style.cssText = 'overflow-y:auto;padding:2rem;';

  const recent = getRecentProjects();
  const allProjects = state.projects || [];

  container.innerHTML = `
    <div style="max-width:800px;margin:0 auto">

      <!-- Header -->
      <div style="margin-bottom:2rem">
        <div style="font-family:var(--font-ui);font-size:1.8rem;font-weight:900;letter-spacing:-2px;color:var(--text)">
          ai<span style="color:var(--accent)">cli</span>
        </div>
        <div style="font-size:0.7rem;color:var(--muted);letter-spacing:2px;text-transform:uppercase;margin-top:0.25rem">
          Multi-LLM developer command centre
        </div>
      </div>

      <!-- Recent projects -->
      ${recent.length > 0 ? `
        <div style="margin-bottom:2rem">
          <div style="font-family:var(--font-ui);font-size:0.75rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--text2);margin-bottom:0.75rem">
            Recent
          </div>
          <div style="display:flex;flex-direction:column;gap:0.35rem">
            ${recent.slice(0, 5).map(name => {
              const p = allProjects.find(x => x.name === name);
              return `
                <div onclick="window._openProject('${name}')"
                  style="display:flex;align-items:center;gap:0.75rem;padding:0.6rem 0.85rem;
                    background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
                    cursor:pointer;transition:border-color 0.15s"
                  onmouseenter="this.style.borderColor='var(--accent)'"
                  onmouseleave="this.style.borderColor='var(--border)'">
                  <span style="color:var(--accent)">◫</span>
                  <span style="flex:1;font-size:0.82rem">${name}</span>
                  ${p?.description ? `<span style="font-size:0.65rem;color:var(--muted)">${p.description}</span>` : ''}
                  ${p?.default_provider ? `<span style="font-size:0.6rem;color:var(--text2);letter-spacing:1px;text-transform:uppercase">${p.default_provider}</span>` : ''}
                  <span style="color:var(--muted);font-size:0.7rem">→</span>
                </div>
              `;
            }).join('')}
          </div>
        </div>
      ` : ''}

      <!-- All projects -->
      <div>
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem">
          <div style="font-family:var(--font-ui);font-size:0.75rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--text2)">
            ${allProjects.length > 0 ? 'All Projects' : 'Get Started'}
          </div>
          <button class="btn btn-primary btn-sm" onclick="window._showNewProject()">+ New Project</button>
        </div>

        ${allProjects.length === 0 ? `
          <div class="empty-state" style="padding:3rem">
            <div class="empty-state-icon">◫</div>
            <p>No projects yet</p>
            <p style="font-size:0.7rem;color:var(--muted);margin-top:0.5rem">Create a project to organise your prompts, chats, and workflows.</p>
            <button class="btn btn-primary btn-sm" style="margin-top:1rem" onclick="window._showNewProject()">Create first project</button>
          </div>
        ` : `
          <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:0.75rem">
            ${allProjects.map(p => `
              <div onclick="window._openProject('${p.name}')"
                style="padding:1rem 1.1rem;background:var(--surface);border:1px solid var(--border);
                  border-radius:var(--radius-lg);cursor:pointer;transition:border-color 0.15s"
                onmouseenter="this.style.borderColor='var(--accent)'"
                onmouseleave="this.style.borderColor='var(--border)'">
                <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.3rem">
                  <span style="color:var(--accent)">◫</span>
                  <span style="font-size:0.85rem;font-weight:600">${p.name}</span>
                </div>
                <div style="font-size:0.68rem;color:var(--muted);margin-bottom:0.4rem">${p.description || 'No description'}</div>
                <div style="font-size:0.58rem;color:var(--text2);letter-spacing:1px;text-transform:uppercase">
                  ${p.default_provider || 'claude'}${p.active ? ' · <span style="color:var(--green)">active</span>' : ''}
                </div>
              </div>
            `).join('')}
          </div>
        `}
      </div>

    </div>
  `;

  _bindNewProjectModal();
}

// ── 4-step wizard ─────────────────────────────────────────────────────────────

function _bindNewProjectModal() {
  window._showNewProject = () => {
    const wizard = {
      step: 1,
      name: '', description: '', code_dir: '',
      template: 'blank', provider: 'claude',
      git: null,          // {method, token, username, email, repo} or null
      claude_cli: false,
      cursor: false,
    };

    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay open';
    document.body.appendChild(overlay);
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });

    function render() {
      const stepTitles = ['Basics', 'Git', 'IDE Support', 'Review'];
      const dots = stepTitles.map((t, i) => {
        const active = i + 1 === wizard.step;
        const done   = i + 1 < wizard.step;
        return `<span style="display:inline-flex;align-items:center;gap:0.3rem;font-size:0.7rem;
          color:${active ? 'var(--accent)' : done ? 'var(--green)' : 'var(--muted)'}">
          <span style="width:8px;height:8px;border-radius:50%;background:${active ? 'var(--accent)' : done ? 'var(--green)' : 'var(--border)'}"></span>
          ${t}
        </span>`;
      }).join('<span style="color:var(--border);margin:0 0.3rem">–</span>');

      const skipBtn = `<button class="btn btn-ghost btn-sm" style="position:absolute;top:1rem;right:1rem"
        onclick="window._wizardSkip()">Skip for now →</button>`;

      let body = '';
      if (wizard.step === 1) body = _step1Html(wizard);
      if (wizard.step === 2) body = _step2Html(wizard);
      if (wizard.step === 3) body = _step3Html(wizard);
      if (wizard.step === 4) body = _step4Html(wizard);

      overlay.innerHTML = `
        <div class="modal" style="min-width:480px;max-width:580px;position:relative">
          <div style="margin-bottom:1.2rem">
            <div style="font-size:0.65rem;color:var(--muted);margin-bottom:0.5rem">
              Step ${wizard.step} of 4
            </div>
            <div style="display:flex;align-items:center;gap:0.2rem;flex-wrap:wrap">${dots}</div>
          </div>
          ${wizard.step > 1 && wizard.step < 4 ? skipBtn : ''}
          ${body}
        </div>
      `;

      // Re-bind global helpers
      window._wizardNext = () => _wizardNext(wizard, overlay, render);
      window._wizardBack = () => { wizard.step--; render(); };
      window._wizardSkip = () => { wizard.step++; render(); };
      window._wizardCreate = () => _wizardCreate(wizard, overlay);
      window._pickCodeDir = async () => {
        const dir = await window.electronAPI?.openDirectory();
        if (dir) {
          const el = document.getElementById('np-code');
          if (el) { el.value = dir; wizard.code_dir = dir; }
          _updateStep3CodeDirState(wizard.code_dir);
        }
      };
      window._wizardGitTabSwitch = (tab) => {
        document.getElementById('git-oauth-tab').style.display = tab === 'oauth' ? '' : 'none';
        document.getElementById('git-pat-tab').style.display  = tab === 'pat'  ? '' : 'none';
        document.querySelectorAll('[data-git-tab]').forEach(b => {
          b.style.borderBottom = b.dataset.gitTab === tab ? '2px solid var(--accent)' : '2px solid transparent';
        });
      };
    }

    render();
  };
}

// ── Step 1: Basics ────────────────────────────────────────────────────────────

function _step1Html(wizard) {
  return `
    <div class="modal-title">New Project</div>
    <div class="modal-subtitle">A project contains prompts, chat history, and workflows.</div>

    <div class="field-group">
      <div class="field-label">Project name <span style="color:var(--red)">*</span></div>
      <input class="field-input" id="np-name" placeholder="my-project" autofocus
        value="${wizard.name}" oninput="window._wizard.name=this.value.replace(/\\s+/g,'-')" />
    </div>
    <div class="field-group">
      <div class="field-label">Description</div>
      <input class="field-input" id="np-desc" placeholder="What is this project for?"
        value="${wizard.description}" oninput="window._wizard.description=this.value" />
    </div>
    <div class="field-group">
      <div class="field-label">Code folder <span style="font-weight:400;color:var(--muted)">(optional)</span></div>
      <div style="display:flex;gap:0.5rem">
        <input class="field-input" id="np-code" placeholder="/path/to/your/code" style="flex:1"
          value="${wizard.code_dir}" oninput="window._wizard.code_dir=this.value" />
        <button class="btn btn-ghost btn-sm" onclick="window._pickCodeDir()">Browse…</button>
      </div>
    </div>
    <div class="field-group">
      <div class="field-label">Template</div>
      <select class="field-input" id="np-template" onchange="window._wizard.template=this.value">
        ${['blank','python_api','quant_notebook','ui_app'].map(t =>
          `<option value="${t}"${wizard.template===t?' selected':''}>${t}</option>`).join('')}
      </select>
    </div>
    <div class="field-group">
      <div class="field-label">Default provider</div>
      <select class="field-input" id="np-provider" onchange="window._wizard.provider=this.value">
        ${['claude','openai','deepseek','gemini','grok'].map(p =>
          `<option value="${p}"${wizard.provider===p?' selected':''}>${p.charAt(0).toUpperCase()+p.slice(1)}</option>`).join('')}
      </select>
    </div>

    <div class="modal-footer">
      <button class="btn btn-ghost" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
      <button class="btn btn-primary" onclick="window._wizardNext()">Next: Git →</button>
    </div>
  `;
}

// ── Step 2: Git ───────────────────────────────────────────────────────────────

function _step2Html(wizard) {
  return `
    <div class="modal-title">Git Setup</div>
    <div class="modal-subtitle">Connect a GitHub repository for auto-commit and push.</div>

    <div style="display:flex;border-bottom:1px solid var(--border);margin-bottom:1rem;gap:0">
      <button data-git-tab="oauth" onclick="window._wizardGitTabSwitch('oauth')"
        style="padding:0.5rem 1rem;background:none;border:none;border-bottom:2px solid var(--accent);
          color:var(--text);cursor:pointer;font-size:0.8rem">GitHub OAuth</button>
      <button data-git-tab="pat" onclick="window._wizardGitTabSwitch('pat')"
        style="padding:0.5rem 1rem;background:none;border:none;border-bottom:2px solid transparent;
          color:var(--text);cursor:pointer;font-size:0.8rem">Personal Token</button>
    </div>

    <div id="git-oauth-tab">
      <div style="font-size:0.78rem;color:var(--muted);margin-bottom:0.75rem">
        Login with GitHub to automatically configure push credentials.
      </div>
      <button class="btn btn-ghost btn-sm" onclick="window._wizardGitOAuth()">Login with GitHub</button>
      <div id="git-oauth-code" style="display:none;margin-top:0.75rem;padding:0.75rem;background:var(--bg);border-radius:var(--radius);font-size:0.8rem"></div>
    </div>

    <div id="git-pat-tab" style="display:none">
      <div class="field-group">
        <div class="field-label">GitHub username</div>
        <input class="field-input" id="git-username" placeholder="octocat"
          value="${wizard.git?.username||''}" oninput="window._wizardSetGit('username',this.value)" />
      </div>
      <div class="field-group">
        <div class="field-label">Email</div>
        <input class="field-input" id="git-email" placeholder="you@example.com"
          value="${wizard.git?.email||''}" oninput="window._wizardSetGit('email',this.value)" />
      </div>
      <div class="field-group">
        <div class="field-label">Personal Access Token</div>
        <input class="field-input" id="git-token" type="password" placeholder="ghp_..."
          value="${wizard.git?.token||''}" oninput="window._wizardSetGit('token',this.value)" />
      </div>
      <div class="field-group">
        <div class="field-label">Repository URL</div>
        <input class="field-input" id="git-repo" placeholder="https://github.com/you/repo"
          value="${wizard.git?.repo||''}" oninput="window._wizardSetGit('repo',this.value)" />
      </div>
    </div>

    <div class="modal-footer">
      <button class="btn btn-ghost" onclick="window._wizardBack()">← Back</button>
      <button class="btn btn-primary" onclick="window._wizardNext()">Next: IDE Support →</button>
    </div>
  `;
}

// ── Step 3: IDE Support ───────────────────────────────────────────────────────

function _step3Html(wizard) {
  const hasCodeDir = !!wizard.code_dir;
  const disabledStyle = hasCodeDir ? '' : 'opacity:0.45;pointer-events:none';
  const disabledNote = hasCodeDir ? '' :
    `<div style="font-size:0.68rem;color:var(--yellow);margin-top:0.5rem">
      ⚠ Set a Code folder in Step 1 to enable IDE integrations.
    </div>`;

  return `
    <div class="modal-title">AI IDE Support</div>
    <div class="modal-subtitle">Integrate aicli memory with your editor.</div>

    ${disabledNote}

    <div style="display:flex;flex-direction:column;gap:0.85rem;margin-top:0.75rem">
      <label style="display:flex;gap:0.75rem;align-items:flex-start;cursor:pointer;${disabledStyle}">
        <input type="checkbox" id="np-claude-cli" style="margin-top:3px"
          ${wizard.claude_cli ? 'checked' : ''}
          onchange="window._wizard.claude_cli=this.checked" />
        <div>
          <div style="font-size:0.82rem;font-weight:600">Claude CLI support</div>
          <div style="font-size:0.7rem;color:var(--muted);margin-top:0.2rem">
            Copies hooks to <code>${wizard.code_dir||'{code_dir}'}/.aicli/scripts/</code><br>
            Creates <code>.claude/settings.local.json</code><br>
            Enables: session logging + auto-commit after each response
          </div>
        </div>
      </label>

      <label style="display:flex;gap:0.75rem;align-items:flex-start;cursor:pointer;${disabledStyle}">
        <input type="checkbox" id="np-cursor" style="margin-top:3px"
          ${wizard.cursor ? 'checked' : ''}
          onchange="window._wizard.cursor=this.checked" />
        <div>
          <div style="font-size:0.82rem;font-weight:600">Cursor support</div>
          <div style="font-size:0.7rem;color:var(--muted);margin-top:0.2rem">
            Creates <code>${wizard.code_dir||'{code_dir}'}/.cursor/rules/aicli.mdrules</code><br>
            Injects project context into Cursor AI
          </div>
        </div>
      </label>
    </div>

    <div class="modal-footer" style="margin-top:1.5rem">
      <button class="btn btn-ghost" onclick="window._wizardBack()">← Back</button>
      <button class="btn btn-primary" onclick="window._wizardNext()">Next: Review →</button>
    </div>
  `;
}

// ── Step 4: Review & Create ───────────────────────────────────────────────────

function _step4Html(wizard) {
  const gitStatus = wizard.git?.token ? (wizard.git.method === 'oauth' ? 'OAuth configured' : 'Token saved') : 'Skipped';
  const ideStatus = [
    wizard.claude_cli ? 'Claude CLI ✓' : null,
    wizard.cursor ? 'Cursor ✓' : null,
  ].filter(Boolean).join(', ') || 'None';

  return `
    <div class="modal-title">Review & Create</div>

    <div style="background:var(--bg);border:1px solid var(--border);border-radius:var(--radius-lg);
      padding:1rem;margin-bottom:1.25rem;display:flex;flex-direction:column;gap:0.5rem">
      ${_reviewRow('Project', `<strong>${wizard.name||'(unnamed)'}</strong> <span style="color:var(--muted)">(template: ${wizard.template})</span>`)}
      ${_reviewRow('Code folder', wizard.code_dir || '<span style="color:var(--muted)">not set</span>')}
      ${_reviewRow('Provider', wizard.provider)}
      ${_reviewRow('Git', gitStatus)}
      ${_reviewRow('IDE support', ideStatus)}
    </div>

    ${!wizard.name ? `<div style="color:var(--red);font-size:0.75rem;margin-bottom:0.75rem">
      ⚠ Project name is required — go back to Step 1.
    </div>` : ''}

    <div class="modal-footer">
      <button class="btn btn-ghost" onclick="window._wizardBack()">← Back</button>
      <button class="btn btn-primary" onclick="window._wizardCreate()" ${!wizard.name?'disabled':''}>
        Create Project →
      </button>
    </div>
  `;
}

function _reviewRow(label, value) {
  return `<div style="display:flex;gap:0.75rem;font-size:0.78rem">
    <span style="color:var(--muted);width:90px;flex-shrink:0">${label}</span>
    <span>${value}</span>
  </div>`;
}

// ── Wizard helpers ────────────────────────────────────────────────────────────

function _wizardNext(wizard, overlay, render) {
  // Collect step-1 field values before advancing
  if (wizard.step === 1) {
    const name = (document.getElementById('np-name')?.value || '').trim().replace(/\s+/g, '-');
    if (!name) { toast('Project name is required', 'error'); return; }
    wizard.name = name;
    wizard.description = (document.getElementById('np-desc')?.value || '').trim();
    wizard.code_dir = (document.getElementById('np-code')?.value || '').trim();
    wizard.template  = document.getElementById('np-template')?.value || 'blank';
    wizard.provider  = document.getElementById('np-provider')?.value || 'claude';
  }
  if (wizard.step === 3) {
    wizard.claude_cli = document.getElementById('np-claude-cli')?.checked || false;
    wizard.cursor     = document.getElementById('np-cursor')?.checked || false;
  }
  wizard.step++;
  // Expose wizard on window so inline oninput handlers can update it
  window._wizard = wizard;
  render();
}

function _updateStep3CodeDirState(codeDir) {
  // Re-enable/disable checkboxes when code_dir is picked via Browse
  const hasDir = !!codeDir;
  ['np-claude-cli', 'np-cursor'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.closest('label').style.cssText += hasDir
      ? 'opacity:1;pointer-events:auto' : 'opacity:0.45;pointer-events:none';
  });
}

window._wizardSetGit = (key, val) => {
  if (!window._wizard.git) window._wizard.git = { method: 'pat' };
  window._wizard.git[key] = val;
};

window._wizardGitOAuth = async () => {
  const el = document.getElementById('git-oauth-code');
  if (!el) return;
  el.style.display = '';
  el.textContent = 'Starting OAuth flow…';
  try {
    const data = await api.gitOauthDeviceStart({ client_id: '' });
    el.innerHTML = `Open <strong>${data.verification_uri}</strong> and enter code: <strong>${data.user_code}</strong>`;
    // Poll for token
    const interval = setInterval(async () => {
      try {
        const poll = await api.gitOauthDevicePoll({ device_code: data.device_code, client_id: '' });
        if (poll.access_token) {
          clearInterval(interval);
          if (!window._wizard.git) window._wizard.git = {};
          window._wizard.git.token = poll.access_token;
          window._wizard.git.method = 'oauth';
          el.textContent = '✓ GitHub authenticated';
        }
      } catch {}
    }, 5000);
  } catch (e) {
    el.textContent = `Error: ${e.message}`;
  }
};

async function _wizardCreate(wizard, overlay) {
  if (!wizard.name) { toast('Project name is required', 'error'); return; }

  const btn = overlay.querySelector('.btn-primary');
  if (btn) { btn.disabled = true; btn.textContent = 'Creating…'; }

  try {
    // 1. Create project
    await api.createProject({
      name: wizard.name,
      template: wizard.template,
      code_dir: wizard.code_dir,
      description: wizard.description,
      default_provider: wizard.provider,
      claude_cli_support: wizard.claude_cli,
      cursor_support: wizard.cursor,
    });

    // 2. Git setup
    if (wizard.git?.token && wizard.git?.repo) {
      try {
        await api.gitSetup(wizard.name, {
          token: wizard.git.token,
          username: wizard.git.username || '',
          email: wizard.git.email || '',
          github_repo: wizard.git.repo,
          git_branch: 'main',
        });
      } catch (e) {
        toast(`Git setup warning: ${e.message}`, 'warning');
      }
    }

    // 3. Generate initial memory files
    try {
      const memResult = await api.generateMemory(wizard.name);
      if (memResult.generated?.length) {
        toast(`Memory files generated (${memResult.generated.length} files)`, 'success');
      }
    } catch {}

    toast(`Project "${wizard.name}" created`, 'success');
    overlay.remove();

    // 4. Refresh + open
    const data = await api.listProjects();
    const { setState } = await import('../stores/state.js');
    setState({ projects: data.projects || [] });
    window._openProject(wizard.name);
  } catch (e) {
    toast(`Error: ${e.message}`, 'error');
    if (btn) { btn.disabled = false; btn.textContent = 'Create Project →'; }
  }
}
