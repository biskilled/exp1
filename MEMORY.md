# Project Memory — aicli
_Generated: 2026-04-08 16:22 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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

diff --git a/aicli_memory.md b/aicli_memory.md
index 226a94a..93b57f2 100644
--- a/aicli_memory.md
+++ b/aicli_memory.md
@@ -1,404 +1,616 @@
 # aicli — Memory & Tagging Architecture
 
-_Last updated: 2026-04-07 | Updated for migration 014 + importance scoring + auto-extract pipeline_
+_Last updated: 2026-04-08 | Reflects migration 016, mem_mrr_commits_code, file-based prompt system_
 
 ---
 
 ## 0. Mental Model
 
-aicli memory has **4 active layers** stacked on top of each other.
-**planner_tags** is the user-managed top layer; everything below is LLM/trigger-managed.
+aicli memory is a **4-layer pipeline**. Data flows **down**: every raw event eventually becomes
+a structured work item. `planner_tags` sits above as the user-managed project view.
 
 ```
- ┌──────────────────────────────────────────────────────────────────────┐
- │ Layer 0 — Ephemeral         In-session message list (RAM / JSON)     │
- │ Layer 1 — Raw Capture       Everything stored as-is   (mem_mrr_*)    │
- │ Layer 2 — AI Events         Digested + embedded        (mem_ai_events)│
- │ Layer 3 — Structured        Work Items + Project Facts                │
- │ Layer 4 — User Tags         planner_tags  (USER-MANAGED)              │
- └──────────────────────────────────────────────────────────────────────┘
+ ┌──────────────────────────────────────────────────────────────────────────────┐
+ │ Layer 0 — Ephemeral     In-session message list (RAM / JSON file)            │
+ │                                                                              │
+ │ Layer 1 — Raw Capture   Everything stored verbatim         (mem_mrr_*)       │
+ │                         ├─ mem_mrr_prompts                                   │
+ │                         ├─ mem_mrr_commits  + mem_mrr_commits_code (new)     │
+ │                         ├─ mem_mrr_items                                     │
+ │                         └─ mem_mrr_messages                                  │
+ │                                                                              │
+ │ Layer 2 — AI Events     Digested + embedded                (mem_ai_events)   │
+ │                                                                              │
+ │ Layer 3 — Structured    AI-detected artifacts              (mem_ai_*)        │
+ │                         ├─ mem_ai_work_items                                 │
+ │                         └─ mem_ai_project_facts                              │
+ │                                                                              │
+ │ Layer 4 — User Tags     planner_tags   ← USER OWNS THIS                     │
+ └──────────────────────────────────────────────────────────────────────────────┘
 ```
 
-**Key design principle**:
-- `planner_tags` = **User** owns this. LLM only writes when user clicks "Run Planner" or "Snapshot".
-- Everything below `planner_tags` = **LLM + Triggers** own it. User does not manually edit.
-- `tag_id` on work items = **User** sets via drag-drop only. `ai_tag_id` = LLM suggestion (auto).
+**Ownership boundary**:
+
+| Layer | Owner | Rule |
+|-------|-------|------|
+| 0–3 | LLM + Triggers | Fully automatic. User does not manually edit. |
+| 4 | **User** | User creates/edits tags. LLM writes ONLY on explicit button click. |
+| `work_items.tag_id` | **User** | Drag-drop only. `ai_tag_id` = LLM suggestion (auto). |
+
+**Phase goal**: AI manages all data through Layer 3 (`mem_ai_work_items`). User manages Layer 4
+(`planner_tags`). Future: merge both via `tag_id` linkage.
 
 ---
 
 ## Layer 0 — Ephemeral (Session Messages)
 
-**Responsible**: Trigger (auto, no DB)
 **Storage**: `workspace/{project}/_system/sessions/{session_id}.json`
-**Python class**: `SessionStore` (`backend/memory/mem_sessions.py`)
+**Python**: `SessionStore` in `backend/memory/memory_sessions.py`
+**Trigger**: Created on first prompt; appended on each turn; never written to PostgreSQL.
 
-Not stored in PostgreSQL — file-only, short-lived within a session.
+Used only for LLM context continuity within a single session. Not searchable.
 
 ---
 
 ## Layer 1 — Raw Capture (`mem_mrr_*`)
 
-Everything stored verbatim as received. No AI processing. The audit trail.
+Everything stored verbatim. No AI processing at insert time. The audit trail.
+
+---
 
 ### `mem_mrr_prompts`
 
-**Trigger**: `post_prompt.sh` hook → `POST /memory/{p}/prompts`
+**Trigger**: `post_prompt.sh` hook → `POST /memory/{project}/prompts`
 
-| Column | Responsible | Notes |
-|--------|-------------|-------|
-| `id` UUID | Trigger | PK |
-| `session_id` | Trigger | Groups turns in a session |
-| `source_id` | Trigger | External ID from hook |
-| `prompt` TEXT | Trigger | Raw user input |
-| `response` TEXT | Trigger | Raw AI response |
-| `tags` JSONB | Trigger | `{source, phase, feature, work-item, llm}` — inline tagging |
-| `created_at` | Trigger | Insert timestamp |
+| Column | Written by | Notes |
+|--------|-----------|-------|
+| `id` UUID | Hook | PK |
+| `session_id` | Hook | Groups turns |
+| `source_id` | Hook | External hook timestamp |
+| `prompt` TEXT | Hook | Raw user input |
+| `response` TEXT | Hook | Raw AI response |
+| `tags` JSONB | Hook | `{source, phase, feature, bug, work-item, llm}` |
+| `created_at` | DB | Auto |
 
-**Relevance: 0/5** — raw data, no digest; only useful as source for Layer 2
+**Downstream trigger**: Every ~5 prompts in a session → `process_prompt_batch()` (Layer 2).
 
 ---
 
 ### `mem_mrr_commits`
 
-**Trigger**: `post_commit.sh` hook → `POST /memory/{p}/commits`
-
-| Column | Responsible | Notes |
-|--------|-------------|-------|
-| `commit_hash` | Trigger | PK |
-| `commit_msg` | Trigger | Git commit message |
-| `summary` TEXT | **LLM** (back-propagated) | Haiku digest written by `process_commit()` |
-| `tags` JSONB | Trigger + **LLM** | Initial: `{source, phase, feature}`; LLM adds `files`, `languages`, `symbols` |
-| `session_id` | Trigger | Links to session |
-| `committed_at` | Trigger | Git timestamp |
+**Trigger**: `post

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index 9913d73..c6206cb 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-08 13:52 UTC
+> Generated by aicli 2026-04-08 14:35 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 360b1e5..c4b2bc1 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 13:52 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 14:35 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.ai/rules.md b/.ai/rules.md
index 360b1e5..c4b2bc1 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 13:52 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 14:35 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

Removed legacy system files CLAUDE.md and CONTEXT.md from the repository root as they are no longer needed. This cleanup eliminates outdated documentation that may have conflicted with or duplicated information in the current documentation structure.

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

