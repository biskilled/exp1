# Project Memory — aicli
_Generated: 2026-03-09 03:24 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling seamless context preservation across claude-cli, cursor, and aicli clients through PostgreSQL pgvector embeddings, relational tagging, and unified commit logging. Currently stabilizing chat history UI, auto-tagging enforcement, and MCP server integration to unlock full cross-tool semantic search and multi-agent workflow capabilities.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron with xterm.js + Monaco editor
- **storage**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV
- **database**: PostgreSQL 15+ with pgvector extension + SQLAlchemy ORM
- **authentication**: JWT (python-jose) + bcrypt + dev_mode toggle
- **planned**: GraphQL, node graph UI for entity relationships and workflow composition, unified provider logging
- **orm**: SQLAlchemy
- **tables**: users, user_usage, usage_logs, billing_logs, workflows, relational_tags, embeddings
- **vector_search**: pgvector for semantic embeddings and entity relationships
- **workflow_execution**: Node-based multi-agent model with YAML config transitioning to UI-managed node graphs
- **vector_db**: pgvector for semantic embeddings and entity relationships
- **integration**: MCP server for cross-tool integration with semantic search
- **ui_framework**: Node.js with event emission for semantic indexing

## Key Decisions

- Flat file storage (JSONL/JSON/CSV) for history tracking + PostgreSQL 15+ with pgvector for semantic search and entity relationships; no ChromaDB/SQLite
- Electron UI with xterm.js terminal + Monaco editor; Vanilla JS frontend (not Tauri)
- JWT auth via python-jose + bcrypt; dev_mode toggle for testing without login; three user roles (admin/paid/free)
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content, _system/ = project state; single history.jsonl per project (no duplicate history folders)
- All LLM providers independent; clients send own API keys in headers; no hardcoded pricing (config-driven via ui/backend/data JSON)
- Multi-agent workflows via node-based execution model with YAML config; each node runs prompt with specified LLM engine and outputs score for conditional branching
- Manual balance entry in UI; admin sees aggregated total across all users; per-user balance visibility with refresh indicator
- PostgreSQL 15+ with SQLAlchemy ORM and pgvector extension for semantic embeddings and entity relationship search
- Memory auto-summarization at token limit; /memory command uploads relevant files for cross-session LLM context
- Hooks auto-commit on claude cli/cursor; aicli tracks own history; unified commit_log.jsonl with all logs (prompts, responses, errors)
- Cost tracking per provider/user/date in PostgreSQL; pricing managed by config/JSON (not hardcoded)
- Mandatory metadata tagging for prompts (project, lifecycle_stage, feature_area) enforced via aicli; tags persist across conversation; relational_tags table links commit_id to metadata
- Smart chunking strategy for commits: summary-level + per-class/method chunks with metadata filters (language, file, feature, project_stage) for semantic retrieval
- MCP server for cross-tool integration providing semantic embedding search across unified commit_log.jsonl and pgvector vectordb
- project_state.json auto-maintained for shared LLM context across sessions; dev_runtime_state.json deprecated

## In Progress

- Chat history UI fix: restore full prompt/response pairs per session with proper LLM response display and per-prompt metadata visibility; fix claude cli hooks to capture responses not just prompts (2026-03-09 02:20, 03:02)
- Auto-tag loop implementation: enforce aicli to assign minimum metadata keys (project, lifecycle_stage, feature_area); implement + UI option for tag selection (feature/bug/task) with dropdown lists; persist tags across multi-turn conversations
- Smart chunking embedding feature: implement summary-level + per-class/method chunk generation; add metadata filters (language, file, feature, project_stage) for filtered semantic retrieval; test event emission for indexing
- MCP server deployment: build semantic embedding search endpoint for claude-cli, cursor, and aicli clients to query pgvector embeddings and commit_log.jsonl; enable cross-tool memory access
- PostgreSQL pgvector validation: confirmed PostgreSQL 15+ instance with pgvector extension; created core tables (users, user_usage, usage_logs, billing_logs, workflows, relational_tags, embeddings); validated relational + vector capabilities
- UI billing/usage integration: fixed usage_logs table population; implemented manual balance entry with refresh indicator; ensured calculations refresh on balance updates; fixed seed defaults for entity categories

## Active Features / Bugs

- **[feature]** tagging `(6 events)`
- **[feature]** shared-memory `(1 events)`
- **[feature]** workflow-runner `(0 events)`
- **[feature]** test-picker-feature `(0 events)`
- **[feature]** mcp `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** auth `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[phase]** development `(6 events)`
- **[phase]** prod `(0 events)`
- **[phase]** discovery `(0 events)`

**2026-03-09 03:02** `claude_cli` — Chat history UI broken: prompts show without LLM responses from claude cli hooks; tag addition UI needs dropdown UI (feature/bug/task selector with existing value lists). **2026-03-09 02:20** `claude_cli` — Identified chat history regression: full prompt/response pairs not displaying; per-prompt metadata visibility required. **2026-03-09 01:47** `claude_cli` — Auto-tag loop implementation prioritized: aicli to enforce metadata keys (project, lifecycle_stage, feature_area) with per-project server-side storage model. **2026-03-09 01:32** `claude_cli` — Summarized new PostgreSQL pgvector architecture: hooks still write local JSONL files; /memory command aggregates and injects into vectordb via relational tagging. **2026-03-09 00:51** `claude_cli` — Validated PostgreSQL 15+ pgvector setup: MCP server, smart chunking (summary + per-class/method with language/file/feature/stage filters), and relational_tags linking commit_id to metadata all confirmed for implementation.