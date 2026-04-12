# Project Memory — aicli
_Generated: 2026-04-12 11:08 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that captures development session events, synthesizes them with Claude, and organizes insights into work items, project facts, and tagged entities. The system runs as a Python FastAPI backend with PostgreSQL+pgvector storage, a vanilla JS Electron desktop UI, and a CLI tool, supporting multi-user projects with semantic search, workflow automation via DAG executors, and integration with multiple LLM providers. Currently stabilizing the work item data model with consistent column naming (name_ai, category_ai, desc_ai, summary_ai) and enhancing the secondary AI tag workflow for metadata management.

## Project Facts

- **ai_event_filtering_logic**: event_type IN ('prompt_batch', 'session_summary') filters mem_ai_events; excludes per-commit and diff_file noise from event_count aggregation
- **ai_tag_color_default**: #4a90e2 replaces var(--accent), applied when wi.ai_tag_color not set
- **ai_tag_label_format**: category:name when both present, falls back to name-only, empty string if neither
- **ai_tag_suggestion_debugging_status**: investigating missing suggested_new tags in ui_tags query and verifying ai_suggestion column population in work item panel refresh workflow
- **ai_tag_suggestion_feature**: ai_tag_suggestion column with approve/remove button handlers (_wiPanelApproveTag/_wiPanelRemoveTag), refactored to simplified chip markup without category prefix display in non-category mode
- **ai_tag_suggestion_ux**: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip improved from 'No existing tag' to 'Does not exist yet'
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
- **event_count_column_semantics**: counts prompt_batch + session_summary events only; now displayed after commit_count (moved from position 2 to position 4)
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
- **prompt_count_metric**: distinct metric tracked separately from event_count in work items API response
- **prompt_loading_pattern**: core.prompt_loader._prompts.content() replaces direct mng_system_roles queries
- **rel:ai_tag_suggestion:user_tags**: replaces
- **rel:ai_tag_suggestion:work_items_table**: related_to
- **rel:commit_processing:exec_llm_flag**: replaces
- **rel:event_filtering:noise_reduction**: implements
- **rel:frontend_ui_pattern:ai_tag_suggestion_feature**: implements
- **rel:mem_ai_events:work_items**: depends_on
- **rel:memory_endpoint:tag_detection**: implements
- **rel:memory_system:session_tags**: implements
- **rel:prompt_loader:mng_system_roles**: replaces
- **rel:route_memory:prompt_loader**: depends_on
- **rel:route_memory:sql_parameter_binding**: depends_on
- **rel:route_prompts:memory_embedding**: depends_on
- **rel:route_search:memory_embedding**: depends_on
- **rel:route_snapshots:prompt_loader**: depends_on
- **rel:route_work_items:sql_parameter_binding**: depends_on
- **rel:session_context:prompt_counter**: implements
- **rel:stag_command:tag_command**: replaces
- **rel:sticky_header:work_items_panel**: implements
- **rel:tag_reminder:session_context**: depends_on
- **rel:ui_notifications:error_handling**: related_to
- **rel:wiDeleteLinked:entities_js**: implements
- **rel:wiUnlink:wiRowLoading**: depends_on
- **rel:work_item_api:prompt_count**: depends_on
- **rel:work_item_deletion:api_endpoint**: depends_on
- **rel:work_item_panel_sort:prompt_count**: implements
- **rel:work_item_panel:state_management**: implements
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- **session_context_prompt_counter**: prompt_count field added to session context JSON, initialized to 0, incremented on each prompt validation
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- **tag_command_alias**: /stag replaces /tag due to Claude Code skill name conflict; identical functionality with immediate availability
- **tag_creation_workflow**: _wiPanelCreateTag creates tags without confirmation, auto-links work item, refreshes tag cache + planner table + category tag list
- **tag_filtering_scope_issue**: non-work-item tags (Shared-memory, billing) incorrectly appearing in work_items panel UI; scope filtering implementation in progress
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
- **tag_reminder_display_format**: soft: '┄ Prompt #{N} ╌ still on: {tags}'; hard: multi-line box with current tags and re-send/update instructions
- **tag_reminder_feature**: soft reminder every N prompts (default 8, configurable via TAG_REMINDER_INTERVAL), hard check at 3× interval with tag confirmation requirement
- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
- **ui_library**: 3_dot_menu_pattern
- **ui_toast_notification**: toast() function displays error messages with 'error' severity level
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition
- **user_tags_rendering**: removed from panel display (userTagsHtml variable deleted), stored in wi.user_tags array but no longer shown in UI
- **work_item_deletion_endpoint**: DELETE /work-items/{id} with confirm dialog, cache clearing via window._wiPanelDelete, panel re-rendering
- **work_item_deletion_handler**: _wiDeleteLinked in entities.js with confirmation dialog and _wiRowLoading state management
- **work_item_deletion_pattern**: client-side confirmation dialog, async api.workItems.delete(), local state cleanup, re-render panel
- **work_item_description_processing**: newlines replaced with spaces and trimmed (replace(/\n/g,' ').trim()), clipped to 70 chars with ellipsis
- **work_item_display_fields**: ai_category icon mapping, status_user color mapping, seq_num sequence number, id identifier
- **work_item_event_association**: two-path join: session_id match from source_event_id OR direct work_item_id link, both filtered by event_type
- **work_item_panel_column_order**: Name, prompt_count, commit_count, event_count, updated_at (prompts column added before commits, events moved last)
- **work_item_panel_column_widths**: prompt_count:46px, commit_count:46px, event_count:46px (resized from 52px event_count + 52px commit_count)
- **work_item_panel_sortable_fields**: prompt_count, event_count, commit_count, seq_num (prompt_count added to sort handler)
- **work_item_panel_state_management**: _wiPanelItems object stores work items, window._wiPanelDelete and window._wiPanelRefresh are global handlers
- **work_item_ui_column_widths**: 56px–80px for multi-column sortable table headers
- **work_item_ui_pattern**: multi-column sortable table with proper header styling, status color badges
- **work_item_unlink_handler**: _wiUnlink uses _wiRowLoading(id, true) for loading state during patch operation

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
- **mcp**: Stdio MCP server with 12+ tools (semantic search, work item management, session tagging)
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories
- **config_management**: config.py + YAML pipelines + pyproject.toml + aicli.yaml session tagging config
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extensions
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
- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; Shared: users, usage_logs, transactions, session_tags, entity_categories, planner_tags, mng_tags_categories

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags_relations, project_facts, work_items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
- Work item column naming convention: ai_name → name_ai, ai_category → category_ai, ai_desc → desc_ai, summary → summary_ai for consistency; FK architecture links many events to one work item
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
- Secondary AI tags stored in ai_tags.confirmed[] array (metadata for doc_type/feature/phase); primary tag_id links work item to category
- Work item counters: prompt_count (raw prompts in source session), event_count (prompt_batch/session_summary events), commit_count (distinct commits per session)
- Session tagging: /stag command with immediate tag propagation via log_user_prompt.sh reading .agent-context
- Railway cloud deployment (Dockerfile + railway.toml) + Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)

## In Progress

- Work item column schema refactoring: completed renaming ai_name→name_ai, ai_category→category_ai, ai_desc→desc_ai, summary→summary_ai across frontend (entities.js) and backend (route_work_items.py, route_projects.py) for naming consistency
- prompt_work_item() trigger integration: added _run_promote_all_work_items() to /memory command execution pipeline to refresh AI text fields and status during memory generation
- Secondary AI tag workflow refinement: _wiSecApprove stores confirmed metadata (doc_type/phase/component) in ai_tags.confirmed[] array; items remain visible with permanent chip indicators instead of deletion
- Work item UI loading states: _wiRowLoading() CSS pulsing animation during async delete/approve/dismiss operations; integrated into tag-linked and unlinked panels with error state recovery
- Tag-linked work item refresh: _loadTagLinkedWorkItems reloads after approve/reject operations; planner table updates reflect linked/unlinked status changes when category selected
- AI tag suggestion UX: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip messaging improved from 'No existing tag' to 'Does not exist yet'

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
- **entity-routing** `[open]`
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
- **graph-workflow** `[open]`

### Phase

- **prod** `[open]`
- **development** `[open]`
- **discovery** `[open]`

### Task

- **memory** `[open]`
- **implement-projects-tab** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index e11df9a..600b26a 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -202,7 +202,7 @@ export function renderEntities(container) {
   };
 
   window._wiBotDragStart = (e, id, name, cat) => {
-    _dragWiData = { id, ai_name: name, ai_category: cat };
+    _dragWiData = { id, name_ai: name, category_ai: cat };
     e.dataTransfer.effectAllowed = 'link';
     e.dataTransfer.setData('text/plain', id);
     e.currentTarget.style.opacity = '0.5';
@@ -232,7 +232,7 @@ export function renderEntities(container) {
     el.style.outline = '';
     if (!_dragWiData || !targetId || targetId === _dragWiData.id) return;
     const sourceId = _dragWiData.id;
-    const sourceName = _dragWiData.ai_name;
+    const sourceName = _dragWiData.name_ai;
     _dragWiData = null;
     try {
       await api.workItems.merge(sourceId, targetId, proj);
@@ -272,7 +272,7 @@ export function renderEntities(container) {
     if (!cat) return;
     const name = prompt('Work item name:');
     if (!name) return;
-    api.workItems.create(project, { ai_category: cat.toLowerCase(), ai_name: name })
+    api.workItems.create(project, { category_ai: cat.toLowerCase(), name_ai: name })
       .then(() => { toast(`Created "${name}"`, 'success'); _loadWiPanel(project); })
       .catch(err => toast(err.message, 'error'));
   };
@@ -302,7 +302,7 @@ export function renderEntities(container) {
 
   // Drag from sub-row in top pane back to bottom panel (to unlink)
   window._wiSubRowDragStart = (e, id, name, cat) => {
-    _dragWiData = { id, ai_name: name, ai_category: cat };
+    _dragWiData = { id, name_ai: name, category_ai: cat };
     e.dataTransfer.effectAllowed = 'move';
     e.dataTransfer.setData('text/plain', id);
   };
@@ -330,7 +330,7 @@ export function renderEntities(container) {
     const proj = _plannerState.project;
     try {
       await api.workItems.patch(wi.id, proj, { tag_id_user: '' });
-      toast(`Unlinked "${wi.ai_name}"`, 'success');
+      toast(`Unlinked "${wi.name_ai}"`, 'success');
       _loadWiPanel(proj);
       _loadTagLinkedWorkItems(proj).catch(() => {});
     } catch(err) { toast('Unlink failed: ' + err.message, 'error'); }
@@ -440,7 +440,7 @@ async function _plannerSelectCat(catId, catName) {
 
 // ── Work Items bottom panel ────────────────────────────────────────────────────
 
-let _dragWiData = null;   // { id, ai_name, ai_category } — set while dragging a work item
+let _dragWiData = null;   // { id, name_ai, category_ai } — set while dragging a work item
 let _wiPanelItems = {};   // id → wi object, cache for bottom panel
 
 async function _loadWiPanel(project) {
@@ -655,9 +655,9 @@ function _renderWiPanel(items, project) {
   const LBL_USER = LBL_BASE + ';color:#4a90e2;border:1px solid #4a90e266;background:#4a90e212';   // blue — user
 
   const rows = sorted.map(wi => {
-    const icon = CAT_ICON[wi.ai_category] || '📋';
+    const icon = CAT_ICON[wi.category_ai] || '📋';
     const sc   = STATUS_C[wi.status_user] || '#888';
-    const desc = (wi.ai_desc || '').replace(/\n/g,' ').trim();
+    const desc = (wi.desc_ai || '').replace(/\n/g,' ').trim();
     // AI(EXISTS) — matched to an existing planner tag
     const aiTagColor = wi.ai_tag_color || '#27ae60';
     const aiTagLabel = wi.ai_tag_name
@@ -746,10 +746,10 @@ function _renderWiPanel(items, project) {
 
     return `<tr draggable="true"
         data-wi-id="${_esc(wi.id)}"
-        data-wi-name="${_esc(wi.ai_name)}"
-        ondragstart="window._wiBotDragStart(event,'${_esc(wi.id)}','${_esc(wi.ai_name)}','${_esc(wi.ai_category)}')"
+        data-wi-name="${_esc(wi.name_ai)}"
+        ondragstart="window._wiBotDragStart(event,'${_esc(wi.id)}','${_esc(wi.name_ai)}','${_esc(wi.category_ai)}')"
         ondragend="window._wiBotDragEnd(event)"
-        onclick="window._plannerOpenWorkItemDrawer('${_esc(wi.id)}','${_esc(wi.ai_category)}','${_esc(project)}')"
+        onclick="window._plannerOpenWorkItemDrawer('${_esc(wi.id)}','${_esc(wi.category_ai)}','${_esc(project)}')"
         style="border-bottom:1px solid var(--border);cursor:pointer;transition:background 0.1s"
         onmouseenter="this.style.background='var(--surface2)'"
         onmouseleave="this.style.background=''">
@@ -762,7 +762,7 @@ function _renderWiPanel(items, project) {
           <span style="flex-shrink:0;font-size:0.78rem">${icon}</span>
           ${wi.seq_num ? `<span style="font-size:0.58rem;color:var(--muted);flex-shrink:0">#${wi.seq_num}</span>` : ''}
           <span style="font-size:0.72rem;color:var(--text);overflow:hidden;text-overflow:ellipsis;
-                       white-space:nowrap;flex:1;min-width:0" title="${_esc(wi.ai_name)}">${_esc(wi.ai_name)}</span>
+                       white-space:nowrap;flex:1;min-width:0" title="${_esc(wi.name_ai)}">${_esc(wi.name_ai)}</span>
           <span style="font-size:0.56rem;color:${sc};background:${sc}1a;
                        padding:0 0.3rem;border-radius:6px;flex-shrink:0;white-space:nowrap">${wi.status_user||'active'}</span>
         </div>
@@ -807,7 +807,7 @@ function _renderWiPanel(items, project) {
 /** Load work items linked to tags in the current category, inject as sub-rows. */
 async function _loadTagLinkedWorkItems(project, catName) {
   try {
-    // Fetch all linked work items (no ai_category filter — a 'task' work item can be linked
+    // Fetch all linked work items (no category_ai filter — a 'task' work item can be linked
     // to a 'feature' tag; we rely on the DOM tr[data-tag-id] selector to scope to current view)
     const data = await api.workItems.list({ project });
     const linked = (data.work_items || []).filter(w => w.tag_id_user && !w.merged_into);
@@ -826,7 +826,7 @@ async function _loadTagLinkedWorkItems(project, catName) {
       // Insert sub-rows (in reverse so first item ends up first)
       [...wis].reverse().forEach(wi => {
         const sc = STATUS_UC[wi.st

### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index 35ca241..e2cf0af 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -58,9 +58,9 @@ _SQL_LIST_WORK_ITEMS_BASE = (
          WHERE project_id=%s AND merged_into IS NOT NULL
          GROUP BY 1
        )
-       SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
+       SELECT w.id, w.category_ai, w.name_ai, w.desc_ai,
               w.status_user, w.status_ai, w.acceptance_criteria_ai, w.action_items_ai,
-              w.code_summary, w.summary,
+              w.code_summary, w.summary_ai,
               w.tags, w.tags_ai, w.tag_id_user, w.tag_id_ai, w.source_event_id,
               w.merged_into, w.start_date,
               w.created_at, w.updated_at, w.seq_num,
@@ -70,7 +70,7 @@ _SQL_LIST_WORK_ITEMS_BASE = (
               COALESCE(cm_count.commit_count, 0) AS commit_count,
               COALESCE(mcount.cnt, 0) AS merge_count
        FROM mem_ai_work_items w
-       LEFT JOIN mng_tags_categories tc ON tc.client_id=1 AND tc.name=w.ai_category
+       LEFT JOIN mng_tags_categories tc ON tc.client_id=1 AND tc.name=w.category_ai
        LEFT JOIN ev_count ON ev_count.wi_id = w.id::text
        LEFT JOIN cm_count ON cm_count.wi_id = w.id::text
        LEFT JOIN mcount ON mcount.wi_id = w.id::text
@@ -82,8 +82,8 @@ _SQL_LIST_WORK_ITEMS_BASE = (
 _SQL_UNLINKED_WORK_ITEMS = """
     WITH wi AS (
         -- Base filter; join source event once to get session_id + event_type
-        SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
-               w.status_user, w.status_ai, w.summary, w.tags, w.tags_ai,
+        SELECT w.id, w.category_ai, w.name_ai, w.desc_ai,
+               w.status_user, w.status_ai, w.summary_ai, w.tags, w.tags_ai,
                w.start_date, w.created_at, w.updated_at, w.seq_num,
                w.tag_id_ai, w.source_event_id, w.project_id,
                e.event_type  AS src_event_type,
@@ -137,8 +137,8 @@ _SQL_UNLINKED_WORK_ITEMS = """
         WHERE project_id = %s AND merged_into IS NOT NULL
         GROUP BY 1
     )
-    SELECT wi.id, wi.ai_category, wi.ai_name, wi.ai_desc,
-           wi.status_user, wi.status_ai, wi.summary, wi.tags, wi.tags_ai,
+    SELECT wi.id, wi.category_ai, wi.name_ai, wi.desc_ai,
+           wi.status_user, wi.status_ai, wi.summary_ai, wi.tags, wi.tags_ai,
            wi.start_date, wi.created_at, wi.updated_at, wi.seq_num,
            wi.tag_id_ai,
            pt.name   AS ai_tag_name,
@@ -160,18 +160,18 @@ _SQL_UNLINKED_WORK_ITEMS = """
 
 _SQL_INSERT_WORK_ITEM = (
     """INSERT INTO mem_ai_work_items
-           (project_id, ai_category, ai_name, ai_desc,
+           (project_id, category_ai, name_ai, desc_ai,
             acceptance_criteria_ai, action_items_ai,
-            code_summary, summary, tags, status_user, status_ai, seq_num)
+            code_summary, summary_ai, tags, status_user, status_ai, seq_num)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s)
-       ON CONFLICT (project_id, ai_category, ai_name) DO NOTHING
-       RETURNING id, ai_name, ai_category, created_at, seq_num"""
+       ON CONFLICT (project_id, category_ai, name_ai) DO NOTHING
+       RETURNING id, name_ai, category_ai, created_at, seq_num"""
 )
 
 _SQL_GET_WORK_ITEM = (
-    """SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
+    """SELECT w.id, w.category_ai, w.name_ai, w.desc_ai,
               w.status_user, w.status_ai, w.acceptance_criteria_ai, w.action_items_ai,
-              w.code_summary, w.summary,
+              w.code_summary, w.summary_ai,
               w.tags, w.tag_id_user, w.tag_id_ai, w.source_event_id,
               w.created_at, w.updated_at, w.seq_num
        FROM mem_ai_work_items w
@@ -190,9 +190,9 @@ _SQL_DELETE_WORK_ITEM = (
 )
 
 _SQL_GET_WORK_ITEM_BY_SEQ = (
-    """SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
+    """SELECT w.id, w.category_ai, w.name_ai, w.desc_ai,
               w.status_user, w.status_ai, w.acceptance_criteria_ai, w.action_items_ai,
-              w.code_summary, w.summary,
+              w.code_summary, w.summary_ai,
               w.tags, w.tag_id_user, w.tag_id_ai,
               w.created_at, w.updated_at, w.seq_num
        FROM mem_ai_work_items w
@@ -284,17 +284,17 @@ async def _trigger_memory_regen(project: str) -> None:
 
 async def _embed_work_item(
     project_id: int, item_id: str,
-    ai_name: str, ai_desc: str, summary: str,
+    name_ai: str, desc_ai: str, summary_ai: str,
     code_summary: str = "",
 ) -> None:
     """Embed work item content and store the vector on the row.
-    Embedding = ai_name + ai_desc + summary + code_summary.
+    Embedding = name_ai + desc_ai + summary_ai + code_summary.
     Used for: (1) semantic search, (2) cosine-similarity matching to planner_tags.
     planner_tags.embedding = summary + action_items_ai → same space, enabling cross-table match.
     """
     try:
         from memory.memory_embedding import _embed
-        text = f"{ai_name} {ai_desc} {summary} {code_summary}".strip()
+        text = f"{name_ai} {desc_ai} {summary_ai} {code_summary}".strip()
         vec = await _embed(text)
         if vec and db.is_available():
             vec_str = f"[{','.join(str(x) for x in vec)}]"
@@ -448,16 +448,16 @@ async def _backlink_tag_to_events(project_id: int, work_item_id: str, tag_id_use
 # ── Models ────────────────────────────────────────────────────────────────────
 
 class WorkItemCreate(BaseModel):
-    ai_category:         str
-    ai_name:             str
-    ai_desc:             str = ""
+    category_ai:         str
+    name_ai:             str
+    desc_ai:             str = ""
     project:             Optional[str] = None
     status_user:         str = "active"
     status_ai:           str = "active"
     acceptance_criteria_ai: str = ""
     action_items_ai:        str = ""
     code_summary:        str = ""
-    summary:             str = ""
+    summary_ai:          str = ""
     t

### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/backend/routers/route_projects.py b/backend/routers/route_projects.py
index e3d9357..08e17da 100644
--- a/backend/routers/route_projects.py
+++ b/backend/routers/route_projects.py
@@ -2022,6 +2022,7 @@ async def generate_memory(project_name: str):
             asyncio.create_task(_process_unembedded_items_messages(project_name))
             asyncio.create_task(_run_work_item_extraction(project_name))
             asyncio.create_task(_run_feature_snapshots(project_name))
+            asyncio.create_task(_run_promote_all_work_items(project_name))
         except Exception:
             pass
 
@@ -2234,6 +2235,18 @@ async def _run_feature_snapshots(project: str) -> None:
         _log.debug(f"_run_feature_snapshots failed: {e}")
 
 
+async def _run_promote_all_work_items(project: str) -> None:
+    """Promote all active work items (refresh AI text fields + status)."""
+    if not db.is_available():
+        return
+    try:
+        from memory.memory_promotion import MemoryPromotion
+        result = await MemoryPromotion().promote_all_work_items(project)
+        logging.getLogger(__name__).debug(f"_run_promote_all_work_items: {result}")
+    except Exception as e:
+        logging.getLogger(__name__).debug(f"_run_promote_all_work_items failed: {e}")
+
+
 async def _run_work_item_extraction(project: str) -> None:
     """Extract work items from recent unprocessed events."""
     if not db.is_available():


### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/backend/prompts/memory/work_items/work_item_promotion.md b/backend/prompts/memory/work_items/work_item_promotion.md
index 57410a5..a9368f4 100644
--- a/backend/prompts/memory/work_items/work_item_promotion.md
+++ b/backend/prompts/memory/work_items/work_item_promotion.md
@@ -1,4 +1,19 @@
-Given a work item's name, description, lifecycle status, acceptance criteria, and implementation plan,
-produce a 2-4 sentence summary capturing: what the item is, current status, and any notable progress.
-Return JSON only: {"summary": "...", "status": "<lifecycle_status>"}
-No preamble, no markdown fences.
+Given a work item's name, description, current status, acceptance criteria, action items,
+and all linked events/commits as context, produce a structured PM update.
+
+Return JSON only:
+{
+  "desc_ai": "1-2 sentence explanation of what this item is and why it matters",
+  "acceptance_criteria_ai": "- [ ] Specific, testable outcome\n- [ ] ...",
+  "action_items_ai": "- Concrete next step\n- ...",
+  "summary_ai": "2-4 sentence PM digest: what was done, what remains, and test coverage status",
+  "status_ai": "active|in_progress|done"
+}
+
+Rules:
+- desc_ai: short, factual. What it is.
+- acceptance_criteria_ai: 1-3 bullet lines starting with "- [ ]". Testable.
+- action_items_ai: 1-4 bullet lines starting with "-". Concrete imperative phrases.
+- summary_ai: PM-facing. Mention recent progress, open gaps, and whether tested.
+- status_ai: reflect actual progress from linked events.
+- No preamble, no markdown fences, return ONLY valid JSON.


### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/backend/memory/memory_tagging.py b/backend/memory/memory_tagging.py
index ccd29bb..c1755fa 100644
--- a/backend/memory/memory_tagging.py
+++ b/backend/memory/memory_tagging.py
@@ -300,7 +300,7 @@ class MemoryTagging:
         with db.conn() as conn:
             with conn.cursor() as cur:
                 cur.execute("""
-                    SELECT id, ai_name, ai_desc, summary, ai_category
+                    SELECT id, name_ai, desc_ai, summary_ai, category_ai
                     FROM mem_ai_work_items WHERE id = %s
                 """, (work_item_id,))
                 row = cur.fetchone()


### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/backend/memory/memory_promotion.py b/backend/memory/memory_promotion.py
index a0e0ff4..8c4da4e 100644
--- a/backend/memory/memory_promotion.py
+++ b/backend/memory/memory_promotion.py
@@ -45,20 +45,45 @@ _SQL_GET_TAG_ID = """
 """
 
 _SQL_GET_WORK_ITEM = """
-    SELECT wi.id, wi.ai_name, wi.ai_desc, wi.status_user, wi.acceptance_criteria_ai
+    SELECT wi.id, wi.name_ai, wi.desc_ai, wi.status_user, wi.acceptance_criteria_ai
     FROM mem_ai_work_items wi
     WHERE wi.project_id=%s
     ORDER BY wi.created_at DESC LIMIT 10
 """
 
 _SQL_GET_WORK_ITEM_BY_NAME = """
-    SELECT wi.id, wi.ai_name, wi.ai_desc, wi.status_user, wi.acceptance_criteria_ai,
+    SELECT wi.id, wi.name_ai, wi.desc_ai, wi.status_user, wi.acceptance_criteria_ai,
            wi.action_items_ai, wi.status_ai, wi.tag_id_user
     FROM mem_ai_work_items wi
-    WHERE wi.project_id=%s AND wi.ai_name=%s
+    WHERE wi.project_id=%s AND wi.name_ai=%s
     LIMIT 1
 """
 
+_SQL_PROMOTE_WORK_ITEM_FIELDS = """
+    UPDATE mem_ai_work_items SET
+        desc_ai                = CASE WHEN %s != '' THEN %s ELSE desc_ai END,
+        acceptance_criteria_ai = CASE WHEN %s != '' THEN %s ELSE acceptance_criteria_ai END,
+        action_items_ai        = CASE WHEN %s != '' THEN %s ELSE action_items_ai END,
+        summary_ai             = CASE WHEN %s != '' THEN %s ELSE summary_ai END,
+        updated_at             = NOW()
+    WHERE id=%s AND project_id=%s
+"""
+
+_SQL_LIST_ACTIVE_WORK_ITEMS = """
+    SELECT name_ai FROM mem_ai_work_items
+    WHERE project_id=%s AND status_user NOT IN ('done', 'archived')
+    ORDER BY created_at DESC
+    LIMIT 50
+"""
+
+_SQL_GET_LINKED_EVENTS = """
+    SELECT summary, action_items
+    FROM mem_ai_events
+    WHERE work_item_id=%s::uuid AND summary IS NOT NULL AND summary != ''
+    ORDER BY created_at DESC
+    LIMIT 5
+"""
+
 _SQL_UPDATE_WORK_ITEM_STATUS_AI = """
     UPDATE mem_ai_work_items SET status_ai=%s, updated_at=NOW()
     WHERE id=%s AND project_id=%s
@@ -140,13 +165,13 @@ _SQL_UPDATE_EVENT_AI_TAGS = """
 
 _SQL_INSERT_EXTRACTED_WORK_ITEM = """
     INSERT INTO mem_ai_work_items
-        (project_id, ai_category, ai_name, ai_desc,
+        (project_id, category_ai, name_ai, desc_ai,
          acceptance_criteria_ai, action_items_ai, tags,
          source_event_id, seq_num)
     VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::uuid,
             (SELECT COALESCE(MAX(seq_num),0)+1 FROM mem_ai_work_items WHERE project_id=%s))
-    ON CONFLICT (project_id, ai_category, ai_name) DO UPDATE SET
-        ai_desc              = EXCLUDED.ai_desc,
+    ON CONFLICT (project_id, category_ai, name_ai) DO UPDATE SET
+        desc_ai              = EXCLUDED.desc_ai,
         acceptance_criteria_ai = CASE WHEN EXCLUDED.acceptance_criteria_ai != ''
                                       THEN EXCLUDED.acceptance_criteria_ai
                                       ELSE mem_ai_work_items.acceptance_criteria_ai END,
@@ -249,11 +274,11 @@ class MemoryPromotion:
     """
 
     async def promote_work_item(
-        self, project: str, tag_name: str
+        self, project: str, name_ai: str
     ) -> Optional[dict]:
         """
-        Summarise the work item associated with tag_name into a 2-4 sentence digest.
-        Returns {summary, status} or None on failure.
+        Refresh all 4 AI text fields for a work item from its linked events + commits.
+        Returns {work_item_id, name_ai, summary_ai, status_ai} or None on failure.
         """
         if not db.is_available():
             return None
@@ -261,54 +286,123 @@ class MemoryPromotion:
         project_id = db.get_or_create_project_id(project)
         with db.conn() as conn:
             with conn.cursor() as cur:
-                cur.execute(_SQL_GET_WORK_ITEM_BY_NAME, (project_id, tag_name))
+                cur.execute(_SQL_GET_WORK_ITEM_BY_NAME, (project_id, name_ai))
                 row = cur.fetchone()
 
         if not row:
-            log.debug(f"promote_work_item: no work item found for '{tag_name}'")
+            log.debug(f"promote_work_item: no work item found for '{name_ai}'")
             return None
 
         wi_id, wi_name, desc, status_user, ac, action_items, status_ai, tag_id_user = row
 
+        # Fetch up to 5 linked event summaries for richer context
+        linked_events: list[str] = []
+        try:
+            with db.conn() as conn:
+                with conn.cursor() as cur:
+                    cur.execute(_SQL_GET_LINKED_EVENTS, (str(wi_id),))
+                    for ev_summary, ev_actions in cur.fetchall():
+                        parts = [p for p in [ev_summary, ev_actions] if p and p.strip()]
+                        if parts:
+                            linked_events.append(" | ".join(parts))
+        except Exception as e:
+            log.debug(f"promote_work_item: linked events fetch error: {e}")
+
         system_prompt = _prompts.content("work_item_promotion") or (
-            "Given a work item, produce a 2-4 sentence summary capturing what it is, "
-            "current status, and any notable progress. "
-            "Return JSON only: {\"summary\": \"...\", \"status_ai\": \"active|in_progress|done\"}"
+            "Given a work item, produce a structured PM update. "
+            "Return JSON only: {\"desc_ai\": \"...\", \"acceptance_criteria_ai\": \"...\", "
+            "\"action_items_ai\": \"...\", \"summary_ai\": \"...\", "
+            "\"status_ai\": \"active|in_progress|done\"}"
         )
 
+        events_section = ""
+        if linked_events:
+            events_section = "\n\nLinked Events (recent):\n" + "\n".join(
+                f"- {e[:200]}" for e in linked_events
+            )
+
         user_msg = (
             f"Work Item: {wi_name}\n"
             f"User Status: {status_user}\n"
             f"Description: {desc or '(none)'}\n"
             f"Acceptance Criteria:\n{ac or '(none)'}\n"
             f"Action Items:\n{action_items or '(none)'}"
+            

## AI Synthesis

**[2026-03-14]** `entities.js, route_work_items.py, route_projects.py` — Completed work item column schema refactoring to enforce consistent naming: ai_name→name_ai, ai_category→category_ai, ai_desc→desc_ai, summary→summary_ai. Updated all frontend references in drag-and-drop handlers, work item creation, and panel rendering. Updated backend SQL queries, model definitions, and embedding logic to use new column names.

**[2026-03-14]** `route_projects.py` — Integrated _run_promote_all_work_items() into the /memory command execution pipeline. New memory promotion task refreshes AI text fields and status for all active work items during memory generation, ensuring work item data stays current.

**[2026-03-14]** `entities.js` — Secondary AI tag workflow now stores confirmed metadata (doc_type/phase/component) in ai_tags.confirmed[] array. Tagged work items remain visible with permanent chip indicators instead of deletion, improving audit trail and re-evaluation capability.

**[2026-03-14]** `entities.js` — Enhanced work item UI with _wiRowLoading() CSS pulsing animation during async delete/approve/dismiss operations. Error state recovery integrated into tag-linked and unlinked panels for better UX feedback.

**[2026-03-14]** `entities.js` — Improved AI tag suggestion UX: clickable ✓ button creates missing ai_suggestion tags with category inference. Tooltip messaging upgraded from 'No existing tag' to 'Does not exist yet' for clarity on tag creation workflow.