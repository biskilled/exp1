# Project Memory — aicli
_Generated: 2026-03-31 22:53 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python 3.12 CLI, FastAPI backend, and Electron desktop UI with PostgreSQL semantic search (pgvector). It manages multi-project development context through unified event tables (mem_ai_events with event_type classification), memory synthesis via Claude Haiku, and workflow automation via async DAG executors. Currently consolidating pr_session_summaries into mem_ai_events and automating memory file generation from project facts and work items.

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
- **db_schema**: Unified: mem_ai_events (with event_type), mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
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

- Session summaries consolidation: merge pr_session_summaries into mem_ai_events with event_type=session_summary column for unified AI event storage
- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from mem_ai_project_facts, mem_ai_work_items, sessions
- Table consolidation completion: verify mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features schema and data migration
- Tagging functionality validation: confirm mem_ai_tags_relations table implementation and ensure all tagging prompts align with feature classification
- Data persistence validation: investigate tags disappearing on session switch (UI rendering vs. database save failure root cause)
- Backend startup race condition: resolve AiCli appearing in Recent projects but remaining unselectable due to dev environment initialization delay

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index f43b4ed..c985ea3 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -43,14 +43,14 @@
     "All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none",
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval",
     "Memory synthesis: Claude Haiku dual-layer (raw JSONL \u2192 interaction_tags \u2192 5 output files); reduces token overhead",
-    "Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) replacing pr_embeddings/pr_memory_events",
+    "Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidating pr_embeddings/pr_memory_events",
     "Table naming convention: mem_ai_* prefix for consolidated memory tables; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features",
     "Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy",
     "_ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load",
     "Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB",
-    "MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval",
     "Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements",
-    "Memory management pattern: load_once_on_access, update_on_save; memory_items and project_facts table population pending clarification"
+    "MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval",
+    "Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer"
   ],
   "implemented_features": [
     "5-layer memory architecture with /memory endpoint + LLM synthesis via Haiku",
@@ -79,12 +79,12 @@
     "config.py reads ~/.aicli/config.json for WORKSPACE_DIR at startup"
   ],
   "in_progress": [
-    "Table consolidation & renaming: pr_project_facts \u2192 mem_ai_project_facts, pr_work_items \u2192 mem_ai_work_items; add mem_ai_features table for final memory layer (Work Items, Feature Snapshots, Project Facts)",
+    "Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md + system prompts for all LLM providers auto-regenerated from project_facts, work_items, sessions (Layer 1 priority)",
+    "Manual relation management design: Developer-declared relations via CLI/admin UI/SQL with types (depends_on, relates_to, blocks, implements) vs. automatic detection",
+    "Table consolidation: pr_embeddings + pr_memory_events \u2192 mem_ai_events; pr_project_facts \u2192 mem_ai_project_facts; pr_work_items \u2192 mem_ai_work_items; add mem_ai_features",
     "Tagging functionality validation: Verify mem_ai_tags_relations table implementation (naming corrected from mng_ai_tags_relations) and all tagging prompts per spec",
     "Data persistence validation: Tags disappearing on session switch; investigate root cause (UI rendering vs. database save failure)",
-    "Memory table population logic: Clarify intended update behavior for memory_items and project_facts; currently not populating per spec",
-    "Backend startup race condition: AiCli appears in Recent projects but remains unavailable as selectable project; dev environment delay documented",
-    "Work Items, Feature Snapshots, and Project Facts trigger & timing design needed for final memory layer completion"
+    "Backend startup race condition: AiCli appears in Recent projects but remains unavailable as selectable project; dev environment delay documen

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index bcfb057..b97b2f9 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-03-31T22:18:49Z",
+  "last_updated": "2026-03-31T22:24:48Z",
   "last_session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d",
-  "last_session_ts": "2026-03-31T22:18:49Z",
-  "session_count": 306,
+  "last_session_ts": "2026-03-31T22:24:48Z",
+  "session_count": 307,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 45d00b2..77df8b0 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 21:42 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-31 22:18 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -49,19 +49,19 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) replacing pr_embeddings/pr_memory_events
+- Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidating pr_embeddings/pr_memory_events
 - Table naming convention: mem_ai_* prefix for consolidated memory tables; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
-- Memory management pattern: load_once_on_access, update_on_save; memory_items and project_facts table population pending clarification
+- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
+- Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-31] Yes please fix that. about pr_embedding. in the prevous prompts I have mention the following: pr_embeddings,pr_memory_ev
 - [2026-03-31] I am not sure all tagging functionality is implemented as I do not see the mng_ai_tags_relations for example. can you pl
 - [2026-03-31] I do see the error . it suppose to be mem_ai_tags_relations not mng_ai_tags_relations. can you fix that ?
 - [2026-03-31] I would like to make sure relation is managed properly.  relation can be managed entries by developers.   Manual relatio
-- [2026-03-31] I would like to make sure that the final layer include Work Items, Feature Snapshots and Project Facts is well managed  
\ No newline at end of file
+- [2026-03-31] I would like to make sure that the final layer include Work Items, Feature Snapshots and Project Facts is well managed  
+- [2026-03-31] This task is related to current memory update (layer 1)  Create all memory files - I would like to make sure that all fi
\ No newline at end of file


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 8173600..d23b012 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -527,3 +527,5 @@
 {"ts": "2026-03-31T20:48:14Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "dd2dc520", "message": "chore: update 38 files", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "98d3af91", "message": "chore: update ai system files and memory after claude session 17cd46bd", "files_count": 46, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T21:42:16Z"}
 {"ts": "2026-03-31T21:42:08Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "98d3af91", "message": "chore: update ai system files and memory after claude session 17cd46bd", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "46ec6642", "message": "chore: update ai context files and memory after cli session 17cd46bd", "files_count": 44, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-31T22:18:56Z"}
+{"ts": "2026-03-31T22:18:49Z", "action": "commit_push", "source": "claude_cli", "session_id": "17cd46bd-a73d-4611-8a20-7e584e13e61d", "hash": "46ec6642", "message": "chore: update ai context files and memory after cli session 17cd46bd", "pushed": true, "push_error": ""}


### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index d5e7e26..c7dc7bd 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-03-31 21:42 UTC by aicli /memory_
+_Generated: 2026-03-31 22:18 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform built on FastAPI backend + PostgreSQL with pgvector, Electron frontend with Vanilla JS (xterm.js, Monaco, Cytoscape.js), and async DAG workflow engine. Currently stabilizing memory table consolidation (mem_ai_* prefix convention), fixing tagging functionality validation, and designing final memory layer for Work Items, Feature Snapshots, and Project Facts management. Development is in Phase 2 with core authentication, LLM provider adapters, and MCP integration operational; pending clarification on memory table population triggers and data persistence edge cases.
+aicli is a shared AI memory platform enabling Claude CLI and LLM tools to maintain persistent project context across sessions via a dual-layer memory architecture (raw events + synthesized facts). Built with Python 3.12 FastAPI backend + PostgreSQL 15+ with pgvector, Electron UI (Vanilla JS + xterm.js + Monaco editor), and async DAG workflows; currently in Layer 1 completion phase automating memory file regeneration from consolidated event and work-item tables.
 
 ## Project Facts
 
@@ -89,23 +89,23 @@ Reviewer: ```json
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) replacing pr_embeddings/pr_memory_events
+- Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidating pr_embeddings/pr_memory_events
 - Table naming convention: mem_ai_* prefix for consolidated memory tables; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
-- Memory management pattern: load_once_on_access, update_on_save; memory_items and project_facts table population pending clarification
+- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
+- Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
 
 ## In Progress
 
-- Table consolidation & renaming: pr_project_facts → mem_ai_project_facts, pr_work_items → mem_ai_work_items; add mem_ai_features table for final memory layer (Work Items, Feature Snapshots, Project Facts)
+- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md + system prompts for all LLM providers auto-regenerated from project_facts, work_items, sessions (Layer 1 priority)
+- Manual relation management design: Developer-declared relations via CLI/admin UI/SQL with types (depends_on, relates_to, blocks, implements) vs. automatic detection
+- Table consolid

### `commit` — 2026-03-31

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index a1f1ce0..d009ed5 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -33,14 +33,14 @@ You are a senior Python software architect with deep expertise in:
 - All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with approval
 - Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
-- Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) replacing pr_embeddings/pr_memory_events
+- Per-project unified event table: mem_ai_events (id, project_id, session_id, session_desc, event_summary) consolidating pr_embeddings/pr_memory_events
 - Table naming convention: mem_ai_* prefix for consolidated memory tables; mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
 - Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
-- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
 - Manual relations managed via CLI/admin UI; types: depends_on, relates_to, blocks, implements
-- Memory management pattern: load_once_on_access, update_on_save; memory_items and project_facts table population pending clarification
+- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
+- Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
 
 ---
 


## AI Synthesis

**[2026-03-31]** `claude_cli` — Proposed consolidating pr_session_summaries into mem_ai_events with event_type column to unify all AI events (session_summary, embeddings, memory_events) in single table for cleaner querying and synthesis. **[2026-03-31]** `claude_cli` — Confirmed mem_ai_tags_relations table naming convention (fixed typo from mng_ai_tags_relations) and aligned on feature classification schema for tagging system. **[2026-03-31]** `claude_cli` — Priority focus on memory file generation automation: auto-regenerate CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts, mem_ai_work_items tables and session data (Layer 1 priority). **[2026-03-31]** `claude_cli` — Clarified manual relation management: developers declare relations (depends_on, relates_to, blocks, implements) via CLI/admin UI/SQL, not automatic detection. **[2026-03-30]** `prior` — Identified data persistence bug: tags disappear on session/project switch; requires root cause analysis of UI state vs. database commit failure. **[2026-03-30]** `prior` — Backend startup race condition: AiCli project selectable after navigation delay; dev environment initialization timing needs resolution.