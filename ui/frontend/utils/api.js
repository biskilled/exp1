/**
 * Backend API layer — wraps fetch() with auth headers.
 *
 * API keys are now stored server-side (admin sets them in Admin panel).
 * Client only sends the JWT Bearer token — no X-*-Key headers.
 * JWT token is stored in localStorage as "aicli_token".
 */

import { state } from '../stores/state.js';

function _base() {
  return (state.settings?.backend_url || 'http://localhost:8000').replace(/\/$/, '');
}

function _headers(extra = {}) {
  const h = { 'Content-Type': 'application/json', ...extra };
  const tok = localStorage.getItem('aicli_token');
  if (tok) h['Authorization'] = `Bearer ${tok}`;
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

  // Unified project history (all sources: ui, claude_cli, workflow)
  historyChat: (project, limit = 200) => _get(`/history/chat?project=${encodeURIComponent(project || '')}&limit=${limit}`),

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

  // Admin — user management + pricing + coupons + api keys (admin only)
  adminGetStats:    ()             => _get('/admin/stats'),
  adminListUsers:   ()             => _get('/admin/users'),
  adminPatchUser:   (id, body)     => fetch(_base() + `/admin/users/${encodeURIComponent(id)}`, {
                                       method: 'PATCH', headers: _headers(), body: JSON.stringify(body),
                                     }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail)))),
  adminDeleteUser:  (id)           => _del(`/admin/users/${encodeURIComponent(id)}`),
  adminGetPricing:  ()             => _get('/admin/pricing'),
  adminSavePricing: (body)         => _put('/admin/pricing', body),
  adminGetCoupons:  ()             => _get('/admin/coupons'),
  adminCreateCoupon:(body)         => _post('/admin/coupons', body),
  adminDeleteCoupon:(code)         => _del(`/admin/coupons/${encodeURIComponent(code)}`),
  adminGetApiKeys:    ()           => _get('/admin/api-keys'),
  adminSaveApiKeys:   (body)       => _put('/admin/api-keys', body),
  adminGetApiBalances:()           => _get('/admin/api-balances'),
  adminGetUsageTable: ()           => _get('/admin/usage-table'),

  // Billing — per-user balance + coupon + history
  billingBalance:      ()          => _get('/billing/balance'),
  billingApplyCoupon:  (code)      => _post('/billing/apply-coupon', { code }),
  billingHistory:      ()          => _get('/billing/history'),
  billingAddPayment:   ()          => _post('/billing/add-payment', {}),
};

// ── API key stub (keys are now server-side; kept for backward compat) ─────────

/** @deprecated Keys are managed server-side. Returns {} so old call-sites don't crash. */
export function loadApiKeys() { return {}; }

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
