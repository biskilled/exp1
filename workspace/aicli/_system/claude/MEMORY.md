# Project Memory — aicli
_Generated: 2026-03-10 01:53 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, PostgreSQL semantic storage, and Vanilla JS + Electron desktop UI. It manages per-project development history, event tracking, nested entity tags, and multi-agent LLM workflows with zero-bundler frontend architecture. Current focus is optimizing database query patterns (batch load on project access, cache in memory, batch save only) and improving Planner UI for nested tag management with better visibility for archive/restore actions.

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
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Picker flow creates root-level tags; nested sub-tags created via Planner tree UI with child button

## In Progress

- Nested tags UI — Planner tree rendering with parent_id hierarchy, child-add buttons per row, archive/restore toggles via 3-dot menu for improved discoverability
- Database query optimization — single batch load of all project tags/categories on project access, cache in tagCache.js, eliminate per-action SQL calls, batch updates only on explicit save
- Chat picker refactor — zero DB calls during selection, reads from cached categories/values, real-time filter with floating dropdown, root-level tag creation only
- Backend connectivity & schema — resolved port 8000 bind conflicts, verified due_date column live in API, confirmed Electron frontend reload working with npm run dev
- Planner tab consolidation — unified Feature/Bug/Tag/Tags into single tag-based system with category hierarchy, status management, due_date, custom properties, archive state
- Action visibility & archive recovery — implement 3-dot menu UI for edit/archive/restore on each tag row, toggle archive state to re-enable items, improve button discoverability

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

**[2026-03-09 04:08]** `claude_cli` — Ran `/memory` LLM synthesis and updated PROJECT.md with feature summaries and ongoing work. **[2026-03-09 23:51]** `claude_cli` — Consolidated Planner from 4 separate tabs (Feature/Bug/Tag/Tags) into unified tag-based system with category hierarchy, status tracking, due_date, and custom properties. **[2026-03-10 00:19]** `claude_cli` — Resolved port 8000 bind conflicts (stale uvicorn), verified due_date column live in API, confirmed Electron dev reload working correctly. **[2026-03-10 00:52]** `claude_cli` — Optimized database calls: implemented single batch load of all project tags/categories on project access, cached in tagCache.js memory, eliminated per-action SQL queries, batch updates only on save. **[2026-03-10 01:11]** `claude_cli` — Designed and feasibility-checked nested tags: added parent_id FK column to entity_values for unlimited depth (category → tag → subtag), root-level tag creation via chat picker, nested creation via Planner tree UI with child buttons. **[2026-03-10 01:42]** `claude_cli` — Implemented nested tags backend (parent_id column, idempotent migration) and frontend tree rendering; identified UI visibility issue with action buttons and archive state recovery — planning 3-dot menu for improved discoverability and toggle restore functionality.