# Project Memory — aicli
_Generated: 2026-03-15 17:55 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a shared AI memory platform for developers that unifies history, commits, and AI interactions across multiple tools (Claude CLI, Cursor, ChatGPT, etc.) into a single queryable project workspace. Built with Python FastAPI backend, Electron UI with Vanilla JS, PostgreSQL + pgvector for semantic search, and flat-file JSONL storage with rotation; currently at v2.2.0 with stable features for nested tags, commit-to-prompt linking, history rotation, pagination, and tag synchronization across all views.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl with rotation, commit_log.jsonl), JSON, CSV — flat file first
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
- History rotation on /memory call: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS)
- Commit-to-prompt linking via source_id timestamp in commit_log.jsonl; bidirectional tagging via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- AI suggestions as dedicated amber banner between tag bar and messages; always-on (DB best-effort), synthesized by Claude Haiku
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- Session phase labeling via 'Phase:' tag bar selector; multiple commits per session each tagged to originating prompt via source_id

## In Progress

- Tag management unified across Chat/History/Commits — all tags deduplicated (149 total, 0 dupes), color preservation on save, removal via ✕ buttons propagates across all views (2026-03-15)
- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation on all three tabs (2026-03-15)
- Commit-to-prompt linking verified end-to-end — source_id timestamp stored in commit_log.jsonl; tags per prompt auto-propagate to linked commits via tag-by-source-id endpoint (2026-03-14)
- History rotation fully operational — /memory triggers rotation at configurable row threshold (default 500 rows); creates timestamped archives (history_YYMMDDHHSS); _load_unified_history() reads all archives on startup (2026-03-15)
- Tag cache optimization in History tab — all categories/values loaded once on tab open; zero DB calls during tag picker operations; color persistence prevents thrashing (2026-03-14)
- Hook noise filtering deployed — filters <task-notification>, <tool-use-id>, and <system-> entries; deployed hook matches template; real prompts/LLM responses now correctly logged to history.jsonl (2026-03-15)

## Active Features / Bugs

- **[feature]** auth `(40 events)`
- **[feature]** workflow-runner `(1 events)`
- **[feature]** billing `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[feature]** tagging `(0 events)`
- **[feature]** mcp `(0 events)`
- **[feature]** test-picker-feature `(0 events)`
- **[feature]** UI `(0 events)`
- **[feature]** dropbox `(0 events)`
- **[feature]** shared-memory `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[phase]** discovery `(1 events)`
- **[phase]** development `(0 events)`
- **[phase]** prod `(0 events)`

**[2026-03-15]** `history.js + entities.py` — Tag management unified across Chat/History/Commits views with deduplication (149 total, 0 duplicates) and color preservation on save. Removal via ✕ buttons propagates across all three tabs. **[2026-03-15]** `history.js` — Pagination added to Chat, History, and Commits tabs displaying offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation controls. **[2026-03-15]** `auto_commit_push.sh` — Hook noise filtering deployed to remove `<task-notification>`, `<tool-use-id>`, and `<system->` entries; real prompts and LLM responses now correctly logged to history.jsonl. **[2026-03-15]** `history.py` — History rotation fully operational: `/memory` triggers rotation at configurable max_rows (default 500); creates timestamped archives; `_load_unified_history()` reads all archives on startup yielding 204+ entries. **[2026-03-14]** `entities.py + history.js` — Commit-to-prompt linking verified end-to-end: source_id timestamp in commit_log.jsonl; tags per prompt auto-propagate to linked commits via POST /entities/events/tag-by-source-id. **[2026-03-14]** `history.js` — Tag cache optimization: all categories/values loaded once on tab open via `_buildTagCache()`; zero DB calls during tag picker operations; color preservation prevents thrashing.