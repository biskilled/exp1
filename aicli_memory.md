# aicli Memory System — Audit & Architecture Reference
_Last updated: 2026-04-27_

---

## 1. Trigger Chains (Event → Files / Work Items)

### 1A. Claude Code Session Stop
```
Claude Code stop hook
  → auto_commit_push.sh
  → git push (workspace/ → remote)
  → POST /projects/{p}/memory
  → generate_memory()
     ├── project_synthesis (Haiku LLM)      → CONTEXT.md + synthesis dict
     ├── memory_files.write_all()            → CLAUDE.md, .cursorrules, openai/*.md, etc.
     ├── _suggest_hotspot_work_items()       → auto-create refactor tasks
     └── auto_populate_from_synthesis()      → mem_ai_project_facts (via save_fact)
```

### 1B. Claude Code Session Start
```
Claude Code start hook
  → check_session_context.sh
  → write_root_files()                       → CLAUDE.md + .cursorrules only (fast path)
```

### 1C. Git Commit Pushed
```
POST /git/{p}/commit-push  (or auto_commit_push.sh)
  → store commit in mem_mrr_commits
  → background: extract_commit_code()
     ├── commit_analysis (Haiku)             → mem_mrr_commits_code summaries
     ├── commit_symbol (Haiku)               → per-symbol diffs stored
     └── update mem_mrr_commits_file_stats + file_coupling
  → background: check_and_trigger("commits") → classify() if threshold reached
```

### 1D. Work Item Classify → Approve → Embed
```
classify() (background, threshold-triggered)
  → _fetch_pending_events()                  ← mem_mrr_prompts + mem_mrr_commits
  → _group_events()
  → classification LLM (Haiku, command_work_items.yaml)
  → INSERT mem_work_items (wi_id = AI0001...) ← draft state

approve(item_id)
  → assign real wi_id (BU0001, FE0002, etc.)
  → UPDATE mem_mrr_prompts/commits wi_id
  → _embed_work_item(7 fields)               → mem_work_items.embedding
  → if use_case: approve_all_under() + refresh_md()

update(item_id, fields)
  → if any of {name, summary, deliveries, delivery_type, AC, plan} changed:
      → _embed_work_item(7 fields) re-run
```

### 1E. /memory POST (manual or stop hook)
```
POST /projects/{p}/memory
  → MemoryBacklog.run()                      → backlog.md (grouped pending items)
  → project_synthesis LLM                   → CONTEXT.md
  → MemoryFiles.write_all()                 → all 5 context files
  → _suggest_hotspot_work_items()           → auto-create tasks for hotspots
  → auto_populate_from_synthesis()          → fact_extraction LLM → mem_ai_project_facts
```

---

## 2. All LLM Prompts in the System

| File | Key | Called By | Model | Purpose |
|------|-----|-----------|-------|---------|
| `event_commit.yaml` | `commit_analysis` | route_git.py background | Haiku | Summarise diff into human description |
| `event_commit.yaml` | `commit_symbol` | route_git.py background | Haiku | Per-symbol diff → LLM summary |
| `event_commit.yaml` | `commit_message` | route_git.py `/git/{p}/commit-push` | Haiku | Generate 1-line git commit message |
| `command_work_items.yaml` | `classification` | _wi_classify.classify() | Haiku | Classify raw events into work items |
| `command_work_items.yaml` | `categories` | _wi_classify (preamble) | — | Category definitions (not a direct call) |
| `command_work_items.yaml` | `summarise` | **UNWIRED** | — | Defined in YAML, never called |
| `command_memory.yaml` | `project_synthesis` | route_projects generate_memory() | Haiku | Synthesise PROJECT.md → CONTEXT.md |
| `command_memory.yaml` | `conflict_detection` | memory_promotion._resolve_conflict() | Haiku | LLM decides supersede/merge/flag |
| `command_memory.yaml` | `fact_extraction` | memory_promotion.auto_populate_from_synthesis() | Haiku | Extract 5-10 stable facts as JSON |
| `command_memory.yaml` | `memory_context_compact` | memory_files (preamble inject) | — | Preamble for compact context files |
| `command_memory.yaml` | `memory_context_full` | memory_files (preamble inject) | — | Preamble for full context files |
| `command_memory.yaml` | `memory_context_openai` | memory_files (preamble inject) | — | Preamble for OpenAI-specific files |
| `agent_react.yaml` | `react_pipeline_base` | agents/agent.py startup | — | ReAct rules for all pipeline agents |
| `agent_react.yaml` | `react_suffix` | agents/agent.py (run() mode) | — | Simpler ReAct format for non-pipeline |
| `misc.yaml` | `tag_suggestion` | route_projects.py suggest-tags | Haiku | Suggest phase/feature tags from text |
| `misc.yaml` | `feature_auto_detect` | **LIKELY UNWIRED** | — | Auto-detect feature from commit (check) |

**Notes:**
- `summarise` (command_work_items.yaml): defined but no Python call site found.
- `feature_auto_detect` (misc.yaml): verify usage; may be dead weight.
- All prompts loaded via `core/prompt_loader.py` (hot-reloadable, 60s cache).
- `command_work_items.yaml` excluded from prompt_loader scan (nested format, not list).

---

## 3. Memory Files — What Gets Written

| File | Path | Written By | Content |
|------|------|-----------|---------|
| `CLAUDE.md` | `workspace/{p}/memory/claude/CLAUDE.md` | MemoryFiles | Architecture + recent work + hotspots |
| `.cursorrules` | `workspace/{p}/memory/cursor/rules.md` | MemoryFiles | Same, cursor-formatted |
| `context.md` | `workspace/{p}/memory/context.md` | MemoryFiles | Shared context (all LLMs) |
| `openai/compact.md` | `workspace/{p}/memory/openai/compact.md` | MemoryFiles | Token-limited compact version |
| `openai/full.md` | `workspace/{p}/memory/openai/full.md` | MemoryFiles | Full project context |
| `code.md` | `workspace/{p}/memory/code.md` | MemoryFiles | Dir tree + file hotspots + coupling |
| `PROJECT.md` | `workspace/{p}/memory/PROJECT.md` | **User-managed** | Source of truth for synthesis |
| `CONTEXT.md` | `workspace/{p}/state/CONTEXT.md` | route_projects | LLM synthesis output |
| `backlog.md` | `workspace/{p}/pipelines/backlog.md` | MemoryBacklog | Pending events grouped |

**code.md lag**: Updated per-commit (via extract_commit_code), but embedding only refreshed on POST /memory. Up to N commits stale for semantic search.

---

## 4. Work Item Lifecycle

```
mem_mrr_prompts / mem_mrr_commits  ←─── raw capture
        │
        ▼ (classify, threshold or manual)
mem_work_items (wi_id = AI0001)    ← draft/pending
        │
        ▼ (user approves in UI)
mem_work_items (wi_id = BU0001)    ← approved
        │ embedding written (7 fields)
        ▼ (user fills AC + plan, pipeline runs)
mem_work_items.acceptance_criteria / implementation_plan
        │ re-embedded on update
        ▼ (use_case: due_date hit, all children validated)
completed_at timestamp + MD moved to documents/completed/
```

### Embedding Fields (7 total)
`name | wi_type | summary | deliveries | delivery_type | acceptance_criteria[:500] | implementation_plan[:500]`

### ID Scheme
| Type | Seq Key | Prefix | Example |
|------|---------|--------|---------|
| use_case | WI_US | US | US0001 |
| feature | WI_FE | FE | FE0001 |
| bug | WI_BU | BU | BU0001 |
| task | WI_TA | TA | TA0001 |
| policy | WI_PO | PO | PO0001 |
| requirement | WI_RE | RE | RE0001 |
| AI draft | WI_AI | AI | AI0001 |
| rejected | WI_AI | REJ | REJ0001 |

---

## 5. Project Facts (mem_ai_project_facts)

**Trigger:** Every `POST /projects/{p}/memory` → `auto_populate_from_synthesis()`

**Flow:**
1. Build text from PROJECT.md + synthesis tech_stack + key_decisions
2. `fact_extraction` prompt (Haiku) → JSON array of `{fact_key, fact_value, category}`
3. For each fact: `save_fact()` checks existing row
   - No existing → INSERT + embed
   - Same value → skip
   - Different value → `detect_fact_conflicts()` → LLM resolves → supersede/merge/flag
4. Expire stale facts (updated > 90 days ago, low relevance)

**Categories:** `stack | pattern | convention | constraint | general`

---

## 6. Embedding / Semantic Search

| Target | Table | Column | Dimensions | When Updated |
|--------|-------|--------|-----------|--------------|
| Work items | `mem_work_items` | `embedding` | 1536 | On approve / on update (semantic fields) |
| Project facts | `mem_ai_project_facts` | `embedding` | 1536 | On save_fact() |
| Code docs | `mem_mrr_commits_code` | — | n/a | No embedding on code diffs |

**Model:** `text-embedding-3-small` (OpenAI), 1536 dimensions, cosine similarity

**MCP search_memory** searches: history (mem_mrr_prompts), commits (mem_mrr_commits), code (mem_mrr_commits_code), facts (mem_ai_project_facts), work items (mem_work_items).

---

## 7. MCP Server — 18 Tools

Defined in `backend/routers/route_mcp.py`. All scoped to a project.

| Tool | Purpose |
|------|---------|
| `search_memory` | Semantic search across all memory layers |
| `get_project_state` | PROJECT.md + active entities summary |
| `get_recent_history` | Last N prompt/response pairs |
| `get_commits` | Recent commits with metadata |
| `get_tagged_context` | All events for a phase/feature tag |
| `get_session_tags` | Current phase + feature tags |
| `set_session_tags` | Update session phase/feature |
| `list_work_items` | Work items by category/status |
| `get_item_by_number` | Single work item by seq_num |
| `create_entity` | Create feature/bug/task entity |
| `run_work_item_pipeline` | Trigger 4-agent PM→Arch→Dev→Review |
| `get_db_schema` | Full DB table structure |
| `sync_github_issues` | Import GitHub issues as work items |
| `commit_push` | Stage + commit + push |
| `get_roles` | List all agent role files |
| + 3 more | (embed-prompts, embed-commits, rebuild) |

---

## 8. Pipeline / Agent Architecture

**Pipelines:** 8 YAMLs in `workspace/_templates/pipelines/`
`standard | build_feature | code_review | python_api | quick_review | trading_strategy | ui_app | update_docs`

**Roles:** 11 YAMLs in `workspace/_templates/pipelines/roles/`
`product_manager | architect | developer | frontend_developer | backend_developer | devops_engineer | aws_architect | qa_engineer | reviewer | security_reviewer | internal_project_fact`

**Run modes:**
- `POST /agents/run` — single agent, full ReAct trace returned
- `POST /agents/run-pipeline` — multi-stage, per-stage results + verdict
- `POST /agents/run-graph` — DAG workflow (pr_graph_* tables), async with loop-back

---

## 9. Major Improvement Areas (Ranked)

### HIGH — Fix now
1. **`implementation_plan` missing from `approve()` embed** — FIXED 2026-04-27. Was passing 6/7 fields; now passes all 7.
2. **`fact_extraction` fallback duplicated** — FIXED 2026-04-27. Removed 6-line inline fallback; YAML is sole source.
3. **`_apply_date_rules()` re-parent gap** — FIXED. Re-parenting to UC now validates existing due_date.

### MEDIUM — Soon
4. **code.md embedding lag** — code.md updated per-commit, but `_embed_code_md()` only called on POST /memory. Fix: call after extract_commit_code() background task completes.
5. **`summarise` prompt unwired** — Defined in command_work_items.yaml, never called. Either wire it to a UI action or delete.
6. **`feature_auto_detect` in misc.yaml** — Verify if called anywhere; delete if dead.

### LOW — Backlog
7. **Project facts sparse** — auto_populate runs on /memory but first fact extraction may be empty until PROJECT.md has good content. No UI to view/edit facts.
8. **No test coverage metrics in MCP** — semantic search doesn't cover test results.
9. **Inline fallback in `agent.py`** — `_REACT_SYSTEM_BASE` and `_REACT_SUFFIX` still have long inline strings as `or` fallback. These are intentional safety nets; acceptable.

---

## 10. Key Files Reference

| File | Lines | Purpose |
|------|-------|---------|
| `backend/core/database.py` | ~1000 | DB helpers, role seeding, migrations |
| `backend/core/db_migrations.py` | 3280 | m001–m079 migration history |
| `backend/core/prompt_loader.py` | ~80 | Hot-reloadable YAML prompt cache |
| `backend/routers/route_projects.py` | 1693 | /memory, /status, project CRUD |
| `backend/routers/route_git.py` | 1691 | commit-store, push, diff |
| `backend/routers/route_work_items.py` | 461 | WI CRUD + approve/reject endpoints |
| `backend/memory/memory_work_items.py` | 2621 | Classification + approval + CRUD |
| `backend/memory/_wi_classify.py` | ~500 | Classification mixin |
| `backend/memory/_wi_helpers.py` | 279 | Shared helpers + embed |
| `backend/memory/_wi_markdown.py` | ~300 | MD file management mixin |
| `backend/memory/memory_files.py` | 990 | Context file renderer (no LLM) |
| `backend/memory/memory_backlog.py` | ~400 | Backlog digest pipeline |
| `backend/memory/memory_promotion.py` | ~400 | Project facts + conflict detection |
| `backend/memory/memory_code_parser.py` | 788 | tree-sitter per-symbol extraction |
| `backend/agents/agent.py` | ~400 | ReAct agent runner |
| `backend/agents/pipeline_orchestrator.py` | ~300 | Multi-stage pipeline runner |
