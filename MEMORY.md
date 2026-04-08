# Project Memory — aicli
_Generated: 2026-04-08 14:47 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI with a FastAPI backend and Electron desktop UI to capture, analyze, and organize development work via semantic embeddings, multi-layer memory synthesis (ephemeral → raw → digested → work items), and intelligent workflow automation. Currently stabilizing prompt management, optimizing database query performance for work item retrieval, and debugging UI visibility of planner tag categories.

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
- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; route_snapshots and route_memory now load prompts from configuration

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

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index f5153fc..7951bce 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Database schema stabilization: commit_short_hash column added; mem_mrr_commits_code now includes all 19 columns with full_symbol properly applied via post-creation DDL
-- DDL runner robustness: investigating silent failures during initial migration caused by table locks and timing issues; generated columns now applied after base table creation
-- Commit code extraction configuration: min_lines and only_on_commits_with_tags settings added to project.yaml templates (python_api and blank)
-- Database query performance optimization: route_work_items showing ~60s latency; investigating indexing for _SQL_UNLINKED_WORK_ITEMS and join operations
-- Memory endpoint data synchronization: tracing data flow from mirror tables through mem_ai_* tables; verifying update triggers and mechanisms
-- Planner tag visibility debugging: categories uploaded but individual tags not displaying in category bindings; verifying router mapping and tag query logic
+- Commit pipeline prompt discovery: tracing all LLM prompts used in commit processing (code extraction, summarization, embedding); located in memory/memory_embedding.py, agents/tools/, and routers/route_snapshots.py
+- Memory endpoint data flow: verifying synchronization from mirror tables (mem_mrr_commits_code) through mem_ai_events and downstream memory tables; identified import migration from mem_embeddings to memory_embedding module
+- Module restructuring: consolidating embedding/ingestion logic into memory_embedding.py; updating imports across route_snapshots.py, route_search.py, route_prompts.py for consistent module paths
+- Database query performance: route_work_items showing ~60s latency; investigating indexing for _SQL_UNLINKED_WORK_ITEMS and join optimization on mem_ai_events
+- Planner tag visibility: debugging category upload and tag binding visibility in UI; verifying router mapping and category query logic
+- DDL runner robustness: investigating silent failures during initial migration caused by table locks; post-creation DDL for generated columns now handled separately from base table creation


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_snapshots.py b/backend/routers/route_snapshots.py
index 6b9a5ed..dbdc65d 100644
--- a/backend/routers/route_snapshots.py
+++ b/backend/routers/route_snapshots.py
@@ -25,6 +25,7 @@ from fastapi import APIRouter, HTTPException
 
 from core.config import settings
 from core.database import db
+from core.prompt_loader import prompts as _prompts
 
 log = logging.getLogger(__name__)
 
@@ -45,12 +46,6 @@ _SQL_GET_MEMORY_EVENTS = """
     ORDER BY me.created_at
 """
 
-_SQL_GET_SYSTEM_ROLE = """
-    SELECT content FROM mng_system_roles
-    WHERE client_id = 1 AND name = %s AND is_active = TRUE
-    LIMIT 1
-"""
-
 _SQL_UPSERT_SNAPSHOT = """
     UPDATE planner_tags SET
         summary      = %s,
@@ -167,11 +162,7 @@ async def generate_snapshot(project: str, tag_name: str):
             detail=f"No memory events found for tag '{tag_name}'. Run a few sessions first.",
         )
 
-    with db.conn() as conn:
-        with conn.cursor() as cur:
-            cur.execute(_SQL_GET_SYSTEM_ROLE, ("memory_feature_snapshot",))
-            role_row = cur.fetchone()
-    system_prompt = role_row[0] if role_row else _DEFAULT_SNAPSHOT_PROMPT
+    system_prompt = _prompts.content("feature_snapshot") or _DEFAULT_SNAPSHOT_PROMPT
 
     by_type: dict[str, list[str]] = {}
     event_ids: list[str] = []


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_memory.py b/backend/routers/route_memory.py
index 91f113b..e06143d 100644
--- a/backend/routers/route_memory.py
+++ b/backend/routers/route_memory.py
@@ -25,6 +25,7 @@ from pydantic import BaseModel
 
 from core.config import settings
 from core.database import db
+from core.prompt_loader import prompts as _prompts
 
 log = logging.getLogger(__name__)
 router = APIRouter()
@@ -39,12 +40,6 @@ _SQL_GET_SESSION_PROMPTS = """
     ORDER BY created_at
 """
 
-_SQL_GET_SYSTEM_ROLE = """
-    SELECT content FROM mng_system_roles
-    WHERE client_id=1 AND name=%s AND is_active=TRUE
-    LIMIT 1
-"""
-
 _SQL_UPSERT_SESSION_SUMMARY = """
     INSERT INTO mem_ai_events
         (project_id, event_type, source_id, session_id,
@@ -140,12 +135,7 @@ async def _generate_session_summary(
             conv_lines.append(f"Assistant: {response[:300]}")
     conv_text = "\n".join(conv_lines)
 
-    # Load synthesis prompt from DB
-    with db.conn() as conn:
-        with conn.cursor() as cur:
-            cur.execute(_SQL_GET_SYSTEM_ROLE, ("session_end_synthesis",))
-            row = cur.fetchone()
-    system_prompt = row[0] if row else (
+    system_prompt = _prompts.content("session_end_synthesis") or (
         "Analyse this development session and produce a structured summary.\n"
         "Return JSON only:\n"
         "{\n"


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_git.py b/backend/routers/route_git.py
index 007fd08..7513630 100644
--- a/backend/routers/route_git.py
+++ b/backend/routers/route_git.py
@@ -18,6 +18,7 @@ from pydantic import BaseModel
 
 from core.config import settings
 from core.database import db
+from core.prompt_loader import prompts as _prompts
 from agents.providers import call_claude
 
 log = logging.getLogger(__name__)
@@ -1307,9 +1308,7 @@ async def _generate_commit_message(
     Returns (commit_message, analysis_dict).
     Falls back to a simple chore message with empty analysis on failure.
     """
-    from pathlib import Path as _Path
-    _sys_prompt_path = _Path(settings.workspace_dir) / "_templates" / "memory" / "prompts" / "system" / "commit_analysis.md"
-    sys_prompt = _sys_prompt_path.read_text().strip() if _sys_prompt_path.exists() else ""
+    sys_prompt = _prompts.content("commit_analysis") or ""
 
     _CONVENTIONAL = ("feat", "fix", "chore", "test", "refactor", "docs", "style", "perf", "ci", "build")
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/prompts/prompts.yaml b/backend/prompts/prompts.yaml
new file mode 100644
index 0000000..b59b4f5
--- /dev/null
+++ b/backend/prompts/prompts.yaml
@@ -0,0 +1,79 @@
+# Internal system prompts — NOT exposed to users, NOT stored in DB.
+# To switch models or tune costs, change `model` or `max_tokens`.
+# Models: haiku (claude-haiku-4-5-20251001) | sonnet (claude-sonnet-4-6)
+
+prompts:
+
+  # ── Commits ────────────────────────────────────────────────────────────────
+  commit_analysis:
+    file: memory/commits/commit_analysis.md
+    model: sonnet       # needs structured JSON + code pattern recognition
+    max_tokens: 800
+
+  commit_digest:
+    file: memory/commits/commit_digest.md
+    model: haiku
+    max_tokens: 200
+
+  commit_symbol:
+    file: memory/commits/commit_symbol.md
+    model: haiku
+    max_tokens: 120
+
+  # ── Memory events ──────────────────────────────────────────────────────────
+  prompt_batch_digest:
+    file: memory/prompt_batch_digest.md
+    model: haiku
+    max_tokens: 250
+
+  item_digest:
+    file: memory/item_digest.md
+    model: haiku
+    max_tokens: 200
+
+  meeting_sections:
+    file: memory/meeting_sections.md
+    model: haiku
+    max_tokens: 1000
+
+  message_chunk_digest:
+    file: memory/message_chunk_digest.md
+    model: haiku
+    max_tokens: 200
+
+  relation_extraction:
+    file: memory/relation_extraction.md
+    model: haiku
+    max_tokens: 400
+
+  session_end_synthesis:
+    file: memory/session_end_synthesis.md
+    model: haiku
+    max_tokens: 600
+
+  # ── Work items ─────────────────────────────────────────────────────────────
+  work_item_extraction:
+    file: memory/work_items/work_item_extraction.md
+    model: haiku
+    max_tokens: 500
+
+  work_item_promotion:
+    file: memory/work_items/work_item_promotion.md
+    model: haiku
+    max_tokens: 300
+
+  # ── Feature / planner ──────────────────────────────────────────────────────
+  feature_snapshot:
+    file: memory/feature_snapshot.md
+    model: haiku
+    max_tokens: 2500
+
+  conflict_detection:
+    file: memory/conflict_detection.md
+    model: haiku
+    max_tokens: 300
+
+  planner_summary:
+    file: memory/planner/planner_summary.md
+    model: haiku
+    max_tokens: 2000


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/prompts/memory/work_items/work_item_promotion.md b/backend/prompts/memory/work_items/work_item_promotion.md
new file mode 100644
index 0000000..57410a5
--- /dev/null
+++ b/backend/prompts/memory/work_items/work_item_promotion.md
@@ -0,0 +1,4 @@
+Given a work item's name, description, lifecycle status, acceptance criteria, and implementation plan,
+produce a 2-4 sentence summary capturing: what the item is, current status, and any notable progress.
+Return JSON only: {"summary": "...", "status": "<lifecycle_status>"}
+No preamble, no markdown fences.


## AI Synthesis

**[2026-03-14]** `core/prompt_loader` — Centralized prompt management system implemented to replace redundant mng_system_roles database queries; reduces latency in memory synthesis and snapshot generation flows. **[2026-03-14]** `route_snapshots.py` — Refactored to use prompt_loader for feature_snapshot prompts; eliminates direct system role queries and improves code maintainability. **[2026-03-14]** `route_memory.py` — Updated session_end_synthesis prompt loading to use centralized prompt cache instead of database lookups. **[in-progress]** `memory_embedding.py` — Module consolidation underway to unify embedding and ingestion logic; import migrations needed across route_snapshots.py, route_search.py, and route_prompts.py. **[in-progress]** `route_work_items` — Performance investigation ongoing; ~60s latency traced to _SQL_UNLINKED_WORK_ITEMS join operations on mem_ai_events; indexing strategy in development. **[in-progress]** `planner_tags_ui` — Category upload working but individual tag bindings not displaying; router mapping and category query logic verification in progress.