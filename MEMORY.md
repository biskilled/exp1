# Project Memory — aicli
_Generated: 2026-03-08 05:28 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling multi-tool collaboration (claude cli, aicli, cursor) through unified history tracking (history.jsonl, commit_log.jsonl) and a FastAPI backend with PostgreSQL. Current focus is consolidating fragmented features (balance persistence, workflow node execution, hooks integration) and establishing the semantic search + multi-agent workflow infrastructure via pgvector and node graph UI.

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

## In Progress

- Unified history + commit_log population — ensure all logs from claude cli hooks, aicli commits, cursor hooks captured; commit_log.jsonl must track errors and system events across all sources
- Balance persistence across UI refresh — manual balance entry saves but doesn't persist; admin sees total across all users; usage_logs table not populating despite creation
- PostgreSQL table cleanup — remove unused tables; consolidate workflow/flows distinction; clarify entities vs node graph UI implementation
- Hooks integration from claude cli — commits not working; history.jsonl captures prompts but not responses; ensure commit_log.jsonl populated from all tools
- Multi-agent workflow execution via node graph — transition from YAML config to UI-managed node graphs; each node runs prompt with specified LLM engine and outputs score for branching
- Shared memory strategy across tools — establish how claude cli, aicli, and cursor read/compress history files; implement /memory command to upload relevant context for cross-session project comprehension

**[2026-03-08 05:18]** `claude_cli` — Clarified multi-agent workflow architecture: nodes execute YAML-based prompts with assigned LLM engines (algo→backtest→qa→summary), each producing scores for conditional progression; node graph UI will replace static YAML management. **[2026-03-08 05:10]** `claude_cli` — Identified PostgreSQL schema bloat; multiple tables created but unclear which are active; consolidation needed between workflows/flows and entities tables. **[2026-03-08 04:47]** `claude_cli` — Workflow execution model clarified: nodes contain prompts as agent roles, LLM engine assignment per node, user approval flow between nodes, output scoring drives next node selection. **[2026-03-08 04:13]** `claude_cli` — Established shared memory compression strategy: /memory command must upload all relevant history files; claude cli, aicli, cursor should leverage commit_log.jsonl + history.jsonl for cross-tool context; dev_runtime_state.json provides session snapshots. **[2026-03-08 00:40]** `claude_cli` — Recognized core project goal: enable shared AI memory between claude cli, aicli, and cursor via unified JSONL history files and PostgreSQL tracking; current gap is that provider_usage hooks exist but no consumer actively reads/ingests them. **[2026-03-07 23:35]** `claude_cli` — Implemented manual balance management: provider APIs (OpenAI, Claude) don't expose usage/balance for personal accounts; shifted to manual balance entry in UI with persistence to JSON config and PostgreSQL billing_logs.