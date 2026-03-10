# Project Memory — aicli
_Generated: 2026-03-09 18:17 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that integrates multiple LLM providers (Claude, OpenAI, DeepSeek, Gemini, Grok) into a unified CLI and web UI, enabling intelligent project tracking, workflow automation, and semantic memory synthesis. It uses PostgreSQL + pgvector for semantic search, per-project event/entity graphs, and a 5-layer memory system (immediate → working → project → historical → global) to maintain context across sessions. Current focus is on richer project dashboards, workflow-to-feature linking, and multi-project session management with persistent unified history.

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
- UI installer: install.sh (one-time) + update.sh (git pull) + start.sh — never touches workspace/

## In Progress

- Memory synthesis pipeline validation — /memory endpoint generates per-LLM summaries; Haiku incremental synthesis; copy to code_dir for persistence
- Project management page redesign — richer dashboard with event count, active features, recent commits, workflow runs, activity timeline
- Workflow ↔ project integration — link workflow runs to features/tasks; auto-create task events from workflow outputs; show workflow status per feature
- Workflow process improvements — better YAML editor UX, step-by-step run log with per-node timing, re-run from any node, templates library
- Project overview dashboard — summary card per project: last activity, open tasks, active features, recent commits, LLM cost this week
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

**[2026-03-09 04:08]** `claude_cli` — /memory endpoint synthesis complete: generates 4 per-LLM summary files using Haiku incremental synthesis; all files copied to code_dir for persistence and multi-session reuse. **[2026-03-09 04:08]** `claude_cli` — Project summary, current features, and ongoing features updated in memory system for next development phases. **[2026-03-09 17:56]** `claude_cli` — Session-based history validation: client install/multi-project support feature tracked in unified history.jsonl; session JSON now properly captures full prompts and synthesized responses separately from long-form features. **[Recent]** `in_progress` — Project management dashboard redesign with metrics (event count, active features, workflow status) and activity timeline; workflow ↔ project linking to auto-create task events. **[Recent]** `in_progress` — Workflow UX improvements: better YAML editor, step-by-step run logs with per-node timing, re-run from any node, template library support.