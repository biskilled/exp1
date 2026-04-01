# Project Memory — aicli
_Generated: 2026-04-01 02:11 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python/FastAPI backend, Electron desktop UI, and PostgreSQL semantic storage to enable collaborative AI-assisted development. The system synthesizes project context via Claude Haiku, executes async DAG workflows, and manages memory persistence across unified mem_ai_* tables with intelligent chunking and tagging. Current focus: solidifying data persistence across session switches, automating memory file generation, and resolving backend startup race conditions.

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
- **storage_primary**: PostgreSQL 15+ per-project schema
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
- **config_management**: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
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
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
- All LLM providers as independent adapters (Claude/OpenAI/DeepSeek/Gemini/Grok); Claude Haiku for dual-layer memory synthesis; server holds API keys
- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for negotiation
- Memory synthesis: Claude Haiku dual-layer generates 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items
- Tags stored in mem_ai_tags_relations (linked via row id), not in summary arrays; sourced from MRR when applicable; load once on project access, cache invalidation on switch
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load; backend_startup_race_condition mitigated
- Data persistence: load_once_on_access, update_on_save pattern; tags disappearing on session switch traced to cache invalidation triggering DB re-load
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements; smart chunking by per-class/function (Python/JS/TS), per-section (MD), per-file (diff)
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix)
- CLI: Python 3.12 + prompt_toolkit + rich; memory endpoint template variable scoping fixed at line 1120
- Deployment: Railway (Dockerfile + railway.toml) for cloud; local dev via bash start_backend.sh + ui/npm run dev; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)

## In Progress

- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from unified mem_ai_* tables with timestamp tracking
- Unified event table validation: mem_ai_events consolidates embeddings and memory events; removed event_summary_tags array and deprecated metadata columns
- Data persistence validation: tags disappearing on session switch root cause traced to cache invalidation triggering DB re-load; fix ensures persistence across switches
- Schema documentation cleanup: updated project_state.json and rules.md to reflect mem_ai_* unified table naming and removed deprecated columns
- Tag column schema correction: mem_ai_tags_relations table DDL fixed; database migrations applied and persistence validated
- Backend startup race condition: AiCli appearing in Recent projects but unselectable on first load; retry logic implemented for empty project list

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 67e9834..3e3d1d4 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -15,11 +15,11 @@
     "llm_providers": "Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok",
     "workflow_engine": "Async DAG executor (asyncio.gather) + YAML config",
     "workflow_ui": "Cytoscape.js + cytoscape-dagre; 2-pane approval panel",
-    "memory_synthesis": "Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files)",
+    "memory_synthesis": "Claude Haiku dual-layer with 5 output files",
     "chunking": "Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)",
     "mcp": "Stdio MCP server with 12+ tools",
     "deployment": "Railway (Dockerfile + railway.toml); local: bash start_backend.sh + ui/npm run dev",
-    "database_schema": "Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles",
+    "database_schema": "Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features",
     "config_management": "config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support",
     "db_tables": "Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles",
     "llm_provider_adapters": "agents/providers/ with pr_ prefix for pricing and provider implementations",
@@ -39,7 +39,7 @@
     "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",
     "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables",
     "Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server",
-    "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern",
+    "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients \u2192 Users; login_as_first_level_hierarchy pattern",
     "All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys",
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel",
     "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)",
@@ -116,13 +116,13 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-01T01:36:36Z",
+  "last_memory_run": "2026-04-01T01:40:36Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",
       "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables",
       "Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server",
-      "JWT a

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 0e44fb6..d5f69f6 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-01T01:40:17Z",
+  "last_updated": "2026-04-01T01:52:10Z",
   "last_session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d",
-  "last_session_ts": "2026-04-01T01:40:17Z",
-  "session_count": 317,
+  "last_session_ts": "2026-04-01T01:52:10Z",
+  "session_count": 318,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index de0d093..582e239 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 01:36 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 01:40 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -20,11 +20,11 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
 - **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
-- **memory_synthesis**: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files)
+- **memory_synthesis**: Claude Haiku dual-layer with 5 output files
 - **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
 - **mcp**: Stdio MCP server with 12+ tools
 - **deployment**: Railway (Dockerfile + railway.toml); local: bash start_backend.sh + ui/npm run dev
-- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
+- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
 - **config_management**: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
 - **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
@@ -45,7 +45,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
 - All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index cfc0d86..c25c37a 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -549,3 +549,5 @@
 {"ts": "2026-04-01T01:15:29Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "5b05724a", "message": "chore: update ai system files and memory/tagging backend logic", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "d3c9f49e", "message": "chore: update ai context files and session state after cli session", "files_count": 38, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T01:36:19Z"}
 {"ts": "2026-04-01T01:36:12Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "d3c9f49e", "message": "chore: update ai context files and session state after cli session", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "d2c4222a", "message": "chore: update AI context files and session memory logs", "files_count": 32, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T01:40:24Z"}
+{"ts": "2026-04-01T01:40:17Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "d2c4222a", "message": "chore: update AI context files and session memory logs", "pushed": true, "push_error": ""}


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index e1112f8..d8a8c87 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-01 01:36 UTC by aicli /memory_
+_Generated: 2026-04-01 01:40 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python CLI frontend with a FastAPI backend, PostgreSQL 15+ storage with pgvector semantic search, and an Electron-based Vanilla JS UI. It implements a 5-layer memory synthesis system using Claude Haiku, async DAG workflow execution with visual Cytoscape.js graphs, and hierarchical authentication (Clients→Users with JWT+bcrypt). Currently stabilizing schema consolidation (mem_ai_* tables), automating memory file generation, and validating data persistence across session switches after recent backend race condition fixes.
+aicli is a shared AI memory platform that integrates with Claude and other LLM providers via a Python CLI backend and Electron-based frontend, enabling persistent project context management across sessions. The system uses PostgreSQL with pgvector for semantic search, unified mem_ai_* tables for memory storage, and async DAG workflows for task execution. Currently stabilizing schema correctness, memory file automation, and data persistence across session switches to ensure reliable context retention.
 
 ## Project Facts
 
@@ -60,11 +60,11 @@ Reviewer: ```json
 - **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
 - **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
-- **memory_synthesis**: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files)
+- **memory_synthesis**: Claude Haiku dual-layer with 5 output files
 - **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
 - **mcp**: Stdio MCP server with 12+ tools
 - **deployment**: Railway (Dockerfile + railway.toml); local: bash start_backend.sh + ui/npm run dev
-- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
+- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
 - **config_management**: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
 - **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
@@ -85,7 +85,7 @@ Reviewer: ```json
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_lev

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index 169f604..3c2c23f 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -29,7 +29,7 @@ You are a senior Python software architect with deep expertise in:
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
 - All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)


## AI Synthesis

**2026-04-01** `internal` — Memory synthesis output files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) now auto-regenerate from unified mem_ai_* tables with timestamp tracking for consistency across session switches. **2026-04-01** `internal` — Unified event table mem_ai_events finalized; event_summary_tags array and deprecated metadata columns removed to consolidate embeddings and memory events into single source of truth. **2026-04-01** `internal` — Tag persistence issue resolved: cache invalidation on session/project switch forced DB re-load; tags stored in mem_ai_tags_relations linked via row id instead of summary arrays. **2026-04-01** `schema` — Database schema documentation updated in project_state.json and rules.md to reflect unified mem_ai_* table naming (events, tags_relations, project_facts, work_items, features) plus per-project and shared tables. **2026-04-01** `database` — mem_ai_tags_relations schema corrections applied with DDL fix and database migrations; persistence validation confirmed across session boundaries. **2026-03-14** `backend` — Backend startup race condition mitigated: AiCli appearing unselectable on first load due to empty project list; retry logic implemented in project initialization. **2026-03-14** `architecture` — Dual-layer memory synthesis via Claude Haiku: raw JSONL → interaction_tags → 5 standardized output files for memory management and code context. **2026-03-14** `api` — Memory endpoint template variable scoping fixed at line 1120; code_dir variable now correctly scoped for per-project memory file generation. **2026-03-14** `integration` — MCP server (stdio) with 12+ tools configured via env vars (BACKEND_URL, ACTIVE_PROJECT) for embedding and data retrieval in work item management workflows. **2026-03-14** `deployment` — Unified local dev environment: bash start_backend.sh + ui/npm run dev; Railway cloud deployment with Dockerfile and railway.toml; Electron-builder for Mac/Windows/Linux desktop.