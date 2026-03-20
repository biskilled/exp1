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

**Planner Tab (UI)** — unified tag manager (renamed from "Projects")
- [x] 2-pane layout: category list (left 160px) + tag table (right flex)
- [x] Category list: icon + name + value_count badge; `+ New category` input at bottom
- [x] Tag table: Name | Status | Description | Due Date | Created | Events | Actions columns
- [x] Status cycle: click badge → active → done → archived (PATCH saved instantly)
- [x] Inline description edit: click text → contenteditable → blur → PATCH
- [x] Due date picker: `<input type="date">` → change → PATCH
- [x] Nested tags via `parent_id` FK: tree UI with indent + ▶ expand + child button
- [x] Archive (⊘) + Delete (✕) action buttons on each row
- [x] `↻ Sync` → `POST /entities/events/sync` to update event_count + auto-propagate tags
- [x] `due_date DATE` column added to `entity_values` (idempotent ALTER TABLE)

**History Tab (UI)**
- [x] Chat sub-tab: source + phase filter bar (client-side, instant, no re-fetch)
- [x] Chat sub-tab: entries grouped by session with commit strip (hashes + GitHub links)
- [x] Chat sub-tab: `⬡ Tag` button per entry → instant picker (cached, zero API calls on open)
- [x] Chat sub-tab: tag chip shown with category color + icon after saving
- [x] Commits sub-tab: `⬡ Tag` button per row — same picker mechanism as chat
- [x] Tags (⬡) sub-tab removed — tag management moved to Planner
- [x] Commits sub-tab: GitHub link on hash (↗) when `github_repo` configured

**Entity Tagging — Backend**
- [x] `POST /entities/events/tag-by-source-id`: tag individual events by timestamp (source_id); creates event record from history.jsonl if not yet synced
- [x] `GET /entities/session-tags`: reload entity chips when switching chat sessions
- [x] `_do_sync_events`: stores `session_id` in commit event metadata; backfills existing rows
- [x] Auto-propagation: every sync copies entity tags from session prompts → session commits (same `session_id`)
- [x] `POST /entities/session-tag`: bulk-tag all events in a session; find-or-create entity value

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
  summary  → views/summary.js        — PROJECT.md viewer/editor
  chat     → views/chat.js           — SSE streaming chat; tag bar (phase + entity chips);
                                        AI suggestions amber banner; session-commit footer
  planner  → views/entities.js       — 2-pane unified tag manager (categories + tag table)
  prompts  → views/prompts.js        — role + feature prompt tree
  code     → views/code.js           — folder tree + file viewer
  workflow → views/workflow.js        — YAML workflow editor
  history  → views/history.js        — Chat (filter+grouped+per-entry tag) | Commits (tag btn) | Runs | Evals
  settings → views/settings.js       — billing, backend URL, theme
  admin    → views/admin.js          — 6-tab admin panel (users/pricing/coupons/api-keys/usage/billing)
            (conditional: admin role only)
```

### Registered API Routers
```
/auth        routers/auth.py          JWT login/register/me
/usage       routers/usage.py         per-user usage stats
/chat        routers/chat.py          SSE streaming chat + session history
/history     routers/history.py       history.jsonl + commits + runs + session-commits
/workflows   routers/workflows.py     YAML workflow CRUD + run execution
/prompts     routers/prompts.py       prompt file tree CRUD
/files       routers/files.py         code directory browser
/projects    routers/projects.py      project CRUD + /memory + context generation
/config      routers/config_sync.py   settings sync
/admin       routers/admin.py         user mgmt + pricing + coupons + api-keys + usage
/git         routers/git.py           git status/pull/push/commit-push + OAuth device flow
/billing     routers/billing.py       user balance + coupon + transaction history
/search      routers/search.py        semantic search (pgvector)
/entities    routers/entities.py      entity taxonomy + events + tagging + suggestions
/graph       routers/graph_workflows.py  async DAG graph workflows (Cytoscape.js)
/work-items  routers/work_items.py    work item CRUD + pipeline trigger + facts + memory-items
/agent-roles routers/agent_roles.py   agent role library (name/prompt/model) + version history
```

---

## Database Table Reference

All tables follow a structured naming convention:
- **`mng_`** — Management/global tables (shared across all clients and projects)
- **`cl_`** — Client-level tables (currently none; reserved for future multi-tenancy)
- **`pr_[client]_[project]_`** — Per-project tables (e.g. `pr_local_aicli_commits`)

### Global Management Tables (`mng_`)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `mng_users` | User accounts, roles, billing balances | `id`, `email`, `role` (free/paid/admin), `balance_added_usd`, `balance_used_usd` |
| `mng_usage_logs` | Per-request LLM cost tracking | `user_id`, `provider`, `model`, `input_tokens`, `output_tokens`, `cost_usd`, `charged_usd` |
| `mng_transactions` | Credit/debit ledger (coupons, top-ups, charges) | `user_id`, `type`, `amount_usd`, `description` |
| `mng_session_tags` | Active session state per project | `project`, `phase`, `feature`, `bug_ref`, `extra` JSONB |
| `mng_entity_categories` | Tag category definitions per project | `project`, `name`, `color`, `icon` |
| `mng_entity_values` | Tag instances (features, bugs, tasks, etc.) | `category_id`, `project`, `name`, `status`, `lifecycle_status`, `due_date`, `parent_id` |
| `mng_entity_value_links` | Dependencies between entity values (blocks/related) | `from_value_id`, `to_value_id`, `link_type` |
| `mng_graph_workflows` | DAG workflow definitions | `project`, `name`, `description`, `max_iterations` |
| `mng_graph_nodes` | Steps within a workflow | `workflow_id`, `name`, `node_type`, `prompt`, `provider`, `model`, `role_id` |
| `mng_graph_edges` | Connections between nodes | `workflow_id`, `source_node`, `target_node`, `edge_type` |
| `mng_graph_runs` | Workflow execution instances | `workflow_id`, `project`, `status`, `total_cost_usd`, `input`, `output` |
| `mng_graph_node_results` | Per-node output within a run | `run_id`, `node_id`, `status`, `output`, `cost` |
| `mng_work_items` | Structured feature/bug/task items with pipeline tracking | `project`, `category_name`, `name`, `lifecycle_status`, `acceptance_criteria`, `implementation_plan`, `agent_run_id`, `agent_status` |
| `mng_interactions` | Unified prompt/response log (replaces per-project events) | `project_id`, `session_id`, `source_id`, `event_type`, `prompt`, `response`, `phase`, `work_item_id` |
| `mng_interaction_tags` | Links interactions to work items | `interaction_id`, `work_item_id`, `auto_tagged` |
| `mng_memory_items` | Trycycle-reviewed session/feature summaries | `project_id`, `scope` (session/feature), `scope_ref`, `content`, `reviewer_score`, `source_ids` |
| `mng_project_facts` | Durable extracted facts ("we use pgvector", "auth is JWT") | `project_id`, `fact_key`, `fact_value`, `valid_until` (NULL = current) |
| `mng_agent_roles` | Reusable LLM personas for workflow nodes | `project`, `name`, `description`, `system_prompt`, `provider`, `model` |
| `mng_agent_role_versions` | Audit log of role prompt/model changes | `role_id`, `system_prompt`, `provider`, `model`, `changed_by` |

### Per-Project Tables (`pr_[client]_[project]_`)

| Table Pattern | Purpose | Key Columns |
|--------------|---------|-------------|
| `pr_local_{project}_commits` | Git commits linked to sessions | `commit_hash`, `session_id`, `prompt_source_id`, `phase`, `feature` |
| `pr_local_{project}_events` | Raw event log (prompt/commit events, pre-interactions) | `event_type`, `source_id`, `phase`, `feature`, `session_id` |
| `pr_local_{project}_embeddings` | Smart-chunked embeddings for semantic search | `source_type`, `source_id`, `chunk_index`, `embedding` VECTOR(1536) |
| `pr_local_{project}_event_tags` | Links events to `mng_entity_values` | `event_id`, `entity_value_id`, `auto_tagged` |
| `pr_local_{project}_event_links` | Event-to-event links | `from_event_id`, `to_event_id`, `link_type` |

---

## Open Questions

- Should the Kanban board state (column positions) live in `entity_values.status` or a separate `board_state` JSONB?
  → Proposal: use `entity_values.status` (backlog/in-progress/review/done) — already exists, no schema change
- Should workflow runs auto-create entity events without user confirmation?
  → Proposal: yes, but show in timeline as auto-tagged so user can dismiss
- Should `workspace/_templates/workflows/` be versioned separately (git submodule)?
  → Leaning: no — keep flat in the main repo, update via `bash ui/update.sh`

## Recent Work

- Project startup race condition fix (2026-03-20) — Sequential `await api.listProjects()` in `_continueToApp` now prevents empty home screen on initial load by properly handling edge case where list succeeds but returns empty
- Pipeline sidebar caching (2026-03-20) — `_listCache` stores {workflows, roles, runs} to prevent redundant API calls during pipeline UI rendering
- UUID validation in pipeline run queries (2026-03-19) — psycopg2 InvalidTextRepresentation error when string 'recent' passed to UUID field; requires UUID object conversion in backend handler
- Approval chat workflow (2026-03-19) — 2-pane approval panel enables requirement negotiation before work_item save; left pane shows current output, right pane for chat interaction
- Memory endpoint code_dir scoping (2026-03-18) — Fixed undefined template variable at line 1120 causing CLAUDE.md generation failure; variable now properly scoped from config
- Memory items and project_facts table population (pending) — Tables exist in schema but update logic unimplemented; blocks improved memory/context mechanism and requires implementation + testing
