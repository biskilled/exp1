# Project Memory — aicli
_Generated: 2026-04-01 18:06 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that bridges CLI and desktop UI (Electron) for managing projects, workflows, and AI interactions across multiple LLM providers. It features a PostgreSQL backend with unified memory tables (mem_ai_events, mem_ai_project_facts, mem_ai_work_items), async DAG workflow execution, Claude-powered memory synthesis generating 5 markdown files, and semantic search via pgvector. Currently focused on stabilizing memory file generation, fixing database cursor handling, and improving feature context loading from inline snapshot data.

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

- Engine/workspace separation: aicli/ contains backend logic; workspace/ contains per-project content; _system/ stores project state and memory files
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules; Claude Haiku for dual-layer memory synthesis generating 5 output files
- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking, not in summary arrays
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/
- Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary)
- Per-feature CLAUDE.md auto-loaded when Claude enters features/{tag}/ directory
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop; local via bash start_backend.sh + ui/npm run dev
- Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support

## In Progress

- Memory file generation refactoring: feature_details context loaded from planner_tags inline fields; _SQL_ACTIVE_TAGS query fixed to return tag names from correct column index; per-feature CLAUDE.md rendering improved with snapshot data integration
- Schema consolidation: mem_ai_tags_relations relations section removed from feature rendering; inline snapshot fields now primary data source for feature details context
- SQL cursor tuple unpacking standardization: memory_promotion.py _SQL_GET_CURRENT_FACTS fixed to unpack 4 columns instead of 5; memory_files.py active tags query corrected
- Memory file lifecycle enhancement: get_active_feature_tags() now correctly filters active/open tags with snapshots; render_feature_claude_md() reads complete tag metadata
- Feature details context loading: planner_tags query limits to 30 most recent tags; context dict populated with id, name, short_desc, requirements, summary, action_items, design, code_summary
- Database cursor handling robustness: standardized tuple unpacking across memory_promotion.py and memory_files.py with improved SQL result column ordering documentation

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-01

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index f7403b5..fde14e7 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Memory file auto-generation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md fully regenerated with timestamp tracking from mem_ai_project_facts and mem_ai_work_items (last run 2026-04-01T13:58:46Z)
+- Memory file auto-generation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md fully regenerated with timestamp tracking from mem_ai_project_facts and mem_ai_work_items (last run 2026-04-01T15:35:11Z)
 - Unified event table consolidation: mem_ai_events schema validated; deprecated event_summary_tags array and metadata columns removed; data persistence across session switches confirmed
 - Backend startup race condition resolved: retry logic implemented to handle empty project list on first load, preventing AiCli project from appearing unselectable in Recent
 - Tag persistence bug fixed: mem_ai_tags_relations now properly maintains row ID linking and cache invalidation during DB reload operations
-- Schema documentation updated: project_state.json and rules.md aligned with mem_ai_* unified naming; legacy database_schema field conflicts removed
+- Schema documentation updated: project_state.json and rules.md aligned with mem_ai_* unified naming; removed webpack reference in node_modules_build clarification
 - Frontend UI refinement: lifecycle button section removed from entities.js drawer to reduce clutter and align with feature scope


### `role` — 2026-04-01

## Your Principles

- **Simplicity over cleverness**: a 20-line function beats a 200-line abstraction
- **Read before writing**: always understand existing code before modifying it
- **Engine/workspace separation**: aicli/ is engine (code), workspace/ is content (prompts, data)
- **Provider contract**: every provider has send(prompt, system) → str and stream() → Generator
- **No shared state between CLI and UI backend** — they are independent services


### `commit` — 2026-04-01

diff --git a/.ai/rules.md b/.ai/rules.md
index df0b1ba..13401fc 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -21,7 +21,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
 - **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
 - **memory_synthesis**: Claude Haiku dual-layer with 5 output files
-- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
+- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
 - **mcp**: Stdio MCP server with 12+ tools
 - **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
 - **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
@@ -58,6 +58,6 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - MCP server (stdio) with 12+ tools configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations (depends_on, relates_to, blocks, implements) via CLI/admin UI
 - Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
-- CLI: Python 3.12 + prompt_toolkit + rich with verb-noun command routing; memory endpoint template variable scoping fixed
+- CLI: Python 3.12 + prompt_toolkit + rich with verb-noun command routing; memory endpoint template variable scoping fixed at line 1120
 - Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
 - Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/


### `role` — 2026-04-01

## Critical Issues (block approval)
- Logic bugs that will cause incorrect behaviour
- Security vulnerabilities (shell injection, path traversal, secret exposure)
- Unhandled exceptions that will crash the program
- Breaking changes to existing interfaces


### `commit` — 2026-04-01

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index ada7155..7421cde 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-01 18:01 UTC by aicli /memory_
+_Generated: 2026-04-01 18:02 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python CLI (prompt_toolkit + rich), FastAPI backend, and Electron desktop UI for AI-assisted development workflows. It unifies event tracking, project facts, and work items in PostgreSQL with semantic search via pgvector embeddings, while supporting multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) with an async DAG workflow executor. Currently stable on v2.2.0 with recent focus on memory synthesis automation, unified table consolidation, and backend startup reliability.
+aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to provide LLM-integrated project memory management. It uses PostgreSQL with pgvector for semantic search, unified event/fact/work-item tables, and supports multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) with Claude Haiku for dual-layer memory synthesis. Current focus is on stabilizing unified database schema, fixing data persistence bugs, and auto-generating memory documentation files with proper timestamp tracking.
 
 ## Project Facts
 
@@ -287,4 +287,4 @@ index 05ae0fa..24e0132 100644
 
 ## AI Synthesis
 
-**[2026-04-01]** `claude` — Memory synthesis pipeline stabilized with Claude Haiku generating 5 unified output files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items; timestamp tracking implemented. **[2026-04-01]** `claude` — Unified event table consolidation completed; mem_ai_events schema finalized with deprecated columns removed; data persistence confirmed across session switches. **[2026-03-28]** `claude` — Backend startup race condition mitigated via retry logic for empty project list on first load; prevents AiCli project from appearing unselectable. **[2026-03-25]** `claude` — Tag persistence bug fixed in mem_ai_tags_relations with proper row ID linking and cache invalidation during DB reload operations. **[2026-03-20]** `claude` — Schema documentation aligned: project_state.json and rules.md use unified mem_ai_* naming; legacy database_schema conflicts removed. **[2026-03-18]** `claude` — Frontend UI refinement: lifecycle section removed from entities.js drawer to reduce clutter while maintaining feature completeness. **[2026-03-15]** `claude` — Memory endpoint template variable scoping fixed at line 1120 in core memory logic. **[2026-03-14]** `claude` — Established dual storage model with PostgreSQL 15+ and pgvector (1536-dim embeddings) for semantic search; unified mem_ai_* table architecture.
\ No newline at end of file
+**2026-04-01** `auto-memory` — Memory file synthesis completed with timestamp tracking for CLAUDE.md, MEMORY.md, context.md, rules.md, and copilot.md; all generated from mem_ai_project_facts and mem_ai_work_items. **2026-04-01** `schema-consolidation` — Unified mem_ai_events table fully validated; deprecated event_summary_tags and metadata columns removed; data persistence across session switches confirmed working. **2026-04-01** `bug-fix` — Backend startup race condition resolved using retry logic to handle empty project list on first load, ensuring AiCli project remains selectable in Recent projects. **2026-04-01** `bug-fix` — Tag persistence fixed in mem_ai_tags_relations with proper row ID linking and cache invalidation during DB reload operations. **2026-04-01** `documentation` — project_state.json and rules.md updated to align with mem_ai_* unified naming convention; legacy database_schema conflicts removed. **2026

### `commit` — 2026-04-01

Commit: docs: update memory and rules files after claude session
Hash: 4bd4c12c
Files changed (16):
  - .ai/rules.md
  - .cursor/rules/aicli.mdrules
  - .github/copilot-instructions.md
  - CLAUDE.md
  - MEMORY.md
  - workspace/aicli/PROJECT.md
  - workspace/aicli/_system/CLAUDE.md
  - workspace/aicli/_system/CONTEXT.md
  - workspace/aicli/_system/aicli/context.md
  - workspace/aicli/_system/aicli/copilot.md
  - workspace/aicli/_system/claude/CLAUDE.md
  - workspace/aicli/_system/claude/MEMORY.md
  - workspace/aicli/_system/commit_log.jsonl
  - workspace/aicli/_system/cursor/rules.md
  - workspace/aicli/_system/dev_runtime_state.json
  - workspace/aicli/_system/project_state.json

## AI Synthesis

**2026-04-01** `memory_files.py + memory_promotion.py` — Fixed SQL cursor tuple unpacking: _SQL_GET_CURRENT_FACTS now correctly unpacks 4 columns instead of 5; _SQL_ACTIVE_TAGS query corrected to read tag names from proper result index [1]. **2026-04-01** `memory_synthesis` — Refactored feature details context loading to read from inline planner_tags snapshot fields (summary, action_items, design, code_summary) rather than mem_ai_tags_relations relations; limits query to 30 most recent tags with embedding or summary. **2026-04-01** `memory_lifecycle` — Enhanced get_active_feature_tags() to correctly filter active/open tags with snapshots; render_feature_claude_md() now reads complete tag metadata including requirements and short_desc. **2026-03-28** `schema_consolidation` — Removed mem_ai_tags_relations relations section from feature rendering pipeline; unified inline snapshot data as primary source for feature context generation. **2026-03-21** `backend_startup` — Implemented retry logic to handle empty project list on first load, resolving race condition preventing AiCli project selection in Recent projects. **2026-03-14** `documentation_update` — Aligned project_state.json and rules.md with mem_ai_* unified naming; clarified node_modules_build and removed webpack references; standardized SQL cursor handling documentation across modules.