# Project Memory — aicli
_Generated: 2026-03-14 19:16 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Anthropic), OpenAI, DeepSeek, Gemini, Grok — independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config + loop-back support
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; always-on (DB best-effort)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server — 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id for unlimited nesting, due_date tracking)

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search; per-project DB tables via project_table()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step; Vite dev server only
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing without login
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Commit-to-prompt linking via source_id (timestamp from history.jsonl) stored in commit_log.jsonl; bidirectional mapping via POST /entities/events/tag-by-source-id
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Session tags persist via GET /entities/session-tags endpoint; tag cache loaded once on history tab open
- AI suggestions as dedicated amber banner with /memory synthesis; always-on (DB best-effort), appears between tag bar and messages
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata; Claude Haiku for memory synthesis
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js for graph visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents (search_memory, get_project_state, commit_push, etc.)
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project with source_id timestamp linking

## In Progress

- Commit-to-prompt-to-session linking fully matured — source_id timestamp from history.jsonl maps bidirectionally; POST /entities/events/tag-by-source-id creates event-value links; multiple commits per session each tagged to originating prompt; verified working (2026-03-14)
- Tag cache persistence fully implemented — all categories/values loaded once on history tab open via Promise.all; color preservation on save prevents DB thrashing; zero DB calls during tag picker operations verified (2026-03-14)
- CLAUDE.md memory layer alignment complete — all recent features (nested tags, commit linking, session persistence, tag cache, graph workflows) captured in synthesis; PROJECT.md v2.2.0 aligned to current state (2026-03-14)
- Session phase labeling and AI suggestions banner stable — 'Phase:' label in tag bar; tag bar flex-wrap displays all suggestion chips; dedicated amber banner distinguishes AI suggestions from user-created tags (2026-03-10–2026-03-14)
- Port stability and Electron restart workflow resolved — freePort() kills stale uvicorn via lsof before restart; Electron before-quit cleanup via process.exit() eliminates bind address conflicts (2026-03-10)
- History tab commit-to-session display implemented — commit logs show source_id linking to originating prompts; /memory suggestions and tag loading optimized for zero thrashing (2026-03-14)

## Active Features / Bugs

- **[feature]** auth `(6 events)`
- **[feature]** tagging `(0 events)`
- **[feature]** dropbox `(0 events)`
- **[feature]** UI `(0 events)`
- **[feature]** workflow-runner `(0 events)`
- **[feature]** test-picker-feature `(0 events)`
- **[feature]** mcp `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[feature]** shared-memory `(0 events)`
- **[phase]** discovery `(1 events)`
- **[phase]** prod `(0 events)`
- **[phase]** development `(0 events)`

## Recent Work (last 10 exchanges)

**[2026-03-14 19:08]** `claude_cli/claude`
Q: I do see session_tags.json - is it used ? Also - history.jsonl start to be very large and I would like to start rotate that (when user is doing /memory) - the current one will remain history.jsonl wbu

**[2026-03-14 13:59]** `claude_cli/claude`
Q: I do see that there is a link between commit and session ID. is it possible to have link between commit/push and prompt ID ? commit are created after prompt (in session there might be several commits,
A: It worked. "Links created: 0" means they already existed from the previous run (conflict). The sample shows 5 real links:  - `d0f14c21` → prompt "It is lookls like hooks are not working now..." - `951768bc` → prompt "do I need the dev_runtime_state.json?..." - `0336f3e5` → prompt "I am thinking to a

**[2026-03-14 13:11]** `claude_cli/claude`
Q: can you run /memory, to make sure all updated. also can you check that system is aligned to CLAUDE.md (memroy layers) properly and add all new feutre that was created
A: `GET /graph/` returns `{"workflows":[]}` — the graph router is live and the tables are working. Everything is now aligned. Here's the full summary of what was done:  ---  ### Memory + Alignment Update — Complete  **`workspace/aicli/PROJECT.md`** — updated to v2.2.0 (2026-03-14): - Goal 9 changed fro

**[2026-03-14 13:04]** `claude_cli/claude`
Q: I do see the option to add tag in history - can you make sure all tags are loaded only once into mermory (to save db calls) as each time I am trying to ad tag, its looks like to loading all tags. also
A: Everything looks correct. Here's a summary of all changes made:  ---  ### Changes  **`ui/frontend/views/history.js`**  1. **Tag cache loaded once on tab open** — `_renderChat` now includes `listCategories` in its initial `Promise.all` (4 parallel requests: history, commits, categories, config). A ne

**[2026-03-14 11:10]** `claude_cli/claude`
Q: I do have some concern how commit/hash are linked to prompts/llm answers. also are tagging is currently works in my system. the goal is to be bale to use/memory in order to update all data (update sum
A: All changes are done. Here's a summary of what was implemented:  ### Changes  **`ui/backend/routers/entities.py`** — new endpoint `POST /entities/events/tag-by-source-id`: - Accepts `{ source_id, entity_value_id, project }` - Looks up event by `source_id` (the timestamp from history.jsonl) - If not 

**[2026-03-13 17:44]** `claude_cli/claude`
Q: I am siting with my freid and try to explain him wha is this system is about ? can you explain that shortly ?
A: **aicli** is a shared AI memory platform for developers.  The core problem it solves: when you use different AI tools (Claude CLI, Cursor, ChatGPT in the browser, etc.), each one starts from scratch — no memory of your project, your decisions, or your history.  **aicli gives all of them the same mem

**[2026-03-10 03:22]** `claude_cli/claude`
Q: I understand the issue. I am using your claude cli and hooks to store propts and llm response. hooks also managing the commit/push (as most communication is from calude CLI). I would like to have that
A: All clean. Here's the full picture:  ---  **No hook changes needed.** The `auto_commit_push.sh` hook already writes `session_id` to `commit_log.jsonl` on lines 181 and 294. The data connection exists. What was missing was the UI to display it.  **How it works now:**  ``` Claude Code CLI starts   └─ 

**[2026-03-10 03:16]** `ui/claude`
Q: hellow, how are you ?
A: Hello! I'm doing well, thanks for asking. Ready to help with the **aicli** project.  Looking at the context, it seems you've been making good progress — recent work includes AI suggestion banners, session tag persistence, planner UI improvements, and port binding fixes.  What would you like to work 

**[2026-03-10 03:14]** `claude_cli/claude`
Q: Are you using the mcp server in order to reciave all project information ? Also, I do not see any sujjestion in any session , api key is configured properly . also I dont see in chat view N commits in
A: ---  Now let me answer your three questions clearly:  ---  **1. Am I (Claude Code) using the aicli MCP server?**  No. I'm reading your files directly using the Read/Grep/Bash tools. The MCP server (`ui/mcp_server.py`) is a **separate integration** — it's designed so that when you run **Claude Code C

**[2026-03-10 02:57]** `claude_cli/claude`
Q: can you run /memory and run some tests? I do not see any sujjestion on all the existing session there are. also I do not see any commint logs at the history tab. also I would like to see for each sess
A: All clean (only the expected module resolution errors from Node's ES module checker, no syntax errors).  ---  Here's everything that was done:  ### 1. `/memory` suggestions — fixed to work without PostgreSQL Previously suggestions were gated behind `if db.is_available()`. Now they always run — DB is
