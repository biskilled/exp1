# Project Memory — aicli
_Generated: 2026-04-17 22:03 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend with Electron desktop UI, PostgreSQL+pgvector storage, and multi-LLM provider support (Claude, OpenAI, DeepSeek, Gemini, Grok). It implements a 4-layer memory architecture (ephemeral → raw capture → LLM digests → work items/facts) with async DAG workflows, semantic search, and intelligent code chunking. Current development focuses on database schema stabilization (m052 migration complete), session management UX fixes, and feature snapshot consolidation for requirement tracking.

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
- Database schema as single source of truth (db_schema.sql) with m001-m052 migration framework; unified mem_tags_relations table for flexible tag-to-entity relationships
- Feature snapshot layer (mem_ai_feature_snapshot): merges user requirements with work items; planner_tags unified with inline snapshot fields
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Column standardization: INT primary keys (client_id, project_id, user_id) in order; created_at/updated_at/embedding always at end of all tables
- Fire-and-forget async DB initialization on startup: asyncio.get_event_loop().run_in_executor() allows server to start immediately while DB connects in background

## In Progress

- Chat UI session display: fixed stale session ID loading on startup by clearing module-level _sessionId and reading last_session_id synchronously from runtime state; session headers now show CLI/UI/Workflow badge, phase chip, session ID (last 5 chars), and timestamp YY/MM/DD-HH:MM
- Session history persistence: confirmed hook-log endpoint working after m050 migration; 531 total prompts now loading correctly (389 DB + ~142 merged from JSONL); newest sessions (April) load first without stale session flashing
- Database schema reorganization: m052 migration completed — all 18 tables reordered to: id → client_id → project_id → user_id → [columns] → created_at → updated_at → embedding; committed_at removed from mem_mrr_commits
- User ID type conversion: m051-m052 migrated mng_users.id from UUID to SERIAL INT; updated_at added to all mirror tables and core event tables; user_id INT added to all tables after project_id
- Event table cleanup: dropped importance column (m037); stripped system metadata tags from 1441 events retaining only phase/feature/bug/source user tags; prompts table column order standardized
- Feature snapshot layer: mem_ai_feature_snapshot table created to merge user requirements with work items; planner_tags streamlined by removing summary/design/embedding/extra columns; deliverables JSONB added for tracking code/documents/designs

## AI Synthesis

**2026-04-17** `chat-ui` — Fixed stale session ID loading by clearing module-level state and reading last_session_id synchronously; session headers now display CLI/UI/Workflow badge, phase chip, truncated session ID, and YY/MM/DD-HH:MM timestamp.

**2026-04-17** `database` — Completed m051-m052 migrations: converted mng_users.id from UUID to SERIAL INT, standardized all 18 tables to id → client_id → project_id → user_id → [columns] → created_at → updated_at → embedding column order.

**2026-04-16** `session-history` — Verified hook-log endpoint functionality post-m050; 531 total prompts now loading correctly (389 from DB + ~142 merged from JSONL), newest sessions (April) load first without stale flashing.

**2026-04-15** `event-cleanup` — Dropped importance column from event table (m037); stripped system metadata tags from 1441 events, retaining only user-facing phase/feature/bug/source tags; standardized prompts table column order.

**2026-04-14** `memory-snapshot` — Implemented mem_ai_feature_snapshot table merging user requirements with work items; streamlined planner_tags by removing summary/design/embedding/extra columns; added deliverables JSONB field for tracking code/documents/designs.

**2026-04-10** `schema-consistency` — Established column standardization across all tables: INT primary keys (client_id, project_id, user_id) in fixed order; created_at/updated_at/embedding always at table end; committed_at removed from mem_mrr_commits for consistency.