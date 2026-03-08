# Project Memory — aicli
_Generated: 2026-03-08 22:34 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling claude cli, aicli, and cursor to collaboratively understand project state across sessions via unified history.jsonl + commit_log.jsonl files. It features a FastAPI backend with JWT auth, PostgreSQL user/billing tracking, and an Electron UI for multi-agent YAML workflows, with planned pgvector semantic search and node-graph UI for workflow management. Current focus is fixing hooks integration, balance persistence, and consolidating the database schema while establishing a shared memory strategy across all tools.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron with xterm.js + Monaco editor
- **storage**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV
- **database**: PostgreSQL (users, user_usage, usage_logs, billing_logs, workflows, runs) + pgvector (planned)
- **authentication**: JWT (python-jose) + bcrypt + dev_mode toggle
- **planned**: GraphQL, node graph UI, pgvector semantic search, unified provider logging
- **orm**: SQLAlchemy

## Key Decisions

- Flat file storage (JSONL/JSON/CSV) for history tracking + PostgreSQL for user_usage/billing logs; no ChromaDB/SQLite
- Electron UI with xterm.js terminal + Monaco editor; Vanilla JS frontend (not Tauri)
- JWT auth via python-jose + bcrypt; dev_mode toggle for testing without login; three user roles (admin/paid/free)
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content, _system/ = project state
- All LLM providers independent; clients send own API keys in headers; no hardcoded pricing (config-driven)
- Multi-agent workflows via node-based execution with YAML config (transitioning to UI-managed node graphs)
- Unified history.jsonl + commit_log.jsonl shared across claude cli, aicli, cursor via hooks and commits
- Manual balance entry in UI (no auto-fetch due to API limitations); admin sees total across all users
- PostgreSQL with SQLAlchemy ORM; pgvector planned for semantic search and entity relationships
- Memory auto-summarization at token limit; /memory command uploads relevant files for LLM context
- dev_runtime_state.json + project_state.json auto-maintained for shared LLM context across sessions
- Hooks auto-commit on claude cli/cursor; aicli tracks own history; all tools share unified commit_log.jsonl
- GraphQL + node graph UI planned for workflow management and entity relationship visualization
- Cost tracking: per provider/user/date in PostgreSQL; pricing managed by config/JSON under ui/backend/data
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history files for cross-session project comprehension

## In Progress

- PostgreSQL table cleanup and consolidation — remove unused tables; clarify workflow vs flows distinction; align database schema with node-graph workflow execution model
- Hooks integration from claude cli — commits not auto-executing; history.jsonl captures prompts but missing responses; ensure commit_log.jsonl populated from all tools (claude cli, aicli, cursor)
- Balance persistence and refresh — manual balance entry saves but doesn't persist across UI refresh; admin dashboard not showing total balance; usage_logs table empty despite creation
- Multi-agent workflow execution — transition from YAML config to UI-managed node graphs; each node runs prompt with specified LLM engine and outputs score for conditional branching
- Shared memory strategy across tools — establish how claude cli, aicli, and cursor read/compress history files; determine how /memory command uploads relevant context for cross-session project understanding
- Project memory optimization — remove unused code files (e.g., hardcoded cost_tracker); consolidate QUICKSTART.md and README.md into single source-of-truth system files; clarify dev_runtime_state.json necessity

**[2026-03-08 05:29]** `claude_cli` — Dropped unused graph tables and removed graph-related code; consolidated database schema to focus on workflows/runs distinction. **[2026-03-08 05:15]** `claude_cli` — Clarified multi-agent workflow architecture: YAML-based node execution where each node runs a prompt with specified LLM, outputs score for conditional branching, and persists runs in _system/runs. **[2026-03-08 04:27]** `claude_cli` — Identified confusion between flows/workflows tables and entities tab; workflows should be primary UI with node-graph visualization planned; removed premature entities implementation. **[2026-03-08 03:14]** `claude_cli` — Proposed GraphQL + pgvector semantic embedding layer for project metadata (tasks, features, bugs) with node-graph UI for multi-agent workflow definition; enables cross-tool context injection via commit_log.jsonl. **[2026-03-08 02:51]** `claude_cli` — Diagnosed hooks not committing; history.jsonl captures prompts but missing responses; commit_log.jsonl not auto-populated from claude cli, aicli, cursor; requires unified hook implementation. **[2026-03-08 02:09]** `claude_cli` — Initiated code optimization: move hardcoded PRICING from cost_tracker to config/JSON under ui/backend/data; remove unused files; consolidate history folder redundancy in workspace structure.