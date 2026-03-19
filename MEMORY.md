# Project Memory — aicli
_Generated: 2026-03-19 13:16 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to manage multi-agent workflows, project context, and semantic memory across LLM platforms. It uses flat-file JSONL for primary storage with PostgreSQL/pgvector for semantic search, supports nested tagging, multi-agent async DAG workflows with visual graph editor, and MCP integration for memory/entity management. Current focus: fixing project visibility race conditions, completing pipeline UI enhancements, and implementing memory_items/project_facts population for improved context synthesis.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: SQL
- **deployment_target**: Claude_CLI_and_LLM_platforms
- **mcp_integration**: embedding_and_data_retrieval
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
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
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK nesting), agent_roles, system_roles
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; inline modal for pipeline creation
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK nesting), agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file primary (JSONL with rotation on /memory); PostgreSQL 15+ with pgvector for semantic search; per-project DB tables with indexed columns (phase/feature/session_id)
- Electron UI with xterm.js + Monaco editor; Vanilla JS frontend (no framework, no bundler); Vite dev server for local dev
- JWT auth via python-jose + bcrypt; DEV_MODE toggle; 3 roles: admin/paid/free; login as first-level hierarchy
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth with tree UI; tags synced across Chat/History/Commits on save
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot rules, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Load-once-on-access pattern: eliminate redundant SQL; tag cache synced on explicit save
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- Port binding safety: freePort() kills stale uvicorn; Electron cleanup via process.exit()
- Backend startup race condition fix: retry logic handles empty project list on first load
- Pipeline/workflow nodes support max_retry, stateless mode, continue_on_fail flags; visual node removal with confirmation dialog

## In Progress

- Pipeline UI node properties (2026-03-19) — Display and configuration of max_retry, stateless, continue_on_fail; node removal with confirmation; inline modal for pipeline creation
- Multi-agent workflow execution (2026-03-19) — Per-node retry/continue logic; chat/run capability for current phase; MEMORY.md updates pending
- Project visibility race condition (2026-03-19) — Projects load in Recent but not selectable as active; backend initialization timing issue under investigation
- Graph workflow UI routing fix (2026-03-19) — Corrected main.js imports and case statements for proper graph_workflow.js renderer routing
- Memory items and project_facts population — Tables exist but update logic unimplemented; blocks improved memory/context mechanism
- Documents tab feature — Add per-project folder mapping; auto-create for new projects; support multi-role document uploads

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(16 events, 13 commits)`

### Doc_type

- **high-level-design** `(1 events)`
- **low-level-design** `(1 events)`
- **retrospective**
- **customer-meeting** — dsds
- **Test**

### Feature

- **shared-memory** `(14 events, 10 commits)`
- **auth** `(13 events, 11 commits)`
- **UI** `(12 events, 10 commits)`
- **graph-workflow** `(1 events)`
- **tagging**
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

**[2026-03-19]** `claude_cli` — Pipeline UI enhanced with inline node property display (model, input/output, max_retry, stateless, continue_on_fail flags); node removal dialog and modal-based pipeline creation implemented; visibility of (x) button improved via CSS inline-block. **[2026-03-19]** `claude_cli` — Multi-agent workflow execution logic refined; retry/continue per-node flags now functional; MEMORY.md updates pending. **[2026-03-19]** `investigation` — Project visibility race condition identified: projects appear in Recent list but not selectable as active project; suspected backend initialization timing issue during project list load. **[2026-03-19]** `fix` — Graph workflow UI routing corrected; main.js case statements now properly delegate to graph_workflow.js renderer. **[2026-03-18]** `fix` — Backend startup race condition resolved; retry logic in _continueToApp() now handles empty project list returns on first load. **[2026-03-18]** `fix` — Memory endpoint CLAUDE.md template error fixed; code_dir variable properly scoped from config (line 1120). **[2026-03-18]** `fix` — AttributeError in main.py resolved; removed stale db.ensure_project_schema() call. **[2026-03-10]** `architecture` — Database performance optimized via load-once-on-access pattern; redundant SQL calls eliminated; tags loaded into memory on project access, updated only on explicit save. **[2026-03-10]** `feature` — Nested tag hierarchy expanded beyond 2-level; parent_id FK enables unlimited depth with tree UI; login confirmed as first-level only. **[unresolved]** `pending` — memory_items and project_facts tables exist but update logic not implemented; blocks improved context mechanism.