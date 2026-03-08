# Project Memory — aicli
_Generated: 2026-03-08 05:06 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform that enables claude cli, aicli (custom CLI), and cursor to collaborate with unified history across JSONL files and PostgreSQL. Users (admin/paid/free) manage API keys, track balance and usage per provider, and design LLM workflows using a planned node graph UI with pgvector semantic search. Current focus: fix hook integration for commit_log.jsonl, persist balance across refreshes, populate PostgreSQL usage_logs, and consolidate workflow/entity management into a single node-based system.

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

- Fix hooks integration — commits not working from claude cli; history.jsonl captures prompts but not responses; ensure all sources write to commit_log.jsonl
- Balance persistence on refresh — manual balance entry saves but doesn't persist on UI refresh; admin sees total, users see own balance
- PostgreSQL usage_logs population — table created but entries not populating; ensure all providers log usage and refresh UI displays totals
- Consolidate workflow/entity management — 'flows' tab created but 'workflow' tab exists; clarify distinction; build node graph UI instead of separate tabs
- Memory system optimization — commit_log.jsonl not capturing all errors/logs from claude cli, aicli, cursor; ensure unified history across all sources
- Shared memory architecture for LLM context — define how /memory command reads/compresses history files; establish memory digest strategy for project understanding

**[2026-03-08 04:47]** `claude_cli` — Workflow system requires node-based execution (prompts as nodes with LLM engines per node, e.g., algo→backtest→qa→summary); consolidate 'flows' + 'workflow' tabs into single node graph UI. **[2026-03-08 04:27]** `claude_cli` — PostgreSQL tables not created; 'entities' vs 'workflows' distinction needed; workflows should use YAML config or UI-managed prompt flows. **[2026-03-08 04:13]** `claude_cli` — /memory command must upload all project files for LLM context; clarify memory compression strategy for understanding project state. **[2026-03-08 04:05]** `claude_cli` — All logs (errors, commits, responses) must write to commit_log.jsonl from claude cli hooks, aicli commits, cursor hooks for unified history. **[2026-03-08 03:14]** `claude_cli` — GraphQL + node graph UI planned for entities/relationships; pgvector for semantic tagging + relational search; vectordb ingestion enables faster project understanding. **[2026-03-08 02:51]** `claude_cli` — Hooks not committing (claude cli); history.jsonl captures prompts only, not responses; commit_log.jsonl not tracking all history. **[2026-03-08 00:30]** `claude_cli` — Balance saved but doesn't persist on refresh; admin sees total balance, users see own; all calculations should update on refresh. **[2026-03-07 23:54]** `claude_cli` — Manual balance setup via usage page; remove row deletion (x) not working; mark unsaved changes in billing UI. **[2026-03-07 21:15]** `claude_cli` — Billing tracker: capture usage from OpenAI/Claude APIs; manual balance entry as fallback (APIs unavailable for personal accounts); track cost per provider/user/date. **[2026-03-07 14:45]** `claude_cli` — UI: add role/plan display; close login/register forms; show refresh symbol for balance updates; persist user status on UI reload.