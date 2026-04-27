# aicli Memory System Audit
_Last updated: 2026-04-27 | Goal: aicli as a living memory layer — gathers facts, reflects real project state, exposes structured knowledge via MCP_

---

## 1. Memory Files — Current State

### CLAUDE.md (rendered by `memory_files.py:render_root_claude_md`)

| Section | Source | State |
|---------|--------|-------|
| Header + context age | timestamp + `project_state.json.last_memory_run` | ✓ Age shown since last fix |
| Project description | PROJECT.md Vision + Core Goals (≤1200 chars) | ✓ Accurate after last fix |
| Code structure | Top-level dirs from `code_dir` (file scan) | ✓ Always fresh on render |
| Stack & Architecture | `project_state.json.tech_stack` | ✓ Accurate — Haiku re-synthesises each /memory run |
| Key Architectural Decisions | `project_state.json.key_decisions` | ✓ REPLACE strategy (PROJECT.md authoritative) |
| In Progress | `project_state.json.in_progress` (last 6 items) | ⚠ Only 6 items; derived from recent prompts, can lag |
| Active Features | `mem_work_items` approved, non-done (LIMIT 20) | ✓ Shows wi_id + name + summary (fixed) + due_date |
| Code Hotspots | `mem_mrr_commits_file_stats` score ≥ threshold | ✓ Refreshed after every commit via `write_root_files` |
| Recently Changed | `mem_mrr_commits_code` last 200 symbols | ✓ Token-budget aware; rolls off oldest first |
| Footer | auto-generated note | ✓ |

**Gap**: `In Progress` section is purely prompt-derived — it reflects what Claude was doing, not what is genuinely "in flight" in the work item tracker. Cross-referencing `user_status='in-progress'` items would be more accurate.

---

### code.md (rendered by `_render_code_md`)

| Section | Source | State |
|---------|--------|-------|
| Directory tree | Walks `code_dir` depth-3, excludes node_modules/venv/etc | ✓ Always current |
| Active Work Items | `mem_work_items` approved, not deleted | ✓ Full list (not capped like CLAUDE.md) |
| Recently Changed | `mem_mrr_commits_code` last 20 symbols | ✓ Symbol-level with llm_summary |
| Code Hotspots | `mem_mrr_commits_file_stats` | ✓ Score + commit count + lines |
| File Coupling | `mem_mrr_commits_file_coupling` co_change ≥ 3 | ✓ Top 10 pairs |

**code.md trigger**: `write_root_files()` called (a) after every commit background task, (b) on `/memory`, (c) on work item update. Previously only `write_code_md()` was called on commit — now fixed to `write_root_files()`.

**code.md well-defined?** Mostly yes. Missing: architectural role definitions (how to write code, naming conventions, patterns). These live only in PROJECT.md — not in code.md. **No coding standards section.**

---

### PROJECT.md

| Aspect | State |
|--------|-------|
| Vision / Core Goals sections | ✓ Feeds CLAUDE.md project description |
| Memory Architecture section | ✓ Feeds `proj_intro` for Haiku synthesis prompt |
| Code conventions / patterns | ✗ Not present — no "how to code in this project" section |
| Who updates it | User-managed; `/memory` reads but does NOT overwrite it |
| Staleness risk | High — if user never updates, key_decisions may still drift |

**Gap**: PROJECT.md has no **coding conventions** section. There is no place that tells Claude Code how to structure files, name methods, import patterns, etc. code.md could include this if it read a `conventions.md` file.

---

### project_state.json (hub for all renders)

| Field | Source | State |
|-------|--------|-------|
| `tech_stack` | Haiku synthesis | ✓ Re-synthesised from recent prompts + PROJECT.md |
| `key_decisions` | Haiku synthesis | ✓ REPLACE each run — PROJECT.md authoritative |
| `in_progress` | Haiku synthesis | ✓ Last ~6 real work activities |
| `project_summary` | Haiku synthesis | ✓ 300 char project description |
| `project_facts` | Haiku synthesis (fallback for empty DB table) | ⚠ Only populated if Haiku adds it |
| `last_memory_run` | Set by `/memory` endpoint | ✓ Shown in CLAUDE.md header |

**Staleness control**: Between `/memory` runs, `project_state.json` is stale. CLAUDE.md reflects the last cached state. No auto-refresh unless commit or work-item update triggers `write_root_files()`.

---

### Project Facts (`mem_ai_project_facts`)

| Aspect | State |
|--------|-------|
| Auto-population | ✗ Never auto-populated — only `memory_promotion.py` writes on conflict detection, which rarely fires |
| Manual population | ✗ No UI or endpoint to add facts directly |
| Embedding | ✓ Table has `VECTOR(1536)` column — facts ARE embedded when saved |
| CLAUDE.md fallback | ✓ Falls back to `project_state.json.project_facts` when DB table is empty |
| Searchable via MCP | ✓ `search_facts` MCP tool queries `mem_work_items` embeddings (but NOT `mem_ai_project_facts`) |

**Critical gap**: `mem_ai_project_facts` is effectively a dead table. The conflict-detection trigger never fires automatically. No LLM call populates it from normal usage. Facts only exist in `project_state.json` (not embedded, not searchable).

---

### Approved Work Items (`mem_work_items` WHERE `approved_at IS NOT NULL`)

| Aspect | State |
|--------|-------|
| In CLAUDE.md | ✓ Top 20 by bug-first / importance — shows wi_id + name + summary + due_date |
| In code.md | ✓ Full approved list |
| Searchable via MCP | ✓ `search_work_items` — pgvector cosine over embedded items |
| Re-embed on edit | ✓ Triggers when name/summary/deliveries/delivery_type change |
| score_status sync | ✓ Auto-sets `score_status=5` when user marks `user_status='done'` |
| acceptance_criteria | ✓ Written by 4-agent pipeline; NOT shown in CLAUDE.md |
| Reclassify on drift | ✓ `POST /wi/{project}/{id}/reclassify` — Haiku re-infers wi_type + scores |

**Gap**: `acceptance_criteria` and `implementation_plan` are never surfaced in any context file. LLMs cannot see the agreed spec unless they call `list_work_items` via MCP.

---

### Unapproved Work Items (`wi_id LIKE 'AI%'`)

| Aspect | State |
|--------|-------|
| In CLAUDE.md | ✗ Excluded (fixed — `approved_at IS NOT NULL` filter) |
| Visible to Claude | ✗ Only via `list_work_items` MCP tool |
| Embedded | ✗ No embedding until approved |
| Searchable | ✗ Cannot be found via semantic search |
| Considered in classification | ✓ `classify()` deletes all AI-drafts and re-runs, so they're regenerated fresh |

**Design note**: Unapproved items are intentionally hidden from LLM context — they are drafts pending human review. Correct behavior.

---

### How New Requirements Override Old

| Change type | Mechanism | Works? |
|-------------|-----------|--------|
| Edit PROJECT.md + run `/memory` | Haiku re-synthesises `key_decisions` from scratch using PROJECT.md | ✓ |
| Add/rename a layer in PROJECT.md | Picked up next `/memory` run | ✓ |
| Old fact in `project_state.json` | REPLACE strategy — not accumulated | ✓ |
| Stale fact in `mem_ai_project_facts` | `valid_until` can soft-expire; conflict detection can mark | ⚠ Rarely used |
| Old events in mem_mrr_* still reference deprecated patterns | They flow into next classify() and can re-create stale items | ✗ No "event expiry" |

---

## 2. Work Item Flows

### Classification (events → items)

| Aspect | State |
|--------|-------|
| Event sources | `mem_mrr_prompts`, `mem_mrr_commits`, `mem_mrr_messages`, `mem_mrr_items` (wi_id IS NULL) |
| Grouping | Token-bounded batches (~3000 tok); events grouped by time + source |
| Use case cap | Max 8 use cases total per run; Haiku checks existing UCs first |
| Child items | One item per distinct change (bug/feature/task — granular) |
| Tags from events | ✓ Phase + feature tags flow from source events into items via `_update_item_tags()` |
| Commit hotspot data | ✓ `mem_mrr_commits_file_stats` included in classification context |
| Duplicate runs | ✓ All AI drafts deleted on each `classify()` run — always fresh |
| Threshold trigger | Optional (project.yaml `mode: threshold`) — off by default |

---

### Item Scores

| Score | Meaning | Set by | Auto-update |
|-------|---------|--------|-------------|
| `score_importance` (0-5) | AI-assessed criticality | Haiku at classify + reclassify | ✓ reclassify |
| `score_status` (0-5) | AI-assessed completeness | Haiku at classify + reclassify | ✓ Auto-set to 5 when user_status='done' |
| `user_status` TEXT | User-managed workflow | User via UI/PATCH | N/A |
| `user_importance` INT | User override of importance | User via UI/PATCH | N/A |

**Two-field design**: `score_status` (AI) and `user_status` (user) never sync automatically — by design. They represent different things: AI assessment vs. workflow state.

---

### User Tags

| Tag | Stored | Used in classification? | Used in CLAUDE.md? |
|-----|--------|------------------------|-------------------|
| `phase` | `mng_session_tags` + event JSONB | ✓ Tag priority in classification prompt | ✗ Not directly |
| `feature` | `mng_session_tags` + event JSONB | ✓ Groups events by feature | ✓ Items named by feature |
| `bug` | event JSONB | ✓ Routes to bug type | ✓ Bugs shown first |
| Session auto-detect | `route_chat.py:_auto_detect_session_feature()` | N/A | Auto-applies feature tag |

---

### Commits → Classification Pipeline

| Stage | What | State |
|-------|------|-------|
| Commit pushed | Sonnet: `commit_analysis` → `diff_summary` stored in `mem_mrr_commits` | ✓ |
| Symbol extraction | Haiku per symbol: `commit_symbol` → `llm_summary` in `mem_mrr_commits_code` | ✓ |
| File hotspots | Scores accumulated in `mem_mrr_commits_file_stats` | ✓ |
| File coupling | Co-change pairs in `mem_mrr_commits_file_coupling` | ✓ |
| Feed into classify | `mem_mrr_commits.diff_summary` + hotspot context passed to Haiku | ✓ |
| CLAUDE.md update | `write_root_files()` called in background after symbol extraction | ✓ (fixed) |

**Gap**: `mem_mrr_commits_code.llm_summary` (per-symbol) is written but only exposed in the "Recently Changed" section of CLAUDE.md. It is NOT fed into `classify()` — only commit-level `diff_summary` is used.

---

### Approved Item Consistency

| Scenario | Handled? |
|----------|----------|
| Name/summary edit → stale embedding | ✓ Re-embeds on update |
| user_status='done' → score_status sync | ✓ Auto-sets score_status=5 |
| Child due_date > parent | ✓ Blocked at update |
| UC due_date change → cascade children | ✓ Auto-cascade |
| Two users edit same item concurrently | ✗ Last write wins — no optimistic lock |
| Item drifts from events after many edits | ✓ `/wi reclassify` re-runs Haiku on current text |
| Merge: source appended to target | ✓ Soft-delete source, append to target summary |

---

## 3. Embedding & MCP Strategy

### What Is Currently Embedded

| Data | Model | Table/Column | When |
|------|-------|-------------|------|
| Approved work items | OpenAI text-embedding-3-small | `mem_work_items.embedding VECTOR(1536)` | On approve + on content-field edit |
| Project facts | OpenAI text-embedding-3-small | `mem_ai_project_facts.embedding VECTOR(1536)` | On conflict-detection save (rare) |
| Unapproved items | OpenAI text-embedding-3-small | `mem_work_items.embedding` | Manual `/embed` only |
| code.md | ✗ Not embedded | — | — |
| mem_mrr_commits | ✗ No VECTOR column | — | — |
| mem_mrr_commits_code | ✗ No VECTOR column | — | — |

### Semantic Search Scope

`POST /search/semantic` queries ONLY `mem_work_items.embedding`. Code structure, commits, symbols, and project facts in the DB table are invisible to semantic search.

---

### Should code.md Be Embedded? (Analysis)

| Option | Pros | Cons |
|--------|------|------|
| Embed full code.md | Single document, always fresh, captures hotspots + structure | Large token count; coarse granularity; one vector for entire codebase |
| Embed per-symbol `llm_summary` rows | Granular code-aware search; 120-token snippets already generated | Requires VECTOR column on `mem_mrr_commits_code`; many rows (~N symbols × commits) |
| Embed commit `diff_summary` | Per-commit context; links to work items | Requires VECTOR column on `mem_mrr_commits`; high churn |
| **Embed code.md as one document** | **Best ROI** — file already exists, re-embed on every `write_root_files()` call, one pgvector row | Limited to file-level granularity |

**Recommendation**: Embed code.md as a single document in `mem_ai_project_facts` (or a new `mem_knowledge_docs` table) — refresh embedding on every `write_root_files()` call. This makes code structure and hotspots searchable via MCP `search_memory` without schema changes to commit tables.

---

### MCP Tools — What Claude Can Ask Today

| Question | Tool | Works? |
|----------|------|--------|
| What features are in progress? | `list_work_items` | ✓ |
| What bugs are open? | `list_work_items(category=bug)` | ✓ |
| What did we decide about auth? | `search_memory("auth decision")` | ✓ (via work item embeddings) |
| What files changed recently? | `get_commits` | ✓ (commit list) |
| What is the current tech stack? | `get_project_state` | ✓ |
| What is the code structure? | ✗ No dedicated tool | Indirect via search |
| What files are hotspots? | ✗ No dedicated tool | — |
| What are the project policies? | ✗ No tool | — |
| What requirements are pending? | `list_work_items` (wi_type=requirement) | ✓ if items exist |
| What changed in file X? | ✗ No tool | — |

---

## Summary

### What Was Missed in Previous Audits

| # | Gap |
|---|-----|
| 1 | `mem_mrr_commits_code.llm_summary` (per-symbol AI description) is generated but NOT fed into `classify()` — only commit-level `diff_summary` is used |
| 2 | `mem_ai_project_facts` has an embedding column and IS searchable — but table is effectively empty (never auto-populated) |
| 3 | MCP `search_facts` tool exists but queries `mem_work_items` not `mem_ai_project_facts` — name is misleading |
| 4 | `write_all_files()` writes per-feature CLAUDE.md files under `memory/claude/features/{tag}/` — this is an additional context layer that was not documented |
| 5 | `acceptance_criteria` + `implementation_plan` from the 4-agent pipeline are stored in `mem_work_items` but never surfaced in any context file |
| 6 | `In Progress` section in CLAUDE.md comes from Haiku prompt analysis, not from `user_status='in-progress'` items |

---

### Major Improvements — How to Improve Current State

#### CLAUDE.md / context files
| Improvement | What | Impact |
|-------------|------|--------|
| Add `in-progress` items from DB | Replace prompt-derived "In Progress" with `WHERE user_status='in-progress'` query | High — accurate real work state |
| Surface `acceptance_criteria` | Show first 100 chars of AC for active use cases in CLAUDE.md | High — LLMs see the agreed spec |
| Add coding conventions section | Add `## Conventions` to PROJECT.md; render it in code.md | Medium — guides code generation |
| Expose hotspots via MCP tool | Add `get_hotspots` MCP tool reading `mem_mrr_commits_file_stats` | Medium |

#### Work Items
| Improvement | What | Impact |
|-------------|------|--------|
| Feed symbol summaries into classify | Pass `llm_summary` from `mem_mrr_commits_code` to classification prompt | High — richer per-symbol context |
| Auto-populate `mem_ai_project_facts` | On each `/memory` run, let Haiku extract 5-10 stable facts from PROJECT.md and save to DB | High — makes facts searchable |
| Surface `acceptance_criteria` in MCP | `get_item_by_number` should return full AC + implementation_plan | Medium |

#### MCP / Embedding
| Improvement | What | Impact |
|-------------|------|--------|
| Embed code.md as single doc | Store code.md text as one `mem_ai_project_facts` row with embedding; refresh on commit | High — code structure becomes searchable |
| Add `get_hotspots` MCP tool | Return top-N hotspot files with score + bug_commits from `mem_mrr_commits_file_stats` | Medium |
| Add `get_open_items` MCP tool | Return items by type (bug/requirement/task) with status filter | Medium |
| Fix `search_facts` to query facts table | Currently queries `mem_work_items` — should query `mem_ai_project_facts` | Low (table empty anyway) |
| Auto-populate project facts on /memory | Haiku extracts key=value facts from PROJECT.md + recent prompts; saves to `mem_ai_project_facts` with embedding | High — unlocks fact-based search |
