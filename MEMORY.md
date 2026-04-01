# Project Memory — aicli
_Generated: 2026-04-01 18:07 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python 3.12 CLI, FastAPI backend, and Electron desktop UI for managing AI-assisted development workflows. It unifies project facts, work items, and events in PostgreSQL with semantic search via pgvector, supporting multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) through independent provider adapters. Current development focuses on solidifying memory file auto-generation with proper snapshot data integration, fixing SQL cursor handling across memory modules, and ensuring reliable data persistence for feature tags across session switches.

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
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development; no shared state between CLI and UI backend
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract; Claude Haiku for dual-layer memory synthesis generating 5 output files
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load preventing startup race conditions
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking; per-feature CLAUDE.md auto-loaded when entering features/{tag}/ directory
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; organized as routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for data access, agents/tools/ (tool_ prefix) and agents/mcp/ for agent implementations
- MCP server (stdio) with 12+ tools for embedding and data retrieval; environment-configured via BACKEND_URL and ACTIVE_PROJECT
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
- Config management: config.py for externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/
- Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); SQL cursor tuple unpacking standardized across memory modules

## In Progress

- Memory file generation refactoring: feature_details context loaded from planner_tags inline fields; _SQL_ACTIVE_TAGS query fixed to return tag names from correct column index; per-feature CLAUDE.md rendering improved with snapshot data integration
- Schema consolidation: mem_ai_tags_relations relations section removed from feature rendering; inline snapshot fields now primary data source for feature details context
- SQL cursor tuple unpacking standardization: memory_promotion.py _SQL_GET_CURRENT_FACTS fixed to unpack 4 columns instead of 5; memory_files.py active tags query corrected for reliable tag filtering
- Memory file lifecycle enhancement: get_active_feature_tags() now correctly filters active/open tags with snapshots; render_feature_claude_md() reads complete tag metadata from planner_tags
- Feature details context loading: planner_tags query limits to 30 most recent tags; context dict populated with id, name, short_desc, requirements, summary, action_items, design, code_summary
- Database cursor handling robustness: standardized tuple unpacking across memory_promotion.py and memory_files.py with improved SQL result column ordering documentation

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/aicli/context.md b/workspace/aicli/_system/aicli/context.md
index 2862c00..9165d29 100644
--- a/workspace/aicli/_system/aicli/context.md
+++ b/workspace/aicli/_system/aicli/context.md
@@ -1,7 +1,7 @@
 [Project Facts] auth_pattern=login_as_first_level_hierarchy; backend_startup_race_condition_fix=retry_logic_handles_empty_project_list_on_first_load; data_model_hierarchy=clients_contain_multiple_users; data_persistence_issue=tags_disappear_on_session_switch; db_engine=SQL; db_schema_method_convention=_ensure_shared_schema_replaces_ensure_project_schema
 
 [PROJECT CONTEXT: aicli]
-aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to provide LLM-integrated project memory management. It uses PostgreSQL with pgvector for semantic search, unified event/fact/work-item tables, and supports multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) with Claude Haiku for dual-layer memory synthesis. Current focus is on stabilizing unified database schema, fixing data persistence bugs, and auto-generating memory documentation files with proper timestamp tracking.
+aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI for managing AI-assisted development workflows. The system unifies project facts, work items, and events in PostgreSQL with semantic search via pgvector, supporting multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) through provider adapters. Current development focuses on solidifying the unified database schema (mem_ai_* tables), fixing data persistence bugs across session switches, and ensuring reliable memory synthesis from project facts.
 Stack: cli=Python 3.12 + prompt_toolkit + rich, backend=FastAPI + uvicorn + python-jose + bcrypt + psycopg2, frontend=Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server, ui_components=xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre, storage_primary=PostgreSQL 15+
-In progress: Memory file auto-generation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md fully regenerated with timestamp tracking from mem_ai_project_facts and mem_ai_work_items (last run 2026-04-01T13:58:46Z), Unified event table consolidation: mem_ai_events schema validated; deprecated event_summary_tags array and metadata columns removed; data persistence across session switches confirmed, Backend startup race condition resolved: retry logic implemented to handle empty project list on first load, preventing AiCli project from appearing unselectable in Recent
+In progress: Memory file auto-generation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md fully regenerated with timestamp tracking from mem_ai_project_facts and mem_ai_work_items (last run 2026-04-01T15:35:11Z), Unified event table consolidation: mem_ai_events schema validated; deprecated event_summary_tags array and metadata columns removed; data persistence across session switches confirmed, Backend startup race condition resolved: retry logic implemented to handle empty project list on first load, preventing AiCli project from appearing unselectable in Recent
 Decisions: Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state and memory files; Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features); Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
\ No newline at end of file


### `commit` — 2026-04-01

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index a5a7350..e8985fe 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -21,7 +21,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - workflow_engine: Async DAG executor (asyncio.gather) + YAML config
 - workflow_ui: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
 - memory_synthesis: Claude Haiku dual-layer with 5 output files
-- chunking: Smart chunking: per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
+- chunking: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
 - mcp: Stdio MCP server with 12+ tools
 - deployment: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
 - database_schema: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
@@ -58,6 +58,6 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - MCP server (stdio) with 12+ tools configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations (depends_on, relates_to, blocks, implements) via CLI/admin UI
 - Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
-- CLI: Python 3.12 + prompt_toolkit + rich with verb-noun command routing; memory endpoint template variable scoping fixed
+- CLI: Python 3.12 + prompt_toolkit + rich with verb-noun command routing; memory endpoint template variable scoping fixed at line 1120
 - Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
 - Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/
\ No newline at end of file


### `role` — 2026-04-01

## Your Principles

- **Simplicity over cleverness**: a 20-line function beats a 200-line abstraction
- **Read before writing**: always understand existing code before modifying it
- **Engine/workspace separation**: aicli/ is engine (code), workspace/ is content (prompts, data)
- **Provider contract**: every provider has send(prompt, system) → str and stream() → Generator
- **No shared state between CLI and UI backend** — they are independent services


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index c6f11a7..4c5f604 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 18:01 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 18:02 UTC
 
 # aicli — Shared AI Memory Platform
 


### `role` — 2026-04-01

# Expert Code Reviewer

You are an expert Python code reviewer with a focus on production-quality software.


### `commit` — 2026-04-01

diff --git a/.ai/rules.md b/.ai/rules.md
index 13401fc..f76448e 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 18:05 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-01 18:06 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -55,9 +55,9 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
 - _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load
 - Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking, not in summary arrays
-- MCP server (stdio) with 12+ tools configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations (depends_on, relates_to, blocks, implements) via CLI/admin UI
 - Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
-- CLI: Python 3.12 + prompt_toolkit + rich with verb-noun command routing; memory endpoint template variable scoping fixed at line 1120
+- Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); mem_ai_tags_relations relations section omitted
+- Per-feature CLAUDE.md auto-loaded when Claude enters features/{tag}/ directory; tag retrieval returns (id, name, status, short_desc, priority, due_date)
 - Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
 - Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/


## AI Synthesis

**2026-04-01** `memory_files.py` — Memory file auto-generation system refactored to read feature details from inline planner_tags snapshot fields (summary, action_items, design, code_summary) rather than mem_ai_tags_relations, improving data consistency and per-feature CLAUDE.md rendering. **2026-03-28** `memory_promotion.py` — SQL cursor tuple unpacking standardized: _SQL_GET_CURRENT_FACTS corrected to unpack 4 columns instead of 5, fixing crashes during memory synthesis from mem_ai_project_facts. **2026-03-26** `get_active_feature_tags()` — Memory file lifecycle enhanced with proper filtering of active/open tags with snapshots; render_feature_claude_md() now reads complete tag metadata ensuring feature context is always populated. **2026-03-20** `mem_ai_* tables` — Schema consolidation complete: unified event/tag/fact/work-item tables replace per-project fragmentation; deprecated event_summary_tags array and metadata columns removed; data persistence across session switches confirmed working. **2026-03-14** `backend_startup_race_condition` — Retry logic implemented to handle empty project list on first load, preventing AiCli project from appearing unselectable in Recent projects UI. **2026-03-10** `planner_tags context loading` — Query limit set to 30 most recent tags per feature; context dict now properly populated with id, name, short_desc, requirements, summary, action_items, design, code_summary fields for feature-specific memory generation.