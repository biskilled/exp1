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

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state
- Dual storage model transitioning to DB-only: PostgreSQL 15+ with pgvector (1536-dim) for semantic search; JSONL currently used but migration planned
- Electron UI with xterm.js + Monaco editor + Cytoscape.js; Vanilla JS frontend (no framework/bundler); Vite dev server
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; 3-tier roles (admin/paid/free); per-user encrypted API keys
- All LLM providers as independent adapters (Claude Haiku for synthesis); server holds API keys; client sends none
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape.js visualization with 2-pane approval
- Memory synthesis: Claude Haiku dual-layer (raw JSONL → interaction_tags → 5 output files); smart chunking per language/section
- Per-project tables: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared auth/usage tables
- Tags load once on project access into memory; cache invalidation on session/project switch forces re-load from DB
- SQL queries as module-level constants (_SQL_VERB_ENTITY pattern); dynamic query building via build_update() for safe parameterization
- MCP server (stdio) with 12+ tools; configured via env vars (BACKEND_URL, ACTIVE_PROJECT); embedding and data retrieval
- Backend modular: core/ for infrastructure, data/ (dl_ prefix) for data access, routers/ for HTTP endpoints, agents/ for business logic
- Hierarchical data model: Clients contain multiple Users; authentication pattern: login_as_first_level_hierarchy
- _ensure_shared_schema pattern replaces ensure_project_schema; retry logic handles empty project list on first load
- Embeddings linked to tags: tag metadata captures context (auth→all authentication prompts; feature/bug→relevant code changes)

---

## Project Documentation

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


*See PROJECT.md for full documentation (383 lines total)*

## Recent Work (last 5 prompts)

- [2026-03-28] `claude_cli`: Before you continue - I would like to understand why in pr_interaction name is not change to pr_prom
- [2026-03-28] `claude_cli`: Yes please do that, and run /memory to check P0#1, and fix P1#5 and P1#3 . also is the system loadin
- [2026-03-28] `claude_cli`: What event insert into event table except prompts and new commits 
- [2026-03-28] `claude_cli`: What is the pr_event_links is used for ? how it is linking events?
- [2026-03-30] `claude_cli`: I would like to update my memory infrastrucutre, in order to have more reliable layers, better promp

---
*Full context: see `_system/CONTEXT.md` — refresh with `GET /projects/aicli/context?save=true`*

---

## Session Memory

Read `MEMORY.md` in this directory for recent work history, key decisions, and in-progress items. It was generated by aicli `/memory` (LLM-synthesized project digest).
