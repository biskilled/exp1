# Project Memory — aicli
_Generated: 2026-03-09 01:22 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling claude cli, aicli CLI, and cursor to collaborate seamlessly across projects by maintaining unified commit logs, semantic vector embeddings, and metadata-tagged workflows in PostgreSQL with pgvector. Currently implementing mandatory metadata tagging, MCP server integration for cross-tool memory access, and multi-agent workflow execution via node-based UI to create a persistent knowledge layer that improves project comprehension and continuity across AI tools and development sessions.

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

- PostgreSQL pgvector validation and schema finalization: confirmed PostgreSQL 15+ instance with pgvector extension; created core tables (users, user_usage, usage_logs, billing_logs, workflows, relational_tags); dropped unused graph tables; validated relational data and vector embedding capability for semantic search
- Balance management UI completion: implemented manual balance entry in Usage tab; fixed balance display in top-right corner with refresh button; admin dashboard aggregates total balance across all users and API keys; per-user balance visibility in user dashboard
- Unified commit_log.jsonl population verification: ensure all logs (prompts, responses, errors) from claude cli hooks, aicli commits, and cursor hooks write to shared commit_log.jsonl; verify hooks auto-commit to git; validate history.jsonl captures both prompts and responses
- Code consolidation and cleanup: removed hardcoded cost_tracker pricing; consolidated duplicate history folder vs _system folder usage; removed unused graph/entity tables and related code; clarified dev_runtime_state.json necessity
- Mandatory metadata tagging system implementation: enforce minimum metadata keys (project, lifecycle_stage, feature_area) for every prompt via aicli; ensure tags persist across conversation; create relational tagging table linking commit_id to lifecycle_stage/feature_area/bug
- MCP server and smart chunking architecture: build MCP server for cross-tool memory access via vectordb semantic embeddings; implement smart chunking strategy for commits with metadata filtering (language, file, feature, project_stage) for quick retrieval by claude cli, aicli, and cursor

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

**[2026-03-07 18:20–19:24]** `claude_cli` — User requested balance display in top-right corner next to online status with refresh button; implemented for admin to see total across all API keys and per-user balance in dashboards.
**[2026-03-07 21:15–23:54]** `claude_cli` — Investigated automated balance fetching from OpenAI and Claude APIs; both failed (Claude requires org account, OpenAI returned zero). Decided to implement manual balance entry in UI instead of automated fetch.
**[2026-03-08 00:11–00:30]** `claude_cli` — Fixed Usage tab update error and Billing tab delete functionality; balance now persists on refresh and users tab shows updated total balance across all recalculations.
**[2026-03-08 00:40–02:51]** `claude_cli` — Discussed shared memory architecture: recognized all sessions written to .aicli/provider_usage; identified need for vectordb integration to enable cross-session project comprehension for claude cli, aicli, and cursor.
**[2026-03-08 02:09–04:27]** `claude_cli` — Optimized code by removing hardcoded cost_tracker pricing (moved to config-driven JSON), consolidated history folder duplication with _system folder, dropped unused graph tables, and clarified dev_runtime_state.json necessity for shared LLM context.
**[2026-03-08 23:21–01:06]** `claude_cli` — Designed mandatory metadata tagging system (project, lifecycle_stage, feature_area) enforced by aicli with persistence across conversation; created PostgreSQL schema with relational_tags table; validated pgvector-enabled instance; implemented MCP server architecture for smart chunking and cross-tool semantic search.