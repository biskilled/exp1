# Project Context: aicli

> Auto-generated 2026-03-21 23:46 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 204
- **Last active**: 2026-03-21T23:46:08Z
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
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings, agent role providers; YAML config for pipeline definitions
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_usage/ (provider_costs.json, runtime data); data/api_keys.json (file-based); pricing, coupons, user_logs (migrating to SQL tables)

## In Progress

- Tool naming convention completion (2026-03-21) — Renamed agents/tools/ files to tool_ prefix; verified import paths functional post-relocation
- Backend module restructure validation (2026-03-21) — Confirmed agents/tools/ and agents/mcp/ import paths functional; cleaned up empty directories
- Database schema consolidation (2026-03-21) — Pricing.json and coupon data migrating from JSON files to SQL tables; api_keys.json remains as file (pre-DB connection requirement)
- Provider storage consolidation (2026-03-21) — Consolidated all provider runtime data to data/provider_usage/; confirmed empty JSON files are gitignored and local-only
- Project visibility bug investigation (ongoing) — AiCli project appearing in Recent but not main project list; backend startup race condition partially fixed with retry logic but root cause unresolved
- Data persistence issue triage (pending) — Tags saved in UI disappearing on session switch; requires investigation into UI rendering vs. database save failure

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
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT)
- Pipelines centralized under workflows/ with pipeline_ prefix; agent tools in agents/tools/ with tool_ prefix
- Backend module organization: routers/ for API endpoints, models/ for data structures, agents/tools/ for agent implementations
- Port binding safety via freePort() to kill stale uvicorn; Electron cleanup via process.exit()
- Graph runner commits via _apply_code_and_commit distinct from git_tool for existing working tree changes
- Database schema consolidation: api_keys.json stays as file; pricing, coupons, user logs migrate to SQL tables

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

**[2026-03-21 23:39]** `claude_cli/claude`  
→ yes please 
← _**Step 9 — Verify everything imports cleanly**_

**[2026-03-21 23:37]** `claude_cli/claude`  
→ Can you recheck what is database schema, I dont think it is required to add 5 new table, but possible to merge that mng_
← _Now I have the full picture. Here's my analysis:  **`api_keys.json`** — stays as a file, but moved **outside** `backend/` to `aicli/data/`. It's server secrets; can't go in DB (you need it to connect _

**[2026-03-21 23:25]** `claude_cli/claude`  
→ The backend is used for code only, it wont have any read permissions... any file data will be updated and used as data h
← _`backend/data/provider_usage/` is already gitignored — the empty files just exist locally and will never be committed. Nothing to change._

**[2026-03-21 23:09]** `claude_cli/claude`  
→ What is anthropic.jsonl , openai,jsonl and local_recalculate.jsonl, they are currently empty 
← _`backend/data/provider_usage/` is already gitignored — the empty files just exist locally and will never be committed. Nothing to change._

**[2026-03-21 23:06]** `claude_cli/claude`  
→ I do see provider files unde data , I do see also provider_usage folder under data (which might make sense) and do see s
← _Done. Final layout:  ``` data/ ├── api_keys.json          ← server secrets (config) ├── coupons.json           ← billing config ├── pricing.json           ← markup/tier config ├── database.py         _

**[2026-03-21 23:02]** `claude_cli/claude`  
→ Ok. we will fix that latter, files under tools can you rename to have prefix tool_ also under mcp - currently there is o
← _Summary of changes: - `tool_git.py`, `tool_file.py` (renamed from `git_tool.py`, `file_tool.py`) - `agents/mcp/tools/` deleted (was empty)_

**[2026-03-21 22:59]** `claude_cli/claude`  
→ Is there is a reason to have tools under mcp as well ?  
← _All imports clean. The backend restructure is complete and verified:  - `agents/tools/` (moved from `tools/agent_tools/`) - `agents/mcp/` (moved from `tools/mcp/`) - `tools/` folder deleted - `routers_

**[2026-03-21 22:48]** `claude_cli/claude`  
→ There is agents and tools and under tools there agent_tools - I think it will be cleaner to movee agent_tools under agen
← _All imports clean. The backend restructure is complete and verified:  - `agents/tools/` (moved from `tools/agent_tools/`) - `agents/mcp/` (moved from `tools/mcp/`) - `tools/` folder deleted - `routers_

**[2026-03-21 22:31]** `claude_cli/claude`  
→ If pipeline engine use that, it is not better to add that under workflows - also, can you rename that to pipelines for c
← _Verify zero stale imports and all modules load:_

**[2026-03-21 22:27]** `claude_cli/claude`  
→ I do see there is gitops and git_tool under agent_tools, is both needed ?
← _Actually `apply_code_and_commit` requires file changes to write — it returns empty if nothing to write. The handlers have genuinely different entry points (one writes files then commits, the other com_

**[2026-03-21 22:22]** `claude_cli/claude`  
→ can you rename all files under providers to start with pr_  also the one under memory - start with mem_ . I do have yaml
← _**Verify everything loads:**_

**[2026-03-21 22:18]** `claude_cli/claude`  
→ All 4 files - pricing and the one start with provider are realted to agents providers. can you add thos files over there
← _Now update `agents/providers/__init__.py` to also surface these:_

**[2026-03-21 21:46]** `claude_cli/claude`  
→ WHy there is model and routers folder, shoud thay all be under routers? also I do see some files like work_item_pipeline
← _All clean. Now verify no remaining references to the deleted modules:_

**[2026-03-21 21:35]** `claude_cli/claude`  
→ test prompt from manual run

**[2026-03-21 21:34]** `claude_cli/claude`  
→ I do not see hooks runing yet. 
← _Clean. Now commit and push:_
