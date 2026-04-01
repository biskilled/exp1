# Project Memory — aicli
_Generated: 2026-04-01 01:36 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI frontend with a FastAPI backend, PostgreSQL 15+ storage with pgvector semantic search, and an Electron-based Vanilla JS UI. It implements a 5-layer memory synthesis system using Claude Haiku, async DAG workflow execution with visual Cytoscape.js graphs, and hierarchical authentication (Clients→Users with JWT+bcrypt). Currently stabilizing schema consolidation (mem_ai_* tables), automating memory file generation, and validating data persistence across session switches after recent backend race condition fixes.

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
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); local: bash start_backend.sh + ui/npm run dev
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
- **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features

## Key Decisions

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
- Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
- All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)
- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary, event_type) consolidates embeddings and memory events
- Tags stored in mem_ai_tags_relations (linked via row id), not summary_tags array; sourced from MRR when applicable
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
- Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT)
- Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
- Deployment: Railway (Dockerfile + railway.toml) for cloud; local dev via bash start_backend.sh + ui/npm run dev

## In Progress

- Tag column schema correction: fixed mem_ai_tags_relations table reference in DDL; database migrations applied and persistence validation across session switches
- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
- Unified event table validation: confirmed mem_ai_events consolidates pr_embeddings/pr_memory_events; removed event_summary_tags array and deprecated metadata
- Backend startup race condition: AiCli appearing in Recent projects but unselectable on first load; retry logic implemented for empty project list
- Data persistence validation: investigated tags disappearing on session switch; root cause traced to cache invalidation triggering DB re-load
- Schema documentation cleanup: updated project_state.json and rules.md to reflect mem_ai_* table naming and removed deprecated columns

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index f874071..09b9564 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -10,7 +10,7 @@
     "ui_components": "xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre",
     "storage_primary": "PostgreSQL 15+ with per-project schema",
     "storage_semantic": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
-    "db_schema": "Unified: mem_ai_events (with event_type, summary_tags removed), mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles",
+    "db_schema": "Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles",
     "authentication": "JWT (python-jose) + bcrypt + DEV_MODE toggle",
     "llm_providers": "Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok",
     "workflow_engine": "Async DAG executor (asyncio.gather) + YAML config",
@@ -39,18 +39,18 @@
     "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",
     "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables",
     "Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server on localhost",
-    "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys",
+    "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern",
     "All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys; client sends none",
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel",
     "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)",
     "Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary, event_type) consolidates embeddings and memory events",
     "Tag storage architecture: tags belong in mem_ai_tags_relations (linked via row id), not summary_tags array; sourced from MRR when applicable",
-    "Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy",
     "_ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load",
     "Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB",
     "Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements",
     "MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work items",
-    "Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer"
+    "Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer",
+    "Deployment: Railway (Dockerfile + railway.toml) for cloud; local dev via bash start_backend.sh + ui/npm run dev"
   ],
   "implemented_features": [
     "5-layer memory architecture with /memory endpoint + LLM synthesis via Haiku",
@@ -79,12 +79,12 @@
     "config.py reads ~/.aicli/config.json for WORKSPACE_DIR at startup"
   ],
   "in_progress": [
-    "Tag column schema correction: fixed mem_ai_tags_relations table reference (was mng_a

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 871d720..6b99cef 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-01T01:05:53Z",
+  "last_updated": "2026-04-01T01:15:29Z",
   "last_session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d",
-  "last_session_ts": "2026-04-01T01:05:53Z",
-  "session_count": 314,
+  "last_session_ts": "2026-04-01T01:15:29Z",
+  "session_count": 315,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index b5fa8c2..2957e7e 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 00:38 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 01:05 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -15,7 +15,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - **storage_primary**: PostgreSQL 15+ with per-project schema
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Unified: mem_ai_events (with event_type, summary_tags removed), mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
+- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle
 - **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
@@ -45,15 +45,15 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server on localhost
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
 - All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)
 - Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary, event_type) consolidates embeddings and memory events
 - Tag storage architecture: tags belong in mem_ai_tags_relations (linked via row id), not summary_tags array; sourced from MRR when applicable
-- Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
 - Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work items
 - Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
+- Deployment: Railway (Dockerfile + railway.toml) for cloud; local dev via bash start_backend.sh + ui/npm run dev


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 4f9a399..e5686e6 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -543,3 +543,5 @@
 {"ts": "2026-04-01T00:16:58Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "5f1cda6c", "message": "chore: update AI context files and refactor backend core modules", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "5df58ee0", "message": "chore: update ai system files and refactor backend modules", "files_count": 36, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T00:38:39Z"}
 {"ts": "2026-04-01T00:38:28Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "5df58ee0", "message": "chore: update ai system files and refactor backend modules", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "56e37c54", "message": "chore: update aicli workspace state and trim database boilerplate", "files_count": 34, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T01:06:00Z"}
+{"ts": "2026-04-01T01:05:52Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "56e37c54", "message": "chore: update aicli workspace state and trim database boilerplate", "pushed": true, "push_error": ""}


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index e479717..581443b 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-01 00:38 UTC by aicli /memory_
+_Generated: 2026-04-01 01:05 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform built on FastAPI + PostgreSQL + pgvector, providing a unified event storage system (mem_ai_events) with semantic search, workflow automation via async DAG execution, and a desktop UI powered by Electron + xterm.js + Cytoscape.js. Currently stabilizing tag persistence, auto-generating memory files, and resolving backend startup race conditions to ensure reliable project initialization and session data consistency.
+aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI for context-aware development workflows. It uses PostgreSQL with pgvector for semantic search, Claude Haiku for memory synthesis, and a DAG-based async workflow engine with visual approval panels. Current focus is finalizing schema consolidation (mem_ai_* unified tables), resolving data persistence issues on session switches, and fixing backend startup race conditions affecting project initialization.
 
 ## Project Facts
 
@@ -55,7 +55,7 @@ Reviewer: ```json
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - **storage_primary**: PostgreSQL 15+ with per-project schema
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Unified: mem_ai_events (with event_type, summary_tags removed), mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
+- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle
 - **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
@@ -85,27 +85,27 @@ Reviewer: ```json
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server on localhost
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
 - All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)
 - Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary, event_type) consolidates embeddings and memory events
 - Tag storage architecture: tags belong in mem_ai_tags_relations (linked via row id), not summary_tags array; sourced from MRR when applicable
-- Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hi

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index a0e3471..c3c1cd2 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -29,18 +29,18 @@ You are a senior Python software architect with deep expertise in:
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server on localhost
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
 - All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)
 - Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary, event_type) consolidates embeddings and memory events
 - Tag storage architecture: tags belong in mem_ai_tags_relations (linked via row id), not summary_tags array; sourced from MRR when applicable
-- Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
 - Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work items
 - Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
+- Deployment: Railway (Dockerfile + railway.toml) for cloud; local dev via bash start_backend.sh + ui/npm run dev
 
 ---
 


## AI Synthesis

**[2026-04-01]** `schema_migration` — Consolidated mem_ai_tags_relations table schema; removed deprecated event_summary_tags array from mem_ai_events and corrected DDL references across all per-project schemas. **[2026-04-01]** `automation` — Implemented automatic memory file generation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md now regenerate from mem_ai_project_facts and mem_ai_work_items with UTC timestamp tracking on each /memory endpoint call. **[2026-03-31]** `data_model` — Confirmed unified event table mem_ai_events architecture consolidating pr_embeddings and pr_memory_events; validated event_type column usage and removed redundant metadata columns. **[2026-03-30]** `bug_fix` — Fixed backend startup race condition where AiCli appeared in Recent projects but remained unselectable on first load; implemented retry logic for empty project list with exponential backoff. **[2026-03-29]** `debugging` — Traced tags disappearing on session switch to cache invalidation pattern forcing DB re-load; implemented proper cache lifecycle management tied to session and project context switches. **[2026-03-28]** `documentation` — Updated project_state.json and rules.md to reflect mem_ai_* unified table naming convention; removed references to deprecated 3-tier role model in favor of hierarchical Clients→Users architecture.