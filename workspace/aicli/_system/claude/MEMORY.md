# Project Memory — aicli
_Generated: 2026-03-08 04:32 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform designed to enable seamless collaboration and context-sharing across multiple AI tools (Claude CLI, aicli, Cursor) through unified history tracking, billing/usage management, and planned semantic search via pgvector. Currently in active development with focus on fixing hooks integration, completing PostgreSQL-backed billing/usage tracking, and establishing the shared memory architecture that allows different LLMs to understand project state through history.jsonl, commit_log.jsonl, and metadata files.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt
- **frontend**: Vanilla JS + Electron (xterm.js + Monaco editor)
- **storage**: JSONL (history.jsonl, commit_log.jsonl) / JSON / CSV
- **database**: PostgreSQL (user_usage, usage_logs, billing logs) + pgvector (planned)
- **authentication**: JWT (python-jose) + bcrypt
- **planned**: GraphQL, node graph UI, pgvector semantic search, unified provider logging
- **orm**: SQLAlchemy (inferred from PostgreSQL usage)

## Key Decisions

- No ChromaDB / SQLite — flat files only (JSONL / JSON / CSV) for history tracking
- Electron UI (not Tauri) with xterm.js terminal + Monaco editor
- Auth: REQUIRE_AUTH toggle; JWT via python-jose; bcrypt for password hashing
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content
- All LLM providers independent — CLI providers/ ≠ ui/backend/core/llm_clients.py
- Client sends own API keys in request headers — server never stores keys
- User roles: admin, paid, free tier with dev_mode toggle for testing
- Manual balance setup via UI (no auto-fetch due to API limitations)
- All history tracked to history.jsonl + commit_log.jsonl for shared LLM memory
- PostgreSQL for user_usage / billing logs; pgvector planned for semantic search
- Hooks auto-commit on claude cli / cursor; aicli tracks own history
- Node graph / GraphQL planned for entity relationships and workflow management
- dev_runtime_state.json + project_state.json auto-maintenance for LLM context
- Memory auto-summarisation at token limit; /memory command uploads all relevant files
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history

## In Progress

- Fix hooks integration — commits not working from claude cli; verify history.jsonl captures responses
- Complete billing/balance tracking — manual balance entry working but not persisting on refresh; admin sees total, users see own balance
- PostgreSQL table creation — usage_logs table exists but entries not populating; need to ensure all providers log usage
- Consolidate workflow management — 'flows' tab created but 'workflow' tab already exists; clarify entity vs workflow distinction
- Memory system optimization — commit_log.jsonl not capturing all errors/logs from all sources; ensure claude cli, aicli, cursor hooks all write unified history
- Shared memory architecture — define how LLMs read/compress history files; establish memory digest strategy for /memory command

**[2026-03-08 04:27]** `claude_cli` — Consolidated understanding: project needs unified history system across claude cli, aicli, cursor; PostgreSQL tables (usage_logs, user_usage) not auto-populating; need to clarify 'flows' vs 'workflow' tabs and entity model. **[2026-03-08 04:13]** `claude_cli` — Asked about memory compression strategy: how LLMs read commit_log.jsonl, project.md, history files to understand project state; /memory command should upload all relevant context. **[2026-03-08 04:05]** `claude_cli` — commit_log.jsonl must capture all logs/errors from claude cli hooks, aicli commits, cursor hooks; currently incomplete. **[2026-03-08 03:27]** `claude_cli` — Proposed pgvector + node graph for workflow management: algo developer (deepseek) → backtesting (claude) → qa (claude) → summary (openai); PostgreSQL already in place. **[2026-03-08 02:51]** `claude_cli` — Identified broken hooks (no git commits from claude cli) and incomplete history tracking (responses not captured in history.jsonl); clarified _system vs history folder redundancy. **[2026-03-08 02:09]** `claude_cli` — Code optimization needed: move hardcoded PRICING from core/cost_tracker.py to UI-managed JSON config; consolidate use of classes and config throughout codebase.