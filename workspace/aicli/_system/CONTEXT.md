# Project Context: aicli

> Auto-generated 2026-03-20 21:52 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 178
- **Last active**: 2026-03-20T21:51:23Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows) + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **memory_synthesis**: Claude Haiku for dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles

## In Progress

- SQL query optimization (2026-03-20) — P0 issues identified: row-by-row INSERT in event migration (2000+ queries for 1000 events) and unbounded fetchall() in memory synthesis; requires batch INSERT refactor and pagination
- Workflow performance optimization (2026-03-20) — Workflow execution runs very slowly; requires analysis of async DAG executor bottlenecks and potential query caching improvements
- System roles enhancement (2026-03-20) — Optimize work_item pipeline to use existing roles (PM, architect) and add system roles with formatting expectations (e.g., document generation role outputs short bullet-point descriptions)
- Pipeline approval workflow rendering (2026-03-20) — Old MD version displayed instead of current output/progress logs; requires chat panel state management and step sequencing investigation
- UUID validation in pipeline run queries (2026-03-19) — psycopg2 InvalidTextRepresentation when string 'recent' passed to UUID field; requires UUID object conversion in backend
- Memory items and project_facts table population (pending) — Tables exist in schema but update logic unimplemented; blocks improved memory/context mechanism

## Key Decisions

- Engine/workspace separation: aicli/ contains code only; workspace/ stores per-project content; _system/ holds project state
- Dual storage: JSONL (history.jsonl with rotation) for primary storage; PostgreSQL 15+ with pgvector for semantic search and per-project indexed tables
- Electron UI with xterm.js + Monaco editor; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication via python-jose + bcrypt; DEV_MODE toggle; 3-tier roles (admin/paid/free); login as first-level hierarchy
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends no keys
- Nested tag hierarchy via parent_id FK with unlimited depth; tags synced across Chat/History/Commits on explicit save
- Load-once-on-access pattern: cache tags/workflows/runs in memory; update DB only on explicit save to eliminate redundant SQL
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js + cytoscape-dagre visualization
- Memory synthesis: Claude Haiku for dual-layer output (raw JSONL → interaction_tags → 5 files); smart chunking per language/section
- Port binding safety via freePort() to kill stale uvicorn; Electron cleanup via process.exit()
- Features linked to work_items with sequence numbering (10000+) for memory and workflow status tracking
- MCP server (stdio) with 12+ tools for project state, memory search, entity management, feature status
- Per-project DB tables indexed on phase/feature/session_id for fast contextual retrieval
- 2-pane approval chat workflow for requirement negotiation before work_item save
- System roles for document generation (e.g., PM, architect roles with specific output formatting expectations)

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

**[2026-03-20 21:48]** `claude_cli/claude`  
→ I would like to start optimising the project motly the following buiding block - sql queries, and running the workflow w
← _## Performance Analysis Results  I found significant issues in both areas. Here's the breakdown:  ---  ### SQL Query Issues (by priority)  | Priority | Issue | Location | Impact | |----------|-------|_

**[2026-03-20 21:32]** `claude_cli/claude`  
→ Work Item pieplien suppose to use the existing roles - PM - project manage, architect - Sr architect. can you optimize t

**[2026-03-20 19:46]** `claude_cli/claude`  
→ I do see that last version is arhcitet, pm... and all the rest are not under old folder. Also - I would like to provide 
← _But `_loadTab` refetches if no cache. The real fix is that `_render()` reattaches to container and `_loadTab` uses the cached data. Let me check how the HistoryView handles this — when `_histData` is _

**[2026-03-20 19:09]** `claude_cli/claude`  
→ I am testing the Pipeline - when I clicked approved I do see the old md version . I would expcet to see process and afte
← _Also verify the Python files have no obvious errors:_

**[2026-03-20 18:19]** `claude_cli/claude`  
→ I still dont see the project loaded when app is started. all I can see in the logs is  Application startup complete. (us
← _Both files pass syntax validation. Here's a summary of what was implemented in the previous session and is ready to test:  **All 6 improvements are in place:**  1. **Projects load on startup** — `_con_

**[2026-03-20 16:29]** `claude_cli/claude`  
→ Projects only loading when I press to prject tab. as Project  loaded as default page, it should load when app is starter
← _Here's a summary of all 8 fixes applied:  ---  **1. Projects not loading on startup** (`main.js`) - Added a re-render of `renderHome(view)` in `_continueToApp`'s `.then()` callback when still on the h_

**[2026-03-20 00:15]** `claude_cli/claude`  
→ Currently  memory_items (compressed knowledge) is based on prompt/responses, commit, workflows node results.  I would li
← _Now let me verify all changes are consistent by doing a quick sanity check:_

**[2026-03-19 23:54]** `claude_cli/claude`  
→ I did reciave the following message : No JSON array found in response ... Also I still dont see project loading when app
← _Now fix the startup project loading:_

**[2026-03-19 23:22]** `claude_cli/claude`  
→ Do you understand what is this app is about ? can you summerise that and let me know who are direct competitors?
← _## What aicli Is  **aicli is a shared AI memory platform for software development teams.**  The core problem it solves: every time you switch between Claude CLI, Cursor, the web UI, or any other AI to_

**[2026-03-19 23:04]** `claude_cli/claude`  
→ Looks better. I would like to have an option to chat as well in order to chance to requirement. once it is agreed, user 
← _The implementation looks correct. Here's what was done:  **Changes made:**  1. **`graph_workflow.js` — module state** (line 43): Added `let _approvalChatHistory = [];`  2. **`graph_workflow.js` — `_sh_

**[2026-03-19 22:05]** `claude_cli/claude`  
→ Can you explain what the run pipeline is doing when it start running from the the planer/feature. I have tried to test t
← _All roles are correctly matched now: - PM → Product Manager ✓ - Architect → Sr. Architect ✓   - Developer → **Backend Developer** ✓ (not Web Developer) - Reviewer → Code Reviewer ✓  Let me do a quick _

**[2026-03-19 20:55]** `claude_cli/claude`  
→ There are some UI improvement - I do see that GET /projects/ take some time to load and that is why I dont see projects 
← _All changes are confirmed in place. Here's a summary of everything done:  **prompts.js (background agent completed):** - Agent Roles on top with `flex:1` for proper spacing - System Roles at bottom wi_

**[2026-03-19 16:47]** `claude_cli/claude`  
→ it looks better, but workflow complated after 2 seconds. I do not see any outcomes in my Documents, not even something m
← _Now restart the backend to pick up all the fixes:_

**[2026-03-19 16:29]** `claude_cli/claude`  
→ I still have the same error - psycopg2.errors.InvalidTextRepresentation: invalid input syntax for type uuid: "recent" [1
← _Now restart the backend to pick up the UUID guard fix:_

**[2026-03-19 16:12]** `claude_cli/claude`  
→ Start to looks better. Now I do see the _work_item_pipeline but all I can see is an error saying - psycopg2.errors.Inval
← _Since the run panel is now at the bottom, there's no need to close the detail panel — they can both be open simultaneously. Let me remove that:_
