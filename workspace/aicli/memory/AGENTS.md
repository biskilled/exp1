<!-- Last updated: 2026-04-29 19:23 UTC -->
# aicli
_2026-04-29 19:23 UTC | Memory synced: 2026-04-29_

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
- tests/
- ui/
- workspace/

## Stack & Architecture

- **language_cli**: Python 3.12
- **cli_framework**: prompt_toolkit + rich
- **backend_framework**: FastAPI + uvicorn
- **backend_auth**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **database**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **database_client**: psycopg2
- **frontend_framework**: Vanilla JS + Electron + Vite
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML pipeline + per-node retry
- **code_parser**: tree-sitter (Python/JavaScript/TypeScript) with 180-day recency-weighted hotspot scoring
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **mcp_transport**: Stdio MCP server with 10 tools; unified REST dispatch

## Key Architectural Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts via /memory POST + Haiku synthesis) → work items (mem_work_items with wi_parent_id hierarchy); ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; CLAUDE.md, CODE.md, PROJECT.md all regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Role YAML → DB sync: YAML files in workspace/_templates/pipelines/roles/ are read-only factory defaults; ON CONFLICT DO NOTHING seeds only new roles on startup; mng_agent_roles DB table is single source of truth for runtime; UI edits persist in DB across restarts
- Tech tag auto-detection: reads tech_stack from project_state.json instead of hardcoded regex; tags validated against actual project technologies in _build_tech_tags_block()
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech tags from project_state.json tech_stack
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval
- Code.md generation: per-symbol diffs via tree-sitter with file coupling/hotspot tables; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio)
- Embeddings strategy: ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector; code.md, project_state.json, project facts, prompts, commits never embed
- MCP server: 10 tools (search_memory, get_project_state, list_work_items, get_work_item, list_commits, search_commits, due_date filters, tags, backlog, classify_wi) dispatched via REST; stdio transport, local machine, no auth required
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract; temperature, max_tokens, model configurable per role YAML
- 4-agent async DAG pipeline: PM (acceptance criteria) → Architect (implementation) → Developer (code) → Reviewer (QA); triggered only on approved items under approved use cases; executed via asyncio.gather
- Authentication: JWT (python-jose + bcrypt) with hierarchical Clients → Users → Projects; DEV_MODE toggle for passwordless local development; MCP runs with no auth (stdio-only, local)
- System prompts consolidation: 3 shared system prompt presets in system_prompts.yaml (coding_general, design_and_planning, review_and_quality); mng_agent_roles.system_prompt_preset references presets by ID
- Tool and MCP management: tools grouped by category (files, git, bash, etc.) with multi-select category dropdowns per role in UI; MCPs stored in mng_mcp_servers table; MCP Catalog accessible from main left nav under Workflows section

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
- `backend/memory/memory_work_items.py` — score 30.0 (28 commits, 1378 lines)
- `backend/memory/memory_files.py` — score 20.0 (18 commits, 1176 lines)
- `backend/routers/route_projects.py` — score 19.0 (17 commits, 1693 lines)
- `backend/core/db_migrations.py` — score 13.0 (11 commits, 3304 lines)
- `backend/agents/mcp/server.py` — score 11.0 (9 commits, 854 lines)
- `ui/frontend/views/work_items.js` — score 11.0 (9 commits, 2595 lines)
- `backend/routers/route_git.py` — score 9.0 (7 commits, 1691 lines)
- `ui/frontend/views/prompts.js` — score 7.0 (5 commits, 1606 lines)
- `backend/routers/route_agent_roles.py` — score 7.0 (5 commits, 1193 lines)

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
_Last updated: 2026-04-29 19:23 UTC_