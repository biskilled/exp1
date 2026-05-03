<!-- Last updated: 2026-05-03 20:46 UTC -->
# aicli
_2026-05-03 20:46 UTC | Memory synced: 2026-05-03_

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
- data/
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
- **frontend_framework**: Vanilla JS (Vite) + Electron
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) with per-node temperature/top_p/provider/model/max_iterations overrides
- **code_parser**: tree-sitter (Python/JavaScript/TypeScript) with 180-day recency-weighted hotspot scoring
- **mcp_transport**: Stdio MCP server with 10 tools; unified REST dispatch
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **pipeline_config**: YAML files (8 pipelines in workspace/_templates/pipelines/)

## Key Architectural Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts) → approved work items (mem_work_items); ONLY approved items (UC/FE/BU/TA prefix) embed to pgvector; re-embedding on item change automatic via update() → _embed_work_item()
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; CLAUDE.md, CODE.md, PROJECT.md all regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Role YAML as factory defaults: workspace/_templates/pipelines/roles/*.yaml are read-only templates seeded with ON CONFLICT DO NOTHING on backend startup; mng_agent_roles DB is single source of truth at runtime; base_snapshot JSONB stores pristine state
- System prompts: 3 shared canonical presets (Coding—General, Design & Planning, Review & Quality) in workspace/_templates/pipelines/system_prompts.yaml; all roles default to one preset; system_roles table contains only 3 canonical entries
- Agent execution: roles define identity/behavior (system_prompt, provider/model, temperature/top_p, tools, mcp, max_iterations); pipeline nodes can override provider/model/temperature/top_p/max_iterations per stage; nodes default to role values when not overridden
- Pipeline execution: 4-agent async DAG triggered on approved items; executed via asyncio.gather; max_iterations mandatory per node; per-node checkboxes: max_retry, stateless, continue-on-fail, approval-gate; mode_use_case and mode_item flags control visibility/executability; pipeline reports save to workspace/{project}/documents/pipelines/{pipeline_name}/{ddmmyy_HHMM}_{uc_slug}.md
- Architect role mandatory research sequence: search_memory → get_project_facts → search_features → list_dir → read_file (in order); outputs file_analysis with current_state and required_changes per file; acts as information gatherer for downstream developer
- Code Reviewer role outputs structured_out JSON with per-item score (0-5) and reasoning; verdict zone displays items_reviewed table after pipeline completion with scores and brief acceptance reasoning
- Pipeline & role activation: Settings → Roles & Pipelines dual-pane shows all roles/pipelines with activation checkboxes; only activated items appear in main tabs and are executable; pipeline activation requires all constituent roles to be activated
- Tool category bundles: tool selection by category (git/files/memory) instead of individual items; categories show tool count; multi-select in role editor
- Execute bar unified input: output folder combobox + searchable project docs dropdown + multi-file upload; files shown as removable chips; supports multiple document and file selections; per-role and per-pipeline execution modes
- Pipeline execution entry points: (1) Pipelines tab with node diagram and exec bar, (2) /pipeline [name] slash command in Chat, (3) /role [name] slash command for direct role execution, (4) Use Cases section with approval gating; each mode (use_case/item) independently togglable
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech_tags from project_state.json tech_stack
- Loop detection: agent._detect_loop now requires identical tool calls (same name + args) 3× in a row to trigger, not just same tool name; fixes false positives when iterating over multiple work items with search_memory

## In Progress

- Verdict zone per-item scores display: items_reviewed table showing FE####/BU####/etc with scores 0-5 and reasoning; working but LLM sometimes outputs 'Thought:' continuation instead of final JSON, preventing structured_out parsing
- Approval/rejection UI flow: approval buttons now use window._ucApprovePipelineRun() instead of inline api reference (ReferenceError fixed); flows to backend PATCH /pipeline/{run_id}/approval endpoint
- Pipeline report markdown generation: saving to workspace/{project}/documents/pipelines/{pipeline_name}/{ddmmyy_HHMM}_{uc_slug}.md using in-memory _stage_mem data collected during execution; folder and filename now editable via PATCH endpoint
- Resizable execution panel in use case view: left-edge drag handle with 7px col-resize cursor, min 300px / max 85% viewport, persists to localStorage; panel width syncs with Documents tree visibility
- Per-role execution logs in use case panel: global 'Execution Log' toggle removed; each stage (architect/developer/reviewer) now has individual <details> log toggle showing ReAct steps (tool calls, observations, final output)
- Batch document delete: DELETE /documents/batch endpoint with checkbox selection in Documents tab; checkbox state managed per-file with removable chips showing selected paths

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
_Last updated: 2026-05-03 20:46 UTC_