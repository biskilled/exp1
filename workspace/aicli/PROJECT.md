# aicli — Shared AI Memory Platform

_Last updated: 2026-04-17 | Version 3.1.0_

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
| 2 | **Backlog pipeline** — Mirror → Backlog digest → User review → Use case files | ✓ Implemented |
| 3 | **Planner** — User-managed tag hierarchy linked to use case files | ✓ Implemented |
| 4 | **Auto-deploy** — Stop hook → auto_commit_push.sh after every Claude Code session | ✓ Hooks |
| 5 | **Billing & usage** — Multi-user, server keys, balance, markup, coupons | ✓ Implemented |
| 6 | **Multi-LLM workflows** — Graph DAG: design → review → develop → test | ✓ Implemented |
| 7 | **Semantic search** — pgvector cosine similarity over events | ✓ Implemented |
| 8 | **Feature snapshots** — Haiku-generated requirements/design per planner tag | ✓ Implemented |
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

Layer 4 — User Taxonomy (planner_tags)
  Human-owned hierarchy: features, bugs, tasks, phases
  file_ref → links to use case .md files
  ← USER OWNS THIS — AI suggests, user confirms
```

### Backlog Pipeline (5 steps)

```
Step 1 — Raw capture:   mem_mrr_* (no LLM)
Step 2 — Backlog:       backlog_config.yaml drives 2-call LLM digest
           per source type:
           call 1 — grouping_prompt  (clusters N rows by topic)
           call 2 — summary_prompt   (per group → requirements + action items)
           → documents/backlog.md (append-only)
Step 3 — User review:   Backlog tab — approve (x), reject (-), add tag
Step 4 — Merge:         POST /memory/{p}/work-items processes approved entries
           → creates/updates documents/use_cases/{slug}.md
           → links planner_tag.file_ref → use case file
Step 5 — Use case LLM:  refreshes Open items with AI score 0-5
```

### How `/memory` syncs context

```
POST /projects/aicli/memory
  ├── Flush all pending mirror rows → backlog.md
  ├── Write CLAUDE.md / .cursorrules / context.md from DB facts + planner_tags
  └── Top events → .claude/memory/top_events.md
```

---

## Code Structure

```
aicli/                          ← Engine (code)
├── backend/                    ← FastAPI server
│   ├── main.py                 ← App init, router registration, DB startup
│   ├── core/                   ← Infrastructure
│   │   ├── config.py           ← Settings (env vars, paths)
│   │   ├── database.py         ← psycopg2 pool + migration runner
│   │   ├── db_migrations.py    ← m001–m056 migrations
│   │   ├── db_schema.sql       ← Single source of truth for table shapes
│   │   ├── pipeline_log.py     ← mem_pipeline_runs helpers
│   │   └── prompt_loader.py    ← Load prompts/*.yaml + .md files
│   ├── routers/                ← HTTP endpoints
│   │   ├── route_projects.py   ← /projects (CRUD, /memory, /context, /snapshot)
│   │   ├── route_memory.py     ← /memory (embed, rebuild, dashboard, backlog)
│   │   ├── route_backlog.py    ← /memory/{p}/backlog endpoints
│   │   ├── route_git.py        ← /git (commit-push, status, pull, commit-store)
│   │   ├── route_history.py    ← /history (commits, prompts, sessions, sync)
│   │   ├── route_chat.py       ← /chat (SSE streaming, hook-log)
│   │   ├── route_tags.py       ← /tags (planner_tags CRUD, deliveries, merge)
│   │   ├── route_entities.py   ← /entities (session tags, event tagging)
│   │   ├── route_search.py     ← /search (semantic search via pgvector)
│   │   ├── route_agents.py     ← /agents (run, run-pipeline, roles)
│   │   ├── route_agent_roles.py← /agent-roles (CRUD + versioning)
│   │   ├── route_graph_workflows.py ← /graph-workflows (DAG CRUD + runs)
│   │   ├── route_workflows.py  ← /workflows (YAML workflow executor)
│   │   ├── route_admin.py      ← /admin (users, api-keys, pricing, usage)
│   │   ├── route_auth.py       ← /auth (login, register, JWT)
│   │   ├── route_billing.py    ← /billing (balance, coupons, transactions)
│   │   └── route_files.py      ← /files (code directory browser)
│   ├── memory/                 ← Memory pipeline classes
│   │   ├── memory_mirroring.py ← INSERT mem_mrr_* rows; tag operations
│   │   ├── memory_embedding.py ← Haiku digest + OpenAI embed → mem_ai_events
│   │   ├── memory_backlog.py   ← Backlog pipeline; run_work_items(); use case files
│   │   ├── memory_promotion.py ← Feature snapshots; fact conflicts
│   │   ├── memory_tagging.py   ← planner_tags CRUD
│   │   ├── memory_files.py     ← Template render → CLAUDE.md / .cursorrules
│   │   ├── memory_sessions.py  ← Layer 2: JSON sessions for LLM message continuity
│   │   └── memory_code_parser.py← tree-sitter symbol extraction for commits
│   ├── agents/                 ← LLM agent pipeline
│   │   ├── providers/          ← Claude, OpenAI, DeepSeek, Gemini, Grok adapters
│   │   └── tools/              ← Agent tool implementations (search, git, memory)
│   ├── data/                   ← Runtime data (api_keys.json, pricing.json)
│   └── prompts/                ← System prompts (prompts.yaml + .md files)
│       └── memory/             ← commit_digest, prompt_batch_digest, session_end_synthesis…
├── ui/
│   ├── electron/               ← Electron shell (BrowserWindow, xterm.js)
│   └── frontend/               ← Vanilla JS (no framework)
│       ├── views/              ← chat.js, entities.js, backlog.js, pipeline.js…
│       └── utils/api.js        ← Unified fetch wrapper
├── cli/                        ← Interactive REPL (prompt_toolkit + rich)
├── workspace/                  ← CONTENT (per-project, version-controlled)
│   ├── _templates/
│   │   ├── backlog_config.yaml ← Default backlog pipeline config (copied to .ai/ on first run)
│   │   ├── use_case_template.md← Template for new use case files
│   │   └── hooks/              ← Canonical hook scripts
│   └── aicli/
│       ├── PROJECT.md          ← This file
│       ├── project.yaml        ← Project config (code_dir, git settings)
│       ├── documents/
│       │   ├── backlog.md      ← Append-only backlog inbox
│       │   └── use_cases/      ← One .md per use case
│       └── _system/            ← Auto-generated memory files
│           ├── claude/CLAUDE.md
│           ├── cursor/rules.md
│           └── llm_prompts/
└── .aicli/
    ├── scripts/                ← Hook scripts (auto_commit_push.sh, etc.)
    └── backlog_config.yaml     ← Runtime backlog config (auto-created from template)
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
| `mng_tags_categories` | Planner tag categories (feature/bug/task/phase) |

### `planner_tags` — User-managed tag hierarchy (1 table)
Columns: `id, name, category_id, parent_id, creator, description, requirements, acceptance_criteria, action_items, deliveries JSONB, status, priority, due_date, file_ref, created_at, updated_at`

`file_ref` links a tag to its use case file: `documents/use_cases/{slug}.md`

### `mem_mrr_*` — Layer 1: Raw capture (4 tables)
| Table | Key columns |
|-------|-------------|
| `mem_mrr_prompts` | id, project_id, session_id, prompt, response, tags, backlog_ref |
| `mem_mrr_commits` | commit_hash PK, project_id, commit_msg, tags, diff_summary, backlog_ref |
| `mem_mrr_commits_code` | commit_hash FK, file_path, symbol_type, full_symbol, diff_snippet |
| `mem_mrr_items` | id, project_id, item_type, title, raw_text, backlog_ref |
| `mem_mrr_messages` | id, project_id, platform, messages JSONB, backlog_ref |

`backlog_ref` — NULL = pending backlog digest; set to ref_id (e.g. `P100042`) once processed.

### `mem_ai_*` — Layer 2/3: AI digests + artifacts (2 active tables)
| Table | Purpose | Key columns |
|-------|---------|-------------|
| `mem_ai_events` | Digested + embedded events | id, project_id, event_type, source_id, tags, summary, embedding |
| `mem_ai_project_facts` | Durable project facts | id, project_id, fact_key, fact_value, valid_until |

### `mem_backlog_links` — Permanent backlog→use case mapping
`ref_id, project_id, tag_id, use_case_slug, source_type, created_at`

### `pr_*` — Graph workflows (6 tables)
`pr_graph_workflows` | `pr_graph_nodes` | `pr_graph_edges` | `pr_graph_runs` | `pr_graph_node_results` | `pr_seq_counters`

---

## Key Patterns

### Auth
- `REQUIRE_AUTH=false` local dev — no gate
- `REQUIRE_AUTH=true` Railway — JWT required
- `DEV_MODE=true` → synthetic admin, no balance deduction

### Backlog Config (`{code_dir}/.ai/backlog_config.yaml`)
Each source type (`commits`, `prompts`, `items`, `messages`) has:
- `cnt` — batch size (trigger threshold)
- `grouping_prompt` — clusters N raw rows into topic groups
- `summary_prompt` — per-group summary → requirements + action items
- `llm` / `temperature` per prompt

Auto-created from `workspace/_templates/backlog_config.yaml` on first run.

### Use Case File Format (`documents/use_cases/{slug}.md`)
```
# {slug}
## Overview
## Requirements (Open / Closed)
## Delivery (code table + docs table)
## Completed (action items + bugs fixed)
## Open (action items + bugs with AI score)
## Events (system-managed)
```

### Memory Pipeline Triggers
| Event | Trigger |
|-------|---------|
| Commit push | `_check_backlog_threshold(project, "commits")` background task |
| Prompt stored (hook-log) | `_check_backlog_threshold(project, "prompts")` background task |
| `/memory` POST | Flush all pending + write context files |
| Session end (Stop hook) | `session-summary` → `/projects/{p}/memory` |

### UI Tab Structure
```
sidebar tabs:
  summary  → views/summary.js        PROJECT.md viewer/editor
  chat     → views/chat.js           SSE streaming + tag bar + session-commit footer
  backlog  → views/backlog.js        Inbox review (approve/reject/tag)
  planner  → views/entities.js       Category list + tag table + use case file preview
  pipeline → views/pipeline.js       Memory pipeline monitoring dashboard
  history  → views/history.js        Chat | Commits | Runs sub-tabs
  workflow → views/workflow.js        YAML workflow editor
  graph    → views/graph_workflow.js  DAG graph editor (Cytoscape.js)
  files    → views/code.js           Folder tree + file viewer
  settings → views/settings.js       Billing, backend URL, theme
  admin    → views/admin.js          Users / pricing / api-keys / usage (admin only)
```

---

## In Progress ◷

- **Backlog pipeline** — 2-step LLM digest (grouping + summary), user review, use case file merge
- **Use case files** — documents/use_cases/{slug}.md with Events section; system-managed EVENTS_START/END markers
- **Planner simplification** — tag list + use case file_ref; no work items; all detail managed in .md files

## Planned ○

- Memory auto-compaction at token limit (compress old entries → LLM summary)
- Stripe real payment integration
- Admin dashboard: revenue summary, top users by spend
- Electron packaging with embedded Python 3.12
- Semantic search over use case file content (pgvector on chunked .md files)

## Recent Work

- MD file generation refinement: Removed HTML comment tags; created/updated dates now plain text; item counts computed from recursive CTEs; status badges (bugs/features/tasks/completed/in-progress/open) derived from database state, not comments
- Use Case due date management: Due dates support calendar (MM/DD/YY) and day offsets; re-parent conflict auto-resolution when items exceed parent due date; completion validation ensures all descendants finished
- Work Items to Use Cases migration: Pending AI-classified items (AI* prefix) require approval in Work Items tab before moving to real IDs (FE/BU/TA); Use Cases tab shows only approved, completed, or in-progress items
- Session ID and timestamp visibility: Chat/History tabs display last 5 chars of session ID in header with full UUID on click; timestamps formatted as YY/MM/DD-HH:MM next to user prompts; session selection loads correct session on startup (no 15s delay)
- Completed section and Planning grouping: Left sidebar reorganized as 'Planning' group (Work Items/Use Cases/Documents/Completed); completed_at column tracks UC completion; MD files auto-move to documents/completed/ folder on completion
- Hook-log stability and prompt loading: m050-m074 migrations fixed DB errors; 531 total prompts load correctly (389 DB + ~142 JSONL); hook shows 0.1h health with proper sorted session list and correct current session on startup
