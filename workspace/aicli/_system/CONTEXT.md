# Project Context: aicli

> Auto-generated 2026-03-22 01:20 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 231
- **Last active**: 2026-03-22T01:19:52Z
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

## In Progress

- UI code optimization (2026-03-22) — Dead code removal (explorer.js, workflow.js, Cytoscape CDN), utils cleanup with XSS fixes and 30s timeout, JSDoc documentation for all 12 view files, memory leak fixes in graph_workflow.js setInterval cleanup
- Data persistence bug investigation — Tags saved in UI disappear on session switch; debugging UI rendering vs. database save failure; project visibility timing issues with AiCli in Recent list
- Backend startup race condition — Retry logic modified to handle empty project list on first load; AiCli visibility in Recent vs. main list under investigation
- Project configuration management — Add pyproject.toml and VS Code config files (.vscode/) to support local development; ensure safe to commit with no secrets
- Memory items and project_facts population — Tables exist but update logic not implemented; required for improved memory/context mechanism
- Query organization refactoring — Applied dynamic query templating and SQL constants extraction (~150 queries) across 23 files; 5 agents complete with build_update() applied

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic; workspace/ stores per-project content; _system/ holds project state
- Dual storage: JSONL (history.jsonl with rotation) for primary; PostgreSQL 15+ with pgvector (1536-dim) for semantic search and indexed per-project tables
- Electron UI with xterm.js + Monaco + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys in database
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization
- Memory synthesis: Claude Haiku for dual-layer output (raw JSONL → interaction_tags → 5 files); smart chunking per language/section
- Load-once-on-access pattern: cache tags/workflows/runs in memory; update DB only on explicit save
- Nested tag hierarchy via parent_id FK with unlimited depth; login is first-level category only
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT)
- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for implementations (tool_ prefix)
- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update()
- _ensure_shared_schema pattern for shared database initialization
- Data layer owns encrypted API key storage; all encryption logic in dl_api_keys.py

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

**[2026-03-22 00:54]** `claude_cli/claude`  
→ ok. option B 
← _That's just a stale comment in `dl_seq.py` itself — the docstring example still says `from core.seq`. Fix it:_

**[2026-03-22 00:54]** `claude_cli/claude`  
→ I do see seq.py which I assume suppose to be part of database.py , is there is a reason to have 2 files ?
← _Done. The structure is now:  ``` core/      → infrastructure: database.py, auth.py, config.py, encryption.py, seq.py data/      → data layer:     dl_user.py, dl_api_keys.py  (+ future dl_events.py, dl_

**[2026-03-22 00:50]** `claude_cli/claude`  
→ So I prefer to store all data layer classes in data folder and have prefix dl_ about database.py - this is not a data la
← _Done. The structure is now:  ``` core/      → infrastructure: database.py, auth.py, config.py, encryption.py, seq.py data/      → data layer:     dl_user.py, dl_api_keys.py  (+ future dl_events.py, dl_

**[2026-03-22 00:47]** `claude_cli/claude`  
→ Ok. so user, api_keys is like a data layer (dl) that expose databse services to router ?
← _All 5 agents are done. Here's the complete summary of what was applied across all 23 files:  ---  **SQL constants extracted:** ~150 queries named `_SQL_VERB_ENTITY`, all placed in a `# ── SQL ──` bloc_

**[2026-03-22 00:41]** `claude_cli/claude`  
→ What about core/user , this is not suppose to be as a router ? I do do see router_user_api_key as well - it is not the s
← _Good question — same pattern as `core/auth.py` vs `routers/route_auth.py`:  **`core/user.py`** — data access library. Contains `create_user()`, `find_by_id()`, `authenticate()`, `list_users()`, `updat_

**[2026-03-22 00:30]** `claude_cli/claude`  
→ scope - apply to all files, Dynamic - try to use tamplate (maybe add that into database.py file). also please review eac
← _Let me launch the remaining router file groups in parallel while the first two agents run._

**[2026-03-22 00:27]** `claude_cli/claude`  
→ is there is a way to manage the queries better, maybe to define quesried at the begining of each file ? 
← _Let me look at a couple of files to understand the current pattern first._

**[2026-03-22 00:25]** `claude_cli/claude`  
→ Basicly all files under route can use db quesries. Is there is any other place that using db queries ?
← _They serve different purposes — no duplication:  - **`core/auth.py`** — shared library: JWT encode/decode, `hash_password`, `verify_password`, `get_current_user` / `get_optional_user` FastAPI dependen_

**[2026-03-22 00:21]** `claude_cli/claude`  
→ I still see duplicate - under core I do see auth.py and under route - raute_auth.py why there are 2 files ?
← _They serve different purposes — no duplication:  - **`core/auth.py`** — shared library: JWT encode/decode, `hash_password`, `verify_password`, `get_current_user` / `get_optional_user` FastAPI dependen_
