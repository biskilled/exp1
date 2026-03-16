# Project Memory — aicli
_Generated: 2026-03-16 00:15 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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

## In Progress

- Phase persistence and UI display — phase now loads on app init from DB, saves via PATCH endpoint, backfills history.jsonl on change, shows red ⚠ badge for missing phase, maintains chronological order (2026-03-15)
- Commit-per-prompt display in Chat — inline commits at bottom of each prompt entry with accent left-border and hash ↗ link; shows only commits linked to that specific prompt via prompt_source_id (2026-03-15)
- Tag deduplication and cross-view synchronization — 149 tags total (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup (2026-03-15)
- AI suggestions auto-save to session — suggestions create tags in proper category via _acceptSuggestedTag; tags appear in Planner; phase filter fully functional (2026-03-15)
- Database schema alignment to project management — phase/feature/session_id as real indexed columns in events_{p}; MCP tools retrieve tagged data efficiently for feature/bug/task lifecycle (2026-03-15)

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(94 events, 51 commits)`

### Doc_type

- **customer-meeting** — dsds `(54 events, 51 commits)`
- **retrospective** `(52 events, 51 commits)`
- **high-level-design** `(52 events, 51 commits)`
- **low-level-design**

### Feature

- **pagination** `(94 events, 51 commits)`
- **auth** `(57 events, 51 commits)`
- **workflow-runner** `(1 events)`
- **dropbox**
- **mcp**
- **shared-memory**
- **graph-workflow**
- **billing**
- **embeddings**
- **tagging**
- **test-picker-feature**
- **UI**

### Phase

- **discovery** `(1 events)`
- **development**
- **prod**

### Task

- **memory** `(94 events, 51 commits)`
- **implement-projects-tab** — Build the UI for managing features/tasks/bugs

## Recent Work (last 10 exchanges)

**[2026-03-15 23:49]** `claude_cli/claude`
Q: 1,2,3,4,5 and 8. I would like to add also anotehr mng table to check how many prompt there are and prompt the user (in using the aicli that /memory is running. also it will run on uploading the porjec

**[2026-03-15 23:38]** `claude_cli/claude`
Q: Is there is any addiotnal improvement that I can implemet for having full memroy , and project management lifecycle ?
A: Based on the audit, here are the gaps and a prioritized roadmap:  ---  ## What's Missing — Prioritized  ### Quick Wins (low effort, high value)  **1. MCP `create_entity` tool** Claude CLI / Cursor can read project entities but can't create features/bugs/tasks. Just one new MCP tool + backend endpoin

**[2026-03-15 23:29]** `claude_cli/claude`
Q: is it align to the 5 steps memory? is there is any addiotnal requirement in order to be able to retreivae details information about the project? I remind that the goal is the have ability to manage pr
A: All three enhancements are implemented and working. Here's a summary of what was done:  ---  **Three changes implemented:**  **1. `GET /entities/summary` — new endpoint in `entities.py`** Returns all non-archived entity values grouped by category, with `description`, `status`, `due_date`, `event_cou

**[2026-03-15 23:13]** `claude_cli/claude`
Q: now that there is porper tagging - can you make sure all is linked, mapped propery in databse schema and used properly for retirive data using mcp tool. tagging was done in order to manage memery effi
A: Everything is working. Here's a summary of all changes made:  ---  ## What was changed and why  ### Schema (`core/database.py`) - Added `phase`, `feature`, `session_id` as **real columns** (not just JSONB) to `events_{p}` table - Added indexes: `idx_{e}_session` and `idx_{e}_phase` — fast filtered q

**[2026-03-15 22:57]** `claude_cli/claude`
Q: It looks good and working as expected. the issue now is how it is linked to Histroy chat and commit. as this is saved by session - it suppose to be linked to all prompts in that session and all commit
A: Now the full flow works. Here's a summary of everything fixed:  **Root causes and fixes:**  1. **History chat filter shows nothing for a phase** — History.jsonl entries had no `phase` field if the session was tagged after-the-fact. Fix: `_backfill_session_phase()` now rewrites all matching `session_

**[2026-03-15 22:51]** `claude_cli/claude`
Q: That looks better. the problem now is that on any change of the phase the session order is changed as well . is it possible to remain the same order (by prompt or session date)
A: Two changes:  1. **Backend** — `patch_session_tags` no longer updates `updated_at` when saving tags. The session's timestamp stays frozen at when it was last messaged.  2. **Frontend** — `_loadSessions` now sorts by `created_at` instead of `updated_at`, so the session order is always by when the ses

**[2026-03-15 22:40]** `claude_cli/claude`
Q: I still do not see that fixed. the session that mandtory fields are not updates suppose to be maked with red. currently I do see some session marked in red (on the left of the sesscio name), but this 
A: The full flow works. Here's what was changed and why:  **Root causes fixed:**  1. **Red `⚠` only on UI sessions** — removed the `s.source === 'ui'` condition. Now ALL sessions (UI, CLI, WF) without a phase show the red `⚠` badge and red left border.  2. **Phase not saving for CLI sessions** — `PATCH

**[2026-03-15 22:22]** `claude_cli/claude`
Q: Lets try to fix the first bug in the Chat session as it is not fixed. when I upload a session - I do not see the correct phase, also when I change from one session to another - I dont see that changed
A: The endpoint is live (404 "Session not found" is the correct response for a non-existent test ID). The fix is complete.  **Summary of what changed:**  The phase change listener in `chat.js` no longer resets `_sessionId = null`. Now:  1. **Phase change on existing session** → calls `api.patchSessionT

**[2026-03-15 21:45]** `claude_cli/claude`
Q: Issue is not fixed - In Chat - I cannot change/update phase. also most chat session do not have the right phase now. and when I swtih from on chat to another - I do not see the phase update. In Histor
A: Here's a summary of all fixes:  **Chat — phase change** (restored): - `_sessionId = null` is back → each phase gets its own new session → sessions have correct phase in metadata - `api.putSessionTags(project, {phase})` persists globally → restored on next app load - On init: `api.getSessionTags(proj

**[2026-03-15 21:15]** `claude_cli/claude`
Q: The error still exists - When I change the phase (on chats) - I am not able to save. also when I switch between diffrent session at the Chat place - phses (in the UI) are not changing properly. also i
A: All changes look good. Here's a summary of everything fixed:  **Issue 1 — Phase can't save** (root cause: `_sessionId = null` on phase change): - Removed `_sessionId = null` from phase change — phase now updates the current session, doesn't force a new one - New `PATCH /chat/sessions/{id}/tags` endp
