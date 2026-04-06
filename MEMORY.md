# Project Memory — aicli
_Generated: 2026-04-06 01:34 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform built on PostgreSQL 15+ with pgvector semantic search, combining a FastAPI backend, Python 3.12 CLI, and Electron desktop UI. It uses multi-LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) with async DAG workflows, JWT authentication, and Claude Haiku dual-layer memory synthesis to create persistent AI-assisted project memory. The platform is currently in active development focusing on completing memory table population, comprehensive documentation, and feature snapshot unification for production readiness.

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
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
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
- **deployment_local**: bash start_backend.sh + npm run dev

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
- Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
- Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking
- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↩ link) showing only that prompt's commits
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
- Backend startup race condition fixed via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
- Feature snapshot consolidation: rename plannet_tags to feature_snapshot and establish unified linkage to work_items and memory structures

## In Progress

- Memory items and project_facts table population: implement missing update logic to enable proper memory functionality as designed
- Memory architecture documentation: comprehensive aicli_memory.md covering all layers, mirroring mechanism, event triggers, and specific prompts at each step
- LLM model identifier visibility: expose model identifier as visible tag in UI interface for transparency and tracking across sessions
- Feature snapshot unification: merge plannet_tags into properly named feature_snapshot structure with complete work_item relationship mapping
- Work item linking: clarify and implement complete linkage between work_item entities and memory/snapshot layers across database and API
- Memory endpoint variable scoping: verify code_dir variable fix at line 1120 remains stable and document pattern

## AI Synthesis

**[2026-03-14]** Architecture — aicli established as unified AI memory platform with PostgreSQL 15+ backend, pgvector semantic layer (1536-dim text-embedding-3-small), and dual-layer Claude Haiku memory synthesis. **[2026-03-14]** Authentication & Access — JWT-based auth (python-jose + bcrypt) with DEV_MODE toggle and hierarchical Client→User pattern implemented. **[2026-03-14]** UI Framework — Electron desktop shell with Vanilla JS (no framework/bundler), xterm.js terminal, Monaco editor, and Cytoscape.js DAG visualization using Vite dev server. **[2026-03-14]** Workflow Engine — Async DAG executor via asyncio.gather with loop-back, max_iterations cap, and 2-pane approval panel for negotiation. **[2026-03-14]** LLM Providers — Multi-provider adapter system (Claude/OpenAI/DeepSeek/Gemini/Grok) with standardized send(prompt, system)→str contract. **[2026-03-14]** Memory Synthesis — Claude Haiku generates 5 output files with LLM response summarization, auto-tag suggestions, timestamp tracking, and tag deduplication. **[2026-03-14]** Data Model — Unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features) with per-project schema; ordered by created_at to prevent reordering on updates. **[2026-03-14]** Code Chunking — Smart per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs) with manual relation support via CLI. **[2026-03-14]** Deployment — Railway cloud (Dockerfile + railway.toml), Electron-builder desktop (Mac/Windows/Linux), local bash+npm development. **[2026-03-14]** Current Work — Memory table population, architecture documentation (aicli_memory.md), LLM model visibility tags, and feature_snapshot unification from plannet_tags.