# Project Memory — aicli
_Generated: 2026-04-24 22:53 UTC by aicli /memory_

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
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_feature_snapshot; Mirror: mem_mrr_commits_code, mem_mrr_prompts, mem_mrr_events; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}; Shared: mng_users, mng_clients, session_tags
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extensions + m001-m074 migration framework
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
- **llm_provider_location**: agents/providers/ with pr_ prefix
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
- Database schema as single source of truth (db_schema.sql) with m001-m074 migration framework; INT PKs canonical order (id → client_id → project_id → user_id); timestamps + embedding at table end
- Work Items vs Use Cases separation: Work Items tab shows pending AI-classified items; Use Cases tab displays approved items with expandable cards, due dates, and recursive descendant tracking
- Use Case lifecycle: due dates (calendar MM/DD/YY or day offsets), completion validation (all descendants must finish), completed_at timestamp tracking, markdown file generation with type-based categorization
- Session history UI with source badges (CLI/UI/Workflow), phase chips, session ID (last 5 chars), timestamp YY/MM/DD-HH:MM; proper session loading on startup without 15s delay
- Completed section and Planning grouping: left sidebar reorganized as Planning group (Work Items/Use Cases/Documents/Completed); completed_at column + auto-move MD to documents/completed/
- Text selection enabled across UI: removed `user-select: none` from body to allow clipboard copy-paste in history, work items, and markdown content

## In Progress

- MD file format refinement: Removed HTML comment tags; created/updated dates now plain text; item counts (bugs/features/tasks) computed from recursive CTEs; status badges derived from database state; recursive CTE ensures all descendants included
- Use Case due date system: Calendar (MM/DD/YY) and day offset support; re-parent conflict auto-resolution when items exceed parent due date; completion validation ensures all descendants finished by parent due date
- Session ID and timestamp visibility: Chat/History tabs show last 5 chars in headers; full UUID on click for copy; YY/MM/DD-HH:MM timestamps next to prompts; correct current session loads on startup
- Work Items to Use Cases UI separation: Two-tab system (Work Items | Use Cases) with different functionality; pending AI-classified items require approval before getting real IDs; approved items show in Use Cases only
- Completed section implementation: New Planning group on left sidebar with Completed subsection; complete_use_case() validates descendant completion and auto-moves MD to documents/completed/
- Text selection and clipboard fix: Flipped user-select approach to enable copy-paste across history entries, work item text, and markdown content in Electron UI

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

### Use_case

- **Work Item Management & Metadata System** `[open]` — Build comprehensive work item lifecycle management with AI-generated metadata, tag integration, and 
- **MCP Configuration** `[open]` — Set up Model Context Protocol (MCP) configurations for multiple LLM providers and IDEs (Claude Code,

## Recent Work (last 10 exchanges)

**[2026-04-24 22:46]** `ui/`
Q: I would like to clean refactor the  worksqapce/_tamplate that will be used as a tamplate for any new project. once that is updated, make sure the aiCli folder is also updated. the goal os to remove un
A: Here's the final structure and what changed:  ---  ## New `_templates/` Structure  ``` _templates/ ├── cli/ │   ├── claude/ │   │   ├── hooks/          ← 10 hook scripts (was: _templates/hooks/) │   │   └── settings.template.json │   └── mcp.template.json   ← shared Claude + Cursor MCP config ├── pi

**[2026-04-24 22:30]** `ui/`
Q: it look like in work item i do see the option parent child/ merge. but when I do parent-child, the child disapred insted of been linked as a child in the UI. in use case it is not working. Also can yo
A: Backend is healthy. Here's a summary of all fixes:  ---  ## Fixes Applied  ### 1. Work Items tab — child no longer disappears  **Root cause**: `_renderList()` only showed items whose parent was a UC. When A became a child of B (non-UC), A was classified as an "orphan".  **Fix**:  - Computed `allSubI

**[2026-04-24 22:08]** `ui/`
Q: I can see that I can move items in use case and in work item - but they are not linked as prent-child. I would like to be able to linked as parent child or merged when user drag an item above another 
A: The `/wi/{project}/{item_id}/merge` route is registered. Everything is in place. Here's a summary of what was implemented:  ---  ## Drag-to-Link/Merge — Implemented  ### What was built  **Backend (3 changes):** - `m076_wi_merged_into` migration — adds `merged_into UUID` self-FK to `mem_work_items` -

**[2026-04-24 21:49]** `ui/`
Q: I do see duplicates title at the md file - for example Features (6) or Tasks (7) .. Also there is title Requirements (1) - twise which is not suppose to be (all requirements suppose to be under requir
A: The MD is now clean. Let me summarize what was fixed and what was done:  ---  **Issues fixed:**  1. **Duplicate `### Features (6)` / `### Tasks (7)` headers** — Root cause: previous `save_md()` parser didn't stop at `##` / `---` boundaries, causing 7 item summaries to accumulate subsequent section h

**[2026-04-24 21:10]** `ui/`
Q: Looks better. in the md file I do see that there is title and line below there is bug/feature.. and below desc. there is no need for the line below the tile as it all grouped already as bugs, features
A: The MD is now clean and correct:  - `## Requirements` — AI1070, AI1075 (both requirement items) - `## Completed (20)` — 7 bugs, 6 features, 7 tasks (no duplicates, no `### Requirements`) - `## Open Items (3)` — 1 bug, 1 feature, 1 task  **Root cause**: The old `save_md()` parser didn't stop at `##`/

**[2026-04-24 21:04]** `ui/`
Q: I do see that it is not possible to makr content and copy paste in the UI (for example mark some content using maouse in order to copy to the clipboard) is it possible to enabe that? Also in history -
A: That's the complete fix. To summarize what changed and why:  **Root cause:** `body { user-select: none }` was blocking text selection everywhere. The "allow" whitelist only covered chat messages, code blocks, and `.view-scrollable` — missing history entries, work item text, MD content, etc.  **Fix:*

**[2026-04-24 19:31]** `ui/`
Q: Looks better, the md file is not looks good yet. dont think there is need to add the <!-- tags >> this data will be save in the database and will be pupoluated from the databse (number of taks, number
A: The format looks excellent. Here's a summary of all changes made:  ---  **MD format — before vs after:**  | Before | After | |--------|-------| | `<!-- STATUS: 2 -->` etc. | Removed — no HTML comments anywhere | | `Created: ... \| Updated: ...` + extra `<!-- CREATED -->` | `created: 2026-04-23 \| up

**[2026-04-24 19:05]** `ui/`
Q: I would like to add completed section on the left side panel.  And arrange that as group on the left - work Items, Use Cases, Documents and Complated. group named planning as all sections related to p
A: All working. Here's a summary of what was implemented and is now live:  **Completed** - all features are fully implemented and working:  **Backend:** - Migration m074 applied — `completed_at TIMESTAMPTZ` column added to `mem_work_items` - `complete_use_case()` — validates all descendants are done (r

**[2026-04-24 18:54]** `ui/`
Q: the md file is not aligned to the use case. there are 21 complated tasks. md file should show complted bug - 7, complated feature - 6, complated tasks - 7. there is one requiremet that I dont see at t
A: Good — all stale MD files cleared. Now the "✎ MD" button in Use Cases will generate fresh files with the new format. Here's a summary of all fixes:  ---  **MD file fixes:**  1. **Missing items (21 → 0 bug)**: `get_md()` now uses a **recursive CTE** to get all descendants (not just direct children). 

**[2026-04-24 18:31]** `ui/`
Q: use case improvemnt - I have asked to add due data, so user can update a due date per use case (in use cases).   If due date is set in use case, all item connected must finished by this due date . due
A: All changes are in place. Here's a summary of what was implemented:  ---  ## Changes implemented  ### Backend (`memory_work_items.py`)  **`update()` — 3 improvements:**  1. **Initial SELECT now includes `due_date`** — needed to detect the conflict case 2. **Re-parent conflict auto-resolution**: when
