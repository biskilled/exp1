# Project Memory — aicli
_Generated: 2026-03-20 18:58 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that integrates multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) with a dual-storage backend (JSONL + PostgreSQL pgvector) to enable semantic search, memory synthesis, and workflow automation. The system combines a Python CLI with an Electron desktop UI featuring embedded terminal and Monaco editor, supporting JWT-authenticated role-based access (admin/paid/free), nested tagging hierarchies, async DAG workflow execution, and MCP integration for project state management.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: SQL
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude_CLI_and_LLM_platforms
- **mcp_integration**: embedding_and_data_retrieval
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
- **performance_optimization**: redundant_SQL_calls_eliminated
- **pipeline/auth**: Acceptance criteria:
# PM Analysis: Email Verification Feature (Revised)

---

## Context Summary

The tagged context confirms this work item builds upon an **existing authentication system** that already includes functional **Sign In and Register forms**. These forms are live and in use. This feature is therefore an **incremental enhancement** — not a greenfield build. The email verification layer must integrate clea

Reviewer: ```json
{
  "passed": false,
  "score": 4,
  "issues": [
    "Implementation is incomplete — file `backend/services/email_verification_service.py` is truncated mid-function at `can_resend_email()`. Cr
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
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK nesting), agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles

## Key Decisions

- Engine/workspace separation: aicli/ contains code only; workspace/ stores per-project content; _system/ holds project state
- Dual storage: JSONL (history.jsonl with rotation on /memory) for primary storage; PostgreSQL 15+ with pgvector for semantic search and per-project indexed tables
- Electron UI with xterm.js + Monaco editor; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication via python-jose + bcrypt; DEV_MODE toggle; 3-tier roles (admin/paid/free); login as first-level hierarchy
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends no keys
- Nested tag hierarchy via parent_id FK with unlimited depth; tags synced across Chat/History/Commits on explicit save
- Load-once-on-access pattern: eliminate redundant SQL by caching tags/workflows/runs in memory; update DB only on explicit save
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js + cytoscape-dagre visualization
- Memory synthesis: Claude Haiku for dual-layer output (raw JSONL → interaction_tags → 5 files); smart chunking per language/section
- Hierarchical data model: Clients contain Users; per-project tables (commits_{p}, events_{p}, embeddings_{p}, etc.); shared auth/billing tables
- Port binding safety via freePort() to kill stale uvicorn; Electron cleanup via process.exit()
- Features linked to work_items with sequence numbering (10000+) for memory and workflow status tracking
- MCP server (stdio) with 12+ tools for project state, memory search, entity management, feature status
- Per-project DB tables indexed on phase/feature/session_id for fast contextual retrieval
- 2-pane approval chat workflow for requirement negotiation before work_item save

## In Progress

- Project startup race condition fix (2026-03-20) — Sequential `await api.listProjects()` in `_continueToApp` now prevents empty home screen on initial load by properly handling edge case where list succeeds but returns empty
- Pipeline sidebar caching (2026-03-20) — `_listCache` stores {workflows, roles, runs} to prevent redundant API calls during pipeline UI rendering
- UUID validation in pipeline run queries (2026-03-19) — psycopg2 InvalidTextRepresentation error when string 'recent' passed to UUID field; requires UUID object conversion in backend handler
- Approval chat workflow (2026-03-19) — 2-pane approval panel enables requirement negotiation before work_item save; left pane shows current output, right pane for chat interaction
- Memory endpoint code_dir scoping (2026-03-18) — Fixed undefined template variable at line 1120 causing CLAUDE.md generation failure; variable now properly scoped from config
- Memory items and project_facts table population (pending) — Tables exist in schema but update logic unimplemented; blocks improved memory/context mechanism and requires implementation + testing

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(38 events, 33 commits)`

### Doc_type

- **low-level-design** `(1 events)`
- **high-level-design** `(1 events)`
- **customer-meeting** — dsds
- **retrospective**
- **Test**

### Feature

- **UI** `(36 events, 30 commits)`
- **auth** `(34 events, 31 commits)`
- **graph-workflow** `(23 events, 20 commits)`
- **workflow-runner** `(21 events, 20 commits)`
- **embeddings** `(21 events, 20 commits)`
- **shared-memory** `(15 events, 10 commits)`
- **tagging**
- **billing**
- **mcp**
- **test-picker-feature**
- **dropbox**
- **pagination**

### Phase

- **discovery** `(32 events, 30 commits)`
- **development**
- **prod**

### Task

- **memory** `(13 events, 10 commits)`
- **implement-projects-tab** — Build the UI for managing features/tasks/bugs `(1 events)`

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

**[2026-03-20]** `dev` — Fixed project startup race condition: sequential `await api.listProjects()` in `_continueToApp` now prevents empty home screen when backend returns empty project list on first load. **[2026-03-20]** `dev` — Implemented pipeline sidebar caching with `_listCache` to store workflows/roles/runs, eliminating redundant API calls during pipeline UI rendering. **[2026-03-19]** `bug` — Identified and documented UUID validation issue: psycopg2 InvalidTextRepresentation when string 'recent' passed to UUID field in pipeline run queries; requires backend UUID object conversion. **[2026-03-19]** `feature` — Designed 2-pane approval chat workflow enabling requirement negotiation before work_item save; left pane shows output, right pane supports interactive chat. **[2026-03-18]** `bug` — Fixed AttributeError in main.py from stale `db.ensure_project_schema()` call; replaced with correct `_ensure_shared_schema()` method. **[2026-03-18]** `bug` — Fixed memory endpoint CLAUDE.md template error: undefined `code_dir` variable at line 1120 now properly scoped from config. **[2026-03-10]** `architecture` — Implemented load-once-on-access pattern: cache tags/workflows/runs in memory on project load, update database only on explicit save actions to reduce redundant SQL calls. **[2026-03-10]** `feature` — Approved nested tag hierarchy expansion via parent_id FK enabling unlimited depth beyond current 2-level structure. **[2026-03-10]** `bug` — Identified data persistence issue: tags saved in UI disappear when switching sessions; unclear if rendering or database save failure—requires investigation. **[pending]** `implementation` — Memory items and project_facts table population logic not implemented; blocks improved memory/context mechanism per original specification.