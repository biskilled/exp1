# Project Memory — aicli
_Generated: 2026-03-31 16:36 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform built on FastAPI + PostgreSQL + Electron, enabling collaborative AI work through semantic search, tagging, and workflow automation. Currently in Phase 1 stabilization with memory synthesis deployed, event tagging fully operational, and MCP integration validated; Phase 2 embedding refactor blocked pending clarification on memory table population logic and user-client schema relationship.

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
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; JSONL migration planned
- Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys
- All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); reduces token overhead
- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
- Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
- _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
- Embeddings linked to tags: tag metadata captures context (auth→all authentication prompts; feature/bug→relevant code changes)
- Backend modular: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic

## In Progress

- Memory table population design review: memory_items and project_facts tables not being populated per design spec; requires clarification on intended behavior before Phase 2 embedding refactor
- Backend startup race condition partially resolved: AiCli now appears in Recent projects but remains unavailable as selectable current project; acknowledged as dev environment delay
- Data persistence validation: tags disappearing on session switch—root cause under investigation (UI rendering vs. database save failure); /memory audit endpoint testing pending
- Embedding logic refactoring planned: Phase 2 work blocked pending clarification on memory table update logic and completion of existing issues
- Port binding stability confirmed: 127.0.0.1:8000 conflicts resolved; bash start_backend.sh initialization sequence documented
- User-client schema relationship confirmed: hierarchical structure validated (clients have multiple users); schema modification status unclear, may require database migration

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `prompt_batch: 8f29a8d3-13a3-42ed-9219-de7bfe53e3d2` — 2026-03-31

# Development Session Summary (2026-03-18)

**Resolved Issues:**
• **`ensure_project_schema` AttributeError** — Removed stale `db.ensure_project_schema(settings.active_project)` call from `main.py` that referenced non-existent database function; replaced with correct `_ensure_shared_schema` method
• **CLAUDE.md memory endpoint error** — Fixed line 1120 by defining missing `code_dir` variable to resolve runtime error when loading memory
• **Backend startup race condition** — Modified `_continueToApp` function to implement retry logic when projects load succeeds but returns empty array on initial startup

**Partially Resolved:**
• **Project visibility** — AiCli project now appears in Recent projects list, but remains unavailable as selectable current project; backend startup delay acknowledged as expected for dev environment (should resolve in production with persistent backend)

**Outstanding Issues:**
• **Memory mechanism implementation mismatch** — `memory_items` and `project_facts` tables not being updated according to design specification; requires clarification on intended behavior vs. current implementation
• **User-client schema relationship** — Confirmed hierarchical structure (clients have multiple users) but schema updates status unclear; may require database migration

**Action Items:** Investigate memory table update logic and complete user-client schema modifications

### `prompt_batch: 5b19c863-f99a-439c-b595-b415d0d342ed` — 2026-03-31

# Development Session Summary (2026-03-16)

- **Memory & Tagging System Audited**: Verified `event_tags_{project}` system is fully wired across chat, history sync, and retrieval; fixed PostgreSQL `ARRAY_AGG(uuid[])` bug causing tag aggregation failures

- **MCP Integration Validated**: Successfully tested end-to-end pipeline with direct HTTP calls using stored API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY from .env); MCP not yet active in session but `.mcp.json` configured

- **Memory Architecture Confirmed**: 5-part improvement system deployed—replaced noisy 40-entry JSONL dumps with synthesized summaries; reduces token overhead while improving context retrieval for complex projects

- **Workflow System Initiated**: Began design for workflow engine similar to specrails (DAG-based task execution); reviewed parent-child task relationships and default pipeline configuration in Planner tab

- **Outstanding**: Locate pipeline configuration source (default Pipeline in Planner tab); reconnect parent-child task hierarchy (UI → Dropbox example); integrate workflows with existing tagging system for better work item management

### `prompt_batch: 03f774e9-ad60-4cf3-8c0c-0191ba9a78d0` — 2026-03-31

# Development Session Summary (2026-03-10)

- **Fixed stale backend process**: Killed lingering uvicorn instance (PID 86671) blocking port 8000; restarted fresh backend

- **Resolved UI loading issues**: Confirmed clean restart process using `NODE_ENV=development` and Vite dev server from `ui/` directory after electron shutdown; port 8000 freed for backend

- **Optimized database queries**: Implemented single-load caching strategy in `chat.js` — tags/categories now loaded once when project opens and stored in memory via `_pickerPopulateCats()` function, eliminating redundant SQL calls during tag picker interactions

- **Designed nested tags architecture**: Confirmed feasibility of multi-level tag hierarchy; planned `parent_id` column addition to `entity_values` table to extend beyond original 2-level (category → tag) structure; clarified that new tags added via chat are always created at root level only

- **Database optimization strategy**: User requested consolidated SQL approach—load data once on project access, save updates only when explicitly saved (not on every change)

## AI Synthesis

**[2026-03-31]** `claude_cli` — Pre-Phase 2 review: user asks if memory table population and embedding refactor should proceed; outstanding issues blocking Phase 2 include memory_items/project_facts table update logic clarification and user-client schema relationship validation. **[2026-03-18]** `development` — Resolved ensure_project_schema AttributeError by replacing with _ensure_shared_schema; fixed CLAUDE.md line 1120 code_dir variable definition; implemented retry logic in _continueToApp for empty project list on startup. **[2026-03-16]** `audit` — Validated event_tags system fully wired across chat/history/retrieval; fixed PostgreSQL ARRAY_AGG(uuid[]) bug; confirmed 5-part memory synthesis reducing JSONL noise from 40 entries to synthesized summaries; MCP integration tested with stored API keys. **[2026-03-10]** `optimization` — Killed stale uvicorn (PID 86671); optimized database with single-load tag caching strategy in chat.js eliminating redundant SQL calls; designed nested tags architecture with parent_id column; consolidated SQL approach: load once on project access, save only on explicit save. **[2026-03-14]** `architecture` — Confirmed per-project schema tables structure (commits, events, embeddings, event_tags, event_links, memory_items, project_facts) and shared auth/usage tables; hierarchical data model (clients→users) with login_as_first_level_hierarchy pattern documented.