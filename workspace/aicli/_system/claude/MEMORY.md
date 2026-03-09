# Project Memory — aicli
_Generated: 2026-03-09 00:31 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform designed to enable seamless context sharing across multiple LLM tools (claude cli, aicli, cursor) for collaborative AI-assisted development. It combines PostgreSQL with pgvector semantic search, unified commit/history logging, multi-agent workflow execution via node-based YAML configs, and mandatory metadata tagging (project/lifecycle_stage/feature_area) to maintain project comprehension across sessions. The platform is transitioning from flat-file history tracking to a sophisticated knowledge graph architecture with relational tagging to support discovery → planning → development → production lifecycle management for multiple concurrent projects.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron with xterm.js + Monaco editor
- **storage**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV
- **database**: PostgreSQL 15+ with pgvector extension + SQLAlchemy ORM
- **authentication**: JWT (python-jose) + bcrypt + dev_mode toggle
- **planned**: GraphQL, node graph UI, pgvector semantic embeddings, unified provider logging
- **orm**: SQLAlchemy
- **tables**: users, user_usage, usage_logs, billing_logs, workflows, relational_tags
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

- PostgreSQL pgvector schema creation and validation: set up new PostgreSQL instance with pgvector extension; create users, usage_logs, billing_logs, workflows tables; drop unused graph tables; validate relational data and vector embedding capability
- Mandatory metadata tagging system: force claude-cli and cursor to attach minimum metadata keys (project, lifecycle_stage, feature_area) to every prompt; ensure tags persist across conversation; create relational tagging table linking commit_id to lifecycle_stage/feature_area/bug
- Unified commit_log.jsonl population: ensure all logs (prompts, responses, errors) from claude cli hooks, aicli commits, and cursor hooks write to shared commit_log.jsonl; verify history.jsonl captures both prompts and responses
- Balance persistence and refresh logic: fix top-right corner balance refresh; ensure admin dashboard aggregates total balance across all users and all API keys; per-user balance visibility in user dashboard and API key management screen
- Hook integration debugging: verify claude cli hooks are auto-committing to git; ensure aicli tracks history properly; consolidate history folder vs _system folder usage to eliminate duplication
- Code consolidation and cleanup: remove hardcoded cost_tracker pricing; clarify dev_runtime_state.json vs project_state.json necessity; merge QUICKSTART.md and README.md documentation

**[2026-03-08 23:52]** `claude_cli` — Decided to implement mandatory metadata tagging system where every prompt from claude-cli/cursor must include project, lifecycle_stage (discovery/development/prod), and feature_area tags; tags persist until explicitly changed. Each commit_id links to tagging metadata in PostgreSQL relational table.

**[2026-03-08 23:21]** `claude_cli` — Confirmed metadata tagging approach: enforce minimum keys (project, phase, feature) to be attached by aicli to every prompt; store tag mappings in PostgreSQL with commit_id as foreign key for relational querying.

**[2026-03-08 23:08]** `claude_cli` — Validated that new PostgreSQL with pgvector instance will support shared memory across claude cli, aicli, and cursor for project lifecycle management (discovery → planning → tracking → creation).

**[2026-03-08 22:32]** `claude_cli` — Initiated AI knowledge layer rethinking: pgvector-based semantic search with relational tagging to improve memory sharing and project comprehension across multiple LLM tools and sessions.

**[2026-03-08 05:29]** `claude_cli` — Completed schema cleanup: dropped all unused graph tables; consolidated workflows vs flows distinction; aligned database schema with node-graph execution model for multi-agent workflows.

**[2026-03-08 05:06]** `claude_cli` — Clarified workflow architecture: multi-agent flows built with YAML config and simple nodes; each node contains a prompt as agent role with specified LLM; nodes execute conditionally based on output scores until user advances to next node.

**[2026-03-08 04:47]** `claude_cli` — Resolved table confusion: workflows table manages multi-agent flows where each node uses a prompt with LLM engine selection (e.g., QA via OpenAI) and output score for conditional branching; removed unused flows and entities tabs.

**[2026-03-08 04:13]** `claude_cli` — Clarified memory improvement strategy: PROJECT.md and summary files updated via compressed session history; /memory command uploads all relevant files; commit_log.jsonl captures all operations for context window optimization.

**[2026-03-08 04:05]** `claude_cli` — Required commit_log.jsonl to capture all logs including errors from all sources (claude cli hooks, aicli commits, cursor hooks) to ensure unified audit trail.

**[2026-03-08 00:30]** `claude_cli` — Explained project comprehension: uses compressed history from previous sessions and current development files (PROJECT.md, tech_stack summaries, JSONL logs) to maintain context across LLM sessions and tools.