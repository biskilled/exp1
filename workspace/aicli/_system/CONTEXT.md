# Project Context: aicli

> Auto-generated 2026-03-21 21:40 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 191
- **Last active**: 2026-03-21T21:39:43Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows) + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **memory_synthesis**: Claude Haiku for dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles

## In Progress

- Automated commit hooks configuration (2026-03-21) — User reported hooks not yet running; requires verification of hook execution logic and environment setup
- Backend code organization refactor — Consolidation of memory management classes under core module; clarification of model usage patterns required
- MCP server path and configuration alignment — Fixed env var references in aicli.yaml, .cursor/mcp.json, .claude/mcp.json; switched from hardcoded arguments
- Electron backend path resolution — Corrected BACKEND_DIR path from old/ui/backend to aicli/backend; verified project lookup endpoints functional
- Project visibility bug investigation — AiCli project appearing in Recent but not main project list; suspected race condition in Electron initialization
- SQL query optimization — Row-by-row INSERT in event migration and unbounded fetchall() in memory synthesis require batch refactor and pagination

## Key Decisions

- Engine/workspace separation: aicli/ contains backend logic only; workspace/ stores per-project content; _system/ holds project state
- Dual storage: JSONL (history.jsonl with rotation) for primary storage; PostgreSQL 15+ with pgvector (1536-dim embeddings) for semantic search and per-project indexed tables
- Electron UI with xterm.js + Monaco editor; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication via python-jose + bcrypt; DEV_MODE toggle; 3-tier roles (admin/paid/free); login as first-level hierarchy
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends no keys
- Nested tag hierarchy via parent_id FK with unlimited depth; tags synced across Chat/History/Commits on explicit save
- Load-once-on-access pattern: cache tags/workflows/runs in memory; update DB only on explicit save to eliminate redundant SQL
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js + cytoscape-dagre visualization
- Memory synthesis: Claude Haiku for dual-layer output (raw JSONL → interaction_tags → 5 files); smart chunking per language/section
- Port binding safety via freePort() to kill stale uvicorn; Electron cleanup via process.exit()
- Features linked to work_items with sequence numbering (10000+) for memory and workflow status tracking
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT) in .cursor/mcp.json and .claude/mcp.json
- Work item pipeline queries mng_agent_roles table; respects configured LLM provider and model per role instead of hardcoded Haiku
- Graph runner commits via `_apply_code_and_commit` with standardized message format for work item traceability
- Per-project DB tables indexed on phase/feature/session_id for fast contextual retrieval

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

**[2026-03-21 21:35]** `claude_cli/claude`  
→ test prompt from manual run

**[2026-03-21 21:34]** `claude_cli/claude`  
→ I do not see hooks runing yet. 
← _Clean. Now commit and push:_

**[2026-03-21 21:24]** `claude_cli/claude`  
→ I would like to make sure backend is witten properly - I do see storage folder who is only managing session, which I don
← _Verify the backend still imports cleanly:_

**[2026-03-21 21:11]** `claude_cli/claude`  
→ looks better. now I dont see any automated commits also mcp server is not configured well. I do see that aiCli.yaml is u
← _Here's a summary of what was fixed:  ---  **1. MCP Server — wrong path (all 3 configs updated)** - `aicli.yaml`: `ui/mcp_server.py` → `backend/tools/mcp/server.py` - `.cursor/mcp.json`: same path fix _

**[2026-03-21 21:03]** `claude_cli/claude`  
→ Now Ui is failing to load - Javascriot error at main process - child_process:483:16
← _Now verify the final path values are correct:_

**[2026-03-21 20:58]** `claude_cli/claude`  
→ I till see the rror - Project did not found aiCli. also I do not see any project loaded. the project aiCli is under the 
← _All three endpoints work correctly. The summary of what was happening and what to do:  ---  ## Root cause  The Electron app (`old/ui/electron/main.js`) was launching the backend with: ```js BACKEND_DI_

**[2026-03-21 20:47]** `claude_cli/claude`  
→ Let me check that all went well. when I try to open aiCli - it mention that it cannot find the project. also there is st
← _Project list returns correctly. Let me kill those test instances and confirm the Electron fix is the only change needed:_

**[2026-03-21 14:25]** `claude_cli/claude`  
→ What is the cli folder is used for ?
← _The `cli/` folder is the **new HTTP-only CLI client** — a terminal REPL that talks to the backend exclusively via HTTP, with no direct LLM provider code of its own.  **What it does:** - Runs a `prompt_

**[2026-03-21 10:46]** `claude_cli/claude`  
→ I think there is bit of confusation , and that is why roles are not defined well. I would like to restrucure the code fo

**[2026-03-20 22:22]** `claude_cli/claude`  
→ I am not sure what the developer did. dont see any output , and not sure there was any commit/push laos reviewer mention
← _Good. Let me also quickly verify that `_apply_code_and_commit` in `graph_runner.py` commits with the right message format for work items:_

**[2026-03-20 22:09]** `claude_cli/claude`  
→ Why work Item pipeline is not using the pre defined roles ? 
← _Up. Here's the complete answer to the question:  ---  ## Why the work item pipeline wasn't using predefined roles  **Root cause (before today's fixes):** The original `work_item_pipeline.py` had all p_

**[2026-03-20 21:55]** `claude_cli/claude`  
→ can you run /memory , also can you check why running workflow is so slow. each steps takes a while, and once step is app
← _Now let me save a note to memory about this fix:_

**[2026-03-20 21:48]** `claude_cli/claude`  
→ I would like to start optimising the project motly the following buiding block - sql queries, and running the workflow w
← _## Performance Analysis Results  I found significant issues in both areas. Here's the breakdown:  ---  ### SQL Query Issues (by priority)  | Priority | Issue | Location | Impact | |----------|-------|_

**[2026-03-20 21:32]** `claude_cli/claude`  
→ Work Item pieplien suppose to use the existing roles - PM - project manage, architect - Sr architect. can you optimize t
← _All 4 pipeline roles load correctly with their system role content appended. Let me update the tasks:_

**[2026-03-20 19:46]** `claude_cli/claude`  
→ I do see that last version is arhcitet, pm... and all the rest are not under old folder. Also - I would like to provide 
← _But `_loadTab` refetches if no cache. The real fix is that `_render()` reattaches to container and `_loadTab` uses the cached data. Let me check how the HistoryView handles this — when `_histData` is _
