# aicli Memory System — System Audit
_Last updated: 2026-04-27 | Goal: shared LLM memory layer — any LLM picks up project context instantly_

---

## 1. System Overview — How Data Flows

```
User/Git Actions                Layer 1 Raw Capture
─────────────────               ───────────────────────────────────────────────────────────
Claude Code stop hook     ────► mem_mrr_prompts   (prompt + response, tags JSONB)
git push (post-commit)    ────► mem_mrr_commits    (hash, msg, tags)
                                    │
                                    └──► [background] extract_commit_code()
                                              mem_mrr_commits_code   (per-symbol: class/method/file)
                                              mem_mrr_commits_file_stats  (hotspot score per file)
                                              mem_mrr_commits_file_coupling  (co-change pairs)
Manual API only           ────► mem_mrr_items    (documents, meetings) ← EMPTY in practice
Manual API only           ────► mem_mrr_messages (Slack/chat)          ← EMPTY in practice

                 Layer 3 Work Items (classify → approve)
                 ─────────────────────────────────────────────────────────────────
POST /wi/classify         reads mem_mrr_* (wi_id IS NULL) → Haiku → draft mem_work_items (wi_id=AI0001…)
User approves in UI       draft → approved (wi_id=BU0001 etc) → embed → MD file written

                 Layer 2 Project Facts (only on /memory POST)
                 ──────────────────────────────────────────────────────────────────
POST /memory/{project}    Haiku synthesis → project_state.json (key_decisions, tech_stack)
                          → mem_ai_project_facts (sparse; code.md embed stored here)
                          → MemoryFiles.write_all_files() → all context files

                 Context File Outputs (memory_files.py — no LLM, deterministic)
                 ─────────────────────────────────────────────────────────────────
After every commit        write_root_files() → CLAUDE.md, .cursorrules, code.md, GEMINI.md, AGENTS.md
                              + _embed_code_md() → mem_ai_project_facts(fact_key='code_structure')
On /memory POST           write_all_files() → all files above + feature CLAUDE.md files
Session start hook        /memory/regenerate?scope=root → write_root_files() (same as after commit)
```

---

## 2. LLM Prompts — Complete Inventory

All prompts are in `backend/prompts/*.yaml`, loaded via `core/prompt_loader.py`.
No inline prompt strings remain in Python.

| Prompt Key | File | Model | Max Tokens | Trigger | Input | Output |
|---|---|---|---|---|---|---|
| `project_synthesis` | command_memory.yaml | Haiku | 2000 | POST /memory | Recent history + PROJECT.md + current state | project_state.json (key_decisions, tech_stack, in_progress, project_summary) |
| `conflict_detection` | command_memory.yaml | Haiku | 300 | POST /memory → MemoryPromotion | Old fact value + new fact value | resolution type + merged value → mem_ai_project_facts |
| `tag_suggestion` | misc.yaml | Haiku | 100 | POST /memory (route_projects) | Recent 5 developer prompts | `{"phase":"...", "feature":"..."}` → shown in /memory response |
| `feature_auto_detect` | misc.yaml | Haiku | 60 | POST /chat/hook-log | List of existing features + new prompt | `{"feature":"..."}` → auto-sets session feature tag |
| `memory_context_compact` | command_memory.yaml | n/a (static) | — | write_all_files() → compact/cursor files | n/a | Preamble injected into .cursorrules, copilot instructions |
| `memory_context_full` | command_memory.yaml | n/a (static) | — | write_all_files() → CLAUDE.md | n/a | Preamble injected into CLAUDE.md, GEMINI.md, AGENTS.md |
| `memory_context_openai` | command_memory.yaml | n/a (static) | — | write_all_files() → api/system_prompt.md | n/a | Preamble for OpenAI/API system prompt |
| `commit_analysis` | event_commit.yaml | Haiku | varies | POST /git/commit-store | Commit hash + message + diff | Tags (phase, feature, bug_ref) + summary |
| `commit_symbol` | event_commit.yaml | Haiku | varies | extract_commit_code() background | Per-symbol diff snippet | llm_summary per class/method |
| `commit_message` | event_commit.yaml | Haiku | varies | POST /git/commit-push | Staged diff | Generated commit message |
| `react_pipeline_base` | agent_react.yaml | n/a (static) | — | agents/agent.py startup | n/a | System prompt prefix for all pipeline agents |
| `react_suffix` | agent_react.yaml | n/a (static) | — | agents/agent.py (run mode) | n/a | Shorter ReAct format for non-pipeline agent.run() |
| _(classify)_ | command_work_items.yaml | Haiku | 4000 | POST /wi/classify | Batched event texts (prompts + commits + items, ~6000 tokens/batch) | JSON array of work items with wi_type, score, parent |
| _(summarise)_ | command_work_items.yaml | Haiku | 2000 | POST /wi/{id}/summarise | UC name + current children list | new_summary + reordered children |
| _(reclassify)_ | command_work_items.yaml | Haiku | 120 | POST /wi/{id}/reclassify | Current item name/summary/status | wi_type + score_importance + score_status |

**Total LLM calls**: ~6 active Haiku call paths; 3 static preambles (no LLM call); all logged to `mng_usage_logs`.

**Issue found & fixed**: `tag_suggestion` was defined in both `misc.yaml` (full prompt) and `command_memory.yaml` (empty stub). Since files sort alphabetically, `misc.yaml` was winning silently. Stub removed from `command_memory.yaml`.

---

## 3. Memory Layers — Current State

### Layer 1: Raw Capture (`mem_mrr_*`)

| Table | Populated By | Event | Used For |
|---|---|---|---|
| `mem_mrr_prompts` | Claude Code stop hook → POST /chat/hook-log | Every session end | Work item classification source |
| `mem_mrr_commits` | git post-commit hook → POST /git/commit-store | Every git push | Classification + commit_analysis LLM |
| `mem_mrr_commits_code` | extract_commit_code() background | After each commit | code.md rendering (hotspots, symbols) |
| `mem_mrr_commits_file_stats` | extract_commit_code() background | After each commit | hotspot_score, bug_commit_count |
| `mem_mrr_commits_file_coupling` | extract_commit_code() background | After each commit | File co-change coupling detection |
| `mem_mrr_items` | Manual POST /items | Never in practice | Intended for meeting notes / docs — **EMPTY** |
| `mem_mrr_messages` | Manual POST /messages | Never in practice | Intended for Slack/chat — **EMPTY** |

**Assessment**: The two active sources (prompts + commits) are well-captured and auto-tagged. `mem_mrr_items` and `mem_mrr_messages` are unused — classify prompt context is prompt+commit only.

### Layer 2: Project Facts (`mem_ai_project_facts`)

**Structure**: `fact_key`, `fact_value`, `category` (stack/pattern/convention/constraint/general/code), `embedding VECTOR(1536)`, `valid_until`

**Written by**:
1. POST /memory → `_auto_populate_project_facts()` — extracts 5-10 facts from PROJECT.md + Haiku synthesis (batch-embedded outside DB connection ✓ fixed this session)
2. `_embed_code_md()` — stores code.md snapshot as `fact_key='code_structure'` category='code' for semantic search

**Assessment**: Facts are sparse in practice. The key LLM context comes from `project_state.json` (also written by /memory), not from this table. The `code_structure` fact is the most useful — it makes the full code map searchable via MCP `search_memory`.

### Layer 3: Work Items (`mem_work_items`)

**Lifecycle**: raw event → [classify] → draft (wi_id=AI0001) → [approve] → approved (wi_id=BU0001)

**Approved items embed**: `_embed_work_item()` includes name + wi_type + summary + deliveries + delivery_type + acceptance_criteria (added this session ✓).
**Re-embed trigger**: approve() + update() when semantic fields changed.
**Markdown file**: Written to `workspace/{project}/documents/use_cases/{slug}.md` on approval.

**Assessment**: Well-structured. Approve/embed/MD chain is solid. Score (`score_importance`, `score_status`) is LLM-assigned at classify time, user-read-only at approve time.

---

## 4. Component Analysis

### 4A. code.md — Is it well-defined and well-triggered?

**Content**: Dir tree (depth 3) + recently changed symbols (class/method from mem_mrr_commits_code) + hotspot files table (score, commits, lines, bugs) + coupling pairs table.

**Trigger chain**:
```
git push → POST /git/commit-store
   → extract_commit_code() [background thread]
       → mem_mrr_commits_code (tree-sitter per-symbol)
       → mem_mrr_commits_file_stats (hotspot recompute)
       → write_root_files() → code.md [written]
           → _embed_code_md() → mem_ai_project_facts[code_structure] [embedded]
```
**Session start**: hook calls `POST /memory/regenerate?scope=root` → same `write_root_files()` path.
**On /memory**: `write_all_files()` → same path.

**Assessment**: ✓ Well-triggered. code.md is always current after each commit AND embedded for semantic search. The "code.md not refreshed on session start" gap from the previous audit was already fixed.

**Gap**: code.md shows recently-changed symbols and hotspots but does **not** include a list of all module/class public APIs (only what changed in recent commits). An LLM reading code.md knows what's hot but not the full project interface.

### 4B. PROJECT.md — Is it well-maintained?

**Content**: Vision + Core Goals (user-managed) + Conventions + Recent Work + Key Decisions (both auto-updated by /memory).

**New this session**: `## Deprecated` section — user lists superseded decisions; they are filtered from CLAUDE.md key_decisions automatically.

**Assessment**: ✓ Vision and Core Goals are static (user-managed). Key Decisions auto-update on /memory. The Deprecated mechanism prevents stale architecture from polluting LLM context. The main gap is that Key Decisions come from Haiku synthesis over *prompts* — not from direct code reading — so they lag behind code changes that haven't been discussed.

### 4C. Project Facts (`mem_ai_project_facts`) — Are they updated and non-duplicate?

**Current state**: Facts are upserted on each /memory run. `valid_until=NOW()` marks old facts stale before inserting new ones (per category). Key normalization (snake_case + dedup) prevents exact duplicates.

**Assessment**: Works for explicit `/memory` runs. Facts are NOT auto-updated on commits — if you switch from JSONL to DB without running `/memory`, the facts stay stale. The conflict_detection LLM prompt handles contradictions when a new fact contradicts an existing one, but it only runs during `/memory` synthesis.

**Gap**: No auto-trigger for fact refresh after architectural changes (only prompts can detect them).

### 4D. Approved Work Items — Are they well-used?

**Shown in CLAUDE.md**: Top 12 approved (non-done), bug-type first. In-progress items shown separately with due dates. Acceptance_criteria shown for use_cases.

**Embed**: Full text embedding (name + summary + deliveries + AC) on approve + re-embed on update.

**Assessment**: ✓ Well-used. Both the human-readable CLAUDE.md section and the semantic search embedding are populated. The `_embed_work_item` now includes acceptance_criteria (fixed this session ✓).

### 4E. Unapproved/Draft Work Items — Are they visible?

**Current state**: AI-draft items (wi_id LIKE 'AI%') are NOT shown in CLAUDE.md or embedded. User must open the Work Items UI to see them.

**Rationale** (confirmed with user): These items can be entirely user-replaced, so showing them to LLM is noise. Only the count *could* be surfaced. Decision: do not show unreviewed items.

**Assessment**: ✓ Correct behavior. The classify() run purges all AI drafts before regenerating — so CLAUDE.md is never polluted with potentially-wrong AI classifications.

### 4F. Architectural Overrides — Are old decisions replaced?

**Mechanism**: `## Deprecated` section in PROJECT.md (added this session ✓). User adds phrases; `_load_context()` parses them; renderers filter `key_decisions` containing those phrases.

**Also**: `project_synthesis` Haiku prompt explicitly says "PROJECT.md is authoritative — replace stale decisions" so fresh /memory runs naturally supersede old entries.

**Assessment**: ✓ Both mechanisms in place. The `## Deprecated` gives instant suppression without needing a /memory run.

### 4G. CLAUDE.md — Does it have complete, current project understanding?

**Sections rendered deterministically from DB**:
- Key Architectural Decisions (from project_state.json synthesis)
- Project Documentation (from PROJECT.md Vision + Core Goals)
- Code Hotspots (from mem_mrr_commits_file_stats)
- Recently Changed symbols (from mem_mrr_commits_code)
- Active Features/Work Items (from mem_work_items, approved only)
- In Progress items (from mem_work_items user_status='in-progress')
- Coding Conventions (from PROJECT.md ## Conventions)
- Tech Stack (from project_state.json)

**Assessment**: ✓ Well-structured. All sections have clear DB sources with token-budget rolloff (oldest symbols dropped first). The main gap is "Recent Work" shows old prompt summaries that aren't refreshed frequently.

---

## 5. Work Item Flows

### Classification Trigger
```
Events piling up in mem_mrr_* (wi_id IS NULL)
    → Manual: POST /wi/classify
    → Auto (threshold mode): route_git.py + route_chat.py check unprocessed token counts
      (prompts: 2000 tokens, commits: 1000, messages: 5000, items: 500)
    → Haiku batch (6000 tokens/batch) → JSON array of work items
    → Draft rows: use_cases first (AI0001), children linked via wi_parent_id
```

### Approve Chain
```
User approves in UI
    → Assign real wi_id (US0001/BU0001/FE0001/TA0001)
    → _embed_work_item() → VECTOR(1536) stored
    → Tag mem_mrr_* rows with real wi_id (marks events as processed)
    → _write_md_file() → documents/use_cases/{slug}.md written
    → write_root_files() triggered → CLAUDE.md refreshed
```

### Score System
| Field | Set By | Meaning |
|---|---|---|
| `score_importance` | Haiku at classify time (1-5) | How important this item is |
| `score_status` | Haiku at classify time (1=not started, 3=in progress, 5=done) | LLM-estimated progress |
| `user_status` | User explicitly in UI | Authoritative status (open/pending/in-progress/review/blocked/done) |

`score_status` is supplementary — `user_status` is the source of truth for CLAUDE.md and MCP queries.

### Commit → Work Item Link
When a commit is stored, `_extract_commit_type()` parses the message for conventional prefixes (fix/feat/refactor). The `wi_id` on `mem_mrr_commits` gets set to the related work item on classification/approval. However, "fixes BU0012" in a commit message does **not** auto-resolve the bug — user must manually update `user_status`.

**Gap**: No auto-closure from commit messages.

### Code Events → Classification Context
`_ClassifyMixin._load_existing_context()` fetches:
- Recent hotspot file names (from mem_mrr_commits_file_stats)
- Per-symbol llm_summaries (from mem_mrr_commits_code, last 20 symbols)
These are injected into the Haiku classify prompt, giving the LLM awareness of which files are changing and what the code-level changes mean.

**Assessment**: ✓ Code changes feed directly into classification quality. File hotspots and symbol summaries are used.

---

## 6. Embedding / MCP Strategy

### What Is Embedded

| Data | When | Table | Used For |
|---|---|---|---|
| Approved work items | approve() + re-embed on update | mem_work_items.embedding | search_memory (semantic) + search/semantic endpoint |
| code.md snapshot | write_root_files() after every commit + /memory | mem_ai_project_facts (code_structure) | search_memory("code structure") |
| Project facts | /memory POST → batch outside DB conn (fixed ✓) | mem_ai_project_facts | search_memory (facts/conventions) |

**Not embedded** (correct):
- Raw prompts/commits (too noisy, too many tokens)
- Per-symbol diffs (code.md re-embed covers this at file-map level)
- Draft (unapproved) work items (cost + noise)

**Assessment**: ✓ Strategy is sound. One searchable "code map" chunk re-embedded on every commit is better than thousands of fragmented symbol rows. Approved work items are the right granularity for semantic search.

### MCP Tools (16 registered)

| Tool | Endpoint | Useful? | Notes |
|---|---|---|---|
| `search_memory` | GET /search/semantic | ✓ | Semantic over work items + code_structure + facts |
| `get_project_state` | GET /projects/{p}/state | ✓ | Tech stack, key decisions, in-progress |
| `get_recent_history` | GET /history/{p} | ✓ | Last N prompts with phase/feature filter |
| `get_commits` | GET /history/{p}/commits | ✓ | Tagged commits |
| `get_tagged_context` | GET /history/{p}/tagged | ✓ | All events for a phase or feature |
| `list_work_items` | GET /wi/{p} | ✓ | Filter by type, status, `due_date_before` (added ✓) |
| `get_item_by_number` | GET /wi/{p}/number/{n} | ✓ | Full detail for one item |
| `create_entity` | POST /wi/{p} | ✓ | Create unapproved item |
| `run_work_item_pipeline` | POST /wi/{p}/{id}/summarise | ✓ | Haiku 4-agent summary |
| `get_hotspots` | GET /memory/{p}/hotspots | ✓ | Direct file churn query |
| `get_file_history` | GET /memory/{p}/file-history | ✓ | Per-file symbol changes |
| `get_session_tags` / `set_session_tags` | GET/PUT /tags | ✓ | Phase/feature tracking |
| `commit_push` | POST /git/{p}/commit-push | ✓ | Cursor session commits |
| `get_roles` | GET /agent-roles | ✓ | Agent role definitions |
| `get_db_schema` | n/a (static) | ✓ | Schema reference |
| `sync_github_issues` | n/a | ✗ stub | Not implemented — returns error message |

**`search_work_items`**: confirmed removed (was only in a comment). ✓
**`get_hotspots`**: confirmed present. ✓
**`due_date_before` on `list_work_items`**: added this session. ✓

### Can MCP Answer Key Questions?

| Question | Tool | Works? |
|---|---|---|
| What are the open bugs? | `list_work_items(category=bug)` | ✓ |
| What is the tech stack? | `get_project_state` | ✓ |
| What are coding conventions? | `search_memory("conventions")` | ✓ via facts embed |
| What is the code structure? | `search_memory("code structure")` | ✓ via code.md embed |
| What files are hotspots? | `get_hotspots` | ✓ direct |
| What changed recently? | `get_commits` | ✓ |
| What items are overdue? | `list_work_items(due_date_before="2026-04-27")` | ✓ (added) |
| What is in progress? | `get_project_state` or `list_work_items(status=active)` | ✓ |
| All commits for bug BU0012? | — | ✗ no direct tool |
| Did this commit fix a bug? | — | ✗ no commit→item closure |
| What's the naming prefix policy? | `search_memory("naming convention prefix")` | ⚠ only if in PROJECT.md/facts |

---

## 7. Code Quality Notes (Last 10-15 Prompts)

### Changes Made This Session
| Change | File | Quality |
|---|---|---|
| Split memory_work_items.py into mixins | `_wi_classify.py` (598L), `_wi_markdown.py` (509L), `_wi_helpers.py` (271L) | ✓ Good separation; mixin pattern is idiomatic |
| Added AC to _embed_work_item | `_wi_helpers.py` | ✓ Simple 1-line add |
| Fixed batch embed outside DB | `route_projects.py` | ✓ Correct — avoids N HTTP calls while holding pool connection |
| `## Deprecated` parsing | `memory_files.py` | ✓ Clean; reuses existing section-parsing loop |
| `due_date_before` MCP filter | `server.py` | ✓ Client-side slice; ISO string compare is lexicographically correct |
| Removed `tag_suggestion` stub | `command_memory.yaml` | ✓ Eliminated silent duplicate |

### Remaining Code Quality Issues

| Issue | File | Severity |
|---|---|---|
| `_WI_STATUS_LABELS` has dead int→str entries (0–5) | `memory_files.py:83` | Low — works but misleading after m079 |
| `memory_work_items.py` still 1343 lines | `memory_work_items.py` | Medium — CRUD methods are dense; could split approve/reject/version into `_wi_crud.py` |
| `sync_github_issues` in MCP returns a static error | `server.py` | Low — should be removed from tool list or implemented |
| Token counting uses `len(text)//4` approximation | `_wi_classify.py` | Low — rough but sufficient for batching |
| `_WI_SQL_*` constants in memory_work_items.py overlap with `_wi_helpers.py` SQL | Both files | Low — not duplicated but could be unified under `_wi_helpers.py` |

---

## 8. What Is Missing (Major Gaps Only)

| # | Gap | Component | Impact |
|---|---|---|---|
| 1 | **`mem_mrr_items` and `mem_mrr_messages` are never populated** — classify has no meeting-note or Slack context | Layer 1 | Medium — LLM misses non-code decisions if team doesn't use commit messages + Claude Code exclusively |
| 2 | **No commit→item auto-closure** — "fixes BU0012" in commit msg does not set `user_status=done` | Work Items | Medium — requires manual update; easy to miss |
| 3 | **Project facts lag behind code** — `mem_ai_project_facts` only updated on manual `/memory` run; architectural changes not auto-detected from commits | Layer 2 | Medium — stale facts between `/memory` runs |
| 4 | **`project_state.json` synthesis not triggered after commits** — key_decisions may be weeks old if user doesn't run `/memory` | Memory Files | Medium — CLAUDE.md tech_stack / key_decisions can lag |
| 5 | **Hotspot work items only suggested on `/memory`** — `_suggest_hotspot_work_items()` not called from commit pipeline | Work Items | Low — refactor suggestions appear slowly |
| 6 | **`sync_github_issues` MCP tool is a dead stub** — returns error; wastes tool-list space | MCP | Low — remove from tool list |
| 7 | **No overdue items section in CLAUDE.md** — requires MCP call with `due_date_before` | Memory Files | Low — now possible via MCP but not auto-surfaced |

---

## 9. Major Improvements Per Component

### Memory Files
| Action | Impact |
|---|---|
| Add a lightweight `/memory/quick-sync` endpoint triggered after commits — re-runs just `project_synthesis` (no file writes) → updates `project_state.json` | key_decisions stay current without full /memory cost |
| Add `## Overdue` section to CLAUDE.md renderer showing items where `due_date < today AND user_status != 'done'` | LLM immediately aware of missed deadlines |

### Work Item Flows
| Action | Impact |
|---|---|
| Parse "fixes BU\d+\|closes FE\d+" from commit messages in `route_git.py`; call `update(wi_id, user_status='done')` | Closes commit→item gap; zero user friction |
| Surface unprocessed event count in CLAUDE.md (e.g. "23 unclassified events — run `/classify`") | LLM and user know when classification is overdue |

### MCP / Embedding
| Action | Impact |
|---|---|
| Remove `sync_github_issues` from tool list (or implement it) | Reduces schema noise; reduces LLM confusion |
| Add `parent_name` to `list_work_items` response | LLM can understand work item hierarchy without extra calls |
