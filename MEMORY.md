# Project Memory — aicli
_Generated: 2026-03-14 11:20 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a shared AI memory platform that unifies prompts, responses, and project state across multiple AI tools (Claude CLI, Cursor, web ChatGPT, etc.) so each tool has access to the same context and history. The system uses JSONL flat files as primary storage, PostgreSQL + pgvector for semantic search, and a FastAPI backend with Electron desktop UI. Current focus is on commit-to-prompt linking, tag persistence and synthesis via /memory, and optimizing database queries to ensure snappy UI performance without redundant SQL calls.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id for nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Anthropic), OpenAI, DeepSeek, Gemini, Grok — independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; always-on (DB best-effort)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server — 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id for nesting)

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search; per-project DB tables via project_table()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step; Vite dev server only
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing without login
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- AI suggestions as dedicated amber banner with /memory synthesis; always-on (DB best-effort), appears between tag bar and messages
- Session tags persist via GET /entities/session-tags endpoint querying event_tags_{p} joined to events/values/categories
- Planner action visibility via 3-dot dropdown menu (⋯) per tag row for edit/archive/restore/delete
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- Commit-to-prompt linking via source_id (timestamp from history.jsonl) stored in commit_log.jsonl

## In Progress

- Commit/prompt linking mechanism — POST /entities/events/tag-by-source-id endpoint maps history.jsonl source_id to events for tagging; enables /memory to update summaries and embeddings via commit reference
- Tagging workflow validation — confirmed tag system works end-to-end: tags persist across sessions, /memory can query and synthesize tags for suggestions, frontend caching eliminates per-action SQL calls
- Session phase labeling and visibility — renamed 'Session:' to 'Phase:' in tag bar; fixed tag bar overflow with flex-wrap to ensure all suggestion chips visible
- AI suggestions banner display — /memory now always runs (DB best-effort), displays suggestions as amber banner between tag bar and messages with approve/reject UI
- Port stability and startup flow — freePort() kills stale uvicorn via lsof before restart; Electron before-quit cleanup via process.exit() resolves bind address conflicts
- Database query optimization — frontend caches all tags/categories on project load, batch saves on explicit save only, eliminated per-action SQL round-trips

## Active Features / Bugs

- **[feature]** workflow-runner `(0 events)`
- **[feature]** test-picker-feature `(0 events)`
- **[feature]** mcp `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** tagging `(0 events)`
- **[feature]** dropbox `(0 events)`
- **[feature]** UI `(0 events)`
- **[feature]** auth `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[feature]** shared-memory `(0 events)`
- **[phase]** discovery `(1 events)`
- **[phase]** development `(0 events)`
- **[phase]** prod `(0 events)`

**[2026-03-14]** `claude_cli` — Implemented commit/prompt linking via source_id (timestamp from history.jsonl) stored in commit_log.jsonl; new POST /entities/events/tag-by-source-id endpoint maps history events to tags, enabling /memory to update summaries and embeddings. Tagging mechanism validated end-to-end: tags persist across sessions, suggestions synthesize correctly, and frontend caching eliminates redundant SQL calls. **[2026-03-10]** `claude_cli` — Fixed /memory suggestions to work without PostgreSQL (DB best-effort fallback); created dedicated amber banner UI between tag bar and messages with approve/reject workflow. Renamed 'Session:' to 'Phase:' for clarity; fixed tag bar flex-wrap to prevent suggestion chip overflow. **[2026-03-10]** `claude_cli` — Implemented session tag persistence via GET /entities/session-tags endpoint querying event_tags_{p} joined to events/values/categories; tags now survive session switches with frontend reload. **[2026-03-10]** `claude_cli` — Improved Planner action visibility by replacing small inline buttons with 3-dot dropdown menu (⋯) per tag row for edit/archive/restore/delete actions. **[2026-03-10]** `claude_cli` — Resolved port binding conflicts by adding freePort() function that kills stale uvicorn via lsof before restart; Electron before-quit handler uses process.exit() to prevent lingering processes. **[2026-03-10]** `claude_cli` — Optimized database queries: frontend now caches all tags/categories on project load (zero DB calls during chat/planner), batch updates only on explicit save via dropzone/planner actions.