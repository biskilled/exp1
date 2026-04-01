# Project Memory — aicli
_Generated: 2026-04-01 00:16 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron UI with PostgreSQL storage and semantic search via pgvector. It manages project-scoped memory through unified event tables (mem_ai_*), integrates multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) for synthesis and analysis, and provides async DAG workflow execution with visual approval workflows. Current focus is on fixing schema inconsistencies, automating memory file generation from structured project facts, validating data persistence across sessions, and resolving backend startup initialization delays.

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
- **db_schema**: Unified: mem_ai_events (with event_type, summary_tags removed), mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
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
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features

## Key Decisions

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas
- Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys
- All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
- Unified event table mem_ai_events consolidates pr_embeddings/pr_memory_events with event_type column for classification
- Table naming convention: mem_ai_* prefix (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features)
- Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
- _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
- Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
- Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer

## In Progress

- Tag column schema correction: fixed mem_ai_tags_relations table reference (was mng_ai_tags_relations) in DDL and verified database migrations applied
- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from mem_ai_project_facts, mem_ai_work_items, sessions
- Tag storage architecture clarification: tags belong in mem_ai_tags_relations (linked via row id), not summary_tags array; tags sourced from MRR when applicable
- Schema column cleanup: validating relevance of language and file_path columns in mem_ai_events; removing unnecessary metadata fields
- Data persistence validation: tags disappearing on session switch root cause investigation (DDL now updated, testing persistence)
- Backend startup race condition: AiCli appearing in Recent projects but remaining unselectable due to dev environment initialization delay

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 5dc6699..0ae4598 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -10,7 +10,7 @@
     "ui_components": "xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre",
     "storage_primary": "PostgreSQL 15+ with per-project schema",
     "storage_semantic": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
-    "db_schema": "Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys",
+    "db_schema": "Unified: mem_ai_events (with event_type), mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles",
     "authentication": "JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free",
     "llm_providers": "Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok",
     "workflow_engine": "Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic",
@@ -43,13 +43,13 @@
     "All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none",
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval",
     "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files); reduces token overhead",
-    "Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events",
-    "Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features",
+    "Unified event table mem_ai_events consolidates pr_embeddings/pr_memory_events with event_type column for classification",
+    "Table naming convention: mem_ai_* prefix (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features)",
     "Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy",
     "_ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load",
     "Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB",
-    "MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval",
     "Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements",
+    "MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval",
     "Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer"
   ],
   "implemented_features": [
@@ -79,11 +79,11 @@
     "config.py reads ~/.aicli/config.json for WORKSPACE_DIR at startup"
   ],
   "in_progress": [
-    "Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md + system prompts for all LLM providers auto-regenerated from mem_ai_project_facts, mem_ai_work_items, sessions (Layer 1 priority)",
-    "Unified memory structure review: clarifying relationships between tagging mechanism (mem_ai_tags_relations), mem_ai_project_facts, and mem_ai_work_items population flow",
-    "Table consolidation completion: verify mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features schema implementation and data migration",
-    "Tagging functionality validation: confirm mem_ai_tags_relations table implementation and ensure all tagging prompts align with feature classification (feature/bug

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index ce0cdb2..fb3806e 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-03-31T22:53:33Z",
+  "last_updated": "2026-03-31T23:08:50Z",
   "last_session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d",
-  "last_session_ts": "2026-03-31T22:53:33Z",
-  "session_count": 308,
+  "last_session_ts": "2026-03-31T23:08:50Z",
+  "session_count": 309,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 657cf61..c3cd364 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 22:24 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 22:53 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -15,7 +15,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - **storage_primary**: PostgreSQL 15+ with per-project schema
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys
+- **db_schema**: Unified: mem_ai_events (with event_type), mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
 - **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
@@ -49,19 +49,19 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events
-- Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
+- Unified event table mem_ai_events consolidates pr_embeddings/pr_memory_events with event_type column for classification
+- Table naming convention: mem_ai_* prefix (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features)
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
+- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-31] I do see the error . it suppose to be mem_ai_tags_relations not mng_ai_tags_relations. can you fix that ?
 - [2026-03-31] I would like to make sure relation is managed properly.  relation can be managed entries by developers.   Manual relatio
 - [2026-03-31] I would like to make sure that the final layer include Work Items, Feature Snapshots and Project Facts is well managed  
 - [2026-03-31] This task is related to current memory update (layer 1)  Create all memory files - I would like to make sure that all fi
-- [2026-03-31] perfect. I would like to have an updated aicli_memory with all updated memory strucuture. Also please advise

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 466e97a..29a5628 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -531,3 +531,5 @@
 {"ts": "2026-03-31T22:18:49Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "46ec6642", "message": "chore: update ai context files and memory after cli session 17cd46bd", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "75a18a27", "message": "chore: update ai context files and session history", "files_count": 33, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T22:24:55Z"}
 {"ts": "2026-03-31T22:24:48Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "75a18a27", "message": "chore: update ai context files and session history", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "ee845bc6", "message": "chore: update ai system files and memory after claude session", "files_count": 43, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T22:53:40Z"}
+{"ts": "2026-03-31T22:53:33Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "ee845bc6", "message": "chore: update ai system files and memory after claude session", "pushed": true, "push_error": ""}


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index d94fc38..fe06c66 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-03-31 22:24 UTC by aicli /memory_
+_Generated: 2026-03-31 22:53 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python FastAPI backend with PostgreSQL (pgvector for semantic search) and an Electron+Vanilla JS frontend. It provides per-project unified event tracking (mem_ai_events), intelligent tagging (mem_ai_tags_relations), and Claude Haiku-powered memory synthesis that auto-generates context files. Currently focused on completing unified table consolidation, validating tagging relationships with feature classification, and resolving data persistence issues during session switches.
+aicli is a shared AI memory platform combining a Python 3.12 CLI, FastAPI backend, and Electron desktop UI with PostgreSQL semantic search (pgvector). It manages multi-project development context through unified event tables (mem_ai_events with event_type classification), memory synthesis via Claude Haiku, and workflow automation via async DAG executors. Currently consolidating pr_session_summaries into mem_ai_events and automating memory file generation from project facts and work items.
 
 ## Project Facts
 
@@ -55,7 +55,7 @@ Reviewer: ```json
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - **storage_primary**: PostgreSQL 15+ with per-project schema
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys
+- **db_schema**: Unified: mem_ai_events (with event_type), mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
 - **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
@@ -89,22 +89,22 @@ Reviewer: ```json
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events
-- Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
+- Unified event table mem_ai_events consolidates pr_embeddings/pr_memory_events with event_type column for classification
+- Table naming convention: mem_ai_* prefix (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features)
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Manual rel

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index d36bcd5..68ce63e 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -33,13 +33,13 @@ You are a senior Python software architect with deep expertise in:
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events
-- Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
+- Unified event table mem_ai_events consolidates pr_embeddings/pr_memory_events with event_type column for classification
+- Table naming convention: mem_ai_* prefix (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features)
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
+- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
 
 ---


## AI Synthesis

**[2026-03-31]** `schema-fix` — Corrected mem_ai_tags_relations table reference in DDL (was incorrectly named mng_ai_tags_relations); verified migrations and database consistency. **[2026-03-31]** `memory-architecture` — Clarified tag storage model: tags reside in mem_ai_tags_relations linked via row id, not as summary_tags arrays; tags sourced from MRR when applicable. **[2026-03-31]** `column-cleanup` — Validated language and file_path columns in mem_ai_events for necessity; removing unnecessary metadata to streamline schema. **[2026-03-31]** `persistence-issue` — Investigated tags disappearing on session switch; root cause identified in DDL, now testing persistence with updated schema. **[2026-03-31]** `memory-generation` — Implemented auto-regeneration of CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts, mem_ai_work_items, and session data. **[2026-03-31]** `startup-race-condition` — Identified AiCli project appearing in Recent list but remaining unselectable; due to dev environment initialization delay; retry logic on empty project list now handling this scenario.