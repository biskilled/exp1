# Project Memory — aicli
_Generated: 2026-04-08 13:46 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to capture, synthesize, and manage project knowledge across sessions using LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) and semantic search via PostgreSQL pgvector. The system uses a 4-layer memory architecture with mirror tables for raw capture, unified AI digests with embeddings, work items with dual status tracking, and user-managed tags. Currently stabilizing the database schema (mem_mrr_commits_code with 19 columns), addressing DDL runner robustness issues, and optimizing query performance for work item routes (~60s latency).

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

- Database schema stabilization: commit_short_hash column added; mem_mrr_commits_code now includes all 19 columns with full_symbol properly applied via post-creation DDL
- DDL runner robustness: investigating silent failures during initial migration caused by table locks and timing issues; generated columns now applied after base table creation
- Commit code extraction configuration: min_lines and only_on_commits_with_tags settings added to project.yaml templates (python_api and blank)
- Database query performance optimization: route_work_items showing ~60s latency; investigating indexing for _SQL_UNLINKED_WORK_ITEMS and join operations
- Memory endpoint data synchronization: tracing data flow from mirror tables through mem_ai_* tables; verifying update triggers and mechanisms
- Planner tag visibility debugging: categories uploaded but individual tags not displaying in category bindings; verifying router mapping and tag query logic

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

Removed legacy flat context files and reorganized them into feature-scoped directories to improve code organization and maintainability.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

Removed outdated CLAUDE.md and CONTEXT.md system files from the root directory to clean up stale documentation and reduce clutter in the project structure.

### `session_summary: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

Summary:
• Added `commit_short_hash` column to database schema
• `mem_mrr_commits_code` table now includes all 19 columns with `full_symbol` as a generated column
• Identified silent failure in DDL runner during initial migration - likely caused by timing issues and table locks during the first run

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/workspace/_templates/python_api/project.yaml b/workspace/_templates/python_api/project.yaml
index 9fff36c..310d1d6 100644
--- a/workspace/_templates/python_api/project.yaml
+++ b/workspace/_templates/python_api/project.yaml
@@ -5,3 +5,6 @@ default_provider: claude
 active_workflows:
   - build_feature
   - code_review
+commit_code_extraction:
+  min_lines: 5
+  only_on_commits_with_tags: false


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/workspace/_templates/blank/project.yaml b/workspace/_templates/blank/project.yaml
index 2a79137..2b98de9 100644
--- a/workspace/_templates/blank/project.yaml
+++ b/workspace/_templates/blank/project.yaml
@@ -3,3 +3,6 @@ description: "Project created from blank template"
 code_dir: "../../{{PROJECT_NAME}}"
 default_provider: claude
 active_workflows: []
+commit_code_extraction:
+  min_lines: 5
+  only_on_commits_with_tags: false


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_memory.py b/backend/routers/route_memory.py
index ea38661..91f113b 100644
--- a/backend/routers/route_memory.py
+++ b/backend/routers/route_memory.py
@@ -375,9 +375,9 @@ async def embed_commits(
 ):
     """Run process_commit() for commits that have no Haiku digest yet.
 
-    Selects commits where tags->>'llm' IS NULL (never processed), runs Haiku
-    digest + embedding for each, back-propagates summary and llm tag to
-    mem_mrr_commits. Returns count processed.
+    Selects commits where exec_llm = FALSE (never processed), runs Haiku
+    digest + embedding for each, back-propagates summary and sets exec_llm=TRUE
+    on mem_mrr_commits. Returns count processed.
     """
     if not db.is_available():
         raise HTTPException(status_code=503, detail="PostgreSQL not available")
@@ -389,7 +389,7 @@ async def embed_commits(
                 cur.execute(
                     """SELECT commit_hash FROM mem_mrr_commits
                        WHERE project_id=%s
-                         AND (tags->>'llm') IS NULL
+                         AND exec_llm = FALSE
                        ORDER BY committed_at DESC NULLS LAST
                        LIMIT %s""",
                     (project_id, limit),


## AI Synthesis

**2026-03-14** `schema` — Stabilized mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column; identified that DDL runner silently fails on initial migrations due to table locks and timing—generated columns must be applied post-creation.

**2026-03-14** `config` — Added min_lines and only_on_commits_with_tags configuration settings to project.yaml templates (python_api and blank) to control commit code extraction behavior.

**2026-03-14** `performance` — Discovered route_work_items endpoint exhibiting ~60s latency; root cause investigation underway focusing on _SQL_UNLINKED_WORK_ITEMS query indexing and join operation optimization.

**2026-03-14** `data-sync` — Tracing memory endpoint data flow from mirror tables (mem_mrr_*) through unified mem_ai_* tables; verifying update triggers and synchronization mechanisms are working correctly.

**2026-03-14** `ui-bug` — Planner tag categories uploading successfully but individual tags not displaying in category bindings; debugging router mapping and tag query logic in frontend.

**2026-03-10** `architecture` — Finalized 4-layer memory architecture: ephemeral session messages → mem_mrr_* raw capture → mem_ai_events LLM digests with embeddings → mem_ai_work_items/project_facts → user-managed planner_tags with dual status tracking (status_user, status_ai).