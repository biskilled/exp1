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
  generateMemory:      (name)       => _post(`/projects/${encodeURIComponent(name)}/memory`, {}),
  getMemoryStatus:     (name)       => _get(`/projects/${encodeURIComponent(name)}/memory-status`),
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
  async chatStream(message, provider, sessionId, system = '', tags = {}) {
    const r = await fetch(_base() + '/chat/stream', {
      method: 'POST',
      headers: _headers(),
      body: JSON.stringify({ message, provider, session_id: sessionId, system, stream: true, tags }),
    });
    if (!r.ok) throw new Error(`Chat error: ${r.statusText}`);
    return r;  // caller reads r.body (ReadableStream)
  },

  // Chat session history
  chatSessions: ()    => _get('/chat/sessions'),
  chatSession:  (id)  => _get(`/chat/sessions/${encodeURIComponent(id)}`),
  patchSessionTags: (id, body, project) => fetch(
    _base() + `/chat/sessions/${encodeURIComponent(id)}/tags` + (project ? `?project=${encodeURIComponent(project)}` : ''),
    { method: 'PATCH', headers: _headers(), body: JSON.stringify(body) },
  ).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),

  // Unified project history (all sources: ui, claude_cli, workflow)
  historyChat: (project, limit = 200) => _get(`/history/chat?project=${encodeURIComponent(project || '')}&limit=${limit}`),
  historyCommits: (project, limit = 100) => _get(`/history/commits?project=${encodeURIComponent(project || '')}&limit=${limit}`),
  patchCommit: (id, body) => fetch(_base() + `/history/commits/${encodeURIComponent(id)}`, {
    method: 'PATCH', headers: _headers(), body: JSON.stringify(body),
  }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  getSessionCommits: (sessionId, project) =>
    _get(`/history/session-commits?session_id=${encodeURIComponent(sessionId)}&project=${encodeURIComponent(project || '')}`),
  syncCommits: (project) => fetch(_base() + `/history/commits/sync?project=${encodeURIComponent(project || '')}`, {
    method: 'POST', headers: _headers(),
  }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  getSessionTags:   (project) => _get(`/history/session-tags?project=${encodeURIComponent(project || '')}`),
  getSessionPhases: (project) => _get(`/history/session-phases?project=${encodeURIComponent(project || '')}`),
  putSessionTags: (project, body) => fetch(_base() + `/history/session-tags?project=${encodeURIComponent(project || '')}`, {
    method: 'PUT', headers: _headers(), body: JSON.stringify(body),
  }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),

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

  // Admin — billing: provider cost config + actual usage fetch
  adminGetProviderCosts:        ()           => _get('/admin/provider-costs'),
  adminSaveProviderCosts:       (body)       => _put('/admin/provider-costs', body),
  adminFetchProviderUsage:      (body)       => _post('/admin/fetch-provider-usage', body),
  adminGetProviderUsageHistory: (provider)   => _get(`/admin/provider-usage-history${provider ? `?provider=${encodeURIComponent(provider)}` : ''}`),
  adminDeleteProviderUsageRecord: (provider, fetched_at) =>
    fetch(_base() + `/admin/provider-usage-history?provider=${encodeURIComponent(provider)}&fetched_at=${encodeURIComponent(fetched_at)}`,
      { method: 'DELETE', headers: _headers() })
      .then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  adminClearProviderUsageHistory: (provider) =>
    fetch(_base() + `/admin/provider-usage-history?provider=${encodeURIComponent(provider)}`,
      { method: 'DELETE', headers: _headers() })
      .then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),

  // Admin — manual provider balances
  adminGetProviderBalances:  ()     => _get('/admin/provider-balances'),
  adminSaveProviderBalances: (body) => _put('/admin/provider-balances', body),

  // Billing — per-user balance + coupon + history
  billingBalance:      ()          => _get('/billing/balance'),
  billingApplyCoupon:  (code)      => _post('/billing/apply-coupon', { code }),
  billingHistory:      ()          => _get('/billing/history'),
  billingAddPayment:   ()          => _post('/billing/add-payment', {}),
};

// ── API key stub (keys are now server-side; kept for backward compat) ─────────

/** @deprecated Keys are managed server-side. Returns {} so old call-sites don't crash. */
export function loadApiKeys() { return {}; }

// ── Workflow runs API ─────────────────────────────────────────────────────────

api.workflowRuns = {
  start:    (project, wfName, userInput) =>
              _post(`/workflows/${encodeURIComponent(wfName)}/runs?project=${encodeURIComponent(project || '')}`,
                    { user_input: userInput }),
  get:      (project, runId) =>
              _get(`/workflows/runs/${encodeURIComponent(runId)}?project=${encodeURIComponent(project || '')}`),
  list:     (project) =>
              _get(`/workflows/runs?project=${encodeURIComponent(project || '')}`),
  decide:   (project, runId, action, nextStep = null) =>
              _post(`/workflows/runs/${encodeURIComponent(runId)}/decision?project=${encodeURIComponent(project || '')}`,
                    { action, next_step: nextStep }),
};

// ── Search API ────────────────────────────────────────────────────────────────

api.search = {
  semantic: (body)    => _post('/search/semantic', body),
  ingest:   (project) => _get(`/search/ingest?project=${encodeURIComponent(project || '')}`),
};

// ── Entities API ──────────────────────────────────────────────────────────────

function _pq(project) { return `project=${encodeURIComponent(project || '')}`; }

api.entities = {
  // Categories
  listCategories: (project)           => _get(`/entities/categories?${_pq(project)}`),
  createCategory: (body)              => _post('/entities/categories', body),
  patchCategory:  (id, body)          => fetch(_base() + `/entities/categories/${id}`, { method:'PATCH', headers:_headers(), body:JSON.stringify(body) }).then(r=>r.ok?r.json():r.json().then(e=>Promise.reject(new Error(e.detail)))),
  deleteCategory: (id)                => _del(`/entities/categories/${id}`),

  // Values
  listValues:     (project, catId, opts = {}) => {
    const q = new URLSearchParams({ project: project || '' });
    if (catId) q.set('category_id', catId);
    if (opts.category_name) q.set('category_name', opts.category_name);
    if (opts.status) q.set('status', opts.status);
    return _get(`/entities/values?${q}`);
  },
  createValue:    (body)              => _post('/entities/values', body),
  patchValue:     (id, body)          => fetch(_base() + `/entities/values/${id}`, { method:'PATCH', headers:_headers(), body:JSON.stringify(body) }).then(r=>r.ok?r.json():r.json().then(e=>Promise.reject(new Error(e.detail)))),
  deleteValue:    (id)                => _del(`/entities/values/${id}`),

  // Events
  listEvents:     (project, opts={}) => {
    const q = new URLSearchParams({ project: project||'' });
    if (opts.event_type) q.set('event_type', opts.event_type);
    if (opts.value_id)   q.set('value_id',   opts.value_id);
    if (opts.limit)      q.set('limit',       opts.limit);
    return _get(`/entities/events?${q}`);
  },
  syncEvents:     (project)           => _post(`/entities/events/sync?${_pq(project)}`, {}),
  addTag:         (eventId, valueId)  => _post(`/entities/events/${eventId}/tag`, { entity_value_id: valueId }),
  removeTag:      (eventId, valueId)  => _del(`/entities/events/${eventId}/tag/${valueId}`),
  valueEvents:    (valId, project)    => _get(`/entities/values/${valId}/events?${_pq(project)}`),

  // Links
  addLink:        (eventId, body)     => _post(`/entities/events/${eventId}/link`, body),
  removeLink:     (fromId, toId, lt)  => _del(`/entities/events/${fromId}/link/${toId}/${lt}`),
  getLinks:       (eventId)           => _get(`/entities/events/${eventId}/links`),

  // Session bulk-tag — tags ALL events in a session with one entity value
  sessionTag:           (body)                  => _post('/entities/session-tag', body),
  // Reload entity tags for a session (used when switching sessions in UI)
  getEntitySessionTags: (sessionId, project)    => _get(`/entities/session-tags?session_id=${encodeURIComponent(sessionId)}&${_pq(project)}`),
  // Tag a single event by its source_id (history.jsonl timestamp or commit hash)
  tagBySourceId:        (body)                  => _post('/entities/events/tag-by-source-id', body),
  // Remove a tag from an event by source_id (History/Commits ✕ button)
  untagBySourceId:      (sourceId, valueId, project) =>
    _del(`/entities/events/tag-by-source-id?source_id=${encodeURIComponent(sourceId)}&value_id=${valueId}&${_pq(project)}`),
  // Remove a tag from all events in a session (Chat ✕ button on applied chips)
  untagSession:         (sessionId, valueId, project) =>
    _del(`/entities/session-tag?session_id=${encodeURIComponent(sessionId)}&value_id=${valueId}&${_pq(project)}`),
  // Return source_id → [tags] map for all tagged events (prompts + commits)
  getSourceTags:        (project)               => _get(`/entities/events/source-tags?${_pq(project)}`),

  // Tag suggestions (auto-tag loop)
  getSuggestions:     (project, sourceId) => _get(
    `/entities/suggestions?${_pq(project)}${sourceId ? `&source_id=${encodeURIComponent(sourceId)}` : ''}`
  ),
  dismissSuggestions: (eventId) => _post(`/entities/suggestions/${eventId}/dismiss`, {}),

  // Value-to-value dependency links (Planner dependencies UI)
  getValueLinks:    (valId)         => _get(`/entities/values/${valId}/links`),
  createValueLink:  (valId, body)   => _post(`/entities/values/${valId}/links`, body),
  deleteValueLink:  (valId, toId, linkType = 'blocks') =>
    _del(`/entities/values/${valId}/links/${toId}?link_type=${encodeURIComponent(linkType)}`),

  // GitHub issue sync
  githubSync: (project, owner, repo, token = '', state = 'open') => {
    const q = new URLSearchParams({ project: project || '', owner, repo, state });
    if (token) q.set('token', token);
    return _post(`/entities/github-sync?${q}`, {});
  },
};


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
