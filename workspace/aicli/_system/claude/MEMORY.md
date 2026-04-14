# Project Memory — aicli
_Generated: 2026-04-14 22:51 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that captures development sessions, synthesizes them into structured work items and project facts, and enables multi-agent pipelines for code generation and planning. It combines a Python FastAPI backend with PostgreSQL/pgvector semantic storage, a Python 3.12 CLI, and an Electron desktop UI, supporting LLM providers (Claude/OpenAI/DeepSeek/Gemini/Grok) for memory synthesis and workflow automation. Currently at v2.2.0, the project is refactoring its agent pipeline to support database-driven role definitions and auto-commit workflows while improving tag suggestions and approval panel state management.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel; Dashboard tab for pipeline visibility
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac/Windows/Linux)
- **database_schema**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features (unified); mem_mrr_commits_code, mem_mrr_tags (mirroring); per-project tables; shared users/usage_logs/transactions/session_tags/entity_categories tables
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extensions + m001-m041 migration framework
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+ with pgvector extensions
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
- **schema_migrations**: m001-m041 framework with db_schema.sql as source of truth
- **llm_provider_location**: agents/providers/

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags, facts, work items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; login_as_first_level_hierarchy pattern for hierarchical Clients → Users
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules in agents/providers/ with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with exec_llm boolean flag
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; system metadata stripped (llm, event, chunk_type, commit_hash retained only phase/feature/bug/source tags)
- Feature snapshot layer (mem_ai_feature_snapshot) merges user requirements with work items: summaries, use cases, delivery types (code/document/architecture/ppt)
- Tag system: retained only user-facing tags (phase, feature, bug, source); planner_tags table with name, status, description, creator, requirements, action_items, deliveries (JSONB)
- Database schema as single source of truth (db_schema.sql) with migration framework (m001-m041); column ordering: client_id → project_id → created_at/processed_at/embedding at end
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)

## In Progress

- Work item pipeline refactor (2026-04-14) — Agent roles loaded from DB (mng_agent_roles) with fallback prompts; 4-stage pipeline (PM→Architect→Developer→Reviewer) now uses _load_role() and _FALLBACK_PROMPTS; auto_commit flag added to role schema
- Agent roles enhancement (2026-04-14) — auto_commit boolean column added to mng_agent_roles; RoleCreate/RoleUpdate models updated; improves pipeline automation workflow
- Tag suggestion and approval flow (2026-04-13) — ai_tag_suggestion column with approve/remove buttons; simplified chip markup; missing suggested_new tags issue under investigation
- Pipeline execution UI rendering (2026-03-20) — Old MD version displayed on approval panel instead of current output/progress logs; requires chat panel state management investigation
- Project startup race condition fix (2026-03-20) — Sequential await api.listProjects() prevents empty home screen; edge case handling implemented
- Memory mirror tables refactor (2026-04-14) — mem_mrr_prompts columns reordered (project_id/event_id after client_id); m037-m039 migrations applied for schema cleanup

## AI Synthesis

**[2026-04-14]** `work_item_pipeline` — Refactored 4-stage agent pipeline (PM→Architect→Developer→Reviewer) to load agent roles from mng_agent_roles DB table with fallback prompts via _load_role() utility; auto_commit boolean flag added to enable automated commit triggering in role schema.

**[2026-04-14]** `agent_roles_schema` — Enhanced mng_agent_roles table with auto_commit column; updated RoleCreate/RoleUpdate Pydantic models to support automation flags; enables pipeline to auto-commit work items without manual approval when configured.

**[2026-04-14]** `schema_consolidation` — Completed memory mirror table refactor: reordered mem_mrr_prompts columns (project_id/event_id moved after client_id for consistency); applied m037-m039 migrations to enforce column ordering: client_id → project_id → created_at/processed_at → embedding.

**[2026-04-13]** `tag_suggestion_ui` — Implemented ai_tag_suggestion column with approve/remove buttons on memory items; simplified chip markup for tag display; identified missing suggested_new tags in approval flow requiring chat panel state investigation.

**[2026-03-20]** `pipeline_ui_rendering` — Discovered approval panel displays old MD version instead of current output/progress logs; requires chat panel state management refactor to show live pipeline execution status and latest LLM outputs.

**[2026-03-20]** `project_startup_fix` — Fixed race condition on home screen by implementing sequential await for api.listProjects(); prevents empty project list on initial load; edge case handling added for concurrent project initialization requests.