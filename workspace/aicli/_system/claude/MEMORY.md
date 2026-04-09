# Project Memory — aicli
_Generated: 2026-04-09 00:56 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python 3.12 CLI backend (FastAPI + PostgreSQL with pgvector embeddings) and an Electron desktop UI (Vanilla JS + Cytoscape visualization). The system captures development events, commits, and interactions across projects, synthesizes them via Claude Haiku into structured work items and project facts, and provides semantic search via MCP tools and workflow automation via YAML-configured DAG pipelines. Currently focused on refining the work items UI (date formatting, column layout, tag scoping) and optimizing database query performance through FK indexing.

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
- **schema_management**: db_schema.sql (single source of truth) + db_migrations.py (m001-m019 framework)

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with UNION consolidation
- Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; mem_mrr_commits.event_id points to mem_ai_events
- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
- Prompt centralization via core.prompt_loader; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
- Work item UI: multi-column sortable table with proper header styling, wider columns (56px–80px), date formatting (YY/MM/DD-HH:MM), and status color badges

## In Progress

- Work item date formatting: changed from YYMMDDHHSS to YY/MM/DD-HH:MM format for better readability in table display
- Work item table column width refinement: increased from 38px to 56px for prompt/commit counts, 80px for date column to accommodate new format
- Tag filtering in work items UI: investigating why non-work-item tags (Shared-memory, billing, etc.) appear in work items panel and implementing proper scope filtering
- Work item deletion implementation: completed wiring of DELETE /work-items/{id} endpoint with confirm dialog, cache clearing, and panel re-rendering
- Header styling standardization: applied uppercase text-transform, letter-spacing, active/inactive state indicators with accent colors across all table headers
- Database query performance optimization: schema-wide FK indexing strategy on work_item_id and event_id columns to resolve query latency

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

### `prompt_batch: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

Fixed UI display issues by implementing hard refresh, restarting backend for SQL changes, and improving header clarity with wider columns (38px→wider), better padding, and visual separation.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 4b7d08b..556d186 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -478,12 +478,13 @@ function _renderWiPanel(items, project) {
 
   function hdr(f, label) {
     const active = window._wiPanelSort.field === f;
-    const arrow  = active ? (window._wiPanelSort.dir === 'asc' ? ' ↑' : ' ↓') : '';
+    const arrow  = active ? (window._wiPanelSort.dir === 'asc' ? '↑' : '↓') : '↕';
     return `<th onclick="window._wiPanelResort('${f}')"
-      style="text-align:right;padding:2px 6px;cursor:pointer;user-select:none;white-space:nowrap;
-             font-size:0.6rem;font-weight:${active?'600':'400'};
-             color:${active?'var(--text)':'var(--muted)'};border-bottom:1px solid var(--border)">
-      ${label}${arrow}
+      style="text-align:right;padding:4px 8px;cursor:pointer;user-select:none;white-space:nowrap;
+             font-size:0.62rem;font-weight:600;letter-spacing:.03em;text-transform:uppercase;
+             color:${active?'var(--accent)':'var(--muted)'};background:var(--surface2);
+             border-bottom:2px solid ${active?'var(--accent)':'var(--border)'};border-left:1px solid var(--border)">
+      ${label}&nbsp;<span style="opacity:${active?1:.35};font-size:0.55rem">${arrow}</span>
     </th>`;
   }
 
@@ -527,21 +528,26 @@ function _renderWiPanel(items, project) {
         ${descClip ? `<div style="font-size:0.57rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;
                                   white-space:nowrap;padding-left:18px" title="${_esc(desc)}">${_esc(descClip)}</div>` : ''}
       </td>
-      <td style="padding:3px 6px;text-align:right;white-space:nowrap;font-size:0.6rem;
-                 color:var(--text2);font-variant-numeric:tabular-nums;width:38px">${wi.prompt_count||0}</td>
-      <td style="padding:3px 6px;text-align:right;white-space:nowrap;font-size:0.6rem;
-                 color:var(--text2);font-variant-numeric:tabular-nums;width:38px">${wi.commit_count||0}</td>
-      <td style="padding:3px 6px;text-align:right;white-space:nowrap;font-size:0.57rem;
-                 color:var(--muted);font-variant-numeric:tabular-nums;font-family:monospace;width:72px">${fmtDate(wi.updated_at||wi.created_at)}</td>
+      <td style="padding:3px 8px;text-align:right;white-space:nowrap;font-size:0.65rem;
+                 color:var(--text2);font-variant-numeric:tabular-nums;
+                 border-left:1px solid var(--border);width:56px">${wi.prompt_count||0}</td>
+      <td style="padding:3px 8px;text-align:right;white-space:nowrap;font-size:0.65rem;
+                 color:var(--text2);font-variant-numeric:tabular-nums;
+                 border-left:1px solid var(--border);width:56px">${wi.commit_count||0}</td>
+      <td style="padding:3px 8px;text-align:right;white-space:nowrap;font-size:0.6rem;
+                 color:var(--muted);font-variant-numeric:tabular-nums;font-family:monospace;
+                 border-left:1px solid var(--border);width:80px">${fmtDate(wi.updated_at||wi.created_at)}</td>
     </tr>`;
   }).join('');
 
   list.innerHTML = `
     <table style="width:100%;border-collapse:collapse;table-layout:fixed">
-      <colgroup><col><col style="width:38px"><col style="width:38px"><col style="width:72px"></colgroup>
+      <colgroup><col><col style="width:56px"><col style="width:56px"><col style="width:80px"></colgroup>
       <thead><tr>
-        <th style="text-align:left;padding:2px 6px;font-size:0.6rem;font-weight:400;
-                   color:var(--muted);border-bottom:1px solid var(--border)">Name / Description</th>
+        <th style="text-align:left;padding:4px 8px;font-size:0.62rem;font-weight:600;
+                   letter-spacing:.03em;text-transform:uppercase;
+                   color:var(--muted);background:var(--surface2);
+                   border-bottom:2px solid var(--border);position:sticky;top:0;z-index:1">Name</th>
         ${hdr('prompt_count','Prompts')}
         ${hdr('commit_count','Commits')}
         ${hdr('updated_at','Updated')}


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index b70d3d6..94cd853 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-09 00:35 UTC
+> Generated by aicli 2026-04-09 00:43 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index dc368db..915a767 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 00:35 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 00:43 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -66,8 +66,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-08] In the ui when I press any tag, I do not the property on the left (I do see that for work_items)
 - [2026-04-08] I do not see mem_mrr_commits_code populated on every commit. is that suppose to be like that? also is expensive to popul
 - [2026-04-08] I would like to understand how work_item are populated. work_item suppose to be linked to all events that relaed to spec
 - [2026-04-09] In the UI - work_items shows as a row. I would each row to have name - desc column, prompts column- show total prompts, 
-- [2026-04-09] I do not see any change at the ui.
\ No newline at end of file
+- [2026-04-09] I do not see any change at the ui.
+- [2026-04-09] Where did you add that ? is it in Work item tab (lower screen) in Planner ?
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.ai/rules.md b/.ai/rules.md
index dc368db..915a767 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 00:35 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 00:43 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -66,8 +66,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-08] In the ui when I press any tag, I do not the property on the left (I do see that for work_items)
 - [2026-04-08] I do not see mem_mrr_commits_code populated on every commit. is that suppose to be like that? also is expensive to popul
 - [2026-04-08] I would like to understand how work_item are populated. work_item suppose to be linked to all events that relaed to spec
 - [2026-04-09] In the UI - work_items shows as a row. I would each row to have name - desc column, prompts column- show total prompts, 
-- [2026-04-09] I do not see any change at the ui.
\ No newline at end of file
+- [2026-04-09] I do not see any change at the ui.
+- [2026-04-09] Where did you add that ? is it in Work item tab (lower screen) in Planner ?
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

Removed deprecated _system root documentation that was no longer needed after session 9315de75.

## AI Synthesis

**[2026-04-09]** `claude_cli` — Completed work item deletion feature with `DELETE /work-items/{id}` endpoint, confirm dialog, and UI cache invalidation. Fixed date display format from YYMMDDHHSS to YY/MM/DD-HH:MM for improved readability. **[2026-04-09]** `claude_cli` — Refined work item table UI: increased column widths (38px→56px for counts, 80px for date), improved header styling with uppercase text-transform, letter-spacing, and accent color indicators for active sort fields. **[2026-04-09]** `claude_cli` — Added prompt_count (event_type='prompt_batch') and commit_count (JOIN mem_mrr_commits via mem_ai_events) to unlinked work items query; updated_at timestamp tracking for sort optimization. **[2026-04-09]** `claude_cli` — Identified tag filtering bug: non-work-item tags (Shared-memory, billing, etc.) incorrectly display in work items panel; requires scope-based tag filtering implementation. **[prior]** — Established Claude Haiku dual-layer memory synthesis architecture generating 5 output files with auto-tag suggestions, timestamp tracking, and LLM response summarization. **[prior]** — Implemented async DAG workflow executor with Cytoscape.js visualization, 2-pane approval panel, and per-node retry/continue logic.