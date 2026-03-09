# Project Memory — aicli
_Generated: 2026-03-09 00:55 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron with xterm.js + Monaco editor
- **storage**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV
- **database**: PostgreSQL 15+ with pgvector extension + SQLAlchemy ORM
- **authentication**: JWT (python-jose) + bcrypt + dev_mode toggle
- **planned**: GraphQL, node graph UI for entity relationships and workflow composition, MCP server for cross-tool integration, unified provider logging
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
- PostgreSQL 15+ with SQLAlchemy ORM and pgvector extension for semantic embeddings and entity relationship search
- Memory auto-summarization at token limit; /memory command uploads relevant files for cross-session LLM context
- dev_runtime_state.json + project_state.json auto-maintained for shared LLM context across sessions
- Hooks auto-commit on claude cli/cursor; aicli tracks own history; all tools share unified commit_log.jsonl
- Cost tracking per provider/user/date in PostgreSQL; pricing managed by config/JSON under ui/backend/data (not hardcoded)
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history files and vectordb for cross-session project comprehension
- Mandatory metadata tagging for prompts (project, lifecycle_stage, feature_area) enforced across all CLI tools to enable semantic search and memory continuity

## In Progress

- PostgreSQL pgvector schema validation: confirmed new PostgreSQL instance with pgvector extension ready; created users, user_usage, usage_logs, billing_logs, workflows tables; dropped unused graph tables; validated relational data and vector embedding capability
- Mandatory metadata tagging system: implement force claude-cli and cursor to attach minimum metadata keys (project, lifecycle_stage, feature_area) to every prompt; ensure tags persist across conversation; create relational tagging table linking commit_id to lifecycle_stage/feature_area/bug
- Balance refresh logic and UI display: fixed top-right corner balance display with refresh button; admin dashboard aggregates total balance across all users and API keys; per-user balance visibility in user dashboard and API key management screen
- Unified commit_log.jsonl population: ensure all logs (prompts, responses, errors) from claude cli hooks, aicli commits, and cursor hooks write to shared commit_log.jsonl; verify history.jsonl captures both prompts and responses
- Code consolidation and cleanup: remove hardcoded cost_tracker pricing; clarify dev_runtime_state.json vs project_state.json necessity; consolidate history folder vs _system folder usage to eliminate duplication
- Hook integration and memory layer: verify claude cli hooks are auto-committing to git; ensure aicli tracks history properly; establish MCP server for cross-tool memory access via vectordb semantic embeddings

## Recent Work (last 10 exchanges)

**[2026-03-09 00:51]** `claude_cli/claude`
Q: can you review what we discussed and make sure all implemeted properly - MCP (3) - do that. Chanking - we spoke about smart chanking for each commit - summery, chank per class/method.. add proper meta

**[2026-03-09 00:35]** `claude_cli/claude`
Q: is all conigured as we discussed? metadata/enetity relationsheep table, embedding table, chanking architecure and mcp server that can be used by you or cursor ?

**[2026-03-09 00:14]** `claude_cli/claude`
Q: can you check if the new postgreurl is working and good for pgvector and for relational data ?

**[2026-03-08 23:52]** `claude_cli/claude`
Q: dont start yet. I would like to add this functionaltiy - tagging will be by aicli. known tag such as repo, project name will be attched. phase - can be discovery, developemet, prod... feature, bug .. 

**[2026-03-08 23:21]** `claude_cli/claude`
Q: dont start yet. Is is possible to force cloude-cli (or cursror) to have some minimm meta data keys for each prompt ? for example this converstion is tagged as aicli (project), discovery (mandatory) an

**[2026-03-08 23:08]** `claude_cli/claude`
Q: I will create postgresql with pgvector. it is a new instanse (so required to create all users table as well). before you continue - I would like to make sure that this approach will help you (claude c

**[2026-03-08 22:32]** `claude_cli/claude`
Q: I would to do rethinking for my AI knowledge layer or AI engineering memory as I am not sure the current solution is good enoguh to share memory / manage project properly over time. below is an archit

**[2026-03-08 05:29]** `claude_cli/claude`
Q: <task-notification> <task-id>ade5c631fc46f568b</task-id> <tool-use-id>toolu_01Pe5xp62Rc7Y1JiE5TMtMtm</tool-use-id> <status>completed</status> <summary>Agent "Drop graph tables and remove graph code" c

**[2026-03-08 05:18]** `claude_cli/claude`
Q: the second one - under _system/run

**[2026-03-08 05:15]** `claude_cli/claude`
Q: let me try to explain workflow again - the goal is to build mutl agent flows. I have managed to do that using yaml . and add simole node (each node have promt as an agent role and which llm is running
