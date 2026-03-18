# Project Memory — aicli
_Generated: 2026-03-18 20:12 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that integrates with Claude CLI and LLM platforms, combining flat-file JSONL history with PostgreSQL pgvector semantic search and a nested tagging system. It features an Electron desktop UI with xterm.js and Monaco, multi-agent workflow orchestration via async DAG execution, and a stdio MCP server for project state/memory queries. Current focus: resolving project visibility/listing bugs and load performance on Railway free tier while maintaining dual-layer memory synthesis and tag consistency across sessions.

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
- Flat file primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables with indexed columns (phase/feature/session_id)
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server for local dev
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free; login as first-level hierarchy
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth with tree UI in Planner; tags synced across Chat/History/Commits
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Load-once-on-access pattern eliminates redundant SQL; tag cache synced across Chat/History/Commits views on save
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization + YAML config
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase; backfills history.jsonl ordered by created_at
- Real DB columns for phase/feature/session_id in events_{p} with indexes; tag cache loaded once per project tab (zero redundant DB calls during chat)

## In Progress

- Project visibility and listing issues (2026-03-18) — Recent projects list shows 'aiCli' but doesn't display it as selectable project; investigating openProject() function and project query logic; backend startup delay on free tier acceptable
- PROJECT.md load performance optimization (2026-03-17) — >1 minute load time on free Railway tier; investigating DB query latency vs file I/O bottleneck; pagination/lazy-loading under consideration
- _continueToApp retry logic (2026-03-18) — Added race condition handling if projects load succeeds but returns empty; retry mechanism to ensure reliable app startup
- Multi-agent workflow system (2026-03-16) — Async DAG executor integration with Cytoscape.js visualization + YAML config for multi-agent prompt orchestration
- Dual-layer memory distillation (2026-03-16) — Raw JSONL → interaction_tags → 5 memory files pipeline; fixed session_bulk_tag() for consistency across both tables
- Session phase persistence and tag deduplication (2026-03-15) — Phase loads from DB on init, saves via PATCH; 149 tags with 0 duplicates; removal propagates across all views

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(7 events, 5 commits)`

### Doc_type

- **high-level-design** `(1 events)`
- **low-level-design** `(1 events)`
- **Test**
- **retrospective**
- **customer-meeting** — dsds

### Feature

- **shared-memory** `(3 events)`
- **test-picker-feature**
- **UI**
- **dropbox**
- **pagination**
- **tagging**
- **graph-workflow**
- **billing**
- **auth**
- **embeddings**
- **mcp**
- **workflow-runner**

### Phase

- **discovery**
- **development**
- **prod**

### Task

- **memory** `(1 events)`
- **implement-projects-tab** — Build the UI for managing features/tasks/bugs

**[2026-03-18]** `session_log` — Project visibility issue identified: aiCli appears in Recent but not as selectable project; requires openProject() and listing query debugging. Backend startup delay on free tier acceptable; _continueToApp retry logic implemented for race conditions.

**[2026-03-17]** `performance_audit` — PROJECT.md load time exceeds 1 minute on Railway free tier; investigating DB query latency vs file I/O; pagination/lazy-loading proposed.

**[2026-03-16]** `feature_integration` — Multi-agent workflow system with async DAG executor and Cytoscape.js visualization approved; dual-layer memory distillation (JSONL → interaction_tags → 5 output files) fixed for consistency.

**[2026-03-15]** `persistence_fix` — Session phase now persists via DB load on init and PATCH save; 149 tags deduplicated (0 duplicates); removal propagates across Chat/History/Commits views.

**[2026-03-10]** `architecture_review` — Nested tag hierarchy expanded beyond 2 levels via parent_id FK; load-once-on-access pattern eliminated redundant SQL calls; 3-dot menu pattern adopted for Planner UI; port binding conflicts resolved via freePort() cleanup.