# Project Context: aicli

> Auto-generated 2026-03-09 00:37 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 28
- **Last active**: 2026-03-09T00:37:33Z
- **Last provider**: claude
- **Version**: 0.3.0

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

## In Progress

- PostgreSQL pgvector schema validation: confirmed new PostgreSQL instance with pgvector extension ready; created users, user_usage, usage_logs, billing_logs, workflows tables; dropped unused graph tables; validated relational data and vector embedding capability
- Mandatory metadata tagging system: implement force claude-cli and cursor to attach minimum metadata keys (project, lifecycle_stage, feature_area) to every prompt; ensure tags persist across conversation; create relational tagging table linking commit_id to lifecycle_stage/feature_area/bug
- Balance refresh logic and UI display: fixed top-right corner balance display with refresh button; admin dashboard aggregates total balance across all users and API keys; per-user balance visibility in user dashboard and API key management screen
- Unified commit_log.jsonl population: ensure all logs (prompts, responses, errors) from claude cli hooks, aicli commits, and cursor hooks write to shared commit_log.jsonl; verify history.jsonl captures both prompts and responses
- Code consolidation and cleanup: remove hardcoded cost_tracker pricing; clarify dev_runtime_state.json vs project_state.json necessity; consolidate history folder vs _system folder usage to eliminate duplication
- Hook integration and memory layer: verify claude cli hooks are auto-committing to git; ensure aicli tracks history properly; establish MCP server for cross-tool memory access via vectordb semantic embeddings

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

---

## Project Documentation (PROJECT.md)

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-08_

---

## Vision

**aicli gives every LLM the same project memory.**

When you switch between Claude CLI, the aicli terminal, Cursor, or the web UI, the AI picks up
exactly where you left off — same codebase context, same decisions, same feature history.
No more copy-pasting context. No more re-explaining your architecture.

---

## Core Goals

| # | Goal | Status |
|---|------|--------|
| 1 | **Shared LLM memory** — Claude CLI, aicli CLI, Cursor, UI all read the same knowledge base | ✓ Implemented |
| 2 | **Prompt management** — Role-based agents (architect, developer, reviewer, QA, security, devops) | ✓ Foundation done |
| 3 | **5-layer memory** — Immediate → Working → Project → Historical → Global | ✓ Architecture in place |
| 4 | **Auto-deploy** — pull → commit → push after every AI session | ✓ Hooks + git.py |
| 5 | **Billing & usage** — Multi-user, server keys, balance, markup, coupons | ✓ Implemented |
| 6 | **Multi-LLM workflows** — YAML chains: design → review → develop → test | ✓ Runner done |

---

## 5-Layer Memory Architecture

```
Layer 1 — Immediate Context
  └── providers/{claude,openai,...}.messages  (in-memory, not persisted)
      Live conversation: current prompt chain within the session

Layer 2 — Working Memory
  └── {cli_data_dir}/sessions/{provider}_messages.json
  └── {cli_data_dir}/session_state.json
      Short-term task state: active feature, tag, last commit, cross-provider handoff

Layer 3 — Project Knowledge
  └── workspace/{project}/PROJECT.md          — living project doc (this file)
  └── workspace/{project}/project_state.json  — structured metadata: tech stack, modules, APIs
  └── workspace/{project}/_system/CLAUDE.md   — synced to code_dir/CLAUDE.md for Claude Code
      Architecture, decisions, coding standards, data models

Layer 4 — Historical Knowledge
  └── workspace/{project}/_system/history.jsonl    — all interactions (UI + CLI + workflow + Cursor)
  └── {cli_data_dir}/memory.jsonl                  — tagged/featured entries, keyword-searchable
      Past decisions, design discussions, feature history, bug postmortems, refactor notes

Layer 5 — Global Knowledge
  └── workspace/_templates/hooks/                  — canonical hook scripts for all projects
  └── workspace/_templates/{blank,python_api,...}  — project starter templates
  └── workspace/_templates/roles/                  — shared AI role prompts (TODO: create)
      Company coding standards, security policies, AI role prompts, architecture templates
```

### How `/memory` syncs layers 3–5 to every LLM tool:

```
_system/claude/CLAUDE.md   →  {code_dir}/CLAUDE.md          ← Claude Code reads at session start
_system/claude/MEMORY.md   →  {code_dir}/MEMORY.md          ← referenced inside CLAUDE.md
_system/cursor/rules.md    →  {code_dir}/.cursor/rules/aicli.mdrules  ← Cursor reads on open
_system/aicli/context.md   →  prepended to every aicli CLI prompt
```

---

## Prompt Management — Roles & Agents

Roles live in `workspace/{project}/prompts/roles/`. Each is a Markdown system prompt.

| Role file | Use case | Provider preference |
|-----------|----------|-------------------|
| `architect.md` | System design, API contracts, tech decisions | Claude (reasoning) |
| `developer.md` | Code implementation, refactoring | Claude / DeepSeek |
| `reviewer.md` | Code review, quality feedback | OpenAI / Gemini |
| `qa.md` | Test design, edge cases, regression | DeepSeek / Claude |


*...229 more lines in PROJECT.md*

---

## Recent Development History

**[2026-03-09 00:35]** `claude_cli/claude`  
→ is all conigured as we discussed? metadata/enetity relationsheep table, embedding table, chanking architecure and mcp se

**[2026-03-09 00:14]** `claude_cli/claude`  
→ can you check if the new postgreurl is working and good for pgvector and for relational data ? 

**[2026-03-08 23:52]** `claude_cli/claude`  
→ dont start yet. I would like to add this functionaltiy - tagging will be by aicli. known tag such as repo, project name 

**[2026-03-08 23:21]** `claude_cli/claude`  
→ dont start yet. Is is possible to force cloude-cli (or cursror) to have some minimm meta data keys for each prompt ? for

**[2026-03-08 23:08]** `claude_cli/claude`  
→ I will create postgresql with pgvector. it is a new instanse (so required to create all users table as well). before you

**[2026-03-08 22:32]** `claude_cli/claude`  
→ I would to do rethinking for my AI knowledge layer or AI engineering memory as I am not sure the current solution is goo

**[2026-03-08 05:29]** `claude_cli/claude`  
→ <task-notification> <task-id>ade5c631fc46f568b</task-id> <tool-use-id>toolu_01Pe5xp62Rc7Y1JiE5TMtMtm</tool-use-id> <stat

**[2026-03-08 05:18]** `claude_cli/claude`  
→ the second one - under _system/run 

**[2026-03-08 05:15]** `claude_cli/claude`  
→ let me try to explain workflow again - the goal is to build mutl agent flows. I have managed to do that using yaml . and

**[2026-03-08 05:10]** `claude_cli/claude`  
→ I do see lot of table in my postgresql - all are required as there were some changes. can you remove table not in use?

**[2026-03-08 05:06]** `claude_cli/claude`  
→ <task-notification> <task-id>ba21592</task-id> <tool-use-id>toolu_01X3GzA6q9L1GhyQMY72Yeqd</tool-use-id> <output-file>/p

**[2026-03-08 04:47]** `claude_cli/claude`  
→ I dont see any worklow. prevoiusly there was some workflow sample that can be managed by yaml config as well. worklow su

**[2026-03-08 04:27]** `claude_cli/claude`  
→ I dont see any new table created in my postgresql . also I do see that you creaed new tab - flows, but there is already 

**[2026-03-08 04:13]** `claude_cli/claude`  
→ I would like to understand how the new update imporve your way to understand all code project, what are you doing in ord

**[2026-03-08 04:05]** `claude_cli/claude`  
→ I do not see that error in the commit_log.jsonl , can you make sure all logs are at this files (also errros). also this 
