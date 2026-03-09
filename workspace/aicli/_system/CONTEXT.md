# Project Context: aicli

> Auto-generated 2026-03-09 04:12 UTC — do not edit manually.

## Quick Stats

- **Provider**: claude
- **GitHub**: https://github.com/biskilled/exp1.git
- **Code dir**: `/Users/user/Documents/gdrive_cellqlick/2026/aicli`
- **Sessions**: 43
- **Last active**: 2026-03-09T04:02:39Z
- **Last provider**: claude
- **Version**: 2.1.0

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows)
- **storage_primary**: JSONL (history.jsonl, commit_log.jsonl), JSON, CSV — flat file first
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Anthropic), OpenAI, DeepSeek, Gemini, Grok — all independent adapters
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server — 8 tools (search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push)
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder

## In Progress

- Project management page redesign — richer dashboard with metrics (event count, active features, recent commits, workflow runs), activity timeline, quick-action buttons
- Workflow ↔ project integration — link workflow runs to features/tasks; auto-create task events from workflow outputs; show workflow status per feature
- Workflow process improvements — better YAML editor UX, step-by-step run log with timing per node, re-run from any node, templates library
- Project overview dashboard — summary card per project: last activity, open tasks, active features, recent commits, LLM cost this week
- DB schema refactoring complete — project_table() and ensure_project_schema() deployed; per-project tables (commits_{p}, events_{p}, embeddings_{p})
- Memory synthesis pipeline — /memory endpoint generates 4 per-LLM summary files; Haiku incremental synthesis; copy to code_dir for persistence

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search and entity graph — no SQLite/ChromaDB
- Per-project DB tables (commits_aicli, events_aicli, etc.) via project_table() + ensure_project_schema() — no full-table scans with project filter
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step
- JWT auth via python-jose + bcrypt (NOT passlib); dev_mode toggle for local testing without login
- All LLM providers independent; server holds API keys (api_keys.json); client sends NO keys
- Config-driven pricing — provider_costs.json is single source of truth; no hardcoded costs
- Multi-agent workflows: async DAG executor via asyncio.gather; loop-back edges with max_iterations cap
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata filters
- 5-layer memory: immediate (in-memory) → working (session JSON) → project (PROJECT.md + project_state.json) → historical (history.jsonl) → global (templates)
- /memory generates 4 per-LLM files + copies to code_dir; LLM synthesis via Haiku; incremental ingest
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Entity/event model: entity_categories + entity_values (shared) + per-project events/event_tags/event_links
- MCP server as standalone stdio process so Claude Code connects without backend running
- UI installer: install.sh (one-time) + update.sh (git pull + deps) + start.sh — never touches workspace/

---

## Project Documentation (PROJECT.md)

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-09 | Version 2.1.0_

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
| 9 | **Project management UI** — Feature/Task/Bug tracking tied to AI workflows | ◷ In Progress |

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


*...230 more lines in PROJECT.md*

---

## Recent Development History

**[2026-03-09 04:08]** `claude_cli/claude`  
→ Assuming I will improve the project management page, workflow processes. can you update /memory - so it can be used for 

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat
← _Implementation complete. Here's a summary of what was done:  ---  ## Summary  ### Part 1 — DB Schema Refactoring  **`core/database.py`** - Added `project_table(base, project)` static method — returns _

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat

**[2026-03-09 03:50]** `claude_cli/claude`  
→ <task-notification> <task-id>a6ebd0b686c66a5d7</task-id> <tool-use-id>toolu_01Jci8F3L8X9pwNVWA2V2Hk8</tool-use-id> <stat
