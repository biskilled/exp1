# aicli Memory System — System Audit
_Last updated: 2026-04-27 | Goal: any LLM can pick up a project instantly — same context, same decisions, same history_

---

## 1. Full Trigger Chain (events → DB → files)

```
══ GIT PUSH ════════════════════════════════════════════════════════════════
route_git: POST /git/{project}/commit-push
  └─ _sync_commit_and_link()
       ├─ UPSERT mem_mrr_commits (hash, msg, diff_summary, tags)
       └─ Link to active session prompt (mem_mrr_prompts.session_id)

  └─ [background thread] _extract_commit_code_background()
       ├─ extract_commit_code()                         ← tree-sitter
       │    ├─ INSERT mem_mrr_commits_code  (per symbol: class/method/file)
       │    ├─ Haiku call → llm_summary per symbol      ← commit_symbol prompt
       │    ├─ UPDATE mem_mrr_commits_file_stats        (hotspot_score recompute)
       │    └─ UPDATE mem_mrr_commits_file_coupling     (co-change pairs)
       │
       ├─ _close_items_from_commit()                   ← NEW
       │    regex "fixes/closes BU0012" →
       │    UPDATE mem_work_items SET score_status=5, user_status='review'
       │
       ├─ _post_commit_synthesis()                     ← NEW (Haiku background)
       │    reads last 15 commits as history →
       │    Haiku call → WRITE project_state.json      ← project_synthesis prompt
       │
       └─ MemoryFiles.write_root_files()
            ├─ _load_context()  [DB + PROJECT.md]
            ├─ WRITE: CLAUDE.md, .cursorrules, code.md, GEMINI.md, AGENTS.md
            └─ _embed_code_md() → UPDATE mem_ai_project_facts[code_structure]

══ CLASSIFY (manual or threshold) ═════════════════════════════════════════
POST /wi/{project}/classify
  └─ _ClassifyMixin.classify()
       ├─ DELETE draft rows (wi_id LIKE 'AI%')
       ├─ _fetch_pending_events()  ← all 4 mem_mrr_* sources, single query each
       │    commits: with batch join to commits_code + hotspot_map
       ├─ _group_events()          ← 3000-token batches
       ├─ For each batch:
       │    _load_existing_context() → approved use cases (for dedup)
       │    _classify_group()     ← Haiku call               ← classification prompt
       │    _save_classifications() → INSERT mem_work_items (AI0001…)
       ├─ _update_item_tags()     ← executemany batch
       └─ _rollup_uc_tags()       ← aggregate children tags to use case

══ USER APPROVES DRAFT ════════════════════════════════════════════════════
PUT /wi/{project}/{id}/approve
  └─ MemoryWorkItems.approve()
       ├─ SELECT current row (must be AI* prefix)
       ├─ _generate_wi_id()        → allocate BU0001 / FE0002 / UC0001 etc.
       ├─ UPDATE mem_work_items SET wi_id=new_id, approved_at=NOW()
       ├─ Batch UPDATE mem_mrr_prompts/commits/messages/items  ← no longer pending
       ├─ _embed_work_item()        → embedding stored in mem_work_items.embedding
       └─ If use_case: approve_all_under() + refresh_md()
            └─ WRITE documents/use_cases/{slug}.md

══ POST /memory (manual or stop-hook) ════════════════════════════════════
POST /projects/{project}/memory
  └─ route_projects.generate_memory()
       ├─ _synthesize_with_llm()                        ← project_synthesis prompt
       │    reads last 50 prompts + PROJECT.md + state
       │    Haiku → WRITE project_state.json
       │    → tag_suggestion prompt → suggested phase/feature returned to caller
       ├─ _auto_populate_project_facts()
       │    Haiku extract → batch embed outside DB → INSERT mem_ai_project_facts
       └─ MemoryFiles.write_all_files()
            ├─ All root files + provider files (CLAUDE.md, .cursorrules, code.md…)
            └─ Feature-specific CLAUDE.md files per approved use case

══ SESSION START (hook) ═══════════════════════════════════════════════════
check_session_context.sh → POST /memory/regenerate?scope=root
  └─ MemoryFiles.write_root_files()  [same path as post-commit]
```

---

## 2. LLM Prompts — Complete Inventory

All prompts are in `backend/prompts/*.yaml`, loaded by `core/prompt_loader.py`.
No inline LLM strings in Python.

| # | Key | File | Model | Max Tokens | When Triggered | Input → Output |
|---|-----|------|-------|-----------|----------------|----------------|
| 1 | `project_synthesis` | command_memory.yaml | Haiku | 2000 | POST /memory | 50 history entries + PROJECT.md + state → `project_state.json` |
| 2 | `conflict_detection` | command_memory.yaml | Haiku | 300 | POST /memory → MemoryPromotion | old + new fact value → resolution type + merged value |
| 3 | `tag_suggestion` | misc.yaml | Haiku | 100 | POST /memory | last 5 developer prompts → `{"phase":"…", "feature":"…"}` |
| 4 | `feature_auto_detect` | misc.yaml | Haiku | 60 | POST /chat/hook-log | existing features + new prompt → auto-tag session |
| 5 | `memory_context_compact` | command_memory.yaml | n/a (static) | — | write_all_files() | preamble → prepended to .cursorrules, copilot |
| 6 | `memory_context_full` | command_memory.yaml | n/a (static) | — | write_all_files() | preamble → prepended to CLAUDE.md, GEMINI.md |
| 7 | `memory_context_openai` | command_memory.yaml | n/a (static) | — | write_all_files() | preamble → OpenAI system_prompt.md |
| 8 | `commit_analysis` | event_commit.yaml | Haiku | 800 | POST /git/commit-store | hash + msg + diff → phase/feature tags + summary |
| 9 | `commit_symbol` | event_commit.yaml | Haiku | 120 | extract_commit_code() [background] | per-symbol diff → 1-sentence llm_summary |
| 10 | `commit_message` | event_commit.yaml | Haiku | 80 | POST /git/commit-push | staged diff → commit message string |
| 11 | `react_pipeline_base` | react_base.yaml | n/a (static) | — | agent.py startup | system prompt prefix for all pipeline agents |
| 12 | `react_suffix` | react_base.yaml | n/a (static) | — | agent.run() | shorter ReAct format for non-pipeline mode |
| 13 | _(classify)_ | work_items.yaml | Haiku | 8000 | POST /wi/classify | batched events (3000 tok/batch) → JSON work item array |
| 14 | _(summarise)_ | work_items.yaml | Haiku | 2000 | POST /wi/{id}/summarise | UC name + children → new_summary + reorder |
| 15 | _(reclassify)_ | work_items.yaml | Haiku | 120 | POST /wi/{id}/reclassify | name + summary + status → wi_type + scores |

**Active Haiku call paths**: 7 (synthesis, conflict, tags, feature-detect, commit-analysis, classify, reclassify)
**Post-commit**: `commit_symbol` (per symbol, background) + `project_synthesis` (background)
**Fixed**: `tag_suggestion` was duplicated in command_memory.yaml (stub); stub removed.

---

## 3. Memory Layers

```
Layer 1 — Raw Capture (mem_mrr_*)
├─ mem_mrr_prompts          prompt+response, session_id, tags JSONB
│   Populated by: Claude Code stop hook → POST /chat/hook-log
│   Used by: classify(), project_synthesis(), recent_work section
│
├─ mem_mrr_commits          hash, msg, diff_summary, tags, commit_type
│   Populated by: git post-commit → POST /git/commit-store
│   Used by: classify(), commit_analysis Haiku, code.md recently-changed
│
├─ mem_mrr_commits_code     per-symbol (class/method/file), llm_summary
│   Populated by: extract_commit_code() [background tree-sitter]
│   Used by: code.md recently-changed section, classify context (_hotspot_files)
│
├─ mem_mrr_commits_file_stats   hotspot_score, bug_commit_count per file
│   Populated by: extract_commit_code() [background]
│   Used by: code.md hotspots table, _suggest_hotspot_work_items()
│
├─ mem_mrr_commits_file_coupling   co-change pairs count
│   Populated by: extract_commit_code() [background]
│   Used by: code.md coupling table, _suggest_decouple_work_items()
│
├─ mem_mrr_items            EMPTY in practice — no auto-ingestion path
│   Populated by: manual POST /items only
│   Used by: classify() (included in batch but never has rows)
│
└─ mem_mrr_messages         EMPTY in practice — no auto-ingestion path
    Populated by: manual POST /messages only
    Used by: classify() (included in batch but never has rows)

Layer 2 — Durable Facts (mem_ai_project_facts)
├─ fact_key, fact_value, category (stack/pattern/convention/general/code)
├─ embedding VECTOR(1536)   ← OpenAI text-embedding-3-small
├─ valid_until              ← previous facts soft-deleted on /memory refresh
├─ code_structure fact      ← full code.md snapshot (embedded for semantic search)
│   Populated by: /memory → _auto_populate_project_facts() [batch embed before DB open]
│   Also by: write_root_files() → _embed_code_md() after every commit
│   Used by: MCP search_memory, render_root_claude_md()
│   Index: idx_mem_ai_pf_pid ON (project_id) WHERE valid_until IS NULL ✓

Layer 3 — Work Items (mem_work_items)
├─ Draft items    wi_id='AI0001' → user reviews in UI
├─ Approved items wi_id='BU0001' → embedded + MD file written
├─ Rejected items wi_id='REJxxxxxx' → soft deleted
├─ wi_type: use_case | feature | bug | task | requirement | policy
├─ user_status (TEXT, m079): open | pending | in-progress | review | blocked | done
├─ embedding VECTOR(1536)   ← _embed_work_item() includes AC + deliveries
│   Populated by: classify() → drafts; approve() → real IDs
│   Used by: MCP search_memory, CLAUDE.md Active Features section

Layer 4 — Context Files (workspace/{project}/memory/)
├─ CLAUDE.md          deterministic render from DB + PROJECT.md (no LLM)
├─ .cursorrules       compact variant (~2000 tokens)
├─ code.md            dir tree + recently-changed symbols + hotspots + coupling
├─ project_state.json Haiku synthesis output (key_decisions, tech_stack, in_progress)
└─ documents/use_cases/{slug}.md   per-approved use_case MD file
    Triggered by: every commit (root files) | /memory (all files) | session start (root)
```

---

## 4. Component Analysis

### 4A. code.md — Well-triggered and complete?

**Content**: ASCII dir tree (depth 3) + recently-changed symbols (last 20 unique) + hotspot files (score/commits/lines/bugs) + coupling pairs.

**Trigger chain**:
```
git push → extract_commit_code() [background]
  → mem_mrr_commits_code + file_stats updated
  → write_root_files() → code.md written
  → _embed_code_md() → mem_ai_project_facts[code_structure] embedded
Session start hook → POST /memory/regenerate?scope=root → write_root_files()
POST /memory → write_all_files() → same path
```

**Status**: ✓ Well-triggered. code.md is always current after commit AND embedded for semantic search (`search_memory("code structure")` retrieves it).

**Gap**: code.md shows *recently-changed* symbols only — not the full public API surface. An LLM reading it knows what's changing, not everything that exists.

**Embedding strategy**: Re-embedding the full code.md on every commit (not per-symbol) is the right call — one searchable "code map" chunk is better than thousands of fragmented rows. Symbol-level data stays in `mem_mrr_commits_code` for classification context.

### 4B. PROJECT.md — Well-maintained?

**Content**: Vision + Core Goals (user-managed) + Conventions + Recent Work + Key Decisions (auto-updated by /memory) + `## Deprecated` section.

**`## Deprecated` mechanism**: phrases under this section are filtered from `key_decisions` in both CLAUDE.md and .cursorrules renderers. Instant suppression without needing `/memory` run.

**Post-commit synthesis** (NEW): `_post_commit_synthesis()` runs Haiku in background after every commit → `project_state.json` stays ≤1 commit stale without manual `/memory`.

**Status**: ✓ Three-layer stale-prevention: `## Deprecated` filter + `project_synthesis` "PROJECT.md is authoritative" instruction + post-commit background synthesis.

**Gap**: Key Decisions come from Haiku synthesis over *prompts* — not direct code reading. Architecture changes only in code (no prompt discussion) won't appear.

### 4C. Project Facts (`mem_ai_project_facts`) — Updated? Non-duplicate?

**Upsert strategy**: `valid_until=NOW()` marks old facts stale before inserting new per category. Key normalization (snake_case) prevents exact duplicates.

**Status**: ✓ Facts stay current after every commit (via post-commit synthesis) and after every `/memory` run. `code_structure` fact stores full code.md for MCP search.

**Concern**: facts are sparse in practice — the primary LLM context comes from `project_state.json`, not this table. Facts are most useful for MCP semantic search (`search_memory("auth approach")`).

### 4D. Approved Work Items — Well-used?

**In CLAUDE.md**: Top 12 approved (non-done), bug-type first. In-progress items with due dates. Acceptance criteria for use_cases.

**Embedding**: includes name + wi_type + summary + deliveries + delivery_type + acceptance_criteria. Re-embedded on `approve()` and `update()` when semantic fields change.

**Commit auto-close** (NEW): `_close_items_from_commit()` — regex parses "fixes/closes/resolves BU0012" from commit message → `score_status=5, score_importance=5, user_status='review'`. Item surfaces prominently in UI for one-click approve.

**Status**: ✓ Well-used. Both human-readable CLAUDE.md and semantic search are populated.

### 4E. Unapproved/Draft Work Items — Considered?

**Current state**: Draft items (wi_id LIKE 'AI%') are NOT shown in CLAUDE.md or embedded — by design. They're user-replaceable noise before approval. The classify() run purges all drafts before regenerating, so CLAUDE.md is never polluted.

**Status**: ✓ Correct behavior (confirmed with user). Draft items are only visible in the Work Items UI.

### 4F. Architectural Overrides — Old decisions replaced?

Three mechanisms working together:
1. `## Deprecated` in PROJECT.md → phrase-filter in renderers (instant)
2. `project_synthesis` Haiku prompt: "PROJECT.md is authoritative — replace stale decisions"
3. `_post_commit_synthesis()` re-runs synthesis after every commit

**Status**: ✓ Solid. No manual `/memory` run needed to suppress stale architecture.

### 4G. CLAUDE.md — Complete and current?

All sections rendered deterministically from DB (no LLM at render time):
- Key Architectural Decisions ← `project_state.json` (now ≤1 commit stale ✓)
- Project Documentation ← PROJECT.md Vision + Core Goals
- Code Hotspots ← `mem_mrr_commits_file_stats` (score ≥ threshold)
- Recently Changed Symbols ← `mem_mrr_commits_code` (last 20 unique)
- Active Features/Work Items ← `mem_work_items` (approved only, bug-first)
- In-Progress Items with due dates
- Coding Conventions ← PROJECT.md `## Conventions`
- Tech Stack ← `project_state.json`

**Status**: ✓ Well-structured. Token-budget rolloff (oldest symbols drop first).

---

## 5. Work Item Flows

### Classification
```
Events in mem_mrr_* (wi_id IS NULL)
  → manual POST /wi/classify  OR  auto threshold-trigger from route_git/route_chat
  → DELETE all AI* draft rows
  → _fetch_pending_events():
       prompts:  up to 200 rows, last 90 days
       commits:  up to 100 rows + batch-joined commits_code symbols + hotspot_map
       messages: up to 50 rows  (EMPTY — no ingestion path)
       items:    up to 50 rows  (EMPTY — no ingestion path)
  → _group_events(): sort chronologically, batch to 3000 tokens
  → For each batch: Haiku classify → draft mem_work_items
  → executemany batch-update item tags
```

### Approve Chain
```
User approves draft in UI
  → assign real wi_id (BU/FE/UC/TA prefix)
  → batch UPDATE mem_mrr_* WHERE id = ANY(...) [no N+1 ✓]
  → _embed_work_item() → VECTOR(1536)
  → WRITE documents/use_cases/{slug}.md
  → write_root_files() → CLAUDE.md refreshed
```

### Score System
| Field | Set By | Meaning |
|---|---|---|
| `score_importance` | Haiku at classify time (1-5) | How important |
| `score_status` | Haiku at classify time (1=not started, 5=done) | LLM-estimated progress |
| `user_status` | User in UI (authoritative) | `open/pending/in-progress/review/blocked/done` |

`user_status` is the source of truth for CLAUDE.md and MCP. `score_status` is supplementary.

### Code Events → Classification Context
Each commit in `_fetch_pending_events()` is enriched with:
- `_hotspot_files`: files touched by this commit + their hotspot scores (batch-joined)
- `_symbol_summaries`: per-symbol LLM summaries from `mem_mrr_commits_code` (batch-joined)

This gives Haiku awareness of *what* changed and *where* — enabling smarter classification.

---

## 6. Embedding / MCP Strategy

### What Is Embedded

| Data | When | Table | Searched Via |
|---|---|---|---|
| Approved work items | approve() + re-embed on update | `mem_work_items.embedding` | MCP `search_memory` + `/search/semantic` |
| code.md snapshot | write_root_files() after every commit + /memory | `mem_ai_project_facts[code_structure]` | MCP `search_memory("code structure")` |
| Project facts | POST /memory → batch outside DB conn | `mem_ai_project_facts` | MCP `search_memory(category)` |

**Not embedded** (correct): raw prompts/commits (noisy), per-symbol diffs (code.md covers this), draft items.

**Embedding strategy**: Re-embedding the full code.md (one chunk) after every commit is correct. Per-symbol embedding would use far more tokens for worse retrieval (fragmented context). An LLM querying `search_memory("router layer")` gets the full code map in one hit.

### MCP Tools (15 active)

| Tool | Purpose | Useful? |
|---|---|---|
| `search_memory` | Parallel search work items + code_structure + facts | ✓ Core tool |
| `get_project_state` | Tech stack, key decisions, in-progress | ✓ Core tool |
| `list_work_items` | Filter by type/status/`due_date_before` | ✓ Core tool |
| `get_commits` | Recent commits with tags | ✓ |
| `get_tagged_context` | All events for a phase or feature | ✓ |
| `get_session_tags` / `set_session_tags` | Phase/feature tracking | ✓ |
| `get_item_by_number` | Full detail for one item (BU0001) | ✓ |
| `create_entity` | Create unapproved work item | ✓ |
| `run_work_item_pipeline` | Haiku 4-agent summary | ✓ |
| `get_hotspots` | Direct file churn query | ✓ |
| `get_file_history` | Per-file symbol changes | ✓ |
| `commit_push` | Cursor session commits | ✓ |
| `get_db_schema` | Schema reference (static) | ✓ |
| `get_roles` | Agent role definitions | ✓ |
| `get_recent_history` | Last N prompts with filter | ✓ |

### MCP Capability Matrix (can it answer project questions?)

| Question | Tool | Works? |
|---|---|---|
| What are the open bugs? | `list_work_items(category=bug, status=open)` | ✓ |
| What is the tech stack? | `get_project_state` | ✓ |
| What are the coding conventions? | `search_memory("conventions")` | ✓ via facts |
| What is the code structure? | `search_memory("code structure")` | ✓ via code.md embed |
| What files are hotspots? | `get_hotspots` | ✓ direct |
| What changed recently? | `get_commits` | ✓ |
| What items are overdue? | `list_work_items(due_date_before="today")` | ✓ |
| What are the main use cases? | `list_work_items(category=use_case)` | ✓ |
| Class naming policy / prefix rules? | `search_memory("naming convention")` | ⚠ only if in PROJECT.md/facts |
| Number of open bugs? | `list_work_items(category=bug)` → count | ✓ |
| Which commits fixed BU0012? | — | ✗ no commit→item lookup tool |
| Full public API surface? | — | ✗ code.md shows recent changes only |

---

## 7. Code Quality Summary (All Recent Fixes)

### Fixes Applied Across This Session

| Fix | File | Before → After |
|---|---|---|
| 4 unbounded recursive CTEs | `_wi_markdown.py` (3), `memory_work_items.py` (1) | No depth → `AND d.depth < 20` |
| N+1 UPDATE in approve/reject | `memory_work_items.py` | Per-row loops → batch `ANY(%s::uuid[])` |
| N+1 hotspot existence checks | `memory_files.py` | Per-file SELECT → batch `WHERE name = ANY(%s)` |
| N+1 `_update_item_tags` | `_wi_helpers.py` | Per-item execute → `executemany` |
| N+1 sync_missing_commits | `route_git.py` | Per-commit SELECT → batch `WHERE commit_hash = ANY(%s)` |
| Token counting | `_wi_helpers.py` | `word_count × 1.3` → `len(text) // 4` |
| `_load_context()` god function | `memory_files.py` | Split into `_query_db_into_ctx()` + `_parse_project_md()`; PROJECT.md read once (was twice) |
| Fragile MD parser | `_wi_markdown.py` | Compiled `_ITEM_HEADER_RE` accepts `—`, `–`; `###` also breaks section |
| Date cascade extraction | `memory_work_items.py` | Inline if-chains → `_apply_date_rules()` helper |
| MCP search URL | `server.py` | String `f"/search/facts?query={quote(...)}"` → params dict |
| MCP timeouts hardcoded | `server.py` | 30/60s → env vars `MCP_TIMEOUT_GET` / `MCP_TIMEOUT_POST` |
| Commit auto-close | `route_git.py` | New `_close_items_from_commit()` |
| Post-commit synthesis | `route_git.py` | New `_post_commit_synthesis()` |
| `## Deprecated` suppression | `memory_files.py` | Phrase-filter in CLAUDE.md + cursorrules renderers |
| `due_date_before` MCP filter | `server.py` | Added to `list_work_items` tool |
| Duplicate `tag_suggestion` key | `command_memory.yaml` | Stub removed; `misc.yaml` is canonical |
| Orphaned `_apply_creds_to_remote` | `route_git.py` | Deleted (never called) |
| Silent embed failures | `_wi_helpers.py`, `memory_work_items.py` | `log.debug` → `log.warning` |

---

## 8. What Is Missing (Major Gaps Only)

| # | Gap | Layer | Impact |
|---|---|---|---|
| 1 | `mem_mrr_items` and `mem_mrr_messages` never populated — classify has no meeting-note or Slack context | Layer 1 | Medium — non-code decisions invisible to LLM |
| 2 | No commit→item lookup in MCP — "which commits fixed BU0012?" not answerable | MCP | Low — use `get_commits` + manual filter |
| 3 | code.md shows recent-change symbols only — full public API surface not visible | Layer 4 | Low — intentional for token budget |
| 4 | Classification is manual only — no real-time trigger after commit stores events | Layer 3 | Medium — draft items lag behind reality |
| 5 | `_rollup_uc_tags()` in `_wi_helpers.py` loops over uc_ids with per-UC SELECT+UPDATE | Code | Low — use case count is small in practice |

---

## 9. Major Improvements Per Section

### Memory Files
| Action | Impact |
|---|---|
| Add `## Overdue` section to CLAUDE.md renderer (`due_date < today AND user_status != 'done'`) | LLM immediately aware of missed deadlines |
| Populate `mem_mrr_items` via GitHub Issues webhook → classify pipeline | Non-code decisions (bugs, feature requests) enter the memory layer automatically |

### Work Item Flows
| Action | Impact |
|---|---|
| Surface unprocessed event count in CLAUDE.md ("23 unclassified events — run /classify") | LLM and user know when classification is overdue |
| Add `parent_name` to `list_work_items` MCP response | LLM understands hierarchy without extra API calls |
| Auto-trigger classify after N new commits (not just token threshold) | Draft items stay current without manual trigger |

### MCP / Embedding
| Action | Impact |
|---|---|
| Add `get_commits_for_item` tool: `GET /git/{p}/commits?wi_id=BU0012` | Closes "which commits fixed this bug?" gap |
| Split `server.py:_dispatch()` into tool handler modules (`tools/search.py`, `tools/work_items.py`) | 854-line file is too large; split improves testability |
| Implement GitHub Issues → `mem_mrr_items` webhook (1 route + 10 lines) | Closes the biggest Layer 1 gap with minimal effort |
