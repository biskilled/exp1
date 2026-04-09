# Project Memory — aicli
_Generated: 2026-04-09 09:56 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend with PostgreSQL pgvector storage and an Electron desktop UI, designed to capture, synthesize, and manage AI-assisted development work through sessions, events, and semantic memory. Currently focused on fixing work item AI suggestion display and refactoring aggregation logic to correctly surface tags through session-based event linking rather than direct work item associations.

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
- **database**: PostgreSQL 15+
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

- Work item UI refresh button: replacing 'new work item' creation with refresh/reload functionality to fetch latest work items and update AI suggestions without requiring manual entry
- AI suggestion display fix: debugging why ai_tag_suggestion column shows empty (EXISTS) instead of actual suggested tags; investigating embedding pipeline trigger and suggestion query logic
- Work item tag aggregation: refining user_tags extraction from mem_ai_events by session_id and project_id instead of work_item_id to correctly surface feature/bug_ref/bug tags
- Work item counts accuracy: verifying prompt_count and commit_count calculations use session-based matching (same session as source_event_id) rather than direct work_item_id links
- Source event ID usage: confirming source_event_id field in mem_ai_work_items serves as anchor for session-based aggregation queries without requiring explicit SELECT visibility
- First event linkage guarantee: ensuring mem_ai_events.work_item_id updates only link to first work item (WHERE work_item_id IS NULL) to prevent overwrites on subsequent promotions

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

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 6bb2f3a..3911881 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Work item panel column layout fix: restored table-layout:fixed to prevent Name column from expanding and pushing right columns off-screen; adjusted colgroup widths
-- Work item tag section labeling: added persistent **AI:** and **User:** row labels to disambiguate tag types; User section shows '—' when no user tags exist
-- Work item detail loading: debugging click handlers on work item rows to ensure details panel opens when row is clicked (separate from button handlers)
-- AI tag suggestion display refinement: ensuring ai_tag_category:ai_tag_name format displays correctly with #4a90e2 default color when ai_tag_color is null
-- User tags aggregation from events: verifying jsonb_agg correctly collects feature/bug_ref/bug tags from mem_ai_events linked to work item
-- Frontend styling consolidation: ensuring consistent button styling (× delete, ✓ approve, × remove) with proper hover states and color differentiation across all tag interaction modes
+- Work item tag display restoration: investigating disappearing tags from work item rows; verifying JOIN logic in _SQL_UNLINKED_WORK_ITEMS query and user_tags aggregation from mem_ai_events
+- Work item description column layout: fixing desc column being cut mid-row; updating colgroup widths and removing table-layout:fixed constraint to display full-length descriptions
+- AI tag suggestion column rendering: ensuring ai_tag_suggestion chip displays correctly with approve (✓) and remove (×) buttons; refactored to simplified chip markup
+- User tags aggregation refinement: extracting feature/bug_ref/bug tags from mem_ai_events connected to work items via jsonb_agg; verifying tag_id matching
+- AI suggestion category-aware matching: confirmed matching pipeline now prioritizes task/bug/feature categories, enables Level 4 fallback for new suggestions, includes 0.60 confidence threshold
+- Frontend styling consolidation: ensuring consistent button styling (× delete, ✓ approve, × remove) with proper hover states and color differentiation across tag interaction modes


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index 5b21629..37776e9 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -82,11 +82,22 @@ _SQL_UNLINKED_WORK_ITEMS = """
            ptc.name  AS ai_tag_category,
            ptc.color AS ai_tag_color,
            (SELECT COUNT(*) FROM mem_ai_work_items src WHERE src.merged_into = w.id) AS merge_count,
-           COALESCE((SELECT COUNT(*) FROM mem_ai_events
-                     WHERE work_item_id = w.id AND event_type = 'prompt_batch'), 0) AS prompt_count,
-           COALESCE((SELECT COUNT(*) FROM mem_mrr_commits c
-                     JOIN mem_ai_events e ON e.id = c.event_id
-                     WHERE e.work_item_id = w.id), 0) AS commit_count,
+           -- Count prompt_batch events in the same session as the source event
+           COALESCE((
+               SELECT COUNT(*)
+               FROM mem_ai_events e2
+               WHERE e2.session_id = (SELECT session_id FROM mem_ai_events WHERE id = w.source_event_id)
+                 AND e2.project_id = w.project_id
+                 AND e2.event_type = 'prompt_batch'
+           ), 0) AS prompt_count,
+           -- Count commits in the same session as the source event
+           COALESCE((
+               SELECT COUNT(*)
+               FROM mem_mrr_commits mc
+               WHERE mc.session_id = (SELECT session_id FROM mem_ai_events WHERE id = w.source_event_id)
+                 AND mc.project_id = w.project_id
+           ), 0) AS commit_count,
+           -- User tags: planner tags referenced in events from the same session
            (SELECT COALESCE(jsonb_agg(DISTINCT ut.name ORDER BY ut.name), '[]'::jsonb)
             FROM mem_ai_events ev
             JOIN planner_tags ut ON ut.project_id = w.project_id
@@ -95,7 +106,8 @@ _SQL_UNLINKED_WORK_ITEMS = """
                      ev.tags->>'bug_ref',
                      ev.tags->>'bug'
                  )
-            WHERE ev.work_item_id = w.id
+            WHERE ev.session_id = (SELECT session_id FROM mem_ai_events WHERE id = w.source_event_id)
+              AND ev.project_id = w.project_id
               AND (ev.tags->>'feature' IS NOT NULL OR ev.tags->>'bug_ref' IS NOT NULL
                    OR ev.tags->>'bug' IS NOT NULL)
            ) AS user_tags
@@ -103,7 +115,7 @@ _SQL_UNLINKED_WORK_ITEMS = """
     LEFT JOIN planner_tags pt   ON pt.id  = w.ai_tag_id
     LEFT JOIN mng_tags_categories ptc ON ptc.id = pt.category_id
     WHERE w.project_id=%s AND w.tag_id IS NULL AND w.status_user != 'done'
-    ORDER BY w.seq_num DESC
+    ORDER BY w.created_at DESC
 """
 
 _SQL_INSERT_WORK_ITEM = (


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/memory/memory_promotion.py b/backend/memory/memory_promotion.py
index 4a39098..f5a548a 100644
--- a/backend/memory/memory_promotion.py
+++ b/backend/memory/memory_promotion.py
@@ -657,15 +657,16 @@ class MemoryPromotion:
                             )
                             row = cur.fetchone()
                             if row:
-                                created += 1
-                                # Link event to its newly created work item
                                 wi_id = str(row[0])
+                                created += 1
+                                # Link event → first work item only (don't overwrite if already set)
                                 cur.execute(
-                                    "UPDATE mem_ai_events SET work_item_id=%s::uuid WHERE id=%s::uuid",
+                                    "UPDATE mem_ai_events SET work_item_id=%s::uuid"
+                                    " WHERE id=%s::uuid AND work_item_id IS NULL",
                                     (wi_id, str(ev_id)),
                                 )
                             else:
-                                updated += 1  # ON CONFLICT DO UPDATE hit an existing item
+                                updated += 1  # ON CONFLICT DO NOTHING hit an existing item
                 except Exception as e:
                     log.debug(f"extract_work_items insert error: {e}")
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 310aa25..dd75ee9 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-09 02:45 UTC
+> Generated by aicli 2026-04-09 02:59 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -59,8 +59,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with UNION consolidation
 - Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; mem_mrr_commits.event_id points to mem_ai_events
-- Work item UI: multi-column sortable table with AI tag suggestions (category:name format) + user tags from connected events; approve/remove/delete buttons with labeled tag sections
-- Work item panel layout: table-layout:fixed restored to prevent Name column expansion; AI/User tag sections always displayed with labels and '—' placeholder for empty user tags
-- Date format frontend: YY/MM/DD-HH:MM format in work item panel and system displays
-- ai_tag_color_default: #4a90e2 replaces var(--accent) when ai_tag_color not set; tag label format is 'category:name' when both present, name-only fallback
-- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
\ No newline at end of file
+- AI suggestion system: category-aware matching (task/bug/feature prioritized), Level 4 fallback to suggest new when no matches ≥0.70, embedding pipeline with 0.60 confidence threshold
+- Work item panel: multi-column sortable table with AI tag suggestions + user tags from connected events; sticky headers with fixed table layout
+- Tag display format: 'category:name' when both present, name-only fallback, #4a90e2 default color when ai_tag_color null
+- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
+- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb) for desktop; bash start_backend.sh + npm run dev for local
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 506209a..875d39a 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 02:45 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 02:59 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -59,16 +59,16 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with UNION consolidation
 - Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; mem_mrr_commits.event_id points to mem_ai_events
-- Work item UI: multi-column sortable table with AI tag suggestions (category:name format) + user tags from connected events; approve/remove/delete buttons with labeled tag sections
-- Work item panel layout: table-layout:fixed restored to prevent Name column expansion; AI/User tag sections always displayed with labels and '—' placeholder for empty user tags
-- Date format frontend: YY/MM/DD-HH:MM format in work item panel and system displays
-- ai_tag_color_default: #4a90e2 replaces var(--accent) when ai_tag_color not set; tag label format is 'category:name' when both present, name-only fallback
+- AI suggestion system: category-aware matching (task/bug/feature prioritized), Level 4 fallback to suggest new when no matches ≥0.70, embedding pipeline with 0.60 confidence threshold
+- Work item panel: multi-column sortable table with AI tag suggestions + user tags from connected events; sticky headers with fixed table layout
+- Tag display format: 'category:name' when both present, name-only fallback, #4a90e2 default color when ai_tag_color null
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
+- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb) for desktop; bash start_backend.sh + npm run dev for local
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] Work_item not loading the details when I click on work item. also in the ui - I do see tag (left of the row) and approve
 - [2026-04-09] I do see there is one ai_tags which is good. but ai_tags suppose to be feature, bug or task with the name . for example 
 - [2026-04-09] I dont see any tags at the rows now (not ai and not users). also I do that desc is cut the the middle of the row instead
 - [2026-04-09] I cannot see the last column now. all I see is the first column name (commits.. ) I would like to add label in order to 
-- [2026-04-09] Can you add some padding on the left side of the table as last column UPDATED, I do see ony yy:mm:dd-HH:.. instead of th
\ No newline at end of file
+- [2026-04-09] Can you add some padding on the left side of the table as last column UPDATED, I do see ony yy:mm:dd-HH:.. instead of th
+- [2026-04-09] I would like to update the ai_sujjestion - it suppose to sujjest one tag from catgories (task, bug or feature) and can s
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.ai/rules.md b/.ai/rules.md
index 506209a..875d39a 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 02:45 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 02:59 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -59,16 +59,16 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with UNION consolidation
 - Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; mem_mrr_commits.event_id points to mem_ai_events
-- Work item UI: multi-column sortable table with AI tag suggestions (category:name format) + user tags from connected events; approve/remove/delete buttons with labeled tag sections
-- Work item panel layout: table-layout:fixed restored to prevent Name column expansion; AI/User tag sections always displayed with labels and '—' placeholder for empty user tags
-- Date format frontend: YY/MM/DD-HH:MM format in work item panel and system displays
-- ai_tag_color_default: #4a90e2 replaces var(--accent) when ai_tag_color not set; tag label format is 'category:name' when both present, name-only fallback
+- AI suggestion system: category-aware matching (task/bug/feature prioritized), Level 4 fallback to suggest new when no matches ≥0.70, embedding pipeline with 0.60 confidence threshold
+- Work item panel: multi-column sortable table with AI tag suggestions + user tags from connected events; sticky headers with fixed table layout
+- Tag display format: 'category:name' when both present, name-only fallback, #4a90e2 default color when ai_tag_color null
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
+- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb) for desktop; bash start_backend.sh + npm run dev for local
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] Work_item not loading the details when I click on work item. also in the ui - I do see tag (left of the row) and approve
 - [2026-04-09] I do see there is one ai_tags which is good. but ai_tags suppose to be feature, bug or task with the name . for example 
 - [2026-04-09] I dont see any tags at the rows now (not ai and not users). also I do that desc is cut the the middle of the row instead
 - [2026-04-09] I cannot see the last column now. all I see is the first column name (commits.. ) I would like to add label in order to 
-- [2026-04-09] Can you add some padding on the left side of the table as last column UPDATED, I do see ony yy:mm:dd-HH:.. instead of th
\ No newline at end of file
+- [2026-04-09] Can you add some padding on the left side of the table as last column UPDATED, I do see ony yy:mm:dd-HH:.. instead of th
+- [2026-04-09] I would like to update the ai_sujjestion - it suppose to sujjest one tag from catgories (task, bug or feature) and can s
\ No newline at end of file


## AI Synthesis

**[2026-04-09]** `claude_cli` — User reported AI tag suggestions showing as empty (EXISTS) in work item panel instead of actual tag values; identified that new work item creation from UI is non-functional, suggesting refresh button would be more practical for updating AI suggestions. **[2026-04]** `memory_promotion.py` — Fixed source event linkage by adding WHERE clause (work_item_id IS NULL) to prevent overwriting first work item assignment on subsequent promotions; changed ON CONFLICT behavior to DO NOTHING. **[2026-04]** `route_work_items.py` — Refactored work item aggregation queries to use session-based matching: prompt_count and commit_count now calculated via session_id from source_event_id instead of direct work_item_id links; user_tags extraction similarly scoped to session + project to surface connected feature/bug_ref/bug tags. **[Prior]** — Established AI suggestion matching pipeline with category-aware prioritization (task/bug/feature) and Level 4 fallback for new suggestions; set 0.60 confidence threshold for embedding matches. **[Prior]** — Standardized tag display format to 'category:name' when both present with #4a90e2 default color fallback; implemented multi-column work item panel with sticky headers and sortable rows.