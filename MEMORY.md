# Project Memory — aicli
_Generated: 2026-03-08 23:10 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling multi-tool collaboration (claude cli, aicli, cursor) through unified history tracking, cost management, and multi-agent workflow orchestration. Current focus: implementing pgvector semantic search in PostgreSQL for cross-session project comprehension, consolidating database schema, fixing hooks to properly populate commit_log.jsonl from all tools, and transitioning workflow management from YAML config to UI-managed node graphs with visual entity relationship representation.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron with xterm.js + Monaco editor
- **storage**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV
- **database**: PostgreSQL with pgvector + SQLAlchemy ORM
- **authentication**: JWT (python-jose) + bcrypt + dev_mode toggle
- **planned**: GraphQL, node graph UI, pgvector semantic embeddings, unified provider logging
- **orm**: SQLAlchemy
- **tables**: users, user_usage, usage_logs, billing_logs, workflows, runs, entities (pending consolidation)

## Key Decisions

- Flat file storage (JSONL/JSON/CSV) for history tracking + PostgreSQL with pgvector for semantic search and entity relationships; no ChromaDB/SQLite
- Electron UI with xterm.js terminal + Monaco editor; Vanilla JS frontend (not Tauri)
- JWT auth via python-jose + bcrypt; dev_mode toggle for testing without login; three user roles (admin/paid/free)
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content, _system/ = project state
- All LLM providers independent; clients send own API keys in headers; no hardcoded pricing (config-driven)
- Multi-agent workflows via node-based execution model with YAML config transitioning to UI-managed node graphs; each node runs prompt with specified LLM engine and outputs score for conditional branching
- Unified history.jsonl + commit_log.jsonl shared across claude cli, aicli, cursor via hooks and commits
- Manual balance entry in UI (provider APIs don't support automated fetching for personal accounts); admin sees aggregated total across all users
- PostgreSQL with SQLAlchemy ORM; pgvector for semantic embeddings and entity relationship search
- Memory auto-summarization at token limit; /memory command uploads relevant files for cross-session LLM context
- dev_runtime_state.json + project_state.json auto-maintained for shared LLM context across sessions
- Hooks auto-commit on claude cli/cursor; aicli tracks own history; all tools share unified commit_log.jsonl
- GraphQL + node graph UI planned for workflow management and visual entity relationship representation
- Cost tracking per provider/user/date in PostgreSQL; pricing managed by config/JSON under ui/backend/data (not hardcoded)
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history files and vectordb for cross-session project comprehension

## In Progress

- PostgreSQL schema optimization: consolidate unused tables; clarify workflow vs flows distinction; align database schema with node-graph execution model
- Hooks integration and history tracking: ensure commit_log.jsonl populated from all tools (claude cli, aicli, cursor); capture both prompts and responses in history.jsonl
- Balance persistence and admin dashboard: manual balance entry saves but doesn't persist on refresh; admin dashboard must show total balance and per-user usage aggregation
- Multi-agent workflow execution: transition from YAML config to UI-managed node graphs; each node execution with LLM engine selection and score-based branching
- Pgvector semantic search and entity relationships: implement PostgreSQL vector storage for project metadata (tasks, features, bugs); add relational tagging for quick cross-session retrieval
- Project memory optimization and code consolidation: remove hardcoded cost_tracker with pricing; consolidate QUICKSTART.md and README.md; clarify necessity of dev_runtime_state.json

**2026-03-08 23:08** `claude_cli` — Decided to create new PostgreSQL instance with pgvector for unified semantic search across project history, aiming to improve cross-session memory sharing for claude cli, aicli, and cursor; focuses on maintaining project lifecycle (discovery, planning, tracking).

**2026-03-08 22:32** `claude_cli` — Proposed rethinking AI knowledge layer architecture for better memory sharing and project management; planning pgvector-based semantic embeddings with relational tagging for quick entity/task retrieval across tools.

**2026-03-08 05:29** `claude_cli` — Completed cleanup: removed unused graph tables and graph code; streamlined database schema to align with workflow/node-graph execution model.

**2026-03-08 05:10** `claude_cli` — Identified schema bloat in PostgreSQL; requested removal of unused tables created during prior changes; clarified that workflows should support multi-agent YAML-configured nodes transitioning to UI-managed node graphs.

**2026-03-08 04:47** `claude_cli` — Clarified workflow execution model: nodes contain prompts with LLM engine assignment (e.g., QA using OpenAI); output score enables conditional branching; workflows managed via YAML config transitioning to node-graph UI; removed unused entities/flows tabs.

**2026-03-08 02:51** `claude_cli` — Identified critical issues: hooks not auto-committing to git; history.jsonl captures prompts but not responses; commit_log.jsonl not populated from all tools; requested consolidation of history tracking across claude cli, aicli, cursor hooks.