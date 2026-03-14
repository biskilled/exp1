# Project Memory — aicli
_Generated: 2026-03-13 17:45 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a unified AI memory platform that syncs prompts, responses, and project state across multiple AI tools (Claude CLI, Cursor, ChatGPT, etc.), so every AI assistant has context. It uses a 5-layer memory stack (immediate → working → project → historical → global), PostgreSQL semantic search, nested tagging with Planner UI, and a FastAPI + Electron desktop app with native terminal and Monaco editor integration.

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
- AI suggestions as dedicated amber banner with synthesized tags from /memory; always-on (DB best-effort), appears between tag bar and messages with approve/reject workflow

## In Progress

- AI suggestions with /memory synthesis — amber banner now always runs (DB best-effort), displays between tag bar and messages with approve/reject UI; fixed to work without PostgreSQL
- Session tag persistence — GET /entities/session-tags endpoint queries event_tags_{p} joined to events/values/categories; tags now persist across session switches with frontend reload
- Planner UI action visibility — replaced small inline buttons with 3-dot dropdown menu (⋯) per tag row for edit/archive/restore/delete actions; improved discoverability
- Database query optimization — frontend tag/category caching on project load eliminates per-action SQL calls during chat/planner; batch updates only on explicit save
- Port binding and startup stability — freePort() kills stale uvicorn via lsof, Electron before-quit cleanup via process.exit(), resolved 127.0.0.1:8000 bind conflicts
- Session phase labeling and tag bar overflow — renamed 'Session:' to 'Phase:' label for clarity; fixed tag bar overflow clipping with flex-wrap to ensure all suggestion chips visible

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

**[2026-03-10 02:40]** `claude_cli` — Phase label renamed from 'Session:' to clarify UI semantics; AI suggestions moved to dedicated amber banner between tag bar and messages with approve/reject workflow for clarity.
**[2026-03-10 02:57]** `claude_cli` — /memory synthesis fixed to always run even without PostgreSQL (DB best-effort); suggestions now appear dynamically when /memory detects tag patterns from project history.
**[2026-03-10 02:12]** `claude_cli` — Session tag persistence implemented via GET /entities/session-tags endpoint; tags now survive session switches by querying event_tags_{p} joined to events, values, and categories.
**[2026-03-10 02:00]** `claude_cli` — Port binding stability resolved with freePort() helper killing stale uvicorn via lsof, plus Electron before-quit handler via process.exit() to prevent 127.0.0.1:8000 conflicts on restart.
**[2026-03-10 01:42]** `claude_cli` — Planner UI action visibility improved by replacing small inline buttons with 3-dot dropdown menu (⋯) per tag row; added restore option for archived tags.
**[2026-03-10 00:52]** `claude_cli` — Frontend tag/category caching implemented on project load, eliminating per-action SQL calls during chat/planner; batch updates only on explicit save.
**[2026-03-10 01:19]** `claude_cli` — Nested tag hierarchy enabled via parent_id FK in entity_values; unlimited depth (category → tag → subtag) with Planner tree UI; root-level creation only from chat picker.
**[2026-03-13 17:44]** `claude_cli` — Project summary articulated: aicli is a shared AI memory platform giving all AI tools (Claude CLI, Cursor, ChatGPT) unified project context via unified history.jsonl across all sources.
**[2026-03-10 03:22]** `claude_cli` — Commit/session connection clarified: auto_commit_push.sh hook already writes session_id to commit_log.jsonl; UI layer missing, not data layer.
**[2026-03-10 00:19]** `claude_cli` — Database schema verified live with due_date column; port 8000 bind conflicts resolved; Vite dev server initialization standardized.