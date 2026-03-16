# Project Context: aicli

> Auto-generated 2026-03-15 23:41 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 102
- **Last active**: 2026-03-15T23:40:53Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude, OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)

## In Progress

- Phase persistence and UI display — phase now loads on app init from DB, saves via PATCH endpoint, backfills history.jsonl on change, shows red ⚠ badge for missing phase, maintains chronological order (2026-03-15)
- Commit-per-prompt display in Chat — inline commits at bottom of each prompt entry with accent left-border and hash ↗ link; shows only commits linked to that specific prompt via prompt_source_id (2026-03-15)
- Tag deduplication and cross-view synchronization — 149 tags total (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup (2026-03-15)
- AI suggestions auto-save to session — suggestions create tags in proper category via _acceptSuggestedTag; tags appear in Planner; phase filter fully functional (2026-03-15)
- Database schema alignment to project management — phase/feature/session_id as real indexed columns in events_{p}; MCP tools retrieve tagged data efficiently for feature/bug/task lifecycle (2026-03-15)

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server for local dev only
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Commit-to-prompt linking via source_id timestamp in commit_log.jsonl; bidirectional tagging via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- AI suggestions as dedicated amber banner between tag bar and messages; Claude Haiku synthesis; auto-save to session with category inheritance
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase; backfills history.jsonl; ordered by created_at (not updated_at)
- Real DB columns for phase, feature, session_id in events_{p} with indexes; tag cache loaded once per project tab (zero DB calls during chat)

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

**[2026-03-15 23:38]** `claude_cli/claude`  
→ Is there is any addiotnal improvement that I can implemet for having full memroy , and project management lifecycle ? 
← _Based on the audit, here are the gaps and a prioritized roadmap:  ---  ## What's Missing — Prioritized  ### Quick Wins (low effort, high value)  **1. MCP `create_entity` tool** Claude CLI / Cursor can_

**[2026-03-15 23:29]** `claude_cli/claude`  
→ is it align to the 5 steps memory? is there is any addiotnal requirement in order to be able to retreivae details inform
← _All three enhancements are implemented and working. Here's a summary of what was done:  ---  **Three changes implemented:**  **1. `GET /entities/summary` — new endpoint in `entities.py`** Returns all _

**[2026-03-15 23:13]** `claude_cli/claude`  
→ now that there is porper tagging - can you make sure all is linked, mapped propery in databse schema and used properly f
← _Everything is working. Here's a summary of all changes made:  ---  ## What was changed and why  ### Schema (`core/database.py`) - Added `phase`, `feature`, `session_id` as **real columns** (not just J_

**[2026-03-15 22:57]** `claude_cli/claude`  
→ It looks good and working as expected. the issue now is how it is linked to Histroy chat and commit. as this is saved by
← _Now the full flow works. Here's a summary of everything fixed:  **Root causes and fixes:**  1. **History chat filter shows nothing for a phase** — History.jsonl entries had no `phase` field if the ses_

**[2026-03-15 22:51]** `claude_cli/claude`  
→ That looks better. the problem now is that on any change of the phase the session order is changed as well . is it possi
← _Two changes:  1. **Backend** — `patch_session_tags` no longer updates `updated_at` when saving tags. The session's timestamp stays frozen at when it was last messaged.  2. **Frontend** — `_loadSession_

**[2026-03-15 22:40]** `claude_cli/claude`  
→ I still do not see that fixed. the session that mandtory fields are not updates suppose to be maked with red. currently 
← _The full flow works. Here's what was changed and why:  **Root causes fixed:**  1. **Red `⚠` only on UI sessions** — removed the `s.source === 'ui'` condition. Now ALL sessions (UI, CLI, WF) without a _

**[2026-03-15 22:22]** `claude_cli/claude`  
→ Lets try to fix the first bug in the Chat session as it is not fixed. when I upload a session - I do not see the correct
← _The endpoint is live (404 "Session not found" is the correct response for a non-existent test ID). The fix is complete.  **Summary of what changed:**  The phase change listener in `chat.js` no longer _

**[2026-03-15 21:45]** `claude_cli/claude`  
→ Issue is not fixed - In Chat - I cannot change/update phase. also most chat session do not have the right phase now. and
← _Here's a summary of all fixes:  **Chat — phase change** (restored): - `_sessionId = null` is back → each phase gets its own new session → sessions have correct phase in metadata - `api.putSessionTags(_

**[2026-03-15 21:15]** `claude_cli/claude`  
→ The error still exists - When I change the phase (on chats) - I am not able to save. also when I switch between diffrent
← _All changes look good. Here's a summary of everything fixed:  **Issue 1 — Phase can't save** (root cause: `_sessionId = null` on phase change): - Removed `_sessionId = null` from phase change — phase _

**[2026-03-15 20:56]** `claude_cli/claude`  
→ There is still UI issue with updateting/ showing the correct phase per session. when ever app is loaded - phase in on re
← _All changes look correct. Here's a summary of what was fixed:  **Root causes:** 1. **App load shows "required"**: No code ever loaded the last phase from DB on startup 2. **Session switch doesn't upda_

**[2026-03-15 20:44]** `claude_cli/claude`  
→ When I run memory through the aiCli - I did see some usefull suggestion that appered - the problem is that is not save p
← _All three changes are done:  **1. AI suggestions auto-save** (`chat.js:625`): - `_acceptSuggestedTag` is now `async` - After pushing to `_pendingEntities`, if `_sessionId` exists it immediately calls _

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
