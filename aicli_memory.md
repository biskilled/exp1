# aicli Memory System Audit
_Last updated: 2026-04-27 | Fresh review — reflects current code state after this session's changes_

---

## 1. Memory Files

### CLAUDE.md (`render_root_claude_md` + `generate_memory` — two separate render paths)

| Section | Source | State |
|---------|--------|-------|
| Header + context age | `project_state.json.last_memory_run` | ✓ |
| Project summary | PROJECT.md Vision + Core Goals (≤1200 chars) | ✓ |
| Code structure | Top-level dirs from `code_dir` (file scan) | ✓ Always fresh |
| Stack & Architecture | `project_state.json.tech_stack` (Haiku synthesis) | ✓ REPLACE each `/memory` run |
| Key Architectural Decisions | `project_state.json.key_decisions` (Haiku synthesis) | ✓ REPLACE each run |
| In Progress | DB `user_status='in-progress'` → fallback to LLM-derived | ✓ Fixed this session |
| Active Features | `mem_work_items` approved, not-done, top 20, bug-first | ✓ wi_id + summary + due_date |
| AC for use cases | `acceptance_criteria` first 150 chars under each UC | ✓ Added this session |
| Code Hotspots | `mem_mrr_commits_file_stats` | ✓ |
| Recently Changed | `mem_mrr_commits_code` last symbols, token-budget aware | ✓ |
| Coding conventions | ✗ Not in CLAUDE.md — only added to code.md this session | ✗ Gap |

**Critical gap**: `generate_memory()` uses `get_project_context()` for CLAUDE.md — NOT `render_root_claude_md()`. All DB in-progress + AC fixes only apply to the commit/work-item trigger path (`write_root_files()`), not to the `/memory` POST path. Two separate render paths exist and are diverging.

---

### code.md (`_render_code_md`)

| Section | Source | State |
|---------|--------|-------|
| Directory tree | Walks `code_dir` depth-3 | ✓ Always current |
| Active Work Items | Approved `mem_work_items`, not-done | ✓ |
| Coding Conventions | `## Conventions` section from `workspace/{p}/memory/PROJECT.md` | ✓ Added this session |
| Recently Changed | `mem_mrr_commits_code` last 20 symbols with llm_summary | ✓ |
| Code Hotspots | `mem_mrr_commits_file_stats` | ✓ |
| File Coupling | `mem_mrr_commits_file_coupling` co_change ≥ 3 | ✓ |

**Trigger**: `write_root_files()` called on (a) commit background task, (b) `/memory`, (c) work item update. Now also calls `_embed_code_md()` at end.
**`write_code_md()`** (lighter call) does NOT call `_embed_code_md()` — but per git grep, commit path uses `write_root_files()`, so this is safe.

---

### PROJECT.md

| Aspect | State |
|--------|-------|
| Vision / Core Goals | ✓ Feeds CLAUDE.md project summary |
| Tech Stack / Architecture | ✓ Feeds Haiku synthesis context |
| Key Decisions section | ✓ Updated by `/memory` from synthesis output |
| Recent Work section | ✓ Updated by `/memory` from synthesis |
| Coding conventions (`## Conventions`) | ✓ Now read into code.md — but user must write it |
| `implementation_plan` / `acceptance_criteria` | ✗ Not in PROJECT.md — only in mem_work_items |
| Staleness | If user never edits, conventions/patterns drift silently |

---

### project_state.json

| Field | Source | State |
|-------|--------|-------|
| `tech_stack` | Haiku synthesis (REPLACE) | ✓ |
| `key_decisions` | Haiku synthesis (REPLACE, max 15) | ✓ |
| `in_progress` | Haiku synthesis — NOW fallback only (DB primary) | ✓ Fixed this session |
| `_synthesis_cache` | Incremental: only resent to Haiku when ≥3 new entries | ✓ |
| `last_memory_run` | ISO timestamp from `/memory` POST | ✓ |
| `project_facts` | Haiku synthesis output — now FALLBACK for empty DB table | ⚠ Rarely populated |

---

### Project Facts (`mem_ai_project_facts`)

| Aspect | State |
|--------|-------|
| Auto-population | ✓ On each `/memory` run via `_auto_populate_project_facts()` — Added this session |
| Expiry of stale facts | ✓ `valid_until = NOW()` for all non-code facts before inserting new — Added this session |
| code.md embedded | ✓ Stored as `fact_key='code_structure'`, refreshed on `write_root_files()` — Added this session |
| Searchable via MCP | ✓ `search_facts` now calls `GET /search/facts` over this table — Fixed this session |
| Duplicate keys | ⚠ Haiku may extract slightly different keys across runs — mitigated by bulk-expiry |
| Conflict detection path | ⚠ `memory_promotion.py` conflict detection still rarely fires |

---

### Approved Work Items (`mem_work_items` WHERE `approved_at IS NOT NULL`)

| Aspect | State |
|--------|-------|
| In CLAUDE.md | ✓ Top 20, bug-first, summary + due_date |
| AC shown in CLAUDE.md | ✓ For use_case type only — Added this session |
| In code.md | ✓ Full list |
| Searchable via MCP | ✓ `search_work_items` → pgvector cosine |
| Re-embed on content edit | ✓ Triggered on name/summary field changes |
| `implementation_plan` surfaced | ✗ Not in any context file — only via MCP `get_item_by_number` |
| Score sync when done | ✓ `user_status='done'` → `score_status=5` auto-set |
| Reclassify on drift | ✓ `POST /wi/{p}/{id}/reclassify` |

---

### Unapproved Work Items (`wi_id LIKE 'AI%'` or `wi_id IS NULL`)

| Aspect | State |
|--------|-------|
| In CLAUDE.md | ✗ Excluded — intentional (drafts pending review) |
| Searchable | ✗ No embedding until approved — intentional |
| Visible to classify() | ✓ All AI-drafts deleted and re-generated each run |
| Visible via MCP | ✓ `list_work_items` and `get_open_items` return all items |

---

### How New Requirements Override Old

| Change | Mechanism | Works? |
|--------|-----------|--------|
| Edit PROJECT.md + run `/memory` | Haiku re-synthesises from scratch using full PROJECT.md | ✓ |
| New architecture decision | Next `/memory` run replaces key_decisions[] entirely | ✓ |
| Deprecated pattern (e.g. no more JSONL) | Haiku should suppress from synthesis if not in PROJECT.md | ⚠ Relies on LLM judgment |
| Old facts in `mem_ai_project_facts` | `valid_until` bulk-expiry before each `/memory` insert | ✓ Fixed this session |
| Old events in `mem_mrr_*` | Still feed into `classify()` — can re-create stale items | ✗ No event expiry |
| Renamed module or class | Only reflected after next commit + write_root_files() | ✓ |

---

## 2. Work Item Flows

### Classification (events → items)

| Aspect | State |
|--------|-------|
| Event sources | `mem_mrr_prompts`, `mem_mrr_commits`, `mem_mrr_messages`, `mem_mrr_items` (wi_id IS NULL) |
| Grouping | Token-bounded batches ~3000 tok; events sorted by time |
| Hotspot context | `mem_mrr_commits_file_stats` attached to commit events | ✓ |
| Per-symbol summaries | `mem_mrr_commits_code.llm_summary` now fed into classify() prompt | ✓ Added this session |
| Use case cap | Max 8 UCs per run; existing UCs passed as context to avoid duplicates | ✓ |
| Duplicate AI-drafts | All AI-draft items deleted before each classify() run | ✓ Always fresh |
| Tag propagation | phase + feature tags flow from source events to item JSONB tags | ✓ |

---

### Item Scores & Status

| Field | Meaning | Set by | Auto-update |
|-------|---------|--------|-------------|
| `score_importance` (0-5) | AI criticality | Haiku at classify + reclassify | ✓ |
| `score_status` (0-5) | AI completeness estimate | Haiku at classify + reclassify | ✓ Auto-5 on done |
| `user_status` TEXT | User workflow stage | User via UI / PATCH | N/A |
| `user_importance` INT | User override | User via UI / PATCH | N/A |

**Gap**: No way to know if an item was "started" vs "just created" from score alone — `score_status` is AI-estimated completeness, not actual implementation progress.

---

### User Tags

| Tag | Stored | In classify? | In CLAUDE.md? |
|-----|--------|-------------|--------------|
| `phase` | `mng_session_tags` + event JSONB | ✓ Priority context | ✗ Indirect |
| `feature` | `mng_session_tags` + event JSONB | ✓ Groups events | ✓ Item names surface it |
| `bug_ref` | event JSONB | ✓ Routes to bug type | ✓ Bugs shown first |

---

### Commits → Code Intelligence Pipeline

| Stage | What | State |
|-------|------|-------|
| Commit pushed | Sonnet: `commit_analysis` → `diff_summary` in `mem_mrr_commits` | ✓ |
| Symbol extraction | Haiku: `commit_symbol` → `llm_summary` in `mem_mrr_commits_code` | ✓ |
| File stats | Hotspot score accumulated in `mem_mrr_commits_file_stats` | ✓ |
| File coupling | Co-change pairs in `mem_mrr_commits_file_coupling` | ✓ |
| Feed into classify() | diff_summary + hotspot + now symbol llm_summary | ✓ Fixed this session |
| CLAUDE.md + code.md update | `write_root_files()` in background after symbol extraction | ✓ |
| code.md embedding | `_embed_code_md()` called at end of `write_root_files()` | ✓ Added this session |

---

### Approved Item Consistency

| Scenario | Handled? |
|----------|----------|
| Name/summary edit → stale embedding | ✓ Re-embeds on update |
| `user_status='done'` → score sync | ✓ Auto-sets `score_status=5` |
| Child `due_date` > parent | ✓ Blocked at update |
| UC `due_date` change → cascade children | ✓ Auto-cascade |
| Concurrent edits by two users | ✗ Last write wins — no optimistic lock |
| Item drifts after many manual edits | ✓ `/wi reclassify` re-runs Haiku |
| Merge: source appended to target | ✓ Soft-delete source, append to target summary |
| `acceptance_criteria` updated → re-embed | ✓ AC is in the re-embed trigger fields |

---

## 3. Embedding & MCP Strategy

### What Is Currently Embedded

| Data | Model | Table.Column | Trigger |
|------|-------|-------------|---------|
| Approved work items | text-embedding-3-small | `mem_work_items.embedding` | On approve + content edit |
| Project facts (auto) | text-embedding-3-small | `mem_ai_project_facts.embedding` | On `/memory` — added this session |
| code.md document | text-embedding-3-small | `mem_ai_project_facts` (`fact_key='code_structure'`) | On `write_root_files()` — added this session |
| Raw prompts | ✗ No vector column | — | — |
| Commits | ✗ No vector column | — | — |
| Per-symbol code | ✗ No vector column | — | — |

---

### MCP Tools — What LLMs Can Ask Now

| Question | Tool | Works? |
|----------|------|--------|
| What features/bugs are open? | `get_open_items(category=bug)` | ✓ Added this session |
| What are in-progress items? | `get_open_items(status=in-progress)` | ✓ Added this session |
| What is the code structure? | `search_facts(category=code)` | ✓ Fixed this session |
| What files are hotspots? | `get_hotspots` | ✓ Added this session |
| What are project conventions / policies? | `search_facts` | ✓ Fixed this session |
| Current tech stack? | `get_project_state` | ✓ |
| What changed recently? | `get_commits` | ✓ |
| Find related features | `search_work_items` | ✓ |
| Recall a past decision | `search_memory` | ⚠ Queries work items, not prompts |
| Item details by ID | `get_item_by_number` | ✓ Returns AC + implementation_plan |
| Number of open bugs | `get_open_items(category=bug)` → count | ✓ |
| What changed in file X? | ✗ No dedicated tool | — |
| Latest project goals / vision | `get_project_state` | ✓ Reads PROJECT.md + state |

---

### Embedding Strategy Analysis

| Option | ROI | Status |
|--------|-----|--------|
| code.md as single doc in facts | High — structure + hotspots searchable, no schema change | ✓ Done |
| Project facts from PROJECT.md | High — makes architecture searchable | ✓ Done |
| Per-symbol `llm_summary` embedding | Medium — granular but ~N×commits rows, needs VECTOR column | ✗ Not done |
| Per-commit `diff_summary` embedding | Low — high churn, coarse, many rows | ✗ Not needed |
| Raw prompt history embedding | Low — noisy, better served by tag filtering | ✗ Intentionally excluded |

---

### `search_memory` Tool — Naming Gap

`search_memory` calls `POST /search/semantic` which queries ONLY `mem_work_items.embedding`. Despite its name, it does NOT search prompt history, commits, code, or project facts. This is confusing — an LLM asking "what did we decide about auth last month" via `search_memory` will only find work items, not actual prompt history. `search_facts` now correctly queries `mem_ai_project_facts`.

---

## Summary

### What Is Still Missing

| # | Gap | Severity |
|---|-----|----------|
| 1 | Dual CLAUDE.md render paths: `generate_memory()` and `render_root_claude_md()` are diverging — DB in-progress/AC fixes only apply to the commit-trigger path | High |
| 2 | `search_memory` queries work items, not actual prompt/commit history — misleading name and behavior | High |
| 3 | `implementation_plan` (from 4-agent pipeline) never surfaced in any context file | Medium |
| 4 | No event expiry — old `mem_mrr_*` rows feed into `classify()` indefinitely and can re-create stale work items | Medium |
| 5 | PROJECT.md has no `## Conventions` section by default — must be user-written for code.md to pick it up | Medium |
| 6 | `mem_ai_project_facts` duplicate keys — Haiku may extract slightly different key names each run | Low |
| 7 | `write_code_md()` (lighter call) does not call `_embed_code_md()` — if ever used in isolation, code.md embedding goes stale | Low |
| 8 | No "what changed in file X" MCP tool — useful for targeted code investigation | Low |

---

### Major Improvements — Per Component

#### Component 1: Memory Files
| Improvement | Action |
|-------------|--------|
| Merge the two CLAUDE.md render paths | `generate_memory()` should call `MemoryFiles().render_root_claude_md(ctx)` instead of `get_project_context()` — single source of truth |
| Add `## Conventions` to starter PROJECT.md templates | All new projects get a conventions scaffold out of the box |
| Surface `implementation_plan` in code.md | Show first 200 chars of `implementation_plan` for approved features in code.md Active Work Items |
| Add conventions to CLAUDE.md | Move conventions from code.md to CLAUDE.md (higher read frequency) or include in both |

#### Component 2: Work Items
| Improvement | Action |
|-------------|--------|
| Event expiry / archive | Add `archived_before` timestamp to `classify()` — events older than N days or already in a done item are skipped |
| Show `user_status` in item score context | When reclassifying, pass current `user_status` to Haiku so `score_status` aligns with reality |
| Backfill missing symbol embeddings | Embed `llm_summary` rows from `mem_mrr_commits_code` into a new search table for file-level search |
| `implementation_plan` in CLAUDE.md | Show 1-liner for features with `user_status='in-progress'` |

#### Component 3: Embedding / MCP
| Improvement | Action |
|-------------|--------|
| Rename or fix `search_memory` | Either search actual prompt history (add embedding column to `mem_mrr_prompts`) or rename to `search_items` to reduce confusion |
| Add `get_file_history` MCP tool | Query `mem_mrr_commits_code` for a specific `file_path` — returns recent changes + llm_summary per symbol |
| Fact deduplication | Before inserting new facts, compare keys with edit-distance; avoid near-duplicate keys like `database` vs `database_engine` |
| Embed `implementation_plan` separately | Store as a second `mem_ai_project_facts` row per approved feature so it's independently searchable |
