# Project Memory — aicli
_Generated: 2026-03-10 02:33 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron/Vanilla JS frontend to manage development workflows with semantic search, multi-agent workflows, and project-scoped entity/event tracking. It integrates PostgreSQL with pgvector for semantic memory, supports multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok), and features a Planner with nested tags, session tag persistence, and flat-file-first history (JSONL) backed by SQL. The system is currently optimizing database queries via frontend caching, stabilizing port binding on startup, and improving Planner UI visibility for tag management.

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

- Session tag persistence — fixed GET /entities/session-tags endpoint to query event_tags_{p} joined to events/values/categories; frontend caches and refreshes on save
- Planner UI discoverability — added 3-dot menu (⋯) per tag row with edit/archive/restore/delete actions; improved button visibility for action triggers
- Database query optimization — batch load all project tags/categories on project access, cache in tagCache.js, eliminate per-action SQL calls during chat/planner interactions
- Chat picker refactor — zero DB calls during selection, reads from cached categories/values, real-time filter with floating dropdown, root-level tag creation only
- Port binding and startup stability — implemented freePort() to kill stale uvicorn, fixed Electron before-quit cleanup via process.exit(), resolved 127.0.0.1:8000 bind conflicts
- Tag bar visibility and session persistence — fixed overflow:hidden clipping in chat tag bar, ensured tags persist across session switches via getEntitySessionTags() endpoint

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

**[2026-03-10 00:52]** `claude_cli` — Eliminated N+1 database calls in Planner by batch-loading all project tags/categories once on project access, caching in tagCache.js, and reading zero-DB chat picker with real-time filtering from cache; saves only on explicit user action. **[2026-03-10 01:11]** `claude_cli` — Designed unlimited nested tags via parent_id FK addition to entity_values, allowing category→tag→subtag hierarchy with Planner tree UI and root-level creation from chat picker only. **[2026-03-10 01:19]** `claude_cli` — Implemented parent_id column in database.py and entities.py (idempotent ALTER TABLE), updated ValueCreate/ValuePatch payloads, and added parent_id handling to SELECT/INSERT/PATCH endpoints. **[2026-03-10 01:42]** `claude_cli` — Improved Planner UI discoverability by adding 3-dot menu (⋯) per tag row with edit/archive/restore/delete actions, replacing hard-to-see inline buttons with accessible dropdown menu. **[2026-03-10 02:00]** `claude_cli` — Fixed port binding crashes by implementing freePort() utility to kill stale uvicorn processes (via lsof + kill -9) and Electron before-quit cleanup (process.exit()), eliminating 127.0.0.1:8000 bind conflicts on restart. **[2026-03-10 02:33]** `claude_cli` — Fixed session tag persistence by adding GET /entities/session-tags endpoint querying event_tags_{p} joined to events/values/categories, and fixed tag bar overflow clipping so tagged items display across session switches.