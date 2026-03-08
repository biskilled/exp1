# Project Memory — aicli
_Generated: 2026-03-08 05:12 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform designed to enable multiple LLMs (claude cli, aicli, cursor) to maintain and access unified project history across sessions. It features a Python CLI with FastAPI backend, Electron UI with terminal/editor, PostgreSQL for billing/usage tracking, JWT authentication with role-based access (admin/paid/free), and JSONL-based shared history. Current focus is fixing hooks integration, ensuring unified commit/error logging across all sources, implementing balance persistence, and planning node-graph workflows with pgvector semantic search.

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
- Workflows: node-based execution with LLM engines per node (e.g., algo→backtest→qa→summary across different models)
- Cost tracking: pricing managed by config/JSON (not hardcoded); usage logged per provider/user/date in PostgreSQL
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history files + commit_log.jsonl

## In Progress

- Fix hooks integration — commits not working from claude cli; history.jsonl captures prompts but not responses; ensure all sources write to commit_log.jsonl with errors/logs
- Balance persistence on UI refresh — manual balance entry saves but doesn't persist after refresh; admin sees total across all users, users see own balance
- PostgreSQL usage_logs table population — table created but entries not populating; ensure all providers log usage and refresh displays totals
- Remove unused PostgreSQL tables — cleanup tables not in use; consolidate workflow/entity management (flows vs workflow tabs distinction)
- Unified history capture from all sources — commit_log.jsonl not capturing claude cli/aicli/cursor errors and logs; ensure all system events logged for shared context
- Implement /memory command strategy — read/compress history files; establish memory digest for cross-session project comprehension

**[2026-03-08 05:10]** `claude_cli` — Completed cleanup of unused PostgreSQL tables; multiple tables created during recent changes need removal.
**[2026-03-08 04:47]** `claude_cli` — Consolidated workflow management: clarified distinction between 'flows' and 'workflow' tabs; node-based execution with LLM engines per node (algo→backtest→qa→summary).
**[2026-03-08 04:27]** `claude_cli` — Identified missing workflow tables in PostgreSQL; workflow/entity management tabs need unification via node graph UI instead of separate tabs.
**[2026-03-08 04:13]** `claude_cli` — Established commit_log.jsonl as unified error/log capture from all sources (claude cli hooks, aicli commits, cursor); /memory command strategy to compress history for LLM context.
**[2026-03-08 04:05]** `claude_cli` — Ensured all logs (errors included) written to commit_log.jsonl from all places; shared memory architecture across claude cli, aicli, cursor.
**[2026-03-08 03:14]** `claude_cli` — Planned GraphQL + node graph for entities and relationships; pgvector semantic embedding for relational tagging; workflow example (deepseek algo → claude backtest → claude qa → openai summary).
**[2026-03-08 02:51]** `claude_cli` — Diagnosed hooks not working (no new commits); history.jsonl captures prompts but not responses; commit_log.jsonl not populated.
**[2026-03-08 00:40]** `claude_cli` — Questioned shared memory architecture: how LLM loads history from compressed sessions and utilizes provider_usage files.
**[2026-03-08 00:30]** `claude_cli` — Balance saving implemented but not persisted on refresh; users tab balance totals not updating after manual entry.
**[2026-03-07 23:54]** `claude_cli` — Manual balance entry added to usage page (replaced separate tab); fixed remove row functionality for Fetch history; marked save changes visually.