# Project Memory — aicli
_Generated: 2026-03-18 18:21 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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

- **hooks**

### Doc_type

- **high-level-design**
- **low-level-design**
- **customer-meeting** — dsds
- **retrospective**
- **Test**

### Feature

- **shared-memory**
- **graph-workflow**
- **billing**
- **auth**
- **embeddings**
- **tagging**
- **mcp**
- **workflow-runner**
- **test-picker-feature**
- **UI**
- **dropbox**
- **pagination**

### Phase

- **discovery**
- **development**
- **prod**

### Task

- **implement-projects-tab** — Build the UI for managing features/tasks/bugs
- **memory**

## Recent Work (last 10 exchanges)

**[2026-03-18 18:15]** `claude_cli/claude`
Q: There are some error - on the first load, it lookls like Backend is failing (after thay it succeed). I have tried to run the memory - and ther ewas an error in line 1120 - {code_dir}/CLAUDE.md  - code

**[2026-03-18 17:44]** `claude_cli/claude`
Q: it looks like it is a bit broken, I have got an error - '_Database' object has no attribute 'ensure_project_schema'. Did you mean: '_ensure_shared_schema'? also I do not see my AiCli project (only at 
A: Everything is working. Here's the summary of all fixes applied:  ---  **3 issues fixed:**  **1. `main.py`** — removed the stale `db.ensure_project_schema(settings.active_project)` call  **2. `database.py` — 4 schema fixes:** - `_ensure_schema()` now runs DDL statement-by-statement instead of as one 

**[2026-03-18 16:00]** `claude_cli/claude`
Q: That is correct. it is bed pattern to use clinet name. there is already mng_users table that can manage client as well (client can have multiple users, but probably small amount if users up to 5 max p

**[2026-03-18 15:49]** `claude_cli/claude`
Q: I would like to know what do you think about the architecure ? Assuming there might be diffrent clients (for each clinet might be diffrenet projects) . Also what is the best way to manage free / unreg
A: ## Architectural Review: 3-Layer Client/Project Tables  ### What's Good  The three-tier naming is clear and the seeding pattern (`mng_` → `cl_local_` on first run) is clean. For a single-tenant tool it works well today.  ---  ### Key Concerns at Scale  **1. Table proliferation**  With the current de

**[2026-03-18 12:51]** `claude_cli/claude`
Q: I would like to make sure the client table are also aligned - for example mng_session_tags - is related to client (that can have multiple projects) also entitiy is per client. currently, as I am testi

**[2026-03-18 12:00]** `claude_cli/claude`
Q: clean that up . also I do remember there was graph support for memroy usage, but I dont see any record in. how graph tables are used in the app, who suppose to manage that? this is not suppose to be a
A: All endpoints working correctly. Here's a summary of everything done:  **All `mng_graph_*` references eliminated** across 4 files:  | File | Changes | |------|---------| | `routers/graph_workflows.py` | Added `project: str = Query("")` to 12 endpoints; all `mng_graph_*` → `db.project_table()` | | `c

**[2026-03-18 11:51]** `claude_cli/claude`
Q: I do see the table mng_session_tags, I also see session_tags.json file at the project workspace - is it in used , what is it for ?
A: Everything is working. Here's the final state:  **Database — 24 tables, clean split:**  | Prefix | Count | Tables | |--------|-------|--------| | `mng_` | 14 | Global config: users, billing, entity taxonomy, graph workflows, agent roles | | `pr_local_aicli_` | 10 | Project data: commits, events, emb

**[2026-03-18 10:46]** `claude_cli/claude`
Q: looks better. why memory_items and project_facts are under systeme managament tables? there are not part of project ?
A: All endpoints working. Let me update MEMORY.md to reflect the final table structure:

**[2026-03-17 21:06]** `claude_cli/claude`
Q: Can you run the command as well, as I dont see any change in the database . also I think that there are old tables that are not in used
A: Clean. Here's the complete summary:  **Before:** 29 tables (mixed naming, 5 stale bare tables)   **After:** 24 tables — perfectly organized  ### Dropped (stale legacy tables) `commits`, `embeddings`, `events`, `event_tags`, `event_links` — these were pre-project-split bare tables with old data; the 

**[2026-03-17 20:36]** `claude_cli/claude`
Q: before I continue - I do see quite lots of table used for this project. can you remove unused tables. also restrucure the table as - mng_TABLE_NAME for all aiCli managend tables (global table for all 
A: Clean. Let me also verify the `work_item_pipeline.py` core file is correct:
