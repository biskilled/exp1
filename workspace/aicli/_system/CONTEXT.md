# Project Context: aicli

> Auto-generated 2026-03-16 17:43 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 107
- **Last active**: 2026-03-16T01:35:18Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot, aicli rules)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 12+ tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push, create_entity, update_entity, list_entities, get_feature_status)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p} (phase/feature/session_id indexed), embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, and MCP integration settings

## In Progress

- Config externalization and optimization (2026-03-16) — backend_url, haiku_model, db_pool_max moved to config.py; removed unused methods; added /health check for MCP readiness
- Memory distillation pipeline refinement (2026-03-16) — dual-layer summarization (raw JSONL → interaction_tags → memory files); fixed session_bulk_tag() to write to both event_tags and interaction_tags
- MCP tool expansion for project management (2026-03-16) — implemented create_entity, update_entity, list_entities, get_feature_status tools; verified all return accurate JSON
- Work item lifecycle tracking (2026-03-15/16) — phase/feature/session_id now real indexed columns in events_{p}; status + due_date tracked in entity_values; backfill on session phase change works
- Tag deduplication and cross-view synchronization (2026-03-15) — 149 tags with 0 duplicates; removal via ✕ buttons propagates across Chat/History/Commits; inline commit display per prompt
- Pagination and filtering across all views (2026-03-15) — Chat/History/Commits show offset ranges (e.g., '1–100 / 204') with ◀ ▶ navigation; unified history loads all archives; phase filter respects backfilled entries

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage primary (JSONL with rotation on /memory); PostgreSQL + pgvector for semantic search; per-project DB tables
- Electron UI with xterm.js + Monaco; Vanilla JS frontend (no React/Vue/bundler); Vite dev server for local dev only
- JWT auth via python-jose + bcrypt; dev_mode toggle; 3 roles: admin/paid/free
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Commit-to-prompt linking via source_id timestamp in commit_log.jsonl; bidirectional tagging via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- AI suggestions as dedicated amber banner between tag bar and messages; Claude Haiku synthesis; auto-save to session with category inheritance
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8+ tools for integration with Claude CLI and external agents
- Session phase (required field) loads from DB on init; PATCH /chat/sessions/{id}/tags saves phase; backfills history.jsonl; ordered by created_at
- Real DB columns for phase, feature, session_id in events_{p} with indexes; tag cache loaded once per project tab (zero DB calls during chat)

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


*...258 more lines in PROJECT.md*

---

## Recent Development History

**[2026-03-16 17:42]** `claude_cli/claude`  
→ Can you run the /memory and go over current architecure - how data is stored, how mcp is used, go ver all memory layer. 

**[2026-03-16 01:34]** `claude_cli/claude`  
→ Can you summersie all improvement - would that make the systme better perfromed , would memroy work better? doad mcp can
← _## Complete System Improvement Summary  ---  ### What Was Built (7 Parts)  **Before:** Every LLM call got either 40 raw JSONL entries (noisy, expensive) or a CLAUDE.md (too coarse). Tags lived in per-_

**[2026-03-16 01:26]** `claude_cli/claude`  
→ After this refactor - can you check if tags are well used ? is memroy improved by new summersation process? will mcp can
← _Here's a complete answer to your questions:  ---  ## Audit Results + What Was Fixed  ### Tags — mostly good, one gap fixed The old `event_tags_{project}` system is fully wired: chat, history sync, and_

**[2026-03-16 00:48]** `claude_cli/claude`  
→ I have started to look in some other solution like https://github.com/danshapiro/trycycle and www.specrails.dev/docs/wor

**[2026-03-16 00:19]** `claude_cli/claude`  
→ I would like to optimise the code : check each file, make sure code is in used and all method are required. make sure th
← _All clean. Here's a summary of everything fixed:  ---  ## Optimization fixes applied  | Issue | File | Fix | |---|---|---| | `haiku_model` hardcoded in 6 places | `config.py` | Added `haiku_model: str_

**[2026-03-15 23:49]** `claude_cli/claude`  
→ 1,2,3,4,5 and 8. I would like to add also anotehr mng table to check how many prompt there are and prompt the user (in u

**[2026-03-15 23:38]** `claude_cli/claude`  
→ Is there is any addiotnal improvement that I can implemet for having full memroy , and project management lifecycle ? 
← _Based on the audit, here are the gaps and a prioritized roadmap:  ---  ## What's Missing — Prioritized  ### Quick Wins (low effort, high value)  **1. MCP `create_entity` tool** Claude CLI / Cursor can_

**[2026-03-15 23:29]** `claude_cli/claude`  
→ is it align to the 5 steps memory? is there is any addiotnal requirement in order to be able to retreivae details inform
← _All three enhancements are implemented and working. Here's a summary of what was done:  ---  **Three changes implemented:**  **1. `GET /entities/summary` — new endpoint in `entities.py`** Returns all _

**[2026-03-15 23:13]** `claude_cli/claude`  
→ now that there is porper tagging - can you make sure all is linked, mapped propery in databse schema and used properly f
← _Everything is working. Here's a summary of all changes made:  ---  ## What was changed and why  ### Schema (`core/database.py`) - Added `phase`, `feature`, `session_id` as **real columns** (not just J_

**[2026-03-15 22:57]** `claude_cli/claude`  
→ It looks good and working as expected. the issue now is how it is linked to Histroy chat and commit. as this is saved by
← _Now the full flow works. Here's a summary of everything fixed:  **Root causes and fixes:**  1. **History chat filter shows nothing for a phase** — History.jsonl entries had no `phase` field if the ses_

**[2026-03-15 22:51]** `claude_cli/claude`  
→ That looks better. the problem now is that on any change of the phase the session order is changed as well . is it possi
← _Two changes:  1. **Backend** — `patch_session_tags` no longer updates `updated_at` when saving tags. The session's timestamp stays frozen at when it was last messaged.  2. **Frontend** — `_loadSession_

**[2026-03-15 22:40]** `claude_cli/claude`  
→ I still do not see that fixed. the session that mandtory fields are not updates suppose to be maked with red. currently 
← _The full flow works. Here's what was changed and why:  **Root causes fixed:**  1. **Red `⚠` only on UI sessions** — removed the `s.source === 'ui'` condition. Now ALL sessions (UI, CLI, WF) without a _

**[2026-03-15 22:22]** `claude_cli/claude`  
→ Lets try to fix the first bug in the Chat session as it is not fixed. when I upload a session - I do not see the correct
← _The endpoint is live (404 "Session not found" is the correct response for a non-existent test ID). The fix is complete.  **Summary of what changed:**  The phase change listener in `chat.js` no longer _

**[2026-03-15 21:45]** `claude_cli/claude`  
→ Issue is not fixed - In Chat - I cannot change/update phase. also most chat session do not have the right phase now. and
← _Here's a summary of all fixes:  **Chat — phase change** (restored): - `_sessionId = null` is back → each phase gets its own new session → sessions have correct phase in metadata - `api.putSessionTags(_

**[2026-03-15 21:15]** `claude_cli/claude`  
→ The error still exists - When I change the phase (on chats) - I am not able to save. also when I switch between diffrent
← _All changes look good. Here's a summary of everything fixed:  **Issue 1 — Phase can't save** (root cause: `_sessionId = null` on phase change): - Removed `_sessionId = null` from phase change — phase _
