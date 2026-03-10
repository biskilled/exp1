# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-10 01:12 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-09 | Version 2.1.0_

---

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (with parent_id for nesting); events table includes due_date column
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Anthropic), OpenAI, DeepSeek, Gemini, Grok — all independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server — 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search and entity graph
- Per-project DB tables (commits_{p}, events_{p}, embeddings_{p}) via project_table() + ensure_project_schema()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing without login
- All LLM providers independent; server holds API keys; client sends NO keys
- Config-driven pricing via provider_costs.json as single source of truth
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- 5-layer memory: immediate → working (session JSON) → project (PROJECT.md) → historical (history.jsonl) → global (templates)
- /memory generates per-LLM files + copies to code_dir; Haiku incremental synthesis
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Entity/event model: shared entity_categories/entity_values + per-project events/event_tags/event_links
- Unified tag-based planner: single category→tags hierarchy with unlimited nesting via parent_id FK
- Frontend caching strategy: load all project tags/categories once on project access, update DB only on explicit save

## Recent Context (last 5 changes)

- [2026-03-09] I dont think your update works. lets start from Planer - there is not need to have 4 tabs - Feture, tag, Bugs and Tags. 
- [2026-03-10] I think there is an issue with ui as it is not loading properly (and I do see error whie bind address 127.0.0.1, 8000)
- [2026-03-10] I am shutting down elecrotn and run fresh - but cannot see anythin. also when when I click on project name - i do not se
- [2026-03-10] It looks like there are multiple database calls that make the system realy slow. try to avoid many sql calls and upload 
- [2026-03-10] Can you make sure that sql queries are optimized (loading one time when project is loading, save in any update). also ca