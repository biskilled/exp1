# Project Memory — aicli
_Generated: 2026-03-31 16:55 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform integrating Claude CLI, LLM platforms, and work item management via MCP server. It uses PostgreSQL 15+ with pgvector for semantic search, FastAPI backend with JWT auth, and Electron/Vanilla JS frontend with Cytoscape.js workflow visualization. Current focus is consolidating embedding/memory event tables, resolving data persistence issues on session switches, and clarifying memory table population logic before Phase 2 refactoring.

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
- **stale_code_removed**: db_ensure_project_schema_call_replaced_with_ensure_shared_schema
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
- **storage_primary**: PostgreSQL 15+ with per-project schema
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools; env var configured (BACKEND_URL, ACTIVE_PROJECT)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash start_backend.sh + ui/npm run dev; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ per-project schema + shared auth/usage tables; agent roles initialized
- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server on localhost
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)

## Key Decisions

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; JSONL migration planned
- Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys
- All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
- Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
- _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
- Embeddings linked to tags: tag metadata captures context (auth→all authentication prompts; feature/bug→relevant code changes)
- Backend modular: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
- pr_embeddings and pr_memory_events tables to be merged into single mem_ai_events table (id, project_id, session_id, session_desc, event_summary)

## In Progress

- Table consolidation design: pr_embeddings and pr_memory_events merging into single mem_ai_events table with event summary schema
- Memory table population logic: memory_items and project_facts tables require clarification on intended update behavior before Phase 2 embedding refactor
- Data persistence validation: tags disappearing on session switch—root cause under investigation (UI rendering vs. database save failure)
- Backend startup race condition: AiCli appears in Recent projects but remains unavailable as selectable project; dev environment delay acknowledged
- Embedding logic refactoring blocked: Phase 2 work pending clarification on memory table update logic and table consolidation design
- Port binding stability: 127.0.0.1:8000 conflicts resolved; bash start_backend.sh initialization sequence documented

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 17937a5..9a00c6f 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -114,7 +114,7 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-03-31T15:37:56Z",
+  "last_memory_run": "2026-03-31T16:34:04Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index ee29cb0..cdf9cac 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-03-31T16:33:38Z",
+  "last_updated": "2026-03-31T16:36:40Z",
   "last_session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d",
-  "last_session_ts": "2026-03-31T16:33:38Z",
-  "session_count": 299,
+  "last_session_ts": "2026-03-31T16:36:40Z",
+  "session_count": 300,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 7d91267..52b8bba 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 15:37 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 16:33 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 99ddf9e..ec77437 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -513,3 +513,5 @@
 {"ts": "2026-03-30T16:59:17Z", "action": "commit_push", "source": "claude_cli", "session_id": "7d89c79f-b6f1-4bd4-a93f-09f2603fd1b1", "hash": "e6a0097f", "message": "chore: update ai workspace state and simplify database.py", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "7d89c79f-b6f1-4bd4-a93f-09f2603fd1b1", "hash": "1732da8e", "message": "chore: update system files and refactor backend routes", "files_count": 39, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T15:37:24Z"}
 {"ts": "2026-03-31T15:37:02Z", "action": "commit_push", "source": "claude_cli", "session_id": "7d89c79f-b6f1-4bd4-a93f-09f2603fd1b1", "hash": "1732da8e", "message": "chore: update system files and refactor backend routes", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "8f221096", "message": "chore: update ai session state and memory after session 17cd46bd", "files_count": 56, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T16:33:48Z"}
+{"ts": "2026-03-31T16:33:38Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "8f221096", "message": "chore: update ai session state and memory after session 17cd46bd", "pushed": true, "push_error": ""}


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 03dec08..4987952 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,12 +1,8 @@
 # Project Memory — aicli
-_Generated: 2026-03-31 15:37 UTC by aicli /memory_
+_Generated: 2026-03-31 16:33 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
-## Project Summary
-
-AiCli is a shared AI memory platform built on FastAPI + PostgreSQL + Electron, enabling users to synthesize development history into structured memory across projects. The system implements dual-layer memory synthesis via Claude Haiku, semantic search with pgvector embeddings, and a DAG-based workflow engine for task orchestration. Currently in active development with focus on completing memory table population, resolving data persistence issues, and stabilizing backend initialization.
-
 ## Project Facts
 
 - **auth_pattern**: login_as_first_level_hierarchy
@@ -154,7 +150,3 @@ Reviewer: ```json
 - **Designed nested tags architecture**: Confirmed feasibility of multi-level tag hierarchy; planned `parent_id` column addition to `entity_values` table to extend beyond original 2-level (category → tag) structure; clarified that new tags added via chat are always created at root level only
 
 - **Database optimization strategy**: User requested consolidated SQL approach—load data once on project access, save updates only when explicitly saved (not on every change)
-
-## AI Synthesis
-
-**[2026-03-18]** `Recent Memory` — Removed stale `ensure_project_schema` call from main.py, replaced with `_ensure_shared_schema`; fixed CLAUDE.md line 1120 code_dir variable; implemented retry logic for empty project list on backend startup. **[2026-03-18]** `In Progress` — Project visibility issue persists (AiCli in Recent but not selectable); memory_items and project_facts tables not populating per spec; user-client schema relationship requires clarification. **[2026-03-16]** `Audit Complete` — event_tags system fully wired across chat/history/retrieval; fixed PostgreSQL ARRAY_AGG bug; MCP integration validated with stored API keys; 5-part memory synthesis replaces 40-entry JSONL dumps. **[2026-03-16]** `Architecture` — Workflow engine designed as DAG-based task execution similar to specrails; pending pipeline configuration source location and parent-child task hierarchy reconnection. **[2026-03-10]** `Optimization` — Implemented single-load caching for tags/categories on project open; eliminated redundant SQL calls during tag picker interactions; planned nested tags architecture via parent_id column on entity_values table.
\ No newline at end of file


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index 8bfbf42..0a1faed 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -119,4 +119,10 @@ Layer 5 — Global Knowledge
 - [2026-03-31] `claude_cli`: I am not so happy with the infrastrucure, think it is bit complicated anbd would like to dp antoehr 
 
 ---
-*Full context: see `_system/CONTEXT.md` — refresh with `GET /projects/aicli/context?save=true`*
\ No newline at end of file
+*Full context: see `_system/CONTEXT.md` — refresh with `GET /projects/aicli/context?save=true`*
+
+---
+
+## Session Memory
+
+Read `MEMORY.md` in this directory for recent work history, key decisions, and in-progress items. It was generated by aicli `/memory` (last 10 development exchanges).


## AI Synthesis

**[2026-03-31 16:50]** `claude_cli` — Identified critical table consolidation requirement: pr_embeddings and pr_memory_events to merge into single mem_ai_events table with event summary schema (id, project_id, session_id, session_desc, event_summary). **[2026-03-31]** `system` — Memory synthesis pipeline running dual-layer Claude Haiku approach (raw JSONL → interaction_tags → 5 output files) to reduce token overhead. **[2026-03-31]** `system` — Backend startup race condition partially resolved: AiCli appears in Recent projects but unavailable for selection due to dev environment timing delays. **[ongoing]** `development` — Data persistence investigation: tags disappearing on session switch requires root cause analysis between UI rendering and database save failures; /memory audit endpoint testing pending. **[ongoing]** `development` — Memory table population design blocked: memory_items and project_facts tables not being populated per design spec; Phase 2 embedding refactor awaiting clarification. **[established]** `architecture` — Hierarchical data model enforced: Clients contain multiple Users with login_as_first_level_hierarchy auth pattern and _ensure_shared_schema replacing ensure_project_schema.