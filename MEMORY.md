# Project Memory — aicli
_Generated: 2026-04-01 18:05 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI for managing AI-assisted development workflows. The system unifies project facts, work items, and events in PostgreSQL with semantic search via pgvector, supporting multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) through provider adapters. Current development focuses on solidifying the unified database schema (mem_ai_* tables), fixing data persistence bugs across session switches, and ensuring reliable memory synthesis from project facts.

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
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + ui/npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state and memory files
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules; Claude Haiku for dual-layer memory synthesis generating 5 output files
- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking, not in summary arrays
- MCP server (stdio) with 12+ tools configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations (depends_on, relates_to, blocks, implements) via CLI/admin UI
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
- CLI: Python 3.12 + prompt_toolkit + rich with verb-noun command routing; memory endpoint template variable scoping fixed
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
- Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/

## In Progress

- Memory file auto-generation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md fully regenerated with timestamp tracking from mem_ai_project_facts and mem_ai_work_items (last run 2026-04-01T15:35:11Z)
- Unified event table consolidation: mem_ai_events schema validated; deprecated event_summary_tags array and metadata columns removed; data persistence across session switches confirmed
- Backend startup race condition resolved: retry logic implemented to handle empty project list on first load, preventing AiCli project from appearing unselectable in Recent
- Tag persistence bug fixed: mem_ai_tags_relations now properly maintains row ID linking and cache invalidation during DB reload operations
- Schema documentation updated: project_state.json and rules.md aligned with mem_ai_* unified naming; removed webpack reference in node_modules_build clarification
- Frontend UI refinement: lifecycle button section removed from entities.js drawer to reduce clutter and align with feature scope

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index fbce857..3c13ac4 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -16,7 +16,7 @@
     "workflow_engine": "Async DAG executor (asyncio.gather) + YAML config",
     "workflow_ui": "Cytoscape.js + cytoscape-dagre; 2-pane approval panel",
     "memory_synthesis": "Claude Haiku dual-layer with 5 output files",
-    "chunking": "Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)",
+    "chunking": "Smart chunking: per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)",
     "mcp": "Stdio MCP server with 12+ tools",
     "deployment": "Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev",
     "database_schema": "Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features",
@@ -29,7 +29,7 @@
     "backend_modules": "routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server",
     "dev_environment": "PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root",
     "database": "PostgreSQL 15+",
-    "node_modules_build": "npm 8+ with webpack/Electron-builder; dev server Vite on localhost",
+    "node_modules_build": "npm 8+ with Electron-builder; Vite dev server",
     "database_version": "PostgreSQL 15+",
     "build_tooling": "npm 8+ with Electron-builder; Vite dev server",
     "db_consolidation": "mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)",
@@ -83,12 +83,12 @@
     "config.py reads ~/.aicli/config.json for WORKSPACE_DIR at startup"
   ],
   "in_progress": [
-    "Memory file auto-generation fully completed: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md regenerated from mem_ai_project_facts and mem_ai_work_items with timestamp tracking",
-    "Unified event table validation: mem_ai_events consolidates embeddings and memory events; removed deprecated event_summary_tags array and metadata columns; schema migration applied",
-    "Data persistence bug fix: tags disappearing on session switch traced to cache invalidation during DB reload; fixed via mem_ai_tags_relations persistence with proper row ID linking",
-    "Backend startup race condition resolved: AiCli project appearing in Recent but unselectable on first load fixed with retry logic for empty project list handling",
-    "Schema documentation cleanup: project_state.json and rules.md updated to reflect mem_ai_* unified naming; removed conflicting legacy database_schema field",
-    "Frontend UI refinement: removed lifecycle button section from entities.js drawer to align with current feature scope and reduce UI clutter"
+    "Memory file auto-generation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md fully regenerated with timestamp tracking from mem_ai_project_facts and mem_ai_work_items",
+    "Unified event table consolidation: mem_ai_events schema validated; deprecated event_summary_tags array and metadata columns removed; data persistence across session switches confirmed",
+    "Backend startup race condition resolved: retry logic implemented to handle empty project list on first load, preventing AiCli project from appearing unselectable in Recent",
+    "Tag persistence bug fixed: mem_ai_tags_relations now properly maintains row ID linking and cache invalidation during DB reload operations",
+    "Schema documentation updated: project_state.json and rules.md aligned with mem_ai_* unified naming; legacy 

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 6f7afec..14a7b34 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-01T15:35:11Z",
-  "last_session_id": "11163d9b-a609-4847-8ca9-702fce4165c5",
-  "last_session_ts": "2026-04-01T15:35:11Z",
-  "session_count": 330,
+  "last_updated": "2026-04-01T18:01:39Z",
+  "last_session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d",
+  "last_session_ts": "2026-04-01T18:01:39Z",
+  "session_count": 331,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index f9f77a7..be64af7 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 13:58 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 15:35 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -21,7 +21,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
 - **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
 - **memory_synthesis**: Claude Haiku dual-layer with 5 output files
-- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
+- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
 - **mcp**: Stdio MCP server with 12+ tools
 - **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
 - **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
@@ -34,7 +34,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
 - **database**: PostgreSQL 15+
-- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
+- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with Electron-builder; Vite dev server
 - **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 0467e34..8e8b888 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -575,3 +575,5 @@
 {"ts": "2026-04-01T13:21:19Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "61db51e1", "message": "feat: add tag routing and enhance entities view with API updates", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "0a280e50", "message": "docs: update memory and rules after claude session 11163d9b", "files_count": 31, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T13:58:31Z"}
 {"ts": "2026-04-01T13:58:21Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "0a280e50", "message": "docs: update memory and rules after claude session 11163d9b", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "aed5228f", "message": "docs: update AI assistant rules and memory after session 11163d9b", "files_count": 31, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T15:35:20Z"}
+{"ts": "2026-04-01T15:35:10Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "aed5228f", "message": "docs: update AI assistant rules and memory after session 11163d9b", "pushed": true, "push_error": ""}


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 283f847..54ea12b 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-01 13:58 UTC by aicli /memory_
+_Generated: 2026-04-01 15:35 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to provide multi-LLM support (Claude, OpenAI, DeepSeek, Gemini, Grok) with persistent semantic memory via PostgreSQL+pgvector. The system recently stabilized core data persistence patterns, unified event/memory tables, and resolved startup race conditions. Currently at v2.2.0 with production deployments on Railway and desktop builds via Electron-builder.
+aicli is a shared AI memory platform combining a Python 3.12 CLI (prompt_toolkit + rich), FastAPI backend, PostgreSQL 15+ with pgvector semantic search, and Electron desktop UI (Vanilla JS + xterm.js + Monaco + Cytoscape). It orchestrates multi-LLM workflows (Claude/OpenAI/DeepSeek/Gemini/Grok) through async DAG execution, manages hierarchical user data (Clients → Users), and auto-generates 5 memory synthesis files using Claude Haiku from unified mem_ai_* tables. Current state: unified event schema fully validated, critical data persistence and backend startup bugs resolved, and documentation aligned with mem_ai_* naming conventions.
 
 ## Project Facts
 
@@ -61,7 +61,7 @@ Reviewer: ```json
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
 - **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
 - **memory_synthesis**: Claude Haiku dual-layer with 5 output files
-- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
+- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
 - **mcp**: Stdio MCP server with 12+ tools
 - **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
 - **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
@@ -74,7 +74,7 @@ Reviewer: ```json
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
 - **database**: PostgreSQL 15+
-- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
+- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with Electron-builder; Vite dev server
 - **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
@@ -104,12 +104,12 @@ Reviewer: ```json
 
 ## In Progress
 
-- Memory file auto-generation fully completed: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md regenerated from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
-- Unified event table validation: mem_ai_events consolidates embeddings and memory events; removed deprecated event_summary_tags array and metadata columns; schema migration applied
-- Data persistence bug fix: tags disappearing on session switch traced to cache invalidation during DB reload; fixed via mem_ai_tags_relations persistence with proper row ID linking


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/aicli/copilot.md b/workspace/aicli/_system/aicli/copilot.md
index 133853b..0a83758 100644
--- a/workspace/aicli/_system/aicli/copilot.md
+++ b/workspace/aicli/_system/aicli/copilot.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-01 13:58 UTC
+> Generated by aicli 2026-04-01 15:35 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -21,7 +21,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - workflow_engine: Async DAG executor (asyncio.gather) + YAML config
 - workflow_ui: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
 - memory_synthesis: Claude Haiku dual-layer with 5 output files
-- chunking: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
+- chunking: Smart chunking: per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
 - mcp: Stdio MCP server with 12+ tools
 - deployment: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
 - database_schema: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
@@ -34,7 +34,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - backend_modules: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - dev_environment: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
 - database: PostgreSQL 15+
-- node_modules_build: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
+- node_modules_build: npm 8+ with Electron-builder; Vite dev server
 - database_version: PostgreSQL 15+
 - build_tooling: npm 8+ with Electron-builder; Vite dev server
 - db_consolidation: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)


## AI Synthesis

**2026-04-01** `aicli` — Memory file auto-generation now fully regenerated with timestamp tracking; CLAUDE.md, MEMORY.md, context.md, rules.md, and copilot.md all sourced from mem_ai_project_facts and mem_ai_work_items unified tables.

**2026-04-01** `backend` — Unified event table (mem_ai_events) schema validated and consolidated; deprecated event_summary_tags array and metadata columns removed; data persistence confirmed across session switches.

**2026-04-01** `backend` — Backend startup race condition fixed with retry logic to handle empty project list on first load, preventing AiCli project from appearing unselectable in Recent projects list.

**2026-04-01** `database` — Tag persistence bug resolved; mem_ai_tags_relations now properly maintains row ID linking and cache invalidation during database reload operations.

**2026-04-01** `documentation` — Schema documentation updated: project_state.json and rules.md aligned with mem_ai_* unified naming convention; removed conflicting legacy references and clarified Electron-builder usage (no webpack).

**2026-04-01** `frontend` — Frontend UI refinement completed: lifecycle button section removed from entities.js drawer to reduce clutter and align with current feature scope.