# Project Memory — aicli
_Generated: 2026-04-25 09:35 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python backend (FastAPI + PostgreSQL + pgvector) with an Electron desktop UI (Vanilla JS + xterm + Monaco) for AI-assisted project management. It implements a 4-layer memory architecture (ephemeral → raw capture → LLM digests → structured work items) with dual semantic/relational storage, async DAG workflow orchestration, and intelligent chunking. Current focus is UI polish: fixing drag-and-drop parent-child linking in Use Cases, implementing persistent undo buttons, aligning MD file generation with use case structure (recursive CTE for all descendants), and completing the Completed section with auto-move to documents folder.

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
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts/feature_snapshot
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
- Database schema as single source of truth (db_schema.sql) with m001-m076 migration framework; INT PKs canonical order (id → client_id → project_id → user_id → created_at → updated_at → embedding)
- Work Items vs Use Cases separation: Work Items tab shows pending AI-classified items; Use Cases tab displays approved items with due dates, completion validation, and auto-markdown generation
- Use Case lifecycle: due dates (calendar MM/DD/YY or day offset), completion validation (all descendants validated), completed_at timestamp, MD file auto-move to documents/completed/ on completion
- Drag-and-drop parent-child linking and merge functionality for work items with type validation (same-type only) and undo support; merged_into self-FK tracks item relationships
- Session history UI with source badges (CLI/UI/Workflow), phase chips, session ID (last 5 chars), timestamp YY/MM/DD-HH:MM, and per-prompt tag management
- Text selection enabled across UI for clipboard copy-paste; undo button in Work Items and Use Cases toolbars as persistent button (not popup); undo stores reverse API call closure

## In Progress

- UI drag-and-drop parent-child/merge in Use Cases fixed via unconditional e.preventDefault() and event delegation targeting any child element; type validation ensures same-type items only link
- Undo button implementation as persistent toolbar button (not popup) in both Work Items and Use Cases; stores reverse API call closure capturing original parent_id before link
- MD file generation aligned with use case structure: recursive CTE fetches all descendants, separate sections for Requirements/Completed/Open Items, no HTML comments, plain text timestamps
- Completed section added to left sidebar under Planning group (Work Items/Use Cases/Documents/Completed); complete_use_case() validates all descendants done, moves MD to documents/completed/
- Backend hardcoded string removal — localhost references in main.js, api.js to be replaced with dynamic config from aicli.yaml; centralizing backend URL configuration across frontend
- Template workspace refactor complete — _templates/ reorganized into cli/pipelines/hooks subdirectories with per-provider hooks; aicli/ folder to be synced with template changes

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

**[2026-04-24]** `ui` — Fixed drag-and-drop parent-child/merge in Use Cases tab by switching to event delegation with unconditional e.preventDefault(); type validation ensures only same-type items can link. **[2026-04-24]** `ui` — Undo button moved from disappearing popup to persistent toolbar button in both Work Items and Use Cases; captures reverse PATCH closure with original parent_id before link applied. **[2026-04-24]** `ui` — MD file format cleaned: removed HTML comments, plain text timestamps (created/updated), recursive CTE fetches all descendants, sections properly separated (Requirements → Completed → Open Items) without duplicates. **[2026-04-24]** `ui` — Completed section added to left sidebar under Planning group; complete_use_case() validates all descendants done, sets completed_at timestamp, auto-moves MD to documents/completed/. **[2026-04-24]** `backend` — Migration m074 applied (completed_at TIMESTAMPTZ to mem_work_items); migration m076 adds merged_into self-FK for item merge tracking. **[2026-04-23]** `ui` — Work Items tab now shows all items (pending + approved); Use Cases tab isolated as separate view with approve pending button; classify flow moved to Work Items only. **[2026-04-23]** `ui` — Due dates implemented for use cases: users can set MM/DD/YY or day offset (e.g. +8 days); all child items inherit deadline; re-parent conflict auto-resolves by preventing child due_date ≤ parent due_date. **[2026-04-24]** `ui` — Template workspace refactor: _templates/ reorganized into cli/{claude/hooks, settings, mcp.config}/ + pipelines/ + hooks removed from root; aicli/ folder sync pending. **[2026-04-15]** `backend` — Migration m051-m052: user_id changed from UUID string to INT SERIAL PK; all mirror tables rebuilt with canonical column order (id → client_id → project_id → user_id → created_at → updated_at). **[2026-04-15]** `ui` — Chat history visibility: session ID badge (last 5 chars) added to session headers; phase chips extracted; full session ID shown in top banner; localStorage cache no longer renders stale session on load.