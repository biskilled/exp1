# Project Memory — aicli
_Generated: 2026-04-08 18:31 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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
- **prompt_management**: core.prompt_loader module with centralized prompt caching

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
- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; routes now load prompts from configuration

## In Progress

- Prompt loader integration: refactoring route_snapshots.py and route_memory.py to use core.prompt_loader._prompts.content() instead of direct mng_system_roles queries; eliminates redundant database lookups
- Commit pipeline prompt discovery: tracing all LLM prompts used in commit processing (code extraction, summarization, embedding) located in memory/memory_embedding.py, agents/tools/, and routers/route_snapshots.py
- Memory endpoint data flow: verifying synchronization from mirror tables (mem_mrr_commits_code) through mem_ai_events and downstream memory tables; identified import migration from mem_embeddings to memory_embedding module
- Module restructuring: consolidating embedding/ingestion logic into memory_embedding.py; updating imports across route_snapshots.py, route_search.py, route_prompts.py for consistent module paths
- Database query performance optimization: route_work_items showing ~60s latency; investigating indexing for _SQL_UNLINKED_WORK_ITEMS and join optimization on mem_ai_events
- Planner tag visibility debugging: categories upload but individual tags don't display in UI bindings; verifying router mapping and category query logic

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

diff --git a/backend/routers/route_work_items.py b/backend/routers/route_work_items.py
index 6093022..3206da2 100644
--- a/backend/routers/route_work_items.py
+++ b/backend/routers/route_work_items.py
@@ -38,10 +38,18 @@ _SQL_LIST_WORK_ITEMS_BASE = (
               w.created_at, w.updated_at, w.seq_num,
               tc.color, tc.icon,
               (SELECT COUNT(*) FROM mem_mrr_prompts p
-               WHERE p.client_id=1 AND p.tags @> jsonb_build_object('work-item', w.id::text)) AS interaction_count,
+               WHERE p.project_id=w.project_id AND p.tags @> jsonb_build_object('work-item', w.id::text)) AS interaction_count,
               (SELECT COUNT(*) FROM mem_mrr_commits c
                WHERE c.project_id=w.project_id AND c.tags @> jsonb_build_object('work-item', w.id::text)) AS commit_count,
-              (SELECT COUNT(*) FROM mem_ai_work_items src WHERE src.merged_into = w.id) AS merge_count
+              (SELECT COUNT(*) FROM mem_ai_work_items src WHERE src.merged_into = w.id) AS merge_count,
+              (SELECT COALESCE(SUM(cc.rows_added), 0)
+               FROM mem_mrr_commits_code cc
+               JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
+               WHERE c.project_id=w.project_id AND c.tags @> jsonb_build_object('work-item', w.id::text)) AS rows_added,
+              (SELECT COALESCE(SUM(cc.rows_removed), 0)
+               FROM mem_mrr_commits_code cc
+               JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
+               WHERE c.project_id=w.project_id AND c.tags @> jsonb_build_object('work-item', w.id::text)) AS rows_removed
        FROM mem_ai_work_items w
        LEFT JOIN mng_tags_categories tc ON tc.client_id=1 AND tc.name=w.ai_category
        WHERE {where}
@@ -111,6 +119,39 @@ _SQL_GET_INTERACTIONS = (
        ORDER BY i.created_at DESC LIMIT %s"""
 )
 
+_SQL_WORK_ITEM_STATS = """
+    SELECT
+        (SELECT COUNT(*) FROM mem_mrr_prompts p
+         WHERE p.project_id=%s AND p.tags @> jsonb_build_object('work-item', %s)) AS prompt_count,
+        (SELECT COUNT(*) FROM mem_mrr_commits c
+         WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)) AS commit_count,
+        (SELECT COUNT(DISTINCT cc.file_path)
+         FROM mem_mrr_commits_code cc
+         JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
+         WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)) AS files_changed,
+        (SELECT COALESCE(SUM(cc.rows_added), 0)
+         FROM mem_mrr_commits_code cc
+         JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
+         WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)) AS rows_added,
+        (SELECT COALESCE(SUM(cc.rows_removed), 0)
+         FROM mem_mrr_commits_code cc
+         JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
+         WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)) AS rows_removed,
+        (SELECT COUNT(DISTINCT cc.full_symbol)
+         FROM mem_mrr_commits_code cc
+         JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
+         WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)
+           AND cc.full_symbol IS NOT NULL) AS symbols_changed,
+        (SELECT jsonb_object_agg(lang, cnt) FROM (
+            SELECT cc.file_language AS lang, COUNT(*) AS cnt
+            FROM mem_mrr_commits_code cc
+            JOIN mem_mrr_commits c ON c.commit_hash = cc.commit_hash
+            WHERE c.project_id=%s AND c.tags @> jsonb_build_object('work-item', %s)
+              AND cc.file_language != ''
+            GROUP BY cc.file_language
+         ) t) AS languages
+"""
+
 _SQL_GET_FACTS = (
     """SELECT id, fact_key, fact_value, valid_from
        FROM mem_ai_project_facts
@@ -630,6 +671,35 @@ async def get_work_item_commits(
     return {"commits": rows, "work_item_id": item_id, "project": p}
 
 
+# ── Per-work-item statistics ──────────────────────────────────────────────────
+
+@router.get("/{item_id}/stats")
+async def get_work_item_stats(
+    item_id: str,
+    project: str | None = Query(None),
+):
+    """Return aggregated stats for a work item: prompt count, commit count,
+    files/rows changed, symbols touched, and languages breakdown.
+
+    All stats are derived from mem_mrr_commits and mem_mrr_commits_code rows
+    tagged with 'work-item': item_id.
+    """
+    _require_db()
+    p = _project(project)
+    p_id = db.get_or_create_project_id(p)
+    # Each placeholder pair (project_id, item_id) repeated 7 times for 7 subqueries
+    params = (p_id, item_id) * 7
+    with db.conn() as conn:
+        with conn.cursor() as cur:
+            cur.execute(_SQL_WORK_ITEM_STATS, params)
+            cols = [d[0] for d in cur.description]
+            row = cur.fetchone()
+    if not row:
+        return {"work_item_id": item_id, "project": p, "stats": {}}
+    stats = dict(zip(cols, row))
+    return {"work_item_id": item_id, "project": p, "stats": stats}
+
+
 # ── Semantic search ───────────────────────────────────────────────────────────
 
 @router.get("/search")


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 33a518a..2525e65 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-08 16:22 UTC
+> Generated by aicli 2026-04-08 17:20 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -61,4 +61,4 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
-- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; route_snapshots and route_memory now load prompts from configuration
\ No newline at end of file
+- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; routes now load prompts from configuration
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index b26856b..9305460 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 16:22 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 17:20 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -61,7 +61,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
-- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; route_snapshots and route_memory now load prompts from configuration
+- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; routes now load prompts from configuration
 
 ## Recent Context (last 5 changes)
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.ai/rules.md b/.ai/rules.md
index b26856b..9305460 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 16:22 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 17:20 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -61,7 +61,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
 - Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
-- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; route_snapshots and route_memory now load prompts from configuration
+- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; routes now load prompts from configuration
 
 ## Recent Context (last 5 changes)
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

Removed outdated auto-generated system context files from aicli project to clean up codebase and reduce clutter.

### `commit` — 2026-04-08

diff --git a/workspace/aicli/project.yaml b/workspace/aicli/project.yaml
index 198132e..6275e50 100644
--- a/workspace/aicli/project.yaml
+++ b/workspace/aicli/project.yaml
@@ -12,3 +12,7 @@ git_username: biskilled
 github_client_id: Ov23ligfv0f2DBdvRdim
 github_repo: https://github.com/biskilled/exp1.git
 name: aicli
+commit_code_extraction:
+  min_lines: 5              # per-symbol llm_summary threshold
+  min_diff_lines: 5         # skip all LLM calls for commits with fewer total changed lines
+  only_on_commits_with_tags: false

