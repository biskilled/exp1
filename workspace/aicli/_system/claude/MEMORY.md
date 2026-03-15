# Project Memory — aicli
_Generated: 2026-03-15 21:00 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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

## In Progress

- Commit-per-prompt display in Chat tab — each prompt entry shows linked commits inline at bottom with accent left-border; replaced session-level commit strip (2026-03-15)
- Tag deduplication and cross-view synchronization — 149 tags total (0 duplicates); tag removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup (2026-03-15)
- Hook noise filtering fully deployed — filters <task-notification>, <tool-use-id>, <system-> entries; real prompts/LLM responses correctly logged to history.jsonl; pagination now accurate (2026-03-15)
- Tag cache optimization in History tab — all categories/values loaded once on tab open; zero DB calls during tag picker; color persistence on save prevents thrashing (2026-03-14)
- Commit-to-prompt linking verified end-to-end — source_id timestamp stored in commit_log.jsonl; tags per prompt auto-propagate to linked commits via tag-by-source-id endpoint (2026-03-14)

## Active Features / Bugs

- **[bug]** hooks `(86 events)`
- **[feature]** pagination `(86 events)`
- **[feature]** auth `(49 events)`
- **[feature]** workflow-runner `(1 events)`
- **[feature]** test-picker-feature `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** shared-memory `(0 events)`
- **[feature]** tagging `(0 events)`
- **[feature]** dropbox `(0 events)`
- **[feature]** UI `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[feature]** mcp `(0 events)`
- **[phase]** discovery `(1 events)`
- **[phase]** development `(0 events)`
- **[phase]** prod `(0 events)`

## Recent Work (last 10 exchanges)

**[2026-03-15 20:56]** `claude_cli/claude`
Q: There is still UI issue with updateting/ showing the correct phase per session. when ever app is loaded - phase in on required (default option) . also when I go to another chat session - it is not upd
A: All changes look correct. Here's a summary of what was fixed:  **Root causes:** 1. **App load shows "required"**: No code ever loaded the last phase from DB on startup 2. **Session switch doesn't update phase**: `session.metadata.tags` could be missing for old sessions; also the `PUT /history/sessio

**[2026-03-15 20:44]** `claude_cli/claude`
Q: When I run memory through the aiCli - I did see some usefull suggestion that appered - the problem is that is not save properly for the session. it also must be saved in the prper category and added t
A: All three changes are done:  **1. AI suggestions auto-save** (`chat.js:625`): - `_acceptSuggestedTag` is now `async` - After pushing to `_pendingEntities`, if `_sessionId` exists it immediately calls `_saveEntitiesToSession()` (which creates the tag in the right category via `api.entities.sessionTag

**[2026-03-15 20:33]** `claude_cli/claude`
Q: The last commit was b255366 which suppose to be linked to the last prompt. it did worked before , but it seems that the last 9 commits are not linked to any prompts
A: All good. Here's what happened and what was fixed:  ---  ## Root Cause  **Phase 5 only ran on explicit `POST /entities/events/sync`.** The `auto_commit_push.sh` hook called `POST /git/{project}/commit-push`, which committed and wrote to `commit_log.jsonl` — but never triggered the DB sync or Phase 5

**[2026-03-15 19:42]** `claude_cli/claude`
Q: I would like to set that up , and also add that to new prokect as autoamted set up. when creating a project there is a flow that ask for IDE support - and MCP config must be supported. currently it is
A: All changes are in place. Here's a summary of everything done:  ---  ## What Changed  ### Fixed now (current aicli project)  | File | Change | |---|---| | `.mcp.json` | Fixed path typo (`/user/ /gdrive` → `/user/Documents/gdrive`) | | `.cursor/mcp.json` | Unified to same format as `.mcp.json` (args-

**[2026-03-15 18:15]** `claude_cli/claude`
Q: let me summerise not. first run /memroy to update all sumeeries, db tagging and all new changes. and answer the following : if will open new session using claude cli or and other llm - how they will b
A: Memory updated successfully. Now for your questions:  ---  ## `/memory` — What Just Happened  All 5 files generated and synced: - `CLAUDE.md` → project root (auto-loaded by Claude Code on every session start) - `MEMORY.md` → project root (LLM-synthesized digest of all recent changes) - `.cursor/rule

**[2026-03-15 18:11]** `claude_cli/claude`
Q: Currently the commit tags in Chat are all on a session phase. I would like to linled each commit into the prompt (same as there is in promot - linkd to commit) can you update that History Chat will sh
A: Good — the `/history/commits` endpoint already returns `prompt_source_id` in every commit row. The frontend `_commitData.commits` will have it.  Done. Here's what changed:  **Before:** All commits in a session appeared in a single strip at the top of the session group.  **After:** - Each prompt entr

**[2026-03-15 17:44]** `claude_cli/claude`
Q: Let me summersie and make sure all work properly - tags (per session) - can be added by Chat, tags (per prompts) can be menaged by Hitroy / prompts. commit - prompts tags are linked properly (so any t
A: All the previous session's fixes are confirmed in place:  - `history.py`: `_load_unified_history` reads current + all `history_*.jsonl` archives ✓ - `history.js`: `data-ts` attribute on entries, `_jumpToPrompt` using `CSS.escape`, `_removeTag` with ✕ buttons ✓ - `entities.py`: `_propagate_tags_phase

**[2026-03-15 17:28]** `claude_cli/claude`
Q: Taggin - there is a wau to add tags in History, commit and chat - which is good. can you make sure all is aligned to the sabe data (there are no duplicate? ) . I would like also to add option to remov
A: 149 tags, 0 duplicates. Everything is clean. Here's a summary of all changes:  ---  **No duplicates** — confirmed: 149 event tags, 0 duplicates. The backend uses `ON CONFLICT DO NOTHING` on every tag insert, and the frontend deduplicates in-memory before calling the API.  **New backend endpoints:** 

**[2026-03-15 16:47]** `claude_cli/claude`
Q: Pagination - I do see now in the chat only 24 prompts (there are much more) can you add pagination < > 24/xxx on the top right where filter tab exists. can you do the same for chats and commits ?
A: All changes are working. Here's a summary:  **Backend — archive files included** - `_load_unified_history()` now reads `history.jsonl` + all `history_*.jsonl` archives - Result: **204 entries** (was 26) — includes the 380-entry archive from Feb 23 (deduped + noise filtered) - Data range: 2026-02-23 

**[2026-03-14 21:36]** `claude_cli/claude`
Q: Something wit hooks is not working now, as I do not see any new prompts / llm response adding into history.jsonl . also can you explain why they are session starting with <task-notification>\n<task-id
A: Everything is working. Here's a summary of all fixes:  ---  **1. Hook fixed — noise filtered at write time** - The deployed hook (`workspace/aicli/_system/hooks/log_user_prompt.sh`) was the old version without noise filtering — real prompts were being written correctly but so were `<task-notificatio
