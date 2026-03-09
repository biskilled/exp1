# Project Memory — aicli
_Generated: 2026-03-09 02:34 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling multiple LLM tools (claude-cli, cursor, aicli) to maintain unified project context through PostgreSQL with pgvector semantic embeddings, mandatory metadata tagging, and MCP server integration. Currently implementing auto-tag enforcement, smart chunking for semantic retrieval, and fixing chat history display to support full conversation recovery and cross-session memory sharing across discovery/development/production lifecycle phases.

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

- Chat history UI fix: restore full prompt/response pairs per session with proper LLM response display and per-prompt metadata visibility (2026-03-09 02:20)
- Auto-tag loop implementation: enforce aicli to assign minimum metadata keys (project, lifecycle_stage, feature_area); persist tags across multi-turn conversations; validate relational_tags table storage
- Smart chunking embedding feature: implement summary-level + per-class/method chunk generation; add metadata filters (language, file, feature, project_stage) for filtered semantic retrieval; test event emission for indexing
- MCP server deployment: build semantic embedding search endpoint for claude-cli, cursor, and aicli clients to query pgvector embeddings and commit_log.jsonl; enable cross-tool memory access
- PostgreSQL pgvector validation: confirmed PostgreSQL 15+ instance; created core tables (users, user_usage, usage_logs, billing_logs, workflows, relational_tags, embeddings); validated relational + vector capabilities
- UI billing/usage integration: fixed usage_logs table population; implemented manual balance entry with refresh indicator; ensured calculations refresh on balance updates

## Active Features / Bugs

- **[feature]** tagging `(6 events)`
- **[feature]** shared-memory `(1 events)`
- **[feature]** workflow-runner `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** auth `(0 events)`
- **[feature]** mcp `(0 events)`
- **[phase]** development `(6 events)`
- **[phase]** prod `(0 events)`
- **[phase]** discovery `(0 events)`

**2026-03-09 01:47** `claude_cli` — Auto-tag loop implementation initiated to enforce minimum metadata keys (project, lifecycle_stage, feature_area) on all aicli prompts, persisting across multi-turn conversations via relational_tags table linking commit_id to metadata.

**2026-03-09 00:56** `claude_cli` — Confirmed PostgreSQL 15+ instance with pgvector extension fully operational; all core tables created (users, user_usage, usage_logs, billing_logs, workflows, relational_tags, embeddings); relational and vector capabilities validated.

**2026-03-09 00:51** `claude_cli` — Reviewed implementation of smart chunking architecture (summary-level + per-class/method chunks with language/file/feature/project_stage metadata filters), MCP server semantic embedding search, and /memory command integration for cross-tool access.

**2026-03-09 01:58 – 02:03** `ui` — Smart chunking embedding feature tested on non-streaming endpoint with auto-tag suggestions; event emission for semantic indexing validated in brief testing.

**2026-03-09 02:20** `claude_cli` — Identified chat history UI regression: chat tab displaying only single prompt with incorrect LLM response instead of full session history with prompt/response pairs and per-prompt metadata.

**2026-03-08 23:52** `claude_cli` — Proposed relational tagging architecture: aicli enforces commit tagging with known keys (repo, project name, phase: discovery/development/prod, feature, bug); PostgreSQL relational_tags table stores commit_id-to-metadata mappings for lifecycle tracking.