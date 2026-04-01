# Project Memory — aicli
_Generated: 2026-03-31 23:43 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform built on Python 3.12 + FastAPI backend and Electron frontend, enabling multi-user collaborative AI workflows with persistent semantic memory via PostgreSQL + pgvector. Currently stabilizing unified database schema (mem_ai_* tables) and tag management architecture to ensure data persistence and support automated memory file generation from project facts, work items, and interaction history.

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
- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events with event_type column
- Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
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
index c985ea3..5dc6699 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -10,7 +10,7 @@
     "ui_components": "xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre",
     "storage_primary": "PostgreSQL 15+ with per-project schema",
     "storage_semantic": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
-    "db_schema": "Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys",
+    "db_schema": "Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys",
     "authentication": "JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free",
     "llm_providers": "Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok",
     "workflow_engine": "Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic",
@@ -43,13 +43,13 @@
     "All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none",
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval",
     "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files); reduces token overhead",
-    "Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidating pr_embeddings/pr_memory_events",
-    "Table naming convention: mem_ai_* prefix for consolidated memory tables; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features",
+    "Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events",
+    "Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features",
     "Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy",
     "_ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load",
     "Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB",
-    "Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements",
     "MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval",
+    "Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements",
     "Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer"
   ],
   "implemented_features": [
@@ -79,12 +79,12 @@
     "config.py reads ~/.aicli/config.json for WORKSPACE_DIR at startup"
   ],
   "in_progress": [
-    "Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md + system prompts for all LLM providers auto-regenerated from project_facts, work_items, sessions (Layer 1 priority)",
-    "Manual relation management design: Developer-declared relations via CLI/admin UI/SQL with types (depends_on, relates_to, blocks, implements) vs. automatic detection",
-    "Table consolidation: pr_embeddings + pr_memory_events \u2192 mem_ai_events; pr_project_facts \u2192 mem_ai_project_facts; pr_work_items \u2192 mem_ai_work_items; add mem_ai_features",
-    "Tagging functionality validation: Verify mem_ai_tags_relations table implementation (naming corrected from mng_ai_tags_rela

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index b97b2f9..ce0cdb2 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-03-31T22:24:48Z",
+  "last_updated": "2026-03-31T22:53:33Z",
   "last_session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d",
-  "last_session_ts": "2026-03-31T22:24:48Z",
-  "session_count": 307,
+  "last_session_ts": "2026-03-31T22:53:33Z",
+  "session_count": 308,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 77df8b0..657cf61 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 22:18 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 22:24 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -15,7 +15,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - **storage_primary**: PostgreSQL 15+ with per-project schema
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys
+- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys
 - **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
 - **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
@@ -49,19 +49,19 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidating pr_embeddings/pr_memory_events
-- Table naming convention: mem_ai_* prefix for consolidated memory tables; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
+- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events
+- Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
+- Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
 - Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-31] I am not sure all tagging functionality is implemented as I do not see the mng_ai_tags_relations for example. can you pl
 - [2026-03-31] I do see the error . it suppose to be mem_ai_tags_relations not mng_ai_tags_relations. can you fix that ?
 - [2026-03-31] I would like to make sure relation is managed properly.  relation can be managed entries by developers.   Manual relatio
 - [2026-03-31] I would like to make sure that the final layer include Work Items, Feature Snapshots and Project Facts is well managed  
-- [2026-03-31] This task is related to current memory update (layer 1)  C

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index d23b012..466e97a 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -529,3 +529,5 @@
 {"ts": "2026-03-31T21:42:08Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "98d3af91", "message": "chore: update ai system files and memory after claude session 17cd46bd", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "46ec6642", "message": "chore: update ai context files and memory after cli session 17cd46bd", "files_count": 44, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T22:18:56Z"}
 {"ts": "2026-03-31T22:18:49Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "46ec6642", "message": "chore: update ai context files and memory after cli session 17cd46bd", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "75a18a27", "message": "chore: update ai context files and session history", "files_count": 33, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T22:24:55Z"}
+{"ts": "2026-03-31T22:24:48Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "75a18a27", "message": "chore: update ai context files and session history", "pushed": true, "push_error": ""}


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index c7dc7bd..d94fc38 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-03-31 22:18 UTC by aicli /memory_
+_Generated: 2026-03-31 22:24 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform enabling Claude CLI and LLM tools to maintain persistent project context across sessions via a dual-layer memory architecture (raw events + synthesized facts). Built with Python 3.12 FastAPI backend + PostgreSQL 15+ with pgvector, Electron UI (Vanilla JS + xterm.js + Monaco editor), and async DAG workflows; currently in Layer 1 completion phase automating memory file regeneration from consolidated event and work-item tables.
+aicli is a shared AI memory platform combining a Python FastAPI backend with PostgreSQL (pgvector for semantic search) and an Electron+Vanilla JS frontend. It provides per-project unified event tracking (mem_ai_events), intelligent tagging (mem_ai_tags_relations), and Claude Haiku-powered memory synthesis that auto-generates context files. Currently focused on completing unified table consolidation, validating tagging relationships with feature classification, and resolving data persistence issues during session switches.
 
 ## Project Facts
 
@@ -55,7 +55,7 @@ Reviewer: ```json
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - **storage_primary**: PostgreSQL 15+ with per-project schema
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys
+- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys
 - **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
 - **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
@@ -89,23 +89,23 @@ Reviewer: ```json
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidating pr_embeddings/pr_memory_events
-- Table naming convention: mem_ai_* prefix for consolidated memory tables; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
+- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events
+- Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, im

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index d009ed5..d36bcd5 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -33,13 +33,13 @@ You are a senior Python software architect with deep expertise in:
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidating pr_embeddings/pr_memory_events
-- Table naming convention: mem_ai_* prefix for consolidated memory tables; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
+- Unified event table mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidates pr_embeddings/pr_memory_events
+- Table naming convention: mem_ai_* prefix; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
+- Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
 - Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
 
 ---


## AI Synthesis

**[2026-03-31]** `claude_cli` — Verified DDL updates applied to database; mem_ai_tables schema now reflects unified memory structure consolidating prior per-project event tables. **[2026-03-31]** `claude_cli` — Corrected table naming: mem_ai_tags_relations (not mng_ai_tags_relations); identified schema bloat with language, file_path, summary_tags columns requiring removal. **[2026-03-31]** `claude_cli` — Established tag architecture: tags stored in mem_ai_tags_relations table (linked by row id), not as array in mem_ai_events; source attribution via MRR reference. **[2026-03-31]** `claude_cli` — Debugged data persistence: confirmed tags were disappearing due to schema mismatch; DDL now corrected and live. **[2026-03-31]** `claude_cli` — Memory synthesis layer integration continues: Work Items, Feature Snapshots, and Project Facts consolidation as Layer 1 priority for automated memory file generation (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md). **[2026-03-31]** `claude_cli` — Backend race condition analysis: AiCli project selectable after brief delay; startup sequencing depends on _ensure_shared_schema retry logic executing before first project list query.