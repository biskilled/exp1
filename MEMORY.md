# Project Memory — aicli
_Generated: 2026-04-17 22:12 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that solves context loss across AI coding tools by maintaining persistent project memory across sessions. It combines a FastAPI backend with PostgreSQL+pgvector, an Electron desktop UI, and a Python CLI, implementing a 4-layer memory architecture (ephemeral → raw capture → LLM digests → work items) with semantic search, event tracking, and feature planning capabilities. Current state: database schema standardized to INT primary keys, session history UI fully functional with 531 prompts loading correctly, and feature snapshot layer ready to merge user requirements with extracted work items.

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
- **database_schema**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features (unified); mem_mrr_commits_code, mem_mrr_tags (mirroring); per-project tables; shared users/usage_logs/transactions/session_tags/entity_categories tables
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector + m001-m052 migration framework
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
- **embeddings**: text-embedding-3-small (1536-dim vectors)
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **schema_migrations**: m001-m050 framework with db_schema.sql as source of truth
- **llm_provider_location**: agents/providers/
- **database_migrations**: m001-m052 framework with db_schema.sql as source of truth
- **schema_core**: mem_tags_relations (unified), planner_tags (with inline snapshot fields), mem_ai_events, mem_mrr_prompts/commits

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; .ai/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags, facts, work items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; login_as_first_level_hierarchy pattern for hierarchical Clients → Users
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules in agents/providers/ with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with exec_llm boolean flag
- Database schema as single source of truth (db_schema.sql) with m001-m052 migration framework; all tables now use INT PKs (client_id → project_id → user_id)
- Feature snapshot layer (mem_ai_feature_snapshot): merges user requirements with work items; planner_tags unified with inline snapshot fields and deliverables JSONB
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Column standardization: INT primary keys in order (id → client_id → project_id → user_id); created_at/updated_at/embedding always at table end
- Fire-and-forget async DB initialization on startup: asyncio.get_event_loop().run_in_executor() allows server to start immediately while DB connects in background

## In Progress

- Session history UI persistence: Chat tab now shows sessions with source badge (CLI/UI/Workflow), phase chip, session ID (last 5 chars), and timestamp YY/MM/DD-HH:MM; fixed stale session loading by clearing module-level variables and reading last_session_id synchronously from runtime state
- Database schema consolidation m051-m052: migrated mng_users.id from UUID to SERIAL INT; reordered all 18 tables to canonical form (id → client_id → project_id → user_id → [...] → created_at → updated_at → embedding); removed committed_at from mem_mrr_commits
- Event table cleanup: dropped importance column from mem_ai_events; stripped system metadata tags from 1441 events retaining only phase/feature/bug/source user tags; mem_mrr_prompts column reordering complete
- Work items linking verification: confirmed all recent work items (#20436-#20443) are commit-sourced with no associated CLI sessions; fixed join logic for commit-sourced items via mem_ai_events.source_id
- Feature snapshot layer: created mem_ai_feature_snapshot table to merge user requirements with work items; added deliverables JSONB to planner_tags for tracking code/documents/designs; streamlined planner_tags by removing summary/design/embedding columns
- Chat UI session display: added session ID badges, full session ID banners with copy functionality, and tag management per prompt; verified hook-log endpoint working correctly after m050 with 531 total prompts loading properly

## AI Synthesis

**[2026-04-15]** `claude_cli` — Fixed hook-log endpoint (m050 migration) to properly persist all prompts to DB; chat UI now displays 531 total prompts (389 DB + ~142 merged from JSONL) with newest sessions (April) loading first. **[2026-04-15]** `claude_cli` — Implemented comprehensive session history UI: added source badges (CLI/UI/Workflow), phase chips, session IDs (last 5 chars), and timestamps (YY/MM/DD-HH:MM) to both chat tab left sidebar and session headers. **[2026-04-15]** `claude_cli` — Fixed stale session ID loading on startup by clearing module-level _sessionId variable and synchronously reading last_session_id from runtime state before any DOM rendering. **[2026-04-15]** `claude_cli` — Completed database schema consolidation (m051-m052): migrated mng_users.id from UUID to SERIAL INT; standardized all 18 tables to canonical column order (id → client_id → project_id → user_id → [...] → created_at → updated_at → embedding). **[2026-04-13]** `claude_cli` — Cleaned up event table by dropping importance column and stripping system metadata tags from 1441 events, retaining only phase/feature/bug/source user tags for meaningful work item extraction. **[2026-04-12]** `claude_cli` — Created mem_ai_feature_snapshot table to merge user requirements with work items; added deliverables JSONB to planner_tags for tracking code/documents/designs; streamlined planner_tags schema by removing unused summary/design/embedding columns.