# aicli — Memory & Tagging Architecture

_Last updated: 2026-04-08 | Reflects migration 016, mem_mrr_commits_code, file-based prompt system_

---

## 0. Mental Model

aicli memory is a **4-layer pipeline**. Data flows **down**: every raw event eventually becomes
a structured work item. `planner_tags` sits above as the user-managed project view.

```
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │ Layer 0 — Ephemeral     In-session message list (RAM / JSON file)            │
 │                                                                              │
 │ Layer 1 — Raw Capture   Everything stored verbatim         (mem_mrr_*)       │
 │                         ├─ mem_mrr_prompts                                   │
 │                         ├─ mem_mrr_commits  + mem_mrr_commits_code (new)     │
 │                         ├─ mem_mrr_items                                     │
 │                         └─ mem_mrr_messages                                  │
 │                                                                              │
 │ Layer 2 — AI Events     Digested + embedded                (mem_ai_events)   │
 │                                                                              │
 │ Layer 3 — Structured    AI-detected artifacts              (mem_ai_*)        │
 │                         ├─ mem_ai_work_items                                 │
 │                         └─ mem_ai_project_facts                              │
 │                                                                              │
 │ Layer 4 — User Tags     planner_tags   ← USER OWNS THIS                     │
 └──────────────────────────────────────────────────────────────────────────────┘
```

**Ownership boundary**:

| Layer | Owner | Rule |
|-------|-------|------|
| 0–3 | LLM + Triggers | Fully automatic. User does not manually edit. |
| 4 | **User** | User creates/edits tags. LLM writes ONLY on explicit button click. |
| `work_items.tag_id` | **User** | Drag-drop only. `ai_tag_id` = LLM suggestion (auto). |

**Phase goal**: AI manages all data through Layer 3 (`mem_ai_work_items`). User manages Layer 4
(`planner_tags`). Future: merge both via `tag_id` linkage.

---

## Layer 0 — Ephemeral (Session Messages)

**Storage**: `workspace/{project}/_system/sessions/{session_id}.json`
**Python**: `SessionStore` in `backend/memory/memory_sessions.py`
**Trigger**: Created on first prompt; appended on each turn; never written to PostgreSQL.

Used only for LLM context continuity within a single session. Not searchable.

---

## Layer 1 — Raw Capture (`mem_mrr_*`)

Everything stored verbatim. No AI processing at insert time. The audit trail.

---

### `mem_mrr_prompts`

**Trigger**: `post_prompt.sh` hook → `POST /memory/{project}/prompts`

| Column | Written by | Notes |
|--------|-----------|-------|
| `id` UUID | Hook | PK |
| `session_id` | Hook | Groups turns |
| `source_id` | Hook | External hook timestamp |
| `prompt` TEXT | Hook | Raw user input |
| `response` TEXT | Hook | Raw AI response |
| `tags` JSONB | Hook | `{source, phase, feature, bug, work-item, llm}` |
| `created_at` | DB | Auto |

**Downstream trigger**: Every ~5 prompts in a session → `process_prompt_batch()` (Layer 2).

---

### `mem_mrr_commits`

**Trigger**: `post_commit.sh` hook → `POST /git/{project}/commit-push`

After the hook fires, **three sequential background tasks** run automatically:

| # | Background Task | Output |
|---|----------------|--------|
| 1 | `_sync_commit_and_link()` | INSERT into `mem_mrr_commits` + link to session/prompt |
| 2 | `_embed_commit_background()` → `process_commit()` | Layer 2: mem_ai_events digest + diff chunks |
| 3 | `_extract_commit_code_background()` → `extract_commit_code()` | Layer 1: mem_mrr_commits_code symbol rows |

#### Columns (after migration 016)

| Column | Written by | Notes |
|--------|-----------|-------|
| `commit_hash` VARCHAR(64) | Hook | PK |
| `commit_short_hash` VARCHAR(8) | DB (generated) | `LEFT(commit_hash,8)` — read-only |
| `author` TEXT | Hook (git log) | Git author name |
| `author_email` TEXT | Hook (git log) | Git author email |
| `commit_msg` TEXT | Hook | Full commit message |
| `diff_summary` TEXT | Hook | `git diff --stat` output |
| `summary` TEXT | **LLM** (back-prop) | 1-2 sentence Haiku digest from `commit_digest` prompt |
| `llm` TEXT | **LLM** (back-prop) | Model used for digest e.g. `claude-haiku-4-5-20251001` |
| `exec_llm` BOOLEAN | **LLM** (back-prop) | TRUE after `process_commit()` runs |
| `session_id` | Hook | Links to active session |
| `prompt_id` UUID | Hook | Links to prompt that triggered the commit |
| `tags` JSONB | Hook | **User intent only**: `{source, phase, feature, bug, work-item}` |
| `tags_ai` JSONB | **LLM** (back-prop) | AI metadata: `{languages: [...]}` from diff analysis |
| `committed_at` | Hook | Git timestamp |
| `created_at` | DB | Auto |

**Key change (migration 016)**: `tags` is now **clean** — no file stats, no symbol lists, no LLM keys.
Old technical keys (`files`, `languages`, `symbols`, `rows_changed`, `llm`, `analysis`) were migrated out:
- `llm` → `llm` column
- `languages` → `tags_ai["languages"]`
- `files`, `symbols`, `rows_changed` → **`mem_mrr_commits_code`** table (per-symbol rows)

#### Commit LLM Prompts

Three prompts fire during a commit, each using a different model:

| Step | Prompt | File | Model | Max tokens | When | Returns |
|------|--------|------|-------|-----------|------|---------|
| 1. Commit message | `commit_analysis` | `memory/commits/commit_analysis.md` | **Sonnet** | 800 | Before `git commit` (in `_generate_commit_message()`) | `{message, summary, key_classes, key_methods, patterns_used, decisions, test_coverage, dependencies}` |
| 2. Digest | `commit_digest` | `memory/commits/commit_digest.md` | **Haiku** | 200 | After commit stored (`process_commit()`) | `{summary, action_items, importance}` |
| 3. Symbol summary | `commit_symbol` | `memory/commits/commit_symbol.md` | **Haiku** | 120 | Per changed symbol (`extract_commit_code()`) | Plain 1-sentence summary |

**Why Sonnet for step 1?** Generating a conventional commit message + full structured analysis from a diff requires deep code understanding. Steps 2 and 3 are simpler digests → Haiku is sufficient and cheaper.

---

### `mem_mrr_commits_code` (new — migration 016)

**Trigger**: Background task 3 above → `extract_commit_code()` in `memory/memory_code_parser.py`
**Tool**: tree-sitter AST parsing (Python, JS/TS, Go, Rust, Java, Ruby)

One row per changed **symbol** (class / method / function) per file per commit.

| Column | Written by | Notes |
|--------|-----------|-------|
| `commit_hash` | FK | References mem_mrr_commits |
| `file_path` TEXT | tree-sitter | Full file path in repo |
| `file_ext` TEXT | Parser | `.py`, `.ts`, etc. |
| `file_language` TEXT | Parser | Detected from extension |
| `file_change` TEXT | Parser | `added` \| `modified` \| `deleted` \| `renamed` |
| `symbol_type` TEXT | tree-sitter | `class` \| `method` \| `function` |
| `class_name` TEXT | tree-sitter | Parent class (NULL for module-level functions) |
| `method_name` TEXT | tree-sitter | Function/method name |
| `full_symbol` TEXT | DB (generated) | `class_name.method_name` or just one of them |
| `symbol_change` TEXT | Parser | `added` \| `modified` \| `deleted` |
| `rows_added` INT | Parser | Lines added within this symbol's range |
| `rows_removed` INT | Parser | Lines removed within this symbol's range |
| `diff_snippet` TEXT | Parser | Diff lines touching this symbol (≤500 chars) |
| `llm_summary` TEXT | **LLM** | 1-sentence summary from `commit_symbol` prompt (skipped if rows_added+rows_removed < min_lines) |
| `embedding` VECTOR(1536) | Trigger | OpenAI embed of `llm_summary` |

**YAML guards** (`workspace/{project}/project.yaml`):
```yaml
commit_code_extraction:
  min_lines: 5                      # skip llm_summary if fewer rows changed
  only_on_commits_with_tags: false  # if true, only extract symbols from tagged commits
```

**Use case**: Semantic search by symbol name, per-feature code coverage, "what touched `ClassName.method`?"

---

### `mem_mrr_items`

**Trigger**: Manual `POST /memory/{project}/items` or CLI import

| Column | Written by | Notes |
|--------|-----------|-------|
| `item_type` | User | `requirement`, `decision`, `meeting`, `note` |
| `raw_text` | User | Full document content |
| `summary` TEXT | **LLM** (back-prop) | Haiku digest |
| `tags` JSONB | User | Classification |

**Downstream trigger**: `process_item()` → Layer 2 (item_digest + optional meeting_sections + relation_extraction).

---

### `mem_mrr_messages`

**Trigger**: Integration hook → `POST /memory/{project}/messages`

Stores Slack / Teams / Discord thread dumps.

**Downstream trigger**: `process_messages()` → Layer 2 (message_chunk_digest).

---

## Layer 2 — AI Events (`mem_ai_events`)

Every Layer 1 source gets a Haiku digest + OpenAI embedding here.
This is the **primary semantic search target**.

**Python**: `MemoryEmbedding` in `backend/memory/memory_embedding.py`

| Column | Written by | Notes |
|--------|-----------|-------|
| `event_type` | Trigger | `prompt_batch` \| `commit` \| `item` \| `message` \| `session_summary` \| `workflow` |
| `source_id` | Trigger | UUID or hash of the Layer 1 row |
| `chunk` INT | Trigger | `0` = summary/digest; `1+` = detail chunks |
| `chunk_type` | Trigger | `full`, `summary`, `section`, `diff_file` |
| `content` TEXT | LLM/Trigger | Haiku digest (chunk=0); raw diff/code (chunk>0) |
| `summary` TEXT | **LLM** | 1-2 sentence Haiku summary |
| `action_items` TEXT | **LLM** | Extracted open tasks |
| `importance` SMALLINT | **LLM** | 0–10 AI-scored |
| `embedding` VECTOR(1536) | Trigger | OpenAI text-embedding-3-small |
| `tags` JSONB | Trigger+LLM | Mirror tags merged with `{llm: model}` |
| `processed_at` | Trigger | Set when `promote_feature_snapshot()` consumes event |

### Importance Scale

| Score | Meaning |
|-------|---------|
| 1–2 | Trivial / chore |
| 3–4 | Minor fix / debug |
| 5–6 | Feature work, new endpoint |
| 7–8 | Significant change, new module |
| 9–10 | Critical / architectural decision |

**Relevance formula**: `importance × exp(-0.01 × age_days)` — foundational facts get 50% floor.

---

### How each `event_type` is produced

#### `prompt_batch`

**When**: Auto after every ~5 prompts in a session (inside `POST /memory/{project}/prompts`)
**Prompt**: `prompt_batch_digest` (Haiku, 250 tokens) → `{summary, action_items, importance}`
**Chunks**: chunk=0 = Haiku digest; chunk≥1 = long response paragraphs (raw embed, no LLM)
**Auto-triggers next**: `extract_work_items_from_events()` in background (fire-and-forget)

#### `commit`

**When**: After commit is stored → background task 2 → `process_commit()`
**Prompt**: `commit_digest` (Haiku, 200 tokens) → `{summary, action_items, importance}`
**Chunks**: chunk=0 = Haiku digest; chunk≥1 = per-file diff sections (code files only; CLAUDE.md / .cursorrules / MEMORY.md filtered out)
**Back-propagates**: `summary` → `mem_mrr_commits.summary`; `llm` + `exec_llm=TRUE` → `mem_mrr_commits`; `languages` → `mem_mrr_commits.tags_ai`

#### `item`

**When**: After `POST /memory/{project}/items` → `process_item()`
**Prompts**:
- Short items (<200 words): `item_digest` (Haiku, 200 tokens) → `{summary, action_items, importance}`
- Meeting/large items: `meeting_sections` (Haiku, 1000 tokens) → `[{title, content}]`
- Always: `relation_extraction` (Haiku, 400 tokens) → `{relations: [{from, relation, to, note}]}`

#### `session_summary`

**When**: `log_session_stop.sh` hook → `POST /memory/{project}/session-summary`
**Prompt**: `session_end_synthesis` (Haiku, 600 tokens) → `{summary, open_threads, next_steps}`
**Importance**: typically 7–8 (session-level synthesis = high signal)

#### `message`

**When**: After `POST /memory/{project}/messages` → `process_messages()`
**Prompt**: `message_chunk_digest` (Haiku, 200 tokens) → plain text summary

#### `workflow`

**When**: After a 4-agent pipeline run completes
**No LLM digest** — workflow output embedded directly

---

## Layer 3 — Structured Artifacts (`mem_ai_*`)

### `mem_ai_work_items` — AI-detected tasks / bugs / features

**Trigger**: `extract_work_items_from_events()` — **auto-triggered** after every prompt batch
**Python**: `MemoryPromotion` in `backend/memory/memory_promotion.py`

| Column | Written by | Notes |
|--------|-----------|-------|
| `ai_category` | **LLM** | `bug`, `feature`, `task` |
| `ai_name` | **LLM** | Lowercase-hyphenated slug; UNIQUE key within project+category |
| `ai_desc` | **LLM** | 1-2 sentence description |
| `summary` | **LLM** (Planner) | 3-4 sentence status summary — written by `run_planner()` |
| `action_items` | **LLM** (Planner) | Remaining tasks — written by `run_planner()` |
| `acceptance_criteria` | **LLM** (Planner) | Testable QA criteria — written by `run_planner()` |
| `requirements` | **LLM** | Functional requirements (from extraction) |
| `code_summary` TEXT | **LLM** | Code context distilled from linked commits |
| `status_ai` | **LLM** | AI suggestion: `active`, `in_progress`, `done` |
| `status_user` | **User** | User-set lifecycle: `active`, `in_progress`, `paused`, `done` |
| `start_date` | User+Trigger | Auto-set when `status_user` → `in_progress` |
| `tag_id` UUID | **User** | Confirmed link to planner_tag (drag-drop ONLY) |
| `ai_tag_id` UUID | **LLM** | Auto-suggested tag (set by `match_work_item_to_tags()`) |
| `source_event_id` UUID | Trigger | mem_ai_events row that generated this item (prevents re-extraction) |
| `embedding` VECTOR | Trigger | Semantic search |
| `seq_num` INT | DB | Auto-increment display number |
| `merged_into` UUID | **User** | Points to canonical work item after user merge |

**LLM prompt**: `work_item_extraction` (Haiku, 500 tokens)
→ `{items: [{category, name, description}]}`
**Input**: Unprocessed `mem_ai_events` summaries + action_items where no `source_event_id` link exists

#### Tag matching pipeline (auto after extract)

```
ai_name exact match → ai_tag_id @ confidence 1.0
       ↓ (no match)
Vector cosine > 0.85 → ai_tag_id auto-set
       ↓ (no match)
Haiku judgment 0.70–0.85 → ai_tag_id set if approved
       ↓ (no match)
ai_tag_id = NULL

tag_id NEVER auto-set — user drag-drop only
```

**Prompt used**: `ai_tag_suggestion` (Haiku) via `MemoryTagging.match_work_item_to_tags()`

---

### `mem_ai_project_facts` — Durable project facts

**Trigger**: `MemoryPromotion.detect_fact_conflicts()` — called during feature snapshots
**LLM prompt**: `conflict_detection` (Haiku, 300 tokens) → `{conflict, resolution, merged_value, reasoning}`

| Column | Written by | Notes |
|--------|-----------|-------|
| `fact_key` | **LLM** | e.g. `primary_database`, `auth_method` |
| `fact_value` | **LLM** | e.g. `PostgreSQL 15 + pgvector` |
| `category` | **LLM** | `stack`, `convention`, `constraint`, `client` |
| `valid_until` | Trigger | NULL = current fact; set when superseded |
| `conflict_status` | LLM+User | `ok`, `supersede`, `merge`, `flag` |
| `embedding` VECTOR | Trigger | Semantic fact search |

---

## Layer 4 — User-Managed Tags (`planner_tags`)

**Owner**: User. No auto-writes.
LLM writes ONLY when user explicitly clicks "Run Planner" or "Snapshot" in the UI.

| Column | Written by | Notes |
|--------|-----------|-------|
| `name` | **User** | Tag identity, UNIQUE per project+category |
| `category_id` | **User** | FK to mng_tags_categories: feature/bug/task |
| `status` | **User** | `open`, `active`, `done`, `archived` |
| `priority` | **User** | 1–5 |
| `short_desc`, `full_desc` | **User** | Human descriptions |
| `requirements` | **User** | What the feature must do (user-written, NOT LLM) |
| `due_date` | **User** | Target completion date |
| `acceptance_criteria` | **LLM** (Run Planner) | Written by `run_planner()` |
| `summary` | **LLM** (Planner/Snapshot) | Use-case summary |
| `action_items` | **LLM** (Planner/Snapshot) | Remaining work |
| `design` JSONB | **LLM** (Snapshot) | `{high_level, low_level, patterns_used}` |
| `code_summary` JSONB | **LLM** (Snapshot) | `{files, key_classes, key_methods, ...}` |
| `embedding` VECTOR | Trigger | From summary+action_items; used by tag matching |

#### LLM writes to planner_tags (explicit user action only)

| User Action | Method | Prompt | Model | Writes |
|------------|--------|--------|-------|--------|
| "Run Planner" button | `MemoryPlanner.run_planner()` | `planner_summary` (Haiku, 2000 tokens) | Haiku | `summary`, `action_items`, `acceptance_criteria`; updates linked work items |
| "Snapshot" button | `MemoryPromotion.promote_feature_snapshot()` | `feature_snapshot` (Haiku, 2500 tokens) | Haiku | `summary` (=requirements), `action_items`, `design`, `code_summary` |

---

## All System Prompts

All prompts are **file-based** in `backend/prompts/` — NOT stored in the DB, NOT exposed to users.
Loaded via `from core.prompt_loader import prompts` (singleton, lazy-loaded).
Change model or cost by editing `backend/prompts/prompts.yaml`.

| Prompt name | File | Model | Max tokens | Trigger | Returns |
|------------|------|-------|-----------|---------|---------|
| `commit_analysis` | `memory/commits/commit_analysis.md` | **Sonnet** | 800 | Before `git commit` | `{message, summary, key_classes, key_methods, patterns_used, decisions, test_coverage, dependencies}` |
| `commit_digest` | `memory/commits/commit_digest.md` | Haiku | 200 | After commit stored | `{summary, action_items, importance}` |
| `commit_symbol` | `memory/commits/commit_symbol.md` | Haiku | 120 | Per changed symbol | 1-sentence plain text |
| `prompt_batch_digest` | `memory/prompt_batch_digest.md` | Haiku | 250 | Every ~5 prompts | `{summary, action_items, importance}` |
| `item_digest` | `memory/item_digest.md` | Haiku | 200 | Item stored (short) | `{summary, action_items, importance}` |
| `meeting_sections` | `memory/meeting_sections.md` | Haiku | 1000 | Item stored (meeting/large) | `[{title, content}]` |
| `message_chunk_digest` | `memory/message_chunk_digest.md` | Haiku | 200 | Message stored | Plain text summary |
| `relation_extraction` | `memory/relation_extraction.md` | Haiku | 400 | Item embed | `{relations: [{from, relation, to, note}]}` |
| `session_end_synthesis` | `memory/session_end_synthesis.md` | Haiku | 600 | Session end hook | `{summary, open_threads, next_steps}` |
| `work_item_extraction` | `memory/work_items/work_item_extraction.md` | Haiku | 500 | After prompt batch | `{items: [{category, name, description}]}` |
| `work_item_promotion` | `memory/work_items/work_item_promotion.md` | Haiku | 300 | Work item pipeline | `{summary, status_ai}` |
| `conflict_detection` | `memory/conflict_detection.md` | Haiku | 300 | Fact upsert | `{conflict, resolution, merged_value, reasoning}` |
| `feature_snapshot` | `memory/feature_snapshot.md` | Haiku | 2500 | Snapshot button | `{requirements, action_items, design, code_summary, relations}` |
| `planner_summary` | `memory/planner/planner_summary.md` | Haiku | 2000 | Run Planner button | `{use_case_summary, done_items, remaining_items, acceptance_criteria, work_item_updates}` |

**To switch a prompt to Sonnet**: edit `prompts.yaml` → `model: sonnet`. No code changes needed.

---

## Full Trigger Flow

```
post_prompt.sh hook
        │
        ▼
POST /memory/{p}/prompts
        │  MemoryMirroring.mirror_prompt()
        ▼
mem_mrr_prompts (insert)
        │
        │  [every ~5 prompts in session]
        ▼
process_prompt_batch()          ← prompt_batch_digest (Haiku)
        │
        ▼
mem_ai_events (event_type='prompt_batch', chunk=0, embedding)
        │
        │  [background, fire-and-forget]
        ▼
extract_work_items_from_events()  ← work_item_extraction (Haiku)
        │
        ▼
mem_ai_work_items (INSERT/upsert)
        │
        │  [background]
        ▼
match_work_item_to_tags()         ← ai_tag_suggestion (Haiku, if needed)
        │
        ▼
work_item.ai_tag_id updated (suggestion only — tag_id requires user drag-drop)


─────────────────────────────────────────────────────────

post_commit.sh hook
        │
        ▼
POST /git/{p}/commit-push
        │  [background task 0: inline]
        │  _generate_commit_message()   ← commit_analysis (Sonnet)
        │  → commit message written to git
        │
        │  git commit + git push
        │
        │  [background task 1]
        ▼
_sync_commit_and_link()
        │  INSERT mem_mrr_commits {commit_hash, author, tags={source,phase,feature,bug,work-item},
        │                          tags_ai={}, exec_llm=FALSE}
        │  LINK to session + prompt_id
        ▼
mem_mrr_commits (insert)
        │
        │  [background task 2]
        ▼
process_commit()                  ← commit_digest (Haiku)
        │
        ├─ mem_ai_events (event_type='commit', chunk=0 = digest + embedding)
        ├─ mem_ai_events (chunk≥1 = per-file diff sections, raw embed)
        │
        ├─ mem_mrr_commits.summary = digest text (back-propagate)
        ├─ mem_mrr_commits.llm = haiku_model (back-propagate)
        ├─ mem_mrr_commits.exec_llm = TRUE (back-propagate)
        └─ mem_mrr_commits.tags_ai["languages"] = [...] (back-propagate)
        │
        │  [background task 3]
        ▼
extract_commit_code()             ← commit_symbol (Haiku, per symbol if rows ≥ min_lines)
        │  tree-sitter AST parse → per-symbol rows
        ▼
mem_mrr_commits_code (bulk insert, ON CONFLICT DO NOTHING)


─────────────────────────────────────────────────────────

log_session_stop.sh hook
        │
        ▼
POST /memory/{p}/session-summary
        │
        ▼
_generate_session_summary()       ← session_end_synthesis (Haiku)
        │
        ▼
mem_ai_events (event_type='session_summary', summary, open_threads, next_steps)
        │
        │  [auto]
        ▼
write_root_files()
        │
        ▼
{code_dir}/CLAUDE.md, .cursorrules, .claude/memory/top_events.md (regenerated)


─────────────────────────────────────────────────────────

User clicks "Snapshot" in UI
        │
        ▼
POST /projects/{p}/snapshot/{tag_name}
        │
        ▼
promote_feature_snapshot()        ← feature_snapshot (Haiku)
        │
        ├─ planner_tags: summary, action_items, design, code_summary, embedding
        └─ detect_fact_conflicts() ← conflict_detection (Haiku)
                │
                ▼
           mem_ai_project_facts (upsert)


─────────────────────────────────────────────────────────

User clicks "Run Planner" in UI
        │
        ▼
POST /projects/{p}/planner/{tag_id}
        │
        ▼
MemoryPlanner.run_planner()       ← planner_summary (Haiku)
        │
        ├─ planner_tags: summary, action_items, acceptance_criteria
        ├─ mem_ai_work_items: action_items, acceptance_criteria, summary (per linked item)
        └─ workspace/{p}/documents/{cat}/{tag}.md  (written to disk)
```

---

## Tagging — How `tags` JSONB Works

Every `mem_mrr_*` table has a `tags JSONB` column. Tags flow from the hook into raw storage, then propagate upward through digests into `mem_ai_events.tags`.

### `mem_mrr_prompts.tags` — set by hook at insert time

```json
{
  "source": "claude_cli",        // hook source: claude_cli | cursor | aicli_cli | ui
  "phase": "development",        // optional: discovery | development | testing | ...
  "feature": "auth-refactor",    // optional: current feature slug
  "bug": "login-500-error",      // optional: bug reference
  "work-item": "uuid-or-slug",   // optional: linked work item
  "llm": "claude-sonnet-4-6"     // optional: LLM used in session
}
```

### `mem_mrr_commits.tags` — user intent only (clean after migration 016)

```json
{
  "source": "commit_push",       // always present
  "phase": "development",        // from active session tags
  "feature": "auth-refactor",    // from active session tags
  "bug": "login-500-error",      // from active session tags
  "work-item": "uuid-or-slug"    // from active session tags
}
```

**`tags_ai`** (AI-enriched, separate):
```json
{
  "languages": ["python", "typescript"],  // from smart_chunk_diff()
  "analysis": { ... }                     // from commit_analysis (Sonnet)
}
```

### `mem_ai_events.tags` — merged from mirror + LLM metadata

```json
{
  "source": "claude_cli",        // from mirror row
  "feature": "auth-refactor",    // from mirror row
  "llm": "claude-haiku-4-5-20251001",  // added by process_*()
  "event": "prompt_batch",       // added by _upsert_event()
  "chunk_type": "full"           // added by _upsert_event()
}
```

---

## Quick Reference: Which Table for What

| Question | Table / Query |
|----------|--------------|
| All prompts this session | `mem_mrr_prompts WHERE session_id=?` |
| Which files changed in a commit | `mem_mrr_commits_code WHERE commit_hash=?` (new!) |
| Which symbols changed in a commit | `mem_mrr_commits_code WHERE commit_hash=? AND symbol_type IN (...)` |
| Semantic search across all history | `mem_ai_events` (vector cosine via `semantic_search()`) |
| What work is in progress | `mem_ai_work_items WHERE status_user='in_progress'` |
| AI-suggested tag for a work item | `mem_ai_work_items.ai_tag_id` |
| Full context for feature X | `planner_tags WHERE name=X` + `mem_ai_work_items WHERE tag_id=X.id` |
| Recent high-importance events | `mem_ai_events ORDER BY importance*exp(-0.01*age_days) DESC` |
| What languages were used in commit | `mem_mrr_commits.tags_ai->>'languages'` |
| Project tech stack | `mem_ai_project_facts WHERE category='stack' AND valid_until IS NULL` |

---

## AI vs. User Ownership — Summary

| Data | AI Writes | User Writes | User Reads |
|------|-----------|-------------|-----------|
| `mem_mrr_prompts` | ✗ | via hook | ✓ history |
| `mem_mrr_commits` | `summary`, `llm`, `exec_llm`, `tags_ai` | via hook: `tags`, `author` | ✓ history |
| `mem_mrr_commits_code` | ALL (tree-sitter + Haiku) | ✗ | ✓ code intelligence |
| `mem_ai_events` | ALL | ✗ | ✓ search results |
| `mem_ai_work_items` | ALL except `status_user`, `tag_id` | `status_user`, `tag_id` | ✓ work board |
| `mem_ai_project_facts` | ALL (LLM resolves conflicts) | review `flag` items | ✓ knowledge |
| `planner_tags` | `summary`, `action_items`, `acceptance_criteria`, `design`, `code_summary` (on button click only) | ALL other fields | ✓ project plan |

---

## Phase Plan: Merging work_items ↔ planner_tags

Current state: Two parallel systems exist.
- `mem_ai_work_items` — AI creates and owns; user can set `status_user` + `tag_id`
- `planner_tags` — User creates and owns; LLM enriches on demand

**Both work correctly independently**. The merge path:

| Step | Action | Field |
|------|--------|-------|
| ✅ Done | AI suggests tag for each work item | `ai_tag_id` (auto, vector search) |
| ✅ Done | User confirms link via drag-drop | `tag_id` (manual) |
| Next | Run Planner reads from linked work_items | `planner_tags.id = work_item.tag_id` |
| Next | Snapshot filters events by `feature` tag | `mem_ai_events.tags->>'feature' = tag_name` |
| Future | Work item creation auto-creates planner_tag if no match | merge into one flow |
