# Project Memory — aicli
_Generated: 2026-03-18 21:06 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron/vanilla JS frontend that synthesizes development history into structured memory using Claude Haiku, semantic search via PostgreSQL + pgvector, and multi-agent workflow orchestration. Currently addressing project visibility bugs, load performance optimization on free tier, and completing dual-layer memory distillation pipeline with MCP server integration for data retrieval and entity management.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: SQL
- **deployment_target**: Claude_CLI_and_LLM_platforms
- **mcp_integration**: embedding_and_data_retrieval
- **memory_management_pattern**: load_once_on_access_update_on_save
- **performance_optimization**: redundant_SQL_calls_eliminated
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **ui_library**: 3_dot_menu_pattern

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows) + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 12+ tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push, create_entity, update_entity, list_entities, get_feature_status)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, and MCP integration settings

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables with indexed columns (phase/feature/session_id)
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server for local dev
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free; login as first-level hierarchy
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth with tree UI in Planner; tags synced across Chat/History/Commits
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Load-once-on-access pattern eliminates redundant SQL; tag cache synced across Chat/History/Commits views on save
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization + YAML config
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase; backfills history.jsonl ordered by created_at
- Real DB columns for phase/feature/session_id in events_{p} with indexes; tag cache loaded once per project tab (zero redundant DB calls during chat)

## In Progress

- Project visibility and listing issues (2026-03-18) — AiCli appears in Recent projects but not displaying as selectable/current project in main view; investigating openProject() timing during backend init
- Backend startup race condition handling (2026-03-18) — Added _continueToApp retry logic to handle projects query success returning empty list; prevents false "project not found" errors
- AttributeError fixes in main.py (2026-03-18) — Removed stale db.ensure_project_schema() call; fixed CLAUDE.md template code_dir variable scoping in memory endpoint
- PROJECT.md load performance (2026-03-17) — >1 minute load time on free Railway tier; investigating DB query latency vs file I/O bottleneck; pagination/lazy-loading under evaluation
- Multi-agent workflow system integration (2026-03-16) — Async DAG executor with Cytoscape.js visualization + YAML config for orchestrating multi-agent prompts
- Dual-layer memory distillation pipeline (2026-03-16) — Raw JSONL → interaction_tags → 5 memory files; fixed session_bulk_tag() consistency across both tables

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(9 events, 7 commits)`

### Doc_type

- **low-level-design** `(1 events)`
- **high-level-design** `(1 events)`
- **customer-meeting** — dsds
- **Test**
- **retrospective**

### Feature

- **UI** `(8 events, 7 commits)`
- **shared-memory** `(4 events)`
- **dropbox**
- **pagination**
- **tagging**
- **graph-workflow**
- **billing**
- **auth**
- **embeddings**
- **mcp**
- **workflow-runner**
- **test-picker-feature**

### Phase

- **discovery** `(8 events, 7 commits)`
- **development**
- **prod**

### Task

- **memory** `(2 events)`
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

**[2026-03-18]** `bug fix` — Removed stale db.ensure_project_schema() call in main.py causing AttributeError; replaced with _ensure_shared_schema pattern.
**[2026-03-18]** `bug fix` — Fixed undefined code_dir variable in CLAUDE.md template generation (line 1120 in memory endpoint); variable now properly scoped from config.
**[2026-03-18]** `architecture` — Enhanced _continueToApp retry logic to handle race condition where projects query succeeds but returns empty list, preventing false "project not found" errors on startup.
**[2026-03-18]** `pending investigation` — Project visibility bug identified: AiCli displays in Recent projects list but fails to show as current active project in main project selector view; timing issue during backend initialization suspected.
**[2026-03-17]** `performance` — Identified >1 minute PROJECT.md load time on free Railway tier; investigating root cause between DB query latency and file I/O bottleneck; pagination/lazy-loading considered as mitigation.
**[2026-03-16]** `feature` — Multi-agent workflow system integration progressing: async DAG executor with Cytoscape.js visualization + YAML configuration for multi-agent prompt orchestration.
**[2026-03-16]** `feature` — Dual-layer memory synthesis pipeline validated: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules); session_bulk_tag() consistency fixed.
**[2026-03-15]** `data model` — Session phase persistence confirmed working: loads from DB on init, saves via PATCH /chat/sessions/{id}/tags; tag deduplication verified (149 tags, 0 duplicates).
**[2026-03-10]** `architecture` — Load-once-on-access pattern implemented to eliminate redundant SQL calls; tag cache loaded once per project tab and synced across Chat/History/Commits on explicit save.
**[2026-03-10]** `ui/ux` — Nested tag hierarchy approved beyond 2-level constraint; login established as first-level hierarchy; 3-dot menu pattern adopted for Planner action visibility.