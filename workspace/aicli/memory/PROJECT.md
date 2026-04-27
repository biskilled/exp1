# aicli — Shared AI Memory Platform

_Last updated: 2026-04-27_

> **How this file works**
> - Sections marked `<!-- user-managed -->` are yours to edit freely — they feed directly into CLAUDE.md.
> - Sections marked `<!-- auto-updated by /memory -->` are refreshed automatically when you run `/memory`.
>   You can still edit them; `/memory` will merge its output in without discarding your additions.
> - `## Deprecated` — list superseded decisions here; they will be hidden from CLAUDE.md key_decisions.
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
  ├── mem_mrr_prompts        raw prompt/response pairs (session-tagged, all in DB)
  ├── mem_mrr_commits        git commits (hash, msg, tags, diff_summary)
  ├── mem_mrr_commits_code   per-symbol diffs (tree-sitter: class, method, file)
  ├── mem_mrr_commits_file_stats   hotspot scores per file
  ├── mem_mrr_commits_file_coupling  co-change pairs
  ├── mem_mrr_items          document/meeting items
  └── mem_mrr_messages       Slack/chat messages

Layer 2 — Structured Artifacts (mem_ai_project_facts)
  Durable facts extracted by /memory → project_state.json
  ("uses pgvector", "auth is JWT") — updated by project_synthesis Haiku call

Layer 3 — Work Items (mem_work_items)
  AI-classified + user-reviewed: wi_type (use_case/feature/bug/task/requirement)
  user_status TEXT: open → pending → in-progress → review → done
  wi_id: AI0001 (draft) → UC0001/FE0001/BU0001/TA0001 (approved)
  Approved items: embedding VECTOR(1536) computed; wi_parent_id links children to use_case
```

### Work Item Classification Pipeline

```
POST /wi/{project}/classify
  1. Delete AI draft rows (wi_id LIKE 'AI%')
  2. Fetch unprocessed mem_mrr_* rows (wi_id IS NULL)
  3. Token-bound batches → Claude Haiku (command_work_items.yaml)
  4. Save drafts: use_cases (AI0001) + children (AI0002…)
  5. User reviews in Planner UI (approve/reject)
  6. Approve → real ID assigned (US/FE/BU/TA) + embedding computed
```

### How `/memory` syncs context files

```
POST /projects/{project}/memory
  1. project_synthesis  — Claude Haiku reads recent prompts → project_state.json
                          (command_memory.yaml: project_synthesis key)
  2. write_root_files() — MemoryFiles renders all context files from project_state.json + DB:
       memory/claude/CLAUDE.md     (token-limited)
       memory/cursor/rules.md
       memory/openai/compact.md + full.md
       memory/context.md           (shared injection)
       memory/code.md              (hotspots + coupling tables)
  3. tag_suggestion     — Claude Haiku suggests 2-3 tags from recent prompts
                          (command_memory.yaml: tag_suggestion key)
  No history.jsonl — all history is in mem_mrr_prompts (DB)
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
│   │   ├── memory_backlog.py   ← Backlog pipeline; run_work_items(); use case files
│   │   ├── memory_work_items.py← Work item classification + approval pipeline
│   │   ├── memory_promotion.py ← Fact conflict detection → mem_ai_project_facts
│   │   ├── memory_files.py     ← Deterministic render → CLAUDE.md, context files (no LLM)
│   │   ├── memory_sessions.py  ← JSON sessions for LLM message continuity
│   │   └── memory_code_parser.py← tree-sitter symbol extraction → mem_mrr_commits_code
│   ├── agents/                 ← LLM agent pipeline
│   │   ├── providers/          ← Claude, OpenAI, DeepSeek, Gemini, Grok adapters
│   │   └── tools/              ← Agent tool implementations (search, git, memory)
│   ├── data/                   ← Runtime data (api_keys.json, pricing.json)
│   └── prompts/                ← LLM system prompts (YAML — no inline Python strings)
│       ├── command_memory.yaml     ← /memory: project_synthesis, conflict_detection, tag_suggestion, memory_context_*
│       ├── event_commit.yaml       ← on git commit: commit_analysis, commit_symbol, commit_message
│       ├── command_work_items.yaml ← /wi/classify: classification, summarise, categories
│       └── agent_react.yaml        ← agents: react_pipeline_base, react_suffix
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

## Conventions

<!-- user-managed — edit freely; this section feeds directly into code.md and CLAUDE.md -->

- **Python style**: Python 3.12+; type hints on all new functions; no `from X import *`
- **Imports**: stdlib → third-party → local; each group alphabetically sorted
- **Async**: use `async`/`await` throughout FastAPI routes; no blocking calls in async context
- **DB access**: always use `db.conn()` context manager (psycopg2 pool); parameterized queries only
- **Error handling**: log with `log.warning()` for expected errors, `log.exception()` for unexpected; return 422/404 from routes, never 500 for known cases
- **Naming**: `snake_case` for Python; `camelCase` for JS; `UPPER_SNAKE` for module-level constants
- **LLM prompts**: all prompts in `backend/prompts/*.yaml`; load via `prompt_loader.prompts.content(key)`; never inline strings
- **Work items**: `user_status` is TEXT (`open|pending|in-progress|review|blocked|done`); `wi_type` is TEXT (`use_case|feature|bug|task|requirement`)
- **No dead code**: remove unused imports, functions, and variables immediately; don't leave `# TODO` comments for more than one session
- **Tests**: add a smoke-test curl command in PR description for any new endpoint

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

- Code optimization audit: eliminated N+1 hotspot checks via batch WHERE queries, fixed token counting (len(text) // 4), optimized _update_item_tags to use executemany instead of N separate calls.
- Database schema & query performance: bounded all recursive CTEs (depth < 20), added date cascade validation in _apply_date_rules() to prevent re-parenting inconsistencies.
- Memory file rendering: refactored _load_context() to split DB queries (_query_db_into_ctx) and PROJECT.md parsing (_parse_project_md) to eliminate double file-read bug.
- Work item approval flow: commit-sourced items now auto-set score_status=5 via regex detection (fixes BU0012 pattern); approval marks user_status='done' and triggers embedding.
- Memory synthesis convergence: unified get_project_context() path used by both /memory POST and commit/work-item event handlers; all 5 output files regenerated from single source.
- Code audit cycle: fresh aicli_memory.md audit in progress reviewing all changes from last 10-15 prompts for optimization, SQL efficiency, code duplication, and file length reasonableness.

## Key Decisions

- Memory architecture: 3 layers — raw captures (mem_mrr_*), structured artifacts (mem_ai_project_facts), and work items (mem_work_items) with pgvector embeddings for approved items only (1536-dim, text-embedding-3-small).
- Work items: unified hierarchy with wi_parent_id linking features/bugs/tasks to use_case parents; approved items (wi_id: UC/FE/BU/TA) embed and trigger 4-agent pipeline; unapproved drafts (AI prefix) never embed.
- File generation: /memory POST endpoint is the ONLY writer to project_state.json via get_project_context() + Haiku synthesis; this single JSON drives all 5 output files (CLAUDE.md, CODE.md, PROJECT.md, cursor/rules, api/).
- File management: backend/memory/memory.yaml is canonical single-source mapping for output files; templates/ holds seed files; memory.yaml is internal engine only, not copied to projects.
- Code.md structure: public symbols (classes/methods/functions) with file coupling/hotspot tables; generated from mem_mrr_commits_code per commit and refreshed post-memory via unified get_project_context() path.
- Prompts: all backend LLM prompts in YAML under backend/memory/prompts/ named by trigger (command_memory.yaml, event_commit.yaml, command_work_items.yaml, misc.yaml, mem_project_state.yaml, mem_session_tags.yaml); loaded via prompt_loader utility.
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract.
- Embeddings: ONLY approved work items embed; code.md, project_state.json, project facts, and prompts are NOT embedded; /search/semantic searches work_items only.
- Work item re-embedding: triggered only on name/summary/description edits for approved items via automatic flag in update(); unapproved drafts never re-embed.
- Commit-sourced work items: regex 'fixes BU0012'/'closes FE0001' in commit message auto-sets score_status=5; user must approve to update user_status to 'done'.
- MCP tools: 14 tools rewired to REST endpoints (search_memory, get_project_state, tags, backlog, create_entity→POST /wi/, list_work_items, run_work_item_pipeline, update_work_item, approve_work_items, get_file_history, etc.).
- Database queries: recursive CTEs bounded (depth < 20); batch queries replace N+1 patterns; hotspot checks use single WHERE name = ANY(%s); token counting: len(text) // 4.
- Code organization: memory_work_items.py split into _wi_helpers.py, _wi_classify.py, _wi_markdown.py with shared imports; all modules < 1500 lines.
- JWT auth: hierarchical Clients→Users→Projects; DEV_MODE toggle for passwordless local development.
- Memory file convergence: unified get_project_context() path confirmed for /memory POST and commit/work-item triggers; all 5 output files regenerated from single DB source.

## Deprecated
<!-- List superseded architectural decisions, one per line.
     Any key_decision containing a phrase from this list will be hidden from CLAUDE.md.
     Format: - phrase (: optional explanation)
     Example: - mem_ai_events: dropped in m078, use mem_work_items instead -->
