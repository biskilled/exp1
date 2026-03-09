# Project Memory — aicli
_Generated: 2026-03-09 01:24 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling multiple LLM tools (claude cli, cursor, custom aicli) to maintain consistent project context across sessions via unified PostgreSQL + pgvector backend. It combines multi-agent workflows (node-based YAML configs), mandatory metadata tagging for lifecycle tracking, and an MCP server for semantic search across commits and embeddings.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron with xterm.js + Monaco editor
- **storage**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV
- **database**: PostgreSQL 15+ with pgvector extension + SQLAlchemy ORM
- **authentication**: JWT (python-jose) + bcrypt + dev_mode toggle
- **planned**: GraphQL, node graph UI for entity relationships and workflow composition, unified provider logging
- **orm**: SQLAlchemy
- **tables**: users, user_usage, usage_logs, billing_logs, workflows, relational_tags
- **vector_search**: pgvector for semantic embeddings and entity relationships
- **workflow_execution**: Node-based multi-agent model with YAML config transitioning to UI-managed node graphs
- **vector_db**: pgvector for semantic embeddings and entity relationships
- **integration**: MCP server for cross-tool integration

## Key Decisions

- Flat file storage (JSONL/JSON/CSV) for history tracking + PostgreSQL 15+ with pgvector for semantic search and entity relationships; no ChromaDB/SQLite
- Electron UI with xterm.js terminal + Monaco editor; Vanilla JS frontend (not Tauri)
- JWT auth via python-jose + bcrypt; dev_mode toggle for testing without login; three user roles (admin/paid/free)
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content, _system/ = project state
- All LLM providers independent; clients send own API keys in headers; no hardcoded pricing (config-driven)
- Multi-agent workflows via node-based execution model with YAML config transitioning to UI-managed node graphs; each node runs prompt with specified LLM engine and outputs score for conditional branching
- Manual balance entry in UI (provider APIs don't support automated fetching for personal accounts); admin sees aggregated total across all users; per-user balance visibility in dashboards
- PostgreSQL 15+ with SQLAlchemy ORM and pgvector extension for semantic embeddings and entity relationship search
- Memory auto-summarization at token limit; /memory command uploads relevant files for cross-session LLM context
- dev_runtime_state.json + project_state.json auto-maintained for shared LLM context across sessions
- Hooks auto-commit on claude cli/cursor; aicli tracks own history; all tools share unified commit_log.jsonl with all logs (prompts, responses, errors)
- Cost tracking per provider/user/date in PostgreSQL; pricing managed by config/JSON under ui/backend/data (not hardcoded)
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history files and vectordb for cross-session project comprehension
- Mandatory metadata tagging for prompts (project, lifecycle_stage, feature_area) enforced across all CLI tools; tags persist across conversation; relational tagging table links commit_id to metadata
- MCP server for cross-tool integration providing semantic embedding search across unified commit_log.jsonl and vectordb

## In Progress

- PostgreSQL pgvector validation and schema finalization: confirmed PostgreSQL 15+ instance with pgvector extension; created core tables (users, user_usage, usage_logs, billing_logs, workflows, relational_tags); removed unused graph tables; validated relational data and vector embedding capability
- Unified commit_log.jsonl population verification: ensure all logs (prompts, responses, errors) from claude cli hooks, aicli commits, and cursor hooks write to shared commit_log.jsonl; verify hooks auto-commit to git; validate history.jsonl captures both prompts and responses
- Code consolidation and cleanup: removed hardcoded cost_tracker pricing; consolidated duplicate history folder vs _system folder usage; removed unused graph/entity tables and related code; clarified dev_runtime_state.json necessity
- Mandatory metadata tagging system implementation: enforce minimum metadata keys (project, lifecycle_stage, feature_area) for every prompt via aicli; ensure tags persist across conversation; create relational tagging table linking commit_id to lifecycle_stage/feature_area/bug
- MCP server and smart chunking architecture: build MCP server for cross-tool memory access via vectordb semantic embeddings; implement smart chunking strategy for commits with metadata filtering (language, file, feature, project_stage) for quick retrieval
- Workflow schema and node-based execution model: restore multi-agent workflow support with YAML config; each node contains prompt (agent role) + LLM engine selection + output scoring for conditional branching

## Active Features / Bugs

- **[feature]** shared-memory `(1 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** workflow-runner `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** auth `(0 events)`
- **[feature]** mcp `(0 events)`
- **[feature]** tagging `(0 events)`
- **[phase]** development `(0 events)`
- **[phase]** discovery `(0 events)`
- **[phase]** prod `(0 events)`

**[2026-03-08 00:30]** `claude_cli` — Balance refresh mechanism implemented; admin sees total balance aggregated across all users; per-user balance visible in user dashboard; all changes persist across page refresh.

**[2026-03-08 02:09]** `claude_cli` — Code optimization initiative: removed hardcoded pricing from cost_tracker (now config-driven via ui/backend/data); consolidated _system vs history folder structure; eliminated unused graph tables and related code.

**[2026-03-08 03:14]** `claude_cli` — Architectural pivot to PostgreSQL + pgvector: semantic embeddings for project comprehension, relational tagging for metadata (tasks, features, bugs), node graph UI for workflow/entity relationships, cross-tool memory sharing via MCP.

**[2026-03-08 04:05]** `claude_cli` — Unified commit_log.jsonl enforcement: all logs (prompts, responses, errors) from claude cli hooks, aicli commits, and cursor hooks must write to single shared file; became core dependency for shared memory.

**[2026-03-08 23:52]** `claude_cli` — Mandatory metadata tagging design: aicli enforces minimum tags (project, phase/lifecycle_stage, feature_area/bug); tags immutable until user changes; relational table links commit_id to metadata for lifecycle tracking (discovery→development→prod).

**[2026-03-09 00:51]** `claude_cli` — Implementation review of MCP server, smart chunking strategy, and metadata/embedding architecture; confirmed PostgreSQL pgvector compatibility; ready to build cross-tool memory layer for claude cli, aicli, and cursor.