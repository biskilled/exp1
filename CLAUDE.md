<!-- Last updated: 2026-04-30 00:10 UTC -->
# aicli
_2026-04-30 00:10 UTC | Memory synced: 2026-04-29_

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
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML pipeline + per-node temperature/top_p overrides
- **code_parser**: tree-sitter (Python/JavaScript/TypeScript) with 180-day recency-weighted hotspot scoring
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **mcp_transport**: Stdio MCP server with 10 MCPs; unified REST dispatch

## Key Architectural Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts via /memory POST + Haiku synthesis) → approved work items (mem_work_items with wi_parent_id hierarchy); ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; CLAUDE.md, CODE.md, PROJECT.md all regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Role YAML factory defaults: workspace/_templates/pipelines/roles/role_*.yaml are read-only templates; ON CONFLICT DO NOTHING seeds only new roles on startup; mng_agent_roles DB is single source of truth at runtime; UI edits persist in DB only; base_snapshot JSONB stores pristine state; refresh endpoint reloads YAML and updates DB
- System prompts consolidation: 3 shared presets in workspace/_templates/pipelines/system_prompts.yaml (Coding — General, Design & Planning, Review & Quality); all 10 roles default to canonical preset; system roles cleaned to 3 canonical entries only
- Role parameters: system_prompt + system_prompt_preset (references 3 shared presets), provider/model, tools (by category: git/files/memory), mcp (multi-select), max_iterations, temperature, top_p configured per role; base_snapshot stores pristine role state for restore
- Agent execution: roles define identity/behavior (system_prompt, provider/model, tools, mcp, max_iterations, temperature, top_p); provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) all accept temperature parameter; pipeline stages can override temperature/top_p at execution time
- Tech tag auto-detection: reads tech_stack from project_state.json instead of hardcoded regex; tags validated against actual project technologies in _build_tech_tags_block()
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech_tags from project_state.json tech_stack
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval
- Code.md generation: per-symbol diffs via tree-sitter with file coupling/hotspot tables; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio)
- Embeddings strategy: ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector; code.md, project_state.json, project facts, prompts, commits never embed
- MCP server: 10 MCPs (github, postgres, slack, linear, jira, stripe, contentful, supabase, s3, openapi) with multi-select in role editor; unified REST dispatch; stdio transport, local machine, no auth required
- 4-agent async DAG pipeline: PM (acceptance criteria) → Architect (implementation) → Developer (code) → Reviewer (QA); triggered only on approved items under approved use cases; executed via asyncio.gather; max_iterations mandatory; per-node temperature/top_p configurable in pipeline YAML
- Authentication: JWT (python-jose + bcrypt) with hierarchical Clients → Users → Projects; DEV_MODE toggle for passwordless local development; MCP runs with no auth (stdio-only, local)

## In Progress

- Automated commit hook execution: chore commits after Claude CLI sessions indicate auto_commit_push.sh integration working across multiple session IDs (1f8ecc78, 45ca1683, 5cf393d1)
- Session persistence & project state sync: repeated chore commits suggest project_state.json updates and memory layer transactions completing after each session
- Work item pipeline automation: commit patterns tracking feature/bug closure via regex matching (fixes/closes work item IDs)
- Role YAML template synchronization: system prompts and provider parameters validated against base_snapshot on session restart
- Memory artifact extraction: /memory POST endpoint processing project context via Haiku synthesis and updating mem_ai_project_facts table
- Pipeline DAG executor testing: asyncio.gather stage coordination with temperature/top_p parameter overrides across 4-agent workflow

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
_Last updated: 2026-04-30 00:10 UTC_