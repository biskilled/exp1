# Project Memory — aicli
_Generated: 2026-04-24 21:06 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform for software development that maintains persistent context across multiple AI tools (Claude, ChatGPT, Cursor) through a unified PostgreSQL database, semantic search via pgvector embeddings, and intelligent memory synthesis. Current state: fully functional 4-layer memory architecture with Work Items/Use Cases management, markdown documentation generation, due date tracking with descendant validation, completed use case tracking, and stable session history UI with proper session ID/timestamp visibility and text selection support.

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

## AI Synthesis

**[2026-04-24]** `ui` — Completed Use Case lifecycle system: added `completed_at` timestamp tracking (m074), implemented completion validation (all descendants must finish), auto-move MD files to documents/completed/, and reopen functionality with descendant re-activation.

**[2026-04-24]** `ui` — Use Case markdown generation now uses recursive CTEs to capture all descendants (not just direct children), generates plain-text created/updated dates + item counts (bugs/features/tasks) from DB state, removes HTML comment tags throughout.

**[2026-04-24]** `ui` — MD file generation fix: "✎ MD" button now calls `api.wi.md.refresh()` before navigating to Documents, ensuring file exists on disk; proper path mapping under use_cases/ folder.

**[2026-04-24]** `ui` — UI/UX improvements: added "Use Cases" entry to left sidebar (separate from Work Items); Approve button removed from Use Cases tab (approval-only in Work Items); due date support with calendar or day offset input; re-parent conflict auto-resolution when children exceed parent due date.

**[2026-04-23]** `ui` — Work Items tab now displays ALL use cases (not just pending AI* items); fixed Work Items/Use Cases tab layout positioning to right side of toolbar; set default max UC to 8 in config to enable classify pipeline.

**[2026-04-24]** `ui` — Fixed text selection across entire UI: removed `user-select: none` from body to enable copy-paste in history entries, work item cards, and markdown content; Electron now fully supports clipboard operations.