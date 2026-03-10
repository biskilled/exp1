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
├── providers/             ← LLM adapters (Claude, OpenAI, DeepSeek, Gemini, Grok)
├── core/                  ← Memory, session, git, hooks, analytics, cost tracking
├── workflows/             ← YAML workflow executor
└── ui/
    ├── electron/          ← Electron shell (BrowserWindow, xterm.js, Monaco)
    ├── frontend/          ← Vanilla JS UI (no framework, no bundler)
    │   ├── views/         ← chat.js, entities.js, history.js, graph_workflow.js, admin.js …
    │   └── api.js         ← unified fetch wrapper for all backend endpoints
    └── backend/           ← FastAPI (localhost:8000)
        ├── routers/       ← auth, chat, projects, admin, billing, git, history,
        │                     workflows, entities, search, graph_workflows
        ├── core/          ← auth, pricing, api_keys, llm_clients, embeddings, database
        └── data/          ← ALL server data (api_keys.json, users.json, pricing.json…)

workspace/                 ← CONTENT — portable, per-project, version-controllable
├── _templates/
│   ├── hooks/             ← Canonical hook scripts (log_user_prompt, auto_commit_push…)
│   ├── workflows/         ← Shared workflow YAML templates (planned)
│   └── {blank,python_api,quant_notebook,ui_app}/
└── {project}/
    ├── PROJECT.md         ← Living project doc (this file)
    ├── project.yaml       ← Project config (code_dir, provider, git settings)
    ├── prompts/
    │   ├── roles/         ← Agent role system prompts
    │   └── {feature}/     ← Feature-specific prompts
    ├── workflows/         ← YAML workflow definitions
    └── _system/
        ├── history.jsonl      ← ALL interactions (all LLMs, all tools)
        ├── project_state.json ← Structured metadata + next_phase_plan
        ├── CONTEXT.md         ← Auto-generated project overview
        ├── claude/CLAUDE.md   ← Claude Code system prompt (synced to code_dir)
        ├── claude/MEMORY.md   ← Distilled history (synced to code_dir)
        ├── cursor/rules.md    ← Cursor AI rules (synced to .cursor/rules/)
        └── aicli/context.md   ← Compact CLI injection block
```

### Database Schema

**Shared tables** (project column filter):
`users`, `usage_logs`, `transactions`, `session_tags`, `entity_categories`, `entity_values`

**Per-project tables** (table name = project, no project column):
`commits_{p}`, `events_{p}`, `embeddings_{p}`, `event_tags_{p}`, `event_links_{p}`

Created lazily via `db.ensure_project_schema(project)` on project create/load.
Migrated from old shared tables via `POST /admin/migrate-project-tables`.

---

## Features

### Implemented ✓

**Memory & Context**
- [x] 5-layer memory architecture with `/memory` → LLM synthesis (Haiku) + incremental ingest
- [x] Unified history.jsonl: all sources (UI, Claude CLI, aicli CLI, workflow) → single file
- [x] Per-LLM output files: `_system/claude/CLAUDE.md`, `MEMORY.md`, `cursor/rules.md`, `aicli/context.md`, `copilot.md`
- [x] JSONL keyword/tag/feature memory search
- [x] Cross-provider session handoff: save/restore messages between CLI sessions
- [x] `_system/aicli/context.md` prepended to every CLI prompt automatically

**Semantic Search**
- [x] pgvector (text-embedding-3-small, 1536-dim) — per-project `embeddings_{p}` table
- [x] Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file-diff
- [x] Metadata filters: language, doc_type, file_path, chunk_type
- [x] `POST /search/semantic` + `GET /search/ingest`

**Entity / Knowledge Graph**
- [x] Entity categories (feature, bug, task, component, phase, doc_type, customer) — per project
- [x] Entity values (named instances, status: active/done/archived)
- [x] Events: raw event log (prompts, commits, docs) in per-project `events_{p}` table
- [x] Event tags: many-to-many `event_tags_{p}` → links events to entity values
- [x] Event links: directed relationships (`implements / fixes / causes / relates_to`) in `event_links_{p}`
- [x] Auto-tag suggestions: session tags applied immediately; Haiku suggests entity values
- [x] Bulk session tagging: `POST /entities/session-tag` — tags all session events at once
- [x] `POST /entities/events/sync` — imports history.jsonl + commits → events (idempotent)
- [x] LLM relationship detection: keyword (fix/close/resolve → bug link) + Haiku semantic links

**Projects Tab (UI)**
- [x] Features / Tasks / Bugs table with status toggle, archive, delete
- [x] Inline create form (type selector + name + description)
- [x] `↻ Sync` button → `POST /entities/events/sync` to update event_count
- [x] Per-project event counts displayed per entity value

**History Tab (UI)**
- [x] Unified sessions tab: all sources (ui/claude_cli/workflow) with source badges
- [x] Commits tab: red border for untagged, inline phase dropdown, editable feature/bug cells
- [x] Tags (⬡) tab: 3-column layout (categories | values | events) with tag picker modal

**Graph Workflows**
- [x] Async DAG executor with `asyncio.gather` for parallel nodes
- [x] Loop-back edges supported (max_iterations cap)
- [x] Cytoscape.js UI: drag-save positions, connect mode for edges, run log polling
- [x] CRUD REST API for workflows, nodes, edges, runs
- [x] Fire-and-forget: embed node outputs + refresh memory after each run

**Prompt Management**
- [x] Workspace prompt folders: `prompts/roles/`, `prompts/{feature}/`
- [x] Role-based system prompts loaded per provider
- [x] Prompts UI: recursive folder tree + textarea editor
- [x] `/compare <prompt.md>` — multi-LLM prompt comparison

**Providers (CLI)**
- [x] Claude: Anthropic SDK, streaming, tool use, MCP
- [x] OpenAI: chat completions, streaming
- [x] DeepSeek: OpenAI-compat API, streaming
- [x] Gemini: google-generativeai SDK, streaming
- [x] Grok: xAI OpenAI-compat API, streaming
- [x] BaseProvider: retry (3 attempts, 1s/3s/10s), provider fallback

**Auto-Deploy / Git**
- [x] Claude Code Stop hook → auto_commit_push.sh after every response
- [x] Backend `POST /git/{project}/commit-push`: LLM-generated commit messages
- [x] Auto-pull before commit; conflict detection

**Billing & Usage**
- [x] Multi-user roles: admin / paid / free
- [x] Server-managed API keys (admin panel → api_keys.json)
- [x] Per-user balance, markup pricing per provider, free-tier limits
- [x] Coupons; transaction log; provider usage fetch from Anthropic + OpenAI APIs
- [x] Manual provider balance tracking

**MCP Server**
- [x] Standalone stdio MCP server registered in `.mcp.json` + `.cursor/mcp.json`
- [x] 8 tools: search_memory, get_project_state, get_recent_history, get_roles, get_commits, get_session_tags, set_session_tags, commit_push

**Infrastructure**
- [x] Per-project DB schema: `project_table()` + `ensure_project_schema()` (lazy init on load)
- [x] `POST /admin/migrate-project-tables`: migrate old shared tables → per-project tables
- [x] UI installer: `install.sh` (one-time setup) + `update.sh` (git pull) + `start.sh`
- [x] `~/.aicli/config.json`: links aicli_dir + workspace_dir; read by config.py at startup
- [x] Railway deployment: Dockerfile + railway.toml

---

## In Progress ◷

### Project Management Page Redesign

**Goal**: transform the Projects tab from a simple CRUD list into a real project management view where AI workflow outputs feed directly into tracked features and tasks.

Planned components:
- **Project overview card**: active features (count + top 3 by event_count), open tasks, last commit, workflow runs, LLM cost this week
- **Activity timeline**: unified event stream (prompts + commits + workflow runs) per project, filterable by type/date/entity
- **Feature detail panel**: click feature → see linked events, commits, workflow runs, related bugs
- **Kanban board** (optional): columns = backlog / in-progress / review / done, drag to move status
- **Quick actions**: + New Feature, + New Task, + New Bug, Run Workflow, Open in Terminal

### Workflow Process Improvements

**Goal**: make workflow runs first-class project artifacts — linked to features, creating tasks, visible in the project timeline.

Planned:
- **Step-by-step run log**: per-node timing, token count, cost, output preview in collapsible rows
- **Re-run from node**: click any completed node and re-run from that point with edited prompt
- **Workflow templates library**: pre-built YAMLs (feature_cycle, code_review, bug_fix, doc_update) in `workspace/_templates/workflows/`
- **Feature-linked workflow runs**: select which feature/task a run belongs to; auto-tag all emitted events
- **Workflow result → task**: workflow output can create/update a task entity value, closing the loop

---

## Planned ○

- Global role library: `workspace/_templates/roles/` with 6 default roles shipped on install
- Memory auto-compaction at token limit (compress old entries → LLM summary)
- `/deploy <aws|railway>` — one-command deploy from CLI
- Stripe real payment integration (placeholder currently returns "coming soon")
- Admin dashboard: revenue summary, top users by spend, model cost breakdown
- Electron app packaging: ship with embedded Python 3.12 to remove system dep friction

---

## Key Patterns

### Single Pricing Source
`ui/backend/data/provider_costs.json` is the single source of truth for all LLM pricing.
`core/cost_tracker.py` + `core/provider_costs.py` + `core/pricing.py` all read from it.

### Per-Project DB Tables
```python
db.project_table("commits", "myproject")  # → "commits_myproject"
db.ensure_project_schema("myproject")     # creates all 5 tables if not exist
```
Called automatically on project create (`POST /projects/`) and project load (`GET /projects/{name}`).

### Provider Contract
```python
class BaseProvider:
    def send(self, prompt: str, system: str = "") -> str: ...
    def stream(self, prompt: str, system: str = "") -> Generator[str, None, None]: ...
```

### Auth Architecture
- `REQUIRE_AUTH=false` (local dev) — no login gate
- `REQUIRE_AUTH=true` (Railway/cloud) — JWT required on all routes
- `DEV_MODE=true` — synthetic admin user, no balance deduction
- First registered user = admin automatically

### UI Tab Structure
```
sidebar tabs:
  chat      → views/chat.js      — SSE streaming chat with tag bar
  summary   → views/summary.js   — PROJECT.md viewer/editor
  prompts   → views/prompts.js   — role + feature prompt tree
  code      → views/files.js     — folder tree + file viewer
  graph     → views/graph_workflow.js — Cytoscape.js DAG editor
  projects  → views/entities.js  — Features/Tasks/Bugs management  ← NEXT PHASE
  history   → views/history.js   — sessions + commits + tags tabs
  admin     → views/admin.js     — 6-tab admin panel
```

---

## Open Questions

- Should the Kanban board state (column positions) live in `entity_values.status` or a separate `board_state` JSONB?
  → Proposal: use `entity_values.status` (backlog/in-progress/review/done) — already exists, no schema change
- Should workflow runs auto-create entity events without user confirmation?
  → Proposal: yes, but show in timeline as auto-tagged so user can dismiss
- Should `workspace/_templates/workflows/` be versioned separately (git submodule)?
  → Leaning: no — keep flat in the main repo, update via `bash ui/update.sh`

## Recent Work

- Session tag persistence — fixed GET /entities/session-tags endpoint to query event_tags_{p} joined to events/values/categories; frontend caches and refreshes on save
- Planner UI discoverability — added 3-dot menu (⋯) per tag row with edit/archive/restore/delete actions; improved button visibility for action triggers
- Database query optimization — batch load all project tags/categories on project access, cache in tagCache.js, eliminate per-action SQL calls during chat/planner interactions
- Chat picker refactor — zero DB calls during selection, reads from cached categories/values, real-time filter with floating dropdown, root-level tag creation only
- Port binding and startup stability — implemented freePort() to kill stale uvicorn, fixed Electron before-quit cleanup via process.exit(), resolved 127.0.0.1:8000 bind conflicts
- Tag bar visibility and session persistence — fixed overflow:hidden clipping in chat tag bar, ensured tags persist across session switches via getEntitySessionTags() endpoint
