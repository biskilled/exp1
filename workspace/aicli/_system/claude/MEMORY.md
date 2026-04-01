# Project Memory — aicli
_Generated: 2026-04-01 01:05 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI for context-aware development workflows. It uses PostgreSQL with pgvector for semantic search, Claude Haiku for memory synthesis, and a DAG-based async workflow engine with visual approval panels. Current focus is finalizing schema consolidation (mem_ai_* unified tables), resolving data persistence issues on session switches, and fixing backend startup race conditions affecting project initialization.

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
- Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server on localhost
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
- All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)
- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary, event_type) consolidates embeddings and memory events
- Tag storage architecture: tags belong in mem_ai_tags_relations (linked via row id), not summary_tags array; sourced from MRR when applicable
- _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
- Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work items
- Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
- Deployment: Railway (Dockerfile + railway.toml) for cloud; local dev via bash start_backend.sh + ui/npm run dev

## In Progress

- Tag column schema correction: fixed mem_ai_tags_relations table reference in DDL; verified database migrations applied and testing persistence across session switches
- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from mem_ai_project_facts and mem_ai_work_items with proper timestamp tracking
- Unified event table validation: confirmed mem_ai_events consolidates pr_embeddings/pr_memory_events with event_type column; removed event_summary_tags array and deprecated metadata (language, file_path)
- Backend startup race condition: AiCli appearing in Recent projects but unselectable on first load; retry logic in place for empty project list with session state persistence
- Data persistence validation: investigated tags disappearing on session switch; root cause traced to cache invalidation triggering DB re-load; migration testing in progress
- Schema documentation cleanup: updated project_state.json and rules.md to reflect current mem_ai_* table naming convention and removal of deprecated columns from mem_ai_events

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index a63440b..1753eb4 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -43,8 +43,8 @@
     "All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none",
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval",
     "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files); reduces token overhead",
-    "Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events with event_type column",
-    "Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features",
+    "Unified event table mem_ai_events consolidates pr_embeddings/pr_memory_events with event_type column for classification",
+    "Table naming convention: mem_ai_* prefix (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features)",
     "Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy",
     "_ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load",
     "Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB",
@@ -116,7 +116,7 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-03-31T23:43:36Z",
+  "last_memory_run": "2026-04-01T00:17:19Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",
@@ -126,8 +126,8 @@
       "All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none",
       "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval",
       "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files); reduces token overhead",
-      "Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events with event_type column",
-      "Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features",
+      "Unified event table mem_ai_events consolidates pr_embeddings/pr_memory_events with event_type column for classification",
+      "Table naming convention: mem_ai_* prefix (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features)",
       "Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy",
       "_ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load",
       "Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB",
@@ -150,15 +150,19 @@
       "ui_components": "xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre",
       "storage_primary": "PostgreSQL 15+ with per-project schema",
       "storage_semantic": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
-      "db_schema": "Unified: mem_ai_events (with event_type, summary_tags removed), mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles",
+      "database_version": "PostgreSQL 15+",
       "authentication": "JWT (python-jose

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index ad2c837..c39ae74 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-01T00:16:58Z",
+  "last_updated": "2026-04-01T00:38:28Z",
   "last_session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d",
-  "last_session_ts": "2026-04-01T00:16:58Z",
-  "session_count": 312,
+  "last_session_ts": "2026-04-01T00:38:28Z",
+  "session_count": 313,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 5e6907e..a6147bf 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 23:43 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 00:16 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -49,19 +49,11 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events with event_type column
-- Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
+- Unified event table mem_ai_events consolidates pr_embeddings/pr_memory_events with event_type column for classification
+- Table naming convention: mem_ai_* prefix (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features)
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
 - Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
-
-## Recent Context (last 5 changes)
-
-- [2026-03-31] perfect. I would like to have an updated aicli_memory with all updated memory strucuture. Also please advise about the n
-- [2026-03-31] Is it advised to merge pr_session_summeries into mem_ai_events. make sure there is column event_type (in this case event
-- [2026-03-31] I think llm_source is missing in mem_ai_events. I also see columns that I am not sure are used anymore like language or 
-- [2026-03-31] It seems that I cannot see the changes in the db
-- [2026-03-31] It is working noew. ddl is updated. still I do se columns that I am not sure are relevant. for example - language or fil
\ No newline at end of file


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index bcee3b7..535bc27 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -539,3 +539,5 @@
 {"ts": "2026-03-31T23:31:37Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "b6f68047", "message": "chore: update ai context files and refactor database.py", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "da3644d4", "message": "fix: improve memory tagging and routing stability", "files_count": 30, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T23:43:10Z"}
 {"ts": "2026-03-31T23:43:03Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "da3644d4", "message": "fix: improve memory tagging and routing stability", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "5f1cda6c", "message": "chore: update AI context files and refactor backend core modules", "files_count": 40, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T00:17:06Z"}
+{"ts": "2026-04-01T00:16:58Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "5f1cda6c", "message": "chore: update AI context files and refactor backend core modules", "pushed": true, "push_error": ""}


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 83fa723..851cc65 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-03-31 23:43 UTC by aicli /memory_
+_Generated: 2026-04-01 00:16 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform built on Python 3.12 + FastAPI backend and Electron frontend, enabling multi-user collaborative AI workflows with persistent semantic memory via PostgreSQL + pgvector. Currently stabilizing unified database schema (mem_ai_* tables) and tag management architecture to ensure data persistence and support automated memory file generation from project facts, work items, and interaction history.
+aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron UI with PostgreSQL storage and semantic search via pgvector. It manages project-scoped memory through unified event tables (mem_ai_*), integrates multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) for synthesis and analysis, and provides async DAG workflow execution with visual approval workflows. Current focus is on fixing schema inconsistencies, automating memory file generation from structured project facts, validating data persistence across sessions, and resolving backend startup initialization delays.
 
 ## Project Facts
 
@@ -89,8 +89,8 @@ Reviewer: ```json
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events with event_type column
-- Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
+- Unified event table mem_ai_events consolidates pr_embeddings/pr_memory_events with event_type column for classification
+- Table naming convention: mem_ai_* prefix (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features)
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
@@ -114,15 +114,15 @@ Reviewer: ```json
 ### `commit` — 2026-03-31
 
 diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
-index c985ea3..5dc6699 100644
+index 5dc6699..0ae4598 100644
 --- a/workspace/aicli/_system/project_state.json
 +++ b/workspace/aicli/_system/project_state.json
 @@ -10,7 +10,7 @@
      "ui_components": "xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre",
      "storage_primary": "PostgreSQL 15+ with per-project schema",
      "storage_semantic": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
--    "db_schema": "Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys",
-+    "db_schema": "Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys",
+-  

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index a158cf5..68ce63e 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -33,8 +33,8 @@ You are a senior Python software architect with deep expertise in:
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events with event_type column
-- Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
+- Unified event table mem_ai_events consolidates pr_embeddings/pr_memory_events with event_type column for classification
+- Table naming convention: mem_ai_* prefix (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features)
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB


## AI Synthesis

**[2026-04-01]** `db_schema` — Unified mem_ai_events table now consolidates pr_embeddings and pr_memory_events with event_type column for classification; removed deprecated summary_tags array and metadata columns (language, file_path). **[2026-03-31]** `tag_architecture` — Confirmed tags belong in mem_ai_tags_relations linked via row id, not in event summary_tags; tags sourced from MRR when applicable and loaded once on project access. **[2026-03-31]** `memory_files` — Automated generation of 5 memory files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items via Claude Haiku dual-layer synthesis. **[2026-03-31]** `data_persistence` — Investigated tags disappearing on session switch; root cause traced to cache invalidation triggering DB re-load; DDL updated and persistence testing underway. **[2026-03-31]** `schema_cleanup` — Validated language and file_path columns in mem_ai_events are no longer relevant; updated project state documentation and removed deprecated references. **[2026-03-31]** `startup_race` — Backend startup race condition identified: AiCli appearing in Recent projects but unselectable due to initialization delay; retry logic now handles empty project list on first load.