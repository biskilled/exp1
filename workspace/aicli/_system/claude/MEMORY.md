# Project Memory — aicli
_Generated: 2026-03-10 01:23 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform built on Python/FastAPI backend with Electron+Vanilla JS frontend, enabling multi-agent workflows, semantic search via PostgreSQL+pgvector, and unified project memory across CLI, chat, and workflow sources. Currently stabilizing nested tag system (unlimited depth via parent_id FK), implementing zero-query frontend caching strategy, and consolidating Planner UI into tag-based management with status/due-date tracking.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (with parent_id for nesting); events table includes due_date column
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Anthropic), OpenAI, DeepSeek, Gemini, Grok — all independent adapters
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
- Per-project DB tables (commits_{p}, events_{p}, embeddings_{p}) via project_table() + ensure_project_schema()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing without login
- All LLM providers independent; server holds API keys; client sends NO keys
- Config-driven pricing via provider_costs.json as single source of truth
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- 5-layer memory: immediate → working (session JSON) → project (PROJECT.md) → historical (history.jsonl) → global (templates)
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Entity/event model: shared entity_categories/entity_values + per-project events/event_tags/event_links
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Frontend tag/category caching on project load: zero DB calls during chat/planner interaction; batch updates only on explicit save
- Picker flow creates root-level tags; nested sub-tags created via Planner tree UI with child button

## In Progress

- Nested tags implementation — added parent_id column to entity_values, implemented tree rendering in Planner with child-add buttons, validated idempotent migration
- Frontend caching strategy — load all project tags/categories once on project access via single batch query, cache in memory, update DB only on explicit save to eliminate repeated SQL calls
- Chat picker optimization — refactored tag picker to read from cached categories/values instead of DB queries, real-time filter with floating dropdown, zero database calls during selection
- Database query optimization — implemented batch updates and single-load patterns across chat.js and planner.js, eliminated per-action DB hits
- Backend connectivity and schema verification — resolved port 8000 bind conflict (stale uvicorn process), confirmed due_date column live in API, Electron frontend reloading correctly with npm run dev
- Planner tab consolidation — unified Feature/Bug/Tag/Tags tabs into single tag-based system with category hierarchy, status management, due_date, and custom properties

## Active Features / Bugs

- **[feature]** workflow-runner `(0 events)`
- **[feature]** test-picker-feature `(0 events)`
- **[feature]** mcp `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** tagging `(0 events)`
- **[feature]** UI `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** auth `(0 events)`
- **[feature]** shared-memory `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[phase]** development `(0 events)`
- **[phase]** prod `(0 events)`
- **[phase]** discovery `(0 events)`

**[2026-03-10 00:52]** `claude_cli` — Implemented frontend tag/category caching strategy on project load to eliminate repeated SQL queries; chat picker now reads from in-memory cache with zero DB calls during interaction and batch-updates only on explicit save. **[2026-03-10 01:11]** `claude_cli` — Designed and approved nested tags architecture via parent_id FK column addition to entity_values table, enabling unlimited depth (category → tag → subtag → ...); picker creates root-level tags, Planner tree UI handles nested sub-tag creation. **[2026-03-10 01:14]** `claude_cli` — Clarified nested tag creation flow: chat picker always creates new tags at root level; nested hierarchy is managed exclusively via Planner tree view with per-row child-add buttons. **[2026-03-10 01:19]** `claude_cli` — Completed nested tags implementation across backend (database.py migration + entities.py endpoints) and frontend (tagCache.js helpers, Planner tree rendering, child button UX); validated idempotent migration and zero-DB-call picker flow. **[2026-03-10 00:11]** `claude_cli` — Resolved port 8000 bind conflict caused by stale uvicorn process (PID 86671); confirmed backend healthy with due_date column live in API; Electron UI now loads correctly after fresh startup with npm run dev. **[2026-03-10 00:52]** `claude_cli` — Consolidated Planner UI from Feature/Bug/Tag/Tags tabs into unified tag-based system with category hierarchy, status management, due_date field, and custom properties per tag.