# Project Memory — aicli
_Generated: 2026-03-08 05:06 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling multiple LLMs (Claude CLI, aicli, Cursor) to collaborate on projects by maintaining unified history files (history.jsonl, commit_log.jsonl) and PostgreSQL-backed user/billing logs. Currently stabilizing core features: hooks-based git integration, balance tracking via manual entry, and multi-user role management (admin/paid/free) with dev_mode testing support; next phase introduces node-graph workflows and pgvector semantic search for intelligent project comprehension.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron (xterm.js + Monaco editor)
- **storage**: JSONL (history.jsonl, commit_log.jsonl) / JSON / CSV
- **database**: PostgreSQL (user_usage, usage_logs, billing_logs) + pgvector (planned)
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
- Balance persistence on UI refresh — manual balance entry saves but doesn't persist; admin sees total across all users, users see own balance
- PostgreSQL usage_logs table population — table created but entries not populating; ensure all providers log usage and refresh displays totals
- Consolidate workflow/entity management — 'flows' tab created but 'workflow' tab exists; clarify distinction and build unified node graph UI instead of separate tabs
- Memory system optimization for LLM understanding — define /memory command strategy to read/compress history files; establish memory digest for cross-session project comprehension
- Unified history capture from all sources — commit_log.jsonl not capturing claude cli/aicli/cursor errors and logs; ensure all system events logged for shared context

**[2026-03-07 13:42]** `claude_cli` — Restructured documentation: consolidated CLAUDE.md (system-copied) and README.md (system-updated) instead of maintaining separate QUICKSTART.md, reducing documentation drift.
**[2026-03-07 14:33]** `claude_cli` — Added user role system (admin, paid, free) with dev_mode toggle for testing without login; backend address conflict and empty UI screen issues fixed.
**[2026-03-07 18:04]** `claude_cli` — Implemented manual balance entry for API keys (avoiding rate-limited balance endpoints); admin dashboard shows total balance/usage across all users; users see personal balance only.
**[2026-03-07 23:35]** `claude_cli` — Confirmed Claude API only works for team accounts (not personal); OpenAI usage API returns zero; decided to support manual balance updates via UI instead of auto-fetch.
**[2026-03-08 01:18]** `claude_cli` — Identified core architectural priority: shared memory between claude cli, aicli, and cursor via unified history.jsonl + commit_log.jsonl for LLM cross-session context.
**[2026-03-08 03:14]** `claude_cli` — Proposed GraphQL + node graph UI for workflows (algo→backtest→qa→summary across different LLM models) + pgvector semantic search with relational tagging for entity/relationship management in PostgreSQL.