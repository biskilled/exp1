# Project Context: aicli

> Auto-generated 2026-03-30 16:52 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 296
- **Last active**: 2026-03-30T16:52:31Z
- **Last provider**: claude
- **Version**: 2.1.0

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

## In Progress

- Data persistence bug: tags disappear on session switch—root cause investigation ongoing; unclear if UI rendering vs database save failure; requires validation via /memory audit
- Memory_items and project_facts table population not implemented—per specification these tables should update to enable improved memory/context mechanism; PENDING implementation and testing
- Project visibility bug investigation—AiCli appears in Recent projects but not displaying as current active project in main view; suspected timing issue during backend initialization
- Backend startup stability fixes—resolved port 127.0.0.1:8000 binding conflicts; documented proper initialization sequence via bash start_backend.sh; retry logic handles empty project list on first load
- Memory endpoint CLAUDE.md template validation—code_dir variable scoped/fixed at line 1120 to resolve runtime failures; endpoint template variable scoping now correct
- JSONL vs. database storage consolidation—migrate away from dual JSONL/DB storage toward DB-only tables to simplify data persistence and eliminate redundant calls

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

**[2026-03-30 16:49]** `claude_cli/claude`  
→ Is all table strucure is implemeted properly ? I dont see the table strucure ? 
← _All 9 new memory infra tables are now created. Here's the summary:  **✅ New tables (9/9 created):** - `mng_tags_categories` — global tag categories - `pr_tags` — per-project tag hierarchy - `pr_tag_me_

**[2026-03-30 16:42]** `claude_cli/claude`  
→ It it still balnck. the error is Uncaught SyntaxError: Identifier '_esc' has already been declared there is also warning
← _Done. Two fixes applied:  1. **`graph_workflow.js`** — removed the duplicate `function _esc` at line 2130 (the one at line 431 is kept). This was the exact cause of `Uncaught SyntaxError: Identifier '_

**[2026-03-30 16:24]** `claude_cli/claude`  
→ Backend looks like it is running. when I run npm start - it looks like electron app is running, but nothing is showing a
← _Now let me verify the final state of the key section of `main.js`:_

**[2026-03-30 16:13]** `claude_cli/claude`  
→ Looks better. Now UI is using exisitng backend, but UI is not loading properly. I dont see anything (backend is running)
← _Good. Now let me also verify the Vite dev server is accessible — the UI will try to connect to `localhost:5173` when it can't find `dist`:_

**[2026-03-30 16:02]** `claude_cli/claude`  
→ Can you recheck, ui is not loading well. please remove the developer tools when I start ui. also when I start ui - it is
← _Now I have the full file. Let me write the updated `aicli_memory.md`:_

**[2026-03-30 15:10]** `claude_cli/claude`  
→ I would like to update my memory infrastrucutre, in order to have more reliable layers, better prompting capabilties and

**[2026-03-28 11:03]** `claude_cli/claude`  
→ What is the pr_event_links is used for ? how it is linking events?
← _`api.entities.getLinks` exists in `api.js` but is **never called from any view** — so `pr_event_links` is populated (by commit/sync hooks) but never surfaced in the current UI.  ---  ## Summary  | Pur_

**[2026-03-28 10:40]** `claude_cli/claude`  
→ What event insert into event table except prompts and new commits 
← _`pr_events` only ever gets **two event types**:  | `event_type` | Written by | Source | |---|---|---| | `prompt` | `route_chat.py` `_append_history()` | Every chat exchange (UI + hooks) | | `prompt` |_

**[2026-03-28 10:13]** `claude_cli/claude`  
→ Yes please do that, and run /memory to check P0#1, and fix P1#5 and P1#3 . also is the system loading hidtory from pr_pr
← _All migrations applied successfully:  - **`pr_prompts`** exists (renamed from `pr_interactions`) — 75 rows - **No embedding columns** — `prompt_embedding` and `response_embedding` are gone - **`pr_mem_

**[2026-03-28 09:45]** `claude_cli/claude`  
→ Before you continue - I would like to understand why in pr_interaction name is not change to pr_prompts at the db ? Also
← _Now I have the full picture. Let me give you clear answers to all four questions.  ---  ## 1. Why isn't `pr_interactions` renamed to `pr_prompts` in the DB yet?  The rename code IS in `database.py` as_

**[2026-03-28 02:38]** `claude_cli/claude`  
→ Can you update the table name from pr_interation to pr_prompts same to pr_interation_tags to pr_prompts_tags. also can g
← _Now I have a full picture. Here's a comprehensive design decision review with priority mapping:  ---  ## Design Decisions — Priority Map  ### P0 — Verify Core Functionality (must confirm before anythi_

**[2026-03-28 02:32]** `claude_cli/claude`  
→ Is it reccomended to merge pr_events and pr_interactions ?
← _The background research agent completed — its findings confirm the rewrite is accurate. The document is ready at `/Users/user/Documents/gdrive_cellqlick/2026/aicli/aicli_memory.md`._

**[2026-03-28 02:13]** `claude_cli/claude`  
→ Can you please rewrite aicli_memory.md. make sure all flows are exatly as they are. all prompts are writeen clear for ea
← _This is a significant research task — I need to read every prompt and understand every table before rewriting. Let me do that thoroughly first._

**[2026-03-28 02:02]** `claude_cli/claude`  
→ I would embedding to be connected to the tagging. for example auth - will be meta data of all authentication prompts.. m
← _Now update `aicli_memory.md` to document this properly and answer the user's questions:_

**[2026-03-28 01:48]** `claude_cli/claude`  
→ I would like to understand more about the embedigng and chunk methods. I do understand it is happend only when using /me
← _Now I have the full picture. Let me give you a complete and accurate answer.  ---  ## Embedding and Chunking — Full Explanation  ### 1. Is embedding only triggered by `/memory`?  **No** — there are 4 _
