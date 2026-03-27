# Project Context: aicli

> Auto-generated 2026-03-27 09:35 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 270
- **Last active**: 2026-03-27T09:34:44Z
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
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel
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
- **billing_storage**: data/provider_usage/ (provider_costs.json, runtime data); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ per-project schema + shared auth/usage tables; agent roles initialized
- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost

## In Progress

- Backend startup stability (2026-03-26) — Documented proper backend initialization sequence: run `bash start_backend.sh` in terminal, keep window open; Electron UI auto-connects to localhost:8000; resolves intermittent port binding conflicts
- Frontend build and dev tooling (2026-03-23) — Fixed npm build failures (missing DMG background), restored ui/node_modules, verified Vite dev server and hot reload working; confirmed full setup sequence (kill, npm install, npm run dev)
- Feature/task/bug status workflow (2026-03-23) — Implement red 'add_info' status when description missing; green 'active' status when complete; enforce missing data detection at creation and sync with database
- Tag visibility and management (2026-03-23) — User requested review of current tags (bug/feature priority); implement tag management UI in Planner tab to surface and edit tags directly; confirm tag hierarchy persists across sessions
- Project visibility bug (2026-03-18) — AiCli appears in Recent projects but not displaying as current active project in main view; fixed stale db.ensure_project_schema() calls; backend startup race condition now handled by retry logic for empty project lists
- Memory items and project_facts table population (pending) — Tables exist in schema but update logic not implemented; required for improved memory/context mechanism and MCP data retrieval capability

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
- _ensure_shared_schema pattern replaces old ensure_project_schema method; retry logic handles empty project list on first load
- Backend startup via bash start_backend.sh; Electron app auto-connects to port 127.0.0.1:8000; keep terminal window open during dev

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

**[2026-03-27 09:28]** `claude_cli/claude`  
→ I do see that in any llm repsonse is summerised - when is it happend, can you also add all the internal prompt you are u
← _Now I'll append the full detailed sections to the existing file:_

**[2026-03-27 09:16]** `claude_cli/claude`  
→ you ddid mention anything about the mcp that is used for memroy as well , how the mcp works, what data it extract ? 
← _I have everything. Now let me add a comprehensive MCP section to the existing file:_

**[2026-03-27 09:07]** `claude_cli/claude`  
→ Allworks as expected. I would like to have full review on all memroy layers - what you are haveing now, when do you summ
← _Created `/Users/user/Documents/gdrive_cellqlick/2026/aicli/aicli_memory.md`.  Here's the summary of what's covered:  **5 Layers:** - **Layer 1** — In-memory only (current session messages, lost on exi_

**[2026-03-26 22:02]** `claude_cli/claude`  
→ how do I run the ui ? 

**[2026-03-26 21:59]** `claude_cli/claude`  
→ I closed all termianl , when I try to run, backend is not loading properly 
← _Backend is running now. For next time, **open a terminal and run**:  ```bash cd /Users/user/Documents/gdrive_cellqlick/2026/aicli/backend bash start_backend.sh ```  Keep that terminal window open whil_

**[2026-03-26 21:57]** `claude_cli/claude`  
→ I do not see the backend starting 
← _Backend is clean — no errors. Now can you clarify what "upload the AiCli project" means? Is it:  1. **Creating a new project workspace** called "aicli" in the UI? 2. **The project selector** in the UI_

**[2026-03-26 21:48]** `claude_cli/claude`  
→ The backend is not loading properly. Also I cannot upload the AiCli proejct 
← _Backend is clean — no errors. Now can you clarify what "upload the AiCli project" means? Is it:  1. **Creating a new project workspace** called "aicli" in the UI? 2. **The project selector** in the UI_

**[2026-03-24 15:36]** `claude_cli/claude`  
→ Can you proide short summery what is AiCli - I would like to add that into my website. it suppose to be the main tools I
← _# aicli — AI-Powered Development Platform  **Stop re-explaining your project to every AI tool. aicli gives every LLM the same shared memory — so Claude CLI, Cursor, your web UI, and your agents all pi_

**[2026-03-23 01:21]** `claude_cli/claude`  
→ yes
← _Pushed successfully. Here's what was done:  1. **Hook fix** — Removed `set -euo pipefail` from `auto_commit_push.sh`. That was the root cause: any command silently redirecting stderr to `/dev/null` (l_

**[2026-03-23 01:06]** `claude_cli/claude`  
→ There is again the problem with the hooks - Stop hook error: Failed with non-blocking status code: No stderr output. Als
← _The large Electron binaries (150+ MB) were added in commit `ae89abd` and deleted in `b416c01`, but GitHub still rejects because the blobs exist in the history being pushed. The cleanest fix is to squa_

**[2026-03-23 00:55]** `claude_cli/claude`  
→ I think there is another issue , as I cannot see any uodate at the UI . I dod location.reload(true) using the dev tools 
← _`ui/` is missing `node_modules`. You need to install dependencies first. Here's the full sequence:  ```bash # 1. Kill the old/ui Vite process kill -9 45399  # 2. Install dependencies in the correct ui_

**[2026-03-23 00:48]** `claude_cli/claude`  
→ When I run npm run build I still got an error - Error #1 ---------------------------------------------------------------
← _---  **What was wrong and how it's fixed:**  | Problem | Root cause | Fix | |---|---|---| | Can't open DevTools | No global shortcut registered; menu only | `globalShortcut.register(Cmd+Option+I)` + *_

**[2026-03-23 00:42]** `claude_cli/claude`  
→ I alway run using npm build dev (not npm run build) when I run npm run build I got errors regarding to old folder such a
← _---  **What was wrong and how it's fixed:**  | Problem | Root cause | Fix | |---|---|---| | Can't open DevTools | No global shortcut registered; menu only | `globalShortcut.register(Cmd+Option+I)` + *_

**[2026-03-23 00:35]** `claude_cli/claude`  
→ can you explain How should I force electorn to flash the memory as I do not see any change at the ui. is there is someth
← _---  **On forcing Electron to reload:**  There is no magic — Electron's renderer is essentially Chromium. Here's what to try, in order:  1. **Hard reload while app is open**: `Cmd+Shift+R` (Mac) — cle_

**[2026-03-23 00:21]** `claude_cli/claude`  
→ It is still not working . I thought to have new status (before active) - preq where all new features/bugs are in that st
← _Now quick syntax check:_
