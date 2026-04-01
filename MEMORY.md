# Project Memory — aicli
_Generated: 2026-04-01 08:56 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that unifies development context across Claude CLI, LLM assistants, and web/desktop UIs through PostgreSQL semantic storage (pgvector), async DAG workflows, and Claude Haiku-powered memory synthesis. The desktop application combines Electron with Vanilla JS, xterm.js, Monaco editor, and Cytoscape.js for workflow visualization and terminal interaction; the backend is FastAPI-based with multi-provider LLM adapter support and MCP server integration. Current focus is stabilizing the unified mem_ai_* event/fact/work-item table schema, resolving data persistence across session switches, and automating memory file generation with proper cache management.

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
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
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
- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + ui/npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic; workspace/ holds per-project content; _system/ stores project state
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- Electron desktop UI: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vanilla JS frontend (no framework/bundler); Vite dev server
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients contain Users; login_as_first_level_hierarchy pattern
- All LLM providers as independent adapters (Claude/OpenAI/DeepSeek/Gemini/Grok); Claude Haiku for dual-layer memory synthesis; server holds API keys
- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for negotiation
- Memory synthesis: Claude Haiku dual-layer generates 5 files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load; backend_startup_race_condition mitigated
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations (linked via row id), not in summary arrays
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements; smart chunking by per-class/function (Python/JS/TS), per-section (MD), per-file (diff)
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
- CLI: Python 3.12 + prompt_toolkit + rich; command routing via verb-noun pattern; memory endpoint template variable scoping fixed
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local dev via bash start_backend.sh + ui/npm run dev
- Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing_storage in data/provider_storage/

## In Progress

- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from unified mem_ai_* tables with timestamp tracking
- Unified event table validation: mem_ai_events consolidates embeddings and memory events; removed event_summary_tags array and deprecated metadata columns
- Data persistence validation: tags disappearing on session switch root cause traced to cache invalidation triggering DB re-load; fix ensures persistence across switches
- Schema documentation cleanup: updated project_state.json and rules.md to reflect mem_ai_* unified table naming and removed deprecated database_schema field
- Tag column schema correction: mem_ai_tags_relations table DDL fixed; database migrations applied and persistence validated across session switches
- Backend startup race condition: AiCli appearing in Recent projects but unselectable on first load; retry logic implemented for empty project list handling

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `role` — 2026-04-01

## Output

Always output structured JSON with score (1-10), approved (bool), issues (list), summary.
Score >= 8 → approved. No critical issues → approved regardless of minor issues.


### `role` — 2026-04-01

## Minor Issues (note but don't block)
- Style inconsistencies with the existing codebase
- Missing type hints on new code
- Missing docstrings on public functions
- Overly verbose variable names


### `role` — 2026-04-01

## Critical Issues (block approval)
- Logic bugs that will cause incorrect behaviour
- Security vulnerabilities (shell injection, path traversal, secret exposure)
- Unhandled exceptions that will crash the program
- Breaking changes to existing interfaces


### `role` — 2026-04-01

## Your Review Process

1. Read the full code before commenting — understand intent before critiquing
2. Distinguish critical issues (bugs, security) from minor suggestions (style)
3. Be specific: "line 45 uses str() instead of Path()" not "use Path objects"
4. Suggest fixes, not just problems
5. Acknowledge strengths — good code deserves recognition


### `role` — 2026-04-01

# Expert Code Reviewer

You are an expert Python code reviewer with a focus on production-quality software.


### `role` — 2026-04-01

## Code Quality Standards

- All functions have type hints
- All file paths use `Path` objects
- No raw `print()` in library code — use `console.print()` or `logger`
- Exception messages tell the user what to do, not just what went wrong
- New modules get a one-paragraph docstring explaining why they exist


## AI Synthesis

**2026-03-14** `schema` — Unified event table (mem_ai_events) consolidated embeddings and memory events; removed deprecated event_summary_tags array and metadata columns to simplify schema. **2026-03-14** `persistence` — Root cause of tag disappearance on session switch traced to cache invalidation triggering unintended DB re-load; fixed via proper cache lifecycle management. **2026-03-14** `memory_synthesis** — Claude Haiku dual-layer memory generation automated to produce 5 standardized files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) with timestamp tracking from unified mem_ai_* tables. **2026-03-14** `startup** — Backend startup race condition (AiCli in Recent projects but unselectable) mitigated with retry logic for empty project list on first load. **2026-03-14** `config** — Schema documentation refreshed: project_state.json and rules.md updated to reflect mem_ai_* unified table naming; deprecated database_schema field removed. **2026-03-14** `relations** — Manual relation management (depends_on, relates_to, blocks, implements) integrated via CLI/admin UI with smart chunking strategies (per-class/function for code, per-section for markdown, per-file for diffs).