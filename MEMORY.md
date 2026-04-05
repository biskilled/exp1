# Project Memory — aicli
_Generated: 2026-04-05 11:02 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI with PostgreSQL/pgvector storage. It provides LLM-powered workflow execution via async DAG pipelines, memory synthesis using Claude Haiku, and semantic search across unified mem_ai_* tables, supporting multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) with JWT authentication and MCP tool integration. Recent work has focused on stabilizing memory file generation through planner_tags snapshot integration and standardizing database cursor handling for robust context synthesis.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: SQL
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude_CLI_and_LLM_platforms
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
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
- **storage_primary**: PostgreSQL 15+
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
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
- **deployment_local**: bash start_backend.sh + ui/npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic and CLI; workspace/ contains per-project content; _system/ stores project state and memory files
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) replace per-project fragmentation
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; organized as routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for data access
- MCP server (stdio) with 12+ tools for embedding and data retrieval; environment-configured via BACKEND_URL and ACTIVE_PROJECT
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop; local via bash start_backend.sh + ui/npm run dev
- Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); SQL cursor tuple unpacking standardized
- Config management: config.py for externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
- Cost tracking via provider_costs.json with fallback pricing; billing storage in data/provider_storage/ with rich table output

## In Progress

- Memory file generation refactoring: planner_tags inline fields now canonical context source; snapshot fields integrated across memory modules for reliable synthesis
- SQL cursor tuple unpacking standardization: memory_promotion.py and memory_files.py fixed for robust 4-column unpacking; _SQL_ACTIVE_TAGS and _SQL_GET_CURRENT_FACTS corrected
- Feature details context loading: planner_tags query optimized to 30 most recent; render_feature_claude_md() reads complete tag metadata from inline snapshot fields
- Memory file lifecycle enhancement: get_active_feature_tags() filters active/open tags with snapshots; context dict populated with id, name, short_desc, requirements, summary, action_items, design, code_summary
- Database cursor handling robustness: standardized tuple unpacking with improved SQL result column ordering; timestamp tracking added to memory synthesis metadata
- Backend refactoring and cleanup: routers and core modules restructured; dev_runtime_state.json and commit logs updated after session 5b19c863

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index c5cc214..1e28815 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-03-18T12:41:57Z",
+  "last_updated": "2026-03-18T12:42:04Z",
   "last_session_id": "5b19c863-f99a-439c-b595-b415d0d342ed",
-  "last_session_ts": "2026-03-18T12:41:57Z",
-  "session_count": 128,
+  "last_session_ts": "2026-03-18T12:42:04Z",
+  "session_count": 129,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 6837faa..b485bc4 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -207,3 +207,5 @@
 {"ts": "2026-03-18T11:53:09Z", "action": "commit_push", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "hash": "dabf6d48", "message": "chore: clear aicli system state after session 5b19c863", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "hash": "5d2afe58", "message": "feat: refactor backend core and routers with improved structure", "files_count": 32, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-18T12:41:50Z"}
 {"ts": "2026-03-18T12:41:47Z", "action": "commit_push", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "hash": "5d2afe58", "message": "feat: refactor backend core and routers with improved structure", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "hash": "bde6bc20", "message": "chore: clean up aicli system files after claude session", "files_count": 26, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-18T12:42:00Z"}
+{"ts": "2026-03-18T12:41:56Z", "action": "commit_push", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "hash": "bde6bc20", "message": "chore: clean up aicli system files after claude session", "pushed": true, "push_error": ""}


### `commit` — 2026-04-03

Commit: chore: clean up aicli system files after claude session 5b19c863
Hash: 6596579f
Files changed (2):
  - workspace/aicli/_system/commit_log.jsonl
  - workspace/aicli/_system/dev_runtime_state.json

### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/history.jsonl b/workspace/aicli/_system/history.jsonl
index f609d20..8a08267 100644
--- a/workspace/aicli/_system/history.jsonl
+++ b/workspace/aicli/_system/history.jsonl
@@ -66,3 +66,4 @@
 {"ts": "2026-03-18T10:46:16Z", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "provider": "claude", "user_input": "looks better. why memory_items and project_facts are under systeme managament tables? there are not part of project ?", "output": "All endpoints working. Let me update MEMORY.md to reflect the final table structure:", "user": null, "feature": null, "tags": [], "stop_reason": "end_turn"}
 {"ts": "2026-03-18T11:51:51Z", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "provider": "claude", "user_input": "I do see the table mng_session_tags, I also see session_tags.json file at the project workspace - is it in used , what is it for ?", "output": "Everything is working. Here's the final state:\n\n**Database \u2014 24 tables, clean split:**\n\n| Prefix | Count | Tables |\n|--------|-------|--------|\n| `mng_` | 14 | Global config: users, billing, entity taxonomy, graph workflows, agent roles |\n| `pr_local_aicli_` | 10 | Project data: commits, events, embeddings, event_tags, event_links, **work_items, interactions, interaction_tags, memory_items, project_facts** |\n\n**Code changes made:**\n- `database.py` \u2014 DDL for the 5 memory tables moved from `_ensure_schema()` \u2192 `ensure_project_schema()` (created per-project on first access)\n- `work_items.py`, `projects.py`, `chat.py`, `entities.py`, `work_item_pipeline.py`, `migrate_to_memory_layers.py` \u2014 all replaced hardcoded `mng_*` names with `db.project_table(\"work_items\", p)` etc. computed dynamically\n\nThe split is now semantically correct: `mng_` is truly global configuration, `pr_` is per-project data.", "user": null, "feature": null, "tags": [], "stop_reason": "end_turn"}
 {"ts": "2026-03-18T12:00:53Z", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "provider": "claude", "user_input": "clean that up . also I do remember there was graph support for memroy usage, but I dont see any record in. how graph tables are used in the app, who suppose to manage that? this is not suppose to be at client level ?", "output": "All endpoints working correctly. Here's a summary of everything done:\n\n**All `mng_graph_*` references eliminated** across 4 files:\n\n| File | Changes |\n|------|---------|\n| `routers/graph_workflows.py` | Added `project: str = Query(\"\")` to 12 endpoints; all `mng_graph_*` \u2192 `db.project_table()` |\n| `core/graph_runner.py` | Added `tbl_g*` vars in `_execute_node`, `run_graph_workflow`, `resume_graph_workflow` |\n| `routers/work_items.py` | Added graph table vars in `run_pipeline` + `_ensure_pipeline_workflow`; fixed 2 typos (`VALUES...)f\"` \u2192 `VALUES...)\"`)|\n| `core/embeddings.py` | `tbl_gnr = db.project_table(...)` in `embed_node_outputs` |\n| `core/database.py` | Rewrote graph DDL: UUID PKs, correct column names (`position_x/y`, `role_file`, `role_prompt`, `inject_context`, etc.); `agent_run_id UUID` (no broken FK) |\n\nBackend starts clean, all endpoints return 200.", "user": null, "feature": null, "tags": [], "stop_reason": "end_turn"}
+{"ts": "2026-03-18T12:51:11Z", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "provider": "claude", "user_input": "I would like to make sure the client table are also aligned - for example mng_session_tags - is related to client (that can have multiple projects) also entitiy is per client. currently, as I am testing there is only one client (local), but the goal is to have registered paid clients. all cleint table will start with cl_ for example mng_session_tags which is related to all tags for client local will be called cl_local_session_tags. I would like to have 3 layers - general managmenet tables (mng), per client table (client can have multip

### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 1e28815..aebdda7 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-03-18T12:42:04Z",
-  "last_session_id": "5b19c863-f99a-439c-b595-b415d0d342ed",
-  "last_session_ts": "2026-03-18T12:42:04Z",
-  "session_count": 129,
+  "last_updated": "2026-03-18T13:45:25Z",
+  "last_session_id": "f69836d1-1f44-4838-867f-55ffd5a2cacc",
+  "last_session_ts": "2026-03-18T13:45:25Z",
+  "session_count": 130,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index b485bc4..07c3064 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -209,3 +209,5 @@
 {"ts": "2026-03-18T12:41:47Z", "action": "commit_push", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "hash": "5d2afe58", "message": "feat: refactor backend core and routers with improved structure", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "hash": "bde6bc20", "message": "chore: clean up aicli system files after claude session", "files_count": 26, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-18T12:42:00Z"}
 {"ts": "2026-03-18T12:41:56Z", "action": "commit_push", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "hash": "bde6bc20", "message": "chore: clean up aicli system files after claude session", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "hash": "6596579f", "message": "chore: clean up aicli system files after claude session 5b19c863", "files_count": 26, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-03-18T12:42:07Z"}
+{"ts": "2026-03-18T12:42:04Z", "action": "commit_push", "source": "claude_cli", "session_id": "5b19c863-f99a-439c-b595-b415d0d342ed", "hash": "6596579f", "message": "chore: clean up aicli system files after claude session 5b19c863", "pushed": true, "push_error": ""}


## AI Synthesis

**2026-03-18** `claude_cli` — Refactored backend core and routers with improved module structure (commit 5d2afe58); standardized SQL cursor tuple unpacking across memory_promotion.py and memory_files.py for robust 4-column result handling. **2026-03-18** `claude_cli` — Integrated planner_tags inline snapshot fields (summary, action_items, design, code_summary) as canonical context source for memory file generation; enhanced render_feature_claude_md() to read complete metadata. **2026-03-18** `claude_cli` — Optimized get_active_feature_tags() to filter active/open tags with snapshots; context dict now populated with id, name, short_desc, requirements, summary, action_items, design, code_summary for feature details loading. **2026-03-18** `claude_cli` — Added timestamp tracking to memory synthesis metadata; improved SQL result column ordering for memory file lifecycle reliability. **2026-03-18** `claude_cli` — Cleaned up aicli system files post-session; dev_runtime_state.json updated to session 129 with latest timestamps and commit logs synchronized (commit bde6bc20).