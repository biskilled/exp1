# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-19 01:57 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-14 | Version 2.2.0_

---

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows) + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking), agent_roles, system_roles
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK nesting), agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables with indexed columns (phase/feature/session_id)
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server for local dev
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free; login as first-level hierarchy
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth with tree UI in Planner; tags synced across Chat/History/Commits
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Load-once-on-access pattern eliminates redundant SQL; tag cache synced across Chat/History/Commits on save
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- Port binding safety: freePort() kills stale uvicorn processes; Electron cleanup via process.exit()
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase
- System roles composable into agent roles (e.g., 'coding' role with clean code/comments/OOP principles)

## Recent Context (last 5 changes)

- [2026-03-18] I would  to make sure memory is optimised the way we discussed previously :  As I do store propts, llm repsonse, tags an
- [2026-03-18] I would like to start to work on the Roles. by adding system roles that can be added into any Agent roles. for example s
- [2026-03-19] I cannot see any system_roles under system_roles. also the + to add system_roles or agent_roel is not working. also I am
- [2026-03-19] When app is stsrting - I still cannot see all project in prject page (only after I open the project). also it seems tha 
- [2026-03-19] I would like to extend the workflow: I woudld like to add tab "Documents" after Code that will be mapped to docusmnet fo