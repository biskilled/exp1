# Project Memory — aicli
_Generated: 2026-04-05 22:11 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend with a PostgreSQL+pgvector database, a Python 3.12 CLI, and a vanilla JavaScript Electron desktop UI, enabling multi-user collaboration around AI-assisted code analysis and memory synthesis. The system uses async DAG workflows, Claude Haiku dual-layer memory generation, and unified database tables to track sessions, tags, commits, and project facts across multiple LLM providers. Currently at v2.2.0, the platform features phase-aware session management, intelligent commit-per-prompt display, auto-suggested tags with deduplication, and multi-platform deployment (Railway cloud, Electron desktop, local development).

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
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
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
- Session phase persistence with red ⚠ badge for missing phase; tag suggestions marked distinctly (separate color) and auto-saved via _acceptSuggestedTag
- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↗ link) showing only that prompt's commits
- Backend: FastAPI + uvicorn; routers/ for API endpoints, core/ for infrastructure, data/ (dl_ prefix) for access, agents/ for tools and MCP
- Unified Planner tab: single tags view with category/status/properties (active/inactive, short description, created date); tag management centralized from Chat
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev
- Backend startup race condition fixed: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention

## In Progress

- Session ordering by created_at verified: maintains chronological list and prevents phase/tag updates from reordering sessions
- Phase persistence enhanced: loads from database on init, PATCH /chat/sessions/{id}/tags saves phase, red ⚠ badge for missing phase across UI/CLI/workflow
- Commit-per-prompt inline display deployed: replaced session-level commit strip with inline commits at bottom of each prompt entry (accent left-border, hash ↗ link)
- Tag deduplication and cross-view sync verified: 149 total tags (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously
- AI suggestion auto-save with tag management: suggestions create tags in proper category via _acceptSuggestedTag; marked distinctly with separate color; appear immediately in Planner
- Planner tab unified redesign completed: consolidated into single tags view with category, active/inactive status, short description, created date

## AI Synthesis

**2026-03-14** `architecture` — Established unified database schema consolidating per-project tables into mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features with shared users/usage_logs tables. **2026-03-14** `ui-component` — Deployed commit-per-prompt inline display replacing session-level strip with inline commits at bottom of each prompt entry featuring accent left-border and hash link. **2026-03-14** `data-layer` — Implemented session ordering by created_at to maintain chronological list and prevent unintended reordering from tag/phase updates. **2026-03-14** `memory-synthesis` — Completed Claude Haiku dual-layer synthesis generating 5 output files with LLM response summarization, auto-tag suggestions, and deduplication logic (149 tags, 0 duplicates). **2026-03-14** `phase-management` — Enhanced phase persistence with database load on init, PATCH endpoint for updates, and red ⚠ badge for missing phase across UI/CLI/workflow. **2026-03-14** `tag-suggestions` — Implemented AI suggestion auto-save via _acceptSuggestedTag creating tags in proper category, marked distinctly with separate color, appearing immediately in Planner. **2026-03-14** `ui-redesign` — Unified Planner tab into single tags view with category, active/inactive status, short description, and created date; centralized tag management from Chat. **2026-03-14** `deployment` — Multi-platform deployment configured: Railway cloud (Dockerfile + railway.toml), Electron-builder for desktop (Mac/Windows/Linux), local dev via bash start_backend.sh + npm run dev. **2026-03-14** `backend-infra` — Established FastAPI structure with routers/ for API endpoints, core/ for infrastructure, data/ (dl_ prefix) for database access, agents/ for tools and MCP server. **2026-03-14** `reliability` — Fixed backend startup race condition with retry_logic_handles_empty_project_list_on_first_load and _ensure_shared_schema convention replacing ensure_project_schema.