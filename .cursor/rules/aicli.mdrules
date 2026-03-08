# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-08 05:28 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-08_

---

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron (xterm.js + Monaco editor)
- **storage**: JSONL (history.jsonl, commit_log.jsonl) / JSON / CSV
- **database**: PostgreSQL (users, user_usage, usage_logs, billing_logs, workflows, runs) + pgvector (planned)
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
- Multi-agent workflows: node-based execution with LLM engines per node via YAML config (algo→backtest→qa→summary across different models)
- Cost tracking: pricing managed by config/JSON (not hardcoded); usage logged per provider/user/date in PostgreSQL
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history files + commit_log.jsonl
- GraphQL + node graph UI planned for entity relationships and workflow management with prompt-based node execution
- Memory auto-summarisation at token limit; /memory command uploads all relevant files for LLM context
- dev_runtime_state.json + project_state.json auto-maintenance for shared LLM context across sessions

## Recent Context (last 5 changes)

- [2026-03-08] I dont see any worklow. prevoiusly there was some workflow sample that can be managed by yaml config as well. worklow su
- [2026-03-08] <task-notification> <task-id>ba21592</task-id> <tool-use-id>toolu_01X3GzA6q9L1GhyQMY72Yeqd</tool-use-id> <output-file>/p
- [2026-03-08] I do see lot of table in my postgresql - all are required as there were some changes. can you remove table not in use?
- [2026-03-08] let me try to explain workflow again - the goal is to build mutl agent flows. I have managed to do that using yaml . and
- [2026-03-08] the second one - under _system/run