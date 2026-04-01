# Project Memory — aicli
_Generated: 2026-04-01 01:52 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform built on Python (FastAPI backend) + Electron (Vanilla JS frontend) that integrates with Claude and multiple LLM providers via adapters. It stores project-scoped data in PostgreSQL with pgvector embeddings, synthesizes conversation memory using Claude Haiku, and provides a workflow DAG executor with interactive visualization and approval panels. Currently stabilizing schema consistency (mem_ai_* tables), fixing data persistence across sessions, and automating memory file generation from unified event tables.

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
index fb48ab8..67e9834 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -39,14 +39,14 @@
     "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",
     "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables",
     "Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server",
-    "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients \u2192 Users",
+    "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern",
     "All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys",
-    "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization",
+    "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel",
     "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)",
-    "Unified event table mem_ai_events consolidates embeddings and memory events with event_type column",
-    "Tags stored in mem_ai_tags_relations (linked via row id), not in summary_tags array; sourced from MRR",
+    "Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary, event_type) consolidates embeddings and memory events",
+    "Tags stored in mem_ai_tags_relations (linked via row id), not summary_tags array; sourced from MRR when applicable",
     "_ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load",
-    "Tags load once on project access into memory; cache invalidation on session/project switch forces re-load",
+    "Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB",
     "Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements",
     "MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT)",
     "Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer",
@@ -116,20 +116,20 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-01T01:15:43Z",
+  "last_memory_run": "2026-04-01T01:36:36Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state",
       "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables",
       "Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server",
-      "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients \u2192 Users",
+      "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern",
       "All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys",
-      "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization",
+      "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel",
       "Me

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index d882c65..0e44fb6 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-01T01:36:12Z",
+  "last_updated": "2026-04-01T01:40:17Z",
   "last_session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d",
-  "last_session_ts": "2026-04-01T01:36:12Z",
-  "session_count": 316,
+  "last_session_ts": "2026-04-01T01:40:17Z",
+  "session_count": 317,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 519c9aa..de0d093 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 01:15 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 01:36 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -45,14 +45,14 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
 - All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys
-- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization
+- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)
-- Unified event table mem_ai_events consolidates embeddings and memory events with event_type column
-- Tags stored in mem_ai_tags_relations (linked via row id), not in summary_tags array; sourced from MRR
+- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary, event_type) consolidates embeddings and memory events
+- Tags stored in mem_ai_tags_relations (linked via row id), not summary_tags array; sourced from MRR when applicable
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load
-- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load
+- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
 - Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT)
 - Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 241a6b0..cfc0d86 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -547,3 +547,5 @@
 {"ts": "2026-04-01T01:05:52Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "56e37c54", "message": "chore: update aicli workspace state and trim database boilerplate", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "5b05724a", "message": "chore: update ai system files and memory/tagging backend logic", "files_count": 36, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T01:15:33Z"}
 {"ts": "2026-04-01T01:15:29Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "5b05724a", "message": "chore: update ai system files and memory/tagging backend logic", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "d3c9f49e", "message": "chore: update ai context files and session state after cli session", "files_count": 38, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T01:36:19Z"}
+{"ts": "2026-04-01T01:36:12Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "d3c9f49e", "message": "chore: update ai context files and session state after cli session", "pushed": true, "push_error": ""}


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 726ff01..e1112f8 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,51 @@
 # Project Memory — aicli
-_Generated: 2026-04-01 01:15 UTC by aicli /memory_
+_Generated: 2026-04-01 01:36 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a FastAPI backend with PostgreSQL 15+ (pgvector) semantic storage, an Electron UI with xterm.js/Monaco/Cytoscape.js visualization, and a Python 3.12 CLI. It manages multi-user projects with per-schema isolation, unified event tables, smart memory synthesis (Claude Haiku dual-layer), async DAG workflows, and MCP tool integration. Current focus is validating unified event table consolidation, fixing tag persistence across session switches, and automating memory file generation from project facts.
+aicli is a shared AI memory platform combining a Python CLI frontend with a FastAPI backend, PostgreSQL 15+ storage with pgvector semantic search, and an Electron-based Vanilla JS UI. It implements a 5-layer memory synthesis system using Claude Haiku, async DAG workflow execution with visual Cytoscape.js graphs, and hierarchical authentication (Clients→Users with JWT+bcrypt). Currently stabilizing schema consolidation (mem_ai_* tables), automating memory file generation, and validating data persistence across session switches after recent backend race condition fixes.
+
+## Project Facts
+
+- **auth_pattern**: login_as_first_level_hierarchy
+- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
+- **data_model_hierarchy**: clients_contain_multiple_users
+- **data_persistence_issue**: tags_disappear_on_session_switch
+- **db_engine**: SQL
+- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
+- **deployment_target**: Claude_CLI_and_LLM_platforms
+- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
+- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
+- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
+- **memory_management_pattern**: load_once_on_access_update_on_save
+- **pending_implementation**: memory_items_and_project_facts_table_population
+- **pending_issues**: project_visibility_bug_active_project_not_displaying
+- **performance_optimization**: redundant_SQL_calls_eliminated
+- **pipeline/auth**: Acceptance criteria:
+# PM Analysis: Email Verification Feature
+
+---
+
+## Context Summary
+
+The tagged context reveals this work item is an **incremental enhancement** to an existing authentication system. Sign In and Create Account forms are already live and functional. The prior PM analysis identified email verification as the missing layer—the system currently accepts any email without confirming ownership. The analys
+
+Reviewer: ```json
+{
+  "passed": false,
+  "score": 4,
+  "issues": [
+    "Implementation is incomplete — cuts off mid-file in EmailService.ts without finishing AWS SES client setup, email template loading, or the
+- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
+- **stale_code_removed**: db_ensure_project_schema_call_replaced_with_ensure_shared_schema
+- **tagging_system**: nested_hierarchy_beyond_2_levels
+- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
+- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
+- **ui_library**: 3_dot_menu_pattern
+- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
+- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition
 
 ## Tech Stack
 
@@ -45,14 +85,14 @@ aicli is a shared AI memory platform combining a FastAPI backend with PostgreSQL
 - Engi

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index 45e97c2..169f604 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -29,14 +29,14 @@ You are a senior Python software architect with deep expertise in:
 - Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
 - Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
 - All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys
-- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization
+- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)
-- Unified event table mem_ai_events consolidates embeddings and memory events with event_type column
-- Tags stored in mem_ai_tags_relations (linked via row id), not in summary_tags array; sourced from MRR
+- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary, event_type) consolidates embeddings and memory events
+- Tags stored in mem_ai_tags_relations (linked via row id), not summary_tags array; sourced from MRR when applicable
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load
-- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load
+- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
 - Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT)
 - Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer


## AI Synthesis

**2026-04-01** `system` — Schema documentation and database naming conventions stabilized; mem_ai_* prefix tables now standard across all per-project and unified storage layers (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features). **2026-04-01** `backend` — Tag persistence validation completed; tags now persist across session switches via mem_ai_tags_relations table with proper cache invalidation on project/session switches. **2026-04-01** `memory_system` — Memory synthesis automation refined; five-file output pipeline (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) now auto-regenerates with timestamp tracking from unified event and project facts tables. **2026-04-01** `startup` — Backend race condition mitigated; retry logic handles empty project list on first load, preventing AiCli from appearing unselectable in Recent projects. **2026-03-14** `architecture` — Unified event table mem_ai_events schema finalized with (id, project_id, session_id, session_desc, event_summary, event_type) consolidating embeddings and memory events; removed deprecated summary_tags array and metadata columns. **2026-03-14** `data_model` — Memory management pattern established as load_once_on_access with update_on_save, triggered by memory endpoint and synthesis layer; cache invalidation forces fresh DB reload on navigation.