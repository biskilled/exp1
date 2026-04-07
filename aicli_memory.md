# aicli — Memory & Tagging Architecture

_Last updated: 2026-04-07 | Updated for migration 014 + importance scoring + auto-extract pipeline_

---

## 0. Mental Model

aicli memory has **4 active layers** stacked on top of each other.
**planner_tags** is the user-managed top layer; everything below is LLM/trigger-managed.

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │ Layer 0 — Ephemeral         In-session message list (RAM / JSON)     │
 │ Layer 1 — Raw Capture       Everything stored as-is   (mem_mrr_*)    │
 │ Layer 2 — AI Events         Digested + embedded        (mem_ai_events)│
 │ Layer 3 — Structured        Work Items + Project Facts                │
 │ Layer 4 — User Tags         planner_tags  (USER-MANAGED)              │
 └──────────────────────────────────────────────────────────────────────┘
```

**Key design principle**:
- `planner_tags` = **User** owns this. LLM only writes when user clicks "Run Planner" or "Snapshot".
- Everything below `planner_tags` = **LLM + Triggers** own it. User does not manually edit.
- `tag_id` on work items = **User** sets via drag-drop only. `ai_tag_id` = LLM suggestion (auto).

---

## Layer 0 — Ephemeral (Session Messages)

**Responsible**: Trigger (auto, no DB)
**Storage**: `workspace/{project}/_system/sessions/{session_id}.json`
**Python class**: `SessionStore` (`backend/memory/mem_sessions.py`)

Not stored in PostgreSQL — file-only, short-lived within a session.

---

## Layer 1 — Raw Capture (`mem_mrr_*`)

Everything stored verbatim as received. No AI processing. The audit trail.

### `mem_mrr_prompts`

**Trigger**: `post_prompt.sh` hook → `POST /memory/{p}/prompts`

| Column | Responsible | Notes |
|--------|-------------|-------|
| `id` UUID | Trigger | PK |
| `session_id` | Trigger | Groups turns in a session |
| `source_id` | Trigger | External ID from hook |
| `prompt` TEXT | Trigger | Raw user input |
| `response` TEXT | Trigger | Raw AI response |
| `tags` JSONB | Trigger | `{source, phase, feature, work-item, llm}` — inline tagging |
| `created_at` | Trigger | Insert timestamp |

**Relevance: 0/5** — raw data, no digest; only useful as source for Layer 2

---

### `mem_mrr_commits`

**Trigger**: `post_commit.sh` hook → `POST /memory/{p}/commits`

| Column | Responsible | Notes |
|--------|-------------|-------|
| `commit_hash` | Trigger | PK |
| `commit_msg` | Trigger | Git commit message |
| `summary` TEXT | **LLM** (back-propagated) | Haiku digest written by `process_commit()` |
| `tags` JSONB | Trigger + **LLM** | Initial: `{source, phase, feature}`; LLM adds `files`, `languages`, `symbols` |
| `session_id` | Trigger | Links to session |
| `committed_at` | Trigger | Git timestamp |

**`tags["files"]`** — `{filename: rows_changed}` — populated by `smart_chunk_diff()` (code files only; CLAUDE.md/.cursorrules/MEMORY.md excluded)
**`tags["symbols"]`** — class/function names extracted from diff (Python, JS, TS)
**`tags["languages"]`** — list of languages in changed files

**NOTE**: `diff_details` and `diff_summary` columns were **DROPPED** in migration 008. Do not reference them.

**Relevance: 3/5** — commit_msg useful; summary+files/symbols make it 4/5

---

### `mem_mrr_items`

**Trigger**: Manual `POST /memory/{p}/items` or CLI import

| Column | Responsible | Notes |
|--------|-------------|-------|
| `id` UUID | Trigger | PK |
| `item_type` | **User** | `requirement`, `decision`, `meeting`, `note` |
| `title` | **User** | Short title |
| `raw_text` | **User** | Full document content |
| `summary` TEXT | **LLM** (back-propagated) | Haiku digest |
| `tags` JSONB | User | Classification |

**Relevance: 4/5** — decisions and requirements are high-value

---

### `mem_mrr_messages`

**Trigger**: Integration hook → `POST /memory/{p}/messages`

| Column | Responsible | Notes |
|--------|-------------|-------|
| `platform` | Trigger | `slack`, `teams`, `discord` |
| `channel` | Trigger | Channel/thread name |
| `messages` JSONB | Trigger | Array of `{user, text, ts}` |
| `tags` JSONB | Trigger | Session/feature classification |

**Relevance: 2/5** — useful when linked to features

---

## Layer 2 — AI Events (`mem_ai_events`)

Every Layer 1 source gets digested by Haiku and embedded. Primary semantic search target.

**Trigger**: `MemoryEmbedding.process_*()` — called after each mirror INSERT
**Responsible**: LLM (digest + importance) + Trigger (embedding)

| Column | Responsible | Notes |
|--------|-------------|-------|
| `id` UUID | Trigger | PK |
| `event_type` | Trigger | `prompt_batch` \| `commit` \| `item` \| `message` \| `session_summary` \| `workflow` |
| `source_id` | Trigger | FK to mirror row |
| `session_id` | Trigger | Propagated from mirror |
| `chunk` INT | Trigger | 0=summary/digest, 1+=detail chunks |
| `chunk_type` | Trigger | `full`, `summary`, `section`, `diff_file`, `class`, `function` |
| `content` TEXT | **LLM** | Haiku digest text (chunk=0); raw diff/code text (chunk>0) |
| `summary` TEXT | **LLM** | Haiku 1-2 sentence summary |
| `action_items` TEXT | **LLM** | Extracted open action items |
| `importance` SMALLINT | **LLM** | **0–10** AI-scored (1=trivial, 10=critical architecture) |
| `embedding` VECTOR(1536) | Trigger | OpenAI text-embedding-3-small |
| `tags` JSONB | Trigger + LLM | Merged from mirror tags + `{llm: model_name}` |
| `processed_at` | Trigger | Set after `promote_feature_snapshot()` consumes event |

### Importance Score Scale (LLM-assigned)

| Score | Meaning |
|-------|---------|
| 1–2 | Trivial / chore (typo, formatting) |
| 3–4 | Minor fix / debug |
| 5–6 | Feature work, new endpoint |
| 7–8 | Significant change, new module |
| 9–10 | Critical / architectural decision |

### How each `event_type` is produced

#### `prompt_batch`
- **When**: Auto after every ~5 prompts in a session
- **LLM prompt**: `prompt_batch_digest` → returns `{summary, action_items, importance}`
- **Auto-triggers**: `extract_work_items_from_events()` in background (asyncio.ensure_future)
- **Chunks**: chunk=0 = Haiku digest; chunk≥1 = long response paragraphs (raw embed)

#### `commit`
- **When**: After `POST /memory/{p}/commits` → `process_commit()` called
- **LLM prompt**: `commit_digest` → returns `{summary, action_items, importance}`
- **Chunks**: chunk=0 = Haiku digest; chunk≥1 = per-file diff (code files only, generated files filtered)
- **Tags back-propagated** to `mem_mrr_commits`: `files`, `languages`, `symbols`

#### `item`
- **When**: After `POST /memory/{p}/items` → `process_item()` called
- **LLM prompts**: `item_digest` → `{summary, action_items, importance}`; `relation_extraction` for tag relationships
- **Chunks**: per-section for meetings/large items

#### `session_summary`
- **When**: `log_session_stop.sh` → `POST /memory/{p}/session-summary`
- **LLM prompt**: `session_end_synthesis` → `{summary, open_threads, next_steps}`
- **importance**: typically 7-8 (session-level synthesis)

#### `workflow`
- **When**: After a 4-agent pipeline run completes
- **No LLM digest** — raw workflow output embedded directly

### Relevance Scoring Formula

```
relevance = importance × exp(-0.01 × age_days)
```
Foundational facts get 50% floor. Time-decay surfaces recent events first.

**Scores by event_type**:
- `session_summary`: 5/5 — highest signal
- `commit` chunk=0: 4/5 — Haiku digest with importance
- `prompt_batch` chunk=0: 3/5 — batch digest
- `item` / `message`: 3/5
- diff_file chunks (chunk>0): 2/5 — raw code, useful for semantic search only

---

## Layer 3 — Structured Artifacts

### `mem_ai_work_items` — AI-detected tasks/bugs/features

**Trigger**: `MemoryPromotion.extract_work_items_from_events()` — **auto-triggered** after each prompt batch
**Responsible**: LLM for all core fields; User for status_user + tag_id only

| Column | Responsible | Relevance | Notes |
|--------|-------------|-----------|-------|
| `ai_category` | **LLM** | 4/5 | `bug`, `feature`, `task` |
| `ai_name` | **LLM** | 5/5 | Slug-style, UNIQUE key |
| `ai_desc` | **LLM** | 5/5 | 1-2 sentence description |
| `summary` | **LLM** (Planner) | 5/5 | 3-4 sentence status summary (updated by `run_planner()`) |
| `action_items` | **LLM** (Planner) | 5/5 | Remaining tasks |
| `acceptance_criteria` | **LLM** (Planner) | 5/5 | Testable QA criteria |
| `code_summary` | **LLM** | 4/5 | Code context from linked commits |
| `requirements` | **LLM** | 3/5 | Functional requirements |
| `status_ai` | **LLM** | 3/5 | AI-suggested: `active`, `in_progress`, `done` |
| `status_user` | **User** | 4/5 | User-set lifecycle: `active`, `in_progress`, `paused`, `done` |
| `start_date` | User + Trigger | 3/5 | Auto-set when status_user→in_progress; user-editable |
| `tag_id` | **User** | 5/5 | Confirmed link to planner_tag (drag-drop ONLY) |
| `ai_tag_id` | **LLM** | 4/5 | AI-suggested tag (auto-set by `match_work_item_to_tags()`) |
| `tags` JSONB | Trigger | 2/5 | Stats: `{commit_count, interaction_count}` |
| `source_event_id` | Trigger | 2/5 | Source mem_ai_events row (prevents re-extraction) |
| `embedding` VECTOR | Trigger | 4/5 | Semantic work-item search |
| `seq_num` INT | Trigger | 3/5 | Auto-increment display number |
| `merged_into` UUID | **User** | 2/5 | Points to canonical work item after merge |

**LLM prompt**: `work_item_extraction` → `{items: [{category, name, description}]}`
**Input**: Event summary + action_items from unprocessed `mem_ai_events`

**Tag matching pipeline** (auto-run after extract):
1. Exact name match → `ai_tag_id` set at confidence 1.0
2. Vector similarity >0.85 → `ai_tag_id` auto-set
3. Haiku judgment 0.70–0.85 → `ai_tag_id` set if approved
4. `tag_id` **NEVER** auto-set — user drag-drop only

---

### `mem_ai_project_facts` — Durable project facts

**Trigger**: `MemoryPromotion.detect_fact_conflicts()` during feature snapshots
**Responsible**: LLM (extraction + conflict resolution) + User (review of flagged)

| Column | Responsible | Relevance | Notes |
|--------|-------------|-----------|-------|
| `fact_key` | **LLM** | 5/5 | Unique identifier e.g. `primary_database` |
| `fact_value` | **LLM** | 5/5 | Current value e.g. `PostgreSQL 15 + pgvector` |
| `category` | **LLM** | 4/5 | `stack`, `convention`, `constraint`, `client` |
| `valid_from` | Trigger | 2/5 | When fact was set |
| `valid_until` | Trigger | 3/5 | NULL = current; set when superseded |
| `conflict_status` | LLM + **User** | 4/5 | `ok`, `supersede`, `merge`, `flag` |
| `embedding` VECTOR | Trigger | 3/5 | Semantic fact search |

**LLM prompt**: `conflict_detection` → `{resolution: supersede|merge|flag, merged_value, reasoning}`

**Relevance: 4/5** — architectural decisions, constraints, stack choices

---

## Layer 4 — User-Managed Tags (`planner_tags`)

**Responsible**: **User** owns all fields. LLM writes ONLY via explicit "Run Planner" or "Snapshot" button.
**Trigger**: None — no auto-write; only `promote_feature_snapshot()` or `run_planner()` when invoked by user.

| Column | Responsible | Relevance | Notes |
|--------|-------------|-----------|-------|
| `id` UUID | User (create) | — | PK |
| `name` | **User** | 5/5 | Tag name, UNIQUE per project+category |
| `category_id` | **User** | 5/5 | FK to mng_tags_categories: feature/bug/task |
| `status` | **User** | 4/5 | `open`, `active`, `done`, `archived` |
| `priority` SMALLINT | **User** | 3/5 | 1–5 |
| `short_desc` | **User** | 4/5 | 1-line description |
| `full_desc` | **User** | 4/5 | Full description |
| `requirements` | **User** | 5/5 | What the feature must do (user-written) |
| `acceptance_criteria` | **LLM** (Planner) | 5/5 | Written by `run_planner()` |
| `due_date` | **User** | 3/5 | Target completion date |
| `summary` | **LLM** (Planner/Snapshot) | 5/5 | Use case summary — written by `run_planner()` or `promote_feature_snapshot()` |
| `action_items` | **LLM** (Planner/Snapshot) | 5/5 | Remaining work — written by `run_planner()` |
| `design` JSONB | **LLM** (Snapshot) | 4/5 | `{high_level, low_level, patterns_used}` from `feature_snapshot` |
| `code_summary` JSONB | **LLM** (Snapshot) | 4/5 | `{files, key_classes, key_methods}` from `feature_snapshot` |
| `embedding` VECTOR | Trigger | 4/5 | From summary+action_items; used by tag matching |

### LLM prompts that write to planner_tags

| Button | Method | Prompt | Writes |
|--------|--------|--------|--------|
| "Run Planner" | `run_planner()` | `planner_summary` | `summary`, `action_items`, `acceptance_criteria` |
| "Snapshot" | `promote_feature_snapshot()` | `feature_snapshot` | `summary`(=requirements), `action_items`, `design`, `code_summary` |

### What's missing vs. work_items (gap analysis)

| planner_tags has | work_items has | Gap |
|-----------------|----------------|-----|
| `requirements` (user-written) | `requirements` (LLM-extracted) | ✓ Both have it |
| `acceptance_criteria` (LLM) | `acceptance_criteria` (LLM) | ✓ Both have it |
| `summary` (LLM) | `summary` (LLM) | ✓ Both have it |
| `action_items` (LLM) | `action_items` (LLM) | ✓ Both have it |
| `design` JSONB (LLM) | ✗ | planner_tags has richer design context |
| `code_summary` JSONB (LLM) | `code_summary` TEXT (LLM) | planner_tags has structured version |
| ✗ | `start_date` | Work items track when work started |
| ✗ | `status_user` + `status_ai` | Work items track dual lifecycle |
| ✗ | `source_event_id` | Work items trace origin event |
| ✗ | `ai_tag_id` (AI suggestion) | Work items know suggested tag |
| `due_date` | ✗ | planner_tags track deadlines |

---

## Data Flow — Trigger Table

| Event | Trigger | Handler | Target |
|-------|---------|---------|--------|
| AI session prompt | `post_prompt.sh` hook | `POST /memory/{p}/prompts` | mem_mrr_prompts |
| Every ~5 prompts | Auto in route | `process_prompt_batch()` | mem_ai_events (prompt_batch) |
| After prompt batch | Auto (asyncio.ensure_future) | `extract_work_items_from_events()` | mem_ai_work_items |
| Work item created | Auto | `match_work_item_to_tags()` | `ai_tag_id` on work item |
| Git commit | `post_commit.sh` hook | `POST /memory/{p}/commits` | mem_mrr_commits |
| Commit stored | Auto | `process_commit()` | mem_ai_events (commit+diff chunks) |
| Session end | `log_session_stop.sh` hook | `POST /memory/{p}/session-summary` | mem_ai_events (session_summary) |
| Session end | Auto | `write_root_files()` | CLAUDE.md, .cursorrules |
| User clicks "Snapshot" | Manual (UI button) | `promote_feature_snapshot()` | planner_tags (summary, design, code_summary) |
| User clicks "Run Planner" | Manual (UI button) | `run_planner()` | planner_tags + work_items + doc file |
| User drag-drops work item | Manual (UI) | `PATCH /work-items/{id}` | `tag_id` on work item |

---

## All Important Columns — Master Table

| Table | Column | Responsible | Relevance | Used For |
|-------|--------|-------------|-----------|---------|
| mem_mrr_prompts | prompt + response | Trigger | 1/5 | Source data for batch digest |
| mem_mrr_prompts | tags | Trigger | 3/5 | Session/feature/work-item routing |
| mem_mrr_commits | commit_msg | Trigger | 3/5 | What changed |
| mem_mrr_commits | summary | LLM | 4/5 | Back-populated Haiku digest |
| mem_mrr_commits | tags.files | LLM | 4/5 | Which code files changed |
| mem_mrr_commits | tags.symbols | LLM | 4/5 | Which classes/methods changed |
| mem_ai_events | summary | LLM | 4/5 | Core searchable content |
| mem_ai_events | action_items | LLM | 5/5 | Open tasks extracted from session |
| mem_ai_events | importance | LLM | 5/5 | Relevance weight 0-10 |
| mem_ai_events | embedding | Trigger | 5/5 | Semantic search via pgvector |
| mem_ai_events | tags | Trigger+LLM | 3/5 | Event classification + routing |
| mem_ai_work_items | ai_name + ai_desc | LLM | 5/5 | Work item identity |
| mem_ai_work_items | summary | LLM | 5/5 | Status digest |
| mem_ai_work_items | action_items | LLM | 5/5 | What still needs doing |
| mem_ai_work_items | acceptance_criteria | LLM | 5/5 | How to know it's done |
| mem_ai_work_items | status_user | User | 4/5 | User-tracked lifecycle |
| mem_ai_work_items | tag_id | User | 5/5 | Connects to planner_tag (user-set) |
| mem_ai_work_items | ai_tag_id | LLM | 4/5 | AI-suggested planner_tag |
| mem_ai_work_items | start_date | User+Trigger | 3/5 | When work started |
| mem_ai_work_items | code_summary | LLM | 4/5 | Code context from commits |
| mem_ai_project_facts | fact_key + fact_value | LLM | 5/5 | Durable project knowledge |
| mem_ai_project_facts | conflict_status | LLM+User | 4/5 | Data integrity |
| planner_tags | name | User | 5/5 | Tag identity |
| planner_tags | requirements | User | 5/5 | What the feature must do |
| planner_tags | summary | LLM (Planner) | 5/5 | Current state / use-case |
| planner_tags | action_items | LLM (Planner) | 5/5 | Remaining work |
| planner_tags | acceptance_criteria | LLM (Planner) | 5/5 | QA criteria |
| planner_tags | design | LLM (Snapshot) | 4/5 | Architecture details |
| planner_tags | code_summary | LLM (Snapshot) | 4/5 | Structured code reference |

---

## Memory System Prompts (mng_system_roles, category='memory')

All editable from the **Roles** tab. Seeded from `workspace/_templates/memory/prompts.yaml`.

| Prompt | Trigger | Returns | Max tokens |
|--------|---------|---------|-----------|
| `prompt_batch_digest` | Every ~5 prompts | `{summary, action_items, importance}` JSON | 250 |
| `commit_digest` | Commit stored | `{summary, action_items, importance}` JSON | 200 |
| `item_digest` | Item stored | `{summary, action_items, importance}` JSON | 200 |
| `meeting_sections` | Meeting item | `[{title, content}]` JSON array | 1000 |
| `message_chunk_digest` | Message stored | `{summary, action_items, importance}` JSON | 200 |
| `ai_tag_suggestion` | Untagged scan | `{tag, is_new, reasoning}` JSON | — |
| `relation_extraction` | Item embed | `{relations: [{from, relation, to, note}]}` | 400 |
| `session_end_synthesis` | Session end | `{summary, open_threads, next_steps}` JSON | 600 |
| `session_review` | Post-summary | `{score, critique, improved_summary, relations}` | — |
| `memory_synthesis` | `/memory` run | Free-form MEMORY.md digest | — |
| `work_item_promotion` | Work item pipeline | `{summary, status_ai}` JSON | 300 |
| `work_item_extraction` | After prompt batch | `{items: [{category, name, description}]}` JSON | 500 |
| `conflict_detection` | Fact upsert | `{conflict, resolution, merged_value, reasoning}` | 300 |
| `feature_snapshot` | Snapshot trigger | Full JSON: requirements, action_items, design, code_summary, relations | 2500 |
| `planner_summary` | Run Planner button | `{use_case_summary, done_items, remaining_items, acceptance_criteria, work_item_updates}` | 2000 |

---

## Known Issues & Gaps

| Issue | Impact | Status |
|-------|--------|--------|
| 64 stale `#20xxx` bug work items (pre-migration noise) | Low | Dedup needed |
| `promote_feature_snapshot()` reads ALL events, not filtered by feature tag | Medium | Fix: filter by `tags->>'feature'=tag_name` |
| Session-end snapshot not auto-triggered | Medium | Stop hook → session-summary → call promote_feature_snapshot |
| `code_summary` on work items often empty | Medium | Populate from linked commits' `tags.symbols` |
| `mem_mrr_commits.diff_summary` queried in old code | Fixed | Removed from memory_planner.py |
| `source_session_id` referenced in extraction SQL | Fixed | Removed (column dropped in migration 012) |

---

## Quick Reference: Which Table for What

| Question | Table |
|----------|-------|
| All prompts this session | `mem_mrr_prompts` WHERE session_id |
| What code changed in a commit | `mem_mrr_commits.tags["files"]`, `tags["symbols"]` |
| Semantic search across all history | `mem_ai_events` (vector cosine) |
| What is the project tech stack | `mem_ai_project_facts` WHERE category='stack' AND valid_until IS NULL |
| What features are in development | `mem_ai_work_items` WHERE status_user='in_progress' |
| Full context for feature X | `planner_tags` WHERE name=X + `mem_ai_work_items` WHERE tag_id=X.id |
| AI-suggested tag for a work item | `mem_ai_work_items.ai_tag_id` |
| All tags and hierarchy | `planner_tags` |
| Recent high-importance events | `mem_ai_events` ORDER BY importance×exp(-0.01×age) DESC |
