# Project Memory — aicli
_Generated: 2026-03-30 16:52 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling Claude CLI and other LLM platforms to access persistent work context across sessions through a hierarchical data model (Clients → Users → Projects) with PostgreSQL semantic storage, MCP integration for embedding-based retrieval, and async DAG workflow execution. Currently at v2.2.0 with 16 active features/tasks spanning UI, authentication, shared memory, tagging, billing, and embeddings; near-term focus on resolving data persistence bugs, completing memory table population, and consolidating JSONL/DB storage layers.

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
- **storage_primary**: PostgreSQL 15+ with per-project schema
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools; env var configured (BACKEND_URL, ACTIVE_PROJECT)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash start_backend.sh + ui/npm run dev; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ per-project schema + shared auth/usage tables; agent roles initialized
- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server on localhost

## Key Decisions

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
- Dual storage model transitioning to DB-only: PostgreSQL 15+ with pgvector (1536-dim) for semantic search; JSONL migration planned
- Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys
- All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); smart chunking per language/section
- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared auth/usage tables
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
- Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
- _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
- Embeddings linked to tags: tag metadata captures context (auth→all authentication prompts; feature/bug→relevant code changes)
- Backend modular: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic

## In Progress

- Data persistence bug: tags disappear on session switch—root cause investigation ongoing; unclear if UI rendering vs database save failure; requires validation via /memory audit
- Memory_items and project_facts table population not implemented—per specification these tables should update to enable improved memory/context mechanism; PENDING implementation and testing
- Project visibility bug investigation—AiCli appears in Recent projects but not displaying as current active project in main view; suspected timing issue during backend initialization
- Backend startup stability fixes—resolved port 127.0.0.1:8000 binding conflicts; documented proper initialization sequence via bash start_backend.sh; retry logic handles empty project list on first load
- Memory endpoint CLAUDE.md template validation—code_dir variable scoped/fixed at line 1120 to resolve runtime failures; endpoint template variable scoping now correct
- JSONL vs. database storage consolidation—migrate away from dual JSONL/DB storage toward DB-only tables to simplify data persistence and eliminate redundant calls

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(139 events, 121 commits)`

### Doc_type

- **Test** `(58 events, 56 commits)`
- **low-level-design** `(52 events, 50 commits)`
- **high-level-design** `(31 events, 29 commits)`
- **retrospective** `(30 events, 29 commits)`
- **customer-meeting** — dsds

### Feature

- **UI** `(126 events, 116 commits)`
- **shared-memory** `(125 events, 116 commits)`
- **auth** `(125 events, 117 commits)`
- **graph-workflow** `(115 events, 106 commits)`
- **tagging** `(82 events, 79 commits)`
- **billing** `(82 events, 79 commits)`
- **mcp** `(81 events, 79 commits)`
- **workflow-runner** `(80 events, 77 commits)`
- **embeddings** `(60 events, 56 commits)`
- **test-picker-feature** `(30 events, 29 commits)`
- **pagination**
- **dropbox**

### Phase

- **discovery** `(122 events, 116 commits)`
- **development** `(121 events, 108 commits)`
- **prod**

### Task

- **memory** `(79 events, 66 commits)`
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

**2026-03-18** `SESSION_SUMMARY` — Removed stale `ensure_project_schema()` call from main.py; fixed memory endpoint CLAUDE.md `code_dir` variable scoping at line 1120; enhanced backend startup retry logic to handle edge case where projects list returns empty on first load. **2026-03-14** `PROJECT_STATE` — Confirmed hierarchical data model (Clients → Users); identified 16 active feature/task/bug entities with 1,200+ total events/commits; documented memory management patterns and tag persistence issue requiring investigation. **2026-03-10** `ARCHITECTURE_AUDIT` — Implemented load-once tag caching strategy on project access to reduce redundant SQL calls; approved nested tag hierarchy expansion; discovered critical data persistence bug where tags disappear on session switch; identified UI visibility issues for memory suggestions and action buttons. **2026-03-10** `STABILITY_FIXES` — Resolved port 127.0.0.1:8000 binding conflicts through documented bash start_backend.sh initialization sequence; stabilized backend startup race condition handling. **PENDING** — memory_items and project_facts table update logic not yet implemented; project visibility bug requires further investigation; JSONL-to-DB migration needed to eliminate dual storage complexity.