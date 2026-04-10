# Project Memory — aicli
_Generated: 2026-04-10 14:52 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform integrating a Python 3.12 CLI backend (FastAPI + PostgreSQL with pgvector) with a desktop Electron UI, designed to capture developer sessions, extract semantic work items through Claude synthesis, and surface them via unified event/tag/work-item architecture. Current state: resolving critical linkage bug where newly created work items have zero associated prompts/events despite /memory command processing, indicating session-to-work-item propagation failure.

## Project Facts

- **ai_event_filtering_logic**: event_type IN ('prompt_batch', 'session_summary') filters mem_ai_events; excludes per-commit and diff_file noise from event_count aggregation
- **ai_tag_color_default**: #4a90e2 replaces var(--accent), applied when wi.ai_tag_color not set
- **ai_tag_label_format**: category:name when both present, falls back to name-only, empty string if neither
- **ai_tag_suggestion_debugging_status**: investigating missing suggested_new tags in ui_tags query and verifying ai_suggestion column population in work item panel refresh workflow
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
- **event_count_column_semantics**: renamed from 'Total events' to 'Digest count'; now counts only prompt_batch + session_summary event types, not all session events
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
- **rel:event_filtering:noise_reduction**: implements
- **rel:frontend_ui_pattern:ai_tag_suggestion_feature**: implements
- **rel:mem_ai_events:work_items**: depends_on
- **rel:memory_endpoint:tag_detection**: implements
- **rel:memory_system:session_tags**: implements
- **rel:prompt_loader:mng_system_roles**: replaces
- **rel:route_memory:prompt_loader**: depends_on
- **rel:route_memory:sql_parameter_binding**: depends_on
- **rel:route_prompts:memory_embedding**: depends_on
- **rel:route_search:memory_embedding**: depends_on
- **rel:route_snapshots:prompt_loader**: depends_on
- **rel:route_work_items:sql_parameter_binding**: depends_on
- **rel:session_context:prompt_counter**: implements
- **rel:sticky_header:work_items_panel**: implements
- **rel:tag_reminder:session_context**: depends_on
- **rel:ui_notifications:error_handling**: related_to
- **rel:work_item_deletion:api_endpoint**: depends_on
- **rel:work_item_panel:state_management**: implements
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- **session_context_prompt_counter**: prompt_count field added to session context JSON, initialized to 0, incremented on each prompt validation
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- **tag_filtering_scope_issue**: non-work-item tags (Shared-memory, billing) incorrectly appearing in work_items panel UI; scope filtering implementation in progress
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
- **tag_reminder_display_format**: soft: '┄ Prompt #{N} ╌ still on: {tags}'; hard: multi-line box with current tags and re-send/update instructions
- **tag_reminder_feature**: soft reminder every N prompts (default 8, configurable via TAG_REMINDER_INTERVAL), hard check at 3× interval with tag confirmation requirement
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
- **work_item_event_association**: two-path join: session_id match from source_event_id OR direct work_item_id link, both filtered by event_type
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
- **mcp**: Stdio MCP server with 12+ tools (semantic search, work item management, session tagging)
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories
- **config_management**: config.py + YAML pipelines + pyproject.toml + aicli.yaml session tagging config
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extensions; unified mem_ai_* tables; per-project schema
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
- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; Shared: users, usage_logs, transactions, session_tags, entity_categories, planner_tags, mng_tags_categories

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
- Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; source_event_id pivot for session-based aggregation
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
- AI tag backlinking: PATCH /work-items with tag_id triggers propagation to all events in source session via category→tag_key mapping
- Commit tracking: mem_mrr_commits_code table with 19 columns; join is mem_ai_events.source_id (short hash) → mem_mrr_commits.commit_short_hash for commit-sourced items
- Work item counters: prompt_count (raw prompts in source session), event_count (prompt_batch/session_summary events), commit_count (distinct commits per session or source commit)
- Session tagging: /tag command with tag_reminder_interval config; valid_tag_keys enforced (phase required, feature/bug/task/component/doc_type/design optional)

## In Progress

- Work item counter architecture overhaul: refactored _SQL_UNLINKED_WORK_ITEMS to separate prompt_count (raw mem_mrr_prompts in source session), event_count (prompt_batch/session_summary digests), and commit_count (session-based or source commit); consolidated event_ct/prompt_ct/commit_ct CTEs with src_session_id and src_source_id tracking
- Query parameter rationalization: reduced _SQL_UNLINKED_WORK_ITEMS from 3 param refs to 2 by removing redundant (p_id, p_id, p_id) pattern; unified WHERE conditions across event/prompt/commit joins
- Frontend column reordering: added prompt_count column to work item panel; sorted display as Name | Prompts | Commits | Events | Updated; added prompt_count to sort handler
- Debugging unlinked work items with zero prompts: investigating why work_item #20442 has event_count=0 despite /memory command processing; hypothesis is session-to-work-item linkage not persisting across prompt_batch extraction
- Memory synthesis linkage investigation: determining root cause of work items created without corresponding mem_mrr_prompts or mem_ai_events in source session; may indicate race condition in prompt capture or session_id mismatch
- Session workflow tracing: planning comprehensive debug of /memory execution: prompt capture → session_id assignment → work_item creation → event_ct join validation

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
index 5fc5ccc..3864a86 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -479,6 +479,7 @@ function _renderWiPanel(items, project) {
   const { field, dir } = window._wiPanelSort;
   const mul = dir === 'asc' ? 1 : -1;
   const sorted = [...items].sort((a, b) => {
+    if (field === 'prompt_count') return mul * ((a.prompt_count||0) - (b.prompt_count||0));
     if (field === 'event_count')  return mul * ((a.event_count||0)  - (b.event_count||0));
     if (field === 'commit_count') return mul * ((a.commit_count||0) - (b.commit_count||0));
     if (field === 'seq_num')      return mul * ((a.seq_num||0)      - (b.seq_num||0));
@@ -724,10 +725,13 @@ function _renderWiPanel(items, project) {
       </td>
       <td style="padding:4px 10px;text-align:right;white-space:nowrap;font-size:0.72rem;vertical-align:top;
                  color:var(--text2);font-variant-numeric:tabular-nums;
-                 border-left:1px solid var(--border)">${wi.event_count||0}</td>
+                 border-left:1px solid var(--border)">${wi.prompt_count||0}</td>
       <td style="padding:4px 10px;text-align:right;white-space:nowrap;font-size:0.72rem;vertical-align:top;
                  color:var(--text2);font-variant-numeric:tabular-nums;
                  border-left:1px solid var(--border)">${wi.commit_count||0}</td>
+      <td style="padding:4px 10px;text-align:right;white-space:nowrap;font-size:0.72rem;vertical-align:top;
+                 color:var(--text2);font-variant-numeric:tabular-nums;
+                 border-left:1px solid var(--border)">${wi.event_count||0}</td>
       <td style="padding:4px 10px 4px 6px;text-align:right;white-space:nowrap;font-size:0.66rem;vertical-align:top;
                  color:var(--muted);font-variant-numeric:tabular-nums;font-family:monospace;
                  border-left:1px solid var(--border)">${fmtDate(wi.updated_at||wi.created_at)}</td>
@@ -736,14 +740,15 @@ function _renderWiPanel(items, project) {
 
   list.innerHTML = `
     <table style="width:100%;border-collapse:collapse;table-layout:fixed">
-      <colgroup><col><col style="width:52px"><col style="width:52px"><col style="width:112px"></colgroup>
+      <colgroup><col><col style="width:46px"><col style="width:46px"><col style="width:46px"><col style="width:112px"></colgroup>
       <thead><tr>
         <th style="text-align:left;padding:5px 8px 5px 12px;font-size:0.68rem;font-weight:600;
                    letter-spacing:.03em;text-transform:uppercase;
                    color:var(--muted);background:var(--surface2);
                    border-bottom:2px solid var(--border);position:sticky;top:0;z-index:1">Name</th>
-        ${hdr('event_count','Events')}
+        ${hdr('prompt_count','Prompts')}
         ${hdr('commit_count','Commits')}
+        ${hdr('event_count','Events')}
         ${hdr('updated_at','Updated')}
       </tr></thead>
       <tbody>${rows}</tbody>


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index 8808280..d7b3e98 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -75,31 +75,54 @@ _SQL_LIST_WORK_ITEMS_BASE = (
 
 _SQL_UNLINKED_WORK_ITEMS = """
     WITH wi AS (
-        -- Base filter: unlinked, non-done items; carry source_event_type for commit detection
+        -- Base filter; join source event once to get session_id + event_type
         SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
                w.status_user, w.status_ai, w.requirements, w.summary, w.tags, w.ai_tags,
                w.start_date, w.created_at, w.updated_at, w.seq_num,
                w.ai_tag_id, w.source_event_id, w.project_id,
-               e.event_type AS src_event_type
+               e.event_type  AS src_event_type,
+               e.session_id  AS src_session_id,
+               e.source_id   AS src_source_id
         FROM mem_ai_work_items w
         LEFT JOIN mem_ai_events e ON e.id = w.source_event_id
         WHERE w.project_id = %s AND w.tag_id IS NULL AND w.status_user != 'done'
     ),
-    -- Events directly linked to this work item via work_item_id (set at extraction time)
+    -- prompt_batch/session_summary events in the source session
+    -- (all items extracted from the same batch share this session → all get same count)
     event_ct AS (
-        SELECT e.work_item_id::text AS wi_id, COUNT(*) AS cnt
-        FROM mem_ai_events e
-        WHERE e.project_id = %s AND e.work_item_id IS NOT NULL
-        GROUP BY 1
+        SELECT wi.id::text AS wi_id, COUNT(DISTINCT e.id) AS cnt
+        FROM wi
+        JOIN mem_ai_events e
+          ON e.project_id = wi.project_id
+         AND e.event_type IN ('prompt_batch', 'session_summary')
+         AND (
+               (wi.src_session_id IS NOT NULL AND e.session_id = wi.src_session_id)
+            OR  e.work_item_id = wi.id          -- fallback for directly linked events
+         )
+        GROUP BY wi.id
+    ),
+    -- raw prompts in the source session
+    prompt_ct AS (
+        SELECT wi.id::text AS wi_id, COUNT(DISTINCT p.id) AS cnt
+        FROM wi
+        JOIN mem_mrr_prompts p
+          ON p.project_id = wi.project_id
+         AND wi.src_session_id IS NOT NULL
+         AND p.session_id = wi.src_session_id
+        GROUP BY wi.id
     ),
-    -- Commits: for commit-sourced items, the source commit itself counts as 1
+    -- commits from source session (prompt-sourced) OR the source commit (commit-sourced)
+    -- Note: src_source_id is the short commit hash stored in mem_ai_events.source_id
     commit_ct AS (
         SELECT wi.id::text AS wi_id, COUNT(DISTINCT mc.commit_hash) AS cnt
         FROM wi
-        LEFT JOIN mem_mrr_commits mc
-               ON mc.project_id = wi.project_id
-              AND wi.src_event_type = 'commit'
-              AND mc.event_id = wi.source_event_id
+        JOIN mem_mrr_commits mc
+          ON mc.project_id = wi.project_id
+         AND (
+               (wi.src_session_id IS NOT NULL AND mc.session_id = wi.src_session_id)
+            OR (wi.src_event_type = 'commit' AND wi.src_source_id IS NOT NULL
+                AND mc.commit_short_hash = wi.src_source_id)
+         )
         GROUP BY wi.id
     ),
     merge_ct AS (
@@ -117,11 +140,13 @@ _SQL_UNLINKED_WORK_ITEMS = """
            ptc.color AS ai_tag_color,
            COALESCE(merge_ct.cnt,  0) AS merge_count,
            COALESCE(event_ct.cnt,  0) AS event_count,
+           COALESCE(prompt_ct.cnt, 0) AS prompt_count,
            COALESCE(commit_ct.cnt, 0) AS commit_count
     FROM wi
     LEFT JOIN planner_tags        pt  ON pt.id  = wi.ai_tag_id
     LEFT JOIN mng_tags_categories ptc ON ptc.id = pt.category_id
     LEFT JOIN event_ct  ON event_ct.wi_id  = wi.id::text
+    LEFT JOIN prompt_ct ON prompt_ct.wi_id = wi.id::text
     LEFT JOIN commit_ct ON commit_ct.wi_id = wi.id::text
     LEFT JOIN merge_ct  ON merge_ct.wi_id  = wi.id::text
     ORDER BY wi.seq_num DESC NULLS LAST
@@ -440,7 +465,7 @@ async def get_unlinked_work_items(project: str | None = Query(None)):
     p_id = db.get_or_create_project_id(p)
     with db.conn() as conn:
         with conn.cursor() as cur:
-            cur.execute(_SQL_UNLINKED_WORK_ITEMS, (p_id, p_id, p_id))
+            cur.execute(_SQL_UNLINKED_WORK_ITEMS, (p_id, p_id))
             cols = [d[0] for d in cur.description]
             rows = []
             for r in cur.fetchall():


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 1c3879b..e9d7810 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-09 14:06 UTC
+> Generated by aicli 2026-04-09 15:09 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 6f09f30..4f44f3d 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 14:06 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 15:09 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -67,8 +67,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] I do see same work item working on mention document summery and update ai memory. all internal work such update internal
 - [2026-04-09] Can you share the quesry you are suing the get all promotps, commit, event per work_item . I want to check that for work
 - [2026-04-09] before you desing. is it possible to add some mechanism to our converstion. for example force adding tags and every 5-10
 - [2026-04-09] I have just tried that, got unknow skill /tag. do I have to open a new session ?
-- [2026-04-09] can you check why it takes to long to  load planner tabs and work items? it looks liike quesry are not optimised. also d
\ No newline at end of file
+- [2026-04-09] can you check why it takes to long to  load planner tabs and work items? it looks liike quesry are not optimised. also d
+- [2026-04-09] I am more confused noew. query - looks like it take longer. why there is DIGEST column ? it  suppose to  be events count
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.ai/rules.md b/.ai/rules.md
index 6f09f30..4f44f3d 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 14:06 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 15:09 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -67,8 +67,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] I do see same work item working on mention document summery and update ai memory. all internal work such update internal
 - [2026-04-09] Can you share the quesry you are suing the get all promotps, commit, event per work_item . I want to check that for work
 - [2026-04-09] before you desing. is it possible to add some mechanism to our converstion. for example force adding tags and every 5-10
 - [2026-04-09] I have just tried that, got unknow skill /tag. do I have to open a new session ?
-- [2026-04-09] can you check why it takes to long to  load planner tabs and work items? it looks liike quesry are not optimised. also d
\ No newline at end of file
+- [2026-04-09] can you check why it takes to long to  load planner tabs and work items? it looks liike quesry are not optimised. also d
+- [2026-04-09] I am more confused noew. query - looks like it take longer. why there is DIGEST column ? it  suppose to  be events count
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

Removed stale auto-generated system context and CLAUDE.md files to clean up repository cruft.

## AI Synthesis

**[2026-04-10]** `user_query` — Uncovered critical gap: work items are being created without linked prompts/events in source session. Work item #20442 (recently updated) has event_count=0 despite /memory command execution, indicating failure in session_id propagation or prompt capture timing.

**[2026-04-09]** `refactor` — Restructured work item counter architecture: separated prompt_count (raw mem_mrr_prompts in session), event_count (prompt_batch/session_summary digests), and commit_count (session-based or source commit). Added src_session_id and src_source_id tracking to _SQL_UNLINKED_WORK_ITEMS for accurate aggregation.

**[2026-04-09]** `frontend_update` — Reordered work item panel columns: Name | Prompts | Commits | Events | Updated. Added prompt_count to sort handler and table colgroup; reduced visual column widths from 52px to 46px for tabular alignment.

**[2026-04-09]** `query_optimization` — Consolidated _SQL_UNLINKED_WORK_ITEMS parameter pattern from (p_id, p_id, p_id) to (p_id, p_id) by unifying event/prompt/commit CTE joins with consistent WHERE conditions on project_id.

**[2026-04-10]** `investigation` — Root cause analysis needed: /memory command execution flow must be traced from prompt capture → session_id assignment → mem_ai_events insertion → work_item source_event_id linkage to identify where unlinked items originate.