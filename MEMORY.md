# Project Memory — aicli
_Generated: 2026-04-07 15:05 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to capture, synthesize, and manage project context across code commits, work items, and LLM interactions. It uses PostgreSQL with pgvector for semantic search, implements dual-layer Claude Haiku memory synthesis for generating project facts, and provides workflow visualization via Cytoscape DAG execution with approval workflows. Currently addressing backend data loading performance (Railway slow initial migrations), frontend reference errors in planner UI components, and work item dual-status implementation for user/AI status tracking.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: SQL
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude_CLI_and_LLM_platforms
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **memory_system_update_status**: updated_with_latest_context_and_session_tags
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
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
- **rel:memory_system:session_tags**: implements
- **rel:route_work_items:sql_parameter_binding**: depends_on
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
- **ui_library**: 3_dot_menu_pattern
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
- Tag filtering in work item list: ai_category must match tag's category, not work item's own category
- Session-level UI consolidation: Planner tab unified for all tag management with category/status/properties; suggested tags marked distinctly
- Memory synthesis triggered from session data via /memory endpoint → Claude Haiku processes commits/events → outputs to mem_ai_events/project_facts tables
- Project facts generated via LLM prompt analyzing session events and commits; stored in mem_ai_project_facts with event_id linkage for traceability

## In Progress

- Backend data loading errors: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS execution) and line 288 (merged_into/start_date column alignment); Railway initial load slow (~60s per round-trip, 0.9s per query), but functional
- Work item drag-and-drop UI refinement: fixing hover state propagation for target tag highlights; ensuring dropped work items persist in correct parent and disappear from source after page reload
- Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions properly scoped and exported to global scope
- Work item column alignment and source_session_id semantics: investigating column sizing consistency and clarifying source_session_id usage in work_items table display
- Work item dual-status implementation: integrating status_user dropdown + status_ai badge with separate color indicators throughout table and item drawer views; schema alignment verification
- Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state with correct event linkage

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **retrospective** `[open]`
- **Test** `[open]`
- **architecture-decision** `[open]`
- **customer-meeting** `[open]`
- **high-level-design** `[open]`
- **low-level-design** `[open]`

### Feature

- **pagination**
- **test-picker-feature** `[open]`
- **graph-workflow** `[open]`
- **billing** `[open]`
- **embeddings** `[open]`
- **tagging** `[open]`
- **mcp** `[open]`
- **workflow-runner** `[open]`
- **shared-memory** `[open]`
- **UI** `[open]`
- **auth** `[open]`
- **dropbox** `[open]`

### Phase

- **development** `[open]`
- **discovery** `[open]`
- **prod** `[open]`

### Task

- **memory** `[open]`
- **implement-projects-tab** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 5deb2ea..23fef02 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -83,12 +83,12 @@
     "config.py reads ~/.aicli/config.json for WORKSPACE_DIR at startup"
   ],
   "in_progress": [
+    "Backend data loading errors: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS execution) and line 288 (merged_into/start_date column alignment); Railway migration takes 60+ seconds per round-trip (~0.9s each), backend is functional but slow on initial load",
     "Work item drag-and-drop UI refinement: fixing hover state propagation so only target tag highlights; ensuring dropped work items persist in correct parent and disappear from source list after page reload",
+    "Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions are properly scoped and exported to global scope",
+    "Work item column alignment and source_session_id semantics: investigating column sizing consistency and clarifying source_session_id usage in work_items table display",
     "Work item dual-status implementation: integrating status_user dropdown + status_ai badge with separate color indicators throughout table and item drawer views; schema alignment verification",
-    "Work item embedding strategy: unified embedding space via code_summary + requirements + summary fields for cosine-similarity matching with planner_tags across work_items and memory_items tables",
-    "Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state",
-    "Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions properly scoped and exported to global scope",
-    "Work item column semantics clarification: investigating source_session_id usage and resolving column alignment inconsistencies in work_items table display"
+    "Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state"
   ],
   "next_phase_plan": {
     "project_management_page": [
@@ -120,7 +120,7 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-07T01:13:15Z",
+  "last_memory_run": "2026-04-07T01:56:20Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files",
@@ -140,12 +140,12 @@
       "Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm dev"
     ],
     "in_progress": [
+      "Backend data loading errors: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS execution) and line 288 (merged_into/start_date column alignment); Railway migration takes 60+ seconds per round-trip (~0.9s each), backend is functional but slow on initial load",
       "Work item drag-and-drop UI refinement: fixing hover state propagation so only target tag highlights; ensuring dropped work items persist in correct parent and disappear from source list after page reload",
+      "Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions are properly scoped and exported to global scope",
+      "Work item column alignment and source_session_id semantics: investigating column sizing consistency and clarifying source_session_id usage in work_items table display",
       "Work item dual-status implementation: integrating status_user dropdown + status_ai badge with separate color indicators throughout table and item drawer views; schema alignment verification",
-      "Work item embedding strategy: unified embedding space via code_summary + requirements + summary fields for cosine-similarity matching with planner_tags across work_items and memory_items tables",
-      "Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state",
-      "Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions properly scoped and exported to global scope",
-      "Work item column semantics clarification: investigating source_session_id usage and resolving column alignment inconsistencies in work_items table display"
+      "Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state"
     ],
     "tech_stack": {
       "cli": "Python 3.12 + prompt_toolkit + rich",
@@ -153,17 +153,19 @@
       "frontend": "Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server",
       "ui_components": "xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre",
       "storage_primary": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
-      "storage_semantic": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
       "authentication": "JWT (python-jose + bcrypt) + DEV_MODE toggle",
       "llm_providers": "Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok",
       "workflow_engine": "Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic",
-      "workflow_ui": "Cytoscape.js + cytoscape-dagre; 2-pane approval panel",
+      "memory_synthesis": "Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization",
+      "chunking": "Smart chunking: per-class/function (Python/JS/TS) + 

### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/llm_prompts/gemini_context.md b/workspace/aicli/_system/llm_prompts/gemini_context.md
index 8e8a50a..cc52165 100644
--- a/workspace/aicli/_system/llm_prompts/gemini_context.md
+++ b/workspace/aicli/_system/llm_prompts/gemini_context.md
@@ -1,5 +1,5 @@
 # Project Context: aicli
-# Generated: 2026-04-07 01:13 UTC
+# Generated: 2026-04-07 10:17 UTC
 
 ## Project Facts
 
@@ -62,14 +62,14 @@ History table contains numerous events that don't make sense and appear to be er
 Category: bug
 Multiple events from history table don't make sense and appear to be erroneous data that should be removed
 
-### #20065 auth
-Category: bug
-aiCli_memory tables are not updated and don't match current schema. Some tables no longer exist, causing inconsistency b
-
 ### #20066 billing
 Category: bug
 History view only shows prompts, not LLM responses. After fixes, only small text snippets are displayed instead of full 
 
+### #20065 auth
+Category: bug
+aiCli_memory tables are not updated and don't match current schema. Some tables no longer exist, causing inconsistency b
+
 ### #20061 billing
 Category: bug
 In route_history line 470, execute_values(cur, _SQL_BATCH_UPSERT, rows) throws 'ON CONFLICT DO UPDATE command cannot aff
@@ -86,18 +86,18 @@ History view shows only prompts but not LLM responses, or displays only small te
 Category: bug
 Error in route_history line 470 with cur.execute(b''.join(parts)) call to execute_values(). Incomplete or malformed SQL 
 
-### #20057 auth
-Category: bug
-History view only displays small text snippets instead of full prompts and LLM responses. Users cannot see complete conv
-
 ### #20059 Spurious history events in database
 Category: bug
 History table contains numerous nonsensical events from previous sessions that should not be there. Data integrity issue
 
-### #20060 Invalid llm_source column data
+### #20060 embeddings
 Category: bug
 llm_source field contains invalid or inconsistent data that doesn't match expected values or schema requirements.
 
+### #20057 auth
+Category: bug
+History view only displays small text snippets instead of full prompts and LLM responses. Users cannot see complete conv
+
 ### #20053 Copy text functionality missing from history UI
 Category: bug
 Users cannot copy text from the history section of the UI, which limits usability for reviewing and sharing past interac


### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/llm_prompts/full.md b/workspace/aicli/_system/llm_prompts/full.md
index 822a947..3193d7f 100644
--- a/workspace/aicli/_system/llm_prompts/full.md
+++ b/workspace/aicli/_system/llm_prompts/full.md
@@ -49,15 +49,15 @@ History
 - `#20068 dropbox` [bug]: Users cannot copy text from the history UI, limiting usability of viewing historical prompts and responses
 - `#20069 mcp` [bug]: History table contains numerous events that don't make sense and appear to be erroneous data. Needs cleanup of invalid e
 - `#20067 auth` [bug]: Multiple events from history table don't make sense and appear to be erroneous data that should be removed
-- `#20065 auth` [bug]: aiCli_memory tables are not updated and don't match current schema. Some tables no longer exist, causing inconsistency b
 - `#20066 billing` [bug]: History view only shows prompts, not LLM responses. After fixes, only small text snippets are displayed instead of full 
+- `#20065 auth` [bug]: aiCli_memory tables are not updated and don't match current schema. Some tables no longer exist, causing inconsistency b
 - `#20061 billing` [bug]: In route_history line 470, execute_values(cur, _SQL_BATCH_UPSERT, rows) throws 'ON CONFLICT DO UPDATE command cannot aff
 - `#20063 UI` [bug]: Users are unable to copy text from the history view in the UI, limiting the ability to export or reuse historical prompt
 - `#20062 mcp` [bug]: History view shows only prompts but not LLM responses, or displays only small text snippets instead of full prompt and L
 - `#20056 SQL execute syntax error` [bug]: Error in route_history line 470 with cur.execute(b''.join(parts)) call to execute_values(). Incomplete or malformed SQL 
-- `#20057 auth` [bug]: History view only displays small text snippets instead of full prompts and LLM responses. Users cannot see complete conv
 - `#20059 Spurious history events in database` [bug]: History table contains numerous nonsensical events from previous sessions that should not be there. Data integrity issue
-- `#20060 Invalid llm_source column data` [bug]: llm_source field contains invalid or inconsistent data that doesn't match expected values or schema requirements.
+- `#20060 embeddings` [bug]: llm_source field contains invalid or inconsistent data that doesn't match expected values or schema requirements.
+- `#20057 auth` [bug]: History view only displays small text snippets instead of full prompts and LLM responses. Users cannot see complete conv
 - `#20053 Copy text functionality missing from history UI` [bug]: Users cannot copy text from the history section of the UI, which limits usability for reviewing and sharing past interac
 - `#20055 Spurious event records in history table` [bug]: The event history table contains many events that don't make sense and appear to be leftover data from previous history 
 - `#20054 Column order not applied in mem_ai_events table` [bug]: After requesting changes to mem_ai_events table structure (llm_source to be after project column, embedding at last colu


### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 0b9a867..4c952b5 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-07T01:55:19Z",
+  "last_updated": "2026-04-07T14:59:24Z",
   "last_session_id": "dca94c94-c618-4866-89ce-7a3178adc777",
-  "last_session_ts": "2026-04-07T01:55:19Z",
-  "session_count": 406,
+  "last_session_ts": "2026-04-07T14:59:24Z",
+  "session_count": 407,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 2a218a8..ec83a79 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,71 +1,9 @@
-# aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-07 01:12 UTC
+## Project: aicli
 
-# aicli — Shared AI Memory Platform
+## Active Features (do not break)
 
-_Last updated: 2026-03-14 | Version 2.2.0_
-
----
-
-## Tech Stack
-
-- **cli**: Python 3.12 + prompt_toolkit + rich
-- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
-- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
-- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
-- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
-- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
-- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
-- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
-- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
-- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
-- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
-- **mcp**: Stdio MCP server with 12+ tools
-- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm
-- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
-- **config_management**: config.py + YAML pipelines + pyproject.toml
-- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
-- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
-- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
-- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
-- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
-- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
-- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
-- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
-- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
-- **database_version**: PostgreSQL 15+
-- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
-- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
-- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
-- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
-- **deployment_cloud**: Railway (Dockerfile + railway.toml)
-- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
-- **deployment_local**: bash start_backend.sh + npm run dev
-
-## Key Decisions
-
-- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
-- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
-- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
-- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
-- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
-- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
-- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
-- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
-- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
-- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt in

### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 374a78e..b61cac0 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -731,3 +731,5 @@
 {"ts": "2026-04-07T01:12:50Z", "action": "commit_push", "source": "claude_cli", "session_id": "dca94c94-c618-4866-89ce-7a3178adc777", "hash": "aeefbb0f", "message": "docs: update system context and memory files after claude session", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "dca94c94-c618-4866-89ce-7a3178adc777", "hash": "4eb54e1f", "message": "docs: update system context and memory after claude session dca94c94", "files_count": 62, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-07T01:55:08Z"}
 {"ts": "2026-04-07T01:55:00Z", "action": "commit_push", "source": "claude_cli", "session_id": "dca94c94-c618-4866-89ce-7a3178adc777", "hash": "4eb54e1f", "message": "docs: update system context and memory after claude session dca94c94", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "dca94c94-c618-4866-89ce-7a3178adc777", "hash": "0a95f13b", "message": "chore: remove outdated system context and claude session files", "files_count": 55, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-07T01:55:27Z"}
+{"ts": "2026-04-07T01:55:19Z", "action": "commit_push", "source": "claude_cli", "session_id": "dca94c94-c618-4866-89ce-7a3178adc777", "hash": "0a95f13b", "message": "chore: remove outdated system context and claude session files", "pushed": true, "push_error": ""}


## AI Synthesis

**[2026-04-07]** `claude_cli` — Analyzed full memory pipeline architecture: mirror tables (`mem_mrr_*`) capture prompts/responses without LLM as pure event log; `mem_ai_events` unified table consolidates across projects; project_facts generated via Claude Haiku analyzing session events+commits with event_id traceability; work_items dual-status (user/AI) drives UI filtering and semantic embedding via code_summary field. **[2026-04-07]** `project_state` — Prioritized backend data loading: route_work_items SQL execution errors on unlinked items and column alignment (merged_into/start_date); Railway initial load takes 60s due to migration overhead (~0.9s/query) but backend functional. **[2026-04-07]** `project_state` — Frontend reference errors in planner helper functions (_plannerSelectAiSubtype undefined in routers.route_logs); requires proper global scope export of all planner utilities. **[2026-04-07]** `project_state` — Work item UI refinement: drag-and-drop hover state isolation (only target tag highlights), persistence after reload, and dual-status indicator integration (status_user dropdown + status_ai badge). **[2026-04-07]** `project_state` — Work item column semantics clarification: source_session_id usage and column sizing consistency investigation for table display alignment. **[2026-04-07]** `project_state` — Memory endpoint data synchronization: /memory endpoint must sync session data into memory_items table and ensure mem_ai_* tables reflect current project state with proper event linkage.