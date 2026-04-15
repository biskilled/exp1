# aicli — Shared AI Memory Platform

_Last updated: 2026-04-15 | Version 3.0.0_

---

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
| 2 | **4-layer memory pipeline** — Mirror → AI Events → Work Items → Project Facts | ✓ Implemented |
| 3 | **Planner / Work Items** — AI-detected tasks linked to user-managed planner_tags | ✓ Implemented |
| 4 | **Auto-deploy** — Stop hook → auto_commit_push.sh after every Claude Code session | ✓ Hooks |
| 5 | **Billing & usage** — Multi-user, server keys, balance, markup, coupons | ✓ Implemented |
| 6 | **Multi-LLM workflows** — Graph DAG: design → review → develop → test | ✓ Implemented |
| 7 | **Semantic search** — pgvector cosine similarity over events + work items | ✓ Implemented |
| 8 | **Feature snapshots** — Haiku-generated requirements/design per tag | ✓ Implemented |
| 9 | **MCP server** — 10 tools: search_memory, get_project_state, work items, tags | ✓ Implemented |

---

## 4-Layer Memory Architecture

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
  is_system=TRUE → system file updates (PROJECT.md etc) skipped for work items
  source_id: batch_{hash8}_{tagfp8} for commits; last prompt UUID for prompt batches
  Tags: only user-intent {phase, feature, bug, source} stored

Layer 3 — Structured Artifacts (mem_ai_*)
  ├── mem_ai_work_items      AI-detected tasks/bugs/features (score_ai 0-5)
  └── mem_ai_project_facts   Durable facts ("uses pgvector", "auth is JWT")

Layer 4 — User Tags (planner_tags)
  Human-owned taxonomy: features, bugs, tasks, phases
  ← USER OWNS THIS — AI suggests, user confirms
```

### How `/memory` syncs context to every LLM tool

```
POST /projects/aicli/memory
  ├── Haiku synthesizes last N events → CLAUDE.md / MEMORY.md / context.md
  ├── _system/claude/CLAUDE.md   →  {code_dir}/CLAUDE.md        ← Claude Code auto-loads
  ├── _system/claude/MEMORY.md   →  {code_dir}/MEMORY.md        ← referenced in CLAUDE.md
  ├── _system/cursor/rules.md    →  {code_dir}/.cursor/rules/   ← Cursor reads on open
  ├── _system/aicli/context.md   →  prepended to every CLI prompt
  ├── _system/aicli/copilot.md   →  .github/copilot-instructions.md
  └── background: promote_all_work_items() + run_feature_snapshots()
```

### PROJECT.md vs CLAUDE.md vs project_facts

| File | Source | Updated by |
|------|--------|-----------|
| `PROJECT.md` | Manual living doc (this file) | Human / Summary tab / `PUT /projects/aicli/summary` |
| `CLAUDE.md` | Auto-generated from DB | `/memory` POST → `write_root_files()` |
| `MEMORY.md` | Auto-generated from DB | `/memory` POST → `write_root_files()` |
| `mem_ai_project_facts` | AI-extracted from events | `extract_project_facts()` in memory_promotion.py |

`mem_ai_project_facts` feeds into `CLAUDE.md` (facts section) but does **not** auto-update `PROJECT.md`.

---

## Code Structure

```
aicli/                          ← Engine (code)
├── backend/                    ← FastAPI server (python3.12 -m uvicorn main:app)
│   ├── main.py                 ← App init, router registration, DB startup
│   ├── core/                   ← Infrastructure
│   │   ├── config.py           ← Settings (env vars, paths)
│   │   ├── database.py         ← psycopg2 pool + migration runner
│   │   ├── db_migrations.py    ← m001–m047 migrations
│   │   ├── db_schema.sql       ← Single source of truth for table shapes
│   │   ├── pipeline_log.py     ← mem_pipeline_runs helpers
│   │   └── prompt_loader.py    ← Load prompts/*.yaml + .md files
│   ├── routers/                ← HTTP endpoints
│   │   ├── route_projects.py   ← /projects (CRUD, /memory, /context, /snapshot)
│   │   ├── route_memory.py     ← /memory (embed-prompts, embed-commits, rebuild, dashboard)
│   │   ├── route_git.py        ← /git (commit-push, status, pull, commit-store)
│   │   ├── route_history.py    ← /history (commits, prompts, sessions, sync)
│   │   ├── route_chat.py       ← /chat (SSE streaming, hook-log)
│   │   ├── route_work_items.py ← /work-items (CRUD, promote, tag link)
│   │   ├── route_tags.py       ← /tags (planner_tags CRUD, deliveries, merge)
│   │   ├── route_snapshots.py  ← /projects/{p}/snapshot/{tag}
│   │   ├── route_entities.py   ← /entities (session tags, event tagging)
│   │   ├── route_search.py     ← /search (semantic search via pgvector)
│   │   ├── route_agents.py     ← /agents (run, run-pipeline, roles)
│   │   ├── route_agent_roles.py← /agent-roles (CRUD + versioning)
│   │   ├── route_graph_workflows.py ← /graph-workflows (DAG CRUD + runs)
│   │   ├── route_workflows.py  ← /workflows (YAML workflow executor)
│   │   ├── route_admin.py      ← /admin (users, api-keys, pricing, usage)
│   │   ├── route_auth.py       ← /auth (login, register, JWT)
│   │   ├── route_billing.py    ← /billing (balance, coupons, transactions)
│   │   ├── route_prompts.py    ← /prompts (role + feature prompt tree)
│   │   ├── route_files.py      ← /files (code directory browser)
│   │   └── route_usage.py      ← /usage (per-user LLM cost stats)
│   ├── memory/                 ← Memory pipeline classes
│   │   ├── memory_mirroring.py ← INSERT mem_mrr_* rows; tag operations
│   │   ├── memory_embedding.py ← Haiku digest + OpenAI embed → mem_ai_events
│   │   ├── memory_promotion.py ← Work item extraction; feature snapshots; facts
│   │   ├── memory_tagging.py   ← planner_tags CRUD; 3-level work_item→tag matching
│   │   ├── memory_files.py     ← Template render → CLAUDE.md / MEMORY.md / context.md
│   │   ├── memory_sessions.py  ← Layer 2: JSON file sessions for LLM message continuity
│   │   ├── memory_code_parser.py← tree-sitter symbol extraction for commits
│   │   ├── memory_planner.py   ← Planner documents (acceptance_criteria sync)
│   │   └── memory_extraction.py← Work item extraction helpers
│   ├── agents/                 ← LLM agent pipeline
│   │   ├── providers/          ← Claude, OpenAI, DeepSeek, Gemini, Grok adapters
│   │   └── tools/              ← Agent tool implementations (search, git, memory)
│   ├── data/                   ← Runtime data (api_keys.json, pricing.json)
│   └── prompts/                ← System prompts (prompts.yaml + .md files)
│       └── memory/             ← commit_digest, prompt_batch_digest, work_item_extraction…
├── ui/
│   ├── electron/               ← Electron shell (BrowserWindow, xterm.js)
│   └── frontend/               ← Vanilla JS (no framework)
│       ├── views/              ← chat.js, entities.js, pipeline.js, history.js…
│       └── api.js              ← Unified fetch wrapper
├── cli/                        ← Interactive REPL (prompt_toolkit + rich)
├── workspace/                  ← CONTENT (per-project, version-controlled)
│   ├── _templates/hooks/       ← Canonical hook scripts
│   └── aicli/
│       ├── PROJECT.md          ← This file
│       ├── project.yaml        ← Project config (code_dir, git settings)
│       └── _system/            ← Auto-generated memory files
│           ├── claude/CLAUDE.md
│           ├── claude/MEMORY.md
│           ├── cursor/rules.md
│           └── aicli/context.md
└── .aicli/scripts/             ← Hook scripts (auto_commit_push.sh, etc.)
```

---

## Database Schema

**Flat architecture** — all tables in a single schema. Project scoping via `project_id INT FK`.

### `mng_*` — Global / client-scoped (11 tables)
| Table | Purpose |
|-------|---------|
| `mng_clients` | Client accounts |
| `mng_users` | Users (role: admin/paid/free), JWT auth |
| `mng_projects` | Projects (id, name, code_dir, workspace_path, git_*) |
| `mng_user_projects` | User↔project roles (owner/editor/viewer) |
| `mng_usage_logs` | Per-request LLM cost tracking |
| `mng_transactions` | Credit/debit ledger |
| `mng_session_tags` | Active phase/feature/bug tags per project |
| `mng_agent_roles` | LLM personas (name, system_prompt, model, react) |
| `mng_agent_role_versions` | Role audit log |
| `mng_system_roles` | Memory synthesis prompts (commit_digest, etc.) |
| `mng_tags_categories` | Planner tag categories (feature/bug/task/phase) |

### `planner_tags` — User-managed tag hierarchy (1 table)
Columns: `id, name, category_id, parent_id, creator, description, requirements, acceptance_criteria, action_items, deliveries JSONB, status, priority, due_date, created_at, updated_at`

### `mem_mrr_*` — Layer 1: Raw capture (4 tables)
| Table | Purpose | Key columns |
|-------|---------|-------------|
| `mem_mrr_prompts` | Raw prompt/response | id, project_id, event_id, session_id, prompt, response, tags |
| `mem_mrr_commits` | Git commits | commit_hash PK, project_id, event_id, commit_msg, tags, diff_summary |
| `mem_mrr_commits_code` | Per-symbol diffs | commit_hash FK, file_path, symbol_type, full_symbol, diff_snippet |
| `mem_mrr_items` | Documents/meetings | id, project_id, item_type, title, raw_text |

### `mem_ai_*` — Layer 2/3: AI digests + artifacts (3 tables)
| Table | Purpose | Key columns |
|-------|---------|-------------|
| `mem_ai_events` | Digested + embedded events | id, project_id, event_type, source_id, tags, is_system, summary, embedding |
| `mem_ai_work_items` | AI-detected tasks | id, project_id, category_ai, name_ai, summary_ai, score_ai, tag_id_user, tag_id_ai |
| `mem_ai_project_facts` | Durable project facts | id, project_id, fact_key, fact_value, valid_until |

### `pr_*` — Graph workflows (6 tables)
`pr_graph_workflows` | `pr_graph_nodes` | `pr_graph_edges` | `pr_graph_runs` | `pr_graph_node_results` | `pr_seq_counters`

---

## Key Patterns

### Auth
- `REQUIRE_AUTH=false` local dev — no gate
- `REQUIRE_AUTH=true` Railway — JWT required
- `DEV_MODE=true` → synthetic admin, no balance deduction
- Login hierarchy: admin → login_as any user

### Memory Pipeline Triggers
| Event | Trigger |
|-------|---------|
| Prompt batch (every 3 prompts) | `process_prompt_batch()` → mem_ai_events |
| Commit push | `process_commit_batch()` when ≥5 pending |
| `/memory` POST | `write_root_files()` + `promote_all_work_items()` + `run_feature_snapshots()` |
| Session end (Stop hook) | `session-summary` → `/projects/{p}/memory` |

### Work Item Flow
```
mem_ai_events (is_system=FALSE) → extract_work_items_from_events()
  → confidence ≥ 0.75 → mem_ai_work_items INSERT
  → match_work_item_to_tags() → tag_id_ai (AI suggestion)
  → user drag-drop → tag_id_user (confirmed link)
  → promote_work_item() → refreshes summary_ai, acceptance_criteria_ai, score_ai
```

### Commit Batch Events
- Grouped by tag fingerprint `{phase, feature, bug}`
- `source_id = batch_{first_hash8}_{tagfp8}`
- `is_system=TRUE` if all changed files are: CLAUDE.md, MEMORY.md, PROJECT.md, .cursorrules, _system/…
- Back-propagated: `mem_mrr_commits.event_id` → UUID of the batch event

### UI Tab Structure
```
sidebar tabs:
  summary  → views/summary.js        PROJECT.md viewer/editor
  chat     → views/chat.js           SSE streaming + tag bar + session-commit footer
  planner  → views/entities.js       2-pane: categories + work items + tag drawer
  pipeline → views/pipeline.js       Memory pipeline monitoring dashboard
  history  → views/history.js        Chat | Commits | Runs sub-tabs
  workflow → views/workflow.js        YAML workflow editor
  graph    → views/graph_workflow.js  DAG graph editor (Cytoscape.js)
  prompts  → views/prompts.js        Role + feature prompt tree
  files    → views/code.js           Folder tree + file viewer
  settings → views/settings.js       Billing, backend URL, theme
  admin    → views/admin.js          Users / pricing / api-keys / usage (admin only)
```

---

## In Progress ◷

- **Work item quality** — score_ai 0-5 (0=noise, 5=critical); confidence gate 0.75 threshold; system commit filtering
- **Feature snapshot pipeline** — Haiku generates requirements/design/action_items per planner_tag (Haiku model, flat JSON)
- **Rebuild command** — `POST /memory/{p}/rebuild` deletes open+unlinked work items, resets mirror event_ids, reprocesses from scratch

## Planned ○

- Memory auto-compaction at token limit (compress old entries → LLM summary)
- Stripe real payment integration
- Admin dashboard: revenue summary, top users by spend
- Electron packaging with embedded Python 3.12
- Global role library: `workspace/_templates/roles/` with 6 default roles

---

## Recent Work

- Agent context consolidation — Consolidated legacy _system/ files to .ai/rules.md, .cursor/rules/aicli.mdrules, .github/copilot-instructions.md as primary agent context; removed stale CLAUDE.md and MEMORY.md
- Memory promotion timing instrumentation — Added time.monotonic() tracking to _run_promote_all_work_items; updated _finish_run calls with t0 parameter for performance measurement
- Snapshot generation refactor — Switched Claude Sonnet to Haiku for cost efficiency; simplified planner_tags upsert to flat string keys (requirements, action_items, design, code_summary)
- Schema cleanup and refactoring — mem_ai_work_items table reorganized: removed status_ai dual-status design, reordered columns with seq_num near id, added FOREIGN KEY constraint for merged_into, added ivfflat embedding index
- Work item pipeline refactor — Agent roles loaded from DB with fallback prompts; RoleCreate/RoleUpdate models updated; auto_commit boolean support added; 4-stage pipeline with provider/model overrides
- Tag suggestion approval flow — ai_tag_suggestion column with approve/remove buttons; simplified chip markup; category inference on tag creation; improved tooltip UX
