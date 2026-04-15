# Project Context: aicli

> Auto-generated 2026-04-15 10:45 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 560
- **Last active**: 2026-04-15T10:39:22Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel; Dashboard tab for pipeline visibility
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac/Windows/Linux)
- **database_schema**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features (unified); mem_mrr_commits_code, mem_mrr_tags (mirroring); per-project tables; shared users/usage_logs/transactions/session_tags/entity_categories tables
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extensions + m001-m041 migration framework
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+ with pgvector extensions
- **build_tooling**: npm 8+ + Electron-builder + Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev
- **prompt_management**: core.prompt_loader module with centralized prompt caching
- **schema_management**: db_schema.sql + db_migrations.py (m001-m037)
- **database_tables**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; Shared: users, usage_logs, transactions, session_tags, entity_categories, planner_tags, mng_tags_categories
- **embeddings**: text-embedding-3-small (1536-dim vectors)
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **schema_migrations**: m001-m041 framework with db_schema.sql as source of truth
- **llm_provider_location**: agents/providers/

## In Progress

- Agent context consolidation (2026-04-15) — Consolidated legacy _system/ files to .ai/rules.md, .cursor/rules/aicli.mdrules, .github/copilot-instructions.md as primary agent context; removed stale CLAUDE.md and MEMORY.md
- Memory promotion timing instrumentation (2026-04-15) — Added time.monotonic() tracking to _run_promote_all_work_items; updated _finish_run calls with t0 parameter for performance measurement
- Snapshot generation refactor (2026-04-15) — Switched Claude Sonnet to Haiku for cost efficiency; simplified planner_tags upsert to flat string keys (requirements, action_items, design, code_summary); improved JSON parsing robustness
- Schema cleanup and refactoring (2026-04-14) — mem_ai_work_items table reorganized: removed status_ai dual-status design, reordered columns with seq_num near id, added explicit FOREIGN KEY constraint for merged_into, added ivfflat embedding index
- Work item pipeline refactor (2026-04-14) — Agent roles loaded from DB with fallback prompts; RoleCreate/RoleUpdate models updated; auto_commit boolean support added; 4-stage pipeline with provider/model overrides
- Tag suggestion approval flow (2026-04-13) — ai_tag_suggestion column with approve/remove buttons; simplified chip markup; category inference on tag creation; improved tooltip UX

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; .ai/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags, facts, work items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; login_as_first_level_hierarchy pattern for hierarchical Clients → Users
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules in agents/providers/ with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash with exec_llm boolean flag
- Event filtering: event_type IN ('prompt_batch', 'session_summary') for work item digests; system metadata stripped, user-facing tags retained
- Agent roles loaded from DB (mng_agent_roles) with fallback prompts; 4-stage work item pipeline (PM→Architect→Developer→Reviewer) with auto_commit flag
- Database schema as single source of truth (db_schema.sql) with m001-m041 migration framework; column ordering: client_id → project_id → created_at/processed_at/embedding
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Tag suggestion with ai_tag_suggestion column and approve/remove buttons; simplified chip markup with category inference on tag creation

---

## Project Documentation (PROJECT.md)

# aicli — Shared AI Memory Platform

_Last updated: 2026-04-15 | Version 3.0.0_

---

## Vision

**aicli gives every LLM the same project memory.**

When you switch between Claude Code, the aicli CLI, Cursor, or the web UI, the AI picks up
exactly where you left off — same codebase context, same decisions, same feature history.
No more copy-pasting context. No more re-explaining your architecture.

---

## Core Goals

| # | Goal | Status |
|---|------|--------|
| 1 | **Shared LLM memory** — Claude Code, aicli CLI, Cursor all read the same knowledge base | ✓ Implemented |
| 2 | **4-layer memory pipeline** — Mirror → AI Events → Work Items → Project Facts | ✓ Implemented |
| 3 | **Planner / Work Items** — AI-detected tasks linked to user-managed planner_tags | ✓ Implemented |
| 4 | **Auto-deploy** — Stop hook → auto_commit_push.sh after every Claude Code session | ✓ Hooks |
| 5 | **Billing & usage** — Multi-user, server keys, balance, markup, coupons | ✓ Implemented |
| 6 | **Multi-LLM workflows** — Graph DAG: design → review → develop → test | ✓ Implemented |
| 7 | **Semantic search** — pgvector cosine similarity over events + work items | ✓ Implemented |
| 8 | **Feature snapshots** — Haiku-generated requirements/design per tag | ✓ Implemented |
| 9 | **MCP server** — 10 tools: search_memory, get_project_state, work items, tags | ✓ Implemented |

---

## 4-Layer Memory Architecture

```
Layer 1 — Raw Capture (mem_mrr_*)
  ├── mem_mrr_prompts        raw prompt/response pairs (session-tagged)
  ├── mem_mrr_commits        git commits (hash, msg, tags, diff_summary)
  ├── mem_mrr_commits_code   per-symbol diffs (tree-sitter: class, method, file)
  ├── mem_mrr_items          document/meeting items
  └── mem_mrr_messages       Slack/chat messages

Layer 2 — AI Events (mem_ai_events)
  Haiku digest + OpenAI embedding (text-embedding-3-small, 1536-dim)
  event_type: prompt_batch | commit | session_summary | item | workflow
  is_system=TRUE → system file updates (PROJECT.md etc) skipped for work items
  source_id: batch_{hash8}_{tagfp8} for commits; last prompt UUID for prompt batches
  Tags: only user-intent {phase, feature, bug, source} stored

Layer 3 — Structured Artifacts (mem_ai_*)
  ├── mem_ai_work_items      AI-detected tasks/bugs/features (score_ai 0-5)
  └── mem_ai_project_facts   Durable facts ("uses pgvector", "auth is JWT")

Layer 4 — User Tags (planner_tags)
  Human-owned taxonomy: features, bugs, tasks, phases
  ← USER OWNS THIS — AI suggests, user confirms
```

### How `/memory` syncs context to every LLM tool

```
POST /projects/aicli/memory
  ├── Haiku synthesizes last N events → CLAUDE.md / MEMORY.md / context.md
  ├── _system/claude/CLAUDE.md   →  {code_dir}/CLAUDE.md        ← Claude Code auto-loads
  ├── _system/claude/MEMORY.md   →  {code_dir}/MEMORY.md        ← referenced in CLAUDE.md
  ├── _system/cursor/rules.md    →  {code_dir}/.cursor/rules/   ← Cursor reads on open
  ├── _system/aicli/context.md   →  prepended to every CLI prompt
  ├── _system/aicli/copilot.md   →  .github/copilot-instructions.md
  └── background: promote_all_work_items() + run_feature_snapshots()
```

### PROJECT.md vs CLAUDE.md vs project_facts

| File | Source | Updated by |
|------|--------|-----------|
| `PROJECT.md` | Manual living doc (this file) | Human / Summary tab / `PUT /projects/aicli/summary` |
| `CLAUDE.md` | Auto-generated from DB | `/memory` POST → `write_root_files()` |
| `MEMORY.md` | Auto-generated from DB | `/memory` POST → `write_root_files()` |
| `mem_ai_project_facts` | AI-extracted from events | `extract_project_facts()` in memory_promotion.py |



*...190 more lines in PROJECT.md*

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
