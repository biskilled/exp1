# Project Context: aicli

> Auto-generated 2026-03-17 20:20 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 122
- **Last active**: 2026-03-17T20:20:26Z
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

- PROJECT.md load performance optimization (2026-03-17) — User reported >1 minute load time on free Railway tier when opening aiCli project; investigating if root cause is DB query latency or file I/O bottleneck; considering pagination/lazy-loading for project initialization
- Project visibility issue (2026-03-17) — aiCli project disappeared from recent projects list; unclear if UI state bug or DB query regression; requires verification of openProject() function and project listing logic
- Multi-agent workflow system (2026-03-16) — Analyzed specrails pattern (Claude Code agent with 12 prompt roles) and evaluated async DAG executor integration with Cytoscape.js visualization + YAML config
- Config externalization and MCP readiness (2026-03-16) — Moved backend_url, haiku_model, db_pool_max to config.py; added /health check for MCP server initialization verification
- Dual-layer memory distillation (2026-03-16) — Implemented raw JSONL → interaction_tags → 5 memory files pipeline; fixed session_bulk_tag() to write to both event_tags and interaction_tags for consistency
- Session phase persistence and tag deduplication (2026-03-15) — Phase now loads from DB on init and saves via PATCH; 149 tags with 0 duplicates; removal via UI buttons propagates across Chat/History/Commits views

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables with real indexed columns (phase/feature/session_id)
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server for local dev
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth with tree UI in Planner; tags synced across Chat/History/Commits
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase; backfills history.jsonl ordered by created_at
- Real DB columns for phase/feature/session_id in events_{p} with indexes; tag cache loaded once per project tab (zero redundant DB calls during chat)
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization + YAML config
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- Performance: load-once-on-access pattern eliminates redundant SQL; tag cache synced across Chat/History/Commits views on save

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

**[2026-03-17 20:13]** `claude_cli/claude`  
→ Planner works partial - I do see the nested work on some category like doc_type but in bug or feature ui is diffrent and
← _Here's a summary of everything done and answers to your questions:  ---  ## What was fixed  **Planner consistency** — removed the split between `entity_values` (doc_type etc.) and `work_items` (featur_

**[2026-03-17 18:50]** `claude_cli/claude`  
→ I would like to go over on all the feutre and plan propery to Planer and Worklow as they are linked. I have created tagg
← _Here's a summary of all changes made:  ---  ## Changes Made  ### Tab renames (`main.js`) - `"Workflow"` → `"Pipelines"` (PROJECT_TABS + global sidebar nav) - `"Prompts"` → `"Roles"` (PROJECT_TABS)  ##_

**[2026-03-17 18:29]** `claude_cli/claude`  
→ I dont see nay changes from the last improvement - current planner do not supposrt nested (parent-child) tags as it used
← _`agent_run_id` is `INT` (not UUID), so `str(row["agent_run_id"])` is fine — it just converts the int to string. That's correct.  The three fixes applied to `work_items.py`:  1. **`WorkItemCreate` mode_

**[2026-03-17 18:28]** `claude_cli/claude`  
→ What is the claude agent sdk is uded for can it be used for my use cases for mutli agents (project manager (high design)
← _## Claude Agent SDK vs Your Current Multi-Agent System  ### What is the Claude Agent SDK?  The **Claude Agent SDK** is Anthropic's official Python/TypeScript framework for building AI agents that can:_

**[2026-03-17 18:18]** `claude_cli/claude`  
→ can you use the mcp tool and explain what the code is doing ?
← _Here's what **aicli** does:  ## aicli — Shared AI Memory Platform  **Core idea**: When you switch between different AI tools (Claude CLI, Cursor, ChatGPT, the aicli web UI), they all forget your proje_

**[2026-03-17 14:35]** `claude_cli/claude`  
→ In the project I used to see the aiCli project, and I do not see that now. also when I press in my recent project - aiCl
← _Everything looks correct. Let me do a final check on the full `openProject` function to make sure it's clean:_

**[2026-03-17 13:33]** `claude_cli/claude`  
→ Somehow, I cannot see the prject now in order at me lat project.. also when I open the project it takes quite long time 
← _Now let's verify the key changes are correct with a quick sanity check:_

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
