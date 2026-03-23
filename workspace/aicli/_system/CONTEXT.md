# Project Context: aicli

> Auto-generated 2026-03-23 00:15 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 256
- **Last active**: 2026-03-23T00:12:55Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles, user_api_keys (encrypted)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Stdio MCP server with 12+ tools; env var configured (BACKEND_URL, ACTIVE_PROJECT)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_usage/ (provider_costs.json, runtime data); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch config (.vscode/launch.json); PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ per-project schema + shared auth/usage tables; agent roles initialized

## In Progress

- Feature/task/bug status workflow (2026-03-23) — Implement red 'add_info' status when description missing; green 'Active' status when complete; lifecycle tags deprecated; user questioned why features show Active without proper descriptions—clarifying status enforcement logic
- Deprecated old/ directory usage (2026-03-23) — Confirmed old/ should not be modified; update memory to reflect this is legacy code; focus development on current directory structure
- Tags loading and cache invalidation (2026-03-22) — Force-reload logic with cache validation; confirmed _plannerShowNewWorkItem calls _renderWorkItemTable() directly (correct path), not _renderTagTableFromCache()
- Agent role standardization (2026-03-22) — Per-agent system roles, prompts, input/output schemas, and ReAct mode execution to eliminate hallucination; Sr. Architect role testing
- Frontend code optimization (2026-03-22) — XSS fixes in markdown.js; 30s timeout in api.js; JSDoc documentation; setInterval cleanup in graph_workflow.js
- Memory items and project_facts table population (pending) — Tables exist in schema but update logic not implemented; required for improved memory/context mechanism

## Key Decisions

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
- Dual storage: JSONL (history.jsonl with rotation) for primary history; PostgreSQL 15+ with pgvector (1536-dim) for semantic search and per-project indexed tables
- Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys in database
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval panel
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); smart chunking per language/section
- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared auth/usage tables
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval for work item management
- Backend modular organization: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
- Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
- Encrypted API key storage in data layer (dl_api_keys.py); server-side key management only; clients never send API credentials
- Feature/task/bug lifecycle: Status 'add_info' (red) when missing description; transitions to 'Active' (green) when fully described; lifecycle tags optional and candidate for deprecation

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

**[2026-03-23 00:09]** `claude_cli/claude`  
→ Why you fix files in old ? this is not suppose to be used. I also dont see any change in the UI - I do see all feature a
← _Good — `_plannerShowNewWorkItem` calls `_renderWorkItemTable()` directly, not `_renderTagTableFromCache()`. The refresh path is correct.  Now update memory to note `old/` should not be touched:_

**[2026-03-22 23:48]** `claude_cli/claude`  
→ Yes implememt 2 and 3. About section 1 - I think feutre , tasks, bugs without a description should be in a status red (a
← _Now do a quick syntax check on the backend file:_

**[2026-03-22 23:35]** `claude_cli/claude`  
→ please fix the embedding. also I would like to understand the feutre as the test will be running the full workflow from 
← _Good data. Here's the complete picture — what actually exists in memory for Auth, and what the Architect would do with it.  ---  ## Input to Sr. Architect  In the `standard` pipeline, the Architect re_

**[2026-03-22 23:21]** `claude_cli/claude`  
→ I would like to start to test the Sr. Architect role. assume the pipeleine start from feature Auth. can you tell me what
← _The skill loaded an old cached version — let me run this directly and also pull the auth history to give you a complete picture:_

**[2026-03-22 22:48]** `claude_cli/claude`  
→ I would like to make sure each agent works same as you are - not hilusinsating, and have a defined system role and promt
← _Everything is working. Now update MEMORY.md:_

**[2026-03-22 10:53]** `claude_cli/claude`  
→ Also I would like to have proper log mechanism for all the app. I do not see any logger used. usualy I buuild looger cla
← _Now update the auto-memory MEMORY.md with logging system details:_

**[2026-03-22 10:44]** `claude_cli/claude`  
→ OK .so when user update from ui / run role push (can run role [role_name] push or role push for all rules - there will b
← _All components of the ReAct Agents implementation are in place:  - **DB migrations** — `tools JSONB`, `react BOOLEAN`, `max_iterations INT` columns added - **Agent tools** — `tool_memory.py` + `tool_w_

**[2026-03-22 10:35]** `claude_cli/claude`  
→ So when yaml is configured - is it suppose to load into the database ? 
← _Now verify the SQL is syntactically correct by doing a dry import:_

**[2026-03-22 10:32]** `claude_cli/claude`  
→ I would like that manage agennts/roles only as an adming (so other customers can only see the role/agent name but cannot
← _Quick verification:_

**[2026-03-22 09:57]** `claude_cli/claude`  
→ I have tried but it is not working
← _Now — the issue is that **you need to restart Claude Code** for it to discover new skills. The skill file is correct at `.claude/skills/ac/SKILL.md`.  After restarting, type `/` and you should see `ac_

**[2026-03-22 09:55]** `claude_cli/claude`  
→ the rason of this change was to declare properly an agent. currently an agent is based only on prompts (or set of prompt

**[2026-03-22 02:53]** `claude_cli/claude`  
→ I dont see any tags loading, it looks like there is no api call to the db . all I can see is just the categoroes 
← _The Vite dev server (HMR) should hot-reload automatically. The Planner tab should now work — switch to another tab and back, or just click a category.  The root cause: **all previous fixes were applie_

**[2026-03-22 02:49]** `claude_cli/claude`  
→ Is it possilbe to creatre skeen that run my aiCli commands from Claude CLI - for example /ac /memory - will run my memor
← _The `/ac` skill is ready. Here's what you can now do in Claude Code:  | Command | What it does | |---------|-------------| | `/ac /memory` | Generates all 5 memory files via your backend | | `/ac /sta_

**[2026-03-22 02:48]** `claude_cli/claude`  
→ This is still not working. I dont see tags loading at all (just empty categories)
← _Good — the backend correctly returns `fallback: True` when DB is unavailable.  The full fix chain now is: - **`tagCache.js`**: checks `vData.fallback` per-category — if any values came back as fallbac_

**[2026-03-22 02:39]** `claude_cli/claude`  
→ Planner still dont load all tags , all I see is ctegories
← _`_plannerState.project` is set. The fix is correct.  The changes make three improvements:  1. **`_initPlanner`**: detects fallback categories (null IDs) and force-reloads the cache with `force=true` b_
