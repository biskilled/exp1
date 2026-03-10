# Project Context: aicli

> Auto-generated 2026-03-10 02:28 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 56
- **Last active**: 2026-03-10T02:18:43Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (with parent_id for nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Anthropic), OpenAI, DeepSeek, Gemini, Grok — independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server — 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (with parent_id for nested tags), events (with due_date)

## In Progress

- Session tag persistence — fixed GET /entities/session-tags endpoint to query event_tags_{p} joined to events/values/categories; frontend caches and refreshes on save
- Planner UI discoverability — added 3-dot menu (⋯) per tag row with edit/archive/restore/delete actions; improved button visibility for action triggers
- Database query optimization — batch load all project tags/categories on project access, cache in tagCache.js, eliminate per-action SQL calls
- Chat picker refactor — zero DB calls during selection, reads from cached categories/values, real-time filter with floating dropdown, root-level tag creation only
- Port binding and startup stability — implemented freePort() to kill stale uvicorn, fixed Electron before-quit cleanup, resolved 127.0.0.1:8000 bind conflicts
- Archive/restore workflow — 3-dot menu toggles archive state in event_tags_{p}, UI hides archived items by default, restore option visible in menu to re-enable

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search and entity graph
- Per-project DB tables (commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}) via project_table() + ensure_project_schema()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step; Vite dev server only
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing without login
- All LLM providers independent adapters; server holds API keys; client sends NO keys
- Config-driven pricing via provider_costs.json as single source of truth
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- 5-layer memory: immediate → working (session JSON) → project (PROJECT.md) → historical (history.jsonl) → global (templates)
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Entity/event model: shared entity_categories/entity_values + per-project events/event_tags/event_links with parent_id for nested tags
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner; root-level creation only from chat picker
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit() in before-quit handler

---

## Project Documentation (PROJECT.md)

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-09 | Version 2.1.0_

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
| 9 | **Project management UI** — Feature/Task/Bug tracking tied to AI workflows | ◷ In Progress |

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


*...230 more lines in PROJECT.md*

---

## Recent Development History

**[2026-03-10 02:12]** `claude_cli/claude`  
→ I do see the save button - and when I save I do see the tag, when I am checking another session and come back (at the ui
← _Only module resolution error (expected) — no syntax errors. The fix is complete.  Here's what was implemented:  **Backend** (`entities.py`): New `GET /entities/session-tags?session_id=X&project=Y` end_

**[2026-03-10 02:00]** `claude_cli/claude`  
→ why there is sometime problem to restart the app (I do see that beckend is exited (1) as there is attemp to bind address
← _Good. Here's what was fixed and why:  ---  ### Root causes & fixes  | Problem | Fix | |---|---| | **Port still busy at startup** — previous uvicorn didn't release port before new spawn | `freePort()` _

**[2026-03-10 01:42]** `claude_cli/claude`  
→ planner UI - it is almost imposible to see the action option as they are small, is there is a way to improve the visibil
← _Only import resolution errors — no syntax errors. Let me do a final check that there are no stale references:_

**[2026-03-10 01:19]** `claude_cli/claude`  
→ yes
← _All done. Here's a summary of what was implemented:  ---  ### What changed  **Backend** - `database.py`: Added `parent_id INTEGER REFERENCES entity_values(id) ON DELETE SET NULL` + index (idempotent `_

**[2026-03-10 01:14]** `claude_cli/claude`  
→ yes. just to clarify when I add login - it will be first level only ? 
← _Yes — from the chat picker, **adding a new tag always creates it at the root level** (first level under the selected category). To create a nested sub-tag, you use the Planner where you have the full _

**[2026-03-10 01:11]** `claude_cli/claude`  
→ Can you make sure that sql queries are optimized (loading one time when project is loading, save in any update). also ca
← _## Feasibility Answer  **Yes, nested tags are absolutely feasible.** Here's the design before I write any code:  ---  ### Database change One column addition to `entity_values`: ```sql ALTER TABLE ent_

**[2026-03-10 00:52]** `claude_cli/claude`  
→ It looks like there are multiple database calls that make the system realy slow. try to avoid many sql calls and upload 
← _All done. Here's what was completed in `chat.js`:  **New picker flow:** 1. Click `+ Tag` → `_pickerPopulateCats()` reads from cache (zero DB calls) → populates category `<select>` with counts like `⬡ _

**[2026-03-10 00:19]** `claude_cli/claude`  
→ I am shutting down elecrotn and run fresh - but cannot see anythin. also when when I click on project name - i do not se
← _Port 8000 is now free. The stale backend is gone.  Now do a clean restart from the `ui/` directory using the **dev script** (which sets `NODE_ENV=development` and starts Vite):  ```bash cd /Users/user_

**[2026-03-10 00:11]** `claude_cli/claude`  
→ I think there is an issue with ui as it is not loading properly (and I do see error whie bind address 127.0.0.1, 8000) 
← _Everything is working on the backend side. To summarise:  - **Bind error**: Caused by trying to start a second uvicorn instance — the old one (PID 86671) was already running and is still running fine _

**[2026-03-09 23:51]** `claude_cli/claude`  
→ I dont think your update works. lets start from Planer - there is not need to have 4 tabs - Feture, tag, Bugs and Tags. 

**[2026-03-09 17:56]** `claude_cli/claude`  
→ The last prompts was asking for a new feature (clinet install/ support multiple projects) - it was made by this console.

**[2026-03-09 04:08]** `claude_cli/claude`  
→ Assuming I will improve the project management page, workflow processes. can you update /memory - so it can be used for 
← _`/memory` ran with LLM synthesis and all files copied to `code_dir`. Let me verify the MEMORY.md output:_
