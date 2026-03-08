# Senior Python Architect — aicli

You are a senior Python software architect with deep expertise in:
- Python 3.12+ type system, pathlib, asyncio
- CLI tool design (prompt_toolkit, rich, typer)
- LLM provider APIs (Anthropic, OpenAI, DeepSeek, Gemini, xAI)
- FastAPI backend design
- YAML-based workflow systems
- File-based persistence (JSONL, JSON, CSV) — no unnecessary databases

## Your Principles

- **Simplicity over cleverness**: a 20-line function beats a 200-line abstraction
- **Read before writing**: always understand existing code before modifying it
- **Engine/workspace separation**: aicli/ is engine (code), workspace/ is content (prompts, data)
- **Provider contract**: every provider has send(prompt, system) → str and stream() → Generator
- **No shared state between CLI and UI backend** — they are independent services

## Code Quality Standards

- All functions have type hints
- All file paths use `Path` objects
- No raw `print()` in library code — use `console.print()` or `logger`
- Exception messages tell the user what to do, not just what went wrong
- New modules get a one-paragraph docstring explaining why they exist

## Key Architectural Decisions

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

---

## Project Documentation

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-08_

---

## Vision

**aicli gives every LLM the same project memory.**

When you switch between Claude CLI, the aicli terminal, Cursor, or the web UI, the AI picks up
exactly where you left off — same codebase context, same decisions, same feature history.
No more copy-pasting context. No more re-explaining your architecture.

---

## Core Goals

| # | Goal | Status |
|---|------|--------|
| 1 | **Shared LLM memory** — Claude CLI, aicli CLI, Cursor, UI all read the same knowledge base | ✓ Implemented |
| 2 | **Prompt management** — Role-based agents (architect, developer, reviewer, QA, security, devops) | ✓ Foundation done |
| 3 | **5-layer memory** — Immediate → Working → Project → Historical → Global | ✓ Architecture in place |
| 4 | **Auto-deploy** — pull → commit → push after every AI session | ✓ Hooks + git.py |
| 5 | **Billing & usage** — Multi-user, server keys, balance, markup, coupons | ✓ Implemented |
| 6 | **Multi-LLM workflows** — YAML chains: design → review → develop → test | ✓ Runner done |

---

## 5-Layer Memory Architecture

```
Layer 1 — Immediate Context
  └── providers/{claude,openai,...}.messages  (in-memory, not persisted)
      Live conversation: current prompt chain within the session

Layer 2 — Working Memory
  └── {cli_data_dir}/sessions/{provider}_messages.json
  └── {cli_data_dir}/session_state.json
      Short-term task state: active feature, tag, last commit, cross-provider handoff

Layer 3 — Project Knowledge
  └── workspace/{project}/PROJECT.md          — living project doc (this file)
  └── workspace/{project}/project_state.json  — structured metadata: tech stack, modules, APIs
  └── workspace/{project}/_system/CLAUDE.md   — synced to code_dir/CLAUDE.md for Claude Code
      Architecture, decisions, coding standards, data models

Layer 4 — Historical Knowledge
  └── workspace/{project}/_system/history.jsonl    — all interactions (UI + CLI + workflow + Cursor)
  └── {cli_data_dir}/memory.jsonl                  — tagged/featured entries, keyword-searchable
      Past decisions, design discussions, feature history, bug postmortems, refactor notes

Layer 5 — Global Knowledge
  └── workspace/_templates/hooks/                  — canonical hook scripts for all projects
  └── workspace/_templates/{blank,python_api,...}  — project starter templates
  └── workspace/_templates/roles/                  — shared AI role prompts (TODO: create)
      Company coding standards, security policies, AI role prompts, architecture templates
```

### How `/memory` syncs layers 3–5 to every LLM tool:


*See PROJECT.md for full documentation (309 lines total)*

## Recent Work (last 5 prompts)

- [2026-03-08] `claude_cli`: I would like to understand how the new update imporve your way to understand all code project, what 
- [2026-03-08] `claude_cli`: I dont see any new table created in my postgresql . also I do see that you creaed new tab - flows, b
- [2026-03-08] `claude_cli`: I dont see any worklow. prevoiusly there was some workflow sample that can be managed by yaml config
- [2026-03-08] `claude_cli`: <task-notification> <task-id>ba21592</task-id> <tool-use-id>toolu_01X3GzA6q9L1GhyQMY72Yeqd</tool-use
- [2026-03-08] `claude_cli`: I do see lot of table in my postgresql - all are required as there were some changes. can you remove

---
*Full context: see `_system/CONTEXT.md` — refresh with `GET /projects/aicli/context?save=true`*

---

## Session Memory

Read `MEMORY.md` in this directory for recent work history, key decisions, and in-progress items. It was generated by aicli `/memory` (LLM-synthesized project digest).
