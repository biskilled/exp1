# Project Memory — aicli
_Generated: 2026-04-09 00:30 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend with PostgreSQL semantic storage and an Electron desktop UI. It captures development context (commits, prompts, sessions) into a 4-layer memory architecture, synthesizes insights via Claude, and manages work items through a unified database schema with intelligent tagging and workflow automation.

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
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts → user planner_tags
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with UNION consolidation
- Work items: FK architecture where mem_ai_events.work_item_id links many events to one work item; mem_mrr_commits.event_id points to mem_ai_events (commit digest)
- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Database schema management: db_schema.sql as single source of truth + db_migrations.py with safe rename→recreate→copy pattern (migrations m001-m019)
- Prompt centralization via core.prompt_loader; eliminates redundant mng_system_roles database lookups; unified prompt cache for all routes
- Work item UI: multi-column sortable table (name/desc, prompts, commits, last-updated date) with drag-and-drop support and work-item-drawer detail view

## In Progress

- Work item table UI refinement: implemented multi-column sortable display (name, prompts, commits, last-updated date); fixed draggable attribute binding to match _attachWorkItemDnd expectations
- Work item counting query optimization: refactored _SQL_LIST_WORK_ITEMS_BASE to count events (event_count, prompt_count) and commits via mem_ai_events FK instead of legacy mem_mrr_* tag queries; fixed interaction_count → prompt_count field mismatch
- Database schema canonicalization: consolidated DDL into db_schema.sql with migration framework db_migrations.py (m001-m019 tracked); single source of truth for all table definitions
- Prompt loader integration: refactored route_snapshots.py and route_memory.py to use core.prompt_loader instead of direct mng_system_roles queries; eliminates redundant DB lookups
- Database query performance optimization: investigating ~60s latency in route_work_items _SQL_UNLINKED_WORK_ITEMS JOIN; need index strategy on work_item_id and event_id FK columns
- Memory embedding pipeline: tracing all LLM prompts in memory_embedding.py, agents/tools/, and routers; synchronizing mirror tables through mem_ai_events with consistent module imports

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
index be58ca5..541b82d 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Planner tag UI binding fix: resolved `catName` ReferenceError in _renderDrawer() (scope issue) and corrected field mismatch v.short_desc → v.desc for proper tag property display on left sidebar
-- Database schema canonicalization: consolidated all DDL into db_schema.sql as single source of truth with migration framework in db_migrations.py (rename → recreate → copy pattern); legacy ALTER TABLE statements now tracked as migrations m001-m017
-- Prompt loader integration: refactoring route_snapshots.py and route_memory.py to use core.prompt_loader instead of direct mng_system_roles queries to eliminate redundant database lookups
+- Planner tag UI binding fix: resolved `catName` ReferenceError in _renderDrawer() (scope issue) and corrected field mismatch v.short_desc → v.desc for proper tag display on left sidebar
+- Database schema canonicalization: consolidated all DDL into db_schema.sql with migration framework db_migrations.py (m001-m017 tracked); single source of truth for database design
+- Prompt loader integration: refactoring route_snapshots.py and route_memory.py to use core.prompt_loader instead of mng_system_roles queries; eliminates redundant DB lookups
 - Commit pipeline prompt discovery: tracing all LLM prompts in memory_embedding.py, agents/tools/, and routers for unified prompt management and cost tracking
 - Memory endpoint data flow verification: synchronizing mirror tables (mem_mrr_commits_code) through mem_ai_events and downstream memory tables with consistent module imports
-- Database query performance: investigating ~60s latency in route_work_items query (_SQL_UNLINKED_WORK_ITEMS join optimization and indexing)
+- Database query performance optimization: investigating ~60s latency in route_work_items (_SQL_UNLINKED_WORK_ITEMS join optimization and indexing needed)


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/ui/frontend/views/entities.js b/ui/frontend/views/entities.js
index 0e53749..7fc3859 100644
--- a/ui/frontend/views/entities.js
+++ b/ui/frontend/views/entities.js
@@ -899,7 +899,8 @@ async function _openWorkItemDrawer(id, catName, project, pane, catColor, catIcon
 
         <!-- Stats row -->
         <div style="display:flex;gap:0.6rem;flex-wrap:wrap;font-size:0.6rem;color:var(--muted)">
-          <span>&#128172; <span id="wi-stat-prompts-${id}">${wi.interaction_count||0} prompts</span></span>
+          <span>&#128172; <span id="wi-stat-prompts-${id}">${wi.prompt_count||0} prompts</span></span>
+          <span>&#9741; ${wi.event_count||0} events</span>
           <span id="wi-stat-words-${id}">~… words</span>
           <span>&#8859; ${wi.commit_count||0} commits</span>
           <span id="wi-stat-files-${id}"></span>


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index ca87dfb..56d249a 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -30,16 +30,19 @@ from data.dl_seq import next_seq
 # ── SQL ──────────────────────────────────────────────────────────────────────
 
 _SQL_LIST_WORK_ITEMS_BASE = (
-    """WITH pcount AS (
-         SELECT tags->>'work-item' AS wi_id, COUNT(*) AS cnt
-         FROM mem_mrr_prompts
-         WHERE project_id=%s AND tags ? 'work-item'
+    """WITH ev_count AS (
+         SELECT work_item_id::text AS wi_id,
+                COUNT(*) AS event_count,
+                COUNT(*) FILTER (WHERE event_type = 'prompt_batch') AS prompt_count
+         FROM mem_ai_events
+         WHERE project_id=%s AND work_item_id IS NOT NULL
          GROUP BY 1
        ),
-       ccount AS (
-         SELECT tags->>'work-item' AS wi_id, COUNT(*) AS cnt
-         FROM mem_mrr_commits
-         WHERE project_id=%s AND tags ? 'work-item'
+       cm_count AS (
+         SELECT e.work_item_id::text AS wi_id, COUNT(*) AS commit_count
+         FROM mem_mrr_commits c
+         JOIN mem_ai_events e ON e.id = c.event_id
+         WHERE c.project_id=%s AND e.work_item_id IS NOT NULL
          GROUP BY 1
        ),
        mcount AS (
@@ -55,13 +58,14 @@ _SQL_LIST_WORK_ITEMS_BASE = (
               w.merged_into, w.start_date,
               w.created_at, w.updated_at, w.seq_num,
               tc.color, tc.icon,
-              COALESCE(pcount.cnt, 0) AS interaction_count,
-              COALESCE(ccount.cnt, 0) AS commit_count,
+              COALESCE(ev_count.event_count,  0) AS event_count,
+              COALESCE(ev_count.prompt_count, 0) AS prompt_count,
+              COALESCE(cm_count.commit_count, 0) AS commit_count,
               COALESCE(mcount.cnt, 0) AS merge_count
        FROM mem_ai_work_items w
        LEFT JOIN mng_tags_categories tc ON tc.client_id=1 AND tc.name=w.ai_category
-       LEFT JOIN pcount ON pcount.wi_id = w.id::text
-       LEFT JOIN ccount ON ccount.wi_id = w.id::text
+       LEFT JOIN ev_count ON ev_count.wi_id = w.id::text
+       LEFT JOIN cm_count ON cm_count.wi_id = w.id::text
        LEFT JOIN mcount ON mcount.wi_id = w.id::text
        WHERE {where}
        ORDER BY w.created_at DESC
@@ -339,7 +343,7 @@ async def list_work_items(
     sql = _SQL_LIST_WORK_ITEMS_BASE.format(where=" AND ".join(where))
     with db.conn() as conn:
         with conn.cursor() as cur:
-            # 3 extra p_id params for the pcount/ccount/mcount CTEs
+            # 3 extra p_id params for the ev_count/cm_count/mcount CTEs
             cur.execute(sql, [p_id, p_id, p_id] + params + [limit])
             cols = [d[0] for d in cur.description]
             rows = []
@@ -497,6 +501,7 @@ async def extract_work_item_code(item_id: str, project: str | None = Query(None)
     return result
 
 
+
 # ── Lookup by sequential number ───────────────────────────────────────────────
 
 @router.get("/number/{seq_num}")


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/routers/route_git.py b/backend/routers/route_git.py
index dd18344..831021e 100644
--- a/backend/routers/route_git.py
+++ b/backend/routers/route_git.py
@@ -179,6 +179,8 @@ def _extract_commit_code_background(project: str, commit_hash: str) -> None:
         loop.close()
 
 
+
+
 # ── Commit→prompt linking background task ─────────────────────────────────────
 
 def _sync_commit_and_link(project: str, commit_hash: str, session_id: str | None,
@@ -1148,7 +1150,7 @@ async def commit_and_push(project_name: str, body: CommitRequest, request: Reque
             commit_author,
             commit_author_email,
         )
-        # Embed the commit (creates mem_ai_events) in background
+        # Embed the commit (creates mem_ai_events, sets event_id on commit) in background
         background.add_task(_embed_commit_background, project_name, commit_hash)
         # Tree-sitter symbol extraction → mem_mrr_commits_code in background
         background.add_task(_extract_commit_code_background, project_name, commit_hash)


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/memory/memory_promotion.py b/backend/memory/memory_promotion.py
index 04cabac..4a39098 100644
--- a/backend/memory/memory_promotion.py
+++ b/backend/memory/memory_promotion.py
@@ -658,6 +658,12 @@ class MemoryPromotion:
                             row = cur.fetchone()
                             if row:
                                 created += 1
+                                # Link event to its newly created work item
+                                wi_id = str(row[0])
+                                cur.execute(
+                                    "UPDATE mem_ai_events SET work_item_id=%s::uuid WHERE id=%s::uuid",
+                                    (wi_id, str(ev_id)),
+                                )
                             else:
                                 updated += 1  # ON CONFLICT DO UPDATE hit an existing item
                 except Exception as e:


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-09

diff --git a/backend/memory/memory_embedding.py b/backend/memory/memory_embedding.py
index 8408f0a..ef5bb81 100644
--- a/backend/memory/memory_embedding.py
+++ b/backend/memory/memory_embedding.py
@@ -448,12 +448,17 @@ class MemoryEmbedding:
             summary=summary_text, action_items=action_items, tags=digest_tags, importance=importance,
         )
 
-        # Back-propagate summary to mem_mrr_commits and set exec_llm flag
+        # Back-propagate summary + link event_id to mem_mrr_commits, set exec_llm flag
         try:
             with db.conn() as conn:
                 with conn.cursor() as cur:
                     cur.execute(_SQL_UPDATE_COMMIT_SUMMARY, (summary_text, commit_hash_val))
                     cur.execute(_SQL_SET_EXEC_LLM, (settings.haiku_model, commit_hash_val))
+                    if event_id:
+                        cur.execute(
+                            "UPDATE mem_mrr_commits SET event_id=%s::uuid WHERE commit_hash=%s",
+                            (event_id, commit_hash_val),
+                        )
         except Exception as e:
             log.debug(f"process_commit column update error: {e}")
 


## AI Synthesis

**[2026-04-09]** `route_work_items.py` — Refactored work item list query to use FK-based counting: replaced legacy mem_mrr_* tag queries with event/commit counts via mem_ai_events.work_item_id joins; fixed field names (interaction_count → prompt_count) to match frontend expectations. **[2026-04-09]** `entities.js` — Enhanced work item table UI with multi-column sortable display: name/desc, prompt_count, commit_count, and last-updated date; fixed draggable attribute binding to support drag-and-drop reordering. **[2026-04-09]** `db_migrations.py` — Established migration framework (m001-m019) with safe rename→recreate→copy pattern; consolidated all DDL into db_schema.sql as single source of truth replacing legacy ALTER TABLE statements. **[2026-04-09]** `core.prompt_loader` — Centralized prompt management module to eliminate redundant mng_system_roles database lookups; integrated into route_snapshots.py and route_memory.py. **[2026-04-09]** `route_work_items.py` — Identified ~60s latency in _SQL_UNLINKED_WORK_ITEMS query; root cause likely missing indexes on work_item_id and event_id FK columns requiring join optimization. **[2026-04-09]** `memory_embedding.py` — Traced LLM prompt pipeline across agents/tools/, routers, and memory synthesis; synchronized mirror table population (mem_mrr_commits_code) through mem_ai_events with consistent module imports.