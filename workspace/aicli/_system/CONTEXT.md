# Project Context: aicli

> Auto-generated 2026-03-08 03:08 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 11
- **Last active**: 2026-03-08T03:08:39Z
- **Last provider**: claude
- **Version**: 0.3.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt
- **frontend**: Vanilla JS + Electron (no framework)
- **storage**: JSONL / JSON / CSV — no databases

## In Progress

- History view showing all sources (UI chat + CLI + Claude Code hooks)
- project_state.json + dev_runtime_state.json auto-maintenance
- Memory auto-summarisation at token limit

## Key Decisions

- No ChromaDB / SQLite — flat files only
- Electron (not Tauri) with xterm.js terminal + Monaco editor
- Auth: REQUIRE_AUTH toggle; JWT via python-jose; bcrypt direct (not passlib)
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content
- All LLM providers independent — CLI providers/ ≠ ui/backend/core/llm_clients.py
- Client sends own API keys in request headers — server never stores keys

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


*...220 more lines in PROJECT.md*

---

## Recent Development History

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

**[2026-03-08 00:40]** `claude_cli/claude`  
→ Can you explain how you get all project info, I do see that sometime you compress the history. and start loading a new s

**[2026-03-08 00:30]** `claude_cli/claude`  
→ It is manage to save balance, but I dont see that when I am rephresh (top right corenr). also on users tab - I dont see 

**[2026-03-08 00:11]** `claude_cli/claude`  
→ Usage tab - when I try to update - I do reciave an error - "Not found". billing tab - when I try to remove a row in the 

**[2026-03-07 23:54]** `claude_cli/claude`  
→ I dont see the balance endpoint at the ui. can you instead of adding a new tab, manage that at usage page. Ui update - m

**[2026-03-07 23:35]** `claude_cli/claude`  
→ apparntly both api calls not working. claude api works only for team or organisation account (I am using personal accoun

**[2026-03-07 22:35]** `claude_cli/claude`  
→ I have tried to fatch usage data from both api - claude and open ai, from both I got 400 and 404 errors. also I would li

**[2026-03-07 21:15]** `claude_cli/claude`  
→ I would like to create better Billing Tracker using the following steps  - Capture Usage Returned by Providers -      op
