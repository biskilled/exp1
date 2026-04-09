# Project Memory — aicli
_Generated: 2026-04-09 13:46 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI + FastAPI backend + Electron desktop UI to capture, synthesize, and search developer context across projects. It uses PostgreSQL with pgvector for semantic search, Claude Haiku for dual-layer memory synthesis, and async DAG workflows for LLM-powered task automation. Currently focusing on session tagging, work item refresh mechanisms, and tag backlinking to ensure consistent context capture across commits, prompts, and work items.

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
- **event_count_column_semantics**: renamed from 'Total events' to 'Digest count'; now counts only prompt_batch + session_summary event types, not all session events
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
- **rel:work_item_deletion:api_endpoint**: depends_on
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
- **database**: PostgreSQL 15+ with pgvector extensions; unified mem_ai_* tables; per-project schema
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
- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories

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
- AI suggestion system: category-aware matching (task/bug/feature prioritized), Level 4 fallback to suggest new when no matches ≥0.70, 0.60 confidence threshold
- Tag backlinking: PATCH /work-items with tag_id triggers _backlink_tag_to_events() propagating assignments to all events in source session
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
- Session tagging via /tag command with tag_reminder_interval config (every N prompts); valid_tag_keys enforced (phase required, feature/bug/task/component/doc_type/design/decision/meeting/customer optional)
- Stdio MCP server with 12+ tools for semantic search, work item management, and session tag updates; embedding pipeline triggered via /memory endpoint

## In Progress

- Session tagging command (/tag) implementation: added tag_reminder_interval config to aicli.yaml with periodic prompt reminders (every 5-10 prompts) to validate prompt relevance to tagged context
- MCP set_session_tags tool documentation: updated schema to clarify phase as required, feature/bug_ref as optional, and 'extra' object for flexible tag categories (task, component, doc_type, design, decision, meeting, customer)
- Tag skill loading in Claude Code: sessions must be restarted to pick up new /tag skill definition; multi-tag syntax supported (phase:development feature:work-items-ui bug:login-500)
- Work item refresh workflow: refresh button triggers /work-items/rematch-all endpoint to refetch unlinked items and update AI tag suggestions in real-time
- Event count aggregation: 'Digests' column displays session-based COUNT(*) from mem_ai_events filtered to prompt_batch and session_summary types only
- AI tag backlinking propagation: tag assignments to work items automatically propagate to all events in source session via category→tag_key mapping (bug/phase/feature)

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
- **graph-workflow** `[open]`
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

### Phase

- **discovery** `[open]`
- **prod** `[open]`
- **development** `[open]`

### Task

- **memory** `[open]`
- **implement-projects-tab** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 7f4aafa..e8a3ddd 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -376,8 +376,8 @@ All tables follow a structured naming convention:
 ## Recent Work
 
 - Work item refresh workflow: replaced 'new work item' button with ↻ refresh button triggering /work-items/rematch-all endpoint to refetch unlinked items and update AI tag suggestions
-- Event count aggregation: added event_count column to work item panel calculated via session-based COUNT(*) from mem_ai_events matching source_event_id's session
+- Event count aggregation: added event_count column (renamed to 'Digests') to work item panel calculated via session-based COUNT(*) from mem_ai_events matching prompt_batch and session_summary types only
 - AI tag backlinking implementation: _backlink_tag_to_events() propagates planner tag assignments back to all events in source session, mapping category→tag_key (bug/phase/feature)
-- Work item panel UI refinement: adjusted colgroup widths (52px per count column), fixed table overflow issues showing only first column, added proper padding/spacing
-- AI tag suggestion debugging: investigating missing suggested_new tags in ui_tags query and verifying ai_suggestion column population in work item panel refresh workflow
+- Work item panel UI refinement: adjusted colgroup widths (52px per count column), fixed table overflow issues, added proper padding/spacing, updated event_count header label to 'Digests'
 - Session-based tag propagation: enabled tag_id field in PATCH /work-items endpoint to trigger async backlinking, ensuring tag consistency across event-to-work-item relationships
+- Interactive tag suggestion feature: user request for mechanism to force-add tags during long sessions and periodically (every 5-10 prompts) validate prompt relevance to tagged context


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/agents/mcp/server.py b/backend/agents/mcp/server.py
index 921f264..7f3811a 100644
--- a/backend/agents/mcp/server.py
+++ b/backend/agents/mcp/server.py
@@ -223,8 +223,10 @@ async def list_tools() -> list[mcp_types.Tool]:
         mcp_types.Tool(
             name="set_session_tags",
             description=(
-                "Update the active session tags (phase, feature, bug_ref). "
-                "Call this when you understand the current task to ensure proper tracking."
+                "Update the active session tags. Call this when you understand the current task "
+                "to ensure prompts and commits are correctly tagged. "
+                "phase is required. feature and bug_ref are optional. "
+                "extra accepts any key:value pairs from: task, component, doc_type, design, decision, meeting, customer."
             ),
             inputSchema={
                 "type": "object",
@@ -232,12 +234,17 @@ async def list_tools() -> list[mcp_types.Tool]:
                     "phase": {
                         "type": "string",
                         "enum": _PHASES,
-                        "description": "Project phase",
+                        "description": "Project phase (required)",
+                    },
+                    "feature": {"type": "string", "description": "Feature slug being worked on (e.g. work-items-ui)"},
+                    "bug_ref": {"type": "string", "description": "Bug slug if fixing a bug (e.g. login-500)"},
+                    "extra": {
+                        "type": "object",
+                        "description": "Additional tags: {task, component, doc_type, design, decision, meeting, customer}",
                     },
-                    "feature": {"type": "string", "description": "Feature name being worked on"},
-                    "bug_ref": {"type": "string", "description": "Bug reference if fixing a bug"},
                     "project": {"type": "string"},
                 },
+                "required": ["phase"],
             },
         ),
         mcp_types.Tool(


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/aicli.yaml b/aicli.yaml
index 40b6df5..105272b 100644
--- a/aicli.yaml
+++ b/aicli.yaml
@@ -22,6 +22,14 @@ test_command: "pytest"
 memory_enabled: true
 memory_top_k: 5
 
+# ------------------------------------------------------------------
+# SESSION TAGGING
+# ------------------------------------------------------------------
+session:
+  tag_reminder_interval: 8   # print "still on X?" reminder every N prompts (0 = off)
+  # valid_tag_keys are enforced in the hook — keys not in this list are rejected
+  valid_tag_keys: [phase, feature, bug, task, component, doc_type, design, decision, meeting, customer]
+
 # ------------------------------------------------------------------
 # MEMORY BATCH SYSTEM
 # ------------------------------------------------------------------


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 876af3d..7476591 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-09 12:13 UTC
+> Generated by aicli 2026-04-09 12:20 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -63,4 +63,4 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Tag backlinking: PATCH /work-items with tag_id triggers _backlink_tag_to_events() propagating assignments to all events in source session
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb) for desktop
-- AI tag display: category:name format when both present, falls back to name-only; default color #4a90e2 applied when ai_tag_color not set
\ No newline at end of file
+- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index bdf7158..c2cc1ab 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 12:13 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 12:20 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -63,12 +63,12 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Tag backlinking: PATCH /work-items with tag_id triggers _backlink_tag_to_events() propagating assignments to all events in source session
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb) for desktop
-- AI tag display: category:name format when both present, falls back to name-only; default color #4a90e2 applied when ai_tag_color not set
+- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] Can you explain how do I see work_item #20006 as the one that was last updated ? the last prompt was about ui, ai tags..
 - [2026-04-09] Can you recheck that ai_tags as I do see new work_item, bit cannot see any sujjeste AI - all i see is mepy AI(EXISTS).. 
 - [2026-04-09] Where are all the rpompts for ai_tags and work_item are ?
 - [2026-04-09] I do see same work item working on mention document summery and update ai memory. all internal work such update internal
-- [2026-04-09] Can you share the quesry you are suing the get all promotps, commit, event per work_item . I want to check that for work
\ No newline at end of file
+- [2026-04-09] Can you share the quesry you are suing the get all promotps, commit, event per work_item . I want to check that for work
+- [2026-04-09] before you desing. is it possible to add some mechanism to our converstion. for example force adding tags and every 5-10
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.ai/rules.md b/.ai/rules.md
index bdf7158..c2cc1ab 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 12:13 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 12:20 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -63,12 +63,12 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Tag backlinking: PATCH /work-items with tag_id triggers _backlink_tag_to_events() propagating assignments to all events in source session
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb) for desktop
-- AI tag display: category:name format when both present, falls back to name-only; default color #4a90e2 applied when ai_tag_color not set
+- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] Can you explain how do I see work_item #20006 as the one that was last updated ? the last prompt was about ui, ai tags..
 - [2026-04-09] Can you recheck that ai_tags as I do see new work_item, bit cannot see any sujjeste AI - all i see is mepy AI(EXISTS).. 
 - [2026-04-09] Where are all the rpompts for ai_tags and work_item are ?
 - [2026-04-09] I do see same work item working on mention document summery and update ai memory. all internal work such update internal
-- [2026-04-09] Can you share the quesry you are suing the get all promotps, commit, event per work_item . I want to check that for work
\ No newline at end of file
+- [2026-04-09] Can you share the quesry you are suing the get all promotps, commit, event per work_item . I want to check that for work
+- [2026-04-09] before you desing. is it possible to add some mechanism to our converstion. for example force adding tags and every 5-10
\ No newline at end of file


## AI Synthesis

**[2026-04-09]** `claude_cli` — Session tagging (/tag) command requires new session restart to be recognized; updated MCP set_session_tags tool schema to clarify phase as required parameter and added flexible 'extra' object for optional tag categories (task, component, doc_type, design, decision, meeting, customer). **[2026-03-14]** `in_progress` — Work item refresh workflow now uses ↻ button instead of 'new work item' to trigger /work-items/rematch-all endpoint for real-time AI tag suggestion updates. **[2026-03-14]** `in_progress` — Event count aggregation renamed 'Digests' column, filtering mem_ai_events to only prompt_batch and session_summary types to exclude per-commit and diff_file noise. **[2026-03-14]** `in_progress` — AI tag backlinking via PATCH /work-items propagates tag assignments to all events in source session using category→tag_key mapping for bug/phase/feature consistency. **[2026-03-14]** `in_progress` — Interactive tag suggestion feature with periodic reminder system (every 5-10 prompts) to validate prompt relevance to tagged context during long sessions. **[2026-03-14]** `in_progress` — Work item panel UI refinement: adjusted colgroup widths, fixed table overflow, added proper padding/spacing, and updated headers for clarity.