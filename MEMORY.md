# Project Memory — aicli
_Generated: 2026-03-22 23:00 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform providing Claude CLI and other LLM platforms with persistent, searchable work context across sessions. It combines dual-layer storage (JSONL + PostgreSQL with pgvector embeddings), Electron-based desktop UI with terminal integration (xterm.js), async DAG workflow execution, and multi-provider LLM support with encrypted server-side key management. Current focus: stabilizing agent behavior through standardized roles/prompts/ReAct execution, fixing tag cache invalidation in planner UI, and populating memory_items/project_facts tables for enhanced context retrieval.

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
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok — each with defined system roles, prompts, input/output schemas, and ReAct execution mode
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **memory_synthesis**: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools; env var configured (BACKEND_URL, ACTIVE_PROJECT)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_usage/ (provider_costs.json, runtime data); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with per-project and shared schema tables; agent roles initialized

## Key Decisions

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
- Dual storage: JSONL (history.jsonl with rotation) for primary history; PostgreSQL 15+ with pgvector (1536-dim) for semantic search and per-project indexed tables
- Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys in database
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); smart chunking per language/section
- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared auth/usage tables
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB; UI renders from in-memory cache
- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- Backend modular organization: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
- Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
- Encrypted API key storage in data layer (dl_api_keys.py); server-side key management only; clients never send API credentials
- Agent roles initialized with real IDs; each agent has defined system role, prompts, input/output schema; ReAct mode for quality outcomes; no hallucination tolerance

## In Progress

- Agent role standardization (2026-03-22) — Implement per-agent system roles, prompts, input/output schemas, and ReAct mode execution to eliminate hallucination and ensure consistent agent behavior across all providers
- Tags loading and cache invalidation (2026-03-22) — User reports no DB API calls for tags on planner load; identified _plannerState.project fallback category issue causing null IDs; implementing force-reload logic with cache validation
- Planner UI tag visibility fix (2026-03-22) — Categories loading but tags not displaying in tag picker; implementing cache invalidation and re-render flow to resolve display issues
- Frontend code optimization (2026-03-22) — XSS fixes in markdown.js; 30s timeout in api.js; JSDoc documentation; setInterval cleanup in graph_workflow.js
- Backend startup race condition fix (2026-03-18) — Modified _continueToApp() retry logic to handle empty projects list on first load; project visibility bug investigation (AiCli not displaying as current in main project view)
- Memory items and project_facts population (pending) — Tables exist in schema but update logic not implemented; required for improved memory/context mechanism per original specification

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(105 events, 92 commits)`

### Doc_type

- **low-level-design** `(52 events, 50 commits)`
- **Test** `(28 events, 27 commits)`
- **high-level-design** `(1 events)`
- **retrospective**
- **customer-meeting** — dsds

### Feature

- **auth** `(97 events, 90 commits)`
- **UI** `(95 events, 87 commits)`
- **shared-memory** `(93 events, 87 commits)`
- **graph-workflow** `(84 events, 77 commits)`
- **workflow-runner** `(80 events, 77 commits)`
- **tagging** `(52 events, 50 commits)`
- **billing** `(51 events, 50 commits)`
- **mcp** `(51 events, 50 commits)`
- **embeddings** `(28 events, 27 commits)`
- **pagination**
- **test-picker-feature**
- **dropbox**

### Phase

- **development** `(93 events, 81 commits)`
- **discovery** `(92 events, 87 commits)`
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

**[2026-03-22]** `claude_cli` — Agent standardization initiative: each agent now requires defined system role, explicit prompts, input/output schema specification, and ReAct mode execution to prevent hallucination and ensure deterministic behavior. **[2026-03-22]** `frontend` — Tag visibility regression in planner UI; categories loading from DB but tags not rendering in picker. Root cause: _plannerState.project fallback causing null category IDs. Solution: implement aggressive cache invalidation on project/session switch with force DB reload. **[2026-03-22]** `frontend` — Code quality pass: XSS sanitization in markdown.js, 30s API timeout in api.js, JSDoc documentation, setInterval cleanup in graph_workflow.js to prevent memory leaks. **[2026-03-18]** `backend` — Backend startup race condition resolved: _continueToApp() retry logic now handles edge case where projects API returns success but empty list on first load (prevented false 'project not found' errors). **[2026-03-18]** `bug` — Project visibility timing issue: AiCli appears in Recent projects list but not rendering as active in main project view; suspected backend initialization race condition. **[2026-03-10]** `database` — Database performance optimization: implemented load-once-on-access pattern for tags (into memory on project load) to eliminate redundant SQL calls; only update DB on explicit save.