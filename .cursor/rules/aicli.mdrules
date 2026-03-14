# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-14 13:42 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-14 | Version 2.2.0_

---

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id for nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Anthropic), OpenAI, DeepSeek, Gemini, Grok — independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config + loop-back support
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; always-on (DB best-effort)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server — 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id for unlimited nesting, due_date tracking)

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search; per-project DB tables via project_table()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step; Vite dev server only
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing without login
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Commit-to-prompt linking via source_id (timestamp from history.jsonl) stored in commit_log.jsonl; POST /entities/events/tag-by-source-id maps commits to events
- Session tags persist via GET /entities/session-tags endpoint querying event_tags_{p} joined to events/values/categories
- Phase labeling (renamed from 'Session:') visible in tag bar; 3-dot dropdown menu (⋯) per tag row for edit/archive/restore/delete actions
- AI suggestions as dedicated amber banner with /memory synthesis; always-on (DB best-effort), appears between tag bar and messages
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata; Claude Haiku for memory synthesis

## Recent Context (last 5 changes)

- [2026-03-10] I understand the issue. I am using your claude cli and hooks to store propts and llm response. hooks also managing the c
- [2026-03-13] I am siting with my freid and try to explain him wha is this system is about ? can you explain that shortly ?
- [2026-03-14] I do have some concern how commit/hash are linked to prompts/llm answers. also are tagging is currently works in my syst
- [2026-03-14] I do see the option to add tag in history - can you make sure all tags are loaded only once into mermory (to save db cal
- [2026-03-14] can you run /memory, to make sure all updated. also can you check that system is aligned to CLAUDE.md (memroy layers) pr