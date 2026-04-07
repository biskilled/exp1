# Project Memory — aicli
_Generated: 2026-04-07 22:38 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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
- **rel:memory_system:session_tags**: implements
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
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm
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
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- 4-layer memory architecture: Layer 0 (ephemeral session messages) → Layer 1 (mem_mrr_* raw capture) → Layer 2 (mem_ai_events LLM digests + embeddings) → Layer 3 (mem_ai_work_items, mem_ai_project_facts) → Layer 4 (user-managed planner_tags)
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
- Tag filtering in work item list: ai_category must match tag's category, not work item's own category
- Session-level UI consolidation: Planner tab unified for all tag management with category/status/properties; suggested tags marked distinctly
- Memory synthesis triggered from session data via /memory endpoint → Claude Haiku processes commits/events → outputs to mem_ai_events/project_facts tables

## In Progress

- Commit table schema verification: confirmed diff_summary (TEXT) stays as human-readable git --stat output; diff_details (JSONB) was dropped and cleaned from mcp/server.py and memory_mirroring.py
- Backend data loading optimization: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS) and line 288 (merged_into/start_date alignment) under investigation; Railway migrations functional but slow (~60s per round-trip, 0.9s per query)
- Work item drag-and-drop UI refinement: fixing hover state propagation for target tag highlights; ensuring dropped work items persist in correct parent and disappear from source after page reload
- Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions properly scoped and exported to global scope
- Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state with correct event linkage
- Mirror table architecture investigation: understanding trigger mechanisms for mem_ai_events and mem_ai_project_facts, LLM prompts used in synthesis, and data flow from session commits/events

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

### `commit: 1c7bb929-1715-485c-bcaa-d4dfd21450ad` — 2026-04-07

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index ba689bf..03f710f 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Tags persistence debugging (2026-03-22) — Planner tag loading issue identified: _plannerState.project fallback categories (null IDs) not triggering cache reload; fix implements force-reload logic in _initPlanner with auto-select of first real category
-- Planner UI tag display (2026-03-22) — Categories loading but all tags not visible; implementing cache invalidation and re-render flow to ensure full tag hierarchy loads on session/project switch
-- Backend module restructuring finalization (2026-03-21-22) — Renamed files with prefixes (tool_, pipeline_, pr_, dl_, mem_); extracted SQL queries to module-level constants; completed agents/ reorganization; removed stale core/encryption.py
-- Database initialization race condition resolution (2026-03-22) — Verified PostgreSQL agent roles have real IDs (10+), router endpoints query proper tables; removed stale fallback workarounds from planner initialization
-- UI code optimization and dead code removal (2026-03-22) — XSS fixes in markdown.js; 30s timeout in api.js; JSDoc documentation; setInterval cleanup for memory leaks in graph_workflow.js
-- Memory items and project_facts table population (pending) — Per specification, these tables should be updated to enable improved memory/context mechanism; logic not yet implemented
+- Tags persistence and cache loading (2026-03-22) — Identified _plannerState.project fallback category issue causing null IDs; implemented force-reload logic in _initPlanner with cache validation check and auto-select of first real category
+- Planner UI tag visibility fix (2026-03-22) — Categories loading but tags not displaying; implementing cache invalidation and re-render flow to ensure full tag hierarchy loads on session/project switch; anyValuesFallback check prevents stale cache
+- Backend module restructuring completion (2026-03-21-22) — Renamed files with prefixes (tool_, pipeline_, pr_, dl_, mem_); extracted SQL queries to module-level constants; reorganized agents/ folder; removed stale core/encryption.py
+- Database initialization and PostgreSQL agent roles (2026-03-22) — Verified agent roles have real IDs (10+); confirmed router endpoints query correct tables per project; eliminated fallback workarounds from planner initialization
+- Frontend code optimization (2026-03-22) — XSS fixes in markdown.js; 30s timeout in api.js; JSDoc documentation; setInterval cleanup in graph_workflow.js to prevent memory leaks
+- Memory items and project_facts population (pending) — Tables exist in schema but update logic not implemented; required for improved memory/context mechanism per specification


### `commit: 1c7bb929-1715-485c-bcaa-d4dfd21450ad` — 2026-04-07

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 1940371..96413e9 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-03-22 02:44 UTC
+> Generated by aicli 2026-03-22 02:51 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -16,7 +16,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - storage_primary: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
 - storage_semantic: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
 - db_schema: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)
-- authentication: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free; encrypted API keys
+- authentication: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
 - llm_providers: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
 - workflow_engine: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
 - workflow_ui: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
@@ -25,7 +25,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - mcp: Stdio MCP server with 12+ tools; env var configured (BACKEND_URL, ACTIVE_PROJECT)
 - deployment: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
 - database_schema: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
-- config_management: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings; YAML for pipeline definitions; pyproject.toml for IDE support
+- config_management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
 - db_tables: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - llm_provider_adapters: agents/providers/ with pr_ prefix for pricing and provider implementations
 - pipeline_engine: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
@@ -33,7 +33,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - billing_storage: data/provider_usage/ (provider_costs.json, runtime data); pricing, coupons, user_logs in SQL tables
 - backend_modules: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - dev_environment: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
-- database: PostgreSQL 15+ with agent roles initialized; per-project and shared schema tables
+- database: PostgreSQL 15+ with per-project and shared schema tables; agent roles initialized
 
 ## Architectural Decisions
 
@@ -43,12 +43,12 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys in database
 - All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends none
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization
-- Memory synthesis: Claude Haiku for dual-layer output (raw JSONL → interaction_tags → 5 files); smart chunking per language/section
+- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); smart chunking per language/section
 - Backend modular organization: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
-- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared tables: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
+- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared tables for users/usage/auth
 - Encrypted API key storage in data layer (dl_api_keys.py); server-side key management only; clients never send API credentials
-- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); moved to agents/mcp/
+- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
 - SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
-- PostgreSQL agent roles properly initialized with real IDs; router mapping queries correct tables per project; no fallback workarounds needed
-- File-based configuration (api_keys.json) external to backend; sensitive data in .env; pricing/coupons/promotions managed in SQL tables
-- Thin UI client: settings.json backed by Electron userData; remote server URL support; spawns backend only for local connections
\ No newline at end of file
+- PostgreSQL agent roles properly initialized with real IDs; router mapping queries correct tables per project; no fallback workarounds
+- File-based configuration (api_keys.json) external to backend; sensitive data in .env; pricing/coupons managed in SQL 

### `commit: fa5883c1-6516-4c07-9124-67308c8aa1af` — 2026-04-07

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 856d6e8..7370b6c 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Feature/task/bug status workflow (2026-03-23) — Implement red 'add_info' status when description missing; green 'Active' status when complete; lifecycle tags deprecated; user questioned why features show Active without proper descriptions—clarifying status enforcement logic
-- Deprecated old/ directory usage (2026-03-23) — Confirmed old/ should not be modified; update memory to reflect this is legacy code; focus development on current directory structure
-- Tags loading and cache invalidation (2026-03-22) — Force-reload logic with cache validation; confirmed _plannerShowNewWorkItem calls _renderWorkItemTable() directly (correct path), not _renderTagTableFromCache()
-- Agent role standardization (2026-03-22) — Per-agent system roles, prompts, input/output schemas, and ReAct mode execution to eliminate hallucination; Sr. Architect role testing
+- Feature/task/bug status workflow (2026-03-23) — Implement red 'add_info' status when description missing; green 'active' status when complete; user reports status not visible in UI Planner tab; enforce missing data detection at creation and sync with database
+- Tag visibility and review (2026-03-23) — User requested review of current tags (bug/feature priority); implement tag management UI in Planner tab to surface and edit tags directly; confirm tag hierarchy persists across sessions
+- Project visibility bug (2026-03-18) — AiCli appears in Recent projects but not displaying as current active project in main project view; timing issue during backend initialization; requires further investigation and fix
+- Memory items and project_facts table population (pending) — Tables exist in schema but update logic not implemented; required for improved memory/context mechanism and MCP data retrieval
 - Frontend code optimization (2026-03-22) — XSS fixes in markdown.js; 30s timeout in api.js; JSDoc documentation; setInterval cleanup in graph_workflow.js
-- Memory items and project_facts table population (pending) — Tables exist in schema but update logic not implemented; required for improved memory/context mechanism
+- Database startup race condition (2026-03-18) — Modified retry logic to handle empty project list on first load; confirmed _ensure_shared_schema pattern replaces old ensure_project_schema method


### `commit: fa5883c1-6516-4c07-9124-67308c8aa1af` — 2026-04-07

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index bfacbed..38e3674 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -131,10 +131,11 @@ async function _initPlanner(project) {
     await loadTagCache(project, true);
   }
   _renderCategoryList();
-  // Auto-select first category so right pane is populated on open
+  // Auto-select first pipeline category (feature/bug/task), else first overall
   const cats = getCacheCategories();
-  if (!_plannerState.selectedCat && cats.length > 0 && cats[0].id != null) {
-    await _plannerSelectCat(cats[0].id, cats[0].name);
+  if (!_plannerState.selectedCat && cats.length > 0) {
+    const first = cats.find(c => _isWorkItemCat(c.name) && c.id != null) || cats.find(c => c.id != null);
+    if (first) await _plannerSelectCat(first.id, first.name);
   }
 }
 
@@ -148,7 +149,11 @@ function _renderCategoryList() {
     list.innerHTML = '<div style="color:var(--muted);font-size:0.62rem;padding:8px 10px">No categories yet</div>';
     return;
   }
-  list.innerHTML = cats.map(c => `
+
+  const pipeline = cats.filter(c => _isWorkItemCat(c.name));
+  const tags     = cats.filter(c => !_isWorkItemCat(c.name));
+
+  const catRow = c => `
     <div class="planner-cat-row" data-id="${c.id}"
          onclick="window._plannerSelectCat(${c.id},'${_esc(c.name)}')"
          style="display:flex;align-items:center;gap:6px;padding:5px 8px;border-radius:5px;
@@ -158,7 +163,14 @@ function _renderCategoryList() {
       <span style="color:${c.color};font-size:0.85rem">${c.icon}</span>
       <span style="font-size:0.65rem;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${_esc(c.name)}</span>
       <span style="font-size:0.55rem;color:var(--muted);flex-shrink:0">${c.value_count ?? getCacheValues(c.id).length}</span>
-    </div>`).join('');
+    </div>`;
+
+  const divider = tags.length ? `
+    <div style="font-size:0.5rem;text-transform:uppercase;letter-spacing:.1em;
+                color:var(--muted);padding:8px 8px 3px;margin-top:4px;
+                border-top:1px solid var(--border)">Tags</div>` : '';
+
+  list.innerHTML = pipeline.map(catRow).join('') + divider + tags.map(catRow).join('');
 }
 
 async function _plannerSelectCat(catId, catName) {


### `commit: fa5883c1-6516-4c07-9124-67308c8aa1af` — 2026-04-07

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 0a6da29..79ca795 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-03-23 00:12 UTC
+> Generated by aicli 2026-03-23 00:26 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -51,4 +51,4 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Backend modular organization: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - Encrypted API key storage in data layer (dl_api_keys.py); server-side key management only; clients never send API credentials
-- Feature/task/bug lifecycle: Status 'add_info' (red) when missing description; transitions to 'Active' (green) when fully described; lifecycle tags optional and candidate for deprecation
\ No newline at end of file
+- Feature/task/bug lifecycle: Status 'add_info' (red) when missing description; transitions to 'active' (green) when fully described; lifecycle tags optional and candidate for deprecation
\ No newline at end of file


### `commit: fa5883c1-6516-4c07-9124-67308c8aa1af` — 2026-04-07

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index ae2b838..142286b 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-23 00:12 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-23 00:26 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -51,12 +51,12 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Backend modular organization: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
 - Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
 - Encrypted API key storage in data layer (dl_api_keys.py); server-side key management only; clients never send API credentials
-- Feature/task/bug lifecycle: Status 'add_info' (red) when missing description; transitions to 'Active' (green) when fully described; lifecycle tags optional and candidate for deprecation
+- Feature/task/bug lifecycle: Status 'add_info' (red) when missing description; transitions to 'active' (green) when fully described; lifecycle tags optional and candidate for deprecation
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-22] I would like to make sure each agent works same as you are - not hilusinsating, and have a defined system role and promt
 - [2026-03-22] I would like to start to test the Sr. Architect role. assume the pipeleine start from feature Auth. can you tell me what
 - [2026-03-22] please fix the embedding. also I would like to understand the feutre as the test will be running the full workflow from 
 - [2026-03-22] Yes implememt 2 and 3. About section 1 - I think feutre , tasks, bugs without a description should be in a status red (a
-- [2026-03-23] Why you fix files in old ? this is not suppose to be used. I also dont see any change in the UI - I do see all feature a
\ No newline at end of file
+- [2026-03-23] Why you fix files in old ? this is not suppose to be used. I also dont see any change in the UI - I do see all feature a
+- [2026-03-23] It is still not working . I thought to have new status (before active) - preq where all new features/bugs are in that st
\ No newline at end of file

