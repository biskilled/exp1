# Project Memory — aicli
_Generated: 2026-04-12 11:19 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a FastAPI backend, PostgreSQL with pgvector semantic search, Python CLI with rich formatting, and an Electron desktop UI (Vanilla JS + xterm.js + Monaco + Cytoscape). It captures development sessions via 4-layer architecture (ephemeral → raw commits → LLM-digested events → semantic work items), with Claude-powered dual-layer synthesis, async DAG workflows, MCP tool server, and multi-provider LLM support (Claude/OpenAI/DeepSeek). Current focus is completing schema cleanup (planner_tag table optimization), finalizing work item embedding integration, and refining secondary AI tag workflows for production use.

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
- **config_management**: config.py + YAML pipelines + pyproject.toml + aicli.yaml
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
- Work item column naming: name_ai, category_ai, desc_ai, summary_ai consolidated for consistency; FK architecture links mem_ai_events.work_item_id to work items
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with exec_llm boolean flag
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise
- Secondary AI tags stored in ai_tags.confirmed[] array (metadata for doc_type/feature/phase); permanent chip indicators without deletion
- Work item counters: prompt_count (raw prompts), event_count (prompt_batch/session_summary), commit_count (distinct commits per session)
- MCP stdio server with 12+ tools including semantic search with vector embeddings on work_items table
- Railway cloud deployment (Dockerfile + railway.toml) + Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)

## In Progress

- planner_tag table schema cleanup: identified seq_num (always null, no auto-population) for removal; consolidating source + creator into single creator field; removing redundant code_summary column; verifying status column uniqueness vs. work_items.status_user/status_ai
- Work item embedding integration: _embed_work_item() persists vectors for name_ai + desc_ai + summary_ai concatenation; integrated into prompt_work_item() trigger during /memory command execution
- Work item vector search in MCP: tool_memory.py semantic search includes work_items table with embedding <=> operator, returning category/name/description/status for non-archived items
- Secondary AI tag workflow refinement: _wiSecApprove stores confirmed metadata in ai_tags.confirmed[] array; items remain visible with permanent chip indicators instead of deletion
- prompt_work_item() trigger automation: integrated _run_promote_all_work_items() into /memory command pipeline to refresh AI text fields and embedding vectors
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

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 4eb4e1b..a84bfcc 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Work item column schema refactoring: renamed ai_name→name_ai, ai_category→category_ai, ai_desc→desc_ai for naming consistency; consolidated summary into desc_ai to reduce column redundancy
-- prompt_work_item() trigger refinement: integrated to run automatically during /memory command execution to ensure work item columns reflect latest AI naming conventions and data consolidation
+- Work item column schema refactoring: completed renaming ai_name→name_ai, ai_category→category_ai, ai_desc→desc_ai, summary→summary_ai across frontend (entities.js) and backend (route_work_items.py, route_projects.py) for naming consistency
+- prompt_work_item() trigger integration: added _run_promote_all_work_items() to /memory command execution pipeline to refresh AI text fields and status during memory generation
+- Secondary AI tag workflow refinement: _wiSecApprove stores confirmed metadata (doc_type/phase/component) in ai_tags.confirmed[] array; items remain visible with permanent chip indicators instead of deletion
 - Work item UI loading states: _wiRowLoading() CSS pulsing animation during async delete/approve/dismiss operations; integrated into tag-linked and unlinked panels with error state recovery
-- Secondary AI tag workflow: _wiSecApprove stores confirmed metadata (doc_type/phase/component) in ai_tags.confirmed[] array; items remain visible with permanent chip indicators instead of deletion
-- Tag-linked work item refresh: _loadTagLinkedWorkItems reloads after approve/reject; planner table updates reflect linked/unlinked status changes when category selected
-- AI tag suggestion UX: clickable ✓ creates missing ai_suggestion tags with category inference; tooltip messaging improved from 'No existing tag' to 'Does not exist yet'
+- Tag-linked work item refresh: _loadTagLinkedWorkItems reloads after approve/reject operations; planner table updates reflect linked/unlinked status changes when category selected
+- AI tag suggestion UX: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip messaging improved from 'No existing tag' to 'Does not exist yet'


### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 1e4bc07..abdeea3 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-12 00:03 UTC
+> Generated by aicli 2026-04-12 11:08 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -58,9 +58,9 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
-- Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; source_event_id pivot for session-based aggregation
+- Work item column naming convention: ai_name → name_ai, ai_category → category_ai, ai_desc → desc_ai, summary → summary_ai for consistency; FK architecture links many events to one work item
 - Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
 - Secondary AI tags stored in ai_tags.confirmed[] array (metadata for doc_type/feature/phase); primary tag_id links work item to category
-- Work item column naming convention: ai_name → name_ai, ai_category → category_ai, ai_desc → desc_ai for consistency; summary merged into desc_ai
 - Work item counters: prompt_count (raw prompts in source session), event_count (prompt_batch/session_summary events), commit_count (distinct commits per session)
-- Session tagging: /stag command with immediate tag propagation via log_user_prompt.sh reading .agent-context
\ No newline at end of file
+- Session tagging: /stag command with immediate tag propagation via log_user_prompt.sh reading .agent-context
+- Railway cloud deployment (Dockerfile + railway.toml) + Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
\ No newline at end of file


### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index fbc7b43..d2538a6 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-12 00:03 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-12 11:08 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -58,12 +58,12 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
-- Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; source_event_id pivot for session-based aggregation
+- Work item column naming convention: ai_name → name_ai, ai_category → category_ai, ai_desc → desc_ai, summary → summary_ai for consistency; FK architecture links many events to one work item
 - Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
 - Secondary AI tags stored in ai_tags.confirmed[] array (metadata for doc_type/feature/phase); primary tag_id links work item to category
-- Work item column naming convention: ai_name → name_ai, ai_category → category_ai, ai_desc → desc_ai for consistency; summary merged into desc_ai
 - Work item counters: prompt_count (raw prompts in source session), event_count (prompt_batch/session_summary events), commit_count (distinct commits per session)
 - Session tagging: /stag command with immediate tag propagation via log_user_prompt.sh reading .agent-context
+- Railway cloud deployment (Dockerfile + railway.toml) + Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
 
 ## Recent Context (last 5 changes)
 


### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

diff --git a/.ai/rules.md b/.ai/rules.md
index fbc7b43..d2538a6 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-12 00:03 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-12 11:08 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -58,12 +58,12 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
-- Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; source_event_id pivot for session-based aggregation
+- Work item column naming convention: ai_name → name_ai, ai_category → category_ai, ai_desc → desc_ai, summary → summary_ai for consistency; FK architecture links many events to one work item
 - Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
 - Secondary AI tags stored in ai_tags.confirmed[] array (metadata for doc_type/feature/phase); primary tag_id links work item to category
-- Work item column naming convention: ai_name → name_ai, ai_category → category_ai, ai_desc → desc_ai for consistency; summary merged into desc_ai
 - Work item counters: prompt_count (raw prompts in source session), event_count (prompt_batch/session_summary events), commit_count (distinct commits per session)
 - Session tagging: /stag command with immediate tag propagation via log_user_prompt.sh reading .agent-context
+- Railway cloud deployment (Dockerfile + railway.toml) + Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
 
 ## Recent Context (last 5 changes)
 


### `commit: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

Removed outdated agent context and system documentation files as part of cleanup work.

### `session_summary: d535da3e-a9f3-44f3-80e0-4c18e0404f00` — 2026-04-12

Summary:
• User requested to work on planner_tag and change the tag to feature:planner
• Session tags updated to phase: development and feature: planner

## AI Synthesis

**[2026-04-12]** `claude_cli` — Comprehensive schema audit of planner_tag table identified three removal candidates: seq_num (never populated, no auto-logic), code_summary (unused), and source/creator consolidation (redundant dual-tracking). Recommended single status column instead of status/status_user/status_ai split. **[2026-04-12]** `work-item-embedding` — Completed work item column naming migration (ai_name→name_ai, ai_category→category_ai, ai_desc→desc_ai, summary→summary_ai) across frontend and backend. Integrated _embed_work_item() vector persistence into prompt_work_item() trigger during /memory command execution. **[2026-04-12]** `mcp-vector-search` — Enhanced MCP semantic search tool_memory.py to include work_items table vector queries using embedding <=> operator, enabling semantic work item discovery with category/status metadata filtering. **[2026-04-12]** `secondary-ai-tags` — Finalized secondary AI tag workflow storing confirmed metadata (doc_type/phase/component) in ai_tags.confirmed[] array as permanent chip indicators instead of deletions, improving audit trail and UX. **[2026-04-12]** `tag-suggestion-ux` — Refined AI tag suggestion panel with clickable ✓ buttons that auto-create missing ai_suggestion tags with category inference; improved tooltip messaging to clarify intent ("Does not exist yet" vs "No existing tag"). **[2026-04-12]** `tag-linked-refresh` — Completed tag-linked work item refresh workflow ensuring _loadTagLinkedWorkItems reloads after approve/reject operations with planner table status sync.