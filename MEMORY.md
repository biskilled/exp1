# Project Memory — aicli
_Generated: 2026-03-08 23:23 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling seamless collaboration between multiple LLM tools (Claude CLI, aicli, Cursor) through unified history tracking, vectordb-powered semantic search, and multi-agent workflow orchestration. Currently focused on consolidating PostgreSQL schema, implementing pgvector embeddings for cross-session project comprehension, establishing mandatory metadata tagging to enforce memory consistency, and transitioning from YAML-based to UI-managed node graph workflows for agent-based prompt execution.

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
- **workflow_execution**: Node-based multi-agent model with YAML config and UI node graphs

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

- PostgreSQL schema optimization: consolidate unused tables (drop graph tables); clarify workflow vs flows distinction; align database schema with node-graph execution model
- Balance persistence and admin dashboard: manual balance entry saves but doesn't persist on refresh; admin dashboard must show total balance and per-user usage aggregation; refresh button on top-right corner
- Hooks integration and history tracking: ensure commit_log.jsonl populated from all tools (claude cli, aicli, cursor); capture both prompts and responses in history.jsonl; verify hooks auto-commit on claude cli
- Multi-agent workflow execution: transition from YAML config to UI-managed node graphs; each node with LLM engine selection and score-based branching; clarify workflow table usage vs flows tab
- AI knowledge layer architecture redesign: implement pgvector semantic embeddings for project metadata (tasks, features, bugs); add relational tagging for quick cross-session retrieval; enforce mandatory metadata keys across all CLI prompts
- Code consolidation and memory optimization: remove hardcoded cost_tracker pricing; clarify necessity of dev_runtime_state.json vs project_state.json; merge QUICKSTART.md and README.md; validate history folder vs _system folder usage

**2026-03-08 23:21** `claude_cli` — Proposed mandatory metadata tagging system for all prompts (project, lifecycle_stage, feature_area) to enable semantic search and enforce consistency across claude cli, aicli, and cursor for better memory continuity. **2026-03-08 23:08** `claude_cli` — Initiated architectural rethinking of AI knowledge layer using new pgvector instance with fresh PostgreSQL schema to support discovery, planning, tracking, and collaborative maintenance across project lifecycle. **2026-03-08 22:32** `claude_cli` — Began comprehensive rethinking of shared memory architecture after recognizing current solution insufficient for managing project memory over time; focusing on semantic embeddings and metadata-driven cross-tool collaboration. **2026-03-08 05:29** `claude_cli` — Completed cleanup: dropped all unused graph tables from PostgreSQL schema to align database with node-based workflow execution model (no graph ORM needed). **2026-03-08 05:15** `claude_cli` — Clarified multi-agent workflow architecture: nodes represent agent roles with prompts, LLM engine selection, and score-based conditional branching for sequential execution until user satisfaction. **2026-03-08 04:47** `claude_cli` — Consolidated workflow terminology: removed "flows" tab (duplicate of workflows); removed unused "entities" tab; established workflows as the single source of truth for multi-agent prompt orchestration. **2026-03-08 00:40** `claude_cli` — Discussed session memory retrieval mechanism: Claude uses compressed project history from previous sessions and history.jsonl to reconstruct full project context without reloading entire repository. **2026-03-08 00:30** `claude_cli` — Fixed balance persistence: balance now saved to PostgreSQL billing_logs table and refreshes on UI reload; admin dashboard displays total balance across all users and per-user usage. **2026-03-07 23:35** `claude_cli` — Confirmed both OpenAI and Claude provider APIs don't support automated balance/usage fetching for personal accounts (Claude requires org account, OpenAI returns zero); implemented manual balance entry UI as workaround. **2026-03-07 18:57** `claude_cli` — Designed user_usage table schema (user_id, date, llm_provider, api_key, balance, total_usage) to track per-provider costs by date and user for unified billing and admin dashboard aggregation.