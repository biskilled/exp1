# Project Context: aicli

> Auto-generated 2026-03-19 13:03 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 157
- **Last active**: 2026-03-19T13:00:01Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows) + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK nesting), agent_roles, system_roles
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; inline modal for pipeline creation
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK nesting), agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings

## In Progress

- Pipeline UI enhancements (2026-03-19) — Added node properties display (max_retry, stateless, continue_on_fail); implemented node removal with confirmation dialog; renamed '+ New Flow' to '+ New Pipeline'; replaced native dialogs with inline modal
- Multi-agent workflow execution (2026-03-19) — Retry/continue logic per node; chat/run capability for current phase; ROLE_PRESETS removed; MEMORY.md updates pending
- Project visibility race condition (2026-03-19) — Projects load in Recent but not selectable as active project; backend init timing issue; requires investigation of project.md loading vs app startup
- Graph workflow UI import fix (2026-03-19) — Fixed main.js imports for graph_workflow.js; corrected case statements for proper renderer routing
- Memory items and project_facts table population (unresolved) — Tables exist but update logic not implemented; blocks improved memory/context; requires implementation and testing
- Documents tab feature (2026-03-19) — Add Documents tab mapped to per-project folder; auto-create for new projects; support multiple roles uploading docs

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file primary (JSONL with rotation on /memory); PostgreSQL 15+ with pgvector for semantic search; per-project DB tables with indexed columns (phase/feature/session_id)
- Electron UI with xterm.js + Monaco editor; Vanilla JS frontend (no framework, no bundler); Vite dev server for local dev
- JWT auth via python-jose + bcrypt; DEV_MODE toggle; 3 roles: admin/paid/free; login as first-level hierarchy
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth with tree UI; tags synced across Chat/History/Commits on save
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot rules, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Load-once-on-access pattern: eliminate redundant SQL; tag cache synced on explicit save
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- Port binding safety: freePort() kills stale uvicorn; Electron cleanup via process.exit()
- Backend startup race condition fix: retry logic handles empty project list on first load
- Pipeline/workflow nodes support max_retry, stateless mode, continue_on_fail flags; visual node removal with confirmation dialog

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


*...303 more lines in PROJECT.md*

---

## Recent Development History

**[2026-03-19 12:46]** `claude_cli/claude`  
→ UI improvmenet - in pipeline for each node - can you add more properties (max retry, stateless, continue on fail - so us
← _Done. Here's a summary of all changes made to `graph_workflow.js`:  **Buttons & labels:** - `+ New Flow` → `+ New Pipeline` (toolbar button, empty state button, modal title) - `Saved Flows` → `Saved P_

**[2026-03-19 12:29]** `claude_cli/claude`  
→  can you update /memory as well to make sure this feature is stored 
← _Also update the `See Also` section at the bottom:_

**[2026-03-19 12:09]** `claude_cli/claude`  
→ system designer - only run of explicitly placed of course . retry is per node, continue is per node (default is False). 
← _All clean — ROLE_PRESETS and exportLangGraph references have been fully removed.  Now let me update the MEMORY.md with the key changes:_

**[2026-03-19 12:01]** `claude_cli/claude`  
→ Yamel config need to be simple . at the moment all flows are sequece - node A -> Node B -> Node C it can have max rettry
← _Good, I have the full picture. Let me write the architecture design now.  ---  ## Architecture Design  ### Current State vs Target  | Aspect | Today | Target | |--------|-------|--------| | Roles | Na_

**[2026-03-19 11:47]** `claude_cli/claude`  
→ Lets fix that - currently there are 2 tabs - Roles - this one is used for changing roles, update roles and add some inou
← _This is a significant architectural redesign. Let me design it properly before touching any code._

**[2026-03-19 02:39]** `claude_cli/claude`  
→ It seems that project list is loading after the app is running as I cannot see any project when app start to run, but se
← _Now verify syntax:_

**[2026-03-19 02:31]** `claude_cli/claude`  
→ I dont see any change in the UI . can you check all is done properly 
← _The root cause was that `main.js` was importing `renderWorkflow` from the old `workflow.js` (YAML editor), while the new pipeline designer lives in `graph_workflow.js` and exports `renderGraphWorkflow_

**[2026-03-19 02:02]** `claude_cli/claude`  
→ I would like to extend the roles and add a way to define input type (prompts, md file located under document folder, jso

**[2026-03-19 01:43]** `claude_cli/claude`  
→ I would like to extend the workflow: I woudld like to add tab "Documents" after Code that will be mapped to docusmnet fo

**[2026-03-19 01:25]** `claude_cli/claude`  
→ When app is stsrting - I still cannot see all project in prject page (only after I open the project). also it seems tha 
← _Now add the `_togglePromptFiles` global:_

**[2026-03-19 00:57]** `claude_cli/claude`  
→  I cannot see any system_roles under system_roles. also the + to add system_roles or agent_roel is not working. also I a
← _Good. Now you need to **restart the backend** for all three fixes to take effect:  ```bash kill $(lsof -ti :8000) && cd ui/backend && python3.12 -m uvicorn main:app --host 127.0.0.1 --port 8000 --relo_

**[2026-03-18 21:16]** `claude_cli/claude`  
→ I would like to start to work on the Roles. by adding system roles that can be added into any Agent roles. for example s

**[2026-03-18 20:54]** `claude_cli/claude`  
→ I would  to make sure memory is optimised the way we discussed previously :  As I do store propts, llm repsonse, tags an
← _All 3 backfilled. Let me do a final verification:_

**[2026-03-18 20:17]** `claude_cli/claude`  
→ Few more strucure - users are also part of client (client can have mutiple users). Also I would like to understand if yo
← _Both fixes are in place. The `from pathlib import Path` import is now added, `mng_users.client_id` FK is defined, and the `history.jsonl` backfill code at line 1017 will now work correctly.  The backe_

**[2026-03-18 20:03]** `claude_cli/claude`  
→ Looks beter. there are some minor issue - in project page, I do see in Recent aiCli, but I do not see that As a project 
← _Now also fix `_continueToApp` — if projects load succeeds but returns empty (e.g. race condition), retry once:_
