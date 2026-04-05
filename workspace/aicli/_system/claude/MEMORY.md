# Project Memory — aicli
_Generated: 2026-04-05 11:14 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that synthesizes development context across projects using Claude Haiku, storing semantic embeddings in PostgreSQL with pgvector. It provides a Python CLI, FastAPI backend, and Electron desktop UI with async DAG workflows, multi-LLM support (Claude/OpenAI/DeepSeek/Gemini/Grok), and memory files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) auto-generated from planner tags. Currently in session 345, the project is focused on stabilizing memory file generation through standardized SQL cursor handling and canonical inline field sourcing.

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

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables replace per-project fragmentation
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Claude Haiku dual-layer memory synthesis generating 5 files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md with timestamp tracking
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list preventing startup race conditions
- Data persistence: load_once_on_access, update_on_save pattern; tags in mem_ai_tags_relations with row ID linking
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Backend: FastAPI + uvicorn; routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for access, agents/ for tools and MCP
- MCP server (stdio) with 12+ tools for embedding and data retrieval; environment-configured via BACKEND_URL and ACTIVE_PROJECT
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev
- Memory file generation reads inline planner_tags fields (summary, action_items, design, code_summary); SQL cursor tuple unpacking standardized
- Config management: config.py for settings, YAML for pipeline definitions, pyproject.toml for IDE; cost tracking via provider_costs.json with fallback pricing

## In Progress

- Memory file generation refactoring: planner_tags inline fields established as canonical context source; snapshot fields integrated across memory modules for reliable synthesis
- SQL cursor tuple unpacking standardization: memory_promotion.py and memory_files.py fixed for robust 4-column unpacking; _SQL_ACTIVE_TAGS and _SQL_GET_CURRENT_FACTS corrected
- Feature details context loading: planner_tags query optimized to 30 most recent; render_feature_claude_md() reads complete tag metadata from inline snapshot fields
- Memory file lifecycle enhancement: get_active_feature_tags() filters active/open tags with snapshots; context dict populated with id, name, short_desc, requirements, summary, action_items, design, code_summary
- Database cursor handling robustness: standardized tuple unpacking with improved SQL result column ordering; timestamp tracking added to memory synthesis metadata
- Backend refactoring and cleanup: routers and core modules restructured; dev_runtime_state.json and commit logs updated; session count now 345

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index fb14048..bcea0cc 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -12,10 +12,10 @@
     "storage_semantic": "PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)",
     "db_schema": "Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles",
     "authentication": "JWT (python-jose + bcrypt) + DEV_MODE toggle",
-    "llm_providers": "Claude (Haiku), OpenAI, DeepSeek, Gemini, Grok",
+    "llm_providers": "Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok",
     "workflow_engine": "Async DAG executor (asyncio.gather) + YAML config",
     "workflow_ui": "Cytoscape.js + cytoscape-dagre; 2-pane approval panel",
-    "memory_synthesis": "Claude Haiku dual-layer with 5 output files + timestamp tracking",
+    "memory_synthesis": "Claude Haiku dual-layer with 5 output files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) + timestamp tracking",
     "chunking": "Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)",
     "mcp": "Stdio MCP server with 12+ tools",
     "deployment": "Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev",
@@ -25,7 +25,7 @@
     "llm_provider_adapters": "agents/providers/ with pr_ prefix for pricing and provider implementations",
     "pipeline_engine": "Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix",
     "pipeline_ui": "Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation",
-    "billing_storage": "data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables",
+    "billing_storage": "data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables",
     "backend_modules": "routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server",
     "dev_environment": "PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root",
     "database": "PostgreSQL 15+",
@@ -44,17 +44,17 @@
     "Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) replace per-project fragmentation",
     "Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development",
     "JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients \u2192 Users with login_as_first_level_hierarchy pattern",
-    "LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) \u2192 str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files",
+    "LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) \u2192 str contract; Claude Haiku for dual-layer memory synthesis",
     "Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation",
     "_ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions",
-    "Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory",
+    "Data persistence: loa

### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index 81fc788..fd30f4a 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-03T20:07:29Z",
+  "last_updated": "2026-04-05T11:02:33Z",
   "last_session_id": "6ffb562b-40dd-4aea-80a1-408ce5204f03",
-  "last_session_ts": "2026-04-03T20:07:29Z",
-  "session_count": 344,
+  "last_session_ts": "2026-04-05T11:02:33Z",
+  "session_count": 345,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 4a6bf52..c5a7350 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-03 19:47 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-03 20:07 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -17,10 +17,10 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
 - **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
-- **llm_providers**: Claude (Haiku), OpenAI, DeepSeek, Gemini, Grok
+- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
 - **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
-- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking
+- **memory_synthesis**: Claude Haiku dual-layer with 5 output files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) + timestamp tracking
 - **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
 - **mcp**: Stdio MCP server with 12+ tools
 - **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
@@ -30,7 +30,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
 - **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
 - **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
-- **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
+- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
 - **database**: PostgreSQL 15+
@@ -50,14 +50,14 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) replace per-project fragmentation
 - Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
-- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files
+- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing start

### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index db5701c..df3d6ba 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -603,3 +603,5 @@
 {"ts": "2026-04-03T19:28:31Z", "action": "commit_push", "source": "claude_cli", "session_id": "6ffb562b-40dd-4aea-80a1-408ce5204f03", "hash": "bf2c52b8", "message": "chore: update system files and memory after claude session 6ffb562b", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "6ffb562b-40dd-4aea-80a1-408ce5204f03", "hash": "41bdb6bf", "message": "chore: update system state and session artifacts after cli session", "files_count": 37, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-03T19:48:05Z"}
 {"ts": "2026-04-03T19:47:58Z", "action": "commit_push", "source": "claude_cli", "session_id": "6ffb562b-40dd-4aea-80a1-408ce5204f03", "hash": "41bdb6bf", "message": "chore: update system state and session artifacts after cli session", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "6ffb562b-40dd-4aea-80a1-408ce5204f03", "hash": "25c29556", "message": "chore: update system context and session state after cli session", "files_count": 34, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-03T20:07:38Z"}
+{"ts": "2026-04-03T20:07:29Z", "action": "commit_push", "source": "claude_cli", "session_id": "6ffb562b-40dd-4aea-80a1-408ce5204f03", "hash": "25c29556", "message": "chore: update system context and session state after cli session", "pushed": true, "push_error": ""}


### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index fe4cb75..9459ca4 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-03 19:47 UTC by aicli /memory_
+_Generated: 2026-04-03 20:07 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python CLI (prompt_toolkit + rich) with a FastAPI backend and Electron desktop UI (Vanilla JS + xterm.js + Monaco + Cytoscape) for AI-assisted development workflows. It uses PostgreSQL 15+ with pgvector semantic search and unified memory tables (mem_ai_events, mem_ai_project_facts, mem_ai_work_items) to synthesize 5 output memory files via Claude Haiku, supporting multi-provider LLM integration and async DAG-based workflow orchestration for teams managing complex projects.
+aicli is a shared AI memory platform combining Claude CLI, FastAPI backend, Electron desktop UI, and PostgreSQL with pgvector for semantic search. It synthesizes project context into memory files (CLAUDE.md, MEMORY.md, etc.) via async DAG workflows, supporting multiple LLM providers with cost tracking and hierarchical user authentication. Currently refactoring memory generation to use inline planner_tags snapshot fields as canonical context, standardizing SQL cursor handling, and consolidating schema across unified tables.
 
 ## Project Facts
 
@@ -57,10 +57,10 @@ Reviewer: ```json
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
 - **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
-- **llm_providers**: Claude (Haiku), OpenAI, DeepSeek, Gemini, Grok
+- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
 - **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
-- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking
+- **memory_synthesis**: Claude Haiku dual-layer with 5 output files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) + timestamp tracking
 - **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
 - **mcp**: Stdio MCP server with 12+ tools
 - **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
@@ -70,7 +70,7 @@ Reviewer: ```json
 - **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
 - **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
 - **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
-- **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
+- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
 - **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
 - **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
 - **database**: PostgreSQL 15+
@@ -90,26 +90,26 @@ Reviewer: ```json
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_f

### `commit` — 2026-04-05

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index 77974b7..f9ff69c 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -30,17 +30,17 @@ You are a senior Python software architect with deep expertise in:
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) replace per-project fragmentation
 - Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
 - JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
-- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files
+- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions
-- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory
+- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
-- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; organized as routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for data access, agents/tools/ (tool_ prefix) and agents/mcp/ for agent implementations
+- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; organized as routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for data access
 - MCP server (stdio) with 12+ tools for embedding and data retrieval; environment-configured via BACKEND_URL and ACTIVE_PROJECT
-- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
-- Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); SQL cursor tuple unpacking standardized across memory modules
-- Config management: config.py for externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/
-- Memory synthesis generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
+- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop; local via bash start_backend.sh + ui/npm run dev
+- Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); SQL cursor tuple unpacking standardized
+- Config management: config.py for externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
+- Cost tracking via provider_costs.json with fallback pricing; billing storage in data/provider_storage/ with rich table output
 
 ---
 


## AI Synthesis

**2026-04-05** `session_345` — Memory file generation refactoring complete: planner_tags inline fields (summary, action_items, design, code_summary) now canonical context source with snapshot field integration across all memory modules. **2026-04-05** `backend` — SQL cursor tuple unpacking standardized across memory_promotion.py and memory_files.py with robust 4-column unpacking; _SQL_ACTIVE_TAGS and _SQL_GET_CURRENT_FACTS corrected for reliable data retrieval. **2026-04-05** `features` — Feature details context loading optimized: planner_tags query limited to 30 most recent; render_feature_claude_md() reads complete tag metadata from inline snapshot fields with full context dict (id, name, short_desc, requirements, summary, action_items, design, code_summary). **2026-04-05** `memory_lifecycle` — Memory file lifecycle enhanced via get_active_feature_tags() filtering active/open tags with snapshots; timestamp tracking added to memory synthesis metadata for better audit trail. **2026-04-03** `database_robustness` — Database cursor handling improved with standardized tuple unpacking and better SQL result column ordering; prevents data loss on session switches. **2026-03-14** `deployment` — Full deployment pipeline established: Railway (cloud), Electron-builder (desktop multi-platform), local development via bash + npm; dev_runtime_state.json tracking session history (345 total sessions).