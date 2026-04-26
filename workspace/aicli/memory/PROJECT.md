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
  AI-classified + user-reviewed: wi_type (use_case/feature/bug/task)
  user_status: open → active → done; due_date; score_importance
  ← USER REVIEWS — AI classifies, user confirms/edits
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
           → upserts mem_work_items row (wi_type, name, summary)
Step 5 — Use case LLM:  refreshes Open items with AI score 0-5
```

### How `/memory` syncs context

```
POST /projects/aicli/memory
  ├── Flush all pending mirror rows → backlog.md
  ├── Write CLAUDE.md / .cursorrules / context.md from DB facts + mem_work_items
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
│   │   ├── memory_promotion.py ← Fact conflict detection (conflict_detection.yaml)
│   │   ├── memory_files.py     ← Template render → CLAUDE.md / .cursorrules
│   │   ├── memory_sessions.py  ← Layer 2: JSON sessions for LLM message continuity
│   │   └── memory_code_parser.py← tree-sitter symbol extraction for commits
│   ├── agents/                 ← LLM agent pipeline
│   │   ├── providers/          ← Claude, OpenAI, DeepSeek, Gemini, Grok adapters
│   │   └── tools/              ← Agent tool implementations (search, git, memory)
│   ├── data/                   ← Runtime data (api_keys.json, pricing.json)
│   └── prompts/                ← LLM system prompts (YAML — no inline Python strings)
│       ├── commit.yaml         ← commit_analysis, commit_symbol, commit_message
│       ├── react_base.yaml     ← react_pipeline_base, react_suffix (agent.py)
│       ├── misc.yaml           ← tag_suggestion
│       ├── memory_files.yaml   ← memory_context_compact/full/openai
│       ├── conflict_detection.yaml ← fact conflict resolver
│       └── work_items.yaml     ← work item extraction/promotion prompts
├── ui/
│   ├── electron/               ← Electron shell (BrowserWindow, xterm.js)
│   └── frontend/               ← Vanilla JS (no framework)
│       ├── views/              ← chat.js, backlog.js, work_items.js, pipeline.js…
│       └── utils/api.js        ← Unified fetch wrapper
├── cli/                        ← Interactive REPL (prompt_toolkit + rich)
├── workspace/                  ← CONTENT (per-project, version-controlled)
│   ├── _templates/
│   │   ├── roles/              ← Agent role YAMLs (11 roles — seeded to DB on startup)
│   │   ├── pipelines/          ← Pipeline YAMLs (standard, build_feature, code_review…)
│   │   ├── cli/claude/hooks/   ← Canonical hook scripts (copy to _system/hooks/)
│   │   ├── backlog_config.yaml ← Default backlog config (copied to .ai/ on first run)
│   │   └── use_case_template.md← Template for new use case files
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
### `mem_work_items` — Work item backlog (Layer 4)
Columns: `wi_id UUID PK, project_id, name, wi_type (use_case/feature/bug/task), summary, user_status (open/active/done), due_date, score_importance, completed_at, deleted_at`

`wi_type` and `user_status` are user-editable; `score_importance` is AI-assigned.

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
  summary   → views/summary.js       PROJECT.md viewer/editor
  chat      → views/chat.js          SSE streaming + tag bar + session-commit footer
  roles     → views/prompts.js       Agent role CRUD (reads mng_agent_roles)
  code      → views/code.js          Folder tree + file viewer
  pipelines → views/graph_workflow.js DAG graph editor + pipeline runner
  dashboard → views/pipeline.js      Memory pipeline monitoring dashboard
  history   → views/history.js       Chat | Commits | Runs sub-tabs
  settings  → views/settings.js      Billing, backend URL, theme
  admin     → views/admin.js         Users / pricing / api-keys / usage (admin only)
  --- Planning group ---
  backlog   → views/work_items.js    Work Items inbox (approve/reject/tag)
  use_cases → views/work_items.js    Approved use cases with due dates
  documents → views/documents.js     Document browser
  completed → views/work_items.js    Completed use cases
```

---

## In Progress ◷

- **Backlog pipeline** — 2-step LLM digest (grouping + summary), user review, use case file merge
- **Work Items lifecycle** — open → active → done with due dates, completion validation, MD file auto-move
- **Prompt YAML consolidation** — all LLM prompts in `backend/prompts/*.yaml`; no inline Python strings

## Planned ○

- Memory auto-compaction at token limit (compress old entries → LLM summary)
- Stripe real payment integration
- Admin dashboard: revenue summary, top users by spend
- Electron packaging with embedded Python 3.12
- Semantic search over use case file content (pgvector on chunked .md files)

<!-- auto-updated by /memory — safe to edit, will be merged on next run -->
## Recent Work

- MCP tool restoration: route_entities.py missing (only .pyc cache); create_entity, sync_github_issues, other work item tools broken; /work-items URL not registered in main.py
- Backend prompt refactoring: ensure all LLM prompts use YAML templates under backend/memory/mem_*.yaml; verify project_state.json populates correct context for /memory
- Frontend hardcoded string removal: ensure all localhost references removed; validate dynamic config loading from aicli.yaml for backend URLs
- Memory file persistence validation: ensure PROJECT.md, CODE.md, CLAUDE.md, cursorrules.md persist to workspace after /memory; add integrity checks for token limit enforcement
- Code.md generation completeness: verify all public symbols from commits are included; confirm file coupling and hotspot tables populated correctly; test is_latest BOOLEAN index
- Embedding audit: confirm mem_work_items VECTOR(1536) populated for semantic search; evaluate if mem_mrr_commits + mem_mrr_prompts embeddings needed for MCP context or semantic history search

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; .ai/ and _system/ removed (replaced by cli/ structure)
- Workspace structure: cli/{claude,mcp}/ for hooks/configs; pipelines/{prompts,samples}/ for workflows; documents/ for project files; state/ for runtime state
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim) for semantic search; unified mem_mrr_* and mem_work_items tables; mem_ai_events dropped
- Memory system: /memory endpoint generates 5 files (PROJECT.md, CODE.md, CLAUDE.md, cursorrules.md, recent_work.md) from project_state.json + database; token-limited by project.yaml config
- Memory files managed by backend/memory/memory.yaml: canonical single source (not duplicated in _templates); templates in backend/memory/templates/
- Code.md structure: public symbols (classes/methods/functions) + file coupling/hotspot tables with is_latest BOOLEAN pattern; single source for all LLM context
- mem_mrr_commits_code (19 columns) with is_latest BOOLEAN: replaces need for separate code_symbols table; updated per commit; partial index optimization
- Project facts deprecated: mem_ai_project_facts no longer auto-populated during /memory; facts extracted inline from memory synthesis; conflict_detection merged into mem_project_state.yaml
- Work Items + Use Cases: items tab shows pending AI-classified items; use cases tab displays hierarchy with due dates, completion validation, auto-markdown generation
- Drag-and-drop parent-child/merge: unconditional e.preventDefault() + document.elementFromPoint() target detection (same implementation for both Work Items and Use Cases)
- Undo as persistent toolbar button: stores reverse API call closure capturing original parent_id before link modification; works for both linking and partial merge
- JWT authentication: python-jose + bcrypt with DEV_MODE toggle; hierarchical Clients → Users → Projects
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract
- Backend prompts: all LLM prompts migrated to YAML files under backend/memory/mem_*.yaml (named by table domain); templates in backend/memory/templates/
- Electron desktop UI: Vanilla JS with xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development; hardcoded localhost removed
