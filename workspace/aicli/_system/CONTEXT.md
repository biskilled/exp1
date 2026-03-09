# Project Context: aicli

> Auto-generated 2026-03-09 02:35 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 41
- **Last active**: 2026-03-09T02:34:30Z
- **Last provider**: claude
- **Version**: 0.3.0

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
- **ui_framework**: Node.js with event emission for semantic indexing

## In Progress

- Chat history UI fix: restore full prompt/response pairs per session with proper LLM response display and per-prompt metadata visibility (2026-03-09 02:20)
- Auto-tag loop implementation: enforce aicli to assign minimum metadata keys (project, lifecycle_stage, feature_area); persist tags across multi-turn conversations; validate relational_tags table storage
- Smart chunking embedding feature: implement summary-level + per-class/method chunk generation; add metadata filters (language, file, feature, project_stage) for filtered semantic retrieval; test event emission for indexing
- MCP server deployment: build semantic embedding search endpoint for claude-cli, cursor, and aicli clients to query pgvector embeddings and commit_log.jsonl; enable cross-tool memory access
- PostgreSQL pgvector validation: confirmed PostgreSQL 15+ instance; created core tables (users, user_usage, usage_logs, billing_logs, workflows, relational_tags, embeddings); validated relational + vector capabilities
- UI billing/usage integration: fixed usage_logs table population; implemented manual balance entry with refresh indicator; ensured calculations refresh on balance updates

## Key Decisions

- Flat file storage (JSONL/JSON/CSV) for history tracking + PostgreSQL 15+ with pgvector for semantic search and entity relationships; no ChromaDB/SQLite
- Electron UI with xterm.js terminal + Monaco editor; Vanilla JS frontend (not Tauri)
- JWT auth via python-jose + bcrypt; dev_mode toggle for testing without login; three user roles (admin/paid/free)
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content, _system/ = project state; single history.jsonl per project (no duplicate history folders)
- All LLM providers independent; clients send own API keys in headers; no hardcoded pricing (config-driven via ui/backend/data JSON)
- Multi-agent workflows via node-based execution model with YAML config; each node runs prompt with specified LLM engine and outputs score for conditional branching
- Manual balance entry in UI; admin sees aggregated total across all users; per-user balance visibility with refresh indicator
- PostgreSQL 15+ with SQLAlchemy ORM and pgvector extension for semantic embeddings and entity relationship search
- Memory auto-summarization at token limit; /memory command uploads relevant files for cross-session LLM context
- Hooks auto-commit on claude cli/cursor; aicli tracks own history; unified commit_log.jsonl with all logs (prompts, responses, errors)
- Cost tracking per provider/user/date in PostgreSQL; pricing managed by config/JSON (not hardcoded)
- Mandatory metadata tagging for prompts (project, lifecycle_stage, feature_area) enforced via aicli; tags persist across conversation; relational_tags table links commit_id to metadata
- Smart chunking strategy for commits: summary-level + per-class/method chunks with metadata filters (language, file, feature, project_stage) for semantic retrieval
- MCP server for cross-tool integration providing semantic embedding search across unified commit_log.jsonl and pgvector vectordb
- project_state.json auto-maintained for shared LLM context across sessions; dev_runtime_state.json deprecated

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

**[2026-03-09 02:31]** `ui/claude`  
→ What is my name and what feature am I working on?
← _Your name is **Alice** and you are working on **feature X**. 😊_

**[2026-03-09 02:31]** `ui/claude`  
→ My name is Alice and I work on feature X
← _Got it, Alice! I'll remember that you work on feature X. How can I help you today? Whether it's questions, brainstorming, troubleshooting, or anything else related to feature X (or beyond), feel free _

**[2026-03-09 02:31]** `ui/claude`  
→ What is my name and what feature am I working on?
← _I don't have any information about your name or what feature you're working on. I don't have access to personal details about you unless you share them in our conversation.  Would you like to tell me?_

**[2026-03-09 02:31]** `ui/claude`  
→ My name is Alice and I work on feature X
← _Thanks for sharing that, Alice! I'll keep in mind that you work on feature X.  Is there something specific about feature X you'd like to discuss or get help with? I'm happy to assist!_

**[2026-03-09 02:20]** `claude_cli/claude`  
→ something went wrong in the chat tab . it used to work properly - I saw all prompts per session, but only the prompt I w

**[2026-03-09 02:03]** `ui/claude`  
→ brief test for event emission
← _## Brief Event Emission Test  ```javascript const EventEmitter = require('events');  // --- Setup --- const emitter = new EventEmitter(); const results = [];  // --- Listeners --- emitter.on('data', (_

**[2026-03-09 02:01]** `ui/claude`  
→ Testing auto-tag suggestions on non-streaming endpoint
← _It looks like you're testing the auto-tag suggestion feature on a non-streaming endpoint! I'm here and responding normally.  Is there anything specific you'd like to test or discuss? Feel free to send_

**[2026-03-09 01:58]** `ui/claude`  
→ I am working on the smart chunking embedding feature for semantic search
← _That's a great feature to work on! Smart chunking is crucial for semantic search quality. Let me help you think through it.  ## Smart Chunking for Semantic Search  ### Key Considerations  **What makes_

**[2026-03-09 01:47]** `claude_cli/claude`  
→ please implemet step1 - auto-tag loop. regarding users - aicli currently hosting services. users working on same project

**[2026-03-09 01:36]** `claude_cli/claude`  
→ what do you think about the porject, can it help / reduce overall deployment? are there any similar tools I can use ?

**[2026-03-09 01:32]** `claude_cli/claude`  
→ Can you summersie all new changes and how /memory currently updte all files? hooks are still writing to local jsonl file

**[2026-03-09 01:06]** `claude_cli/claude`  
→ continue 

**[2026-03-09 00:56]** `claude_cli/claude`  
→ yes

**[2026-03-09 00:51]** `claude_cli/claude`  
→ can you review what we discussed and make sure all implemeted properly - MCP (3) - do that. Chanking - we spoke about sm

**[2026-03-09 00:35]** `claude_cli/claude`  
→ is all conigured as we discussed? metadata/enetity relationsheep table, embedding table, chanking architecure and mcp se
