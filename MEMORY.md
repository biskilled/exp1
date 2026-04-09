# Project Memory — aicli
_Generated: 2026-04-09 03:12 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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

### `commit` — 2026-04-09

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 84aff7c..a56099a 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -540,14 +540,13 @@ function _renderWiPanel(items, project) {
     } catch(e) { toast('Remove failed: ' + e.message, 'error'); }
   };
 
-  window._wiPanelCreateTag = async (id, tagName, proj) => {
-    if (!confirm(`Create new tag "${tagName}" and link this work item?`)) return;
+  window._wiPanelCreateTag = async (id, tagName, categoryName, proj) => {
+    const catLabel = categoryName || 'task';
+    if (!confirm(`Create new ${catLabel} tag "${tagName}" and link this work item?`)) return;
     try {
-      const wi = _wiPanelItems[id];
-      const cat = wi ? wi.ai_category : 'task';
-      // Find or create the category id
+      // Resolve category id from name
       const cats = await api.tags.categories.list(proj);
-      const catObj = cats.find(c => c.name === cat) || cats.find(c => c.name === 'task') || cats[0];
+      const catObj = cats.find(c => c.name === catLabel) || cats.find(c => c.name === 'task') || cats[0];
       const newTag = await api.tags.create({ name: tagName, project: proj, category_id: catObj?.id });
       await api.workItems.patch(id, proj, { tag_id: newTag.id });
       delete _wiPanelItems[id];
@@ -555,7 +554,7 @@ function _renderWiPanel(items, project) {
       _renderWiPanel(remaining, proj);
       const cnt = document.getElementById('wi-panel-count');
       if (cnt) cnt.textContent = remaining.length ? `(${remaining.length} unlinked)` : '(all linked ✓)';
-      toast(`Created tag "${tagName}" and linked`, 'success');
+      toast(`Created ${catLabel} tag "${tagName}" and linked`, 'success');
     } catch(e) { toast('Create failed: ' + e.message, 'error'); }
   };
 
@@ -573,8 +572,10 @@ function _renderWiPanel(items, project) {
     const aiTagLabel = wi.ai_tag_name
       ? (wi.ai_tag_category ? wi.ai_tag_category + ':' + wi.ai_tag_name : wi.ai_tag_name)
       : '';
-    // AI(NEW) — stored in ai_tags.suggested_new (set by backend when no existing tag fits)
+    // AI(NEW) — stored in ai_tags.suggested_new + suggested_category
     const aiNew = (wi.ai_tags && wi.ai_tags.suggested_new) ? wi.ai_tags.suggested_new : '';
+    const aiNewCat = (wi.ai_tags && wi.ai_tags.suggested_category) ? wi.ai_tags.suggested_category : 'task';
+    const aiNewLabel = aiNew ? (aiNewCat + ':' + aiNew) : '';
     const userTagsList = Array.isArray(wi.user_tags) ? wi.user_tags : [];
 
     // AI row — always shown; show EXISTS first, then NEW if no exists match
@@ -597,8 +598,8 @@ function _renderWiPanel(items, project) {
         <span style="${LBL_AI_N}">AI(NEW)</span>
         <span style="font-size:0.65rem;font-weight:500;padding:1px 6px;border-radius:4px;
                      color:#e74c3c;border:1px solid #e74c3c;background:#e74c3c1a;
-                     white-space:nowrap">${_esc(aiNew)}</span>
-        <button onclick="event.stopPropagation();window._wiPanelCreateTag('${_esc(wi.id)}','${_esc(aiNew)}','${_esc(project)}')"
+                     white-space:nowrap">${_esc(aiNewLabel)}</span>
+        <button onclick="event.stopPropagation();window._wiPanelCreateTag('${_esc(wi.id)}','${_esc(aiNew)}','${_esc(aiNewCat)}','${_esc(project)}')"
           title="Create this tag" style="background:none;border:1px solid #e74c3c;color:#e74c3c;
                  cursor:pointer;font-size:0.6rem;font-weight:700;padding:1px 6px;border-radius:4px;line-height:1.5">✓</button>
         <button onclick="event.stopPropagation();window._wiPanelRemoveTag('${_esc(wi.id)}','${_esc(project)}')"


### `commit` — 2026-04-09

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index 2b18ef1..5b21629 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -103,7 +103,7 @@ _SQL_UNLINKED_WORK_ITEMS = """
     LEFT JOIN planner_tags pt   ON pt.id  = w.ai_tag_id
     LEFT JOIN mng_tags_categories ptc ON ptc.id = pt.category_id
     WHERE w.project_id=%s AND w.tag_id IS NULL AND w.status_user != 'done'
-    ORDER BY w.updated_at DESC
+    ORDER BY w.seq_num DESC
 """
 
 _SQL_INSERT_WORK_ITEM = (
@@ -273,10 +273,13 @@ async def _run_matching(project: str, work_item_id: str) -> None:
                         (best["tag_id"], work_item_id),
                     )
                 elif best.get("suggested_new"):
-                    # New tag suggestion — store in ai_tags JSONB
+                    # New tag suggestion — store name + category in ai_tags JSONB
                     cur.execute(
                         "UPDATE mem_ai_work_items SET ai_tags=ai_tags||%s::jsonb, updated_at=NOW() WHERE id=%s::uuid",
-                        (json.dumps({"suggested_new": best["suggested_new"]}), work_item_id),
+                        (json.dumps({
+                            "suggested_new": best["suggested_new"],
+                            "suggested_category": best.get("suggested_category") or "task",
+                        }), work_item_id),
                     )
     except Exception:
         pass  # non-critical background task


### `commit` — 2026-04-09

diff --git a/backend/memory/memory_tagging.py b/backend/memory/memory_tagging.py
index d6c249c..b8507ff 100644
--- a/backend/memory/memory_tagging.py
+++ b/backend/memory/memory_tagging.py
@@ -323,20 +323,25 @@ class MemoryTagging:
                     return None
                 return {'id': str(row[0]), 'name': row[1], 'category_id': row[2]}
 
-    def _load_all_tags(self, project: str, limit: int = 40) -> list[dict]:
-        """Load all active planner tags (no embedding required) for Haiku-fallback matching."""
+    def _load_all_tags(self, project: str, limit: int = 50) -> list[dict]:
+        """Load all active planner tags with category name, prioritising task/bug/feature."""
         project_id = db.get_or_create_project_id(project)
         with db.conn() as conn:
             with conn.cursor() as cur:
                 cur.execute("""
-                    SELECT id, name, category_id, short_desc
-                    FROM planner_tags
-                    WHERE project_id = %s AND status != 'archived'
-                    ORDER BY created_at DESC LIMIT %s
+                    SELECT t.id, t.name, t.category_id, t.short_desc, tc.name AS category_name
+                    FROM planner_tags t
+                    LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
+                    WHERE t.project_id = %s AND t.status != 'archived'
+                    ORDER BY
+                        CASE WHEN tc.name IN ('task','bug','feature') THEN 0 ELSE 1 END,
+                        t.created_at DESC
+                    LIMIT %s
                 """, (project_id, limit))
                 rows = cur.fetchall()
                 return [{'id': str(r[0]), 'name': r[1], 'category_id': r[2],
-                         'short_desc': r[3] or '', 'score': 0.0} for r in rows]
+                         'short_desc': r[3] or '', 'category_name': r[4] or '',
+                         'score': 0.0} for r in rows]
 
     def _vector_search_tags(self, project: str, embedding: list, limit: int = 15) -> list[dict]:
         project_id = db.get_or_create_project_id(project)
@@ -363,30 +368,39 @@ class MemoryTagging:
         return resp.data[0].embedding
 
     async def _claude_judge_candidates(self, wi: dict, candidates: list[dict]) -> list[dict]:
-        """Use Claude Haiku to find the best matching tag for a work item."""
+        """Use Claude Haiku to find the best matching tag for a work item.
+
+        Candidates show their category. Haiku must prioritise task/bug/feature categories.
+        When no existing tag fits it suggests a new one in the most appropriate category.
+        """
         cand_text = '\n'.join(
-            f"- {c['name']} | {c.get('short_desc','')}" for c in candidates
+            f"- [{c.get('category_name','?')}] {c['name']} | {c.get('short_desc','')}"
+            for c in candidates
         )
         prompt = (
             f"WORK ITEM: {wi['name']} — {wi.get('description','')}\n\n"
-            f"AVAILABLE TAGS:\n{cand_text}\n\n"
-            "Pick the SINGLE best matching tag for this work item.\n"
-            "If a tag fits (confidence ≥ 0.70), return it with relation 'exact' or 'similar'.\n"
-            "If NO existing tag fits, suggest a short new tag name (kebab-case, ≤3 words) as suggested_new.\n"
-            'Respond ONLY in JSON:\n'
-            '  Match exists:  {"tag_name":"existing-tag","relation":"exact|similar","confidence":0.0-1.0,"suggested_new":null}\n'
-            '  No match:      {"tag_name":null,"relation":"none","confidence":0.0,"suggested_new":"new-tag-name"}'
+            f"AVAILABLE TAGS (format: [category] name | description):\n{cand_text}\n\n"
+            "Rules:\n"
+            "1. Prefer matching to a tag in the 'task', 'bug', or 'feature' category.\n"
+            "2. If no task/bug/feature tag fits, match to phase, doc_type, or other category.\n"
+            "3. If no existing tag fits (confidence < 0.70), suggest a short new tag name "
+            "(kebab-case, ≤3 words) AND pick the best category: 'task', 'bug', or 'feature'.\n"
+            "Respond ONLY in JSON (pick ONE):\n"
+            '  Match:    {"tag_name":"existing-name","category":"existing-category",'
+            '"relation":"exact|similar","confidence":0.0-1.0,"suggested_new":null,"suggested_category":null}\n'
+            '  New tag:  {"tag_name":null,"category":null,"relation":"none","confidence":0.0,'
+            '"suggested_new":"new-tag-name","suggested_category":"task|bug|feature"}'
         )
         system = (
             "You are a technical project memory assistant. "
-            "Match AI-generated work items to project feature/task tags. "
+            "Match AI-generated work items to project feature/task/bug tags. "
             "Respond ONLY in valid JSON — no markdown, no explanation."
         )
 
         client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
         msg = await client.messages.create(
             model='claude-haiku-4-5-20251001',
-            max_tokens=128,
+            max_tokens=150,
             system=system,
             messages=[{'role': 'user', 'content': prompt}]
         )
@@ -411,13 +425,15 @@ class MemoryTagging:
                         'relation': m.get('relation', 'none'),
                         'confidence': float(m.get('confidence', 0.75)),
                         'suggested_new': None,
+                        'suggested_category': None,
                     })
             elif suggested_new:
-                # No existing tag match — suggest a new tag name
+                # No existing tag match — suggest a new tag in the right category
                 results.append({
                     'tag_id': None,
                     'relation': 'new',
                     'confidence': 0.60,
                     'suggested_new': suggested_new,
+                    'suggested_category': m.get('suggested_category') or 'task',
                 })
         return results


### `commit` — 2026-04-09

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index ba45f6e..310aa25 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-09 02:21 UTC
+> Generated by aicli 2026-04-09 02:45 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit` — 2026-04-09

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index d4af2c8..506209a 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 02:21 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 02:45 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -67,8 +67,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] I cannot see the sujjestion. is it on each row in work_items ?
 - [2026-04-09] Work_item not loading the details when I click on work item. also in the ui - I do see tag (left of the row) and approve
 - [2026-04-09] I do see there is one ai_tags which is good. but ai_tags suppose to be feature, bug or task with the name . for example 
 - [2026-04-09] I dont see any tags at the rows now (not ai and not users). also I do that desc is cut the the middle of the row instead
-- [2026-04-09] I cannot see the last column now. all I see is the first column name (commits.. ) I would like to add label in order to 
\ No newline at end of file
+- [2026-04-09] I cannot see the last column now. all I see is the first column name (commits.. ) I would like to add label in order to 
+- [2026-04-09] Can you add some padding on the left side of the table as last column UPDATED, I do see ony yy:mm:dd-HH:.. instead of th
\ No newline at end of file


### `commit` — 2026-04-09

diff --git a/.ai/rules.md b/.ai/rules.md
index d4af2c8..506209a 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 02:21 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-09 02:45 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -67,8 +67,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-09] I cannot see the sujjestion. is it on each row in work_items ?
 - [2026-04-09] Work_item not loading the details when I click on work item. also in the ui - I do see tag (left of the row) and approve
 - [2026-04-09] I do see there is one ai_tags which is good. but ai_tags suppose to be feature, bug or task with the name . for example 
 - [2026-04-09] I dont see any tags at the rows now (not ai and not users). also I do that desc is cut the the middle of the row instead
-- [2026-04-09] I cannot see the last column now. all I see is the first column name (commits.. ) I would like to add label in order to 
\ No newline at end of file
+- [2026-04-09] I cannot see the last column now. all I see is the first column name (commits.. ) I would like to add label in order to 
+- [2026-04-09] Can you add some padding on the left side of the table as last column UPDATED, I do see ony yy:mm:dd-HH:.. instead of th
\ No newline at end of file

