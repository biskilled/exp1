# Project Memory — aicli
_Generated: 2026-03-08 23:52 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform designed to enable seamless context sharing across multiple LLM tools (claude-cli, aicli, cursor) within a single project workspace. It combines PostgreSQL with pgvector for semantic embeddings, multi-agent workflow execution via node-based YAML/UI configs, and mandatory metadata tagging to maintain project comprehension across discovery, development, and production lifecycle phases. Current work focuses on schema optimization, balance persistence in the admin dashboard, hooks integration for unified history tracking, and implementing pgvector-backed semantic search to help any LLM quickly understand project state and make informed decisions.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron with xterm.js + Monaco editor
- **storage**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV
- **database**: PostgreSQL with pgvector + SQLAlchemy ORM
- **authentication**: JWT (python-jose) + bcrypt + dev_mode toggle
- **planned**: GraphQL, node graph UI, pgvector semantic embeddings, unified provider logging
- **orm**: SQLAlchemy
- **tables**: users, user_usage, usage_logs, billing_logs, workflows, runs (graph tables dropped)
- **vector_search**: pgvector for semantic embeddings and entity relationships
- **workflow_execution**: Node-based multi-agent model with YAML config transitioning to UI-managed node graphs
- **vector_db**: pgvector for semantic embeddings and entity relationships

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
- Cost tracking per provider/user/date in PostgreSQL; pricing managed by config/JSON under ui/backend/data (not hardcoded)
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history files and vectordb for cross-session project comprehension
- Mandatory metadata tagging for prompts (project, lifecycle_stage, feature_area) enforced across all CLI tools to enable semantic search and memory continuity

## In Progress

- PostgreSQL schema cleanup: drop unused graph tables; consolidate workflows vs flows distinction; align database schema with node-graph execution model for multi-agent workflows
- Balance persistence and admin dashboard: fix balance refresh on top-right corner; ensure admin sees total balance aggregated across all users; per-user balance visibility in user dashboard
- Hooks integration and history tracking: populate commit_log.jsonl from all tools (claude cli, aicli, cursor); capture both prompts and responses in history.jsonl; verify auto-commit on claude cli works
- Mandatory metadata tagging system: force claude-cli and cursor to attach minimum metadata keys (project, lifecycle_stage, feature_area) to every prompt; ensure tags persist across conversation
- PostgreSQL pgvector implementation: create semantic embedding schema for project metadata (tasks, features, bugs); add relational tagging table linking commit_id to lifecycle_stage/feature_area; validate approach improves cross-tool project comprehension
- Code consolidation: remove hardcoded cost_tracker pricing; clarify dev_runtime_state.json vs project_state.json necessity; consolidate history folder vs _system folder usage; merge QUICKSTART.md and README.md

**[2026-03-08 05:29]** `claude_cli` — Dropped unused graph tables from PostgreSQL; consolidated database schema to remove duplicate/abandoned entities table and clarify workflows vs flows distinction. **[2026-03-08 23:52]** `claude_cli` — Designed mandatory metadata tagging system where commits attach project, lifecycle_stage (discovery/development/prod), and feature_area tags; tags persist across responses to enable semantic search and memory continuity. **[2026-03-08 23:21]** `claude_cli` — Decided to implement pgvector semantic embeddings in new PostgreSQL instance with relational tagging tables to help claude-cli, aicli, and cursor maintain cross-tool project comprehension across lifecycle phases. **[2026-03-08 22:32]** `claude_cli` — Rethought AI knowledge layer architecture from file-based history to structured semantic layer; pgvector will index project metadata (tasks, features, bugs) with lifecycle_stage and feature_area tags for rapid cross-session retrieval. **[2026-03-08 00:30]** `claude_cli` — Identified balance persistence bug on refresh; admin dashboard must aggregate total balance across all users and show per-user usage; balance manual entry works but doesn't survive page reload. **[2026-03-08 02:51]** `claude_cli` — Detected hooks not triggering git commits from claude-cli; history.jsonl only captures prompts, not responses; identified missing unified commit_log.jsonl population from all tools (claude-cli, aicli, cursor).