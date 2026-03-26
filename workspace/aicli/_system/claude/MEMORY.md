# Project Memory — aicli
_Generated: 2026-03-26 21:58 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel
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
- **database**: PostgreSQL 15+ per-project schema + shared auth/usage tables; agent roles initialized
- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost

## Key Decisions

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
- Dual storage: JSONL (history.jsonl with rotation) for primary history; PostgreSQL 15+ with pgvector (1536-dim) for semantic search and per-project indexed tables
- Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys in database
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); smart chunking per language/section
- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared auth/usage tables
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- Backend modular organization: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
- Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
- Encrypted API key storage in data layer (dl_api_keys.py); server-side key management only; clients never send API credentials
- _ensure_shared_schema pattern replaces old ensure_project_schema method; retry logic handles empty project list on first load

## In Progress

- Frontend build tooling fix (2026-03-23) — Resolved `npm run build` failing on missing DMG background image in old/ folder; confirmed ui/node_modules missing and reinstalled dependencies; verified Vite dev server and dev tools shortcuts (Cmd+R, Cmd+Option+I) now functional
- UI update visibility issue (2026-03-23) — Debugged changes not reflecting in browser; root cause was missing node_modules in ui/ directory; confirmed full setup sequence (kill processes, npm install, npm run dev) restores hot reload functionality
- Feature/task/bug status workflow (2026-03-23) — Implement red 'add_info' status when description missing; green 'active' status when complete; user reports status not visible in UI Planner tab; enforce missing data detection at creation and sync with database
- Tag visibility and review (2026-03-23) — User requested review of current tags (bug/feature priority); implement tag management UI in Planner tab to surface and edit tags directly; confirm tag hierarchy persists across sessions
- Project visibility bug (2026-03-18) — AiCli appears in Recent projects but not displaying as current active project in main project view; timing issue during backend initialization; requires further investigation and fix
- Memory items and project_facts table population (pending) — Tables exist in schema but update logic not implemented; required for improved memory/context mechanism and MCP data retrieval

## Recent Work (last 10 exchanges)

**[2026-03-26 21:57]** `claude_cli/claude`
Q: I do not see the backend starting
A: Backend is clean — no errors. Now can you clarify what "upload the AiCli project" means? Is it:  1. **Creating a new project workspace** called "aicli" in the UI? 2. **The project selector** in the UI not showing/loading the project? 3. **Something specific** in the Settings or Admin tab?  Also — ar

**[2026-03-26 21:48]** `claude_cli/claude`
Q: The backend is not loading properly. Also I cannot upload the AiCli proejct
A: Backend is clean — no errors. Now can you clarify what "upload the AiCli project" means? Is it:  1. **Creating a new project workspace** called "aicli" in the UI? 2. **The project selector** in the UI not showing/loading the project? 3. **Something specific** in the Settings or Admin tab?  Also — ar

**[2026-03-24 15:36]** `claude_cli/claude`
Q: Can you proide short summery what is AiCli - I would like to add that into my website. it suppose to be the main tools I am using to help customer build project fast and scalblae. pleae explain (marke
A: # aicli — AI-Powered Development Platform  **Stop re-explaining your project to every AI tool. aicli gives every LLM the same shared memory — so Claude CLI, Cursor, your web UI, and your agents all pick up exactly where you left off.**  ---  ## What Is aicli?  aicli is a development acceleration pla

**[2026-03-23 01:21]** `claude_cli/claude`
Q: yes
A: Pushed successfully. Here's what was done:  1. **Hook fix** — Removed `set -euo pipefail` from `auto_commit_push.sh`. That was the root cause: any command silently redirecting stderr to `/dev/null` (like `git add -A 2>/dev/null`) would cause the script to exit 1 with no output — exactly the "No stde

**[2026-03-23 01:06]** `claude_cli/claude`
Q: There is again the problem with the hooks - Stop hook error: Failed with non-blocking status code: No stderr output. Also I remove the old folder from the project
A: The large Electron binaries (150+ MB) were added in commit `ae89abd` and deleted in `b416c01`, but GitHub still rejects because the blobs exist in the history being pushed. The cleanest fix is to squash those 4 unpushed commits — since the large files were added then deleted, they'll cancel out in t

**[2026-03-23 00:55]** `claude_cli/claude`
Q: I think there is another issue , as I cannot see any uodate at the UI . I dod location.reload(true) using the dev tools - but nothing is changed
A: `ui/` is missing `node_modules`. You need to install dependencies first. Here's the full sequence:  ```bash # 1. Kill the old/ui Vite process kill -9 45399  # 2. Install dependencies in the correct ui/ directory cd /Users/user/Documents/gdrive_cellqlick/2026/aicli/ui npm install  # 3. Start the app 

**[2026-03-23 00:48]** `claude_cli/claude`
Q: When I run npm run build I still got an error - Error #1 -------------------------------------------------------------------------------- Error: ENOENT: no such file or directory, stat '/Users/user/Do
A: ---  **What was wrong and how it's fixed:**  | Problem | Root cause | Fix | |---|---|---| | Can't open DevTools | No global shortcut registered; menu only | `globalShortcut.register(Cmd+Option+I)` + **auto-opens DevTools in dev mode** | | Changes don't show | Cmd+R not registered as global shortcut 

**[2026-03-23 00:42]** `claude_cli/claude`
Q: I alway run using npm build dev (not npm run build) when I run npm run build I got errors regarding to old folder such aicli/old/ui/static/dmg-bg.png is not exists - Error: ENOENT: no such file or dir
A: ---  **What was wrong and how it's fixed:**  | Problem | Root cause | Fix | |---|---|---| | Can't open DevTools | No global shortcut registered; menu only | `globalShortcut.register(Cmd+Option+I)` + **auto-opens DevTools in dev mode** | | Changes don't show | Cmd+R not registered as global shortcut 

**[2026-03-23 00:35]** `claude_cli/claude`
Q: can you explain How should I force electorn to flash the memory as I do not see any change at the ui. is there is something more distinct than task (I think its good for now). maybe it will be easier 
A: ---  **On forcing Electron to reload:**  There is no magic — Electron's renderer is essentially Chromium. Here's what to try, in order:  1. **Hard reload while app is open**: `Cmd+Shift+R` (Mac) — clears the renderer cache for this session 2. **Open DevTools first** (`Cmd+Option+I`), then reload — D

**[2026-03-23 00:21]** `claude_cli/claude`
Q: It is still not working . I thought to have new status (before active) - preq where all new features/bugs are in that status if there is missing data such as description . I annot see that in the UI /
A: Now quick syntax check:
