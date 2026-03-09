# Project Memory — aicli
_Generated: 2026-03-09 02:03 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform enabling cross-tool collaboration (Claude CLI, Cursor, aicli client) to maintain unified project context through semantic embeddings, metadata tagging, and multi-agent workflows. Currently implementing PostgreSQL pgvector integration with smart chunking, auto-tag enforcement, and MCP server for seamless memory sharing across sessions and different LLM providers.

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
- Multi-agent workflows via node-based execution model with YAML config; each node runs prompt with specified LLM engine and outputs score for conditional branching
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
- PostgreSQL pgvector validation and table cleanup: confirmed PostgreSQL 15+ instance; created core tables (users, user_usage, usage_logs, billing_logs, workflows, relational_tags, embeddings); removed unused tables; validated relational + vector capability
- UI billing/usage integration: fixed usage_logs table population from UI; implemented manual balance entry; added refresh indicator; ensured all calculations refresh correctly on balance updates
- Smart chunking embedding feature: testing auto-tag suggestions on non-streaming endpoint; event emission for semantic search indexing

## Active Features / Bugs

- **[feature]** tagging `(2 events)`
- **[feature]** shared-memory `(1 events)`
- **[feature]** workflow-runner `(0 events)`
- **[feature]** embeddings `(0 events)`
- **[feature]** graph-workflow `(0 events)`
- **[feature]** billing `(0 events)`
- **[feature]** auth `(0 events)`
- **[feature]** mcp `(0 events)`
- **[phase]** development `(2 events)`
- **[phase]** prod `(0 events)`
- **[phase]** discovery `(0 events)`

**[2026-03-08 00:11]** `claude_cli` — Usage/billing UI issues resolved: fixed balance save indicator, removed broken delete functionality from fetch history, corrected error handling for updates.
**[2026-03-08 00:30]** `claude_cli` — Balance persistence fixed; implemented refresh-on-change for all calculations across usage, billing, and users tabs; admin sees aggregated total across all users.
**[2026-03-08 02:29]** `claude_cli` — Clarified workspace structure: _system/ holds project state (single history.jsonl per project), removed duplicate history folders, deprecated dev_runtime_state.json; cost_tracker hardcoded pricing migrated to config-driven JSON.
**[2026-03-08 04:27]** `claude_cli` — PostgreSQL pgvector instance verified and core tables created (users, user_usage, usage_logs, billing_logs, workflows, relational_tags, embeddings); removed unused tables; validated relational + vector capability.
**[2026-03-08 05:29]** `claude_cli` — Cleaned up unused graph/entity tables; confirmed multi-agent workflow architecture: node-based execution with YAML config, each node has prompt/LLM/scoring for conditional branching.
**[2026-03-09 00:35]** `claude_cli` — MCP server, smart chunking, and auto-tag loop approved for implementation; PostgreSQL 15+ with pgvector ready; metadata relational_tags table and embedding table configured for semantic search across commit_log.jsonl.
**[2026-03-09 01:47]** `claude_cli` — Started auto-tag loop Step 1: aicli to enforce minimum metadata keys (project, lifecycle_stage, feature_area); relational_tags links commit_id to tags; /memory command to upload relevant context for cross-session LLM access.
**[2026-03-09 01:58]** `ui` — Smart chunking embedding feature initiated: discussion on semantic boundary preservation, context retention, chunk sizing for embedding models, handling multi-language code.
**[2026-03-09 02:01]** `ui` — Auto-tag suggestion endpoint tested on non-streaming; event emission framework validated for semantic indexing.
**[2026-03-09 02:03]** `ui` — Event emission test suite confirmed working for data payload emission and listener binding.