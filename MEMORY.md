# Project Memory — aicli
_Generated: 2026-04-14 23:22 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend, PostgreSQL with pgvector for semantic search, and an Electron desktop UI for persistent project context and AI-assisted workflows. The system orchestrates multi-stage work item pipelines via agent roles (PM→Architect→Developer→Reviewer), synthesizes memory via Claude, and provides tagging, embeddings, and real-time collaboration features. Currently enhancing agent role management, improving tag suggestion workflows, and refactoring pipeline execution UI for proper state rendering.

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
- **database**: PostgreSQL 15+ with pgvector extensions + m001-m041 migration framework
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
- **llm_provider_location**: agents/providers/

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags, facts, work items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; login_as_first_level_hierarchy pattern for hierarchical Clients → Users
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules in agents/providers/ with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with exec_llm boolean flag
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; system metadata stripped, user-facing tags retained (phase, feature, bug, source)
- Agent roles loaded from DB (mng_agent_roles) with fallback prompts; 4-stage work item pipeline (PM→Architect→Developer→Reviewer) with auto_commit flag
- Database schema as single source of truth (db_schema.sql) with m001-m041 migration framework; column ordering: client_id → project_id → created_at/processed_at/embedding
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Tag suggestion with ai_tag_suggestion column and approve/remove buttons; simplified chip markup with category inference on tag creation

## In Progress

- Agent roles enhancement (2026-04-14) — auto_commit boolean column added to mng_agent_roles; RoleCreate/RoleUpdate models updated; improves pipeline automation workflow
- Work item pipeline refactor (2026-04-14) — Agent roles loaded from DB with fallback prompts; 4-stage pipeline now uses _load_role() and _FALLBACK_PROMPTS; all stages support provider/model overrides
- Memory mirror tables refactor (2026-04-14) — mem_mrr_prompts columns reordered (project_id/event_id after client_id); m037-m039 migrations applied for schema cleanup
- Tag suggestion and approval flow (2026-04-13) — ai_tag_suggestion column with approve/remove buttons; simplified chip markup; suggested_new tags rendering under investigation
- Pipeline execution UI rendering (2026-03-20) — Old MD version displayed on approval panel instead of current output/progress logs; chat panel state management needs investigation
- Project startup race condition fix (2026-03-20) — Sequential await api.listProjects() prevents empty home screen; edge case where list succeeds but returns empty now handled

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

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index b776c67..a455e25 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Pipeline approval workflow rendering (2026-03-20) — Old MD version displayed on approval panel instead of current output and progress logs; requires investigation of chat panel state management and step sequencing
-- Project startup race condition fix (2026-03-20) — Sequential `await api.listProjects()` prevents empty home screen by properly handling edge case where list succeeds but returns empty
+- Pipeline approval workflow rendering (2026-03-20) — Old MD version displayed instead of current output/progress logs; requires chat panel state management and step sequencing investigation
+- Project startup race condition fix (2026-03-20) — Sequential `await api.listProjects()` prevents empty home screen; edge case where list succeeds but returns empty now handled
 - Pipeline sidebar caching (2026-03-20) — `_listCache` stores {workflows, roles, runs} to prevent redundant API calls during pipeline UI rendering
-- UUID validation in pipeline run queries (2026-03-19) — psycopg2 InvalidTextRepresentation error when string 'recent' passed to UUID field; requires UUID object conversion in backend handler
+- UUID validation in pipeline run queries (2026-03-19) — psycopg2 InvalidTextRepresentation when string 'recent' passed to UUID field; requires UUID object conversion in backend
 - Memory endpoint code_dir scoping (2026-03-18) — Fixed undefined template variable causing CLAUDE.md generation failure; variable now properly scoped from config
 - Memory items and project_facts table population (pending) — Tables exist in schema but update logic unimplemented; blocks improved memory/context mechanism


### `commit` — 2026-04-14

diff --git a/ui/backend/routers/agent_roles.py b/ui/backend/routers/agent_roles.py
index 133583c..24625d3 100644
--- a/ui/backend/routers/agent_roles.py
+++ b/ui/backend/routers/agent_roles.py
@@ -56,6 +56,7 @@ def _row_to_role(row, include_prompt: bool = True) -> dict:
         "outputs":       row[12] if len(row) > 12 and row[12] is not None else [],
         "role_type":     row[13] if len(row) > 13 and row[13] else "agent",
         "output_schema": row[14] if len(row) > 14 else None,
+        "auto_commit":   row[15] if len(row) > 15 else False,
     }
     if include_prompt:
         r["system_prompt"] = row[4]
@@ -76,7 +77,7 @@ async def list_roles(
             cur.execute(
                 """SELECT id, project, name, description, system_prompt,
                           provider, model, tags, is_active, created_at, updated_at,
-                          inputs, outputs, role_type, output_schema
+                          inputs, outputs, role_type, output_schema, auto_commit
                    FROM mng_agent_roles
                    WHERE client_id=1 AND is_active=TRUE AND (project='_global' OR project=%s)
                    ORDER BY (project='_global') DESC, name""",
@@ -103,6 +104,7 @@ class RoleCreate(BaseModel):
     outputs:       list      = []
     role_type:     str       = "agent"
     output_schema: Optional[dict] = None
+    auto_commit:   bool      = False
 
 
 @router.post("/")
@@ -115,16 +117,17 @@ async def create_role(body: RoleCreate, user=Depends(get_optional_user)):
             cur.execute(
                 """INSERT INTO mng_agent_roles
                        (client_id, project, name, description, system_prompt, provider, model, tags,
-                        inputs, outputs, role_type, output_schema)
-                   VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
+                        inputs, outputs, role_type, output_schema, auto_commit)
+                   VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, project, name, description, system_prompt,
                              provider, model, tags, is_active, created_at, updated_at,
-                             inputs, outputs, role_type, output_schema""",
+                             inputs, outputs, role_type, output_schema, auto_commit""",
                 (body.project, body.name, body.description, body.system_prompt,
                  body.provider, body.model, body.tags,
                  _json.dumps(body.inputs), _json.dumps(body.outputs),
                  body.role_type,
-                 _json.dumps(body.output_schema) if body.output_schema else None),
+                 _json.dumps(body.output_schema) if body.output_schema else None,
+                 body.auto_commit),
             )
             row = cur.fetchone()
     return _row_to_role(row, include_prompt=True)
@@ -143,6 +146,7 @@ class RoleUpdate(BaseModel):
     outputs:       Optional[list]      = None
     role_type:     Optional[str]       = None
     output_schema: Optional[dict]      = None
+    auto_commit:   Optional[bool]      = None
     note:          str                 = ""
 
 
@@ -179,6 +183,7 @@ async def update_role(role_id: int, body: RoleUpdate, user=Depends(get_optional_
         ("model",         body.model),
         ("tags",          body.tags),
         ("role_type",     body.role_type),
+        ("auto_commit",   body.auto_commit),
     ]:
         if val is not None:
             fields.append(f"{col}=%s")
@@ -214,7 +219,7 @@ async def update_role(role_id: int, body: RoleUpdate, user=Depends(get_optional_
             cur.execute(
                 """SELECT id, project, name, description, system_prompt,
                           provider, model, tags, is_active, created_at, updated_at,
-                          inputs, outputs, role_type, output_schema
+                          inputs, outputs, role_type, output_schema, auto_commit
                    FROM mng_agent_roles WHERE id=%s""",
                 (role_id,),
             )


### `commit` — 2026-04-14

diff --git a/ui/backend/core/work_item_pipeline.py b/ui/backend/core/work_item_pipeline.py
index 1452125..b093323 100644
--- a/ui/backend/core/work_item_pipeline.py
+++ b/ui/backend/core/work_item_pipeline.py
@@ -1,11 +1,11 @@
 """
 work_item_pipeline.py — 4-agent pipeline for work item development.
 
-Pipeline stages (all via Anthropic API):
-  1. PM        (Haiku)  — write acceptance criteria from description + project_facts
-  2. Architect (Haiku)  — write implementation plan using project_facts + memory_items
-  3. Developer (claude_model) — implement against plan + acceptance_criteria
-  4. Reviewer  (Haiku, fresh context = Trycycle) — review against criteria only;
+Pipeline stages (all via Anthropic API, prompts loaded from DB agent roles):
+  1. PM        (Product Manager role)  — write acceptance criteria from description
+  2. Architect (Sr. Architect role)    — write implementation plan
+  3. Developer (Web Developer role)    — implement against plan + AC
+  4. Reviewer  (Code Reviewer role, fresh context) — review against criteria only;
      returns {passed, score, issues}; loops back to Developer if score < 7, max_iterations=2
 
 Stores graph_runs.id → work_items.agent_run_id on start.
@@ -24,13 +24,92 @@ log = logging.getLogger(__name__)
 
 _MAX_ITERATIONS = 2
 
+# Role name → fallback system prompt (used when DB is unavailable)
+_FALLBACK_PROMPTS: dict[str, str] = {
+    "Product Manager": (
+        "You are a senior product manager. Given a work item, produce ONLY:\n\n"
+        "## Task\n<one-sentence task statement>\n\n"
+        "## Description\n<2-3 sentences: goal, user value, scope>\n\n"
+        "## Acceptance Criteria\n"
+        "- [ ] <specific, testable criterion 1>\n"
+        "- [ ] <specific, testable criterion 2>\n"
+        "- [ ] <specific, testable criterion 3 (max 5 total)>\n\n"
+        "Rules: under 250 words total. No preamble."
+    ),
+    "Sr. Architect": (
+        "You are a senior software architect. Given a task and acceptance criteria, "
+        "produce ONLY:\n\n"
+        "## Plan\n1. <concrete step>\n2. <concrete step>\n...(max 6 steps)\n\n"
+        "## Files to Change\n"
+        "- `path/to/file.py` — <what to add/modify>\n\n"
+        "## Notes\n<2-3 sentences: key decisions, patterns to follow, risks>\n\n"
+        "Rules: under 300 words. Be precise about file paths."
+    ),
+    "Web Developer": (
+        "You are a senior full-stack developer. Given an implementation plan and "
+        "acceptance criteria, write the actual code changes.\n\n"
+        "For EACH file you create or modify, use this EXACT format:\n\n"
+        "### File: path/to/file.ext\n```language\n<complete file content>\n```\n\n"
+        "After all files, add:\n"
+        "## Summary\n- <bullet: what changed>\n- <bullet: why>"
+    ),
+    "Code Reviewer": (
+        "You are a senior code reviewer. Review the implementation against "
+        "the acceptance criteria.\n\n"
+        "Return ONLY valid JSON (no markdown fences, no preamble):\n"
+        '{"score": <1-10>, "passed": <true|false>, '
+        '"issues": ["..."], "suggestions": ["..."]}\n\n'
+        "Score >= 7 means passed."
+    ),
+}
+
+
+def _load_role(role_name: str) -> tuple[str, str, str]:
+    """Return (system_prompt, provider, model) for the named role.
+
+    Falls back to _FALLBACK_PROMPTS if DB is unavailable or role not found.
+    Returns (haiku_model, haiku_model, haiku_model) provider/model defaults.
+    """
+    if db.is_available():
+        try:
+            with db.conn() as conn:
+                with conn.cursor() as cur:
+                    cur.execute(
+                        """SELECT ar.system_prompt, ar.provider, ar.model,
+                                  COALESCE(
+                                    string_agg(sr.content, E'\\n\\n' ORDER BY rl.order_index),
+                                    ''
+                                  ) AS sys_content
+                           FROM   mng_agent_roles ar
+                           LEFT JOIN mng_role_system_links rl ON rl.role_id = ar.id
+                           LEFT JOIN mng_system_roles sr ON sr.id = rl.system_role_id
+                           WHERE  ar.name = %s AND ar.client_id = 1
+                           GROUP  BY ar.id, ar.system_prompt, ar.provider, ar.model""",
+                        (role_name,),
+                    )
+                    row = cur.fetchone()
+                    if row:
+                        base_prompt = row[0] or ""
+                        provider = row[1] or "claude"
+                        model = row[2] or settings.haiku_model
+                        sys_content = row[3] or ""
+                        if sys_content:
+                            full_prompt = f"{base_prompt}\n\n{sys_content}".strip()
+                        else:
+                            full_prompt = base_prompt
+                        return full_prompt, provider, model
+        except Exception as e:
+            log.debug(f"_load_role DB error for '{role_name}': {e}")
+
+    # Fallback
+    prompt = _FALLBACK_PROMPTS.get(role_name, f"You are a {role_name}.")
+    return prompt, "claude", settings.haiku_model
+
 
 def _save_pipeline_doc(project: str, work_item_id: str, filename: str, content: str) -> None:
     """Save a pipeline stage output to the documents folder. Silent on error."""
     import re
     from pathlib import Path
-    from config import settings
-    from core.database import db
     if not db.is_available():
         return
     try:
@@ -105,21 +184,18 @@ async def trigger_work_item_pipeline(
             context_block += f"[Recent Project Memory]\n{memory_text[:1500]}\n\n"
 
         # ── Stage 1: PM — short task spec + acceptance criteria ─────────────
-        pm_prompt = (
+        pm_prompt_sys, _, pm_model = _load_role("Product Manager")
+        pm_user = (
             f"{context_block}"
             f"Work item: **{name}**\nDescription: {description}\n\n"
     

### `commit` — 2026-04-14

diff --git a/ui/backend/core/graph_runner.py b/ui/backend/core/graph_runner.py
index 50cb8e3..751e1dd 100644
--- a/ui/backend/core/graph_runner.py
+++ b/ui/backend/core/graph_runner.py
@@ -639,17 +639,25 @@ def _load_workflow_from_db(workflow_id: str) -> tuple[dict, dict[str, dict], lis
             }
 
             cur.execute(
-                """SELECT id, name, role_file, role_prompt, provider, model,
-                          output_schema, inject_context, require_approval, approval_msg, role_id,
-                          stateless, retry_config, success_criteria,
-                          order_index, max_retry, continue_on_fail, auto_commit
-                   FROM pr_graph_nodes WHERE workflow_id=%s ORDER BY order_index, created_at""",
+                """SELECT n.id, n.name, n.role_file, n.role_prompt, n.provider, n.model,
+                          n.output_schema, n.inject_context, n.require_approval, n.approval_msg,
+                          n.role_id, n.stateless, n.retry_config, n.success_criteria,
+                          n.order_index, n.max_retry, n.continue_on_fail,
+                          COALESCE(n.auto_commit, ar.auto_commit, FALSE) AS auto_commit,
+                          COALESCE(NULLIF(n.role_prompt, ''), ar.system_prompt, '') AS effective_prompt,
+                          COALESCE(NULLIF(n.provider, ''), ar.provider, '') AS effective_provider,
+                          COALESCE(NULLIF(n.model, ''), ar.model, '') AS effective_model
+                   FROM   pr_graph_nodes n
+                   LEFT JOIN mng_agent_roles ar ON ar.id = n.role_id
+                   WHERE  n.workflow_id=%s ORDER BY n.order_index, n.created_at""",
                 (workflow_id,),
             )
             for r in cur.fetchall():
                 nodes[r[0]] = {
                     "id": r[0], "name": r[1], "role_file": r[2],
-                    "role_prompt": r[3], "provider": r[4], "model": r[5],
+                    "role_prompt": r[18],           # effective_prompt (node or role)
+                    "provider": r[19],              # effective_provider
+                    "model": r[20],                 # effective_model
                     "output_schema": r[6], "inject_context": r[7],
                     "require_approval": r[8] if len(r) > 8 else False,
                     "approval_msg": r[9] if len(r) > 9 else "",


### `commit` — 2026-04-14

diff --git a/ui/backend/core/database.py b/ui/backend/core/database.py
index e20e283..20dbd22 100644
--- a/ui/backend/core/database.py
+++ b/ui/backend/core/database.py
@@ -196,6 +196,7 @@ ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS inputs        JSONB
 ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS outputs       JSONB        DEFAULT '[]';
 ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS role_type     VARCHAR(50)  NOT NULL DEFAULT 'agent';
 ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS output_schema JSONB        DEFAULT NULL;
+ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS auto_commit   BOOLEAN      NOT NULL DEFAULT FALSE;
 CREATE UNIQUE INDEX IF NOT EXISTS idx_mar_cid_proj_name
     ON mng_agent_roles(client_id, project, name);
 CREATE INDEX IF NOT EXISTS idx_mar_cp ON mng_agent_roles(client_id, project);
@@ -633,9 +634,10 @@ class _Database:
             _Database._run_ddl_statements(conn, sql, label)
             log.debug(f"✅ {label} DDL done")
 
-        # Seed built-in global agent roles + system roles (idempotent)
+        # Seed built-in global agent roles + system roles + links (idempotent)
         _Database._seed_agent_roles(conn)
         _Database._seed_system_roles(conn)
+        _Database._seed_role_system_links(conn)
 
     def _ensure_shared_schema(self, conn) -> None:
         """Create all 15 pr_* flat tables. Runs once per process lifetime."""
@@ -1196,101 +1198,144 @@ class _Database:
 
     @staticmethod
     def _seed_agent_roles(conn) -> None:
-        """Insert the 10 built-in global roles (client_id=1). Idempotent."""
+        """Upsert the 10 built-in global roles (client_id=1).
+
+        Uses DO UPDATE so improved prompts take effect on server restart.
+        auto_commit=True is set on developer roles so pipeline nodes that
+        link to them automatically commit+push their file changes.
+        """
+        # (name, description, system_prompt, provider, model, role_type, auto_commit)
         _ROLES = [
             (
                 "Product Manager",
-                "Translates feature descriptions into acceptance criteria and user stories.",
-                "You are a senior product manager. Given a feature description, write 3-8 "
-                "acceptance criteria as bullet points starting with '- [ ]'. Each must be "
-                "specific, measurable, and testable. Also identify 2-3 user stories in "
-                "'As a [user], I want [goal]' format. Respond in plain text.",
-                "claude", "claude-haiku-4-5-20251001",
+                "Produces a concise task spec with acceptance criteria.",
+                "You are a senior product manager. Given a work item, produce ONLY:\n\n"
+                "## Task\n<one-sentence task statement>\n\n"
+                "## Description\n<2-3 sentences: goal, user value, scope>\n\n"
+                "## Acceptance Criteria\n"
+                "- [ ] <specific, testable criterion 1>\n"
+                "- [ ] <specific, testable criterion 2>\n"
+                "- [ ] <specific, testable criterion 3 (max 5 total)>\n\n"
+                "Rules: under 250 words total. No preamble. No user stories unless asked.",
+                "claude", "claude-haiku-4-5-20251001", "agent", False,
             ),
             (
                 "Sr. Architect",
-                "Designs technical architecture and numbered implementation plans.",
-                "You are a senior software architect. Given a feature and acceptance criteria, "
-                "write a numbered technical implementation plan. Include: specific files to "
-                "create or modify, functions/methods to add, database schema changes, and "
-                "integration points. Be precise about HOW to implement, not just WHAT.",
-                "claude", "claude-sonnet-4-6",
+                "Produces a concise numbered implementation plan with file paths.",
+                "You are a senior software architect. Given a task and acceptance criteria, "
+                "produce ONLY:\n\n"
+                "## Plan\n1. <concrete step>\n2. <concrete step>\n...(max 6 steps)\n\n"
+                "## Files to Change\n"
+                "- `path/to/file.py` — <what to add/modify>\n\n"
+                "## Notes\n<2-3 sentences: key decisions, patterns to follow, risks>\n\n"
+                "Rules: under 300 words. Be precise about file paths and function names. "
+                "No lengthy prose.",
+                "claude", "claude-sonnet-4-6", "system_designer", False,
             ),
             (
                 "Web Developer",
-                "Implements full-stack features against a technical plan.",
+                "Implements full-stack features; outputs complete files ready to commit.",
                 "You are a senior full-stack developer. Given an implementation plan and "
-                "acceptance criteria, write the actual code. Include complete file contents "
-                "or clear code diffs. Cover both frontend and backend changes. Add inline "
-                "comments for non-obvious logic. Ensure all acceptance criteria are met.",
-                "claude", "claude-sonnet-4-6",
+                "acceptance criteria, write the actual code changes.\n\n"
+                "For EACH file you create or modify, use this EXACT format:\n\n"
+                "### File: path/to/file.ext\n```language\n<complete file content>\n```\n\n"
+                "After all files, add:\n"
+                "## Summary\n- <bullet: what changed>\n- <bullet: why>\n\n"
+                "Rules:\n"
+                "- Write COMPLETE file content (not partial diffs)\n"
+                "- Cover both frontend and backend if needed\n"
+                "- All acceptance criteria must be met\n"
+                "- Add inline comments for non-obvious logic",
+                "claude", "claude-sonnet-4-6", "developer", True,
             ),
             (
                 "Backend Develop

### `commit` — 2026-04-14

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index de3fcfe..eca8ccf 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-03-20 19:38 UTC
+> Generated by aicli 2026-03-20 19:53 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -36,7 +36,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - JWT authentication via python-jose + bcrypt; DEV_MODE toggle; 3-tier roles (admin/paid/free); login as first-level hierarchy
 - All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends no keys
 - Nested tag hierarchy via parent_id FK with unlimited depth; tags synced across Chat/History/Commits on explicit save
-- Load-once-on-access pattern: eliminate redundant SQL by caching tags/workflows/runs in memory; update DB only on explicit save
+- Load-once-on-access pattern: cache tags/workflows/runs in memory; update DB only on explicit save to eliminate redundant SQL
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js + cytoscape-dagre visualization
 - Memory synthesis: Claude Haiku for dual-layer output (raw JSONL → interaction_tags → 5 files); smart chunking per language/section
 - Port binding safety via freePort() to kill stale uvicorn; Electron cleanup via process.exit()


## AI Synthesis

**[2026-04-14]** `routers/agent_roles.py` — Agent roles enhancement: auto_commit boolean column added to mng_agent_roles schema and RoleCreate/RoleUpdate models to support pipeline automation flags. **[2026-04-14]** `core/work_item_pipeline.py` — Work item pipeline refactor: 4-stage pipeline (PM→Architect→Developer→Reviewer) now loads agent roles from DB via _load_role() function with comprehensive _FALLBACK_PROMPTS dict for offline fallback; roles support provider/model overrides. **[2026-04-14]** `db_migrations` — Memory mirror tables refactor: mem_mrr_prompts column reordering (project_id/event_id positioned after client_id) completed via m037-m039 migrations for schema standardization. **[2026-04-13]** `ui/work_items` — Tag suggestion UX refinement: ai_tag_suggestion column with clickable approve/remove buttons; chip markup simplified, category inference added to tag creation flow. **[2026-03-20]** `ui/pipeline` — Pipeline approval panel rendering issue identified: old markdown version displayed instead of current output/progress logs; requires chat panel state management investigation. **[2026-03-20]** `ui/home` — Project startup race condition fixed: sequential await api.listProjects() prevents empty home screen by properly handling edge case where API succeeds but returns empty list.