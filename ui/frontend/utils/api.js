/**
 * api.js — Backend API layer
 *
 * Wraps fetch() with JWT auth headers, a 30-second AbortController timeout,
 * and structured error propagation. API keys live server-side; the client
 * sends only a Bearer token stored in localStorage as "aicli_token".
 * Exports the `api` namespace object plus `loadApiKeys` (deprecated shim) and
 * project-recency helpers `addRecentProject` / `getRecentProjects`.
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

function _errMsg(e, fallback) {
  // FastAPI 422 returns detail as array of {loc, msg, type} objects; others return a string.
  if (!e || !e.detail) return fallback;
  if (Array.isArray(e.detail)) return e.detail.map(d => d.msg || JSON.stringify(d)).join('; ');
  return String(e.detail);
}

async function _get(path) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 30_000);
  try {
    const r = await fetch(_base() + path, { headers: _headers(), signal: ctrl.signal });
    if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(_errMsg(e, r.statusText)); }
    return r.json();
  } finally {
    clearTimeout(timer);
  }
}

async function _post(path, body = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 30_000);
  try {
    const r = await fetch(_base() + path, { method: 'POST', headers: _headers(), body: JSON.stringify(body), signal: ctrl.signal });
    if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(_errMsg(e, r.statusText)); }
    return r.json();
  } finally {
    clearTimeout(timer);
  }
}

async function _put(path, body = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 30_000);
  try {
    const r = await fetch(_base() + path, { method: 'PUT', headers: _headers(), body: JSON.stringify(body), signal: ctrl.signal });
    if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(_errMsg(e, r.statusText)); }
    return r.json();
  } finally {
    clearTimeout(timer);
  }
}

async function _patch(path, body = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 30_000);
  try {
    const r = await fetch(_base() + path, { method: 'PATCH', headers: _headers(), body: JSON.stringify(body), signal: ctrl.signal });
    if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(_errMsg(e, r.statusText)); }
    return r.json();
  } finally {
    clearTimeout(timer);
  }
}

async function _del(path) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 30_000);
  try {
    const r = await fetch(_base() + path, { method: 'DELETE', headers: _headers(), signal: ctrl.signal });
    if (!r.ok) { const e = await r.json().catch(() => ({ detail: r.statusText })); throw new Error(_errMsg(e, r.statusText)); }
    return r.json();
  } finally {
    clearTimeout(timer);
  }
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
  relinkCommits: (project) => fetch(_base() + `/history/relink-commits?project=${encodeURIComponent(project || '')}`, {
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
  allValues:      (project) => _get(`/entities/all-values?${_pq(project)}`),
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
  // Tag a single event by its source_id — body: {source_id, tag: "cat:name", project?}
  tagBySourceId:        (body)                  => _post('/entities/events/tag-by-source-id', body),
  // Remove a tag string from an event by source_id (History/Commits ✕ button)
  untagBySourceId:      (sourceId, tag, project) =>
    _del(`/entities/events/tag-by-source-id?source_id=${encodeURIComponent(sourceId)}&tag=${encodeURIComponent(tag)}&${_pq(project)}`),
  // Remove a tag from all events in a session (Chat ✕ button on applied chips)
  untagSession:         (sessionId, tag, project) =>
    _del(`/entities/session-tag?session_id=${encodeURIComponent(sessionId)}&tag=${encodeURIComponent(tag)}&${_pq(project)}`),
  // Return source_id → string[] map for all tagged events (prompts + commits)
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


// ── Tags API ──────────────────────────────────────────────────────────────────

function enc(v) { return encodeURIComponent(v || ''); }

api.tags = {
  list:           (proj)         => _get(`/tags?project=${enc(proj)}`),
  create:         (body)         => _post('/tags', body),
  update:         (id, body)     => fetch(_base() + `/tags/${id}`, { method:'PATCH', headers:_headers(), body:JSON.stringify(body) }).then(r=>r.ok?r.json():r.json().then(e=>Promise.reject(new Error(e.detail)))),
  delete:         (id, proj, force=false) => _del(`/tags/${enc(id)}?project=${enc(proj)}${force?'&force=true':''}`),
  merge:                 (body)  => _post('/tags/merge', body),
  migrateToAiSuggestions:(proj) => _post(`/tags/migrate-to-ai-suggestions?project=${enc(proj)}`),
  plan:           (id, proj)     => _post(`/tags/${enc(id)}/plan?project=${enc(proj)}`),
getSources:     (id, proj)     => _get(`/tags/${enc(id)}/sources?project=${enc(proj)}`),
  addSource:      (body)         => _post('/tags/source', body),
  removeSource:   (id)           => _del(`/tags/source/${enc(id)}`),
  sessionContext: (proj)         => _get(`/tags/session-context?project=${enc(proj)}`),
  saveContext:    (proj, body)   => _post(`/tags/session-context?project=${enc(proj)}`, body),
  categories: {
    list:   ()         => _get('/tags/categories'),
    create: (body)     => _post('/tags/categories', body),
    update: (id, body) => fetch(_base() + `/tags/categories/${id}`, { method:'PATCH', headers:_headers(), body:JSON.stringify(body) }).then(r=>r.ok?r.json():r.json().then(e=>Promise.reject(new Error(e.detail)))),
    delete: (id)       => _del(`/tags/categories/${id}`),
  },
  suggestions: {
    generate: (proj)         => _post(`/tags/suggestions/generate?project=${enc(proj)}`),
    apply:    (proj, body)   => _post(`/tags/suggestions/apply?project=${enc(proj)}`, body),
    ignore:   (proj, body)   => _post(`/tags/suggestions/ignore?project=${enc(proj)}`, body),
  },
  relations: {
    list:   (proj)     => _get(`/tags/relations?project=${enc(proj)}`),
    create: (body)     => _post('/tags/relations', body),
    delete: (id)       => _del(`/tags/relations/${enc(id)}`),
    listForWorkItem: (project, workItemId) =>
      _get(`/tags/relations?project=${encodeURIComponent(project)}&work_item_id=${encodeURIComponent(workItemId)}`),
    listForTag: (project, tagId) =>
      _get(`/tags/relations?project=${encodeURIComponent(project)}&tag_id=${encodeURIComponent(tagId)}`),
    approve: (id) => fetch(_base() + `/tags/relations/${encodeURIComponent(id)}`, { method: 'PATCH', headers: _headers(), body: JSON.stringify({ related_approved: 'approved' }) }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
    reject:  (id) => fetch(_base() + `/tags/relations/${encodeURIComponent(id)}`, { method: 'PATCH', headers: _headers(), body: JSON.stringify({ related_approved: 'rejected' }) }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  },
};


// ── Work Items API ────────────────────────────────────────────────────────────

api.workItems = {
  list:         (projectOrOpts, category, status) => {
    const opts = (projectOrOpts && typeof projectOrOpts === 'object')
      ? projectOrOpts : { project: projectOrOpts, category, status };
    const q = new URLSearchParams({ project: opts.project || '' });
    if (opts.category)      q.set('category',      opts.category);
    if (opts.status)        q.set('status',         opts.status);
    if (opts.name)          q.set('name',           opts.name);
    if (opts.quality_stage) q.set('quality_stage',  opts.quality_stage);
    if (opts.limit)         q.set('limit',          String(opts.limit));
    return _get(`/work-items?${q}`);
  },
  get:          (id, project) => _get(`/work-items/${enc(id)}?project=${enc(project || '')}`),
  unlinked:     (project) => _get(`/work-items/unlinked?project=${enc(project || '')}`),
  rematchAll:   (project) => _post(`/work-items/rematch-all?project=${enc(project || '')}`, {}),
  create:       (project, body) => _post(`/work-items?project=${enc(project)}`, body),
  patch:        (id, project, body) => fetch(
    _base() + `/work-items/${enc(id)}?project=${enc(project)}`,
    { method: 'PATCH', headers: _headers(), body: JSON.stringify(body) }
  ).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  delete:       (id, project) => fetch(
    _base() + `/work-items/${enc(id)}?project=${enc(project)}`,
    { method: 'DELETE', headers: _headers() }
  ).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  interactions: (id, project, limit = 20) => _get(`/work-items/${enc(id)}/interactions?project=${enc(project)}&limit=${limit}`),
  commits:      (id, project, limit = 20) => _get(`/work-items/${enc(id)}/commits?project=${enc(project)}&limit=${limit}`),
  merge:        (id, mergeWith, project) => fetch(
    _base() + `/work-items/${enc(id)}/merge?project=${enc(project)}`,
    { method: 'POST', headers: _headers(), body: JSON.stringify({ merge_with: mergeWith }) }
  ).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  dismerge:     (id, project) => fetch(
    _base() + `/work-items/${enc(id)}/dismerge?project=${enc(project)}`,
    { method: 'POST', headers: _headers() }
  ).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  facts:        (project)     => _get(`/tags/${enc(project)}/facts`),
  memoryItems:  (project, scope) => {
    const q = new URLSearchParams({ project: project || '' });
    if (scope) q.set('scope', scope);
    return _get(`/work-items/memory-items?${q}`);
  },
  extract:      (id, proj) => _post(`/work-items/${enc(id)}/extract?project=${enc(proj)}`),
  refresh:      (id, proj) => _post(`/work-items/${enc(id)}/refresh?project=${enc(proj)}`),
  runPipeline:  (itemId, workflowId, project) =>
    _post(`/work-items/${enc(itemId)}/run-pipeline?workflow_id=${enc(workflowId)}&project=${enc(project)}`, {}),
};

// ── Agent Roles API ───────────────────────────────────────────────────────────

api.agentRoles = {
  list:           (project = '_global') => _get(`/agent-roles/?project=${enc(project)}`),
  create:         (body)                => _post('/agent-roles/', body),
  patch:          (id, body)            => fetch(_base() + `/agent-roles/${id}`, {
    method: 'PATCH', headers: _headers(), body: JSON.stringify(body),
  }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  delete:         (id)                  => _del(`/agent-roles/${id}`),
  versions:       (id)                  => _get(`/agent-roles/${id}/versions`),
  restore:        (id, versionId)       => _post(`/agent-roles/${id}/restore/${versionId}`, {}),
  availableTools: ()                    => _get('/agent-roles/available-tools'),
  validateYaml:   (body)                => _post('/agent-roles/validate-yaml', body),
  syncYaml:       (body)                => _post('/agent-roles/sync-yaml', body),
  exportYaml:     (id)                  => fetch(_base() + `/agent-roles/${id}/export-yaml`, {
    headers: _headers(),
  }).then(r => r.ok ? r.text() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
};

// ── System Roles API ──────────────────────────────────────────────────────────

api.systemRoles = {
  list:      ()                    => _get('/system-roles/'),
  create:    (body)                => _post('/system-roles/', body),
  patch:     (id, body)            => fetch(_base() + `/system-roles/${id}`, {
    method: 'PATCH', headers: _headers(), body: JSON.stringify(body),
  }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  delete:    (id)                  => _del(`/system-roles/${id}`),
  listLinks: (roleId)              => _get(`/system-roles/agent-roles/${roleId}/links`),
  attach:    (roleId, body)        => _post(`/system-roles/agent-roles/${roleId}/links`, body),
  detach:    (roleId, systemRoleId) => _del(`/system-roles/agent-roles/${roleId}/links/${systemRoleId}`),
};

// ── ReAct Agents API ─────────────────────────────────────────────────────────

api.agents = {
  listRoles:    ()           => _get('/agents/roles'),
  listPipelines:()           => _get('/agents/pipelines'),
  runAgent:     (body)       => _post('/agents/run', body),
  runPipeline:  (body)       => _post('/agents/run-pipeline', body),
  getRun:       (runId)      => _get(`/agents/runs/${enc(runId)}`),
};

// ── Graph Workflows API ───────────────────────────────────────────────────────

api.graphWorkflows = {
  list:       (project)           => _get(`/graph/?project=${enc(project)}`),
  create:     (body)              => _post('/graph/', body),
  get:        (id)                => _get(`/graph/${id}`),
  update:     (id, body)          => fetch(_base() + `/graph/${id}`, { method: 'PUT',    headers: _headers(), body: JSON.stringify(body) }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  delete:     (id)                => _del(`/graph/${id}`),
  createNode: (wfId, body)        => _post(`/graph/${wfId}/nodes`, body),
  updateNode: (wfId, nId, body)   => fetch(_base() + `/graph/${wfId}/nodes/${nId}`, { method: 'PATCH',  headers: _headers(), body: JSON.stringify(body) }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  deleteNode: (wfId, nId)         => _del(`/graph/${wfId}/nodes/${nId}`),
  createEdge: (wfId, body)        => _post(`/graph/${wfId}/edges`, body),
  updateEdge: (wfId, eId, body)   => fetch(_base() + `/graph/${wfId}/edges/${eId}`, { method: 'PATCH',  headers: _headers(), body: JSON.stringify(body) }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  deleteEdge: (wfId, eId)         => _del(`/graph/${wfId}/edges/${eId}`),
  startRun:   (wfId, body)        => _post(`/graph/${wfId}/runs`, body),
  getRun:     (runId)             => _get(`/graph/runs/${runId}`),
  listRuns:   (wfId)              => _get(`/graph/${wfId}/runs`),
  cancelRun:  (runId)             => _del(`/graph/runs/${runId}`),
  decide:       (runId, body)       => _post(`/graph/runs/${runId}/decision`, body),
  approvalChat: (runId, body)       => _post(`/graph/runs/${runId}/chat`,     body),
  exportYAML:   (wfId)              => fetch(_base() + `/graph/${enc(wfId)}/export-yaml`, { headers: _headers() }).then(r => r.ok ? r.text() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  importYAML:   (project, yamlText) => _post(`/graph/import-yaml?project=${enc(project)}`, { yaml_text: yamlText }),
  recentRuns:   (project, limit=20) => _get(`/graph/runs/recent?project=${enc(project)}&limit=${limit}`),
  deliverables: (runId)             => _get(`/graph/runs/${enc(runId)}/deliverables`),
};

// ── Documents API ─────────────────────────────────────────────────────────────

api.documents = {
  list:   (project)                => _get(`/documents/?project=${enc(project)}`),
  read:   (path, project)          => _get(`/documents/read?path=${enc(path)}&project=${enc(project)}`),
  save:   (path, content, project) => fetch(
    _base() + `/documents/?project=${enc(project)}`,
    { method: 'PUT', headers: _headers(), body: JSON.stringify({ path, content }) },
  ).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  delete: (path, project)          => fetch(
    _base() + `/documents/?path=${enc(path)}&project=${enc(project)}`,
    { method: 'DELETE', headers: _headers() },
  ).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
};

// ── Work Items (mem_work_items) API ───────────────────────────────────────────

api.wi = {
  stats:          (p)       => _get(`/wi/${enc(p)}/stats`),
  pending:        (p)       => _get(`/wi/${enc(p)}/pending`),
  pendingGrouped: (p)       => _get(`/wi/${enc(p)}/pending/grouped`),
  list:           (p, params) => _get(`/wi/${enc(p)}${params ? `?${params}` : ''}`),
  classify:   (p, maxUc, bg) => {
    const qs = [bg && 'background=true', maxUc && `max_use_cases=${maxUc}`].filter(Boolean).join('&');
    return _post(`/wi/${enc(p)}/classify${qs ? `?${qs}` : ''}`, {});
  },
  approve:    (p, id)       => _post(`/wi/${enc(p)}/${enc(id)}/approve`, {}),
  reject:     (p, id)       => _post(`/wi/${enc(p)}/${enc(id)}/reject`, {}),
  approveAll: (p, parentId) => _post(`/wi/${enc(p)}/approve-all`, { parent_id: parentId }),
  update:     (p, id, b)    => _patch(`/wi/${enc(p)}/${enc(id)}`, b),
  remove:     (p, id)       => _del(`/wi/${enc(p)}/${enc(id)}`),
  moveEvent:  (p, id, b)    => _post(`/wi/${enc(p)}/${enc(id)}/move`, b),
  reset:      (p)           => _post(`/wi/${enc(p)}/reset`, {}),
  create:     (p, b)        => _post(`/wi/${enc(p)}`, b),
  reorder:    (p, items)    => _post(`/wi/${enc(p)}/reorder`, { items }),
  useCases:  (p)          => _get(`/wi/${enc(p)}/use-cases`),
  summarise: (p, ucId)    => _post(`/wi/${enc(p)}/${enc(ucId)}/ai-summarise`, {}),
  versions: {
    list:  (p, ucId)         => _get(`/wi/${enc(p)}/${enc(ucId)}/versions`),
    create: (p, ucId)        => _post(`/wi/${enc(p)}/${enc(ucId)}/versions`, {}),
    apply:  (p, ucId, vid)   => _post(`/wi/${enc(p)}/${enc(ucId)}/versions/${enc(vid)}/apply`, {}),
  },
  md: {
    get:     (p, id)      => _get(`/wi/${enc(p)}/${enc(id)}/md`),
    save:    (p, id, txt) => _post(`/wi/${enc(p)}/${enc(id)}/md`, { content: txt }),
    refresh: (p, id)      => _post(`/wi/${enc(p)}/${enc(id)}/md/refresh`, {}),
  },
};

// ── Pipeline API ──────────────────────────────────────────────────────────────

api.backlog = {
  stats:             (project)              => _get(`/memory/${enc(project)}/backlog-stats`),
  entries:           (project)              => _get(`/memory/${enc(project)}/backlog`),
  syncBacklog:       (project, mode, source) => _post(`/memory/${enc(project)}/sync-backlog${mode ? `?mode=${enc(mode)}` : source ? `?source=${enc(source)}` : ''}`, {}),
  runWorkItems:      (project)              => _post(`/memory/${enc(project)}/work-items/sync`, {}),
  patch:             (project, refId, body)   => _patch(`/memory/${enc(project)}/backlog/${enc(refId)}`, body),
  patchGroup:        (project, slug, body)    => _patch(`/memory/${enc(project)}/backlog/group/${enc(slug)}`, body),
  approveGroup:      (project, slug, approve) => _post(`/memory/${enc(project)}/backlog/approve-group`, { slug, approve }),
  deleteEntry:       (project, refId)         => _del(`/memory/${enc(project)}/backlog/${enc(refId)}`),
  listSlugs:         (project)               => _get(`/memory/${enc(project)}/use-case-slugs`),
  getUseCaseSection: (project, ref)           => _get(`/memory/${enc(project)}/use-case-section?ref=${enc(ref)}`),
  codeStats:              (project, slug) => _get(`/memory/${enc(project)}/backlog/code-stats/${enc(slug)}`),
  listPlannerTags:        (project)       => _get(`/tags?project=${enc(project)}`),
  exportCommitAnalysis:   (project)       => _post(`/memory/${enc(project)}/export-commit-analysis`, {}),
  listUseCaseItems:  (project, slug)       => _get(`/memory/${enc(project)}/use-case-items/${enc(slug)}`),
  deleteUseCaseItem: (project, body)       => fetch(
    _base() + `/memory/${enc(project)}/use-case-item`,
    { method: 'DELETE', headers: _headers(), body: JSON.stringify(body) },
  ).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  restoreUseCaseItem:(project, body)       => _post(`/memory/${enc(project)}/use-case-item`, body),
};

api.pipeline = {
  status:          (project)                        => _get(`/memory/${enc(project)}/pipeline-status`),
  dashboard:       (project)                        => _get(`/memory/${enc(project)}/data-dashboard`),
  templates:       (project)                        => _get(`/memory/${enc(project)}/workflow-templates`),
  llmCosts:        (project)                        => _get(`/memory/${enc(project)}/llm-costs`),
  qualityCheck:    (project)                        => _post(`/memory/${enc(project)}/quality-check`, {}),
  pruneTags:       (project, keepIds)               => _post(`/memory/${enc(project)}/prune-tags`, { keep_ids: keepIds }),
};

// ── UI log helper — callable from any view ─────────────────────────────────────
/** Send a log entry to the backend log files (appears in app.log / error.log). */
export function logToBackend(level, message, context = null) {
  fetch(_base() + '/logs/ui-error', {
    method: 'POST',
    headers: _headers(),
    body: JSON.stringify({ level, message, context, url: window.location.href }),
  }).catch(() => {});
}

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
