# Project Memory — aicli
_Generated: 2026-03-10 02:43 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that integrates development workflow, semantic search, and multi-agent collaboration through a unified CLI, FastAPI backend, and Electron desktop UI. Currently at v2.1.0, the project focuses on scalable flat-file + PostgreSQL storage, nested entity tagging with unlimited hierarchy depth, zero-DB-call frontend caching, and robust port binding for reliable local development startup.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (with parent_id for nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Anthropic), OpenAI, DeepSeek, Gemini, Grok — independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run
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
- Entity/event model: shared entity_categories/entity_values + per-project events/event_tags/event_links with parent_id for nested tags
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner; root-level creation only from chat picker
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit() in before-quit handler

## In Progress

- Tag persistence across sessions — fixed GET /entities/session-tags endpoint to query event_tags_{p} joined to events/values/categories; frontend now correctly retrieves and displays tags when switching sessions
- Planner UI action visibility — added 3-dot menu (⋯) per tag row with edit/archive/restore/delete actions; replaced small inline buttons with discoverable dropdown menu
- Database query optimization — batch load all project tags/categories on project access, cache in tagCache.js, eliminated per-action SQL calls during chat/planner interactions
- Port binding and startup stability — implemented freePort() to kill stale uvicorn, fixed Electron before-quit cleanup via process.exit(), resolved 127.0.0.1:8000 bind conflicts on app restart
- AI suggestions UX — added dedicated amber banner between tag bar and messages showing LLM-synthesized tags; banner only appears when /memory returns suggestions with clear approval workflow
- Session tag bar improvements — fixed overflow:hidden clipping in chat tag bar, renamed 'Session:' label to 'Phase:' for clarity, ensured tags persist and display correctly when switching between sessions

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
- **[phase]** development `(0 events)`
- **[phase]** discovery `(0 events)`
- **[phase]** prod `(0 events)`

**[2026-03-10 00:52]** `claude_cli` — Database query optimization: eliminated multiple SQL calls per action by batch-loading all project tags/categories on project load and caching them in tagCache.js; chat picker now reads from cache with zero DB calls during selection. **[2026-03-10 01:11]** `claude_cli` — Nested tags architecture approved: added parent_id FK column to entity_values for unlimited depth (category → tag → subtag); root-level tag creation only via chat picker, nested creation via Planner tree UI. **[2026-03-10 01:19]** `claude_cli` — Nested tags implementation complete: backend supports parent_id in ValueCreate/ValuePatch endpoints; tagCache.js helpers generate tree structure client-side; Planner renders hierarchical tags with expand/collapse and '+ child' buttons. **[2026-03-10 01:42]** `claude_cli` — Planner UI discoverability improved: replaced small inline action buttons with 3-dot dropdown menu (⋯) per tag row; fixed archive/restore logic so archived items can be restored via menu. **[2026-03-10 02:00]** `claude_cli` — Port binding stability: implemented freePort() to kill stale uvicorn before restart via lsof + kill -9; Electron cleanup fixed with process.exit() in before-quit handler to prevent hang on force-quit. **[2026-03-10 02:40]** `claude_cli` — Session tag persistence and UX clarity: added GET /entities/session-tags endpoint to retrieve tags per session; fixed tag bar overflow clipping; renamed 'Session:' to 'Phase:'; AI suggestions now appear in dedicated amber banner only when /memory returns suggestions.