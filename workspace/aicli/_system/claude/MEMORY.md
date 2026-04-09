# Project Memory — aicli
_Generated: 2026-04-09 02:59 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python/FastAPI backend with PostgreSQL semantic search (pgvector) and an Electron desktop UI, enabling teams to capture, synthesize, and retrieve project context across commits, events, and work items. The system implements AI-driven tag suggestion (category-aware matching with Claude Haiku), async DAG workflow execution with visual approval panels, and MCP tool integration. Current development focuses on stabilizing work item panel rendering (tag display, column layout) and refining the AI suggestion matching pipeline's category prioritization and fallback logic.

## Project Facts

- **ai_tag_color_default**: #4a90e2 replaces var(--accent), applied when wi.ai_tag_color not set
- **ai_tag_label_format**: category:name when both present, falls back to name-only, empty string if neither
- **ai_tag_suggestion_feature**: ai_tag_suggestion column with approve/remove button handlers (_wiPanelApproveTag/_wiPanelRemoveTag), refactored to simplified chip markup without category prefix display in non-category mode
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
- **frontend_sticky_header_pattern**: CSS position:sticky;top:0;z-index:1 on table headers for work_items panel
- **frontend_ui_pattern**: inline event handlers with event.stopPropagation(), CSS opacity/color hover states via onmouseenter/onmouseleave, escaped string interpolation in onclick via _esc()
- **known_bug_active**: planner_tag_visibility: categories upload but individual tags don't display in UI bindings
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **memory_sync_workflow**: /memory endpoint executes embedding pipeline refresh to sync prompts with work_items and detect new tags
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
- **rel:ai_tag_suggestion:user_tags**: replaces
- **rel:ai_tag_suggestion:work_items_table**: related_to
- **rel:commit_processing:exec_llm_flag**: replaces
- **rel:frontend_ui_pattern:ai_tag_suggestion_feature**: implements
- **rel:memory_endpoint:tag_detection**: implements
- **rel:memory_system:session_tags**: implements
- **rel:prompt_loader:mng_system_roles**: replaces
- **rel:route_memory:prompt_loader**: depends_on
- **rel:route_memory:sql_parameter_binding**: depends_on
- **rel:route_prompts:memory_embedding**: depends_on
- **rel:route_search:memory_embedding**: depends_on
- **rel:route_snapshots:prompt_loader**: depends_on
- **rel:route_work_items:sql_parameter_binding**: depends_on
- **rel:sticky_header:work_items_panel**: implements
- **rel:ui_notifications:error_handling**: related_to
- **rel:work_item_deletion:api_endpoint**: depends_on
- **rel:work_item_panel:state_management**: implements
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- **tag_filtering_scope_issue**: non-work-item tags (Shared-memory, billing) incorrectly appearing in work_items panel UI; scope filtering implementation in progress
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
- **ui_library**: 3_dot_menu_pattern
- **ui_toast_notification**: toast() function displays error messages with 'error' severity level
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition
- **user_tags_rendering**: removed from panel display (userTagsHtml variable deleted), stored in wi.user_tags array but no longer shown in UI
- **work_item_deletion_endpoint**: DELETE /work-items/{id} with confirm dialog, cache clearing via window._wiPanelDelete, panel re-rendering
- **work_item_deletion_pattern**: client-side confirmation dialog, async api.workItems.delete(), local state cleanup, re-render panel
- **work_item_description_processing**: newlines replaced with spaces and trimmed (replace(/\n/g,' ').trim()), clipped to 70 chars with ellipsis
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
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories
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
- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories

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
- AI suggestion system: category-aware matching (task/bug/feature prioritized), Level 4 fallback to suggest new when no matches ≥0.70, embedding pipeline with 0.60 confidence threshold
- Work item panel: multi-column sortable table with AI tag suggestions + user tags from connected events; sticky headers with fixed table layout
- Tag display format: 'category:name' when both present, name-only fallback, #4a90e2 default color when ai_tag_color null
- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb) for desktop; bash start_backend.sh + npm run dev for local

## In Progress

- Work item tag display restoration: investigating disappearing tags from work item rows; verifying JOIN logic in _SQL_UNLINKED_WORK_ITEMS query and user_tags aggregation from mem_ai_events
- Work item description column layout: fixing desc column being cut mid-row; updating colgroup widths and removing table-layout:fixed constraint to display full-length descriptions
- AI tag suggestion column rendering: ensuring ai_tag_suggestion chip displays correctly with approve (✓) and remove (×) buttons; refactored to simplified chip markup
- User tags aggregation refinement: extracting feature/bug_ref/bug tags from mem_ai_events connected to work items via jsonb_agg; verifying tag_id matching
- AI suggestion category-aware matching: confirmed matching pipeline now prioritizes task/bug/feature categories, enables Level 4 fallback for new suggestions, includes 0.60 confidence threshold
- Frontend styling consolidation: ensuring consistent button styling (× delete, ✓ approve, × remove) with proper hover states and color differentiation across tag interaction modes

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

Fixed critical matching pipeline bugs: restored json import, removed stray commit, enabled Level 4 fallback when embedding finds no matches ≥0.70, included suggested_new (0.60 confidence) in results, and prevented rematch-all from re-queuing processed items.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

Reorganized internal system memory files in the aicli workspace to align with Claude's structure and conventions.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index bb403ea..a0bdf19 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Work item table sticky header implementation: applied position:sticky;top:0;z-index:1 to all 3 sortable column headers for persistence during vertical scroll
-- AI tag suggestion display in work items: added ai_tag_name rendering on each row with approve (✓) and remove (×) buttons; approve button patches tag_id=ai_tag_id and removes item from unlinked panel
-- Tag suggestion workflow: clicking approve triggers PATCH endpoint, deletes from _wiPanelItems cache, re-renders panel, and updates unlinked count with success toast
-- Remove suggestion button handler: clicking × calls _wiPanelRemoveTag to clear ai_tag_id, nullify ai_tag_name, and refresh panel display without deleting work item
-- Memory embedding pipeline sync: executing /memory endpoint to refresh embeddings for recent prompts and work items, verifying event-to-work-item linkage accuracy post-suggestion
-- Work item scope filtering refinement: investigating display of non-work-item tags (Shared-memory, billing) appearing in work items panel and implementing proper scope-based filtering logic
+- Work item tag display fix: tags (both AI suggestions and user tags) disappeared from rows; investigating JOIN logic in _SQL_UNLINKED_WORK_ITEMS query and user_tags aggregation from mem_ai_events
+- Description column layout issue: desc being cut in middle of row instead of using full row width; updating colgroup to make Name column flexible and removing table-layout:fixed constraint
+- Work item row rendering: adjusting Name column colspan to display full-length descriptions and accommodate both ai_tag_suggestion chip and user_tags pill display
+- Tag suggestion query refinement: verifying ai_tag_id/ai_tag_name/ai_tag_category/ai_tag_color columns are correctly joined from planner_tags and mng_tags_categories
+- User tags aggregation: extracting feature/bug_ref/bug tags from mem_ai_events connected to work items and building jsonb_agg array for display
+- Frontend styling consolidation: ensuring consistent button styling (× delete, ✓ approve, × remove) with border-radius, hover states, and color differentiation across work item panel


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index c57489f..5ce748d 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -534,17 +534,51 @@ function _renderWiPanel(items, project) {
     } catch(e) { toast('Remove failed: ' + e.message, 'error'); }
   };
 
+  const LBL = 'font-size:0.58rem;color:var(--muted);flex-shrink:0;min-width:32px;font-weight:500;letter-spacing:.02em';
+
   const rows = sorted.map(wi => {
     const icon = CAT_ICON[wi.ai_category] || '📋';
     const sc   = STATUS_C[wi.status_user] || '#888';
     const desc = (wi.ai_desc || '').replace(/\n/g,' ').trim();
-    // AI tag suggestion: "category:name" chip with approve/remove
     const aiTagColor = wi.ai_tag_color || '#4a90e2';
     const aiTagLabel = wi.ai_tag_name
       ? (wi.ai_tag_category ? wi.ai_tag_category + ':' + wi.ai_tag_name : wi.ai_tag_name)
       : '';
-    // User tags from connected events
     const userTagsList = Array.isArray(wi.user_tags) ? wi.user_tags : [];
+
+    // AI row: always shown
+    const aiRow = aiTagLabel
+      ? `<div style="display:flex;align-items:center;gap:4px;margin-top:3px">
+           <span style="${LBL}">AI:</span>
+           <span style="font-size:0.65rem;font-weight:500;padding:1px 6px;border-radius:4px;
+                        color:${aiTagColor};border:1px solid ${aiTagColor};background:${aiTagColor}1a;
+                        white-space:nowrap">${_esc(aiTagLabel)}</span>
+           <button onclick="event.stopPropagation();window._wiPanelApproveTag('${_esc(wi.id)}','${_esc(project)}')"
+             title="Approve" style="background:none;border:1px solid ${aiTagColor};color:${aiTagColor};
+                    cursor:pointer;font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">✓</button>
+           <button onclick="event.stopPropagation();window._wiPanelRemoveTag('${_esc(wi.id)}','${_esc(project)}')"
+             title="Dismiss" style="background:none;border:1px solid #e74c3c;color:#e74c3c;cursor:pointer;
+                    font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">×</button>
+         </div>`
+      : `<div style="display:flex;align-items:center;gap:4px;margin-top:3px">
+           <span style="${LBL}">AI:</span>
+           <span style="font-size:0.62rem;color:var(--muted);opacity:.45">—</span>
+         </div>`;
+
+    // User row: always shown
+    const userRow = userTagsList.length
+      ? `<div style="display:flex;align-items:center;flex-wrap:wrap;gap:3px;margin-top:2px">
+           <span style="${LBL}">User:</span>
+           ${userTagsList.map(t =>
+             `<span style="font-size:0.62rem;color:var(--muted);border:1px solid var(--border);
+                           padding:1px 5px;border-radius:4px;white-space:nowrap">${_esc(t)}</span>`
+           ).join('')}
+         </div>`
+      : `<div style="display:flex;align-items:center;gap:4px;margin-top:2px">
+           <span style="${LBL}">User:</span>
+           <span style="font-size:0.62rem;color:var(--muted);opacity:.45">—</span>
+         </div>`;
+
     return `<tr draggable="true"
         data-wi-id="${_esc(wi.id)}"
         data-wi-name="${_esc(wi.ai_name)}"
@@ -554,59 +588,39 @@ function _renderWiPanel(items, project) {
         style="border-bottom:1px solid var(--border);cursor:pointer;transition:background 0.1s"
         onmouseenter="this.style.background='var(--surface2)'"
         onmouseleave="this.style.background=''">
-      <td style="padding:4px 8px;min-width:0;overflow:hidden">
+      <td style="padding:4px 8px 6px;min-width:0;overflow:hidden">
         <div style="display:flex;align-items:center;gap:4px;min-width:0">
           <button title="Delete this item"
             onclick="event.stopPropagation();window._wiPanelDelete('${_esc(wi.id)}','${_esc(project)}')"
-            style="background:none;border:1px solid #e74c3c;color:#e74c3c;cursor:pointer;font-size:0.62rem;
-                   font-weight:700;padding:0 4px;border-radius:4px;line-height:1.7;flex-shrink:0"
-            onmouseenter="this.style.opacity='.7'"
-            onmouseleave="this.style.opacity='1'">×</button>
-          <span style="flex-shrink:0;font-size:0.8rem">${icon}</span>
-          ${wi.seq_num ? `<span style="font-size:0.6rem;color:var(--muted);flex-shrink:0">#${wi.seq_num}</span>` : ''}
+            style="background:none;border:1px solid #e74c3c;color:#e74c3c;cursor:pointer;font-size:0.6rem;
+                   font-weight:700;padding:1px 5px;border-radius:4px;line-height:1.5;flex-shrink:0">×</button>
+          <span style="flex-shrink:0;font-size:0.78rem">${icon}</span>
+          ${wi.seq_num ? `<span style="font-size:0.58rem;color:var(--muted);flex-shrink:0">#${wi.seq_num}</span>` : ''}
           <span style="font-size:0.72rem;color:var(--text);overflow:hidden;text-overflow:ellipsis;
                        white-space:nowrap;flex:1;min-width:0" title="${_esc(wi.ai_name)}">${_esc(wi.ai_name)}</span>
-          <span style="font-size:0.58rem;color:${sc};background:${sc}22;
+          <span style="font-size:0.56rem;color:${sc};background:${sc}1a;
                        padding:0 0.3rem;border-radius:6px;flex-shrink:0;white-space:nowrap">${wi.status_user||'active'}</span>
         </div>
-        ${desc ? `<div style="font-size:0.65rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;
-                              white-space:nowrap;padding-left:22px;margin-top:1px"
-                       title="${_esc(desc)}">${_esc(desc)}</div>` : ''}
-        ${aiTagLabel ? `<div style="display:flex;align-items:center;gap:4px;padding-left:22px;margin-top:3px">
-          <span style="font-size:0.6rem;color:var(--muted)">✦</span>
-          <span style="font-size:0.68rem;font-weight:500;padding:1px 6px;border-radius:4px;
-                       color:${aiTagColor};border:1px solid ${aiTagColor};background:${aiTagColor}22;
-                       white-space:nowr

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 1bd4060..ebe3239 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-09 02:04 UTC
+> Generated by aicli 2026-04-09 02:15 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -45,6 +45,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - deployment_local: bash start_backend.sh + npm run dev
 - prompt_management: core.prompt_loader module with centralized prompt caching
 - schema_management: db_schema.sql (single source of truth) + db_migrations.py (m001-m019 framework)
+- database_tables: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories
 
 ## Architectural Decisions
 
@@ -59,7 +60,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with UNION consolidation
 - Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; mem_mrr_commits.event_id points to mem_ai_events
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
-- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
 - Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
-- Prompt centralization via core.prompt_loader; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
-- Work item UI: multi-column sortable table with sticky headers (position:sticky;top:0;z-index:1), YY/MM/DD-HH:MM date formatting, status color badges, AI tag suggestions with approve/reject buttons
\ No newline at end of file
+- Work item UI: multi-column sortable table with AI tag suggestions (category:name format) + user tags from connected events; approve/reject buttons for suggestions
+- Tag suggestion workflow: clicking approve patches tag_id=ai_tag_id, deletes from unlinked panel cache, refreshes display with success toast; remove button clears ai_tag_id only
+- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 18a1f69..4f03061 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 02:04 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 02:15 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -45,6 +45,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **deployment_local**: bash start_backend.sh + npm run dev
 - **prompt_management**: core.prompt_loader module with centralized prompt caching
 - **schema_management**: db_schema.sql (single source of truth) + db_migrations.py (m001-m019 framework)
+- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories
 
 ## Key Decisions
 
@@ -59,15 +60,15 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with UNION consolidation
 - Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; mem_mrr_commits.event_id points to mem_ai_events
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
-- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
 - Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
-- Prompt centralization via core.prompt_loader; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
-- Work item UI: multi-column sortable table with sticky headers (position:sticky;top:0;z-index:1), YY/MM/DD-HH:MM date formatting, status color badges, AI tag suggestions with approve/reject buttons
+- Work item UI: multi-column sortable table with AI tag suggestions (category:name format) + user tags from connected events; approve/reject buttons for suggestions
+- Tag suggestion workflow: clicking approve patches tag_id=ai_tag_id, deletes from unlinked panel cache, refreshes display with success toast; remove button clears ai_tag_id only
+- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] What did you do now ?
 - [2026-04-09] I would like that the header wont disappear when user scroll down in work_items. also can you /momry in order to update 
 - [2026-04-09] I cannot see the sujjestion. is it on each row in work_items ?
 - [2026-04-09] Work_item not loading the details when I click on work item. also in the ui - I do see tag (left of the row) and approve
-- [2026-04-09] I do see there is one ai_tags which is good. but ai_tags suppose to be feature, bug or task with the name . for example 
\ No newline at end of file
+- [2026-04-09] I do see there is one ai_tags which is good. but ai_tags suppose to be feature, bug or task with the name . for example 
+- [2026-04-09] I dont see any tags at the rows now (not ai and not users). also I do that desc is cut the the middle of the row instead
\ No newline at end of file


## AI Synthesis

**[2026-04-09]** `claude_cli` — Refactored AI suggestion system to be category-aware: prioritizes task/bug/feature categories, implements Level 4 fallback for new suggestions when no matches ≥0.70, includes 0.60 confidence threshold for suggested_new results. Matching pipeline now processing 103 AI(EXISTS) and 15 AI(NEW) suggestions with proper category ordering.

**[2026-04-08]** `development` — Reorganized internal system memory files in aicli workspace to align with Claude's structure and conventions; consolidating project state and memory file organization.

**[2026-04-07]** `frontend` — Work item panel column layout restoration: applied table-layout:fixed with fixed colgroup widths to prevent Name column expansion; added persistent **AI:** and **User:** section labels for tag type disambiguation; implemented User section fallback showing '—' when no user tags exist.

**[2026-04-06]** `frontend` — Work item tag display refinement: ensuring ai_tag_category:ai_tag_name format displays correctly with #4a90e2 default color when ai_tag_color is null; added approve (✓) and remove (×) button handlers; integrated user_tags aggregation from mem_ai_events linked to work items.

**[2026-04-05]** `backend` — Fixed critical matching pipeline bugs: restored json import, removed stray commit, enabled Level 4 fallback when embedding finds no matches ≥0.70, included suggested_new (0.60 confidence) in results, prevented rematch-all from re-queuing processed items.

**[2026-04-04]** `frontend` — Debugging work item click handlers to ensure details panel opens on row click; separate button handlers for tag approval/removal; refined tag suggestion workflow with PATCH endpoint integration and panel re-render on approve.