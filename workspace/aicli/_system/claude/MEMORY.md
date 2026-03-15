# Project Memory — aicli
_Generated: 2026-03-15 23:35 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that unifies history, commits, and project state across multiple LLM tools (Claude CLI, Cursor, ChatGPT, etc.) using a flat-file + PostgreSQL + semantic search architecture. Currently at v2.2.0, it supports nested tagging, session phase tracking, commit-to-prompt linking, pagination, and MCP integration for external agents to manage features/bugs/tasks via a unified memory layer.

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
- Flat file storage primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables via project_table()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server only for local development
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner; tag cache loaded once per project tab (zero DB calls during chat)
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Commit-to-prompt linking via source_id timestamp in commit_log.jsonl; bidirectional tagging via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- AI suggestions as dedicated amber banner between tag bar and messages; Claude Haiku synthesis; auto-save to session with category inheritance
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- Session phase (required field) fixed on init from DB; PATCH /chat/sessions/{id}/tags saves phase; backfill to history.jsonl on phase change
- Session ordering by created_at (not updated_at) to prevent tag/phase updates from reordering the session list; real columns (phase, feature, session_id) in events_{p} with indexes

## In Progress

- Session phase persistence across Chat/History/Commits — phase now loads on app init from DB, saves via PATCH endpoint, backfills history.jsonl on change, shows red ⚠ badge for missing phase, maintains chronological order (2026-03-15)
- Commit-per-prompt display in Chat — inline commits at bottom of each prompt entry with accent left-border, hash ↗ link; shows only commits for that specific prompt via prompt_source_id (2026-03-15)
- Tag deduplication and cross-view synchronization — 149 tags total (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup (2026-03-15)
- AI suggestions auto-save to session — suggestions create tags in proper category via _acceptSuggestedTag; tags appear in Planner; phase filter fully functional (2026-03-15)
- Database schema alignment to 5-step memory — phase/feature/session_id as real indexed columns in events_{p}; MCP tools retrieve tagged data efficiently for project management (2026-03-15)

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

**[2026-03-15]** `claude_cli` — Session phase persistence completed: phase loads on app init, saves via PATCH endpoint, backfills history.jsonl on change, shows red ⚠ badge for missing phase, maintains chronological order by created_at. **[2026-03-15]** `claude_cli` — Commit-per-prompt linking: each prompt now displays its linked commits inline at bottom with accent border and hash ↗ link via prompt_source_id. **[2026-03-15]** `claude_cli` — Tag deduplication verified (149 tags, 0 duplicates); ✕ remove buttons propagate across Chat/History/Commits simultaneously. **[2026-03-15]** `claude_cli` — Pagination UI added to Chat/History/Commits showing offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives. **[2026-03-15]** `claude_cli` — AI suggestions auto-save to session: Claude Haiku suggestions appear in amber banner, user accepts via ✓, saves to proper category in Planner. **[2026-03-15]** `claude_cli` — Database schema aligned to 5-step memory: phase/feature/session_id added as real indexed columns to events_{p}; MCP tools retrieve tagged data efficiently for project feature/bug/task management.