# Project Memory — aicli
_Generated: 2026-04-24 18:30 UTC by aicli /memory_

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
- Database schema as single source of truth (db_schema.sql) with m001-m052 migration framework; INT PKs in canonical order (id → client_id → project_id → user_id); created_at/updated_at at table end before embedding
- Feature snapshot layer (mem_ai_feature_snapshot): merges user requirements with work items; planner_tags cleaned with deliverables JSONB
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Session history UI persistence: Chat/History tabs display sessions with source badge (CLI/UI/Workflow), phase chip, session ID (last 5 chars), timestamp YY/MM/DD-HH:MM
- Mirror tables (mem_mrr_*) capture raw events with user_id INT; all 18 tables standardized with canonical column order and created_at/updated_at timestamps

## In Progress

- Use Cases UI separation: Work Items and Use Cases now on separate pages in left sidebar; Work Items shows pending AI-classified items awaiting approval; Use Cases displays approved use cases with expandable cards
- Copy item functionality: ⎘ button copies work item text to clipboard in formatted Markdown (name, type, ID, summary, deliveries); removed unintended item duplication on copy
- MD file navigation from Use Cases: clicking ✎ MD button auto-navigates to Documents section and opens the corresponding Markdown file by path
- Use Case approval workflow: 'Approve X pending' button commits child items (AI-prefixed IDs) to real work item IDs (FE1001, BU1002, etc.); pending items hidden until approved
- Hook-log endpoint stability: m050 fixed silent DB error in prompt storage; hook health now shows 0.1h (last prompt 8.3h ago); 531 total prompts loaded (389 DB + ~142 JSONL merged)
- UI dropdown styling: parent selector in Use Cases now has proper background color and visual clarity for better user understanding

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

**[2026-04-24 18:21]** `ui/`
Q: It started to work. some improvemnts:   Title suppose to be US1003 - Userc case name (add the use case Id at the beginign for the title)  created date, updated date - at the top of the file (not as <!
A: The file was created at the correct path. Everything is working:  **Summary of what's done:**  1. **`get_md()`** — regenerates with new format: `# US1002 — Use Case Name`, readable Created/Updated dates, `## Summary`, `## Requirements`, `## Completed (N)`, `## Open Items (N)`, bullet items with `<!-

**[2026-04-24 17:56]** `ui/`
Q: It is still dont find the file. the file should be stored unde documents. and it is still not created when user click on the md file button

**[2026-04-24 17:52]** `ui/`
Q: When I am trying to aeding the use case usng md file , I still see an error - Not found . path is under use_cases.. and for use case - Work Item Management & Metadata System the path is work-item-mana
A: Two fixes:  1. **MD "Not found"** — clicking "✎ MD" now calls `api.wi.md.refresh()` first, which generates the content and writes the file to disk, before navigating to Documents. Previously the file didn't exist on disk unless it had been through the old backlog pipeline.  2. **Rename arrow positio

**[2026-04-24 17:44]** `ui/`
Q: Approve items suppose to be only on work items - when user approved they get real ID , in use cases - all items already approved.
A: Done. The "Approve X pending" button is removed from the Use Cases toolbar — it only exists in Work Items now.

**[2026-04-24 10:59]** `ui/`
Q: when i am tryiong to  open the md file,it show error - file not found. Also what is the butoon approve 12 pending is  used for in the use case ?
A: Both fixes done. Now for your second question:  **"Approve X pending" button in Use Cases** — this approves child items under that UC that have been AI-classified but not yet manually approved. Items with IDs starting with `AI...` are "pending" — they've been created by the classify pipeline but nee

**[2026-04-23 18:04]** `ui/`
Q: Ok. When I press copy. I do see the item duplcated, which I am not sure is needed (same item with (copy) at the end) . when user is copies is suppose to copy as you mention. Also the change parnet but
A: All looks clean. Here's a summary of what was implemented:  ---  **MD → Documents navigation** — clicking "✎ MD" in Use Cases now navigates to the Documents section and auto-opens the file: - `documents.js`: `renderDocuments(container, projectName, opts = {})` accepts an `opts.openFile` path; after 

**[2026-04-23 16:58]** `ui/`
Q: that looks better and started to work properly. what is the copy item button is used for ? can I copy to conetent as text ?
A: The ⎘ button now copies the item's text to clipboard in this format:  ``` ## Audit and clean planner_tags table schema Type: task  |  ID: TA4001  ### Summary Review planner_tags table for redundant/unused columns...  ### Deliveries Schema audit completed. Recommendations provided... ```  Includes na

**[2026-04-23 10:05]** `ui/`
Q: I did not wanted 2 tabs under  work items. I wanted work item (selct from the left side bar) to show work items and a new section Use cases that managin the  use  cases. Also I do see now that the def
A: Everything is in place. Here's what changed:  **Navigation (main.js):** - "Work Items" remains in the left sidebar (📥 icon) — shows pending items + classify flow - New "Use Cases" entry added below it (◻ icon) — completely separate page showing approved use cases  **Work Items page** — now clean, no

**[2026-04-23 09:20]** `ui/`
Q: it is still not working and it seems the the UI is broken. instesd of having 2 tab - Work itersm and use cases on the top. can you make another tab ob the right. first one  is for Work items  and the 
A: The empty state message will say "Click Classify to generate AI-suggested use cases from **199 prompts** + **667 commits**." — clear and actionable.  Here's what changed and what you should see now:  **Tab layout**: The two tab buttons are now on the **right side** of the toolbar, grouped as a borde

**[2026-04-23 09:06]** `ui/`
Q: I still cannot see all work_items in Work itme tab. Also use case not showing any items. And I do seethe message Hook offline(last promt 8.3H) - which makes sense  as it was the lat prompt
A: Good. The hook is now healthy (0.1h). Here's a summary of what was done and what to expect:  **What I fixed:**  1. **Work Items tab now shows all items** — changed `_renderList()` to display ALL use cases (not just pending AI* ones). Previously, once a UC was approved, it disappeared from Work Items
