# Project Memory — aicli
_Generated: 2026-04-24 23:45 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python/FastAPI backend with an Electron desktop UI, enabling collaborative project memory management through semantic embeddings, LLM-driven work item classification, and async DAG-based workflows. The current focus is on use case management lifecycle (due dates, completion validation, MD generation), drag-and-drop parent-child linking with undo support, and UI optimization including hardcoded string removal and config-driven backends.

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
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
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
- **database_migrations**: m001-m074 framework with db_schema.sql as source of truth
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
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts/feature_snapshot
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
- Database schema as single source of truth (db_schema.sql) with m001-m076 migration framework; INT PKs canonical order (id → client_id → project_id → user_id)
- Work Items vs Use Cases separation: Work Items tab shows pending AI-classified items; Use Cases tab displays approved items with due dates, completion validation, and MD generation
- Use Case lifecycle: due dates (calendar MM/DD/YY or day offsets), completion validation (all descendants must finish), completed_at timestamp tracking, markdown file generation with auto-move to documents/completed/
- Drag-and-drop parent-child linking and merge functionality for work items with type validation and undo support; merged_into self-FK tracks item relationships
- Session history UI with source badges (CLI/UI/Workflow), phase chips, session ID (last 5 chars), timestamp YY/MM/DD-HH:MM, and per-prompt tag management
- Text selection enabled across UI for clipboard copy-paste; undo button in Work Items and Use Cases toolbars as persistent button (not popup)

## In Progress

- UI hardcoded string removal — replacing localhost references in main.js, api.js with dynamic config from aicli.yaml; centralizing backend URL configuration
- Drag-and-drop parent-child/merge in Use Cases — event delegation fixed to detect drop targets on any child element; type validation ensures only same-type items link
- Undo button implementation — added to Work Items and Use Cases toolbars; captures reverse API call as closure before link happens; _setUndoAction stores PATCH with original parent_id
- MD file format refinement — removed HTML comment tags; created/updated dates as plain text; item counts computed from recursive CTEs; requirements mapped correctly without duplicates
- Use Case completion flow — complete_use_case() validates all descendants done (recursive CTE), sets completed_at timestamp, auto-moves MD to documents/completed/; reopen_use_case() reverses
- Template workspace refactor — reorganized _templates/ with cli/, pipelines/, and hooks/ subdirectories; removed unused files; simplified structure for new projects

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

**[2026-04-24 23:45]** `ui` — Undo mechanism implemented as persistent button in Work Items and Use Cases toolbars; captures reverse API call as closure before link/merge happens, stores original parent_id to restore on undo click.

**[2026-04-24 23:24]** `ui` — Fixed drag-and-drop parent-child/merge in Use Cases via event delegation; added undo button to toolbar; both Work Items and Use Cases now support type validation (only same-type items can link).

**[2026-04-24 22:55]** `ui` — Template workspace refactor completed; reorganized _templates/ into cli/(claude/, mcp.template.json), pipelines/, hooks/ subdirectories; removed unused files; simplified structure for new projects.

**[2026-04-24 22:30]** `ui` — Merged parent-child linking fully wired; orphan detection fixed by computing allSubItems and excluding re-parented children; use case improvements including due date conflict auto-resolution and type validation for merges.

**[2026-04-24 18:54]** `ui` — MD file format refined; removed all HTML comments (no <!-- tags -->); created/updated dates as plain text; item counts (bugs/features/tasks) computed from recursive CTEs; Requirements section now correctly deduplicated and mapped without nested headers.

**[2026-04-23 09:06]** `ui` — Work Items tab fixed to show all items (not just pending AI*); Use Cases tab now properly displays approved items; hook health restored (0.1h after 8.3h offline); empty state message clarified with prompt/commit counts for Classify action.