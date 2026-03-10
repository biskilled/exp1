# Project Memory — aicli
_Generated: 2026-03-10 00:15 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that unifies project development history across multiple LLM sources (Claude, OpenAI, DeepSeek, etc.) via a Vanilla JS + Electron frontend backed by FastAPI, PostgreSQL with pgvector, and flat-file JSONL storage. Current state (v2.1.0) includes a unified tag-based planner replacing separate Feature/Bug tabs, session memory capture in history.jsonl, and /memory synthesis with per-LLM summaries; immediate focus is validating session logging, fixing frontend reload on startup, and integrating workflow status with features/tasks.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values; events table includes due_date column
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
- MCP server as standalone stdio process for Claude Code integration without backend dependency
- Unified tag-based planner: single category→tags hierarchy replaces separate Features/Bugs/Tags tabs; tags store status, description, custom properties, due_date

## In Progress

- Planner UI redesign — consolidate Feature/Bug/Tag tabs into unified tag-based system with category hierarchy, status management, custom properties (due_date, user-created fields), and full CRUD via API
- Session memory capture validation — ensure user prompts and LLM responses are logged to session context; verify /memory synthesis increments correctly from last_memory_run; validate history.jsonl persistence across sources
- Backend API integration for planner — added due_date column to database schema and API endpoint; frontend tags.js now calls updated /entities endpoints
- Frontend reload issue resolution — identified bind address conflict (uvicorn PID 86671 already running); confirmed backend healthy and schema live; frontend requires Cmd+R reload in Electron
- Project management dashboard enhancement — plan richer summary cards with event count, recent commits, active features, workflow runs, and activity timeline
- Client install / multi-project support — design session-based project switching with persistent unified history.jsonl per project

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

**[2026-03-09 04:08]** `claude_cli` — /memory endpoint ran with LLM synthesis; all summaries copied to code_dir for next development phase.
**[2026-03-09 17:56]** `claude_cli` — User identified that session capture for prompts and responses is missing; expected synthesis in history.jsonl alongside /memory output.
**[2026-03-09 23:51]** `claude_cli` — Planner UI redesign initiated: consolidated Feature/Bug/Tag/Tags tabs into unified tag-based system with category hierarchy, status, description, and custom properties (due_date, user-created fields).
**[2026-03-10 00:11]** `claude_cli` — Frontend UI loading issue diagnosed: uvicorn bind error at 127.0.0.1:8000 caused by existing PID 86671; backend confirmed healthy with due_date column live in API; frontend syntax valid; fix: Cmd+R reload in Electron.
**[2026-03-10 (inferred)]** — Planner tag-based API endpoints updated with due_date and custom properties support; /entities endpoints integrated into frontend tags.js.
**[2026-03-10 (inferred)]** — Session memory capture validation prioritized: ensure prompts/responses logged to session context, /memory increments from last_memory_run, and history.jsonl persists across all sources (ui/claude_cli/workflow).