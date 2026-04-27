# aicli Memory System Audit
_Last updated: 2026-04-27 | Goal: shared LLM memory layer — any LLM can pick up context instantly_

---

## 1. Memory Files — Do LLMs get real, current project understanding?

### code.md

| Item | State |
|------|-------|
| Triggered on commit push | ✓ Background after every git push |
| Triggered on `/memory` POST | ✓ Explicit call |
| Triggered on session start | ✗ Only `write_root_files()` runs (CLAUDE.md / .cursorrules) — `code.md` NOT refreshed |
| Dir tree structure | ✓ Depth-3 ASCII tree with `_TREE_SKIP` filter |
| Recently Changed symbols | ✓ Last 20 symbols (class/method/file level) |
| Code hotspots table | ✓ score, commits, lines, bug_fixes, last_changed |
| Active work items + AC | ✓ Shown for use_cases; implementation_plan for in-progress |
| Coding conventions | ✓ From `## Conventions` in PROJECT.md |
| **GAP: stale between commits** | Mid-session code changes (not yet committed) are invisible to code.md |
| **GAP: missing role/architecture narrative** | Describes what changed, not how the system is structured conceptually |

### PROJECT.md

| Item | State |
|------|-------|
| Vision + Core Goals | ✓ User-managed, shown in CLAUDE.md project summary |
| Conventions section | ✓ Feeds code.md + cursorrules |
| Auto-updated: Recent Work / Key Decisions | ✓ Haiku synthesis on each `/memory` run |
| Path fixed | ✓ `workspace/{p}/memory/PROJECT.md` (was wrong in previous version) |
| **GAP: architectural overrides not tracked** | If "we switched from JSONL to DB", old layer descriptions persist until user manually rewrites Vision section |
| **GAP: key_decisions capped at 15** | Old decisions stay in the list — no pruning of superseded decisions |
| **GAP: no staleness warning** | CLAUDE.md shows "last updated" but doesn't flag stale PROJECT.md (e.g. 30+ days) |

### project_state.json (tech_stack, key_decisions)

| Item | State |
|------|-------|
| Replaced on each `/memory` run | ✓ Full rewrite from Haiku synthesis |
| Feeds CLAUDE.md directly | ✓ |
| **GAP: no delta between runs** | Can't tell what changed since last synthesis — no history of decisions |

### project_facts (`mem_ai_project_facts`)

| Item | State |
|------|-------|
| Auto-populated on `/memory` | ✓ 5-10 Haiku-extracted facts (stack/pattern/convention/constraint) |
| Stale facts expired before insert | ✓ `valid_until = NOW()` for non-code category |
| Embed batch fix | ✓ All facts embedded BEFORE DB connection opens (fixed this session) |
| Key normalization | ✓ Snake_case + lowercase dedup |
| **GAP: facts extracted from PROJECT.md, not from live code** | If codebase changed but PROJECT.md not updated, facts are stale |
| **GAP: no contradiction detection across runs** | "uses_database=PostgreSQL" + "uses_database=SQLite" can both exist in different fact rows if keys differ slightly |
| **GAP: category=code only from code.md embed** | No structured "architecture fact" (e.g. layer count) auto-extracted |

### Approved work items in CLAUDE.md

| Item | State |
|------|-------|
| Top 12 non-done items (bug-first) | ✓ Shown in CLAUDE.md |
| In-progress items shown | ✓ `user_status='in-progress'` |
| AC shown for use_cases | ✓ |
| Implementation plan shown | ✓ First 180 chars for in-progress |
| **GAP: pending (unapproved, wi_id LIKE 'AI%') items not shown** | LLM has no awareness of AI-classified but not yet approved items |

### CLAUDE.md overall completeness

| Item | State |
|------|-------|
| Project summary | ✓ From PROJECT.md Vision + Core Goals |
| Tech stack | ✓ From project_state.json synthesis |
| Key decisions | ✓ Up to 15 from synthesis |
| In-progress items | ✓ DB-primary |
| Recently changed symbols | ✓ Token-budget aware rolloff |
| Code hotspots | ✓ Score-filtered |
| Active features | ✓ Top 12 approved |
| Coding conventions | ✓ From `## Conventions` |
| **MISSING: "what has changed architecturally"** | No diff between past and current project structure — LLM can't detect drift |
| **MISSING: pending items** | New AI-classified items invisible until user approves |

---

## 2. Work Item Flows

### Classification (events → items)

| Item | State |
|------|-------|
| All source types time-bounded (event_horizon_days) | ✓ Fixed |
| Commit symbol summaries in prompt | ✓ `llm_summary` per class/method |
| Hotspot files flagged in prompt | ✓ `_hotspot_files` attached |
| Commit + prompt queries merged | ✓ Single `mem_mrr_commits_code` query |
| Max use cases cap | ✓ Default 8, configurable |
| AI draft rows cleared before each run | ✓ `wi_id LIKE 'AI%'` purge |
| **GAP: implementation_plan not in reclassify context** | 4-agent pipeline output not fed back into classify() |
| **GAP: commit_type (fix/feat/refactor) not auto-detected** | Can't distinguish "this commit fixed BU0012" from "introduced regression" |
| **GAP: no link from commit → resolved work item** | Code that closes a bug doesn't auto-update `user_status` |

### Work item scores & status

| Item | State |
|------|-------|
| `user_status` TEXT (m079) | ✓ `open/pending/in-progress/review/blocked/done` |
| `score_status` auto-5 when user marks done | ✓ |
| Re-embed on content change (approved only) | ✓ name/summary/deliveries/delivery_type |
| `acceptance_criteria` now in embed text | ✓ Fixed this session |
| **GAP: pending item update → no embed** | If user edits a pending (AI-draft) item's summary, it's never embedded |
| **GAP: overdue items** | `due_date < today AND status < done` — no MCP tool or CLAUDE.md section surfaces these |

### Commit / code changes → intelligence

| Item | State |
|------|-------|
| File hotspot scores | ✓ `mem_mrr_commits_file_stats` updated after each commit |
| File coupling detection | ✓ `mem_mrr_commits_file_coupling` with configurable threshold |
| Symbol-level summaries | ✓ Haiku per class/method per commit |
| code.md refresh after commit | ✓ Background |
| code.md embed after commit | ✓ `_embed_code_md()` called |
| `diff_summary` per commit | ✓ Stored in `mem_mrr_commits` |
| **GAP: no commit→item closure** | Commit message "fixes BU0012" doesn't auto-close the bug item |
| **GAP: hotspot suggest work items** | `_suggest_hotspot_work_items()` creates tasks, but runs only on `/memory` — not on high-hotspot commits |

### Approved items — quality & recency

| Item | State |
|------|-------|
| Approve triggers embed | ✓ |
| Approve triggers MD refresh for use_cases | ✓ `refresh_md()` called in `approve()` |
| Update triggers re-embed (approved + semantic field change) | ✓ |
| Tags merged from source events | ✓ `_update_item_tags()` + `_rollup_uc_tags()` |
| **GAP: no "last activity" on items** | `updated_at` is updated but no event log — can't tell "this bug was last discussed 3 months ago" |
| **GAP: work item ↔ commit two-way link weak** | `mrr_ids.commits` links item to commits, but `mem_mrr_commits.wi_id` is set — however searching "all commits for this item" requires a JOIN that no MCP tool exposes |

---

## 3. Embedding / MCP Strategy

### What is embedded

| Data | Model | Trigger | State |
|------|-------|---------|-------|
| code.md as single doc | text-embedding-3-small | `write_root_files`, `write_code_md`, `/memory` | ✓ |
| Approved work items (name+type+summary+deliveries+AC) | text-embedding-3-small | approve + content edit | ✓ |
| project_facts (all categories) | text-embedding-3-small | `/memory` POST (batch, outside DB conn) | ✓ fixed |
| Per-commit diffs | — | Never | Correct — noisy, low ROI |
| Per-symbol embeddings | — | Never | Low ROI vs code.md re-embed |
| Pending (unapproved) work items | — | Never | **GAP** |

**Embedding strategy assessment**: Re-embedding the full code.md on each commit is the right call. It gives one searchable "code map" chunk instead of thousands of fragmented symbol rows. Token cost is fixed (8000 chars ≈ 2000 tokens per embed call).

### MCP tools (16 tools)

| Tool | Useful? | Can answer |
|------|---------|-----------|
| `search_memory` | ✓ | Semantic search across work items + facts (code_structure chunk) |
| `get_project_state` | ✓ | Tech stack, key decisions, session tags, in-progress |
| `get_recent_history` | ✓ | Last N prompts with phase/feature filter |
| `get_commits` | ✓ | Recent commits + tags |
| `get_tagged_context` | ✓ | All events for a phase/feature |
| `list_work_items` | ✓ | Open bugs/features/tasks with status |
| `get_item_by_number` | ✓ | Full details for one item |
| `create_entity` | ✓ | Create unapproved item |
| `run_work_item_pipeline` | ✓ | Trigger 4-agent PM→Dev→Reviewer |
| `set_session_tags` / `get_session_tags` | ✓ | Track phase/feature context |
| `commit_push` | ✓ | Cursor sessions |
| `get_roles` | ✓ | Agent role definitions |
| `get_db_schema` | ✓ | Static schema reference |
| `search_work_items` | **STILL PRESENT** | Redundant with `search_memory` — should be removed |
| `get_file_history` | ✓ | Per-file symbol-level changes (dispatch added) |
| **MISSING: `get_hotspots`** | — | No dedicated tool; LLM must guess via `search_memory` |
| **MISSING: date filter on `list_work_items`** | — | Can't ask "what's overdue" or "due this week" |
| **MISSING: `get_item_history`** | — | Can't ask "all commits that touched bug BU0012" |

### Can MCP answer key project questions?

| Question | Tool | Works? |
|----------|------|--------|
| What are the open bugs? | `list_work_items(category=bug)` | ✓ |
| What's the tech stack? | `get_project_state` | ✓ |
| What are the coding conventions? | `search_memory(query="conventions")` | ✓ (via facts embed) |
| What is the code structure? | `search_memory(query="code structure")` | ✓ (via code.md embed) |
| What files are hotspots? | `search_memory(query="hotspot files")` | ⚠ Semantic, not exact |
| What changed recently? | `get_commits` or `get_recent_history` | ✓ |
| How many bugs are in-progress? | `list_work_items` + count | ✓ |
| What are the main use cases? | `list_work_items(category=use_case)` | ✓ |
| What is overdue? | — | ✗ No date filter |
| What is the project policy / prefix convention? | `search_memory(query="naming convention prefix")` | ⚠ Only if in facts/conventions |
| All commits for bug BU0012? | — | ✗ No tool |
| Did this commit fix something? | — | ✗ No commit→item link query |

---

## Summary

### What Is Missing (Major)

| # | Gap | Severity | Component |
|---|-----|----------|-----------|
| 1 | **Architectural override not tracked**: PROJECT.md Vision/Core Goals don't auto-invalidate old key_decisions. LLM sees stale architecture narrative until user manually rewrites. | **High** | Memory Files |
| 2 | **Pending items invisible**: AI-classified items (wi_id LIKE 'AI%') not shown in CLAUDE.md or code.md — LLM unaware of what the system classified but user hasn't approved yet. | **Medium** | Memory Files |
| 3 | **Commit → item closure missing**: A commit message "fixes BU0012" doesn't auto-resolve the work item. Human has to update status manually. | **Medium** | Work Item Flows |
| 4 | **No overdue items surface**: No section in CLAUDE.md, no MCP tool filter for `due_date < today`. | **Medium** | MCP / Memory Files |
| 5 | **`search_work_items` still present in MCP**: Redundant with `search_memory`. Adds schema weight to every call. Remove. | **Low** | MCP |
| 6 | **`get_hotspots` MCP tool missing**: File churn data exists in DB but only reachable by fuzzy semantic search. A direct tool would be more reliable. | **Low** | MCP |
| 7 | **code.md not refreshed on session start**: Only CLAUDE.md + cursorrules are written at start hook — code.md may be days old between commits. | **Low** | Memory Files |
| 8 | **No MCP date filter on `list_work_items`**: Can't ask "what's due this week" or "what's overdue". | **Low** | MCP |

### Major Improvements — Per Component

#### Component 1: Memory Files
| Action | Impact |
|--------|--------|
| Add "supersedes" mechanism in PROJECT.md (e.g. `## Deprecated`) — `/memory` excludes deprecated entries from key_decisions | Prevents LLM seeing outdated architecture |
| Show pending item count in CLAUDE.md (e.g. "12 unreviewed AI items — run `/items` to review") | LLM aware of unreviewed work |
| Refresh code.md on session start hook (add to `write_root_files()`) | Always-fresh code map |

#### Component 2: Work Item Flows
| Action | Impact |
|--------|--------|
| Parse commit message for `fixes #BU0001` / `closes FE0012` — auto-set `user_status=done` | Closes the commit→item gap |
| Surface overdue items in CLAUDE.md (below in-progress section) | Visible to LLM without MCP call |

#### Component 3: MCP / Embedding
| Action | Impact |
|--------|--------|
| Remove `search_work_items` tool (still present) | Reduces MCP schema weight |
| Add `get_hotspots` tool (direct DB query, no semantic fuzzy) | Reliable hotspot answers |
| Add `due_date_before` param to `list_work_items` dispatch | Enables overdue queries |
