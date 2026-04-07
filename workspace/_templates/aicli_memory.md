# aicli Memory Pipeline — Architecture Reference

_Last updated: 2026-04-07 · Version 2.3.0_

---

## Overview

The aicli memory pipeline is a 4-layer system that captures developer activity (prompts, commits,
documents, messages), digests it with Haiku, embeds it with OpenAI, and promotes structured
artifacts (work items, project facts) upward toward human-managed planner tags.

```
Developer activity
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 0 — Source Trigger                               │
│  Hook scripts → POST /memory/* endpoints                │
└──────────────────────────┬──────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 1 — Mirror (mem_mrr_*)                           │
│  Raw data verbatim, inline tags JSONB                   │
└──────────────────────────┬──────────────────────────────┘
                           │ MemoryEmbedding.process_*()
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2 — AI Events (mem_ai_events)                    │
│  Haiku digest + OpenAI embedding + importance score     │
└──────────────────────────┬──────────────────────────────┘
                           │ MemoryPromotion.*()
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 3 — Structured Artifacts                         │
│  mem_ai_work_items  ·  mem_ai_project_facts             │
└──────────────────────────┬──────────────────────────────┘
                           │ User drag-drop / Planner button
                           ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 4 — User-Managed Tags (planner_tags)             │
│  Features · Bugs · Tasks — owned by users               │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Mirror Tables (`mem_mrr_*`)

### `mem_mrr_prompts` — Raw prompt/response pairs

**Trigger**: Hook script `post_prompt.sh` → `POST /memory/{project}/prompts`
**Responsible**: Trigger (auto, no LLM)

| Column | Responsible | Notes |
|--------|-------------|-------|
| `id` | Trigger | UUID PK |
| `session_id` | Trigger | Groups turns in a session |
| `source_id` | Trigger | External ID from hook |
| `prompt` | Trigger | Raw user input |
| `response` | Trigger | Raw AI response |
| `tags` | Trigger | Inline JSONB: `{source, phase, feature, work-item, llm}` |
| `created_at` | Trigger | Insert timestamp |

**Relevance score**: 0/5 — raw data, no digest yet; useful only as source for Layer 2

---

### `mem_mrr_commits` — Raw git commits

**Trigger**: Post-commit hook `post_commit.sh` → `POST /memory/{project}/commits`
**Responsible**: Trigger (auto, no LLM initially)

| Column | Responsible | Notes |
|--------|-------------|-------|
| `commit_hash` | Trigger | PK |
| `commit_msg` | Trigger | Git commit message |
| `summary` | **LLM** (back-propagated) | Haiku digest back-written by `process_commit()` |
| `tags` | Trigger + LLM | Initial: `{source, phase, feature}`; LLM adds `files`, `languages`, `symbols` |
| `session_id` | Trigger | Links to session |
| `committed_at` | Trigger | Git timestamp |

**`tags["files"]`**: `{filename: rows_changed}` — populated by `smart_chunk_diff()` from actual diff
**`tags["symbols"]`**: class/function names from diff (Python/JS/TS) — populated by code symbol extraction
**`tags["languages"]`**: list of languages in diff — populated by `_detect_language()`

**Relevance score**: 3/5 — commit message is useful; summary + files/symbols make it 4/5

---

### `mem_mrr_items` — Documents, requirements, decisions

**Trigger**: Manual `POST /memory/{project}/items` or CLI import
**Responsible**: User (creates) + LLM (digests)

| Column | Responsible | Notes |
|--------|-------------|-------|
| `id` | Trigger | UUID PK |
| `item_type` | User | `requirement`, `decision`, `meeting`, `note` |
| `title` | User | Short title |
| `raw_text` | User | Full document content |
| `summary` | **LLM** | Haiku digest (back-propagated if short item) |
| `tags` | User | Inline JSONB classification |

**Relevance score**: 4/5 — decisions and requirements are high-value; meeting notes 3/5

---

### `mem_mrr_messages` — Platform messages (Slack, Teams)

**Trigger**: Integration hook → `POST /memory/{project}/messages`
**Responsible**: Trigger (auto)

| Column | Responsible | Notes |
|--------|-------------|-------|
| `id` | Trigger | UUID PK |
| `platform` | Trigger | `slack`, `teams`, `discord` |
| `channel` | Trigger | Channel/thread name |
| `messages` | Trigger | JSONB array of `{user, text, ts}` |
| `tags` | Trigger | Session/feature classification |

**Relevance score**: 2/5 — discussion context; useful when linked to features

---

## Layer 2 — AI Events (`mem_ai_events`)

**Trigger**: `MemoryEmbedding.process_*()` — called after each mirror INSERT
**Responsible**: LLM (digest + importance) + Trigger (embedding)

| Column | Responsible | Notes |
|--------|-------------|-------|
| `id` | Trigger | UUID PK |
| `event_type` | Trigger | `prompt_batch`, `commit`, `item`, `message`, `session_summary`, `workflow` |
| `source_id` | Trigger | FK to mirror row |
| `session_id` | Trigger | Propagated from mirror |
| `chunk` | Trigger | 0=summary/digest, 1+=detail chunks |
| `chunk_type` | Trigger | `full`, `summary`, `section`, `diff_file`, `class`, `function` |
| `content` | **LLM** | Haiku digest text (chunk=0); raw diff/code (chunk>0) |
| `summary` | **LLM** | Haiku 1-2 sentence summary |
| `action_items` | **LLM** | Extracted open action items |
| `importance` | **LLM** | 0–10 score (1=trivial, 10=critical architecture) |
| `embedding` | Trigger | OpenAI text-embedding-3-small 1536-dim vector |
| `tags` | Trigger + LLM | Merged from mirror tags + LLM model label |
| `processed_at` | Trigger | Set after `promote_feature_snapshot()` consumes event |

### Prompt Batch Digest
- **LLM prompt**: `prompt_batch_digest` (mng_system_roles)
- **Input**: Last N prompt/response pairs from session
- **Output JSON**: `{summary, action_items, importance}`
- **Auto-trigger**: After digest, fires `extract_work_items_from_events()` in background

### Commit Digest
- **LLM prompt**: `commit_digest`
- **Input**: commit_msg + existing summary
- **Output JSON**: `{summary, action_items, importance}`
- **Extra**: Per-file diff chunks with code symbol extraction; generated files filtered

### Session Summary
- **LLM prompt**: `session_end_synthesis`
- **Trigger**: Stop hook → `POST /memory/{project}/session-summary`
- **Output JSON**: `{summary, open_threads, next_steps}`

**Relevance scores by event_type**:
- `session_summary`: 5/5 — highest signal, explicitly synthesised
- `commit` (chunk=0): 4/5 — Haiku digest with importance
- `prompt_batch` (chunk=0): 3/5 — batch digest
- `item`/`message`: 3/5
- diff_file chunks (chunk>0): 2/5 — raw code, useful for semantic search

---

## Layer 3 — Structured Artifacts

### `mem_ai_work_items` — AI-detected tasks/bugs/features

**Trigger**: `MemoryPromotion.extract_work_items_from_events()` — auto-triggered after each prompt batch
**Responsible**: LLM (all core fields)

| Column | Responsible | Notes |
|--------|-------------|-------|
| `id` | Trigger | UUID PK |
| `ai_category` | **LLM** | `bug`, `feature`, `task` |
| `ai_name` | **LLM** | Slug-style name, UNIQUE key |
| `ai_desc` | **LLM** | 1-2 sentence description |
| `summary` | **LLM** | 3-4 sentence status summary (updated by Planner) |
| `action_items` | **LLM** | Remaining tasks (updated by Planner) |
| `acceptance_criteria` | **LLM** | Testable criteria (updated by Planner) |
| `code_summary` | **LLM** | Code context from linked commits |
| `requirements` | **LLM** | Functional requirements |
| `status_ai` | **LLM** | AI-suggested status: `active`, `in_progress`, `done` |
| `status_user` | **User** | User-set lifecycle: `active`, `in_progress`, `paused`, `done` |
| `tag_id` | **User** | User-confirmed link to planner_tag (drag-drop only) |
| `ai_tag_id` | **LLM** | AI-suggested tag match (auto-set by `match_work_item_to_tags()`) |
| `start_date` | User + Trigger | Set when status_user→in_progress; editable |
| `tags` | **LLM** | Stats JSONB: `{total_time, prompts_cnt, total_words, commit_count}` |
| `source_event_id` | Trigger | Source mem_ai_events row (prevents re-extraction) |
| `embedding` | Trigger | Vector for semantic work-item search |
| `seq_num` | Trigger | Auto-increment display number |

**LLM prompt**: `work_item_extraction` (in mng_system_roles)
**Input**: Event summary + action_items
**Output JSON**: `{items: [{category, name, description}]}`

**Matching pipeline** (auto-run after extraction):
1. Exact name match against planner_tags → `ai_tag_id` set at confidence 1.0
2. Vector similarity >0.85 → `ai_tag_id` set automatically
3. Haiku judgment for 0.70–0.85 borderline → `ai_tag_id` set if approved
4. `tag_id` is NEVER auto-set — only user drag-drop in UI

**Relevance scores**:
- `ai_desc` + `summary`: 5/5 — core work item signal
- `acceptance_criteria` + `action_items`: 5/5 — actionable
- `code_summary`: 4/5 — code context
- `status_user`: 4/5 — user tracks progress
- `status_ai`: 3/5 — AI suggestion only

---

### `mem_ai_project_facts` — Durable project facts

**Trigger**: `MemoryPromotion.detect_fact_conflicts()` — called during feature snapshots
**Responsible**: LLM (extraction) + User (review of flagged conflicts)

| Column | Responsible | Notes |
|--------|-------------|-------|
| `fact_key` | **LLM** | Unique fact identifier |
| `fact_value` | **LLM** | Current fact value |
| `category` | **LLM** | `stack`, `convention`, `constraint`, etc. |
| `valid_from` | Trigger | When fact was set |
| `valid_until` | Trigger | Set when superseded (NULL = current) |
| `conflict_status` | LLM + User | `ok`, `supersede`, `merge`, `flag` |
| `embedding` | Trigger | Vector for semantic fact search |

**LLM prompt**: `conflict_detection`
**Input**: Old fact value vs new fact value
**Output**: `{resolution: supersede|merge|flag, merged_value, reasoning}`

**Relevance score**: 4/5 — architectural decisions, constraints, stack choices are high value

---

## Layer 4 — User-Managed Tags (`planner_tags`)

**Responsible**: User (all fields) — LLM writes ONLY via explicit Planner button
**Trigger**: None — no auto-write; only `promote_feature_snapshot()` or `run_planner()` when invoked

| Column | Responsible | Notes |
|--------|-------------|-------|
| `id` | User (create) | UUID PK |
| `name` | **User** | Tag name, UNIQUE per project+category |
| `category_id` | **User** | FK to mng_tags_categories: feature/bug/task |
| `status` | **User** | `open`, `active`, `done`, `archived` |
| `priority` | **User** | 1–5 |
| `short_desc` | **User** | 1-line description |
| `full_desc` | **User** | Full description |
| `requirements` | **User** | What the feature must do (user-written) |
| `due_date` | **User** | Target completion date |
| `requester` | **User** | Who requested it |
| `summary` | **LLM** (Planner) | Written by `run_planner()` — use case summary |
| `action_items` | **LLM** (Planner) | Remaining work items from Planner |
| `acceptance_criteria` | **LLM** (Planner) | Testable QA criteria from Planner |
| `design` | **LLM** (snapshot) | `{high_level, low_level, patterns_used}` from feature_snapshot |
| `code_summary` | **LLM** (snapshot) | `{files, key_classes, key_methods}` from feature_snapshot |
| `embedding` | Trigger | Vector from summary+action_items |

**LLM prompts that write to planner_tags**:
- `feature_snapshot` → `promote_feature_snapshot()` → writes `summary`, `action_items`, `design`, `code_summary`
- `planner_summary` → `run_planner()` → writes `summary`, `action_items`, `acceptance_criteria`

---

## Data Flow Triggers Summary

| Event | Trigger | Handler | Target |
|-------|---------|---------|--------|
| AI session prompt | post_prompt hook | `POST /memory/{p}/prompts` | mem_mrr_prompts |
| Every ~5 prompts | Auto in route | `process_prompt_batch()` | mem_ai_events |
| After prompt batch | Auto (asyncio.ensure_future) | `extract_work_items_from_events()` | mem_ai_work_items |
| Work item created | Auto | `match_work_item_to_tags()` | ai_tag_id on work item |
| Git commit | post_commit hook | `POST /memory/{p}/commits` | mem_mrr_commits |
| Commit stored | Auto | `process_commit()` | mem_ai_events (digest+diff chunks) |
| Session end | Stop hook | `POST /memory/{p}/session-summary` | mem_ai_events (session_summary) |
| Session end | Auto | `write_root_files()` | CLAUDE.md, .cursorrules |
| User clicks "Snapshot" | Manual (UI) | `promote_feature_snapshot()` | planner_tags |
| User clicks "Run Planner" | Manual (UI) | `run_planner()` | planner_tags + work_items + doc file |
| User drag-drops work item | Manual (UI) | `PATCH /work-items/{id}` | tag_id on work item |

---

## Gap Analysis — What Data Is Missing

| Gap | Impact | Fix Needed |
|-----|--------|-----------|
| `code_summary` on work items is often empty | 3/5 | Populate from linked mem_mrr_commits.tags["symbols"] |
| 64 stale `#20xxx` bug work items | 2/5 | Dedup: merge work items with no tag_id + no prompts |
| `promote_feature_snapshot()` reads ALL events | 2/5 | Filter by `tags->>'feature'=tag_name` |
| Session-end snapshot not auto-triggered | 3/5 | Stop hook → session-summary → call promote_feature_snapshot |
| Work item stats (prompts_cnt etc.) not in tags | 2/5 | Compute and store as tags stats on extract |

---

## Importance Score Guide (0–10)

| Score | Meaning | Example |
|-------|---------|---------|
| 1–2 | Trivial / chore | Formatting fix, typo, minor cleanup |
| 3–4 | Minor fix | Bug fix, small refactor |
| 5–6 | Feature work | New endpoint, UI component, integration |
| 7–8 | Significant change | New module, schema migration, architecture change |
| 9–10 | Critical / architectural | Core system redesign, security change, data model change |

**Relevance formula**: `importance × exp(-0.01 × age_days)` — foundational facts get 50% floor

---

## MCP Exposure

All memory data is exposed via the `aicli_project` MCP server:
- `search_memory(query)` — semantic search over mem_ai_events embeddings
- `get_recent_history(limit)` — latest prompt/response pairs
- `list_work_items(category)` — active work items with status
- `get_project_state()` — PROJECT.md + active entities

**Chunking for MCP**: mem_ai_events chunks are sized ≤6000 chars. Diff files are stored per-file
with symbol names in tags, making semantic search effective for "which files changed for feature X".

---

_Auto-generated by aicli · see backend/memory/ for implementation details_
