# Project Memory — aicli
_Generated: 2026-04-14 11:28 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI backend (FastAPI) with an Electron desktop UI, enabling multi-client collaboration through unified PostgreSQL storage with semantic search via pgvector embeddings. The system captures work context across sessions, commits, and prompts into a 4-layer memory architecture (ephemeral → raw mirror tables → digested AI events → structured work items), with Claude-powered synthesis, tagging workflows, and async DAG-based pipeline execution for complex AI agent orchestration.

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
- **db_migration_sequence**: m031_commits_cleanup follows m030_pipeline_runs in MIGRATIONS list
- **db_schema_management**: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_electron_builder_scope**: Electron-builder for desktop; Mac dmg, Windows nsis, Linux AppImage+deb removed from explicit enumeration
- **deployment_target**: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **event_count_column_semantics**: counts prompt_batch + session_summary events only; now displayed after commit_count (moved from position 2 to position 4)
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
- **rel:mcp_tool_memory:work_items_table**: depends_on
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
- **database_schema**: Unified (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features); Per-project (commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}); Shared (users, usage_logs, transactions, session_tags, entity_categories, planner_tags, mng_tags_categories)
- **config_management**: config.py + YAML pipelines + pyproject.toml + aicli.yaml
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
- **build_tooling**: npm 8+ + Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev
- **prompt_management**: core.prompt_loader module with centralized prompt caching
- **schema_management**: db_schema.sql (single source of truth) + db_migrations.py (m001-m037)
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
- mem_mrr_tags per-source UPSERT strategy: one row per (tag, source) combination with ON CONFLICT backfill of event_id/work_item_id when available
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; system metadata (llm, chunk_type, commit_hash, etc.) stripped; only phase/feature/bug/source user tags retained
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Database schema as single source of truth (db_schema.sql) with migration framework (m001-m037); column naming: prefix_noun_adjective order
- mem_ai_feature_snapshot: unified layer merging planner_tags user requirements with work_items; captures summary, use cases, and delivery artifacts per type
- Session source tracking: session_src_id and session_src_desc (e.g., 'claude_cli') capture origin context in mem_mrr_tags for multi-client coordination

## In Progress

- Tag system metadata cleanup (2026-04-13): Stripped system metadata from 1441 events; retained only user tags (phase, feature, bug, source); fixed 6 corrupt session_summary events with JSON array→object conversion
- mem_mrr_tags per-source UPSERT refactoring (2026-04-13): Implemented separate ON CONFLICT strategies for prompt/commit/item/message sources; added session context (session_src_id, session_src_desc) tracking
- Event summary consolidation design: mem_ai_events unified table with event_summary schema replacing fragmented prompt + commit event handling
- History display enhancement (2026-04-06): Fixing incomplete prompt + response rendering and copy-to-clipboard functionality in frontend history view
- PostgreSQL schema migration stability: Execution of m001-m037 migration chain with nohup logging and column reordering validation
- Backend startup race condition mitigation (2026-03-18): Retry logic for empty projects list; aicli project visibility in main list improved but selection blocking persists

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

### `commit` — 2026-04-13

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 04056ad..f711bfe 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Memory table population design review: memory_items and project_facts tables not being populated per design spec; requires clarification on intended behavior before Phase 2 embedding refactor
-- Backend startup race condition partially resolved: AiCli now appears in Recent projects but remains unavailable as selectable current project; acknowledged as dev environment delay
-- Data persistence validation: tags disappearing on session switch—root cause under investigation (UI rendering vs. database save failure); /memory audit endpoint testing pending
-- Embedding logic refactoring planned: Phase 2 work blocked pending clarification on memory table update logic and completion of existing issues
-- Port binding stability confirmed: 127.0.0.1:8000 conflicts resolved; bash start_backend.sh initialization sequence documented
-- User-client schema relationship confirmed: hierarchical structure validated (clients have multiple users); schema modification status unclear, may require database migration
+- Table consolidation design: pr_embeddings and pr_memory_events merging into single mem_ai_events table with event summary schema
+- Memory table population logic: memory_items and project_facts tables require clarification on intended update behavior before Phase 2 embedding refactor
+- Data persistence validation: tags disappearing on session switch—root cause under investigation (UI rendering vs. database save failure)
+- Backend startup race condition: AiCli appears in Recent projects but remains unavailable as selectable project; dev environment delay acknowledged
+- Embedding logic refactoring blocked: Phase 2 work pending clarification on memory table update logic and table consolidation design
+- Port binding stability: 127.0.0.1:8000 conflicts resolved; bash start_backend.sh initialization sequence documented


### `commit` — 2026-04-13

diff --git a/backend/routers/route_tags.py b/backend/routers/route_tags.py
index d2f7af0..f5395b6 100644
--- a/backend/routers/route_tags.py
+++ b/backend/routers/route_tags.py
@@ -105,8 +105,10 @@ _SQL_GET_TAG_SOURCES = """
 """
 
 _SQL_INSERT_SOURCE_TAG = """
-    INSERT INTO mem_mrr_tags (tag_id, prompt_id, commit_id, item_id, message_id, auto_tagged)
-    VALUES (%s::uuid, %s, %s, %s, %s, %s)
+    INSERT INTO mem_mrr_tags
+           (tag_id, session_id, session_src_id, session_src_desc,
+            prompt_id, commit_id, item_id, message_id, auto_tagged)
+    VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
     RETURNING id
 """
 
@@ -182,6 +184,9 @@ class TagMerge(BaseModel):
 
 class SourceTagCreate(BaseModel):
     tag_id: str
+    session_id: Optional[str] = None
+    session_src_id: Optional[str] = None
+    session_src_desc: Optional[str] = None
     prompt_id: Optional[str] = None
     commit_id: Optional[int] = None
     item_id: Optional[str] = None
@@ -409,8 +414,8 @@ async def add_source_tag(body: SourceTagCreate):
         with conn.cursor() as cur:
             cur.execute(
                 _SQL_INSERT_SOURCE_TAG,
-                (body.tag_id, body.prompt_id, body.commit_id,
-                 body.item_id, body.message_id, body.auto_tagged),
+                (body.tag_id, body.session_id, body.session_src_id, body.session_src_desc,
+                 body.prompt_id, body.commit_id, body.item_id, body.message_id, body.auto_tagged),
             )
             row = cur.fetchone()
     if not row:


### `commit` — 2026-04-13

diff --git a/backend/memory/memory_tagging.py b/backend/memory/memory_tagging.py
index 01f4d42..9a95300 100644
--- a/backend/memory/memory_tagging.py
+++ b/backend/memory/memory_tagging.py
@@ -9,7 +9,9 @@ Public API::
 
     tagging = MemoryTagging()
     tag_id = tagging.get_or_create_tag(project, name, category_id)
-    tagging.link_to_mirroring(tag_id, session_id, prompt_id=uuid)
+    tagging.link_to_mirroring(tag_id, session_id, session_src_desc='claude_cli', prompt_id=uuid)
+    tagging.link_to_mirroring(tag_id, session_id, commit_id=42, commit_created=ts, event_id=evt_uuid)
+    tagging.update_event_id_for_prompts(event_id, [prompt_uuid1, prompt_uuid2])
     tagging.link_to_event(event_id, tag_id)
     tagging.add_relation(from_tag_id, 'depends_on', to_tag_id)
     tree = tagging.get_tag_tree(project)
@@ -47,23 +49,113 @@ _SQL_INSERT_TAG = """
     RETURNING id
 """
 
-_SQL_INSERT_MRR_TAG = """
+# Per-source-type UPSERT SQL — one row per (tag, source) combination.
+# ON CONFLICT updates the *_updated timestamp and backfills event_id/work_item_id when available.
+_SQL_UPSERT_MRR_TAG_PROMPT = """
     INSERT INTO mem_mrr_tags
            (tag_id, session_id, session_src_id, session_src_desc,
-            prompt_id, prompt_created,
-            commit_id, commit_created,
-            item_id, item_created,
-            message_id, message_created,
-            work_item_id, auto_tagged)
-       VALUES (%s::uuid, %s, %s, %s,
-               %s, %s,
-               %s, %s,
-               %s::uuid, %s,
-               %s::uuid, %s,
-               %s::uuid, %s)
+            prompt_id, prompt_created, prompt_updated,
+            work_item_id, work_item_created, work_item_updated,
+            event_id, event_created, event_updated, auto_tagged)
+    VALUES (%s::uuid, %s, %s, %s,
+            %s::uuid, %s, %s,
+            %s::uuid, %s, %s,
+            %s::uuid, %s, %s, %s)
+    ON CONFLICT (tag_id, prompt_id) WHERE prompt_id IS NOT NULL
+    DO UPDATE SET
+        prompt_updated    = COALESCE(EXCLUDED.prompt_updated,    NOW()),
+        event_id          = COALESCE(EXCLUDED.event_id,          mem_mrr_tags.event_id),
+        event_updated     = COALESCE(EXCLUDED.event_updated,     mem_mrr_tags.event_updated),
+        work_item_id      = COALESCE(EXCLUDED.work_item_id,      mem_mrr_tags.work_item_id),
+        work_item_updated = COALESCE(EXCLUDED.work_item_updated, mem_mrr_tags.work_item_updated),
+        session_src_desc  = COALESCE(EXCLUDED.session_src_desc,  mem_mrr_tags.session_src_desc),
+        updated_at        = NOW()
     RETURNING id
 """
 
+_SQL_UPSERT_MRR_TAG_COMMIT = """
+    INSERT INTO mem_mrr_tags
+           (tag_id, session_id, session_src_id, session_src_desc,
+            commit_id, commit_created, commit_updated,
+            work_item_id, work_item_created, work_item_updated,
+            event_id, event_created, event_updated, auto_tagged)
+    VALUES (%s::uuid, %s, %s, %s,
+            %s, %s, %s,
+            %s::uuid, %s, %s,
+            %s::uuid, %s, %s, %s)
+    ON CONFLICT (tag_id, commit_id) WHERE commit_id IS NOT NULL
+    DO UPDATE SET
+        commit_updated    = COALESCE(EXCLUDED.commit_updated,    NOW()),
+        event_id          = COALESCE(EXCLUDED.event_id,          mem_mrr_tags.event_id),
+        event_updated     = COALESCE(EXCLUDED.event_updated,     mem_mrr_tags.event_updated),
+        work_item_id      = COALESCE(EXCLUDED.work_item_id,      mem_mrr_tags.work_item_id),
+        work_item_updated = COALESCE(EXCLUDED.work_item_updated, mem_mrr_tags.work_item_updated),
+        session_src_desc  = COALESCE(EXCLUDED.session_src_desc,  mem_mrr_tags.session_src_desc),
+        updated_at        = NOW()
+    RETURNING id
+"""
+
+_SQL_UPSERT_MRR_TAG_ITEM = """
+    INSERT INTO mem_mrr_tags
+           (tag_id, session_id, session_src_id, session_src_desc,
+            item_id, item_created, item_updated,
+            work_item_id, work_item_created, work_item_updated,
+            event_id, event_created, event_updated, auto_tagged)
+    VALUES (%s::uuid, %s, %s, %s,
+            %s::uuid, %s, %s,
+            %s::uuid, %s, %s,
+            %s::uuid, %s, %s, %s)
+    ON CONFLICT (tag_id, item_id) WHERE item_id IS NOT NULL
+    DO UPDATE SET
+        item_updated      = COALESCE(EXCLUDED.item_updated,      NOW()),
+        event_id          = COALESCE(EXCLUDED.event_id,          mem_mrr_tags.event_id),
+        event_updated     = COALESCE(EXCLUDED.event_updated,     mem_mrr_tags.event_updated),
+        work_item_id      = COALESCE(EXCLUDED.work_item_id,      mem_mrr_tags.work_item_id),
+        work_item_updated = COALESCE(EXCLUDED.work_item_updated, mem_mrr_tags.work_item_updated),
+        session_src_desc  = COALESCE(EXCLUDED.session_src_desc,  mem_mrr_tags.session_src_desc),
+        updated_at        = NOW()
+    RETURNING id
+"""
+
+_SQL_UPSERT_MRR_TAG_MESSAGE = """
+    INSERT INTO mem_mrr_tags
+           (tag_id, session_id, session_src_id, session_src_desc,
+            message_id, message_created, message_updated,
+            work_item_id, work_item_created, work_item_updated,
+            event_id, event_created, event_updated, auto_tagged)
+    VALUES (%s::uuid, %s, %s, %s,
+            %s::uuid, %s, %s,
+            %s::uuid, %s, %s,
+            %s::uuid, %s, %s, %s)
+    ON CONFLICT (tag_id, message_id) WHERE message_id IS NOT NULL
+    DO UPDATE SET
+        message_updated   = COALESCE(EXCLUDED.message_updated,   NOW()),
+        event_id          = COALESCE(EXCLUDED.event_id,          mem_mrr_tags.event_id),
+        event_updated     = COALESCE(EXCLUDED.event_updated,     mem_mrr_tags.event_updated),
+        work_item_id      = COALESCE(EXCLUDED.work_item_id,      mem_mrr_tags.work_item_id),
+        work_item_updated = COALESCE(EXCLUDED.work_item_updated, mem_mrr_tags.work_item_updated),
+        session_src_desc  = COALESCE(EXCLUDED.session_src_desc,  mem_mrr_tags.session_src_desc),
+        updated_at        = NOW()
+  

### `commit` — 2026-04-13

diff --git a/backend/core/database.py b/backend/core/database.py
index 7f0d53d..7ba4f6b 100644
--- a/backend/core/database.py
+++ b/backend/core/database.py
@@ -708,6 +708,11 @@ CREATE INDEX IF NOT EXISTS idx_mem_mrr_tags_tag     ON mem_mrr_tags(tag_id);
 CREATE INDEX IF NOT EXISTS idx_mem_mrr_tags_session ON mem_mrr_tags(session_id);
 CREATE INDEX IF NOT EXISTS idx_mem_mrr_tags_prompt  ON mem_mrr_tags(prompt_id);
 CREATE INDEX IF NOT EXISTS idx_mem_mrr_tags_commit  ON mem_mrr_tags(commit_id);
+-- Partial unique indexes enable UPSERT per source type (one row per tag+source combination)
+CREATE UNIQUE INDEX IF NOT EXISTS idx_mem_mrr_tags_prompt_uniq  ON mem_mrr_tags(tag_id, prompt_id)   WHERE prompt_id  IS NOT NULL;
+CREATE UNIQUE INDEX IF NOT EXISTS idx_mem_mrr_tags_commit_uniq  ON mem_mrr_tags(tag_id, commit_id)   WHERE commit_id  IS NOT NULL;
+CREATE UNIQUE INDEX IF NOT EXISTS idx_mem_mrr_tags_item_uniq    ON mem_mrr_tags(tag_id, item_id)     WHERE item_id    IS NOT NULL;
+CREATE UNIQUE INDEX IF NOT EXISTS idx_mem_mrr_tags_message_uniq ON mem_mrr_tags(tag_id, message_id)  WHERE message_id IS NOT NULL;
 
 -- ── AI tags on embedding events ──────────────────────────────────────────────
 CREATE TABLE IF NOT EXISTS mem_ai_tags (
@@ -824,6 +829,7 @@ END $$;
 # ─── Column additions to existing tables (memory infra) ──────────────────────
 
 _DDL_MEMORY_INFRA_ALTERS = """
+ALTER TABLE planner_tags         ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
 ALTER TABLE mem_mrr_commits      ADD COLUMN IF NOT EXISTS prompt_id UUID REFERENCES mem_mrr_prompts(id);
 ALTER TABLE mem_mrr_commits      ADD COLUMN IF NOT EXISTS diff_summary TEXT NOT NULL DEFAULT '';
 ALTER TABLE pr_work_items        ADD COLUMN IF NOT EXISTS tag_id UUID REFERENCES planner_tags(id);


### `commit` — 2026-04-13

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 24ed10e..4aea9ab 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-03-31 16:36 UTC
+> Generated by aicli 2026-03-31 16:55 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -15,7 +15,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - ui_components: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - storage_primary: PostgreSQL 15+ with per-project schema
 - storage_semantic: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- db_schema: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)
+- db_schema: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys
 - authentication: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
 - llm_providers: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - workflow_engine: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
@@ -37,6 +37,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - node_modules_build: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
 - database_version: PostgreSQL 15+
 - build_tooling: npm 8+ with webpack/Electron-builder; Vite dev server on localhost
+- db_consolidation: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
 
 ## Architectural Decisions
 
@@ -49,9 +50,9 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
 - Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Embeddings linked to tags: tag metadata captures context (auth→all authentication prompts; feature/bug→relevant code changes)
-- Backend modular: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
\ No newline at end of file
+- Backend modular: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
+- pr_embeddings and pr_memory_events tables to be merged into single mem_ai_events table (id, project_id, session_id, session_desc, event_summary)
\ No newline at end of file


### `commit` — 2026-04-13

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index fa53830..bf2bbd4 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 16:36 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 16:55 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -15,7 +15,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - **storage_primary**: PostgreSQL 15+ with per-project schema
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)
+- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys
 - **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
 - **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
@@ -37,6 +37,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server on localhost
+- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
 
 ## Key Decisions
 
@@ -49,17 +50,17 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
 - Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Embeddings linked to tags: tag metadata captures context (auth→all authentication prompts; feature/bug→relevant code changes)
 - Backend modular: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
+- pr_embeddings and pr_memory_events tables to be merged into single mem_ai_events table (id, project_id, session_id, session_desc, event_summary)
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-18] it looks like it is a bit broken, I have got an error - '_Database' object has no attribute 'ensure_project_schema'. Did
 - [2026-03-18] There are some error - on the first load, it lookls like Backend is failing (after thay it succeed). I have tried to run
 - [2026-03-18] Looks beter. there are some minor issue - in project page, I do see in Recent aiCli, but I do not see that As a project 
 - [2026-03-18] Few more strucure - users are also part of client (client can have mutiple users). Also I would like to understand if yo
-- [2026-03-31] Is it makes more sense, before I continue to the secopnd phase (refactor embedding logic) . is there is anything else yo
\ No newline at end of file
+- [2026-03-31] Is it makes more sense, before I continue to the secopnd phase (refactor embedding logic) . is there is anything else yo
+- [2026-03-31] Yes please fix that. about pr_embedding. in the prevous prompts I have mention the following: pr_embeddings,pr_memory_ev
\ No newline at end of file


## AI Synthesis

**[2026-04-13]** `claude_cli` — Completed multi-pass tag system cleanup: Pass 0 fixed 6 corrupt session_summary events (JSON array→object); Pass 1 stripped system metadata (llm, chunk_type, commit_hash, etc.) from 1441 events, retaining only user tags (phase, feature, bug, source); Pass 2+ focused on event digest consolidation.

**[2026-04-13]** `system` — Refactored mem_mrr_tags architecture to per-source UPSERT strategy with four separate ON CONFLICT blocks (prompt/commit/item/message) for reliable backfill of event_id and work_item_id when available; added session_src_id and session_src_desc context fields.

**[2026-04-06]** `system` — Fixed PostgreSQL JSONB operator conflict in route_history (line 466-470) causing batch upsert failures; identified and resolved null byte stale file handle issue with nohup logging.

**[2026-04-06]** `system` — Prioritized history display enhancement: incomplete prompt + response rendering and copy-to-clipboard functionality gaps reported by users.

**[2026-03-18]** `system` — Partially resolved backend startup race condition: AiCli now appears in Recent projects but remains unavailable as selectable current project; acknowledged as dev environment delay requiring retry logic on empty projects list.