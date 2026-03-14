# Project Memory — aicli
_Generated: 2026-03-14 20:15 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a unified AI memory platform for developers that captures prompts, LLM responses, commits, and structured tags across multiple AI tools (Claude CLI, Cursor, ChatGPT, etc.), enabling consistent context across sessions. It combines flat-file history (JSONL) with PostgreSQL+pgvector for semantic search, offers nested tag hierarchies, commit-to-prompt linking, and workflow automation via DAG executors. Currently at v2.2.0 with mature features including history rotation, session persistence, tag caching, and AI-synthesized suggestions via Claude Haiku.

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
- Commit-to-prompt linking: source_id (history.jsonl timestamp) stored in commit_log.jsonl; bidirectional via POST /entities/events/tag-by-source-id
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- History rotation on /memory call: configurable max_rows (default 500), creates history_YYMMDDHHSS archive, original becomes history.jsonl
- AI suggestions as dedicated amber banner with /memory synthesis; always-on (DB best-effort), appears between tag bar and messages
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata; Claude Haiku for memory synthesis
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- Session tags persist via GET /entities/session-tags endpoint; tag cache loaded once on history tab open

## In Progress

- Commit-to-prompt linking matured — source_id timestamp from history.jsonl maps to commits via POST /entities/events/tag-by-source-id; multiple commits per session each tagged to originating prompt (2026-03-14)
- Tag cache persistence in history view — all categories/values loaded once on history tab open via Promise.all; color preservation on save prevents DB thrashing; zero DB calls during tag picker (2026-03-14)
- History rotation fully operational — /memory triggers rotation at configurable row threshold (default 500); creates timestamped archive (history_YYMMDDHHSS), original becomes history.jsonl (2026-03-14)
- Project memory layers (PROJECT.md + CLAUDE.md) fully aligned to v2.2.0 — all recent features (nested tags, commit linking, session persistence, tag cache, graph workflows, history rotation) documented (2026-03-14)
- Session phase labeling and AI suggestions banner stable — 'Phase:' label in tag bar; amber banner with AI suggestions appears between tag bar and messages; suggestions from /memory synthesis work without PostgreSQL (2026-03-10–2026-03-14)
- Port stability and Electron restart workflow resolved — freePort() kills stale uvicorn via lsof; Electron before-quit cleanup via process.exit() eliminates bind address conflicts (2026-03-10)

## Active Features / Bugs

- **[feature]** auth `(9 events)`
- **[feature]** workflow-runner `(1 events)`
- **[feature]** dropbox `(0 events)`
- **[feature]** UI `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** tagging `(0 events)`
- **[feature]** test-picker-feature `(0 events)`
- **[feature]** mcp `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[feature]** shared-memory `(0 events)`
- **[phase]** discovery `(1 events)`
- **[phase]** prod `(0 events)`
- **[phase]** development `(0 events)`

**[2026-03-14]** `claude_cli` — History rotation now fully operational; `/memory` triggers rotation at configurable threshold (default 500 rows), creating timestamped archives (history_YYMMDDHHSS) while original becomes history.jsonl. **[2026-03-14]** `claude_cli` — Commit-to-prompt bidirectional linking matured via POST /entities/events/tag-by-source-id; source_id timestamps from history.jsonl map to commits, allowing multiple commits per session each tagged to originating prompt. **[2026-03-14]** `claude_cli` — Tag cache persistence in history view implemented; all categories/values loaded once on tab open via Promise.all (zero DB calls during picker); color preservation on save prevents DB thrashing. **[2026-03-14]** `claude_cli` — Project memory layers (PROJECT.md + CLAUDE.md) aligned to v2.2.0; all features (nested tags, commit linking, session persistence, tag cache, graph workflows, history rotation) now fully documented. **[2026-03-10–2026-03-14]** `claude_cli` — AI suggestions banner stabilized as dedicated amber UI element appearing between tag bar and messages; suggestions always-on via /memory synthesis (DB best-effort, works without PostgreSQL). **[2026-03-10]** `claude_cli` — Port stability resolved; freePort() kills stale uvicorn via lsof; Electron before-quit cleanup via process.exit() eliminates bind address conflicts.