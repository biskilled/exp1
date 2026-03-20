# Project Memory — aicli
_Generated: 2026-03-20 21:51 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform designed for collaborative LLM-assisted development with per-project semantic storage (PostgreSQL + pgvector), multi-provider LLM integration, and async workflow orchestration. The project currently comprises 15 active features (UI, shared-memory, auth, graph-workflow, tagging, MCP integration) with ongoing performance optimization of SQL queries and workflow execution, plus system role enhancement for document generation workflows.

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
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles

## Key Decisions

- Engine/workspace separation: aicli/ contains code only; workspace/ stores per-project content; _system/ holds project state
- Dual storage: JSONL (history.jsonl with rotation) for primary storage; PostgreSQL 15+ with pgvector for semantic search and per-project indexed tables
- Electron UI with xterm.js + Monaco editor; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication via python-jose + bcrypt; DEV_MODE toggle; 3-tier roles (admin/paid/free); login as first-level hierarchy
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends no keys
- Nested tag hierarchy via parent_id FK with unlimited depth; tags synced across Chat/History/Commits on explicit save
- Load-once-on-access pattern: cache tags/workflows/runs in memory; update DB only on explicit save to eliminate redundant SQL
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js + cytoscape-dagre visualization
- Memory synthesis: Claude Haiku for dual-layer output (raw JSONL → interaction_tags → 5 files); smart chunking per language/section
- Port binding safety via freePort() to kill stale uvicorn; Electron cleanup via process.exit()
- Features linked to work_items with sequence numbering (10000+) for memory and workflow status tracking
- MCP server (stdio) with 12+ tools for project state, memory search, entity management, feature status
- Per-project DB tables indexed on phase/feature/session_id for fast contextual retrieval
- 2-pane approval chat workflow for requirement negotiation before work_item save
- System roles for document generation (e.g., PM, architect roles with specific output formatting expectations)

## In Progress

- SQL query optimization (2026-03-20) — P0 issues identified: row-by-row INSERT in event migration (2000+ queries for 1000 events) and unbounded fetchall() in memory synthesis; requires batch INSERT refactor and pagination
- Workflow performance optimization (2026-03-20) — Workflow execution runs very slowly; requires analysis of async DAG executor bottlenecks and potential query caching improvements
- System roles enhancement (2026-03-20) — Optimize work_item pipeline to use existing roles (PM, architect) and add system roles with formatting expectations (e.g., document generation role outputs short bullet-point descriptions)
- Pipeline approval workflow rendering (2026-03-20) — Old MD version displayed instead of current output/progress logs; requires chat panel state management and step sequencing investigation
- UUID validation in pipeline run queries (2026-03-19) — psycopg2 InvalidTextRepresentation when string 'recent' passed to UUID field; requires UUID object conversion in backend
- Memory items and project_facts table population (pending) — Tables exist in schema but update logic unimplemented; blocks improved memory/context mechanism

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(40 events, 35 commits)`

### Doc_type

- **Test** `(23 events, 22 commits)`
- **low-level-design** `(1 events)`
- **high-level-design** `(1 events)`
- **retrospective**
- **customer-meeting** — dsds

### Feature

- **UI** `(38 events, 32 commits)`
- **shared-memory** `(37 events, 32 commits)`
- **auth** `(36 events, 33 commits)`
- **graph-workflow** `(25 events, 22 commits)`
- **workflow-runner** `(23 events, 22 commits)`
- **embeddings** `(23 events, 22 commits)`
- **tagging**
- **billing**
- **mcp**
- **test-picker-feature**
- **dropbox**
- **pagination**

### Phase

- **discovery** `(34 events, 32 commits)`
- **development** `(23 events, 22 commits)`
- **prod**

### Task

- **memory** `(35 events, 32 commits)`
- **implement-projects-tab** — Build the UI for managing features/tasks/bugs `(23 events, 22 commits)`

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

**[2026-03-20]** `claude_cli` — Identified P0 SQL performance issues: row-by-row INSERT in event migration (2000+ queries for 1000 events at admin.py:666-695) and unbounded fetchall() in memory synthesis requiring batch refactoring and pagination. **[2026-03-20]** `claude_cli` — Workflow execution performance severely degraded; requires bottleneck analysis in async DAG executor and query caching strategy review. **[2026-03-20]** `claude_cli` — System roles enhancement initiated to map work_item pipeline to existing roles (PM, architect) with formatting expectations for document generation (short bullets). **[2026-03-20]** `feature` — Pipeline approval workflow showing stale MD output instead of current logs; blocked on chat panel state management and step sequencing. **[2026-03-19]** `bug` — UUID validation failure when string 'recent' passed to UUID field in pipeline run queries; backend needs UUID object conversion. **[2026-03-18]** `bug` — Memory endpoint CLAUDE.md generation fixed by properly scoping code_dir variable from config (line 1120). **[2026-03-18]** `bug` — Backend startup race condition mitigated with retry logic handling empty project list on first load. **[2026-03-10]** `decision` — Implemented load-once-on-access pattern to cache tags/workflows/runs in memory, updating DB only on explicit save to reduce redundant SQL. **[2026-03-10]** `bug` — Tags saved in UI disappear on session switch; cause unclear (rendering vs database), requires investigation. **[pending]** `task` — memory_items and project_facts tables exist but update logic not implemented; blocks memory/context mechanism improvements.