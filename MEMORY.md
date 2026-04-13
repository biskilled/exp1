# Project Memory — aicli
_Generated: 2026-04-12 23:22 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a FastAPI backend + PostgreSQL with pgvector, a Python CLI, and an Electron desktop UI (Vanilla JS + Cytoscape) to capture, analyze, and synthesize project development history across commits, sessions, and work items. It uses a 4-layer memory architecture (ephemeral → raw → digested → synthesized) with dual-layer Claude Haiku synthesis, async DAG workflow execution, and MCP integration for semantic search and work item management.

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
- **db_migration_m027**: planner_tags_drop_ai_cols removes summary/design/embedding/extra via ALTER TABLE DROP IF EXISTS pattern
- **db_migration_m029**: mem_ai_feature_snapshot table: per-tag per-use-case feature snapshots with version='ai' (overwritten on each run) and version='user' (promoted, never overwritten); unique constraint on (project_id, tag_id, use_case_num, version); 3 indexes on project_id, tag_id, tag_id+version
- **db_migration_sequence**: m029 follows m028_add_deliveries in MIGRATIONS list
- **db_schema_management**: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
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
- **rel:frontend_ui_pattern:ai_tag_suggestion_feature**: implements
- **rel:mcp_tool_memory:work_items_table**: depends_on
- **rel:mem_ai_events:work_items**: depends_on
- **rel:mem_ai_feature_snapshot:mng_clients**: depends_on
- **rel:mem_ai_feature_snapshot:mng_projects**: depends_on
- **rel:mem_ai_feature_snapshot:planner_tags**: depends_on
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
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
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
- **mcp**: Stdio MCP server with 12+ tools (semantic search, work item management, session tagging, vector search)
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories
- **config_management**: config.py + YAML pipelines + pyproject.toml + aicli.yaml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extension
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
- **schema_management**: db_schema.sql (single source of truth) + db_migrations.py (m001-m027 framework)
- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; Shared: users, usage_logs, transactions, session_tags, entity_categories, planner_tags, mng_tags_categories
- **embeddings**: text-embedding-3-small (1536-dim vectors)

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags_relations, project_facts, work_items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with exec_llm boolean flag
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise
- mem_ai_feature_snapshot: unified layer merging planner_tags user requirements with work_items; captures summary, use cases, and delivery artifacts
- planner_tags deliveries column: JSONB field storing user-selected delivery artifact types (code, document, architect_design, ppt) after action_items
- Work item embedding integration: _embed_work_item() persists 1536-dim vectors for name_ai + desc_ai during /memory command execution
- MCP stdio server with 12+ tools including semantic search with vector embeddings on work_items table
- Multi-workflow trigger model: pipelines executable from planner UI, docs (feature snapshots), or direct chat; dashboard as new UI tab for pipeline visibility

## In Progress

- Dashboard/Pipeline Health tab implementation: 30-second auto-refresh showing commit_embed, session_summary, tag_match, work_item_embed status with pending/error counts and recent workflow runs visualization
- AI tag suggestion workflow bug fix: investigating missing ai_suggestion tags in UI and work item panel refresh; addressing work_item disappearance after tag approval and empty planner category display
- Workflow visibility architecture: designing multi-trigger pipeline execution model (planner, docs, chat) with unified orchestration and dashboard insights
- mem_ai_feature_snapshot table finalization: merging planner_tags user requirements with work_items tracking summary, use cases, and delivery artifacts per artifact type
- Work item embedding vector search: integrating _embed_work_item() persistence for name_ai + desc_ai concatenation with MCP semantic search on work_items table
- Pipeline template mapping: creating workflow-templates YAML with delivery_category/type → preferred_roles suggestions for code, architecture_design, document, and presentation deliveries

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **architecture-decision** `[open]`
- **customer-meeting** `[open]`
- **high-level-design** `[open]`
- **low-level-design** `[open]`
- **retrospective** `[open]`
- **Test** `[open]`

### Feature

- **pagination**
- **graph-workflow** `[open]`
- **auth** `[open]`
- **billing** `[open]`
- **test-picker-feature** `[open]`
- **mcp** `[open]`
- **entity-routing** `[open]`
- **shared-memory** `[open]`
- **tagging** `[open]`
- **workflow-runner** `[open]`
- **dropbox** `[open]`
- **embeddings** `[open]`
- **UI** `[open]`

### Phase

- **prod** `[open]`
- **development** `[open]`
- **discovery** `[open]`

### Task

- **memory** `[open]`
- **implement-projects-tab** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit: 6036bb3e-bf2f-49c8-9873-2d1cc5637f79` — 2026-04-12

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index d4e16fd..a1be707 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- mem_ai_feature_snapshot table design: new unified layer merging planner_tags user requirements with work_items; tracks summary, use cases, and delivery artifacts per use case
-- planner_tags deliveries column implementation: adding JSONB field after action_items for user-selected delivery artifacts (code, document, architect_design, ppt) with per-artifact type definitions
-- planner_tag schema finalization: m027 migration completed; creator field consolidates user/ai distinction; updater and timestamp fields added for audit trail
+- mem_ai_feature_snapshot table design: merge user requirements/tags with work_items; tracks summary, use cases, and delivery artifacts for comprehensive feature tracking
+- planner_tags deliveries column implementation: adding JSONB field after action_items for user-selected delivery artifacts (code, document, architect_design, ppt)
 - Work item embedding integration: _embed_work_item() persists 1536-dim vectors for name_ai + desc_ai concatenation during /memory command execution
 - Work item vector search in MCP: tool_memory.py semantic search includes work_items table with embedding <=> operator for non-archived items
-- Secondary AI tag workflow: _wiSecApprove stores confirmed metadata in ai_tags.confirmed[] array; items remain visible with permanent chip indicators
+- Workflow visibility improvements: exploring options to give more visibility into all flows and decision paths in the system
+- Pipeline execution architecture: designing second workflow trigger model based on approved features to enable more flexible pipeline orchestration


### `commit: 6036bb3e-bf2f-49c8-9873-2d1cc5637f79` — 2026-04-12

diff --git a/workspace/_templates/workflows/templates.yaml b/workspace/_templates/workflows/templates.yaml
new file mode 100644
index 0000000..232994d
--- /dev/null
+++ b/workspace/_templates/workflows/templates.yaml
@@ -0,0 +1,27 @@
+# Templates map delivery_category/type → workflow suggestion metadata.
+# Used by GET /memory/{project}/workflow-templates to suggest best-fit workflows.
+templates:
+  code/python:
+    name: "Python Code Delivery"
+    preferred_roles: [developer, tester, reviewer]
+  code/sql:
+    name: "SQL Migration"
+    preferred_roles: [developer, reviewer]
+  code/javascript:
+    name: "JavaScript Delivery"
+    preferred_roles: [developer, tester, reviewer]
+  code/typescript:
+    name: "TypeScript Delivery"
+    preferred_roles: [developer, tester, reviewer]
+  architecture_design/visio:
+    name: "Architecture Design"
+    preferred_roles: [architect, reviewer]
+  architecture_design/mermaid:
+    name: "Mermaid Diagram"
+    preferred_roles: [architect, developer]
+  document/markdown:
+    name: "Documentation"
+    preferred_roles: [developer, reviewer]
+  presentation/powerpoint:
+    name: "Presentation Deck"
+    preferred_roles: [architect]


### `commit: 6036bb3e-bf2f-49c8-9873-2d1cc5637f79` — 2026-04-12

diff --git a/ui/frontend/views/pipeline.js b/ui/frontend/views/pipeline.js
new file mode 100644
index 0000000..59f5051
--- /dev/null
+++ b/ui/frontend/views/pipeline.js
@@ -0,0 +1,192 @@
+/**
+ * pipeline.js — Pipeline Health Dashboard view.
+ *
+ * Renders background task health stats (commit_embed, session_summary, tag_match, etc.)
+ * with 30-second auto-refresh and links to recent workflow runs.
+ */
+
+import { api } from '../utils/api.js';
+import { toast } from '../utils/toast.js';
+
+let _refreshTimer = null;
+let _currentProject = null;
+
+export function destroyPipeline() {
+  if (_refreshTimer) {
+    clearInterval(_refreshTimer);
+    _refreshTimer = null;
+  }
+}
+
+export async function renderPipeline(container, project) {
+  destroyPipeline();
+  _currentProject = project;
+  container.innerHTML = `
+    <div style="padding:1.5rem;max-width:900px;margin:0 auto;overflow-y:auto;height:100%">
+      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.2rem">
+        <h2 style="margin:0;font-size:1.1rem">Pipeline Health</h2>
+        <button id="pipeline-refresh-btn" class="btn btn-ghost btn-sm" onclick="window._pipelineRefresh()">↻ Refresh</button>
+      </div>
+      <div id="pipeline-cards" style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.75rem;margin-bottom:1.5rem">
+        <div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">Loading…</div>
+      </div>
+      <div id="pipeline-pending" style="margin-bottom:1.2rem"></div>
+      <div id="pipeline-errors" style="margin-bottom:1.5rem"></div>
+      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.75rem">
+        <h3 style="margin:0;font-size:0.95rem">Recent Workflow Runs</h3>
+        <button class="btn btn-ghost btn-sm" onclick="window._nav('workflow')">→ Pipelines</button>
+      </div>
+      <div id="pipeline-runs">
+        <div style="color:var(--muted);font-size:0.8rem">Loading…</div>
+      </div>
+    </div>
+  `;
+
+  window._pipelineRefresh = () => _loadAll(container, project);
+  await _loadAll(container, project);
+
+  // Auto-refresh every 30s
+  _refreshTimer = setInterval(() => {
+    if (_currentProject === project) {
+      _loadAll(container, project);
+    }
+  }, 30_000);
+}
+
+const _PIPELINE_LABELS = {
+  commit_embed:         'commit_embed',
+  commit_store:         'commit_store',
+  commit_code_extract:  'commit_code',
+  session_summary:      'session_summary',
+  tag_match:            'tag_match',
+  work_item_embed:      'wi_embed',
+};
+
+function _fmtTime(iso) {
+  if (!iso) return '—';
+  const d = new Date(iso);
+  const now = new Date();
+  const diff = now - d;
+  if (diff < 60_000)  return `${Math.floor(diff/1000)}s ago`;
+  if (diff < 3600_000) return `${Math.floor(diff/60_000)}m ago`;
+  if (diff < 86400_000) return `${Math.floor(diff/3600_000)}h ago`;
+  return d.toLocaleDateString();
+}
+
+async function _loadAll(container, project) {
+  if (!project) {
+    container.querySelector('#pipeline-cards').innerHTML =
+      '<div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">No project selected</div>';
+    return;
+  }
+
+  try {
+    const [statusData, runsData] = await Promise.all([
+      api.pipeline.status(project).catch(() => null),
+      api.graphWorkflows.recentRuns(project, 10).catch(() => null),
+    ]);
+
+    _renderCards(container, statusData);
+    _renderPending(container, statusData);
+    _renderErrors(container, statusData);
+    _renderRuns(container, runsData);
+  } catch (e) {
+    console.warn('Pipeline load error:', e);
+  }
+}
+
+function _renderCards(container, data) {
+  const el = container.querySelector('#pipeline-cards');
+  if (!el) return;
+  if (!data) {
+    el.innerHTML = '<div style="color:var(--muted);font-size:0.8rem;grid-column:1/-1">Pipeline data unavailable</div>';
+    return;
+  }
+
+  const last24h = data.last_24h || {};
+  const pipelines = Object.keys(_PIPELINE_LABELS);
+
+  el.innerHTML = pipelines.map(key => {
+    const stats = last24h[key] || { ok: 0, error: 0, skipped: 0, last_run: null };
+    const hasData = stats.ok > 0 || stats.error > 0 || stats.skipped > 0;
+    const dotColor = !hasData ? 'var(--muted)' : stats.error > 0 ? 'var(--red, #e74c3c)' : 'var(--green, #27ae60)';
+    const label = _PIPELINE_LABELS[key] || key;
+    return `
+      <div style="background:var(--surface2);border-radius:var(--radius);padding:0.75rem;
+                  border:1px solid var(--border)">
+        <div style="display:flex;align-items:center;gap:0.4rem;margin-bottom:0.5rem">
+          <div style="width:7px;height:7px;border-radius:50%;background:${dotColor};flex-shrink:0"></div>
+          <span style="font-size:0.72rem;font-weight:600;color:var(--text);font-family:monospace">${label}</span>
+        </div>
+        <div style="font-size:0.72rem;color:var(--muted);display:flex;gap:0.6rem">
+          <span style="color:var(--green,#27ae60)">&#10003;${stats.ok}</span>
+          <span style="color:${stats.error>0?'var(--red,#e74c3c)':'var(--muted)'}">&#10007;${stats.error}</span>
+          <span>&#9197;${stats.skipped}</span>
+        </div>
+        <div style="font-size:0.65rem;color:var(--muted);margin-top:0.3rem">${_fmtTime(stats.last_run)}</div>
+      </div>
+    `;
+  }).join('');
+}
+
+function _renderPending(container, data) {
+  const el = container.querySelector('#pipeline-pending');
+  if (!el) return;
+  const pending = data?.pending || {};
+  const items = [];
+  if (pending.commits_not_embedded > 0)
+    items.push(`&#9888; Pending: ${pending.commits_not_embedded} commit${pending.commits_not_embedded !== 1 ? 's' : ''} not embedded`);
+  if (pending.work_items_unmatched > 0)
+    items.push(`&#9888; Pending: ${pending.work_items_unmatched} work item${pending.work_items_unmatched !== 1 ? 's' : ''} unmatched`);
+  el.innerHTML = items.map(t =>
+    `<div style="font-size:0.78rem;color:var(--accent);margin-bottom:0.

### `commit: 6036bb3e-bf2f-49c8-9873-2d1cc5637f79` — 2026-04-12

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index e1cd405..6c6f27a 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -10,6 +10,7 @@
 import { state } from '../stores/state.js';
 import { api } from '../utils/api.js';
 import { toast } from '../utils/toast.js';
+import { showWorkflowPicker } from '../utils/workflowPicker.js';
 import {
   loadTagCache, isCacheLoaded, getCacheProject,
   getCacheCategories, getCacheValues,
@@ -149,6 +150,8 @@ export function renderEntities(container) {
   window._plannerDrawerRemoveLink = _plannerDrawerRemoveLink;
   window._plannerGenerateSnapshot = _plannerGenerateSnapshot;
   window._plannerDrawerMerge      = _plannerDrawerMerge;
+  window._plannerWfPicker = (tagId, ucNum, ucSummary, project) =>
+    showWorkflowPicker(tagId, ucNum, ucSummary, project);
 
   window._plannerRunPlan = async (tagId, tagName, catName, project) => {
     const btn = document.getElementById('drawer-planner-btn');
@@ -1686,6 +1689,8 @@ function _plannerOpenDrawer(catId, valId) {
     const v = getCacheValues(catId).find(x => x.id === valId);
     if (v) _loadDrawerPipeline(selectedCatName, v.name, project);
   }
+  // Async: load feature snapshot use cases for workflow triggers
+  _loadDrawerSnapshot(valId, _plannerState.project);
 }
 
 function _plannerCloseDrawer() {
@@ -1695,6 +1700,40 @@ function _plannerCloseDrawer() {
   _drawerCatId = null;
 }
 
+async function _loadDrawerSnapshot(tagId, project) {
+  const el = document.getElementById('drawer-wf-uc-section');
+  if (!el) return;
+  try {
+    const snap = await api.tags.getSnapshot(tagId, project, 'user')
+      .catch(() => api.tags.getSnapshot(tagId, project, 'ai').catch(() => null));
+    if (!snap?.use_cases?.length) { el.innerHTML = ''; return; }
+    el.innerHTML = `
+      <div style="border-top:1px solid var(--border);padding-top:0.75rem">
+        <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);
+                    letter-spacing:.06em;margin-bottom:0.4rem">Use Cases</div>
+        ${snap.use_cases.map(uc => `
+          <div style="display:flex;align-items:center;justify-content:space-between;
+                      gap:0.4rem;margin-bottom:0.35rem">
+            <span style="font-size:0.67rem;color:var(--text2);overflow:hidden;
+                         text-overflow:ellipsis;white-space:nowrap;flex:1"
+                  title="${uc.use_case_summary||''}">
+              UC${uc.use_case_num}: ${uc.use_case_type||'feature'}
+            </span>
+            <button
+              onclick="window._plannerWfPicker('${tagId}',${uc.use_case_num},'${(uc.use_case_summary||'').replace(/'/g,'\\')}','${project}')"
+              style="font-size:0.6rem;padding:0.18rem 0.45rem;white-space:nowrap;
+                     background:var(--surface2);border:1px solid var(--border);
+                     border-radius:var(--radius);cursor:pointer;color:var(--accent);
+                     font-family:var(--font);outline:none;flex-shrink:0">
+              ▶ Workflow
+            </button>
+          </div>
+        `).join('')}
+      </div>
+    `;
+  } catch { el.innerHTML = ''; }
+}
+
 function _renderDrawer() {
   const inner = document.getElementById('planner-drawer-inner');
   if (!inner || !_drawerValId) return;
@@ -1920,6 +1959,9 @@ function _renderDrawer() {
         </div>
       </div>
 
+      <!-- Use Cases / Workflow -->
+      <div id="drawer-wf-uc-section"></div>
+
       <!-- Add sub-tag -->
       <div style="border-top:1px solid var(--border);padding-top:0.75rem">
         <div style="font-size:0.55rem;text-transform:uppercase;color:var(--muted);


### `commit: 6036bb3e-bf2f-49c8-9873-2d1cc5637f79` — 2026-04-12

diff --git a/ui/frontend/views/documents.js b/ui/frontend/views/documents.js
index dedb0da..457bd23 100644
--- a/ui/frontend/views/documents.js
+++ b/ui/frontend/views/documents.js
@@ -10,6 +10,7 @@
 import { api } from '../utils/api.js';
 import { toast } from '../utils/toast.js';
 import { renderMd } from '../utils/markdown.js';
+import { showWorkflowPicker } from '../utils/workflowPicker.js';
 
 const TREE_W_KEY = 'aicli_docs_tree_w';
 
@@ -249,6 +250,10 @@ function _renderViewer(path, content) {
   const viewer = document.getElementById('doc-viewer');
   if (!viewer) return;
   const isMd = path.endsWith('.md') || path.endsWith('.markdown');
+
+  // Detect feature snapshot files: features/<slug>/feature_ai.md or feature_final.md
+  const featureMatch = path.match(/^features\/([^/]+)\/(feature_ai|feature_final)\.md$/);
+
   viewer.innerHTML = `
     <div style="display:flex;align-items:center;justify-content:space-between;
                 padding:0.5rem 0.75rem;border-bottom:1px solid var(--border);flex-shrink:0">
@@ -256,6 +261,8 @@ function _renderViewer(path, content) {
         ${_esc(path)}
       </span>
       <div style="display:flex;gap:0.4rem;flex-shrink:0">
+        ${featureMatch ? `<button class="btn btn-ghost btn-sm" id="doc-workflow-btn"
+                style="font-size:0.65rem;padding:0.15rem 0.5rem;color:var(--accent)">▶ Workflow</button>` : ''}
         <button class="btn btn-ghost btn-sm" id="doc-edit-btn"
                 style="font-size:0.65rem;padding:0.15rem 0.5rem">Edit</button>
         <button class="btn btn-ghost btn-sm" id="doc-delete-btn"
@@ -271,6 +278,71 @@ function _renderViewer(path, content) {
   `;
   document.getElementById('doc-edit-btn').addEventListener('click', () => _editDoc(path, content));
   document.getElementById('doc-delete-btn').addEventListener('click', () => _deleteDoc(path));
+
+  if (featureMatch) {
+    const tagSlug = featureMatch[1];
+    document.getElementById('doc-workflow-btn').addEventListener('click', async () => {
+      try {
+        // Find tag by slug match (slugify tag name and compare)
+        const tags = await api.tags.list(_project);
+        const flatTags = [];
+        const flatten = (arr) => arr.forEach(t => { flatTags.push(t); if (t.children) flatten(t.children); });
+        flatten(tags);
+        const _slugify = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
+        const tag = flatTags.find(t => _slugify(t.name) === tagSlug);
+        if (!tag) { toast('Feature tag not found', 'warning'); return; }
+
+        const snap = await api.tags.getSnapshot(tag.id, _project, 'user')
+          .catch(() => api.tags.getSnapshot(tag.id, _project, 'ai').catch(() => null));
+        if (!snap?.use_cases?.length) { toast('No use cases found in snapshot', 'warning'); return; }
+
+        if (snap.use_cases.length === 1) {
+          const uc = snap.use_cases[0];
+          await showWorkflowPicker(tag.id, uc.use_case_num, uc.use_case_summary, _project);
+        } else {
+          // Multiple use cases — show a quick picker
+          const choice = await _pickUseCase(snap.use_cases);
+          if (choice) await showWorkflowPicker(tag.id, choice.use_case_num, choice.use_case_summary, _project);
+        }
+      } catch (e) {
+        toast(`Workflow error: ${e.message}`, 'error');
+      }
+    });
+  }
+}
+
+async function _pickUseCase(useCases) {
+  return new Promise(resolve => {
+    const overlay = document.createElement('div');
+    overlay.style.cssText = 'position:fixed;inset:0;z-index:9400;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,0.55)';
+    overlay.innerHTML = `
+      <div style="background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);
+                  padding:1.2rem;width:340px;max-width:95vw">
+        <div style="font-size:0.9rem;font-weight:600;margin-bottom:0.75rem">Select Use Case</div>
+        ${useCases.map(uc => `
+          <div data-uc="${uc.use_case_num}" style="padding:0.5rem 0.65rem;border-radius:var(--radius);
+               border:1px solid var(--border);margin-bottom:0.35rem;cursor:pointer;font-size:0.78rem;
+               background:var(--surface2)" onmouseenter="this.style.borderColor='var(--accent)'"
+               onmouseleave="this.style.borderColor='var(--border)'">
+            UC${uc.use_case_num}: ${uc.use_case_type||'feature'} — ${(uc.use_case_summary||'').slice(0,60)}
+          </div>
+        `).join('')}
+        <button style="margin-top:0.5rem;width:100%;background:none;border:1px solid var(--border);
+                border-radius:var(--radius);padding:0.35rem;cursor:pointer;font-size:0.75rem;color:var(--muted)"
+                id="uc-cancel-btn">Cancel</button>
+      </div>
+    `;
+    document.body.appendChild(overlay);
+    overlay.querySelectorAll('[data-uc]').forEach(el => {
+      el.addEventListener('click', () => {
+        const ucNum = parseInt(el.dataset.uc, 10);
+        const uc = useCases.find(u => u.use_case_num === ucNum);
+        overlay.remove(); resolve(uc || null);
+      });
+    });
+    overlay.querySelector('#uc-cancel-btn').onclick = () => { overlay.remove(); resolve(null); };
+    overlay.addEventListener('click', e => { if (e.target === overlay) { overlay.remove(); resolve(null); }});
+  });
 }
 
 function _editDoc(path, content) {


### `commit: 6036bb3e-bf2f-49c8-9873-2d1cc5637f79` — 2026-04-12

diff --git a/ui/frontend/views/chat.js b/ui/frontend/views/chat.js
index d67dc08..6e4ceeb 100644
--- a/ui/frontend/views/chat.js
+++ b/ui/frontend/views/chat.js
@@ -703,6 +703,7 @@ const COMMANDS = [
   { cmd: '/analytics',   args: '',                 desc: 'Show usage and cost stats'                },
   { cmd: '/history',     args: '',                 desc: 'Show last 20 commits'                     },
   { cmd: '/reload',      args: '',                 desc: 'Reload system prompt'                     },
+  { cmd: '/pipeline',   args: '[status]',          desc: 'Show pipeline health dashboard'           },
   { cmd: '/clear',       args: '',                 desc: 'Clear conversation history'               },
 ];
 
@@ -1208,7 +1209,8 @@ window._chatSend = async () => {
       `| \`/analytics\` | Show usage and cost stats |\n` +
       `| \`/history\` | Show last 20 commits |\n` +
       `| \`/reload\` | Reload system prompt |\n` +
-      `| \`/clear\` | Clear conversation history |`
+      `| \`/clear\` | Clear conversation history |\n` +
+      `| \`/pipeline [status]\` | Show pipeline health dashboard |`
     );
     return;
   }
@@ -1306,6 +1308,43 @@ window._chatSend = async () => {
   }
 
   // Handle /clear command locally
+
+  // Handle /pipeline [status] — show pipeline health as formatted message
+  if (message === '/pipeline' || message === '/pipeline status') {
+    input.value = '';
+    input.style.height = 'auto';
+    const proj = state.currentProject?.name;
+    if (!proj) { toast('No project open', 'error'); return; }
+    _appendSystemMsg('Fetching pipeline status…');
+    try {
+      const data = await api.pipeline.status(proj);
+      const last24h = data?.last_24h || {};
+      const pending = data?.pending || {};
+      const pipelines = ['commit_embed','commit_store','commit_code_extract','session_summary','tag_match','work_item_embed'];
+      const labels    = { commit_embed:'commit_embed', commit_store:'commit_store',
+                          commit_code_extract:'commit_code', session_summary:'session_summary',
+                          tag_match:'tag_match', work_item_embed:'wi_embed' };
+      let table = `## Pipeline Health — last 24h\n\n`;
+      table += `| Pipeline | OK | Errors | Skipped | Last Run |\n`;
+      table += `|---|---|---|---|---|\n`;
+      for (const key of pipelines) {
+        const s = last24h[key] || { ok: 0, error: 0, skipped: 0, last_run: null };
+        const lastRun = s.last_run ? new Date(s.last_run).toLocaleTimeString() : '—';
+        table += `| \`${labels[key]}\` | ${s.ok} | ${s.error} | ${s.skipped} | ${lastRun} |\n`;
+      }
+      const pendingLines = [];
+      if (pending.commits_not_embedded > 0) pendingLines.push(`- ${pending.commits_not_embedded} commit(s) not embedded`);
+      if (pending.work_items_unmatched > 0) pendingLines.push(`- ${pending.work_items_unmatched} work item(s) unmatched`);
+      if (pendingLines.length) table += `\n**Pending:**\n${pendingLines.join('\n')}`;
+      _appendSystemMsg(table);
+      // Also navigate to the Pipeline tab
+      window._nav('pipeline');
+    } catch (e) {
+      _appendSystemMsg(`**Pipeline status error:** ${e.message}`);
+    }
+    return;
+  }
+
   if (message === '/clear') {
     input.value = '';
     input.style.height = 'auto';


## AI Synthesis

**[2026-04-12]** `dev_history` — Identified UI regression: planner category display shows only work_items (not bug/ category); ai_suggestion tags not persisting in panel refresh; work_items disappear after tag approval. Root cause likely in work_item panel refresh workflow and ai_tag_suggestion column population.

**[2026-04-11]** `in_progress` — Pipeline Health dashboard implemented with 30-second auto-refresh showing status cards for commit_embed, session_summary, tag_match, work_item_embed; recent workflow runs linked to full pipeline view.

**[2026-04-10]** `in_progress` — mem_ai_feature_snapshot table design finalized: merges planner_tags (user requirements) with work_items (execution details); tracks summary, use cases, and delivery artifacts (code, document, architect_design, ppt) per artifact type.

**[2026-04-09]** `in_progress` — planner_tags deliveries JSONB column implementation: stores user-selected artifact types post action_items; m027 migration completed with creator, updater, and timestamp fields for audit trail.

**[2026-04-08]** `in_progress` — Work item embedding vector search integrated: _embed_work_item() persists 1536-dim vectors for concatenated name_ai + desc_ai; MCP tool_memory.py semantic search on work_items table with embedding <=> operator for non-archived items.

**[2026-04-07]** `in_progress` — Workflow trigger architecture designed: multi-model enabling pipeline execution from planner (work_items), docs (feature snapshots), and chat (direct initiation) with unified orchestration and new dashboard visibility tab.