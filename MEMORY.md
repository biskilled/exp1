# Project Memory — aicli
_Generated: 2026-03-09 01:33 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling seamless context sharing across multiple LLM interfaces (claude-cli, aicli CLI, Cursor) within a project. It uses PostgreSQL 15+ with pgvector for semantic embeddings, mandatory metadata tagging (project/lifecycle_stage/feature_area), and multi-agent workflows with node-based execution. Current focus: finalizing pgvector schema, implementing MCP server for cross-tool memory access, consolidating commit logging, and validating smart chunking architecture for fast semantic retrieval.

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

## Key Decisions

- Flat file storage (JSONL/JSON/CSV) for history tracking + PostgreSQL 15+ with pgvector for semantic search and entity relationships; no ChromaDB/SQLite
- Electron UI with xterm.js terminal + Monaco editor; Vanilla JS frontend (not Tauri)
- JWT auth via python-jose + bcrypt; dev_mode toggle for testing without login; three user roles (admin/paid/free)
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content, _system/ = project state; single history.jsonl per project (no duplicate history folders)
- All LLM providers independent; clients send own API keys in headers; no hardcoded pricing (config-driven via ui/backend/data JSON)
- Multi-agent workflows via node-based execution model with YAML config transitioning to UI-managed node graphs; each node runs prompt with specified LLM engine and outputs score for conditional branching
- Manual balance entry in UI (provider APIs don't support automated fetching for personal accounts); admin sees aggregated total across all users; per-user balance visibility in dashboards with refresh indicator
- PostgreSQL 15+ with SQLAlchemy ORM and pgvector extension for semantic embeddings and entity relationship search
- Memory auto-summarization at token limit; /memory command uploads relevant files for cross-session LLM context
- dev_runtime_state.json necessity deprecated; project_state.json auto-maintained for shared LLM context across sessions
- Hooks auto-commit on claude cli/cursor; aicli tracks own history; all tools share unified commit_log.jsonl with all logs (prompts, responses, errors)
- Cost tracking per provider/user/date in PostgreSQL; pricing managed by config/JSON under ui/backend/data (not hardcoded)
- Mandatory metadata tagging for prompts (project, lifecycle_stage, feature_area) enforced via aicli; tags persist across conversation; relational_tags table links commit_id to metadata
- Smart chunking strategy for commits: summary-level + per-class/method chunks with metadata filters (language, file, feature, project_stage) for semantic retrieval
- MCP server for cross-tool integration providing semantic embedding search across unified commit_log.jsonl and pgvector vectordb

## In Progress

- PostgreSQL pgvector validation and schema finalization: confirmed PostgreSQL 15+ instance with pgvector extension; created core tables (users, user_usage, usage_logs, billing_logs, workflows, relational_tags); removed unused graph/entity tables; validated relational data and vector embedding capability
- Unified commit_log.jsonl population verification: ensure all logs (prompts, responses, errors) from claude cli hooks, aicli commits, and cursor hooks write to shared commit_log.jsonl; verify hooks auto-commit to git; validate history.jsonl captures both prompts and responses
- Code consolidation and cleanup: removed hardcoded cost_tracker pricing; consolidated duplicate history folder vs _system folder usage; removed unused graph/entity tables and related code; clarified dev_runtime_state.json is deprecated
- Mandatory metadata tagging system implementation: enforce minimum metadata keys (project, lifecycle_stage, feature_area) for every prompt via aicli; ensure tags persist across conversation; create relational_tags table linking commit_id to lifecycle_stage/feature_area/bug
- MCP server and smart chunking architecture: build MCP server for cross-tool memory access via pgvector semantic embeddings; implement smart chunking strategy (summary + per-class/method) with metadata filtering for quick retrieval by claude-cli, aicli, cursor
- Workflow schema and node-based execution model: restore multi-agent workflow support with YAML config; each node contains prompt (agent role) + LLM engine selection + output scoring for conditional branching; validate schema against postgres workflows table

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

**2026-03-07 18:40–19:24** `claude_cli` — Identified balance display issues: moved balance to top status bar, added per-API balance visibility for admin users, created users_usage table schema (date, user_id, llm, api_key, balance, usage).

**2026-03-07 21:15–23:35** `claude_cli` — Attempted automated billing tracker via OpenAI/Anthropic usage APIs; both failed (400/404 errors). Anthropic personal accounts don't support API calls; OpenAI returned zero usage. Switched to manual balance entry in UI as preferred solution.

**2026-03-07 23:54–00:30** `claude_cli` — Consolidated balance management into usage page; fixed refresh indicator for balance updates; fixed delete functionality in Fetch History table to remove rows from JSON config files; improved error handling for balance updates and user-visible calculations.

**2026-03-08 00:44–01:30** `claude_cli` — Discussed core project goal: shared LLM memory across claude-cli, aicli, cursor via unified commit_log.jsonl and vectordb. Initiated code optimization: removed hardcoded cost_tracker pricing (move to config), clarified history folder consolidation (single _system/history.jsonl sufficient), validated hook auto-commit functionality.

**2026-03-08 03:14–04:47** `claude_cli` — Designed PostgreSQL+pgvector architecture with relational_tags table for metadata (project, lifecycle_stage, feature_area, bug). Planned multi-agent workflows via node graph UI replacing YAML. Removed unused graph/entity tables; confirmed workflows table structure for node-based execution (prompt + LLM engine + output scoring).

**2026-03-08 22:32–01:06** `claude_cli` — Finalized PostgreSQL pgvector instance; validated core schema (users, user_usage, usage_logs, billing_logs, workflows, relational_tags, embeddings). Implemented mandatory metadata tagging enforcement via aicli. Designed MCP server with smart chunking (summary-level + per-class/method chunks) using metadata filters (language, file, feature, project_stage) for semantic retrieval across claude-cli, aicli, cursor.