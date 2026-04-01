# Project Memory — aicli
_Generated: 2026-04-01 08:27 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to enable collaborative AI-assisted development. It features dual-storage (PostgreSQL + pgvector for semantic search), unified memory tables (mem_ai_events, project_facts, work_items), async DAG workflow execution with Cytoscape visualization, and multi-provider LLM support (Claude, OpenAI, DeepSeek, Gemini, Grok) with server-side key management. Current focus is on stabilizing schema consistency, ensuring data persistence across sessions, and automating memory synthesis through Claude Haiku dual-layer processing.

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
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
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
- **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+
- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + ui/npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- Electron desktop UI: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vanilla JS frontend (no framework/bundler); Vite dev server
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
- All LLM providers as independent adapters (Claude/OpenAI/DeepSeek/Gemini/Grok); Claude Haiku for dual-layer memory synthesis; server holds API keys
- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for negotiation
- Memory synthesis: Claude Haiku dual-layer generates 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load; backend_startup_race_condition mitigated
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations (linked via row id), not in summary arrays
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements; smart chunking by per-class/function (Python/JS/TS), per-section (MD), per-file (diff)
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
- CLI: Python 3.12 + prompt_toolkit + rich; command routing via verb-noun pattern; memory endpoint template variable scoping fixed
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local dev via bash start_backend.sh + ui/npm run dev
- Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing_storage in data/provider_storage/

## In Progress

- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from unified mem_ai_* tables with timestamp tracking
- Unified event table validation: mem_ai_events consolidates embeddings and memory events; removed event_summary_tags array and deprecated metadata columns
- Data persistence validation: tags disappearing on session switch root cause traced to cache invalidation triggering DB re-load; fix ensures persistence across switches
- Schema documentation cleanup: updated project_state.json and rules.md to reflect mem_ai_* unified table naming and removed deprecated database_schema field
- Tag column schema correction: mem_ai_tags_relations table DDL fixed; database migrations applied and persistence validated across session switches
- Backend startup race condition: AiCli appearing in Recent projects but unselectable on first load; retry logic implemented for empty project list handling

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `role` — 2026-04-01

## Minor Issues (note but don't block)
- Style inconsistencies with the existing codebase
- Missing type hints on new code
- Missing docstrings on public functions
- Overly verbose variable names


### `commit` — 2026-04-01

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 4f251bf..007356b 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -378,6 +378,6 @@ All tables follow a structured naming convention:
 - Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from unified mem_ai_* tables with timestamp tracking
 - Unified event table validation: mem_ai_events consolidates embeddings and memory events; removed event_summary_tags array and deprecated metadata columns
 - Data persistence validation: tags disappearing on session switch root cause traced to cache invalidation triggering DB re-load; fix ensures persistence across switches
-- Schema documentation cleanup: updated project_state.json and rules.md to reflect mem_ai_* unified table naming and removed deprecated columns
-- Tag column schema correction: mem_ai_tags_relations table DDL fixed; database migrations applied and persistence validated
-- Backend startup race condition: AiCli appearing in Recent projects but unselectable on first load; retry logic implemented for empty project list
+- Schema documentation cleanup: updated project_state.json and rules.md to reflect mem_ai_* unified table naming and removed deprecated database_schema field
+- Tag column schema correction: mem_ai_tags_relations table DDL fixed; database migrations applied and persistence validated across session switches
+- Backend startup race condition: AiCli appearing in Recent projects but unselectable on first load; retry logic implemented for empty project list handling


### `commit` — 2026-04-01

diff --git a/MEMORY.md b/MEMORY.md
index 9ea9dc4..77fc697 100644
--- a/MEMORY.md
+++ b/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-01 02:11 UTC by aicli /memory_
+_Generated: 2026-04-01 08:25 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python/FastAPI backend, Electron desktop UI, and PostgreSQL semantic storage to enable collaborative AI-assisted development. The system synthesizes project context via Claude Haiku, executes async DAG workflows, and manages memory persistence across unified mem_ai_* tables with intelligent chunking and tagging. Current focus: solidifying data persistence across session switches, automating memory file generation, and resolving backend startup race conditions.
+aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to manage AI-assisted development workflows. It features dual-storage (PostgreSQL + pgvector for semantic search), unified memory tables (mem_ai_events, project_facts, work_items), async DAG workflow execution with Cytoscape visualization, and multi-provider LLM support (Claude, OpenAI, DeepSeek, Gemini, Grok) with server-side key management. Current focus is on stabilizing schema consistency, ensuring data persistence across sessions, and automating memory synthesis through Claude Haiku dual-layer processing.
 
 ## Project Facts
 
@@ -53,7 +53,7 @@ Reviewer: ```json
 - **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
 - **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
 - **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
-- **storage_primary**: PostgreSQL 15+ per-project schema
+- **storage_primary**: PostgreSQL 15+
 - **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
 - **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
@@ -65,7 +65,7 @@ Reviewer: ```json
 - **mcp**: Stdio MCP server with 12+ tools
 - **deployment**: Railway (Dockerfile + railway.toml); local: bash start_backend.sh + ui/npm run dev
 - **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
-- **config_management**: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
+- **config_management**: config.py with externalized settings; YAML for pipelines; pyproject.toml for IDE
 - **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
 - **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
@@ -88,27 +88,27 @@ Reviewer: ```json
 - Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) plus pe

### `role` — 2026-04-01

## Critical Issues (block approval)
- Logic bugs that will cause incorrect behaviour
- Security vulnerabilities (shell injection, path traversal, secret exposure)
- Unhandled exceptions that will crash the program
- Breaking changes to existing interfaces


### `role` — 2026-04-01

## Your Review Process

1. Read the full code before commenting — understand intent before critiquing
2. Distinguish critical issues (bugs, security) from minor suggestions (style)
3. Be specific: "line 45 uses str() instead of Path()" not "use Path objects"
4. Suggest fixes, not just problems
5. Acknowledge strengths — good code deserves recognition


### `commit` — 2026-04-01

diff --git a/CLAUDE.md b/CLAUDE.md
index 5f88b54..df95e0a 100644
--- a/CLAUDE.md
+++ b/CLAUDE.md
@@ -29,18 +29,18 @@ You are a senior Python software architect with deep expertise in:
 - Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state
 - Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) plus per-project schemas
 - Electron desktop UI: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vanilla JS frontend (no framework/bundler); Vite dev server
-- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users; login_as_first_level_hierarchy pattern
+- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
 - All LLM providers as independent adapters (Claude/OpenAI/DeepSeek/Gemini/Grok); Claude Haiku for dual-layer memory synthesis; server holds API keys
 - Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for negotiation
 - Memory synthesis: Claude Haiku dual-layer generates 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items
-- Tags stored in mem_ai_tags_relations (linked via row id), not in summary arrays; sourced from MRR when applicable; load once on project access, cache invalidation on switch
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load; backend_startup_race_condition mitigated
-- Data persistence: load_once_on_access, update_on_save pattern; tags disappearing on session switch traced to cache invalidation triggering DB re-load
+- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations (linked via row id), not in summary arrays
 - MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
 - Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements; smart chunking by per-class/function (Python/JS/TS), per-section (MD), per-file (diff)
-- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix)
-- CLI: Python 3.12 + prompt_toolkit + rich; memory endpoint template variable scoping fixed at line 1120
+- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
+- CLI: Python 3.12 + prompt_toolkit + rich; command routing via verb-noun pattern; memory endpoint template variable scoping fixed at line 1120
 - Deployment: Railway (Dockerfile + railway.toml) for cloud; local dev via bash start_backend.sh + ui/npm run dev; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
+- Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing_storage in data/provider_storage/
 
 ---
 


## AI Synthesis

**2026-04-01** `project_state.json` — Unified mem_ai_* table naming consolidated across documentation; deprecated database_schema field removed to reduce duplication with db_schema. **2026-04-01** `schema_validation` — mem_ai_tags_relations DDL corrected and migrations applied; tag persistence across session switches validated and fixed via cache invalidation fix. **2026-04-01** `project_summary` — Updated to emphasize dual-storage architecture (PostgreSQL + pgvector), unified memory tables, and multi-provider LLM support with server-side key management. **2026-03-xx** `backend_startup` — Retry logic implemented to handle empty project list on first load; AiCli now selectable immediately in Recent projects. **2026-03-xx** `data_persistence` — Root cause of tag disappearance on session switch traced to cache invalidation; fix ensures persistence across workspace switches. **2026-03-xx** `memory_synthesis` — Claude Haiku dual-layer processing configured to auto-generate 5 memory files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items with timestamp tracking.