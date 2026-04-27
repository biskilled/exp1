# aicli Memory System — System Audit
_Last updated: 2026-04-27 | Goal: any LLM can pick up a project instantly — same context, same decisions, same history_

---

## 1. Full Trigger Chain

```
══ GIT COMMIT PUSHED ════════════════════════════════════════════════════
route_git: POST /git/{project}/commit-push
  └─ _sync_commit_and_link()
       ├─ UPSERT mem_mrr_commits (hash, msg, diff_summary, tags)
       └─ Link to active session prompt (mem_mrr_prompts.session_id)

  └─ [background] _extract_commit_code_background()
       ├─ memory_code_parser.extract_commit_code()           ← tree-sitter
       │    ├─ INSERT mem_mrr_commits_code  (per symbol: class/method/file)
       │    ├─ Haiku call [commit_symbol, 100→120 tok]       ← 1-sentence llm_summary
       │    ├─ UPSERT mem_mrr_commits_file_stats             (hotspot_score recompute)
       │    └─ UPSERT mem_mrr_commits_file_coupling          (co-change pairs)
       │
       ├─ _close_items_from_commit()
       │    regex "fixes/closes BU0001" →
       │    UPDATE mem_work_items SET score_status=5, user_status='review'
       │
       ├─ _post_commit_synthesis()                           ← Haiku background
       │    last 15 commits + PROJECT.md →
       │    Haiku call [project_synthesis, 2000→2000 tok] →
       │    WRITE workspace/{p}/state/project_state.json
       │
       └─ memory_files.write_code_md()
            ├─ Load hotspots + coupling + recent symbols from DB
            ├─ WRITE workspace/{p}/memory/code.md
            └─ _embed_code_md() → UPSERT mem_ai_project_facts[code_structure]

══ CLASSIFY (POST /wi/{project}/classify) ══════════════════════════════
_wi_classify.classify()
  ├─ DELETE draft rows (wi_id LIKE 'AI%')
  ├─ _fetch_pending_events()  ← single query per source table
  │    mem_mrr_prompts (≤200), mem_mrr_commits (≤100),
  │    mem_mrr_messages (≤50), mem_mrr_items (≤50)
  │    + JOIN mem_mrr_commits_code for symbols
  │    + JOIN mem_mrr_commits_file_stats for hotspot context
  │
  ├─ _group_events()          ← token-bounded batches (~3000 tok each)
  │
  └─ For each batch:
       ├─ _load_existing_context() → approved use cases (dedup guard)
       ├─ Haiku call [classification, 3000→4000 tok] → JSON array
       ├─ _save_classifications() → INSERT mem_work_items (AI0001…)
       │    Phase 1: use_cases first (to get UUIDs)
       │    Phase 2: children with wi_parent_id
       ├─ _update_item_tags() → executemany batch JSONB merge
       └─ _rollup_uc_tags()   → aggregate child tags → parent UC

══ USER APPROVES DRAFT (PUT /wi/{project}/{id}/approve) ════════════════
memory_work_items.approve()
  ├─ SELECT current row (must be wi_id LIKE 'AI%')
  ├─ _generate_wi_id() → allocate BU0001 / FE0002 / UC0001 via pr_seq_counters
  ├─ UPDATE mem_work_items SET wi_id=new_id, approved_at=NOW()
  ├─ Batch UPDATE mem_mrr_prompts/commits/messages/items (ANY[] array)
  ├─ _embed_work_item() → UPDATE mem_work_items.embedding (1536-dim)
  └─ If use_case:
       ├─ approve_all_under() → recurse approve children (depth < 20 CTE)
       └─ refresh_md() → WRITE documents/use_cases/{slug}.md

══ POST /memory (manual or stop-hook) ══════════════════════════════════
route_projects.generate_memory()
  ├─ _synthesize_with_llm()
  │    last 50 prompts + PROJECT.md (600 chars) →
  │    Haiku [project_synthesis] → WRITE project_state.json
  │    + Haiku [tag_suggestion, 200→100 tok] → suggested phase/feature tags
  │
  ├─ _auto_populate_project_facts()                 ← sparse, manual extraction
  │    Haiku extract → batch embed → INSERT mem_ai_project_facts
  │
  └─ memory_files.write_all_files()
       ├─ _load_context()  ← single DB connection, 7 queries
       │    facts, active items, in-progress, recently changed symbols,
       │    hotspots, coupling pairs, PROJECT.md (read once)
       ├─ _write_root_files_with_ctx()
       │    WRITE: CLAUDE.md, .cursorrules, code.md, GEMINI.md, AGENTS.md
       │    Token-limited: rolloff oldest "recently changed" first
       ├─ _embed_code_md() → UPSERT mem_ai_project_facts[code_structure]
       ├─ _suggest_hotspot_work_items() → INSERT refactor/decouple tasks
       └─ write_feature_files() → WRITE memory/claude/features/{tag}/CLAUDE.md

══ SESSION START HOOK ══════════════════════════════════════════════════
check_session_context.sh → POST /memory/regenerate?scope=root
  └─ memory_files.write_root_files()
       Reuses cached project_state.json (no LLM call if fresh)
       WRITE: CLAUDE.md + .cursorrules to code_dir
       (Same path as /memory but only root files, no feature files)

══ USER UPDATES WORK ITEM (PUT /wi/{project}/{id}) ═════════════════════
memory_work_items.update()
  ├─ Load current (wi_type, parent_id, current_due_date)
  ├─ _apply_date_rules() → validate + cascade
  │    date change: auto-set start_date = today
  │    child due_date > parent's: return error
  │    re-parent to UC: validate existing due_date vs new UC due_date   ← NEW
  │    re-parent to non-UC: child.start_date = parent.due_date (sequential)
  ├─ UPDATE mem_work_items with new values
  ├─ If UC due_date changed: cascade UPDATE to children
  └─ If semantic fields changed (name/summary/deliveries/delivery_type):
       _embed_work_item() → UPDATE embedding
       ⚠ Gap: acceptance_criteria + implementation_plan changes
         do NOT trigger re-embed
```

---

## 2. LLM Prompts — Complete Inventory

| # | Key | File | Model | Trigger | Input → Output | Tok In/Out | Status |
|---|-----|------|-------|---------|----------------|------------|--------|
| 1 | `classification` | command_work_items.yaml | Haiku | POST /wi/classify (per batch) | events_block + existing_ctx → JSON array of items | 3000 → 4000 | ✓ Active |
| 2 | `summarise` | command_work_items.yaml | Haiku | PUT /wi/{id}/ai-summarise (optional) | UC + children → rewritten summary + reordered items | 2000 → 500 | ✓ Active |
| 3 | `project_synthesis` | command_memory.yaml | Haiku | /memory + post-commit synthesis | history + PROJECT.md → key_decisions, tech_stack, in_progress | 2000 → 2000 | ✓ Active |
| 4 | `conflict_detection` | conflict_detection.yaml | Haiku | memory_promotion.detect_fact_conflicts() | old_value vs new_value → supersede\|merge\|flag | 300 → 300 | ⚠ Dormant |
| 5 | `commit_symbol` | commit.yaml | Haiku | extract_commit_code() per symbol | symbol diff → 1-sentence summary | 100 → 120 | ✓ Active |
| 6 | `commit_analysis` | commit.yaml | Sonnet | — | git diff → JSON analysis | 500 → 800 | ✗ Unused |
| 7 | `commit_message` | commit.yaml | Haiku | — | changed files + diff → commit message | 100 → 80 | ✗ Unused |
| 8 | `tag_suggestion` | misc.yaml | Haiku | /memory (after project_synthesis) | last 5 prompts → {phase, feature} | 200 → 100 | ✓ Active |
| 9 | `react_pipeline_base` | react_base.yaml | — | Prepended to all pipeline agents | (system rules) | N/A | ✓ Active |
| 10 | `react_suffix` | react_base.yaml | — | Non-pipeline run() mode | (ReAct format) | N/A | ✓ Active |
| 11-N | work_items.yaml keys | work_items.yaml | Haiku | Pipeline work item agents | AC + plan generation | varies | ✓ Active |

**Notes**:
- `commit_analysis` (Sonnet): Defined in commit.yaml but no caller found in route_git.py. Leftover from earlier design. Safe to delete the key.
- `commit_message`: Defined but no caller. The git push route generates messages via LLM in route_git.py using a different code path — verify it actually uses this key or has its own prompt.
- `conflict_detection`: Only runs when `detect_fact_conflicts()` is called, which requires a manually-triggered fact extraction. Since facts are sparse, this never fires in practice.

---

## 3. Memory Layers

```
Layer 1 — Raw Capture (mem_mrr_*)        ← high volume, append-only
  mem_mrr_prompts        Claude Code hook log + /chat (session-tagged)
  mem_mrr_commits        git commits (hash, msg, diff_summary, tags)
  mem_mrr_commits_code   per-symbol diffs (tree-sitter: class, method, file)
  mem_mrr_commits_file_stats   hotspot_score = commit_count + 2 (if ≥800 lines)
  mem_mrr_commits_file_coupling    co-change pairs (co_change_count per pair)
  mem_mrr_items          [EMPTY] manual API only — no integrations
  mem_mrr_messages       [EMPTY] manual API only — no integrations

Layer 2 — Durable Facts (mem_ai_project_facts)    ← sparse
  fact_key, fact_value, embedding VECTOR(1536)
  code_structure = embedded code.md (first 8000 chars) — auto-updated
  All other keys = manual extraction only — NOT auto-updated
  Conflict detection: dormant (detect_fact_conflicts never fires in practice)

Layer 3 — Work Items (mem_work_items)    ← user-reviewed backlog
  Draft:    wi_id='AI0001' (pending user review, NOT in context files)
  Approved: wi_id='BU0001' (embedded, appears in CLAUDE.md + code.md)
  Rejected: wi_id='REJxxxxxx' (soft-deleted from view)
  Embedding: name + wi_type + summary + deliveries + delivery_type + AC

Layer 4 — Context Files                  ← LLM-readable, generated
  workspace/{p}/memory/claude/CLAUDE.md      ← Claude Code primary context
  workspace/{p}/memory/cursor/rules.md       ← Cursor
  workspace/{p}/memory/code.md               ← codebase structure
  workspace/{p}/state/project_state.json     ← key_decisions, tech_stack
  workspace/{p}/documents/use_cases/*.md     ← per-UC markdown (user-editable)
  workspace/{p}/memory/claude/features/*/CLAUDE.md  ← per-feature context
```

---

## 4. Component Analysis

### 4A. code.md
**What goes in**: directory tree (depth 3) + hotspot files (score ≥ threshold) + coupling pairs (co-change ≥ 3) + recently changed symbols (class/method with llm_summary) + active approved work items.

**Triggered**: Post-commit (write_code_md) + every /memory call. ✓ Well-timed.

**Embedded**: Yes — as `mem_ai_project_facts[code_structure]` (first 8000 chars, 1536-dim). MCP `search_memory` can find it.

**What's missing**:
- No test file detection (test files mix with prod in hotspots)
- No per-symbol embedding (only whole-file code.md; can't search "find the auth class")
- No public API surface documented (routes, endpoints not listed)

---

### 4B. PROJECT.md (user-managed)
**How used**: Read once per /memory call by `_parse_project_md()`. Extracts:
- Vision + Core Goals → `project_summary` (rendered in CLAUDE.md)
- Conventions section → `conventions` block (rendered in CLAUDE.md)
- `## Deprecated` section → phrases filtered from key_decisions (prevent stale facts surfacing)

**In synthesis**: Only first 600 chars passed to `project_synthesis` prompt as `{proj_intro}`. Large PROJECT.md files are silently truncated.

**As authoritative truth**: project_synthesis prompt treats PROJECT.md as override — stale key_decisions conflicting with it are replaced on next /memory run.

**Weaknesses**:
- No schema: arbitrary sections; only Vision/Goals/Conventions/Deprecated are parsed
- No versioning: no audit trail of when decisions changed
- 600-char truncation: long PROJECT.md files partially silenced in synthesis
- No auto-fact-extraction from its sections (tech_stack, coding style sit unused unless user manually extracts)

---

### 4C. Project Facts (mem_ai_project_facts)
**Population**:
- `code_structure`: auto-updated on every /memory + post-commit ✓
- Everything else: manual via `_auto_populate_project_facts()` — rarely called, sparse in practice

**Conflict detection**: `detect_fact_conflicts()` compares new vs existing fact values. If conflict, calls `conflict_detection` prompt (Haiku) → supersede/merge/flag. **Never fires automatically** — only if new fact inserted manually.

**Staleness**: Facts have `valid_until` (soft expiry). Old `code_structure` fact superseded on each update. Other facts never superseded automatically.

**Gap**: System relies on user populating facts. In practice, only `code_structure` is live. Everything else is effectively empty.

---

### 4D. Approved Work Items
**In context files**:
- `CLAUDE.md`: up to 12 active items, sorted by score_importance DESC
- `code.md`: all active approved items
- `.cursorrules`: compact list (up to 5)

**Embedded**: Yes, on approval. Re-embedded if name/summary/deliveries/delivery_type change.

**Gap**: `acceptance_criteria` + `implementation_plan` (added by pipeline) do NOT trigger re-embed. Semantic search won't find items by their AC content unless name/summary also changed.

---

### 4E. Unapproved/Draft Work Items (wi_id LIKE 'AI%')
**Not in any context file** — invisible to LLMs until user approves.

This is by design (drafts are noisy) but means new requirements pending review are invisible to Claude Code.

**Re-classification**: Manual only (unless `mode=threshold` in project.yaml). If 10 commits come in while 5 pending items sit in draft, the new commits won't be linked to existing drafts — they'll create new items on next classify run.

---

### 4F. How New Requirements Override Old
When project changes (e.g., "drop JSON files, use PostgreSQL"):

1. Developer updates PROJECT.md to reflect new architecture
2. Next /memory call → `_parse_project_md()` reads updated PROJECT.md
3. `project_synthesis` Haiku treats PROJECT.md as truth → old key_decisions about JSON files replaced
4. New CLAUDE.md written with updated architecture

**Not detected automatically**:
- `mem_ai_project_facts` still has old "uses JSON files" fact until manually superseded
- Old work items referencing JSON storage remain approved (score_status not reset)
- No "architectural drift" detection — gap between code reality and PROJECT.md is invisible

---

## 5. Work Item Flows

### 5A. Classification Quality
**Event sources used**:
- Prompts: ✓ (session-tagged, 90-day horizon)
- Commits: ✓ (with symbol summaries + hotspot context attached)
- Messages: ⚠ (queried but table empty — no integrations)
- Items: ⚠ (queried but table empty — no integrations)

**Commit enrichment**: For each commit, classifier sees:
```
[CHANGED SYMBOLS] auth.py::LoginView::post — Added JWT token refresh logic
[FILE HOTSPOTS]   auth.py  score=12  commits=8  bug_commits=3  lines=890
```
This is good — classification understands WHAT changed and HOW HOT the file is.

**Score system**:
- `score_importance` (0-5): used to sort items in CLAUDE.md (DESC) ✓
- `score_status` (0-5): used in markdown status label (requirement/in_progress/done) ✓
- `score_importance=5 + score_status=5` set by commit auto-close → surfaces to top for review ✓

**Tag propagation**: Child tags rolled up to parent UC via `_rollup_uc_tags()` ✓

### 5B. Commit → Work Item Auto-Close
Pattern: `r'\b(?:fix(?:es|ed)?|clos(?:e|es|ed)|resolv(?:e|es|ed))\s+([A-Z]{2}\d{4})\b'`

Matches: "fixes BU0001", "closes FE0023", "resolved TA0012"

Sets: `score_status=5`, `score_importance=5`, `user_status='review'` (not 'done' — requires user confirm)

**Limitations**: Requires exact 4-digit format (BU0001). "fixes BU1" or "closes bug-123" won't match.

### 5C. Re-embedding on Update
Triggered by: name, summary, deliveries, delivery_type changes.

**Gap**: `acceptance_criteria`, `implementation_plan` changes (added by 4-agent pipeline) do NOT trigger re-embed. Items found by semantic search may lag behind their actual AC content.

---

## 6. Embedding & MCP Strategy

### 6A. What Is Embedded

| Entity | Table | When | Text |
|--------|-------|------|------|
| Approved work items | `mem_work_items.embedding` | On approval + semantic field update | name + wi_type + summary + deliveries + delivery_type + AC |
| code.md | `mem_ai_project_facts[code_structure]` | Post-commit + /memory | First 8000 chars of code.md |
| Other project facts | `mem_ai_project_facts.embedding` | Manual extraction only | fact_value |
| Commits | NOT embedded | — | — |
| Prompts | NOT embedded | — | — |

**code.md strategy**: Embedding the whole file is pragmatic. Fine-grained per-symbol embeddings would allow queries like "find the auth class" but at the cost of hundreds of rows and complex update logic. Whole-file is better for now.

### 6B. MCP Can Answer

| Question | Tool | Complete? |
|----------|------|-----------|
| "Open bugs?" | `list_work_items(category=bug, status=active)` | ✓ Yes |
| "Code style policy?" | `search_memory("code style conventions")` | ✓ If in PROJECT.md |
| "Biggest files / hotspots?" | `search_memory("hotspot")` → finds code_structure fact | ✓ Indirect |
| "Last 5 commits?" | `get_commits(limit=5)` | ✓ Yes (message + tags, no diff) |
| "Current architecture?" | `get_project_state` → key_decisions | ✓ Yes |
| "What's in-progress?" | `get_project_state` OR `list_work_items(status=in-progress)` | ✓ Redundant in 2 tools |
| "Project conventions / prefixes?" | `search_memory("conventions")` | ⚠ Only if in facts |
| "Number of bugs?" | `list_work_items` → count | ✓ Via client-side count |

### 6C. MCP Tools — Gaps
- No `get_codebase_structure` tool (returns file tree + hotspots directly)
- No `get_architectural_decisions` tool (returns key_decisions without full state)
- `search_memory` + any work item search could be unified with `type=` filter
- `get_project_state` + `list_work_items` return overlapping in-progress data

---

## 7. What's Missing (Top Gaps)

| # | Gap | Impact | Fix |
|---|-----|--------|-----|
| 1 | **AC/plan don't trigger re-embed** — pipeline output invisible to semantic search | Medium | Add `acceptance_criteria`, `implementation_plan` to `_embed_fields` in `update()` |
| 2 | **mem_mrr_items + mem_mrr_messages always empty** — classify processes 0 rows for 2 of 4 sources | Medium | Implement GitHub Issues → mem_mrr_items sync (one API call, huge value) |
| 3 | **project_facts auto-extraction absent** — only `code_structure` is live; conflict detection dormant | Medium | Auto-extract facts from PROJECT.md sections (Vision, Core Goals, Conventions) on each /memory run |
| 4 | **Architectural drift undetected** — if code changes without PROJECT.md update, memory stays stale | Medium | Add git-diff-driven PROJECT.md suggestion: "you changed 3 architecture files, update PROJECT.md?" |
| 5 | **Draft items invisible to LLMs** — new requirements sit in AI* state, not surfaced in any context file | Low | Optional `include_pending_items` section in CLAUDE.md (count + brief list) |
| 6 | **commit_analysis + commit_message prompts unused** — dead YAML keys | Low | Delete `commit_analysis` key; verify `commit_message` caller or delete |
| 7 | **PROJECT.md truncated at 600 chars in synthesis** — large docs silently clipped | Low | Increase limit or pass section-by-section |

---

## 8. Major Improvements Per Section

### Memory Files (memory_files.py)
1. **Extend `_embed_fields`** to include `acceptance_criteria` + `implementation_plan` in `update()` — one-line fix, high semantic search impact
2. **Auto-extract project facts from PROJECT.md** in `generate_memory()`: parse Vision → fact `project_vision`, Core Goals → `project_goals`, Conventions → `code_conventions`. These rarely change and would make MCP policy queries much more useful.

### Work Item Flows (_wi_classify.py, memory_work_items.py)
1. **GitHub Issues → mem_mrr_items**: One `GET /repos/{owner}/{repo}/issues` sync populates the currently-empty `mem_mrr_items` table. Classification immediately uses it — no code changes needed in classify().
2. **Extend auto-close regex** to support flexible formats: "fixes BU1" (variable-length ID), "closes #BU0001" (with hash) — minor regex change, big usability win.

### Embedding / MCP (server.py)
1. **Add `get_codebase_structure` MCP tool**: returns file tree + top 5 hotspots + top 5 coupling pairs directly. Answers "how is the project structured?" without needing semantic search.
2. **Add `get_conventions` MCP tool**: reads PROJECT.md Conventions section + `code_conventions` fact directly. Answers "what are the naming/coding rules?" precisely.
3. **Delete unused commit_analysis key** from commit.yaml — reduces confusion in prompt_loader.

### Project Facts (memory_promotion.py)
1. **Auto-trigger fact extraction** from key_decisions in `project_synthesis` output — each key_decision can be stored as a fact with category="architecture". Conflict detection fires automatically when the same decision appears with a new value. Currently the whole conflict detection pipeline is built but never auto-invoked.

---

_End of audit. Backend starts cleanly; all 11 roles + 8 pipelines load from YAML._
