# Project Memory — aicli
_Generated: 2026-04-14 13:24 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend with PostgreSQL/pgvector semantic storage and an Electron desktop UI. It captures development events (commits, code changes, prompts) into a unified mem_ai_* schema with LLM-powered synthesis, work item management, and async DAG-based workflows. Currently in active development focusing on work item merge functionality, tag system cleanup, and data integrity repairs.

## Project Facts

- **ai_event_filtering_logic**: event_type IN ('prompt_batch', 'session_summary') filters mem_ai_events; excludes per-commit and diff_file noise from event_count aggregation
- **ai_event_tags_schema**: mem_ai_events.tags JSONB object; preserved keys: phase, feature, bug, source; system metadata (llm, event, chunk_type, commit_hash, commit_msg, file, files, languages, symbols, rows_changed, changed_files) stripped during backfill
- **ai_tag_color_default**: #4a90e2 replaces var(--accent), applied when wi.ai_tag_color not set
- **ai_tag_label_format**: category:name when both present, falls back to name-only, empty string if neither
- **ai_tag_suggestion_debugging_status**: investigating missing suggested_new tags in ui_tags query and verifying ai_suggestion column population in work item panel refresh workflow
- **ai_tag_suggestion_feature**: ai_tag_suggestion column with approve/remove button handlers (_wiPanelApproveTag/_wiPanelRemoveTag), refactored to simplified chip markup without category prefix display in non-category mode
- **ai_tag_suggestion_ux**: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip improved from 'No existing tag' to 'Does not exist yet'
- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **code_extraction_configuration**: min_lines: 5 (per-symbol threshold), min_diff_lines: 5 (commit-level threshold), only_on_commits_with_tags: false
- **column_naming_convention**: prefix_noun_adjective order: commit_hash_short (not commit_short_hash); standardized across schema
- **commit_processing_flag**: exec_llm boolean column replaces tags->>'llm' NULL check
- **commit_tracking_exec_llm_deprecation**: exec_llm boolean column replaced by event_id IS NULL sentinel (event_id set by process_commit() on completion)
- **commit_tracking_schema**: mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **date_format_frontend**: YY/MM/DD-HH:MM format in work item panel
- **db_engine**: PostgreSQL with SQL parameter binding
- **db_migration_m027**: planner_tags_drop_ai_cols removes summary/design/embedding/extra via ALTER TABLE DROP IF EXISTS pattern
- **db_migration_m029**: mem_ai_feature_snapshot table: per-tag per-use-case feature snapshots with version='ai' (overwritten on each run) and version='user' (promoted, never overwritten); unique constraint on (project_id, tag_id, use_case_num, version); 3 indexes on project_id, tag_id, tag_id+version
- **db_migration_m031**: m031_commits_cleanup: drops tags_ai and exec_llm from mem_mrr_commits; renames commit_short_hash to commit_hash_short; uses DROP COLUMN IF EXISTS pattern
- **db_migration_m037**: dropped importance column from mem_ai_events table; deprecated as semantically relevant only for work_items
- **db_migration_sequence**: m031_commits_cleanup follows m030_pipeline_runs in MIGRATIONS list
- **db_schema_management**: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_electron_builder_scope**: Electron-builder for desktop; Mac dmg, Windows nsis, Linux AppImage+deb removed from explicit enumeration
- **deployment_target**: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **event_count_column_semantics**: counts prompt_batch + session_summary events only; now displayed after commit_count (moved from position 2 to position 4)
- **event_tag_backfill_endpoint**: POST /admin/backfill-event-tags with project and dry_run params; returns per-pass counts; requires admin auth
- **event_tag_backfill_process**: three-pass idempotent operation: Pass 1 strip system metadata, Pass 2 backfill commit events from mem_mrr_commits via source_id or event_id, Pass 3 backfill prompt_batch events from mem_mrr_prompts via event_id
- **event_tags_corrupt_recovery**: Pass 0 detects and resets non-object JSONB tags (arrays/scalars) to {} before backfill
- **feature_snapshot_schema**: 19 columns: id (UUID PK), client_id (default 1), project_id (FK), tag_id (FK), use_case_num, name, category, status, priority, due_date, summary, use_case_summary, use_case_type, use_case_delivery_category, use_case_delivery_type, related_work_items (JSONB), requirements (JSONB), action_items (JSONB), version (default 'ai'), created_at, updated_at
- **feature_snapshot_versioning**: two-tier: version='ai' auto-overwritten on snapshot runs; version='user' promoted from AI snapshot, never overwritten by subsequent AI runs
- **frontend_sticky_header_pattern**: CSS position:sticky;top:0;z-index:1 on table headers for work_items panel
- **frontend_ui_pattern**: inline event handlers with event.stopPropagation(), CSS opacity/color hover states via onmouseenter/onmouseleave, escaped string interpolation in onclick via _esc()
- **known_bug_active**: planner_tag_visibility: categories upload but individual tags don't display in UI bindings
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **mcp_tools_count**: 12+ tools including semantic search with work_items vector search, work item management, session tagging
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **memory_sync_workflow**: /memory endpoint executes embedding pipeline refresh to sync prompts with work_items and detect new tags
- **memory_synthesis_output_format**: 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) with LLM response summarization instead of full output
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
- **pipeline_log_error_handling**: graceful degradation: _insert_run/_finish_run return None/silently fail if db.is_available() false, logged at debug level
- **pipeline_logging_api_endpoint**: GET /memory/{project}/pipeline-status dashboard exposes mem_pipeline_runs data
- **pipeline_logging_pattern**: async context manager pipeline_run() and sync tuple-return pipeline_run_sync() wrapping background tasks with mem_pipeline_runs insert/update
- **pipeline_run_context_pattern**: context dict with items_in/items_out keys, caller mutates ctx[key] inside async with block
- **pipeline_run_status_values**: status column accepts 'running', 'ok', 'error'
- **pipeline_run_table_schema**: mem_pipeline_runs: project_id, pipeline, source_id, status, items_in, items_out, duration_ms, error_msg (max 500 chars), finished_at, id (uuid)
- **pipeline_run_timing_method**: time.monotonic() for duration calculation, stored as integer duration_ms
- **planner_tag_schema_consolidation_proposed**: drop seq_num and source columns; keep creator only; reduce descriptors (short_desc, full_desc, requirements, acceptance_criteria, summary, action_items, design) to essential fields
- **planner_tags_core_columns**: requirements, acceptance_criteria, action_items, status, priority, due_date, requester, creator, created_at, updater, updated_at retained
- **planner_tags_schema_cleanup**: dropped summary, design, embedding (VECTOR 1536), extra columns; move to future merge-layer table (m027)
- **prompt_architecture**: core.prompt_loader for centralization; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
- **prompt_count_metric**: distinct metric tracked separately from event_count in work items API response
- **prompt_loading_pattern**: core.prompt_loader._prompts.content() replaces direct mng_system_roles queries
- **prompt_work_item_trigger_automation**: _run_promote_all_work_items() integrated into /memory command pipeline to refresh AI text fields and embedding vectors during memory generation
- **rel:ai_tag_suggestion:user_tags**: replaces
- **rel:ai_tag_suggestion:work_items_table**: related_to
- **rel:background_tasks:pipeline_logging**: depends_on
- **rel:commit_processing:exec_llm_flag**: replaces
- **rel:db_migrations:planner_tags**: implements
- **rel:embedding_integration:prompt_work_item_trigger**: implements
- **rel:embedding_vectors:semantic_search**: enables
- **rel:event_filtering:noise_reduction**: implements
- **rel:exec_llm:event_id**: replaces
- **rel:frontend_ui_pattern:ai_tag_suggestion_feature**: implements
- **rel:m037:importance_column**: replaces
- **rel:mcp_tool_memory:work_items_table**: depends_on
- **rel:mem_ai_events:mem_mrr_commits**: backfill_depends_on
- **rel:mem_ai_events:mem_mrr_prompts**: backfill_depends_on
- **rel:mem_ai_events:work_items**: depends_on
- **rel:mem_ai_feature_snapshot:mng_clients**: depends_on
- **rel:mem_ai_feature_snapshot:mng_projects**: depends_on
- **rel:mem_ai_feature_snapshot:planner_tags**: depends_on
- **rel:mem_mrr_commits:mem_ai_events**: replaces
- **rel:mem_mrr_commits:mem_mrr_commits_code**: replaces
- **rel:memory_endpoint:tag_detection**: implements
- **rel:memory_system:session_tags**: implements
- **rel:pipeline_run:mem_pipeline_runs**: implements
- **rel:planner_tags:vector_embedding**: replaces
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
- **rel:work_item_consolidation:desc_ai**: depends_on
- **rel:work_item_deletion:api_endpoint**: depends_on
- **rel:work_item_embedding:prompt_work_item_trigger**: implements
- **rel:work_item_panel_sort:prompt_count**: implements
- **rel:work_item_panel:state_management**: implements
- **rel:work_item_vector_search:mcp_tools**: implements
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
- **tags_ai_deprecation**: tags_ai column in mem_mrr_commits removed; data now stored in mem_mrr_commits_code (per-symbol) and mem_ai_events (commit digest)
- **tag_suggestion_workflow**: auto-saved to session via _acceptSuggestedTag; tag management flows through Chat tab (+) with category selection and deduplication
- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
- **ui_library**: 3_dot_menu_pattern
- **ui_toast_notification**: toast() function displays error messages with 'error' severity level
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition
- **user_tags_rendering**: removed from panel display (userTagsHtml variable deleted), stored in wi.user_tags array but no longer shown in UI
- **work_item_column_consolidation**: summary consolidated into desc_ai to reduce redundancy; ai_name→name_ai, ai_category→category_ai, ai_desc→desc_ai refactoring completed
- **work_item_deletion_endpoint**: DELETE /work-items/{id} with confirm dialog, cache clearing via window._wiPanelDelete, panel re-rendering
- **work_item_deletion_handler**: _wiDeleteLinked in entities.js with confirmation dialog and _wiRowLoading state management
- **work_item_deletion_pattern**: client-side confirmation dialog, async api.workItems.delete(), local state cleanup, re-render panel
- **work_item_description_processing**: newlines replaced with spaces and trimmed (replace(/\n/g,' ').trim()), clipped to 70 chars with ellipsis
- **work_item_display_fields**: ai_category icon mapping, status_user color mapping, seq_num sequence number, id identifier
- **work_item_embedding_integration**: _embed_work_item() persists vectors for name_ai + desc_ai + summary_ai concatenation; integrated into prompt_work_item() trigger and new work item creation flow
- **work_item_event_association**: two-path join: session_id match from source_event_id OR direct work_item_id link, both filtered by event_type
- **work_item_panel_column_order**: Name, prompt_count, commit_count, event_count, updated_at (prompts column added before commits, events moved last)
- **work_item_panel_column_widths**: prompt_count:46px, commit_count:46px, event_count:46px (resized from 52px event_count + 52px commit_count)
- **work_item_panel_sortable_fields**: prompt_count, event_count, commit_count, seq_num (prompt_count added to sort handler)
- **work_item_panel_state_management**: _wiPanelItems object stores work items, window._wiPanelDelete and window._wiPanelRefresh are global handlers
- **work_item_ui_column_widths**: 56px–80px for multi-column sortable table headers
- **work_item_ui_pattern**: multi-column sortable table with proper header styling, status color badges
- **work_item_unlink_handler**: _wiUnlink uses _wiRowLoading(id, true) for loading state during patch operation
- **work_item_vector_search**: MCP tool_memory.py semantic search includes work_items table with embedding <=> operator, returns category/name/description/status for non-archived items

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel; Dashboard tab for pipeline visibility
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac/Windows/Linux)
- **database_schema**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features (unified); mem_mrr_commits_code, mem_mrr_tags (mirroring); per-project tables; shared users/usage_logs/transactions/session_tags/entity_categories tables
- **config_management**: config.py + YAML pipelines + pyproject.toml + aicli.yaml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ + Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev
- **prompt_management**: core.prompt_loader module with centralized prompt caching
- **schema_management**: db_schema.sql + db_migrations.py (m001-m037)
- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; Shared: users, usage_logs, transactions, session_tags, entity_categories, planner_tags, mng_tags_categories
- **embeddings**: text-embedding-3-small (1536-dim vectors)
- **deployment_backend**: Railway (Dockerfile + railway.toml)

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with exec_llm boolean flag
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise
- Work item embedding integration: _embed_work_item() persists 1536-dim vectors for name_ai + desc_ai during /memory command execution
- Database schema as single source of truth (db_schema.sql) with migration framework (m001-m037); column naming: prefix_noun_adjective order
- MCP stdio server with 12+ tools including semantic search with vector embeddings on work_items table
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Tag system metadata cleanup: retained only user-facing tags (phase, feature, bug, source); stripped system metadata (llm, event, chunk_type, commit_hash, etc.)

## In Progress

- Work item merge functionality: implemented POST /work-items/{id}/merge endpoint with merged_into tracking; UI drag-drop merge in entities.js with merge_with body param
- Work items bottom panel: added persistent 210px planner-wi-panel in entities.js with drag-drop merge support, unlink button, and new item creation UI
- Work item panel API integration: wired api.workItems.merge(), _loadWiPanel() auto-refresh, and _wiPanelNewItem() creation workflow with toast feedback
- Schema migration for merged_into column: added merged_into UUID column to mem_ai_work_items with list filtering (WHERE w.merged_into IS NULL)
- Tag system metadata cleanup: Pass 0-2 completed removing system tags from 1441 events; retained only user-facing tags (phase, feature, bug, source)
- Event corruption fix: repaired 6 corrupt session_summary events with malformed JSON tag arrays; reset to empty objects {} as baseline

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
- **shared-memory** `[open]`
- **billing** `[open]`
- **embeddings** `[open]`
- **tagging** `[open]`
- **mcp** `[open]`
- **workflow-runner** `[open]`
- **test-picker-feature** `[open]`
- **UI** `[open]`
- **auth** `[open]`
- **dropbox** `[open]`
- **entity-routing** `[open]`
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

### `commit` — 2026-04-14

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 0076ce2..86f4459 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -88,7 +88,30 @@ export function renderEntities(container) {
         </div>
 
       </div>
+
+      <!-- Bottom panel: Work Items (always visible) -->
+    <div id="planner-wi-panel"
+         style="height:210px;border-top:2px solid var(--border);flex-shrink:0;
+                display:flex;flex-direction:column;background:var(--surface)">
+      <!-- Panel header -->
+      <div style="display:flex;align-items:center;gap:0.5rem;padding:3px 10px;
+                  border-bottom:1px solid var(--border);flex-shrink:0;
+                  background:var(--surface2)">
+        <span style="font-size:0.6rem;font-weight:700;color:var(--text);letter-spacing:.03em">⬡ WORK ITEMS</span>
+        <span id="wi-panel-count" style="font-size:0.55rem;color:var(--muted)"></span>
+        <span style="flex:1"></span>
+        <button id="wi-panel-add-btn"
+          style="background:var(--accent);border:none;color:#fff;font-size:0.57rem;
+                 padding:0.13rem 0.42rem;border-radius:var(--radius);cursor:pointer;
+                 font-family:var(--font);outline:none">+ New</button>
+      </div>
+      <!-- Panel list -->
+      <div id="wi-panel-list" style="flex:1;overflow-y:auto;overflow-x:hidden">
+        <div style="padding:0.5rem 1rem;font-size:0.65rem;color:var(--muted)">Loading…</div>
+      </div>
     </div>
+
+  </div>
   `;
 
   // Wire window globals
@@ -112,6 +135,64 @@ export function renderEntities(container) {
   window._plannerDrawerRemoveLink = _plannerDrawerRemoveLink;
   window._plannerGenerateSnapshot = _plannerGenerateSnapshot;
   window._plannerDrawerMerge      = _plannerDrawerMerge;
+  window._plannerOpenWorkItemDrawer = (id, cat, proj) => _openWorkItemDrawer(id, cat, proj, null, '#4a90e2', '📋');
+  window._wiBotDragStart = (e, id, name, cat) => {
+    _dragWiData = { id, ai_name: name, ai_category: cat };
+    e.dataTransfer.effectAllowed = 'link';
+    e.dataTransfer.setData('text/plain', id);
+    e.currentTarget.style.opacity = '0.5';
+  };
+  window._wiBotDragEnd = (e) => {
+    if (e && e.currentTarget) e.currentTarget.style.opacity = '';
+    _dragWiData = null;
+    document.querySelectorAll('[data-tag-id]').forEach(r => { r.style.background = ''; r.style.outline = ''; });
+    const h = document.getElementById('planner-dnd-hint');
+    if (h) h.style.display = 'none';
+  };
+  window._wiBotItemDragOver = (e, el) => {
+    const targetId = el.dataset.wiId;
+    if (!_dragWiData || !targetId || targetId === _dragWiData.id) return;
+    e.preventDefault();
+    e.stopPropagation();
+    el.style.outline = '2px solid var(--accent)';
+    const h = document.getElementById('planner-dnd-hint');
+    if (h) { h.style.display = 'block'; h.textContent = `⊕ Merge with "${_esc(el.dataset.wiName || '')}"`;
+             h.style.left = (e.clientX+16)+'px'; h.style.top = (e.clientY+12)+'px'; }
+  };
+  window._wiBotItemDragLeave = (e, el) => { el.style.outline = ''; };
+  window._wiBotItemDrop = async (e, targetId, proj) => {
+    e.preventDefault();
+    e.stopPropagation();
+    const el = e.currentTarget;
+    el.style.outline = '';
+    if (!_dragWiData || !targetId || targetId === _dragWiData.id) return;
+    const sourceId = _dragWiData.id;
+    const sourceName = _dragWiData.ai_name;
+    _dragWiData = null;
+    try {
+      await api.workItems.merge(sourceId, targetId, proj);
+      toast(`Merged "${sourceName}" ⊕ merged`, 'success');
+      _loadWiPanel(proj);
+    } catch(err) { toast('Merge failed: ' + err.message, 'error'); }
+  };
+  window._wiUnlink = async (id, proj) => {
+    try {
+      await api.workItems.patch(id, proj, { tag_id: '' });
+      toast('Unlinked', 'success');
+      _loadWiPanel(proj);
+    } catch(err) { toast('Unlink failed: ' + err.message, 'error'); }
+  };
+  window._wiPanelNewItem = () => {
+    const { project } = _plannerState;
+    const cat = prompt('Category (bug/feature/task):');
+    if (!cat) return;
+    const name = prompt('Work item name:');
+    if (!name) return;
+    api.workItems.create(project, { ai_category: cat.toLowerCase(), ai_name: name })
+      .then(() => { toast(`Created "${name}"`, 'success'); _loadWiPanel(project); })
+      .catch(err => toast(err.message, 'error'));
+  };
+  document.getElementById('wi-panel-add-btn')?.addEventListener('click', window._wiPanelNewItem);
 
   if (!project) {
     document.getElementById('planner-tags-pane').innerHTML =
@@ -144,6 +225,8 @@ async function _initPlanner(project) {
     const first = cats.find(c => _isWorkItemCat(c.name) && c.id != null) || cats.find(c => c.id != null);
     if (first) await _plannerSelectCat(first.id, first.name);
   }
+  // Load persistent work items bottom panel
+  _loadWiPanel(project);
 }
 
 // ── Category list ─────────────────────────────────────────────────────────────
@@ -160,7 +243,6 @@ function _renderCategoryList() {
   const pipeline  = cats.filter(c => _isWorkItemCat(c.name));
   const tags      = cats.filter(c => !_isWorkItemCat(c.name) && c.name !== 'ai_suggestion');
 
-  const isSelWI   = _plannerState.selectedCatName === '__work_items__';
   const isSel = (id) => _plannerState.selectedCat === id;
   const catRow = c => `
     <div class="planner-cat-row" data-id="${c.id}" data-cat-name="${_esc(c.name)}"
@@ -177,52 +259,17 @@ function _renderCategoryList() {
       <span style="font-size:0.55rem;color:var(--muted);flex-shrink:0">${getCacheValues(c.id).length}</span>
     </div>`;
 
-  // Work Items sentinel row (always shown at top)
-  const wiSentinel = `
-    <div class="planner-cat-row" data-cat-name="__work_items__"
-         onclick="window._plannerSelectCat('__work_items__','__work_items__')"
-         style="display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:5px;
-                cursor:pointer;margin-bottom:2px;transition:b

### `commit` — 2026-04-14

diff --git a/ui/frontend/utils/api.js b/ui/frontend/utils/api.js
index b478745..81c2254 100644
--- a/ui/frontend/utils/api.js
+++ b/ui/frontend/utils/api.js
@@ -376,6 +376,10 @@ api.workItems = {
   ).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
   interactions: (id, project, limit = 20) => _get(`/work-items/${enc(id)}/interactions?project=${enc(project)}&limit=${limit}`),
   commits:      (id, project, limit = 20) => _get(`/work-items/${enc(id)}/commits?project=${enc(project)}&limit=${limit}`),
+  merge:        (id, mergeWith, project) => fetch(
+    _base() + `/work-items/${enc(id)}/merge?project=${enc(project)}`,
+    { method: 'POST', headers: _headers(), body: JSON.stringify({ merge_with: mergeWith }) }
+  ).then(r => r.ok ? r.json() : r.json().then(e => Promise.reject(new Error(e.detail || r.statusText)))),
   facts:        (project)     => _get(`/work-items/facts?project=${enc(project)}`),
   memoryItems:  (project, scope) => {
     const q = new URLSearchParams({ project: project || '' });


### `commit` — 2026-04-14

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index 4d16eb9..17c3501 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -34,6 +34,7 @@ _SQL_LIST_WORK_ITEMS_BASE = (
               w.status_user, w.status_ai, w.acceptance_criteria, w.action_items,
               w.requirements, w.code_summary, w.summary,
               w.tags, w.tag_id, w.ai_tag_id, w.source_event_id,
+              w.merged_into,
               w.created_at, w.updated_at, w.seq_num,
               tc.color, tc.icon,
               (SELECT COUNT(*) FROM mem_mrr_prompts p
@@ -210,6 +211,10 @@ class WorkItemCreate(BaseModel):
     tags:                dict = {}
 
 
+class WorkItemMerge(BaseModel):
+    merge_with: str   # UUID of the other work item to merge with
+
+
 class WorkItemPatch(BaseModel):
     ai_name:             Optional[str] = None
     ai_desc:             Optional[str] = None
@@ -223,6 +228,7 @@ class WorkItemPatch(BaseModel):
     tags:                Optional[dict] = None
     tag_id:              Optional[str] = None
     ai_tag_id:           Optional[str] = None
+    merged_into:         Optional[str] = None
 
 
 # ── CRUD ─────────────────────────────────────────────────────────────────────
@@ -269,6 +275,7 @@ async def list_work_items(
         where.append("w.ai_category=%s"); params.append(category)
     if status:
         where.append("w.status_user=%s"); params.append(status)
+    where.append("w.merged_into IS NULL")   # exclude items absorbed into a merge
     if name:
         where.append("w.ai_name=%s"); params.append(name)
 
@@ -359,6 +366,9 @@ async def patch_work_item(
     if body.ai_tag_id           is not None:
         fields.append("ai_tag_id=%s")
         params.append(body.ai_tag_id if body.ai_tag_id else None)
+    if body.merged_into         is not None:
+        fields.append("merged_into=%s")
+        params.append(body.merged_into if body.merged_into else None)
 
     if not fields:
         raise HTTPException(400, "Nothing to update")
@@ -462,6 +472,85 @@ async def get_work_item_interactions(
     return {"interactions": rows, "work_item_id": item_id, "project": p}
 
 
+# ── Merge two work items ─────────────────────────────────────────────────────
+
+
+@router.post("/{item_id}/merge", status_code=201)
+async def merge_work_item_into(
+    item_id: str,
+    body: WorkItemMerge,
+    background_tasks: BackgroundTasks,
+    project: str | None = Query(None),
+):
+    """Merge item_id and body.merge_with into a new combined work item.
+    Both originals are marked merged_into=<new_id>, status_user='done'.
+    """
+    _require_db()
+    p = _project(project)
+    p_id = db.get_or_create_project_id(p)
+
+    with db.conn() as conn:
+        with conn.cursor() as cur:
+            cur.execute(
+                "SELECT id, ai_category, ai_name, ai_desc, requirements, action_items, "
+                "acceptance_criteria, summary, tag_id, seq_num "
+                "FROM mem_ai_work_items WHERE project_id=%s AND id=ANY(%s::uuid[])",
+                (p_id, [item_id, body.merge_with]),
+            )
+            rows = cur.fetchall()
+
+    if len(rows) < 2:
+        raise HTTPException(404, "One or both work items not found")
+
+    a = dict(zip(["id","ai_category","ai_name","ai_desc","requirements","action_items",
+                  "acceptance_criteria","summary","tag_id","seq_num"], rows[0]))
+    b = dict(zip(["id","ai_category","ai_name","ai_desc","requirements","action_items",
+                  "acceptance_criteria","summary","tag_id","seq_num"], rows[1]))
+
+    # Build merged item — combine fields, prefer non-empty values
+    import json as _json
+    new_name        = f"{a['ai_name']} + {b['ai_name']}"
+    new_desc        = f"{a['ai_desc'] or ''}\n{b['ai_desc'] or ''}".strip()
+    new_req         = f"{a['requirements'] or ''}\n{b['requirements'] or ''}".strip()
+    new_actions     = f"{a['action_items'] or ''}\n{b['action_items'] or ''}".strip()
+    new_criteria    = f"{a['acceptance_criteria'] or ''}\n{b['acceptance_criteria'] or ''}".strip()
+    new_category    = a['ai_category']  # use first item's category
+    linked_tag_id   = a['tag_id'] or b['tag_id']  # keep any linked tag
+
+    with db.conn() as conn:
+        with conn.cursor() as cur:
+            seq = next_seq(cur, p_id, new_category)
+            cur.execute(
+                """INSERT INTO mem_ai_work_items
+                       (project_id, ai_category, ai_name, ai_desc, requirements,
+                        action_items, acceptance_criteria, tag_id, status_user, status_ai, seq_num)
+                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'active','active',%s)
+                   ON CONFLICT (project_id, ai_category, ai_name) DO NOTHING
+                   RETURNING id""",
+                (p_id, new_category, new_name, new_desc, new_req,
+                 new_actions, new_criteria,
+                 str(linked_tag_id) if linked_tag_id else None, seq),
+            )
+            new_row = cur.fetchone()
+            if not new_row:
+                raise HTTPException(409, f"Merged item '{new_name}' already exists")
+            new_id = str(new_row[0])
+
+            # Mark both originals as merged
+            cur.execute(
+                "UPDATE mem_ai_work_items SET merged_into=%s::uuid, status_user='done', updated_at=NOW() "
+                "WHERE id=ANY(%s::uuid[]) AND project_id=%s",
+                (new_id, [item_id, body.merge_with], p_id),
+            )
+
+    asyncio.create_task(_embed_work_item(p_id, new_id, new_name, new_desc, new_req, ""))
+    asyncio.create_task(_trigger_memory_regen(p))
+    background_tasks.add_task(_run_matching, p, new_id)
+
+    return {"id": new_id, "ai_name": new_name, "ai_category": new_category,
+            "merged_from": [item_id, body.merge_with], "project": p}
+
+
 # ── Commits linked to a work item ────────────────────────────────────────────
 
 @router.get("/{ite

### `commit` — 2026-04-14

diff --git a/backend/core/database.py b/backend/core/database.py
index 4147e83..437afd7 100644
--- a/backend/core/database.py
+++ b/backend/core/database.py
@@ -397,6 +397,7 @@ CREATE TABLE IF NOT EXISTS mem_ai_work_items (
     tags                JSONB        NOT NULL DEFAULT '{}',
     ai_tag_id           UUID         REFERENCES planner_tags(id),
     tag_id              UUID         REFERENCES planner_tags(id),
+    merged_into         UUID         REFERENCES mem_ai_work_items(id) ON DELETE SET NULL,
     status_user         VARCHAR(20)  NOT NULL DEFAULT 'active',
     status_ai           VARCHAR(20)  NOT NULL DEFAULT 'active',
     seq_num             INT,
@@ -1180,6 +1181,10 @@ CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_sai   ON mem_ai_work_items(status_ai);
 -- Migrate status → status_user (plain statement, no DO block needed since ADD sets DEFAULT)
 UPDATE mem_ai_work_items SET status_user = status WHERE status IS NOT NULL AND status_user = 'active';
 ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS status;
+-- ── 013_work_items_merge ──────────────────────────────────────────────────────
+-- merged_into: when two work items are merged, both originals point to the new item.
+ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS merged_into UUID REFERENCES mem_ai_work_items(id) ON DELETE SET NULL;
+CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_merged ON mem_ai_work_items(merged_into) WHERE merged_into IS NOT NULL;
 """
 
 


### `commit` — 2026-04-14

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 5ed5e13..d47c5dd 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-06 14:11 UTC
+> Generated by aicli 2026-04-06 14:18 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -55,9 +55,9 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
+- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
 - Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
-- Commit deduplication by hash with UNION consolidation; commits linked per-prompt with inline display (accent left-border)
+- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with mem_mrr_commits table
 - Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
 - Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation
-- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
-- PostgreSQL batch upsert with explicit ::jsonb casting for tags field to prevent duplicate row insertion on ON CONFLICT DO UPDATE
\ No newline at end of file
+- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
\ No newline at end of file


### `commit` — 2026-04-14

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index ab5e67b..e59d880 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 14:11 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 14:18 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -55,17 +55,17 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
+- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
 - Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
-- Commit deduplication by hash with UNION consolidation; commits linked per-prompt with inline display (accent left-border)
+- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with mem_mrr_commits table
 - Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
 - Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
-- PostgreSQL batch upsert with explicit ::jsonb casting for tags field to prevent duplicate row insertion on ON CONFLICT DO UPDATE
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-06] Histroy used to show promp and llm response . I currently see only prompt
 - [2026-04-06] I have  got the following error -  cur.execute(b''.join(parts)) started  route_history line 470 - execute_values(cur, _S
 - [2026-04-06] I still dont see the same issue in route_history line 470. cur.execute(b''.join(parts)) saying  ON CONFLICT DO UPDATE co
 - [2026-04-06] I am checking the aiCli_memory - and it is looks likje it is not updated at all. table are not as the current one and th
-- [2026-04-06] I would like to make sure columns are aligned in work_items. What is source_session_id usaed from in work_items? Also th
\ No newline at end of file
+- [2026-04-06] I would like to make sure columns are aligned in work_items. What is source_session_id usaed from in work_items? Also th
+- [2026-04-06] I do see an issue - Uncaught ReferenceError: _plannerSelectAiSubtype is not defined in ERROR    | routers.route_logs    
\ No newline at end of file


## AI Synthesis

**[2026-03-14]** `entities.js + route_work_items.py` — Implemented work item merge functionality with POST /work-items/{id}/merge endpoint; added merged_into UUID column to schema with list filtering to exclude absorbed items. **[2026-03-14]** `entities.js` — Built persistent 210px bottom panel (planner-wi-panel) for work items with drag-drop merge UX, unlink button, and new item creation via modal prompts. **[2026-03-14]** `api.js` — Wired api.workItems.merge() fetch method and integrated _loadWiPanel() auto-refresh after merge/creation operations with toast feedback. **[2026-03-14]** `route_work_items.py` — Merge endpoint creates new combined work item with concatenated requirements/actions/criteria, marks both originals as merged_into=new_id and status_user='done', triggers embedding + memory regen. **[Recent]** Tag system metadata cleanup — Completed Pass 0-2 removing system tags (llm, event, chunk_type, commit_hash, etc.) from 1441 events; retained only user-facing tags (phase, feature, bug, source). **[Recent]** Event corruption fix — Repaired 6 corrupt session_summary events with malformed JSON tag arrays; reset to empty objects {} as baseline for consistent state.