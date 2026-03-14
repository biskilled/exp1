# Project Memory — aicli
_Generated: 2026-03-14 21:22 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a shared AI memory platform for developers that unifies history and decisions across multiple AI tools (Claude CLI, Cursor, ChatGPT, etc.). Current state (v2.2.0): all core features are stable — nested tag hierarchies with unlimited depth, commit-to-prompt linking via source_id, history rotation on /memory synthesis, tag caching to eliminate DB calls, session phase labeling, and AI suggestions banner. The system uses flat-file storage (JSONL) as primary with PostgreSQL+pgvector for semantic search, Electron desktop UI with Vanilla JS, FastAPI backend with JWT auth, and supports multi-agent workflows via async DAG executor with Cytoscape visualization.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl with rotation support, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Anthropic), OpenAI, DeepSeek, Gemini, Grok — independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config + loop-back support
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; always-on (DB best-effort)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server — 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search; per-project DB tables via project_table()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step; Vite dev server only
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing without login
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Tag cache loaded once on project tab open: zero DB calls during chat/planner; batch updates only on explicit save
- History rotation on /memory call: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS), original becomes history.jsonl
- Commit-to-prompt linking: source_id (history.jsonl timestamp) stored in commit_log.jsonl; bidirectional via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- AI suggestions as dedicated amber banner between tag bar and messages; always-on (DB best-effort), synthesized by Claude Haiku from /memory
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- Session phase labeling: 'Phase:' tag bar selector; multiple commits per session each tagged to originating prompt via source_id

## In Progress

- Commit-to-prompt linking fully operational — source_id timestamp stored in commit_log.jsonl; bidirectional tagging via POST /entities/events/tag-by-source-id; multiple commits per session linked to originating prompt (2026-03-14)
- History rotation fully implemented — /memory triggers rotation at configurable row threshold (default 500); creates timestamped archive (history_YYMMDDHHSS), rotates original to history.jsonl (2026-03-14)
- Tag cache persistence in history view — all categories/values loaded once on tab open; zero DB calls during tag picker; color preservation on save prevents thrashing (2026-03-14)
- Project memory layers (PROJECT.md + CLAUDE.md) fully aligned to v2.2.0 — all features documented: nested tags, commit linking, session persistence, tag cache, graph workflows, history rotation (2026-03-14)
- Session phase labeling and AI suggestions banner stable — 'Phase:' label in tag bar; amber banner with suggestions between tag bar and messages; works without PostgreSQL via best-effort DB (2026-03-10)
- Port stability and Electron restart resolved — freePort() kills stale uvicorn via lsof; before-quit cleanup via process.exit() eliminates bind address conflicts (2026-03-10)

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

**[2026-03-14]** `POST /entities/events/tag-by-source-id` — implemented bidirectional commit-to-prompt linking using source_id (history.jsonl timestamp) stored in commit_log.jsonl; multiple commits per session now tagged to originating prompt. **[2026-03-14]** `_rotate_history()` — history rotation wired into `/memory` call with configurable max_rows (default 500); creates timestamped archives (history_YYMMDDHHSS) and rotates original to history.jsonl. **[2026-03-14]** Tag cache optimization — all categories/values loaded once on tab open into memory; tag picker now zero DB calls during chat/planner; color preservation on save prevents thrashing. **[2026-03-14]** PROJECT.md + CLAUDE.md alignment — updated to v2.2.0 with all new features (nested tags, commit linking, session persistence, tag cache, graph workflows, history rotation). **[2026-03-10]** AI suggestions banner — dedicated amber banner between tag bar and messages; synthesized by Claude Haiku from /memory; works without PostgreSQL via best-effort DB integration. **[2026-03-10]** Port stability fixes — freePort() kills stale uvicorn via lsof; Electron cleanup via process.exit() eliminates bind address 127.0.0.1:8000 conflicts on restart.