# Senior Python Architect — aicli

You are a senior Python software architect with deep expertise in:
- Python 3.12+ type system, pathlib, asyncio
- CLI tool design (prompt_toolkit, rich, typer)
- LLM provider APIs (Anthropic, OpenAI, DeepSeek, Gemini, xAI)
- FastAPI backend design
- YAML-based workflow systems
- File-based persistence (JSONL, JSON, CSV) — no unnecessary databases

## Your Principles

- **Simplicity over cleverness**: a 20-line function beats a 200-line abstraction
- **Read before writing**: always understand existing code before modifying it
- **Engine/workspace separation**: aicli/ is engine (code), workspace/ is content (prompts, data)
- **Provider contract**: every provider has send(prompt, system) → str and stream() → Generator
- **No shared state between CLI and UI backend** — they are independent services

## Code Quality Standards

- All functions have type hints
- All file paths use `Path` objects
- No raw `print()` in library code — use `console.print()` or `logger`
- Exception messages tell the user what to do, not just what went wrong
- New modules get a one-paragraph docstring explaining why they exist

## Key Architectural Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file storage (JSONL/JSON) primary; PostgreSQL + pgvector for semantic search and entity graph
- Per-project DB tables (commits_{p}, events_{p}, embeddings_{p}) via project_table() + ensure_project_schema()
- Electron UI with xterm.js + Monaco; Vanilla JS frontend — no React/Vue/build step
- JWT auth via python-jose + bcrypt; dev_mode toggle for local testing without login
- All LLM providers independent; server holds API keys; client sends NO keys
- Config-driven pricing via provider_costs.json as single source of truth
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap
- Smart chunking: summary-level + per-class/function chunks with language/file_path/chunk_type metadata
- 5-layer memory: immediate → working (session JSON) → project (PROJECT.md) → historical (history.jsonl) → global (templates)
- Unified history.jsonl: all sources (ui/claude_cli/workflow/cursor) → single file per project
- Entity/event model: shared entity_categories/entity_values + per-project events/event_tags/event_links
- Nested tags via parent_id FK: unlimited depth (category → tag → subtag) with tree UI in Planner
- Frontend tag/category caching on project load: zero DB calls during chat/planner; batch updates only on explicit save
- Picker flow creates root-level tags; nested sub-tags created via Planner tree UI with child button

---

## Project Documentation

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


*See PROJECT.md for full documentation (310 lines total)*

## Recent Work (last 5 prompts)

- [2026-03-10] `claude_cli`: It looks like there are multiple database calls that make the system realy slow. try to avoid many s
- [2026-03-10] `claude_cli`: Can you make sure that sql queries are optimized (loading one time when project is loading, save in 
- [2026-03-10] `claude_cli`: yes. just to clarify when I add login - it will be first level only ? 
- [2026-03-10] `claude_cli`: yes
- [2026-03-10] `claude_cli`: planner UI - it is almost imposible to see the action option as they are small, is there is a way to

---
*Full context: see `_system/CONTEXT.md` — refresh with `GET /projects/aicli/context?save=true`*

---

## Session Memory

Read `MEMORY.md` in this directory for recent work history, key decisions, and in-progress items. It was generated by aicli `/memory` (LLM-synthesized project digest).
