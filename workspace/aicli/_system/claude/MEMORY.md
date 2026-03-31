# Project Memory — aicli
_Generated: 2026-03-31 18:57 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling developers to build intelligent workflows via Claude CLI and LLM platforms. Built with Python FastAPI backend, Electron + Vanilla JS frontend, PostgreSQL + pgvector storage, and async DAG workflow execution. Currently in Phase 1 completion—tagging functionality validation and table consolidation design are blocking Phase 2 embedding refactor; startup race condition and data persistence issues are under investigation.

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
- pr_embeddings and pr_memory_events tables to merge into single mem_ai_events table (id, project_id, session_id, session_desc, event_summary)

## In Progress

- Tagging functionality validation: Review mng_ai_tags_relations table implementation and verify all tagging prompts work as documented; core feature completeness check
- Table consolidation design: pr_embeddings and pr_memory_events merging into single mem_ai_events table with event summary schema; Phase 2 blocker
- Memory table population logic: memory_items and project_facts tables require clarification on intended update behavior; currently not populating per spec
- Data persistence validation: tags disappearing on session switch; root cause investigation needed (UI rendering vs. database save failure)
- Backend startup race condition: AiCli appears in Recent projects but remains unavailable as selectable project; dev environment delay documented
- Embedding logic refactoring blocked: Phase 2 work pending table consolidation design and memory table population clarification

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 9a00c6f..0bc98e7 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -35,13 +35,13 @@
   },
   "key_decisions": [
     "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",
-    "Dual storage model transitioning to DB-only: PostgreSQL 15+ with pgvector (1536-dim) for semantic search; JSONL migration planned",
+    "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; JSONL migration planned",
     "Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server",
     "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys",
     "All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none",
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval",
-    "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files); smart chunking per language/section",
-    "Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared auth/usage tables",
+    "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files); reduces token overhead",
+    "Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}",
     "Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB",
     "SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization",
     "MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval",
@@ -77,12 +77,12 @@
     "config.py reads ~/.aicli/config.json for WORKSPACE_DIR at startup"
   ],
   "in_progress": [
-    "Memory table implementation: memory_items and project_facts tables not being populated per design spec; requires clarification on intended behavior and completion of update logic",
-    "Project visibility timing issue: AiCli appears in Recent projects but not selectable as current active project; backend startup delay acknowledged, expected to resolve in production",
-    "Data persistence bug investigation: tags disappear on session switch; root cause unclear (UI rendering vs. database save failure); requires validation via /memory audit endpoint",
-    "Backend startup stability: resolved port 127.0.0.1:8000 binding conflicts; documented initialization sequence via bash start_backend.sh; retry logic handles empty project list",
-    "Memory endpoint template variable scoping: fixed code_dir variable at line 1120 in CLAUDE.md template to resolve runtime failures",
-    "User-client schema relationship: confirmed hierarchical structure (clients have multiple users) but schema modifications status unclear; may require database migration"
+    "Memory table population design review: memory_items and project_facts tables not being populated per design spec; requires clarification on intended behavior before Phase 2 embedding refactor",
+    "Backend startup race condition partially resolved: AiCli now appears in Recent projects but remains unavailable as selectable current project; acknowledged as dev environment delay",
+    "Data persistence validation: tags disappearing on session switch\u2014root cause under investigation (UI rendering vs. database save failure); /memory audit endpoint testing pending",
+    "Embedding logic refactoring planned: Phase 2 work blocked pending clarification

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index cdf9cac..66c927a 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-03-31T16:36:40Z",
+  "last_updated": "2026-03-31T16:55:07Z",
   "last_session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d",
-  "last_session_ts": "2026-03-31T16:36:40Z",
-  "session_count": 300,
+  "last_session_ts": "2026-03-31T16:55:07Z",
+  "session_count": 301,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 52b8bba..fa53830 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 16:33 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 16:36 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -41,13 +41,13 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 ## Key Decisions
 
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
-- Dual storage model transitioning to DB-only: PostgreSQL 15+ with pgvector (1536-dim) for semantic search; JSONL migration planned
+- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; JSONL migration planned
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval
-- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); smart chunking per language/section
-- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared auth/usage tables
+- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
+- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
 - SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
@@ -58,8 +58,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-18] That is correct. it is bed pattern to use clinet name. there is already mng_users table that can manage client as well (
 - [2026-03-18] it looks like it is a bit broken, I have got an error - '_Database' object has no attribute 'ensure_project_schema'. Did
 - [2026-03-18] There are some error - on the first load, it lookls like Backend is failing (after thay it succeed). I have tried to run
 - [2026-03-18] Looks beter. there are some minor issue - in project page, I do see in Recent aiCli, but I do not see that As a project 
-- [2026-03-18] Few more strucure - users are also part of client (client can have mutiple users). Also I would like to understand if yo
\ No newline at end of file
+- [2026-03-18] Few more strucure - users are also part of client (client can have mutiple users). Also I would like to understand if yo
+- [2026-03-31] Is it makes more sense, before I continue to the secopnd phase (refactor embedding logic) . is there is anything else yo
\ No newline at end of file


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index ec77437..39257df 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -515,3 +515,5 @@
 {"ts": "2026-03-31T15:37:02Z", "action": "commit_push", "source": "claude_cli", "session_id": "7d89c79f-b6f1-4bd4-a93f-09f2603fd1b1", "hash": "1732da8e", "message": "chore: update system files and refactor backend routes", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "8f221096", "message": "chore: update ai session state and memory after session 17cd46bd", "files_count": 56, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T16:33:48Z"}
 {"ts": "2026-03-31T16:33:38Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "8f221096", "message": "chore: update ai session state and memory after session 17cd46bd", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "cad8c096", "message": "chore: update AI context files and session history logs", "files_count": 32, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T16:36:50Z"}
+{"ts": "2026-03-31T16:36:40Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "cad8c096", "message": "chore: update AI context files and session history logs", "pushed": true, "push_error": ""}


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 4987952..ab0ccd2 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,8 +1,12 @@
 # Project Memory — aicli
-_Generated: 2026-03-31 16:33 UTC by aicli /memory_
+_Generated: 2026-03-31 16:36 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
+## Project Summary
+
+aicli is a shared AI memory platform built on FastAPI + PostgreSQL + Electron, enabling collaborative AI work through semantic search, tagging, and workflow automation. Currently in Phase 1 stabilization with memory synthesis deployed, event tagging fully operational, and MCP integration validated; Phase 2 embedding refactor blocked pending clarification on memory table population logic and user-client schema relationship.
+
 ## Project Facts
 
 - **auth_pattern**: login_as_first_level_hierarchy
@@ -77,13 +81,13 @@ Reviewer: ```json
 ## Key Decisions
 
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
-- Dual storage model transitioning to DB-only: PostgreSQL 15+ with pgvector (1536-dim) for semantic search; JSONL migration planned
+- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; JSONL migration planned
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval
-- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); smart chunking per language/section
-- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared auth/usage tables
+- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
+- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
 - SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
@@ -94,12 +98,12 @@ Reviewer: ```json
 
 ## In Progress
 
-- Memory table implementation: memory_items and project_facts tables not being populated per design spec; requires clarification on intended behavior and completion of update logic
-- Project visibility timing issue: AiCli appears in Recent projects but not selectable as current active project; backend startup delay acknowledged, expected to resolve in production
-- Data persistence bug investigation: tags disappear on session switch; root cause unclear (UI rendering vs. database save failure); requires validation via /memory audit endpoint
-- Backend startup stability: resolved port 127.0.0.1:8000 binding conflicts; documented initialization sequence via bash start_backend.sh; retry logic handles empty project list
-- Memory endpoint template variable scoping: fixed code_dir variable at line 1120 in CLAUDE.md template to resolve runtime failures
-- User-client schema relationship: confirmed hierarchical structure (clients have multiple users) but schema modifications status unclear; may require database migration
+- Memory table population design review: memory_items and project_facts tables n

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index 0a1faed..6a515b4 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -27,13 +27,13 @@ You are a senior Python software architect with deep expertise in:
 ## Key Architectural Decisions
 
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
-- Dual storage model transitioning to DB-only: PostgreSQL 15+ with pgvector (1536-dim) for semantic search; JSONL migration planned
+- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; JSONL migration planned
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval
-- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); smart chunking per language/section
-- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared auth/usage tables
+- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
+- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
 - SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
@@ -125,4 +125,4 @@ Layer 5 — Global Knowledge
 
 ## Session Memory
 
-Read `MEMORY.md` in this directory for recent work history, key decisions, and in-progress items. It was generated by aicli `/memory` (last 10 development exchanges).
+Read `MEMORY.md` in this directory for recent work history, key decisions, and in-progress items. It was generated by aicli `/memory` (LLM-synthesized project digest).


## AI Synthesis

**[2026-03-31]** `claude_cli` — Tagging functionality completeness audit initiated; mng_ai_tags_relations table implementation and all tagging prompts require validation against design spec. **[2026-03-31]** `dev_runtime_state` — Session count reached 301; backend startup race condition persists (AiCli visible in Recent but not selectable); acknowledged as dev environment delay pending production resolution. **[2026-03-18]** `project_state` — Hierarchical data model confirmed: clients contain multiple users with login_as_first_level_hierarchy pattern; _ensure_shared_schema pattern replaces ensure_project_schema with retry logic for empty project lists. **[2026-03-18]** `dev_environment` — Backend startup stability improved; port 127.0.0.1:8000 binding conflicts resolved; initialization sequence documented via bash start_backend.sh. **[2026-03-18]** `data_persistence` — Tags disappearing on session switch under investigation; root cause unclear (UI rendering vs. database save failure); /memory audit endpoint testing pending. **[2026-03-31]** `Phase 2 planning` — Table consolidation design required (pr_embeddings + pr_memory_events → mem_ai_events); memory table population (memory_items, project_facts) clarification needed before embedding logic refactor proceeds.