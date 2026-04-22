# Project Memory — aicli
_Generated: 2026-04-22 22:49 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform for software development that maintains project context across multiple AI tools and sessions. It consists of a Python backend (FastAPI + PostgreSQL with pgvector), a Python CLI, and an Electron desktop UI, with an async DAG workflow engine for pipeline execution. The system currently focuses on completing database schema standardization (m052 migration), fixing session UI persistence in the Chat/History tabs, and validating that all 531 prompts load correctly with proper metadata attribution.

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
- Column standardization: INT primary keys in canonical order; created_at/updated_at at table end; embedding as final column
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Session history UI persistence: Chat/History tabs display sessions with source badge, phase chip, session ID (last 5 chars), and timestamp YY/MM/DD-HH:MM

## In Progress

- Database schema finalization (m051-m052): user_id migrated to SERIAL INT across all 18 tables; canonical column ordering enforced; updated_at added to all mirror tables; committed_at removed from commits table
- Session UI improvements: Chat and History tabs now show session metadata (source badge, phase chip, last 5 char session ID); stale session loading fixed with last_session_id from runtime state
- Hook-log endpoint verified: all 531 prompts (389 DB + ~142 JSONL merged) loading correctly with proper descending sort order; session attribution and timestamp display functional
- Chat tab session persistence: current session highlighted on load using last_session_id; localStorage cache prevents stale session display; full session ID shown in sticky banner with copy button
- Event table cleanup completed: importance column dropped; system metadata tags stripped from 1441 events; only phase/feature/bug/source user tags retained
- Dashboard and pipeline UI added: new Dashboard tab for visibility; Cytoscape.js DAG visualization with 2-pane approval panel; pipelines executable from planner/docs/chat tabs

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

- **MCP Configuration** `[open]` — Set up Model Context Protocol (MCP) configurations for multiple LLM providers and IDEs (Claude Code,

## AI Synthesis

**[2026-04-15]** `database` — Completed m051-m052 migration refactor: user_id changed from UUID to SERIAL INT, all 18 tables reordered to canonical form (id→client_id→project_id→user_id), created_at/updated_at standardized at table end, committed_at removed from commits table to avoid duplication with created_at.

**[2026-04-15]** `ui` — Fixed stale session loading on Chat tab startup: last_session_id now read synchronously from runtime state before any network calls; localStorage cache renders with correct session highlighted immediately; full session ID shown in sticky banner with copy button.

**[2026-04-15]** `backend` — Verified hook-log endpoint functioning correctly after m050 fix: all 531 prompts (389 from DB + ~142 merged from JSONL) loading with proper descending sort; session attribution and timestamp display working.

**[2026-04-15]** `database` — Cleaned mem_ai_events table: dropped importance column (moved to work_items only), stripped 1441 system metadata tags (llm, event, chunk_type, commit metadata) retaining only phase/feature/bug/source user tags.

**[2026-04-12]** `database` — Created mem_ai_feature_snapshot table merging user requirements with work items: stores summary, use cases (each with type and delivery type), acceptance criteria, action items, and deliverables (code, document, architecture design, PPT).

**[2026-04-12]** `ui` — Added Dashboard tab with Cytoscape.js DAG visualization and 2-pane approval panel for pipeline execution; pipelines now runnable from planner tags, docs (feature-based), or chat tabs with approval workflow.