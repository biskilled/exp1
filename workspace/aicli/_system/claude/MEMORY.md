# Project Memory — aicli
_Generated: 2026-04-01 08:25 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to manage AI-assisted development workflows. It features dual-storage (PostgreSQL + pgvector for semantic search), unified memory tables (mem_ai_events, project_facts, work_items), async DAG workflow execution with Cytoscape visualization, and multi-provider LLM support (Claude, OpenAI, DeepSeek, Gemini, Grok) with server-side key management. Current focus is on stabilizing schema consistency, ensuring data persistence across sessions, and automating memory synthesis through Claude Haiku dual-layer processing.

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
- **storage_primary**: PostgreSQL 15+
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); local: bash start_backend.sh + ui/npm run dev
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **config_management**: config.py with externalized settings; YAML for pipelines; pyproject.toml for IDE
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+
- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) plus per-project schemas
- Electron desktop UI: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vanilla JS frontend (no framework/bundler); Vite dev server
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
- All LLM providers as independent adapters (Claude/OpenAI/DeepSeek/Gemini/Grok); Claude Haiku for dual-layer memory synthesis; server holds API keys
- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for negotiation
- Memory synthesis: Claude Haiku dual-layer generates 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load; backend_startup_race_condition mitigated
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations (linked via row id), not in summary arrays
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements; smart chunking by per-class/function (Python/JS/TS), per-section (MD), per-file (diff)
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
- CLI: Python 3.12 + prompt_toolkit + rich; command routing via verb-noun pattern; memory endpoint template variable scoping fixed at line 1120
- Deployment: Railway (Dockerfile + railway.toml) for cloud; local dev via bash start_backend.sh + ui/npm run dev; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing_storage in data/provider_storage/

## In Progress

- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from unified mem_ai_* tables with timestamp tracking
- Unified event table validation: mem_ai_events consolidates embeddings and memory events; removed event_summary_tags array and deprecated metadata columns
- Data persistence validation: tags disappearing on session switch root cause traced to cache invalidation triggering DB re-load; fix ensures persistence across switches
- Schema documentation cleanup: updated project_state.json and rules.md to reflect mem_ai_* unified table naming and removed deprecated database_schema field
- Tag column schema correction: mem_ai_tags_relations table DDL fixed; database migrations applied and persistence validated across session switches
- Backend startup race condition: AiCli appearing in Recent projects but unselectable on first load; retry logic implemented for empty project list handling

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 3e3d1d4..bdb61c2 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -28,7 +28,7 @@
     "billing_storage": "data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables",
     "backend_modules": "routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server",
     "dev_environment": "PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root",
-    "database": "PostgreSQL 15+ per-project schema + shared auth/usage tables; agent roles initialized",
+    "database": "PostgreSQL 15+",
     "node_modules_build": "npm 8+ with webpack/Electron-builder; dev server Vite on localhost",
     "database_version": "PostgreSQL 15+",
     "build_tooling": "npm 8+ with webpack/Electron-builder; Vite dev server",
@@ -39,7 +39,7 @@
     "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",
     "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables",
     "Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server",
-    "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients \u2192 Users; login_as_first_level_hierarchy pattern",
+    "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern",
     "All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys",
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel",
     "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)",
@@ -116,13 +116,13 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-01T01:40:36Z",
+  "last_memory_run": "2026-04-01T01:52:29Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",
       "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables",
       "Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server",
-      "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients \u2192 Users; login_as_first_level_hierarchy pattern",
+      "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern",
       "All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys",
       "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel",
       "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)",
@@ -150,7 +150,6 @@
       "ui_components": "xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre",
       "storage_primary": "PostgreSQL 15+ with per-project schema",
       "storage_semantic": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
-      "database_schema": "Per-project: commits_{p}, events_{p}, embeddings

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index d5f69f6..f38af73 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-01T01:52:10Z",
-  "last_session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d",
-  "last_session_ts": "2026-04-01T01:52:10Z",
-  "session_count": 318,
+  "last_updated": "2026-04-01T02:11:30Z",
+  "last_session_id": "11163d9b-a609-4847-8ca9-702fce4165c5",
+  "last_session_ts": "2026-04-01T02:11:30Z",
+  "session_count": 319,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 582e239..9a5e26c 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 01:40 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 01:52 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -33,7 +33,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
-- **database**: PostgreSQL 15+ per-project schema + shared auth/usage tables; agent roles initialized
+- **database**: PostgreSQL 15+
 - **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server
@@ -45,7 +45,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
 - All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index c25c37a..e815c4c 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -551,3 +551,5 @@
 {"ts": "2026-04-01T01:36:12Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "d3c9f49e", "message": "chore: update ai context files and session state after cli session", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "d2c4222a", "message": "chore: update AI context files and session memory logs", "files_count": 32, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T01:40:24Z"}
 {"ts": "2026-04-01T01:40:17Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "d2c4222a", "message": "chore: update AI context files and session memory logs", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "d79175fa", "message": "chore: update workspace state and memory after claude session 17cd46bd", "files_count": 39, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T01:52:18Z"}
+{"ts": "2026-04-01T01:52:10Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "d79175fa", "message": "chore: update workspace state and memory after claude session 17cd46bd", "pushed": true, "push_error": ""}


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index d8a8c87..1569ed2 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-01 01:40 UTC by aicli /memory_
+_Generated: 2026-04-01 01:52 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform that integrates with Claude and other LLM providers via a Python CLI backend and Electron-based frontend, enabling persistent project context management across sessions. The system uses PostgreSQL with pgvector for semantic search, unified mem_ai_* tables for memory storage, and async DAG workflows for task execution. Currently stabilizing schema correctness, memory file automation, and data persistence across session switches to ensure reliable context retention.
+aicli is a shared AI memory platform built on Python (FastAPI backend) + Electron (Vanilla JS frontend) that integrates with Claude and multiple LLM providers via adapters. It stores project-scoped data in PostgreSQL with pgvector embeddings, synthesizes conversation memory using Claude Haiku, and provides a workflow DAG executor with interactive visualization and approval panels. Currently stabilizing schema consistency (mem_ai_* tables), fixing data persistence across sessions, and automating memory file generation from unified event tables.
 
 ## Project Facts
 
@@ -73,7 +73,7 @@ Reviewer: ```json
 - **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
-- **database**: PostgreSQL 15+ per-project schema + shared auth/usage tables; agent roles initialized
+- **database**: PostgreSQL 15+
 - **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server
@@ -85,7 +85,7 @@ Reviewer: ```json
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
 - All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)
@@ -114,60 +114,62 @@ Reviewer: ```json
 ### `commit` — 2026-04-01
 
 diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
-index 09b9564..fb48ab8 100644
+index fb48ab8..67e9834 100644
 --- a/workspace/aicli/_system/project_state.json
 +++ b/workspace/aicli/_system/project_state.json
-@@ -38,17 +38,17 @@
-   "key_decisions": [
+@@ -39,14 +39,14 @@
      "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index 3c2c23f..169f604 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -29,7 +29,7 @@ You are a senior Python software architect with deep expertise in:
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
 - All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)


## AI Synthesis

**2026-04-01** `memory_synthesis` — Completed unified event table validation consolidating embeddings and memory events into mem_ai_events with normalized schema; removed deprecated event_summary_tags array and metadata columns for consistency. **2026-04-01** `schema_management` — Fixed mem_ai_tags_relations DDL and applied database migrations to ensure tags persist across session switches; root cause was cache invalidation triggering unnecessary DB re-loads. **2026-04-01** `documentation` — Updated project_state.json and rules.md to reflect mem_ai_* unified table naming convention; removed deprecated database_schema field for cleaner documentation. **2026-04-01** `infrastructure` — Implemented retry logic for backend startup race condition where AiCli project appeared in Recent but was unselectable on first load due to empty project list. **2026-04-01** `memory_files` — Established auto-regeneration pipeline for 5 memory files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from unified mem_ai_project_facts and mem_ai_work_items tables with timestamp tracking. **Session 319** — Maintained 318+ session continuity with dev_runtime_state tracking last_session_id, session_count, and provider preferences for seamless CLI experience.