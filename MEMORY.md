# Project Memory — aicli
_Generated: 2026-04-07 14:59 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend with PostgreSQL/pgvector storage, a Claude-powered memory synthesis engine, and an Electron desktop UI with workflow visualization. It enables teams to capture work item metadata, commits, and session events into unified semantic tables, generate AI-driven project facts and insights, and manage complex workflows through a DAG-based executor with approval panels. Currently stabilizing backend performance (60-second migration delays), fixing SQL query errors in work item retrieval, and refining work item dual-status UI with proper tag linkage persistence.

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
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
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

- Backend data loading errors: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS execution) and line 288 (merged_into/start_date column alignment); Railway migration takes 60+ seconds per round-trip, backend functional but slow on initial load
- Work item drag-and-drop UI refinement: fixing hover state propagation so only target tag highlights; ensuring dropped work items persist in correct parent and disappear from source list after page reload
- Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions are properly scoped and exported to global scope
- Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state with correct event linkage
- Mirror table architecture investigation: understanding trigger mechanisms for mem_ai_events and mem_ai_project_facts, LLM prompts used in synthesis, and data flow from session commits/events
- Work item dual-status implementation: integrating status_user dropdown + status_ai badge with separate color indicators throughout table and item drawer views; schema alignment verification

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

### `prompt_batch: dca94c94-c618-4866-89ce-7a3178adc777` — 2026-04-07

Memory system updated with latest context and session tags. Identified two SQL errors in `route_work_items`: line 249's `cur.execute()` call for unlinked items and line 288's incomplete column selection in merged work item query—both need parameter binding and column list review.

### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 5d04407..6f5760d 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-07T01:12:51Z",
+  "last_updated": "2026-04-07T01:55:01Z",
   "last_session_id": "dca94c94-c618-4866-89ce-7a3178adc777",
-  "last_session_ts": "2026-04-07T01:12:51Z",
-  "session_count": 404,
+  "last_session_ts": "2026-04-07T01:55:01Z",
+  "session_count": 405,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 0a2d52d..2a218a8 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-07 01:11 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-07 01:12 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index c06034c..b56e0ed 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -727,3 +727,5 @@
 {"ts": "2026-04-06T23:06:20Z", "action": "commit_push", "source": "claude_cli", "session_id": "04974a99-4e27-44d8-ba75-c7b9e54ba9c7", "hash": "d760cb38", "message": "docs: update system context and memory after claude session 04974a99", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "dca94c94-c618-4866-89ce-7a3178adc777", "hash": "46b5b785", "message": "docs: update system prompts and memory after claude session", "files_count": 66, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-07T01:10:44Z"}
 {"ts": "2026-04-07T01:10:33Z", "action": "commit_push", "source": "claude_cli", "session_id": "dca94c94-c618-4866-89ce-7a3178adc777", "hash": "46b5b785", "message": "docs: update system prompts and memory after claude session", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "dca94c94-c618-4866-89ce-7a3178adc777", "hash": "aeefbb0f", "message": "docs: update system context and memory files after claude session", "files_count": 61, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-07T01:13:03Z"}
+{"ts": "2026-04-07T01:12:50Z", "action": "commit_push", "source": "claude_cli", "session_id": "dca94c94-c618-4866-89ce-7a3178adc777", "hash": "aeefbb0f", "message": "docs: update system context and memory files after claude session", "pushed": true, "push_error": ""}


### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index b119aee..8508436 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-07 01:11 UTC by aicli /memory_
+_Generated: 2026-04-07 01:12 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python CLI backend (FastAPI + PostgreSQL + pgvector), Electron desktop UI (Vanilla JS + Cytoscape DAG visualization), and multi-provider LLM support (Claude/OpenAI/DeepSeek/Gemini/Grok) for semantic tagging, workflow automation, and collaborative memory synthesis. Currently stabilizing work item drag-drop UI, dual-status tracking, and memory population after recent schema consolidation around unified mem_ai_* tables.
+aicli is a shared AI memory platform combining a Python FastAPI backend with Electron desktop UI and CLI, using PostgreSQL+pgvector for semantic search and multi-provider LLM support (Claude/OpenAI/DeepSeek/Gemini/Grok). It provides unified project memory management via mem_ai_* tables, work item tracking with dual status (user/AI), async DAG workflow execution, and session-based tagging. Current focus is resolving work item drag-drop persistence bugs and completing dual-status UI with proper embedding strategy for cross-table semantic matching.
 
 ## Project Facts
 
@@ -104,12 +104,12 @@ Reviewer: ```json
 
 ## In Progress
 
-- Work item UI drag-and-drop refinement: fixing hover state propagation (only target tag highlights) and ensuring dropped work items persist in correct parent and disappear from source list after reload
-- Work item column alignment and source_session_id semantics: investigating column sizing consistency and clarifying source_session_id usage in work_items table schema
-- Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions are properly scoped and exported
-- Work item dual-status UI completion: integrating status_user dropdown + status_ai badge with separate color indicators throughout table and item drawer views
-- Work item embedding strategy for cross-matching: unified embedding space via code_summary + requirements + summary fields for cosine-similarity matching with planner_tags
-- Memory items and system state refresh: running /memory endpoint to update all memory_items with latest session data and ensure memory tables are properly populated across workspace
+- Work item drag-and-drop UI refinement: fixing hover state propagation so only target tag highlights; ensuring dropped work items persist in correct parent and disappear from source list after page reload
+- Work item dual-status implementation: integrating status_user dropdown + status_ai badge with separate color indicators throughout table and item drawer views; schema alignment verification
+- Work item embedding strategy: unified embedding space via code_summary + requirements + summary fields for cosine-similarity matching with planner_tags across work_items and memory_items tables
+- Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state
+- Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions properly scoped and exported to global scope
+- Work item column semantics clarification: investigating source_session_id usage and resolving column alignment inconsistencies in work_items table display
 
 ## Active Features / Bugs / Tasks
 
@@ -160,193 +160,286 @@ Reviewer: ```json
 
 > Distilled summaries (Trycycle-reviewed). Feature summaries shown first.
 
-### `commit` — 2026-04-06
+### `commit` — 2026-04-07
 
-diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
-index 3044ebd..5f65c9c 100644
---- a/.github/copilot-instructions.md
-+++ b/.github/copilot-instructions.md
-@@ -1,5 +1,5 @@
- # aicli — GitHub Copilot Instructions
--> Generated by aicli 2026-04-06 18:14 UTC
-+> Generated by aicli 2026-04-06 22:55 UTC
- 
- # aicli — Shared AI Memory Platform
+diff --git a/workspace/aicli/_system/aicli/context.md b/workspace/aicli/_system/aicli/context.md
+index c4643a1..a3dbb88 100644
+--- a/workspace/aicli/_system/aicli/context.md
++++ b/workspace/aicli/_system/aicli/context.md
+@@ -1,9 +1,9 @@
+ [Project Facts] auth_pattern=login_as_first_level_hierarchy; backend_startup_race_condition_fix=retry_logic_handles_empty_project_list_on_first_load; data_model_hierarchy=clients_contain_multiple_users; data_persistence_issue=tags_disappear_on_session_switch; db_engine=SQL; db_schema_method_convention=_ensure_shared_schema_replaces_ensure_project_schema
  
-@@ -56,8 +56,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
- - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- - Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
- - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
--- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with mem_mrr_commits table
--- Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
--- Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation
--- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _en

### `commit` — 2026-04-07

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index 44e2973..f93a220 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -119,10 +119,4 @@ Layer 5 — Global Knowledge
 - [2026-03-31] `claude_cli`: I am not so happy with the infrastrucure, think it is bit complicated anbd would like to dp antoehr 
 
 ---
-*Full context: see `_system/CONTEXT.md` — refresh with `GET /projects/aicli/context?save=true`*
-
----
-
-## Session Memory
-
-Read `MEMORY.md` in this directory for recent work history, key decisions, and in-progress items. It was generated by aicli `/memory` (LLM-synthesized project digest).
+*Full context: see `_system/CONTEXT.md` — refresh with `GET /projects/aicli/context?save=true`*
\ No newline at end of file


## AI Synthesis

**[2026-04-07]** `claude_cli` — Diagnostic investigation of mirror table architecture: clarified that mem_ai_events stores unified session data (commits, events, work item changes) triggered by /memory endpoint; mem_ai_project_facts generated via Claude Haiku LLM prompt analyzing session context (commits, tags, events) to extract high-level insights; work_items table triggered by drag-drop UI interactions and /memory sync endpoint.

**[2026-04-07]** `diagnostic` — Identified critical backend performance bottleneck: Railway migrations take 60+ seconds per round-trip (~0.9s each request), causing initial project load slowness; route_work_items has two SQL errors (line 249 unlinked items query and line 288 merged item column alignment) requiring parameter binding fixes.

**[2026-03-14]** `memory_synthesis` — Claude Haiku dual-layer memory system fully operational: processes commits/events into 5 output files with LLM response summarization, auto-tag suggestions, and timestamp tracking; tag deduplication prevents duplicates across sessions.

**[Recent sessions]** `development` — Work item dual-status tracking (status_user + status_ai) integrated with color indicators; planner tab unified for tag management with suggested tags marked distinctly; drag-drop linkage saves correctly to DB with proper tag JSONB encoding.

**[Recent sessions]** `ui_refinement` — Fixed tag filtering regression (ai_category must match tag's category, not work item's own); session ordering by created_at prevents reordering on tag updates; work item persistence across navigation working correctly.

**[Recent sessions]** `frontend_debugging` — Planner helper functions scoped and exported to global scope; _plannerSelectAiSubtype reference errors resolved; work item column alignment verified for dual-status display and code_summary embedding field.