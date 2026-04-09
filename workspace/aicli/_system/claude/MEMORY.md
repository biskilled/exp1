# Project Memory — aicli
_Generated: 2026-04-09 10:45 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that captures, synthesizes, and organizes development context across projects using PostgreSQL with vector embeddings, Claude LLM processing, and async DAG workflows. The desktop UI (Electron + Vanilla JS) and CLI backend provide work item management with AI-suggested tags, semantic search via MCP tools, and multi-provider LLM support. Currently finalizing work item panel UI polish, tag backlinking propagation, and AI suggestion display debugging to ensure proper tag consistency across event-to-work-item relationships.

## Project Facts

- **ai_tag_color_default**: #4a90e2 replaces var(--accent), applied when wi.ai_tag_color not set
- **ai_tag_label_format**: category:name when both present, falls back to name-only, empty string if neither
- **ai_tag_suggestion_feature**: ai_tag_suggestion column with approve/remove button handlers (_wiPanelApproveTag/_wiPanelRemoveTag), refactored to simplified chip markup without category prefix display in non-category mode
- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **code_extraction_configuration**: min_lines: 5 (per-symbol threshold), min_diff_lines: 5 (commit-level threshold), only_on_commits_with_tags: false
- **commit_processing_flag**: exec_llm boolean column replaces tags->>'llm' NULL check
- **commit_tracking_schema**: mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **date_format_frontend**: YY/MM/DD-HH:MM format in work item panel
- **db_engine**: PostgreSQL with SQL parameter binding
- **db_schema_management**: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **frontend_sticky_header_pattern**: CSS position:sticky;top:0;z-index:1 on table headers for work_items panel
- **frontend_ui_pattern**: inline event handlers with event.stopPropagation(), CSS opacity/color hover states via onmouseenter/onmouseleave, escaped string interpolation in onclick via _esc()
- **known_bug_active**: planner_tag_visibility: categories upload but individual tags don't display in UI bindings
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **memory_sync_workflow**: /memory endpoint executes embedding pipeline refresh to sync prompts with work_items and detect new tags
- **memory_system_update_status**: updated_with_latest_context_and_session_tags
- **pending_feature**: tags display under work_items in shared memory context
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
- **performance_issue_active**: route_work_items latency ~60s; investigating _SQL_UNLINKED_WORK_ITEMS indexing and mem_ai_events join optimization
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
- **prompt_architecture**: core.prompt_loader for centralization; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
- **prompt_loading_pattern**: core.prompt_loader._prompts.content() replaces direct mng_system_roles queries
- **rel:ai_tag_suggestion:user_tags**: replaces
- **rel:ai_tag_suggestion:work_items_table**: related_to
- **rel:commit_processing:exec_llm_flag**: replaces
- **rel:frontend_ui_pattern:ai_tag_suggestion_feature**: implements
- **rel:memory_endpoint:tag_detection**: implements
- **rel:memory_system:session_tags**: implements
- **rel:prompt_loader:mng_system_roles**: replaces
- **rel:route_memory:prompt_loader**: depends_on
- **rel:route_memory:sql_parameter_binding**: depends_on
- **rel:route_prompts:memory_embedding**: depends_on
- **rel:route_search:memory_embedding**: depends_on
- **rel:route_snapshots:prompt_loader**: depends_on
- **rel:route_work_items:sql_parameter_binding**: depends_on
- **rel:sticky_header:work_items_panel**: implements
- **rel:ui_notifications:error_handling**: related_to
- **rel:work_item_deletion:api_endpoint**: depends_on
- **rel:work_item_panel:state_management**: implements
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- **tag_filtering_scope_issue**: non-work-item tags (Shared-memory, billing) incorrectly appearing in work_items panel UI; scope filtering implementation in progress
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
- **ui_library**: 3_dot_menu_pattern
- **ui_toast_notification**: toast() function displays error messages with 'error' severity level
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition
- **user_tags_rendering**: removed from panel display (userTagsHtml variable deleted), stored in wi.user_tags array but no longer shown in UI
- **work_item_deletion_endpoint**: DELETE /work-items/{id} with confirm dialog, cache clearing via window._wiPanelDelete, panel re-rendering
- **work_item_deletion_pattern**: client-side confirmation dialog, async api.workItems.delete(), local state cleanup, re-render panel
- **work_item_description_processing**: newlines replaced with spaces and trimmed (replace(/\n/g,' ').trim()), clipped to 70 chars with ellipsis
- **work_item_display_fields**: ai_category icon mapping, status_user color mapping, seq_num sequence number, id identifier
- **work_item_panel_state_management**: _wiPanelItems object stores work items, window._wiPanelDelete and window._wiPanelRefresh are global handlers
- **work_item_ui_column_widths**: 56px–80px for multi-column sortable table headers
- **work_item_ui_pattern**: multi-column sortable table with proper header styling, status color badges

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev
- **prompt_management**: core.prompt_loader module with centralized prompt caching
- **schema_management**: db_schema.sql (single source of truth) + db_migrations.py (m001-m019 framework)
- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with UNION consolidation
- Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; source_event_id pivot for session-based aggregation
- AI suggestion system: category-aware matching (task/bug/feature prioritized), Level 4 fallback to suggest new when no matches ≥0.70, 0.60 confidence threshold
- Work item panel: multi-column sortable table with AI tag suggestions + user tags from connected events; event_count aggregation via session matching
- Tag backlinking: PATCH /work-items with tag_id triggers _backlink_tag_to_events() propagating assignments to all events in source session
- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb) for desktop

## In Progress

- Work item refresh workflow: replaced 'new work item' button with ↻ refresh button triggering /work-items/rematch-all endpoint to refetch unlinked items and update AI tag suggestions
- Event count aggregation: added event_count column to work item panel calculated via session-based COUNT(*) from mem_ai_events matching source_event_id's session
- AI tag backlinking implementation: _backlink_tag_to_events() propagates planner tag assignments back to all events in source session, mapping category→tag_key (bug/phase/feature)
- Work item panel UI refinement: adjusted colgroup widths (52px per count column), fixed table overflow issues showing only first column, added proper padding/spacing
- Session-based tag propagation: enabled tag_id field in PATCH /work-items endpoint to trigger async backlinking, ensuring tag consistency across event-to-work-item relationships
- AI tag display debugging: investigating missing suggested_new tags in ui_tags query and verifying ai_suggestion column population in work item panel refresh

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **high-level-design** `[open]`
- **architecture-decision** `[open]`
- **customer-meeting** `[open]`
- **Test** `[open]`
- **retrospective** `[open]`
- **low-level-design** `[open]`

### Feature

- **pagination**
- **graph-workflow** `[open]`
- **billing** `[open]`
- **embeddings** `[open]`
- **tagging** `[open]`
- **mcp** `[open]`
- **workflow-runner** `[open]`
- **test-picker-feature** `[open]`
- **UI** `[open]`
- **auth** `[open]`
- **dropbox** `[open]`
- **shared-memory** `[open]`

### Phase

- **discovery** `[open]`
- **prod** `[open]`
- **development** `[open]`

### Task

- **memory** `[open]`
- **implement-projects-tab** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `prompt_batch: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

AI suggestion system updated to prioritize task/bug/feature categories with fallback to new tag suggestions; discovered ui_tags query missing suggested_new tags display, and identified need for refresh button instead of new work_item creation, plus requirement to propagate user-assigned tags to all linked events and add event counters.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.ai/rules.md b/.ai/rules.md
index 42c8677..eeac744 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 03:12 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 09:56 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -33,7 +33,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
-- **database**: PostgreSQL 15+ with pgvector extension
+- **database**: PostgreSQL 15+
 - **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with Electron-builder; Vite dev server
@@ -67,8 +67,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] I dont see any tags at the rows now (not ai and not users). also I do that desc is cut the the middle of the row instead
 - [2026-04-09] I cannot see the last column now. all I see is the first column name (commits.. ) I would like to add label in order to 
 - [2026-04-09] Can you add some padding on the left side of the table as last column UPDATED, I do see ony yy:mm:dd-HH:.. instead of th
 - [2026-04-09] I would like to update the ai_sujjestion - it suppose to sujjest one tag from catgories (task, bug or feature) and can s
-- [2026-04-09] Can you explain how do I see work_item #20006 as the one that was last updated ? the last prompt was about ui, ai tags..
\ No newline at end of file
+- [2026-04-09] Can you explain how do I see work_item #20006 as the one that was last updated ? the last prompt was about ui, ai tags..
+- [2026-04-09] Can you recheck that ai_tags as I do see new work_item, bit cannot see any sujjeste AI - all i see is mepy AI(EXISTS).. 
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

Reorganized _system documentation from monolithic structure into modular, feature-based layout for improved maintainability and navigation.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index a56099a..8381e01 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -110,10 +110,11 @@ export function renderEntities(container) {
         <span style="font-size:0.6rem;font-weight:700;color:var(--text);letter-spacing:.03em">⬡ WORK ITEMS</span>
         <span id="wi-panel-count" style="font-size:0.55rem;color:var(--muted)"></span>
         <span style="flex:1"></span>
-        <button id="wi-panel-add-btn"
-          style="background:var(--accent);border:none;color:#fff;font-size:0.57rem;
-                 padding:0.13rem 0.42rem;border-radius:var(--radius);cursor:pointer;
-                 font-family:var(--font);outline:none">+ New</button>
+        <button id="wi-panel-refresh-btn"
+          title="Refresh list and trigger AI tag matching for new items"
+          style="background:none;border:1px solid var(--border);color:var(--muted);font-size:0.62rem;
+                 padding:0.1rem 0.4rem;border-radius:var(--radius);cursor:pointer;
+                 font-family:var(--font);outline:none">↺</button>
       </div>
       <!-- Panel list (also a drop zone for unlinking) -->
       <div id="wi-panel-list" style="flex:1;overflow-y:auto;overflow-x:hidden"
@@ -443,13 +444,30 @@ async function _loadWiPanel(project) {
   } catch(e) {
     if (list) list.innerHTML = '<div style="padding:0.5rem 1rem;font-size:0.65rem;color:var(--muted)">Could not load work items</div>';
   }
+
+  // Wire up refresh button (only on first load)
+  const btn = document.getElementById('wi-panel-refresh-btn');
+  if (btn && !btn._wired) {
+    btn._wired = true;
+    btn.addEventListener('click', async () => {
+      btn.textContent = '…';
+      btn.disabled = true;
+      try {
+        await api.workItems.rematchAll(project);
+        await _loadWiPanel(project);
+      } catch(e) { /* ignore */ } finally {
+        btn.textContent = '↺';
+        btn.disabled = false;
+      }
+    });
+  }
 }
 
 function _renderWiPanel(items, project) {
   const list = document.getElementById('wi-panel-list');
   if (!list) return;
   if (!items.length) {
-    list.innerHTML = '<div style="padding:0.5rem 1rem;font-size:0.65rem;color:var(--muted)">No work items yet — click + New to create one</div>';
+    list.innerHTML = '<div style="padding:0.5rem 1rem;font-size:0.65rem;color:var(--muted)">All work items linked ✓ — or click ↺ to refresh</div>';
     return;
   }
 
@@ -598,12 +616,9 @@ function _renderWiPanel(items, project) {
         <span style="${LBL_AI_N}">AI(NEW)</span>
         <span style="font-size:0.65rem;font-weight:500;padding:1px 6px;border-radius:4px;
                      color:#e74c3c;border:1px solid #e74c3c;background:#e74c3c1a;
-                     white-space:nowrap">${_esc(aiNewLabel)}</span>
-        <button onclick="event.stopPropagation();window._wiPanelCreateTag('${_esc(wi.id)}','${_esc(aiNew)}','${_esc(aiNewCat)}','${_esc(project)}')"
-          title="Create this tag" style="background:none;border:1px solid #e74c3c;color:#e74c3c;
-                 cursor:pointer;font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">✓</button>
+                     white-space:nowrap" title="No existing tag — create one manually in the Planner">${_esc(aiNewLabel)}</span>
         <button onclick="event.stopPropagation();window._wiPanelRemoveTag('${_esc(wi.id)}','${_esc(project)}')"
-          title="Dismiss" style="background:none;border:1px solid #888;color:#888;cursor:pointer;
+          title="Dismiss suggestion" style="background:none;border:1px solid #888;color:#888;cursor:pointer;
                  font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">×</button>
       </div>`;
     } else {
@@ -660,6 +675,9 @@ function _renderWiPanel(items, project) {
       <td style="padding:4px 10px;text-align:right;white-space:nowrap;font-size:0.72rem;vertical-align:top;
                  color:var(--text2);font-variant-numeric:tabular-nums;
                  border-left:1px solid var(--border)">${wi.commit_count||0}</td>
+      <td style="padding:4px 10px;text-align:right;white-space:nowrap;font-size:0.72rem;vertical-align:top;
+                 color:var(--text2);font-variant-numeric:tabular-nums;
+                 border-left:1px solid var(--border)">${wi.event_count||0}</td>
       <td style="padding:4px 10px 4px 6px;text-align:right;white-space:nowrap;font-size:0.66rem;vertical-align:top;
                  color:var(--muted);font-variant-numeric:tabular-nums;font-family:monospace;
                  border-left:1px solid var(--border)">${fmtDate(wi.updated_at||wi.created_at)}</td>
@@ -668,7 +686,7 @@ function _renderWiPanel(items, project) {
 
   list.innerHTML = `
     <table style="width:100%;border-collapse:collapse;table-layout:fixed">
-      <colgroup><col><col style="width:58px"><col style="width:58px"><col style="width:112px"></colgroup>
+      <colgroup><col><col style="width:52px"><col style="width:52px"><col style="width:52px"><col style="width:112px"></colgroup>
       <thead><tr>
         <th style="text-align:left;padding:5px 8px 5px 12px;font-size:0.68rem;font-weight:600;
                    letter-spacing:.03em;text-transform:uppercase;
@@ -676,6 +694,7 @@ function _renderWiPanel(items, project) {
                    border-bottom:2px solid var(--border);position:sticky;top:0;z-index:1">Name</th>
         ${hdr('prompt_count','Prompts')}
         ${hdr('commit_count','Commits')}
+        ${hdr('event_count','Events')}
         ${hdr('updated_at','Updated')}
       </tr></thead>
       <tbody>${rows}</tbody>


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/ui/frontend/utils/api.js b/ui/frontend/utils/api.js
index 87a7662..7e3a106 100644
--- a/ui/frontend/utils/api.js
+++ b/ui/frontend/utils/api.js
@@ -367,6 +367,7 @@ api.workItems = {
   },
   get:          (id, project) => _get(`/work-items/${enc(id)}?project=${enc(project || '')}`),
   unlinked:     (project) => _get(`/work-items/unlinked?project=${enc(project || '')}`),
+  rematchAll:   (project) => _post(`/work-items/rematch-all?project=${enc(project || '')}`, {}),
   create:       (project, body) => _post(`/work-items?project=${enc(project)}`, body),
   patch:        (id, project, body) => fetch(
     _base() + `/work-items/${enc(id)}?project=${enc(project)}`,


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index 37776e9..1c1698d 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -97,6 +97,13 @@ _SQL_UNLINKED_WORK_ITEMS = """
                WHERE mc.session_id = (SELECT session_id FROM mem_ai_events WHERE id = w.source_event_id)
                  AND mc.project_id = w.project_id
            ), 0) AS commit_count,
+           -- Total events in the same session
+           COALESCE((
+               SELECT COUNT(*)
+               FROM mem_ai_events e3
+               WHERE e3.session_id = (SELECT session_id FROM mem_ai_events WHERE id = w.source_event_id)
+                 AND e3.project_id = w.project_id
+           ), 0) AS event_count,
            -- User tags: planner tags referenced in events from the same session
            (SELECT COALESCE(jsonb_agg(DISTINCT ut.name ORDER BY ut.name), '[]'::jsonb)
             FROM mem_ai_events ev
@@ -297,6 +304,54 @@ async def _run_matching(project: str, work_item_id: str) -> None:
         pass  # non-critical background task
 
 
+async def _backlink_tag_to_events(project_id: int, work_item_id: str, tag_id: str) -> None:
+    """When a work item is linked to a planner tag, propagate that tag to related events.
+
+    Finds the session from source_event_id, then updates all events in that session
+    to include the tag name in their tags JSONB (using the category-appropriate key).
+    Only writes if the event doesn't already have a user tag for that key.
+    """
+    try:
+        with db.conn() as conn:
+            with conn.cursor() as cur:
+                # Get tag name + category
+                cur.execute("""
+                    SELECT pt.name, tc.name AS cat
+                    FROM planner_tags pt
+                    LEFT JOIN mng_tags_categories tc ON tc.id = pt.category_id
+                    WHERE pt.id = %s::uuid
+                """, (tag_id,))
+                tag_row = cur.fetchone()
+                if not tag_row:
+                    return
+                tag_name, tag_cat = tag_row
+                # Map category to events tags key
+                tag_key = 'bug' if tag_cat == 'bug' else 'phase' if tag_cat == 'phase' else 'feature'
+
+                # Get session_id from source_event_id
+                cur.execute("""
+                    SELECT session_id FROM mem_ai_events
+                    WHERE id = (SELECT source_event_id FROM mem_ai_work_items WHERE id=%s::uuid)
+                """, (work_item_id,))
+                sess_row = cur.fetchone()
+                if not sess_row or not sess_row[0]:
+                    return
+                session_id = sess_row[0]
+
+                # Update events in that session that don't already have this key
+                cur.execute("""
+                    UPDATE mem_ai_events
+                    SET tags = tags || jsonb_build_object(%s, %s)
+                    WHERE session_id = %s
+                      AND project_id = %s
+                      AND (tags->>%s IS NULL OR tags->>%s = '')
+                """, (tag_key, tag_name, session_id, project_id, tag_key, tag_key))
+                log.debug(f"_backlink_tag_to_events: updated {cur.rowcount} events "
+                          f"session={session_id[:8]} tag={tag_key}:{tag_name}")
+    except Exception as e:
+        log.debug(f"_backlink_tag_to_events error: {e}")
+
+
 # ── Models ────────────────────────────────────────────────────────────────────
 
 class WorkItemCreate(BaseModel):
@@ -522,6 +577,10 @@ async def patch_work_item(
             asyncio.create_task(_embed_work_item(p_id, item_id, row[0], row[1] or "", row[2] or "", row[3] or ""))
         background.add_task(_run_matching, p, item_id)
 
+    # When tag_id is set, back-link that tag to all events in the same session
+    if body.tag_id and body.tag_id != '':
+        asyncio.create_task(_backlink_tag_to_events(p_id, item_id, body.tag_id))
+
     asyncio.create_task(_trigger_memory_regen(p))
     return {"ok": True, "id": item_id, "status_user": result[1]}
 


## AI Synthesis

**[2026-04-09]** `claude_cli` — Centralized prompt location mapping: work_item_extraction and work_item_promotion prompts in prompts/memory/work_items/ directory used by MemoryEmbedding and MemoryPromotion classes respectively. **[2026-04-09]** `user_session` — Fixed work item panel column visibility: adjusted colgroup widths to 52px per count column, added proper left padding to UPDATED column, and resolved table overflow showing only first column. **[2026-04-09]** `user_session` — AI tag suggestion UI issues identified: missing suggested_new tags display in ui_tags query and empty AI tag suggestions despite work_item.ai_suggestion population. **[2026-04-09]** `implementation` — Tag backlinking feature completed: _backlink_tag_to_events() now propagates user-assigned planner tags to all events in source session via category→tag_key mapping (bug/phase/feature). **[2026-04-09]** `implementation` — Event count aggregation: added event_count column to work item panel using session-based COUNT(*) from mem_ai_events matching source_event_id. **[2026-04-09]** `implementation` — Replaced 'new work item' button with refresh (↻) button triggering /work-items/rematch-all endpoint to refetch unlinked items and update AI tag suggestions dynamically.