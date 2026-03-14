# Project Memory — aicli
_Generated: 2026-03-14 13:57 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a shared AI memory platform for developers that unifies history, prompts, and responses across multiple AI tools (Claude CLI, Cursor, ChatGPT) into a single project-scoped memory. Currently at v2.2.0, it features JWT authentication, PostgreSQL semantic search with pgvector, nested tagging (unlimited depth via parent_id), and an Electron-based UI with vanilla JS frontend. The system persists all data (JSONL for history, commits to PostgreSQL), uses Claude Haiku for memory synthesis, supports multi-agent workflows via async DAG, and integrates an MCP server for external tool access.

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
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Commit-to-prompt linking via source_id (timestamp from history.jsonl) stored in commit_log.jsonl; POST /entities/events/tag-by-source-id maps commits to events
- Session tags persist via GET /entities/session-tags endpoint querying event_tags_{p} joined to events/values/categories
- Phase labeling (renamed from 'Session:') visible in tag bar; 3-dot dropdown menu (⋯) per tag row for edit/archive/restore/delete actions
- AI suggestions as dedicated amber banner with /memory synthesis; always-on (DB best-effort), appears between tag bar and messages
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata; Claude Haiku for memory synthesis

## In Progress

- Tag cache persistence in history tab — all categories/values loaded once on tab open via Promise.all; color preservation on save prevents DB thrashing (2026-03-14)
- Commit-to-prompt linking mechanism — POST /entities/events/tag-by-source-id endpoint maps history.jsonl source_id to events; enables /memory to update summaries/embeddings via commit reference (2026-03-14)
- CLAUDE.md memory layer alignment — verified synthesis logic matches multi-layer design; all recent features (nested tags, commit linking, session persistence, tag cache) captured in memory output (2026-03-14)
- Port stability and startup flow — freePort() kills stale uvicorn via lsof before restart; Electron before-quit cleanup via process.exit() resolves bind address conflicts (2026-03-10)
- AI suggestions banner refinement — /memory runs always (DB best-effort), displays dedicated amber banner with approve/reject UI; works even without PostgreSQL (2026-03-10)
- Session phase labeling clarity — 'Phase:' label instead of 'Session:'; tag bar flex-wrap displays all suggestion chips; amber banner for AI suggestions between tag bar and messages (2026-03-10)

## Active Features / Bugs

- **[feature]** auth `(2 events)`
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

**[2026-03-14]** `claude_cli` — Implemented commit-to-prompt linking: POST /entities/events/tag-by-source-id maps history.jsonl source_id (timestamp) to events in event_tags_{p}, enabling /memory to synthesize and update embeddings by commit reference. **[2026-03-14]** `claude_cli` — Tag cache optimization: all categories/values now load once on history tab open via Promise.all, eliminating repeated DB calls; color preservation on save prevents thrashing. **[2026-03-14]** `claude_cli` — CLAUDE.md memory layer alignment verified: nested tags (parent_id FK for unlimited depth), commit linking, session persistence, and tag cache all integrated; v2.2.0 released. **[2026-03-10]** `claude_cli` — Port binding stability fix: freePort() kills stale uvicorn via lsof before restart; Electron process.exit() cleanup resolves 127.0.0.1:8000 bind conflicts on app restart. **[2026-03-10]** `claude_cli` — AI suggestions banner redesigned: dedicated amber banner between tag bar and messages, always-on (works without PostgreSQL via Haiku fallback), with approve (✓)/reject (×) UI. **[2026-03-10]** `claude_cli` — Phase labeling and UI clarity: 'Phase:' label replaces 'Session:' in tag bar; 3-dot menu (⋯) dropdown per tag row for edit/archive/restore/delete actions; tag bar flex-wrap handles overflow.