# Project Memory — aicli
_Generated: 2026-04-08 13:50 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **code_extraction_configuration**: min_lines: 5, only_on_commits_with_tags: false in project.yaml templates
- **commit_processing_flag**: exec_llm boolean column replaces tags->>'llm' NULL check
- **commit_tracking_schema**: mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: PostgreSQL with SQL parameter binding
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude CLI and LLM platforms
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **memory_system_update_status**: updated_with_latest_context_and_session_tags
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
- **rel:commit_processing:exec_llm_flag**: replaces
- **rel:memory_system:session_tags**: implements
- **rel:route_memory:sql_parameter_binding**: depends_on
- **rel:route_work_items:sql_parameter_binding**: depends_on
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
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
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
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
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session messages → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts → user-managed planner_tags
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; mem_mrr_commits_code includes 19 columns with full_symbol as generated column
- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Mirror table pattern (mem_mrr_*) captures raw events; generated columns require explicit post-creation migration to avoid DDL runner silent failures

## In Progress

- Database schema stabilization: commit_short_hash column added; mem_mrr_commits_code now includes all 19 columns with full_symbol properly applied via post-creation DDL
- DDL runner robustness: investigating silent failures during initial migration caused by table locks and timing issues; generated columns now applied after base table creation
- Commit code extraction configuration: min_lines and only_on_commits_with_tags settings added to project.yaml templates (python_api and blank)
- Database query performance optimization: route_work_items showing ~60s latency; investigating indexing for _SQL_UNLINKED_WORK_ITEMS and join operations
- Memory endpoint data synchronization: tracing data flow from mirror tables through mem_ai_* tables; verifying update triggers and mechanisms
- Planner tag visibility debugging: categories uploaded but individual tags not displaying in category bindings; verifying router mapping and tag query logic

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **high-level-design** `[open]`
- **architecture-decision** `[open]`
- **customer-meeting** `[open]`
- **Test** `[open]`
- **retrospective** `[open]`
- **low-level-design** `[open]`

### Feature

- **pagination**
- **graph-workflow** `[open]`
- **billing** `[open]`
- **embeddings** `[open]`
- **tagging** `[open]`
- **mcp** `[open]`
- **workflow-runner** `[open]`
- **test-picker-feature** `[open]`
- **UI** `[open]`
- **auth** `[open]`
- **dropbox** `[open]`
- **shared-memory** `[open]`

### Phase

- **discovery** `[open]`
- **prod** `[open]`
- **development** `[open]`

### Task

- **memory** `[open]`
- **implement-projects-tab** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 819c972..5b1c442 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Commit table schema clarification: investigating mem_ai_commits columns (diff_summary, diff_details) and their usage in event linkage and embedding workflows
-- Memory flow documentation: tracing data flow from mirror tables through mem_ai_* tables; identifying triggers and update mechanisms for each mirror table
-- Database query performance optimization: route_work_items showing ~60s round-trip latency; investigating indexing strategy for _SQL_UNLINKED_WORK_ITEMS and join operations
+- Database schema stabilization: commit_short_hash column added to database; mem_mrr_commits_code now includes all 19 columns with full_symbol generated column properly applied
+- DDL runner robustness: investigating silent failures during initial migration caused by table locks and timing issues; generated columns now applied after base table creation
+- Commit code extraction configuration: added min_lines and only_on_commits_with_tags settings to project.yaml templates (python_api and blank)
+- Database query performance optimization: route_work_items showing ~60s latency; investigating indexing for _SQL_UNLINKED_WORK_ITEMS and join operations
+- Memory endpoint data synchronization: tracing data flow from mirror tables through mem_ai_* tables; verifying update triggers and mechanisms
 - Planner tag visibility debugging: categories uploaded but individual tags not displaying in category bindings; verifying router mapping and tag query logic
-- Project ID resolution in embed_commits: fixing project parameter to use project_id instead of project string in database queries
-- Memory endpoint data synchronization: running /memory to sync session data into memory_items and ensure mem_ai_* tables reflect latest project state


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index e12d018..5c91374 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-08 00:28 UTC
+> Generated by aicli 2026-04-08 13:30 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -15,7 +15,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - ui_components: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - storage_primary: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
 - storage_semantic: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- db_schema: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
+- db_schema: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - authentication: JWT (python-jose + bcrypt) + DEV_MODE toggle
 - llm_providers: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
 - workflow_engine: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
@@ -59,5 +59,5 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
-- Tag filtering in work item list: ai_category must match tag's category, not work item's own category
-- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
\ No newline at end of file
+- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
+- Mirror table pattern (mem_mrr_*) captures raw events; generated columns (full_symbol) require explicit migration timing to avoid DDL runner silent failures
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index f5b57a0..1a81f2f 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 00:28 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 13:30 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -15,7 +15,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
+- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
 - **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
@@ -59,13 +59,13 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
-- Tag filtering in work item list: ai_category must match tag's category, not work item's own category
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
+- Mirror table pattern (mem_mrr_*) captures raw events; generated columns (full_symbol) require explicit migration timing to avoid DDL runner silent failures
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-07] In addtion to your reccomendation, I would like to check the following -  mem_ai_coomits -  what is diff_details is used
 - [2026-04-07] dont you have any moemry, did you see the previous file you din - aicli_memoy.md under the project root ?
 - [2026-04-07] I still see the columns in commit table - diif_summery and diff_details . is it suppose to be ?
 - [2026-04-07] I would like to understand the commit table - do you have my previous comment? mem_ai_coomits -  diff_details - all I se
-- [2026-04-07] Where simple extraction flow can be something like that:  pr_tags_map   WHERE related_type = 'commit'   AND tag_id = sma
\ No newline at end of file
+- [2026-04-07] Where simple extraction flow can be something like that:  pr_tags_map   WHERE related_type = 'commit'   AND tag_id = sma
+- [2026-04-08] I do not see any update at the database
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.ai/rules.md b/.ai/rules.md
index f5b57a0..1a81f2f 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 00:28 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 13:30 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -15,7 +15,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
 - **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
-- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
+- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
 - **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
@@ -59,13 +59,13 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
-- Tag filtering in work item list: ai_category must match tag's category, not work item's own category
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
+- Mirror table pattern (mem_mrr_*) captures raw events; generated columns (full_symbol) require explicit migration timing to avoid DDL runner silent failures
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-07] In addtion to your reccomendation, I would like to check the following -  mem_ai_coomits -  what is diff_details is used
 - [2026-04-07] dont you have any moemry, did you see the previous file you din - aicli_memoy.md under the project root ?
 - [2026-04-07] I still see the columns in commit table - diif_summery and diff_details . is it suppose to be ?
 - [2026-04-07] I would like to understand the commit table - do you have my previous comment? mem_ai_coomits -  diff_details - all I se
-- [2026-04-07] Where simple extraction flow can be something like that:  pr_tags_map   WHERE related_type = 'commit'   AND tag_id = sma
\ No newline at end of file
+- [2026-04-07] Where simple extraction flow can be something like that:  pr_tags_map   WHERE related_type = 'commit'   AND tag_id = sma
+- [2026-04-08] I do not see any update at the database
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

Removed deprecated top-level `_system CLAUDE.md` and `CONTEXT.md` files as part of cleanup effort to eliminate outdated system configuration files.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

Removed legacy flat context files and reorganized them into feature-scoped directories to improve code organization and maintainability.
