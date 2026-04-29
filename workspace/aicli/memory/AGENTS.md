<!-- Last updated: 2026-04-29 15:06 UTC -->
# aicli
_2026-04-29 15:06 UTC | Memory synced: 2026-04-29_

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

- **language_cli**: Python 3.12
- **cli_framework**: prompt_toolkit + rich
- **backend_framework**: FastAPI + uvicorn
- **backend_auth**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **database**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **database_client**: psycopg2
- **frontend_framework**: Vanilla JS + Electron + Vite
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry
- **code_parser**: tree-sitter (Python/JavaScript/TypeScript) with 180-day recency-weighted hotspot scoring
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **mcp_transport**: Stdio MCP server with 14 tools; unified REST dispatch
- **memory_config**: YAML under backend/prompts/ + workspace/_templates/roles/

## Key Architectural Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts via /memory POST + Haiku synthesis) → work items (mem_work_items with wi_parent_id hierarchy); ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector (1536-dim, text-embedding-3-small)
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; all 3 output files (CLAUDE.md, CODE.md, PROJECT.md) regenerated from single JSON state in _write_root_files_with_ctx()
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001', 'resolve TA0003') in commit messages auto-set score_status=5 and score_importance=5 for user approval in review queue
- Code.md generation: per-symbol diffs via tree-sitter with file coupling/hotspot tables; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio) to prioritize recent changes
- Embeddings strategy: ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector; code.md, project_state.json, project facts, prompts, and commits never embed
- MCP server: 14 tools (search_memory, get_project_state, list_work_items, get_work_item, list_commits, search_commits, due_date_before filter, etc.) dispatched via REST endpoints in agents/mcp/server.py; stdio transport running locally on developer machine with no auth
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract; temperature, max_tokens, model configurable per role
- 4-agent pipeline: PM (acceptance criteria) → Architect (implementation plan) → Developer (code) → Reviewer (QA); triggered only on approved items under approved use cases; async DAG executor via asyncio.gather
- Authentication: JWT (python-jose + bcrypt) with hierarchical Clients → Users → Projects; DEV_MODE toggle for passwordless local development; MCP server runs with no auth (stdio-only, local machine)
- All backend LLM prompts stored in YAML: backend/prompts/command_memory.yaml (fact_extraction, conflict_detection, project_synthesis) + workspace/_templates/roles/ (role YAML only); delivery_type classification uses full project tech_stack context to improve pipeline routing accuracy
- Recursive CTE safety: all bounded to depth < 20 with safeguards; date cascade validation prevents re-parenting children to use cases with earlier due_dates
- Database optimization: batch queries replace N+1 patterns; single WHERE name = ANY(%s) per category for hotspot/coupling checks; token counting: len(text) // 4 (~4 chars per token); _update_item_tags uses executemany
- UI transparency badges: _waitingBadge() showing '⏳ X days waiting' (grey ≤3d, amber 4–7d, red >7d) for pending items and _openDaysBadge() showing '📂 X days open' for approved use cases
- Shared LLM memory across tools: Claude Code, aicli CLI, Cursor, and web UI all read the same knowledge base via /memory POST endpoint and project_state.json; ReAct checkbox enables/disables Thought/Action/Observation framework in agent execution

## In Progress

- Improve delivery_type and pipeline routing accuracy: added full project tech_stack context (frontend/backend/database keywords) to Haiku classifier system prompt to reduce misclassification (e.g., TA4001 'planner' now correctly maps to database instead of frontend)
- Remove unused role UI fields: deleted inputs, outputs, and role_type columns from mng_agent_roles; removed corresponding validation and serialization code; updated role edit dialog to eliminate unused form fields
- Fix undefined column errors: route_entities (line 359: t.lifecycle) and route_history (line 228: event_type) — columns removed in migration m080 but route code not yet updated
- Remove lifecycle tags from Planner UI: 11 active drag-and-drop, category display, archive toggle, and tagging UI errors related to deprecated lifecycle field
- Fix backend startup race condition: active project not displayed in project selector after startup; recent projects list missing aiCli project; likely init sequencing issue in project loader
- Optimize PROJECT.md file loading: currently >60s timeout when opening project; performance audit ongoing; may need database indices on project, wi_type, user_status or single-pass read refactoring

## Coding Conventions

- **Python style**: Python 3.12+; type hints on all new functions; no `from X import *`
- **Imports**: stdlib → third-party → local; each group alphabetically sorted
- **Async**: use `async`/`await` throughout FastAPI routes; no blocking calls in async context
- **DB access**: always use `db.conn()` context manager (psycopg2 pool); parameterized queries only
- **Error handling**: log with `log.warning()` for expected errors, `log.exception()` for unexpected; return 422/404 from routes, never 500 for known cases
- **Naming**: `snake_case` for Python; `camelCase` for JS; `UPPER_SNAKE` for module-level constants
- **LLM prompts**: all prompts in `backend/prompts/*.yaml`; load via `prompt_loader.prompts.content(key)`; never inline strings
- **Work items**: `user_status` is TEXT (`open|pending|

## Recently Changed

(no commit history indexed yet)

---
_Auto-generated by aicli memory system. Run `/memory` to refresh._
_Last updated: 2026-04-29 15:06 UTC_