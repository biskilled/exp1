# Project Memory — aicli
_Generated: 2026-03-18 18:24 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI, FastAPI backend, and Electron desktop UI to provide persistent semantic memory, project tracking, and multi-agent workflow orchestration across LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok). Currently at version 2.2.0, it uses PostgreSQL+pgvector for semantic search, JSONL for history with rotation, and an MCP server for tool integration; active focus is resolving PROJECT.md load performance issues and a project visibility regression on the free Railway tier.

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
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase; backfills history.jsonl ordered by created_at
- Real DB columns for phase/feature/session_id in events_{p} with indexes; tag cache loaded once per project tab (zero redundant DB calls during chat)
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization + YAML config
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Load-once-on-access pattern eliminates redundant SQL; tag cache synced across Chat/History/Commits views on save

## In Progress

- PROJECT.md load performance optimization (2026-03-17) — >1 minute load time on free Railway tier when opening aiCli project; investigating DB query latency vs file I/O bottleneck; considering pagination/lazy-loading
- Project visibility issue (2026-03-17) — aiCli project disappeared from recent projects list; requires verification of openProject() function and project listing query logic
- Multi-agent workflow system (2026-03-16) — Async DAG executor integration with Cytoscape.js visualization + YAML config for multi-agent prompt orchestration
- Config externalization and MCP readiness (2026-03-16) — Moved backend_url, haiku_model, db_pool_max to config.py; added /health check for MCP server initialization
- Dual-layer memory distillation (2026-03-16) — Raw JSONL → interaction_tags → 5 memory files pipeline; fixed session_bulk_tag() for consistency across both tables
- Session phase persistence and tag deduplication (2026-03-15) — Phase loads from DB on init, saves via PATCH; 149 tags with 0 duplicates; removal propagates across all views

## Active Features / Bugs / Tasks

### Bug

- **hooks** `(2 events)`

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

**[2026-03-17]** `issue_report` — PROJECT.md load time exceeds 1 minute on free Railway tier; investigating whether root cause is DB query latency or file I/O; requires pagination/lazy-loading analysis.

**[2026-03-17]** `bug_report` — aiCli project disappeared from recent projects list; underlying cause unclear (UI state bug vs DB query regression); openProject() function verification needed.

**[2026-03-16]** `feature_complete` — Multi-agent workflow system analyzed and approved; async DAG executor with Cytoscape.js visualization and YAML config for orchestrating multi-agent prompt chains.

**[2026-03-16]** `refactor_complete` — Config externalization finished: backend_url, haiku_model, db_pool_max moved to config.py; /health check endpoint added for MCP server readiness verification.

**[2026-03-16]** `feature_complete` — Dual-layer memory distillation pipeline implemented: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot rules, aicli rules); session_bulk_tag() fixed for table consistency.

**[2026-03-15]** `bug_fix` — Session phase persistence resolved: phase loads from DB on init and persists via PATCH /chat/sessions/{id}/tags; tag deduplication audit found 149 tags with zero duplicates; removal propagates across Chat/History/Commits.

**[2026-03-10]** `performance_optimization` — Eliminated redundant SQL calls by implementing load-once-on-access pattern; tag cache loaded once per project tab and updated only on explicit save.

**[2026-03-10]** `feature_approved` — Nested tags hierarchy expanded beyond 2-level limit via parent_id FK; login remains first-level only; tree UI implemented in Planner with unlimited depth support.

**[2026-03-10]** `ux_improvement` — Planner action visibility increased via 3-dot menu button replacing small action buttons; unarchive capability added; AI suggestions marked clearly as requiring approval.

**[2026-03-10]** `bug_identified` — Tags saved in UI disappear on session switch; unknown if UI rendering issue or DB save failure; root cause investigation deferred.