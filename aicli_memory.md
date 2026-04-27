# aicli Memory System Audit
_Last updated: 2026-04-27 | Fresh audit — reflects code state after last 10 prompts_

---

## 1. Memory Files

### CLAUDE.md / context files

| Item | State |
|------|-------|
| Project summary | **BUG** — `_load_context()` reads from `workspace/{p}/PROJECT.md` (line 335) but actual file is at `workspace/{p}/memory/PROJECT.md`. Project summary section is always empty. |
| Conventions | ✓ Reads correctly from `memory/PROJECT.md` `## Conventions` section |
| Stack & Architecture | ✓ From `project_state.json.tech_stack` (Haiku synthesis, replaced each run) |
| Key Decisions | ✓ From `project_state.json.key_decisions` (max 15) |
| In Progress | ✓ DB-primary (`user_status='in-progress'`), fallback to LLM-derived |
| Active Features | ✓ Top 12, bug-first, from `mem_work_items` approved items |
| Acceptance Criteria | ✓ Shown for `use_case` type items only |
| Implementation Plan | ✓ Shown for `in-progress` items (first 180 chars) |
| Code Hotspots | ✓ From `mem_mrr_commits_file_stats` |
| Recently Changed | ✓ Symbol-level from commits, token-budget aware |
| Coding Conventions | ✓ From `PROJECT.md ## Conventions` section |
| Unapproved work items | ✗ Never shown — no "pending review" section |

### code.md

| Item | State |
|------|-------|
| Directory tree | ✓ Always fresh (walks `code_dir` depth-3) |
| Active Work Items | ✓ Approved, not-done |
| AC for use_cases | ✓ Added |
| Implementation plan | ✓ For in-progress items |
| Coding Conventions | ✓ Pulled from `PROJECT.md ## Conventions` |
| Recently Changed (table) | ✓ Last 20 symbols |
| Code Hotspots (table) | ✓ File + score + commits + bug fixes |
| File Coupling | ✓ Co-change pairs |
| Embedding (facts table) | ✓ `write_code_md()` + `write_root_files()` + `generate_memory()` all call `_embed_code_md()` |
| Trigger on `/memory` POST | ✓ `generate_memory()` explicitly calls `_embed_code_md(project_name)` at step 5b |

### PROJECT.md

| Item | State |
|------|-------|
| Vision / Core Goals | ✓ User-managed; feeds CLAUDE.md project summary |
| Conventions section | ✓ Added to aicli project and `_templates/memory/PROJECT.md` starter |
| Recent Work / Key Decisions | ✓ Auto-updated by `/memory` via synthesis |
| Starter template | ✓ `_templates/memory/PROJECT.md` created; seeded on project create |
| Staleness detection | ✓ `_Last updated_` date bumped on each `/memory` run |

### project_state.json

| Item | State |
|------|-------|
| `tech_stack` | ✓ Haiku synthesis, REPLACED each run |
| `key_decisions` | ✓ Haiku synthesis, REPLACED each run, max 15 |
| `in_progress` | ✓ Fallback only — DB primary now |
| `last_memory_run` | ✓ Timestamp shown in CLAUDE.md age note |

### Project Facts (`mem_ai_project_facts`)

| Item | State |
|------|-------|
| Auto-population on `/memory` | ✓ Haiku extracts 5-10 facts from PROJECT.md + synthesis |
| Key normalization | ✓ `_norm_key()` lowercases + snake_cases before insert |
| Stale fact expiry | ✓ Bulk `valid_until=NOW()` for non-code facts before each run |
| Code structure embedded | ✓ code.md stored as `fact_key='code_structure'` |
| Embedding inside open conn | **PERF** — `_embed_sync()` called per-fact inside `with db.conn()` block. N blocking embed calls while holding a DB connection. Should embed all texts first, then insert in batch. |
| Duplicate INSERT pattern | MINOR — two near-identical INSERT blocks (with/without embedding vec) could be one. |

### SQL Issues — memory_files.py

| Issue | Detail |
|-------|--------|
| Duplicate coupling SQL | `_SQL_COUPLING` (hardcoded threshold=3) and `_SQL_COUPLING_HIGH` (parameterized) query the same table. Merge into one parameterized constant. |
| `_SQL_RECENTLY_CHANGED` fetches 200 rows | Only 30 shown (max_recent default). `LIMIT 50` is enough. |
| `get_active_feature_tags()` re-queries DB | Runs `_SQL_ACTIVE_WORK_ITEMS` again; data already in `ctx["active_tags"]`. Pass `ctx` instead. |
| `write_root_files()` reads project.yaml twice | Once in `_load_context()`, again at line 1097 for log cleanup. Use `ctx["memory_config"]`. |

---

## 2. Work Item Flows

### Classification (events → items)

| Item | State |
|------|-------|
| Event sources | `mem_mrr_prompts`, `mem_mrr_commits`, `mem_mrr_messages`, `mem_mrr_items` |
| Event horizon | ✓ Configurable `event_horizon_days` (default 90) applied to prompts/commits/messages |
| `mem_mrr_items` horizon | **BUG** — date cutoff not applied to `mem_mrr_items` query. Only source type without time filter. Old items re-enter classification indefinitely. |
| Commit symbol summaries | ✓ Per-symbol `llm_summary` from `mem_mrr_commits_code` fed into classify prompt |
| Hotspot context | ✓ File hotspot scores attached to commit events |
| Two queries for same hashes | **PERF** — `_fetch_pending_events` queries `mem_mrr_commits_code` twice for the same `commit_hashes`: once for file paths (hotspot), once for symbol summaries. Can be merged into one query. |
| Double `db.is_available()` check | MINOR — called at lines 434 and 437, identical check. Remove duplicate. |
| Use case cap | ✓ Max 8 UCs per run; existing UCs passed as context to avoid duplicates |
| AI draft lifecycle | ✓ All AI-draft items deleted before each classify() run |

### Work Item Scores & Status

| Item | State |
|------|-------|
| `user_status` in reclassify | ✓ Fetched from DB, mapped to score hint, passed to Haiku |
| `score_status` auto-5 on done | ✓ |
| `implementation_plan` in classify prompt | ✗ The 4-agent pipeline writes this, but it's not fed back into `classify()` context for reclassification |

### Embedding & Re-embedding

| Item | State |
|------|-------|
| Re-embed on name/summary edit | ✓ Triggered on content update |
| `acceptance_criteria` in embed text | **GAP** — `_embed_work_item()` embeds only `name + wi_type + summary + deliveries`. AC is not included, so semantic search won't match on criteria text. |
| Embed triggered on approve | ✓ |
| AC included in approve embed | ✗ Same gap as above — approval embeds only name/summary |

### Commits → Code Intelligence

| Item | State |
|------|-------|
| `commit_analysis` → `diff_summary` | ✓ Stored in `mem_mrr_commits` |
| Symbol extraction | ✓ Haiku → `llm_summary` in `mem_mrr_commits_code` |
| File stats / coupling | ✓ `mem_mrr_commits_file_stats`, `mem_mrr_commits_file_coupling` |
| code.md refresh after commit | ✓ `write_code_md()` called in background |
| `code.md` embed after commit | ✓ `write_code_md()` calls `_embed_code_md()` |

### File & Code Quality

| Item | State |
|------|-------|
| `memory_work_items.py` size | **2621 lines** — largest hotspot. Needs splitting into `_classify.py`, `_crud.py`, `_embed.py`, `_approval.py` |
| `_config()` reads from `code_dir/project.yaml` | Inconsistency with `memory_files.py` which reads from `workspace/{p}/project.yaml`. May point to different files if `code_dir ≠ workspace/{p}`. |

---

## 3. Embedding / MCP Strategy

### What Is Embedded

| Data | Model | Trigger | State |
|------|-------|---------|-------|
| Approved work items | text-embedding-3-small | On approve + content edit | ✓ |
| Project facts (auto) | text-embedding-3-small | On `/memory` | ✓ |
| code.md document | text-embedding-3-small | On `write_root_files()` and `write_code_md()` | ✓ but NOT from `/memory` POST |
| `acceptance_criteria` text | — | Never | ✗ |

### MCP Tools (18 tools — too many)

| Tool | Useful? | Note |
|------|---------|------|
| `search_memory` | ✓ | Now searches work_items + facts combined |
| `search_work_items` | **REDUNDANT** | Subset of `search_memory`. Remove. |
| `search_facts` | ✓ | Focused search for architecture/conventions |
| `get_project_state` | ✓ | Project overview, session tags |
| `get_open_items` | **REDUNDANT** | Same as `list_work_items?status=active`. Remove or merge. |
| `list_work_items` | ✓ | Full list with status filter |
| `get_hotspots` | ✓ | File churn ranking |
| `get_file_history` | ✓ | Per-file symbol-level changes |
| `get_commits` | ✓ | Recent commits with tags |
| `get_item_by_number` | ✓ | Resolve wi_id → full details |
| `get_recent_history` | ✓ | Last N prompts |
| `get_tagged_context` | ✓ | All events for a phase/feature |
| `get_tag_context` | ⚠ | Similar to `get_tagged_context`; different API; naming confusing |
| `set_session_tags` | ✓ | Tag current session |
| `get_session_tags` | ✓ | Read current tags |
| `commit_push` | ✓ | For Cursor sessions |
| `create_entity` | ✓ | Create unapproved item |
| `run_work_item_pipeline` | ✓ | 4-agent pipeline trigger |
| `get_db_schema` | ✓ | Static schema reference (inline dict — doesn't hit DB) |

**Tool count**: 18. Every MCP call sends all 18 schemas to the LLM. Target: 14-15 by removing `search_work_items` and `get_open_items`.

### MCP — Can It Answer Key Questions?

| Question | Tool | Works? |
|----------|------|--------|
| What are the open bugs? | `get_open_items(category=bug)` | ✓ |
| How many bugs are in-progress? | `get_open_items(category=bug, status=in-progress)` | ✓ |
| What is the project's tech stack? | `get_project_state` | ✓ |
| What are the coding conventions? | `search_facts(query="conventions coding style")` | ✓ |
| What changed in file X recently? | `get_file_history(file_path=X)` | ✓ (new) |
| What files are hotspots? | `get_hotspots` | ✓ |
| What are the main use cases? | `list_work_items(category=use_case)` | ✓ |
| What is currently in-progress? | `list_work_items(status=active)` + filter client-side | ✓ |
| What decisions were made about auth? | `search_memory(query="auth decision")` | ✓ (improved) |
| What's the code structure? | `search_facts(category=code)` | ✓ (via embedded code.md) |
| Latest updates / commits | `get_commits` | ✓ |
| Number of pending items | `list_work_items` → count | ✓ |

### Embedding Strategy Analysis

| Option | Status | Assessment |
|--------|--------|------------|
| code.md as single embedded doc | ✓ Done | High ROI — entire code map searchable |
| Per-symbol embedding | ✗ Not done | Medium ROI, high cost — ~N×commits rows |
| code.md embed from `/memory` POST | ✗ Missing | Should call `_embed_code_md()` at end of `generate_memory()` |
| `acceptance_criteria` in work item embed | ✗ Not done | Medium ROI — AC text is search-relevant |
| Per-commit diff embedding | ✗ Not done | Low ROI — noisy, already in `get_commits` |

---

## Summary

### What Is Still Missing / Fixed This Session

| # | Gap | Severity | Fixed? |
|---|-----|----------|--------|
| 1 | **Project summary path BUG**: `_load_context()` read wrong path for PROJECT.md | Critical | ✓ Fixed |
| 2 | **`mem_mrr_items` not time-bounded**: old items re-entered classify forever | Medium | ✓ Fixed |
| 3 | **Duplicate coupling SQL + 200-row over-fetch + redundant `get_active_feature_tags` DB query** | Low | ✓ Fixed |
| 4 | **`_embed_code_md` truncation**: embedded `[:8000]` but stored `[:4000]` | Low | ✓ Fixed |
| 5 | **18 MCP tools**: `search_work_items` + `get_open_items` redundant | Low | ✓ Fixed (16 tools) |
| 6 | **`acceptance_criteria` not in work item embedding**: AC text not findable via semantic search | Medium | ✗ Open |
| 7 | **`_auto_populate_project_facts` embeds inside open DB connection**: N blocking embed calls while holding pool connection | Medium | ✗ Open |
| 8 | **`memory_work_items.py` at 2621 lines**: Two DB queries merged (commit_code) but file still needs splitting | Low | ✗ Open |

---

### Major Improvements — Per Component

#### Component 1: Memory Files
| Improvement | Action |
|-------------|--------|
| ~~Fix project_summary path~~ | ✓ Done — `workspace/{p}/memory/PROJECT.md` |
| ~~Merge duplicate coupling SQL~~ | ✓ Done — single `_SQL_COUPLING(pid, threshold)` |
| ~~Remove project.yaml double-read~~ | ✓ Done — uses `ctx["memory_config"]` |
| ~~Remove redundant `get_active_feature_tags` query~~ | ✓ Done — `write_all_files()` now uses ctx |

#### Component 2: Work Item Flows
| Improvement | Action |
|-------------|--------|
| Add date horizon to `mem_mrr_items` | Add `AND created_at > NOW() - INTERVAL '1 day' * %s` to items query |
| Merge two `mem_mrr_commits_code` queries | One query selecting both `file_path` and `llm_summary` per symbol |
| Include AC in work item embedding | Add `acceptance_criteria` to `_embed_work_item()` text composition |
| Split `memory_work_items.py` | Extract `_classify.py` (~700 lines), `_approval.py` (~300 lines), `_crud.py` (~600 lines) |

#### Component 3: Embedding / MCP
| Improvement | Action |
|-------------|--------|
| Remove `search_work_items` tool | Covered by `search_memory` — reduces tool count to 17 |
| Remove `get_open_items` tool | Merge into `list_work_items` as default `status=active` — reduces to 16 |
| Fix `_auto_populate_project_facts` embed order | Collect all (fact_key, fact_value) texts, batch embed outside DB conn, then bulk insert |
| Fix `_embed_code_md` truncation | Align `content[:8000]` for both embedding and storage |
