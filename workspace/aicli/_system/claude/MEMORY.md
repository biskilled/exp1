# Project Memory — aicli
_Generated: 2026-03-16 18:44 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that combines a Python CLI, FastAPI backend, and Electron/Vanilla JS frontend to provide persistent, semantically-searchable project context across LLM interactions. It features nested tagging, multi-provider LLM support, dual-layer memory synthesis via Claude Haiku, PostgreSQL+pgvector semantic search, and an MCP server for Claude integration—currently refining workflow automation with async DAG execution and Cytoscape.js graph visualization.

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
- Commit-to-prompt linking via source_id timestamp; bidirectional tagging via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase; backfills history.jsonl ordered by created_at
- Real DB columns for phase/feature/session_id in events_{p} with indexes; tag cache loaded once per project tab (zero DB calls during chat)
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization + YAML config

## In Progress

- Workflow system design (2026-03-16) — Analyzed specrails pattern (Claude Code agent with 12 prompt roles) and external workflow tooling; evaluating integration approach for node-based async DAG executor with YAML config and Cytoscape.js UI
- Config externalization and optimization (2026-03-16) — Moved backend_url, haiku_model, db_pool_max to config.py; removed unused methods; added /health check for MCP readiness
- Memory distillation pipeline refinement (2026-03-16) — Implemented dual-layer summarization (raw JSONL → interaction_tags → 5 memory files); fixed session_bulk_tag() to write to both event_tags and interaction_tags tables
- MCP tool expansion for project management (2026-03-16) — Implemented create_entity, update_entity, list_entities, get_feature_status tools; verified JSON output accuracy
- Session phase persistence and backfill (2026-03-15) — Phase now loads from DB on init, saves via PATCH /chat/sessions/{id}/tags, backfills all matching history.jsonl entries preserving session order
- Tag deduplication and cross-view synchronization (2026-03-15) — 149 tags with 0 duplicates; removal via ✕ buttons propagates across Chat/History/Commits views; inline commit display per prompt

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
- **shared-memory** `(3 events)`
- **mcp** `(1 events)`
- **workflow-runner** `(1 events)`
- **embeddings**
- **billing**
- **test-picker-feature**
- **UI**
- **dropbox**
- **graph-workflow**
- **tagging**

### Phase

- **discovery** `(1 events)`
- **development** `(1 events)`
- **prod**

### Task

- **memory** `(96 events, 51 commits)`
- **implement-projects-tab** — Build the UI for managing features/tasks/bugs

**[2026-03-16]** `config.py` — Externalized backend configuration (backend_url, haiku_model, db_pool_max); added /health endpoint for MCP readiness validation. **[2026-03-16]** `workflow-design` — Analyzed specrails (12-prompt Claude Code agent pattern) and external tools; proposed node-based async DAG executor with YAML config and Cytoscape.js visualization for multi-agent workflows. **[2026-03-16]** `memory-pipeline` — Implemented dual-layer memory synthesis (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules); unified session_bulk_tag() to persist across event_tags and interaction_tags. **[2026-03-16]** `mcp-tools` — Expanded MCP server with create_entity, update_entity, list_entities, get_feature_status tools; verified JSON output correctness for project management queries. **[2026-03-15]** `session-phase` — Phase field now loads from DB on project init, persists via PATCH /chat/sessions/{id}/tags, backfills all matching history.jsonl entries ordered by created_at. **[2026-03-15]** `tag-sync` — Achieved 149 tags with 0 duplicates; cross-view removal via ✕ buttons propagates across Chat/History/Commits; added inline commit display per prompt.