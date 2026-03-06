/**
 * Backend API layer — wraps fetch() with auth + API key headers.
 *
 * API keys are stored in localStorage keyed by "aicli_api_keys" (JSON object).
 * JWT token is stored in localStorage as "aicli_token".
 * All LLM calls send the user's own keys as X-*-Key headers.
 */

import { state } from '../stores/state.js';

function _base() {
  return (state.settings?.backend_url || 'http://localhost:8000').replace(/\/$/, '');
}

function _apiKeys() {
  try { return JSON.parse(localStorage.getItem('aicli_api_keys') || '{}'); }
  catch { return {}; }
}

function _headers(extra = {}) {
  const h = { 'Content-Type': 'application/json', ...extra };
  const tok = localStorage.getItem('aicli_token');
  if (tok) h['Authorization'] = `Bearer ${tok}`;
  const keys = _apiKeys();
  if (keys.claude)   h['X-Anthropic-Key']  = keys.claude;
  if (keys.openai)   h['X-OpenAI-Key']     = keys.openai;
  if (keys.deepseek) h['X-DeepSeek-Key']   = keys.deepseek;
  if (keys.gemini)   h['X-Gemini-Key']     = keys.gemini;
  if (keys.grok)     h['X-Grok-Key']       = keys.grok;
  return h;
}

async function _get(path) {
  const r = await fetch(_base() + path, { headers: _headers() });
  if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(e.detail || r.statusText); }
  return r.json();
}

async function _post(path, body = {}) {
  const r = await fetch(_base() + path, { method: 'POST', headers: _headers(), body: JSON.stringify(body) });
  if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(e.detail || r.statusText); }
  return r.json();
}

async function _put(path, body = {}) {
  const r = await fetch(_base() + path, { method: 'PUT', headers: _headers(), body: JSON.stringify(body) });
  if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(e.detail || r.statusText); }
  return r.json();
}

async function _del(path) {
  const r = await fetch(_base() + path, { method: 'DELETE', headers: _headers() });
  if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(e.detail || r.statusText); }
  return r.json();
}

// ── API surface ───────────────────────────────────────────────────────────────

export const api = {
  // Health
  health: () => _get('/health'),

  // Auth
  login:    (email, password) => _post('/auth/login',    { email, password }),
  register: (email, password) => _post('/auth/register', { email, password }),
  me:       ()                => _get('/auth/me'),
  usage:    ()                => _get('/usage/me'),

  // Projects
  listProjects:        ()           => _get('/projects/'),
  getProject:          (name)       => _get(`/projects/${encodeURIComponent(name)}`),
  createProject:       (body)       => _post('/projects/', body),
  switchProject:       (name)       => _post(`/projects/switch/${encodeURIComponent(name)}`),
  getProjectConfig:    (name)       => _get(`/projects/${encodeURIComponent(name)}/config`),
  updateProjectConfig: (name, cfg)  => _put(`/projects/${encodeURIComponent(name)}/config`, cfg),
  getProjectSummary:   (name)       => _get(`/projects/${encodeURIComponent(name)}/summary`),
  updateProjectSummary:(name, content) => _put(`/projects/${encodeURIComponent(name)}/summary`, { content }),
  getProjectContext:   (name, save = false) => _get(`/projects/${encodeURIComponent(name)}/context?save=${save}`),
  runCommand:          (name, cmd)  => _post(`/projects/${encodeURIComponent(name)}/run-command`, { command: cmd }),

  // Prompts
  listPrompts:  (project)                 => _get(`/prompts/?project=${encodeURIComponent(project)}`),
  readPrompt:   (path, project)           => _get(`/prompts/read?path=${encodeURIComponent(path)}&project=${encodeURIComponent(project)}`),
  writePrompt:  (path, content, project)  => _put(`/prompts/?project=${encodeURIComponent(project)}`, { path, content }),
  deletePrompt: (path, project)           => _del(`/prompts/?path=${encodeURIComponent(path)}&project=${encodeURIComponent(project)}`),

  // Workflows
  listWorkflows:  (project)             => _get(`/workflows/?project=${encodeURIComponent(project)}`),
  readWorkflow:   (project, name)       => _get(`/workflows/${encodeURIComponent(name)}?project=${encodeURIComponent(project)}`),
  writeWorkflow:  (project, name, content) => _put(`/workflows/${encodeURIComponent(name)}?project=${encodeURIComponent(project)}`, { yaml_content: content }),

  // Files (code dir browser)
  getFiles: (maxDepth = 3) => _get(`/files/code?max_depth=${maxDepth}`),
  readFile: (path) => _get(`/files/read?path=${encodeURIComponent(path)}&root=code`),

  // Chat streaming — returns a ReadableStream, caller reads chunks
  async chatStream(message, provider, sessionId, system = '') {
    const r = await fetch(_base() + '/chat/stream', {
      method: 'POST',
      headers: _headers(),
      body: JSON.stringify({ message, provider, session_id: sessionId, system, stream: true }),
    });
    if (!r.ok) throw new Error(`Chat error: ${r.statusText}`);
    return r;  // caller reads r.body (ReadableStream)
  },

  // Chat session history
  chatSessions: ()    => _get('/chat/sessions'),
  chatSession:  (id)  => _get(`/chat/sessions/${encodeURIComponent(id)}`),

  // Git
  gitStatus:      (project)        => _get(`/git/${encodeURIComponent(project)}/status`),
  gitBranches:         (project)  => _get(`/git/${encodeURIComponent(project)}/branches`),
  gitOauthDeviceStart: (body)     => _post('/git/oauth/device/start', body),
  gitOauthDevicePoll:  (body)     => _post('/git/oauth/device/poll', body),
  gitOauthCreateRepo:  (body)     => _post('/git/oauth/create-repo', body),
  gitTestConnection:   (project)  => _get(`/git/${encodeURIComponent(project)}/test`),
  gitPull:             (project)  => _post(`/git/${encodeURIComponent(project)}/pull`, {}),
  gitPushAll:          (project)  => _post(`/git/${encodeURIComponent(project)}/push-all`, {}),
  gitSetup:       (project, body)  => _post(`/git/${encodeURIComponent(project)}/setup`, body),
  gitCommitPush:  (project, body)  => _post(`/git/${encodeURIComponent(project)}/commit-push`, body),

  // Admin — user management (admin only)
  adminListUsers:  ()              => _get('/admin/users'),
  adminPatchUser:  (id, body)      => fetch(_base() + `/admin/users/${encodeURIComponent(id)}`, {
                                       method: 'PATCH', headers: _headers(), body: JSON.stringify(body),
                                     }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail)))),
  adminDeleteUser: (id)            => _del(`/admin/users/${encodeURIComponent(id)}`),
};

// ── API key helpers (localStorage) ───────────────────────────────────────────

export function saveApiKeys(keys) {
  localStorage.setItem('aicli_api_keys', JSON.stringify(keys));
}

export function loadApiKeys() {
  return _apiKeys();
}

// ── Recent projects (localStorage) ───────────────────────────────────────────

const RECENT_KEY = 'aicli_recent_projects';

export function addRecentProject(name) {
  let recent = getRecentProjects();
  recent = [name, ...recent.filter(n => n !== name)].slice(0, 10);
  localStorage.setItem(RECENT_KEY, JSON.stringify(recent));
}

export function getRecentProjects() {
  try { return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]'); }
  catch { return []; }
}
