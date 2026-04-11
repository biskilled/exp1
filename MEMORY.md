# Project Memory — aicli
_Generated: 2026-04-11 13:29 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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
- Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; source_event_id pivot for session-based aggregation
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
- Secondary AI tags stored in ai_tags.confirmed[] array (metadata for doc_type/feature/phase); primary tag_id links work item to category, secondary tags remain as chips
- Work item counters: prompt_count (raw prompts in source session), event_count (prompt_batch/session_summary events), commit_count (distinct commits per session)
- Session tagging: /stag command (replaced /tag due to Claude Code skill conflict) with immediate tag propagation via log_user_prompt.sh reading .agent-context
- UI state management: _wiPanelItems object-keyed cache; _renderWiPanel for unlinked items; tag-linked items persist across category switches

## In Progress

- Work item row loading states: _wiRowLoading() helper with CSS pulsing animation during async operations (delete, approve, dismiss); integrated into _wiDeleteLinked, _wiUnlink, _wiPanelDelete, _wiPanelApproveTag, _wiPanelRemoveTag handlers
- Secondary AI tag workflow refinement: _wiSecApprove now stores confirmed metadata (doc_type/phase/component) in ai_tags.confirmed[] array instead of removing items from panel; items remain visible with permanent chip indicators
- Work item panel consistency: error handling improved to restore loading state on catch; toast messaging clarified for approve (link to tag), remove (clear metadata), and secondary approve (save as metadata)
- Tag-linked work item refresh: _loadTagLinkedWorkItems reloads after approve/reject operations; planner table updates to reflect linked/unlinked status changes when category is selected
- AI tag suggestion UX: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip messaging improved from 'No existing tag' to 'Does not exist yet'
- Work item deletion UI: confirmation dialogs + loading indicators for _wiDeleteLinked (tag-linked panel) and _wiPanelDelete (unlinked panel); delete operations remove items and refresh counts

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

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index b73b1fd..67d006f 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Skill naming conflict resolution: /tag command conflicted with Claude Code reserved skill name; created /stag as replacement with identical functionality and immediate availability
-- Work item deletion UI: _wiDeleteLinked handler in entities.js with confirmation dialog; delete button appears in tag-linked work item panel with opacity toggle hover effect
+- Secondary AI tag UX refinement: _wiSecApprove stores doc_type/feature/phase/bug/task tags in ai_tags.confirmed[] array; items remain visible in work item list with ✓ button showing as permanent chip indicator
+- Work item deletion UI: implemented _wiDeleteLinked handler with confirmation dialog; delete button appears in tag-linked work items panel with opacity toggle hover effect
 - Tag creation with auto-link workflow: _wiPanelCreateTag creates new tags without confirmation, auto-links work item, refreshes tag cache + planner table + category tag list
-- AI suggestion chips UX refinement: added clickable ✓ button to create missing ai_suggestion tags with category inference; improved tooltip UX
-- Tag confirmation/deletion UX clarification: investigate current confirm/delete button behavior for AI tags; accept should trigger 'remove' rather than separate 'confirm' action
-- Tag-linked work item refresh: after approve/reject/create operations, _loadTagLinkedWorkItems reloads to reflect linked/unlinked status changes in planner view
+- AI suggestion chips UX: added clickable ✓ button to create missing ai_suggestion tags with category inference; improved tooltip messaging for non-existent tags
+- Tag-linked work item refresh: _loadTagLinkedWorkItems reloads after approve/reject/create operations to reflect linked/unlinked status changes in planner view
+- Work item persistence across sessions: ensuring tag-linked and newly-created work items remain accessible across tag switches and session changes


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index ef5d2f0..e11df9a 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -183,8 +183,8 @@ export function renderEntities(container) {
       const msg = `${agg.commit_count || 0} commits · ${(agg.all_files || []).length} files`;
       toast(`Extracted · ${msg}`, 'success');
       if (statusEl) statusEl.textContent = msg;
-      // Refresh ai_tags display
-      const aiTagsEl = document.getElementById(`wi-ai-tags-${id}`);
+      // Refresh tags_ai display
+      const tagsAiEl = document.getElementById(`wi-ai-tags-${id}`);
       if (aiTagsEl) {
         const cs = r.code_summary || {};
         const tc = r.test_coverage || {};
@@ -255,7 +255,7 @@ export function renderEntities(container) {
   window._wiUnlink = async (id, proj) => {
     _wiRowLoading(id, true);
     try {
-      await api.workItems.patch(id, proj, { tag_id: '' });
+      await api.workItems.patch(id, proj, { tag_id_user: '' });
       toast('Unlinked', 'success');
       _loadWiPanel(proj);
       const { selectedCatName } = _plannerState;
@@ -329,7 +329,7 @@ export function renderEntities(container) {
     _dragWiData = null;
     const proj = _plannerState.project;
     try {
-      await api.workItems.patch(wi.id, proj, { tag_id: '' });
+      await api.workItems.patch(wi.id, proj, { tag_id_user: '' });
       toast(`Unlinked "${wi.ai_name}"`, 'success');
       _loadWiPanel(proj);
       _loadTagLinkedWorkItems(proj).catch(() => {});
@@ -567,10 +567,10 @@ function _renderWiPanel(items, project) {
 
   window._wiPanelApproveTag = async (id, proj) => {
     const wi = _wiPanelItems[id];
-    if (!wi || !wi.ai_tag_id) return;
+    if (!wi || !wi.tag_id_ai) return;
     _wiRowLoading(id, true);
     try {
-      await api.workItems.patch(id, proj, { tag_id: wi.ai_tag_id });
+      await api.workItems.patch(id, proj, { tag_id_user: wi.tag_id_ai });
       delete _wiPanelItems[id];
       const remaining = Object.values(_wiPanelItems);
       _renderWiPanel(remaining, proj);
@@ -585,13 +585,13 @@ function _renderWiPanel(items, project) {
   window._wiPanelRemoveTag = async (id, proj) => {
     _wiRowLoading(id, true);
     try {
-      await api.workItems.patch(id, proj, { ai_tag_id: '', ai_tags: {} });
+      await api.workItems.patch(id, proj, { tag_id_ai: '', tags_ai: {} });
       if (_wiPanelItems[id]) {
-        _wiPanelItems[id].ai_tag_id = null;
+        _wiPanelItems[id].tag_id_ai = null;
         _wiPanelItems[id].ai_tag_name = null;
         _wiPanelItems[id].ai_tag_category = null;
         _wiPanelItems[id].ai_tag_color = null;
-        _wiPanelItems[id].ai_tags = {};
+        _wiPanelItems[id].tags_ai = {};
       }
       _renderWiPanel(Object.values(_wiPanelItems), proj);
     } catch(e) { toast('Remove failed: ' + e.message, 'error'); _wiRowLoading(id, false); }
@@ -602,28 +602,28 @@ function _renderWiPanel(items, project) {
   window._wiSecApprove = async (id, proj, tagId, tagName, tagCat) => {
     _wiRowLoading(id, true);
     try {
-      const current = (_wiPanelItems[id]?.ai_tags) || {};
+      const current = (_wiPanelItems[id]?.tags_ai) || {};
       const confirmed = Array.isArray(current.confirmed) ? current.confirmed : [];
       const updated = {
         ...current,
         secondary: null,
         confirmed: [...confirmed, { tag_id: tagId, tag_name: tagName, category: tagCat }],
       };
-      await api.workItems.patch(id, proj, { ai_tags: updated });
-      if (_wiPanelItems[id]) _wiPanelItems[id].ai_tags = updated;
+      await api.workItems.patch(id, proj, { tags_ai: updated });
+      if (_wiPanelItems[id]) _wiPanelItems[id].tags_ai = updated;
       _renderWiPanel(Object.values(_wiPanelItems), proj);
       toast(`Saved ${tagCat ? tagCat + ':' : ''}${tagName || ''} as metadata`, 'success');
     } catch(e) { toast('Failed: ' + e.message, 'error'); _wiRowLoading(id, false); }
   };
 
-  // Secondary AI suggestion: dismiss = clear ai_tags.secondary only, item stays in list
+  // Secondary AI suggestion: dismiss = clear tags_ai.secondary only, item stays in list
   window._wiSecDismiss = async (id, proj) => {
     _wiRowLoading(id, true);
     try {
-      const current = (_wiPanelItems[id]?.ai_tags) || {};
+      const current = (_wiPanelItems[id]?.tags_ai) || {};
       const updated = { ...current, secondary: null };
-      await api.workItems.patch(id, proj, { ai_tags: updated });
-      if (_wiPanelItems[id]) _wiPanelItems[id].ai_tags = updated;
+      await api.workItems.patch(id, proj, { tags_ai: updated });
+      if (_wiPanelItems[id]) _wiPanelItems[id].tags_ai = updated;
       _renderWiPanel(Object.values(_wiPanelItems), proj);
     } catch(e) { toast('Dismiss failed: ' + e.message, 'error'); _wiRowLoading(id, false); }
   };
@@ -635,7 +635,7 @@ function _renderWiPanel(items, project) {
       const cats = await api.tags.categories.list(proj);
       const catObj = cats.find(c => c.name === catLabel) || cats.find(c => c.name === 'task') || cats[0];
       const newTag = await api.tags.create({ name: tagName, project: proj, category_id: catObj?.id });
-      await api.workItems.patch(id, proj, { tag_id: newTag.id });
+      await api.workItems.patch(id, proj, { tag_id_user: newTag.id });
       delete _wiPanelItems[id];
       const remaining = Object.values(_wiPanelItems);
       _renderWiPanel(remaining, proj);
@@ -663,9 +663,9 @@ function _renderWiPanel(items, project) {
     const aiTagLabel = wi.ai_tag_name
       ? (wi.ai_tag_category ? wi.ai_tag_category + ':' + wi.ai_tag_name : wi.ai_tag_name)
       : '';
-    // AI(NEW) — stored in ai_tags.suggested_new + suggested_category
-    const aiNew = (wi.ai_tags && wi.ai_tags.suggested_new) ? wi.ai_tags.suggested_new : '';
-    const aiNewCat = (wi.ai_tags && wi.ai_tags.suggested_category) ? wi.ai_tags.suggested_category : 'task';
+    // AI(NEW) — stored in tags_ai.suggested_new + suggested_category
+    const aiN

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index d7b3e98..fbb714e 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -5,7 +5,7 @@ Endpoints:
     GET    /work-items                    ?project=&category=&status=
     GET    /work-items/unlinked           ?project=
     POST   /work-items                    {ai_category, ai_name, ai_desc, ...}
-    PATCH  /work-items/{id}               {ai_name?, ai_desc?, tag_id?, ...}
+    PATCH  /work-items/{id}               {ai_name?, ai_desc?, tag_id_user?, ...}
     DELETE /work-items/{id}
     GET    /work-items/{id}/interactions  ?limit=20
     GET    /work-items/number/{seq_num}
@@ -32,6 +32,8 @@ from data.dl_seq import next_seq
 
 _SQL_LIST_WORK_ITEMS_BASE = (
     """WITH ev_count AS (
+         -- Count all events linked to each work item via work_item_id FK
+         -- (populated by m022 backfill + ongoing backlink in memory_promotion.py)
          SELECT work_item_id::text AS wi_id,
                 COUNT(*) AS event_count,
                 COUNT(*) FILTER (WHERE event_type = 'prompt_batch') AS prompt_count
@@ -40,10 +42,14 @@ _SQL_LIST_WORK_ITEMS_BASE = (
          GROUP BY 1
        ),
        cm_count AS (
-         SELECT e.work_item_id::text AS wi_id, COUNT(*) AS commit_count
-         FROM mem_mrr_commits c
-         JOIN mem_ai_events e ON e.id = c.event_id
-         WHERE c.project_id=%s AND e.work_item_id IS NOT NULL
+         -- Commits in the same session as linked events (session-based, consistent
+         -- with _SQL_UNLINKED_WORK_ITEMS; avoids relying on c.event_id which is sparse)
+         SELECT e.work_item_id::text AS wi_id, COUNT(DISTINCT c.commit_hash) AS commit_count
+         FROM mem_ai_events e
+         JOIN mem_mrr_commits c ON c.project_id = e.project_id
+                               AND c.session_id = e.session_id
+                               AND c.session_id IS NOT NULL
+         WHERE e.project_id=%s AND e.work_item_id IS NOT NULL
          GROUP BY 1
        ),
        mcount AS (
@@ -53,9 +59,9 @@ _SQL_LIST_WORK_ITEMS_BASE = (
          GROUP BY 1
        )
        SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
-              w.status_user, w.status_ai, w.acceptance_criteria, w.action_items,
-              w.requirements, w.code_summary, w.summary,
-              w.tags, w.ai_tags, w.tag_id, w.ai_tag_id, w.source_event_id,
+              w.status_user, w.status_ai, w.acceptance_criteria_ai, w.action_items_ai,
+              w.code_summary, w.summary,
+              w.tags, w.tags_ai, w.tag_id_user, w.tag_id_ai, w.source_event_id,
               w.merged_into, w.start_date,
               w.created_at, w.updated_at, w.seq_num,
               tc.color, tc.icon,
@@ -77,15 +83,15 @@ _SQL_UNLINKED_WORK_ITEMS = """
     WITH wi AS (
         -- Base filter; join source event once to get session_id + event_type
         SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
-               w.status_user, w.status_ai, w.requirements, w.summary, w.tags, w.ai_tags,
+               w.status_user, w.status_ai, w.summary, w.tags, w.tags_ai,
                w.start_date, w.created_at, w.updated_at, w.seq_num,
-               w.ai_tag_id, w.source_event_id, w.project_id,
+               w.tag_id_ai, w.source_event_id, w.project_id,
                e.event_type  AS src_event_type,
                e.session_id  AS src_session_id,
                e.source_id   AS src_source_id
         FROM mem_ai_work_items w
         LEFT JOIN mem_ai_events e ON e.id = w.source_event_id
-        WHERE w.project_id = %s AND w.tag_id IS NULL AND w.status_user != 'done'
+        WHERE w.project_id = %s AND w.tag_id_user IS NULL AND w.status_user != 'done'
     ),
     -- prompt_batch/session_summary events in the source session
     -- (all items extracted from the same batch share this session → all get same count)
@@ -132,9 +138,9 @@ _SQL_UNLINKED_WORK_ITEMS = """
         GROUP BY 1
     )
     SELECT wi.id, wi.ai_category, wi.ai_name, wi.ai_desc,
-           wi.status_user, wi.status_ai, wi.requirements, wi.summary, wi.tags, wi.ai_tags,
+           wi.status_user, wi.status_ai, wi.summary, wi.tags, wi.tags_ai,
            wi.start_date, wi.created_at, wi.updated_at, wi.seq_num,
-           wi.ai_tag_id,
+           wi.tag_id_ai,
            pt.name   AS ai_tag_name,
            ptc.name  AS ai_tag_category,
            ptc.color AS ai_tag_color,
@@ -143,7 +149,7 @@ _SQL_UNLINKED_WORK_ITEMS = """
            COALESCE(prompt_ct.cnt, 0) AS prompt_count,
            COALESCE(commit_ct.cnt, 0) AS commit_count
     FROM wi
-    LEFT JOIN planner_tags        pt  ON pt.id  = wi.ai_tag_id
+    LEFT JOIN planner_tags        pt  ON pt.id  = wi.tag_id_ai
     LEFT JOIN mng_tags_categories ptc ON ptc.id = pt.category_id
     LEFT JOIN event_ct  ON event_ct.wi_id  = wi.id::text
     LEFT JOIN prompt_ct ON prompt_ct.wi_id = wi.id::text
@@ -155,18 +161,18 @@ _SQL_UNLINKED_WORK_ITEMS = """
 _SQL_INSERT_WORK_ITEM = (
     """INSERT INTO mem_ai_work_items
            (project_id, ai_category, ai_name, ai_desc,
-            requirements, acceptance_criteria, action_items,
+            acceptance_criteria_ai, action_items_ai,
             code_summary, summary, tags, status_user, status_ai, seq_num)
-       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
+       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (project_id, ai_category, ai_name) DO NOTHING
        RETURNING id, ai_name, ai_category, created_at, seq_num"""
 )
 
 _SQL_GET_WORK_ITEM = (
     """SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
-              w.status_user, w.status_ai, w.acceptance_criteria, w.action_items,
-              w.requirements, w.code_summary, w.summary,
-              w.tags, w.tag_id, w.ai_tag_id, w.source_event_id,
+              w.status_user, w.status_ai, w.acceptance_criteria_ai, w.action_items_ai,
+              w.code_summary, w.summary,
+              w.ta

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/backend/memory/memory_tagging.py b/backend/memory/memory_tagging.py
index ced3489..ccd29bb 100644
--- a/backend/memory/memory_tagging.py
+++ b/backend/memory/memory_tagging.py
@@ -216,7 +216,7 @@ class MemoryTagging:
         """3-level matching: exact name → semantic (>0.85 auto) → Claude judgment (0.70–0.85).
 
         Returns list of dicts: {tag_id, relation, confidence}.
-        Best match is auto-persisted to mem_ai_work_items.ai_tag_id.
+        Best match is auto-persisted to mem_ai_work_items.tag_id_ai.
         """
         wi = self._load_work_item(work_item_id)
         if not wi:
@@ -226,7 +226,7 @@ class MemoryTagging:
         tag = self._find_exact_tag(project, wi['name'])
         if tag:
             result = [{'tag_id': tag['id'], 'relation': 'exact', 'confidence': 1.0}]
-            self._persist_ai_tag_id(work_item_id, tag['id'])
+            self._persist_tag_id_ai(work_item_id, tag['id'])
             return result
 
         # Level 2 — semantic similarity
@@ -273,26 +273,26 @@ class MemoryTagging:
             except Exception:
                 pass
 
-        # Persist best match to ai_tag_id (highest confidence)
+        # Persist best match to tag_id_ai (highest confidence)
         if results:
             best = max(results, key=lambda r: r.get('confidence', 0))
             if best.get('tag_id'):
-                self._persist_ai_tag_id(work_item_id, best['tag_id'])
+                self._persist_tag_id_ai(work_item_id, best['tag_id'])
 
         return results
 
-    def _persist_ai_tag_id(self, work_item_id: str, tag_id: str) -> None:
-        """Update ai_tag_id on the work item (AI suggestion only — never overwrites tag_id)."""
+    def _persist_tag_id_ai(self, work_item_id: str, tag_id: str) -> None:
+        """Update tag_id_ai on the work item (AI suggestion only — never overwrites tag_id)."""
         try:
             with db.conn() as conn:
                 with conn.cursor() as cur:
                     cur.execute(
-                        "UPDATE mem_ai_work_items SET ai_tag_id=%s::uuid, updated_at=NOW() "
-                        "WHERE id=%s::uuid AND ai_tag_id IS DISTINCT FROM %s::uuid",
+                        "UPDATE mem_ai_work_items SET tag_id_ai=%s::uuid, updated_at=NOW() "
+                        "WHERE id=%s::uuid AND tag_id_ai IS DISTINCT FROM %s::uuid",
                         (tag_id, work_item_id, tag_id),
                     )
         except Exception as e:
-            log.debug(f"_persist_ai_tag_id error: {e}")
+            log.debug(f"_persist_tag_id_ai error: {e}")
 
     # ── Private helpers ─────────────────────────────────────────────────────
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/backend/memory/memory_promotion.py b/backend/memory/memory_promotion.py
index d2d5dee..79e20b6 100644
--- a/backend/memory/memory_promotion.py
+++ b/backend/memory/memory_promotion.py
@@ -45,15 +45,15 @@ _SQL_GET_TAG_ID = """
 """
 
 _SQL_GET_WORK_ITEM = """
-    SELECT wi.id, wi.ai_name, wi.ai_desc, wi.status_user, wi.acceptance_criteria
+    SELECT wi.id, wi.ai_name, wi.ai_desc, wi.status_user, wi.acceptance_criteria_ai
     FROM mem_ai_work_items wi
     WHERE wi.project_id=%s
     ORDER BY wi.created_at DESC LIMIT 10
 """
 
 _SQL_GET_WORK_ITEM_BY_NAME = """
-    SELECT wi.id, wi.ai_name, wi.ai_desc, wi.status_user, wi.acceptance_criteria,
-           wi.action_items, wi.status_ai, wi.tag_id
+    SELECT wi.id, wi.ai_name, wi.ai_desc, wi.status_user, wi.acceptance_criteria_ai,
+           wi.action_items_ai, wi.status_ai, wi.tag_id_user
     FROM mem_ai_work_items wi
     WHERE wi.project_id=%s AND wi.ai_name=%s
     LIMIT 1
@@ -254,7 +254,7 @@ class MemoryPromotion:
             log.debug(f"promote_work_item: no work item found for '{tag_name}'")
             return None
 
-        wi_id, wi_name, desc, status_user, ac, action_items, status_ai, tag_id = row
+        wi_id, wi_name, desc, status_user, ac, action_items, status_ai, tag_id_user = row
 
         system_prompt = _prompts.content("work_item_promotion") or (
             "Given a work item, produce a 2-4 sentence summary capturing what it is, "
@@ -672,12 +672,17 @@ class MemoryPromotion:
                             if row:
                                 wi_id = str(row[0])
                                 created += 1
-                                # Link event → first work item only (don't overwrite if already set)
-                                cur.execute(
-                                    "UPDATE mem_ai_events SET work_item_id=%s::uuid"
-                                    " WHERE id=%s::uuid AND work_item_id IS NULL",
-                                    (wi_id, str(ev_id)),
-                                )
+                                # Backlink ALL events in the same session → one-to-many relationship
+                                # Events without work_item_id get assigned to this work item.
+                                cur.execute("""
+                                    UPDATE mem_ai_events
+                                    SET work_item_id = %s::uuid
+                                    WHERE session_id = (
+                                        SELECT session_id FROM mem_ai_events WHERE id = %s::uuid
+                                    )
+                                      AND project_id = %s
+                                      AND work_item_id IS NULL
+                                """, (wi_id, str(ev_id), project_id))
                                 # Queue AI tag matching for the new work item
                                 try:
                                     import asyncio as _aio


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/backend/memory/memory_planner.py b/backend/memory/memory_planner.py
index bf3ea5e..6746c72 100644
--- a/backend/memory/memory_planner.py
+++ b/backend/memory/memory_planner.py
@@ -36,10 +36,10 @@ _SQL_GET_TAG = """
 
 _SQL_GET_WORK_ITEMS = """
     SELECT wi.id, wi.ai_name, wi.ai_desc, wi.status_user, wi.status_ai,
-           wi.acceptance_criteria, wi.action_items, wi.summary,
-           wi.requirements, wi.seq_num, wi.start_date
+           wi.acceptance_criteria_ai, wi.action_items_ai, wi.summary,
+           wi.seq_num, wi.start_date
     FROM mem_ai_work_items wi
-    WHERE wi.tag_id = %s::uuid AND wi.project_id = %s
+    WHERE wi.tag_id_user = %s::uuid AND wi.project_id = %s
       AND wi.merged_into IS NULL
     ORDER BY wi.created_at
 """
@@ -66,7 +66,7 @@ _SQL_UPDATE_TAG = """
 
 _SQL_UPDATE_WORK_ITEM = """
     UPDATE mem_ai_work_items
-    SET action_items = %s, acceptance_criteria = %s, summary = %s, updated_at = NOW()
+    SET action_items_ai = %s, acceptance_criteria_ai = %s, summary = %s, updated_at = NOW()
     WHERE id = %s::uuid AND project_id = %s
 """
 
@@ -314,9 +314,9 @@ class MemoryPlanner:
             lines.append(f"ID: {wi['id']}")
             lines.append(f"Status: {wi.get('status_user', 'active')}")
             lines.append(f"Description: {wi.get('ai_desc') or '—'}")
-            lines.append(f"Requirements: {wi.get('requirements') or '—'}")
-            lines.append(f"Action items: {wi.get('action_items') or '—'}")
-            lines.append(f"Acceptance criteria: {wi.get('acceptance_criteria') or '—'}")
+            lines.append(f"Requirements: —")
+            lines.append(f"Action items: {wi.get('action_items_ai') or '—'}")
+            lines.append(f"Acceptance criteria: {wi.get('acceptance_criteria_ai') or '—'}")
             lines.append(f"Summary: {wi.get('summary') or '—'}")
             lines.append(f"Prompts: {wi['n_prompts']} · ~{wi['words']} words · {wi['n_commits']} commits")
             if wi["files"]:
@@ -390,8 +390,8 @@ class MemoryPlanner:
                 f"{wi['n_commits']} commits · Started: {start_str}_\n\n"
                 f"{wi.get('summary') or wi.get('ai_desc') or ''}\n\n"
                 + (
-                    f"**Remaining:** {wi.get('action_items') or '—'}\n"
-                    if wi.get("action_items")
+                    f"**Remaining:** {wi.get('action_items_ai') or '—'}\n"
+                    if wi.get("action_items_ai")
                     else ""
                 )
             )

