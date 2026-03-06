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

function _bindNewProjectModal() {
  window._showNewProject = () => {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay open';
    overlay.innerHTML = `
      <div class="modal" style="min-width:420px">
        <div class="modal-title">New Project</div>
        <div class="modal-subtitle">A project contains prompts, chat history, and workflow configs.</div>

        <div class="field-group">
          <div class="field-label">Project name <span style="color:var(--red)">*</span></div>
          <input class="field-input" id="np-name" placeholder="my-project" autofocus />
        </div>
        <div class="field-group">
          <div class="field-label">Description</div>
          <input class="field-input" id="np-desc" placeholder="What is this project for?" />
        </div>
        <div class="field-group">
          <div class="field-label">Code folder <span style="font-weight:400;color:var(--muted)">(optional — separate path for your code)</span></div>
          <div style="display:flex;gap:0.5rem">
            <input class="field-input" id="np-code" placeholder="/path/to/your/code" style="flex:1" />
            <button class="btn btn-ghost btn-sm" onclick="window._pickCodeDir()">Browse…</button>
          </div>
        </div>
        <div class="field-group">
          <div class="field-label">Template</div>
          <select class="field-input" id="np-template">
            <option value="blank">blank</option>
            <option value="python_api">python_api</option>
            <option value="quant_notebook">quant_notebook</option>
            <option value="ui_app">ui_app</option>
          </select>
        </div>
        <div class="field-group">
          <div class="field-label">Default provider</div>
          <select class="field-input" id="np-provider">
            <option value="claude">Claude</option>
            <option value="openai">OpenAI</option>
            <option value="deepseek">DeepSeek</option>
            <option value="gemini">Gemini</option>
            <option value="grok">Grok</option>
          </select>
        </div>

        <div class="modal-footer">
          <button class="btn btn-ghost" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
          <button class="btn btn-primary" onclick="window._createProject()">Create Project</button>
        </div>
      </div>
    `;
    document.body.appendChild(overlay);
    overlay.addEventListener('click', e => { if (e.target === overlay) overlay.remove(); });

    window._pickCodeDir = async () => {
      const dir = await window.electronAPI?.openDirectory();
      if (dir) document.getElementById('np-code').value = dir;
    };

    window._createProject = async () => {
      const name = document.getElementById('np-name').value.trim().replace(/\s+/g, '-');
      const desc = document.getElementById('np-desc').value.trim();
      const code = document.getElementById('np-code').value.trim();
      const tmpl = document.getElementById('np-template').value;
      const prov = document.getElementById('np-provider').value;

      if (!name) { toast('Project name is required', 'error'); return; }

      try {
        const result = await api.createProject({ name, template: tmpl, code_dir: code });
        // Update project.yaml with extra fields
        await api.updateProjectConfig(name, { description: desc, default_provider: prov, code_dir: code });
        toast(`Project "${name}" created`, 'success');
        overlay.remove();
        // Refresh project list then open
        const data = await api.listProjects();
        const { setState } = await import('../stores/state.js');
        setState({ projects: data.projects || [] });
        window._openProject(name);
      } catch (e) {
        toast(`Error: ${e.message}`, 'error');
      }
    };
  };
}
