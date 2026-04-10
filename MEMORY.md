# Project Memory — aicli
_Generated: 2026-04-10 15:36 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a FastAPI backend + PostgreSQL with pgvector, a Python CLI with prompt_toolkit, and an Electron desktop UI with Vanilla JS. It synthesizes work sessions into structured memory via Claude LLM, tracking events/commits/tags across projects with semantic embeddings. Current focus: fixing skill naming conflicts (/tag→/stag), optimizing work item queries, and refining tag approval/deletion UX in the planner interface.

## Project Facts

- **ai_event_filtering_logic**: event_type IN ('prompt_batch', 'session_summary') filters mem_ai_events; excludes per-commit and diff_file noise from event_count aggregation
- **ai_tag_color_default**: #4a90e2 replaces var(--accent), applied when wi.ai_tag_color not set
- **ai_tag_label_format**: category:name when both present, falls back to name-only, empty string if neither
- **ai_tag_suggestion_debugging_status**: investigating missing suggested_new tags in ui_tags query and verifying ai_suggestion column population in work item panel refresh workflow
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
- **rel:sticky_header:work_items_panel**: implements
- **rel:tag_reminder:session_context**: depends_on
- **rel:ui_notifications:error_handling**: related_to
- **rel:work_item_api:prompt_count**: depends_on
- **rel:work_item_deletion:api_endpoint**: depends_on
- **rel:work_item_panel_sort:prompt_count**: implements
- **rel:work_item_panel:state_management**: implements
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- **session_context_prompt_counter**: prompt_count field added to session context JSON, initialized to 0, incremented on each prompt validation
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
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
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
- Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; source_event_id pivot for session-based aggregation
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
- AI tag backlinking: PATCH /work-items with tag_id triggers propagation to all events in source session via category→tag_key mapping
- Commit tracking: mem_mrr_commits_code table with 19 columns; join is mem_ai_events.source_id (short hash) → mem_mrr_commits.commit_short_hash
- Session tagging: /tag command replaced with /stag due to skill loader conflict; renamed skill maintains same tag:category functionality; immediate propagation via log_user_prompt.sh
- Work item counters: prompt_count (raw prompts in source session), event_count (prompt_batch/session_summary events), commit_count (distinct commits per session)

## In Progress

- Skill naming conflict resolution: /tag command conflicted with Claude Code reserved skill name; created /stag as replacement with identical functionality and immediate availability
- Work item deletion UI: _wiDeleteLinked handler in entities.js with confirmation dialog; delete button appears in tag-linked work item panel with opacity toggle hover effect
- Tag creation with auto-link workflow: _wiPanelCreateTag creates new tags without confirmation, auto-links work item, refreshes tag cache + planner table + category tag list
- AI suggestion chips UX refinement: added clickable ✓ button to create missing ai_suggestion tags with category inference; improved tooltip UX
- Tag confirmation/deletion UX clarification: investigate current confirm/delete button behavior for AI tags; accept should trigger 'remove' rather than separate 'confirm' action
- Tag-linked work item refresh: after approve/reject/create operations, _loadTagLinkedWorkItems reloads to reflect linked/unlinked status changes in planner view

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

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-10

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 58357d5..3ea4893 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-10 15:00 UTC
+> Generated by aicli 2026-04-10 15:18 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-10

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 9d9156c..41fff4b 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-10 15:00 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-10 15:18 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -67,8 +67,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] I have just tried that, got unknow skill /tag. do I have to open a new session ?
 - [2026-04-09] can you check why it takes to long to  load planner tabs and work items? it looks liike quesry are not optimised. also d
 - [2026-04-09] I am more confused noew. query - looks like it take longer. why there is DIGEST column ? it  suppose to  be events count
 - [2026-04-09] now I dont see the counter or the promts. also, I still see work item   that  are  not having any events or prompts (204
-- [2026-04-10] I still dont understand how there are work_items without any linked prompts. can you update all work_item using /mmeory 
\ No newline at end of file
+- [2026-04-10] I still dont understand how there are work_items without any linked prompts. can you update all work_item using /mmeory 
+- [2026-04-10] In the ui - when I accept AI tag - configrm should be remove (only delete suppose to stay). when I confirm existing tag 
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-10

diff --git a/.ai/rules.md b/.ai/rules.md
index 9d9156c..41fff4b 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-10 15:00 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-10 15:18 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -67,8 +67,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] I have just tried that, got unknow skill /tag. do I have to open a new session ?
 - [2026-04-09] can you check why it takes to long to  load planner tabs and work items? it looks liike quesry are not optimised. also d
 - [2026-04-09] I am more confused noew. query - looks like it take longer. why there is DIGEST column ? it  suppose to  be events count
 - [2026-04-09] now I dont see the counter or the promts. also, I still see work item   that  are  not having any events or prompts (204
-- [2026-04-10] I still dont understand how there are work_items without any linked prompts. can you update all work_item using /mmeory 
\ No newline at end of file
+- [2026-04-10] I still dont understand how there are work_items without any linked prompts. can you update all work_item using /mmeory 
+- [2026-04-10] In the ui - when I accept AI tag - configrm should be remove (only delete suppose to stay). when I confirm existing tag 
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-10

Removed obsolete agent context and system documentation files from a completed session (9315de). This is a maintenance task to clean up temporary or session-specific artifacts.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-10

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 3864a86..cd44fd2 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -240,6 +240,17 @@ export function renderEntities(container) {
       _loadWiPanel(proj);
     } catch(err) { toast('Merge failed: ' + err.message, 'error'); }
   };
+  window._wiDeleteLinked = async (id, proj) => {
+    if (!confirm('Delete this work item?')) return;
+    try {
+      await api.workItems.delete(id, proj);
+      const tr = document.querySelector(`.wi-sub-row[data-wi-id="${CSS.escape(id)}"]`);
+      if (tr) tr.remove();
+      delete _wiPanelItems[id];
+      toast('Work item deleted', 'success');
+    } catch(e) { toast('Delete failed: ' + e.message, 'error'); }
+  };
+
   window._wiUnlink = async (id, proj) => {
     try {
       await api.workItems.patch(id, proj, { tag_id: '' });
@@ -537,12 +548,14 @@ function _renderWiPanel(items, project) {
     if (!wi || !wi.ai_tag_id) return;
     try {
       await api.workItems.patch(id, proj, { tag_id: wi.ai_tag_id });
-      delete _wiPanelItems[id];  // now linked → remove from unlinked panel
+      delete _wiPanelItems[id];
       const remaining = Object.values(_wiPanelItems);
       _renderWiPanel(remaining, proj);
       const cnt = document.getElementById('wi-panel-count');
       if (cnt) cnt.textContent = remaining.length ? `(${remaining.length} unlinked)` : '(all linked ✓)';
       toast(`Linked to "${wi.ai_tag_name}"`, 'success');
+      const { selectedCatName } = _plannerState;
+      if (selectedCatName) _loadTagLinkedWorkItems(proj, selectedCatName).catch(() => {});
     } catch(e) { toast('Approve failed: ' + e.message, 'error'); }
   };
 
@@ -570,6 +583,8 @@ function _renderWiPanel(items, project) {
       const cnt = document.getElementById('wi-panel-count');
       if (cnt) cnt.textContent = remaining.length ? `(${remaining.length} unlinked)` : '(all linked ✓)';
       toast('Linked via secondary suggestion', 'success');
+      const { selectedCatName } = _plannerState;
+      if (selectedCatName) _loadTagLinkedWorkItems(proj, selectedCatName).catch(() => {});
     } catch(e) { toast('Approve failed: ' + e.message, 'error'); }
   };
 
@@ -588,9 +603,7 @@ function _renderWiPanel(items, project) {
 
   window._wiPanelCreateTag = async (id, tagName, categoryName, proj) => {
     const catLabel = categoryName || 'task';
-    if (!confirm(`Create new ${catLabel} tag "${tagName}" and link this work item?`)) return;
     try {
-      // Resolve category id from name
       const cats = await api.tags.categories.list(proj);
       const catObj = cats.find(c => c.name === catLabel) || cats.find(c => c.name === 'task') || cats[0];
       const newTag = await api.tags.create({ name: tagName, project: proj, category_id: catObj?.id });
@@ -601,6 +614,11 @@ function _renderWiPanel(items, project) {
       const cnt = document.getElementById('wi-panel-count');
       if (cnt) cnt.textContent = remaining.length ? `(${remaining.length} unlinked)` : '(all linked ✓)';
       toast(`Created ${catLabel} tag "${tagName}" and linked`, 'success');
+      // Reload tag cache so the new tag appears in the planner table, then inject sub-row
+      await loadTagCache(proj, true);
+      _renderCategoryList();
+      if (_plannerState.selectedCat) _renderTagTableFromCache();
+      _loadTagLinkedWorkItems(proj, catLabel).catch(() => {});
     } catch(e) { toast('Create failed: ' + e.message, 'error'); }
   };
 
@@ -644,7 +662,10 @@ function _renderWiPanel(items, project) {
         <span style="${LBL_AI_N}">AI(NEW)</span>
         <span style="font-size:0.65rem;font-weight:500;padding:1px 6px;border-radius:4px;
                      color:#e74c3c;border:1px solid #e74c3c;background:#e74c3c1a;
-                     white-space:nowrap" title="No existing tag — create one manually in the Planner">${_esc(aiNewLabel)}</span>
+                     white-space:nowrap" title="Does not exist yet — click ✓ to create">${_esc(aiNewLabel)}</span>
+        <button onclick="event.stopPropagation();window._wiPanelCreateTag('${_esc(wi.id)}','${_esc(aiNew)}','${_esc(aiNewCat)}','${_esc(project)}')"
+          title="Create this tag and link" style="background:none;border:1px solid #27ae60;color:#27ae60;cursor:pointer;
+                 font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">✓</button>
         <button onclick="event.stopPropagation();window._wiPanelRemoveTag('${_esc(wi.id)}','${_esc(project)}')"
           title="Dismiss suggestion" style="background:none;border:1px solid #888;color:#888;cursor:pointer;
                  font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">×</button>
@@ -794,6 +815,11 @@ async function _loadTagLinkedWorkItems(project, catName) {
                     title="${_esc(wi.ai_desc||'')}">${_esc(wi.ai_name)}</span>
               <span style="font-size:0.52rem;color:${sc};background:${sc}22;
                            padding:0.02rem 0.25rem;border-radius:8px;flex-shrink:0">${wi.status_user||'active'}</span>
+              <button title="Delete work item"
+                onclick="event.stopPropagation();window._wiDeleteLinked('${_esc(wi.id)}','${_esc(project)}')"
+                style="background:none;border:1px solid #e74c3c;color:#e74c3c;cursor:pointer;font-size:0.55rem;
+                       font-weight:700;padding:0 3px;border-radius:3px;line-height:1.3;flex-shrink:0;opacity:.6"
+                onmouseenter="this.style.opacity=1" onmouseleave="this.style.opacity=.6">×</button>
               <button title="Unlink — move back to Work Items"
                 onclick="event.stopPropagation();window._wiUnlink('${_esc(wi.id)}','${_esc(project)}')"
                 style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:0.75rem;


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-10

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index c1b0a1e..58357d5 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-10 14:52 UTC
+> Generated by aicli 2026-04-10 15:00 UTC
 
 # aicli — Shared AI Memory Platform
 


## AI Synthesis

**[2026-04-10]** `claude_cli` — Resolved `/tag` command skill naming conflict: Claude Code's skill loader reserved `tag` as system keyword, causing 'unknown skill' errors. Created `/stag` as functional replacement with identical tag:category functionality and immediate CLI availability after restart. Issue affected session tagging workflow where tags should propagate via log_user_prompt.sh context reading.

**[2026-04-09→04-10]** `work_item_queries` — User reported performance issues with planner tab and work item loading; queries appear unoptimized. Concurrent issue: DIGEST column presence confusing (should be event count). Work items appear without linked events despite FK constraints suggesting they should exist.

**[2026-04-09]** `ai_tag_suggestion_feature` — Implemented clickable chip UI for creating missing ai_suggestion tags with category inference. Improved tooltip messaging from 'No existing tag' to clarify 'Does not exist yet' status. Added category detection logic for auto-suggesting appropriate tag categories.

**[2026-04-10]** `tag_linked_work_items_ui` — Refined work item deletion UX in tag-linked panel with _wiDeleteLinked handler; added confirmation dialog and opacity-toggled delete button. Tag-linked work item list now refreshes after approve/reject/create operations to reflect link status changes.

**[2026-04-09]** `memory_synthesis_refresh` — Copilot instructions and AI rules files updated (timestamp 15:00→15:18 UTC) confirming successful `/memory` command execution. Recent context window captures user confusion about work item event counts and query performance degradation.

**[2026-04-10]** `ai_tag_confirmation_ux` — User feedback indicates 'confirm' button behavior for accepting AI tags should be 'remove' instead; only 'delete' should remain as separate action. Suggests current UI conflates approval action with confirmation/removal semantics.