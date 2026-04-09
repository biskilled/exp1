# Project Memory — aicli
_Generated: 2026-04-09 00:48 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining Python FastAPI backend with Electron desktop UI, PostgreSQL+pgvector semantic search, and multi-provider LLM adapters (Claude/OpenAI/DeepSeek/Gemini/Grok). It captures and synthesizes project context through smart code chunking, embeddings, and a 4-layer memory system, enabling AI workflows via async DAG executor and MCP tools. Currently focused on work item UI refinement (sortable table, proper headers), database query optimization, and consistent prompt/embedding pipeline across all routers.

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
- Work item UI: multi-column sortable table with proper header styling, wider columns (38px→60+px), date formatting (YYMMDDHHSS), and status color badges

## In Progress

- Work item table UI refinement: implemented multi-column sortable display with separate sort state (field/direction); added date formatter (fmtDate), header styling with active indicators, improved column widths and visual separation
- Work item counting optimization: added prompt_count (event_type='prompt_batch') and commit_count (JOIN mem_mrr_commits via mem_ai_events) to _SQL_UNLINKED_WORK_ITEMS query; added updated_at timestamp tracking
- Table header clarity: increased column width from 38px, added background/border styling to headers, implemented dynamic active-field indicator arrows (↑/↓), fixed text contrast for muted vs active states
- Database query performance: schema-wide FK indexing strategy on work_item_id and event_id columns to resolve ~60s latency in unlinked work items JOIN
- Memory embedding pipeline: synchronized LLM prompt tracing across memory_embedding.py, agents/tools/, and routers/ with consistent module imports
- Prompt loader integration: refactored route_snapshots.py and route_memory.py to use core.prompt_loader instead of direct mng_system_roles queries

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

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 19c813d..4b7d08b 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -452,53 +452,102 @@ function _renderWiPanel(items, project) {
     list.innerHTML = '<div style="padding:0.5rem 1rem;font-size:0.65rem;color:var(--muted)">No work items yet — click + New to create one</div>';
     return;
   }
-  const CAT_ICON = { feature: '✨', bug: '🐛', task: '📋' };
-  const STATUS_UC = { active: '#27ae60', in_progress: '#e67e22', done: '#4a90e2', paused: '#888' };
-  list.innerHTML = items.map(wi => {
+
+  const CAT_ICON  = { feature: '✨', bug: '🐛', task: '📋' };
+  const STATUS_C  = { active: '#27ae60', in_progress: '#e67e22', done: '#4a90e2', paused: '#888' };
+
+  // Sort state for bottom panel (separate from the category-pane sort)
+  if (!window._wiPanelSort) window._wiPanelSort = { field: 'updated_at', dir: 'desc' };
+  const { field, dir } = window._wiPanelSort;
+  const mul = dir === 'asc' ? 1 : -1;
+  const sorted = [...items].sort((a, b) => {
+    if (field === 'prompt_count')  return mul * ((a.prompt_count||0)  - (b.prompt_count||0));
+    if (field === 'commit_count')  return mul * ((a.commit_count||0)  - (b.commit_count||0));
+    return mul * (new Date(a.updated_at||a.created_at||0) - new Date(b.updated_at||b.created_at||0));
+  });
+
+  function fmtDate(iso) {
+    if (!iso) return '—';
+    const d = new Date(iso);
+    return String(d.getFullYear()).slice(2)
+      + String(d.getMonth()+1).padStart(2,'0')
+      + String(d.getDate()).padStart(2,'0')
+      + String(d.getHours()).padStart(2,'0')
+      + String(d.getMinutes()).padStart(2,'0');
+  }
+
+  function hdr(f, label) {
+    const active = window._wiPanelSort.field === f;
+    const arrow  = active ? (window._wiPanelSort.dir === 'asc' ? ' ↑' : ' ↓') : '';
+    return `<th onclick="window._wiPanelResort('${f}')"
+      style="text-align:right;padding:2px 6px;cursor:pointer;user-select:none;white-space:nowrap;
+             font-size:0.6rem;font-weight:${active?'600':'400'};
+             color:${active?'var(--text)':'var(--muted)'};border-bottom:1px solid var(--border)">
+      ${label}${arrow}
+    </th>`;
+  }
+
+  window._wiPanelResort = (f) => {
+    if (window._wiPanelSort.field === f) {
+      window._wiPanelSort.dir = window._wiPanelSort.dir === 'asc' ? 'desc' : 'asc';
+    } else {
+      window._wiPanelSort.field = f;
+      window._wiPanelSort.dir = 'desc';
+    }
+    _renderWiPanel(Object.values(_wiPanelItems), project);
+  };
+
+  const rows = sorted.map(wi => {
     const icon = CAT_ICON[wi.ai_category] || '📋';
-    const sc = STATUS_UC[wi.status_user] || '#888';
-    const mergeBadge = wi.merge_count > 0
-      ? `<span title="${wi.merge_count} item(s) merged into this"
-               style="font-size:0.5rem;color:var(--accent);background:var(--accent)20;
-                      padding:0.02rem 0.3rem;border-radius:8px;white-space:nowrap;flex-shrink:0
-                      ">⊕ ${wi.merge_count}</span>`
-      : '';
-    const linkedBadge = wi.tag_id
-      ? `<span title="Linked" style="font-size:0.52rem;color:var(--accent);margin-left:2px">✓</span>
-         <button title="Unlink from tag" onclick="event.stopPropagation();window._wiUnlink('${_esc(wi.id)}','${_esc(project)}')"
-           style="background:none;border:none;color:var(--muted);cursor:pointer;font-size:0.7rem;
-                  padding:0 2px;line-height:1;vertical-align:middle">×</button>`
-      : (wi.ai_tag_id
-          ? `<span title="AI-suggested link" style="font-size:0.52rem;color:var(--muted);margin-left:2px;opacity:.7">✦</span>`
-          : '');
-    const detail = (wi.action_items || wi.ai_desc || '').replace(/\n/g, ' ').slice(0, 80);
-    return `<div draggable="true"
-         data-wi-id="${_esc(wi.id)}"
-         data-wi-name="${_esc(wi.ai_name)}"
-         ondragstart="window._wiBotDragStart(event,'${_esc(wi.id)}','${_esc(wi.ai_name)}','${_esc(wi.ai_category)}')"
-         ondragend="window._wiBotDragEnd(event)"
-         onclick="window._plannerOpenWorkItemDrawer('${_esc(wi.id)}','${_esc(wi.ai_category)}','${_esc(project)}')"
-         style="display:grid;grid-template-columns:1fr 1fr;padding:3px 8px;
-                border-bottom:1px solid var(--border);cursor:grab;user-select:none;
-                transition:background 0.1s"
-         onmouseenter="this.style.background='var(--surface2)'"
-         onmouseleave="this.style.background=''">
-      <div style="display:flex;align-items:center;gap:3px;overflow:hidden;min-width:0">
-        <span style="flex-shrink:0;font-size:0.78rem">${icon}</span>
-        <span style="font-size:0.64rem;color:var(--text);overflow:hidden;text-overflow:ellipsis;
-                     white-space:nowrap" title="${_esc(wi.ai_name)}">${_esc(wi.ai_name)}</span>
-        <span style="font-size:0.52rem;color:${sc};background:${sc}22;padding:0.02rem 0.25rem;
-                     border-radius:8px;white-space:nowrap;flex-shrink:0">${wi.status_user || 'active'}</span>
-        ${mergeBadge}
-        ${linkedBadge}
-      </div>
-      <div style="font-size:0.6rem;color:var(--muted);overflow:hidden;text-overflow:ellipsis;
-                  white-space:nowrap;align-self:center;padding-left:4px"
-           title="${_esc(wi.ai_desc || '')}">
-        ${_esc(detail) || '—'}
-      </div>
-    </div>`;
+    const sc   = STATUS_C[wi.status_user] || '#888';
+    const desc = (wi.ai_desc || '').replace(/\n/g,' ');
+    const descClip = desc.length > 70 ? desc.slice(0,70)+'…' : desc;
+    const linked = wi.tag_id
+      ? `<span style="font-size:0.48rem;color:var(--accent);flex-shrink:0">✓</span>`
+      : (wi.ai_tag_id ? `<span style="font-size:0.48rem;color:var(--muted);flex-shrink:0;opacity:.7">✦</span>` : '');
+    return `<tr draggable="true"
+        data-wi-id="${_esc(wi.id)}"
+        data-wi-name="${_esc(wi.ai_name)}"
+        ondragstart="window._wiBotDragStart(event,'${_esc(wi.id)}','${_esc(wi.ai

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index 56d249a..ea21726 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -75,13 +75,18 @@ _SQL_LIST_WORK_ITEMS_BASE = (
 _SQL_UNLINKED_WORK_ITEMS = """
     SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
            w.status_user, w.status_ai, w.requirements, w.summary, w.tags, w.ai_tags,
-           w.start_date, w.created_at, w.seq_num,
+           w.start_date, w.created_at, w.updated_at, w.seq_num,
            pt.name AS ai_tag_name,
-           (SELECT COUNT(*) FROM mem_ai_work_items src WHERE src.merged_into = w.id) AS merge_count
+           (SELECT COUNT(*) FROM mem_ai_work_items src WHERE src.merged_into = w.id) AS merge_count,
+           COALESCE((SELECT COUNT(*) FROM mem_ai_events
+                     WHERE work_item_id = w.id AND event_type = 'prompt_batch'), 0) AS prompt_count,
+           COALESCE((SELECT COUNT(*) FROM mem_mrr_commits c
+                     JOIN mem_ai_events e ON e.id = c.event_id
+                     WHERE e.work_item_id = w.id), 0) AS commit_count
     FROM mem_ai_work_items w
     LEFT JOIN planner_tags pt ON pt.id = w.ai_tag_id
     WHERE w.project_id=%s AND w.tag_id IS NULL AND w.status_user != 'done'
-    ORDER BY w.created_at DESC
+    ORDER BY w.updated_at DESC
 """
 
 _SQL_INSERT_WORK_ITEM = (
@@ -309,7 +314,7 @@ async def get_unlinked_work_items(project: str | None = Query(None)):
             for r in cur.fetchall():
                 row = dict(zip(cols, r))
                 row["id"] = str(row["id"])
-                for dt_field in ("created_at", "start_date"):
+                for dt_field in ("created_at", "updated_at", "start_date"):
                     if row.get(dt_field):
                         row[dt_field] = row[dt_field].isoformat()
                 rows.append(row)


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 381c829..b70d3d6 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-09 00:30 UTC
+> Generated by aicli 2026-04-09 00:35 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 0378619..dc368db 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 00:30 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 00:35 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -66,8 +66,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-08] I would like to sapparte database.py in order to have methgods and tables schema. can you create  db_schema.sql file tha
 - [2026-04-08] In the ui when I press any tag, I do not the property on the left (I do see that for work_items)
 - [2026-04-08] I do not see mem_mrr_commits_code populated on every commit. is that suppose to be like that? also is expensive to popul
 - [2026-04-08] I would like to understand how work_item are populated. work_item suppose to be linked to all events that relaed to spec
-- [2026-04-09] In the UI - work_items shows as a row. I would each row to have name - desc column, prompts column- show total prompts, 
\ No newline at end of file
+- [2026-04-09] In the UI - work_items shows as a row. I would each row to have name - desc column, prompts column- show total prompts, 
+- [2026-04-09] I do not see any change at the ui.
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.ai/rules.md b/.ai/rules.md
index 0378619..dc368db 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 00:30 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 00:35 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -66,8 +66,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-08] I would like to sapparte database.py in order to have methgods and tables schema. can you create  db_schema.sql file tha
 - [2026-04-08] In the ui when I press any tag, I do not the property on the left (I do see that for work_items)
 - [2026-04-08] I do not see mem_mrr_commits_code populated on every commit. is that suppose to be like that? also is expensive to popul
 - [2026-04-08] I would like to understand how work_item are populated. work_item suppose to be linked to all events that relaed to spec
-- [2026-04-09] In the UI - work_items shows as a row. I would each row to have name - desc column, prompts column- show total prompts, 
\ No newline at end of file
+- [2026-04-09] In the UI - work_items shows as a row. I would each row to have name - desc column, prompts column- show total prompts, 
+- [2026-04-09] I do not see any change at the ui.
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

Removed stale auto-generated context files and CLAUDE.md documentation from the _sys directory to clean up repository clutter.

## AI Synthesis

**[2026-04-09]** `entities.js + route_work_items.py` — Refactored work item table UI from grid layout to semantic HTML table with proper header styling: increased column width (38px→60+px), added active sort indicator arrows (↑/↓), implemented date formatter (YYMMDDHHSS), and separated sort state from category-pane sorting. **[2026-04-09]** `route_work_items.py` — Enhanced _SQL_UNLINKED_WORK_ITEMS query to count prompt_batch events and commits linked via mem_ai_events FK, enabling table columns for prompt_count and commit_count; added updated_at timestamp field for better recency sorting. **[2026-04-09]** `route_work_items.py` — Fixed work item drawer integration by adding updated_at to ISO datetime serialization alongside created_at and start_date; ensures proper date filtering in UI. **[2026-04-09]** `copilot-instructions.md` — Auto-regenerated project summary; aicli is a shared AI memory platform with PostgreSQL + pgvector semantic search, Claude/OpenAI LLM adapters, async DAG workflow engine, and Electron desktop UI for managing project context, work items, and AI-driven memory synthesis. **[Prior sessions]** — Established 4-layer memory architecture (ephemeral → mem_mrr raw capture → mem_ai_events LLM digests → mem_ai_work_items/project_facts), implemented prompt_loader centralization to eliminate redundant DB queries, deployed Railway + Electron-builder for cloud/desktop, and established db_schema.sql + db_migrations.py as source of truth.