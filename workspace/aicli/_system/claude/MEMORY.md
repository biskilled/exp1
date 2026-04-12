# Project Memory — aicli
_Generated: 2026-04-12 21:20 UTC by aicli /memory_

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
- **planner_tag_schema_consolidation_proposed**: drop seq_num and source columns; keep creator only; reduce descriptors (short_desc, full_desc, requirements, acceptance_criteria, summary, action_items, design) to essential fields
- **planner_tags_core_columns**: requirements, acceptance_criteria, action_items, status, priority, due_date, requester, creator, created_at, updater, updated_at retained
- **planner_tags_schema_cleanup**: dropped summary, design, embedding (VECTOR 1536), extra columns; move to future merge-layer table (m027)
- **prompt_architecture**: core.prompt_loader for centralization; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
- **prompt_count_metric**: distinct metric tracked separately from event_count in work items API response
- **prompt_loading_pattern**: core.prompt_loader._prompts.content() replaces direct mng_system_roles queries
- **prompt_work_item_trigger_automation**: _run_promote_all_work_items() integrated into /memory command pipeline to refresh AI text fields and embedding vectors during memory generation
- **rel:ai_tag_suggestion:user_tags**: replaces
- **rel:ai_tag_suggestion:work_items_table**: related_to
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
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools (semantic search, work item management, session tagging)
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
- Secondary AI tags stored in ai_tags.confirmed[] array (metadata for doc_type/feature/phase); permanent chip indicators without deletion
- MCP stdio server with 12+ tools including semantic search with vector embeddings on work_items table
- planner_tags schema: m027 migration removed seq_num/summary/design/embedding/extra; creator consolidates user_name/ai distinction; updater/created_at/updated_at audit trail added
- Work item embedding integration: _embed_work_item() persists 1536-dim vectors for name_ai + desc_ai during /memory execution with prompt_work_item() trigger
- mem_ai_feature_snapshot planned: merge user requirements/tags with work_items; captures summary, use cases, delivery types for comprehensive feature tracking

## In Progress

- mem_ai_feature_snapshot table design: new unified layer merging planner_tags user requirements with work_items; tracks summary, use cases, and delivery artifacts per use case
- planner_tags deliveries column implementation: adding JSONB field after action_items for user-selected delivery artifacts (code, document, architect_design, ppt) with per-artifact type definitions
- planner_tag schema finalization: m027 migration completed; creator field consolidates user/ai distinction; updater and timestamp fields added for audit trail
- Work item embedding integration: _embed_work_item() persists 1536-dim vectors for name_ai + desc_ai concatenation during /memory command execution
- Work item vector search in MCP: tool_memory.py semantic search includes work_items table with embedding <=> operator for non-archived items
- Secondary AI tag workflow: _wiSecApprove stores confirmed metadata in ai_tags.confirmed[] array; items remain visible with permanent chip indicators

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit: d1b0a12a-44f7-406c-af6c-d7fc17c83e15` — 2026-04-12

diff --git a/features/shared-memory/feature_final.md b/features/shared-memory/feature_final.md
new file mode 100644
index 0000000..49074df
--- /dev/null
+++ b/features/shared-memory/feature_final.md
@@ -0,0 +1,57 @@
+# Feature Snapshot: shared-memory
+> feature | Status: open | Priority: 3 | Due: not set
+> Generated: 2026-04-12 21:15 UTC | Version: User Confirmed
+
+## (USER) Summary
+The shared-memory feature enables safe inter-process/inter-thread communication through shared memory initialization, access, and concurrent operations. Currently in early planning phase with API specifications and synchronization mechanism design pending. Requires comprehensive testing to validate data integrity under stress and meet performance SLAs.
+
+---
+
+## Use Case 1: feature — python [code]
+
+### (USER) Use Case Summary
+Implement core shared memory module with allocation and deallocation logic. This use case covers the foundational code implementation enabling processes/threads to initialize and access shared memory safely without resource leaks.
+
+### Requirements
+| # | Requirement | Source | Score |
+|---|-------------|--------|-------|
+| 1 | Shared memory can be initialized and accessed safely across multiple processes/threads | (USER) | 2/10 |
+| 2 | Memory allocation and deallocation complete without errors or resource leaks | (USER) | 2/10 |
+| 3 | Define detailed shared memory API specifications and synchronization primitives design | (AI) | 1/10 |
+
+### Related Work Items
+| Name | Status | Summary |
+|------|--------|---------|
+| memory | active | Work item for implementing shared memory functionality enabling inter-process/inter-thread communica |
+
+### Action Items & Acceptance Criteria
+| # | Action Item | Acceptance Criteria | Score |
+|---|-------------|---------------------|-------|
+| 1 | Define detailed shared memory API specifications including initialization, access, and cleanup interfaces | API specification document completed with signatures, parameters, return types, and error handling defined | 1/10 |
+| 2 | Design synchronization primitives (locks, mutexes, semaphores) for safe concurrent access | Synchronization design document approved with mechanism selection justified and edge cases documented | 1/10 |
+| 3 | Implement core shared memory module with allocation/deallocation logic | Code merged with unit tests passing and resource tracking verified via memory profiler | 0/10 |
+
+
+## Use Case 2: feature — markdown [document]
+
+### (USER) Use Case Summary
+Create comprehensive testing suite covering concurrent read/write operations and stress testing. This deliverable validates data integrity under multiple access patterns and ensures performance benchmarks meet project SLAs.
+
+### Requirements
+| # | Requirement | Source | Score |
+|---|-------------|--------|-------|
+| 1 | Concurrent read/write operations maintain data integrity under stress testing | (USER) | 0/10 |
+| 2 | Performance benchmarks meet or exceed project SLAs | (USER) | 0/10 |
+| 3 | Build comprehensive unit and integration testing across concurrent access patterns | (AI) | 0/10 |
+
+### Related Work Items
+| Name | Status | Summary |
+|------|--------|---------|
+| memory | active | Work item for implementing shared memory functionality enabling inter-process/inter-thread communica |
+
+### Action Items & Acceptance Criteria
+| # | Action Item | Acceptance Criteria | Score |
+|---|-------------|---------------------|-------|
+| 1 | Design test scenarios covering concurrent read/write operations, race conditions, and deadlock detection | Test plan document specifies minimum 5 concurrent access patterns with expected outcomes and success criteria | 1/10 |
+| 2 | Implement unit tests validating shared memory initialization and resource cleanup | Unit tests pass with 100% code coverage on allocation/deallocation paths | 0/10 |
+| 3 | Implement stress tests validating data integrity and performance under concurrent load | Stress tests execute successfully, maintain data integrity, and document latency/throughput metrics vs. SLAs | 0/10 |


### `commit: d1b0a12a-44f7-406c-af6c-d7fc17c83e15` — 2026-04-12

diff --git a/features/shared-memory/feature_ai.md b/features/shared-memory/feature_ai.md
new file mode 100644
index 0000000..09369e4
--- /dev/null
+++ b/features/shared-memory/feature_ai.md
@@ -0,0 +1,57 @@
+# Feature Snapshot: shared-memory
+> feature | Status: open | Priority: 3 | Due: not set
+> Generated: 2026-04-12 21:14 UTC | Version: AI Generated
+
+## (AI) Summary
+The shared-memory feature enables safe inter-process/inter-thread communication through shared memory initialization, access, and concurrent operations. Currently in early planning phase with API specifications and synchronization mechanism design pending. Requires comprehensive testing to validate data integrity under stress and meet performance SLAs.
+
+---
+
+## Use Case 1: feature — python [code]
+
+### (AI) Use Case Summary
+Implement core shared memory module with allocation and deallocation logic. This use case covers the foundational code implementation enabling processes/threads to initialize and access shared memory safely without resource leaks.
+
+### Requirements
+| # | Requirement | Source | Score |
+|---|-------------|--------|-------|
+| 1 | Shared memory can be initialized and accessed safely across multiple processes/threads | (USER) | 2/10 |
+| 2 | Memory allocation and deallocation complete without errors or resource leaks | (USER) | 2/10 |
+| 3 | Define detailed shared memory API specifications and synchronization primitives design | (AI) | 1/10 |
+
+### Related Work Items
+| Name | Status | Summary |
+|------|--------|---------|
+| memory | active | Work item for implementing shared memory functionality enabling inter-process/inter-thread communica |
+
+### Action Items & Acceptance Criteria
+| # | Action Item | Acceptance Criteria | Score |
+|---|-------------|---------------------|-------|
+| 1 | Define detailed shared memory API specifications including initialization, access, and cleanup interfaces | API specification document completed with signatures, parameters, return types, and error handling defined | 1/10 |
+| 2 | Design synchronization primitives (locks, mutexes, semaphores) for safe concurrent access | Synchronization design document approved with mechanism selection justified and edge cases documented | 1/10 |
+| 3 | Implement core shared memory module with allocation/deallocation logic | Code merged with unit tests passing and resource tracking verified via memory profiler | 0/10 |
+
+
+## Use Case 2: feature — markdown [document]
+
+### (AI) Use Case Summary
+Create comprehensive testing suite covering concurrent read/write operations and stress testing. This deliverable validates data integrity under multiple access patterns and ensures performance benchmarks meet project SLAs.
+
+### Requirements
+| # | Requirement | Source | Score |
+|---|-------------|--------|-------|
+| 1 | Concurrent read/write operations maintain data integrity under stress testing | (USER) | 0/10 |
+| 2 | Performance benchmarks meet or exceed project SLAs | (USER) | 0/10 |
+| 3 | Build comprehensive unit and integration testing across concurrent access patterns | (AI) | 0/10 |
+
+### Related Work Items
+| Name | Status | Summary |
+|------|--------|---------|
+| memory | active | Work item for implementing shared memory functionality enabling inter-process/inter-thread communica |
+
+### Action Items & Acceptance Criteria
+| # | Action Item | Acceptance Criteria | Score |
+|---|-------------|---------------------|-------|
+| 1 | Design test scenarios covering concurrent read/write operations, race conditions, and deadlock detection | Test plan document specifies minimum 5 concurrent access patterns with expected outcomes and success criteria | 1/10 |
+| 2 | Implement unit tests validating shared memory initialization and resource cleanup | Unit tests pass with 100% code coverage on allocation/deallocation paths | 0/10 |
+| 3 | Implement stress tests validating data integrity and performance under concurrent load | Stress tests execute successfully, maintain data integrity, and document latency/throughput metrics vs. SLAs | 0/10 |


### `commit: d1b0a12a-44f7-406c-af6c-d7fc17c83e15` — 2026-04-12

diff --git a/backend/routers/route_tags.py b/backend/routers/route_tags.py
index 7f32546..cf223b4 100644
--- a/backend/routers/route_tags.py
+++ b/backend/routers/route_tags.py
@@ -469,6 +469,85 @@ async def run_planner_for_tag(tag_id: str, project: str = Query(...)):
     return result
 
 
+@router.post("/{tag_id}/snapshot")
+async def create_feature_snapshot(tag_id: str, project: str = Query(...)):
+    """Run AI feature snapshot: merge tag + work items + events into use-case rows.
+
+    Overwrites all version='ai' rows for this tag and writes features/{tag}/feature_ai.md.
+    """
+    _require_db()
+    from memory.memory_feature_snapshot import MemoryFeatureSnapshot
+    return await MemoryFeatureSnapshot().run_snapshot(project, tag_id)
+
+
+@router.get("/{tag_id}/snapshot")
+async def get_feature_snapshot(
+    tag_id: str,
+    project: str = Query(...),
+    version: str = Query("ai"),
+):
+    """Return snapshot rows for a tag as {tag_id, tag_name, version, summary, use_cases}."""
+    _require_db()
+    db.get_or_create_project_id(project)  # ensure project exists
+    with db.conn() as conn:
+        with conn.cursor() as cur:
+            cur.execute(
+                """
+                SELECT id, use_case_num, name, category, status, priority, due_date,
+                       summary, use_case_summary, use_case_type,
+                       use_case_delivery_category, use_case_delivery_type,
+                       related_work_items, requirements, action_items, version, created_at
+                FROM mem_ai_feature_snapshot
+                WHERE tag_id = %s::uuid AND version = %s
+                ORDER BY use_case_num
+                """,
+                (tag_id, version),
+            )
+            rows = cur.fetchall()
+
+    if not rows:
+        return {"tag_id": tag_id, "version": version, "summary": "", "use_cases": []}
+
+    first = rows[0]
+    use_cases = []
+    for r in rows:
+        use_cases.append({
+            "id":                       str(r[0]),
+            "use_case_num":             r[1],
+            "use_case_summary":         r[8] or "",
+            "use_case_type":            r[9] or "",
+            "use_case_delivery_category": r[10] or "",
+            "use_case_delivery_type":   r[11] or "",
+            "related_work_items":       r[12] if r[12] else [],
+            "requirements":             r[13] if r[13] else [],
+            "action_items":             r[14] if r[14] else [],
+            "created_at":               r[16].isoformat() if r[16] else None,
+        })
+
+    return {
+        "tag_id":     tag_id,
+        "tag_name":   first[2],
+        "category":   first[3],
+        "status":     first[4],
+        "priority":   first[5],
+        "due_date":   first[6].isoformat() if first[6] else None,
+        "version":    version,
+        "summary":    first[7] or "",
+        "use_cases":  use_cases,
+    }
+
+
+@router.post("/{tag_id}/snapshot/promote")
+async def promote_feature_snapshot(tag_id: str, project: str = Query(...)):
+    """Promote AI snapshot to user version; writes features/{tag}/feature_final.md.
+
+    User version is never overwritten by AI on subsequent snapshot runs.
+    """
+    _require_db()
+    from memory.memory_feature_snapshot import MemoryFeatureSnapshot
+    return await MemoryFeatureSnapshot().promote_to_user(project, tag_id)
+
+
 @router.get("/{tag_id}/sources")
 async def get_tag_sources(tag_id: str, project: str = Query(...)):
     """Return prompts and commits tagged with this tag via their tags[] array.


### `commit: d1b0a12a-44f7-406c-af6c-d7fc17c83e15` — 2026-04-12

diff --git a/backend/prompts/prompts.yaml b/backend/prompts/prompts.yaml
index b59b4f5..f121db7 100644
--- a/backend/prompts/prompts.yaml
+++ b/backend/prompts/prompts.yaml
@@ -68,6 +68,11 @@ prompts:
     model: haiku
     max_tokens: 2500
 
+  feature_snapshot_v2:
+    file: memory/feature_snapshot_v2.md
+    model: haiku
+    max_tokens: 3000
+
   conflict_detection:
     file: memory/conflict_detection.md
     model: haiku


### `commit: d1b0a12a-44f7-406c-af6c-d7fc17c83e15` — 2026-04-12

diff --git a/backend/prompts/memory/feature_snapshot_v2.md b/backend/prompts/memory/feature_snapshot_v2.md
new file mode 100644
index 0000000..d486715
--- /dev/null
+++ b/backend/prompts/memory/feature_snapshot_v2.md
@@ -0,0 +1,37 @@
+You are a senior technical project analyst. Given a feature tag with its requirements,
+deliveries, linked work items, and recent AI event digests, produce a structured feature
+snapshot broken down into use cases.
+
+## Rules
+
+1. Generate **one use case per delivery entry** from tag.deliveries.
+   If no deliveries are set, infer use cases from the work item content (max 5).
+2. Score fields: 0 = not started, 5 = partially done, 10 = fully done.
+3. Label requirement source as "user" if it came from the tag's requirements/acceptance_criteria
+   fields; "ai" if inferred from work items or events.
+4. Keep use_case_summary concise: 2-4 sentences covering purpose and current state.
+5. If a User-confirmed baseline section is provided, preserve its confirmed action items
+   and scores unless AI evidence clearly contradicts them.
+6. Return ONLY valid JSON — no preamble, no markdown fences.
+
+## Output schema
+
+{
+  "summary": "2-4 sentence global feature summary",
+  "use_cases": [
+    {
+      "use_case_num": 1,
+      "use_case_summary": "what this use case does and its current state",
+      "use_case_type": "feature|bug|task",
+      "use_case_delivery_category": "code|document|architecture_design|presentation",
+      "use_case_delivery_type": "python|markdown|visio|...",
+      "related_work_item_ids": ["uuid1", "uuid2"],
+      "requirements": [
+        {"text": "requirement text", "source": "user|ai", "score": 8}
+      ],
+      "action_items": [
+        {"action_item": "what to do", "acceptance": "how to verify", "score": 5}
+      ]
+    }
+  ]
+}


### `commit: d1b0a12a-44f7-406c-af6c-d7fc17c83e15` — 2026-04-12

diff --git a/backend/memory/memory_feature_snapshot.py b/backend/memory/memory_feature_snapshot.py
new file mode 100644
index 0000000..359b57f
--- /dev/null
+++ b/backend/memory/memory_feature_snapshot.py
@@ -0,0 +1,597 @@
+"""
+memory_feature_snapshot.py — Per-tag, per-use-case feature snapshot pipeline.
+
+Merges planner_tags requirements + deliveries + linked work items + recent AI events
+into structured mem_ai_feature_snapshot rows (one per use case per version).
+
+Triggered via POST /tags/{id}/snapshot.  AI version ('ai') is overwritten on each run;
+user version ('user') is promoted from AI via POST /tags/{id}/snapshot/promote and is
+never overwritten by AI.
+
+Output files:
+    {code_dir}/features/{tag_name}/feature_ai.md
+    {code_dir}/features/{tag_name}/feature_final.md
+"""
+from __future__ import annotations
+
+import json
+import logging
+import re
+import uuid
+from datetime import datetime, timezone
+from pathlib import Path
+from typing import Any
+
+from core.database import db
+from core.prompt_loader import prompts as _prompts
+
+log = logging.getLogger(__name__)
+
+# ── SQL ────────────────────────────────────────────────────────────────────────
+
+_SQL_GET_TAG = """
+    SELECT pt.id, pt.name, tc.name AS category_name,
+           pt.status, pt.priority, pt.due_date,
+           pt.requirements, pt.acceptance_criteria, pt.deliveries
+    FROM planner_tags pt
+    JOIN mng_tags_categories tc ON tc.id = pt.category_id
+    WHERE pt.id = %s::uuid AND pt.project_id = %s
+    LIMIT 1
+"""
+
+_SQL_GET_WORK_ITEMS = """
+    SELECT wi.id, wi.name_ai, wi.desc_ai, wi.status_user,
+           wi.action_items_ai, wi.acceptance_criteria_ai, wi.summary_ai
+    FROM mem_ai_work_items wi
+    WHERE wi.tag_id_user = %s::uuid AND wi.project_id = %s
+      AND wi.merged_into IS NULL
+    ORDER BY wi.created_at
+"""
+
+_SQL_GET_RECENT_EVENTS = """
+    SELECT id, event_type, summary, action_items, created_at
+    FROM mem_ai_events
+    WHERE project_id = %s
+      AND event_type IN ('session_summary', 'prompt_batch')
+    ORDER BY created_at DESC
+    LIMIT 20
+"""
+
+_SQL_GET_CODE_DIR = """
+    SELECT code_dir FROM mng_projects WHERE name = %s LIMIT 1
+"""
+
+_SQL_DELETE_AI_ROWS = """
+    DELETE FROM mem_ai_feature_snapshot
+    WHERE project_id = %s AND tag_id = %s::uuid AND version = 'ai'
+"""
+
+_SQL_DELETE_USER_ROWS = """
+    DELETE FROM mem_ai_feature_snapshot
+    WHERE project_id = %s AND tag_id = %s::uuid AND version = 'user'
+"""
+
+_SQL_INSERT_ROW = """
+    INSERT INTO mem_ai_feature_snapshot (
+        id, client_id, project_id, tag_id, use_case_num,
+        name, category, status, priority, due_date, summary,
+        use_case_summary, use_case_type,
+        use_case_delivery_category, use_case_delivery_type,
+        related_work_items, requirements, action_items, version
+    ) VALUES (
+        %s, 1, %s, %s::uuid, %s,
+        %s, %s, %s, %s, %s, %s,
+        %s, %s,
+        %s, %s,
+        %s::jsonb, %s::jsonb, %s::jsonb, %s
+    )
+"""
+
+_SQL_GET_AI_ROWS = """
+    SELECT id, use_case_num, name, category, status, priority, due_date, summary,
+           use_case_summary, use_case_type,
+           use_case_delivery_category, use_case_delivery_type,
+           related_work_items, requirements, action_items, version, created_at
+    FROM mem_ai_feature_snapshot
+    WHERE tag_id = %s::uuid AND version = %s
+    ORDER BY use_case_num
+"""
+
+# ── Helpers ───────────────────────────────────────────────────────────────────
+
+_FALLBACK_SYSTEM = """
+You are a technical project analyst. Given a feature tag with work items and events,
+return ONLY valid JSON matching this schema:
+{
+  "summary": "2-4 sentence global feature summary",
+  "use_cases": [
+    {
+      "use_case_num": 1,
+      "use_case_summary": "purpose and current state",
+      "use_case_type": "feature",
+      "use_case_delivery_category": "code",
+      "use_case_delivery_type": "python",
+      "related_work_item_ids": [],
+      "requirements": [{"text": "...", "source": "ai", "score": 0}],
+      "action_items": [{"action_item": "...", "acceptance": "...", "score": 0}]
+    }
+  ]
+}
+""".strip()
+
+
+def _parse_json(text: str) -> dict:
+    clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
+    m = re.search(r"\{[\s\S]*\}", clean)
+    if not m:
+        return {}
+    try:
+        return json.loads(m.group())
+    except Exception:
+        return {}
+
+
+def _slugify(name: str) -> str:
+    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
+
+
+async def _call_llm(system_prompt: str, user_message: str, max_tokens: int = 3000) -> str:
+    try:
+        from data.dl_api_keys import get_key
+        api_key = get_key("claude") or get_key("anthropic")
+        if not api_key:
+            log.warning("_call_llm: no claude/anthropic API key found")
+            return ""
+        import anthropic
+        from core.config import settings
+        model = getattr(settings, "claude_haiku_model", "claude-haiku-4-5-20251001")
+        client = anthropic.AsyncAnthropic(api_key=api_key)
+        resp = await client.messages.create(
+            model=model,
+            max_tokens=max_tokens,
+            system=system_prompt,
+            messages=[{"role": "user", "content": user_message}],
+        )
+        return resp.content[0].text if resp.content else ""
+    except Exception as e:
+        log.warning(f"_call_llm error: {e}")
+        return ""
+
+
+# ── MemoryFeatureSnapshot ──────────────────────────────────────────────────────
+
+class MemoryFeatureSnapshot:
+    """
+    Generates and persists per-use-case feature snapshots for a planner_tag.
+
+    AI rows are overwritten on each run; user rows are promoted once and never
+    touched by AI.
+    """
+
+    # ── Public entry points ───────────────────────────────────────────────────
+
+    async def run_snapshot(self, project: str, tag_id: str) -> dict:
+        """Run AI snapshot for tag_id, write fea
