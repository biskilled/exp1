# Project Memory — aicli
_Generated: 2026-04-07 22:41 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to enable teams to collaboratively capture, organize, and synthesize project context through semantic memory, work item tracking, and AI-powered workflow automation. Currently in active development (v2.2.0) with focus on performance optimization, tag visibility in the planner UI, agent role-based access control, and pipeline DAG loading—all built on PostgreSQL with pgvector embeddings and multi-LLM provider support (Claude, OpenAI, DeepSeek, Gemini, Grok).

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
- 4-layer memory architecture: ephemeral session messages → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items, mem_ai_project_facts → user-managed planner_tags
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
- Tag filtering in work item list: ai_category must match tag's category, not work item's own category
- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm

## In Progress

- Database query performance optimization: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS) and line 288 (merged_into/start_date alignment) showing ~60s round-trip, 0.9s per query; investigating indexing and join strategy
- Planner tag visibility debugging: categories uploaded but individual tags not displaying in category; checking router mapping and tag query logic in category-to-tag binding
- Agent roles PostgreSQL setup: agent_roles and system_roles tables required for role-based functionality; schema initialization and permission mapping pending
- Pipeline DAG loading failure: workflows not populating in UI; verifying Cytoscape graph initialization and node/edge data binding from backend
- Project ID resolution in embed_commits: fixing project parameter to use project_id instead of project string in database queries (route_memory.py line 391)
- Memory endpoint data synchronization: running /memory to sync session data into memory_items and ensure mem_ai_* tables reflect latest project state with correct event linkage

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

### `commit: dca94c94-c618-4866-89ce-7a3178adc777` — 2026-04-07

diff --git a/workspace/aicli/documents/feature/shared-memory.md b/workspace/aicli/documents/feature/shared-memory.md
index 32a9f27..731106b 100644
--- a/workspace/aicli/documents/feature/shared-memory.md
+++ b/workspace/aicli/documents/feature/shared-memory.md
@@ -2,30 +2,30 @@
 _Last updated: 2026-04-07 · Project: aicli_
 
 ## Use Case Summary
-Implement shared memory functionality to enable safe inter-process/inter-thread communication. Currently in early planning stages with requirements and technical specifications defined but no implementation or commit history yet.
+Implement shared memory functionality to enable safe inter-process/inter-thread communication with proper synchronization and thread-safety guarantees. Currently in early planning stages with requirements and technical specifications defined but no implementation or commits yet.
 
 ## Work Items (1)
 
 ### #None memory · active
 _Prompts: 0 · ~0 words · 0 commits · Started: —_
 
-This work item tracks the implementation of shared memory functionality. Currently in early planning with no committed implementation. Requires detailed specification of memory management, synchronization primitives, and API design before development can begin. Will need comprehensive testing across concurrent access patterns.
+Implements shared memory functionality for inter-process/inter-thread communication. Currently in early planning phase with no implementation or commits. Requires detailed API specification, synchronization mechanism design, and comprehensive testing across concurrent access patterns before development can commence.
 
-**Remaining:** Define detailed requirements for shared memory API
-Design synchronization and safety mechanisms
+**Remaining:** Define detailed shared memory API specifications
+Design and specify synchronization primitives (mutexes, semaphores, etc.)
 Implement core shared memory module
-Write unit and integration tests
-Document API and usage patterns
+Build comprehensive unit and integration test suite
+Document API design patterns and usage examples
 
 
 ---
 
 ## What Was Done
-- Identified core acceptance criteria for shared memory initialization and concurrent access
+- Defined overall requirements and acceptance criteria for shared memory feature
 
 ## What Remains
 - Define detailed functional requirements and API specifications for shared memory interface
-- Design synchronization mechanisms and thread-safety guarantees
+- Design synchronization mechanisms (mutexes, semaphores) and thread-safety guarantees
 - Implement core shared memory module with memory allocation/deallocation
 - Develop unit and integration tests covering concurrent access scenarios
 - Create comprehensive API documentation and usage examples
@@ -43,4 +43,4 @@ Document API and usage patterns
 | — | — | — |
 
 ---
-_Auto-generated by aicli Planner · 2026-04-07 16:43 UTC_
+_Auto-generated by aicli Planner · 2026-04-07 22:20 UTC_


### `commit: dca94c94-c618-4866-89ce-7a3178adc777` — 2026-04-07

diff --git a/.ai/rules.md b/.ai/rules.md
index 0d6ba29..18adae5 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-07 17:12 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-07 22:38 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -64,8 +64,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-07] Can you use aiCli_memeory to describe the followng : how flow works from mirror. each mirrr table - what is the trigeer,
 - [2026-04-07] Can you use aiCli_memeory to describe the followng : how flow works from mirror. each mirrr table - what is the trigeer,
 - [2026-04-07] In addtion to your reccomendation, I would like to check the following -  mem_ai_coomits -  what is diff_details is used
 - [2026-04-07] dont you have any moemry, did you see the previous file you din - aicli_memoy.md under the project root ?
-- [2026-04-07] I still see the columns in commit table - diif_summery and diff_details . is it suppose to be ?
\ No newline at end of file
+- [2026-04-07] I still see the columns in commit table - diif_summery and diff_details . is it suppose to be ?
+- [2026-04-07] I would like to understand the commit table - do you have my previous comment? mem_ai_coomits -  diff_details - all I se
\ No newline at end of file


### `commit` — 2026-04-07

Commit: chore: remove aicli system context and claude memory files
Hash: 413d1a2a
Generated/internal files: workspace/aicli/_system/commit_log.jsonl, workspace/aicli/_system/dev_runtime_state.json

### `commit: fa708653-5003-4882-8b5c-07ef4d0d32e5` — 2026-04-07

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 7ce0d5b..c0f87ac 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -118,12 +118,18 @@ export function renderEntities(container) {
 // ── Init: use cache if warm, otherwise load ──────────────────────────────────
 
 async function _initPlanner(project) {
-  if (!isCacheLoaded() || getCacheProject() !== project) {
+  const hasFallback = getCacheCategories().some(c => c.id === null);
+  if (!isCacheLoaded() || getCacheProject() !== project || hasFallback) {
     document.getElementById('planner-cat-list').innerHTML =
       '<div style="color:var(--muted);font-size:0.62rem;padding:8px 10px">Loading…</div>';
-    await loadTagCache(project);
+    await loadTagCache(project, hasFallback);
   }
   _renderCategoryList();
+  // Auto-select first category so right pane is populated on open
+  const cats = getCacheCategories();
+  if (!_plannerState.selectedCat && cats.length > 0 && cats[0].id != null) {
+    await _plannerSelectCat(cats[0].id, cats[0].name);
+  }
 }
 
 // ── Category list ─────────────────────────────────────────────────────────────
@@ -150,6 +156,16 @@ function _renderCategoryList() {
 }
 
 async function _plannerSelectCat(catId, catName) {
+  // Fallback categories have null IDs — reload cache and resolve real ID by name
+  if (catId === null || catId === undefined) {
+    const pane = document.getElementById('planner-tags-pane');
+    if (pane) pane.innerHTML = '<div style="color:var(--muted);font-size:0.7rem;padding:16px">Loading…</div>';
+    await loadTagCache(_plannerState.project, true);
+    const real = getCacheCategories().find(c => c.name === catName && c.id != null);
+    if (real) return _plannerSelectCat(real.id, real.name);
+    if (pane) pane.innerHTML = '<div style="color:var(--muted);font-size:0.7rem;padding:16px">Database not ready yet — try again shortly</div>';
+    return;
+  }
   _plannerState.selectedCat = catId;
   _plannerState.selectedCatName = catName;
   const cat = getCacheCategories().find(c => c.id === catId) || {};


### `commit: dca94c94-c618-4866-89ce-7a3178adc777` — 2026-04-07

Commit: docs: update system context and memory files after claude session
Hash: 538614e3
Code files (3):
  - .ai/rules.md
  - .cursor/rules/aicli.mdrules
  - .github/copilot-instructions.md
Generated/internal files: CLAUDE.md, MEMORY.md, workspace/aicli/_system/CLAUDE.md, workspace/aicli/_system/CONTEXT.md, workspace/aicli/_system/aicli/context.md

### `commit: dca94c94-c618-4866-89ce-7a3178adc777` — 2026-04-07

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index c033571..965ef1a 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,7 +375,7 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Schema cleanup: removed diff_summary and source_session_id columns from work item commit queries; verified migration 008 dropped these fields and memory_planner.py now uses tags['files'] dict instead of deprecated columns
+- Commit table schema verification: confirmed diff_summary (TEXT) stays as human-readable git --stat output; diff_details (JSONB) was dropped and cleaned from mcp/server.py and memory_mirroring.py
 - Backend data loading optimization: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS) and line 288 (merged_into/start_date alignment) under investigation; Railway migrations functional but slow (~60s per round-trip, 0.9s per query)
 - Work item drag-and-drop UI refinement: fixing hover state propagation for target tag highlights; ensuring dropped work items persist in correct parent and disappear from source after page reload
 - Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions properly scoped and exported to global scope


## AI Synthesis

**[2026-04-07]** `memory system` — Memory synthesis system updated with latest context and session tags; 4-layer architecture consolidates ephemeral messages → raw captures → LLM digests → work items → user planner tags. **[2026-04-07]** `shared-memory feature` — Shared memory functionality scoped for inter-process/inter-thread communication; acceptance criteria defined with focus on synchronization primitives and thread-safety guarantees; currently in planning phase with no implementation commits yet. **[2026-03-14]** `project foundation` — aicli v2.2.0 established with dual storage (PostgreSQL + pgvector), JWT auth with hierarchical Clients→Users pattern, LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok), and Electron desktop UI using Vanilla JS + Cytoscape.js for workflow visualization. **[2026-03-14]** `workflow engine` — Async DAG executor implemented via asyncio.gather with loop-back logic and max_iterations cap; Cytoscape provides graph visualization with 2-pane approval panel for user negotiation in workflows. **[2026-03-14]** `data model` — Unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) with per-project tables (commits, events, embeddings, tags, links, memory_items, facts); tag deduplication and session ordering by created_at to prevent unintended reordering. **[2026-03-14]** `chunking strategy` — Smart chunking per source type: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI. **[2026-03-14]** `mcp integration` — Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint for data synchronization. **[2026-03-14]** `deployment` — Three-tier deployment: Railway for cloud (Dockerfile + railway.toml), Electron-builder for desktop (Mac/Windows/Linux), local bash/npm for development. **[in-progress]** `performance` — Backend startup and query performance under investigation; route_work_items queries averaging 0.9s with ~60s round-trip times; indexing strategy and join optimization pending. **[in-progress]** `tag visibility` — Planner tag display issue where categories upload but individual tags don't cascade; debugging router mapping and tag query logic.