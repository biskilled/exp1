# Project Context: aicli

> Auto-generated 2026-03-22 02:52 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 242
- **Last active**: 2026-03-22T02:51:37Z
- **Last provider**: claude
- **Version**: 2.1.0

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

## In Progress

- Tags persistence and cache loading (2026-03-22) — Identified _plannerState.project fallback category issue causing null IDs; implemented force-reload logic in _initPlanner with cache validation check and auto-select of first real category
- Planner UI tag visibility fix (2026-03-22) — Categories loading but tags not displaying; implementing cache invalidation and re-render flow to ensure full tag hierarchy loads on session/project switch; anyValuesFallback check prevents stale cache
- Backend module restructuring completion (2026-03-21-22) — Renamed files with prefixes (tool_, pipeline_, pr_, dl_, mem_); extracted SQL queries to module-level constants; reorganized agents/ folder; removed stale core/encryption.py
- Database initialization and PostgreSQL agent roles (2026-03-22) — Verified agent roles have real IDs (10+); confirmed router endpoints query correct tables per project; eliminated fallback workarounds from planner initialization
- Frontend code optimization (2026-03-22) — XSS fixes in markdown.js; 30s timeout in api.js; JSDoc documentation; setInterval cleanup in graph_workflow.js to prevent memory leaks
- Memory items and project_facts population (pending) — Tables exist in schema but update logic not implemented; required for improved memory/context mechanism per specification

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic; workspace/ stores per-project content; _system/ holds project state
- Dual storage: JSONL (history.jsonl with rotation) for primary; PostgreSQL 15+ with pgvector (1536-dim) for semantic search and indexed per-project tables
- Electron UI with xterm.js + Monaco + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys in database
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); smart chunking per language/section
- Backend modular organization: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared tables for users/usage/auth
- Encrypted API key storage in data layer (dl_api_keys.py); server-side key management only; clients never send API credentials
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
- PostgreSQL agent roles properly initialized with real IDs; router mapping queries correct tables per project; no fallback workarounds
- File-based configuration (api_keys.json) external to backend; sensitive data in .env; pricing/coupons managed in SQL tables
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB; UI renders from in-memory cache

---

## Project Documentation (PROJECT.md)

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-14 | Version 2.2.0_

---

## Vision

**aicli gives every LLM the same project memory.**

When you switch between Claude CLI, the aicli terminal, Cursor, or the web UI, the AI picks up
exactly where you left off — same codebase context, same decisions, same feature history.
No more copy-pasting context. No more re-explaining your architecture.

---

## Core Goals

| # | Goal | Status |
|---|------|--------|
| 1 | **Shared LLM memory** — Claude CLI, aicli CLI, Cursor, UI all read the same knowledge base | ✓ Implemented |
| 2 | **Prompt management** — Role-based agents (architect, developer, reviewer, QA, security, devops) | ✓ Implemented |
| 3 | **5-layer memory** — Immediate → Working → Project → Historical → Global | ✓ Implemented |
| 4 | **Auto-deploy** — pull → commit → push after every AI session | ✓ Hooks + git.py |
| 5 | **Billing & usage** — Multi-user, server keys, balance, markup, coupons | ✓ Implemented |
| 6 | **Multi-LLM workflows** — Graph DAG: design → review → develop → test | ✓ Implemented |
| 7 | **Entity/knowledge graph** — Tag every event (prompt/commit) to features, bugs, tasks | ✓ Implemented |
| 8 | **Semantic search** — pgvector cosine similarity over chunked history + code | ✓ Implemented |
| 9 | **Project management UI** — Unified Planner: 2-pane tag manager, per-entry tagging, commit linking | ✓ Implemented |

---

## 5-Layer Memory Architecture

```
Layer 1 — Immediate Context
  └── providers/{claude,openai,...}.messages  (in-memory, not persisted)
      Live conversation: current prompt chain within the session

Layer 2 — Working Memory
  └── {cli_data_dir}/sessions/{provider}_messages.json
  └── {cli_data_dir}/session_state.json
      Short-term task state: active feature, tag, last commit, cross-provider handoff

Layer 3 — Project Knowledge
  └── workspace/{project}/PROJECT.md          — living project doc (this file)
  └── workspace/{project}/_system/project_state.json  — structured metadata + next_phase_plan
  └── workspace/{project}/_system/CLAUDE.md   — synced to code_dir/CLAUDE.md for Claude Code

Layer 4 — Historical Knowledge
  └── workspace/{project}/_system/history.jsonl    — all interactions (UI + CLI + workflow + Cursor)
  └── workspace/{project}/_system/events_{p}       — PostgreSQL event log, tagged to features/bugs
      Past decisions, design discussions, feature history, bug postmortems, refactor notes

Layer 5 — Global Knowledge
  └── workspace/_templates/hooks/                  — canonical hook scripts for all projects
  └── workspace/_templates/{blank,python_api,...}  — project starter templates
  └── workspace/_templates/workflows/              — shared workflow YAML library (planned)
  └── workspace/_templates/roles/                  — shared AI role prompts (planned)
```

### How `/memory` syncs layers 3–5 to every LLM tool

```
_system/claude/CLAUDE.md   →  {code_dir}/CLAUDE.md                    ← Claude Code reads at start
_system/claude/MEMORY.md   →  {code_dir}/MEMORY.md                    ← referenced in CLAUDE.md
_system/cursor/rules.md    →  {code_dir}/.cursor/rules/aicli.mdrules  ← Cursor reads on open
_system/aicli/context.md   →  prepended to every aicli CLI prompt      ← all providers
_system/aicli/copilot.md   →  {code_dir}/.github/copilot-instructions.md
```

---

## Architecture

### Engine / Workspace Separation

```
aicli/                     ← ENGINE — code only, no project-specific content
├── cli.py                 ← Interactive REPL (prompt_toolkit + rich)


*...303 more lines in PROJECT.md*

---

## Recent Development History

**[2026-03-22 02:49]** `claude_cli/claude`  
→ Is it possilbe to creatre skeen that run my aiCli commands from Claude CLI - for example /ac /memory - will run my memor

**[2026-03-22 02:48]** `claude_cli/claude`  
→ This is still not working. I dont see tags loading at all (just empty categories)
← _Good — the backend correctly returns `fallback: True` when DB is unavailable.  The full fix chain now is: - **`tagCache.js`**: checks `vData.fallback` per-category — if any values came back as fallbac_

**[2026-03-22 02:39]** `claude_cli/claude`  
→ Planner still dont load all tags , all I see is ctegories
← _`_plannerState.project` is set. The fix is correct.  The changes make three improvements:  1. **`_initPlanner`**: detects fallback categories (null IDs) and force-reloads the cache with `force=true` b_

**[2026-03-22 02:34]** `claude_cli/claude`  
→ I do see categroeis uploaded in Planner tab, but I do not see all the tags in each categroy. Also I do got an error when
← _Now restart the backend and verify both fixes:_

**[2026-03-22 02:07]** `claude_cli/claude`  
→ PostgreSql is up and running, why do you build a workaround. it looks like router mappig not query the proper tables
← _DB is connected — roles have real IDs (`id: 10`, no fallback). Let me verify all the previously-failing endpoints:_

**[2026-03-22 02:04]** `claude_cli/claude`  
→ I still do not see All Planner tags (categroeis, existing tags...) also Pipelines are not loading 
← _Good — `source-tags` already has the fallback. Now restart and test all four:_

**[2026-03-22 01:55]** `claude_cli/claude`  
→ looks better. planner is loading well. Also there is an issue with Roles (PostgreSQL required agent roles) Also Pipeline
← _Now restart the backend and verify both endpoints:_

**[2026-03-22 01:35]** `claude_cli/claude`  
→ I do see that backend is failing to start (it also take quite a while to load ) 
← _Now verify the backend starts immediately:_

**[2026-03-22 01:26]** `claude_cli/claude`  
→ I have created pyproject.toml manualy. can you update that file again ? also I do see error in stop hook which preventin
← _Push succeeded — no force needed since the rewritten commits built on the same base. Now fix `pyproject.toml`:_

**[2026-03-22 01:13]** `claude_cli/claude`  
→ Now, code looks more optimised. can you do the same for the ui code- make sure all code is well defined, documented, the
← _4 agents running in parallel:  1. **Dead code removal** — deleting `explorer.js`, `workflow.js`, removing Cytoscape CDN from `index.html` 2. **Utils cleanup** — fixing XSS in `markdown.js`, adding 30s_

**[2026-03-22 01:10]** `claude_cli/claude`  
→ Can you add the pyproject.toml (can be pushed to git as well) 
← _Also add the VS Code config (safe to commit, no secrets):_

**[2026-03-22 01:07]** `claude_cli/claude`  
→ I do see that when you use import you are using relative import for example from core.config import settings. which are 
← _These are not relative imports — they're **absolute imports that assume `backend/` is on `sys.path`**. They work when you `cd backend && uvicorn main:app` because Python adds the CWD to `sys.path`. Th_

**[2026-03-22 01:03]** `claude_cli/claude`  
→ Is it worth to change core to shared (folder name) ? 
← _Not really worth it. `core/` is the standard Python/FastAPI convention for foundational infrastructure — config, auth, DB pool. `shared/` is more of a frontend/JS pattern and is vaguer ("shared by who_

**[2026-03-22 00:59]** `claude_cli/claude`  
→ Ok. ,erge encryption to dl_api_keys 
← _Done. `core/encryption.py` deleted, and no remaining references to it anywhere in the backend._

**[2026-03-22 00:57]** `claude_cli/claude`  
→ For what encryption is used for ? also auth - is is looks like a general auth , it is not part of route ? 
← _Done. `data/` layer now has three files:  ``` data/   dl_user.py      — user CRUD   dl_api_keys.py  — encrypted key storage     dl_seq.py       — atomic sequential ID allocation ```  `core/` is now pu_
