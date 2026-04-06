# Project Memory — aicli
_Generated: 2026-04-06 17:36 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI backend with an Electron desktop frontend, enabling LLM-driven project analysis with semantic search via PostgreSQL+pgvector. Current focus is work item management with dual-status tracking (user vs AI suggestions), semantic embedding of code/requirements, and commit association—implementing intelligent task planning and memory synthesis across multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok).

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: SQL
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude_CLI_and_LLM_platforms
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
- **performance_optimization**: redundant_SQL_calls_eliminated
- **pipeline/auth**: Acceptance criteria:
# PM Analysis: Email Verification Feature

---

## Context Summary

The tagged context reveals this work item is an **incremental enhancement** to an existing authentication system. Sign In and Create Account forms are already live and functional. The prior PM analysis identified email verification as the missing layer—the system currently accepts any email without confirming ownership. The analys

Reviewer: ```json
{
  "passed": false,
  "score": 4,
  "issues": [
    "Implementation is incomplete — cuts off mid-file in EmailService.ts without finishing AWS SES client setup, email template loading, or the
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
- **ui_library**: 3_dot_menu_pattern
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local bash/npm
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with mem_mrr_commits table
- Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
- Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation
- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev

## In Progress

- Work item dual-status UI: implemented status_user (user dropdown) and status_ai (AI suggestion badge) with separate color indicators; updated table headers and drawer UI
- Work item schema migration: replaced single status field with status_user + status_ai; added code_summary field for semantic embedding and planner_tags matching
- Work item commits association: added /work-items/{id}/commits endpoint returning linked commits via JSONB tags filtering; integrated api.workItems.commits() client method
- Work item embedding strategy: unified embedding space for work_items + planner_tags via code_summary + requirements + summary fields for cross-table cosine-similarity matching
- Database query optimization: extended _SQL_LIST_WORK_ITEMS_BASE with commit_count subquery and status column updates; refactored _SQL_UNLINKED_WORK_ITEMS to filter by status_user != 'done'
- System context cleanup: removed outdated system context and claude session files; consolidated dev_runtime_state.json tracking (session count 396, last session 2026-04-06T17:34:59Z)

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **architecture-decision** `[open]`
- **customer-meeting** `[open]`
- **Test** `[open]`
- **low-level-design** `[open]`
- **high-level-design** `[open]`
- **retrospective** `[open]`

### Feature

- **UI** `[open]`
- **pagination** `[open]`
- **test-picker-feature** `[open]`
- **graph-workflow** `[open]`
- **billing** `[open]`
- **embeddings** `[open]`
- **tagging** `[open]`
- **mcp** `[open]`
- **workflow-runner** `[open]`
- **shared-memory** `[open]`
- **auth** `[open]`
- **dropbox** `[open]`

### Phase

- **prod** `[open]`
- **development** `[open]`
- **discovery** `[open]`

### Task

- **implement-projects-tab** `[open]`
- **memory** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 97dfb0b..223f762 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-06T17:34:35Z",
+  "last_updated": "2026-04-06T17:34:59Z",
   "last_session_id": "04974a99-4e27-44d8-ba75-c7b9e54ba9c7",
-  "last_session_ts": "2026-04-06T17:34:35Z",
-  "session_count": 395,
+  "last_session_ts": "2026-04-06T17:34:59Z",
+  "session_count": 396,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 14cfa36..3030f4e 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -708,3 +708,5 @@
 {"ts": "2026-04-06T14:17:59Z", "action": "commit_push", "source": "claude_cli", "session_id": "04974a99-4e27-44d8-ba75-c7b9e54ba9c7", "hash": "6714241e", "message": "docs: update system context files after claude cli session", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "04974a99-4e27-44d8-ba75-c7b9e54ba9c7", "hash": "a85bbac6", "message": "docs: update system context and memory after claude session 04974a99", "files_count": 65, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-06T17:30:00Z"}
 {"ts": "2026-04-06T17:29:50Z", "action": "commit_push", "source": "claude_cli", "session_id": "04974a99-4e27-44d8-ba75-c7b9e54ba9c7", "hash": "a85bbac6", "message": "docs: update system context and memory after claude session 04974a99", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "04974a99-4e27-44d8-ba75-c7b9e54ba9c7", "hash": "e7b9e994", "message": "chore: remove outdated system context and claude session files", "files_count": 55, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-06T17:34:45Z"}
+{"ts": "2026-04-06T17:34:34Z", "action": "commit_push", "source": "claude_cli", "session_id": "04974a99-4e27-44d8-ba75-c7b9e54ba9c7", "hash": "e7b9e994", "message": "chore: remove outdated system context and claude session files", "pushed": true, "push_error": ""}


### `commit` — 2026-04-06

Commit: chore: remove aicli system context files after claude session
Hash: 4addfaa5
Files changed (2):
  - workspace/aicli/_system/commit_log.jsonl
  - workspace/aicli/_system/dev_runtime_state.json

### `commit` — 2026-04-06

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 288674e..cb2d4e0 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -453,8 +453,13 @@ function _wiSetTableBody(tableBody, byId, catName, catColor, catIcon, project) {
 function _wiRenderRows(byId, catName, catColor, catIcon, project) {
   const rows = Object.values(byId);
 
+  const STATUS_UC = {active:'#27ae60', in_progress:'#e67e22', done:'#4a90e2', paused:'#888'};
+
   function rowFor(wi) {
-    const sc     = wi.status === 'active' ? '#27ae60' : wi.status === 'done' ? '#4a90e2' : '#888';
+    const su = wi.status_user || 'active';
+    const sa = wi.status_ai  || 'active';
+    const scU = STATUS_UC[su] || '#888';
+    const scA = STATUS_UC[sa] || '#888';
     const seqBadge = wi.seq_num
       ? `<span style="font-size:0.52rem;color:var(--muted);background:var(--surface2);
                       border:1px solid var(--border);padding:0.05rem 0.28rem;
@@ -483,8 +488,11 @@ function _wiRenderRows(byId, catName, catColor, catIcon, project) {
           </div>
         </td>
         <td style="padding:0.5rem 0.4rem;white-space:nowrap">
-          <span style="font-size:0.6rem;color:${sc};background:${sc}22;
-                       padding:0.12rem 0.4rem;border-radius:10px">${_esc(wi.status)}</span>
+          <span style="font-size:0.57rem;color:${scU};background:${scU}22;
+                       padding:0.1rem 0.38rem;border-radius:10px" title="User status">${_esc(su)}</span>
+          ${sa !== su ? `<span style="font-size:0.52rem;color:${scA};background:${scA}18;
+                                     padding:0.08rem 0.3rem;border-radius:10px;margin-left:2px;
+                                     opacity:.8" title="AI suggests: ${_esc(sa)}">AI:${_esc(sa)}</span>` : ''}
         </td>
         <td style="padding:0.5rem 0.4rem;color:var(--muted);font-size:0.65rem;
                    max-width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
@@ -498,7 +506,7 @@ function _wiRenderRows(byId, catName, catColor, catIcon, project) {
       <thead>
         <tr style="border-bottom:2px solid var(--border)">
           <th style="text-align:left;padding:0.35rem 0.5rem;color:var(--muted);font-weight:500">Name</th>
-          <th style="text-align:left;padding:0.35rem 0.4rem;color:var(--muted);font-weight:500;width:65px">Status</th>
+          <th style="text-align:left;padding:0.35rem 0.4rem;color:var(--muted);font-weight:500;width:90px">Status</th>
           <th style="text-align:left;padding:0.35rem 0.4rem;color:var(--muted);font-weight:500;max-width:110px">Criteria</th>
           <th style="text-align:left;padding:0.35rem 0.4rem;color:var(--muted);font-weight:500;width:70px">Tag</th>
         </tr>
@@ -546,6 +554,32 @@ async function _openWorkItemDrawer(id, catName, project, pane, catColor, catIcon
 
       <div style="padding:0.85rem 1rem;display:flex;flex-direction:column;gap:0.85rem">
 
+        <!-- Status row: user dropdown + AI badge -->
+        <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap">
+          <div style="display:flex;flex-direction:column;gap:0.2rem">
+            <div style="font-size:0.52rem;text-transform:uppercase;color:var(--muted);
+                        letter-spacing:.06em">Your Status</div>
+            <select
+              style="background:var(--surface2);border:1px solid var(--border);
+                     color:var(--text);font-size:0.65rem;padding:0.2rem 0.4rem;
+                     border-radius:var(--radius);font-family:var(--font);cursor:pointer"
+              onchange="api.workItems.patch('${id}','${project}',{status_user:this.value}).catch(e=>toast(e.message,'error'))">
+              ${['active','in_progress','paused','done'].map(s =>
+                `<option value="${s}"${wi.status_user===s?' selected':''}>${s}</option>`).join('')}
+            </select>
+          </div>
+          <div style="display:flex;flex-direction:column;gap:0.2rem">
+            <div style="font-size:0.52rem;text-transform:uppercase;color:var(--muted);
+                        letter-spacing:.06em">AI Status</div>
+            <span style="font-size:0.62rem;padding:0.18rem 0.5rem;border-radius:10px;
+                         color:${{active:'#27ae60',in_progress:'#e67e22',done:'#4a90e2',paused:'#888'}[wi.status_ai]||'#888'};
+                         background:${{active:'#27ae60',in_progress:'#e67e22',done:'#4a90e2',paused:'#888'}[wi.status_ai]||'#888'}22;
+                         border:1px solid currentColor;opacity:.8" title="AI-suggested status based on progress">
+              ${_esc(wi.status_ai || 'active')}
+            </span>
+          </div>
+        </div>
+
         <!-- Description -->
         <div>
           <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
@@ -605,12 +639,29 @@ async function _openWorkItemDrawer(id, catName, project, pane, catColor, catIcon
         <!-- AI Summary (read-only) -->
         <div>
           <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
-                      letter-spacing:.06em;margin-bottom:0.3rem">AI Summary</div>
+                      letter-spacing:.06em;margin-bottom:0.3rem">AI Progress Summary</div>
           <div style="font-size:0.65rem;color:var(--text2);line-height:1.5;
                       background:var(--surface2);padding:0.35rem 0.45rem;
                       border-radius:var(--radius)">${_esc(wi.summary)}</div>
         </div>` : ''}
 
+        ${wi.code_summary ? `
+        <!-- Code Summary (read-only) -->
+        <div>
+          <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
+                      letter-spacing:.06em;margin-bottom:0.3rem">Code Summary</div>
+          <div style="font-size:0.65rem;color:var(--text2);line-height:1.5;font-family:monospace;
+                      background:var(--surface2);padding:0.35rem 0.45rem;
+                      border

### `commit` — 2026-04-06

diff --git a/ui/frontend/utils/api.js b/ui/frontend/utils/api.js
index e641363..b478745 100644
--- a/ui/frontend/utils/api.js
+++ b/ui/frontend/utils/api.js
@@ -375,6 +375,7 @@ api.workItems = {
     { method: 'DELETE', headers: _headers() }
   ).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
   interactions: (id, project, limit = 20) => _get(`/work-items/${enc(id)}/interactions?project=${enc(project)}&limit=${limit}`),
+  commits:      (id, project, limit = 20) => _get(`/work-items/${enc(id)}/commits?project=${enc(project)}&limit=${limit}`),
   facts:        (project)     => _get(`/work-items/facts?project=${enc(project)}`),
   memoryItems:  (project, scope) => {
     const q = new URLSearchParams({ project: project || '' });


### `commit` — 2026-04-06

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index eeed890..4d16eb9 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -31,13 +31,15 @@ from data.dl_seq import next_seq
 
 _SQL_LIST_WORK_ITEMS_BASE = (
     """SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
-              w.status, w.acceptance_criteria, w.action_items,
-              w.requirements, w.content, w.summary,
-              w.tags, w.tag_id, w.ai_tag_id,
+              w.status_user, w.status_ai, w.acceptance_criteria, w.action_items,
+              w.requirements, w.code_summary, w.summary,
+              w.tags, w.tag_id, w.ai_tag_id, w.source_event_id,
               w.created_at, w.updated_at, w.seq_num,
               tc.color, tc.icon,
               (SELECT COUNT(*) FROM mem_mrr_prompts p
-               WHERE p.client_id=1 AND p.tags @> jsonb_build_object('work-item', w.id::text)) AS interaction_count
+               WHERE p.client_id=1 AND p.tags @> jsonb_build_object('work-item', w.id::text)) AS interaction_count,
+              (SELECT COUNT(*) FROM mem_mrr_commits c
+               WHERE c.project_id=w.project_id AND c.tags @> jsonb_build_object('work-item', w.id::text)) AS commit_count
        FROM mem_ai_work_items w
        LEFT JOIN mng_tags_categories tc ON tc.client_id=1 AND tc.name=w.ai_category
        WHERE {where}
@@ -47,12 +49,12 @@ _SQL_LIST_WORK_ITEMS_BASE = (
 
 _SQL_UNLINKED_WORK_ITEMS = """
     SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
-           w.status, w.requirements, w.summary, w.tags,
+           w.status_user, w.status_ai, w.requirements, w.summary, w.tags,
            w.created_at, w.seq_num,
            pt.name AS ai_tag_name
     FROM mem_ai_work_items w
     LEFT JOIN planner_tags pt ON pt.id = w.ai_tag_id
-    WHERE w.project_id=%s AND w.tag_id IS NULL AND w.status='active'
+    WHERE w.project_id=%s AND w.tag_id IS NULL AND w.status_user != 'done'
     ORDER BY w.created_at DESC
 """
 
@@ -60,30 +62,38 @@ _SQL_INSERT_WORK_ITEM = (
     """INSERT INTO mem_ai_work_items
            (project_id, ai_category, ai_name, ai_desc,
             requirements, acceptance_criteria, action_items,
-            content, summary, tags, status, seq_num)
-       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
+            code_summary, summary, tags, status_user, status_ai, seq_num)
+       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (project_id, ai_category, ai_name) DO NOTHING
        RETURNING id, ai_name, ai_category, created_at, seq_num"""
 )
 
 _SQL_GET_WORK_ITEM = (
     """SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
-              w.status, w.acceptance_criteria, w.action_items,
-              w.requirements, w.content, w.summary,
-              w.tags, w.tag_id, w.ai_tag_id,
+              w.status_user, w.status_ai, w.acceptance_criteria, w.action_items,
+              w.requirements, w.code_summary, w.summary,
+              w.tags, w.tag_id, w.ai_tag_id, w.source_event_id,
               w.created_at, w.updated_at, w.seq_num
        FROM mem_ai_work_items w
        WHERE w.project_id=%s AND w.id=%s::uuid"""
 )
 
+_SQL_GET_COMMITS = (
+    """SELECT c.commit_hash, c.commit_msg, c.summary, c.committed_at
+       FROM mem_mrr_commits c
+       WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s::text)
+       ORDER BY c.committed_at DESC LIMIT %s"""
+)
+
 _SQL_DELETE_WORK_ITEM = (
     "DELETE FROM mem_ai_work_items WHERE id=%s::uuid AND project_id=%s RETURNING id"
 )
 
 _SQL_GET_WORK_ITEM_BY_SEQ = (
     """SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
-              w.status, w.acceptance_criteria, w.action_items,
-              w.requirements, w.summary, w.tags, w.tag_id, w.ai_tag_id,
+              w.status_user, w.status_ai, w.acceptance_criteria, w.action_items,
+              w.requirements, w.code_summary, w.summary,
+              w.tags, w.tag_id, w.ai_tag_id,
               w.created_at, w.updated_at, w.seq_num
        FROM mem_ai_work_items w
        WHERE w.project_id=%s AND w.seq_num=%s
@@ -142,11 +152,16 @@ async def _trigger_memory_regen(project: str) -> None:
 async def _embed_work_item(
     project_id: int, item_id: str,
     ai_name: str, ai_desc: str, requirements: str, summary: str,
+    code_summary: str = "",
 ) -> None:
-    """Embed work item content and store the vector on the row."""
+    """Embed work item content and store the vector on the row.
+    Embedding = ai_name + ai_desc + requirements + summary + code_summary.
+    Used for: (1) semantic search, (2) cosine-similarity matching to planner_tags.
+    planner_tags.embedding = summary + action_items → same space, enabling cross-table match.
+    """
     try:
         from memory.memory_embedding import _embed
-        text = f"{ai_name} {ai_desc} {requirements} {summary}".strip()
+        text = f"{ai_name} {ai_desc} {requirements} {summary} {code_summary}".strip()
         vec = await _embed(text)
         if vec and db.is_available():
             vec_str = f"[{','.join(str(x) for x in vec)}]"
@@ -185,11 +200,12 @@ class WorkItemCreate(BaseModel):
     ai_name:             str
     ai_desc:             str = ""
     project:             Optional[str] = None
-    status:              str = "active"
+    status_user:         str = "active"
+    status_ai:           str = "active"
     requirements:        str = ""
     acceptance_criteria: str = ""
     action_items:        str = ""
-    content:             str = ""
+    code_summary:        str = ""
     summary:             str = ""
     tags:                dict = {}
 
@@ -197,11 +213,12 @@ class WorkItemCreate(BaseModel):
 class WorkItemPatch(BaseModel):
     ai_name:             Optional[str] = None
     ai_desc:             Optional[str] = None
-    status:              Optional[str] = None
+    status_user:         Optional[str] = None   # set by user: active / paused / done
+    status_ai:           Optio

## AI Synthesis

**[2026-04-06]** `claude_cli` — Work item dual-status UI completed with separate status_user (user dropdown) and status_ai (AI suggestion badge) controls; status_user/status_ai schema migration replaces single status field. **[2026-04-06]** `claude_cli` — Work item schema extended with code_summary field for semantic embedding and planner_tags cross-matching in unified embedding space. **[2026-04-06]** `claude_cli` — Added /work-items/{id}/commits endpoint returning linked commits via JSONB tags filtering; integrated api.workItems.commits() client method for commit association. **[2026-04-06]** `claude_cli` — Database query optimizations: extended _SQL_LIST_WORK_ITEMS_BASE with commit_count subquery; refactored _SQL_UNLINKED_WORK_ITEMS to filter by status_user != 'done'. **[2026-04-06]** `claude_cli` — Frontend initialization stabilized: removed undefined _plannerSelectAiSubtype reference and fixed init crash; verified work item drawer renders status controls without errors. **[2026-04-06]** `claude_cli` — System context cleanup: removed outdated claude session files and consolidated dev_runtime_state.json; maintained 396 sessions with last update at 2026-04-06T17:34:59Z.