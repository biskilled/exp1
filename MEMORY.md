# Project Memory — aicli
_Generated: 2026-03-15 22:51 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform for developers that unifies conversation history, embeddings, commits, and semantic tagging across multiple AI tools (Claude CLI, Cursor, ChatGPT, etc.). Currently at v2.2.0, the system features session-phase tracking, commit-to-prompt linking, nested tagging with zero-DB-call caching, and LLM-synthesized memory rotation. The most recent work (2026-03-15) focused on stabilizing phase persistence, fixing session ordering, implementing per-prompt commit display, and ensuring tag deduplication across all UI views.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
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
- Flat file storage primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables via project_table()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server only for local development
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Tag cache loaded once per project tab open: zero DB calls during chat/planner; batch updates only on explicit save
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Commit-to-prompt linking via source_id timestamp in commit_log.jsonl; bidirectional tagging via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- AI suggestions as dedicated amber banner between tag bar and messages; Claude Haiku synthesis; auto-save to session
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- Each prompt has multiple linked commits; each commit inherits session phase + prompt-level tags via source_id linking

## In Progress

- Phase persistence per session — fixed on init to load from DB; PATCH /chat/sessions/{id}/tags saves phase; UI/CLI/WF all supported with red ⚠ badge for missing phase (2026-03-15)
- Session ordering by created_at instead of updated_at — prevents phase/tag updates from reordering session list; sessions stay in chronological order (2026-03-15)
- Commit-per-prompt display in Chat — inline commits at bottom of each prompt entry with accent left-border, hash ↗ link; shows only commits for that specific prompt (2026-03-15)
- Tag deduplication and cross-view synchronization — 149 tags total (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup (2026-03-15)
- AI suggestions auto-save to session — suggestions create tags in proper category via _acceptSuggestedTag; tags appear in Planner; phase filter fully functional (2026-03-15)

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

**[2026-03-15]** `claude_cli` — Phase persistence fixed: sessions now load correct phase from DB on init, PATCH /chat/sessions/{id}/tags saves phase to session JSON, red ⚠ badge shows on UI/CLI/WF sessions without phase. **[2026-03-15]** `claude_cli` — Session ordering stabilized: changed sort from updated_at to created_at to prevent phase/tag updates from reordering the session list; sessions now stay chronologically ordered. **[2026-03-15]** `claude_cli` — Commit-per-prompt linking completed: each prompt now shows only its linked commits inline at bottom with accent left-border and hash ↗ link, replacing session-level commit strip. **[2026-03-15]** `claude_cli` — Tag deduplication verified: 149 total event tags with 0 duplicates confirmed; tag removal via ✕ buttons now propagates instantly across Chat/History/Commits views. **[2026-03-15]** `claude_cli` — Pagination unified: Chat/History/Commits all show offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; backend now loads history.jsonl + all archived history_*.jsonl files on startup (204 total entries). **[2026-03-15]** `claude_cli` — AI suggestions auto-persist: `/memory` suggestions now create tags in proper category via _acceptSuggestedTag async call, appear in Planner immediately, phase filter fully functional across all views.