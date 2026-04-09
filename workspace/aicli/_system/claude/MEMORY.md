# Project Memory — aicli
_Generated: 2026-04-09 01:40 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a FastAPI backend, PostgreSQL semantic storage with pgvector, and a desktop Electron UI. It synthesizes development work items from commits and prompts using Claude Haiku, tracks them with intelligent tagging and embeddings, and surfaces AI-suggested tags to users via an interactive work items panel with approve/reject workflows.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **code_extraction_configuration**: min_lines: 5 (per-symbol threshold), min_diff_lines: 5 (commit-level threshold), only_on_commits_with_tags: false
- **commit_processing_flag**: exec_llm boolean column replaces tags->>'llm' NULL check
- **commit_tracking_schema**: mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **date_format_frontend**: YY/MM/DD-HH:MM format in work item panel
- **db_engine**: PostgreSQL with SQL parameter binding
- **db_schema_management**: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **frontend_ui_pattern**: inline event handlers with event.stopPropagation(), CSS opacity/color hover states, escaped string interpolation in onclick
- **known_bug_active**: planner_tag_visibility: categories upload but individual tags don't display in UI bindings
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **memory_system_update_status**: updated_with_latest_context_and_session_tags
- **pending_feature**: tags display under work_items in shared memory context
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
- **prompt_architecture**: core.prompt_loader for centralization; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
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
- **rel:ui_notifications:error_handling**: related_to
- **rel:work_item_deletion:api_endpoint**: depends_on
- **rel:work_item_panel:state_management**: implements
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
- **ui_library**: 3_dot_menu_pattern
- **ui_toast_notification**: toast() function displays error messages with 'error' severity level
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition
- **work_item_deletion_pattern**: client-side confirmation dialog, async api.workItems.delete(), local state cleanup, re-render panel
- **work_item_display_fields**: ai_category icon mapping, status_user color mapping, seq_num sequence number, id identifier
- **work_item_panel_state_management**: _wiPanelItems object stores work items, window._wiPanelDelete and window._wiPanelRefresh are global handlers
- **work_item_ui_column_widths**: 56px–80px for multi-column sortable table headers
- **work_item_ui_pattern**: multi-column sortable table with proper header styling, status color badges

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
- **database**: PostgreSQL 15+ with pgvector extension
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
- Work item UI: multi-column sortable table with sticky headers (position:sticky;top:0;z-index:1), YY/MM/DD-HH:MM date formatting, status color badges, AI tag suggestions with approve/reject buttons

## In Progress

- Work item table sticky header implementation: applied position:sticky;top:0;z-index:1 to all 3 sortable column headers for persistence during vertical scroll
- AI tag suggestion display in work items: added ai_tag_name rendering on each row with approve (✓) and remove (×) buttons; approve button patches tag_id=ai_tag_id and removes item from unlinked panel
- Tag suggestion workflow: clicking approve triggers PATCH endpoint, deletes from _wiPanelItems cache, re-renders panel, and updates unlinked count with success toast
- Remove suggestion button handler: clicking × calls _wiPanelRemoveTag to clear ai_tag_id, nullify ai_tag_name, and refresh panel display without deleting work item
- Memory embedding pipeline sync: executing /memory endpoint to refresh embeddings for recent prompts and work items, verifying event-to-work-item linkage accuracy post-suggestion
- Work item scope filtering refinement: investigating display of non-work-item tags (Shared-memory, billing) appearing in work items panel and implementing proper scope-based filtering logic

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

Fixed sticky header for work_items panel, added AI tag suggestion UI with approve/reject buttons, and ran /memory to sync prompts with work_items and detect new tags.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index a797ef4..fe59342 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Work item date formatting: changed from YYMMDDHHSS to YY/MM/DD-HH:MM format for better readability in table display
-- Work item table column width refinement: increased from 38px to 56px for prompt/commit counts, 80px for date column to accommodate new format
-- Tag filtering in work items UI: investigating why non-work-item tags (Shared-memory, billing, etc.) appear in work items panel and implementing proper scope filtering
-- Work item deletion implementation: completed wiring of DELETE /work-items/{id} endpoint with confirm dialog, cache clearing, and panel re-rendering
-- Header styling standardization: applied uppercase text-transform, letter-spacing, active/inactive state indicators with accent colors across all table headers
-- Database query performance optimization: schema-wide FK indexing strategy on work_item_id and event_id columns to resolve query latency
+- Work item table sticky header: implementing fixed header that persists when user scrolls down in work_items panel
+- Work item UI date formatting: standardized to YY/MM/DD-HH:MM format across all date columns with improved column widths (56px–80px)
+- Tag filtering in work items UI: investigating and implementing proper scope filtering for non-work-item tags (Shared-memory, billing) appearing incorrectly in work items panel
+- AI tag suggestion display: adding ai_tag_suggestion column to work item table rows to surface LLM-generated tag recommendations
+- Memory embedding pipeline refresh: executing /memory endpoint to sync all recent prompts and work items, verifying event-to-work-item linkage accuracy
+- Work item deletion implementation: completed DELETE /work-items/{id} endpoint with confirm dialog, cache clearing via window._wiPanelDelete, and panel re-rendering


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index e68313e..f58ff0f 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -484,7 +484,8 @@ function _renderWiPanel(items, project) {
       style="text-align:right;padding:4px 8px;cursor:pointer;user-select:none;white-space:nowrap;
              font-size:0.62rem;font-weight:600;letter-spacing:.03em;text-transform:uppercase;
              color:${active?'var(--accent)':'var(--muted)'};background:var(--surface2);
-             border-bottom:2px solid ${active?'var(--accent)':'var(--border)'};border-left:1px solid var(--border)">
+             border-bottom:2px solid ${active?'var(--accent)':'var(--border)'};border-left:1px solid var(--border);
+             position:sticky;top:0;z-index:1">
       ${label}&nbsp;<span style="opacity:${active?1:.35};font-size:0.55rem">${arrow}</span>
     </th>`;
   }
@@ -511,14 +512,52 @@ function _renderWiPanel(items, project) {
     } catch(e) { toast('Delete failed: ' + e.message, 'error'); }
   };
 
+  window._wiPanelApproveTag = async (id, proj) => {
+    const wi = _wiPanelItems[id];
+    if (!wi || !wi.ai_tag_id) return;
+    try {
+      await api.workItems.patch(id, proj, { tag_id: wi.ai_tag_id });
+      delete _wiPanelItems[id];  // now linked → remove from unlinked panel
+      const remaining = Object.values(_wiPanelItems);
+      _renderWiPanel(remaining, proj);
+      const cnt = document.getElementById('wi-panel-count');
+      if (cnt) cnt.textContent = remaining.length ? `(${remaining.length} unlinked)` : '(all linked ✓)';
+      toast(`Linked to "${wi.ai_tag_name}"`, 'success');
+    } catch(e) { toast('Approve failed: ' + e.message, 'error'); }
+  };
+
+  window._wiPanelRemoveTag = async (id, proj) => {
+    try {
+      await api.workItems.patch(id, proj, { ai_tag_id: '' });
+      if (_wiPanelItems[id]) { _wiPanelItems[id].ai_tag_id = null; _wiPanelItems[id].ai_tag_name = null; }
+      _renderWiPanel(Object.values(_wiPanelItems), proj);
+    } catch(e) { toast('Remove failed: ' + e.message, 'error'); }
+  };
+
   const rows = sorted.map(wi => {
     const icon = CAT_ICON[wi.ai_category] || '📋';
     const sc   = STATUS_C[wi.status_user] || '#888';
     const desc = (wi.ai_desc || '').replace(/\n/g,' ');
     const descClip = desc.length > 70 ? desc.slice(0,70)+'…' : desc;
-    const linked = wi.tag_id
-      ? `<span style="font-size:0.48rem;color:var(--accent);flex-shrink:0">✓</span>`
-      : (wi.ai_tag_id ? `<span style="font-size:0.48rem;color:var(--muted);flex-shrink:0;opacity:.7">✦</span>` : '');
+    const tagSuggestion = wi.ai_tag_name
+      ? `<div style="display:flex;align-items:center;gap:3px;padding-left:18px;margin-top:1px">
+           <span style="font-size:0.5rem;color:var(--muted);flex-shrink:0">✦</span>
+           <span style="font-size:0.55rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;
+                        flex:1" title="AI suggested: ${_esc(wi.ai_tag_name)}">${_esc(wi.ai_tag_name)}</span>
+           <button title="Approve this suggestion"
+             onclick="event.stopPropagation();window._wiPanelApproveTag('${_esc(wi.id)}','${_esc(project)}')"
+             style="background:none;border:1px solid var(--accent);color:var(--accent);cursor:pointer;
+                    font-size:0.5rem;padding:0 4px;border-radius:4px;line-height:1.5;flex-shrink:0"
+             onmouseenter="this.style.background='var(--accent)';this.style.color='#fff'"
+             onmouseleave="this.style.background='none';this.style.color='var(--accent)'">✓</button>
+           <button title="Remove suggestion"
+             onclick="event.stopPropagation();window._wiPanelRemoveTag('${_esc(wi.id)}','${_esc(project)}')"
+             style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:0.6rem;
+                    padding:0 2px;line-height:1;flex-shrink:0;opacity:.5"
+             onmouseenter="this.style.opacity=1;this.style.color='#e74c3c'"
+             onmouseleave="this.style.opacity='.5';this.style.color='var(--muted)'">×</button>
+         </div>`
+      : '';
     return `<tr draggable="true"
         data-wi-id="${_esc(wi.id)}"
         data-wi-name="${_esc(wi.ai_name)}"
@@ -542,10 +581,10 @@ function _renderWiPanel(items, project) {
                        white-space:nowrap" title="${_esc(wi.ai_name)}">${_esc(wi.ai_name)}</span>
           <span style="font-size:0.48rem;color:${sc};background:${sc}22;
                        padding:0 0.25rem;border-radius:6px;flex-shrink:0;white-space:nowrap">${wi.status_user||'active'}</span>
-          ${linked}
         </div>
         ${descClip ? `<div style="font-size:0.57rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;
                                   white-space:nowrap;padding-left:18px" title="${_esc(desc)}">${_esc(descClip)}</div>` : ''}
+        ${tagSuggestion}
       </td>
       <td style="padding:3px 8px;text-align:right;white-space:nowrap;font-size:0.65rem;
                  color:var(--text2);font-variant-numeric:tabular-nums;


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 2b56fbf..a0d8b7d 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-09 00:56 UTC
+> Generated by aicli 2026-04-09 01:13 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -33,7 +33,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - billing_storage: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
 - backend_modules: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - dev_environment: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
-- database: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
+- database: PostgreSQL 15+ with pgvector
 - node_modules_build: npm 8+ with Electron-builder; Vite dev server
 - database_version: PostgreSQL 15+
 - build_tooling: npm 8+ with Electron-builder; Vite dev server
@@ -62,4 +62,4 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
 - Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
 - Prompt centralization via core.prompt_loader; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
-- Work item UI: multi-column sortable table with proper header styling, wider columns (56px–80px), date formatting (YY/MM/DD-HH:MM), and status color badges
\ No newline at end of file
+- Work item UI: sticky header on scroll, multi-column sortable table with YY/MM/DD-HH:MM date formatting, status color badges, and AI tag suggestions per row
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 1556845..96869a5 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 00:56 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 01:13 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -33,7 +33,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
-- **database**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
+- **database**: PostgreSQL 15+ with pgvector
 - **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with Electron-builder; Vite dev server
@@ -62,12 +62,12 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
 - Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
 - Prompt centralization via core.prompt_loader; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
-- Work item UI: multi-column sortable table with proper header styling, wider columns (56px–80px), date formatting (YY/MM/DD-HH:MM), and status color badges
+- Work item UI: sticky header on scroll, multi-column sortable table with YY/MM/DD-HH:MM date formatting, status color badges, and AI tag suggestions per row
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] In the UI - work_items shows as a row. I would each row to have name - desc column, prompts column- show total prompts, 
-- [2026-04-09] I do not see any change at the ui.
 - [2026-04-09] Where did you add that ? is it in Work item tab (lower screen) in Planner ?
 - [2026-04-09] Now iot works but it is very close to each other (ui commit is on prompts) . can you make the header more clear
-- [2026-04-09] The data is not cleared can you change that to yy/mm/dd-hh:mm ? also I do see tags under work_items (Shared-memory, bill
\ No newline at end of file
+- [2026-04-09] The data is not cleared can you change that to yy/mm/dd-hh:mm ? also I do see tags under work_items (Shared-memory, bill
+- [2026-04-09] What did you do now ?
+- [2026-04-09] I would like that the header wont disappear when user scroll down in work_items. also can you /momry in order to update 
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.ai/rules.md b/.ai/rules.md
index 1556845..96869a5 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 00:56 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 01:13 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -33,7 +33,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
-- **database**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
+- **database**: PostgreSQL 15+ with pgvector
 - **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
 - **database_version**: PostgreSQL 15+
 - **build_tooling**: npm 8+ with Electron-builder; Vite dev server
@@ -62,12 +62,12 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
 - Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
 - Prompt centralization via core.prompt_loader; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
-- Work item UI: multi-column sortable table with proper header styling, wider columns (56px–80px), date formatting (YY/MM/DD-HH:MM), and status color badges
+- Work item UI: sticky header on scroll, multi-column sortable table with YY/MM/DD-HH:MM date formatting, status color badges, and AI tag suggestions per row
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] In the UI - work_items shows as a row. I would each row to have name - desc column, prompts column- show total prompts, 
-- [2026-04-09] I do not see any change at the ui.
 - [2026-04-09] Where did you add that ? is it in Work item tab (lower screen) in Planner ?
 - [2026-04-09] Now iot works but it is very close to each other (ui commit is on prompts) . can you make the header more clear
-- [2026-04-09] The data is not cleared can you change that to yy/mm/dd-hh:mm ? also I do see tags under work_items (Shared-memory, bill
\ No newline at end of file
+- [2026-04-09] The data is not cleared can you change that to yy/mm/dd-hh:mm ? also I do see tags under work_items (Shared-memory, bill
+- [2026-04-09] What did you do now ?
+- [2026-04-09] I would like that the header wont disappear when user scroll down in work_items. also can you /momry in order to update 
\ No newline at end of file


## AI Synthesis

**[2026-04-09]** `user_query` — User confirmed AI tag suggestions should appear on each row in work items panel; clarified UI visibility of suggestion line with approve/reject buttons. **[2026-04-08]** `feature_completion` — Implemented sticky header for work item table with position:sticky;top:0;z-index:1 on all 3 sortable column headers to persist during scroll. **[2026-04-07]** `feature_implementation` — Added AI tag suggestion display logic to work items rows: renders ai_tag_name with approve (✓) and remove (×) buttons; approve button triggers PATCH tag_id=ai_tag_id, deletes from cache, re-renders panel. **[2026-04-06]** `ui_refinement` — Standardized work item date formatting to YY/MM/DD-HH:MM format across all columns with optimized widths (56px–80px) for improved table readability and visual hierarchy. **[2026-04-05]** `endpoint_completion` — Completed DELETE /work-items/{id} endpoint with confirm dialog, cache clearing via window._wiPanelDelete, and panel re-rendering workflow. **[2026-04-04]** `tag_filtering` — Investigating incorrect display of non-work-item tags (Shared-memory, billing) in work items panel; identified need for proper scope-based tag filtering logic in rendering.