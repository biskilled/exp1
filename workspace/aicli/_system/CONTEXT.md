# Project Context: aicli

> Auto-generated 2026-03-08 05:06 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 17
- **Last active**: 2026-03-08T05:06:01Z
- **Last provider**: claude
- **Version**: 0.3.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt + SQLAlchemy
- **frontend**: Vanilla JS + Electron (xterm.js + Monaco editor)
- **storage**: JSONL (history.jsonl, commit_log.jsonl) / JSON / CSV
- **database**: PostgreSQL (user_usage, usage_logs, billing_logs) + pgvector (planned)
- **authentication**: JWT (python-jose) + bcrypt + dev_mode toggle
- **planned**: GraphQL, node graph UI, pgvector semantic search, unified provider logging
- **orm**: SQLAlchemy

## In Progress

- Fix hooks integration — commits not working from claude cli; history.jsonl captures prompts but not responses; ensure all sources write to commit_log.jsonl
- Balance persistence on refresh — manual balance entry saves but doesn't persist on UI refresh; admin sees total, users see own balance
- PostgreSQL usage_logs population — table created but entries not populating; ensure all providers log usage and refresh UI displays totals
- Consolidate workflow/entity management — 'flows' tab created but 'workflow' tab exists; clarify distinction; build node graph UI instead of separate tabs
- Memory system optimization — commit_log.jsonl not capturing all errors/logs from claude cli, aicli, cursor; ensure unified history across all sources
- Shared memory architecture for LLM context — define how /memory command reads/compresses history files; establish memory digest strategy for project understanding

## Key Decisions

- No ChromaDB / SQLite — flat files only (JSONL / JSON / CSV) for history tracking; PostgreSQL for user_usage / billing logs only
- Electron UI (not Tauri) with xterm.js terminal + Monaco editor; Vanilla JS frontend
- Auth: REQUIRE_AUTH toggle; JWT via python-jose; bcrypt for password hashing; dev_mode for testing without login
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content; _system folder stores all project state
- All LLM providers independent — CLI providers/ ≠ ui/backend/core/llm_clients.py; client sends own API keys in headers
- User roles: admin, paid, free tier with dev_mode toggle; manual balance entry via UI (no auto-fetch due to API limitations)
- All history tracked to history.jsonl + commit_log.jsonl for shared LLM memory across claude cli, aicli, cursor
- PostgreSQL for user_usage / billing logs with pgvector planned for semantic search; SQLAlchemy ORM
- Hooks auto-commit on claude cli / cursor; aicli tracks own history; unified history.jsonl + commit_log.jsonl
- Node graph / GraphQL planned for entity relationships and workflow management with prompt-based node execution
- Memory auto-summarisation at token limit; /memory command uploads all relevant files for LLM context
- dev_runtime_state.json + project_state.json auto-maintenance for shared LLM context across sessions
- Workflows: node-based execution with LLM engines per node (e.g., algo→backtest→qa→summary across different models)
- Cost tracking: pricing managed by config/JSON (not hardcoded); usage logged per provider/user/date in PostgreSQL
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history files + commit_log.jsonl

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

**[2026-03-08 02:09]** `claude_cli/claude`  
→ before I continue, I would like to optimise the code - when ever possible to use config, and classes. I do see some code

**[2026-03-08 01:30]** `claude_cli/claude`  
→ continue

**[2026-03-08 01:18]** `claude_cli/claude`  
→ Lets start to fix that , as this is the major goal of this project - shared memory between diffrent llm, so I can use cl

**[2026-03-08 00:53]** `claude_cli/claude`  
→ Would using vectordb and enabling you reading the data from vectordb will make that more easy for you (or other llm) to 

**[2026-03-08 00:44]** `claude_cli/claude`  
→ The main goal of this project is to be able for you and other llm to share memory. I have started to do that, and I do s
