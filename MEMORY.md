# Project Memory — aicli
_Generated: 2026-04-09 15:09 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
- Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; source_event_id pivot for session-based aggregation
- AI suggestion system: category-aware matching (task/bug/feature prioritized), Level 4 fallback to suggest new when no matches ≥0.70, 0.60 confidence threshold
- Tag backlinking: PATCH /work-items with tag_id triggers _backlink_tag_to_events() propagating assignments to all events in source session
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
- Session tagging via /tag command with tag_reminder_interval config (every N prompts); valid_tag_keys enforced (phase required, feature/bug/task/component/doc_type/design/decision/meeting/customer optional)
- Stdio MCP server with 12+ tools for semantic search, work item management, and session tag updates; embedding pipeline triggered via /memory endpoint

## In Progress

- Session tagging command (/tag) implementation: added tag_reminder_interval config to aicli.yaml with periodic prompt reminders (every 5-10 prompts) to validate prompt relevance to tagged context
- MCP set_session_tags tool documentation: updated schema to clarify phase as required, feature/bug_ref as optional, and 'extra' object for flexible tag categories (task, component, doc_type, design, decision, meeting, customer)
- Tag skill loading in Claude Code: sessions must be restarted to pick up new /tag skill definition; multi-tag syntax supported (phase:development feature:work-items-ui bug:login-500)
- Work item refresh workflow: refresh button triggers /work-items/rematch-all endpoint to refetch unlinked items and update AI tag suggestions in real-time
- Event count aggregation: 'Digests' column displays session-based COUNT(*) from mem_ai_events filtered to prompt_batch and session_summary types only
- AI tag backlinking propagation: tag assignments to work items automatically propagate to all events in source session via category→tag_key mapping (bug/phase/feature)

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

User requested tagging mechanism with periodic reminders; implemented via hooks that remind every 8 prompts. Attempted `/tag` skill but requires new session to load. Performance investigation revealed missing composite indexes on work_items and event queries; migration m020 added 5 indexes to accelerate session lookups, event filtering, and tag resolution.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index ba7eded..87fb7fb 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Work item refresh workflow: replaced 'new work item' button with ↻ refresh button triggering /work-items/rematch-all endpoint to refetch unlinked items and update AI tag suggestions
-- Event count aggregation: added event_count column (renamed to 'Digests') to work item panel calculated via session-based COUNT(*) from mem_ai_events matching prompt_batch and session_summary types only
-- AI tag backlinking implementation: _backlink_tag_to_events() propagates planner tag assignments back to all events in source session, mapping category→tag_key (bug/phase/feature)
-- Work item panel UI refinement: adjusted colgroup widths (52px per count column), fixed table overflow issues, added proper padding/spacing, updated event_count header label to 'Digests'
-- Interactive tag suggestion feature: prompt counter + periodic tag reminder system (every 5-10 prompts) to validate prompt relevance to tagged context during long sessions
-- AI tag display debugging: investigating missing suggested_new tags in ui_tags query and verifying ai_suggestion column population in work item panel refresh workflow
+- Session tagging command (/tag) implementation: added tag_reminder_interval config to aicli.yaml with periodic prompt reminders (every 5-10 prompts) to validate prompt relevance to tagged context
+- MCP set_session_tags tool documentation: updated schema to clarify phase as required, feature/bug_ref as optional, and 'extra' object for flexible tag categories (task, component, doc_type, design, decision, meeting, customer)
+- Tag skill loading in Claude Code: sessions must be restarted to pick up new /tag skill definition; multi-tag syntax supported (phase:development feature:work-items-ui bug:login-500)
+- Work item refresh workflow: refresh button triggers /work-items/rematch-all endpoint to refetch unlinked items and update AI tag suggestions in real-time
+- Event count aggregation: 'Digests' column displays session-based COUNT(*) from mem_ai_events filtered to prompt_batch and session_summary types only
+- AI tag backlinking propagation: tag assignments to work items automatically propagate to all events in source session via category→tag_key mapping (bug/phase/feature)


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index 8b42bbb..53318f3 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -74,71 +74,84 @@ _SQL_LIST_WORK_ITEMS_BASE = (
 )
 
 _SQL_UNLINKED_WORK_ITEMS = """
-    SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
-           w.status_user, w.status_ai, w.requirements, w.summary, w.tags, w.ai_tags,
-           w.start_date, w.created_at, w.updated_at, w.seq_num,
-           w.ai_tag_id,
-           pt.name AS ai_tag_name,
-           ptc.name  AS ai_tag_category,
+    WITH wi AS (
+        -- base filter once; carry session_id from source_event in one pass
+        SELECT w.id, w.ai_category, w.ai_name, w.ai_desc,
+               w.status_user, w.status_ai, w.requirements, w.summary, w.tags, w.ai_tags,
+               w.start_date, w.created_at, w.updated_at, w.seq_num,
+               w.ai_tag_id, w.source_event_id, w.project_id,
+               e.session_id AS src_session_id
+        FROM mem_ai_work_items w
+        LEFT JOIN mem_ai_events e ON e.id = w.source_event_id
+        WHERE w.project_id = %s AND w.tag_id IS NULL AND w.status_user != 'done'
+    ),
+    prompt_ct AS (
+        SELECT wi.id AS wi_id, COUNT(DISTINCT e.id) AS cnt
+        FROM wi
+        JOIN mem_ai_events e ON e.project_id = wi.project_id
+             AND e.event_type = 'prompt_batch'
+             AND (   (wi.src_session_id IS NOT NULL AND e.session_id = wi.src_session_id)
+                  OR e.work_item_id = wi.id )
+        GROUP BY wi.id
+    ),
+    commit_ct AS (
+        SELECT wi.id AS wi_id, COUNT(*) AS cnt
+        FROM wi
+        JOIN mem_mrr_commits mc ON mc.project_id = wi.project_id
+             AND wi.src_session_id IS NOT NULL
+             AND mc.session_id = wi.src_session_id
+        GROUP BY wi.id
+    ),
+    digest_ct AS (
+        SELECT wi.id AS wi_id, COUNT(DISTINCT e.id) AS cnt
+        FROM wi
+        JOIN mem_ai_events e ON e.project_id = wi.project_id
+             AND e.event_type IN ('prompt_batch', 'session_summary')
+             AND (   (wi.src_session_id IS NOT NULL AND e.session_id = wi.src_session_id)
+                  OR e.work_item_id = wi.id )
+        GROUP BY wi.id
+    ),
+    merge_ct AS (
+        SELECT merged_into AS wi_id, COUNT(*) AS cnt
+        FROM mem_ai_work_items
+        WHERE project_id = %s AND merged_into IS NOT NULL
+        GROUP BY 1
+    ),
+    user_tag_ct AS (
+        SELECT wi.id AS wi_id,
+               COALESCE(jsonb_agg(DISTINCT ut.name ORDER BY ut.name), '[]'::jsonb) AS tags
+        FROM wi
+        JOIN mem_ai_events ev ON ev.project_id = wi.project_id
+             AND wi.src_session_id IS NOT NULL
+             AND ev.session_id = wi.src_session_id
+             AND (ev.tags->>'feature' IS NOT NULL
+                  OR ev.tags->>'bug_ref' IS NOT NULL
+                  OR ev.tags->>'bug'     IS NOT NULL)
+        JOIN planner_tags ut ON ut.project_id = wi.project_id
+             AND ut.name IN (ev.tags->>'feature', ev.tags->>'bug_ref', ev.tags->>'bug')
+        GROUP BY wi.id
+    )
+    SELECT wi.id, wi.ai_category, wi.ai_name, wi.ai_desc,
+           wi.status_user, wi.status_ai, wi.requirements, wi.summary, wi.tags, wi.ai_tags,
+           wi.start_date, wi.created_at, wi.updated_at, wi.seq_num,
+           wi.ai_tag_id,
+           pt.name  AS ai_tag_name,
+           ptc.name AS ai_tag_category,
            ptc.color AS ai_tag_color,
-           (SELECT COUNT(*) FROM mem_ai_work_items src WHERE src.merged_into = w.id) AS merge_count,
-           -- Prompt count: session-based OR direct work_item_id link
-           COALESCE((
-               SELECT COUNT(*) FROM (
-                   SELECT id FROM mem_ai_events
-                   WHERE project_id = w.project_id
-                     AND event_type = 'prompt_batch'
-                     AND session_id IS NOT NULL
-                     AND session_id = (SELECT session_id FROM mem_ai_events
-                                       WHERE id = w.source_event_id AND session_id IS NOT NULL)
-                   UNION
-                   SELECT id FROM mem_ai_events
-                   WHERE project_id = w.project_id AND work_item_id = w.id
-                     AND event_type = 'prompt_batch'
-               ) _p
-           ), 0) AS prompt_count,
-           -- Commit count: session-based OR direct back-link
-           COALESCE((
-               SELECT COUNT(*) FROM mem_mrr_commits mc
-               WHERE mc.project_id = w.project_id
-                 AND mc.session_id IS NOT NULL
-                 AND mc.session_id = (SELECT session_id FROM mem_ai_events
-                                      WHERE id = w.source_event_id AND session_id IS NOT NULL)
-           ), 0) AS commit_count,
-           -- Digest count: prompt_batch + session_summary only (exclude per-commit/diff_file noise)
-           COALESCE((
-               SELECT COUNT(*) FROM (
-                   SELECT id FROM mem_ai_events
-                   WHERE project_id = w.project_id
-                     AND event_type IN ('prompt_batch', 'session_summary')
-                     AND session_id IS NOT NULL
-                     AND session_id = (SELECT session_id FROM mem_ai_events
-                                       WHERE id = w.source_event_id AND session_id IS NOT NULL)
-                   UNION
-                   SELECT id FROM mem_ai_events
-                   WHERE project_id = w.project_id AND work_item_id = w.id
-                     AND event_type IN ('prompt_batch', 'session_summary')
-               ) _e
-           ), 0) AS event_count,
-           -- User tags: planner tags referenced in events from the same session
-           (SELECT COALESCE(jsonb_agg(DISTINCT ut.name ORDER BY ut.name), '[]'::jsonb)
-            FROM mem_ai_events ev
-            JOIN planner_tags ut ON ut.project_id = w.project_id
-                 AND ut.name IN (
-                     ev.tags->>'fea

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/routers/route_entities.py b/backend/routers/route_entities.py
index 84f7bd3..066342b 100644
--- a/backend/routers/route_entities.py
+++ b/backend/routers/route_entities.py
@@ -188,6 +188,162 @@ _SQL_UPSERT_TAG_GITHUB = """
     RETURNING (xmax = 0) AS was_inserted, id::text
 """
 
+# Validate category id exists (global lookup)
+_SQL_GET_CATEGORY_BY_ID = """
+    SELECT id FROM mng_tags_categories WHERE client_id=1 AND id=%s
+"""
+
+# Get category name by id (global lookup)
+_SQL_GET_CATEGORY_NAME_BY_ID = """
+    SELECT name FROM mng_tags_categories WHERE client_id=1 AND id=%s
+"""
+
+# Resolve tag string "category:name" for a planner_tags UUID — used for tagging/events
+_SQL_GET_TAG_STRING_BY_ID = """
+    SELECT tc.name || ':' || t.name
+    FROM planner_tags t
+    JOIN mng_tags_categories tc ON tc.id = t.category_id
+    WHERE t.id=%s::uuid AND t.client_id=1
+    LIMIT 1
+"""
+
+# Work items per category for entity summary augmentation
+_SQL_WI_BY_CATEGORY = """
+    SELECT name, agent_status, acceptance_criteria, implementation_plan, lifecycle_status
+    FROM mem_ai_work_items
+    WHERE project_id=%s AND category_name=%s AND status != 'archived'
+"""
+
+# List commits for events endpoint
+_SQL_LIST_COMMIT_EVENTS = """
+    SELECT commit_hash, 'commit', commit_hash, left(commit_msg,120), committed_at
+    FROM mem_mrr_commits WHERE project_id=%s
+    ORDER BY committed_at DESC NULLS LAST LIMIT %s
+"""
+
+# List prompts for events endpoint
+_SQL_LIST_PROMPT_EVENTS = """
+    SELECT source_id, 'prompt', source_id, left(prompt,120), created_at
+    FROM mem_mrr_prompts WHERE project_id=%s AND event_type='prompt'
+    ORDER BY created_at DESC LIMIT %s
+"""
+
+# Find existing planner_tag by project + name
+_SQL_GET_TAG_BY_NAME = """
+    SELECT id::text FROM planner_tags WHERE project_id=%s AND name=%s
+"""
+
+# Insert session tag with short_desc
+_SQL_INSERT_SESSION_TAG_WITH_DESC = """
+    INSERT INTO planner_tags (project_id, name, category_id, seq_num, short_desc)
+    VALUES (%s, %s, %s, %s, %s) RETURNING id::text
+"""
+
+# Apply a JSONB tag to all prompts in a session
+_SQL_TAG_PROMPTS_BY_SESSION = """
+    UPDATE mem_mrr_prompts SET tags = tags || %s::jsonb
+    WHERE project_id=%s AND session_id=%s
+"""
+
+# Apply a JSONB tag to all commits in a session
+_SQL_TAG_COMMITS_BY_SESSION = """
+    UPDATE mem_mrr_commits SET tags = tags || %s::jsonb
+    WHERE project_id=%s AND session_id=%s
+"""
+
+# Apply a JSONB tag to a single commit by hash
+_SQL_TAG_COMMIT_BY_HASH = """
+    UPDATE mem_mrr_commits SET tags = tags || %s::jsonb
+    WHERE project_id=%s AND commit_hash=%s
+"""
+
+# Propagate tag from commit → its linked prompt
+_SQL_TAG_PROMPT_FROM_COMMIT = """
+    UPDATE mem_mrr_prompts pr
+       SET tags = pr.tags || %s::jsonb
+      FROM mem_mrr_commits c
+     WHERE c.project_id=%s AND c.commit_hash=%s
+       AND pr.id = c.prompt_id
+    RETURNING pr.source_id
+"""
+
+# Apply a JSONB tag to a single prompt by source_id
+_SQL_TAG_PROMPT_BY_SOURCE = """
+    UPDATE mem_mrr_prompts SET tags = tags || %s::jsonb
+    WHERE project_id=%s AND source_id=%s
+"""
+
+# Propagate tag from prompt → its linked commit
+_SQL_TAG_COMMIT_FROM_PROMPT = """
+    UPDATE mem_mrr_commits c
+       SET tags = c.tags || %s::jsonb
+      FROM mem_mrr_prompts p
+     WHERE p.project_id=%s AND p.source_id=%s
+       AND c.prompt_id = p.id
+    RETURNING c.commit_hash
+"""
+
+# Remove a tag key from a commit by hash
+_SQL_UNTAG_COMMIT_BY_HASH = """
+    UPDATE mem_mrr_commits SET tags = tags - %s
+    WHERE project_id=%s AND commit_hash=%s
+"""
+
+# Propagate tag removal from commit → its linked prompt
+_SQL_UNTAG_PROMPT_FROM_COMMIT = """
+    UPDATE mem_mrr_prompts pr
+       SET tags = pr.tags - %s
+      FROM mem_mrr_commits c
+     WHERE c.project_id=%s AND c.commit_hash=%s
+       AND pr.id = c.prompt_id
+    RETURNING pr.source_id
+"""
+
+# Remove a tag key from a prompt by source_id
+_SQL_UNTAG_PROMPT_BY_SOURCE = """
+    UPDATE mem_mrr_prompts SET tags = tags - %s
+    WHERE project_id=%s AND source_id=%s
+"""
+
+# Propagate tag removal from prompt → its linked commit
+_SQL_UNTAG_COMMIT_FROM_PROMPT = """
+    UPDATE mem_mrr_commits c
+       SET tags = c.tags - %s
+      FROM mem_mrr_prompts p
+     WHERE p.project_id=%s AND p.source_id=%s
+       AND c.prompt_id = p.id
+    RETURNING c.commit_hash
+"""
+
+# Remove a tag key from all prompts in a session
+_SQL_UNTAG_PROMPTS_BY_SESSION = """
+    UPDATE mem_mrr_prompts SET tags = tags - %s
+    WHERE project_id=%s AND session_id=%s
+"""
+
+# Remove a tag key from all commits in a session
+_SQL_UNTAG_COMMITS_BY_SESSION = """
+    UPDATE mem_mrr_commits SET tags = tags - %s
+    WHERE project_id=%s AND session_id=%s
+"""
+
+# All tagged prompts for source-tags endpoint (exclude internal-only tags)
+_SQL_GET_TAGGED_PROMPTS = """
+    SELECT source_id, tags FROM mem_mrr_prompts
+    WHERE project_id=%s AND (tags - 'source' - 'llm') != '{}'::jsonb
+"""
+
+# All tagged commits for source-tags endpoint (exclude internal-only tags)
+_SQL_GET_TAGGED_COMMITS = """
+    SELECT commit_hash, tags FROM mem_mrr_commits
+    WHERE project_id=%s AND (tags - 'source' - 'llm') != '{}'::jsonb
+"""
+
+# Set due_date on a planner_tag by id
+_SQL_SET_TAG_DUE_DATE = """
+    UPDATE planner_tags SET due_date=%s WHERE id=%s::uuid
+"""
+
 # ────────────────────────────────────────────────────────────────────────────────
 
 router = APIRouter()
@@ -424,13 +580,7 @@ async def entity_summary(project: str | None = Query(None)):
         try:
             with db.conn() as conn:
                 with conn.cursor() as cur:
-                    cur.execute(
-                        """SELECT name, agent_status, acceptance_criteria,
-                                  implementation_plan, lifecycle_status
-                           FROM mem_ai_work_items
-                           WHERE project_id=%s AND category_name=%s AND status != 'archived'""",
-        

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/core/db_migrations.py b/backend/core/db_migrations.py
index 50b0ef0..4e6a29d 100644
--- a/backend/core/db_migrations.py
+++ b/backend/core/db_migrations.py
@@ -169,6 +169,42 @@ def m019_wi_event_fk_columns(conn) -> None:
     log.info("m019_wi_event_fk_columns: event_id on commits + work_item_id on events applied")
 
 
+def m020_perf_indexes(conn) -> None:
+    """Add missing composite indexes for query performance.
+
+    The work items and planner queries were doing O(N) correlated subqueries
+    or full-table scans due to missing indexes on frequently-filtered columns.
+    """
+    with conn.cursor() as cur:
+        # mem_ai_events — session_id lookups (used in _SQL_UNLINKED_WORK_ITEMS CTE)
+        cur.execute(
+            "CREATE INDEX IF NOT EXISTS idx_mae_project_session "
+            "ON mem_ai_events(project_id, session_id) WHERE session_id IS NOT NULL"
+        )
+        # mem_ai_events — event_type filter (prompt_batch/session_summary counts)
+        cur.execute(
+            "CREATE INDEX IF NOT EXISTS idx_mae_project_etype "
+            "ON mem_ai_events(project_id, event_type)"
+        )
+        # mem_mrr_commits — session_id lookups (commit count per session in work items)
+        cur.execute(
+            "CREATE INDEX IF NOT EXISTS idx_mmrrc_project_session "
+            "ON mem_mrr_commits(project_id, session_id) WHERE session_id IS NOT NULL"
+        )
+        # planner_tags — name lookups (entity/tag search)
+        cur.execute(
+            "CREATE INDEX IF NOT EXISTS idx_planner_tags_project_name "
+            "ON planner_tags(project_id, name)"
+        )
+        # mem_ai_work_items — status_user filter (unlinked items query skips 'done')
+        cur.execute(
+            "CREATE INDEX IF NOT EXISTS idx_mawi_project_status_user "
+            "ON mem_ai_work_items(project_id, status_user)"
+        )
+    conn.commit()
+    log.info("m020_perf_indexes: composite indexes applied")
+
+
 MIGRATIONS: list[tuple[str, Callable]] = [
     # All migrations through m017 (ai_tags column) were applied via the legacy
     # ALTER TABLE system in database.py and are tracked as:
@@ -176,4 +212,5 @@ MIGRATIONS: list[tuple[str, Callable]] = [
     #   work_items_alters_v1, commit_code_v1
     ("m018_work_items_links", m018_work_items_links),
     ("m019_wi_event_fk_columns", m019_wi_event_fk_columns),
+    ("m020_perf_indexes", m020_perf_indexes),
 ]


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index a390f4f..15ff563 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-09 13:40 UTC
+> Generated by aicli 2026-04-09 13:46 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -22,10 +22,10 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - workflow_ui: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
 - memory_synthesis: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
 - chunking: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
-- mcp: Stdio MCP server with 12+ tools
+- mcp: Stdio MCP server with 12+ tools (semantic search, work item management, session tagging)
 - deployment: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
 - database_schema: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, planner_tags, mng_tags_categories
-- config_management: config.py + YAML pipelines + pyproject.toml
+- config_management: config.py + YAML pipelines + pyproject.toml + aicli.yaml session tagging config
 - db_tables: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - llm_provider_adapters: agents/providers/ with pr_ prefix for pricing and provider implementations
 - pipeline_engine: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
@@ -33,7 +33,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - billing_storage: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
 - backend_modules: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - dev_environment: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
-- database: PostgreSQL 15+ with pgvector extensions
+- database: PostgreSQL 15+ with pgvector extensions; unified mem_ai_* tables; per-project schema
 - node_modules_build: npm 8+ with Electron-builder; Vite dev server
 - database_version: PostgreSQL 15+
 - build_tooling: npm 8+ with Electron-builder; Vite dev server
@@ -62,5 +62,5 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - AI suggestion system: category-aware matching (task/bug/feature prioritized), Level 4 fallback to suggest new when no matches ≥0.70, 0.60 confidence threshold
 - Tag backlinking: PATCH /work-items with tag_id triggers _backlink_tag_to_events() propagating assignments to all events in source session
 - Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
-- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
-- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb) for desktop
\ No newline at end of file
+- Session tagging via /tag command with tag_reminder_interval config (every N prompts); valid_tag_keys enforced (phase required, feature/bug/task/component/doc_type/design/decision/meeting/customer optional)
+- Stdio MCP server with 12+ tools for semantic search, work item management, and session tag updates; embedding pipeline triggered via /memory endpoint
\ No newline at end of file

