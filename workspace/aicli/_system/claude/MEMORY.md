# Project Memory — aicli
_Generated: 2026-03-17 20:20 UTC by aicli /memory_

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

- **hooks** `(94 events, 51 commits)`

### Doc_type

- **customer-meeting** — dsds `(54 events, 51 commits)`
- **high-level-design** `(52 events, 51 commits)`
- **retrospective** `(52 events, 51 commits)`
- **low-level-design**
- **Test**

### Feature

- **pagination** `(94 events, 51 commits)`
- **auth** `(58 events, 51 commits)`
- **mcp** `(4 events)`
- **shared-memory** `(4 events)`
- **graph-workflow** `(1 events)`
- **UI** `(1 events)`
- **workflow-runner** `(1 events)`
- **tagging**
- **billing**
- **embeddings**
- **test-picker-feature**
- **dropbox**

### Phase

- **discovery** `(2 events)`
- **development** `(1 events)`
- **prod**

### Task

- **memory** `(97 events, 51 commits)`
- **implement-projects-tab** — Build the UI for managing features/tasks/bugs

## Recent Work (last 10 exchanges)

**[2026-03-17 20:13]** `claude_cli/claude`
Q: Planner works partial - I do see the nested work on some category like doc_type but in bug or feature ui is diffrent and this is not working. also I do see there is life cycle project, but I am not su
A: Here's a summary of everything done and answers to your questions:  ---  ## What was fixed  **Planner consistency** — removed the split between `entity_values` (doc_type etc.) and `work_items` (feature/bug/task). Now ALL categories use the same `_renderTagTable` renderer reading from `entity_values`

**[2026-03-17 18:50]** `claude_cli/claude`
Q: I would like to go over on all the feutre and plan propery to Planer and Worklow as they are linked. I have created tagging mechasim in order to help map prompt/commit to proper tags. the aiCli can su
A: Here's a summary of all changes made:  ---  ## Changes Made  ### Tab renames (`main.js`) - `"Workflow"` → `"Pipelines"` (PROJECT_TABS + global sidebar nav) - `"Prompts"` → `"Roles"` (PROJECT_TABS)  ### Nested tag button (`entities.js`) - Added `+▸` button directly in **every regular tag row** (previ

**[2026-03-17 18:29]** `claude_cli/claude`
Q: I dont see nay changes from the last improvement - current planner do not supposrt nested (parent-child) tags as it used to be. also, pipeline seems to be hardcoded and used the new infrastrucre of wo
A: `agent_run_id` is `INT` (not UUID), so `str(row["agent_run_id"])` is fine — it just converts the int to string. That's correct.  The three fixes applied to `work_items.py`:  1. **`WorkItemCreate` model** — added `parent_id: Optional[str] = None` 2. **INSERT query** — added `parent_id` column and `bo

**[2026-03-17 18:28]** `claude_cli/claude`
Q: What is the claude agent sdk is uded for can it be used for my use cases for mutli agents (project manager (high design), develop , tester , reviewer) ?
A: ## Claude Agent SDK vs Your Current Multi-Agent System  ### What is the Claude Agent SDK?  The **Claude Agent SDK** is Anthropic's official Python/TypeScript framework for building AI agents that can: - Execute tools (file read, bash, web search, custom MCP tools) - Delegate to **subagents** (specia

**[2026-03-17 18:18]** `claude_cli/claude`
Q: can you use the mcp tool and explain what the code is doing ?
A: Here's what **aicli** does:  ## aicli — Shared AI Memory Platform  **Core idea**: When you switch between different AI tools (Claude CLI, Cursor, ChatGPT, the aicli web UI), they all forget your project context. aicli solves this by giving every LLM the **same persistent memory**.  ### What the code

**[2026-03-17 14:35]** `claude_cli/claude`
Q: In the project I used to see the aiCli project, and I do not see that now. also when I press in my recent project - aiCli - it is start to load after few seconds. loading PRPJECT.md file take really l
A: Everything looks correct. Let me do a final check on the full `openProject` function to make sure it's clean:

**[2026-03-17 13:33]** `claude_cli/claude`
Q: Somehow, I cannot see the prject now in order at me lat project.. also when I open the project it takes quite long time to load summery and History. can check why is that? and add some flow to explain
A: Now let's verify the key changes are correct with a quick sanity check:

**[2026-03-17 13:30]** `claude_cli/claude`
Q: can you use the mcp tool and explain what the prject is about ?

**[2026-03-16 19:02]** `claude_cli/claude`
Q: yes
A: All changes look correct. The Agent Roles implementation in `graph_workflow.js` is now complete. Here's a summary of what was done in this session:  **`graph_workflow.js` — completed:** - `_gwOnRoleChange(val)`: now auto-populates `cfg-provider` / `cfg-model` from the selected role's defaults, updat

**[2026-03-16 19:00]** `claude_cli/claude`
Q: I do mention to sotre the prompts in database, would there be a way to change the prompts as it might be improved over time (or stored that as local md files linked ..) I do want to store the prompts 
A: Good design direction. Here's how this maps cleanly to what's already planned:  ---  ## Design: Agent Roles in Database  ### Schema (`agent_roles` + `agent_role_versions`)  ```sql -- Live role definitions CREATE TABLE agent_roles (     id        SERIAL PRIMARY KEY,     project   TEXT NOT NULL DEFAUL
