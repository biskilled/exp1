# Project Memory — aicli
_Generated: 2026-03-31 20:41 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform built on PostgreSQL 15+, FastAPI, and Electron with Claude Haiku synthesis. It provides per-project semantic search via pgvector, async DAG workflows with visual approval panels, and MCP-based tool integration. Current focus is on fixing table naming conventions (mem_ai_tags_relations), validating tagging functionality, and designing Phase 2 table consolidation to merge embeddings and memory events into a unified schema.

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

- Table naming fix: corrected mem_ai_tags_relations (was incorrectly referenced as mng_ai_tags_relations); validation of tagging functionality implementation
- Tagging functionality validation: Review mem_ai_tags_relations table implementation and verify all tagging prompts work as documented
- Table consolidation design: pr_embeddings and pr_memory_events merging into single mem_ai_events table; Phase 2 blocker
- Memory table population logic: memory_items and project_facts tables require clarification on intended update behavior; currently not populating per spec
- Data persistence validation: tags disappearing on session switch; root cause investigation needed (UI rendering vs. database save failure)
- Backend startup race condition: AiCli appears in Recent projects but remains unavailable as selectable project; dev environment delay documented

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 0bc98e7..902b99a 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -10,7 +10,7 @@
     "ui_components": "xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre",
     "storage_primary": "PostgreSQL 15+ with per-project schema",
     "storage_semantic": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
-    "db_schema": "Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)",
+    "db_schema": "Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys",
     "authentication": "JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free",
     "llm_providers": "Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok",
     "workflow_engine": "Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic",
@@ -31,7 +31,8 @@
     "database": "PostgreSQL 15+ per-project schema + shared auth/usage tables; agent roles initialized",
     "node_modules_build": "npm 8+ with webpack/Electron-builder; dev server Vite on localhost",
     "database_version": "PostgreSQL 15+",
-    "build_tooling": "npm 8+ with webpack/Electron-builder; Vite dev server on localhost"
+    "build_tooling": "npm 8+ with webpack/Electron-builder; Vite dev server on localhost",
+    "db_consolidation": "mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)"
   },
   "key_decisions": [
     "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",
@@ -43,12 +44,12 @@
     "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files); reduces token overhead",
     "Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}",
     "Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB",
-    "SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization",
     "MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval",
     "Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy",
     "_ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load",
     "Embeddings linked to tags: tag metadata captures context (auth\u2192all authentication prompts; feature/bug\u2192relevant code changes)",
-    "Backend modular: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic"
+    "Backend modular: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic",
+    "pr_embeddings and pr_memory_events tables to be merged into single mem_ai_events table (id, project_id, session_id, session_desc, event_summary)"
   ],
   "implemented_features": [
     "5-layer memory architecture with /memory endpoint + LLM synthesis via Haiku",
@@ -77,12 +78,12 @@
     "config.py reads ~/.aicli/config.json for WORKSPACE_DIR at startup"
   ],
   "in_progress": [
-    "Memory table population design review: memory_items and project_facts tables not being populated per design spec; requires clarification on intended behavior before Ph

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 66c927a..0c877bc 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-03-31T16:55:07Z",
+  "last_updated": "2026-03-31T18:57:49Z",
   "last_session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d",
-  "last_session_ts": "2026-03-31T16:55:07Z",
-  "session_count": 301,
+  "last_session_ts": "2026-03-31T18:57:49Z",
+  "session_count": 302,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index fa53830..bf2bbd4 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 16:36 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 16:55 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -15,7 +15,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - **storage_primary**: PostgreSQL 15+ with per-project schema
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)
+- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys
 - **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
 - **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
@@ -37,6 +37,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server on localhost
+- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
 
 ## Key Decisions
 
@@ -49,17 +50,17 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
 - Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Embeddings linked to tags: tag metadata captures context (auth→all authentication prompts; feature/bug→relevant code changes)
 - Backend modular: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
+- pr_embeddings and pr_memory_events tables to be merged into single mem_ai_events table (id, project_id, session_id, session_desc, event_summary)
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-18] it looks like it is a bit broken, I have got an error - '_Database' object has no attribute 'ensure_project_schema'. Did
 - [2026-03-18] There are some error - on the first load, it lookls like Backend is failing (after thay it succeed). I have tried to run
 - [2026-03-18] Looks beter. there are some minor issue - in project page, I do see in Recent aiCli, but I do not see that As a project 
 - [2026-03-18] Few more strucure - users are also part of client (client can have mutiple users). Also I would like to understand if yo
-- [2026-03-31] Is it makes

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 39257df..37b9cce 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -517,3 +517,5 @@
 {"ts": "2026-03-31T16:33:38Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "8f221096", "message": "chore: update ai session state and memory after session 17cd46bd", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "cad8c096", "message": "chore: update AI context files and session history logs", "files_count": 32, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T16:36:50Z"}
 {"ts": "2026-03-31T16:36:40Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "cad8c096", "message": "chore: update AI context files and session history logs", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "7ea756e6", "message": "chore: update ai context files and memory after cli session", "files_count": 37, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T16:55:16Z"}
+{"ts": "2026-03-31T16:55:07Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "7ea756e6", "message": "chore: update ai context files and memory after cli session", "pushed": true, "push_error": ""}


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index ab0ccd2..fd4b94b 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-03-31 16:36 UTC by aicli /memory_
+_Generated: 2026-03-31 16:55 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform built on FastAPI + PostgreSQL + Electron, enabling collaborative AI work through semantic search, tagging, and workflow automation. Currently in Phase 1 stabilization with memory synthesis deployed, event tagging fully operational, and MCP integration validated; Phase 2 embedding refactor blocked pending clarification on memory table population logic and user-client schema relationship.
+aicli is a shared AI memory platform integrating Claude CLI, LLM platforms, and work item management via MCP server. It uses PostgreSQL 15+ with pgvector for semantic search, FastAPI backend with JWT auth, and Electron/Vanilla JS frontend with Cytoscape.js workflow visualization. Current focus is consolidating embedding/memory event tables, resolving data persistence issues on session switches, and clarifying memory table population logic before Phase 2 refactoring.
 
 ## Project Facts
 
@@ -55,7 +55,7 @@ Reviewer: ```json
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - **storage_primary**: PostgreSQL 15+ with per-project schema
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)
+- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys
 - **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
 - **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
@@ -77,6 +77,7 @@ Reviewer: ```json
 - **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server on localhost
+- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
 
 ## Key Decisions
 
@@ -89,72 +90,144 @@ Reviewer: ```json
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
 - Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Embeddings linked to tags: tag metadata captures context (auth→all authentication prompts; feature/bug→relevant code changes)
 - Backend modular: core/ for i

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index 6a515b4..676ba88 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -35,12 +35,12 @@ You are a senior Python software architect with deep expertise in:
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
 - Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Embeddings linked to tags: tag metadata captures context (auth→all authentication prompts; feature/bug→relevant code changes)
 - Backend modular: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
+- pr_embeddings and pr_memory_events tables to be merged into single mem_ai_events table (id, project_id, session_id, session_desc, event_summary)
 
 ---
 


## AI Synthesis

**[2026-03-31]** `claude_cli` — Corrected table naming: mem_ai_tags_relations (not mng_ai_tags_relations) in database schema; critical for tagging functionality validation. **[2026-03-31]** `session_302` — Updated db_consolidation design decision: pr_embeddings and pr_memory_events tables slated for merge into unified mem_ai_events table (id, project_id, session_id, session_desc, event_summary). **[2026-03-18]** `claude_cli` — Resolved backend startup race condition: _ensure_shared_schema pattern replacing ensure_project_schema; retry logic now handles empty project list on first load. **[2026-03-18]** `claude_cli` — Completed hierarchical data model clarification: Clients contain multiple Users; authentication pattern is login_as_first_level_hierarchy. **[Ongoing]** — Phase 2 blocker: Memory table population (memory_items, project_facts) not populating per spec; data persistence issue (tags disappearing on session switch) requires root cause analysis of UI rendering vs. database save failure.