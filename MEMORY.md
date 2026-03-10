# Project Memory — aicli
_Generated: 2026-03-10 00:07 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that provides multi-agent AI workflows, semantic project history, and unified task management via a flat-file + PostgreSQL backend. It unifies CLI, Electron desktop, and web UI with JWT auth, integrates 5+ LLM providers via independent adapters, and supports Claude Code via standalone MCP server. Current focus: fixing session memory capture, consolidating planner UI into a unified tag-based system, and linking workflows to project features for full traceability.

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
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search and entity graph
- Per-project DB tables (commits_{p}, events_{p}, embeddings_{p}) via project_table() + ensure_project_schema()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing without login
- All LLM providers independent; server holds API keys; client sends NO keys
- Config-driven pricing via provider_costs.json as single source of truth
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- 5-layer memory: immediate (in-memory) → working (session JSON) → project (PROJECT.md) → historical (history.jsonl) → global (templates)
- /memory generates 4 per-LLM files + copies to code_dir; Haiku incremental synthesis
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Entity/event model: shared entity_categories/entity_values + per-project events/event_tags/event_links
- MCP server as standalone stdio process for Claude Code integration without backend dependency
- Unified tag-based planner: single category→tags hierarchy replaces separate Features/Bugs/Tags tabs; tags store status, description, properties

## In Progress

- Planner UI redesign — consolidate Feature/Bug/Tag/Status tabs into unified tag-based system with categories, status management, and custom properties per tag
- Session memory capture — ensure user prompts and LLM responses are logged to session context alongside /memory synthesis; validate history.jsonl persistence
- Memory synthesis validation — verify /memory endpoint generates per-LLM summaries with incremental Haiku synthesis and copies to code_dir
- Project management dashboard — richer summary cards with event count, recent commits, active features, workflow runs, activity timeline
- Workflow ↔ project integration — link workflow runs to features/tasks; auto-create task events from workflow outputs; show workflow status per feature
- Client install / multi-project support — session-based project switching with persistent history per project in unified history.jsonl

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

**[2026-03-09 04:08]** `claude_cli` — /memory endpoint synthesized with per-LLM outputs and Haiku incremental synthesis; all files copied to code_dir for persistence. **[2026-03-09 17:56]** `claude_cli` — Identified gap: session-based memory capture not working; user prompts and responses should appear in session context alongside history.jsonl and /memory synthesis. **[2026-03-09 23:51]** `claude_cli` — Major planner UX decision: replace 4-tab system (Features/Bugs/Tags/Status) with unified tag-based model using category→tags hierarchy; each tag stores status, description, and custom properties; eliminates UI duplication. **[ongoing]** — Memory pipeline validation in progress; project dashboard redesign underway with event counts and activity timeline; workflow↔project linking to auto-create task events; multi-project session support with persistent unified history.jsonl.