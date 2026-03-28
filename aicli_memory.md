# aicli Memory System — Architecture Reference

_Last updated: 2026-03-28_

---

## Overview

aicli uses a **5-layer memory architecture** that persists context across every AI tool —
Claude Code, Cursor, the web UI, the aicli CLI, and pipeline agents.

Storage is **dual-track**: JSONL files (fast write, portable, no DB required) + PostgreSQL
(query, search, analytics). The two tracks are kept in sync by the `/memory` command.

---

## The 5 Layers at a Glance

| Layer | Storage | Written by | Purpose |
|-------|---------|------------|---------|
| 1 — Immediate | In-memory (Python list) | LLM provider adapters | Current conversation window |
| 2 — Working | `history.jsonl` + `pr_interactions` | Hooks + chat.py + pipeline | Raw prompts + responses |
| 3 — Project | `CLAUDE.md`, `MEMORY.md`, `context.md`, `rules.md`, `copilot.md` | `/memory` command | Synthesized files read by each AI tool |
| 4 — Historical | `pr_events`, `pr_commits`, `pr_embeddings` | Background sync + hooks | Permanent tagged + searchable record |
| 5 — Global | `pr_memory_items`, `pr_project_facts` | `/memory` distillation pipeline | Distilled facts + summaries |

---

## Layer 1 — Immediate Context

**Storage**: Python list in RAM (never written to disk).

**Contents**: System prompt + conversation turns + tool call results.

**Written by**: Provider adapters in `backend/agents/providers/` during live session.

**Lifespan**: Lost on process exit. This is the LLM's context window only.

---

## Layer 2 — Working Memory

The raw material that feeds all summarization. Every prompt and response ends up here.

### Files

| File | Written by | Contents |
|------|-----------|----------|
| `workspace/{p}/_system/history.jsonl` | `log_user_prompt.sh` + `chat.py` | All prompts + responses (max 500 rows before rotation) |
| `workspace/{p}/_system/commit_log.jsonl` | `auto_commit_push.sh` | Commit outcomes (hash, message, push status) |
| `workspace/{p}/_system/dev_runtime_state.json` | `log_session_stop.sh` | last_session_id, session_count, last_provider |
| `workspace/{p}/_system/project_state.json` | `/memory` command | tech_stack, key_decisions, in_progress, last_memory_run, _synthesis_cache |

### Database — `pr_interactions`

**Primary prompt/response log**. This is the table that feeds session summarization.

```
id (UUID), client_id=1, project
session_id      — links all prompts in a session
event_type      — always 'prompt' for user messages
llm_source      — 'claude_cli', 'ui', 'pipeline:{role}'
source_id       — matches history.jsonl `ts` field (UNIQUE where not null)
prompt          — user prompt text
response        — assistant response text
phase           — current phase tag at time of prompt
tags[]          — string tag array
work_item_id    — FK → pr_work_items (if tagged to a work item)
metadata        — JSONB extra fields
```

**Written by**:
- `route_chat._append_history()` — every UI chat response
- `orchestrator.py` `AgentWorkflow` — after each pipeline stage completes
- `session_bulk_tag()` also writes `pr_interaction_tags` linking interactions → work_items

**Read by**: `_summarize_session_memory()` — the session distillation pipeline

---

## Layer 4 — Historical Knowledge

The permanent, append-only record. Never summarized away. Used for tagging and semantic search.

### `pr_events` — The Tagging Layer

All timestamped project events, imported from history.jsonl and commit_log.jsonl.

```
id (SERIAL), client_id=1, project
event_type      — 'prompt' | 'commit' | 'tool'
source_id       — history.jsonl `ts` timestamp OR commit hash
title           — first 200 chars of prompt, or commit message
content         — full text
phase, feature  — session tag values at time of event
session_id      — links commits to prompts in same session
metadata        — JSONB (session_id, provider, etc.)
```

**Written by**: `_do_sync_events()` — bulk import from history.jsonl + pr_commits.
**Read by**:
- `pr_event_tags` — entity value links (Planner tagging system)
- `get_tagged_context` MCP tool — retrieves all events for a phase/feature
- `/search/tagged` — REST endpoint for phase/feature filtered events
- `_detect_relationships()` — creates `pr_event_links` (causal links between events)

### `pr_event_tags` — Entity Tag Links

```
event_id (FK → pr_events), entity_value_id (FK → mng_entity_values),
auto_tagged (bool), created_at
```

Every time a user tags a History entry in the Planner, a row is inserted here.
Auto-propagation also copies tags from prompt events to commit events in the same session.

### `pr_event_links` — Causal Relationships

```
from_event_id, to_event_id, link_type (implements|fixes|causes|relates_to|references|closes)
```

Created by `_detect_relationships()` — keyword scan (fix/close/resolve in commit messages) + Haiku semantic analysis.

### `pr_commits` — VCS Commits

```
id, client_id=1, project
commit_hash, commit_msg, summary
phase, feature, bug_ref
session_id, prompt_source_id
```

**Written by**: `auto_commit_push.sh` hook → `POST /git/{project}/commit-push`.

### `pr_embeddings` — pgvector Semantic Index

```
id, client_id=1, project
source_type     — 'history' | 'commit' | 'role' | 'doc' | 'memory_item' | 'node_output'
source_id       — matches source record (timestamp for history, hash for commit, filename for role)
chunk_index     — 0-based chunk number within the source
content         — chunk text
embedding       — vector(1536) — OpenAI text-embedding-3-small
chunk_type      — 'full' | 'summary' | 'class' | 'function' | 'section' | 'file_diff'
doc_type        — 'session_summary' | 'commit_diff' | 'role_prompt' | 'feature_summary' | ...
language        — 'python' | 'javascript' | ...
file_path       — for code chunks: which file
metadata        — JSONB: phase, feature, entity_tags ([{id, name, category}])
```

**Unique key**: `(client_id, project, source_type, source_id, chunk_index)` with `ON CONFLICT DO UPDATE` — re-running `/memory` updates in-place, no duplicates.

---

## Two Event Tables — Why Both Exist

The most common question: **why are there two "event" tables?**

| Aspect | `pr_interactions` | `pr_events` |
|--------|------------------|-------------|
| Written by | `chat.py` (UI), `orchestrator.py` (pipeline) | `_do_sync_events()` (bulk import from JSONL) |
| When written | Real-time, immediately after each prompt | Async, during `/memory` background sync |
| Primary columns | `prompt`, `response`, `session_id`, `work_item_id` | `event_type`, `source_id`, `title`, `content` |
| Read by | `_summarize_session_memory()` | `pr_event_tags`, MCP `get_tagged_context` |
| Purpose | Session summarization feed | Entity tagging + causal relationship tracking |
| Format | Full prompt + response text | Title + short content, typed as prompt/commit/tool |

**The chain**:
```
pr_interactions → _summarize_session_memory() → pr_memory_items → pr_project_facts
pr_events       → pr_event_tags               → pr_embeddings.metadata (entity filter)
```

**Can they be merged?** Technically yes — both hold prompt text. In practice they serve
different read patterns:
- `pr_interactions` is optimized for `GROUP BY session_id HAVING COUNT(*) >= 3` (sequential scan of text)
- `pr_events` is optimized for `JOIN pr_event_tags ON event_id` (lookup by entity)

A future refactor could unify them with a single `pr_events` table that gains the
`response`, `work_item_id`, and `session_id` columns from `pr_interactions`. This would
eliminate the sync step and simplify the architecture. The main risk: the bulk import
pattern (`_do_sync_events`) would need to be replaced by real-time writes.

---

## Layer 5 — Global / Distilled Knowledge

The most valuable layer. Slow to build, but extremely precise context.

### `pr_memory_items` — Trycycle-Reviewed Summaries

```
id (UUID), client_id=1, project
scope           — 'session' | 'feature'
scope_ref       — session_id (for session) | work_item name (for feature)
content         — synthesized summary (Trycycle improved if score < 7)
source_ids      — UUID[] — which pr_interactions rows were summarized
reviewer_score  — 1-10 Haiku quality rating
reviewer_critique — Haiku critique text
```

**Two scopes**:

**`scope='session'`**: Created by `_summarize_session_memory()`. Triggered by `/memory`.
Summarizes all `pr_interactions` for sessions with ≥3 prompts not yet in memory_items.
Two Haiku calls (summarize → Trycycle review). One row per session_id.

**`scope='feature'`**: Created by `_summarize_feature_memory()`. Triggered when a work item
`lifecycle_status` is set to `'done'`. Collects session memory_items whose `source_ids`
overlap with that work item's `pr_interaction_tags`, then uses two Haiku calls to write
a permanent feature postmortem. One row per work item (scope_ref = work item name).

Both scopes are immediately embedded into `pr_embeddings` (doc_type = 'session_summary'
or 'feature_summary') for semantic search.

### `pr_project_facts` — Durable Facts with Temporal Validity

```
id (UUID), client_id=1, project
fact_key        — e.g. 'auth_method', 'database', 'rel:auth:jwt'
fact_value      — e.g. 'JWT + bcrypt', 'PostgreSQL 15 + pgvector', 'implements'
valid_from      — timestamptz (when this fact was first extracted)
valid_until     — NULL = currently true; NOT NULL = superseded by newer value
source_memory_id — FK → pr_memory_items (which summary produced this fact)
```

**Written by**: `_extract_project_facts()`. Reads the 6 most recent `pr_memory_items` rows,
calls Haiku (via the `internal_project_fact` role from `mng_agent_roles`), gets back
`[{key, value, confidence}]`, and upserts with temporal validity.

**Temporal upsert**: If a fact's value changes (e.g. auth method switches), the old row
gets `valid_until = NOW()` and a new row is inserted. Full audit trail always preserved.
Query what was true at any past timestamp: `WHERE valid_until IS NULL OR valid_until > $ts`.

**The chain**:
```
pr_interactions (≥3 prompts/session)
        ↓  _summarize_session_memory()  [2× Haiku, Trycycle]
        ↓
pr_memory_items (scope='session')
        ↓  _extract_project_facts()  [1× Haiku via internal_project_fact role]
        ↓
pr_project_facts (fact_key → fact_value, valid_until=NULL means current)
        ↓  _synthesize_with_llm()  [1× Haiku]
        ↓
5 output files (MEMORY.md, CLAUDE.md, context.md, rules.md, copilot.md)
```

**Feature path (separate chain)**:
```
work_item lifecycle → 'done'
        ↓  _summarize_feature_memory()  [2× Haiku, Trycycle]
        ↓
pr_memory_items (scope='feature', scope_ref=work_item_name)
        ↓  [feeds next _extract_project_facts() run]
        ↓
pr_project_facts
```

---

## What Happens When You Run `/memory`

`POST /projects/{name}/memory` — full sequence in `route_projects.py:generate_memory()`:

```
1. Load config
   - project.yaml: history_max_rows (500), memory_threshold (20), code_dir
   - project_state.json: last_memory_run, tech_stack, key_decisions, _synthesis_cache

2. Load raw history
   - Read history.jsonl (last 120 lines)
   - Filter noise (entries starting with <task-notification>, <tool-use-id>, etc.)
   - Keep last 40 meaningful entries (user_input non-empty, not noisy)

3. Rotate history if > history_max_rows
   - Archive: history_{YYMMDDHHMM}.jsonl (named from first archived entry's ts)
   - Keep: most recent max_rows in history.jsonl

4. Load entity summary
   - SQL: mng_entity_values JOIN mng_entity_categories (active values only, not archived)
   - Returns per-category groups with event_count, commit_count per entity
   - Formatted for LLM: "[feature] react-agents (active) | 12 events, 3 commits"

5. Session distillation — _summarize_session_memory(project)   [AWAITED — runs before synthesis]
   - Finds sessions in pr_interactions with ≥3 prompts, no pr_memory_items row yet
   - For each session (up to 10 per /memory run):
       Haiku Call 1: summarize → Haiku Call 2: Trycycle review
       INSERT pr_memory_items(scope='session', reviewer_score, source_ids)
       fire-and-forget: embed_and_store() → pr_embeddings
   - See exact prompts below

6. Load distilled context
   - pr_project_facts WHERE valid_until IS NULL (all current facts)
   - pr_memory_items ORDER BY created_at DESC LIMIT 8 (most recent summaries)
   - Formatted: "[Project Facts]\n  auth_method: JWT + bcrypt\n...\n\n[Recent Memory Summaries]\n..."

7. LLM synthesis — _synthesize_with_llm()
   - Incremental check: new entries since last_memory_run < 10 AND distilled_memory_items exist?
       YES → send only new_entries + distilled context (8× cheaper)
       NO  → send all 40 recent raw history entries
   - See exact prompt below
   - Returns {key_decisions, in_progress, tech_stack, memory_digest, project_summary}
   - Merged into project_state.json (LLM wins on new fields, prior stable decisions preserved)

8. Write 5 output files (Layer 3)
   - _system/claude/MEMORY.md  → copies to <code_dir>/MEMORY.md
   - _system/claude/CLAUDE.md  → copies to <code_dir>/CLAUDE.md
   - _system/cursor/rules.md   → copies to <code_dir>/.cursor/rules/aicli.mdrules
   - _system/aicli/context.md  (compact 600-char block, injected by CLI)
   - _system/aicli/copilot.md  → copies to <code_dir>/.github/copilot-instructions.md

9. Background tasks (asyncio.create_task — fire-and-forget, run AFTER response sent)
   ├─ _extract_project_facts()
   │   Reads 6 most recent pr_memory_items + existing pr_project_facts
   │   Calls Haiku via internal_project_fact role → [{key, value, confidence}]
   │   Temporal upsert → pr_project_facts
   │
   ├─ ingest_history(since=last_memory_run)
   │   Embeds new history.jsonl entries (chunk_type='full') → pr_embeddings
   │
   ├─ ingest_roles()
   │   Re-embeds all workspace/_templates/roles/*.yaml files
   │   smart_chunk_markdown() → per-section chunks → pr_embeddings
   │
   ├─ ingest_commits(project)
   │   Embeds commits not yet in pr_embeddings (checked via NOT EXISTS subquery)
   │   smart_chunk_diff() → 1 summary + 1 chunk per changed file → pr_embeddings
   │
   ├─ _sync_and_autotag()
   │   Phase 1: Import history.jsonl prompt entries → pr_events
   │   Phase 2: Import pr_commits → pr_events (event_type='commit')
   │   Phase 3: Backfill session_ids on old pr_events rows
   │   Phase 4: SQL auto-propagate entity tags: prompt events → commit events in same session
   │   Then: Haiku tags untagged pr_events with existing mng_entity_values
   │   Background: _detect_relationships() → pr_event_links
   │   Then: backfill_entity_tags() → merges entity_tags into pr_embeddings.metadata
   │
   ├─ _detect_relationships()
   │   Strategy 1 (keyword): commit messages with fix/close/resolve → pr_event_links
   │   Strategy 2 (LLM): Haiku semantic links between events → pr_event_links
   │   link_types: implements, fixes, causes, relates_to, references, closes
   │
   ├─ _auto_create_entities(project, since=last_memory_run)
   │   Scans untagged pr_events since last run
   │   Haiku detects NEW features/bugs/tasks not in mng_entity_values
   │   Creates mng_entity_values at confidence ≥ 0.85 (lifecycle_status='idea')
   │
   └─ _suggest_tags() → suggested_tags returned in API response

10. Update project_state.json: last_memory_run = NOW()

11. Return:
    {
      "generated": ["MEMORY.md", "CLAUDE.md", "rules.md", "context.md", "copilot.md"],
      "copied_to": ["<code_dir>/CLAUDE.md", "<code_dir>/MEMORY.md", ...],
      "synthesized": true,
      "run_ts": "2026-03-28T...",
      "suggested_tags": [{"name": "react-agents", "category": "feature", "is_new": false}]
    }
```

---

## All Internal LLM Prompts — Exact Text

### 1. Session Summary — Call 1 (Haiku, max_tokens=800)

**Function**: `_summarize_session_memory()` in `route_projects.py`

**Trigger**: `/memory` run. Once per unsummarized session (≥3 prompts, no existing memory_item).

**Input query** (builds `history_text` — Q/A pairs truncated to 300/200 chars):
```sql
SELECT i.session_id, COUNT(*) AS cnt,
       ARRAY_AGG(i.id ORDER BY i.created_at) AS ids,
       STRING_AGG(
           '[' || LEFT(i.created_at::text, 16) || '] Q: '
           || LEFT(COALESCE(i.prompt,''), 300)
           || CASE WHEN i.response != '' THEN E'\n A: ' || LEFT(i.response,200) ELSE '' END,
           E'\n\n' ORDER BY i.created_at
       ) AS history_text
FROM pr_interactions i
WHERE i.client_id=1 AND i.project=%s
  AND i.event_type='prompt'
  AND i.session_id IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM pr_memory_items m
      WHERE m.client_id=1 AND m.project=i.project
        AND m.scope='session' AND m.scope_ref=i.session_id
  )
GROUP BY i.session_id
HAVING COUNT(*) >= 3
LIMIT 10
```

**User message**:
```
Summarize this development session — focus on decisions and code changes
(3-8 bullet points max, be specific):

[2026-03-27T14:30] Q: How should I wire the ReAct loop...
 A: The ReAct loop should...

[2026-03-27T14:35] Q: What about the tool registry...
 A: ...
```
_(history_text truncated to 3000 chars)_

---

### 2. Session Summary — Call 2 / Trycycle Review (Haiku, max_tokens=600)

**User message**:
```
Rate this session summary 1-10 for completeness and accuracy.
Return ONLY valid JSON: {"score": N, "critique": "...", "improved_summary": "..."}.

Original session:
{history_text[:2000]}

Summary to rate:
{output of Call 1}
```

**Logic**: if `score < 7` → use `improved_summary`; else use original summary.

**Stored** in `pr_memory_items(scope='session', scope_ref=session_id, reviewer_score, source_ids)`.

---

### 3. Feature Summary — Call 1 (Haiku, max_tokens=600)

**Function**: `_summarize_feature_memory()` in `route_projects.py`

**Trigger**: Work item `lifecycle_status` set to `'done'`.

**Input query** (finds session summaries whose `source_ids` overlap with the work item's interactions):
```sql
SELECT m.content
FROM pr_memory_items m
WHERE m.client_id=1 AND m.project=%s AND m.scope='session'
  AND EXISTS (
      SELECT 1 FROM pr_interaction_tags it
      WHERE it.work_item_id=%s::uuid
        AND it.interaction_id = ANY(m.source_ids)
  )
ORDER BY m.created_at
LIMIT 10
```

**User message**:
```
Summarize the complete development history for feature '{wi_name}': {wi_desc}.

Session summaries:
{combined session summaries[:2500]}

Write a concise feature postmortem (decisions, implementation approach, outcome).
```

---

### 4. Feature Summary — Call 2 / Trycycle Review (Haiku, max_tokens=500)

**User message**:
```
Rate this feature summary 1-10. Return ONLY JSON:
{"score": N, "critique": "...", "improved_summary": "..."}.

Summary:
{output of Call 1}
```

**Stored** in `pr_memory_items(scope='feature', scope_ref=work_item_name)`.

---

### 5. Fact Extraction (Haiku via `internal_project_fact` role, max_tokens=600)

**Function**: `_extract_project_facts()` in `route_projects.py`

**Trigger**: Background task after every `/memory` run.

**Input queries**:
```sql
-- Source: 6 most recent memory_items (session + feature scopes combined)
SELECT id::text, content FROM pr_memory_items
WHERE client_id=1 AND project=%s
ORDER BY created_at DESC LIMIT 6

-- Existing facts (for delta — only return changed or new)
SELECT fact_key, fact_value FROM pr_project_facts
WHERE client_id=1 AND project=%s AND valid_until IS NULL
ORDER BY fact_key
```

**System prompt**: Loaded from `mng_agent_roles WHERE name='internal_project_fact' AND project='_global'`.
Configurable in the Roles tab. The default prompt (seeded in `_INTERNAL_FACT_PROMPT` in `database.py`):
```
You are a technical fact extractor for a software project.
Extract ONLY concrete, durable architectural facts from development notes.

Return a JSON array: [{"key": "short_snake_key", "value": "fact value", "confidence": 0.0-1.0}]

Examples of GOOD facts: auth_method, database_engine, frontend_framework, test_runner, deploy_target
Examples of BAD facts: current_task, recent_bug, today_worked_on (not durable)

ALSO extract architectural relationships as facts using key prefix 'rel:':
  {"key": "rel:component_a:component_b", "value": "implements|depends_on|causes|replaces|related_to",
   "confidence": 0.0-1.0}

Return [] if no clear durable facts found. confidence >= 0.70 required.
```

**User message**:
```
Already-extracted facts (confirm if still true, update value if changed, skip if unchanged):
  auth_method: JWT + bcrypt
  database: PostgreSQL 15 + pgvector
  ...

Development notes to analyze:
{last 5 memory_items joined with '---', truncated to 3500 chars}
```

**Response** (expected):
```json
[
  {"key": "auth_method",  "value": "JWT + bcrypt",          "confidence": 0.95},
  {"key": "frontend",     "value": "Electron + Vanilla JS", "confidence": 0.88},
  {"key": "rel:auth:jwt", "value": "implements",            "confidence": 0.90}
]
```

**Temporal upsert**:
```sql
-- Expire old value if it changed
UPDATE pr_project_facts SET valid_until=NOW()
WHERE client_id=1 AND project=%s AND fact_key=%s AND valid_until IS NULL AND fact_value != %s

-- Insert new (ON CONFLICT DO NOTHING if value unchanged)
INSERT INTO pr_project_facts (client_id, project, fact_key, fact_value, source_memory_id)
VALUES (1, %s, %s, %s, %s::uuid)
ON CONFLICT (client_id, project, fact_key) WHERE valid_until IS NULL DO NOTHING
```

---

### 6. LLM Synthesis (Haiku, max_tokens=2000)

**Function**: `_synthesize_with_llm()` in `route_projects.py`

**Trigger**: Every `/memory` run, after sessions are distilled.

**Incremental mode**: If `new_entries_since_last_memory < 10` AND `distilled_memory_items` exist
→ send only new entries + distilled context (8× cheaper than sending all 40 raw entries).

**User message** (exact string built in code):
```
You are analyzing development history for project "{project_name}".

Current structured state:
{json: tech_stack, key_decisions, in_progress from project_state.json}

Prior synthesis (merge, do not discard stable decisions):   ← only if prior_synthesis exists
{json: prior key_decisions, in_progress, tech_stack, project_summary, truncated to 800 chars}

Project intro (from PROJECT.md):
{first section of PROJECT.md, up to 600 chars}

Active project entities (features/bugs/tasks):              ← only if entities exist
{entity_text: "[feature] react-agents (active) | 12 events, 3 commits" per line}

Development history ({N} entries, oldest→newest):
[{ts} | {source}]
Q: {user_input[:300]}
A: {output[:400]}
...

Return ONLY valid JSON (no markdown fences) with exactly these fields:
{
  "key_decisions": ["up to 15 stable architectural/technical decisions any LLM must know"],
  "in_progress": ["up to 6 items most recently worked on, based on last 5 sessions"],
  "tech_stack": {"component": "technology or version"},
  "memory_digest": "Markdown: synthesize the 10 most important recent work items.
                    Format each as: **[date]** `source` — description of what was done/decided.",
  "project_summary": "2-3 sentence description of what this project is and its current state."
}

Rules:
- key_decisions: permanent facts (tech choices, auth approach, architecture patterns)
- in_progress: what was MOST RECENTLY worked on (infer from last 5 sessions)
- tech_stack: merge existing + any new tech mentioned in history
- memory_digest: synthesize meaningfully, don't just copy. Focus on decisions + features.
- Return ONLY valid JSON, no explanation outside the JSON.
```

**Result merged** into `project_state.json`:
```json
{
  "tech_stack": {"backend": "FastAPI", "db": "PostgreSQL 15 + pgvector"},
  "key_decisions": ["JWT auth with bcrypt", "Flat table naming mng_/pr_", ...],
  "in_progress": ["ReAct pipeline wiring", "UI prereq status"],
  "_synthesis_cache": {"memory_digest": "...", "project_summary": "..."}
}
```

---

### 7. Tag Suggestions (Haiku, max_tokens=150)

**Function**: `_suggest_tags()` in `route_projects.py`

**Trigger**: End of every `/memory` run. Runs inline (not background).

**System prompt**:
```
You are a JSON API. Respond with a valid JSON array only. No explanation, no preamble, no markdown.
```

**User message**:
```
Recent developer prompts:
{last 10 history entries, user_input[:200] each, joined by newline}

Existing tags: react-agents, logging, auth-refactor, ...

Suggest 2-3 relevant tags for these prompts. Prefer existing tags where applicable;
propose new ones only if clearly needed.
Respond ONLY as valid JSON array: [{"name":"tag","category":"feature|bug|task","is_new":true}]
```

**Returned** in `/memory` response as `suggested_tags` → shown as amber chips in UI.

---

### 8. Auto-Create Entity Values (Haiku, max_tokens=400)

**Function**: `_auto_create_entities()` in `route_projects.py`

**Trigger**: Background task after every `/memory` run.

**Input**: Untagged `pr_events` since `last_memory_run` (up to 25 events, title only).

**User message**:
```
Analyze these project events and identify NEW entities that should be tracked.

Available entity categories: bug, feature, task

Already tracked (do NOT re-create):
  feature: react-agents
  bug: hook-failure
  ...

Events:
  123: [prompt] How should I wire the ReAct loop...
  124: [commit] feat(agents): add hallucination guard
  ...

Return a JSON array of NEW entities only. Each item:
{"category": "bug|feature|task", "name": "short descriptive name",
 "description": "one sentence", "confidence": 0.0-1.0}

Rules: confidence >= 0.85 required. Return [] if nothing clearly new.
```

**Result**: Creates `mng_entity_values` rows with `lifecycle_status='idea'` at confidence ≥ 0.85.

---

### 9. Bug Auto-Detection (Haiku, max_tokens=400)

**Endpoint**: `POST /projects/{project}/auto-detect-bugs` in `route_projects.py`

**Trigger**: Stop hook fires this after every Claude Code session (fire-and-forget).

**Input**: Last 24h of `pr_events WHERE event_type='prompt'` (up to 15 events).

**User message**:
```
Analyze these developer session notes for bug reports or errors encountered.

Session notes:
  [prompt title] content...
  ...

Return a JSON array of bugs found. Each item:
{"name": "short bug title", "description": "what went wrong and where",
 "confidence": 0.0-1.0}

Rules: confidence >= 0.80 required. Only real bugs/errors, not planned tasks.
Return [] if no bugs found.
```

**Result**: Creates `pr_work_items(status='prereq', lifecycle_status='idea', category_name='bug')` at confidence ≥ 0.80.

---

### 10. The ReAct Base Prompt (injected into every pipeline agent)

**Defined in**: `backend/agents/agent.py` as `_REACT_SYSTEM_BASE`

**Injected when**: `agent.react=True` (DB column), called via `run_pipeline()`.

```
You are an aicli AI agent. You operate in a strict ReAct loop.

## ReAct Rules
- ALWAYS write Thought: before any action
- ONE action per step — never batch multiple tool calls
- ALWAYS wait for the Observation before the next Thought
- NEVER assume a tool result — wait for the actual observation
- NEVER fabricate file contents, test results, or memory
- If unsure, call a tool. Never guess.

## Anti-Hallucination Rules
- If you don't know something, say "I need to check this" and call a tool
- Never describe code you haven't read this session
- Never claim tests pass without running them or reading diff output
- Never reference a past decision unless memory confirms it exists
- If memory returns empty, say "no relevant memory found" — don't invent context
- If a tool fails, reason about why before retrying

## Handoff Rules
- Your final output MUST be a structured JSON object (no markdown fences)
- Never pass raw conversation — only structured, verified facts
- Include "confidence" (0.0–1.0) reflecting how certain you are
- Include "memory_references" citing exactly what memory returned
- Include your "role" field so the next agent knows who produced this
```

A simpler `_REACT_SUFFIX` (no anti-hallucination rules) is used for `run()` mode (non-pipeline).

---

## Smart Chunking for Embeddings

Before embedding, content is split into meaningful chunks via `backend/memory/mem_embeddings.py`:

| Content type | Chunker | Splits on | Rows created |
|-------------|---------|-----------|--------------|
| History entries | none | — single blob `"Q: ...\nA: ..."` | **1 per entry** (chunk_type='full') |
| Markdown docs / role YAML | `smart_chunk_markdown()` | `##` headings; sub-split at `###` if >3000 chars | **N per file** (1 per section) |
| Git diffs | `smart_chunk_diff()` | `diff --git a/... b/...` file boundaries | **1 summary + 1 per changed file** |
| Python/JS code files | `smart_chunk_code()` | `class` / `def` / `function` / `const` top-level | **N per file** (1 per symbol) |

**Deduplication**: `ON CONFLICT (client_id, project, source_type, source_id, chunk_index) DO UPDATE SET content=..., embedding=..., created_at=NOW()`.
Re-running `/memory` updates existing embeddings in-place.

---

## Entity Tags → Embedding Metadata

**The connection**: When you tag a prompt with "auth feature" in the Planner, that tag needs
to flow into `pr_embeddings.metadata` so semantic search can filter by entity.

**How it works**: `backfill_entity_tags(project)` in `mem_embeddings.py` runs a single SQL UPDATE:

```sql
UPDATE pr_embeddings e
SET metadata = e.metadata || jsonb_build_object('entity_tags',
    (SELECT jsonb_agg(jsonb_build_object('id', v.id, 'name', v.name, 'category', c.name))
     FROM pr_events ev
     JOIN pr_event_tags et ON et.event_id = ev.id
     JOIN mng_entity_values v  ON v.id = et.entity_value_id AND v.client_id=1
     JOIN mng_entity_categories c ON c.id = v.category_id AND c.client_id=1
     WHERE ev.client_id=1 AND ev.project=%s AND ev.source_id = e.source_id)
)
WHERE e.client_id=1 AND e.project=%s
  AND EXISTS (
      SELECT 1 FROM pr_events ev
      JOIN pr_event_tags et ON et.event_id = ev.id
      WHERE ev.client_id=1 AND ev.project=%s AND ev.source_id = e.source_id
  )
```

**Result**: `pr_embeddings.metadata` gets an `entity_tags` array:
```json
{
  "phase": "development",
  "feature": "auth",
  "entity_tags": [
    {"id": 5, "name": "auth", "category": "feature"},
    {"id": 12, "name": "UI dropbox", "category": "bug"}
  ]
}
```

**When it runs** (automatically, fire-and-forget):
- After every manual tag in History tab (`POST /entities/events/{id}/tag`)
- After every un-tag (`DELETE /entities/events/{id}/tag/{value_id}`)
- After `_sync_and_autotag()` completes (inside every `/memory` run)

**How to filter by entity in search**:
```
POST /search/semantic
{
  "query": "login error handling",
  "entity_name": "auth",           ← JSONB containment filter on metadata
  "entity_category": "bug",
  "source_types": ["history", "commit"]
}
```

**MCP `search_memory`** now accepts `entity_name` and `entity_category`:
```
search_memory(query="dropbox error", entity_name="UI dropbox", entity_category="bug")
→ returns only embeddings tagged with the "UI dropbox" bug entity
```

---

## Embedding Write Triggers

| Trigger | What gets embedded | Timing |
|---|---|---|
| `/memory` (Stop hook or manual) | New history since `last_memory_run` + new commits + all roles | ~15s after session end |
| Every UI chat response | The Q&A pair | After each response |
| Role file save (Roles tab) | Saved role YAML content | On save |
| Session memory_item created | Session summary text | After each `_summarize_session_memory()` call |
| Feature memory_item created | Feature postmortem text | After `_summarize_feature_memory()` call |
| `/search/ingest` (admin) | History + roles | On demand |
| Graph pipeline node result | Node output text | After each pipeline run |

---

## Complete Tagging System

### What Is an Entity Tag?

A row in `mng_entity_values`:
```
id, client_id=1, project, category_id (FK → mng_entity_categories)
name, description, status (active/done/archived)
lifecycle_status (idea→design→development→testing→review→done)
due_date, parent_id (for nested entities)
seq_num — unique sequential number per category (features: 10000+, bugs: 20000+, tasks: 30000+)
```

### The 4 Tag Tables

| Table | Links | Set by |
|-------|-------|--------|
| `mng_session_tags` | Current session → phase + feature + bug_ref | User (tag bar / MCP set_session_tags) |
| `pr_event_tags` | `pr_events` row → `mng_entity_values` row | Auto-propagation + manual History tagging |
| `pr_interaction_tags` | `pr_interactions` row → `pr_work_items` row | Bulk session tag |
| `mng_entity_value_links` | `mng_entity_values` → `mng_entity_values` | Manual (dependency graph) |

### Tagging Paths

**Path 1 — Session tag bar**:
1. User sets phase/feature in UI → `PUT /history/session-tags`
2. Upserts `mng_session_tags` (one row per project)
3. All subsequent `pr_events` and `pr_interactions` carry `phase` + `feature`

**Path 2 — Manual ⬡ Tag on History entry**:
1. UI sends `POST /entities/events/tag-by-source-id` with `{source_id, entity_value_id}`
2. Backend finds or imports the `pr_events` row, inserts `pr_event_tags`
3. Background: `backfill_entity_tags()` propagates to `pr_embeddings.metadata`

**Path 3 — Bulk session tag (Chat tab)**:
`POST /entities/session-tag` with `{session_id, entity_name, category_name}`:
1. Resolve or create `mng_entity_values` row
2. Tag all `pr_events` for the session → `pr_event_tags`
3. Link all `pr_interactions` to work_item → `pr_interaction_tags`

**Path 4 — Auto-propagation** (runs in `_do_sync_events()`):
```sql
-- Tags from prompt events copy to commit events in the same session
INSERT INTO pr_event_tags (event_id, entity_value_id, auto_tagged)
SELECT DISTINCT commit_ev.id, pt.entity_value_id, TRUE
FROM pr_events commit_ev
JOIN pr_events prompt_ev
     ON COALESCE(prompt_ev.session_id, prompt_ev.metadata->>'session_id')
      = COALESCE(commit_ev.session_id, commit_ev.metadata->>'session_id')
     AND session_id IS NOT NULL AND session_id != ''
JOIN pr_event_tags pt ON pt.event_id = prompt_ev.id
WHERE commit_ev.event_type = 'commit'
  AND prompt_ev.event_type  = 'prompt'
  AND commit_ev.client_id=1 AND commit_ev.project=%s
ON CONFLICT DO NOTHING
```

**Path 5 — AI auto-detection** (`_auto_detect_session_feature()` in `chat.py`):
- Fires on first prompt of a new session if no feature tag is set
- Haiku reads the prompt + last 5 history entries → suggests which feature is being worked on
- If accepted: updates `mng_session_tags.feature`, shows suggestion banner in UI

**Path 6 — Auto-entity creation** (`_auto_create_entities()` — background):
- Haiku scans untagged `pr_events` → creates `mng_entity_values` at confidence ≥ 0.85

**Path 7 — Bug auto-detection** (`auto-detect-bugs` endpoint — fired from Stop hook):
- Haiku scans last 24h prompts → creates `pr_work_items` (bug category) at confidence ≥ 0.80

---

## Complete Hook Logic

### Hook 1: `log_user_prompt.sh` (UserPromptSubmit)

Fires: Every prompt submitted in Claude Code.

```
1. Read stdin JSON: {"hook_event_name":"UserPromptSubmit","session_id":"abc123","prompt":"..."}
2. Extract prompt text and session_id via python3 -c "import json,sys; ..."
3. Detect active project from aicli.yaml
4. Filter noise — skip if prompt starts with:
   <task-notification> | <tool-use-id> | <task-id> | <parameter>
5. Skip empty prompts
6. Write JSONL entry to workspace/{project}/_system/history.jsonl:
   {"ts":"...", "source":"claude_cli", "session_id":"...", "provider":"claude",
    "user_input":"...", "output":"", "tags":[]}
7. exit 0
```

Does NOT write to DB — that happens during `/memory` via `_do_sync_events()`.

---

### Hook 2: `log_session_stop.sh` (Stop)

Fires: When Claude Code finishes responding.

```
1. Read stdin JSON: {"hook_event_name":"Stop","session_id":"abc123","stop_reason":"end_turn"}
2. Extract session_id and stop_reason
3. Detect active project from aicli.yaml
4. Read Claude Code session file:
   ~/.claude/projects/{project-hash}/{session_id}.jsonl
   - Find LAST assistant message (type='assistant')
   - Extract text content blocks (skip tool_use, tool_result)
   - Truncate to 2000 chars
5. Update history.jsonl:
   - Find latest claude_cli entry for this session_id with empty output
   - Fill in: output = response_text, stop_reason = stop_reason
6. Update dev_runtime_state.json: {last_session_id, session_count++, last_provider}
7. Background (non-blocking):
   curl -sf -X POST {BACKEND_URL}/projects/{ACTIVE_PROJECT}/memory &
8. Background (non-blocking):
   curl -sf -X POST {BACKEND_URL}/projects/{ACTIVE_PROJECT}/auto-detect-bugs &
9. exit 0
```

---

### Hook 3: `auto_commit_push.sh` (Stop)

Fires: Same Stop event as log_session_stop.sh.

```
1. Read stdin JSON (same Stop event)
2. Detect WORK_DIR from CLAUDE_PROJECT_DIR env var or pwd
3. Check auto_commit_push in workspace/{project}/project.yaml → if not "yes": exit 0
4. Read CODE_DIR from project.yaml
5. Check .git exists in CODE_DIR → else exit 0
6. Extract session_id
7. Check backend health: curl -sf {BACKEND_URL}/health → BACKEND_OK=yes|no

   If BACKEND_OK=yes:
   → POST {BACKEND_URL}/git/{project}/commit-push
     {message_hint: "after claude cli session {session_id[:8]}",
      provider:"claude", skip_pull:false, session_id, source:"claude_cli"}
   → If committed=true: log to commit_log.jsonl
   → If committed=false: log "skipped/no_changes"

   If BACKEND_OK=no (fallback direct git):
   → git status --porcelain → if empty: exit 0
   → Load GIT_TOKEN, GIT_USERNAME, GITHUB_REPO, GIT_BRANCH from .git_token file
   → git add -A
   → git commit -m "chore(cli): auto-commit after AI session — {N} files — {timestamp}"
   → git push with authenticated URL (token in URL only)
   → Log outcome to commit_log.jsonl
```

---

## MCP Tools — What Each Reads

The MCP server (`backend/agents/mcp/server.py`) exposes 13 tools to Claude Code and Cursor.
Transport: stdio JSON-RPC → HTTP to FastAPI backend. **No direct DB access in the MCP server**.

| Tool | Backend call | Reads from |
|------|-------------|-----------|
| `search_memory` | `POST /search/semantic` | `pr_embeddings` (pgvector cosine, 1536-dim) |
| `get_project_state` | `GET /projects/{p}` + `/entities/summary` + `/work-items/facts` + `/work-items/memory-items` | project_state.json + mng_entity_values + pr_project_facts + pr_memory_items |
| `get_recent_history` | `GET /history/chat` | history.jsonl |
| `get_commits` | `GET /history/commits` | pr_commits |
| `get_tagged_context` | `GET /search/tagged` | pr_events + pr_event_tags + mng_entity_values |
| `get_session_tags` | `GET /history/session-tags` | mng_session_tags |
| `set_session_tags` | `PUT /history/session-tags` | mng_session_tags (write) |
| `commit_push` | `POST /git/{p}/commit-push` | git + pr_commits (write) |
| `create_entity` | `POST /entities/values` | mng_entity_values (write) |
| `list_work_items` | `GET /work-items` | pr_work_items JOIN mng_entity_categories |
| `run_work_item_pipeline` | `POST /work-items/{id}/run-pipeline` | triggers pipeline (write) |
| `get_item_by_number` | `GET /work-items/number/{seq}` | pr_work_items |
| `get_db_schema` | hard-coded DDL | — |

**`search_memory` filters**: `source_types`, `language`, `doc_type`, `file_path`, `chunk_types`,
`phase`, `feature`, `entity_name` (Planner entity), `entity_category` (bug/feature/task).

**`get_project_state` returns**:
```json
{
  "project": "aicli",
  "active_tags": {"phase": "development", "feature": "react-agents"},
  "entities": {"feature": [{...}], "bug": [{...}]},
  "project_facts": {"auth_method": "JWT + bcrypt", "database": "PostgreSQL 15"},
  "recent_memory": [{"scope": "session", "content": "• Implemented ReAct loop..."}]
}
```

---

## Agent Tools (Pipeline Agents — Direct DB Access)

ReAct agents in the pipeline have these tools via `backend/agents/tools/`:

| Tool | File | Reads from |
|------|------|-----------|
| `search_memory` | `tool_memory.py` | `pr_embeddings` (pgvector, direct DB) |
| `get_recent_history` | `tool_memory.py` | `pr_interactions` (direct DB) |
| `get_project_facts` | `tool_memory.py` | `workspace/{p}/_system/project_state.json` |
| `list_work_items` | `tool_workitems.py` | `pr_work_items JOIN mng_entity_categories` |
| `create_work_item` | `tool_workitems.py` | `pr_work_items` + `mng_entity_values` (write) |
| `read_file` | `tool_files.py` | Filesystem (code_dir) |
| `write_file` | `tool_files.py` | Filesystem (code_dir) |
| `list_dir` | `tool_files.py` | Filesystem (code_dir) |
| `git_status` | `tool_git.py` | git (read) |
| `git_diff` | `tool_git.py` | git (read) |
| `git_commit` | `tool_git.py` | git (write) |
| `git_push` | `tool_git.py` | git (write) |

Each agent role's `tools` column in `mng_agent_roles` (JSONB array) controls which subset is available.

---

## Complete Table Reference

All 10 memory-related tables:

| Table | Purpose | Written by | Read by |
|-------|---------|-----------|---------|
| `pr_interactions` | Prompt/response log (session summarization feed) | chat.py + pipeline | `_summarize_session_memory()` |
| `pr_interaction_tags` | Links interactions → work items | `session_bulk_tag()` | `_summarize_feature_memory()` |
| `pr_events` | Typed event ledger (tagging + relationship layer) | `_do_sync_events()` | pr_event_tags, `get_tagged_context` MCP |
| `pr_event_tags` | Events → entity values (Planner tags) | Auto-propagation + History tab | `backfill_entity_tags()`, entity summary |
| `pr_event_links` | Causal event relationships | `_detect_relationships()` | Relationship queries |
| `pr_commits` | VCS commits + metadata | `auto_commit_push.sh` → git endpoint | pr_events sync, commit history |
| `pr_embeddings` | pgvector semantic index | `embed_and_store()`, ingest functions | `semantic_search()`, MCP `search_memory` |
| `pr_memory_items` | Trycycle-reviewed summaries (session + feature) | `_summarize_session/feature_memory()` | `_extract_project_facts()`, synthesis |
| `pr_project_facts` | Durable facts with temporal validity | `_extract_project_facts()` | synthesis, MCP `get_project_state` |
| `mng_session_tags` | Current session context (phase, feature, bug_ref) | Tag bar + MCP `set_session_tags` | All writes that carry phase/feature |

---

## Key Design Decisions

| Decision | Why |
|----------|-----|
| **Two event tables** (pr_events + pr_interactions) | Different read patterns: pr_interactions feeds sequential summarization; pr_events feeds JOIN-heavy entity tagging. Could be merged in a future refactor. |
| **Trycycle review** (2× Haiku per summary) | Quality gate: score < 7 → use improved_summary; ensures only high-quality content enters Layer 5 |
| **Incremental synthesis** | Send only new entries if distilled context exists → ~8× token savings on repeat `/memory` runs |
| **Temporal facts** (valid_until IS NULL) | Full audit trail: query what was true at any past timestamp; change detection without data loss |
| **Per-tool output files** | Each AI tool reads its own format (CLAUDE.md / rules.md / context.md); works offline and independently |
| **Fire-and-forget background tasks** | Embeddings, fact extraction, entity sync run after `/memory` returns — user not blocked on slow Haiku calls |
| **Smart chunking** | Per-class/function for code, per-section for markdown, per-file for diffs → precise semantic search |
| **Entity → embedding backfill** | SQL UPDATE propagates Planner tags into pgvector metadata so entity-filtered semantic search works |
| **Confidence thresholds** | Facts ≥ 0.70, entities ≥ 0.85, bugs ≥ 0.80 — higher for permanent writes, lower for queryable facts |
