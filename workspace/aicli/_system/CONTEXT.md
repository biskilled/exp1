# Project Context: aicli

> Auto-generated 2026-03-22 00:58 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 224
- **Last active**: 2026-03-22T00:58:06Z
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
- **memory_synthesis**: Claude Haiku for dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools; env var configured (BACKEND_URL, ACTIVE_PROJECT)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings, agent role providers; YAML config for pipeline definitions
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_usage/ (provider_costs.json, runtime data); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server

## In Progress

- Data layer refactoring (2026-03-22) — Extracted user CRUD, encrypted API key storage, and atomic ID allocation into data/ layer files (dl_user.py, dl_api_keys.py, dl_seq.py); core/ now pure infrastructure
- Query organization refactoring (2026-03-22) — Applied dynamic query templating and SQL constants extraction (~150 queries named _SQL_VERB_ENTITY) across 23 files; 5 agents complete with build_update() applied
- API keys.json file removal (2026-03-22) — Verified no remaining code paths write to data/api_keys.json; 35+ import sites validated; core/api_keys.py patterns clarified as data layer
- Data persistence bug investigation (2026-03-21) — Tags saved in UI disappear on session switch; root cause unclear (UI rendering vs. database save failure); investigation ongoing with project visibility timing issues
- Backend startup race condition resolution (2026-03-21) — Modified retry logic to handle empty project list on first load; AiCli visibility in Recent vs. main list still under investigation
- Memory items and project_facts table population (2026-03-18) — Tables created but update logic not yet implemented; blocking improved memory/context mechanism; requires implementation and testing

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic; workspace/ stores per-project content; _system/ holds project state
- Dual storage: JSONL (history.jsonl with rotation) for primary; PostgreSQL 15+ with pgvector (1536-dim) for semantic search and indexed per-project tables
- Electron UI with xterm.js + Monaco + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys in database
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization
- Memory synthesis: Claude Haiku for dual-layer output (raw JSONL → interaction_tags → 5 files); smart chunking per language/section
- Load-once-on-access pattern: cache tags/workflows/runs in memory; update DB only on explicit save to eliminate redundant SQL
- Nested tag hierarchy via parent_id FK with unlimited depth; login is first-level category only
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT)
- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for implementations (tool_ prefix)
- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern) in # ─── SQL ─── blocks; build_update() for dynamic UPDATEs
- _ensure_shared_schema pattern replaces ensure_project_schema for shared database initialization
- Port binding safety via freePort() to kill stale uvicorn; Electron cleanup via process.exit()

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

**[2026-03-22 00:12]** `claude_cli/claude`  
→ Can you make sure UI contain only client interface and backend manage all backend activity , as I would like to package 
← _Done. Here's what was implemented:  **`ui/electron/main.js`** - Added `loadSettings()` / `saveSettings()` backed by `Electron userData/settings.json` - `getServerUrl()` returns saved URL or `http://12_

**[2026-03-22 00:02]** `claude_cli/claude`  
→ Is there is a problen to remove data\api_keys.json 
← _Now verify nothing still writes `api_keys.json`:_

**[2026-03-22 00:00]** `claude_cli/claude`  
→ I do see the api_keys.json under backend\data folder. also when it removed - there are only 2 files remain, maybe it wil
← _Stale file + 35 import sites to update. Doing it all at once:_

**[2026-03-21 23:55]** `claude_cli/claude`  
→ I do api_keys.json under data which is not suppose to be at all (sensitive data). main app api keys are stored in my .en
← _**8 — Verify**_

**[2026-03-21 23:39]** `claude_cli/claude`  
→ yes please 
← _**Step 9 — Verify everything imports cleanly**_
