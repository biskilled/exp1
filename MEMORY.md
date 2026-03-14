# Project Memory — aicli
_Generated: 2026-03-14 14:37 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that unifies history and context across multiple AI tools (Claude CLI, Cursor, ChatGPT, etc.) for developers. It stores unified prompt/response history per project in JSONL format, enables semantic search via PostgreSQL + pgvector, and provides a desktop UI (Electron + Vanilla JS) and CLI for managing sessions, tags, commits, and workflows. Current state (v2.2.0): commit-to-prompt linking complete, tag caching optimized, memory synthesis working, phase-based session management live, and multi-agent DAG workflows visualized via Cytoscape.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
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
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Commit-to-prompt linking via source_id (timestamp from history.jsonl) stored in commit_log.jsonl; POST /entities/events/tag-by-source-id maps commits to events
- Session tags persist via GET /entities/session-tags endpoint; tag cache loaded once on history tab open
- Phase labeling visible in tag bar; 3-dot dropdown menu (⋯) per tag row for edit/archive/restore/delete actions
- AI suggestions as dedicated amber banner with /memory synthesis; always-on (DB best-effort), appears between tag bar and messages
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata; Claude Haiku for memory synthesis
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js for graph visualization

## In Progress

- Commit-to-prompt-to-session linking — source_id timestamp from history.jsonl maps to events in event_tags_{p}; POST /entities/events/tag-by-source-id creates bidirectional links between commits and prompts; multiple commits per session each tagged to their originating prompt (2026-03-14)
- Tag cache persistence in history tab — all categories/values loaded once on tab open via Promise.all; color preservation on save prevents DB thrashing; zero DB calls during tag picker operations (2026-03-14)
- CLAUDE.md memory layer alignment — verified synthesis logic matches multi-layer design; all recent features (nested tags, commit linking, session persistence, tag cache, graph workflows) captured in memory output; PROJECT.md v2.2.0 updated (2026-03-14)
- Port stability and startup flow — freePort() kills stale uvicorn via lsof before restart; Electron before-quit cleanup via process.exit() resolves bind address conflicts; clean restart workflow documented (2026-03-10)
- AI suggestions banner refinement — /memory runs always (DB best-effort), displays dedicated amber banner with approve/reject UI between tag bar and messages; works even without PostgreSQL fallback (2026-03-10)
- Session phase labeling clarity — 'Phase:' label instead of 'Session:' in tag bar; tag bar flex-wrap displays all suggestion chips; amber banner for AI suggestions with clear approval workflow (2026-03-10)

## Active Features / Bugs

- **[feature]** auth `(2 events)`
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

**[2026-03-14]** `claude_cli` — Commit-to-prompt linking finalized: POST /entities/events/tag-by-source-id maps history.jsonl source_id timestamps to events; enables tracking which commits relate to which specific prompts within a session; multiple commits per session each linked to originating prompt. **[2026-03-14]** `claude_cli` — Tag cache optimization completed: history tab loads all categories/values once on open via Promise.all; color preservation on save prevents DB thrashing; tag picker now operates with zero DB calls. **[2026-03-14]** `claude_cli` — Memory layer alignment verified: CLAUDE.md multi-layer design confirmed; PROJECT.md updated to v2.2.0; all recent features (nested tags, commit linking, session persistence, tag cache, graph workflows) properly documented. **[2026-03-10]** `claude_cli` — Port binding and startup stability resolved: freePort() kills stale uvicorn via lsof before port reuse; Electron before-quit cleanup via process.exit() prevents bind address conflicts; clean startup workflow documented. **[2026-03-10]** `claude_cli` — AI suggestions banner finalized: /memory runs always (DB best-effort fallback), displays dedicated amber banner between tag bar and messages; includes approve/reject UI with clear visual distinction from session tags. **[2026-03-10]** `claude_cli` — Phase labeling and session tag clarity improved: 'Phase:' label replaces 'Session:' in tag bar; tag bar flex-wrap handles multiple suggestion chips; session-tags endpoint persists tags across sessions; 3-dot menu (⋯) enables archive/restore/delete workflows.