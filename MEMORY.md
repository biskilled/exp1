# Project Memory — aicli
_Generated: 2026-04-25 10:25 UTC by aicli /memory_

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
- **config_management**: config.py + YAML pipelines + pyproject.toml + aicli.yaml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extensions + m001-m076 migration framework
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
- **database_migrations**: m001-m076 framework with db_schema.sql as source of truth
- **schema_core**: mem_tags_relations (unified), planner_tags (with inline snapshot fields), mem_ai_events, mem_mrr_prompts/commits
- **storage**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; .ai/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags, facts, work items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users → Projects
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules in agents/providers/ with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
- Database schema as single source of truth (db_schema.sql) with m001-m076 migration framework; INT PKs canonical order (id → client_id → project_id → user_id → created_at → updated_at → embedding)
- Work Items vs Use Cases separation: Work Items tab shows pending AI-classified items; Use Cases tab displays approved items with due dates, completion validation, auto-markdown generation
- Use Case lifecycle: due dates (calendar MM/DD/YY or day offset), completion validation (all descendants validated), completed_at timestamp, MD file auto-move to documents/completed/ on completion
- Drag-and-drop parent-child linking and merge functionality for work items with type validation (same-type only) and undo support via stored reverse API call closure
- Text selection enabled across UI for clipboard copy-paste; undo button in Work Items and Use Cases toolbars as persistent button (not popup)
- Template workspace refactor: _templates/ reorganized into cli/pipelines/hooks subdirectories with per-provider hooks; aicli/ folder synced with template changes

## In Progress

- Drag-and-drop parent-child/merge in Use Cases fixed via unconditional e.preventDefault() and document.elementFromPoint(e.clientX, e.clientY) target detection; relatedTarget=null bug on drop resolved
- Undo button implementation as persistent toolbar button in Work Items and Use Cases; stores reverse API call closure capturing original parent_id before link
- MD file generation aligned with use case structure: recursive CTE fetches all descendants, separate sections for Requirements/Completed/Open Items, no HTML comments, plain text timestamps
- Completed section added to left sidebar under Planning group (Work Items/Use Cases/Documents/Completed); complete_use_case() validates all descendants done, moves MD to documents/completed/
- Backend hardcoded string removal — localhost references in main.js, api.js to be replaced with dynamic config from aicli.yaml; centralizing backend URL configuration across frontend
- UI code optimization and refactoring — removing duplicate/unused code, cleaning hardcoded strings, consolidating initialization methods across work_items.js and use_cases.js

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

**[2026-04-25 10:16]** `ui/`
Q: Still not working !
A: Clean. The fix is:  1. **Deleted** `_attachUcDragListeners()` and its 3 module-level variables — they were a parallel reimplementation that had a subtle bug 2. **Added** `reloadFn = _loadAll` param to `_attachDragListeners()` — all 3 `_loadAll` calls inside are now `reloadFn` 3. **Added** `wi-drop-z

**[2026-04-25 09:58]** `ui/`
Q: Still not working. can you compare to work item and see why it is working on work item and not on use cases ?
A: The implementation now mirrors Work Items exactly:  | | Work Items | Use Cases (now) | |---|---|---| | `dragstart`/`dragend` | Per-card, direct | Per-card, direct | | State variables | Module-level `_dragItemId`, `_dragOverItemId` | Module-level `_ucDragItemId`, `_ucDragOverId` | | Drop detection | 

**[2026-04-25 09:49]** `ui/`
Q: Not working yet. dan drag items, but it is not linked (tried any items in use case section)
A: Now open the browser DevTools console (F12), go to Use Cases tab, try dragging one item onto another, then paste what the console shows. Specifically I need to see:  1. `[UC-drag] attached to N zones` — how many zones were found 2. `[UC-drag] dragstart` — whether `_ucDragId` is set 3. `[UC-drag] dro

**[2026-04-25 09:38]** `ui/`
Q: This is still not working. I can move item , but it is not linked anywhere
A: The real bug: `dragleave` fires with `relatedTarget = null` right before `drop` completes — a known browser behaviour when the mouse releases. This cleared `_ucHoverTarget`, so by the time `drop` ran, the target was already null and `_showLinkMergePopover` was never called.  The fix: the `drop` hand

**[2026-04-25 09:34]** `ui/`
Q: It is still not working on use cases. how come it works well on work item and you can not fix that in use case ?
A: Good. The root cause was two things that Work Items got right but UC didn't:  1. **`e.preventDefault()` must be unconditional** — in the previous UC version it was inside an `if (card)` guard, so if `e.target.closest()` returned null for any reason (hovering over a gap, a section header, or any elem

**[2026-04-25 09:21]** `ui/`
Q: Can undo on merge work partialy (expose the old item, but the new one will be with the latest summery ) ? Also merge/ set parent-child still not workng in Use cases

**[2026-04-24 23:45]** `ui/`
Q: how is the undo works, if item is linked - there is db update, how doas undo work?
A: It works by **storing a reverse API call as a closure** before anything is applied:  1. **Before** the link happens, `originalParentId = draggedItem?.wi_parent_id ?? null` is captured (line ~1095).  2. **After** the `PATCH /wi/{project}/{id}` sets `wi_parent_id = targetId`, `_setUndoAction` stores a

**[2026-04-24 23:24]** `ui/`
Q: it seems that the drag and drop working in work item, but is it not working in use cases, when I am dragging an item (the same type) nothing happend . I dont see the option to merge or parent-child. c
A: Done. Here's what was completed:  **1. Undo button wired** (`_setupEvents` at line 457): The `#wi-undo-btn` click handler is now active in both the Work Items and Use Cases views (both call `_setupEvents`). On click it calls `undoFn()`, clears the undo state, shows a toast, then reloads.  **2. Undo 

**[2026-04-24 23:08]** `ui/`
Q: can you go over the UI and optimise that, make sure the code is clean there are no duplicate or unused code. make sure code and merthod are optimised.  I do see some hard coded string like localhost (

**[2026-04-24 22:55]** `ui/`
Q: It looks like the drag and drop with parent-child work for work items but it is not working for the use cases . Also is it possible to add undo button in both section (work items and use cases) so use
A: All done. Here's a summary of what was implemented:  ---  ### Fixes & Features  **1. UC tab drag-and-drop (fixed)** - Rewrote `_attachUcDragListeners` to use **event delegation** on the parent `listEl` container - `dragover`/`drop` handlers now use `e.target.closest('.wi-uc-children .wi-card[data-it
