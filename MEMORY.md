# Project Memory — aicli
_Generated: 2026-03-14 19:20 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a unified AI memory platform for developers that captures all prompts, responses, and project context across multiple AI tools (Claude CLI, Cursor, ChatGPT, etc.) into a single searchable history with semantic search via PostgreSQL + pgvector. It provides an Electron desktop app with a vanilla JS frontend (no build step), nested tag/category organization, session-to-commit linking, workflow graph automation, and always-on memory synthesis via Claude Haiku. Currently at v2.2.0 (2026-03-14) with full commit-to-prompt traceability, zero-DB-call tag caching, history rotation, and MCP server integration for external agent access.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl with rotation support), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id for unlimited nesting, due_date tracking)
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
- Commit-to-prompt linking via source_id (timestamp from history.jsonl) stored in commit_log.jsonl; bidirectional mapping via POST /entities/events/tag-by-source-id
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Session tags persist via GET /entities/session-tags endpoint; tag cache loaded once on history tab open
- AI suggestions as dedicated amber banner with /memory synthesis; always-on (DB best-effort), appears between tag bar and messages
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata; Claude Haiku for memory synthesis
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js for graph visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- History rotation on /memory call: configurable max_rows (default 500), creates history_YYMMDDHHSS archive, original becomes history.jsonl

## In Progress

- Commit-to-prompt-to-session linking fully matured — source_id timestamp from history.jsonl maps bidirectionally; POST /entities/events/tag-by-source-id creates event-value links; multiple commits per session each tagged to originating prompt (2026-03-14)
- Tag cache persistence fully implemented — all categories/values loaded once on history tab open via Promise.all; color preservation on save prevents DB thrashing; zero DB calls during tag picker operations (2026-03-14)
- History rotation and tag caching on history tab — tag cache loads once when history tab opens; color fidelity preserved on save; history.jsonl rotates to history_YYMMDDHHSS when /memory processes (2026-03-14)
- CLAUDE.md memory layer alignment complete — all recent features (nested tags, commit linking, session persistence, tag cache, graph workflows) captured; PROJECT.md v2.2.0 aligned to current state (2026-03-14)
- Session phase labeling and AI suggestions banner stable — 'Phase:' label in tag bar; amber banner distinguishes AI suggestions; suggestions populate from /memory synthesis without DB requirement (2026-03-10–2026-03-14)
- Port stability and Electron restart workflow resolved — freePort() kills stale uvicorn via lsof; Electron before-quit cleanup via process.exit() eliminates bind address conflicts (2026-03-10)

## Active Features / Bugs

- **[feature]** auth `(6 events)`
- **[feature]** tagging `(0 events)`
- **[feature]** dropbox `(0 events)`
- **[feature]** UI `(0 events)`
- **[feature]** workflow-runner `(0 events)`
- **[feature]** test-picker-feature `(0 events)`
- **[feature]** mcp `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[feature]** shared-memory `(0 events)`
- **[phase]** discovery `(1 events)`
- **[phase]** prod `(0 events)`
- **[phase]** development `(0 events)`

**[2026-03-14]** `claude_cli` — Commit-to-prompt linking finalized via source_id (timestamp from history.jsonl); POST /entities/events/tag-by-source-id creates bidirectional event-value links so each commit in a session maps back to its originating prompt. **[2026-03-14]** `claude_cli` — Tag cache optimization: all categories/values loaded once on history tab open via Promise.all (4 parallel requests); color fidelity preserved on save; zero DB calls during tag picker operations verified. **[2026-03-14]** `claude_cli` — History rotation implemented: _rotate_history() triggered on every /memory call; configurable max_rows (default 500); creates history_YYMMDDHHSS archive and resets history.jsonl to new entries only. **[2026-03-14]** `claude_cli` — CLAUDE.md memory layer alignment complete; PROJECT.md v2.2.0 updated with all new features (nested tags, commit linking, session persistence, tag cache, workflow graphs); all Goals marked ✓ Implemented. **[2026-03-10–2026-03-14]** `claude_cli` — AI suggestions banner stable: dedicated amber banner between tag bar and messages; suggestions sourced from /memory synthesis without DB dependency; 'Phase:' label in tag bar clarifies session phase selection. **[2026-03-10]** `claude_cli` — Port binding resolved: freePort() kills stale uvicorn via lsof before restart; Electron process.exit() on before-quit eliminates bind address conflicts; clean restart workflow verified.