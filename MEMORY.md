# Project Memory — aicli
_Generated: 2026-03-15 18:15 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a shared AI memory platform for developers that unifies history, tagging, and context across multiple AI tools (Claude CLI, Cursor, ChatGPT) via a FastAPI backend, PostgreSQL semantic search, flat-file JSONL storage, and an Electron UI. Current state (v2.2.0): fully functional with commit-to-prompt linking, nested tags, pagination across Chat/History/Commits, tag deduplication, hook noise filtering, and MCP server integration ready for external agent access.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for nested tags)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude, OpenAI, DeepSeek, Gemini, Grok — independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config + loop-back support
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; always-on (DB best-effort)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server — 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage primary (JSONL/JSON with rotation); PostgreSQL + pgvector for semantic search; per-project DB tables via project_table()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server only for local development
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing; 3 roles: admin/paid/free
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Tag cache loaded once per project tab open: zero DB calls during chat/planner; batch updates only on explicit save
- History rotation on /memory call: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Commit-to-prompt linking via source_id timestamp in commit_log.jsonl; bidirectional tagging via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- AI suggestions as dedicated amber banner between tag bar and messages; always-on (DB best-effort), synthesized by Claude Haiku
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- Each prompt has multiple linked commits; each commit tagged inherits session phase + prompt-level tags via source_id linking

## In Progress

- Commit-per-prompt display in Chat tab — each prompt entry shows linked commits inline at bottom with accent left-border; replaced session-level commit strip (2026-03-15)
- Tag deduplication and cross-view synchronization — 149 tags total (0 duplicates); tag removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup (2026-03-15)
- Hook noise filtering fully deployed — filters <task-notification>, <tool-use-id>, <system-> entries; real prompts/LLM responses correctly logged to history.jsonl; pagination now accurate (2026-03-15)
- Tag cache optimization in History tab — all categories/values loaded once on tab open; zero DB calls during tag picker; color persistence on save prevents thrashing (2026-03-14)
- Commit-to-prompt linking verified end-to-end — source_id timestamp stored in commit_log.jsonl; tags per prompt auto-propagate to linked commits via tag-by-source-id endpoint (2026-03-14)

## Active Features / Bugs

- **[feature]** auth `(40 events)`
- **[feature]** workflow-runner `(1 events)`
- **[feature]** billing `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[feature]** tagging `(0 events)`
- **[feature]** mcp `(0 events)`
- **[feature]** test-picker-feature `(0 events)`
- **[feature]** UI `(0 events)`
- **[feature]** dropbox `(0 events)`
- **[feature]** shared-memory `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[phase]** discovery `(1 events)`
- **[phase]** development `(0 events)`
- **[phase]** prod `(0 events)`

**[2026-03-15]** `chat.js` — Commit-per-prompt display: each prompt now shows linked commits inline at bottom with accent left-border styling; replaced old session-level commit strip for clearer prompt↔commit relationship.
**[2026-03-15]** `entities.js`, `history.js`, `chat.js` — Tag deduplication verified: 149 unique tags, 0 duplicates; ✕ button removes tags simultaneously across Chat/History/Commits tabs via DELETE /entities/events/tag-by-source-id.
**[2026-03-15]** `history.js`, `chat.js`, `commits.js` — Pagination added to all three tabs: displays range (e.g., '1–100 / 204') with ◀ ▶ controls; backend unified history loads current + all `history_*.jsonl` archives on startup.
**[2026-03-15]** `auto_commit_push.sh` hook — Noise filtering deployed: filters <task-notification>, <tool-use-id>, <system-> entries at write time; only real prompts/LLM responses logged to history.jsonl; pagination counts now accurate.
**[2026-03-14]** `history.js` — Tag cache optimization: all categories/values loaded once on tab open via Promise.all; zero DB calls during tag picker UI; color persistence on save prevents color thrashing.
**[2026-03-14]** `entities.py` — Commit-to-prompt linking verified: source_id timestamp from history.jsonl stored in commit_log.jsonl; tags added to prompt auto-propagate to all linked commits via tag-by-source-id endpoint.