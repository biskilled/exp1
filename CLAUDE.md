<!-- Last updated: 2026-04-27 13:12 UTC -->
# aicli
_2026-04-27 13:12 UTC | Memory synced: 2026-04-27_

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
| 3 | **Work Items** — AI-classified backlog items (open → active → done) backed by `mem_work_items` | ✓ Implemented |
| 4 | **Auto-deploy** — Stop hook → auto_commit_push.sh after every Claude Code session | ✓ Hooks |
| 5 | **Billing & usage** — Multi-user, server keys, balance, markup, coupons | ✓ Implemented |
| 6 | **Multi-LLM workflows** — Graph DAG: design → review → develop → test | ✓ Implemented |
| 7 | **Semantic search** — pgvector cosine similarity over events | ✓ Implemented |
| 8 | **Role YAML** — All agent roles + pipelines defined in `workspace/_templates/` (no inline Python) | ✓ Refactor

## Structure

- backend/
- cli/
- documents/
- features/
- tests/
- ui/
- workspace/

## Stack & Architecture

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS + Electron + Vite
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js
- **storage**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry
- **memory_synthesis**: Claude Haiku (project_state.json) + 5 output files (CLAUDE.md, CODE.md, PROJECT.md, cursor/rules, api/) with token limits in project.yaml
- **chunking**: Smart: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 14 tools rewired to REST endpoints
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database_migrations**: PostgreSQL with m001-m080 framework (m080 adds 4-agent pipeline columns)

## Key Architectural Decisions

- Workspace structure: aicli/cli/{claude,mcp}/ for hooks/configs; aicli/pipelines/{prompts,samples}/ for workflows; aicli/documents/ for project files; aicli/state/ for runtime state. No .ai/, _system/, or .ai/ folders.
- Memory files (PROJECT.md, CODE.md, CLAUDE.md, cursor/rules, api/) generated ONLY by POST /memory endpoint from project_state.json + database queries; token-limited by project.yaml config. Not copied to projects.
- backend/memory/memory.yaml is canonical single source for file mapping; templates in backend/memory/templates/; memory.yaml itself is NOT copied to projects (internal logic only).
- code.md structure: public symbols (classes/methods/functions) with file coupling/hotspot tables; generated from mem_mrr_commits_code per commit + refreshed post-commit via sync_code_structure().
- mem_mrr_commits_code (19 columns) with is_latest BOOLEAN: per-symbol diffs tracked; replaces separate symbols table; updated per commit.
- Work Items unified hierarchy: wi_parent_id links features/bugs/tasks to use_case parents; approved items trigger 4-agent pipeline (PM→Architect→Developer→Reviewer) with acceptance_criteria, implementation_plan, pipeline_status, pipeline_run_id columns.
- Approved work items ONLY are embedded (pgvector, 1536-dim, text-embedding-3-small); code.md, project_state.json, project facts, and prompts are NOT embedded; /search/semantic searches work_items only.
- JWT authentication: python-jose + bcrypt with DEV_MODE toggle; hierarchical Clients→Users→Projects.
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract.
- All backend LLM prompts in YAML files under backend/memory/prompts/: command_memory.yaml (/memory), command_work_items.yaml (/wi classify), event_commit.yaml (post-commit), event_hook_context.yaml (hook synthesis), misc.yaml (inline prompts).
- Commit-sourced work items: regex 'fixes BU0012'/'closes FE0001' in commit message auto-closes items with score_status=5, score_importance=5; user must approve to update user_status to 'done'.
- project_state.json generated ONLY by POST /memory endpoint; drives all 5 memory file outputs; no other code path writes it.
- MCP tools rewired to REST: create_entity→POST /wi/{project}, list_work_items→GET /wi/{project}, sync_github_issues→PATCH /wi/{project}, get_file_history→GET /memory/{project}/file-history.
- Code refactoring: memory_work_items.py split into _wi_helpers.py (225 lines), _wi_classify.py (360 lines), _wi_markdown.py (485 lines); recursive CTEs bounded at depth 20; N+1 queries replaced with batch operations.
- Recursive CTE safety: all 6 unbounded CTEs (descendants, tree, approve_all, etc.) capped with depth < 20; token counting uses len(text) // 4 for accuracy.

## In Progress

- `TA4001` Audit and clean planner_tags table schema

## Coding Conventions

- **Python style**: Python 3.12+; type hints on all new functions; no `from X import *`
- **Imports**: stdlib → third-party → local; each group alphabetically sorted
- **Async**: use `async`/`await` throughout FastAPI routes; no blocking calls in async context
- **DB access**: always use `db.conn()` context manager (psycopg2 pool); parameterized queries only
- **Error handling**: log with `log.warning()` for expected errors, `log.exception()` for unexpected; return 422/404 from routes, never 500 for known cases
- **Naming**: `snake_case` for Python; `camelCase` for JS; `UPPER_SNAKE` for module-level constants
- **LLM prompts**: all prompts in `backend/prompts/*.yaml`; load via `prompt_loader.prompts.content(key)`; never inline strings
- **Work items**: `user_status` is TEXT (`open|pending|

## Active Features

- `BU3008` `Work Item UI Category Display Bug` [pending] — Planner UI not displaying bug/category labels properly—only shows 'work_item' category. When AI tag (due 2026-05-02)
- `US1002` `Work Item Management & Metadata System` [open] — Build comprehensive work item lifecycle management with AI-generated metadata, tag integration, and (due 2026-05-02)
- `US1001` `MCP Configuration` [open] — Set up Model Context Protocol (MCP) configurations for multiple LLM providers and IDEs (Claude Code,
- `TA4009` `Verify Hook-Log DB Storage After Migration` [pending] — Verify that hook-log endpoint correctly stores all prompts to database after migration m050. Ensure (due 2026-05-02)
- `TA4001` `Audit and clean planner_tags table schema` [in-progress] — Review planner_tags table for redundant/unused columns: drop seq_num (always null), merge source int

## Code Hotspots

- `backend/memory/memory_code_parser.py` — score 58.9626 (2 commits, 788 lines)
- `backend/memory/memory_work_items.py` — score 26.0 (24 commits, 1360 lines)
- `backend/memory/memory_files.py` — score 19.0 (17 commits, 1179 lines)
- `backend/routers/route_projects.py` — score 16.0 (14 commits, 1821 lines)
- `backend/core/db_migrations.py` — score 11.0 (9 commits, 3280 lines)
- `ui/frontend/views/work_items.js` — score 11.0 (9 commits, 2595 lines)
- `backend/agents/mcp/server.py` — score 11.0 (9 commits, 854 lines)
- `backend/routers/route_git.py` — score 9.0 (7 commits, 1691 lines)
- `backend/routers/route_work_items.py` — score 7.0 (7 commits, 594 lines)
- `backend/routers/route_memory.py` — score 5.0 (3 commits, 836 lines)

## Recently Changed (last commits)

- `MemoryFiles` — modified in b3d2fda3 — The MemoryFiles class was updated to include additional fields (event_type, crea
- `MemoryFiles.get_top_events` — modified in b3d2fda3 — The `get_top_events` method now converts database query results into a structure
- `m051_schema_refactor_user_id_updated_at` — modified in b3d2fda3 — This migration function refactors the database schema to convert user IDs from U
- `_resolve_user_id` — modified in b3d2fda3 — The function now handles multiple input types (int, str, or None) and defaults t
- `chat_history` — modified in b48376c2 — The `chat_history` function was modified to fetch a larger set of database rows 
- `_loadSessions` — modified in b48376c2 — The `_loadSessions` function was updated to restore the last known session ID fr
- `_normalize_jsonl_entry` — modified in b4a10441 — This new function normalizes history.jsonl entries to match the database respons
- `m050_prompts_source_id_index` — modified in d45c125b — Added a database migration to create a unique partial index on `mem_mrr_prompts(
- `_Database` — modified in 18dc4454 — The `_Database` class now validates database connections before use by testing t
- `_Database.conn` — modified in 18dc4454 — The `conn` method now validates database connections before returning them and a
- `MemoryEmbedding.process_item` — modified in 25e5c306 — The method now includes error handling to catch and log exceptions during item p
- `MemoryEmbedding` — modified in 25e5c306 — I don't see a diff provided in your message. Could you please share the actual d
- `m047_events_is_system` — modified in ec75b516 — Added a database migration to add an `is_system` BOOLEAN column to the `mem_ai_e
- `_upsert_event` — modified in ec75b516
- `_embed_commits_background` — modified in ec75b516 — The `_embed_commits_background` function was enhanced to asynchronously batch-pr
- `_is_system_commit` — modified in ec75b516 — The function `_is_system_commit` was added to detect auto-generated system file 
- `sync_commits` — modified in ec75b516
- `MemoryEmbedding.process_commit_batch` — modified in ec75b516 — The method now detects and flags commits that only modify system files (PROJECT.
- `_run_promote_all_work_items` — modified in 514a4b47 — The function now tracks execution time using `monotonic()` and passes the start 
- `_call_sonnet` — modified in 514a4b47
- `get_snapshot` — modified in 514a4b47 — The function now converts database row values to appropriate types (strings for 
- `_parse_snapshot_json` — modified in 514a4b47 — The function was enhanced to robustly extract and parse JSON from markdown-forma
- `generate_snapshot` — modified in 514a4b47 — The `generate_snapshot` function was enhanced with debug logging to track LLM ou
- `_reprocess` — modified in 6e2659a1 — The `_reprocess` function was added to asynchronously reprocess pending memory p
- `rebuild_work_items` — modified in 6e2659a1 — Added a new async endpoint function that rebuilds open, unlinked work items by d
- `MemoryPromotion` — modified in 87852109 — The `MemoryPromotion` class now selectively applies AI extraction to only `promp
- `MemoryPromotion.extract_work_items_from_events` — modified in 87852109 — The method now restricts AI-powered extraction to only "prompt_batch" and "sessi
- `embed_prompts` — modified in 8bf532b9 — Added a new async endpoint function `embed_prompts` that processes pending promp
- `rowFor` — modified in 8bf532b9 — The `rowFor` function was modified to display filtered tags (phase, feature, bug
- `_openWorkItemDrawer` — modified in 8bf532b9 — Added display of context tags (phase/feature/bug) from work item events as color
_(20 older entries rolled off — run `git log` for full history)_

---
_Auto-generated by aicli memory system. Run `/memory` to refresh._
_Last updated: 2026-04-27 13:12 UTC_