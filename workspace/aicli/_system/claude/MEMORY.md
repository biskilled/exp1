# Project Memory — aicli
_Generated: 2026-03-22 02:06 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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

## Recent Work (last 10 exchanges)

**[2026-03-22 02:04]** `claude_cli/claude`
Q: I still do not see All Planner tags (categroeis, existing tags...) also Pipelines are not loading
A: Good — `source-tags` already has the fallback. Now restart and test all four:

**[2026-03-22 01:55]** `claude_cli/claude`
Q: looks better. planner is loading well. Also there is an issue with Roles (PostgreSQL required agent roles) Also Pipeline and History/Runs is loading well
A: Now restart the backend and verify both endpoints:

**[2026-03-22 01:35]** `claude_cli/claude`
Q: I do see that backend is failing to start (it also take quite a while to load )
A: Now verify the backend starts immediately:

**[2026-03-22 01:26]** `claude_cli/claude`
Q: I have created pyproject.toml manualy. can you update that file again ? also I do see error in stop hook which preventing to push the new updates
A: Push succeeded — no force needed since the rewritten commits built on the same base. Now fix `pyproject.toml`:

**[2026-03-22 01:13]** `claude_cli/claude`
Q: Now, code looks more optimised. can you do the same for the ui code- make sure all code is well defined, documented, there are not old or unsued code, and make sure to code is clean, and optimized fro
A: 4 agents running in parallel:  1. **Dead code removal** — deleting `explorer.js`, `workflow.js`, removing Cytoscape CDN from `index.html` 2. **Utils cleanup** — fixing XSS in `markdown.js`, adding 30s timeout to `api.js`, adding module docs to all 7 utils 3. **View docs** — adding JSDoc comments to 

**[2026-03-22 01:10]** `claude_cli/claude`
Q: Can you add the pyproject.toml (can be pushed to git as well)
A: Also add the VS Code config (safe to commit, no secrets):

**[2026-03-22 01:07]** `claude_cli/claude`
Q: I do see that when you use import you are using relative import for example from core.config import settings. which are not support when I am working in Pycharm ide. (only long one such from aicli.bac
A: These are not relative imports — they're **absolute imports that assume `backend/` is on `sys.path`**. They work when you `cd backend && uvicorn main:app` because Python adds the CWD to `sys.path`. The IDE just doesn't know that.  ## Fix for both IDEs  **Option A — Simplest (PyCharm only)**  Right-c

**[2026-03-22 01:03]** `claude_cli/claude`
Q: Is it worth to change core to shared (folder name) ?
A: Not really worth it. `core/` is the standard Python/FastAPI convention for foundational infrastructure — config, auth, DB pool. `shared/` is more of a frontend/JS pattern and is vaguer ("shared by whom?").  The contents you have (`config.py`, `auth.py`, `database.py`) are genuinely *core infrastruct

**[2026-03-22 00:59]** `claude_cli/claude`
Q: Ok. ,erge encryption to dl_api_keys
A: Done. `core/encryption.py` deleted, and no remaining references to it anywhere in the backend.

**[2026-03-22 00:57]** `claude_cli/claude`
Q: For what encryption is used for ? also auth - is is looks like a general auth , it is not part of route ?
A: Done. `data/` layer now has three files:  ``` data/   dl_user.py      — user CRUD   dl_api_keys.py  — encrypted key storage     dl_seq.py       — atomic sequential ID allocation ```  `core/` is now pure infrastructure: `database.py`, `auth.py`, `config.py`, `encryption.py`.
