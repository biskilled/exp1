# Project Memory — aicli
_Generated: 2026-04-03 19:47 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI (prompt_toolkit + rich) with a FastAPI backend and Electron desktop UI (Vanilla JS + xterm.js + Monaco + Cytoscape) for AI-assisted development workflows. It uses PostgreSQL 15+ with pgvector semantic search and unified memory tables (mem_ai_events, mem_ai_project_facts, mem_ai_work_items) to synthesize 5 output memory files via Claude Haiku, supporting multi-provider LLM integration and async DAG-based workflow orchestration for teams managing complex projects.

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
- **stale_code_removed**: db_ensure_project_schema_call_replaced_with_ensure_shared_schema
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
- **llm_providers**: Claude (Haiku), OpenAI, DeepSeek, Gemini, Grok
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
- **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
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
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; organized as routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for data access, agents/tools/ (tool_ prefix) and agents/mcp/ for agent implementations
- MCP server (stdio) with 12+ tools for embedding and data retrieval; environment-configured via BACKEND_URL and ACTIVE_PROJECT
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
- Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); SQL cursor tuple unpacking standardized across memory modules
- Config management: config.py for externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/
- Memory synthesis generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking

## In Progress

- Memory file generation refactoring: feature_details context loaded from planner_tags inline fields (summary, action_items, design, code_summary); snapshot fields now primary data source for feature rendering
- Schema consolidation: mem_ai_tags_relations relations section removed from feature rendering; inline snapshot fields integrated as canonical context source across memory modules
- SQL cursor tuple unpacking standardization: memory_promotion.py and memory_files.py fixed for reliable column indexing; _SQL_ACTIVE_TAGS and _SQL_GET_CURRENT_FACTS queries corrected for 4-column unpacking
- Memory file lifecycle enhancement: get_active_feature_tags() correctly filters active/open tags with snapshots; render_feature_claude_md() reads complete tag metadata from planner_tags
- Feature details context loading: planner_tags query limits to 30 most recent tags; context dict populated with id, name, short_desc, requirements, summary, action_items, design, code_summary from inline fields
- Database cursor handling robustness: standardized tuple unpacking across memory modules with improved SQL result column ordering documentation; timestamp tracking added to memory synthesis metadata

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 17eac20..b2ca1f5 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -42,11 +42,10 @@
   "key_decisions": [
     "Engine/workspace separation: aicli/ contains backend logic and CLI; workspace/ contains per-project content; _system/ stores project state and memory files",
     "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) replace per-project fragmentation",
-    "Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development; no shared state between CLI and UI backend",
+    "Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development",
     "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients \u2192 Users with login_as_first_level_hierarchy pattern",
     "LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) \u2192 str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files",
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation",
-    "Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking",
     "_ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions",
     "Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory",
     "Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI",
@@ -54,7 +53,8 @@
     "MCP server (stdio) with 12+ tools for embedding and data retrieval; environment-configured via BACKEND_URL and ACTIVE_PROJECT",
     "Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev",
     "Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); SQL cursor tuple unpacking standardized across memory modules",
-    "Config management: config.py for externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/"
+    "Config management: config.py for externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/",
+    "Memory synthesis generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items"
   ],
   "implemented_features": [
     "5-layer memory architecture with /memory endpoint + LLM synthesis via Haiku",
@@ -120,16 +120,15 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-02T09:56:40Z",
+  "last_memory_run": "2026-04-03T17:26:57Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ contains backend logic and CLI; workspace/ contains per-project content; _system/ stores project state and memory files",
       "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations

### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index efd6376..b4a16de 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-03T17:26:36Z",
-  "last_session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d",
-  "last_session_ts": "2026-04-03T17:26:36Z",
-  "session_count": 341,
+  "last_updated": "2026-04-03T19:28:31Z",
+  "last_session_id": "6ffb562b-40dd-4aea-80a1-408ce5204f03",
+  "last_session_ts": "2026-04-03T19:28:31Z",
+  "session_count": 342,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 12bdd79..d5e45fd 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-02 09:56 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-03 17:26 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -48,11 +48,10 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 - Engine/workspace separation: aicli/ contains backend logic and CLI; workspace/ contains per-project content; _system/ stores project state and memory files
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) replace per-project fragmentation
-- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development; no shared state between CLI and UI backend
+- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
 - LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
-- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions
 - Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
@@ -61,3 +60,4 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
 - Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); SQL cursor tuple unpacking standardized across memory modules
 - Config management: config.py for externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/
+- Memory synthesis generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items


### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 8264652..19cadaf 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -597,3 +597,5 @@
 {"ts": "2026-04-01T18:16:27Z", "action": "commit_push", "source": "claude_cli", "session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d", "hash": "0574731d", "message": "chore: sync system files and update memory/chat after claude session", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d", "hash": "43cbb0ca", "message": "chore: update system state and memory after claude session d7be5539", "files_count": 33, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-02T09:56:28Z"}
 {"ts": "2026-04-02T09:56:20Z", "action": "commit_push", "source": "claude_cli", "session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d", "hash": "43cbb0ca", "message": "chore: update system state and memory after claude session d7be5539", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d", "hash": "ba6edb1d", "message": "docs: update memory and rules after claude session d7be5539", "files_count": 31, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-03T17:26:45Z"}
+{"ts": "2026-04-03T17:26:36Z", "action": "commit_push", "source": "claude_cli", "session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d", "hash": "ba6edb1d", "message": "docs: update memory and rules after claude session d7be5539", "pushed": true, "push_error": ""}


### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 3ba8891..b3b494b 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-02 09:56 UTC by aicli /memory_
+_Generated: 2026-04-03 17:26 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to create context-aware AI assistants. It uses PostgreSQL with pgvector for semantic search, unified memory tables (mem_ai_* schema), and async DAG workflows to synthesize project memory via Claude Haiku into 5 markdown files. Currently refactoring memory file generation to standardize SQL cursor handling and consolidate feature context loading from inline planner_tags snapshots instead of fragmented relations.
+aicli is a shared AI memory platform combining a Python CLI (3.12 + prompt_toolkit + rich), FastAPI backend with PostgreSQL 15+ (pgvector for semantic search), and Electron desktop UI (Vanilla JS + xterm.js + Monaco + Cytoscape). The system synthesizes project memory via Claude Haiku into 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from unified database tables, executes async DAG workflows with chat-based approval, and supports multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok). Currently stabilizing memory file generation with standardized SQL cursor handling and planner_tags inline field integration for feature context loading.
 
 ## Project Facts
 
@@ -88,11 +88,10 @@ Reviewer: ```json
 
 - Engine/workspace separation: aicli/ contains backend logic and CLI; workspace/ contains per-project content; _system/ stores project state and memory files
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) replace per-project fragmentation
-- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development; no shared state between CLI and UI backend
+- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
 - LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
-- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions
 - Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
@@ -101,6 +100,7 @@ Reviewer: ```json
 - Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
 - Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); SQL cursor tuple un

### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index e1219f4..6a0c247 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -28,11 +28,10 @@ You are a senior Python software architect with deep expertise in:
 
 - Engine/workspace separation: aicli/ contains backend logic and CLI; workspace/ contains per-project content; _system/ stores project state and memory files
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) replace per-project fragmentation
-- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development; no shared state between CLI and UI backend
+- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
 - LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
-- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions
 - Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
@@ -41,6 +40,7 @@ You are a senior Python software architect with deep expertise in:
 - Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
 - Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); SQL cursor tuple unpacking standardized across memory modules
 - Config management: config.py for externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/
+- Memory synthesis generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items
 
 ---
 


## AI Synthesis

**2026-04-03** `project_state` — Memory synthesis architecture consolidated: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md generation now tied directly to mem_ai_project_facts and mem_ai_work_items tables with timestamp tracking. **2026-04-03** `memory_modules` — SQL cursor unpacking standardized across memory_promotion.py and memory_files.py with corrected 4-column tuple handling for _SQL_ACTIVE_TAGS and _SQL_GET_CURRENT_FACTS queries. **2026-04-03** `feature_context` — Feature details loading refactored: planner_tags inline fields (summary, action_items, design, code_summary) now serve as primary context source; get_active_feature_tags() filters to 30 most recent with proper snapshot integration. **2026-04-02** `schema_consolidation` — mem_ai_tags_relations relations section removed from feature rendering; unified inline snapshot fields established as canonical context across all memory modules. **2026-04-02** `file_generation` — Memory file lifecycle enhanced with robust cursor handling; timestamp tracking added to synthesis metadata for better audit trails.