/**
 * api.js — Backend API layer
 *
 * Wraps fetch() with JWT auth headers, a 30-second AbortController timeout,
 * and structured error propagation. API keys live server-side; the client
 * sends only a Bearer token stored in localStorage as "aicli_token".
 * Exports the `api` namespace object and project-recency helpers
 * `addRecentProject` / `getRecentProjects`.
 */

import { state } from '../stores/state.js';
import { BACKEND_URL } from './config.js';

function _base() {
  return (state.settings?.backend_url || BACKEND_URL).replace(/\/$/, '');
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


// ── Agent Roles API ───────────────────────────────────────────────────────────

api.agentRoles = {
  list:           (project = '_global', showDeactivated = false) =>
    _get(`/agent-roles/?project=${enc(project)}${showDeactivated ? '&show_deactivated=true' : ''}`),
  create:         (body)                => _post('/agent-roles/', body),
  patch:          (id, body, project = 'aicli') => fetch(_base() + `/agent-roles/${id}?project=${enc(project)}`, {
    method: 'PATCH', headers: _headers(), body: JSON.stringify(body),
  }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  delete:         (id)                  => _del(`/agent-roles/${id}`),
  versions:       (id)                  => _get(`/agent-roles/${id}/versions`),
  restore:        (id, versionId)       => _post(`/agent-roles/${id}/restore/${versionId}`, {}),
  restoreDefault: (id)                  => _post(`/agent-roles/${id}/restore`, {}),
  setBase:        (id)                  => _post(`/agent-roles/${id}/set-base`, {}),
  resetToBase:    (id)                  => _post(`/agent-roles/${id}/reset-to-base`, {}),
  reloadFromYaml: (project = 'aicli')  => _post(`/agent-roles/reload?project=${enc(project)}`, {}),
  providers:      ()                    => _get('/agent-roles/providers'),
  availableTools: ()                    => _get('/agent-roles/available-tools'),
  validateYaml:   (body)                => _post('/agent-roles/validate-yaml', body),
  syncYaml:       (body)                => _post('/agent-roles/sync-yaml', body),
  exportYaml:     (id)                  => fetch(_base() + `/agent-roles/${id}/export-yaml`, {
    headers: _headers(),
  }).then(r => r.ok ? r.text() : r.text().then(t => { try { const e = JSON.parse(t); return Promise.reject(new Error(e.detail || r.statusText)); } catch(_){ return Promise.reject(new Error(t || r.statusText)); } })),
  // MCP Catalog
  mcpCatalog:     (project)             => _get(`/agent-roles/mcp-catalog?project=${enc(project)}`),
  mcpCatalogSave: (project, body)       => fetch(_base() + `/agent-roles/mcp-catalog?project=${enc(project)}`, {
    method: 'PUT', headers: _headers(), body: JSON.stringify(body),
  }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  mcpActive:      (project)             => _get(`/agent-roles/mcp-active?project=${enc(project)}`),
  mcpActivate:    (project, body)       => _post(`/agent-roles/mcp-activate?project=${enc(project)}`, body),
  mcpDeactivate:  (project, name)       => _del(`/agent-roles/mcp-activate/${enc(name)}?project=${enc(project)}`),
  mcpUsage:       (project, name)       => _get(`/agent-roles/mcp-usage?project=${enc(project)}&mcp_name=${enc(name)}`),
  systemPrompts:  ()                    => _get(`/agent-roles/system-prompts`),
  pipelinesConfig: (project = 'aicli') => _get(`/agent-roles/pipelines-config?project=${enc(project)}`),
  patchPipeline:  (name, body, project = 'aicli') => fetch(_base() + `/agent-roles/pipelines/${enc(name)}?project=${enc(project)}`, {
    method: 'PATCH',
    headers: _headers(),
    body: JSON.stringify(body),
  }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || JSON.stringify(e))))),
  getPipelineConfig: (name, project = 'aicli') => _get(`/agent-roles/pipelines/${enc(name)}?project=${enc(project)}`),
};

// ── System Roles API ──────────────────────────────────────────────────────────

api.systemRoles = {
  list:          ()                    => _get('/system-roles/'),
  create:        (body)                => _post('/system-roles/', body),
  patch:         (id, body)            => fetch(_base() + `/system-roles/${id}`, {
    method: 'PATCH', headers: _headers(), body: JSON.stringify(body),
  }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
  delete:        (id)                  => _del(`/system-roles/${id}`),
  resetDefaults: ()                    => _post('/system-roles/reset-defaults'),
  listLinks:     (roleId)              => _get(`/system-roles/agent-roles/${roleId}/links`),
  attach:        (roleId, body)        => _post(`/system-roles/agent-roles/${roleId}/links`, body),
  detach:        (roleId, systemRoleId) => _del(`/system-roles/agent-roles/${roleId}/links/${systemRoleId}`),
};

// ── ReAct Agents API ─────────────────────────────────────────────────────────

api.agents = {
  listRoles:         ()                  => _get('/agents/roles'),
  listPipelines:     (mode)              => _get('/agents/pipelines' + (mode ? '?mode=' + enc(mode) : '')),
  runAgent:          (body)              => _post('/agents/run', body),
  runPipeline:       (body)              => _post('/agents/run-pipeline', body),
  getRun:            (runId)             => _get(`/agents/runs/${enc(runId)}`),
  // Async pipeline run endpoints
  startPipelineRun:  (body)              => _post('/agents/pipeline-runs', body),
  getPipelineRun:    (id)                => _get(`/agents/pipeline-runs/${enc(id)}`),
  listPipelineRuns:  (project, pipeline, limit = 20) => {
    const q = new URLSearchParams({ project: enc(project) || '', limit });
    if (pipeline) q.set('pipeline_name', pipeline);
    return _get(`/agents/pipeline-runs?${q}`);
  },
  approvePipelineRun:(id, body)          => _post(`/agents/pipeline-runs/${enc(id)}/approve`, body),
  scoreRun:          (id, score)         => fetch(_base() + `/agents/pipeline-runs/${enc(id)}/score`, {
    method: 'PATCH', headers: _headers(), body: JSON.stringify({ score }),
  }).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
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
    const qs = [bg && 'background=true', maxUc > 0 && `max_use_cases=${maxUc}`].filter(Boolean).join('&');
    return _post(`/wi/${enc(p)}/classify${qs ? `?${qs}` : ''}`, {});
  },
  classifyStatus: (p) => _get(`/wi/${enc(p)}/classify-status`),
  approve:    (p, id)       => _post(`/wi/${enc(p)}/${enc(id)}/approve`, {}),
  reject:     (p, id)       => _post(`/wi/${enc(p)}/${enc(id)}/reject`, {}),
  approveAll: (p, parentId) => _post(`/wi/${enc(p)}/approve-all`, { parent_id: parentId }),
  update:     (p, id, b)    => _patch(`/wi/${enc(p)}/${enc(id)}`, b),
  remove:     (p, id)       => _del(`/wi/${enc(p)}/${enc(id)}`),
  moveEvent:  (p, id, b)    => _post(`/wi/${enc(p)}/${enc(id)}/move`, b),
  reset:      (p)           => _post(`/wi/${enc(p)}/reset`, {}),
  create:     (p, b)        => _post(`/wi/${enc(p)}`, b),
  reorder:    (p, items)    => _post(`/wi/${enc(p)}/reorder`, { items }),
  merge:      (p, targetId, sourceId) => _post(`/wi/${enc(p)}/${enc(targetId)}/merge`, { source_id: sourceId }),
  unmerge:    (p, sourceId)          => _post(`/wi/${enc(p)}/${enc(sourceId)}/unmerge`, {}),
  useCases:   (p)          => _get(`/wi/${enc(p)}/use-cases`),
  completed:  (p)          => _get(`/wi/${enc(p)}/completed`),
  complete:   (p, id)      => _post(`/wi/${enc(p)}/${enc(id)}/complete`, {}),
  reopen:     (p, id)      => _post(`/wi/${enc(p)}/${enc(id)}/reopen`, {}),
  hookHealth:   (p)             => _get(`/chat/${enc(p)}/hook-health`),
  fileHotspots: (p, opts = {}) => _get(`/wi/${enc(p)}/file-hotspots`, opts),
  summarise:    (p, ucId)      => _post(`/wi/${enc(p)}/${enc(ucId)}/ai-summarise`, {}),
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
  facts:     (p)         => _get(`/tags/${enc(p)}/facts`),
  openItems: (p, ucId)   => _get(`/wi/${enc(p)}?parent_id=${enc(ucId)}&user_status=open&limit=50`),
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

// ── System API ─────────────────────────────────────────────────────────────────

api.system = {
  version:        () => _get('/system/version'),
  updateManifest: () => _get('/system/update-manifest'),
  saveManifest:   (body) => _put('/system/update-manifest', body),  // admin only
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
