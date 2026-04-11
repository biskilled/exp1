# Project Memory — aicli
_Generated: 2026-04-11 23:00 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Facts

- **ai_event_filtering_logic**: event_type IN ('prompt_batch', 'session_summary') filters mem_ai_events; excludes per-commit and diff_file noise from event_count aggregation
- **ai_tag_color_default**: #4a90e2 replaces var(--accent), applied when wi.ai_tag_color not set
- **ai_tag_label_format**: category:name when both present, falls back to name-only, empty string if neither
- **ai_tag_suggestion_debugging_status**: investigating missing suggested_new tags in ui_tags query and verifying ai_suggestion column population in work item panel refresh workflow
- **ai_tag_suggestion_feature**: ai_tag_suggestion column with approve/remove button handlers (_wiPanelApproveTag/_wiPanelRemoveTag), refactored to simplified chip markup without category prefix display in non-category mode
- **ai_tag_suggestion_ux**: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip improved from 'No existing tag' to 'Does not exist yet'
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
- **event_count_column_semantics**: counts prompt_batch + session_summary events only; now displayed after commit_count (moved from position 2 to position 4)
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
- **prompt_count_metric**: distinct metric tracked separately from event_count in work items API response
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
- **rel:stag_command:tag_command**: replaces
- **rel:sticky_header:work_items_panel**: implements
- **rel:tag_reminder:session_context**: depends_on
- **rel:ui_notifications:error_handling**: related_to
- **rel:wiDeleteLinked:entities_js**: implements
- **rel:wiUnlink:wiRowLoading**: depends_on
- **rel:work_item_api:prompt_count**: depends_on
- **rel:work_item_deletion:api_endpoint**: depends_on
- **rel:work_item_panel_sort:prompt_count**: implements
- **rel:work_item_panel:state_management**: implements
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- **session_context_prompt_counter**: prompt_count field added to session context JSON, initialized to 0, incremented on each prompt validation
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- **tag_command_alias**: /stag replaces /tag due to Claude Code skill name conflict; identical functionality with immediate availability
- **tag_creation_workflow**: _wiPanelCreateTag creates tags without confirmation, auto-links work item, refreshes tag cache + planner table + category tag list
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
- **work_item_deletion_handler**: _wiDeleteLinked in entities.js with confirmation dialog and _wiRowLoading state management
- **work_item_deletion_pattern**: client-side confirmation dialog, async api.workItems.delete(), local state cleanup, re-render panel
- **work_item_description_processing**: newlines replaced with spaces and trimmed (replace(/\n/g,' ').trim()), clipped to 70 chars with ellipsis
- **work_item_display_fields**: ai_category icon mapping, status_user color mapping, seq_num sequence number, id identifier
- **work_item_event_association**: two-path join: session_id match from source_event_id OR direct work_item_id link, both filtered by event_type
- **work_item_panel_column_order**: Name, prompt_count, commit_count, event_count, updated_at (prompts column added before commits, events moved last)
- **work_item_panel_column_widths**: prompt_count:46px, commit_count:46px, event_count:46px (resized from 52px event_count + 52px commit_count)
- **work_item_panel_sortable_fields**: prompt_count, event_count, commit_count, seq_num (prompt_count added to sort handler)
- **work_item_panel_state_management**: _wiPanelItems object stores work items, window._wiPanelDelete and window._wiPanelRefresh are global handlers
- **work_item_ui_column_widths**: 56px–80px for multi-column sortable table headers
- **work_item_ui_pattern**: multi-column sortable table with proper header styling, status color badges
- **work_item_unlink_handler**: _wiUnlink uses _wiRowLoading(id, true) for loading state during patch operation

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
- **database**: PostgreSQL 15+ with pgvector extensions
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
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags_relations, project_facts, work_items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
- Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; source_event_id pivot for session-based aggregation
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
- Secondary AI tags stored in ai_tags.confirmed[] array (metadata for doc_type/feature/phase); primary tag_id links work item to category, secondary tags remain as chips
- Work item counters: prompt_count (raw prompts in source session), event_count (prompt_batch/session_summary events), commit_count (distinct commits per session)
- Session tagging: /stag command (replaced /tag due to Claude Code skill conflict) with immediate tag propagation via log_user_prompt.sh reading .agent-context
- UI state management: _wiPanelItems object-keyed cache; _renderWiPanel for unlinked items; tag-linked items persist across category switches

## In Progress

- Work item row loading states: _wiRowLoading() helper with CSS pulsing animation during async operations (delete, approve, dismiss); integrated into _wiDeleteLinked, _wiUnlink, _wiPanelDelete, _wiPanelApproveTag, _wiPanelRemoveTag handlers
- Secondary AI tag workflow refinement: _wiSecApprove now stores confirmed metadata (doc_type/phase/component) in ai_tags.confirmed[] array instead of removing items from panel; items remain visible with permanent chip indicators
- Work item panel consistency: error handling improved to restore loading state on catch; toast messaging clarified for approve (link to tag), remove (clear metadata), and secondary approve (save as metadata)
- Tag-linked work item refresh: _loadTagLinkedWorkItems reloads after approve/reject operations; planner table updates to reflect linked/unlinked status changes when category is selected
- AI tag suggestion UX: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip messaging improved from 'No existing tag' to 'Does not exist yet'
- Work item deletion UI: confirmation dialogs + loading indicators for _wiDeleteLinked (tag-linked panel) and _wiPanelDelete (unlinked panel); delete operations remove items and refresh counts

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
- **entity-routing** `[open]`
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
- **graph-workflow** `[open]`

### Phase

- **prod** `[open]`
- **development** `[open]`
- **discovery** `[open]`

### Task

- **memory** `[open]`
- **implement-projects-tab** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 67d006f..8890c87 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Secondary AI tag UX refinement: _wiSecApprove stores doc_type/feature/phase/bug/task tags in ai_tags.confirmed[] array; items remain visible in work item list with ✓ button showing as permanent chip indicator
-- Work item deletion UI: implemented _wiDeleteLinked handler with confirmation dialog; delete button appears in tag-linked work items panel with opacity toggle hover effect
-- Tag creation with auto-link workflow: _wiPanelCreateTag creates new tags without confirmation, auto-links work item, refreshes tag cache + planner table + category tag list
-- AI suggestion chips UX: added clickable ✓ button to create missing ai_suggestion tags with category inference; improved tooltip messaging for non-existent tags
-- Tag-linked work item refresh: _loadTagLinkedWorkItems reloads after approve/reject/create operations to reflect linked/unlinked status changes in planner view
-- Work item persistence across sessions: ensuring tag-linked and newly-created work items remain accessible across tag switches and session changes
+- Work item row loading states: _wiRowLoading() helper with CSS pulsing animation during async operations (delete, approve, dismiss); integrated into _wiDeleteLinked, _wiUnlink, _wiPanelDelete, _wiPanelApproveTag, _wiPanelRemoveTag handlers
+- Secondary AI tag workflow refinement: _wiSecApprove now stores confirmed metadata (doc_type/phase/component) in ai_tags.confirmed[] array instead of removing items from panel; items remain visible with permanent chip indicators
+- Work item panel consistency: error handling improved to restore loading state on catch; toast messaging clarified for approve (link to tag), remove (clear metadata), and secondary approve (save as metadata)
+- Tag-linked work item refresh: _loadTagLinkedWorkItems reloads after approve/reject operations; planner table updates to reflect linked/unlinked status changes when category is selected
+- AI tag suggestion UX: clickable ✓ button creates missing ai_suggestion tags with category inference; tooltip messaging improved from 'No existing tag' to 'Does not exist yet'
+- Work item deletion UI: confirmation dialogs + loading indicators for _wiDeleteLinked (tag-linked panel) and _wiPanelDelete (unlinked panel); delete operations remove items and refresh counts


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index fbb714e..35ca241 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -163,7 +163,7 @@ _SQL_INSERT_WORK_ITEM = (
            (project_id, ai_category, ai_name, ai_desc,
             acceptance_criteria_ai, action_items_ai,
             code_summary, summary, tags, status_user, status_ai, seq_num)
-       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
+       VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s,%s)
        ON CONFLICT (project_id, ai_category, ai_name) DO NOTHING
        RETURNING id, ai_name, ai_category, created_at, seq_num"""
 )
@@ -550,9 +550,9 @@ async def list_work_items(
                     row["tag_id_user"] = str(row["tag_id_user"])
                 if row.get("tag_id_ai"):
                     row["tag_id_ai"] = str(row["tag_id_ai"])
-                if row.get("tags") is None:
-                    row["tags"] = {}
-                if row.get("tags_ai") is None:
+                if not isinstance(row.get("tags"), dict):
+                    row["tags"] = {}   # handles NULL and legacy TEXT[] values
+                if not isinstance(row.get("tags_ai"), dict):
                     row["tags_ai"] = {}
                 rows.append(row)
     return {"work_items": rows, "project": p, "total": len(rows)}
@@ -615,7 +615,7 @@ async def patch_work_item(
     if body.summary             is not None: fields.append("summary=%s");             params.append(body.summary)
     if body.tags                is not None:
         import json as _json
-        fields.append("tags=%s"); params.append(_json.dumps(body.tags))
+        fields.append("tags=%s::jsonb"); params.append(_json.dumps(body.tags))
     if body.tags_ai             is not None:
         import json as _json
         fields.append("tags_ai = tags_ai || %s::jsonb"); params.append(_json.dumps(body.tags_ai))


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/backend/prompts/memory/work_items/work_item_extraction.md b/backend/prompts/memory/work_items/work_item_extraction.md
index d718b69..7acb499 100644
--- a/backend/prompts/memory/work_items/work_item_extraction.md
+++ b/backend/prompts/memory/work_items/work_item_extraction.md
@@ -4,7 +4,13 @@ identify actionable work items AND suggest session tags.
 Return JSON only:
 {
   "items": [
-    {"category": "bug|feature|task", "name": "short-slug", "description": "1-2 sentence explanation"}
+    {
+      "category": "bug|feature|task",
+      "name": "short-slug",
+      "description": "1-2 sentence explanation of what this is and why it matters",
+      "acceptance_criteria": "- [ ] Specific, testable outcome 1\n- [ ] Specific, testable outcome 2",
+      "action_items": "- First concrete step to take\n- Second concrete step\n- Third step if needed"
+    }
   ],
   "suggested_tags": {
     "phase": "discovery|development|testing|review|production|maintenance|bugfix",
@@ -14,6 +20,8 @@ Return JSON only:
 
 Rules:
 - items: at most 5 entries. Use lowercase-hyphenated slugs for name. Empty array if nothing actionable.
+- acceptance_criteria: 1-3 bullet lines, each starting with "- [ ]". Must be specific and testable. Short.
+- action_items: 1-4 bullet lines, each starting with "-". Concrete next steps. Short imperative phrases.
 - suggested_tags.phase: pick the most fitting phase from the list above based on the activity.
 - suggested_tags.feature: a slug matching the primary feature being worked on, or null if unclear.
 - No preamble, no markdown fences, return ONLY valid JSON.


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/backend/memory/memory_promotion.py b/backend/memory/memory_promotion.py
index 79e20b6..f031c4a 100644
--- a/backend/memory/memory_promotion.py
+++ b/backend/memory/memory_promotion.py
@@ -141,15 +141,29 @@ _SQL_UPDATE_EVENT_AI_TAGS = """
 _SQL_INSERT_EXTRACTED_WORK_ITEM = """
     INSERT INTO mem_ai_work_items
         (project_id, ai_category, ai_name, ai_desc,
+         acceptance_criteria_ai, action_items_ai, tags,
          source_event_id, seq_num)
-    VALUES (%s, %s, %s, %s, %s::uuid,
+    VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s::uuid,
             (SELECT COALESCE(MAX(seq_num),0)+1 FROM mem_ai_work_items WHERE project_id=%s))
     ON CONFLICT (project_id, ai_category, ai_name) DO UPDATE SET
-        ai_desc    = EXCLUDED.ai_desc,
-        updated_at = NOW()
+        ai_desc              = EXCLUDED.ai_desc,
+        acceptance_criteria_ai = CASE WHEN EXCLUDED.acceptance_criteria_ai != ''
+                                      THEN EXCLUDED.acceptance_criteria_ai
+                                      ELSE mem_ai_work_items.acceptance_criteria_ai END,
+        action_items_ai      = CASE WHEN EXCLUDED.action_items_ai != ''
+                                    THEN EXCLUDED.action_items_ai
+                                    ELSE mem_ai_work_items.action_items_ai END,
+        tags                 = CASE WHEN EXCLUDED.tags != '{}'::jsonb
+                                    THEN mem_ai_work_items.tags || EXCLUDED.tags
+                                    ELSE mem_ai_work_items.tags END,
+        updated_at           = NOW()
     RETURNING id
 """
 
+# Keys considered "user intent" tags — copied from event tags to work item tags
+_USER_TAG_KEYS = frozenset({"source", "phase", "feature", "bug", "component",
+                             "doc_type", "design", "decision", "meeting", "customer"})
+
 
 # ── Helpers ───────────────────────────────────────────────────────────────────
 
@@ -654,18 +668,25 @@ class MemoryPromotion:
             if not items:
                 continue
 
+            # Build filtered tags from source event (user-intent keys only)
+            wi_tags = json.dumps({k: v for k, v in event_tags.items()
+                                  if k in _USER_TAG_KEYS and v})
+
             for item in items[:5]:
                 category = item.get("category", "task")
                 name = (item.get("name") or "").strip().lower()[:200]
                 description = (item.get("description") or "").strip()[:1000]
                 if not name or not description:
                     continue
+                ac = (item.get("acceptance_criteria") or "").strip()[:2000]
+                ai = (item.get("action_items") or "").strip()[:2000]
                 try:
                     with db.conn() as conn:
                         with conn.cursor() as cur:
                             cur.execute(
                                 _SQL_INSERT_EXTRACTED_WORK_ITEM,
                                 (project_id, category, name, description,
+                                 ac, ai, wi_tags,
                                  str(ev_id), project_id),
                             )
                             row = cur.fetchone()


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/backend/core/db_migrations.py b/backend/core/db_migrations.py
index b1e57b9..461100b 100644
--- a/backend/core/db_migrations.py
+++ b/backend/core/db_migrations.py
@@ -252,6 +252,62 @@ def m022_backfill_event_work_item_ids(conn) -> None:
     log.info(f"m022_backfill_event_work_item_ids: {updated} events backlinked")
 
 
+def m023_work_items_tags_to_jsonb(conn) -> None:
+    """Convert mem_ai_work_items.tags from TEXT[] to JSONB.
+
+    Old design stored tags as a text array {source:claude_cli, phase:dev} — never
+    populated and hard to query. New design: JSONB object {source, phase, feature, ...}
+    matching the tags on mem_mrr_* tables.
+
+    All existing rows have tags={} (empty array) so the USING clause just sets '{}'.
+    """
+    with conn.cursor() as cur:
+        # Step 1: drop the old TEXT[] default so PostgreSQL allows the type change
+        cur.execute("ALTER TABLE mem_ai_work_items ALTER COLUMN tags DROP DEFAULT")
+        # Step 2: alter type with explicit USING — all existing rows are empty arrays
+        cur.execute("""
+            ALTER TABLE mem_ai_work_items
+            ALTER COLUMN tags TYPE JSONB
+            USING CASE WHEN array_length(tags, 1) IS NULL THEN '{}'::jsonb
+                       ELSE array_to_json(tags)::jsonb END
+        """)
+        # Step 3: restore default and NOT NULL constraint for JSONB
+        cur.execute("ALTER TABLE mem_ai_work_items ALTER COLUMN tags SET DEFAULT '{}'::jsonb")
+        cur.execute("ALTER TABLE mem_ai_work_items ALTER COLUMN tags SET NOT NULL")
+    conn.commit()
+    log.info("m023_work_items_tags_to_jsonb: tags column converted TEXT[] → JSONB")
+
+
+def m024_backfill_work_item_tags(conn) -> None:
+    """Backfill work item tags from source event tags.
+
+    For each work item whose tags={} and has a source_event_id,
+    copies the user-intent keys (source, phase, feature, bug, component, doc_type)
+    from the source event's tags JSONB into the work item.
+
+    This is a one-time data migration for items created before m023/m024.
+    Going forward, tags are set at extraction time in memory_promotion.py.
+    """
+    _USER_KEYS = "source", "phase", "feature", "bug", "component", "doc_type"
+    key_filter = " OR ".join(f"e.tags ? '{k}'" for k in _USER_KEYS)
+    with conn.cursor() as cur:
+        cur.execute(f"""
+            UPDATE mem_ai_work_items wi
+            SET tags = (
+                SELECT jsonb_object_agg(kv.key, kv.value)
+                FROM jsonb_each_text(e.tags) AS kv(key, value)
+                WHERE kv.key = ANY(ARRAY['source','phase','feature','bug','component','doc_type'])
+            )
+            FROM mem_ai_events e
+            WHERE e.id = wi.source_event_id
+              AND wi.tags = '{{}}'::jsonb
+              AND ({key_filter})
+        """)
+        updated = cur.rowcount
+    conn.commit()
+    log.info(f"m024_backfill_work_item_tags: {updated} work items backfilled with event tags")
+
+
 MIGRATIONS: list[tuple[str, Callable]] = [
     # All migrations through m017 (ai_tags column) were applied via the legacy
     # ALTER TABLE system in database.py and are tracked as:
@@ -262,4 +318,6 @@ MIGRATIONS: list[tuple[str, Callable]] = [
     ("m020_perf_indexes", m020_perf_indexes),
     ("m021_rename_work_item_columns", m021_rename_work_item_columns),
     ("m022_backfill_event_work_item_ids", m022_backfill_event_work_item_ids),
+    ("m023_work_items_tags_to_jsonb", m023_work_items_tags_to_jsonb),
+    ("m024_backfill_work_item_tags", m024_backfill_work_item_tags),
 ]


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-11

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 48c2671..5448e58 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-10 15:45 UTC
+> Generated by aicli 2026-04-11 12:27 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -50,7 +50,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 ## Architectural Decisions
 
 - Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
-- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
+- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags_relations, project_facts, work_items, features
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
 - LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
 - Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
@@ -60,7 +60,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
 - Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; source_event_id pivot for session-based aggregation
 - Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; excludes per-commit and diff_file noise from event_count aggregation
-- AI tag backlinking: PATCH /work-items with tag_id triggers propagation to all events in source session via category→tag_key mapping
 - Secondary AI tags stored in ai_tags.confirmed[] array (metadata for doc_type/feature/phase); primary tag_id links work item to category, secondary tags remain as chips
 - Work item counters: prompt_count (raw prompts in source session), event_count (prompt_batch/session_summary events), commit_count (distinct commits per session)
-- Session tagging: /stag command (replaced /tag due to Claude Code skill conflict) with immediate tag propagation via log_user_prompt.sh reading .agent-context
\ No newline at end of file
+- Session tagging: /stag command (replaced /tag due to Claude Code skill conflict) with immediate tag propagation via log_user_prompt.sh reading .agent-context
+- UI state management: _wiPanelItems object-keyed cache; _renderWiPanel for unlinked items; tag-linked items persist across category switches
\ No newline at end of file

