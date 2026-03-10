# Project Memory — aicli
_Generated: 2026-03-10 03:19 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI + FastAPI backend + Electron desktop UI to manage project history, semantic search, multi-agent workflows, and collaborative AI-assisted development. It uses flat-file storage (JSONL) as primary with PostgreSQL + pgvector for semantic indexing, nested tagging, and entity graphs. Current focus is on stabilizing UI/UX (session persistence, AI suggestion visibility, optimized DB queries) and fixing infrastructure issues (port binding, startup reliability).

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (with parent_id for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Anthropic), OpenAI, DeepSeek, Gemini, Grok — independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; always-on (DB best-effort)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server — 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (with parent_id for nesting, due_date tracking)

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search and entity graph
- Per-project DB tables (commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}) via project_table() + ensure_project_schema()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step; Vite dev server only
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing without login
- All LLM providers independent adapters; server holds API keys; client sends NO keys
- Config-driven pricing via provider_costs.json as single source of truth
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- 5-layer memory: immediate → working (session JSON) → project (PROJECT.md) → historical (history.jsonl) → global (templates)
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner; root-level creation only from chat picker
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit() in before-quit handler
- AI suggestions as dedicated amber banner between tag bar and messages; appears only when /memory returns suggestions with explicit approve/reject workflow

## In Progress

- AI suggestions workflow — amber banner with synthesized tags from /memory; fixed to always run (DB best-effort), appears between tag bar and messages with approve/reject UI
- Session tag persistence — GET /entities/session-tags endpoint queries event_tags_{p} joined to events/values/categories; tags now persist across session switches
- Planner UI action visibility — replaced small inline buttons with 3-dot dropdown menu (⋯) per tag row for edit/archive/restore/delete actions in discoverable format
- Database query optimization — frontend tag/category caching on project load eliminates per-action SQL calls during chat/planner; batch updates only on explicit save
- Port binding and startup stability — freePort() kills stale uvicorn via lsof, Electron before-quit cleanup via process.exit(), resolved 127.0.0.1:8000 bind conflicts
- Session phase labeling and tag bar overflow — renamed 'Session:' to 'Phase:' label for clarity; fixed tag bar overflow clipping to ensure all suggestion chips are visible

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

**[2026-03-10 02:40]** `claude_cli` — Redesigned AI suggestions as dedicated amber banner between tag bar and messages; renamed Session label to Phase for clarity; fixed tag bar overflow clipping so suggestion chips are always visible. **[2026-03-10 02:33]** `claude_cli` — Implemented GET /entities/session-tags endpoint to query event_tags_{p} joined to events/values/categories; tags now persist across session switches with proper load/refresh. **[2026-03-10 02:12]** `claude_cli` — Fixed session tag persistence: tags now save to event_tags_{p} and reload correctly when switching sessions; verified via API endpoint. **[2026-03-10 02:00]** `claude_cli` — Resolved port binding conflicts with freePort() helper that kills stale uvicorn via lsof + xargs; fixed Electron before-quit cleanup via process.exit() to prevent dangling processes. **[2026-03-10 01:42]** `claude_cli` — Replaced small inline planner action buttons with 3-dot dropdown menu (⋯) per tag row; menu displays edit/archive/restore/delete in discoverable format; added restore action for archived tags. **[2026-03-10 00:52]** `claude_cli` — Optimized database queries by implementing frontend tag/category caching on project load; eliminated per-action SQL calls during chat/planner interactions; batch updates trigger only on explicit save.