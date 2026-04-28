<!-- Last updated: 2026-04-28 11:46 UTC -->
# aicli
_2026-04-28 11:46 UTC | Memory synced: 2026-04-28_

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
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry + 4-agent pipeline
- **memory_synthesis**: Claude Haiku synthesis of project_state.json; pgvector embeddings ONLY for approved work items (UC/FE/BU/TA prefix)
- **chunking**: tree-sitter (Python/JS/TS) per-symbol diffs + per-section markdown
- **mcp**: Stdio MCP server with 14 tools; unified dispatch via REST endpoints
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database_migrations**: PostgreSQL m001-m080 (m080 adds 4-agent pipeline columns)
- **code_parser**: tree-sitter (Python/JavaScript/TypeScript) for per-symbol diffs; hotspot recency weighting: 180-day half-life EXP(-0.693 × age_ratio)

## Key Architectural Decisions

- Memory architecture: 3 layers — raw captures (mem_mrr_* tables: prompts, commits, code diffs, file stats, coupling), structured artifacts (mem_ai_project_facts with Haiku synthesis), and work items (mem_work_items with pgvector embeddings ONLY for approved items prefixed UC/FE/BU/TA).
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; all 5 output files (CLAUDE.md, CODE.md, PROJECT.md, cursor/rules, api/) regenerated from single JSON.
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task) and wi_parent_id linking children to use_case parents; wi_id format: AI0001 (unapproved draft) → UC/FE/BU/TA0001 (approved); only approved items embed and trigger 4-agent pipeline.
- Code.md generation: per-symbol diffs via tree-sitter (Python/JS/TS) with file coupling/hotspot tables; refreshed post-commit and post-memory; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio) to prioritize recently-changed files.
- Embeddings strategy: ONLY approved work items (wi_id: UC/FE/BU/TA) embed to pgvector; code.md, project_state.json, project facts, and prompts never embed; /search/semantic searches work_items only.
- Work item re-embedding: triggered automatically on name/summary/description edits for approved items via update(); unapproved drafts (AI prefix) never embed; commit-sourced items auto-set score_status=5 and score_importance=5 via regex 'fixes BU0012' pattern for user approval.
- Prompts: all backend LLM prompts stored in YAML under backend/memory/prompts/ (command_memory.yaml, event_commit.yaml, command_work_items.yaml, mem_project_state.yaml, mem_session_tags.yaml, misc.yaml); loaded via prompt_loader utility.
- MCP server: 14 tools rewired to REST endpoints; stdio server in agents/mcp/server.py with unified dispatch pattern matching tool name to REST route; tools include search_memory, get_project_state, list_work_items, classify, approve, run_pipeline.
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract.
- 4-agent pipeline: PM (acceptance criteria) → Architect (implementation plan) → Developer (code) → Reviewer; triggered only on approved items under approved use cases; stored in mem_work_items columns acceptance_criteria, implementation_plan, pipeline_status, pipeline_run_id.
- Authentication: JWT (python-jose + bcrypt) with hierarchical Clients → Users → Projects; DEV_MODE toggle for passwordless local development.
- Code organization: memory_work_items.py split into _wi_helpers.py (225 lines), _wi_classify.py (360 lines), _wi_markdown.py (600 lines) with shared imports; all modules < 1500 lines; recursive CTEs bounded to depth < 20 with safeguards.
- Date cascade validation: _apply_date_rules() prevents re-parenting work items to use cases with earlier due_dates; depth check added when wi_parent_id changes to prevent silent data inconsistency.
- File management: backend/memory/memory.yaml is canonical single-source mapping for output files and project creation; templates/ holds seed files; memory.yaml is internal engine only, not copied to projects.
- Database optimization: batch queries replace N+1 patterns (hotspot checks use single WHERE name = ANY(%s)); token counting: len(text) // 4; recursive CTEs bounded to depth < 20; unbounded CTE depth safeguards added.

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
- `backend/memory/memory_work_items.py` — score 29.0 (27 commits, 1378 lines)
- `backend/memory/memory_files.py` — score 20.0 (18 commits, 1176 lines)
- `backend/routers/route_projects.py` — score 17.0 (15 commits, 1693 lines)
- `backend/core/db_migrations.py` — score 12.0 (10 commits, 3307 lines)
- `backend/agents/mcp/server.py` — score 11.0 (9 commits, 854 lines)
- `ui/frontend/views/work_items.js` — score 11.0 (9 commits, 2595 lines)
- `backend/routers/route_git.py` — score 9.0 (7 commits, 1691 lines)
- `backend/routers/route_work_items.py` — score 7.0 (7 commits, 594 lines)
- `backend/routers/route_memory.py` — score 5.0 (3 commits, 836 lines)

## Recently Changed (last commits)

- `m051_schema_refactor_user_id_updated_at` — modified in b3d2fda3 — This migration function refactors the database schema to convert user IDs from U
- `_resolve_user_id` — modified in b3d2fda3 — The function now handles multiple input types (int, str, or None) and defaults t
- `MemoryFiles` — modified in b3d2fda3 — The MemoryFiles class was updated to include additional fields (event_type, crea
- `MemoryFiles.get_top_events` — modified in b3d2fda3 — The `get_top_events` method now converts database query results into a structure
- `_loadSessions` — modified in b48376c2 — The `_loadSessions` function was updated to restore the last known session ID fr
- `chat_history` — modified in b48376c2 — The `chat_history` function was modified to fetch a larger set of database rows 
- `_normalize_jsonl_entry` — modified in b4a10441 — This new function normalizes history.jsonl entries to match the database respons
- `m050_prompts_source_id_index` — modified in d45c125b — Added a database migration to create a unique partial index on `mem_mrr_prompts(
- `_Database` — modified in 18dc4454 — The `_Database` class now validates database connections before use by testing t
- `_Database.conn` — modified in 18dc4454 — The `conn` method now validates database connections before returning them and a
- `MemoryEmbedding.process_item` — modified in 25e5c306 — The method now includes error handling to catch and log exceptions during item p
- `MemoryEmbedding` — modified in 25e5c306 — I don't see a diff provided in your message. Could you please share the actual d
- `m047_events_is_system` — modified in ec75b516 — Added a database migration to add an `is_system` BOOLEAN column to the `mem_ai_e
- `_is_system_commit` — modified in ec75b516 — The function `_is_system_commit` was added to detect auto-generated system file 
- `sync_commits` — modified in ec75b516
- `_embed_commits_background` — modified in ec75b516 — The `_embed_commits_background` function was enhanced to asynchronously batch-pr
- `MemoryEmbedding.process_commit_batch` — modified in ec75b516 — The method now detects and flags commits that only modify system files (PROJECT.

---
_Auto-generated by aicli memory system. Run `/memory` to refresh._
_Last updated: 2026-04-28 11:46 UTC_