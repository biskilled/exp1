# Project Memory — aicli
_Generated: 2026-04-09 02:15 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python 3.12 backend (FastAPI + PostgreSQL + pgvector embeddings), Electron desktop UI (vanilla JS + xterm.js + Monaco), and CLI tool for capturing and organizing development events into intelligent work items and project facts. Current focus: fixing work item row rendering (tags disappeared, description overflow) and refining AI tag suggestion workflow with category-aware display and user tag aggregation from connected events.

## Project Facts

- **ai_tag_suggestion_feature**: ai_tag_suggestion column added to work_items table with approve/reject button handlers (_wiPanelApproveTag/_wiPanelRejectTag)
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
- **frontend_ui_pattern**: inline event handlers with event.stopPropagation(), CSS opacity/color hover states, escaped string interpolation in onclick
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
- **rel:ai_tag_suggestion:work_items_table**: related_to
- **rel:commit_processing:exec_llm_flag**: replaces
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
- **work_item_deletion_endpoint**: DELETE /work-items/{id} with confirm dialog, cache clearing via window._wiPanelDelete, panel re-rendering
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
- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
- Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
- Work item UI: multi-column sortable table with AI tag suggestions (category:name format) + user tags from connected events; approve/reject buttons for suggestions
- Tag suggestion workflow: clicking approve patches tag_id=ai_tag_id, deletes from unlinked panel cache, refreshes display with success toast; remove button clears ai_tag_id only
- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)

## In Progress

- Work item tag display fix: tags (both AI suggestions and user tags) disappeared from rows; investigating JOIN logic in _SQL_UNLINKED_WORK_ITEMS query and user_tags aggregation from mem_ai_events
- Description column layout issue: desc being cut in middle of row instead of using full row width; updating colgroup to make Name column flexible and removing table-layout:fixed constraint
- Work item row rendering: adjusting Name column colspan to display full-length descriptions and accommodate both ai_tag_suggestion chip and user_tags pill display
- Tag suggestion query refinement: verifying ai_tag_id/ai_tag_name/ai_tag_category/ai_tag_color columns are correctly joined from planner_tags and mng_tags_categories
- User tags aggregation: extracting feature/bug_ref/bug tags from mem_ai_events connected to work items and building jsonb_agg array for display
- Frontend styling consolidation: ensuring consistent button styling (× delete, ✓ approve, × remove) with border-radius, hover states, and color differentiation across work item panel

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

Frontend UI refinements: work item details loading fixed via direct GET endpoint, tag suggestions now display as `category:name` format (bug:auth, feature:dropbox) with new/existing tag color differentiation, user tags added as informational pills, fonts increased 15-20% for Electron readability, date column padding fixed to show full timestamps, × removal button styled bold red for visibility, and suggestion row compacted with inline-flex layout.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 9ddca92..4e1f316 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -539,25 +539,39 @@ function _renderWiPanel(items, project) {
     const sc   = STATUS_C[wi.status_user] || '#888';
     const desc = (wi.ai_desc || '').replace(/\n/g,' ');
     const descClip = desc.length > 70 ? desc.slice(0,70)+'…' : desc;
-    const tagSuggestion = wi.ai_tag_name
-      ? `<div style="display:inline-flex;align-items:center;gap:4px;padding-left:18px;margin-top:2px">
+    // AI tag suggestion chip: "category:name" in category color with ✓ / × buttons
+    const aiTagColor  = wi.ai_tag_color  || 'var(--accent)';
+    const aiTagLabel  = wi.ai_tag_category && wi.ai_tag_name
+      ? `${wi.ai_tag_category}:${wi.ai_tag_name}`
+      : (wi.ai_tag_name || '');
+    const tagSuggestion = aiTagLabel
+      ? `<div style="display:inline-flex;align-items:center;gap:3px;padding-left:22px;margin-top:2px">
            <span style="font-size:0.58rem;color:var(--muted);flex-shrink:0">✦</span>
-           <span style="font-size:0.68rem;color:var(--muted);white-space:nowrap"
-                 title="AI suggested: ${_esc(wi.ai_tag_name)}">${_esc(wi.ai_tag_name)}</span>
+           <span style="font-size:0.68rem;font-weight:500;color:${aiTagColor};white-space:nowrap;
+                        background:${aiTagColor}18;padding:0 5px;border-radius:4px;border:1px solid ${aiTagColor}44"
+                 title="AI suggested tag">${_esc(aiTagLabel)}</span>
            <button title="Approve"
              onclick="event.stopPropagation();window._wiPanelApproveTag('${_esc(wi.id)}','${_esc(project)}')"
-             style="background:none;border:1px solid var(--accent);color:var(--accent);cursor:pointer;
-                    font-size:0.6rem;padding:0 5px;border-radius:4px;line-height:1.6;flex-shrink:0"
-             onmouseenter="this.style.background='var(--accent)';this.style.color='#fff'"
-             onmouseleave="this.style.background='none';this.style.color='var(--accent)'">✓</button>
+             style="background:none;border:1px solid ${aiTagColor};color:${aiTagColor};cursor:pointer;
+                    font-size:0.62rem;padding:0 5px;border-radius:4px;line-height:1.7;flex-shrink:0;font-weight:600"
+             onmouseenter="this.style.background='${aiTagColor}';this.style.color='#fff'"
+             onmouseleave="this.style.background='none';this.style.color='${aiTagColor}'">✓</button>
            <button title="Remove suggestion"
              onclick="event.stopPropagation();window._wiPanelRemoveTag('${_esc(wi.id)}','${_esc(project)}')"
-             style="background:none;border:none;color:#e74c3c;cursor:pointer;font-size:0.85rem;
-                    font-weight:700;padding:0 2px;line-height:1;flex-shrink:0"
+             style="background:none;border:1px solid #e74c3c;color:#e74c3c;cursor:pointer;font-size:0.62rem;
+                    font-weight:700;padding:0 5px;border-radius:4px;line-height:1.7;flex-shrink:0"
              onmouseenter="this.style.opacity='.7'"
              onmouseleave="this.style.opacity='1'">×</button>
          </div>`
       : '';
+    // User tags: names from connected events (informational)
+    const userTagsList = Array.isArray(wi.user_tags) ? wi.user_tags : [];
+    const userTagsHtml = userTagsList.length
+      ? `<div style="display:flex;flex-wrap:wrap;gap:3px;padding-left:22px;margin-top:2px">
+           ${userTagsList.map(t => `<span style="font-size:0.6rem;color:var(--muted);background:var(--surface2);
+               border:1px solid var(--border);padding:0 5px;border-radius:4px;white-space:nowrap">${_esc(t)}</span>`).join('')}
+         </div>`
+      : '';
     return `<tr draggable="true"
         data-wi-id="${_esc(wi.id)}"
         data-wi-name="${_esc(wi.ai_name)}"
@@ -571,8 +585,8 @@ function _renderWiPanel(items, project) {
         <div style="display:flex;align-items:center;gap:4px">
           <button title="Delete this item"
             onclick="event.stopPropagation();window._wiPanelDelete('${_esc(wi.id)}','${_esc(project)}')"
-            style="background:none;border:none;color:#e74c3c;cursor:pointer;font-size:0.9rem;
-                   font-weight:700;padding:0 3px;line-height:1;flex-shrink:0"
+            style="background:none;border:1px solid #e74c3c;color:#e74c3c;cursor:pointer;font-size:0.62rem;
+                   font-weight:700;padding:0 4px;border-radius:4px;line-height:1.7;flex-shrink:0"
             onmouseenter="this.style.opacity='.7'"
             onmouseleave="this.style.opacity='1'">×</button>
           <span style="flex-shrink:0;font-size:0.8rem">${icon}</span>
@@ -585,6 +599,7 @@ function _renderWiPanel(items, project) {
         ${descClip ? `<div style="font-size:0.65rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;
                                   white-space:nowrap;padding-left:22px" title="${_esc(desc)}">${_esc(descClip)}</div>` : ''}
         ${tagSuggestion}
+        ${userTagsHtml}
       </td>
       <td style="padding:4px 10px;text-align:right;white-space:nowrap;font-size:0.72rem;
                  color:var(--text2);font-variant-numeric:tabular-nums;


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index 2dd99e2..857af4a 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -76,15 +76,31 @@ _SQL_UNLINKED_WORK_ITEMS = """
     SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
            w.status_user, w.status_ai, w.requirements, w.summary, w.tags, w.ai_tags,
            w.start_date, w.created_at, w.updated_at, w.seq_num,
+           w.ai_tag_id,
            pt.name AS ai_tag_name,
+           ptc.name  AS ai_tag_category,
+           ptc.color AS ai_tag_color,
            (SELECT COUNT(*) FROM mem_ai_work_items src WHERE src.merged_into = w.id) AS merge_count,
            COALESCE((SELECT COUNT(*) FROM mem_ai_events
                      WHERE work_item_id = w.id AND event_type = 'prompt_batch'), 0) AS prompt_count,
            COALESCE((SELECT COUNT(*) FROM mem_mrr_commits c
                      JOIN mem_ai_events e ON e.id = c.event_id
-                     WHERE e.work_item_id = w.id), 0) AS commit_count
+                     WHERE e.work_item_id = w.id), 0) AS commit_count,
+           (SELECT COALESCE(jsonb_agg(DISTINCT ut.name ORDER BY ut.name), '[]'::jsonb)
+            FROM mem_ai_events ev
+            JOIN planner_tags ut ON ut.project_id = w.project_id
+                 AND ut.name IN (
+                     ev.tags->>'feature',
+                     ev.tags->>'bug_ref',
+                     ev.tags->>'bug'
+                 )
+            WHERE ev.work_item_id = w.id
+              AND (ev.tags->>'feature' IS NOT NULL OR ev.tags->>'bug_ref' IS NOT NULL
+                   OR ev.tags->>'bug' IS NOT NULL)
+           ) AS user_tags
     FROM mem_ai_work_items w
-    LEFT JOIN planner_tags pt ON pt.id = w.ai_tag_id
+    LEFT JOIN planner_tags pt   ON pt.id  = w.ai_tag_id
+    LEFT JOIN mng_tags_categories ptc ON ptc.id = pt.category_id
     WHERE w.project_id=%s AND w.tag_id IS NULL AND w.status_user != 'done'
     ORDER BY w.updated_at DESC
 """
@@ -314,6 +330,10 @@ async def get_unlinked_work_items(project: str | None = Query(None)):
             for r in cur.fetchall():
                 row = dict(zip(cols, r))
                 row["id"] = str(row["id"])
+                if row.get("ai_tag_id"):
+                    row["ai_tag_id"] = str(row["ai_tag_id"])
+                if row.get("user_tags") is None:
+                    row["user_tags"] = []
                 for dt_field in ("created_at", "updated_at", "start_date"):
                     if row.get(dt_field):
                         row[dt_field] = row[dt_field].isoformat()


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

Removed legacy system files and reorganized the _system directory structure for improved maintainability and clarity.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index fe59342..09c9940 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Work item table sticky header: implementing fixed header that persists when user scrolls down in work_items panel
-- Work item UI date formatting: standardized to YY/MM/DD-HH:MM format across all date columns with improved column widths (56px–80px)
-- Tag filtering in work items UI: investigating and implementing proper scope filtering for non-work-item tags (Shared-memory, billing) appearing incorrectly in work items panel
-- AI tag suggestion display: adding ai_tag_suggestion column to work item table rows to surface LLM-generated tag recommendations
-- Memory embedding pipeline refresh: executing /memory endpoint to sync all recent prompts and work items, verifying event-to-work-item linkage accuracy
+- Work item date formatting: standardized from YYMMDDHHSS to YY/MM/DD-HH:MM format for improved table readability
+- Work item table column width refinement: increased widths to 56px–80px to accommodate date format and better visual separation
+- Tag filtering in work items UI: investigating incorrect display of non-work-item tags (Shared-memory, billing, etc.) in work items panel; implementing proper scope filtering
 - Work item deletion implementation: completed DELETE /work-items/{id} endpoint with confirm dialog, cache clearing via window._wiPanelDelete, and panel re-rendering
+- AI tag suggestion display: adding ai_tag_suggestion column to work item table rows to surface LLM-generated tag recommendations
+- Memory embedding pipeline refresh: executing /memory endpoint to sync recent prompts and work items, verifying event-to-work-item linkage accuracy


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index ea21726..e5f6ba9 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -506,6 +506,35 @@ async def extract_work_item_code(item_id: str, project: str | None = Query(None)
     return result
 
 
+@router.post("/rematch-all")
+async def rematch_all_work_items(project: str | None = Query(None), background: BackgroundTasks = None):
+    """Run tag-matching for all unlinked work items (no ai_tag_id set) in the background."""
+    _require_db()
+    p = _project(project)
+    with db.conn() as conn:
+        with conn.cursor() as cur:
+            cur.execute(
+                "SELECT id FROM mem_ai_work_items WHERE project_id=%s AND ai_tag_id IS NULL AND status_user!='done' LIMIT 100",
+                (db.get_project_id(p),),
+            )
+            ids = [str(r[0]) for r in cur.fetchall()]
+    for wi_id in ids:
+        background.add_task(_run_matching, p, wi_id)
+    return {"queued": len(ids), "project": p}
+
+
+@router.post("/{item_id}/match")
+async def match_work_item_tags(item_id: str, project: str | None = Query(None)):
+    """Run tag matching synchronously for a single work item — returns matches for debugging."""
+    _require_db()
+    p = _project(project)
+    from memory.memory_tagging import MemoryTagging
+    try:
+        matches = await MemoryTagging().match_work_item_to_tags(p, item_id)
+        return {"matches": matches, "count": len(matches)}
+    except Exception as e:
+        return {"error": str(e), "matches": []}
+
 
 # ── Lookup by sequential number ───────────────────────────────────────────────
 


## AI Synthesis

**[2026-04-09]** `development` — Debugging work item row tag display: AI tag suggestions and user tags disappeared from work_items panel; investigating _SQL_UNLINKED_WORK_ITEMS query JOINs with planner_tags/mng_tags_categories and user_tags aggregation logic from mem_ai_events feature/bug_ref/bug fields. **[2026-04-09]** `development` — Description text overflow fix: Name column layout broken, causing ai_desc to be cut mid-row instead of full width; removing table-layout:fixed and adjusting colgroup to allow flexible Name column expansion. **[2026-03-14]** `feature_complete` — AI tag suggestion UI refinement: ai_tag_name now displays as `category:name` format (e.g., bug:auth, feature:dropbox) with category color background, white-space:nowrap, and inline-flex layout with ✓/× buttons for approve/remove actions. **[2026-03-14]** `feature_complete` — User tags display layer: extracted feature/bug_ref/bug tags from mem_ai_events connected to each work_item and rendered as informational pills in compact row layout below AI tag suggestion chip. **[2026-03-14]** `ui_refinement` — Font scaling and spacing: increased work item panel font sizes 15-20% for Electron readability, fixed date column padding to show full YY/MM/DD-HH:MM timestamps, styled × delete button bold red with border styling matching ✓ approve button. **[2026-03-14]** `architecture` — Tag suggestion workflow: approve button patches tag_id=ai_tag_id on work_item, deletes item from _wiPanelItems cache, refreshes panel without API reload, shows success toast; remove button only clears ai_tag_id/ai_tag_name (preserves work item).