# Project Memory — aicli
_Generated: 2026-04-03 19:28 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform providing a unified CLI and desktop interface (Electron) for multi-project AI collaboration with PostgreSQL-backed semantic search, LLM provider abstraction, and async DAG workflow execution. The project recently consolidated memory file generation to use inline planner_tags snapshot fields as the canonical data source, standardized SQL cursor handling across modules, and enhanced memory synthesis with timestamp tracking for improved data lineage and consistency.

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
index f86d459..17eac20 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -46,7 +46,7 @@
     "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients \u2192 Users with login_as_first_level_hierarchy pattern",
     "LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) \u2192 str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files",
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation",
-    "Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items",
+    "Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking",
     "_ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions",
     "Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory",
     "Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI",
@@ -120,7 +120,7 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-01T18:16:48Z",
+  "last_memory_run": "2026-04-02T09:56:40Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ contains backend logic and CLI; workspace/ contains per-project content; _system/ stores project state and memory files",
@@ -129,7 +129,7 @@
       "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients \u2192 Users with login_as_first_level_hierarchy pattern",
       "LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) \u2192 str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files",
       "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation",
-      "Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items",
+      "Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking",
       "_ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions",
       "Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory",
       "Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI",
@@ -160,11 +160,14 @@
       "memory_synthesis": "Claude Haiku dual-layer with 5 output files",
       "chunking": "Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)",
       "mcp": "Stdio MCP server with 12+ tools",
-      "deployment": "Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev",
+      "deployment_cloud": "Railway (Dockerfile + railway.toml)",
+      "deployment_desktop": "Electron-builder (Mac dmg, Windows nsis, Linux AppImage+d

### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index dbab46f..efd6376 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-02T09:56:20Z",
+  "last_updated": "2026-04-03T17:26:36Z",
   "last_session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d",
-  "last_session_ts": "2026-04-02T09:56:20Z",
-  "session_count": 340,
+  "last_session_ts": "2026-04-03T17:26:36Z",
+  "session_count": 341,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 4886da4..12bdd79 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 18:16 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-02 09:56 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -52,7 +52,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
 - LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
-- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items
+- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions
 - Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI


### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index e0de58f..8264652 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -595,3 +595,5 @@
 {"ts": "2026-04-01T18:07:18Z", "action": "commit_push", "source": "claude_cli", "session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d", "hash": "d522ddae", "message": "docs: update AI context files and trim MEMORY.md after session", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d", "hash": "0574731d", "message": "chore: sync system files and update memory/chat after claude session", "files_count": 42, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-01T18:16:36Z"}
 {"ts": "2026-04-01T18:16:27Z", "action": "commit_push", "source": "claude_cli", "session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d", "hash": "0574731d", "message": "chore: sync system files and update memory/chat after claude session", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d", "hash": "43cbb0ca", "message": "chore: update system state and memory after claude session d7be5539", "files_count": 33, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-02T09:56:28Z"}
+{"ts": "2026-04-02T09:56:20Z", "action": "commit_push", "source": "claude_cli", "session_id": "d7be5539-344e-41d1-9fde-439ba88afd8d", "hash": "43cbb0ca", "message": "chore: update system state and memory after claude session d7be5539", "pushed": true, "push_error": ""}


### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 947cf33..3ba8891 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-01 18:16 UTC by aicli /memory_
+_Generated: 2026-04-02 09:56 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining Claude CLI + desktop Electron UI with PostgreSQL semantic storage (pgvector). It unifies project memory across 5 synthesized files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) using Claude Haiku dual-layer synthesis, structured around a DAG workflow executor with provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok). Current development focuses on stabilizing memory file generation by standardizing SQL tuple unpacking and ensuring inline snapshot fields correctly populate feature context through refined planner_tags queries.
+aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to create context-aware AI assistants. It uses PostgreSQL with pgvector for semantic search, unified memory tables (mem_ai_* schema), and async DAG workflows to synthesize project memory via Claude Haiku into 5 markdown files. Currently refactoring memory file generation to standardize SQL cursor handling and consolidate feature context loading from inline planner_tags snapshots instead of fragmented relations.
 
 ## Project Facts
 
@@ -92,7 +92,7 @@ Reviewer: ```json
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
 - LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
-- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items
+- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions
 - Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
@@ -118,55 +118,52 @@ Reviewer: ```json
 ### `commit` — 2026-04-01
 
 diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
-index 0971cc1..236e955 100644
+index 236e955..958af7b 100644
 --- a/workspace/aicli/_system/project_state.json
 +++ b/workspace/aicli/_system/project_state.json
 @@ -40,21 +40,21 @@
      "deployment_local": "bash start_backend.sh + ui/npm run dev"
    },
    "key_decisions": [
--    "Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state and memory files",
-+    "Engine/workspace separation: aicli/ contains backend logic; workspace/ contains per-project content; _system/ stores project state and memory files",
-     "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)",
-     "Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cyto

### `commit` — 2026-04-03

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index df9b5a6..e1219f4 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -32,7 +32,7 @@ You are a senior Python software architect with deep expertise in:
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
 - LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
-- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items
+- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions
 - Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI


## AI Synthesis

**2026-04-02** `memory_modules` — Fixed SQL cursor tuple unpacking in memory_promotion.py and memory_files.py; _SQL_ACTIVE_TAGS query now correctly returns tag names from proper column index for reliable tag filtering. **2026-04-02** `feature_rendering` — Consolidated feature details context loading to use inline planner_tags snapshot fields (summary, action_items, design, code_summary) as primary data source instead of fragmented mem_ai_tags_relations relations. **2026-04-02** `schema_consolidation` — Removed mem_ai_tags_relations relations section from feature rendering; get_active_feature_tags() now correctly filters active/open tags with valid snapshots. **2026-04-02** `memory_synthesis` — Added timestamp tracking to memory file generation metadata; render_feature_claude_md() now reads complete tag metadata with 30-tag limit per feature for context completeness. **2026-04-01** `db_standardization` — Standardized cursor handling across memory modules with improved SQL result column ordering documentation; fixed context dict population to include id, name, short_desc, requirements, summary, action_items, design, code_summary fields.