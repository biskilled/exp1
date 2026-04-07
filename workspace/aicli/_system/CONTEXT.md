# Project Context: aicli

> Auto-generated 2026-04-07 01:05 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 402
- **Last active**: 2026-04-06T23:06:20Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local bash/npm
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev

## In Progress

- Work item tag-linking persistence and display: fixed _loadTagLinkedWorkItems filter logic where ai_category was incorrectly matching work item's category instead of tag's category; work items now persist and display correctly after drag-drop linkage and page reload
- Work item dual-status UI implementation: status_user dropdown for user control + status_ai badge for AI suggestions with separate color indicators; integrated into table headers and item drawer
- Work item embedding strategy: unified embedding space via code_summary + requirements + summary fields for cross-table cosine-similarity matching with planner_tags
- Work item commits association: /work-items/{id}/commits endpoint returning linked commits via JSONB tags filtering; commit-per-prompt inline display with accent left-border
- Tag deduplication across views: 149 tags total (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously
- UI drag-and-drop work item feature: user can drag work items between panes with visual feedback; investigating pane resizing via separator line interaction

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
- Tag filtering in work item list: ai_category must match tag's category, not work item's own category (fixed regression in _loadTagLinkedWorkItems)
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev
- Session-level UI consolidation: Planner tab unified for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created
- Work item persistence across navigation: drag-drop linkage saves correctly to DB; reload of project/page maintains linked work items in list display

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

**[2026-03-31 15:44]** `claude_cli/claude`  
→ I am not so happy with the infrastrucure, think it is bit complicated anbd would like to dp antoehr refactor before I co

**[2026-03-30 17:12]** `claude_cli/claude`  
→ I think the sujjestion tagging is missing now (it used to be prevously ) - when user run /memeoy it is also checking onl
← _All done. Here's a summary of what was completed in this session:  **Step 11 (aicli_memory.md) — verified complete.** The file was already fully updated (v3.0, 2026-03-30) covering all sections the pl_

**[2026-03-30 16:53]** `claude_cli/claude`  
→ yes, continue with data migration 
← _Now verify a clean backend restart works with no errors:_

**[2026-03-30 16:49]** `claude_cli/claude`  
→ Is all table strucure is implemeted properly ? I dont see the table strucure ? 
← _All 9 new memory infra tables are now created. Here's the summary:  **✅ New tables (9/9 created):** - `mng_tags_categories` — global tag categories - `pr_tags` — per-project tag hierarchy - `pr_tag_me_

**[2026-03-30 16:42]** `claude_cli/claude`  
→ It it still balnck. the error is Uncaught SyntaxError: Identifier '_esc' has already been declared there is also warning
← _Done. Two fixes applied:  1. **`graph_workflow.js`** — removed the duplicate `function _esc` at line 2130 (the one at line 431 is kept). This was the exact cause of `Uncaught SyntaxError: Identifier '_

**[2026-03-30 16:24]** `claude_cli/claude`  
→ Backend looks like it is running. when I run npm start - it looks like electron app is running, but nothing is showing a
← _Now let me verify the final state of the key section of `main.js`:_

**[2026-03-30 16:13]** `claude_cli/claude`  
→ Looks better. Now UI is using exisitng backend, but UI is not loading properly. I dont see anything (backend is running)
← _Good. Now let me also verify the Vite dev server is accessible — the UI will try to connect to `localhost:5173` when it can't find `dist`:_

**[2026-03-30 16:02]** `claude_cli/claude`  
→ Can you recheck, ui is not loading well. please remove the developer tools when I start ui. also when I start ui - it is
← _Now I have the full file. Let me write the updated `aicli_memory.md`:_

**[2026-03-30 15:10]** `claude_cli/claude`  
→ I would like to update my memory infrastrucutre, in order to have more reliable layers, better prompting capabilties and

**[2026-03-28 11:03]** `claude_cli/claude`  
→ What is the pr_event_links is used for ? how it is linking events?
← _`api.entities.getLinks` exists in `api.js` but is **never called from any view** — so `pr_event_links` is populated (by commit/sync hooks) but never surfaced in the current UI.  ---  ## Summary  | Pur_

**[2026-03-28 10:40]** `claude_cli/claude`  
→ What event insert into event table except prompts and new commits 
← _`pr_events` only ever gets **two event types**:  | `event_type` | Written by | Source | |---|---|---| | `prompt` | `route_chat.py` `_append_history()` | Every chat exchange (UI + hooks) | | `prompt` |_

**[2026-03-28 10:13]** `claude_cli/claude`  
→ Yes please do that, and run /memory to check P0#1, and fix P1#5 and P1#3 . also is the system loading hidtory from pr_pr
← _All migrations applied successfully:  - **`pr_prompts`** exists (renamed from `pr_interactions`) — 75 rows - **No embedding columns** — `prompt_embedding` and `response_embedding` are gone - **`pr_mem_

**[2026-03-28 09:45]** `claude_cli/claude`  
→ Before you continue - I would like to understand why in pr_interaction name is not change to pr_prompts at the db ? Also
← _Now I have the full picture. Let me give you clear answers to all four questions.  ---  ## 1. Why isn't `pr_interactions` renamed to `pr_prompts` in the DB yet?  The rename code IS in `database.py` as_

**[2026-03-28 02:38]** `claude_cli/claude`  
→ Can you update the table name from pr_interation to pr_prompts same to pr_interation_tags to pr_prompts_tags. also can g
← _Now I have a full picture. Here's a comprehensive design decision review with priority mapping:  ---  ## Design Decisions — Priority Map  ### P0 — Verify Core Functionality (must confirm before anythi_

**[2026-03-28 02:32]** `claude_cli/claude`  
→ Is it reccomended to merge pr_events and pr_interactions ?
← _The background research agent completed — its findings confirm the rewrite is accurate. The document is ready at `/Users/user/Documents/gdrive_cellqlick/2026/aicli/aicli_memory.md`._
