# Project Context: aicli

> Auto-generated 2026-03-18 20:00 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 140
- **Last active**: 2026-03-18T18:22:51Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows) + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 12+ tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push, create_entity, update_entity, list_entities, get_feature_status)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, and MCP integration settings

## In Progress

- PROJECT.md load performance optimization (2026-03-17) — >1 minute load time on free Railway tier when opening aiCli project; investigating DB query latency vs file I/O bottleneck; considering pagination/lazy-loading
- Project visibility issue (2026-03-17) — aiCli project disappeared from recent projects list; requires verification of openProject() function and project listing query logic
- Multi-agent workflow system (2026-03-16) — Async DAG executor integration with Cytoscape.js visualization + YAML config for multi-agent prompt orchestration
- Config externalization and MCP readiness (2026-03-16) — Moved backend_url, haiku_model, db_pool_max to config.py; added /health check for MCP server initialization
- Dual-layer memory distillation (2026-03-16) — Raw JSONL → interaction_tags → 5 memory files pipeline; fixed session_bulk_tag() for consistency across both tables
- Session phase persistence and tag deduplication (2026-03-15) — Phase loads from DB on init, saves via PATCH; 149 tags with 0 duplicates; removal propagates across all views

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables with indexed columns (phase/feature/session_id)
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server for local dev
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free; login as first-level hierarchy
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth with tree UI in Planner; tags synced across Chat/History/Commits
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase; backfills history.jsonl ordered by created_at
- Real DB columns for phase/feature/session_id in events_{p} with indexes; tag cache loaded once per project tab (zero redundant DB calls during chat)
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization + YAML config
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Load-once-on-access pattern eliminates redundant SQL; tag cache synced across Chat/History/Commits views on save

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

**[2026-03-18 18:15]** `claude_cli/claude`  
→ There are some error - on the first load, it lookls like Backend is failing (after thay it succeed). I have tried to run
← _Memory endpoint works. Now let me check the "first load backend failing" and "aicli not shown as current project" issues:_

**[2026-03-18 17:44]** `claude_cli/claude`  
→ it looks like it is a bit broken, I have got an error - '_Database' object has no attribute 'ensure_project_schema'. Did
← _Everything is working. Here's the summary of all fixes applied:  ---  **3 issues fixed:**  **1. `main.py`** — removed the stale `db.ensure_project_schema(settings.active_project)` call  **2. `database_

**[2026-03-18 16:00]** `claude_cli/claude`  
→ That is correct. it is bed pattern to use clinet name. there is already mng_users table that can manage client as well (

**[2026-03-18 15:49]** `claude_cli/claude`  
→ I would like to know what do you think about the architecure ? Assuming there might be diffrent clients (for each clinet
← _## Architectural Review: 3-Layer Client/Project Tables  ### What's Good  The three-tier naming is clear and the seeding pattern (`mng_` → `cl_local_` on first run) is clean. For a single-tenant tool i_

**[2026-03-18 12:51]** `claude_cli/claude`  
→ I would like to make sure the client table are also aligned - for example mng_session_tags - is related to client (that 

**[2026-03-18 12:00]** `claude_cli/claude`  
→ clean that up . also I do remember there was graph support for memroy usage, but I dont see any record in. how graph tab
← _All endpoints working correctly. Here's a summary of everything done:  **All `mng_graph_*` references eliminated** across 4 files:  | File | Changes | |------|---------| | `routers/graph_workflows.py`_

**[2026-03-18 11:51]** `claude_cli/claude`  
→ I do see the table mng_session_tags, I also see session_tags.json file at the project workspace - is it in used , what i
← _Everything is working. Here's the final state:  **Database — 24 tables, clean split:**  | Prefix | Count | Tables | |--------|-------|--------| | `mng_` | 14 | Global config: users, billing, entity ta_

**[2026-03-18 10:46]** `claude_cli/claude`  
→ looks better. why memory_items and project_facts are under systeme managament tables? there are not part of project ?
← _All endpoints working. Let me update MEMORY.md to reflect the final table structure:_

**[2026-03-17 21:06]** `claude_cli/claude`  
→ Can you run the command as well, as I dont see any change in the database . also I think that there are old tables that 
← _Clean. Here's the complete summary:  **Before:** 29 tables (mixed naming, 5 stale bare tables)   **After:** 24 tables — perfectly organized  ### Dropped (stale legacy tables) `commits`, `embeddings`, _

**[2026-03-17 20:36]** `claude_cli/claude`  
→ before I continue - I do see quite lots of table used for this project. can you remove unused tables. also restrucure th
← _Clean. Let me also verify the `work_item_pipeline.py` core file is correct:_

**[2026-03-17 20:13]** `claude_cli/claude`  
→ Planner works partial - I do see the nested work on some category like doc_type but in bug or feature ui is diffrent and
← _Here's a summary of everything done and answers to your questions:  ---  ## What was fixed  **Planner consistency** — removed the split between `entity_values` (doc_type etc.) and `work_items` (featur_

**[2026-03-17 18:50]** `claude_cli/claude`  
→ I would like to go over on all the feutre and plan propery to Planer and Worklow as they are linked. I have created tagg
← _Here's a summary of all changes made:  ---  ## Changes Made  ### Tab renames (`main.js`) - `"Workflow"` → `"Pipelines"` (PROJECT_TABS + global sidebar nav) - `"Prompts"` → `"Roles"` (PROJECT_TABS)  ##_

**[2026-03-17 18:29]** `claude_cli/claude`  
→ I dont see nay changes from the last improvement - current planner do not supposrt nested (parent-child) tags as it used
← _`agent_run_id` is `INT` (not UUID), so `str(row["agent_run_id"])` is fine — it just converts the int to string. That's correct.  The three fixes applied to `work_items.py`:  1. **`WorkItemCreate` mode_

**[2026-03-17 18:28]** `claude_cli/claude`  
→ What is the claude agent sdk is uded for can it be used for my use cases for mutli agents (project manager (high design)
← _## Claude Agent SDK vs Your Current Multi-Agent System  ### What is the Claude Agent SDK?  The **Claude Agent SDK** is Anthropic's official Python/TypeScript framework for building AI agents that can:_

**[2026-03-17 18:18]** `claude_cli/claude`  
→ can you use the mcp tool and explain what the code is doing ?
← _Here's what **aicli** does:  ## aicli — Shared AI Memory Platform  **Core idea**: When you switch between different AI tools (Claude CLI, Cursor, ChatGPT, the aicli web UI), they all forget your proje_
