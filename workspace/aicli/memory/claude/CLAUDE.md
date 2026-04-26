<!-- Last updated: 2026-04-26 21:43 UTC -->
# Role: Developer — aicli

You are working on **aicli**.

## Key Architectural Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; .ai/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables for events, tags, facts, work items, features
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users → Projects
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules in agents/providers/ with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); commit deduplication by hash
- Database schema as single source of truth (db_schema.sql) with m001-m076 migration framework; INT PKs canonical order (id → client_id → project_id → user_id → created_at → updated_at → embedding)
- Work Items vs Use Cases separation: Work Items tab shows pending AI-classified items; Use Cases tab displays approved items with due dates, completion validation, auto-markdown generation
- Use Case lifecycle: due dates (calendar MM/DD/YY or day offset), completion validation (all descendants validated), completed_at timestamp, MD file auto-move to documents/completed/ on completion
- Drag-and-drop parent-child linking and merge functionality for work items with type validation (same-type only) and undo support via stored reverse API call closure
- Text selection enabled across UI for clipboard copy-paste; undo button in Work Items and Use Cases toolbars as persistent button (not popup)
- Template workspace refactor: _templates/ reorganized into cli/pipelines/hooks subdirectories with per-provider hooks; aicli/ folder synced with template changes

---

## Project Documentation

# aicli — Shared AI Memory Platform

_Last updated: 2026-04-26_

> **How this file works**
> - Sections marked `<!-- user-managed -->` are yours to edit freely — they feed directly into CLAUDE.md.
> - Sections marked `<!-- auto-updated by /memory -->` are refreshed automatically when you run `/memory`.
>   You can still edit them; `/memory` will merge its output in without discarding your additions.
> - Run `/memory` to regenerate CLAUDE.md, cursor rules, and all LLM prompt files from this document.

---

<!-- user-managed -->
## Vision

**aicli gives every LLM the same project memory.**

When you switch between Claude Code, the aicli CLI, Cursor, or the web UI, the AI picks up
exactly where you left off — same codebase context, same decisions, same feature history.
No more copy-pasting context. No more re-explaining your architecture.

---

<!-- user-managed -->
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
| 8 | **Role YAML** — All agent roles + pipelines defined in `workspace/_templates/` (no inline Python) | ✓ Refactored |
| 9 | **MCP server** — 10 tools: search_memory, get_project_state, tags, backlog | ✓ Implemented |

---

## Memory Architecture

```
Layer 1 — Raw Capture (mem_mrr_*)
  ├── mem_mrr_prompts        raw prompt/response pairs (session-tagged)
  ├── mem_mrr_commits        git commits (hash, msg, tags, diff_summary)
  ├── mem_mrr_commits_code   per-symbol diffs (tree-sitter: class, method, file)
  ├── mem_mrr_items          document/meeting items
  └── mem_mrr_messages       Slack/chat messages

Layer 2 — AI Events (mem_ai_events)
  Haiku digest + OpenAI embedding (text-embedding-3-small, 1536-dim)
  event_type: prompt_batch | commit | session_summary | item | workflow
  source_id: batch_{hash8}_{tagfp8} for commits; last prompt UUID for prompt batches
  Tags: only user-intent {phase, feature, bug, source} stored

Layer 3 — Structured Artifacts (mem_ai_project_facts)
  Durable facts ("uses pgvector", "auth is JWT")

Layer 4 — Work Items (mem_work_items)


*See PROJECT.md for full documentation (292 lines total)*

## Recent Work (last 5 prompts)

- [2026-03-30] `claude_cli`: It it still balnck. the error is Uncaught SyntaxError: Identifier '_esc' has already been declared t
- [2026-03-30] `claude_cli`: Is all table strucure is implemeted properly ? I dont see the table strucure ? 
- [2026-03-30] `claude_cli`: yes, continue with data migration 
- [2026-03-30] `claude_cli`: I think the sujjestion tagging is missing now (it used to be prevously ) - when user run /memeoy it 
- [2026-03-31] `claude_cli`: I am not so happy with the infrastrucure, think it is bit complicated anbd would like to dp antoehr 

---
*Full context: see `state/CONTEXT.md` — refresh with `GET /projects/aicli/context?save=true`*

## Code Hotspots

- `backend/memory/memory_code_parser.py` — score 58.9626 (2 commits, 788 lines)
- `backend/memory/memory_work_items.py` — score 16.0 (14 commits, 2621 lines)
- `ui/frontend/views/work_items.js` — score 11.0 (9 commits, 2595 lines)
- `backend/core/db_migrations.py` — score 10.0 (8 commits, 3250 lines)
- `backend/memory/memory_files.py` — score 8.0 (6 commits, 990 lines)
- `backend/routers/route_projects.py` — score 8.0 (6 commits, 1662 lines)
- `backend/routers/route_work_items.py` — score 5.0 (5 commits, 461 lines)

_Full details: `memory/code.md`_