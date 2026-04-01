# aicli Memory System — Architecture Reference

_Last updated: 2026-04-01 | v4.0 — Three-Layer Memory Architecture_

---

## Overview

aicli uses a **three-layer memory architecture** that persists context across every AI tool —
Claude Code, Cursor, the web UI, the aicli CLI, and pipeline agents.

Storage is **DB-primary**: PostgreSQL 15 with pgvector (VECTOR(1536) via text-embedding-3-small).
Three explicit layers build on each other: raw source data → AI digests + embeddings → distilled
output files. Every layer is searchable and tag-aware.

---

## The Three Layers

```
Layer 1 — Mirroring (mem_mrr_*)
  Store source data as-is. Every row carries ai_tags status.
  mem_mrr_prompts | mem_mrr_commits | mem_mrr_items | mem_mrr_messages | mem_mrr_tags

Layer 2 — AI / Embedding (mem_ai_*)
  One summarised + embedded row per unit.
  mem_ai_events | mem_ai_tags | mem_ai_project_facts | mem_ai_work_items | mem_ai_features

Layer 3 — Tag Hierarchy (planner_*)
  Per-project tag registry with categories, hierarchy, metadata, and relations.
  planner_tags | planner_tags_meta | mng_ai_tags_relations
```

---

## Complete Table Reference

### Global Tables (`mng_*`)

| Table | Purpose |
|-------|---------|
| `mng_clients` | Client registry |
| `mng_users` | User accounts + bcrypt passwords + billing balances |
| `mng_usage_logs` | Per-request token usage + cost |
| `mng_transactions` | Balance top-ups + charges |
| `mng_session_tags` | Current session context (phase, feature, bug_ref) per project |
| `mng_tags_categories` | Global tag category vocabulary (feature/bug/task/design/decision/meeting/ai_suggestion) |
| `mng_agent_roles` | Agent role definitions (system_prompt, tools JSONB, react BOOL, max_iterations INT) |
| `mng_agent_role_versions` | Version history for agent roles |
| `mng_system_roles` | Internal LLM prompts for memory pipeline (15 prompts, editable from Roles UI) |
| `mng_ai_tags_relations` | **Global** directed relations between planner_tags (depends_on, blocks, relates_to, etc.) |

### Tag Hierarchy Tables (`planner_*`)

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `planner_tags` | id UUID PK, client_id, project, name, category_id FK→mng_tags_categories, parent_id FK→self, lifecycle, status, seq_num | Per-project tag registry — every feature/bug/task has a tag |
| `planner_tags_meta` | tag_id UUID UNIQUE FK→planner_tags, description TEXT, requirements TEXT, due_date, priority | Work item metadata for tags |

### Layer 1 — Mirroring Tables (`mem_mrr_*`)

All have `ai_tags TEXT` column: `NULL` = not yet processed · `'approved'` = AI-suggested & accepted · `'ignored'` = rejected

| Table | Key Columns | Written by |
|-------|-------------|-----------|
| `mem_mrr_prompts` | id UUID PK, client_id, project, session_id, prompt TEXT, response TEXT, phase, source, ai_tags, work_item_id FK→mem_ai_work_items | Hooks + UI chat |
| `mem_mrr_commits` | commit_hash TEXT PK, client_id, project, commit_msg, diff TEXT, diff_details JSONB, session_id, phase, feature, ai_tags | auto_commit_push.sh hook |
| `mem_mrr_items` | id UUID PK, client_id, project, item_type, title, raw_text, summary, ai_tags | Item ingest API |
| `mem_mrr_messages` | id UUID PK, client_id, project, platform, channel, content, ai_tags | Platform connectors |
| `mem_mrr_tags` | id UUID PK, tag_id FK→planner_tags, session_id, prompt_id FK→mem_mrr_prompts, commit_id FK→mem_mrr_commits, item_id FK→mem_mrr_items, message_id FK→mem_mrr_messages, auto_tagged | All tagging paths — any combination of source FKs, no one-source CHECK |

### Layer 2 — AI / Embedding Tables (`mem_ai_*`)

| Table | Key Columns | Purpose |
|-------|-------------|---------|
| `mem_ai_events` | id UUID PK, client_id, project, event_type TEXT, source_id TEXT, session_id, chunk INT, chunk_type TEXT, content TEXT, **embedding VECTOR(1536)**, summary TEXT, importance SMALLINT, processed_at, UNIQUE(client_id, project, event_type, source_id, chunk) | Unified embedding table — one row per digested unit |
| `mem_ai_tags` | id UUID PK, event_id FK→mem_ai_events, tag_id FK→planner_tags, ai_suggested BOOL, UNIQUE(event_id, tag_id) | Links tags to AI events (promoted from mem_mrr_tags when event is created) |
| `mem_ai_project_facts` | id UUID PK, client_id, project, fact_key TEXT, fact_value TEXT, category TEXT, **embedding VECTOR(1536)**, valid_from, valid_until (NULL=current), source_memory_id UUID | Durable facts with temporal validity |
| `mem_ai_work_items` | id UUID PK, client_id, project, category_name TEXT, name TEXT, description TEXT, status, lifecycle_status, acceptance_criteria TEXT, implementation_plan TEXT, tag_id FK→planner_tags, **embedding VECTOR(1536)**, agent_run_id, agent_status, seq_num INT | Feature/bug/task items with 4-agent pipeline |
| `mem_ai_features` | id UUID PK, client_id, project, tag_id FK→planner_tags, requirements TEXT, action_items TEXT, design JSONB, code_summary JSONB, file_paths TEXT[], **embedding VECTOR(1536)**, UNIQUE(client_id, project, tag_id) | 4-layer feature snapshots |

`event_type` values in `mem_ai_events`: `'prompt_batch'` · `'commit'` · `'item'` · `'message'` · `'session_summary'` · `'workflow'`

### Graph Tables (`pr_*`)

`pr_graph_workflows` | `pr_graph_nodes` | `pr_graph_edges` | `pr_graph_runs` | `pr_graph_node_results` | `pr_seq_counters`

---

## Data Flow

```
Prompt arrives
  → mem_mrr_prompts (ai_tags=NULL)
  → every N prompts: MemoryEmbedding.process_prompt_batch()
      → Haiku digest → embed → mem_ai_events (event_type='prompt_batch')
      → tags copied: mem_mrr_tags → mem_ai_tags  [promote_source_tags_to_event()]
  → if context_tags in hook payload: mem_mrr_tags auto-created

Commit arrives
  → mem_mrr_commits (ai_tags=NULL)
  → MemoryEmbedding.process_commit()
      → Haiku digest → embed → mem_ai_events (event_type='commit')
      → tags copied: mem_mrr_tags → mem_ai_tags

Work item created/patched
  → mem_ai_work_items
  → _embed_work_item() background: embed name+description+criteria → embedding VECTOR

/memory run or session end
  → _extract_project_facts()
      → Haiku reads mem_ai_events → [{key, value, confidence}]
      → temporal upsert → mem_ai_project_facts
      → _embed_project_facts() background: embed fact_key+fact_value → embedding VECTOR
  → MemoryFiles.write_root_files() → CLAUDE.md, .cursorrules, top_events.md

Feature snapshot triggered (POST /projects/{p}/snapshot/{tag} or lifecycle→done)
  → MemoryPromotion.promote_feature_snapshot()
      → Haiku reads mem_ai_events for tag → 4-layer JSON
      → upsert mem_ai_features (requirements, action_items, design, code_summary, embedding)

AI tag suggestions
  → MemoryTagging.suggest_tags_for_untagged()
      → scans mem_mrr_* rows with ai_tags=NULL
      → scans mem_ai_events with no mem_ai_tags entry
      → Haiku suggests tag per event → returned to UI for approve/ignore
```

---

## Memory Output Files

Written by `MemoryFiles` class (`backend/memory/memory_files.py`):

| File | Location | Read by |
|------|----------|---------|
| `CLAUDE.md` | `{code_dir}/CLAUDE.md` | Claude Code (auto-loaded) |
| `.cursorrules` | `{code_dir}/.cursorrules` | Cursor (auto-loaded) |
| `top_events.md` | `{code_dir}/.claude/memory/top_events.md` | Claude Code (per-session inject) |
| `compact.md` | `workspace/{p}/_system/llm_prompts/compact.md` | GPT-4 / small context |
| `full.md` | `workspace/{p}/_system/llm_prompts/full.md` | Claude / Deepseek / Gemini |
| `features/{tag}/CLAUDE.md` | `{code_dir}/features/{tag}/CLAUDE.md` | Per-feature auto-load |

---

## Memory Python Classes (`backend/memory/`)

| Class | File | Responsibility |
|-------|------|----------------|
| `MemoryMirroring` | `memory_mirroring.py` | Store raw rows, `get_untagged()`, `set_ai_tag_status()` |
| `MemoryTagging` | `memory_tagging.py` | Tag CRUD, `link_to_mirroring()`, `link_to_event()`, `promote_source_tags_to_event()`, `suggest_tags_for_untagged()`, `add_relation()` |
| `MemoryEmbedding` | `memory_embedding.py` | `process_prompt_batch()`, `process_commit()`, `process_item()`, `process_messages()`, `semantic_search()` |
| `MemoryPromotion` | `memory_promotion.py` | `promote_feature_snapshot()`, `promote_work_item()`, `detect_fact_conflicts()` |
| `MemoryFiles` | `memory_files.py` | Render + write `CLAUDE.md`, `.cursorrules`, `top_events.md`, per-feature files |

---

## MCP Tools (Claude Code / Cursor — `backend/agents/mcp/server.py`)

18 tools via stdio JSON-RPC. All call the FastAPI backend via HTTP.

| Tool | Endpoint | What it reads |
|------|----------|---------------|
| `search_memory` | `POST /search/semantic` | `mem_ai_events` (vector + text) |
| `get_project_state` | `GET /projects/{p}` + `/work-items` + `/work-items/facts` | PROJECT.md + active work items + facts |
| `get_recent_history` | `GET /history/chat` | `mem_mrr_prompts` |
| `get_commits` | `GET /history/commits` | `mem_mrr_commits` |
| `get_tagged_context` | `GET /search/tagged` | `mem_mrr_prompts JOIN mem_mrr_tags JOIN planner_tags` |
| `get_session_tags` | `GET /history/session-tags` | `mng_session_tags` |
| `set_session_tags` | `PUT /history/session-tags` | `mng_session_tags` (write) |
| `commit_push` | `POST /git/{p}/commit-push` | git + `mem_mrr_commits` (write) |
| `list_work_items` | `GET /work-items` | `mem_ai_work_items` |
| `run_work_item_pipeline` | `POST /work-items/{id}/run-pipeline` | pipeline trigger |
| `get_item_by_number` | `GET /work-items/number/{seq}` | `mem_ai_work_items` |
| `create_entity` | `POST /tags` | `planner_tags` (write) |
| `sync_github_issues` | `POST /entities/github-sync` | GitHub API → `planner_tags` |
| **`search_facts`** | `GET /work-items/facts/search` | `mem_ai_project_facts.embedding` |
| **`search_work_items`** | `GET /work-items/search` | `mem_ai_work_items.embedding` |
| **`get_tag_context`** | `GET /tags/context` | planner_tags + mem_ai_events + mem_ai_features + mem_ai_work_items + mng_ai_tags_relations |
| `get_roles` | `GET /prompts/` | `mng_agent_roles` |
| `get_db_schema` | (inline) | Schema reference |

---

## Pipeline Agent Tools (ReAct — `backend/agents/tools/`)

14 tools for agents running inside the 4-agent pipeline (PM → Architect → Developer → Reviewer).
Direct DB access (no HTTP). Available to roles based on `mng_agent_roles.tools JSONB`.

### Memory tools (`tool_memory.py`)

| Tool | What it reads |
|------|---------------|
| `search_memory` | Vector search on `mem_ai_events.embedding`, text fallback, optional tag filter |
| `get_recent_history` | `mem_mrr_prompts` with optional `mem_mrr_tags JOIN planner_tags` filter |
| `get_project_facts` | `mem_ai_project_facts WHERE valid_until IS NULL` (grouped by category) |
| **`get_tag_context`** | Full tag context: `planner_tags` + `planner_tags_meta` + `mem_ai_features` + `mem_ai_events` via `mem_ai_tags` + `mem_ai_work_items` + `mng_ai_tags_relations` |
| **`search_features`** | Vector or name search on `mem_ai_features.embedding` → requirements + action_items + code_summary |

### Work item tools (`tool_workitems.py`)

| Tool | What it reads/writes |
|------|----------------------|
| `list_work_items` | `mem_ai_work_items` (direct — no tag join required) |
| `create_work_item` | `planner_tags` + `planner_tags_meta` + `mem_ai_work_items` (write, assigns seq_num) |

### File tools (`tool_file.py`)

`read_file` · `write_file` · `list_dir` — filesystem access within `code_dir`

### Git tools (`tool_git.py`)

`git_status` · `git_diff` · `git_commit` · `git_push`

---

## Tagging System

### Three tagging paths for mirroring layer

**Path 1 — Session context** (`check_session_context.sh` hook):
- Reads `.agent-context` file → `_tag_prompt_from_context()` → inserts `mem_mrr_tags(prompt_id, tag_id, auto_tagged=True)`

**Path 2 — Manual from Planner UI** (`route_tags.py`):
- `POST /tags/source` → inserts `mem_mrr_tags` row

**Path 3 — AI suggestion** (`MemoryTagging.suggest_tags_for_untagged()`):
- Scans `mem_mrr_*` rows with `ai_tags IS NULL` and `mem_ai_events` with no `mem_ai_tags` entry
- Haiku suggests tag → user approve/ignore in UI → sets `ai_tags='approved'|'ignored'`

### Tag promotion to AI layer

When `MemoryEmbedding` creates a `mem_ai_events` row, it calls
`MemoryTagging.promote_source_tags_to_event(event_id, source_type, source_ids)`:
- Copies distinct `tag_id` values from `mem_mrr_tags` for the contributing sources → `mem_ai_tags`
- This ensures every AI event inherits the tags of its source data

### Tag relations (`mng_ai_tags_relations`)

Directed edges between `planner_tags`. Relation types: `part_of` · `depends_on` · `blocks` · `relates_to` · `replaces` · `extracted_from`

---

## 4-Layer Feature Snapshot

Generated by `MemoryPromotion.promote_feature_snapshot()` or `POST /projects/{p}/snapshot/{tag}`:

```
1. Resolve tag_id from planner_tags WHERE name = tag_name
2. Load mem_ai_events via mem_ai_tags JOIN WHERE tag_id
3. Load mem_mrr_prompts/commits/items referenced in mem_mrr_tags for this tag
4. Load mem_ai_work_items WHERE tag_id = tag_id
5. Call Haiku with feature_snapshot prompt → parse JSON
6. Upsert mem_ai_features (ON CONFLICT tag_id DO UPDATE)
7. Embed (requirements + action_items) → embedding VECTOR(1536) on mem_ai_features
8. Mark contributing mem_ai_events.processed_at = NOW()
```

JSON output shape:
```json
{
  "requirements": "what the feature must do",
  "action_items": "open tasks and next steps",
  "design": {
    "high_level": "architecture overview",
    "low_level": "implementation details",
    "patterns_used": ["ReAct", "pgvector cosine search"]
  },
  "code_summary": {
    "files": ["backend/routers/route_tags.py"],
    "key_classes": ["MemoryTagging"],
    "key_methods": ["promote_source_tags_to_event"],
    "dependencies_added": [],
    "dependencies_removed": []
  }
}
```

---

## How Pipelines Use Memory

The 4-agent work item pipeline (PM → Architect → Developer → Reviewer) runs via ReAct loop.
Each agent calls tools in this order:

### PM Agent (product_manager role)
1. `get_tag_context(tag_name)` — full history, snapshot, relations, open work items
2. `get_project_facts()` — architectural constraints
3. `search_memory(query)` — any relevant past decisions
4. Output: `{acceptance_criteria, work_items, risks, confidence}`

### Architect Agent
1. `get_tag_context(tag_name)` — understand existing design
2. `search_features(query)` — find similar features for pattern reuse
3. `get_project_facts()` — constraints (DB choice, auth method, etc.)
4. `read_file(path)` — inspect relevant source files
5. Output: `{approach, files_to_touch, patterns, conflicts_with_existing}`

### Developer Agent
1. `search_memory(query)` — find similar past implementations
2. `read_file(path)` → `write_file(path)` → `git_diff()` → `git_commit()`
3. Output: `{changes_made, tests_run, issues_encountered}`

### Reviewer Agent
1. `git_diff()` — inspect what changed
2. `read_file(path)` — verify implementation
3. `search_memory(query)` — check against past decisions
4. Output: `{verdict: pass|reject|needs_changes, issues, suggested_fixes}`

---

## Memory System Prompts (`mng_system_roles` — 15 prompts)

All editable from the **Roles** tab in the UI (category = 'memory'). Seeded from
`workspace/_templates/memory/prompts.yaml` at startup.

| Name | Model | Trigger |
|------|-------|---------|
| `commit_digest` | Haiku | On commit embed |
| `prompt_batch_digest` | Haiku | Every N prompts |
| `item_digest` | Haiku | On item embed |
| `meeting_sections` | Haiku | Meeting item chunking |
| `message_chunk_digest` | Haiku | On message embed |
| `ai_tag_suggestion` | Haiku | Untagged row scan |
| `relation_extraction` | Haiku | Tag relation suggestions |
| `session_summary` | Haiku | Session end |
| `session_review` | Haiku | After session_summary (Trycycle quality gate) |
| `session_end_synthesis` | Haiku | Final session wrap |
| `memory_synthesis` | Haiku | Every `/memory` run |
| `work_item_promotion` | Haiku | Work item pipeline |
| `conflict_detection` | Haiku | Fact conflict check |
| `feature_snapshot` | Haiku | Feature snapshot (6 batch types) |
| `internal_project_fact` | Haiku | Fact extraction from mem_ai_events |

---

## Hook Flow

### Hook 1: `check_session_context.sh` (UserPromptSubmit — runs first)
1. Skip noise (`<task-notification>`, `<tool-use-id>`, etc.)
2. Read `workspace/{project}/_system/.agent-context`
3. If missing/stale: write defaults, print context to user, **exit 2 (block)**
4. Second attempt: file exists → exit 0 (allow)

### Hook 2: `log_user_prompt.sh` (UserPromptSubmit)
1. Read stdin JSON → extract prompt + session_id + context_tags
2. `POST /chat/{project}/hook-log` → inserts `mem_mrr_prompts`
3. Backend: counts session prompts → if `count % batch_size == 0`: fires `process_prompt_batch()`
4. Backend: if `context_tags` non-empty → fires `_tag_prompt_from_context()`

### Hook 3: `log_session_stop.sh` (Stop)
1. Extract last assistant response from session JSONL
2. `POST /chat/{project}/hook-response` → updates `mem_mrr_prompts.response`
3. Background: `POST /projects/{project}/memory` (non-blocking)

### Hook 4: `auto_commit_push.sh` (Stop)
1. If `auto_commit_push: yes` in `project.yaml` → `POST /git/{project}/commit-push`

---

## Key Design Decisions

| Decision | Why |
|----------|-----|
| **Named layer prefixes** (`mem_mrr_*`, `mem_ai_*`, `planner_*`) | Table purpose is self-documenting; eliminates "which table is this?" confusion |
| **Single embedding table** (`mem_ai_events`) | One search target for all event types; `event_type` column discriminates; avoids join complexity |
| **Embeddings on all mem_ai_* tables** | `mem_ai_events`, `mem_ai_features`, `mem_ai_project_facts`, `mem_ai_work_items` all have `VECTOR(1536)` — every artifact layer is semantically searchable |
| **Wide junction table** (`mem_mrr_tags`) | No CHECK constraint — a tag can be linked to prompts AND commits simultaneously; enables richer tag history |
| **Tag promotion** (`promote_source_tags_to_event`) | AI events automatically inherit tags from source rows — semantic search results are already tag-filtered |
| **`get_tag_context` in both MCP and agent tools** | PM agent needs full tag history before writing acceptance criteria; available whether running in Claude Code, Cursor, or the pipeline |
| **Temporal facts** (`valid_until IS NULL`) | Full audit trail; change detection without data loss; query past state at any timestamp |
| **Haiku for all LLM calls** | Cost/quality trade-off: digests + fact extraction + tag suggestions are Haiku; only Sonnet for graph workflows |
| **System prompts in DB** (`mng_system_roles`) | All 15 memory prompts editable from Roles UI without code changes; versioned via `mng_agent_role_versions` |
