<!-- Last updated: 2026-04-27 14:04 UTC -->
# aicli
_2026-04-27 14:04 UTC | Memory synced: 2026-04-27_

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
- **prompt_management**: YAML files in backend/memory/prompts/ with prompt_loader utility

## Key Architectural Decisions

- Memory architecture: 3 layers — raw captures (mem_mrr_*), structured artifacts (mem_ai_project_facts), and work items (mem_work_items) with pgvector embeddings for approved items only (1536-dim, text-embedding-3-small).
- Work items: unified hierarchy with wi_parent_id linking features/bugs/tasks to use_case parents; approved items (wi_id: UC/FE/BU/TA) embed and trigger 4-agent pipeline; unapproved drafts (AI prefix) never embed or run pipeline.
- File generation: /memory POST endpoint is the ONLY writer to project_state.json via get_project_context() + Haiku synthesis; this single JSON drives all 5 output files (CLAUDE.md, CODE.md, PROJECT.md, cursor/rules, api/).
- File management: backend/memory/memory.yaml is the canonical single-source mapping for output files; templates/ holds seed files (_CLAUDE.md, _settings.json, _mcp.json); memory.yaml itself is NOT copied to projects (internal engine only).
- Code.md structure: public symbols (classes/methods/functions) with file coupling/hotspot tables; generated from mem_mrr_commits_code per commit via sync_code_structure() and refreshed post-memory via unified get_project_context() path.
- Prompts: all backend LLM prompts in YAML under backend/memory/prompts/ named by trigger (command_memory.yaml, command_work_items.yaml, event_commit.yaml, event_hook_context.yaml, misc.yaml); loaded via prompt_loader utility.
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract.
- Embeddings: ONLY approved work items embed (mem_work_items.embedding VECTOR); code.md, project_state.json, project facts, and prompts are NOT embedded; /search/semantic searches work_items only.
- Work item re-embedding: triggered only on name/summary/description edits for approved items via automatic flag in update(); unapproved drafts never re-embed.
- Commit-sourced work items: regex 'fixes BU0012'/'closes FE0001'/'resolve TA0003' in commit message auto-closes items with score_status=5, score_importance=5; user must approve to update user_status to 'done'.
- MCP tools: 14 tools rewired to REST endpoints (create_entity→POST /wi, list_work_items→GET /wi, sync_github_issues→PATCH /wi, get_file_history→GET /memory/file-history, etc.).
- Database queries: recursive CTEs bounded (depth < 20); batch queries replace N+1 patterns; hotspot checks use single WHERE name = ANY(%s) with batch execution instead of per-row queries.
- Code organization: memory_work_items.py (1343 lines) split into _wi_helpers.py (225 lines), _wi_classify.py (360 lines), _wi_markdown.py (400 lines) with shared imports.
- Token counting: len(text) // 4 for Claude token estimation in work item synthesis and prompt truncation.
- JWT auth: hierarchical Clients→Users→Projects; DEV_MODE toggle for passwordless local development.

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
- `backend/memory/memory_work_items.py` — score 28.0 (26 commits, 1377 lines)
- `backend/memory/memory_files.py` — score 19.0 (17 commits, 1179 lines)
- `backend/routers/route_projects.py` — score 17.0 (15 commits, 1693 lines)
- `ui/frontend/views/work_items.js` — score 11.0 (9 commits, 2595 lines)
- `backend/agents/mcp/server.py` — score 11.0 (9 commits, 854 lines)
- `backend/core/db_migrations.py` — score 11.0 (9 commits, 3280 lines)
- `backend/routers/route_git.py` — score 9.0 (7 commits, 1691 lines)
- `backend/routers/route_work_items.py` — score 7.0 (7 commits, 594 lines)
- `backend/routers/route_chat.py` — score 5.0 (3 commits, 975 lines)

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
_Last updated: 2026-04-27 14:04 UTC_