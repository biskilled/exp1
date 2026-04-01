# Project Memory — aicli
_Generated: 2026-04-01 13:21 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to manage AI-assisted development workflows. It features dual storage (PostgreSQL + pgvector for semantic search), unified memory tables, LLM provider adapters, async DAG workflow execution with Cytoscape visualization, and Claude Haiku-powered memory synthesis generating 5 structured memory files. Currently stabilized with memory file auto-generation, unified event table validation, data persistence fixes, and clean schema documentation.

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
- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
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
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules; Claude Haiku for dual-layer memory synthesis generating 5 output files
- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load; backend_startup_race_condition mitigated
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking, not in summary arrays
- MCP server (stdio) with 12+ tools configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations (depends_on, relates_to, blocks, implements) managed via CLI/admin UI
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
- CLI: Python 3.12 + prompt_toolkit + rich with verb-noun command routing; memory endpoint template variable scoping fixed
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
- Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/

## In Progress

- Memory file auto-generation fully completed: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md regenerated from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
- Unified event table validation: mem_ai_events consolidates embeddings and memory events; removed deprecated event_summary_tags array and metadata columns; schema migration applied
- Data persistence bug fix: tags disappearing on session switch traced to cache invalidation during DB reload; fixed via mem_ai_tags_relations persistence with proper row ID linking
- Backend startup race condition resolved: AiCli project appearing in Recent but unselectable on first load fixed with retry logic for empty project list handling
- Schema documentation cleanup: project_state.json and rules.md updated to reflect mem_ai_* unified naming; removed conflicting legacy database_schema field
- Frontend UI refinement: removed lifecycle button section from entities.js drawer to align with current feature scope and reduce UI clutter

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 30d87bc..fe89c91 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -40,21 +40,21 @@
     "deployment_local": "bash start_backend.sh + ui/npm run dev"
   },
   "key_decisions": [
-    "Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state",
+    "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state and memory files",
     "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)",
-    "Electron desktop UI: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vanilla JS frontend (no framework/bundler); Vite dev server",
-    "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern",
-    "All LLM providers as independent adapters (Claude/OpenAI/DeepSeek/Gemini/Grok); Claude Haiku for dual-layer memory synthesis; server holds API keys",
-    "Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for negotiation",
-    "Memory synthesis: Claude Haiku dual-layer generates 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items",
+    "Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development",
+    "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients \u2192 Users; login_as_first_level_hierarchy pattern",
+    "LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules; Claude Haiku for dual-layer memory synthesis generating 5 output files",
+    "Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation",
+    "Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking",
     "_ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load; backend_startup_race_condition mitigated",
-    "Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations (linked via row id), not in summary arrays",
-    "MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management",
-    "Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements; smart chunking by per-class/function (Python/JS/TS), per-section (MD), per-file (diff)",
+    "Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking, not in summary arrays",
+    "MCP server (stdio) with 12+ tools configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management",
+    "Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations (depends_on, relates_to, blocks, implements) managed via CLI/admin UI",
     "Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server",
-    "CLI: Python 3.12 + prompt_toolkit + rich; command routing via verb-noun pattern; memory endpoint template variable scoping fixed",
-    "Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); lo

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index dcdeb3d..8bf6bf1 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-01T12:26:19Z",
+  "last_updated": "2026-04-01T12:37:21Z",
   "last_session_id": "11163d9b-a609-4847-8ca9-702fce4165c5",
-  "last_session_ts": "2026-04-01T12:26:19Z",
-  "session_count": 326,
+  "last_session_ts": "2026-04-01T12:37:21Z",
+  "session_count": 327,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 93ac067..8f5a7ae 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 09:06 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 12:26 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -46,18 +46,18 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Key Decisions
 
-- Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state
+- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state and memory files
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
-- Electron desktop UI: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
-- All LLM providers as independent adapters (Claude/OpenAI/DeepSeek/Gemini/Grok); Claude Haiku for dual-layer memory synthesis; server holds API keys
-- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for negotiation
-- Memory synthesis: Claude Haiku dual-layer generates 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items
+- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
+- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules; Claude Haiku for dual-layer memory synthesis generating 5 output files
+- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
+- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load; backend_startup_race_condition mitigated
-- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations (linked via row id), not in summary arrays
-- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
-- Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements; smart chunking by per-class/function (Python/JS/TS), per-section (MD), per-file (diff)
+- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking, not in summary arrays
+- MCP server (stdio) with 12+ tools configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
+- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations (depends_on, relates_to, blocks, implements) managed via CLI/admin UI
 - Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
-- CLI: Python 3.12 + prompt_toolkit + rich; command routing via verb-noun pattern; memory endpoint template variable scoping fixed
-- Deployment: Railway (Dockerfile + railway.toml) for 

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 33781e4..a5d4709 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -567,3 +567,5 @@
 {"ts": "2026-04-01T08:56:35Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "fc265cbe", "message": "chore: update system docs, memory, and session artifacts", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "6ea736e5", "message": "chore: update ai workspace state and trim MEMORY.md after session", "files_count": 31, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T09:06:35Z"}
 {"ts": "2026-04-01T09:06:25Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "6ea736e5", "message": "chore: update ai workspace state and trim MEMORY.md after session", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "f341693a", "message": "chore: update system files and memory after claude session", "files_count": 31, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T12:26:35Z"}
+{"ts": "2026-04-01T12:26:19Z", "action": "commit_push", "source": "claude_cli", "session_id": "11163d9b-a609-4847-8ca9-702fce4165c5", "hash": "f341693a", "message": "chore: update system files and memory after claude session", "pushed": true, "push_error": ""}


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 56d5794..e52de72 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-01 09:06 UTC by aicli /memory_
+_Generated: 2026-04-01 12:26 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to enable collaborative AI-assisted development with persistent context across multiple LLM tools. It features dual-storage (PostgreSQL 15+ + pgvector for semantic search), unified memory tables, async DAG workflow execution with Cytoscape visualization, and multi-provider LLM support (Claude, OpenAI, DeepSeek, Gemini, Grok) with server-side key management. Current focus is stabilizing schema consistency, validating data persistence across sessions, automating memory synthesis via Claude Haiku dual-layer processing, and resolving backend startup race conditions.
+aicli is a shared AI memory platform unifying development context across Claude CLI, LLM assistants, and web/desktop UIs through PostgreSQL semantic storage (pgvector), async DAG workflows, and Claude Haiku-powered memory synthesis. The architecture features an Electron desktop UI combining Vanilla JS with xterm.js, Monaco editor, and Cytoscape.js for workflow visualization; the backend is FastAPI-based with support for multiple LLM providers and MCP integration. Current focus is on stabilizing the unified mem_ai_* table schema, ensuring data persistence across session switches, and automating memory synthesis from project facts and work items.
 
 ## Project Facts
 
@@ -86,133 +86,83 @@ Reviewer: ```json
 
 ## Key Decisions
 
-- Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state
+- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state and memory files
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
-- Electron desktop UI: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
-- All LLM providers as independent adapters (Claude/OpenAI/DeepSeek/Gemini/Grok); Claude Haiku for dual-layer memory synthesis; server holds API keys
-- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for negotiation
-- Memory synthesis: Claude Haiku dual-layer generates 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items
+- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
+- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules; Claude Haiku for dual-layer memory synthesis generating 5 output files
+- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
+- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list o

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index 490106f..05ae0fa 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -26,21 +26,21 @@ You are a senior Python software architect with deep expertise in:
 
 ## Key Architectural Decisions
 
-- Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state
+- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state and memory files
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
-- Electron desktop UI: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
-- All LLM providers as independent adapters (Claude/OpenAI/DeepSeek/Gemini/Grok); Claude Haiku for dual-layer memory synthesis; server holds API keys
-- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for negotiation
-- Memory synthesis: Claude Haiku dual-layer generates 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items
+- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
+- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules; Claude Haiku for dual-layer memory synthesis generating 5 output files
+- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
+- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load; backend_startup_race_condition mitigated
-- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations (linked via row id), not in summary arrays
-- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
-- Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements; smart chunking by per-class/function (Python/JS/TS), per-section (MD), per-file (diff)
+- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking, not in summary arrays
+- MCP server (stdio) with 12+ tools configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
+- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations (depends_on, relates_to, blocks, implements) managed via CLI/admin UI
 - Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
-- CLI: Python 3.12 + prompt_toolkit + rich; command routing via verb-noun pattern; memory endpoint template variable scoping fixed
-- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local dev via bash start_backend.sh + ui/npm run dev
-- Config management: config.py with externalized settings; YAML f

## AI Synthesis

**2026-04-01** `memory_synthesis` — Completed unified memory file auto-generation: CLAUDE.md, MEMORY.md, context.md, rules.md, and copilot.md now regenerated from mem_ai_project_facts and mem_ai_work_items with full timestamp tracking integration. **2026-04-01** `database_migration` — Validated unified event table (mem_ai_events) consolidating embeddings and memory events; removed deprecated event_summary_tags array and metadata columns with schema migration applied. **2026-03-31** `data_persistence` — Fixed critical tag persistence bug where tags disappeared on session switch; root cause traced to cache invalidation during DB reload; resolved via mem_ai_tags_relations persistence with proper row ID linking. **2026-03-30** `backend_stability` — Resolved backend startup race condition preventing AiCli project selection on first load; implemented retry logic for empty project list handling in project initialization. **2026-03-29** `documentation` — Updated project_state.json and rules.md to reflect unified mem_ai_* table naming convention; removed conflicting legacy database_schema field for schema consistency. **2026-03-28** `frontend_ui` — Removed lifecycle button section from entities.js drawer to align with current feature scope and reduce UI complexity.