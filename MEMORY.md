# Project Memory — aicli
_Generated: 2026-03-10 02:18 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI with FastAPI backend and Electron + Vanilla JS frontend to manage multi-agent workflows, per-project context, and semantic search over development history. Current focus is optimizing database query patterns (zero calls during UI interaction, batch saves only), implementing hierarchical tag management with archive/restore via 3-dot menus, and ensuring session tag state persists correctly across project switches.

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
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (with parent_id for nested tags), events (with due_date)

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

- Session tag persistence — fixed GET /entities/session-tags endpoint to query event_tags_{p} joined to events/values/categories; frontend caches and refreshes on save
- Planner UI discoverability — added 3-dot menu (⋯) per tag row with edit/archive/restore/delete actions; improved button visibility for action triggers
- Database query optimization — batch load all project tags/categories on project access, cache in tagCache.js, eliminate per-action SQL calls
- Chat picker refactor — zero DB calls during selection, reads from cached categories/values, real-time filter with floating dropdown, root-level tag creation only
- Port binding and startup stability — implemented freePort() to kill stale uvicorn, fixed Electron before-quit cleanup, resolved 127.0.0.1:8000 bind conflicts
- Archive/restore workflow — 3-dot menu toggles archive state in event_tags_{p}, UI hides archived items by default, restore option visible in menu to re-enable

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

**[2026-03-09 23:51]** `claude_cli` — Consolidated Planner from 4 tabs (Feature/Bug/Tag/Tags) into unified tag-based system with category hierarchy, status management, due_date tracking, and custom properties per tag.

**[2026-03-10 00:11]** `claude_cli` — Resolved port 8000 bind conflict by killing stale uvicorn process; confirmed backend health and due_date column live in API; fixed Electron frontend reload via npm run dev.

**[2026-03-10 00:52]** `claude_cli` — Implemented zero-DB-call chat picker by caching all categories and entity values on project load into tagCache; real-time filter with floating dropdown; root-level tag creation only.

**[2026-03-10 01:11]** `claude_cli` — Added parent_id column to entity_values for unlimited nested tag depth (category → tag → subtag); updated backend entities.py and frontend tagCache.js to support hierarchical tree rendering in Planner with child-add buttons.

**[2026-03-10 01:42]** `claude_cli` — Improved Planner UI discoverability by adding 3-dot menu (⋯) per tag row with edit/archive/restore/delete actions; archive state toggles visibility in UI; batch tag updates only on explicit save.

**[2026-03-10 02:12]** `claude_cli` — Fixed session tag persistence by creating GET /entities/session-tags endpoint that queries event_tags_{p} joined to events/values/categories; frontend now refreshes tag list after save and across session switches.