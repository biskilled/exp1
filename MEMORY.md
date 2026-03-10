# Project Memory — aicli
_Generated: 2026-03-10 01:12 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that integrates multiple LLM providers (Claude, OpenAI, DeepSeek, etc.) with a unified project workspace, semantic search via PostgreSQL+pgvector, and a workflow engine for multi-agent DAG execution. The system combines flat-file history (JSONL) with relational storage, features a Vanilla JS + Electron UI with terminal emulation and code editor, and uses JWT-based role authentication. Current focus is optimizing database queries through frontend caching, consolidating the planner into a unified tag-based system with nested hierarchy support, and ensuring session memory capture flows correctly into persistent history.

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
- /memory generates per-LLM files + copies to code_dir; Haiku incremental synthesis
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Entity/event model: shared entity_categories/entity_values + per-project events/event_tags/event_links
- Unified tag-based planner: single category→tags hierarchy with unlimited nesting via parent_id FK
- Frontend caching strategy: load all project tags/categories once on project access, update DB only on explicit save

## In Progress

- Nested tags architecture — added parent_id column to entity_values for unlimited tag depth (category → tag → subtag); validating database migration and planner UI tree rendering
- SQL query optimization — implemented frontend tag/category caching on project load to eliminate repeated DB calls; batch updates on save instead of per-action queries
- Planner UI consolidation — merged Feature/Bug/Tag/Tags tabs into unified tag-based system with category hierarchy, status management, due_date, and custom properties
- Session memory validation — ensuring user prompts and LLM responses logged to history.jsonl; verifying /memory incremental synthesis from last_memory_run timestamp
- Frontend reload and backend connectivity — resolved port 8000 bind conflict (stale uvicorn process); confirmed schema live with due_date column; Electron frontend now loads correctly with npm run dev
- Project dashboard enhancement — planning richer summary cards with event count, recent commits, active features, workflow runs, and activity timeline

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

**[2026-03-09 04:08]** `claude_cli` — /memory synthesis run with project summary and feature updates to code_dir. **[2026-03-09 17:56]** `claude_cli` — Identified gap: user prompts and LLM responses should appear in session context before full history.jsonl persistence. **[2026-03-09 23:51]** `claude_cli` — Planner redesign: consolidated Feature/Bug/Tag/Tags into unified tag system with category hierarchy, status, due_date, and custom properties. **[2026-03-10 00:11]** `claude_cli` — Resolved port 8000 bind conflict (stale uvicorn PID 86671); confirmed backend healthy with due_date column live in API. **[2026-03-10 00:52]** `claude_cli` — Optimized frontend: eliminated repeated SQL calls by caching all tags/categories in memory on project load; updates only on explicit save. **[2026-03-10 01:11]** `claude_cli` — Designed nested tags via parent_id FK in entity_values table, enabling unlimited tag hierarchy depth for richer organization.