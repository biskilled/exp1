# Project Memory — aicli
_Generated: 2026-04-14 15:53 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that combines a Python FastAPI backend with an Electron desktop client to enable AI-assisted development workflows. It uses PostgreSQL with pgvector for semantic search, Claude/OpenAI LLMs for memory synthesis, and a unified event/work-item storage model with embedded tagging and workflow automation via async DAG execution. Current focus is stabilizing tag management, work item merging, and AI-driven tag suggestions while ensuring robust startup behavior and clean data lineage.

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
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extensions
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+ with pgvector extensions
- **build_tooling**: npm 8+ + Electron-builder + Vite dev server
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
- **schema_migrations**: m001-m041 framework with db_schema.sql as source of truth

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; login_as_first_level_hierarchy pattern for hierarchical Clients → Users
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with exec_llm boolean flag
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise
- Work item embedding integration: _embed_work_item() persists 1536-dim vectors during /memory command execution
- Database schema as single source of truth (db_schema.sql) with migration framework (m001-m041); column naming: prefix_noun_adjective order
- MCP stdio server with 12+ tools including semantic search with vector embeddings on work_items table
- Tag system: retained only user-facing tags (phase, feature, bug, source); stripped system metadata (llm, event, chunk_type, commit_hash, etc.)
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)

## In Progress

- Backend startup race condition fix: retry logic handles empty project list on first load during initialization
- PostgreSQL agent roles initialization: router mapping queries correct tables per project; removed fallback workarounds
- Planner tags UI completion: categories uploaded to Planner tab; investigating missing tags display per category and tag filtering workflow
- Tag system metadata cleanup: retained user-facing tags (phase, feature, bug, source); stripped system metadata from 1441+ events during Pass 0-2
- Work item merge functionality: POST /work-items/{id}/merge endpoint with merged_into UUID tracking and filtered list queries
- AI tag suggestion feature: approved/removed tag handlers (_wiPanelApproveTag/_wiPanelRemoveTag) with category inference and tooltip improvements

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

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 26ca053..224288f 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-03-21 23:10 UTC
+> Generated by aicli 2026-03-21 23:27 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit` — 2026-04-14

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 3dd3e1c..e8e0de0 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-21 23:10 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-21 23:27 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -52,8 +52,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-21] There is agents and tools and under tools there agent_tools - I think it will be cleaner to movee agent_tools under agen
 - [2026-03-21] Is there is a reason to have tools under mcp as well ?
 - [2026-03-21] Ok. we will fix that latter, files under tools can you rename to have prefix tool_ also under mcp - currently there is o
 - [2026-03-21] I do see provider files unde data , I do see also provider_usage folder under data (which might make sense) and do see s
-- [2026-03-21] What is anthropic.jsonl , openai,jsonl and local_recalculate.jsonl, they are currently empty
\ No newline at end of file
+- [2026-03-21] What is anthropic.jsonl , openai,jsonl and local_recalculate.jsonl, they are currently empty
+- [2026-03-21] The backend is used for code only, it wont have any read permissions... any file data will be updated and used as data h
\ No newline at end of file


### `commit` — 2026-04-14

diff --git a/.ai/rules.md b/.ai/rules.md
index 3dd3e1c..e8e0de0 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-21 23:10 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-21 23:27 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -52,8 +52,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-21] There is agents and tools and under tools there agent_tools - I think it will be cleaner to movee agent_tools under agen
 - [2026-03-21] Is there is a reason to have tools under mcp as well ?
 - [2026-03-21] Ok. we will fix that latter, files under tools can you rename to have prefix tool_ also under mcp - currently there is o
 - [2026-03-21] I do see provider files unde data , I do see also provider_usage folder under data (which might make sense) and do see s
-- [2026-03-21] What is anthropic.jsonl , openai,jsonl and local_recalculate.jsonl, they are currently empty
\ No newline at end of file
+- [2026-03-21] What is anthropic.jsonl , openai,jsonl and local_recalculate.jsonl, they are currently empty
+- [2026-03-21] The backend is used for code only, it wont have any read permissions... any file data will be updated and used as data h
\ No newline at end of file


### `commit` — 2026-04-14

Commit: chore: update system context and memory files post-session
Hash: 978f5227
Code files (3):
  - .ai/rules.md
  - .cursor/rules/aicli.mdrules
  - .github/copilot-instructions.md
Generated/internal files: CLAUDE.md, MEMORY.md, workspace/aicli/_system/CLAUDE.md, workspace/aicli/_system/CONTEXT.md, workspace/aicli/_system/aicli/context.md

### `commit` — 2026-04-14

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 3e0ac40..7dea092 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
+- Database schema consolidation (2026-03-21) — Identified that pricing.json and coupon data should migrate from JSON files to SQL tables; api_keys.json remains as file (needed pre-DB connection); mng_users and mng_users_logs can be merged into single table
 - Provider storage consolidation (2026-03-21) — Consolidated all provider runtime data to data/provider_usage/; confirmed empty JSON files (anthropic.jsonl, openai.jsonl, local_recalculate.jsonl) are gitignored and local-only
 - Tool naming convention completion (2026-03-21) — Renamed agents/tools/ files to tool_ prefix; verified import paths functional post-relocation
 - Backend module restructure validation (2026-03-21) — Confirmed agents/tools/ and agents/mcp/ import paths functional; cleaned up empty directories
 - Project visibility bug investigation (ongoing) — AiCli project appearing in Recent but not main project list; backend startup race condition partially fixed with retry logic but root cause unresolved
 - Data persistence issue triage (pending) — Tags saved in UI disappearing on session switch; requires investigation into UI rendering vs. database save failure
-- SQL query optimization backlog — Row-by-row INSERT in event migration and unbounded fetchall() in memory synthesis require batch refactor and pagination


### `commit` — 2026-04-14

diff --git a/backend/routers/billing.py b/backend/routers/billing.py
index 9f854ff..e03d8e5 100644
--- a/backend/routers/billing.py
+++ b/backend/routers/billing.py
@@ -7,15 +7,13 @@ GET  /billing/history        → last 50 transactions
 POST /billing/add-payment    → placeholder (Stripe not yet integrated)
 """
 
-import json
 from datetime import datetime, timezone
-from pathlib import Path
 
 from fastapi import APIRouter, Depends, HTTPException
 from pydantic import BaseModel
 
-from core.config import settings
 from core.auth import get_current_user
+from data.database import db
 from agents.providers.pr_pricing import load_pricing
 from data.user import find_by_id, update_user
 
@@ -24,57 +22,90 @@ router = APIRouter()
 
 # ── Transaction helpers ────────────────────────────────────────────────────────
 
-def _tx_path(user_id: str) -> Path:
-    p = Path(settings.data_dir) / "transactions" / f"{user_id}.jsonl"
-    p.parent.mkdir(parents=True, exist_ok=True)
-    return p
+def _append_transaction(user_id: str, tx_type: str, amount_usd: float, description: str, ref: str = "") -> None:
+    if not db.is_available():
+        return
+    try:
+        with db.conn() as conn:
+            with conn.cursor() as cur:
+                cur.execute(
+                    """INSERT INTO mng_transactions (user_id, type, amount_usd, description, ref)
+                       VALUES (%s, %s, %s, %s, %s)""",
+                    (user_id, tx_type, amount_usd, description, ref),
+                )
+    except Exception:
+        pass
 
 
 def _load_transactions(user_id: str) -> list[dict]:
-    path = _tx_path(user_id)
-    if not path.exists():
+    if not db.is_available():
+        return []
+    try:
+        with db.conn() as conn:
+            with conn.cursor() as cur:
+                cur.execute(
+                    """SELECT type, amount_usd, description, ref, created_at
+                       FROM mng_transactions WHERE user_id=%s
+                       ORDER BY created_at DESC LIMIT 50""",
+                    (user_id,),
+                )
+                return [
+                    {
+                        "type":        r[0],
+                        "amount_usd":  float(r[1]),
+                        "description": r[2],
+                        "ref":         r[3],
+                        "ts":          r[4].isoformat() if r[4] else None,
+                    }
+                    for r in cur.fetchall()
+                ]
+    except Exception:
         return []
-    records = []
-    for line in path.read_text(encoding="utf-8").splitlines():
-        line = line.strip()
-        if line:
-            try:
-                records.append(json.loads(line))
-            except json.JSONDecodeError:
-                pass
-    return records
-
-
-def _append_transaction(user_id: str, tx_type: str, amount_usd: float, description: str, ref: str = "") -> None:
-    record = {
-        "ts": datetime.now(timezone.utc).isoformat(),
-        "type": tx_type,
-        "amount_usd": amount_usd,
-        "description": description,
-        "ref": ref,
-    }
-    with open(_tx_path(user_id), "a", encoding="utf-8") as f:
-        f.write(json.dumps(record) + "\n")
 
 
 # ── Coupon helpers ─────────────────────────────────────────────────────────────
 
-def _coupons_path() -> Path:
-    return Path(settings.data_dir) / "coupons.json"
-
-
-def _load_coupons() -> list[dict]:
-    path = _coupons_path()
-    if not path.exists():
-        return []
+def _get_coupon(code: str) -> dict | None:
+    if not db.is_available():
+        return None
     try:
-        return json.loads(path.read_text(encoding="utf-8"))
+        with db.conn() as conn:
+            with conn.cursor() as cur:
+                cur.execute(
+                    """SELECT code,amount_usd,max_uses,used_count,used_by,expires_at
+                       FROM mng_coupons WHERE client_id=1 AND code=%s""",
+                    (code,),
+                )
+                r = cur.fetchone()
+                if not r:
+                    return None
+                return {
+                    "code":       r[0],
+                    "amount_usd": float(r[1]),
+                    "max_uses":   r[2],
+                    "used_count": r[3],
+                    "used_by":    r[4] or [],
+                    "expires_at": r[5].isoformat() if r[5] else None,
+                }
     except Exception:
-        return []
+        return None
 
 
-def _save_coupons(coupons: list[dict]) -> None:
-    _coupons_path().write_text(json.dumps(coupons, indent=2), encoding="utf-8")
+def _mark_coupon_used(code: str, user_id: str) -> None:
+    if not db.is_available():
+        return
+    try:
+        with db.conn() as conn:
+            with conn.cursor() as cur:
+                cur.execute(
+                    """UPDATE mng_coupons
+                       SET used_count = used_count + 1,
+                           used_by    = used_by || %s::jsonb
+                       WHERE client_id=1 AND code=%s""",
+                    (f'["{user_id}"]', code),
+                )
+    except Exception:
+        pass
 
 
 # ── Routes ────────────────────────────────────────────────────────────────────
@@ -82,7 +113,6 @@ def _save_coupons(coupons: list[dict]) -> None:
 @router.get("/balance")
 async def get_balance(current_user: dict = Depends(get_current_user)):
     user_id = current_user.get("sub") or current_user.get("id")
-    # dev admin — synthetic response
     if user_id == "dev-admin":
         return {
             "role": "admin",
@@ -134,20 +164,16 @@ async def apply_coupon(body: CouponBody, current_user: dict = Depends(get_curren
         raise HTTPException(status_code=404, detail="User not found")
 
     code = body.code.upper().strip()
-    coupons = _load_coupons()
-    coupon = next((c for c in coupons if c["code"] == code), None)
+    coupon = _get_coupon(code)
     if not coupon:
         raise HTTPException(status_code=4

## AI Synthesis

**[2026-03-21]** `infrastructure` — Backend startup race condition addressed with retry logic for empty project lists on first load; PostgreSQL agent roles initialization corrected with proper per-project table routing.
**[2026-03-21]** `ui` — Planner tags UI expanded with category uploads; ongoing investigation into missing tags display per category and tag filtering workflow integration.
**[2026-03-21]** `data-quality` — Tag system metadata cleanup completed: user-facing tags (phase, feature, bug, source) retained across 1441+ events; system metadata (llm, event, chunk_type, commit_hash) stripped during backfill passes.
**[2026-03-21]** `features` — Work item merge functionality implemented via POST /work-items/{id}/merge with merged_into UUID tracking; filtered list queries prevent merged items from appearing in main view.
**[2026-03-21]** `ai-features` — AI tag suggestion feature: approved/removed tag handlers refactored with category inference logic and improved tooltips (changed from 'No existing tag' to 'Does not exist yet').
**[2026-03-14]** `schema` — Database schema standardized to prefix_noun_adjective column naming convention (commit_hash_short not commit_short_hash); m001-m041 migration framework with db_schema.sql as single source of truth.
**[2026-03-14]** `memory` — 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts; work item vectors persisted on /memory execution.
**[2026-03-14]** `filtering` — Event filtering logic finalized: event_type IN ('prompt_batch', 'session_summary') filters work item digests; per-commit and diff_file noise excluded from event_count aggregation.
**[2026-03-14]** `deployment` — Railway backend deployment with Dockerfile + railway.toml; Electron-builder desktop clients (Mac dmg, Windows nsis, Linux AppImage+deb) configured.