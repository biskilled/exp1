# Project Memory — aicli
_Generated: 2026-03-09 01:56 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling multiple LLM tools (claude-cli, cursor, aicli) to maintain unified context across development sessions via PostgreSQL+pgvector semantic search, JSONL history logs, and mandatory metadata tagging. The project uses node-based multi-agent workflows, JWT authentication with provider-agnostic API key management, and an MCP server for cross-tool memory access. Current focus is implementing auto-tag loops to enforce metadata capture, deploying semantic chunking for smart retrieval, and validating the pgvector infrastructure for relational entity search.

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
- Manual balance entry in UI (provider APIs don't support automated fetching for personal accounts); admin sees aggregated total across all users; per-user balance visibility with refresh indicator
- PostgreSQL 15+ with SQLAlchemy ORM and pgvector extension for semantic embeddings and entity relationship search
- Memory auto-summarization at token limit; /memory command uploads relevant files for cross-session LLM context
- Hooks auto-commit on claude cli/cursor; aicli tracks own history; all tools share unified commit_log.jsonl with all logs (prompts, responses, errors)
- Cost tracking per provider/user/date in PostgreSQL; pricing managed by config/JSON under ui/backend/data (not hardcoded)
- Mandatory metadata tagging for prompts (project, lifecycle_stage, feature_area) enforced via aicli; tags persist across conversation; relational_tags table links commit_id to metadata
- Smart chunking strategy for commits: summary-level + per-class/method chunks with metadata filters (language, file, feature, project_stage) for semantic retrieval
- MCP server for cross-tool integration providing semantic embedding search across unified commit_log.jsonl and pgvector vectordb
- project_state.json auto-maintained for shared LLM context across sessions; dev_runtime_state.json deprecated

## In Progress

- Auto-tag loop implementation: enforce aicli to assign minimum metadata keys (project, lifecycle_stage, feature_area) to every prompt; ensure tags persist across multi-turn conversations; validate relational_tags table stores commit_id→metadata links
- MCP server deployment: build semantic embedding search endpoint for claude-cli, cursor, and aicli clients to query pgvector embeddings and commit_log.jsonl; enable cross-tool memory access via /memory command
- Smart chunking architecture: implement summary-level + per-class/method chunk generation for commits; add metadata filters (language, file, feature, project_stage) to support filtered semantic retrieval
- Multi-agent workflow schema restoration: restore YAML-based workflow definitions with node-based execution; each node contains agent role prompt + LLM engine selection + output scoring for conditional branching
- PostgreSQL pgvector validation and table cleanup: confirmed PostgreSQL 15+ instance; created core tables (users, user_usage, usage_logs, billing_logs, workflows, relational_tags, embeddings); removed unused tables; validated relational + vector capability
- UI billing/usage integration: fixed usage_logs table population from UI; implemented manual balance entry; added refresh indicator; ensured all calculations refresh correctly on balance updates

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

**[2026-03-07 to 2026-03-08 00:40]** `claude_cli` — Fixed UI billing/usage integration: implemented manual balance entry (API provider fetching not viable for personal accounts), added refresh indicator, ensured row deletion works in fetch history, and verified all calculations refresh correctly on data updates. **[2026-03-08 00:40 to 00:53]** `claude_cli` — Established unified memory architecture: all sessions logged to commit_log.jsonl via hooks (claude cli, aicli, cursor); identified pgvector + relational tagging as core solution for shared LLM memory across tools. **[2026-03-08 22:32 to 23:52]** `claude_cli` — Designed auto-tag loop enforcement: aicli enforces minimum metadata keys (project, lifecycle_stage, feature_area) on every prompt; tags persist across multi-turn conversations; relational_tags table links commit_id to metadata for semantic retrieval. **[2026-03-09 00:14 to 00:51]** `claude_cli` — Validated PostgreSQL 15+ pgvector instance; created core tables (users, user_usage, usage_logs, billing_logs, workflows, relational_tags, embeddings); removed unused graph/entity tables; confirmed relational + vector capability ready. **[2026-03-09 00:51 to 01:06]** `claude_cli` — Reviewed smart chunking architecture: summary-level + per-class/method chunks with metadata filters (language, file, feature, project_stage) for filtered semantic retrieval; MCP server deployment for cross-tool memory access via /memory command. **[2026-03-09 01:32 to 01:47]** `claude_cli` — Clarified multi-user project memory: aicli server-side hosting with per-project data storage; /memory command aggregates all files for LLM context; hooks continue writing to local JSONL; step 1 (auto-tag loop) prioritized for implementation.