# aicli Memory System — Architecture Reference

_Last updated: 2026-03-30 | v3.0 — Memory Infrastructure Redesign_

---

## Overview

aicli uses a **5-layer memory architecture** that persists context across every AI tool —
Claude Code, Cursor, the web UI, the aicli CLI, and pipeline agents.

Storage is **DB-primary**: PostgreSQL 15 with pgvector. JSONL files are no longer written
by hooks — they write directly to the DB. The five memory layers build on each other:
raw prompts → batch digests → distilled facts → synthesized output files.

---

## The 5 Layers at a Glance

| Layer | Storage | Written by | Purpose |
|-------|---------|------------|---------|
| 1 — Immediate | In-memory (Python list) | LLM provider adapters | Current conversation window |
| 2 — Working | `pr_prompts` | Hooks + chat.py + pipeline | Raw prompts + responses |
| 3 — Project | `CLAUDE.md`, `MEMORY.md`, `context.md`, `rules.md`, `copilot.md` | `/memory` command | Synthesized files read by each AI tool |
| 4 — Historical | `pr_tags`, `pr_source_tags`, `pr_commits`, `pr_embeddings` | Hooks + batch system | Tagged + searchable record |
| 5 — Global | `pr_memory_events`, `pr_project_facts`, `pr_feature_snapshots` | Batch system + /memory | Distilled facts, digests, 4-layer snapshots |

---

## Layer 1 — Immediate Context

**Storage**: Python list in RAM (never written to disk).

**Contents**: System prompt + conversation turns + tool call results.

**Written by**: Provider adapters in `backend/agents/providers/` during live session.

**Lifespan**: Lost on process exit. This is the LLM's context window only.

---

## Layer 2 — Working Memory

The raw material that feeds all summarization. Every prompt and response ends up here.

### Database — `pr_prompts`

**Primary prompt/response log**. Written in real-time by hooks and UI.

```
id (UUID), client_id=1, project
session_id      — links all prompts in a session
event_type      — always 'prompt' for user messages
llm_source      — 'claude_cli', 'ui', 'pipeline:{role}'
source_id       — unique identifier from caller (UNIQUE where not null)
prompt          — user prompt text
response        — assistant response text
phase           — current phase tag at time of prompt
tags[]          — string tag array
work_item_id    — FK → pr_work_items (if tagged to a work item)
metadata        — JSONB extra fields
```

**Written by**:
- `route_chat.hook_log_prompt()` — from `log_user_prompt.sh` hook (with `context_tags`)
- `route_chat.hook_log_response()` — from `log_session_stop.sh` hook
- `route_chat._append_history()` — UI chat responses
- `orchestrator.py` `AgentWorkflow` — after each pipeline stage

**Read by**: `_summarize_session_memory()` — feeds session distillation

### Support Files

| File | Written by | Contents |
|------|-----------|----------|
| `workspace/{p}/_system/project_state.json` | `/memory` command | tech_stack, key_decisions, in_progress, last_memory_run, _synthesis_cache |
| `workspace/{p}/_system/.agent-context` | `check_session_context.sh` | Current session tags: `{session_id, tags: {stage, feature}, set_at}` |

---

## Layer 4 — Historical Knowledge

The permanent tagged record. Used for feature tracking and semantic search.

### `pr_tags` — Project Tag Hierarchy

Per-project tag registry. Replaces `mng_entity_values`.

```
id (UUID PK), client_id=1, project
name            — unique per project
category_id     — FK → mng_tags_categories (global vocabulary)
parent_id       — FK → pr_tags (self, for nested tags)
merged_into     — FK → pr_tags (when this tag was merged into another)
status          — 'active' | 'done' | 'archived'
lifecycle       — 'idea'|'design'|'development'|'testing'|'review'|'done'
seq_num         — display order
created_at
```

**Written by**: `route_tags.py` CRUD endpoints; auto-created by `_tag_prompt_from_context()`.

### `mng_tags_categories` — Global Category Vocabulary

Client-scoped (shared across all projects). Replaces `mng_entity_categories`.

```
id (SERIAL PK), client_id=1
name, color, icon, description
```

Default categories seeded at startup: `feature` (#22c55e ⚡), `bug` (#ef4444 🐛),
`task` (#3b82f6 ✓), `design` (#a855f7 ◈), `decision` (#f59e0b ⚑), `meeting` (#6b7280 ◷).

### `pr_tag_meta` — Work Item Metadata for Tags

One row per tag that represents a work item (optional).

```
tag_id (UUID FK → pr_tags), client_id=1, project
description, requirements, due_date, requester
priority (1–5), extra JSONB (assignee, sprint, story_points)
```

### `pr_source_tags` — Unified Junction Table

Links **any** source type to a tag. Replaces both `pr_event_tags` and `pr_prompt_tags`.

```
id (UUID), tag_id (FK → pr_tags)
prompt_id   | commit_id | item_id | message_id   — exactly ONE is non-null
auto_tagged — bool (TRUE = set by system)
CHECK: exactly one of prompt_id/commit_id/item_id/message_id is non-null
```

### `pr_commits` — VCS Commits

```
id, client_id=1, project
commit_hash, commit_msg, summary
phase, feature, bug_ref
session_id, prompt_source_id
prompt_id   — FK → pr_prompts (direct causal link, 2026-03-30)
```

**Written by**: `auto_commit_push.sh` hook → `POST /git/{project}/commit-push`.

### `pr_embeddings` — pgvector Semantic Index

```
id, client_id=1, project
source_type     — 'history' | 'commit' | 'role' | 'doc' | 'memory_event' | 'node_output'
source_id       — matches source record
chunk_index     — 0-based chunk number within the source
content         — chunk text
embedding       — vector(1536) — OpenAI text-embedding-3-small
chunk_type      — 'full' | 'summary' | 'class' | 'function' | 'section' | 'file_diff'
doc_type        — 'session_summary' | 'commit_diff' | 'role_prompt' | ...
language        — 'python' | 'javascript' | ...
file_path       — for code chunks: which file
metadata        — JSONB: phase, feature, tag_ids (from pr_source_tags)
```

---

## Layer 5 — Global / Distilled Knowledge

### `pr_memory_events` — Batch Digests + Embeddings

One digest row per N prompts (batch) per session. Replaces scope-based `pr_memory_items`.

```
id (UUID), client_id=1, project
source_type   — 'prompt_batch' | 'commit' | 'item' | 'message'
source_id     — UUID pointing to source (last prompt in batch for 'prompt_batch')
session_id    — session this digest covers
content       — 1-2 sentence Haiku digest (the embedding input)
embedding     — VECTOR(1536) — cosine-indexed for semantic search
importance    — SMALLINT 1–5 (default 1)
processed_at  — NULL = not yet promoted to feature snapshot
created_at
```

**Written by**: `_generate_memory_batch()` in `route_chat.py` — fires every N prompts
(N = `memory.batch_size` in `aicli.yaml`, default 3).

**Tags linked via**: `pr_memory_tags` (event_id ↔ tag_id, copied from source tags at insert time).

### `pr_feature_snapshots` — 4-Layer Feature Artifacts

One per tag. Generated on demand via Sonnet from `pr_memory_events`.

```
id (UUID), client_id=1, project
tag_id (UUID FK → pr_tags)
work_item_type — 'feature' | 'bug' | 'task'
requirements   — string (Layer 1)
action_items   — string (Layer 2)
design         — JSONB {high_level, low_level, patterns_used}
code_summary   — JSONB {files, key_classes, key_methods, dependencies_added/removed}
prompt_ids     — UUID[]
commit_hashes  — TEXT[]
file_paths     — TEXT[]
embedding      — VECTOR(1536) — embed(requirements + ' ' + action_items)
is_reusable    — bool
```

**Generated by**: `POST /projects/{project}/snapshot/{tag_name}`

### `pr_project_facts` — Durable Facts with Temporal Validity

```
id (UUID), client_id=1, project
fact_key      — e.g. 'auth_method', 'database', 'rel:auth:jwt'
fact_value    — e.g. 'JWT + bcrypt', 'PostgreSQL 15 + pgvector', 'implements'
valid_from    — timestamptz (when first extracted)
valid_until   — NULL = currently true; NOT NULL = superseded
embedding     — VECTOR(1536) (2026-03-30 addition)
```

**Temporal upsert**: When a fact value changes, old row gets `valid_until = NOW()` and a
new row is inserted. Full audit trail. Query current state: `WHERE valid_until IS NULL`.

---

## Memory Batch System

### How Batches Fire

Every time a prompt is logged via the hook endpoint:

```
hook_log_prompt()
    └─ _count_session_prompts(project, session_id) → int N
    └─ if N > 0 and N % _get_batch_size(project) == 0:
           asyncio.create_task(_generate_memory_batch(project, session_id, batch_size))
    └─ if context_tags non-empty:
           asyncio.create_task(_tag_prompt_from_context(project, prompt_id, context_tags))
```

### `_generate_memory_batch()` — Haiku Digest

1. Loads last N `pr_prompts` for the session (Q/A pairs, truncated)
2. Loads `memory_batch_digest` system role from `mng_system_roles`
3. Calls Haiku → 1-2 sentence content digest
4. Embeds the digest → VECTOR(1536)
5. INSERTs into `pr_memory_events` (source_type='prompt_batch', source_id=last_prompt_id)
6. Copies `pr_source_tags` from the N prompts → `pr_memory_tags`

**aicli.yaml config**:
```yaml
memory:
  batch_size: 3        # digest every N prompts per session
  auto_snapshot: false # auto-trigger snapshot when lifecycle → done
```

### `_tag_prompt_from_context()` — Session Context Tagging

Converts `.agent-context` tags (e.g. `{stage: "discovery", feature: "auth"}`) into
`pr_source_tags` rows: get_or_create each `pr_tags` row → insert with `auto_tagged=True`.

---

## 4-Layer Feature Snapshot

### Endpoint: `POST /projects/{project}/snapshot/{tag_name}`

Full flow in `backend/routers/route_snapshots.py`:

```
1. Resolve tag_id from pr_tags WHERE name = tag_name
2. Load all pr_memory_events via pr_memory_tags JOIN WHERE tag_id
3. Load system prompt from mng_system_roles WHERE name='memory_feature_snapshot'
4. Build user message grouped by source_type (prompt_batch / commit / item / meeting)
5. Call Sonnet (quality matters) → parse JSON
6. Embed (requirements + action_items) → VECTOR(1536)
7. Upsert pr_feature_snapshots (ON CONFLICT tag_id DO UPDATE)
8. Extract design.patterns_used → upsert pr_project_facts
9. Mark contributing pr_memory_events.processed_at = NOW()
```

**Expected LLM JSON**:
```json
{
  "requirements": "string — what the feature must do",
  "action_items": "string — open tasks and next steps",
  "design": {
    "high_level": "overview",
    "low_level": "implementation details",
    "patterns_used": ["ReAct", "pgvector cosine search"]
  },
  "code_summary": {
    "files": ["backend/routers/route_tags.py"],
    "key_classes": ["Router"],
    "key_methods": ["list_tags", "create_tag"],
    "dependencies_added": [],
    "dependencies_removed": []
  }
}
```

---

## What Happens When You Run `/memory`

`POST /projects/{name}/memory` — full sequence in `route_projects.py:generate_memory()`:

```
1. Load config
   - aicli.yaml: memory.batch_size, code_dir
   - project_state.json: last_memory_run, tech_stack, key_decisions, _synthesis_cache

2. Load tag summary
   - SQL: pr_tags JOIN mng_tags_categories JOIN pr_tag_meta (active tags only)
   - Returns per-category groups with tag name, lifecycle, description, due_date

3. Session distillation — _summarize_session_memory(project)
   - Finds sessions in pr_prompts with ≥3 prompts not yet batch-digested
   - For each session (up to 10 per /memory run):
       • If pr_memory_events already exists (batch ran) → use existing digest
       • Else: Haiku Call 1: summarize → Haiku Call 2: Trycycle review
         INSERT pr_memory_events(source_type='prompt_batch', reviewer_score)

4. Load distilled context
   - pr_project_facts WHERE valid_until IS NULL (all current facts)
   - pr_memory_events ORDER BY created_at DESC LIMIT 8 (most recent digests)

5. LLM synthesis — _synthesize_with_llm()
   - System role: mng_system_roles WHERE name='memory_synthesis'
   - Incremental: if new_entries < 10 AND digests exist → send only new + distilled context
   - Returns {key_decisions, in_progress, tech_stack, memory_digest, project_summary}
   - Merged into project_state.json

6. Write 5 output files (Layer 3)
   - _system/claude/MEMORY.md   → copies to <code_dir>/MEMORY.md
   - _system/claude/CLAUDE.md   → copies to <code_dir>/CLAUDE.md
   - _system/cursor/rules.md    → copies to <code_dir>/.cursor/rules/aicli.mdrules
   - _system/aicli/context.md  (compact 600-char block, injected by CLI)
   - _system/aicli/copilot.md  → copies to <code_dir>/.github/copilot-instructions.md

7. Background tasks (asyncio.create_task — fire-and-forget)
   ├─ _extract_project_facts()
   │   Reads 6 most recent pr_memory_events + existing pr_project_facts
   │   Calls Haiku via internal_project_fact role → [{key, value, confidence}]
   │   Temporal upsert → pr_project_facts
   │
   ├─ ingest_history(since=last_memory_run)
   │   Embeds new pr_prompts entries → pr_embeddings
   │
   ├─ ingest_roles()
   │   Re-embeds all workspace/_templates/roles/*.yaml → pr_embeddings
   │
   ├─ ingest_commits(project)
   │   Embeds commits not yet indexed → pr_embeddings
   │
   └─ _suggest_tags() → suggested_tags returned in response

8. Update project_state.json: last_memory_run = NOW()

9. Return:
    {
      "generated": ["MEMORY.md", "CLAUDE.md", "rules.md", "context.md", "copilot.md"],
      "copied_to": ["<code_dir>/CLAUDE.md", ...],
      "synthesized": true,
      "run_ts": "2026-03-30T...",
      "suggested_tags": [{"name": "memory-infra", "category": "feature", "is_new": false}]
    }
```

---

## All Internal LLM Prompts — Locations

All memory system prompts are stored in `mng_system_roles` (category='memory') and are
editable from the Roles tab UI. They are seeded at startup by `_seed_memory_system_roles()`.

| Role name | Model | Trigger | Purpose |
|-----------|-------|---------|---------|
| `memory_batch_digest` | Haiku (max 200) | Every N prompts in session | 1-2 sentence digest of N Q/A pairs |
| `memory_session_summary` | Haiku (max 800) | `/memory` — unsummarized sessions | 3-8 bullet session summary |
| `memory_session_review` | Haiku (max 600) | After session_summary | Trycycle: score + improved_summary JSON |
| `memory_feature_snapshot` | Sonnet (max 2000) | `POST /snapshot/{tag}` | 4-layer JSON artifact |
| `memory_synthesis` | Haiku (max 2000) | Every `/memory` run | Final synthesis → 5 output files |

The `internal_project_fact` role (already in `mng_agent_roles`) is reused for fact extraction.

---

## Tagging System

### Architecture

```
mng_tags_categories (global, client-scoped)
        ↓ category_id FK
pr_tags (per-project, UUID PK)
        ↓ tag_id FK
pr_tag_meta (optional work-item metadata: description, requirements, due_date, priority)

pr_source_tags (junction — any source type ↔ tag)
    tag_id FK → pr_tags
    prompt_id | commit_id | item_id | message_id  (exactly one non-null)
    auto_tagged BOOL

pr_memory_tags (junction — memory event ↔ tag)
    event_id FK → pr_memory_events
    tag_id FK → pr_tags
```

### Tagging Paths

**Path 1 — Session context enforcement** (`check_session_context.sh`):
1. Hook reads `.agent-context` (stage/feature tags)
2. `_tag_prompt_from_context()` get_or_creates `pr_tags` rows for each tag
3. Inserts `pr_source_tags(tag_id, prompt_id, auto_tagged=True)` for every prompt

**Path 2 — Manual tag from Planner** (`route_tags.py`):
1. UI sends `POST /tags/source` with `{tag_id, prompt_id|commit_id}`
2. Inserts `pr_source_tags` row

**Path 3 — Session bulk tag** (`POST /tags/source` with all session prompts):
1. Resolve or create `pr_tags` row
2. Insert `pr_source_tags` row for each prompt in the session

**Path 4 — Auto-copy to memory** (`_generate_memory_batch()`):
1. On batch creation, copies all `pr_source_tags` for batch's prompts → `pr_memory_tags`
2. Tags thus flow automatically from prompt events to their memory digests

**Path 5 — AI auto-detection** (`_auto_detect_session_feature()` in `chat.py`):
- Fires on first prompt of a new session if no feature tag is set
- Haiku suggests feature → if accepted, updates session tags + `.agent-context`

---

## Session Context Enforcement

### How It Works

The `check_session_context.sh` hook fires before `log_user_prompt.sh` on every prompt.

```
1. Skip tool noise (<task-notification>, <tool-use-id>, <task-id>, <parameter>)
2. Skip empty prompts
3. Read workspace/{project}/_system/.agent-context
4. IF file exists AND session_id matches → exit 0 (allow)
5. IF missing or stale:
   a. GET /tags/session-context?project=...  → fetch last known tags
   b. Write .agent-context with default {stage: "discovery"} or last tags
   c. Print to stdout (shown to user by Claude Code):
      ⚡ Session context loaded. Review and re-send your message.
      Tags: stage=discovery  feature=memory-infra
      To change: edit workspace/{project}/_system/.agent-context
   d. exit 2 (block — Claude Code holds the prompt)
6. On second attempt (file now exists) → exit 0
```

### `.agent-context` File Format

Location: `workspace/{project}/_system/.agent-context`

```json
{
  "session_id": "abc123",
  "session_src": "claude_cli",
  "tags": { "stage": "development", "feature": "memory-infra" },
  "set_at": "2026-03-30T10:00:00Z"
}
```

---

## Complete Hook Logic

### Hook 1: `check_session_context.sh` (UserPromptSubmit — runs first)

See "Session Context Enforcement" above.

---

### Hook 2: `log_user_prompt.sh` (UserPromptSubmit)

Fires: Every prompt submitted in Claude Code (after check_session_context allows it).

```
1. Read stdin JSON: {"hook_event_name":"UserPromptSubmit","session_id":"abc123","prompt":"..."}
2. Extract prompt text and session_id
3. Detect active project from aicli.yaml
4. Filter noise — skip if prompt starts with:
   <task-notification> | <tool-use-id> | <task-id> | <parameter>
5. Skip empty prompts
6. Read workspace/{project}/_system/.agent-context → CONTEXT_TAGS dict
7. POST {BACKEND_URL}/chat/{project}/hook-log:
   {ts, session_id, prompt, source: 'claude_cli', provider: 'claude', context_tags: {...}}
8. exit 0
```

Backend (`hook_log_prompt()`):
- Inserts into `pr_prompts`
- Counts session prompts → if count % batch_size == 0: fires `_generate_memory_batch()`
- If `context_tags` non-empty: fires `_tag_prompt_from_context()`

---

### Hook 3: `log_session_stop.sh` (Stop)

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
5. POST {BACKEND_URL}/chat/{project}/hook-response:
   {session_id, response: response_text, stop_reason}
6. Background (non-blocking):
   curl -sf -X POST {BACKEND_URL}/projects/{ACTIVE_PROJECT}/memory &
7. exit 0
```

---

### Hook 4: `auto_commit_push.sh` (Stop)

Fires: Same Stop event as log_session_stop.sh.

```
1. Check auto_commit_push in workspace/{project}/project.yaml → if not "yes": exit 0
2. Check backend health → if BACKEND_OK=yes:
   POST {BACKEND_URL}/git/{project}/commit-push
   {message_hint:"after claude cli session {session_id[:8]}", session_id, source:"claude_cli"}
   → logs to commit_log.jsonl if committed=true
3. Fallback: direct git add/commit/push if backend down
```

---

## MCP Tools — What Each Reads

The MCP server (`backend/agents/mcp/server.py`) exposes 13 tools via stdio JSON-RPC.

| Tool | Backend call | Reads from |
|------|-------------|-----------|
| `search_memory` | `POST /search/semantic` | `pr_memory_events` (content ILIKE) + `pr_embeddings` (pgvector) |
| `get_project_state` | `GET /projects/{p}` + `/work-items/facts` + `/work-items/memory-items` | project_state.json + pr_project_facts + pr_memory_events |
| `get_recent_history` | `GET /history/chat` | `pr_prompts` |
| `get_commits` | `GET /history/commits` | `pr_commits` |
| `get_tagged_context` | `GET /search/tagged` | `pr_source_tags JOIN pr_tags` |
| `get_session_tags` | `GET /history/session-tags` | `mng_session_tags` |
| `set_session_tags` | `PUT /history/session-tags` | `mng_session_tags` (write) |
| `commit_push` | `POST /git/{p}/commit-push` | git + `pr_commits` (write) |
| `create_entity` | `POST /tags` | `pr_tags` + `mng_tags_categories` (write) |
| `list_work_items` | `GET /work-items` | `pr_work_items JOIN pr_tags JOIN mng_tags_categories` |
| `run_work_item_pipeline` | `POST /work-items/{id}/run-pipeline` | triggers pipeline (write) |
| `get_item_by_number` | `GET /work-items/number/{seq}` | `pr_work_items` |
| `get_db_schema` | hard-coded DDL | — |

---

## Agent Tools (Pipeline Agents — Direct DB Access)

ReAct agents in the pipeline have these tools via `backend/agents/tools/`:

| Tool | File | Reads from |
|------|------|-----------|
| `search_memory` | `tool_memory.py` | `pr_memory_events` (content search) + `pr_embeddings` (pgvector) |
| `get_recent_history` | `tool_memory.py` | `pr_prompts` (with tag filter via `pr_source_tags JOIN pr_tags`) |
| `get_project_facts` | `tool_memory.py` | `pr_project_facts WHERE valid_until IS NULL` |
| `list_work_items` | `tool_workitems.py` | `pr_work_items JOIN pr_tags JOIN mng_tags_categories JOIN pr_tag_meta` |
| `create_work_item` | `tool_workitems.py` | `mng_tags_categories` + `pr_tags` + `pr_tag_meta` + `pr_work_items` (write) |
| `read_file` | `tool_files.py` | Filesystem (code_dir) |
| `write_file` | `tool_files.py` | Filesystem (code_dir) |
| `list_dir` | `tool_files.py` | Filesystem (code_dir) |
| `git_status` | `tool_git.py` | git (read) |
| `git_diff` | `tool_git.py` | git (read) |
| `git_commit` | `tool_git.py` | git (write) |
| `git_push` | `tool_git.py` | git (write) |

---

## Smart Chunking for Embeddings

Before embedding, content is split into meaningful chunks via `backend/memory/mem_embeddings.py`:

| Content type | Chunker | Splits on | Rows created |
|-------------|---------|-----------|--------------|
| Prompt/memory events | none — single blob | — | **1 per row** (chunk_type='full') |
| Markdown docs / role YAML | `smart_chunk_markdown()` | `##` headings; sub-split at `###` if >3000 chars | **N per file** (1 per section) |
| Git diffs | `smart_chunk_diff()` | `diff --git a/... b/...` file boundaries | **1 summary + 1 per changed file** |
| Python/JS code files | `smart_chunk_code()` | `class` / `def` / `function` / `const` top-level | **N per file** (1 per symbol) |

**Deduplication**: `ON CONFLICT (client_id, project, source_type, source_id, chunk_index) DO UPDATE`.

---

## Complete Table Reference

All 27 tables (9 mng_ global + 18 pr_ project-scoped):

### `mng_` Tables (Global, Client-Scoped)

| Table | Purpose |
|-------|---------|
| `mng_clients` | Client registry |
| `mng_users` | User accounts + bcrypt passwords |
| `mng_usage_logs` | Per-request token usage + cost |
| `mng_transactions` | Balance top-ups + charges |
| `mng_session_tags` | Current session context (phase, feature, bug_ref) per project |
| `mng_tags_categories` | Global tag category vocabulary (feature/bug/task/design/decision/meeting) |
| `mng_agent_roles` | Agent role definitions (system_prompt, tools, react, max_iterations) |
| `mng_agent_role_versions` | Version history for agent roles |
| `mng_system_roles` | Internal LLM prompts (memory batch, synthesis, snapshot, fact extraction) |

### `pr_` Tables (Per-Project)

| Table | Purpose | Written by | Read by |
|-------|---------|-----------|---------|
| `pr_prompts` | Prompt/response log (session summarization feed) | hooks + chat.py + pipeline | `_summarize_session_memory()` |
| `pr_commits` | VCS commits + metadata + prompt_id causal link | `auto_commit_push.sh` hook | commit history, pr_source_tags |
| `pr_embeddings` | pgvector semantic index for code + history + roles | `embed_and_store()` | `semantic_search()`, `search_memory` |
| `pr_tags` | Per-project tag hierarchy (replaces mng_entity_values) | `route_tags.py` CRUD + `_tag_prompt_from_context()` | all tagging paths |
| `pr_tag_meta` | Work item metadata for tags (description, requirements, due_date, priority) | `route_tags.py`, `create_work_item()` | Planner drawer, work items |
| `pr_source_tags` | Junction: tag ↔ any source (prompt/commit/item/message) | tagging paths | semantic search metadata, `get_tagged_context` |
| `pr_items` | Documents: requirements, decisions, client notes, meetings | item ingest API | tagging, snapshot generation |
| `pr_messages` | Slack/Teams/Discord message chunks (future) | platform connectors | tagging, snapshot generation |
| `pr_memory_events` | Batch digests + embeddings (1-2 sentences per N prompts) | `_generate_memory_batch()` | `_extract_project_facts()`, snapshot, synthesis |
| `pr_memory_tags` | Junction: memory_event ↔ tag (copied from source tags at insert) | `_generate_memory_batch()` | snapshot generation |
| `pr_feature_snapshots` | 4-layer JSON artifact per tag (requirements→action→design→code) | `route_snapshots.py` | Planner drawer, semantic search |
| `pr_project_facts` | Durable facts with temporal validity + embedding | `_extract_project_facts()` | synthesis, MCP `get_project_state` |
| `pr_work_items` | Work items with tag_id FK to pr_tags | `route_work_items.py` + pipeline | Planner, pipeline agents |
| `pr_graph_workflows` | Workflow DAG definitions | `route_workflows.py` | graph runner |
| `pr_graph_nodes` | DAG nodes | `route_workflows.py` | graph runner |
| `pr_graph_edges` | DAG edges | `route_workflows.py` | graph runner |
| `pr_graph_runs` | Workflow run history | `graph_runner.py` | run history UI |
| `pr_graph_node_results` | Per-node output per run | `graph_runner.py` | run history UI |

---

## Key Design Decisions

| Decision | Why |
|----------|-----|
| **Unified junction table** (`pr_source_tags`) | Single table for all source types (prompt/commit/item/message) with CHECK constraint → no "which table do I query?" ambiguity; replaces `pr_event_tags` + `pr_prompt_tags` |
| **pr_tags as UUID PK** | Supports cross-project references, merge semantics (`merged_into` FK), and future global tag sharing; replaces SERIAL integer `mng_entity_values` |
| **mng_tags_categories global** | Categories (feature/bug/task/design/decision/meeting) are the same across all projects; seeded once at startup; eliminates per-project category duplication |
| **Batch digest model** (`pr_memory_events`) | Fire every N prompts → cheap Haiku digest captures in-session decisions; replaces scope-based `pr_memory_items` which required waiting for session end |
| **Session context enforcement** (`check_session_context.sh`) | Guarantees every prompt carries structured metadata (stage + feature); blocks first prompt, writes `.agent-context`, allows second → zero-friction workflow |
| **Sonnet for snapshots, Haiku for batches** | Quality/cost trade-off: batch digests are fast and cheap (Haiku); 4-layer snapshot is a durable artifact worth Sonnet's quality |
| **System prompts in DB** (`mng_system_roles` category='memory') | All LLM prompts are editable from the Roles tab UI without code changes; versioned via `mng_agent_role_versions` |
| **Trycycle review** (2× Haiku per session summary) | Quality gate: score < 7 → use improved_summary; ensures only high-quality content enters the distillation chain |
| **Temporal facts** (`valid_until IS NULL`) | Full audit trail: query what was true at any past timestamp; change detection without data loss |
| **Fire-and-forget background tasks** | Batch digests, embeddings, fact extraction all run async → user not blocked; tasks are idempotent (ON CONFLICT DO UPDATE) |
| **pr_commits.prompt_id direct FK** | Causal link: which prompt caused which commit — enables "show me the code that changed when I asked about X" queries |
