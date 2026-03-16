# Project Memory — aicli
_Generated: 2026-03-16 19:01 UTC by aicli /memory_

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
- **high-level-design** `(52 events, 51 commits)`
- **retrospective** `(52 events, 51 commits)`
- **low-level-design**

### Feature

- **pagination** `(94 events, 51 commits)`
- **auth** `(58 events, 51 commits)`
- **shared-memory** `(3 events)`
- **mcp** `(1 events)`
- **graph-workflow** `(1 events)`
- **workflow-runner** `(1 events)`
- **tagging**
- **test-picker-feature**
- **UI**
- **dropbox**
- **billing**
- **embeddings**

### Phase

- **discovery** `(2 events)`
- **development** `(1 events)`
- **prod**

### Task

- **memory** `(96 events, 51 commits)`
- **implement-projects-tab** — Build the UI for managing features/tasks/bugs

## Recent Work (last 10 exchanges)

**[2026-03-16 19:00]** `claude_cli/claude`
Q: I do mention to sotre the prompts in database, would there be a way to change the prompts as it might be improved over time (or stored that as local md files linked ..) I do want to store the prompts 
A: Good design direction. Here's how this maps cleanly to what's already planned:  ---  ## Design: Agent Roles in Database  ### Schema (`agent_roles` + `agent_role_versions`)  ```sql -- Live role definitions CREATE TABLE agent_roles (     id        SERIAL PRIMARY KEY,     project   TEXT NOT NULL DEFAUL

**[2026-03-16 18:52]** `claude_cli/claude`
Q: I do see you have crete a defualt pipe line in the Planner tab that run defualt Pipeline . where is this pipeline configure ? also there used to be parent - child support (for example UI -> dropbox) w
A: Now I have the full picture. Let me answer all three questions clearly.  ---  ## Answers to your questions  ### 1. Where is the "Run Pipeline" configured?  It's in `ui/backend/core/work_item_pipeline.py` — **completely hardcoded**. 4 stages are Python-coded directly: PM → Architect → Developer → Rev

**[2026-03-16 18:34]** `claude_cli/claude`
Q: I would like to start working on the workflows - the goal is to be able to be similar to https://www.specrails.dev/docs/workflows, you can check also the github - https://github.com/fjpulidop/specrail
A: Now I have everything I need. Let me write the comprehensive comparison and design proposal.  ---  ## Workflow System Design: Comparison & Proposal  ### What the two external systems do  **specrails** is essentially a **Claude Code agent system** — 12 specialized prompt files (`.md` role definitions

**[2026-03-16 18:26]** `claude_cli/claude`
Q: are you using the mcp now?
A: ---  **To answer your question directly:**  No, I'm not using the MCP in this session. Everything I did was via direct HTTP calls (`curl`, Python `urllib`).  **What changes:**  - `.mcp.json` is now at the project root — Claude Code will pick it up **on next session start** - `enableAllProjectMcpServ

**[2026-03-16 18:02]** `claude_cli/claude`
Q: Keys are stored at my .env file which you can load - for claude api the key is under ANTHROPIC_API_KEY and for openai the key is under OPENAI_API_KEY
A: Everything is working end-to-end. Here's the full picture:  ---  ## Full Pipeline — Now Working  ### What just happened in sequence: 1. **Bug found and fixed** — `ARRAY_AGG(uuid[])` came back from psycopg2 as a raw string `'{uuid1,uuid2}'`, causing `[str(i) for i in ids]` to iterate over characters 

**[2026-03-16 17:42]** `claude_cli/claude`
Q: Can you run the /memory and go over current architecure - how data is stored, how mcp is used, go ver all memory layer. and check that tagging are working properly and helping to embed/retrive data by
A: Now I have a complete picture. Let me give you a clear, honest assessment.  ---  ## `/memory` Run Results  **Ran successfully** — generated 5 files at 17:43 UTC. Result: `"synthesized": false` because it used a cached synthesis (last full synthesis was at 01:35 today, less than 20 prompts ago — with

**[2026-03-16 01:34]** `claude_cli/claude`
Q: Can you summersie all improvement - would that make the systme better perfromed , would memroy work better? doad mcp can provide more accurate answer in order to manage work item , create workflow bas
A: ## Complete System Improvement Summary  ---  ### What Was Built (7 Parts)  **Before:** Every LLM call got either 40 raw JSONL entries (noisy, expensive) or a CLAUDE.md (too coarse). Tags lived in per-project tables. Work items were just entity values with no intelligence. MCP had read-only project s

**[2026-03-16 01:26]** `claude_cli/claude`
Q: After this refactor - can you check if tags are well used ? is memroy improved by new summersation process? will mcp can be improved answering and storing data related to the project and will I be abl
A: Here's a complete answer to your questions:  ---  ## Audit Results + What Was Fixed  ### Tags — mostly good, one gap fixed The old `event_tags_{project}` system is fully wired: chat, history sync, and the tag-by-source-id UI all write to it. The new `interaction_tags` table (for the memory pipeline)

**[2026-03-16 00:48]** `claude_cli/claude`
Q: I have started to look in some other solution like https://github.com/danshapiro/trycycle and www.specrails.dev/docs/workflows (github page - https://github.com/fjpulidop/specrails/tree/main) and got 

**[2026-03-16 00:19]** `claude_cli/claude`
Q: I would like to optimise the code : check each file, make sure code is in used and all method are required. make sure that there are no text string that need to be in config file. for example backen u
A: All clean. Here's a summary of everything fixed:  ---  ## Optimization fixes applied  | Issue | File | Fix | |---|---|---| | `haiku_model` hardcoded in 6 places | `config.py` | Added `haiku_model: str = "claude-haiku-4-5-20251001"` | | `backend_url` hardcoded | `config.py` | Added `backend_url: str 
