# Project Memory — aicli
_Generated: 2026-03-08 04:22 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

**aicli** is a shared AI memory platform enabling multiple LLMs (Claude, aicli CLI, Cursor) to collaboratively develop projects by reading/writing unified history, commit logs, and metadata. Currently building: PostgreSQL billing tracker, auto-commit hooks across all editors, pgvector semantic search, and a GraphQL node graph for entity relationships and multi-LLM workflows.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt
- **frontend**: Vanilla JS + Electron (xterm.js + Monaco editor)
- **storage**: JSONL (history.jsonl, commit_log.jsonl) / JSON / CSV
- **database**: PostgreSQL (user_usage, billing logs); pgvector planned
- **authentication**: JWT (python-jose) + bcrypt
- **planned**: GraphQL, node graph, pgvector semantic search

## Key Decisions

- No ChromaDB / SQLite — flat files only (JSONL / JSON / CSV)
- Electron UI (not Tauri) with xterm.js terminal + Monaco editor
- Auth: REQUIRE_AUTH toggle; JWT via python-jose; bcrypt direct
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content
- All LLM providers independent — CLI providers/ ≠ ui/backend/core/llm_clients.py
- Client sends own API keys in request headers — server never stores keys
- User roles: admin, paid, free tier with dev_mode toggle for testing
- Balance tracking: manual setup via UI (no auto-fetch due to API limitations)
- All history tracked to history.jsonl + commit_log.jsonl for LLM memory sharing
- PostgreSQL for user_usage / billing logs; pgvector planned for semantic search
- Hooks auto-commit on claude cli / cursor; aicli tracks own history
- Node graph / GraphQL planned for entity relationships and workflow management
- dev_runtime_state.json + project_state.json auto-maintenance for LLM context
- Memory auto-summarisation at token limit; /memory command uploads all relevant files
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history

## In Progress

- Commit hooks integration — ensure all claude cli, aicli, cursor changes auto-commit to git
- Billing/usage tracking UI — balance display (top-right), per-API-key balance in admin panel, refresh button
- History tracking completeness — verify all prompts + responses captured in history.jsonl
- Memory/context optimization — LLM reads commit_log.jsonl, project.md, history files to understand project state
- PostgreSQL + pgvector integration — user_usage table, semantic search for project entities
- GraphQL node graph for workflows — entity relationships, task/feature/bug metadata management

**[2026-03-08 04:13]** `claude_cli` — User clarified project goal: **shared memory between different LLMs** (claude cli, aicli, cursor). All history must flow to commit_log.jsonl with errors; all hooks (claude cli, aicli, cursor) must commit to git. **[2026-03-08 04:05]** `claude_cli` — Expanded vision: add PostgreSQL + pgvector for semantic embedding, node graph for workflow/role relationships (e.g., algo→backtest→QA→summary), metadata (tasks/features/bugs) in SQL. **[2026-03-08 03:07]** `claude_cli` — Questioning dev_runtime_state.json necessity; asking how unified history improves LLM project understanding. **[2026-03-08 00:53]** `claude_cli` — Recognized provider_usage files exist but unused; proposed vectordb for faster context retrieval across LLMs. **[2026-03-08 00:30]** `claude_cli` — Balance persists but doesn't refresh on page reload; users tab balance not updating. Requested current state documentation. **[2026-03-07 23:54]** `claude_cli` — Balance endpoint missing; consolidated balance management to usage page. Billing/usage bugs: fetch history rows not deletable, update returns 404.