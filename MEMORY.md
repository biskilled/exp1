# Project Memory — aicli
_Generated: 2026-03-21 21:29 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining Claude CLI, FastAPI backend, PostgreSQL semantic search, and Electron desktop UI. It manages per-project development history via dual storage (JSONL + pgvector), implements DAG-based workflow execution with visual graph interface, and integrates MCP for context retrieval. Current focus: backend code organization refactoring, MCP configuration alignment, and SQL query optimization.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: SQL
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude_CLI_and_LLM_platforms
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **mcp_integration**: embedding_and_data_retrieval
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
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows) + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **memory_synthesis**: Claude Haiku for dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic only; workspace/ stores per-project content; _system/ holds project state
- Dual storage: JSONL (history.jsonl with rotation) for primary storage; PostgreSQL 15+ with pgvector (1536-dim embeddings) for semantic search and per-project indexed tables
- Electron UI with xterm.js + Monaco editor; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication via python-jose + bcrypt; DEV_MODE toggle; 3-tier roles (admin/paid/free); login as first-level hierarchy
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends no keys
- Nested tag hierarchy via parent_id FK with unlimited depth; tags synced across Chat/History/Commits on explicit save
- Load-once-on-access pattern: cache tags/workflows/runs in memory; update DB only on explicit save to eliminate redundant SQL
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js + cytoscape-dagre visualization
- Memory synthesis: Claude Haiku for dual-layer output (raw JSONL → interaction_tags → 5 files); smart chunking per language/section
- Port binding safety via freePort() to kill stale uvicorn; Electron cleanup via process.exit()
- Features linked to work_items with sequence numbering (10000+) for memory and workflow status tracking
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT) in .cursor/mcp.json and .claude/mcp.json
- Work item pipeline queries mng_agent_roles table; respects configured LLM provider and model per role instead of hardcoded Haiku
- Graph runner commits via `_apply_code_and_commit` with standardized message format for work item traceability
- Per-project DB tables indexed on phase/feature/session_id for fast contextual retrieval

## In Progress

- Backend code organization refactor (2026-03-21) — User questioned storage folder managing sessions and scattered memory management classes under core; requires consolidation of memory classes and clarification of model usage
- MCP server path and configuration alignment (2026-03-21) — Fixed path references in aicli.yaml, .cursor/mcp.json, .claude/mcp.json; switched to env vars instead of hardcoded arguments; created missing .claude/mcp.json
- Electron backend path resolution (2026-03-21) — Fixed BACKEND_DIR path pointing to old/ui/backend instead of correct aicli/backend; verified all project lookup endpoints work correctly
- Automated commit hooks configuration (2026-03-21) — Ensured all hooks configured without hardcoded strings; using backend_url environment variable; hooks not yet fully operational
- Project visibility bug investigation (2026-03-21) — AiCli project appearing in Recent but not in main project list; suspected race condition in Electron initialization; partial fix applied
- SQL query optimization (2026-03-20) — Row-by-row INSERT in event migration and unbounded fetchall() in memory synthesis; requires batch INSERT refactor and pagination

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(45 events, 40 commits)`

### Doc_type

- **Test** `(28 events, 27 commits)`
- **low-level-design** `(1 events)`
- **high-level-design** `(1 events)`
- **retrospective**
- **customer-meeting** — dsds

### Feature

- **UI** `(43 events, 37 commits)`
- **shared-memory** `(42 events, 37 commits)`
- **auth** `(41 events, 38 commits)`
- **graph-workflow** `(31 events, 27 commits)`
- **workflow-runner** `(29 events, 27 commits)`
- **embeddings** `(28 events, 27 commits)`
- **tagging**
- **billing**
- **mcp**
- **test-picker-feature**
- **dropbox**
- **pagination**

### Phase

- **discovery** `(39 events, 37 commits)`
- **development** `(31 events, 28 commits)`
- **prod**

### Task

- **memory** `(41 events, 37 commits)`
- **implement-projects-tab** — Build the UI for managing features/tasks/bugs `(28 events, 27 commits)`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `session: 5b19c863-f99a-439c-b595-b415d0d342ed` — 2026-03-16

# Development Session Summary

**Session Focus**: Architecture audit and capability assessment of memory management, tagging system, and MCP integration

**Actions Completed**:
• Executed `/memory` command to audit data storage layers and tagging system functionality
• Reviewed how MCP integrates with memory layer for embedding and data retrieval
• Validated tag system implementation for data organization across Claude CLI and other LLMs

**Key Questions Addressed**:
• Refactor impact on tag usage and memory efficiency from new summarization process
• MCP's capability to answer work item management queries and generate workflows
• Whether improved architecture enables better complex project delivery
• Real-time MCP functionality and data retrieval accuracy within session

**Findings/Outcomes**: [INCOMPLETE - Session summary ends mid-question; actual results, performance metrics, identified issues, and recommendations not documented]

**Follow-up Needed**: Clarify final question intent and document concrete findings from /memory audit and MCP capability test

### `session: 03f774e9-ad60-4cf3-8c0c-0191ba9a78d0` — 2026-03-16

# Development Session Summary (2026-03-10)

• **Database Performance Issue**: Identified multiple redundant SQL calls slowing the system; implemented strategy to load data once on project access (e.g., tags into memory) and only update DB on explicit save actions

• **Tag Hierarchy Enhancement**: Approved nested tags feature to expand beyond current 2-level hierarchy (category → tag); confirmed login will be first-level only

• **UI/UX Improvements for Planner**:
  - Increased visibility of action options (currently too small)
  - Replaced small action buttons with 3-dot menu button to improve clarity
  - Added ability to unarchive archived items

• **Data Persistence Bug**: Discovered tags saved in UI disappear when switching sessions—unclear if UI rendering issue or database save failure; requires investigation

• **AI Suggestions UI**: Need to make `/memory` suggestions more visible and clearly labeled as "AI suggestions requiring approval," including which session they apply to and direct GitHub commit links

• **Backend Stability**: Intermittent app restart failures due to port 127.0.0.1:8000 binding conflicts

### `session: 8f29a8d3-13a3-42ed-9219-de7bfe53e3d2` — 2026-03-18

# Development Session Summary (2026-03-18)

## Issues Fixed

• **AttributeError in `main.py`** — Removed stale `db.ensure_project_schema(settings.active_project)` call (method doesn't exist; should use `_ensure_shared_schema` instead)

• **Memory endpoint CLAUDE.md template error** — Undefined `code_dir` variable at line 1120 causing runtime failure; variable now properly scoped/defined from config

• **Backend startup race condition** — Modified `_continueToApp()` retry logic to handle edge case where projects load succeeds but returns empty list (prevents false "project not found" errors on first load)

## Issues Identified but Unresolved

• **Project visibility bug** — AiCli appears in Recent projects but not displaying as current active project in main project view; suspected timing issue during backend initialization; **PENDING: Further investigation**

## Design Gaps Requiring Implementation

• **memory_items and project_facts tables not updating** — Per original specification, these tables should be populated to enable improved memory/context mechanism, but update logic not implemented; **PENDING: Implementation and testing**

## Data Model Clarification

• Confirmed hierarchical structure: Clients contain multiple Users (previously unclear)

## AI Synthesis

**[2026-03-21]** `in_progress` — Backend code organization refactoring requested: consolidate scattered memory management classes currently under core module, clarify model usage, and eliminate storage folder redundancy for session management. **[2026-03-21]** `in_progress` — MCP configuration finalized: switched from hardcoded arguments to environment variables (BACKEND_URL, ACTIVE_PROJECT) across aicli.yaml, .cursor/mcp.json, and .claude/mcp.json; created missing .claude/mcp.json. **[2026-03-21]** `bug_fix` — Electron backend path resolution corrected: BACKEND_DIR was pointing to old/ui/backend instead of aicli/backend; verified all project lookup endpoints now functional. **[2026-03-21]** `bug_investigation` — Project visibility race condition identified: AiCli project appears in Recent projects list but fails to display as active in main project view during Electron initialization; partial retry logic fix applied. **[2026-03-20]** `perf_issue` — SQL query inefficiencies discovered: event migration uses row-by-row INSERT and memory synthesis has unbounded fetchall(); requires batch INSERT refactor and pagination implementation. **[2026-03-10]** `architecture` — Load-once-on-access pattern implemented to reduce redundant SQL calls: tags and workflows cached in memory on project access, updated to DB only on explicit save actions.