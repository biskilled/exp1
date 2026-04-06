# Project Memory — aicli
_Generated: 2026-04-06 14:11 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining Python CLI, FastAPI backend, and Electron desktop UI to synthesize, store, and navigate project development history using semantic search (pgvector) and LLM-driven memory consolidation. The system leverages Claude Haiku dual-layer synthesis, multi-provider LLM support (Claude/OpenAI/DeepSeek/Gemini/Grok), async DAG workflows with visual approval panels, and a unified PostgreSQL schema (mem_ai_* tables) for persistent, queryable memory across development sessions. Current focus is completing memory layer implementation (project_facts population, architecture documentation), exposing LLM model identifiers in the UI, and unifying feature snapshots with work items.

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
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
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
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization + auto-tag suggestions
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local bash/npm
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) with JSONB UNION batch upsert
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
- Commit deduplication by hash with UNION consolidation; commits linked per-prompt with inline display (accent left-border)
- Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
- Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
- PostgreSQL batch upsert with explicit ::jsonb casting for tags field to prevent duplicate row insertion on ON CONFLICT DO UPDATE

## In Progress

- Memory items and project_facts table population: implement missing update logic to enable event-based triggering with differentiated process_item/messages handling
- Memory architecture documentation: comprehensive aicli_memory.md covering all layers, mirroring mechanisms, event triggers, and processing prompts for each synthesis stage
- MEMORY.md schema alignment: tables updated to reflect current schema (mem_ai_* tables); verification that all documentation mirrors implementation
- Copy-to-clipboard functionality: text selection and copying capability in history UI for improved usability and content accessibility
- LLM model identifier visibility: expose model identifier as visible tag/indicator in UI for transparency and tracking across sessions
- Feature snapshot consolidation: unify plannet_tags structure with work_items and memory linkage; verify prompt-response hook integration

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **architecture-decision** `[open]`
- **customer-meeting** `[open]`
- **Test** `[open]`
- **low-level-design** `[open]`
- **high-level-design** `[open]`
- **retrospective** `[open]`

### Feature

- **UI** `[open]`
- **pagination** `[open]`
- **test-picker-feature** `[open]`
- **graph-workflow** `[open]`
- **billing** `[open]`
- **embeddings** `[open]`
- **tagging** `[open]`
- **mcp** `[open]`
- **workflow-runner** `[open]`
- **shared-memory** `[open]`
- **auth** `[open]`
- **dropbox** `[open]`

### Phase

- **prod** `[open]`
- **development** `[open]`
- **discovery** `[open]`

### Task

- **implement-projects-tab** `[open]`
- **memory** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index 741e6fe..b52cded 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -35,11 +35,11 @@ You are a senior Python software architect with deep expertise in:
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
-- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
 - Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
-- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↪ link) showing only that prompt's commits
+- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ⤴ link) showing only that prompt's commits
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
+- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures
 
 ---


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/aicli/copilot.md b/workspace/aicli/_system/aicli/copilot.md
index d9103f2..32145be 100644
--- a/workspace/aicli/_system/aicli/copilot.md
+++ b/workspace/aicli/_system/aicli/copilot.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-06 01:32 UTC
+> Generated by aicli 2026-04-06 01:33 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -55,9 +55,9 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
-- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
 - Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
-- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↪ link) showing only that prompt's commits
+- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ⤴ link) showing only that prompt's commits
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
+- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures
\ No newline at end of file


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/aicli/context.md b/workspace/aicli/_system/aicli/context.md
index 6dfee9b..859c1af 100644
--- a/workspace/aicli/_system/aicli/context.md
+++ b/workspace/aicli/_system/aicli/context.md
@@ -1,8 +1,5 @@
-[Project Facts] auth_pattern=login_as_first_level_hierarchy; backend_startup_race_condition_fix=retry_logic_handles_empty_project_list_on_first_load; data_model_hierarchy=clients_contain_multiple_users; data_persistence_issue=tags_disappear_on_session_switch; db_engine=SQL; db_schema_method_convention=_ensure_shared_schema_replaces_ensure_project_schema
-
 [PROJECT CONTEXT: aicli]
-aicli is a shared AI memory platform combining a Python CLI + FastAPI backend with a desktop Electron UI to manage project context, memory synthesis, and workflow automation. It uses PostgreSQL with pgvector for semantic search, multiple LLM providers (Claude/OpenAI/DeepSeek), and an async DAG workflow engine. Current focus is on completing memory layer implementation (database population for memory_items/project_facts), documenting the full memory architecture, and unifying feature snapshot structures with proper work_item linkage.
+aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to synthesize, store, and navigate project development history using semantic search (pgvector) and LLM-driven memory consolidation. The system uses Claude Haiku dual-layer synthesis, multi-LLM provider support (Claude/OpenAI/DeepSeek/Gemini/Grok), async DAG workflows with visual approval panels, and unified PostgreSQL schema (mem_ai_* tables) to enable persistent, queryable memory across development sessions. Current work focuses on completing memory layer implementation (project_facts population, architecture documentation), exposing LLM model identifiers in the UI, unifying feature snapshots with work items, and verifying endpoint variable scoping stability.
 Stack: cli=Python 3.12 + prompt_toolkit + rich, backend=FastAPI + uvicorn + python-jose + bcrypt + psycopg2, frontend=Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server, ui_components=xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre, storage_primary=PostgreSQL 15+
 In progress: Memory items and project_facts table population: implement missing update logic to enable proper memory functionality as designed, Memory architecture documentation: comprehensive aicli_memory.md covering all layers, mirroring mechanism, event triggers, and specific prompts at each step, LLM model identifier visibility: expose model identifier as visible tag in UI interface for transparency and tracking across sessions
-Decisions: Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files; Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features); JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
-Last work (2026-04-06): I would like to add mng_projects table that will be used for project data. currenlty there all table use project (text) as a project id. I would like 
\ No newline at end of file
+Decisions: Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files; Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features); JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
\ No newline at end of file


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/CONTEXT.md b/workspace/aicli/_system/CONTEXT.md
index 8f24f65..628609a 100644
--- a/workspace/aicli/_system/CONTEXT.md
+++ b/workspace/aicli/_system/CONTEXT.md
@@ -1,14 +1,14 @@
 # Project Context: aicli
 
-> Auto-generated 2026-04-06 01:33 UTC — do not edit manually.
+> Auto-generated 2026-04-06 01:34 UTC — do not edit manually.
 
 ## Quick Stats
 
 - **Provider**: claude
 - **GitHub**: https://github.com/biskilled/exp1.git
 - **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
-- **Sessions**: 367
-- **Last active**: 2026-04-06T01:33:14Z
+- **Sessions**: 368
+- **Last active**: 2026-04-06T01:33:58Z
 - **Last provider**: claude
 - **Version**: 2.1.0
 
@@ -69,11 +69,11 @@
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
-- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
 - Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
-- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↪ link) showing only that prompt's commits
+- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ⤴ link) showing only that prompt's commits
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
+- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures
 
 ---


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/CLAUDE.md b/workspace/aicli/_system/CLAUDE.md
index 741e6fe..b52cded 100644
--- a/workspace/aicli/_system/CLAUDE.md
+++ b/workspace/aicli/_system/CLAUDE.md
@@ -35,11 +35,11 @@ You are a senior Python software architect with deep expertise in:
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
-- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
 - Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
-- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↪ link) showing only that prompt's commits
+- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ⤴ link) showing only that prompt's commits
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
+- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures
 
 ---


### `commit` — 2026-04-06

diff --git a/MEMORY.md b/MEMORY.md
index f9004b3..51ae20a 100644
--- a/MEMORY.md
+++ b/MEMORY.md
@@ -1,51 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-06 01:32 UTC by aicli /memory_
+_Generated: 2026-04-06 01:33 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python CLI + FastAPI backend with a desktop Electron UI to manage project context, memory synthesis, and workflow automation. It uses PostgreSQL with pgvector for semantic search, multiple LLM providers (Claude/OpenAI/DeepSeek), and an async DAG workflow engine. Current focus is on completing memory layer implementation (database population for memory_items/project_facts), documenting the full memory architecture, and unifying feature snapshot structures with proper work_item linkage.
-
-## Project Facts
-
-- **auth_pattern**: login_as_first_level_hierarchy
-- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
-- **data_model_hierarchy**: clients_contain_multiple_users
-- **data_persistence_issue**: tags_disappear_on_session_switch
-- **db_engine**: SQL
-- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
-- **deployment_target**: Claude_CLI_and_LLM_platforms
-- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
-- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
-- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
-- **memory_management_pattern**: load_once_on_access_update_on_save
-- **pending_implementation**: memory_items_and_project_facts_table_population
-- **pending_issues**: project_visibility_bug_active_project_not_displaying
-- **performance_optimization**: redundant_SQL_calls_eliminated
-- **pipeline/auth**: Acceptance criteria:
-# PM Analysis: Email Verification Feature
-
----
-
-## Context Summary
-
-The tagged context reveals this work item is an **incremental enhancement** to an existing authentication system. Sign In and Create Account forms are already live and functional. The prior PM analysis identified email verification as the missing layer—the system currently accepts any email without confirming ownership. The analys
-
-Reviewer: ```json
-{
-  "passed": false,
-  "score": 4,
-  "issues": [
-    "Implementation is incomplete — cuts off mid-file in EmailService.ts without finishing AWS SES client setup, email template loading, or the
-- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
-- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
-- **tagging_system**: nested_hierarchy_beyond_2_levels
-- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
-- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
-- **ui_library**: 3_dot_menu_pattern
-- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
-- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition
+aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to synthesize, store, and navigate project development history using semantic search (pgvector) and LLM-driven memory consolidation. The system uses Claude Haiku dual-layer synthesis, multi-LLM provider support (Claude/OpenAI/DeepSeek/Gemini/Grok), async DAG workflows with visual approval panels, and unified PostgreSQL schema (mem_ai_* tables) to enable persistent, queryable memory across development sessions. Current work focuses on completing memory layer implementation (project_facts population, architecture documentation), exposing LLM model identifiers in the UI, unifying feature snapshots with work items, and verifying endpoint variable scoping stability.
 
 ## Tech Stack
 
@@ -95,11 +55,11 @@ Reviewer: ```json
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
-- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
 - Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
-- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↪ link) showing only that prompt's commits
+- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ⤴ link) showing only that prompt's commits
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
+- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures
 
 ## In Progress
@@ -111,174 +71,6 @@ Reviewer: ```json
 - Work item linking: clarify and implement complete linkage between work_item entities and memory/snapshot layers across database and API
 - Memory endpoint variable scoping: verify code_dir variable fix at line 1120 remains stable and document pattern
 
-## Active Features / Bugs / Tasks
-
-### Ai_suggestion
-
-- **test123** `[open]`
-
-### Bu

## AI Synthesis

**2026-04-06** `context.md` — Refined project summary to emphasize Claude Haiku dual-layer synthesis, multi-LLM provider ecosystem, async DAG workflows with approval panels, and unified PostgreSQL mem_ai_* schema for persistent queryable memory. **2026-04-06** `claude.md + copilot.md` — Committed architectural decisions on backend startup race condition fix, memory layer event-based triggering, commit-per-prompt inline display (updated symbol ↪ → ⤴), and feature snapshot consolidation with work_item linkage. **2026-04-06** `in_progress tracking` — Identified three critical blockers: (1) memory_items and project_facts table population missing update logic, (2) comprehensive aicli_memory.md documentation gap covering all synthesis layers and event triggers, (3) LLM model identifier visibility for UI transparency. **Ongoing** `MEMORY.md alignment` — Verified mem_ai_* unified tables (events, tags_relations, project_facts, work_items, features) reflect current schema; commit deduplication via seen dict and batch upsert ::jsonb casting implemented. **Pending** `Memory synthesis activation` — Dual-hook architecture (hook-response + session-summary) established; awaiting project_facts table population to trigger differentiated process_item/messages handling in core memory pathway.