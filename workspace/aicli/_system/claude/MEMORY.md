# Project Memory — aicli
_Generated: 2026-03-15 21:20 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a shared AI memory platform for developers that unifies prompt history, semantic search, tagging, and workflow orchestration across multiple AI tools (Claude CLI, Cursor, ChatGPT, etc.). It uses flat-file JSONL storage (rotated on /memory) + PostgreSQL pgvector for semantic indexing, with an Electron UI providing Chat, History, Commits, and Planner tabs. Current focus is on session/prompt/commit linking, phase-based filtering, and real-time tag synchronization across all views.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for nested tags)
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
- Flat file storage primary (JSONL/JSON with rotation); PostgreSQL + pgvector for semantic search; per-project DB tables via project_table()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server only for local development
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing; 3 roles: admin/paid/free
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Tag cache loaded once per project tab open: zero DB calls during chat/planner; batch updates only on explicit save
- History rotation on /memory call: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Commit-to-prompt linking via source_id timestamp in commit_log.jsonl; bidirectional tagging via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- AI suggestions as dedicated amber banner between tag bar and messages; Claude Haiku synthesis; always-on (DB best-effort)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- Each prompt has multiple linked commits; each commit inherits session phase + prompt-level tags via source_id linking

## In Progress

- Phase synchronization across Chat tabs — fixed: phase now updates current session (not forcing new one); PATCH /chat/sessions/{id}/tags endpoint writes phase to session JSON; phase persists on session switch (2026-03-15)
- Commit-per-prompt display in Chat tab — replaced session-level commit strip with inline commits at bottom of each prompt entry (accent left-border, hash ↗ link); shows linked commits only for that prompt (2026-03-15)
- Tag deduplication and cross-view synchronization — 149 tags total (0 duplicates); tag removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup; 204 total entries including Feb 23 archive (2026-03-15)
- AI suggestions auto-save to session — fixed: suggestions now immediately create tags in proper category via _acceptSuggestedTag async call; tags appear in Planner; phase filter fully functional (2026-03-15)
- Commit phase filtering — added phase column to Commits table in Chat view; filter by phase same as Chat tab; phase persists per commit in database (2026-03-15)

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

**[2026-03-15]** `chat.js + api.js` — Phase synchronization fixed: phase now persists on session switch via PATCH /chat/sessions/{id}/tags; removed stale _sessionId = null on phase change.

**[2026-03-15]** `chat.js` — Commit-per-prompt display: replaced session-level commit strip with inline commits at bottom of each prompt (accent border, hash ↗ link); each prompt shows only its linked commits.

**[2026-03-15]** `entities.py + chat.js + history.js` — Tag deduplication verified: 149 tags, 0 duplicates; ✕ button removal propagates across Chat/History/Commits simultaneously via DELETE /entities/events/tag-by-source-id.

**[2026-03-15]** `history.js + projects.py` — Pagination: Chat/History/Commits now show offset ranges (e.g., '1–100 / 204'); unified history loads all archives on startup (current + history_*.jsonl); 204 total entries.

**[2026-03-15]** `chat.js` — AI suggestions auto-save: _acceptSuggestedTag now async; immediately creates tag in proper category and adds to Planner; phase filter fully functional.

**[2026-03-15]** `chat.js + entities.py` — Commit phase filtering: Commits table now displays phase column; filter by phase same as Chat tab; phase persists per commit in database.

**[2026-03-14]** `entities.py + chat.js` — Session-to-prompt linking verified: source_id timestamp stored in commit_log.jsonl; tags per prompt auto-propagate to linked commits via tag-by-source-id endpoint.

**[2026-03-14]** `history.js` — Tag cache optimization: all categories/values loaded once on tab open; zero DB calls during tag picker; color persistence on save prevents thrashing.

**[2026-03-14]** `auto_commit_push.sh + projects.py` — History rotation: triggered on /memory call; reads history_max_rows from project.yaml (default 500); creates timestamped archive history_YYMMDDHHSS.jsonl.

**[2026-03-10]** `database.py + entities.py + planner.js` — Nested tags implemented: parent_id FK added to entity_values; unlimited depth (category → tag → subtag); Planner tree UI with + child buttons per row.