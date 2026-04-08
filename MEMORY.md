# Project Memory — aicli
_Generated: 2026-04-08 13:52 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining Python CLI + FastAPI backend + Electron desktop UI, enabling semantic search and workflow automation across multi-project workspaces. Currently stabilizing database schema (commit tracking with mem_mrr_commits_code, 19-column structure), optimizing query performance (route_work_items latency), and resolving module consolidation for embedding pipeline consistency across routers.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **code_extraction_configuration**: min_lines: 5, only_on_commits_with_tags: false in project.yaml templates
- **commit_processing_flag**: exec_llm boolean column replaces tags->>'llm' NULL check
- **commit_tracking_schema**: mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: PostgreSQL with SQL parameter binding
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude CLI and LLM platforms
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **memory_system_update_status**: updated_with_latest_context_and_session_tags
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
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
- **rel:commit_processing:exec_llm_flag**: replaces
- **rel:memory_system:session_tags**: implements
- **rel:route_memory:sql_parameter_binding**: depends_on
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
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session messages → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts → user-managed planner_tags
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; mem_mrr_commits_code includes 19 columns with full_symbol as generated column
- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Mirror table pattern (mem_mrr_*) captures raw events; generated columns require explicit post-creation migration to avoid DDL runner silent failures

## In Progress

- Commit pipeline prompt discovery: tracing all LLM prompts used in commit processing (code extraction, summarization, embedding); located in memory/memory_embedding.py, agents/tools/, and routers/route_snapshots.py
- Memory endpoint data flow: verifying synchronization from mirror tables (mem_mrr_commits_code) through mem_ai_events and downstream memory tables; identified import migration from mem_embeddings to memory_embedding module
- Module restructuring: consolidating embedding/ingestion logic into memory_embedding.py; updating imports across route_snapshots.py, route_search.py, route_prompts.py for consistent module paths
- Database query performance: route_work_items showing ~60s latency; investigating indexing for _SQL_UNLINKED_WORK_ITEMS and join optimization on mem_ai_events
- Planner tag visibility: debugging category upload and tag binding visibility in UI; verifying router mapping and category query logic
- DDL runner robustness: investigating silent failures during initial migration caused by table locks; post-creation DDL for generated columns now handled separately from base table creation

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

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_snapshots.py b/backend/routers/route_snapshots.py
index e17dbb2..6b9a5ed 100644
--- a/backend/routers/route_snapshots.py
+++ b/backend/routers/route_snapshots.py
@@ -123,7 +123,7 @@ async def _call_sonnet(system_prompt: str, user_message: str) -> str:
 
 async def _embed_text(text: str) -> Optional[list]:
     try:
-        from memory.mem_embeddings import get_embedding
+        from memory.memory_embedding import get_embedding
         return await get_embedding(text)
     except Exception:
         return None


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_search.py b/backend/routers/route_search.py
index dd32175..d049ffd 100644
--- a/backend/routers/route_search.py
+++ b/backend/routers/route_search.py
@@ -68,7 +68,7 @@ async def semantic_search(body: SearchRequest, user=Depends(get_optional_user)):
     if not db.is_available():
         raise HTTPException(503, "PostgreSQL + pgvector required for semantic search")
 
-    from memory.mem_embeddings import semantic_search as _search
+    from memory.memory_embedding import semantic_search as _search
     project = body.project or settings.active_project or "default"
     results = await _search(
         project=project,
@@ -169,7 +169,7 @@ async def ingest(project: str = Query(""), user=Depends(get_optional_user)):
     p = project or settings.active_project or "default"
 
     async def _do_ingest():
-        from memory.mem_embeddings import ingest_history, ingest_roles
+        from memory.memory_embedding import ingest_history, ingest_roles
         h = await ingest_history(p)
         r = await ingest_roles(p)
         import logging


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_prompts.py b/backend/routers/route_prompts.py
index 2b5356d..46edb58 100644
--- a/backend/routers/route_prompts.py
+++ b/backend/routers/route_prompts.py
@@ -63,7 +63,7 @@ async def write_prompt(body: PromptWrite, project: str | None = Query(None)):
     # Embed role files for semantic search (fire-and-forget)
     if "roles/" in body.path:
         try:
-            from memory.mem_embeddings import embed_and_store as _embed
+            from memory.memory_embedding import embed_and_store as _embed
             p = project or settings.active_project or "default"
             asyncio.create_task(_embed(p, "role", body.path, body.content))
         except Exception:


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_projects.py b/backend/routers/route_projects.py
index 66db4c0..e3d9357 100644
--- a/backend/routers/route_projects.py
+++ b/backend/routers/route_projects.py
@@ -887,7 +887,7 @@ async def update_project_summary(project_name: str, body: dict = Body(...)):
     (proj_dir / "PROJECT.md").write_text(content)
     # Embed updated PROJECT.md for semantic search (fire-and-forget)
     try:
-        from memory.mem_embeddings import embed_and_store as _embed
+        from memory.memory_embedding import embed_and_store as _embed
         asyncio.create_task(_embed(project_name, "project_md", "PROJECT.md", content))
     except Exception:
         pass
@@ -1191,7 +1191,7 @@ async def _summarize_session_memory(project: str) -> int:
                             created += 1
                             # Embed into pgvector for semantic search
                             try:
-                                from memory.mem_embeddings import embed_and_store
+                                from memory.memory_embedding import embed_and_store
                                 asyncio.create_task(embed_and_store(
                                     project, "memory_item", str(row[0]), final_summary,
                                     doc_type="session_summary",
@@ -1299,7 +1299,7 @@ async def _summarize_feature_memory(project: str, work_item_id: str) -> str | No
                 memory_id = str(row[0])
                 # Embed into pgvector for semantic search
                 try:
-                    from memory.mem_embeddings import embed_and_store
+                    from memory.memory_embedding import embed_and_store
                     asyncio.create_task(embed_and_store(
                         project, "memory_item", memory_id, final_summary,
                         doc_type="feature_summary",
@@ -1994,7 +1994,7 @@ async def generate_memory(project_name: str):
 
     # ── Fire-and-forget background tasks (incremental — only process new data) ─
     try:
-        from memory.mem_embeddings import ingest_history as _ih, ingest_roles as _ir, ingest_commit as _ic
+        from memory.memory_embedding import ingest_history as _ih, ingest_roles as _ir, ingest_commit as _ic
         # Pass since=last_memory_run so only new history entries are embedded
         asyncio.create_task(_ih(project_name, since=last_memory_run))
         asyncio.create_task(_ir(project_name))  # roles: always re-embed (files may change)
@@ -2276,7 +2276,7 @@ async def _sync_and_autotag(project: str, since: str | None = None) -> None:
     Only propagates entity tags into embedding metadata (non-destructive).
     """
     try:
-        from memory.mem_embeddings import backfill_entity_tags as _bfe
+        from memory.memory_embedding import backfill_entity_tags as _bfe
         await _bfe(project)
     except Exception:
         pass


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_chat.py b/backend/routers/route_chat.py
index 60658f2..5336538 100644
--- a/backend/routers/route_chat.py
+++ b/backend/routers/route_chat.py
@@ -24,7 +24,7 @@ from core.database import db
 from agents.providers.pr_pricing import load_pricing, calculate_cost, can_user_access
 from agents.providers import call_claude, call_deepseek, call_gemini, call_grok
 from routers.route_usage import log_usage
-from memory.mem_sessions import SessionStore
+from memory.memory_sessions import SessionStore
 
 # ── SQL ─────────────────────────────────────────────────────────────────────────
 
@@ -309,7 +309,7 @@ async def _stream_response(
 
         # Fire-and-forget: embed + proactive feature detection
         try:
-            from memory.mem_embeddings import embed_and_store as _embed
+            from memory.memory_embedding import embed_and_store as _embed
             asyncio.create_task(_embed(
                 project, "history", _ts, f"Q: {message}\nA: {content}",
                 chunk_index=0, chunk_type="full",


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/pipelines/pipeline_graph_runner.py b/backend/pipelines/pipeline_graph_runner.py
index 0d4c991..642cbe9 100644
--- a/backend/pipelines/pipeline_graph_runner.py
+++ b/backend/pipelines/pipeline_graph_runner.py
@@ -943,7 +943,7 @@ def _fire_background(run_id: str, project: str) -> None:
     """
     async def _safe_embed():
         try:
-            from memory.mem_embeddings import embed_node_outputs
+            from memory.memory_embedding import embed_node_outputs
             await embed_node_outputs(run_id, project)
         except Exception as _e:
             log.debug(f"Background embed failed (non-critical): {_e}")


## AI Synthesis

**[2026-04-08]** `claude_cli` — Traced commit pipeline prompts across memory_embedding.py, agents/tools/, and route_snapshots.py; identified full flow from code extraction through LLM summarization and embedding. **[2026-04-08]** `development` — Module refactoring: consolidated embedding logic into memory_embedding.py and updated imports in route_snapshots.py, route_search.py, route_prompts.py for consistency. **[ongoing]** `infrastructure` — Database performance investigation: route_work_items experiencing ~60s latency; indexing optimization needed on _SQL_UNLINKED_WORK_ITEMS join operations. **[ongoing]** `features` — Planner tag visibility debugging: categories upload succeeds but individual tag bindings not displaying; router mapping and tag query logic under review. **[ongoing]** `database` — DDL runner stability: post-creation migration of generated columns (full_symbol) now handled separately from base table creation to prevent silent failures.