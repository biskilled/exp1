# aicli — Memory & Tagging Architecture

_Last updated: 2026-04-01 | Full rewrite — covers all 5 layers, tagging flows, Planner UI, issues, and refactoring advice_

---

## 0. Mental Model

aicli memory has **5 layers** stacked on top of each other.
**Tagging is a separate, orthogonal system** that cuts across all layers to connect everything.

```
 ┌──────────────────────────────────────────────────────────────────────┐
 │ Layer 0 — Ephemeral         In-session message list (RAM / JSON)     │
 │ Layer 1 — Raw Capture       Everything stored as-is   (mem_mrr_*)    │
 │ Layer 2 — AI Events         Digested + embedded        (mem_ai_events)│
 │ Layer 3 — Structured        Facts / Work Items / Snapshots           │
 │ Layer 4 — Context Files     CLAUDE.md, .cursorrules, llm_prompts/    │
 └──────────────────────────────────────────────────────────────────────┘

 ┌──────────────────────────────────────────────────────────────────────┐
 │ Tagging (orthogonal)        planner_tags + mem_mrr_tags + mem_ai_tags│
 └──────────────────────────────────────────────────────────────────────┘
```

---

## Layer 0 — Ephemeral (Session Messages)

**What it is**: The live `messages[]` array forwarded to the LLM on every turn.

**Storage**: `workspace/{project}/_system/sessions/{session_id}.json`
**Python class**: `SessionStore` (`backend/memory/mem_sessions.py`)
**NOT stored in PostgreSQL** — file-only, short-lived.

**Schema (per JSON file)**:
```json
{
  "id": "uuid",
  "created_at": "iso",
  "updated_at": "iso",
  "messages": [
    { "role": "user|assistant", "content": "...", "ts": "iso" }
  ],
  "metadata": { "phase": "...", "feature": "...", "bug_ref": "..." }
}
```

**Trigger**: Every API request that calls `SessionStore.append_message()`.

**Purpose**: Maintain conversation continuity within a session. Has nothing to do with the DB pipeline.

---

## Layer 1 — Raw Capture (`mem_mrr_*`)

**What it is**: Everything stored exactly as received. No AI processing. Acts as the source-of-truth audit trail.

### Tables

| Table | PK | Key columns | Written by |
|-------|----|-------------|-----------|
| `mem_mrr_prompts` | `id UUID` | project, session_id, prompt TEXT (≤4000), response TEXT (≤8000), source_id, llm_source, phase, ai_tags, work_item_id FK→mem_ai_work_items | `log_user_prompt.sh` hook → `POST /chat/{p}/hook-log` |
| `mem_mrr_commits` | `commit_hash VARCHAR(64)` | project, commit_msg, diff_summary, diff_details JSONB, session_id, phase, feature, bug_ref, ai_tags, committed_at | `auto_commit_push.sh` hook → `POST /git/{p}/commit-push` |
| `mem_mrr_items` | `id UUID` | project, item_type ('requirement'/'decision'/'meeting'), title, raw_text, summary, meeting_at, attendees TEXT[], ai_tags | Item ingest API (`POST /history/items`) |
| `mem_mrr_messages` | `id UUID` | project, platform ('slack'/'teams'/'discord'), channel, thread_ref, messages JSONB, date_range TSTZRANGE, ai_tags | Platform connector API |

**The `ai_tags` lifecycle** (on all 4 tables):
```
NULL          → row arrived, not yet processed by AI tagging pipeline
'approved'    → AI suggested a tag, user accepted it
'ignored'     → AI suggested a tag, user rejected it
```

**Python class**: `MemoryMirroring` (`backend/memory/memory_mirroring.py`)
Key methods: `store_prompt()`, `store_commit()`, `store_item()`, `store_message()`, `get_untagged()`, `set_ai_tag_status()`

**Idempotent**: All inserts use ON CONFLICT patterns — safe to replay.

---

## Layer 2 — AI Events (`mem_ai_events`)

**What it is**: Every Layer 1 source gets digested by Haiku and embedded into a 1536-dim vector. This is the primary semantic search target.

### Table: `mem_ai_events`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| client_id | INT | |
| project | VARCHAR | |
| event_type | TEXT | `'prompt_batch'` \| `'commit'` \| `'item'` \| `'message'` \| `'session_summary'` \| `'workflow'` |
| source_id | TEXT | UUID, commit hash, or session_id depending on event_type |
| session_id | TEXT | Session that produced this event |
| llm_source | VARCHAR(100) | Model that created the digest (e.g. `claude-haiku-4-5-20251001`) |
| chunk | INT | 0 = full; >0 = multi-part (large docs/commits split into sections) |
| chunk_type | TEXT | `'full'` \| `'section'` \| `'function'` \| `'diff_file'` |
| content | TEXT | The actual text passed to the embedder |
| **embedding** | VECTOR(1536) | pgvector — cosine similarity search |
| summary | TEXT | Haiku digest (1–2 sentences) |
| open_threads | TEXT | session_summary only — unresolved items |
| next_steps | TEXT | session_summary only — what to do next |
| doc_type | TEXT | item only: `'requirement'` \| `'decision'` \| `'meeting'` |
| language | TEXT | code chunk only: `'python'` \| `'javascript'` \| etc. |
| file_path | TEXT | code/commit chunk source |
| metadata | JSONB | arbitrary extras |
| importance | SMALLINT | 1 (default) — 2 for session_summaries; used in relevance scoring |
| processed_at | TIMESTAMPTZ | When last used for feature snapshot |
| created_at | TIMESTAMPTZ | |

**UNIQUE** on `(client_id, project, event_type, source_id, chunk)` — prevents duplicate embeddings.

**Python class**: `MemoryEmbedding` (`backend/memory/memory_embedding.py`)

### How Each event_type is Produced

#### `prompt_batch`
- **Trigger**: After every `batch_size` prompts in a session (counted via `MemoryMirroring.count_session_prompts()`), OR when `/memory` is run manually.
- **Source**: Last N rows from `mem_mrr_prompts` for the session.
- **AI prompt**: `prompt_batch_digest` (Haiku, ≤200 tokens) → 1–2 sentence digest.
- **Embedding**: `text-embedding-3-small(content + summary)` → VECTOR(1536).
- **Side effect**: Calls `MemoryTagging.promote_source_tags_to_event()` → copies tags from `mem_mrr_tags` rows for those prompt_ids into `mem_ai_tags`.

#### `commit`
- **Trigger**: Manual call or workflow trigger. NOT auto-triggered on commit arrival — commit embedding must be explicitly requested.
- **Source**: One `mem_mrr_commits` row.
- **AI prompt**: `commit_digest` (Haiku, ≤150 tokens) → 1 sentence.
- **Smart chunking**: `smart_chunk_diff()` — creates one summary chunk + one chunk per changed file.
- **Side effect**: `promote_source_tags_to_event()` for this commit's `mem_mrr_tags` rows.

#### `item`
- **Trigger**: After `store_item()` + explicit call to `process_item()`.
- **Source**: One `mem_mrr_items` row.
- **AI prompts**:
  - `meeting_sections` → splits large text into JSON array of sections.
  - `item_digest` (Haiku, ≤150 tokens) → per-section summary.
  - `relation_extraction` (Haiku, ≤400 tokens) → detect tag relationships → upsert `mem_ai_tags_relations`.
- **Smart chunking**: `smart_chunk_markdown()` — splits by H2/H3, ≤3000 chars/chunk.

#### `message`
- **Trigger**: After `store_message()` + explicit call to `process_messages()`.
- **AI prompt**: `message_chunk_digest` (Haiku, ≤150 tokens).

#### `session_summary`
- **Trigger**: `POST /memory/{project}/session-summary` — called by `log_session_stop.sh` hook at end of every session.
- **Source**: Last 20 prompt/response pairs from `mem_mrr_prompts` for the session.
- **AI prompt**: `session_end_synthesis` (Haiku, ≤600 tokens) → JSON `{summary, open_threads, next_steps}`.
- **Stored**: `mem_ai_events` with `event_type='session_summary'`, `importance=2`.
- **Side effect**: Background task → `MemoryFiles.write_root_files()` (regenerates CLAUDE.md etc.)

#### `workflow`
- **Trigger**: After a 4-agent pipeline run completes.
- **Source**: Concatenated node outputs.
- **AI prompt**: None — raw workflow output embedded directly.

### Relevance Scoring
Used for ranking events in context injection:
```
score = importance × exp(-0.01 × age_days)
```
Foundational facts get a 50% floor. Time-decay ensures recent events surface first.

---

## Layer 3 — Structured Artifacts (`mem_ai_work_items`, `mem_ai_project_facts`, `mem_ai_features`)

**What it is**: Higher-level, structured knowledge extracted from Layer 2. All three tables have `VECTOR(1536)` for semantic search.

### `mem_ai_work_items` — Features, Bugs, Tasks

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| client_id | INT | |
| project | VARCHAR | |
| category_name | TEXT | `'feature'` \| `'bug'` \| `'task'` |
| name | TEXT | Item title |
| description | TEXT | Detailed description |
| status | VARCHAR(20) | `'active'` \| `'prereq'` \| `'done'` \| `'archived'` |
| lifecycle_status | VARCHAR(20) | `'idea'` → `'design'` → `'development'` → `'testing'` → `'review'` → `'done'` |
| acceptance_criteria | TEXT | Criteria the item must satisfy |
| implementation_plan | TEXT | Step-by-step plan |
| tag_id | UUID FK→planner_tags | Optional link to a planner_tag |
| **embedding** | VECTOR(1536) | Populated on create/patch |
| agent_run_id | UUID | Last pipeline run ID |
| agent_status | VARCHAR(20) | `'running'` \| `'done'` \| `'error'` |
| seq_num | INT | Sequential ID within (project, category_name) |
| parent_id | UUID FK→self | Hierarchical work items |
| due_date | DATE | |

**How work items are created**:
- **Manual** via UI: `POST /work-items` → `route_work_items.py` → inserts into `mem_ai_work_items`.
- **Pipeline agents** (`tool_workitems.py`): `create_work_item()` → creates `planner_tags` entry first, then `mem_ai_work_items`.
- **NOT auto-created** from prompts/commits — always requires explicit creation.

**How embedding is populated**:
- `_embed_work_item()` called in background after `create_work_item()` or `patch_work_item()` when `name`/`description`/`acceptance_criteria` change.
- Content: `name + '\n' + description + '\n' + acceptance_criteria`

**Semantic search**: `GET /work-items/search?query=...` → cosine similarity on `embedding`.

**Pipeline trigger**: `POST /work-items/{id}/run-pipeline` → starts 4-agent PM→Architect→Developer→Reviewer DAG.

---

### `mem_ai_project_facts` — Durable Extracted Facts

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| client_id, project | | |
| fact_key | TEXT | e.g. `'primary_database'`, `'auth_method'` |
| fact_value | TEXT | e.g. `'PostgreSQL 15 + pgvector'`, `'JWT with bcrypt'` |
| category | TEXT | `'stack'` \| `'pattern'` \| `'convention'` \| `'constraint'` \| `'client'` |
| **embedding** | VECTOR(1536) | Populated on insert |
| valid_from | TIMESTAMPTZ | When fact became true |
| valid_until | TIMESTAMPTZ | NULL = currently valid; set when superseded |
| source_memory_id | UUID | Which `mem_ai_events` row produced this fact |
| conflict_status | TEXT | `'ok'` \| `'superseded'` \| `'pending_review'` |

**UNIQUE** on `(client_id, project, fact_key)` WHERE `valid_until IS NULL` — only one current value per key.

**How facts are created**:
- Extracted during `/memory` regeneration via `internal_project_fact` Haiku prompt.
- Read from `mem_ai_events` → find factual statements → temporal upsert with conflict detection.

**Conflict detection**: `MemoryPromotion.detect_fact_conflicts()` — calls Haiku with `conflict_detection` prompt when a new value contradicts an existing active fact → resolves as `supersede` / `merge` / `flag`.

---

### `mem_ai_features` — 4-Layer Feature Snapshots

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| client_id, project | | |
| tag_id | UUID FK→planner_tags | The feature/bug this snapshot is for |
| requirements | TEXT | What the feature must do |
| action_items | TEXT | Open tasks and next steps |
| design | JSONB | `{high_level, low_level, patterns_used}` |
| code_summary | JSONB | `{files, key_classes, key_methods, dependencies_added, dependencies_removed}` |
| file_paths | TEXT[] | Source files involved |
| **embedding** | VECTOR(1536) | Embed of requirements + action_items |
| work_item_status | TEXT | lifecycle_status at snapshot time |

**UNIQUE** on `(client_id, project, tag_id)` — one snapshot per tag per project.

**How snapshots are created**:
1. `MemoryPromotion.promote_feature_snapshot(project, tag_name)` called.
2. Loads all `mem_ai_events` linked to this tag via `mem_ai_tags`.
3. Groups into 6 buckets: prompt_batch, commit, item, message, session_summary, workflow.
4. Calls Haiku with `feature_snapshot` prompt (≤2500 tokens) → returns JSON.
5. Upserts `mem_ai_features` (ON CONFLICT tag_id DO UPDATE).
6. Embeds `requirements + action_items` → VECTOR.
7. AI-detected relations → upsert `mem_ai_tags_relations` (source=`'ai_snapshot'`).
8. Marks contributing `mem_ai_events.processed_at = NOW()`.

**Trigger**: Manually via `POST /projects/{p}/snapshot/{tag}`, or when a work item lifecycle reaches `'done'`.

---

## Layer 4 — Context Files (Filesystem)

**What it is**: Deterministic template renders from the DB. **No LLM calls** in this layer. Written by `MemoryFiles` (`backend/memory/memory_files.py`).

### Files Written by `write_root_files()`

| File | Path | Read by |
|------|------|---------|
| `CLAUDE.md` | `{code_dir}/CLAUDE.md` | Claude Code (auto-loaded at session start) |
| `.cursorrules` | `{code_dir}/.cursorrules` | Cursor (auto-loaded) — ≤2000 tokens |
| `top_events.md` | `{code_dir}/.claude/memory/top_events.md` | Injected per-session by Claude Code |
| `full.md` | `{sys_dir}/llm_prompts/full.md` | Claude / Deepseek / Gemini |
| `compact.md` | `{sys_dir}/llm_prompts/compact.md` | GPT-4 / small-context models |
| `gemini_context.md` | `{sys_dir}/llm_prompts/gemini_context.md` | Gemini Files API |

### Per-Feature Files (from `write_feature_files(tag_name)`)

| File | Path |
|------|------|
| `features/{tag}/CLAUDE.md` | `{code_dir}/features/{tag}/CLAUDE.md` (auto-loaded by Claude Code when working in that directory) |

### What Each File Contains (from DB)

**CLAUDE.md / full.md**: Tech stack facts → active work items (by lifecycle) → blockers → depends_on links → last session summary → open threads → conventions → constraints → client requirements.

**compact.md / .cursorrules**: Tech stack + patterns + conventions only (≤2000 tokens).

**top_events.md**: Top-5 `mem_ai_events` ranked by `importance × exp(-0.01 × age_days)`.

### Triggers for `write_root_files()`

| Trigger | Code path |
|---------|-----------|
| Session end | `log_session_stop.sh` → `POST /memory/{p}/session-summary` → background task |
| Work item create/patch | `route_work_items.py` → background task |
| Tag relation create | `route_tags.py` → background task |
| Manual `/memory` command | MCP tool `commit_push` or `POST /projects/{p}/memory` → `POST /memory/{p}/regenerate` |
| New session start | `check_session_context.sh` hook |

---

## Tagging System (Orthogonal Infrastructure)

The tagging system connects all layers to a **project knowledge graph** (planner_tags hierarchy). It has three separate junction tables for three different purposes.

### Core Tag Registry

```
mng_tags_categories   ← global vocabulary (feature/bug/task/design/decision/meeting/ai_suggestion)
      ↓ category_id
planner_tags          ← per-project tag instances (the actual "auth-refactor" bug, "retry-dashboard" feature)
      ↓ tag_id (UUID)
  mem_mrr_tags        ← links tag → raw sources (Layer 1)
  mem_ai_tags         ← links tag → AI events (Layer 2)
  mem_ai_features     ← one snapshot per tag (Layer 3)
  mem_ai_work_items   ← work item optionally linked to a tag (Layer 3)
```

### `planner_tags` — The Tag Registry

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| client_id | INT | |
| project | VARCHAR | |
| name | TEXT | e.g. `'retry-dashboard'`, `'auth-refactor'` |
| category_id | INT FK→mng_tags_categories | feature / bug / task / ai_suggestion / etc. |
| parent_id | UUID FK→self | Hierarchical nesting |
| merged_into | UUID FK→self | If merged, the canonical surviving tag |
| status | VARCHAR(20) | `'active'` \| `'archived'` |
| ~~lifecycle~~ | VARCHAR(20) | **⚠ REMOVABLE** — superseded by `mem_ai_work_items.lifecycle_status`; UI no longer shows it |
| seq_num | INT | Sequential ID — allocated from `pr_seq_counters` |

### `planner_tags_meta` — Extended Metadata (1:1 with planner_tags)

| Column | Notes |
|--------|-------|
| description TEXT | Long description; also stores `[suggested: X]` prefix for AI-auto-created tags |
| requirements TEXT | Acceptance criteria for the tag |
| due_date DATE | |
| requester TEXT | |
| priority SMALLINT (1–5) | |
| extra JSONB | |

### `mem_mrr_tags` — Layer 1 Junction (Tag → Raw Sources)

Links a tag to raw source data. Uses a **wide junction** design: one row per (tag, source) with many nullable FK columns.

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tag_id | UUID FK→planner_tags | The tag |
| session_id | TEXT | Session context when tag was applied |
| prompt_id | UUID FK→mem_mrr_prompts | Set when tagging a prompt |
| commit_id | TEXT FK→mem_mrr_commits(commit_hash) | Set when tagging a commit |
| item_id | UUID FK→mem_mrr_items | Set when tagging a document |
| message_id | UUID FK→mem_mrr_messages | Set when tagging a message |
| work_item_id | UUID FK→mem_ai_work_items | Set when tagging a work item |
| auto_tagged | BOOL | True = AI applied tag; False = user applied |
| event_id, snapshot_id, fact_id | UUID (no FK) | ⚠ **UNUSED** — nullable, no FK constraint; planned but not implemented |

**Unique partial indexes** prevent duplicates per source type: `UNIQUE(tag_id, prompt_id) WHERE prompt_id IS NOT NULL`, etc.

**How rows are created**:
- Hook `log_user_prompt.sh` via `_tag_prompt_from_context()` (session context tags → auto_tagged=True)
- Manual `POST /tags/source` from UI
- AI suggestion applied via `MemoryTagging.apply_suggestion(layer='mrr')`

### `mem_ai_tags` — Layer 2 Junction (Tag → AI Events)

| Column | Notes |
|--------|-------|
| event_id UUID FK→mem_ai_events | The AI event |
| tag_id UUID FK→planner_tags | The tag |
| ai_suggested BOOL | Was this connection proposed by AI? |

**How rows are created**:
- `MemoryTagging.promote_source_tags_to_event()` — called by every `MemoryEmbedding.process_*()` method: copies distinct tag_ids from `mem_mrr_tags` source rows into `mem_ai_tags` for the newly created event.
- `MemoryTagging.link_to_event(event_id, tag_id)` — direct link.
- AI suggestion applied via `apply_suggestion(layer='ai')`.

### `mem_ai_tags_relations` — Tag Relationship Graph

| Column | Notes |
|--------|-------|
| from_tag_id UUID FK→planner_tags | |
| relation TEXT | `'part_of'` \| `'depends_on'` \| `'blocks'` \| `'relates_to'` \| `'implements'` \| `'replaces'` |
| to_tag_id UUID FK→planner_tags | |
| note TEXT | Explanation |
| source VARCHAR(20) | `'manual'` \| `'ai_snapshot'` \| `'ai_extracted'` |

**⚠ No project column** — relation is between tag UUIDs which are project-scoped, so this is correct. But the name `mng_ai_tags_relations` in some places vs `mem_ai_tags_relations` in others is inconsistent — pick one.

---

## AI Tag Suggestion Workflow

How the AI suggests which tags to apply to unprocessed rows:

```
1. MemoryTagging.suggest_tags_for_untagged(project, batch_size=20)
     ↓
2. Scan mem_mrr_prompts/commits/items/messages WHERE ai_tags IS NULL
   + scan mem_ai_events with no mem_ai_tags entries
     ↓
3. For each row: call Haiku with 'ai_tag_suggestion' prompt
     Input: content snippet + existing tag names list
     Output: { "tag": "retry-dashboard", "is_new": false, "reasoning": "..." }
     ↓
4. Return suggestions to UI as { source_type, source_id, suggested_tag, is_new, reasoning }
     ↓
5. User approves:  MemoryTagging.apply_suggestion()
     → get_or_create_tag(project, tag_name)
     → link_to_mirroring() / link_to_event()
     → set_ai_tag_status(source_type, source_id, 'approved')
     ↓
6. User ignores:  ignore_suggestion()
     → set_ai_tag_status(source_type, source_id, 'ignored')
```

---

## Planner UI — Data Sources

The Planner tab shows data from **two different tables** depending on which category is selected. This is a known source of confusion (see Issues section).

### Left Pane (Categories)

| What | Table | API |
|------|-------|-----|
| Category list | `mng_tags_categories` | `GET /entities/categories?project=X` |
| Category counter | `planner_tags` count per category | Embedded in category list response |

### Right Pane — Regular Tag Categories (ai_suggestion, design, decision, etc.)

| What | Table | API |
|------|-------|-----|
| Tag tree (roots + children) | `planner_tags` + `planner_tags_meta` | `GET /entities/values?project=X&category_id=N` |
| Tag counter | Live from `tagCache` (`getCacheValues(catId).length`) | Client-side cache |
| Tag status badge | `planner_tags.status` | |
| Drawer details | `planner_tags` + `planner_tags_meta` + `mem_mrr_tags` sources | `GET /tags/{id}/sources` |
| Drawer links | `mem_ai_tags_relations` | `GET /entities/values/{id}/links` |
| AI tag suggestions | `mem_mrr_prompts` + `mem_ai_events` (ai_tags IS NULL or no mem_ai_tags entry) | `POST /tags/suggestions/generate` |

### Right Pane — Work Item Categories (feature, bug, task)

| What | Table | API |
|------|-------|-----|
| Work item tree | `mem_ai_work_items` | `GET /work-items?project=X&category=bug` |
| Status, lifecycle | `mem_ai_work_items.status`, `.lifecycle_status` | |
| Acceptance criteria | `mem_ai_work_items.acceptance_criteria` | |
| Agent status badge | `mem_ai_work_items.agent_status` | |
| Drawer: description, AC, impl_plan | `mem_ai_work_items` | `GET /work-items?project=X&category=bug` (full item) |
| Pipeline run | `pr_graph_runs` | `POST /work-items/{id}/run-pipeline` |

### How Planner Updates

| Event | What updates |
|-------|-------------|
| User creates tag | `POST /entities/values` → `planner_tags` → `addCachedValue()` (instant client-side) |
| User renames/moves tag | `PATCH /tags/{id}` → `planner_tags` → `updateCachedValue()` |
| DnD merge | `POST /tags/merge` → archives `planner_tags.merged_into`; remaps `mem_mrr_tags` + `mem_ai_tags` |
| DnD reparent | `PATCH /tags/{id}` with `{parent_id: ...}` → `planner_tags.parent_id` |
| DnD re-categorize (ai_suggestion → other) | `PATCH /tags/{id}` with `{category_id: ...}` → `planner_tags.category_id` |
| AI sync button (↻ Sync) | `POST /entities/sync-events?project=X` → imports new prompts/commits + runs `_auto_create_entities()` |
| `⇢ Fix AI tags` button | `POST /tags/migrate-to-ai-suggestions?project=X` → moves 0-event planner_tags from feature/bug/task to ai_suggestion |

---

## Full Data Flow (End-to-End)

```
USER TYPES A PROMPT
  ↓
check_session_context.sh (UserPromptSubmit hook)
  → Reads .agent-context file → ensures session tags exist
  → Writes workspace/{p}/_system/.agent-context if missing
  ↓
log_user_prompt.sh (UserPromptSubmit hook)
  → POST /chat/{p}/hook-log
      → mem_mrr_prompts INSERT (ai_tags=NULL)
      → count_session_prompts(session_id)
      → if count % batch_size == 0:
          MemoryEmbedding.process_prompt_batch()
            → Haiku digest → OpenAI embed
            → mem_ai_events INSERT (event_type='prompt_batch')
            → promote_source_tags_to_event()
              → mem_mrr_tags → mem_ai_tags (copy tags)
      → if context_tags in hook payload:
          _tag_prompt_from_context() → mem_mrr_tags INSERT (auto_tagged=True)

SESSION ENDS
  ↓
log_session_stop.sh (Stop hook)
  → POST /chat/{p}/hook-response → updates mem_mrr_prompts.response
  → POST /memory/{p}/session-summary
      → Haiku session_end_synthesis → JSON {summary, open_threads, next_steps}
      → mem_ai_events INSERT (event_type='session_summary', importance=2)
      → background: MemoryFiles.write_root_files()
          → reads: mem_ai_project_facts, mem_ai_work_items, mem_ai_events (top-N),
                   planner_tags (blockers), mem_ai_tags_relations
          → writes: CLAUDE.md, .cursorrules, top_events.md, llm_prompts/*.md

GIT COMMIT
  ↓
auto_commit_push.sh (Stop hook)
  → POST /git/{p}/commit-push
      → mem_mrr_commits INSERT
      → (commit embedding requires explicit trigger — not automatic)

USER RUNS /memory
  ↓
MCP tool commit_push → POST /projects/{p}/memory → POST /memory/{p}/regenerate
  → MemoryEmbedding.process_prompt_batch() (catch up any unbatched prompts)
  → _extract_project_facts() → Haiku internal_project_fact prompt
      → temporal upsert → mem_ai_project_facts
      → _embed_project_facts() → embedding VECTOR
  → MemoryFiles.write_all_files() → all output files regenerated

WORK ITEM PIPELINE
  ↓
User clicks ▶ in Planner → POST /work-items/{id}/run-pipeline
  → pr_graph_runs INSERT
  → PM agent: get_tag_context() + get_project_facts() + search_memory()
      → writes acceptance_criteria to mem_ai_work_items
  → Architect agent: search_features() + read_file()
      → writes implementation_plan to mem_ai_work_items
  → Developer agent: read_file() + write_file() + git_commit()
  → Reviewer agent: git_diff() + search_memory()
      → sets agent_status = 'done' | 'error'
  → background: MemoryFiles.write_root_files()
```

---

## Issues, Duplicates, and Refactoring Advice

### Issue 1 — Two Tables for "Features/Bugs/Tasks" ⚠ MAJOR CONFUSION

**Problem**: There are two parallel systems for tracking features/bugs/tasks:

| System | Table | Has embedding | Has pipeline | Has hierarchy | UI shows |
|--------|-------|---------------|--------------|---------------|----------|
| Tag system | `planner_tags` (category=feature/bug/task) | No | No | Yes (parent_id) | When AI Suggestions or custom categories selected |
| Work item system | `mem_ai_work_items` (category_name=feature/bug/task) | Yes | Yes | Yes (parent_id) | When feature/bug/task category selected |

**Root cause**: `planner_tags` was the original system. `mem_ai_work_items` was added for richer pipeline support. The UI now conditionally shows different tables depending on which category is clicked. `planner_tags` with category=feature/bug/task are now orphaned in terms of UI visibility (they show in counters but the table shows work items).

**Recommendation**: Decide one of two directions:
- **Option A (Clean separation)**: Remove feature/bug/task from `mng_tags_categories`. Work items are always in `mem_ai_work_items`. Regular tags only use custom categories + ai_suggestion. Counter on left pane reads from `mem_ai_work_items` for feature/bug/task.
- **Option B (Unified)**: Make `mem_ai_work_items.tag_id` mandatory (not nullable). Every work item MUST have a corresponding `planner_tags` entry. The planner_tags entry is the registry ID; mem_ai_work_items is the detail. Counter always reads from `mem_ai_work_items` for these categories.

Option B is cleaner architecturally but requires a migration.

---

### Issue 2 — `route_entities.py` is a Legacy Wrapper ⚠ TECH DEBT

**Problem**: `route_entities.py` and `route_tags.py` both manage planner_tags. The frontend `tagCache.js` uses the entities API (`/entities/values`, `/entities/categories`) for loading. This means two routers for the same data.

**Recommendation**: Consolidate. Replace entities API calls in `tagCache.js` with the tags API calls. Then delete `route_entities.py`. This is a medium-sized but safe refactor.

---

### Issue 3 — `mem_mrr_tags` Wide Junction Has Dead Columns ⚠ SCHEMA BLOAT

**Problem**: `mem_mrr_tags` has these columns with no FK constraint and no known usage:
- `event_id`, `event_created`, `event_updated` (not FK to mem_ai_events)
- `snapshot_id`, `snapshot_created`, `snapshot_updated` (no FK)
- `fact_id`, `fact_created`, `fact_updated` (no FK)

These were planned but never implemented. Every row has 9 NULL columns.

**Recommendation**: Drop `event_id`, `snapshot_id`, `fact_id` and their associated `*_created`/`*_updated` columns. The link from tags to AI events is handled by `mem_ai_tags` — there is no need for a second path.

---

### Issue 4 — `planner_tags.lifecycle` Column is Dead

**Problem**: The `lifecycle` column exists in `planner_tags` but has been removed from all UI views. `mem_ai_work_items.lifecycle_status` is the correct location for lifecycle tracking.

**Recommendation**: Run `ALTER TABLE planner_tags DROP COLUMN lifecycle;`

---

### Issue 5 — `mem_ai_tags_relations` Table Name Inconsistency

**Problem**: The table is sometimes referenced as `mng_ai_tags_relations` (in some route code) and `mem_ai_tags_relations` (in database.py). This causes FK errors if the table name doesn't match.

**Recommendation**: Standardize on `mem_ai_tags_relations` (the `mem_` prefix fits — it's AI-generated relationship data, not a global config table).

---

### Issue 6 — `mem_ai_work_items.tag_id` is Inconsistently Used

**Problem**: `tag_id` FK on `mem_ai_work_items` is nullable and not always populated. When set, it links the work item to a *specific* planner_tag (e.g., "auth-refactor"), not the category. But many work items have no tag_id set, making the link unreliable for queries.

**Recommendation**: Either enforce NOT NULL (require a planner_tag for every work item) or drop the column and rely on `category_name` + `name` for identification.

---

### Issue 7 — `seq_num` on Both `planner_tags` and `mem_ai_work_items`

**Problem**: For feature/bug/task categories, both tables allocate a `seq_num` for the same conceptual item, resulting in two different sequence numbers for the same item.

**Recommendation**: If Option A or B from Issue 1 is implemented, standardize on `mem_ai_work_items.seq_num` for work items. Remove `planner_tags.seq_num` from feature/bug/task categories, or only use it for ai_suggestion/custom categories.

---

### Issue 8 — Missing `created_by` Audit Column

**Problem**: `planner_tags` has no `created_by` column. There is no way to distinguish user-created tags from AI-auto-created tags (the `_auto_create_entities()` function now uses `ai_suggestion` category + description prefix as a workaround).

**Recommendation**: Add `created_by VARCHAR(20) NOT NULL DEFAULT 'user'` — values: `'user'` | `'ai_auto'` | `'pipeline'`. This makes the `⇢ Fix AI tags` migration unnecessary.

---

### Removable Columns Summary

| Table | Column(s) | Reason |
|-------|-----------|--------|
| `planner_tags` | `lifecycle` | Dead — UI removed; `mem_ai_work_items.lifecycle_status` is the canonical field |
| `mem_mrr_tags` | `event_id`, `event_created`, `event_updated` | No FK, never written, purpose covered by `mem_ai_tags` |
| `mem_mrr_tags` | `snapshot_id`, `snapshot_created`, `snapshot_updated` | No FK, never written |
| `mem_mrr_tags` | `fact_id`, `fact_created`, `fact_updated` | No FK, never written |

### Missing Columns Summary

| Table | Column | Why Needed |
|-------|--------|-----------|
| `planner_tags` | `created_by VARCHAR(20)` | Distinguish user vs AI-auto-created tags without heuristics |
| `mem_mrr_prompts` | `source` (rename `llm_source`?) | Distinguish Claude CLI vs UI vs cursor vs webhook prompts more clearly |
| `mem_ai_events` | No action needed | Table is complete |
| `mem_ai_work_items` | `created_by VARCHAR(20)` | Know if work item was user-created or pipeline-created |

---

## Memory System Prompts (15 — in `mng_system_roles`)

All editable from the **Roles** tab in the UI (category = `'memory'`). Seeded from `workspace/_templates/memory/prompts.yaml`.

| Prompt name | Trigger | Goal | Max tokens |
|-------------|---------|------|-----------|
| `prompt_batch_digest` | Every N prompts | 1–2 sentence digest of Q/A batch | 200 |
| `commit_digest` | Commit embed | 1 sentence commit summary | 150 |
| `item_digest` | Per section | Section summary for documents/meetings | 150 |
| `meeting_sections` | Meeting item ingest | Split meeting transcript into JSON sections array | 1000 |
| `message_chunk_digest` | Message embed | Thread summary | 150 |
| `ai_tag_suggestion` | Untagged row scan | Suggest best tag: `{tag, is_new, reasoning}` | — |
| `relation_extraction` | Item embed | Detect tag relationships: `[{from, relation, to, note}]` | 400 |
| `session_end_synthesis` | Session end | Wrap session: `{summary, open_threads, next_steps}` | 600 |
| `session_review` | After session_summary | Quality gate on summary | — |
| `memory_synthesis` | `/memory` run | Synthesise overall project context | — |
| `work_item_promotion` | Work item pipeline | 2–4 sentence digest: `{summary, status}` | 300 |
| `conflict_detection` | Fact upsert | Resolve old vs new fact: `{conflict, resolution, merged_value}` | 300 |
| `feature_snapshot` | Snapshot trigger | 4-layer snapshot JSON (requirements, action_items, design, code_summary, relations) | 2500 |
| `internal_project_fact` | `/memory` run | Extract facts from events: `[{key, value, category, confidence}]` | — |
| + legacy aliases | (4) | Backward compatibility only | — |

---

## Quick Reference: Which Table for What

| Question | Table |
|----------|-------|
| "Show me all prompts this session" | `mem_mrr_prompts` WHERE session_id |
| "What commits reference feature X" | `mem_mrr_commits` JOIN `mem_mrr_tags` WHERE tag.name = X |
| "Semantic search across all history" | `mem_ai_events` (vector cosine) |
| "What is the project tech stack" | `mem_ai_project_facts` WHERE category='stack' AND valid_until IS NULL |
| "What features are in development" | `mem_ai_work_items` WHERE lifecycle_status='development' |
| "Full context for feature X" | `mem_ai_features` WHERE tag_id = X.id |
| "All tags and their hierarchy" | `planner_tags` + `planner_tags_meta` (LEFT JOIN) |
| "What sources are tagged with X" | `mem_mrr_tags` WHERE tag_id = X.id |
| "What AI events are tagged with X" | `mem_ai_tags` WHERE tag_id = X.id |
| "Dependencies between features" | `mem_ai_tags_relations` WHERE relation='depends_on' |
| "Active session phase/feature" | `mng_session_tags` WHERE project |
