# Project Context: aicli

> Auto-generated 2026-03-08 22:34 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 23
- **Last active**: 2026-03-08T22:34:08Z
- **Last provider**: claude
- **Version**: 0.3.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron with xterm.js + Monaco editor
- **storage**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV
- **database**: PostgreSQL (users, user_usage, usage_logs, billing_logs, workflows, runs) + pgvector (planned)
- **authentication**: JWT (python-jose) + bcrypt + dev_mode toggle
- **planned**: GraphQL, node graph UI, pgvector semantic search, unified provider logging
- **orm**: SQLAlchemy

## In Progress

- PostgreSQL table cleanup and consolidation — remove unused tables; clarify workflow vs flows distinction; align database schema with node-graph workflow execution model
- Hooks integration from claude cli — commits not auto-executing; history.jsonl captures prompts but missing responses; ensure commit_log.jsonl populated from all tools (claude cli, aicli, cursor)
- Balance persistence and refresh — manual balance entry saves but doesn't persist across UI refresh; admin dashboard not showing total balance; usage_logs table empty despite creation
- Multi-agent workflow execution — transition from YAML config to UI-managed node graphs; each node runs prompt with specified LLM engine and outputs score for conditional branching
- Shared memory strategy across tools — establish how claude cli, aicli, and cursor read/compress history files; determine how /memory command uploads relevant context for cross-session project understanding
- Project memory optimization — remove unused code files (e.g., hardcoded cost_tracker); consolidate QUICKSTART.md and README.md into single source-of-truth system files; clarify dev_runtime_state.json necessity

## Key Decisions

- Flat file storage (JSONL/JSON/CSV) for history tracking + PostgreSQL for user_usage/billing logs; no ChromaDB/SQLite
- Electron UI with xterm.js terminal + Monaco editor; Vanilla JS frontend (not Tauri)
- JWT auth via python-jose + bcrypt; dev_mode toggle for testing without login; three user roles (admin/paid/free)
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content, _system/ = project state
- All LLM providers independent; clients send own API keys in headers; no hardcoded pricing (config-driven)
- Multi-agent workflows via node-based execution with YAML config (transitioning to UI-managed node graphs)
- Unified history.jsonl + commit_log.jsonl shared across claude cli, aicli, cursor via hooks and commits
- Manual balance entry in UI (no auto-fetch due to API limitations); admin sees total across all users
- PostgreSQL with SQLAlchemy ORM; pgvector planned for semantic search and entity relationships
- Memory auto-summarization at token limit; /memory command uploads relevant files for LLM context
- dev_runtime_state.json + project_state.json auto-maintained for shared LLM context across sessions
- Hooks auto-commit on claude cli/cursor; aicli tracks own history; all tools share unified commit_log.jsonl
- GraphQL + node graph UI planned for workflow management and entity relationship visualization
- Cost tracking: per provider/user/date in PostgreSQL; pricing managed by config/JSON under ui/backend/data
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history files for cross-session project comprehension

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

**[2026-03-08 03:27]** `claude_cli/claude`  
→ I am using postgresql already and can extend that to use pgvector for semantic embedding. node grapg will be used to bui

**[2026-03-08 03:14]** `claude_cli/claude`  
→ I am thinking to add graphql supprt (node graph ) that user can manaege entities and relatioships. add project meta data

**[2026-03-08 03:07]** `claude_cli/claude`  
→ do I need the dev_runtime_state.json ? also - now (assuming all history wokrs properly) - how can you use that to improv

**[2026-03-08 02:51]** `claude_cli/claude`  
→ It is lookls like hooks are not working now as I dont see new commits into the git repo (I am currently using the claude

**[2026-03-08 02:29]** `claude_cli/claude`  
→ Under workspace for each project there is _system and history folder. do I need the history folder as well? I do see tha
