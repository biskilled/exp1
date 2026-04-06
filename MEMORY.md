# Project Memory — aicli
_Generated: 2026-04-06 10:22 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend, PostgreSQL semantic storage (pgvector), and an Electron desktop UI for collaborative AI-driven development workflows. It synthesizes project context into structured memory (events, facts, work items, features) using Claude Haiku dual-layer analysis, supports multi-LLM providers, and executes async DAG workflows with visual approval panels. Currently stabilizing database upsert logic, commit synchronization, and memory synthesis triggers while expanding UI usability (copy-to-clipboard, full commit metadata display).

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
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
- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
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
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
- Memory layer trigger consolidation: event-based triggering for all new items (/memory pathway) with differentiated process_item/messages handling
- PostgreSQL batch upsert JSONB with explicit ::jsonb casting for tags field to prevent duplicate row insertion on ON CONFLICT DO UPDATE
- Backend startup race condition handled via retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↩ link) showing only that prompt's commits
- Phase persistence with red ⚠ badge for missing phase; tag suggestions auto-saved via _acceptSuggestedTag with distinct visual marking

## In Progress

- PostgreSQL batch upsert JSONB fix: resolved ON CONFLICT DO UPDATE duplicate row insertion error with explicit ::jsonb casting for tags field
- Commit sync and deduplication: implemented /history/commits/sync endpoint to import 364+ unique commit hashes with proper prompt linkage
- Commits tab full loading: fixed commit message truncation ensuring database population supports complete metadata display in UI
- History display dual-hook architecture: verified hook-response and session-summary hooks properly save prompts and LLM responses to mem_mrr_prompts
- Memory items and project_facts population: enable event-based triggering with differentiated process_item/messages handling for core memory functionality
- Copy-to-clipboard functionality: implement text selection and copying capability in history UI for improved usability

## AI Synthesis

**[2026-03-14]** `PostgreSQL` — Fixed ON CONFLICT DO UPDATE duplicate row insertion error by adding explicit ::jsonb casting for tags field in batch upsert queries.
**[2026-03-14]** `Commit Sync` — Implemented /history/commits/sync endpoint to import 364+ unique commit hashes with proper prompt linkage and deduplication logic.
**[2026-03-14]** `UI/History` — Fixed commit message truncation in commits tab to ensure complete metadata displays; verified dual-hook architecture saves prompts and responses to mem_mrr_prompts.
**[2026-03-14]** `Memory Layer` — Enabled event-based triggering for memory items and project_facts population with differentiated process_item/messages handling.
**[2026-03-14]** `Startup Robustness` — Resolved backend race condition on first load with retry_logic_handles_empty_project_list and _ensure_shared_schema consolidation.
**[2026-03-14]** `Phase & Tags` — Implemented red ⚠ badge for missing phase; auto-saved tag suggestions via _acceptSuggestedTag with distinct visual marking.
**[2026-03-14]** `Data Persistence` — Standardized load_once_on_access, update_on_save pattern; session ordering by created_at to prevent reordering on tag/phase updates.
**[2026-03-14]** `Commit Display` — Added commit-per-prompt inline display with accent left-border and hash ↩ links showing only that prompt's commits.
**[2026-03-14]** `Chunking Strategy` — Smart chunking per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs) with manual relations via CLI/admin UI.
**[2026-03-14]** `Deployment & CLI` — Unified deployment across Railway cloud (Dockerfile + railway.toml), Electron-builder desktop, and local bash/npm startup scripts.