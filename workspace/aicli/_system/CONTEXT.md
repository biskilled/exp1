# Project Context: aicli

> Auto-generated 2026-03-15 20:40 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 91
- **Last active**: 2026-03-15T20:39:33Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for nested tags)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude, OpenAI, DeepSeek, Gemini, Grok — independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config + loop-back support
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; always-on (DB best-effort)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server — 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)

## In Progress

- Commit-per-prompt display in Chat tab — each prompt entry shows linked commits inline at bottom with accent left-border; replaced session-level commit strip (2026-03-15)
- Tag deduplication and cross-view synchronization — 149 tags total (0 duplicates); tag removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup (2026-03-15)
- Hook noise filtering fully deployed — filters <task-notification>, <tool-use-id>, <system-> entries; real prompts/LLM responses correctly logged to history.jsonl; pagination now accurate (2026-03-15)
- Tag cache optimization in History tab — all categories/values loaded once on tab open; zero DB calls during tag picker; color persistence on save prevents thrashing (2026-03-14)
- Commit-to-prompt linking verified end-to-end — source_id timestamp stored in commit_log.jsonl; tags per prompt auto-propagate to linked commits via tag-by-source-id endpoint (2026-03-14)

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage primary (JSONL/JSON with rotation); PostgreSQL + pgvector for semantic search; per-project DB tables via project_table()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server only for local development
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing; 3 roles: admin/paid/free
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Tag cache loaded once per project tab open: zero DB calls during chat/planner; batch updates only on explicit save
- History rotation on /memory call: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Commit-to-prompt linking via source_id timestamp in commit_log.jsonl; bidirectional tagging via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- AI suggestions as dedicated amber banner between tag bar and messages; always-on (DB best-effort), synthesized by Claude Haiku
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- Each prompt has multiple linked commits; each commit tagged inherits session phase + prompt-level tags via source_id linking

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


*...258 more lines in PROJECT.md*

---

## Recent Development History

**[2026-03-15 20:33]** `claude_cli/claude`  
→ The last commit was b255366 which suppose to be linked to the last prompt. it did worked before , but it seems that the 
← _All good. Here's what happened and what was fixed:  ---  ## Root Cause  **Phase 5 only ran on explicit `POST /entities/events/sync`.** The `auto_commit_push.sh` hook called `POST /git/{project}/commit_

**[2026-03-15 19:42]** `claude_cli/claude`  
→ I would like to set that up , and also add that to new prokect as autoamted set up. when creating a project there is a f
← _All changes are in place. Here's a summary of everything done:  ---  ## What Changed  ### Fixed now (current aicli project)  | File | Change | |---|---| | `.mcp.json` | Fixed path typo (`/user/ /gdriv_

**[2026-03-15 18:15]** `claude_cli/claude`  
→ let me summerise not. first run /memroy to update all sumeeries, db tagging and all new changes. and answer the followin
← _Memory updated successfully. Now for your questions:  ---  ## `/memory` — What Just Happened  All 5 files generated and synced: - `CLAUDE.md` → project root (auto-loaded by Claude Code on every sessio_

**[2026-03-15 18:11]** `claude_cli/claude`  
→ Currently the commit tags in Chat are all on a session phase. I would like to linled each commit into the prompt (same a
← _Good — the `/history/commits` endpoint already returns `prompt_source_id` in every commit row. The frontend `_commitData.commits` will have it.  Done. Here's what changed:  **Before:** All commits in _

**[2026-03-15 17:44]** `claude_cli/claude`  
→ Let me summersie and make sure all work properly - tags (per session) - can be added by Chat, tags (per prompts) can be 
← _All the previous session's fixes are confirmed in place:  - `history.py`: `_load_unified_history` reads current + all `history_*.jsonl` archives ✓ - `history.js`: `data-ts` attribute on entries, `_jum_

**[2026-03-15 17:28]** `claude_cli/claude`  
→ Taggin - there is a wau to add tags in History, commit and chat - which is good. can you make sure all is aligned to the
← _149 tags, 0 duplicates. Everything is clean. Here's a summary of all changes:  ---  **No duplicates** — confirmed: 149 event tags, 0 duplicates. The backend uses `ON CONFLICT DO NOTHING` on every tag _

**[2026-03-15 16:47]** `claude_cli/claude`  
→ Pagination - I do see now in the chat only 24 prompts (there are much more) can you add pagination < > 24/xxx on the top
← _All changes are working. Here's a summary:  **Backend — archive files included** - `_load_unified_history()` now reads `history.jsonl` + all `history_*.jsonl` archives - Result: **204 entries** (was 2_

**[2026-03-14 21:36]** `claude_cli/claude`  
→ Something wit hooks is not working now, as I do not see any new prompts / llm response adding into history.jsonl . also 
← _Everything is working. Here's a summary of all fixes:  ---  **1. Hook fixed — noise filtered at write time** - The deployed hook (`workspace/aicli/_system/hooks/log_user_prompt.sh`) was the old versio_

**[2026-03-14 19:08]** `claude_cli/claude`  
→  I do see session_tags.json - is it used ? Also - history.jsonl start to be very large and I would like to start rotate 
← _Everything works. Here's the summary of what was completed:  **History rotation — done:** - `_rotate_history()` was already in `projects.py`; added `log = logging.getLogger(__name__)` and wired up the_

**[2026-03-14 13:59]** `claude_cli/claude`  
→ I do see that there is a link between commit and session ID. is it possible to have link between commit/push and prompt 
← _It worked. "Links created: 0" means they already existed from the previous run (conflict). The sample shows 5 real links:  - `d0f14c21` → prompt "It is lookls like hooks are not working now..." - `951_

**[2026-03-14 13:11]** `claude_cli/claude`  
→ can you run /memory, to make sure all updated. also can you check that system is aligned to CLAUDE.md (memroy layers) pr
← _`GET /graph/` returns `{"workflows":[]}` — the graph router is live and the tables are working. Everything is now aligned. Here's the full summary of what was done:  ---  ### Memory + Alignment Update_

**[2026-03-14 13:04]** `claude_cli/claude`  
→ I do see the option to add tag in history - can you make sure all tags are loaded only once into mermory (to save db cal
← _Everything looks correct. Here's a summary of all changes made:  ---  ### Changes  **`ui/frontend/views/history.js`**  1. **Tag cache loaded once on tab open** — `_renderChat` now includes `listCatego_

**[2026-03-14 11:10]** `claude_cli/claude`  
→ I do have some concern how commit/hash are linked to prompts/llm answers. also are tagging is currently works in my syst
← _All changes are done. Here's a summary of what was implemented:  ### Changes  **`ui/backend/routers/entities.py`** — new endpoint `POST /entities/events/tag-by-source-id`: - Accepts `{ source_id, enti_

**[2026-03-13 17:44]** `claude_cli/claude`  
→ I am siting with my freid and try to explain him wha is this system is about ? can you explain that shortly ?
← _**aicli** is a shared AI memory platform for developers.  The core problem it solves: when you use different AI tools (Claude CLI, Cursor, ChatGPT in the browser, etc.), each one starts from scratch —_

**[2026-03-10 03:22]** `claude_cli/claude`  
→ I understand the issue. I am using your claude cli and hooks to store propts and llm response. hooks also managing the c
← _All clean. Here's the full picture:  ---  **No hook changes needed.** The `auto_commit_push.sh` hook already writes `session_id` to `commit_log.jsonl` on lines 181 and 294. The data connection exists._
