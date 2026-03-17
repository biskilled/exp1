# Project Memory — aicli
_Generated: 2026-03-17 14:40 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that provides Claude, OpenAI, and other LLMs with persistent access to development project state via an MCP server. It combines a Python CLI backend (FastAPI + PostgreSQL + pgvector for semantic search) with an Electron UI (Vanilla JS + xterm.js + Monaco editor) to enable cross-session memory synthesis, multi-agent workflows, and real-time project tracking. Current focus is optimizing PROJECT.md load performance on Railway free tier and investigating project visibility regressions.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows) + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 12+ tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push, create_entity, update_entity, list_entities, get_feature_status)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, and MCP integration settings

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables with real indexed columns (phase/feature/session_id)
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server for local dev
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth with tree UI in Planner; tags synced across Chat/History/Commits
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase; backfills history.jsonl ordered by created_at
- Real DB columns for phase/feature/session_id in events_{p} with indexes; tag cache loaded once per project tab (zero redundant DB calls during chat)
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization + YAML config
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Performance: load-once-on-access pattern eliminates redundant SQL; tag cache synced across Chat/History/Commits views on save

## In Progress

- PROJECT.md load performance optimization (2026-03-17) — User reported >1 minute load time on free Railway tier when opening aiCli project; investigating if root cause is DB query latency or file I/O bottleneck; considering pagination/lazy-loading for project initialization
- Project visibility issue (2026-03-17) — aiCli project disappeared from recent projects list; unclear if UI state bug or DB query regression; requires verification of openProject() function and project listing logic
- Multi-agent workflow system (2026-03-16) — Analyzed specrails pattern (Claude Code agent with 12 prompt roles) and evaluated async DAG executor integration with Cytoscape.js visualization + YAML config
- Config externalization and MCP readiness (2026-03-16) — Moved backend_url, haiku_model, db_pool_max to config.py; added /health check for MCP server initialization verification
- Dual-layer memory distillation (2026-03-16) — Implemented raw JSONL → interaction_tags → 5 memory files pipeline; fixed session_bulk_tag() to write to both event_tags and interaction_tags for consistency
- Session phase persistence and tag deduplication (2026-03-15) — Phase now loads from DB on init and saves via PATCH; 149 tags with 0 duplicates; removal via UI buttons propagates across Chat/History/Commits views

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(94 events, 51 commits)`

### Doc_type

- **customer-meeting** — dsds `(54 events, 51 commits)`
- **retrospective** `(52 events, 51 commits)`
- **high-level-design** `(52 events, 51 commits)`
- **low-level-design**

### Feature

- **pagination** `(94 events, 51 commits)`
- **auth** `(58 events, 51 commits)`
- **shared-memory** `(4 events)`
- **mcp** `(2 events)`
- **UI** `(1 events)`
- **workflow-runner** `(1 events)`
- **graph-workflow** `(1 events)`
- **test-picker-feature**
- **dropbox**
- **embeddings**
- **tagging**
- **billing**

### Phase

- **discovery** `(2 events)`
- **development** `(1 events)`
- **prod**

### Task

- **memory** `(97 events, 51 commits)`
- **implement-projects-tab** — Build the UI for managing features/tasks/bugs

**[2026-03-17]** `user_report` — aiCli project disappeared from recent projects list and PROJECT.md takes >1 minute to load on free Railway tier; suspected DB query latency or file I/O bottleneck affecting project initialization flow. **[2026-03-16]** `architecture` — Multi-agent workflow system designed with async DAG executor, asyncio.gather for parallel node execution, Cytoscape.js visualization, and YAML configuration; specrails pattern evaluated for Claude Code agent with 12 prompt roles. **[2026-03-16]** `config` — Backend configuration externalized (backend_url, haiku_model, db_pool_max to config.py); /health check endpoint added for MCP server readiness verification. **[2026-03-16]** `memory` — Dual-layer memory synthesis pipeline completed: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot rules, aicli rules); session_bulk_tag() fixed to persist to both event_tags and interaction_tags tables. **[2026-03-15]** `persistence` — Session phase field now loads from DB on init and saves via PATCH /chat/sessions/{id}/tags; backfill logic preserves history.jsonl order by created_at. **[2026-03-15]** `tagging` — Tag deduplication completed (149 tags, 0 duplicates); removal propagates across Chat/History/Commits views via UI buttons; load-once-on-access pattern eliminates redundant SQL calls.