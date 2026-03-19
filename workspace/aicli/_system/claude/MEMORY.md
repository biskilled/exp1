# Project Memory — aicli
_Generated: 2026-03-19 02:25 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that integrates CLI, web, and desktop UIs with multi-LLM support (Claude, OpenAI, DeepSeek, Gemini, Grok) for collaborative development workflows. It features PostgreSQL+pgvector semantic search, nested tag hierarchies, role-based access control (admin/paid/free), MCP server integration, and node-based workflow execution with Cytoscape visualization. Current focus: extending role system with configurable input/output types, implementing Documents tab, resolving project visibility race conditions, and populating memory_items/project_facts tables for improved context delivery.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: SQL
- **deployment_target**: Claude_CLI_and_LLM_platforms
- **mcp_integration**: embedding_and_data_retrieval
- **memory_management_pattern**: load_once_on_access_update_on_save
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
- **performance_optimization**: redundant_SQL_calls_eliminated
- **stale_code_removed**: db.ensure_project_schema_call_replaced_with_ensure_shared_schema
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **ui_library**: 3_dot_menu_pattern
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows) + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking), agent_roles, system_roles
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK nesting), agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables with indexed columns (phase/feature/session_id)
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server for local dev
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free; login as first-level hierarchy
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth with tree UI in Planner; tags synced across Chat/History/Commits
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Load-once-on-access pattern eliminates redundant SQL; tag cache synced across Chat/History/Commits on save
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- Composable system roles (e.g., 'coding' with clean code/comments/OOP) addable to agent roles; input/output types configurable (prompts, MD files, JSON, GitHub code)
- Stateful vs stateless reviewer roles: stateful accumulates history across interactions; stateless operates on fresh context per request
- Port binding safety: freePort() kills stale uvicorn processes; Electron cleanup via process.exit()

## In Progress

- Role extensibility and input/output type definition (2026-03-19) — Add configurable input types (prompts, MD files from documents folder, JSON) and output targets (MD files, JSON, LLM response, GitHub code); support stateful (history-accumulating) vs stateless reviewer roles
- Documents tab feature (2026-03-19) — Add 'Documents' tab after Code, mapped to per-project document folder; auto-create for all new projects; support multiple roles (PM, engineer, etc.) uploading docs
- Project visibility in main view (2026-03-19) — Projects load in Recent section but not selectable/visible as current active project in main panel; race condition during backend init suspected
- UI action buttons and Prompt Files visibility (2026-03-19) — Plus button (+) for adding items non-functional; system prompts not displaying; requires UI refactor
- System roles feature design (2026-03-18) — Architecting composable system roles; removing stale db.ensure_project_schema() call; fixed CLAUDE.md template code_dir scoping
- Memory items and project_facts table population (unresolved) — Tables exist but update logic not implemented; blocks improved memory/context mechanism

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(13 events, 10 commits)`

### Doc_type

- **low-level-design** `(1 events)`
- **high-level-design** `(1 events)`
- **Test**
- **customer-meeting** — dsds
- **retrospective**

### Feature

- **shared-memory** `(14 events, 10 commits)`
- **UI** `(11 events, 10 commits)`
- **auth** `(11 events, 10 commits)`
- **tagging**
- **graph-workflow**
- **billing**
- **embeddings**
- **mcp**
- **workflow-runner**
- **test-picker-feature**
- **dropbox**
- **pagination**

### Phase

- **discovery** `(11 events, 10 commits)`
- **development**
- **prod**

### Task

- **memory** `(12 events, 10 commits)`
- **implement-projects-tab** — Build the UI for managing features/tasks/bugs

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

**[2026-03-19]** `dev_history` — Initiated role extensibility architecture to support configurable input types (prompts, MD files, JSON) and output targets (MD files, JSON, LLM response, GitHub code); designed stateful vs stateless reviewer role patterns for handling history accumulation vs fresh-context processing. **[2026-03-19]** `in_progress` — Documents tab feature scoped: add per-project document folder with auto-creation for new projects; support multi-role uploads (PM, engineer). **[2026-03-19]** `bug_tracking` — Project visibility race condition identified: projects appear in Recent but not selectable as active in main panel; backend initialization timing suspected. **[2026-03-18]** `fixed_bugs` — Removed stale db.ensure_project_schema() call causing AttributeError; scoped code_dir variable in CLAUDE.md template; added retry logic for empty project edge case during startup. **[2026-03-18]** `design_gaps` — memory_items and project_facts table population logic remains unimplemented despite table schema existence; blocks improved memory/context delivery. **[2026-03-10]** `performance` — Implemented load-once-on-access pattern to eliminate redundant SQL calls; tag cache now synced across Chat/History/Commits on explicit save. **[2026-03-10]** `ui_improvements` — Increased action button visibility in Planner; replaced small action buttons with 3-dot menu; added unarchive capability for archived items. **[2026-03-10]** `data_bug` — Tags saved in UI disappear on session switch; root cause unclear (rendering vs database persistence); requires investigation. **[2026-03-10]** `architecture` — Approved nested tag hierarchy expansion beyond 2 levels (category → tag); confirmed login as first-level-only constraint. **[2026-03-10]** `stability` — Port binding conflicts on 127.0.0.1:8000 causing intermittent restart failures; freePort() process cleanup strategy in place.