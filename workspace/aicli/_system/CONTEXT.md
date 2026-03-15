# Project Context: aicli

> Auto-generated 2026-03-15 17:41 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 86
- **Last active**: 2026-03-15T17:39:53Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl with rotation support, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Anthropic), OpenAI, DeepSeek, Gemini, Grok — independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config + loop-back support
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; always-on (DB best-effort)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server — 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK for unlimited nesting, due_date tracking)

## In Progress

- Commit-to-prompt linking fully operational — source_id timestamp stored in commit_log.jsonl; bidirectional tagging via POST /entities/events/tag-by-source-id; multiple commits per session linked to originating prompt (2026-03-14)
- History rotation fully implemented — /memory triggers rotation at configurable row threshold (default 500); creates timestamped archive (history_YYMMDDHHSS), rotates original to history.jsonl (2026-03-14)
- Tag cache persistence in history view — all categories/values loaded once on tab open; zero DB calls during tag picker; color preservation on save prevents thrashing (2026-03-14)
- Project memory layers (PROJECT.md + CLAUDE.md) fully aligned to v2.2.0 — all features documented: nested tags, commit linking, session persistence, tag cache, graph workflows, history rotation (2026-03-14)
- Session phase labeling and AI suggestions banner stable — 'Phase:' label in tag bar; amber banner with suggestions between tag bar and messages; works without PostgreSQL via best-effort DB (2026-03-10)
- Port stability and Electron restart resolved — freePort() kills stale uvicorn via lsof; before-quit cleanup via process.exit() eliminates bind address conflicts (2026-03-10)

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search; per-project DB tables via project_table()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step; Vite dev server only
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing without login
- All LLM providers as independent adapters; server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Tag cache loaded once on project tab open: zero DB calls during chat/planner; batch updates only on explicit save
- History rotation on /memory call: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS), original becomes history.jsonl
- Commit-to-prompt linking: source_id (history.jsonl timestamp) stored in commit_log.jsonl; bidirectional via POST /entities/events/tag-by-source-id
- Port binding safety: freePort() kills stale uvicorn processes before restart; Electron cleanup via process.exit()
- AI suggestions as dedicated amber banner between tag bar and messages; always-on (DB best-effort), synthesized by Claude Haiku from /memory
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- MCP server (stdio): 8 tools for integration with Claude CLI and external agents
- Session phase labeling: 'Phase:' tag bar selector; multiple commits per session each tagged to originating prompt via source_id

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

**[2026-03-15 17:28]** `claude_cli/claude`  
→ Taggin - there is a wau to add tags in History, commit and chat - which is good. can you make sure all is aligned to the
← _149 tags, 0 duplicates. Everything is clean. Here's a summary of all changes:  ---  **No duplicates** — confirmed: 149 event tags, 0 duplicates. The backend uses `ON CONFLICT DO NOTHING` on every tag _

**[2026-03-15 16:47]** `claude_cli/claude`  
→ Pagination - I do see now in the chat only 24 prompts (there are much more) can you add pagination < > 24/xxx on the top
← _All changes are working. Here's a summary:  **Backend — archive files included** - `_load_unified_history()` now reads `history.jsonl` + all `history_*.jsonl` archives - Result: **204 entries** (was 2_

**[2026-03-14 21:36]** `claude_cli/claude`  
→ Something wit hooks is not working now, as I do not see any new prompts / llm response adding into history.jsonl . also 
← _Everything is working. Here's a summary of all fixes:  ---  **1. Hook fixed — noise filtered at write time** - The deployed hook (`workspace/aicli/_system/hooks/log_user_prompt.sh`) was the old versio_

**[2026-03-14 19:08]** `claude_cli/claude`  
→  I do see session_tags.json - is it used ? Also - history.jsonl start to be very large and I would like to start rotate 
← _Everything works. Here's the summary of what was completed:  **History rotation — done:** - `_rotate_history()` was already in `projects.py`; added `log = logging.getLogger(__name__)` and wired up the_

**[2026-03-14 13:59]** `claude_cli/claude`  
→ I do see that there is a link between commit and session ID. is it possible to have link between commit/push and prompt 
← _It worked. "Links created: 0" means they already existed from the previous run (conflict). The sample shows 5 real links:  - `d0f14c21` → prompt "It is lookls like hooks are not working now..." - `951_

**[2026-03-14 13:11]** `claude_cli/claude`  
→ can you run /memory, to make sure all updated. also can you check that system is aligned to CLAUDE.md (memroy layers) pr
← _`GET /graph/` returns `{"workflows":[]}` — the graph router is live and the tables are working. Everything is now aligned. Here's the full summary of what was done:  ---  ### Memory + Alignment Update_

**[2026-03-14 13:04]** `claude_cli/claude`  
→ I do see the option to add tag in history - can you make sure all tags are loaded only once into mermory (to save db cal
← _Everything looks correct. Here's a summary of all changes made:  ---  ### Changes  **`ui/frontend/views/history.js`**  1. **Tag cache loaded once on tab open** — `_renderChat` now includes `listCatego_

**[2026-03-14 11:10]** `claude_cli/claude`  
→ I do have some concern how commit/hash are linked to prompts/llm answers. also are tagging is currently works in my syst
← _All changes are done. Here's a summary of what was implemented:  ### Changes  **`ui/backend/routers/entities.py`** — new endpoint `POST /entities/events/tag-by-source-id`: - Accepts `{ source_id, enti_

**[2026-03-13 17:44]** `claude_cli/claude`  
→ I am siting with my freid and try to explain him wha is this system is about ? can you explain that shortly ?
← _**aicli** is a shared AI memory platform for developers.  The core problem it solves: when you use different AI tools (Claude CLI, Cursor, ChatGPT in the browser, etc.), each one starts from scratch —_

**[2026-03-10 03:22]** `claude_cli/claude`  
→ I understand the issue. I am using your claude cli and hooks to store propts and llm response. hooks also managing the c
← _All clean. Here's the full picture:  ---  **No hook changes needed.** The `auto_commit_push.sh` hook already writes `session_id` to `commit_log.jsonl` on lines 181 and 294. The data connection exists._

**[2026-03-10 03:16]** `ui/claude`  
→ hellow, how are you ?
← _Hello! I'm doing well, thanks for asking. Ready to help with the **aicli** project.  Looking at the context, it seems you've been making good progress — recent work includes AI suggestion banners, ses_

**[2026-03-10 03:14]** `claude_cli/claude`  
→ Are you using the mcp server in order to reciave all project information ? Also, I do not see any sujjestion in any sess
← _---  Now let me answer your three questions clearly:  ---  **1. Am I (Claude Code) using the aicli MCP server?**  No. I'm reading your files directly using the Read/Grep/Bash tools. The MCP server (`u_

**[2026-03-10 02:57]** `claude_cli/claude`  
→ can you run /memory and run some tests? I do not see any sujjestion on all the existing session there are. also I do not
← _All clean (only the expected module resolution errors from Node's ES module checker, no syntax errors).  ---  Here's everything that was done:  ### 1. `/memory` suggestions — fixed to work without Pos_

**[2026-03-10 02:40]** `claude_cli/claude`  
→ can you run /memory, and make the UI more clear. add your sujjestion in a clear place where user can understand it is ai
← _Only the expected module resolution error (no syntax errors). Here's a summary of all changes:  **1. "Session:" → "Phase:"** in the tag bar label — it's the phase selector, not a session identifier.  _

**[2026-03-10 02:33]** `claude_cli/claude`  
→ Where do I click accept , is it in the Chat at the top ? I dont see that
← _The tag bar is the **thin bar at the top of the chat area**, right below the title and above the messages. After running `/memory`:  1. The bar will show amber/gold italic chips like: `✦ auth-refactor_
