# Project Context: aicli

> Auto-generated 2026-04-22 23:08 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 699
- **Last active**: 2026-04-22T23:07:45Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel; Dashboard tab for pipeline visibility
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop
- **database_schema**: m001-m052 migration framework; canonical INT PK order (id → client_id → project_id → user_id); unified mem_ai_* tables + per-project tables + shared users/roles tables
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with pgvector extensions + m001-m052 migration framework
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+ with pgvector extensions + m001-m052 migration framework
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
- **embeddings**: OpenAI text-embedding-3-small (1536-dim)
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **schema_migrations**: m001-m050 framework with db_schema.sql as source of truth
- **llm_provider_location**: agents/providers/
- **database_migrations**: m001-m052 framework with db_schema.sql as source of truth
- **schema_core**: mem_tags_relations (unified), planner_tags (with inline snapshot fields), mem_ai_events, mem_mrr_prompts/commits

## In Progress

- Database schema finalization (m051-m052): user_id migrated to SERIAL INT across all 18 tables; canonical column ordering enforced (id → client_id → project_id → user_id); created_at/updated_at positioned at end before embedding; committed_at removed from commits table
- Session UI improvements complete: Chat and History tabs show session metadata (source badge, phase chip, last 5 char session ID); stale session loading fixed by reading last_session_id from runtime state synchronously on tab open
- Chat tab session persistence: current session highlighted on load; localStorage cache prevents stale session display; full session ID shown in sticky banner with copy button; timestamp YY/MM/DD-HH:MM added next to user prompts
- Hook-log endpoint verified: all 531 prompts (389 DB + ~142 JSONL merged) loading correctly with proper descending sort order; m050 migration fixed silent DB error in prompt storage
- Event table cleanup completed: importance column dropped; system metadata tags stripped from 1441 events; only phase/feature/bug/source user tags retained; tags consolidated from mirror tables
- Dashboard and pipeline UI added: new Dashboard tab for workflow visibility; Cytoscape.js DAG visualization with 2-pane approval panel; pipelines executable from planner/docs/chat tabs; feature_snapshot table created to merge requirements with work items

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; .ai/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags, facts, work items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users → Projects
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules in agents/providers/ with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts/feature_snapshot
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
- Database schema as single source of truth (db_schema.sql) with m001-m052 migration framework; INT PKs in canonical order (id → client_id → project_id → user_id)
- Feature snapshot layer (mem_ai_feature_snapshot): merges user requirements with work items; planner_tags unified with deliverables JSONB
- Column standardization: INT primary keys in canonical order; created_at/updated_at at table end; embedding as final column; user_id as INT SERIAL
- Backend module organization: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations
- Deployment: Railway (Dockerfile + railway.toml) for backend; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Session history UI persistence: Chat/History tabs display sessions with source badge, phase chip, session ID (last 5 chars), and timestamp YY/MM/DD-HH:MM

---

## Project Documentation (PROJECT.md)

# aicli — Shared AI Memory Platform

_Last updated: 2026-04-17 | Version 3.1.0_

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
| 2 | **Backlog pipeline** — Mirror → Backlog digest → User review → Use case files | ✓ Implemented |
| 3 | **Planner** — User-managed tag hierarchy linked to use case files | ✓ Implemented |
| 4 | **Auto-deploy** — Stop hook → auto_commit_push.sh after every Claude Code session | ✓ Hooks |
| 5 | **Billing & usage** — Multi-user, server keys, balance, markup, coupons | ✓ Implemented |
| 6 | **Multi-LLM workflows** — Graph DAG: design → review → develop → test | ✓ Implemented |
| 7 | **Semantic search** — pgvector cosine similarity over events | ✓ Implemented |
| 8 | **Feature snapshots** — Haiku-generated requirements/design per planner tag | ✓ Implemented |
| 9 | **MCP server** — 10 tools: search_memory, get_project_state, tags, backlog | ✓ Implemented |

---

## Memory Architecture

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
  source_id: batch_{hash8}_{tagfp8} for commits; last prompt UUID for prompt batches
  Tags: only user-intent {phase, feature, bug, source} stored

Layer 3 — Structured Artifacts (mem_ai_project_facts)
  Durable facts ("uses pgvector", "auth is JWT")

Layer 4 — User Taxonomy (planner_tags)
  Human-owned hierarchy: features, bugs, tasks, phases
  file_ref → links to use case .md files
  ← USER OWNS THIS — AI suggests, user confirms
```

### Backlog Pipeline (5 steps)

```
Step 1 — Raw capture:   mem_mrr_* (no LLM)
Step 2 — Backlog:       backlog_config.yaml drives 2-call LLM digest
           per source type:
           call 1 — grouping_prompt  (clusters N rows by topic)
           call 2 — summary_prompt   (per group → requirements + action items)
           → documents/backlog.md (append-only)
Step 3 — User review:   Backlog tab — approve (x), reject (-), add tag
Step 4 — Merge:         POST /memory/{p}/work-items processes approved entries
           → creates/updates documents/use_cases/{slug}.md
           → links planner_tag.file_ref → use case file
Step 5 — Use case LLM:  refreshes Open items with AI score 0-5
```

### How `/memory` syncs context

```
POST /projects/aicli/memory
  ├── Flush all pending mirror rows → backlog.md
  ├── Write CLAUDE.md / .cursorrules / context.md from DB facts + planner_tags
  └── Top events → .claude/memory/top_events.md


*...201 more lines in PROJECT.md*

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
