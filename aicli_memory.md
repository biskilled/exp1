# aicli Memory System — System Audit
_Last updated: 2026-04-27 | Goal: shared LLM memory layer — any LLM picks up project context instantly_

---

## 1. System Overview — Data Flow

```
User/Git Actions                Layer 1 Raw Capture (mem_mrr_*)
─────────────────               ─────────────────────────────────────────────────
Claude Code stop hook     ────► mem_mrr_prompts   (prompt+response, tags, session_id)
git push (post-commit)    ────► mem_mrr_commits    (hash, msg, tags, diff_summary)
                                    │
                                    └──► [background thread] _extract_commit_code_background()
                                              ├── mem_mrr_commits_code   (tree-sitter: class/method/file)
                                              ├── mem_mrr_commits_file_stats  (hotspot_score per file)
                                              ├── mem_mrr_commits_file_coupling  (co-change pairs)
                                              ├── _close_items_from_commit()  ← NEW
                                              │     "fixes BU0012" → score_status=5, user_status='review'
                                              ├── _post_commit_synthesis()    ← NEW
                                              │     Haiku synthesis → project_state.json (background)
                                              └── write_root_files() → code.md + CLAUDE.md + embed
Manual API only           ────► mem_mrr_items    (documents, meetings) ← EMPTY in practice
Manual API only           ────► mem_mrr_messages (Slack/chat)          ← EMPTY in practice

                 Layer 2 Project Facts (mem_ai_project_facts)
                 ─────────────────────────────────────────────────────────────────
POST /memory/{p}          Haiku project_synthesis → project_state.json (key_decisions, tech_stack)
                          _auto_populate_project_facts() → batch-embed outside DB conn → mem_ai_project_facts
                          _embed_code_md() → code_structure fact (searchable via MCP search_memory)

                 Layer 3 Work Items (mem_work_items)
                 ─────────────────────────────────────────────────────────────────
POST /wi/classify         mem_mrr_* (wi_id IS NULL) → Haiku batch → draft items (wi_id=AI0001…)
User approves in UI       AI0001 → BU0001 + embed + MD file + write_root_files()
Commit "fixes BU0012"     score_status=5, score_importance=5, user_status='review' ← NEW

                 Context File Outputs (memory_files.py — deterministic, no LLM)
                 ─────────────────────────────────────────────────────────────────
After every commit        write_root_files() → CLAUDE.md, .cursorrules, code.md, GEMINI.md, AGENTS.md
                          _embed_code_md() → mem_ai_project_facts[code_structure]
POST /memory              write_all_files() → all files above + provider-specific files
Session start hook        POST /memory/regenerate?scope=root → write_root_files()
```

---

## 2. LLM Prompts — Complete Inventory

All prompts live in `backend/prompts/*.yaml`, hot-reloaded by `core/prompt_loader.py`.
No inline LLM strings remain in Python.

| Prompt Key | File | Model | Trigger | Input → Output |
|---|---|---|---|---|
| `project_synthesis` | command_memory.yaml | Haiku 2000tok | POST /memory | history + PROJECT.md + state → project_state.json |
| `conflict_detection` | command_memory.yaml | Haiku 300tok | POST /memory → MemoryPromotion | old+new fact → resolution type |
| `tag_suggestion` | misc.yaml | Haiku 100tok | POST /memory | last 5 developer prompts → `{"phase":"…","feature":"…"}` |
| `feature_auto_detect` | misc.yaml | Haiku 60tok | POST /chat/hook-log | existing features + new prompt → auto-tag session feature |
| `memory_context_compact` | command_memory.yaml | n/a (preamble) | write_all_files() | — → prepended to .cursorrules, copilot |
| `memory_context_full` | command_memory.yaml | n/a (preamble) | write_all_files() | — → prepended to CLAUDE.md, GEMINI.md |
| `memory_context_openai` | command_memory.yaml | n/a (preamble) | write_all_files() | — → prepended to api/system_prompt.md |
| `commit_analysis` | event_commit.yaml | Haiku | POST /git/commit-store | hash+msg+diff → phase/feature tags + summary |
| `commit_symbol` | event_commit.yaml | Haiku | extract_commit_code() background | per-symbol diff → llm_summary |
| `commit_message` | event_commit.yaml | Haiku | POST /git/commit-push | staged diff → generated commit message |
| `react_pipeline_base` | react_base.yaml | n/a (static) | agent.py startup | — → ReAct system prompt prefix |
| `react_suffix` | react_base.yaml | n/a (static) | agent.run() | — → shorter ReAct format |
| _(classify)_ | work_items.yaml | Haiku 4000tok | POST /wi/classify | batched events (~3000 tok/batch) → work item JSON |
| _(summarise)_ | work_items.yaml | Haiku 2000tok | POST /wi/{id}/summarise | UC name+children → new_summary + reorder |
| _(reclassify)_ | work_items.yaml | Haiku 120tok | POST /wi/{id}/reclassify | item name/summary/status → wi_type + scores |

**Active Haiku call paths**: 6 (project_synthesis, conflict_detection, tag_suggestion, commit_analysis, commit_symbol/message, classify). 3 static preambles (no LLM call).

**Fixed**: `tag_suggestion` was duplicated in `command_memory.yaml` (empty stub) and `misc.yaml` (full prompt). Alphabetical load order → misc.yaml wins. Stub removed from command_memory.yaml.

---

## 3. Memory Layers — Current State

### Layer 1: Raw Capture (`mem_mrr_*`)

| Table | Populated By | Frequency | Used For |
|---|---|---|---|
| `mem_mrr_prompts` | Claude Code stop hook → POST /chat/hook-log | Every session end | Work item classify source |
| `mem_mrr_commits` | git post-commit hook → POST /git/commit-store | Every push | Classify + commit_analysis LLM |
| `mem_mrr_commits_code` | extract_commit_code() [background] | After each commit | code.md hotspots + symbol summaries |
| `mem_mrr_commits_file_stats` | extract_commit_code() [background] | After each commit | hotspot_score, bug_commit_count |
| `mem_mrr_commits_file_coupling` | extract_commit_code() [background] | After each commit | co-change coupling detection |
| `mem_mrr_items` | Manual POST /items | **Never in practice** | Meeting notes / docs — **EMPTY** |
| `mem_mrr_messages` | Manual POST /messages | **Never in practice** | Slack/chat — **EMPTY** |

**Assessment**: prompts + commits are well-captured and auto-tagged. `mem_mrr_items` and `mem_mrr_messages` exist in schema but have no auto-population path — classify context is prompt+commit only.

### Layer 2: Project Facts (`mem_ai_project_facts`)

**Structure**: `fact_key`, `fact_value`, `category` (stack/pattern/convention/constraint/general/code), `embedding VECTOR(1536)`, `valid_until`

**Written by**:
1. POST /memory → `_auto_populate_project_facts()` — batch-embeds outside DB connection (fixed ✓)
2. `_embed_code_md()` — stores full code.md as `fact_key='code_structure'` for semantic search

**Assessment**: Facts are sparse in practice. The primary LLM context comes from `project_state.json` (written by /memory + NOW ALSO by `_post_commit_synthesis()` after every commit). The `code_structure` fact is the most valuable — makes the full code map searchable via MCP.

### Layer 3: Work Items (`mem_work_items`)

**Lifecycle**: raw event → [classify] → draft (AI0001) → [approve] → approved (BU0001) → [done] → `user_status='done'`

**Approved items embed**: `_embed_work_item()` includes name + wi_type + summary + deliveries + delivery_type + acceptance_criteria (✓).
**Re-embed trigger**: `approve()` + `update()` when semantic fields change.
**Markdown file**: Written to `workspace/{project}/documents/use_cases/{slug}.md` on approval.
**Commit auto-close** ← NEW: `_close_items_from_commit()` regex parses "fixes/closes/resolves BU0012" → score_status=5, score_importance=5, user_status='review'.

---

## 4. Component Analysis

### 4A. code.md — Well-triggered?

**Content**: Dir tree (depth 3) + recently changed symbols (from mem_mrr_commits_code, last 20) + hotspot files table (score, commits, lines, bugs) + coupling pairs.

**Trigger chain**:
```
git push → mem_mrr_commits → [background] extract_commit_code()
    → mem_mrr_commits_code + file_stats + file_coupling
    → write_root_files() → code.md written
        → _embed_code_md() → mem_ai_project_facts[code_structure]
Session start hook → POST /memory/regenerate?scope=root → write_root_files() (same path)
POST /memory → write_all_files() (same path)
```

**Status**: ✓ Well-triggered. Always current after commit AND embedded for semantic search.

**Minor gap**: code.md shows *recently changed* symbols + hotspots but not the full public API surface. An LLM knows what's changing, not what everything does.

### 4B. PROJECT.md — Well-maintained?

**Content**: Vision + Core Goals (user-managed) + Conventions + Recent Work + Key Decisions (auto-updated by /memory) + `## Deprecated` section (NEW ✓).

**`## Deprecated` mechanism**: User adds phrases under this section. `_load_context()` in memory_files.py parses them; CLAUDE.md and .cursorrules renderers filter matching `key_decisions`. Instant suppression without needing `/memory` run.

**Status**: ✓ Both the `## Deprecated` filter and the Haiku `project_synthesis` prompt ("PROJECT.md is authoritative — replace stale decisions") prevent old architecture from polluting LLM context.

**Gap**: Key Decisions come from Haiku synthesis over *prompts* — not direct code reading. They lag behind code changes that haven't been discussed in prompts.

### 4C. Project Facts (`mem_ai_project_facts`) — Updated and non-duplicate?

**Upsert strategy**: `valid_until=NOW()` marks old facts stale before inserting new (per category). Key normalization prevents exact duplicates.

**Status**: ✓ Works for explicit `/memory` runs. NOW ALSO updated via `_post_commit_synthesis()` (background after every commit) — project_state.json stays fresh without manual /memory.

**Missing index**: `CREATE INDEX ... ON mem_ai_project_facts(project_id, valid_until) WHERE valid_until IS NULL` — currently full table scan per render.

### 4D. Approved Work Items — Well-used?

**In CLAUDE.md**: Top 12 approved (non-done), bug-type first. In-progress items shown separately with due dates. Acceptance criteria for use_cases.

**Status**: ✓ Well-used. Both human-readable CLAUDE.md section and semantic search embedding are populated with acceptance_criteria included.

### 4E. Unapproved/Draft Work Items — Visibility

**Status**: ✓ Correct behavior (confirmed with user). Draft items (wi_id LIKE 'AI%') are NOT shown in CLAUDE.md or embedded — they're user-replaceable noise. Only visible in Work Items UI. Classify purges all AI drafts before regenerating.

### 4F. Architectural Overrides — Stale decisions replaced?

**Mechanisms** (both active):
1. `## Deprecated` in PROJECT.md → instant phrase-filter in renderers
2. `project_synthesis` Haiku prompt → "PROJECT.md is authoritative, replace stale decisions"
3. `_post_commit_synthesis()` → re-runs synthesis after every commit (NEW ✓)

**Status**: ✓ Three-layer protection against stale architecture in LLM context.

### 4G. CLAUDE.md — Complete and current?

**Sections** (all from DB, deterministic):
- Key Architectural Decisions ← project_state.json (now updated on every commit ✓)
- Project Documentation ← PROJECT.md Vision + Core Goals
- Code Hotspots ← mem_mrr_commits_file_stats
- Recently Changed Symbols ← mem_mrr_commits_code
- Active Features/Work Items ← mem_work_items (approved only, bug-first)
- In Progress Items with due dates
- Coding Conventions ← PROJECT.md ## Conventions
- Tech Stack ← project_state.json

**Status**: ✓ Well-structured. Token-budget rolloff (oldest symbols drop first). Key Decisions now always ≤1 commit stale.

---

## 5. Work Item Flows

### Classification Trigger
```
Events piling up in mem_mrr_* (wi_id IS NULL)
    → Manual: POST /wi/classify
    → Auto (threshold mode): check_and_trigger() from route_git.py + route_chat.py
      (prompts: 2000 tokens, commits: 1000, messages: 5000, items: 500)
    → Haiku batch (3000 tokens/batch) → JSON array of work items
    → Draft rows: use_cases first (AI0001), children via wi_parent_id
```

### Approve Chain
```
User approves in UI
    → Assign real wi_id (US0001/BU0001/FE0001/TA0001)
    → batch UPDATE mem_mrr_* SET wi_id=new_id WHERE id = ANY(...)  ← FIXED (was N+1)
    → _embed_work_item() → VECTOR(1536) stored
    → _write_md_file() → documents/use_cases/{slug}.md written
    → write_root_files() → CLAUDE.md refreshed
```

### Commit → Work Item Auto-Close (NEW)
```
git push → commit msg "fixes BU0012" or "closes FE0001"
    → _close_items_from_commit(project_id, commit_msg)
        → regex: fix(es|ed)|clos(e|es|ed)|resolv(e|es|ed) + [A-Z]{2}[0-9]{4}
        → UPDATE mem_work_items SET score_status=5, score_importance=5, user_status='review'
        → User sees item in 'review' queue with high confidence → one-click approve
```

### Score System
| Field | Set By | Meaning |
|---|---|---|
| `score_importance` | Haiku at classify time (1-5) | How important this item is |
| `score_status` | Haiku at classify time (1=not started, 5=done) | LLM-estimated progress |
| `user_status` | User in UI (authoritative) | `open/pending/in-progress/review/blocked/done` |

`score_status` is supplementary — `user_status` is source of truth for CLAUDE.md and MCP.

### Code Events → Classification Context
`_ClassifyMixin._fetch_pending_events()` attaches to each commit:
- `_hotspot_files`: files touched by commit with their hotspot scores
- `_symbol_summaries`: per-symbol LLM summaries from mem_mrr_commits_code

These feed the Haiku classify prompt → LLM-aware of which files are changing and what code-level changes mean.

---

## 6. Embedding / MCP Strategy

### What Is Embedded

| Data | Trigger | Table | Searchable Via |
|---|---|---|---|
| Approved work items | approve() + re-embed on update | mem_work_items.embedding | MCP search_memory + /search/semantic |
| code.md snapshot | write_root_files() after every commit + /memory | mem_ai_project_facts(code_structure) | MCP search_memory("code structure") |
| Project facts | POST /memory → batch outside DB conn | mem_ai_project_facts | MCP search_memory(category) |

**Not embedded** (correct): raw prompts/commits (noisy), per-symbol diffs (covered by code.md), draft items.

### MCP Tools (15 registered — sync_github_issues dispatch removed ✓)

| Tool | Status | Notes |
|---|---|---|
| `search_memory` | ✓ | Cosine similarity over work items + code_structure + facts |
| `get_project_state` | ✓ | Tech stack, key decisions, in-progress |
| `get_recent_history` | ✓ | Last N prompts with phase/feature filter |
| `get_commits` | ✓ | Tagged commits |
| `get_tagged_context` | ✓ | All events for a phase or feature |
| `list_work_items` | ✓ | Filter by type, status, `due_date_before` (added ✓) |
| `get_item_by_number` | ✓ | Full detail for one item |
| `create_entity` | ✓ | Create unapproved item |
| `run_work_item_pipeline` | ✓ | Haiku 4-agent summary |
| `get_hotspots` | ✓ | Direct file churn query |
| `get_file_history` | ✓ | Per-file symbol changes |
| `get_session_tags` / `set_session_tags` | ✓ | Phase/feature tracking |
| `commit_push` | ✓ | Cursor session commits |
| `get_roles` | ✓ | Agent role definitions |
| `get_db_schema` | ✓ | Schema reference (static) |

### MCP Capability Matrix

| Question | Tool | Works? |
|---|---|---|
| What are the open bugs? | `list_work_items(category=bug)` | ✓ |
| What is the tech stack? | `get_project_state` | ✓ |
| What are coding conventions? | `search_memory("conventions")` | ✓ via facts |
| What is the code structure? | `search_memory("code structure")` | ✓ via code.md embed |
| What files are hotspots? | `get_hotspots` | ✓ direct |
| What changed recently? | `get_commits` | ✓ |
| What items are overdue? | `list_work_items(due_date_before="today")` | ✓ added ✓ |
| What is in progress? | `get_project_state` or `list_work_items(status=in-progress)` | ✓ |
| All commits for bug BU0012? | — | ✗ no direct tool |
| What's the full API surface? | — | ✗ code.md shows recent changes only |

---

## 7. Code Quality — Changes Applied This Session

### Fixes Applied

| Fix | File | Before → After |
|---|---|---|
| 4 unbounded recursive CTEs | `_wi_markdown.py` (3 CTEs), `memory_work_items.py` (1 CTE) | No depth limit → `AND d.depth < 20` added to all |
| N+1 UPDATE in approve() | `memory_work_items.py` | 4 per-row loops → 4 `WHERE id = ANY(%s::uuid[])` batch updates |
| N+1 UPDATE in reject() | `memory_work_items.py` | Same pattern fixed |
| Commit → item auto-close | `route_git.py` | New `_close_items_from_commit()` via regex |
| Post-commit synthesis | `route_git.py` | New `_post_commit_synthesis()` keeps project_state.json fresh |
| MCP dead stub | `server.py` | `sync_github_issues` dispatch branch removed |
| Duplicate tag_suggestion | `command_memory.yaml` | Stub removed; misc.yaml is canonical |
| `## Deprecated` section | `memory_files.py` | Phrase-filter in both CLAUDE.md + cursorrules renderers |
| `due_date_before` filter | `server.py` | Added to `list_work_items` MCP tool |

### 2 CTEs already had depth limits

`memory_work_items.py` lines 286 and 416 (`desc_tree`) already used `AND dt.depth < 10`. Only the 4 `tree`/`descendants` CTEs in `_wi_markdown.py` and `approve_all_under` were unbounded.

### Remaining Quality Notes

| Issue | File | Severity |
|---|---|---|
| Missing DB index on project_facts | `mem_ai_project_facts(project_id, valid_until)` | Medium — full table scan per render |
| Token counting uses `len(text.split()) * 1.3` | `_wi_classify.py:_count_tokens()` | Low — ~10% under-estimate; benign for batching |
| `memory_work_items.py` still ~1350 lines | CRUD methods dense | Low — mixins extracted; remaining methods are cohesive |
| N+1 hotspot existence checks | `route_projects.py:_suggest_hotspot_work_items()` | Low — one DB query per hotspot file |

---

## 8. What Is Missing (Major Gaps Only)

| # | Gap | Impact | Status |
|---|---|---|---|
| 1 | `mem_mrr_items` and `mem_mrr_messages` never populated | Medium — non-code decisions invisible to classify | No auto-ingestion path |
| 2 | Missing DB index on `mem_ai_project_facts` | Medium — full table scan on every /memory render | Not yet added (migration needed) |
| 3 | No overdue items section in CLAUDE.md | Low — requires MCP call; not auto-surfaced | By design (MCP covers it) |
| 4 | code.md lacks full API surface | Low — only recent-change symbols shown | Intentional for token budget |
| 5 | No commit→wi_id lookup tool in MCP | Low — "all commits for BU0012?" not answerable | Not yet implemented |

---

## 9. Major Improvements Per Component

### Memory Files
| Action | Impact |
|---|---|
| Add missing index: `CREATE INDEX ON mem_ai_project_facts(project_id, valid_until) WHERE valid_until IS NULL` | Removes full table scan on every render |
| Add `## Overdue` section to CLAUDE.md renderer (`due_date < today AND user_status != 'done'`) | LLM immediately aware of missed deadlines |

### Work Item Flows
| Action | Impact |
|---|---|
| Surface unprocessed event count in CLAUDE.md (e.g. "23 unclassified events — run `/classify`") | LLM and user know when classification is overdue |
| Add `parent_name` to `list_work_items` MCP response | LLM understands hierarchy without extra calls |

### MCP / Embedding
| Action | Impact |
|---|---|
| Add `get_commits_for_item` tool: `GET /git/{p}/commits?wi_id=BU0012` | Closes the "which commits fixed this bug?" gap |
| Populate `mem_mrr_items` via webhook (GitHub Issues → items) | Non-code decisions enter classify pipeline |
