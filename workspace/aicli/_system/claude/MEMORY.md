# Project Memory — aicli
_Generated: 2026-03-15 22:44 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that unifies prompts, responses, and project state across multiple AI tools (Claude CLI, Cursor, ChatGPT, etc.) so they all operate with the same context. The current state (v2.2.0) includes a fully functional Electron + FastAPI desktop app with per-session phase tracking, commit linking, nested tagging, semantic search via PostgreSQL+pgvector, and MCP integration for external agents. Recent work focused on fixing phase persistence across chat sessions, adding commit-per-prompt display in the UI, and ensuring tag synchronization across all views.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude, OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables via project_table()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server only for local development
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Tag cache loaded once per project tab open: zero DB calls during chat/planner; batch updates only on explicit save
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Commit-to-prompt linking via source_id timestamp in commit_log.jsonl; bidirectional tagging via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- AI suggestions as dedicated amber banner between tag bar and messages; Claude Haiku synthesis; auto-save to session
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- Each prompt has multiple linked commits; each commit inherits session phase + prompt-level tags via source_id linking

## In Progress

- Phase synchronization across Chat tabs — fixed: phase now updates current session (not forcing new one); PATCH /chat/sessions/{id}/tags endpoint writes phase to session JSON; phase persists on session switch and loads correctly on app init for both UI and CLI sessions (2026-03-15)
- Commit-per-prompt display in Chat tab — replaced session-level commit strip with inline commits at bottom of each prompt entry (accent left-border, hash ↗ link); shows linked commits only for that prompt (2026-03-15)
- Tag deduplication and cross-view synchronization — 149 tags total (0 duplicates); tag removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
- Pagination for Chat/History/Commits — displays offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup; 204 total entries including Feb 23 archive (2026-03-15)
- AI suggestions auto-save to session — suggestions immediately create tags in proper category via _acceptSuggestedTag async call; tags appear in Planner; phase filter fully functional (2026-03-15)
- Commit phase filtering — added phase column to Commits table; filter by phase same as Chat tab; phase persists per commit in database; red ⚠ badge on sessions without phase (UI/CLI/WF all supported) (2026-03-15)

## Active Features / Bugs

- **[bug]** hooks `(86 events)`
- **[feature]** pagination `(86 events)`
- **[feature]** auth `(49 events)`
- **[feature]** workflow-runner `(1 events)`
- **[feature]** test-picker-feature `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** shared-memory `(0 events)`
- **[feature]** tagging `(0 events)`
- **[feature]** dropbox `(0 events)`
- **[feature]** UI `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[feature]** mcp `(0 events)`
- **[phase]** discovery `(1 events)`
- **[phase]** development `(0 events)`
- **[phase]** prod `(0 events)`

**[2026-03-15 22:40]** `claude_cli` — Phase persistence fixed: all sessions (UI/CLI/WF) now show red ⚠ badge if phase missing; phase loaded on app init from session JSON metadata; PATCH /chat/sessions/{id}/tags enables phase change without creating new session. **[2026-03-15 21:45]** `claude_cli` — Commit phase filtering added: Commits table now displays phase column with same filter controls as Chat tab; phase persists per commit in database. **[2026-03-15 20:44]** `claude_cli` — AI suggestions auto-save: /memory suggestions now immediately create tags in proper category via async _acceptSuggestedTag call; tags appear in Planner tree; phase filter fully functional. **[2026-03-15 18:11]** `claude_cli` — Commit-per-prompt linking: replaced session-level commit strip with inline commits at bottom of each prompt entry (small ⑂ hash ↗ row with accent left-border); each prompt shows only its linked commits from commit_log.jsonl via prompt_source_id field. **[2026-03-15 17:44]** `claude_cli` — Tag cross-view sync: 149 total tags (0 duplicates); DELETE /entities/events/tag-by-source-id enables tag removal with ✕ buttons; tag changes propagate instantly across Chat/History/Commits views. **[2026-03-15 17:28]** `claude_cli` — Pagination added: Chat/History/Commits all display offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives on startup; 204 total entries including Feb 23 archive.