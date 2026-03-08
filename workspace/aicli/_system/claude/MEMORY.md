# Project Memory — aicli
_Generated: 2026-03-08 05:16 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling multiple LLM tools (claude cli, aicli, cursor) to collaborate on projects via unified history files, PostgreSQL tracking, and multi-agent workflows. The project supports user roles (admin/paid/free), manual API key/balance management via Electron UI, and is working toward GraphQL node graphs and pgvector semantic search for deeper project understanding across LLM sessions.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron (xterm.js + Monaco editor)
- **storage**: JSONL (history.jsonl, commit_log.jsonl) / JSON / CSV
- **database**: PostgreSQL (user_usage, usage_logs, billing_logs, users table) + pgvector (planned)
- **authentication**: JWT (python-jose) + bcrypt + dev_mode toggle
- **planned**: GraphQL, node graph UI, pgvector semantic search, unified provider logging
- **orm**: SQLAlchemy

## Key Decisions

- No ChromaDB / SQLite — flat files only (JSONL / JSON / CSV) for history tracking; PostgreSQL for user_usage / billing logs only
- Electron UI (not Tauri) with xterm.js terminal + Monaco editor; Vanilla JS frontend
- Auth: REQUIRE_AUTH toggle; JWT via python-jose; bcrypt for password hashing; dev_mode for testing without login
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content; _system folder stores all project state
- All LLM providers independent — CLI providers/ ≠ ui/backend/core/llm_clients.py; client sends own API keys in headers
- User roles: admin, paid, free tier with dev_mode toggle; manual balance entry via UI (no auto-fetch due to API limitations)
- All history tracked to history.jsonl + commit_log.jsonl for shared LLM memory across claude cli, aicli, cursor
- PostgreSQL for user_usage / billing logs with pgvector planned for semantic search; SQLAlchemy ORM
- Hooks auto-commit on claude cli / cursor; aicli tracks own history; unified history.jsonl + commit_log.jsonl
- Node graph / GraphQL planned for entity relationships and workflow management with prompt-based node execution
- Memory auto-summarisation at token limit; /memory command uploads all relevant files for LLM context
- dev_runtime_state.json + project_state.json auto-maintenance for shared LLM context across sessions
- Multi-agent workflows: node-based execution with LLM engines per node (e.g., algo→backtest→qa→summary across different models)
- Cost tracking: pricing managed by config/JSON (not hardcoded); usage logged per provider/user/date in PostgreSQL
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history files + commit_log.jsonl

## In Progress

- Unified history capture from all sources — commit_log.jsonl not capturing claude cli/aicli/cursor errors and logs; ensure all system events logged for shared context across all tools
- Balance persistence on UI refresh — manual balance entry saves but doesn't persist after refresh; admin sees total across all users, users see own balance correctly
- PostgreSQL usage_logs table population — table created but entries not populating; ensure all providers log usage and refresh displays totals per user/provider/date
- Remove unused PostgreSQL tables — cleanup tables not in use; consolidate workflow/flows distinction and clarify entities vs node graph UI implementation
- Hooks integration from claude cli — commits not working from claude cli; history.jsonl captures prompts but not responses; ensure commit_log.jsonl populated with errors/logs from all sources
- Implement /memory command strategy — read/compress history files; establish memory digest for cross-session project comprehension and shared LLM understanding

**[2026-03-08 05:15]** `claude_cli` — Multi-agent workflow architecture clarified: goal is to build flows with YAML-defined nodes where each node has a prompt (agent role) and assigned LLM engine; nodes execute sequentially until user satisfaction before advancing. **[2026-03-08 05:10]** `claude_cli` — Request to remove unused PostgreSQL tables created during recent changes. **[2026-03-08 04:47]** `claude_cli` — Workflow/flows distinction unclear; existing workflow tab expected to manage all workflows via YAML config with prompt-based node execution and LLM engine assignment per node. **[2026-03-08 04:27]** `claude_cli` — PostgreSQL workflow/entities tables not created; flows tab added but conflicts with existing workflow tab; need clarification on entities purpose vs node graph UI implementation. **[2026-03-08 04:13]** `claude_cli` — Requested clarification on how /memory command summarizes/compresses project data for LLM understanding; commit_log.jsonl should centralize all logs from claude cli hooks, aicli commits, cursor hooks. **[2026-03-08 04:05]** `claude_cli` — All logs and errors must be written to commit_log.jsonl from all sources (claude cli hooks, aicli, cursor) for unified project history.