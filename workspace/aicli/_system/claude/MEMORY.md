# Project Memory — aicli
_Generated: 2026-04-09 02:04 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/memory/memory_tagging.py b/backend/memory/memory_tagging.py
index 4b14c9f..1f779b1 100644
--- a/backend/memory/memory_tagging.py
+++ b/backend/memory/memory_tagging.py
@@ -234,12 +234,13 @@ class MemoryTagging:
         if not query.strip():
             return []
 
+        candidates: list[dict] = []
         try:
             emb = await self._embed_text(query)
+            candidates = self._vector_search_tags(project, emb, limit=15)
         except Exception:
-            return []
+            pass  # no embedding available — fall through to Haiku fallback
 
-        candidates = self._vector_search_tags(project, emb, limit=15)
         strong = [c for c in candidates if c['score'] > 0.85]
         border = [c for c in candidates if 0.70 < c['score'] <= 0.85]
 
@@ -257,6 +258,18 @@ class MemoryTagging:
             except Exception:
                 pass
 
+        # Level 4 — no vector candidates (tags have no embeddings yet): ask Haiku directly
+        if not candidates:
+            try:
+                all_tags = self._load_all_tags(project)
+                if all_tags:
+                    judgments = await self._claude_judge_candidates(wi, all_tags)
+                    for j in judgments:
+                        if j.get('relation') not in (None, 'none') and j.get('confidence', 0) >= 0.70:
+                            results.append(j)
+            except Exception:
+                pass
+
         # Persist best match to ai_tag_id (highest confidence)
         if results:
             best = max(results, key=lambda r: r.get('confidence', 0))
@@ -306,6 +319,21 @@ class MemoryTagging:
                     return None
                 return {'id': str(row[0]), 'name': row[1], 'category_id': row[2]}
 
+    def _load_all_tags(self, project: str, limit: int = 40) -> list[dict]:
+        """Load all active planner tags (no embedding required) for Haiku-fallback matching."""
+        project_id = db.get_or_create_project_id(project)
+        with db.conn() as conn:
+            with conn.cursor() as cur:
+                cur.execute("""
+                    SELECT id, name, category_id, short_desc
+                    FROM planner_tags
+                    WHERE project_id = %s AND status != 'archived'
+                    ORDER BY created_at DESC LIMIT %s
+                """, (project_id, limit))
+                rows = cur.fetchall()
+                return [{'id': str(r[0]), 'name': r[1], 'category_id': r[2],
+                         'short_desc': r[3] or '', 'score': 0.0} for r in rows]
+
     def _vector_search_tags(self, project: str, embedding: list, limit: int = 15) -> list[dict]:
         project_id = db.get_or_create_project_id(project)
         with db.conn() as conn:
@@ -331,41 +359,51 @@ class MemoryTagging:
         return resp.data[0].embedding
 
     async def _claude_judge_candidates(self, wi: dict, candidates: list[dict]) -> list[dict]:
-        """Use Claude Haiku to judge borderline tag candidates."""
+        """Use Claude Haiku to find the best matching tag for a work item."""
         cand_text = '\n'.join(
-            f"- {c['name']} (score:{c['score']:.2f}) | {c.get('short_desc','')}"
-            for c in candidates
+            f"- {c['name']} | {c.get('short_desc','')}" for c in candidates
         )
         prompt = (
-            f"WORK ITEM: name: {wi['name']}  summary: {wi.get('description','')}\n"
-            f"CANDIDATE TAGS:\n{cand_text}\n\n"
-            "For each candidate, determine if it matches this work item.\n"
-            "Exact: same concept, scope, intent. Similar: overlapping but not identical. None: unrelated.\n"
-            'Respond ONLY in JSON: {"matches":[{"tag_name":"...","relation":"exact|similar|none","confidence":0.0-1.0}]}'
+            f"WORK ITEM: {wi['name']} — {wi.get('description','')}\n\n"
+            f"AVAILABLE TAGS:\n{cand_text}\n\n"
+            "Pick the SINGLE best matching tag for this work item (if any).\n"
+            "relation: 'exact' (same concept), 'similar' (overlapping), or 'none' (no match).\n"
+            'Respond ONLY in JSON: {"tag_name":"...","relation":"exact|similar|none","confidence":0.0-1.0}\n'
+            'If no tag fits, respond: {"tag_name":null,"relation":"none","confidence":0.0}'
         )
         system = (
             "You are a technical project memory assistant. "
-            "Given an AI-generated work item and candidate tags, determine if any match. "
-            "Respond ONLY in JSON."
+            "Match AI-generated work items to project feature/task tags. "
+            "Respond ONLY in valid JSON — no markdown, no explanation."
         )
 
         client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
         msg = await client.messages.create(
             model='claude-haiku-4-5-20251001',
-            max_tokens=512,
+            max_tokens=128,
             system=system,
             messages=[{'role': 'user', 'content': prompt}]
         )
         text = msg.content[0].text.strip()
+        # Strip markdown code fences if present
+        if text.startswith('```'):
+            text = text.split('```')[1]
+            if text.startswith('json'):
+                text = text[4:]
+            text = text.strip()
         data = json.loads(text)
         name_to_id = {c['name']: c['id'] for c in candidates}
+        # Handle both single-object and array response
+        matches = data if isinstance(data, list) else [data]
         results = []
-        for m in data.get('matches', []):
-            tid = name_to_id.get(m.get('tag_name'))
-            if tid:
+        for m in matches:
+            if not m.get('tag_name'):
+                continue
+            tid = name_to_id.get(m['tag_name'])
+            if tid and m.get('relation', 'none') != 'none':
                 results.append({
                     'tag_id': tid,
                     'relation': m.get('relation', 'none'),
-                    'confidence':

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index a0d8b7d..0a9eb0a 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-09 01:13 UTC
+> Generated by aicli 2026-04-09 01:16 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -62,4 +62,4 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
 - Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
 - Prompt centralization via core.prompt_loader; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
-- Work item UI: sticky header on scroll, multi-column sortable table with YY/MM/DD-HH:MM date formatting, status color badges, and AI tag suggestions per row
\ No newline at end of file
+- Work item UI: multi-column sortable table with YY/MM/DD-HH:MM date formatting, wider columns (56px–80px), status color badges, and scope-filtered tag display
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 96869a5..05c6f84 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 01:13 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 01:16 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -62,7 +62,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
 - Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
 - Prompt centralization via core.prompt_loader; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
-- Work item UI: sticky header on scroll, multi-column sortable table with YY/MM/DD-HH:MM date formatting, status color badges, and AI tag suggestions per row
+- Work item UI: multi-column sortable table with YY/MM/DD-HH:MM date formatting, wider columns (56px–80px), status color badges, and scope-filtered tag display
 
 ## Recent Context (last 5 changes)
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/.ai/rules.md b/.ai/rules.md
index 96869a5..05c6f84 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 01:13 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 01:16 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -62,7 +62,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
 - Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
 - Prompt centralization via core.prompt_loader; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
-- Work item UI: sticky header on scroll, multi-column sortable table with YY/MM/DD-HH:MM date formatting, status color badges, and AI tag suggestions per row
+- Work item UI: multi-column sortable table with YY/MM/DD-HH:MM date formatting, wider columns (56px–80px), status color badges, and scope-filtered tag display
 
 ## Recent Context (last 5 changes)
 

