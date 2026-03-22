# Project Memory — aicli
_Generated: 2026-03-22 02:02 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform with a FastAPI backend, PostgreSQL semantic storage, and Electron/Vanilla JS frontend. It provides multi-provider LLM integration (Claude, OpenAI, etc.), async DAG workflow execution, encrypted per-user API key management, and dual-layer memory synthesis. Currently optimizing backend startup performance, consolidating data layer architecture with consistent dl_ prefixes, and cleaning UI code with JSDoc documentation and memory leak fixes.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free; encrypted API keys in database
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **memory_synthesis**: Claude Haiku for dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools; env var configured (BACKEND_URL, ACTIVE_PROJECT)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings; YAML for pipeline definitions; pyproject.toml and VS Code config for dev environment
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_usage/ (provider_costs.json, runtime data); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic; workspace/ stores per-project content; _system/ holds project state
- Dual storage: JSONL (history.jsonl with rotation) for primary; PostgreSQL 15+ with pgvector (1536-dim) for semantic search and indexed per-project tables
- Electron UI with xterm.js + Monaco + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys in database
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization
- Memory synthesis: Claude Haiku for dual-layer output (raw JSONL → interaction_tags → 5 files); smart chunking per language/section
- Backend modular organization: core/ for infrastructure (auth, config, database), data/ for data access (dl_ prefix), routers/ for HTTP endpoints, agents/ for business logic, pipelines/ for workflow engine
- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared tables: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)
- Encrypted API key storage in data layer (dl_api_keys.py); server-side key management only; clients never send API credentials
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); moved to agents/mcp/
- File-based configuration (api_keys.json) external to backend; sensitive data in .env; pricing/coupons/promotions managed in SQL tables
- Thin UI client: settings.json backed by Electron userData; remote server URL support; spawns backend only for local connections
- PyProject.toml and VS Code config for IDE support; absolute imports via sys.path; PyCharm: Mark backend/ as Sources Root

## In Progress

- Backend startup optimization and role initialization (2026-03-22) — Fixed slow loading; PostgreSQL agent roles configuration required; Planner, Pipeline, History/Runs endpoints verified working
- UI code optimization (2026-03-22) — Dead code removal (explorer.js, workflow.js, Cytoscape CDN); XSS fixes in markdown.js; 30s timeout in api.js; JSDoc documentation for 12 view files; setInterval cleanup in graph_workflow.js for memory leaks
- Backend module restructuring completion (2026-03-21-22) — Moved agents/tools, agents/mcp under agents/; renamed files with prefixes (tool_, pipeline_, pr_, dl_, mem_); extracted SQL queries to module-level constants; implemented build_update() for dynamic queries
- Data layer consolidation (2026-03-21-22) — Created dl_user.py, dl_api_keys.py (with encryption), dl_seq.py; removed core/encryption.py; merged encryption into dl_api_keys.py; moved provider_usage files to data/provider_usage/
- Configuration and authentication cleanup (2026-03-21-22) — Removed stale api_keys.json; externalized sensitive data to .env; implemented user-scoped encrypted API key storage in database; added PyProject.toml for IDE support
- Tags persistence and project visibility debugging (2026-03-18-22) — Tags saved in UI disappearing on session switch; AiCli appearing in Recent but not as active project; race condition fixes in initialization; continue investigating rendering vs. database save timing

## AI Synthesis

**[2026-03-22]** `backend optimization` — Fixed slow backend startup; verified Planner, Pipeline, History/Runs endpoints working; PostgreSQL agent roles configuration still required. **[2026-03-22]** `UI code cleanup` — Completed dead code removal (explorer.js, workflow.js, Cytoscape CDN); added XSS fixes (markdown.js), 30s timeout (api.js), JSDoc for 12 view files, setInterval cleanup (graph_workflow.js) to fix memory leaks. **[2026-03-21-22]** `backend restructure` — Reorganized agents/tools and agents/mcp under agents/; implemented consistent file prefixes (tool_, pipeline_, pr_, dl_, mem_); extracted 150+ SQL queries as module-level constants; implemented build_update() for safe dynamic UPDATE statements. **[2026-03-21-22]** `data layer consolidation` — Created dl_user.py, dl_api_keys.py (with encryption), dl_seq.py; removed core/encryption.py and stale api_keys.json; moved provider_usage to data/provider_usage/; all sensitive data now in .env. **[2026-03-21-22]** `configuration & IDE support` — Added PyProject.toml and VS Code launch.json for proper IDE debugging; fixed absolute import paths (sys.path via backend/ as Sources Root in PyCharm); externalized config to config.py. **[2026-03-18-22]** `session & visibility bugs` — Investigated tags disappearing on session switch (UI save vs DB persistence timing); AiCli appearing in Recent but not as active project; fixed race conditions in startup initialization; continues investigation needed.