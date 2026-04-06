# Project Memory — aicli
_Generated: 2026-04-06 00:58 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python 3.12 CLI, FastAPI backend, and Electron desktop UI to enable multi-LLM collaboration with semantic memory synthesis. It uses PostgreSQL 15+ with pgvector for unified event/tag/fact storage, Claude Haiku dual-layer synthesis for intelligent summarization, and async DAG workflows with visual approval panels. Currently stabilizing memory table population, implementing LLM model visibility in the UI, and unifying feature snapshots with work items across the architecture.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization + auto-tag suggestions
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local bash/npm
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + ui/npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
- Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
- Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↪ link) showing only that prompt's commits
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
- Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures

## In Progress

- Memory architecture documentation: comprehensive aicli_memory.md covering all layers, mirroring mechanism, event triggers, and specific prompts at each step
- LLM model identifier visibility: expose model identifier as visible tag in UI interface for transparency and tracking across sessions
- Feature snapshot unification: merge plannet_tags into properly named feature_snapshot structure with complete work_item relationship mapping
- Work item linking: clarify and implement complete linkage between work_item entities and memory/snapshot layers across database and API
- Memory endpoint variable scoping: verify code_dir variable fix at line 1120 remains stable and document pattern
- Memory items and project_facts table population: implement missing update logic to enable proper memory functionality as designed

## AI Synthesis

**2026-03-14** `architecture` — Established unified mem_ai_* table schema (events, tags_relations, project_facts, work_items, features) consolidating all memory data into PostgreSQL with pgvector semantic search at 1536 dimensions. **2026-03-14** `memory_synthesis` — Implemented Claude Haiku dual-layer memory synthesis pipeline generating 5 timestamped output files with auto-tag suggestions and LLM response summarization; tag deduplication prevents duplicates across layers. **2026-03-14** `workflow_ui` — Built Cytoscape.js-based async DAG executor visualization with 2-pane approval panel for chat negotiation; supports loop-back logic with max_iterations cap via asyncio.gather parallelization. **2026-03-14** `authentication` — Finalized JWT (python-jose + bcrypt) authentication with DEV_MODE toggle and hierarchical Clients → Users pattern using login_as_first_level_hierarchy convention. **2026-03-14** `deployment` — Consolidated deployment strategy: Railway cloud (Dockerfile + railway.toml), Electron-builder for desktop (Mac/Windows/Linux), local development via bash start_backend.sh + npm run dev. **2026-03-14** `ui_improvements` — Designed commit-per-prompt inline display with accent left-border and hash links; implemented phase persistence with red ⚠ badge for missing phase and tag suggestion auto-save via _acceptSuggestedTag. **2026-03-14** `data_persistence` — Standardized load_once_on_access, update_on_save pattern; ordered sessions by created_at (not updated_at) to prevent reordering on tag/phase updates. **2026-03-14** `backend_fixes` — Resolved backend startup race condition via retry_logic_handles_empty_project_list_on_first_load; replaced ensure_project_schema with _ensure_shared_schema convention for reliability. **2026-03-14** `feature_consolidation` — Initiated feature snapshot unification renaming plannet_tags to feature_snapshot with complete work_item relationship mapping across memory structures. **2026-03-14** `documentation` — Scoped memory architecture documentation (aicli_memory.md) covering all layers, mirroring mechanism, event triggers, and specific prompts at each synthesis step.