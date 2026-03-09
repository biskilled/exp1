# Project Memory — aicli
_Generated: 2026-03-09 04:12 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a shared AI memory platform (v2.1.0) that integrates multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) with persistent project memory, semantic search via PostgreSQL+pgvector, and workflow automation. It combines a Python CLI (prompt_toolkit + rich) with a web UI (Vanilla JS + Electron) featuring an embedded terminal (xterm.js), Monaco editor, and Cytoscape-based workflow graphs. Currently enhancing project management dashboards, workflow-to-project integration for feature tracking, and memory synthesis pipelines to enable rich historical context for multi-session AI collaboration.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values
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
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search and entity graph — no SQLite/ChromaDB
- Per-project DB tables (commits_aicli, events_aicli, etc.) via project_table() + ensure_project_schema() — no full-table scans with project filter
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step
- JWT auth via python-jose + bcrypt (NOT passlib); dev_mode toggle for local testing without login
- All LLM providers independent; server holds API keys (api_keys.json); client sends NO keys
- Config-driven pricing — provider_costs.json is single source of truth; no hardcoded costs
- Multi-agent workflows: async DAG executor via asyncio.gather; loop-back edges with max_iterations cap
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata filters
- 5-layer memory: immediate (in-memory) → working (session JSON) → project (PROJECT.md + project_state.json) → historical (history.jsonl) → global (templates)
- /memory generates 4 per-LLM files + copies to code_dir; LLM synthesis via Haiku; incremental ingest
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Entity/event model: entity_categories + entity_values (shared) + per-project events/event_tags/event_links
- MCP server as standalone stdio process so Claude Code connects without backend running
- UI installer: install.sh (one-time) + update.sh (git pull + deps) + start.sh — never touches workspace/

## In Progress

- Project management page redesign — richer dashboard with metrics (event count, active features, recent commits, workflow runs), activity timeline, quick-action buttons
- Workflow ↔ project integration — link workflow runs to features/tasks; auto-create task events from workflow outputs; show workflow status per feature
- Workflow process improvements — better YAML editor UX, step-by-step run log with timing per node, re-run from any node, templates library
- Project overview dashboard — summary card per project: last activity, open tasks, active features, recent commits, LLM cost this week
- DB schema refactoring complete — project_table() and ensure_project_schema() deployed; per-project tables (commits_{p}, events_{p}, embeddings_{p})
- Memory synthesis pipeline — /memory endpoint generates 4 per-LLM summary files; Haiku incremental synthesis; copy to code_dir for persistence

## Active Features / Bugs

- **[feature]** workflow-runner `(0 events)`
- **[feature]** test-picker-feature `(0 events)`
- **[feature]** mcp `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** tagging `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** auth `(0 events)`
- **[feature]** shared-memory `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[phase]** development `(0 events)`
- **[phase]** discovery `(0 events)`
- **[phase]** prod `(0 events)`

**[2026-03-09]** `claude_cli` — DB schema refactoring completed: added `project_table(base, project)` static method and `ensure_project_schema(project)` to create per-project tables (commits_aicli, events_aicli, embeddings_aicli, etc.) without redundant project columns. Removed legacy shared commits/events tables; schema now enforces project isolation at table level, not filter level. **[2026-03-09]** `claude_cli` — Prepared /memory endpoint for synthesis: generates 4 per-LLM summary files using Claude Haiku for incremental synthesis since last_memory_run, copies to code_dir for persistence. Ready to integrate with project dashboard. **[2026-03-09]** `in-progress` — Project management page redesign underway: adding metrics dashboard (event count, active features, recent commits, workflow runs), activity timeline, and quick-action buttons to replace static project list. **[2026-03-09]** `in-progress` — Workflow ↔ project integration: planning to link workflow run outputs to feature/task events, auto-create task events from node outputs, and display workflow status per feature in Projects tab for end-to-end feature tracking. **[2026-03-09]** `in-progress` — Workflow UX improvements: better YAML editor, step-by-step run log with per-node timing, re-run from arbitrary nodes, and workflow templates library in workspace/_templates/workflows/. **[2026-03-09]** `in-progress` — Global knowledge layer: shipping 6 default shared roles in workspace/_templates/roles/ on install, enabling multi-agent collaboration without per-project role duplication.