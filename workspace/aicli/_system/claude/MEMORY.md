# Project Memory — aicli
_Generated: 2026-04-08 23:30 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform (v2.2.0) combining a Python 3.12 CLI backend with FastAPI, PostgreSQL pgvector storage, and an Electron desktop UI, designed to capture, synthesize, and manage project knowledge using multi-layer memory (ephemeral → raw capture → LLM digests → work items → user tags). The system executes async DAG workflows, provides semantic search via embeddings, and integrates multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) with MCP tooling for intelligent code and work item management. Currently stabilizing database schema design, centralizing prompt management, and optimizing query performance for production readiness.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **code_extraction_configuration**: min_lines: 5 (per-symbol threshold), min_diff_lines: 5 (commit-level threshold), only_on_commits_with_tags: false
- **commit_processing_flag**: exec_llm boolean column replaces tags->>'llm' NULL check
- **commit_tracking_schema**: mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: PostgreSQL with SQL parameter binding
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude CLI and LLM platforms
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **known_bug_active**: planner_tag_visibility: categories upload but individual tags don't display in UI bindings
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **memory_system_update_status**: updated_with_latest_context_and_session_tags
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
- **performance_issue_active**: route_work_items latency ~60s; investigating _SQL_UNLINKED_WORK_ITEMS indexing and mem_ai_events join optimization
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
- **prompt_loading_pattern**: core.prompt_loader._prompts.content() replaces direct mng_system_roles queries
- **rel:commit_processing:exec_llm_flag**: replaces
- **rel:memory_system:session_tags**: implements
- **rel:prompt_loader:mng_system_roles**: replaces
- **rel:route_memory:prompt_loader**: depends_on
- **rel:route_memory:sql_parameter_binding**: depends_on
- **rel:route_prompts:memory_embedding**: depends_on
- **rel:route_search:memory_embedding**: depends_on
- **rel:route_snapshots:prompt_loader**: depends_on
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
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev
- **prompt_management**: core.prompt_loader module with centralized prompt caching
- **schema_management**: db_schema.sql (single source of truth) + db_migrations.py (safe rename/recreate/copy pattern)

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts → user planner_tags
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with UNION consolidation
- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Prompt centralization via core.prompt_loader; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
- Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m017)
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates

## In Progress

- Planner tag UI binding fix: resolved `catName` ReferenceError in _renderDrawer() (scope issue) and corrected field mismatch v.short_desc → v.desc for proper tag display on left sidebar
- Database schema canonicalization: consolidated all DDL into db_schema.sql with migration framework db_migrations.py (m001-m017 tracked); single source of truth for database design
- Prompt loader integration: refactoring route_snapshots.py and route_memory.py to use core.prompt_loader instead of mng_system_roles queries; eliminates redundant DB lookups
- Commit pipeline prompt discovery: tracing all LLM prompts in memory_embedding.py, agents/tools/, and routers for unified prompt management and cost tracking
- Memory endpoint data flow verification: synchronizing mirror tables (mem_mrr_commits_code) through mem_ai_events and downstream memory tables with consistent module imports
- Database query performance optimization: investigating ~60s latency in route_work_items (_SQL_UNLINKED_WORK_ITEMS join optimization and indexing needed)

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
index 5810212..be58ca5 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Prompt loader integration: refactoring route_snapshots.py and route_memory.py to use core.prompt_loader._prompts.content() instead of direct mng_system_roles queries; eliminates redundant database lookups
-- Commit pipeline prompt discovery: tracing all LLM prompts used in commit processing (code extraction, summarization, embedding) located in memory/memory_embedding.py, agents/tools/, and routers/route_snapshots.py
-- Memory endpoint data flow: verifying synchronization from mirror tables (mem_mrr_commits_code) through mem_ai_events and downstream memory tables; identified import migration from mem_embeddings to memory_embedding module
-- Module restructuring: consolidating embedding/ingestion logic into memory_embedding.py; updating imports across route_snapshots.py, route_search.py, route_prompts.py for consistent module paths
-- Database query performance optimization: route_work_items showing ~60s latency; investigating indexing for _SQL_UNLINKED_WORK_ITEMS and join optimization on mem_ai_events
-- Planner tag visibility debugging: categories upload but individual tags don't display in UI bindings; verifying router mapping and category query logic
+- Planner tag UI binding fix: resolved `catName` ReferenceError in _renderDrawer() (scope issue) and corrected field mismatch v.short_desc → v.desc for proper tag property display on left sidebar
+- Database schema canonicalization: consolidated all DDL into db_schema.sql as single source of truth with migration framework in db_migrations.py (rename → recreate → copy pattern); legacy ALTER TABLE statements now tracked as migrations m001-m017
+- Prompt loader integration: refactoring route_snapshots.py and route_memory.py to use core.prompt_loader instead of direct mng_system_roles queries to eliminate redundant database lookups
+- Commit pipeline prompt discovery: tracing all LLM prompts in memory_embedding.py, agents/tools/, and routers for unified prompt management and cost tracking
+- Memory endpoint data flow verification: synchronizing mirror tables (mem_mrr_commits_code) through mem_ai_events and downstream memory tables with consistent module imports
+- Database query performance: investigating ~60s latency in route_work_items query (_SQL_UNLINKED_WORK_ITEMS join optimization and indexing)


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 416510b..15dde7b 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-08 19:01 UTC
+> Generated by aicli 2026-04-08 22:52 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -44,6 +44,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - deployment_desktop: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
 - deployment_local: bash start_backend.sh + npm run dev
 - prompt_management: core.prompt_loader module with centralized prompt caching
+- schema_management: db_schema.sql (single source of truth) + db_migrations.py (safe rename/recreate/copy pattern)
 
 ## Architectural Decisions
 
@@ -61,4 +62,4 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
-- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; routes now load prompts from configuration
\ No newline at end of file
+- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; routes load prompts from configuration
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index f1be727..cdf8015 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 19:01 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 22:52 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -44,6 +44,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
 - **deployment_local**: bash start_backend.sh + npm run dev
 - **prompt_management**: core.prompt_loader module with centralized prompt caching
+- **schema_management**: db_schema.sql (single source of truth) + db_migrations.py (safe rename/recreate/copy pattern)
 
 ## Key Decisions
 
@@ -61,12 +62,12 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
-- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; routes now load prompts from configuration
+- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; routes load prompts from configuration
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-08] can you explain where are the  prompts that used for update new commit ?
 - [2026-04-08] Can you explain how commit data statitics are connected to work_items ? Is there is a way to know how many rows/promtps 
 - [2026-04-08] three is link from prompts to commits. each five prompts summeries to event, which meand in this action also all related
 - [2026-04-08] There is a problem to load work_items - line 331 in route_work_items -column w.ai_tags does not exist
-- [2026-04-08] I would like to sapparte database.py in order to have methgods and tables schema. can you create  db_schema.sql file tha
\ No newline at end of file
+- [2026-04-08] I would like to sapparte database.py in order to have methgods and tables schema. can you create  db_schema.sql file tha
+- [2026-04-08] In the ui when I press any tag, I do not the property on the left (I do see that for work_items)
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.ai/rules.md b/.ai/rules.md
index f1be727..cdf8015 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 19:01 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 22:52 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -44,6 +44,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
 - **deployment_local**: bash start_backend.sh + npm run dev
 - **prompt_management**: core.prompt_loader module with centralized prompt caching
+- **schema_management**: db_schema.sql (single source of truth) + db_migrations.py (safe rename/recreate/copy pattern)
 
 ## Key Decisions
 
@@ -61,12 +62,12 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
-- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; routes now load prompts from configuration
+- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; routes load prompts from configuration
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-08] can you explain where are the  prompts that used for update new commit ?
 - [2026-04-08] Can you explain how commit data statitics are connected to work_items ? Is there is a way to know how many rows/promtps 
 - [2026-04-08] three is link from prompts to commits. each five prompts summeries to event, which meand in this action also all related
 - [2026-04-08] There is a problem to load work_items - line 331 in route_work_items -column w.ai_tags does not exist
-- [2026-04-08] I would like to sapparte database.py in order to have methgods and tables schema. can you create  db_schema.sql file tha
\ No newline at end of file
+- [2026-04-08] I would like to sapparte database.py in order to have methgods and tables schema. can you create  db_schema.sql file tha
+- [2026-04-08] In the ui when I press any tag, I do not the property on the left (I do see that for work_items)
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

Removed stale auto-generated system context and CLAUDE.md documentation files that were no longer maintained or relevant.

### `prompt_batch: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

Fixed tag property drawer display by correcting variable scope error (catName undefined), field name mismatch (short_desc vs description), and added missing cache fields (requirements, acceptance_criteria, priority) to SQL query.

## AI Synthesis

**[2026-04-08]** `planner_tag_ui` — Fixed `catName` ReferenceError in _renderDrawer() scope and corrected v.short_desc → v.desc field mismatch; planner tags now display properties correctly in left sidebar. **[2026-04-08]** `db_schema` — Consolidated all DDL into single db_schema.sql file as source of truth; created db_migrations.py framework with rename→recreate→copy pattern; tracked legacy ALTER TABLE statements as m001-m017. **[2026-04-08]** `prompt_loader` — Began refactoring route_snapshots.py and route_memory.py to use core.prompt_loader._prompts.content() instead of direct mng_system_roles queries; eliminates redundant database lookups per route. **[2026-04-08]** `commit_prompts` — Traced all LLM prompts used in commit processing (code extraction, summarization, embedding) across memory_embedding.py, agents/tools/, and routers; unified prompt management for cost tracking. **[2026-04-08]** `memory_flow` — Verified synchronization path from mirror tables (mem_mrr_commits_code) through mem_ai_events and downstream memory tables; updated module imports for consistent data flow. **[2026-04-08]** `performance` — Identified ~60s latency in route_work_items; investigating _SQL_UNLINKED_WORK_ITEMS join optimization and database indexing.