# Project Context: aicli

> Auto-generated 2026-03-17 13:41 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 115
- **Last active**: 2026-03-16T19:14:12Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows) + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 12+ tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push, create_entity, update_entity, list_entities, get_feature_status)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, and MCP integration settings

## In Progress

- Workflow system design (2026-03-16) — Analyzed specrails pattern (Claude Code agent with 12 prompt roles) and external workflow tooling; evaluating integration approach for node-based async DAG executor with YAML config and Cytoscape.js UI
- Config externalization and optimization (2026-03-16) — Moved backend_url, haiku_model, db_pool_max to config.py; removed unused methods; added /health check for MCP readiness
- Memory distillation pipeline refinement (2026-03-16) — Implemented dual-layer summarization (raw JSONL → interaction_tags → 5 memory files); fixed session_bulk_tag() to write to both event_tags and interaction_tags tables
- MCP tool expansion for project management (2026-03-16) — Implemented create_entity, update_entity, list_entities, get_feature_status tools; verified JSON output accuracy
- Session phase persistence and backfill (2026-03-15) — Phase now loads from DB on init, saves via PATCH /chat/sessions/{id}/tags, backfills all matching history.jsonl entries preserving session order
- Tag deduplication and cross-view synchronization (2026-03-15) — 149 tags with 0 duplicates; removal via ✕ buttons propagates across Chat/History/Commits views; inline commit display per prompt

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables with real indexed columns (phase/feature/session_id)
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server for local dev
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth with tree UI in Planner; tags synced across Chat/History/Commits
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Commit-to-prompt linking via source_id timestamp; bidirectional tagging via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase; backfills history.jsonl ordered by created_at
- Real DB columns for phase/feature/session_id in events_{p} with indexes; tag cache loaded once per project tab (zero DB calls during chat)
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization + YAML config

---

## Project Documentation (PROJECT.md)

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-14 | Version 2.2.0_

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
| 2 | **Prompt management** — Role-based agents (architect, developer, reviewer, QA, security, devops) | ✓ Implemented |
| 3 | **5-layer memory** — Immediate → Working → Project → Historical → Global | ✓ Implemented |
| 4 | **Auto-deploy** — pull → commit → push after every AI session | ✓ Hooks + git.py |
| 5 | **Billing & usage** — Multi-user, server keys, balance, markup, coupons | ✓ Implemented |
| 6 | **Multi-LLM workflows** — Graph DAG: design → review → develop → test | ✓ Implemented |
| 7 | **Entity/knowledge graph** — Tag every event (prompt/commit) to features, bugs, tasks | ✓ Implemented |
| 8 | **Semantic search** — pgvector cosine similarity over chunked history + code | ✓ Implemented |
| 9 | **Project management UI** — Unified Planner: 2-pane tag manager, per-entry tagging, commit linking | ✓ Implemented |

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
  └── workspace/{project}/_system/project_state.json  — structured metadata + next_phase_plan
  └── workspace/{project}/_system/CLAUDE.md   — synced to code_dir/CLAUDE.md for Claude Code

Layer 4 — Historical Knowledge
  └── workspace/{project}/_system/history.jsonl    — all interactions (UI + CLI + workflow + Cursor)
  └── workspace/{project}/_system/events_{p}       — PostgreSQL event log, tagged to features/bugs
      Past decisions, design discussions, feature history, bug postmortems, refactor notes

Layer 5 — Global Knowledge
  └── workspace/_templates/hooks/                  — canonical hook scripts for all projects
  └── workspace/_templates/{blank,python_api,...}  — project starter templates
  └── workspace/_templates/workflows/              — shared workflow YAML library (planned)
  └── workspace/_templates/roles/                  — shared AI role prompts (planned)
```

### How `/memory` syncs layers 3–5 to every LLM tool

```
_system/claude/CLAUDE.md   →  {code_dir}/CLAUDE.md                    ← Claude Code reads at start
_system/claude/MEMORY.md   →  {code_dir}/MEMORY.md                    ← referenced in CLAUDE.md
_system/cursor/rules.md    →  {code_dir}/.cursor/rules/aicli.mdrules  ← Cursor reads on open
_system/aicli/context.md   →  prepended to every aicli CLI prompt      ← all providers
_system/aicli/copilot.md   →  {code_dir}/.github/copilot-instructions.md
```

---

## Architecture

### Engine / Workspace Separation

```
aicli/                     ← ENGINE — code only, no project-specific content
├── cli.py                 ← Interactive REPL (prompt_toolkit + rich)


*...258 more lines in PROJECT.md*

---

## Recent Development History

**[2026-03-17 13:33]** `claude_cli/claude`  
→ Somehow, I cannot see the prject now in order at me lat project.. also when I open the project it takes quite long time 

**[2026-03-17 13:30]** `claude_cli/claude`  
→ can you use the mcp tool and explain what the prject is about ?

**[2026-03-16 19:02]** `claude_cli/claude`  
→ yes
← _All changes look correct. The Agent Roles implementation in `graph_workflow.js` is now complete. Here's a summary of what was done in this session:  **`graph_workflow.js` — completed:** - `_gwOnRoleCh_

**[2026-03-16 19:00]** `claude_cli/claude`  
→ I do mention to sotre the prompts in database, would there be a way to change the prompts as it might be improved over t
← _Good design direction. Here's how this maps cleanly to what's already planned:  ---  ## Design: Agent Roles in Database  ### Schema (`agent_roles` + `agent_role_versions`)  ```sql -- Live role definit_

**[2026-03-16 18:52]** `claude_cli/claude`  
→ I do see you have crete a defualt pipe line in the Planner tab that run defualt Pipeline . where is this pipeline config
← _Now I have the full picture. Let me answer all three questions clearly.  ---  ## Answers to your questions  ### 1. Where is the "Run Pipeline" configured?  It's in `ui/backend/core/work_item_pipeline._

**[2026-03-16 18:34]** `claude_cli/claude`  
→ I would like to start working on the workflows - the goal is to be able to be similar to https://www.specrails.dev/docs/
← _Now I have everything I need. Let me write the comprehensive comparison and design proposal.  ---  ## Workflow System Design: Comparison & Proposal  ### What the two external systems do  **specrails**_

**[2026-03-16 18:26]** `claude_cli/claude`  
→ are you using the mcp now? 
← _---  **To answer your question directly:**  No, I'm not using the MCP in this session. Everything I did was via direct HTTP calls (`curl`, Python `urllib`).  **What changes:**  - `.mcp.json` is now at_

**[2026-03-16 18:02]** `claude_cli/claude`  
→ Keys are stored at my .env file which you can load - for claude api the key is under ANTHROPIC_API_KEY and for openai th
← _Everything is working end-to-end. Here's the full picture:  ---  ## Full Pipeline — Now Working  ### What just happened in sequence: 1. **Bug found and fixed** — `ARRAY_AGG(uuid[])` came back from psy_

**[2026-03-16 17:42]** `claude_cli/claude`  
→ Can you run the /memory and go over current architecure - how data is stored, how mcp is used, go ver all memory layer. 
← _Now I have a complete picture. Let me give you a clear, honest assessment.  ---  ## `/memory` Run Results  **Ran successfully** — generated 5 files at 17:43 UTC. Result: `"synthesized": false` because_

**[2026-03-16 01:34]** `claude_cli/claude`  
→ Can you summersie all improvement - would that make the systme better perfromed , would memroy work better? doad mcp can
← _## Complete System Improvement Summary  ---  ### What Was Built (7 Parts)  **Before:** Every LLM call got either 40 raw JSONL entries (noisy, expensive) or a CLAUDE.md (too coarse). Tags lived in per-_

**[2026-03-16 01:26]** `claude_cli/claude`  
→ After this refactor - can you check if tags are well used ? is memroy improved by new summersation process? will mcp can
← _Here's a complete answer to your questions:  ---  ## Audit Results + What Was Fixed  ### Tags — mostly good, one gap fixed The old `event_tags_{project}` system is fully wired: chat, history sync, and_

**[2026-03-16 00:48]** `claude_cli/claude`  
→ I have started to look in some other solution like https://github.com/danshapiro/trycycle and www.specrails.dev/docs/wor

**[2026-03-16 00:19]** `claude_cli/claude`  
→ I would like to optimise the code : check each file, make sure code is in used and all method are required. make sure th
← _All clean. Here's a summary of everything fixed:  ---  ## Optimization fixes applied  | Issue | File | Fix | |---|---|---| | `haiku_model` hardcoded in 6 places | `config.py` | Added `haiku_model: str_

**[2026-03-15 23:49]** `claude_cli/claude`  
→ 1,2,3,4,5 and 8. I would like to add also anotehr mng table to check how many prompt there are and prompt the user (in u

**[2026-03-15 23:38]** `claude_cli/claude`  
→ Is there is any addiotnal improvement that I can implemet for having full memroy , and project management lifecycle ? 
← _Based on the audit, here are the gaps and a prioritized roadmap:  ---  ## What's Missing — Prioritized  ### Quick Wins (low effort, high value)  **1. MCP `create_entity` tool** Claude CLI / Cursor can_
