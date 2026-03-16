# Project Memory — aicli
_Generated: 2026-03-16 00:29 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a shared AI memory platform that unifies prompt/response history, commits, and project metadata across multiple AI tools (Claude CLI, Cursor, ChatGPT, etc.). It uses JSONL for primary storage + PostgreSQL for semantic search, with per-project tagging (nested via parent_id), phase-based session management, and an MCP server for external agent integration. Currently v2.2.0 (2026-03-16): all core features (history rotation, commit linking, tag deduplication, pagination, phase persistence) are implemented and operational.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude, OpenAI, DeepSeek, Gemini, Grok (independent adapters; configurable haiku_model in config.py)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 8+ tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push, create_entity)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, and MCP integration settings

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
- MCP server (stdio): 8+ tools for integration with Claude CLI and external agents
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase; backfills history.jsonl; ordered by created_at (not updated_at)
- Real DB columns for phase, feature, session_id in events_{p} with indexes; tag cache loaded once per project tab (zero DB calls during chat)

## In Progress

- Phase persistence and per-session display — phase loads on app init from session JSON, persists via PATCH endpoint, backfills history.jsonl on change, shows red ⚠ badge for missing phase, maintains chronological order by created_at (2026-03-15)
- Commit-per-prompt linking and display in Chat — inline commits at bottom of each prompt entry with accent left-border and hash ↗ link; shows only commits linked to that specific prompt via prompt_source_id (2026-03-15)
- Tag deduplication and cross-view synchronization — 149 tags, 0 duplicates; removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup; default filter = all phases (2026-03-15)
- Database schema alignment for project lifecycle management — phase/feature/session_id as real indexed columns in events_{p}; MCP tools (get_commits, get_session_tags) retrieve tagged data efficiently for feature/bug/task management (2026-03-15)
- Code optimization and config externalization — backend_url, haiku_model, db_pool_max moved to config.py; removed unused methods; hardcoded strings replaced; added /health check for MCP readiness (2026-03-16)

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

**[2026-03-10]** `claude_cli` — Tag cache optimization: loaded once on project tab open, zero DB calls during chat; nested tags via parent_id FK in entity_values (unlimited depth). **[2026-03-14]** `claude_cli` — Commit-to-prompt linking via source_id timestamps; tag deduplication confirmed (149 tags, 0 duplicates); history rotation on /memory with configurable max_rows (default 500). **[2026-03-15 morning]** `claude_cli` — Phase persistence: loads from session JSON on app init, persists via PATCH endpoint, backfills history.jsonl on change, maintains chronological order by created_at. **[2026-03-15 afternoon]** `claude_cli` — Commit-per-prompt display in Chat with inline commits at bottom of each prompt entry; pagination UI for Chat/History/Commits showing offset ranges (1–204 unified history). **[2026-03-15 evening]** `claude_cli` — Database schema alignment: phase/feature/session_id as real indexed columns in events_{p}; MCP tools enhanced for project lifecycle management (get_commits, get_session_tags, create_entity). **[2026-03-16]** `claude_cli` — Code optimization: backend_url, haiku_model, db_pool_max externalized to config.py; removed unused methods; eliminated hardcoded strings; added /health endpoint for MCP readiness checks.