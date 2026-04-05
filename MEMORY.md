# Project Memory — aicli
_Generated: 2026-04-05 18:10 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python 3.12 CLI + FastAPI backend + Electron desktop UI for collaborative AI-assisted development workflows. It uses PostgreSQL 15+ with pgvector for semantic search, multiple LLM providers (Claude/OpenAI/DeepSeek/Gemini/Grok), async DAG workflow execution, and unified database tables (mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features) to track sessions, tags, commits, and memory synthesis across projects. Current focus: refining session/tag/commit relationships with chronological ordering, phase persistence, and unified UI consolidation.

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
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables replace per-project fragmentation
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization (not full output) + auto-tag suggestions
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; tags in mem_ai_tags_relations with row ID linking and suggested/user-created distinction
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Session ordering by created_at (not updated_at) to prevent tag/phase updates from reordering session list
- Unified UI: Planner tab consolidates all tag management (single tags view with category/status/properties); Chat (+) for tag selection with category filtering
- Tag suggestions marked distinctly (separate color/mark) and auto-saved via _acceptSuggestedTag; phase persistence with red ⚠ badge for missing phase
- Commit-per-prompt inline display: commits at bottom of each prompt entry (accent left-border, hash ↗ link) showing only that prompt's commits
- Backend: FastAPI + uvicorn; routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for access, agents/ for tools and MCP
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev

## In Progress

- Session ordering refactored: sessions now order by created_at instead of updated_at to maintain chronological list and prevent phase/tag updates from reordering
- Phase persistence enhanced: loads from database on init, PATCH /chat/sessions/{id}/tags saves phase, red ⚠ badge for missing phase across UI/CLI/workflow
- Commit-per-prompt inline display completed: replaced session-level commit strip with inline commits at bottom of each prompt entry (accent left-border, hash ↗ link)
- Tag deduplication and cross-view sync: 149 total tags (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously
- AI suggestion auto-save with tag management: suggestions create tags in proper category via _acceptSuggestedTag; marked distinctly with separate color; appear immediately in Planner
- Planner tab unified redesign: consolidated into single tags view with category, active/inactive status, short description, created date; removed Feature/Bugs/Tags split

## AI Synthesis

**[2026-03-14]** `core/ui` — Session ordering refactored to use created_at instead of updated_at, preventing tag/phase updates from reordering the session list chronologically. **[2026-03-14]** `data/persistence` — Phase persistence enhanced with database load-on-init and PATCH endpoint; red ⚠ badge displays across UI/CLI/workflow when phase is missing. **[2026-03-14]** `frontend/chat` — Commit-per-prompt inline display replaced session-level commit strip; commits now appear at bottom of each prompt entry with accent left-border and hash↗ link. **[2026-03-14]** `data/tags` — Tag deduplication completed: 149 total tags with zero duplicates; removal via ✕ buttons now propagates atomically across Chat/History/Commits views. **[2026-03-14]** `agents/suggestions` — AI suggestion auto-save implemented via _acceptSuggestedTag; suggestions create properly-categorized tags, marked with distinct color, appearing immediately in Planner. **[2026-03-14]** `frontend/planner` — Planner tab unified into single consolidated tags view with category, active/inactive status, short description, and created date; removed fragmented Feature/Bugs/Tags split.