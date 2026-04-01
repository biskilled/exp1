# Project Memory — aicli
_Generated: 2026-04-01 01:15 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a FastAPI backend with PostgreSQL 15+ (pgvector) semantic storage, an Electron UI with xterm.js/Monaco/Cytoscape.js visualization, and a Python 3.12 CLI. It manages multi-user projects with per-schema isolation, unified event tables, smart memory synthesis (Claude Haiku dual-layer), async DAG workflows, and MCP tool integration. Current focus is validating unified event table consolidation, fixing tag persistence across session switches, and automating memory file generation from project facts.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with per-project schema
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); local: bash start_backend.sh + ui/npm run dev
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ per-project schema + shared auth/usage tables; agent roles initialized
- **node_modules_build**: npm 8+ with webpack/Electron-builder; dev server Vite on localhost
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with webpack/Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features

## Key Decisions

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; per-project schemas with mem_ai_* prefix tables
- Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users
- All LLM providers as independent adapters; Claude Haiku for synthesis; server holds API keys
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md)
- Unified event table mem_ai_events consolidates embeddings and memory events with event_type column
- Tags stored in mem_ai_tags_relations (linked via row id), not in summary_tags array; sourced from MRR
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load
- Manual relations managed via CLI/admin UI: depends_on, relates_to, blocks, implements
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT)
- Memory management pattern: load_once_on_access, update_on_save; triggered by memory endpoint and synthesis layer
- Deployment: Railway (Dockerfile + railway.toml) for cloud; local dev via bash start_backend.sh + ui/npm run dev

## In Progress

- Tag column schema correction: fixed mem_ai_tags_relations table reference in DDL; database migrations applied and persistence validation across session switches
- Memory file generation automation: CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md auto-regenerated from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
- Unified event table validation: confirmed mem_ai_events consolidates pr_embeddings/pr_memory_events; removed event_summary_tags array and deprecated metadata
- Backend startup race condition: AiCli appearing in Recent projects but unselectable on first load; retry logic implemented for empty project list
- Data persistence validation: investigated tags disappearing on session switch; root cause traced to cache invalidation triggering DB re-load
- Schema documentation cleanup: updated project_state.json and rules.md to reflect mem_ai_* table naming and removed deprecated columns

## AI Synthesis

**[2026-03-14]** `schema` — Consolidated mem_ai_events table now unifies embeddings and memory events with event_type discriminator; removed deprecated event_summary_tags array and metadata fields (language, file_path). **[2026-03-14]** `persistence` — Debugged tag disappearance across session switches; root cause identified as cache invalidation forcing DB re-load; implemented load_once_on_access pattern with explicit cache management. **[2026-03-14]** `memory_synthesis` — Automated generation of 5 output files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md) from mem_ai_project_facts and mem_ai_work_items with timestamp tracking for incremental updates. **[2026-03-14]** `startup` — Fixed backend race condition where AiCli appeared in Recent projects but was unselectable on first load; implemented retry logic for empty project list with session state persistence. **[2026-03-14]** `migrations` — Applied DDL corrections to mem_ai_tags_relations table reference; validated database schema consistency and tested persistence across multiple session cycles. **[2026-03-14]** `documentation` — Updated project_state.json and rules.md to reflect mem_ai_* naming convention; removed references to deprecated columns and clarified tag storage in mem_ai_tags_relations vs summary_tags anti-pattern.