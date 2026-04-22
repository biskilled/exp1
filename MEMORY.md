# Project Memory — aicli
_Generated: 2026-04-22 14:57 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel; Dashboard tab for pipeline visibility
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop
- **database_schema**: m001-m052 migration framework; canonical INT PK order (id → client_id → project_id → user_id); unified mem_ai_* tables + per-project tables + shared users/roles tables
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extensions + m001-m052 migration framework
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+ with pgvector extensions + m001-m052 migration framework
- **build_tooling**: npm 8+ + Electron-builder + Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev
- **prompt_management**: core.prompt_loader module with centralized prompt caching
- **schema_management**: db_schema.sql + db_migrations.py (m001-m037)
- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; Shared: users, usage_logs, transactions, session_tags, entity_categories, planner_tags, mng_tags_categories
- **embeddings**: OpenAI text-embedding-3-small (1536-dim)
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **schema_migrations**: m001-m050 framework with db_schema.sql as source of truth
- **llm_provider_location**: agents/providers/
- **database_migrations**: m001-m052 framework with db_schema.sql as source of truth
- **schema_core**: mem_tags_relations (unified), planner_tags (with inline snapshot fields), mem_ai_events, mem_mrr_prompts/commits

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; .ai/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags, facts, work items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users → Projects
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules in agents/providers/ with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts/feature_snapshot
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
- Database schema as single source of truth (db_schema.sql) with m001-m052 migration framework; INT PKs in canonical order (id → client_id → project_id → user_id)
- Feature snapshot layer (mem_ai_feature_snapshot): merges user requirements with work items; planner_tags unified with deliverables JSONB
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Column standardization: INT primary keys in canonical order; created_at/updated_at at table end; embedding as final column
- Session history UI persistence: Chat/History tabs display sessions with source badge, phase chip, session ID (last 5 chars), and timestamp YY/MM/DD-HH:MM

## In Progress

- Database schema refactor (m051-m052): user_id migrated from UUID to SERIAL INT; all 18 tables reordered to canonical form; updated_at added to mirror tables
- Session history UI improvements: Chat and History tabs display sessions with source badge, phase chip, session ID, and timestamp; stale session loading fixed
- Hook-log endpoint verification: all 531 prompts (389 DB + ~142 JSONL merged) loading correctly with proper sort order and session attribution
- Chat tab session persistence: current session highlighted on load using last_session_id from runtime state; localStorage cache supports offline viewing
- Event table cleanup: importance column dropped; system metadata tags stripped from 1441 events; only phase/feature/bug/source user tags retained
- Dashboard and pipeline UI: new Dashboard tab added; Cytoscape.js visualization with 2-pane approval panel; pipelines runnable from planner/docs/chat tabs

## Active Features / Bugs / Tasks

### Bug

- **ui-rendering-bugs** `[open]` — Diagnosed bind error on port 8000 caused by stale uvicorn instance; verified backend is healthy.

### Feature

- **ui-rendering-bugs** `[open]` — User reports history shows only small text instead of full prompt/LLM response and requests copy fun
- **general-commits** `[open]` — Add memory embedding and event extraction to memory promotion flow

### Task

- **Audit and clean planner_tags table schema** `[open]` — Review planner_tags table for redundant/unused columns: drop seq_num (always null), merge source int
- **ui-rendering-bugs** `[open]` — Provided clean restart procedure using dev script with NODE_ENV=development after killing stale back
- **general-commits** `[open]` — Refactor memory promotion and work item column naming across DB/memory/router modules
- **discovery** `[open]` — Greeting and project context refresh

## Recent Work (last 10 exchanges)

**[2026-04-15 23:03]** `claude_cli/`
Q: I did ask to change the position in the table as well which not happend . for example in mem_mrr_promot - user_id suppose to be after project_id. not need for cimmited_at as there is updated_at and cr
A: All tables are correctly ordered. Here's a summary of everything done:  **Migration m052 — done (18 tables rebuilt):**  | Rule | Result | |------|--------| | `id → client_id → project_id → user_id` order | ✅ All tables | | `created_at → updated_at → embedding` always at end | ✅ All tables | | `commi

**[2026-04-15 22:38]** `claude_cli/`
Q: I would like to move to another database refactor - user_id this suppose to be int (same as project_id and clinet_id) not string. I would like also to add updated_at for each mirror table. for all mir
A: Clean startup, no errors. Migration m051 is complete and the backend is running correctly. Here's what was accomplished:  **Migration m051 — done:** - `mng_users.id`: now `SERIAL INT` PK; old UUID preserved as `uuid_id VARCHAR(36)` - `updated_at` added to: `mng_users`, `mng_clients`, all `mem_mrr_*`

**[2026-04-15 21:42]** `claude_cli/`
Q: it still loading on the start session 7d89c79f-b6f1-4bd4-a93f-09f2603fd1b1 and after 15 seconds it is updated to the right session (current one) . I would like to load the current session on start
A: The flow is now:  1. `renderChat()` → `_sessionId = null` (clears stale session) 2. `_loadSessions()` starts → **immediately** reads `state.currentProject.dev_runtime_state.last_session_id` and sets `_sessionId = "f6648726..."` — **synchronous, no network call** 3. Cache renders from localStorage → 

**[2026-04-15 21:25]** `claude_cli/`
Q: The sort is ok. but when it is loading it loading with session id - 7d89c79f-b6f1-4bd4-a93f-09f2603fd1b1 whule the current session is f6648726-1e7f-48bf-b604-4c74bf7c8154. it is update the the current
A: Here's what was fixed:  **Stale session ID on load** — Two root causes: 1. `_sessionId` was a module-level var that persisted across tab navigations. Fixed by resetting it to `null` at the start of `renderChat()` (along with `_appliedEntities`/`_pendingEntities`). 2. The localStorage cache rendered 

**[2026-04-15 21:12]** `claude_cli/`
Q: The loading is still an issue. when system start - I do not see all prompts only prompts started from certain point . is it loading from _system/session files ? why there are so many files over there 
A: The sort is now correct with `limit=500` (April at top, March at bottom). The previous test with `limit=10` only showed the first 10 of all 389 entries which happened to be DB-only from the old code run. The total is now **531** (389 DB + ~142 merged from JSONL).  The fix is working correctly: - Apr

**[2026-04-15 21:04]** `claude_cli/`
Q: lloks better . the session_id on the right panel is shown not on the top. (can you show just session_id at the tab where there is feature list box on the left and tag on the right? Also phase is alrea
A: Only the definition, no calls. All changes are clean. Here's what was done:  ---  **1. Session ID in tag bar** (not in messages): - Added a monospace `(ab3f9)` badge between the entity chips and `+ Tag` button - Badge is hidden when no session is active; shows last 5 chars when a session loads - Cli

**[2026-04-15 20:37]** `claude_cli/`
Q: I understand the issue. you have worked on Tab prompts in history and I am reffering to chat . in chat - each session suppose to be on the left. user can access into a chat and continue. I would like 
A: All changes are in place. Here's a summary of everything that now works in the **Chat view**:  ---  **Left sidebar — each session item now shows:** - `CLI · development · (ab3f9)` — source badge, phase chip, last 5 chars of session ID in monospace - Hovering shows full session ID as tooltip  **When 

**[2026-04-15 19:31]** `claude_cli/`
Q: test: is hook-log working now after m050?

**[2026-04-15 19:02]** `claude_cli/`
Q: I still do not see the change in the chat tab. I do see the 5 last digit in the test prompts . I would like that to be at the header CLI <pahse> (session number). I would like to see all the session i
A: All changes look correct. Here's a summary of everything that changed:  ---  **Session header** now shows: `▼ CLI · development · (ab3f9) · 3 prompts · 26/04/15-19:31` - Source label: `claude_cli` → `CLI`, `ui` → `UI`, `workflow` → `Workflow` - Phase chip (blue) extracted from entries' tags - Sessio

**[2026-04-15 18:51]** `claude_cli/`
Q: I startrd to see the latest prompts which is good. I do not see on each promot the time stamp next to YOU . also I do not see the session id anywhere. it suppose to be one the left panet (5 last charc
A: All changes look correct. Here's a summary of what was changed in `history.js`:  1. **Session ID badge**: `sid.slice(-4)` → `sid.slice(-5)` — shows last **5** chars as `…xxxxx` in the left panel header  2. **Session ID in body (right pane)**: Replaced the plain monospace text with a styled banner:  
