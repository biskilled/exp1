# aicli Memory System — Reference Guide

_Last updated: 2026-04-25 (m078 — planner_tags removed; m079 planned — code.md + is_latest)_

This is the single authoritative reference for how aicli stores, updates, and serves project memory across every supported LLM tool. Written from scratch to reflect the post-m078 architecture. If this contradicts anything in CLAUDE.md, this document is more specific.

---

## 1. Memory Layers — Current DB Tables

> `mem_ai_events` was **dropped in m057**. `planner_tags` was **dropped in m078**. Neither exists any more.

### Layer 1 — Raw Mirror (`mem_mrr_*`)
Raw data captured as-is, no AI processing. The `wi_id` column tracks whether a row has been classified.

| Table | Content | `wi_id` meaning |
|-------|---------|-----------------|
| `mem_mrr_prompts` | Every user prompt + response from all tools | NULL = unclassified; set to real ID after approve |
| `mem_mrr_commits` | Git commits (hash, msg, summary, commit_type, is_external) | Same pattern |
| `mem_mrr_commits_code` | Per-symbol diffs from tree-sitter (file, class, method, diff_snippet, llm_summary) | N/A (no wi_id) |
| `mem_mrr_items` | Imported documents / meeting notes | Same pattern |
| `mem_mrr_messages` | Slack / chat messages | Same pattern |
| `mem_mrr_commits_file_stats` | Per-file hotspot metrics (commit_count, bug_commit_count, hotspot_score) | N/A |
| `mem_mrr_commits_file_coupling` | Co-change file pairs | N/A |

### Layer 2 — Work Items (`mem_work_items`) — Single Source of Truth
All use cases, features, bugs, tasks, policies, and requirements live in one table.

**Key columns:**
- `wi_id` — NULL (pending AI draft) → AI0001 (draft) → US/FE/BU/TA/PO/RE prefixed (approved) → REJxxxxxx (rejected)
- `wi_type` — `use_case | feature | bug | task | policy | requirement`
- `wi_parent_id` — UUID FK to self (hierarchy: use_case → feature/bug/task children)
- `name`, `summary`, `deliveries` — the substance
- `user_status`, `score_importance` (0–5), `score_status` (0–5)
- `start_date`, `due_date`, `completed_at`, `deleted_at`, `merged_into`
- `embedding VECTOR(1536)` — set on approve via OpenAI text-embedding-3-small

**wi_id prefix scheme:**

| Type | Prefix | Example |
|------|--------|---------|
| use_case | US | US0001 |
| feature | FE | FE0001 |
| bug | BU | BU0001 |
| task | TA | TA0001 |
| policy | PO | PO0001 |
| requirement | RE | RE0001 |

**Companion table:** `mem_wi_versions` — snapshots of use-case items at each update (m068).

### Layer 3 — Project Facts (`mem_ai_project_facts`)
Durable architectural decisions that survive across sessions.

- `fact_key` (UNIQUE per project where `valid_until IS NULL`)
- `fact_value`, `category` (stack / pattern / convention / constraint / client / general)
- `conflict_status` — `pending_review` blocks the fact from being rendered into CLAUDE.md
- `embedding VECTOR(1536)` — for semantic search

Written by `memory_promotion.py:save_fact()`. Rarely populated automatically now; used primarily when conflict detection fires.

### Dropped Tables (do NOT reference in code)
| Table | Dropped in | Replaced by |
|-------|-----------|-------------|
| `mem_ai_events` | m057 | `mem_work_items` |
| `mem_ai_work_items` | m057 | `mem_work_items` (m063+) |
| `planner_tags` | m078 | `mem_work_items` |
| `mng_tags_categories` | m078 | `wi_type` column on `mem_work_items` |
| `mem_backlog_links` | m078 | direct `wi_id` FK on `mem_mrr_*` |
| `planner_tag_deps` | m078 | `wi_parent_id` on `mem_work_items` |
| `mem_ai_feature_snapshot` | m078 | `summary` / `mem_wi_versions` |
| `mng_deliveries` | m078 | `deliveries JSONB` on `mem_work_items` |

---

## 2. Output Files Written by `/memory`

`memory_files.py` is **deterministic** — no LLM calls. Reads DB, renders templates, writes files.

| File | Path | Consumed by |
|------|------|-------------|
| `CLAUDE.md` | `{code_dir}/CLAUDE.md` | **Claude Code** — auto-loaded from project root |
| `CLAUDE.md` | `{workspace}/_system/claude/CLAUDE.md` | Archive copy |
| `.cursorrules` | `{code_dir}/.cursorrules` | **Cursor** — auto-loaded |
| `rules.md` | `{workspace}/_system/cursor/rules.md` | Archive copy |
| `compact.md` | `{workspace}/_system/llm_prompts/compact.md` | GPT-4, any small-window model (≤2000 tokens) |
| `full.md` | `{workspace}/_system/llm_prompts/full.md` | Claude CLI, DeepSeek, Grok (large context) |
| `gemini_context.md` | `{workspace}/_system/llm_prompts/gemini_context.md` | **Gemini** Files API upload |
| `openai.md` | `{workspace}/_system/llm_prompts/openai.md` | OpenAI API system prompt |
| `system_prompt.md` | `{workspace}/_system/openai/system_prompt.md` | **Codex CLI** `--system-prompt` flag |

### What goes into CLAUDE.md

Data comes from three DB tables:
1. `mem_ai_project_facts` — Stack, patterns, conventions, constraints
2. `mem_work_items` — Active use cases + features (not completed, not deleted)
3. `mem_mrr_commits` + `mem_mrr_commits_code` — Recently changed symbols (top 200, deduplicated)

### Auto-regen triggers

| Event | What fires |
|-------|-----------|
| `POST /projects/{p}/memory` | Full synthesis (LLM) + `write_root_files()` |
| Session stop hook | Session summary → `write_root_files()` |
| Session start hook | `write_root_files()` only (no LLM) |
| Work item approve/update | `write_root_files()` (background) |

---

## 3. LLM Prompts — All Locations

All prompts are under `backend/prompts/`. Changes take effect without restart (hot-reloaded by `prompt_loader.py`).

### `backend/prompts/commit.yaml`

| Key | Model | Max tokens | Trigger | Output |
|-----|-------|-----------|---------|--------|
| `commit_analysis` | Sonnet | 800 | `POST /git/commit-store` | JSON: message, summary, key_classes, key_methods, patterns_used, decisions, test_coverage, dependencies |
| `commit_symbol` | Haiku | 120 | After each commit, per symbol above `min_lines` | One-sentence change summary for `mem_mrr_commits_code.llm_summary` |

### `backend/prompts/work_items.yaml`

| Key | Model | Max tokens | Trigger | Output |
|-----|-------|-----------|---------|--------|
| `classification` | Haiku | 4000 | `POST /wi/{p}/classify` (manual or threshold) | Flat JSON array of use cases + children with scores |
| `summarise` | Haiku | 2000 | `POST /wi/{p}/summarize/{id}` | Reorganized use case: updated summary + in_progress + completed groupings |

This file also contains category config (colors, seq prefixes) — parsed directly by `memory_work_items.py` via PyYAML, not `prompt_loader`.

### `backend/prompts/memory_synthesis.yaml`

| Trigger | Model | Output |
|---------|-------|--------|
| `POST /projects/{p}/memory` | Haiku | JSON: `key_decisions[]`, `in_progress[]`, `tech_stack{}`, `project_summary` → written to `project_state.json` + PROJECT.md |

### `backend/prompts/conflict_detection.yaml`

| Trigger | Model | Output |
|---------|-------|--------|
| `memory_promotion.py:save_fact()` when value contradicts existing | Haiku | JSON: `resolution` (supersede/merge/flag), `merged_value`, `reasoning` |

---

## 4. All LLM Call Sites

Every place in the codebase that makes an LLM API call:

| # | File | Function | Prompt source | Model | When |
|---|------|----------|--------------|-------|------|
| 1 | `route_projects.py` | `_synthesize_with_llm()` | `memory_synthesis.yaml` | Haiku | `POST /projects/{p}/memory` |
| 2 | `memory_work_items.py` | `classify()` | `work_items.yaml:classification` | Haiku | `POST /wi/{p}/classify` or auto-threshold |
| 3 | `memory_work_items.py` | `summarize_use_case()` | `work_items.yaml:summarise` | Haiku | `POST /wi/{p}/summarize/{id}` |
| 4 | `route_git.py` | commit analysis | `commit.yaml:commit_analysis` | Sonnet | `POST /git/commit-store` |
| 5 | `memory_code_parser.py` | `_haiku()` | `commit.yaml:commit_symbol` | Haiku | Per symbol in each commit |
| 6 | `memory_promotion.py` | `_call_llm()` | `conflict_detection.yaml` | Haiku | When `save_fact()` detects contradiction |
| 7 | `agents/agent.py` | ReAct loop | Agent role `system_prompt` from `mng_agent_roles` | Configurable | `POST /agents/run` |
| 8 | `pipelines/pipeline_runner.py` | YAML pipeline step | Each step's `prompt:` field in pipeline YAML | Configurable | `POST /agents/run-pipeline` |
| 9 | `pipelines/pipeline_graph_runner.py` | DAG node | Node's agent role system_prompt | Configurable | `POST /graph-workflows/{id}/run` |

**Embedding calls** (OpenAI `text-embedding-3-small`, 1536-dim):

| Where | When |
|-------|------|
| `memory_work_items.py:_embed_work_item()` | On work item approve |
| `route_search.py` | On every `POST /search/semantic` query |

---

## 5. Data Flow

### 5a. Developer Session → Memory Update

```
Claude Code / Cursor session
  │
  ├── Every prompt → log_user_prompt.sh hook
  │     → POST /hook-log/prompt
  │     → INSERT mem_mrr_prompts (wi_id=NULL)
  │
  ├── git push → auto_commit_push.sh hook
  │     → POST /git/commit-store
  │     ├── Sonnet: commit_analysis → mem_mrr_commits
  │     └── tree-sitter → mem_mrr_commits_code
  │           + Haiku: per-symbol summaries
  │
  └── Session end → log_session_stop.sh hook
        → POST /projects/{p}/memory
        ├── Haiku: memory_synthesis.yaml
        │     → project_state.json + PROJECT.md
        └── write_root_files() (no LLM)
              → CLAUDE.md, .cursorrules, llm_prompts/*
```

### 5b. Raw Mirror → Work Items (classification pipeline)

```
mem_mrr_prompts / mem_mrr_commits (wi_id IS NULL)
  │
  ├── Auto: threshold check after each INSERT
  │     prompts: 2000 tokens accumulated
  │     commits: 1000 tokens accumulated
  │
  └── Manual: POST /wi/{p}/classify
        ├── Fetch unprocessed rows (max 200 prompts / 100 commits)
        ├── Group into ~6000-token batches
        └── For each batch:
              Haiku: work_items classification prompt
                → flat JSON: use_cases[] + children[]
              INSERT mem_work_items (wi_id=AI0001..., draft)

User reviews in Work Items tab → approve
  ├── Assign real ID (US0001, FE0002, BU0003…)
  ├── SET mem_mrr_*.wi_id = real ID
  ├── OpenAI embed(summary + name) → mem_work_items.embedding
  └── Write/refresh use case MD file (optional)
```

### 5c. Fact Conflict Detection

```
save_fact(project, key, value)
  ├── SELECT existing fact (valid_until IS NULL)
  └── If exists AND different value:
        Haiku: conflict_detection.yaml
          → { resolution: "supersede|merge|flag", merged_value }
        UPDATE mem_ai_project_facts based on resolution
```

---

## 6. Supported CLI Tools

aicli is a **FastAPI backend** (HTTP API). All integrations work by calling HTTP endpoints or running hook scripts. There is no separate CLI binary.

### Claude Code (primary)

Set up hooks in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [{ "command": "/path/to/log_user_prompt.sh" }],
    "Stop": [
      { "command": "/path/to/log_session_stop.sh" },
      { "command": "/path/to/auto_commit_push.sh" }
    ],
    "PreToolUse": [{ "command": "/path/to/check_session_context.sh" }]
  }
}
```

Hook scripts live in `workspace/_templates/cli/claude/hooks/`:

| Script | Trigger | What it does |
|--------|---------|-------------|
| `log_user_prompt.sh` | Every prompt | POST to `/hook-log/prompt` → inserts into `mem_mrr_prompts` |
| `log_session_stop.sh` | Session end | POST to `/projects/{p}/memory` → LLM synthesis + write_root_files |
| `auto_commit_push.sh` | Session end | `git add/commit/push` + POST to `/git/commit-log` |
| `check_session_context.sh` | Session start | `write_root_files()` to refresh CLAUDE.md |
| `log_commit.sh` | Git hook | POST to `/git/commit-store` |
| `slack_notify.sh` | Session end | Slack webhook notification |
| `format_on_save.sh` | Tool use | Run formatter on modified files |

### Cursor

- `.cursorrules` auto-loaded from project root (kept ≤2000 tokens)
- MCP server: add to Cursor MCP settings pointing to `backend/agents/mcp/server.py`
- Use `commit_push` MCP tool for tagging commits with phase/feature

### Claude CLI (terminal)

```bash
cat workspace/aicli/_system/llm_prompts/full.md | claude -
# or pipe it as system prompt
claude --system-prompt "$(cat workspace/aicli/_system/llm_prompts/full.md)"
```

### OpenAI / GPT-4

```python
system = open("workspace/aicli/_system/llm_prompts/openai.md").read()
client.chat.completions.create(model="gpt-4.1",
    messages=[{"role": "system", "content": system}, ...])
```

### Codex CLI

```bash
codex --system-prompt "$(cat workspace/aicli/_system/openai/system_prompt.md)"
```

### DeepSeek / Grok / Any OpenAI-compatible

Use `llm_prompts/full.md` as system prompt — provider-agnostic plain text.

### Gemini

Upload `gemini_context.md` via Files API, reference the file URI in your request. Contains all facts + active work items.

---

## 7. LLM Providers

Five providers are supported. Each has an adapter in `backend/agents/providers/`.

| Provider | File | Default model | Env var |
|----------|------|--------------|---------|
| **Anthropic (Claude)** | `pr_claude.py` | `claude-sonnet-4-6` | `ANTHROPIC_API_KEY` |
| **OpenAI** | `pr_openai.py` | `gpt-4.1` | `OPENAI_API_KEY` |
| **DeepSeek** | `pr_deepseek.py` | `deepseek-chat` / `deepseek-reasoner` | `DEEPSEEK_API_KEY` |
| **Google Gemini** | `pr_gemini.py` | `gemini-2.0-flash` | `GEMINI_API_KEY` |
| **xAI Grok** | `pr_grok.py` | `grok-3` | `GROK_API_KEY` |

**Haiku** (`claude-haiku-4-5-20251001`) is used for all internal memory pipeline calls (classification, synthesis, conflict detection, symbol summaries) — it's fast and cheap.

**Sonnet** (`claude-sonnet-4-6`) is used for commit analysis (higher quality needed).

**OpenAI `text-embedding-3-small`** is used for all vector embeddings (1536 dimensions).

### Shared System Prompts (`mng_system_roles`)

Admin-managed text blocks that prepend to any agent role's system_prompt. Managed via `GET/POST/PATCH /system-roles`.

Built-in blocks: `coding_standards`, `output_format`, `security_principles`, `testing_standards`, `performance_standards`, `documentation_standards`, `deployment_standards`.

Linked to agent roles via `mng_role_system_links` (with `order_index` for priority stacking).

---

## 8. MCP Integration

The MCP server (`backend/agents/mcp/server.py`) uses **stdio transport** and exposes 18 tools. Add it to Claude Code or Cursor settings.

### Tool List

| Tool | What it returns / does |
|------|------------------------|
| `search_memory` | Semantic + text search over history, commits, docs, code chunks (pgvector cosine) |
| `get_project_state` | PROJECT.md + tech_stack + in_progress + active work items (live DB) |
| `get_recent_history` | Last N prompt/response entries (filterable: phase, feature, provider) |
| `get_roles` | Available AI role YAML files |
| `get_commits` | Recent commits with phase/feature tags (untagged = red flag) |
| `get_tagged_context` | All events with a specific phase or feature tag |
| `get_session_tags` | Current active session tags (phase, feature, bug_ref) |
| `set_session_tags` | Update active session tags |
| `commit_push` | Stage → commit → push; logs to `commit_log.jsonl` with `source='cursor_mcp'` |
| `create_entity` | Create feature/bug/task/use_case in `mem_work_items` |
| `sync_github_issues` | Import GitHub issues as work items (bug/feature/task) |
| `list_work_items` | Active work items (filterable by category, status) |
| `run_work_item_pipeline` | Trigger 4-agent pipeline: PM → Architect → Developer → Reviewer |
| `get_db_schema` | Full table schema reference for the current project |
| `search_facts` | Semantic search over `mem_ai_project_facts` |
| `search_work_items` | Semantic search over `mem_work_items` embeddings |
| `get_tag_context` | Full context for a work item: summary + recent prompts |
| `get_item_by_number` | Resolve `#US0001` → full work item record |

**Why bother with MCP when CLAUDE.md exists?**
CLAUDE.md is a snapshot at the last `/memory` run. MCP gives live DB access: semantic search over all history, create items mid-session, tag the session. Use both.

---

## 9. File Locations Quick Reference

```
backend/
  prompts/
    commit.yaml              ← commit_analysis (Sonnet) + commit_symbol (Haiku)
    work_items.yaml          ← classification + summarise (both Haiku) + category config
    conflict_detection.yaml  ← fact conflict resolution (Haiku)
    memory_synthesis.yaml    ← /memory LLM synthesis (Haiku)

  memory/
    memory_files.py          ← deterministic renderer → CLAUDE.md / .cursorrules / llm_prompts/*
    memory_mirroring.py      ← INSERT into mem_mrr_* tables
    memory_work_items.py     ← classify() + approve() + reject() pipeline
    memory_code_parser.py    ← tree-sitter AST → mem_mrr_commits_code + hotspot scoring
    memory_promotion.py      ← fact conflict detection + save_fact()
    memory_sessions.py       ← per-turn LLM message continuity (JSON file sessions)

  routers/
    route_work_items.py      ← /wi/* endpoints (classify, pending, approve, reject, update)
    route_projects.py        ← /projects/* + /memory synthesis + session-tags endpoint
    route_git.py             ← /git/commit-store, /git/sync-commits
    route_memory.py          ← /memory/stats + pipeline-status + data-dashboard
    route_search.py          ← /search/tagged + /search/semantic

workspace/{project}/
  PROJECT.md                 ← User-maintained; auto-updated "Key Decisions" + "Recent Work"
  _system/
    claude/CLAUDE.md         ← Full context (primary archive)
    cursor/rules.md          ← Compact Cursor rules (≤2000 tokens)
    llm_prompts/
      compact.md             ← GPT-4 / small-window models
      full.md                ← Claude CLI / DeepSeek / Grok
      gemini_context.md      ← Gemini Files API
      openai.md              ← OpenAI API
    openai/
      system_prompt.md       ← Codex CLI --system-prompt

{code_dir}/
  CLAUDE.md                  ← Auto-loaded by Claude Code
  .cursorrules               ← Auto-loaded by Cursor
```

---

## 10. Code Structure File (`code.md`)

`code.md` is a **deterministic, LLM-free** snapshot of the project's current class/method structure. It is generated from `mem_mrr_commits_code` and written to `{code_dir}/code.md`.

---

### Why it exists

`PROJECT.md` once had a "Code Structure" section but it decayed quickly — no process kept it updated. `code.md` solves this by being generated automatically from the same tree-sitter data that drives commit analysis, using the `is_latest` pattern to always reflect the current codebase state.

---

### `is_latest` Pattern (m079 — planned)

The `mem_mrr_commits_code` table is append-only by design (every commit adds new rows). To get _current_ state without a separate table, migration m079 adds:

```sql
ALTER TABLE mem_mrr_commits_code ADD COLUMN is_latest BOOLEAN DEFAULT TRUE;
CREATE INDEX idx_mrr_code_latest ON mem_mrr_commits_code(project_id, is_latest)
  WHERE is_latest = TRUE;
-- Backfill: for each (project_id, file_path, full_symbol), keep only the most recent row
UPDATE mem_mrr_commits_code c
SET    is_latest = FALSE
WHERE  id NOT IN (
    SELECT DISTINCT ON (project_id, file_path, full_symbol) id
    FROM   mem_mrr_commits_code
    ORDER  BY project_id, file_path, full_symbol, created_at DESC
);
```

**On each new commit** (`memory_code_parser.py`): before inserting new rows for a file, set `is_latest = FALSE` on all existing rows for that `(project_id, file_path)`. New rows land with `is_latest = TRUE`. Deleted files get all rows set to `is_latest = FALSE`.

This gives a current-state view with a simple `WHERE is_latest = TRUE` filter — no new table needed.

---

### `code.md` Format

Generated by `memory_files.py:write_code_md()` using:

```sql
SELECT file_path, class_name, method_name, symbol_type,
       rows_added + rows_removed AS churn,
       llm_summary
FROM   mem_mrr_commits_code
WHERE  project_id = %s
  AND  is_latest = TRUE
  AND  file_change != 'deleted'
ORDER  BY file_path, class_name NULLS LAST, method_name
```

Output structure (Markdown table per module):

```markdown
# Code Structure
_Generated: 2026-04-25 — 142 symbols across 18 files_

## backend/memory/memory_files.py
| Symbol | Type | Summary | Churn |
|--------|------|---------|-------|
| `MemoryFiles` | class | Deterministic renderer for CLAUDE.md / .cursorrules | 48 |
| `MemoryFiles.write_root_files` | method | Entry point: writes all 5 output files | 12 |
| `MemoryFiles.render_root_claude_md` | method | Renders CLAUDE.md from templates + DB context | 31 |
| `MemoryFiles.write_code_md` | method | Writes code.md from is_latest rows | 8 |

## backend/routers/route_projects.py
...
```

**Condensed version for `CLAUDE.md`** — class names only (no methods), capped at ~50 lines:

```markdown
## Code Structure (classes)
| File | Class | Summary |
|------|-------|---------|
| memory/memory_files.py | MemoryFiles | Deterministic renderer |
| routers/route_projects.py | — | Project + memory endpoints |
...
_Full structure: code.md_
```

---

### 4 Triggers That Update `code.md`

| Trigger | Flow | Notes |
|---------|------|-------|
| **Commit stored** | `POST /git/{p}/commit-store` → `memory_code_parser.py` (background) sets `is_latest=FALSE` on old rows, inserts new rows → `write_code_md()` at the end | Real-time; fires on every Claude Code Stop hook if auto-commit is configured |
| **Sync-commits** | `POST /git/{p}/sync-commits` → processes all commits in batch → calls `write_code_md()` once at the end | Used for from-scratch rebuild or catching up after a period offline |
| **`/memory`** | `POST /projects/{p}/memory` → `write_root_files()` → `write_code_md()` | Always refreshes code.md even if no new commits (e.g., user edited code manually) |
| **Session start hook** | `check_session_context.sh` calls `write_root_files()` if CLAUDE.md is stale | Ensures code.md is current at the start of each Claude Code session |

---

### From-Scratch Bootstrap via `sync-commits`

If `mem_mrr_commits_code` is empty (fresh install, DB reset, new project):

```bash
# Walk entire git history from beginning
POST /git/{project}/sync-commits
# Body: {} (no last_hash → starts from first commit)
```

Flow:
1. `route_git.py` gets all commits with `git log --oneline` (oldest→newest)
2. Each commit: stores to `mem_mrr_commits`, then queues tree-sitter extraction
3. `memory_code_parser.py` processes each commit: parse AST → extract symbols → set `is_latest=FALSE` on previous rows for each touched file → insert new rows
4. After all commits: `is_latest` state matches the actual HEAD of the repository
5. `write_code_md()` runs once → `code.md` written

**Incremental catch-up** (the common case): `sync-commits` checks `mem_mrr_commits` for the most recent `commit_hash` for the project, then runs `git log {last_hash}..HEAD`. Only new commits are processed.

**Detecting stale / missing commits**: `GET /git/{project}/sync-commits` (or stats endpoint) compares `git rev-list --count HEAD` vs `COUNT(*) FROM mem_mrr_commits WHERE project_id=X` to surface drift.

---

### Where `code.md` Content Is Injected

| Output | Content | Method |
|--------|---------|--------|
| `{code_dir}/code.md` | Full table (all classes + methods) | `write_code_md()` |
| `{code_dir}/CLAUDE.md` | Condensed: classes only, ≤50 lines + link to `code.md` | `render_root_claude_md()` |
| `_system/llm_prompts/full.md` | Full table (models with large context windows) | `render_full_prompt()` |
| `_system/llm_prompts/compact.md` | Classes only (small-context models) | `render_compact_prompt()` |
| MCP `get_project_state` | Classes only section in response | `mcp/server.py` tool handler |

---

## 11. Recommendations for Improvement

These are genuine gaps based on the current architecture — ordered by impact:

### High impact

**1. Commit code embeddings** — `mem_mrr_commits_code` has `llm_summary` per symbol but no embedding. A semantic search "show me all auth-related code changes" is impossible without it. The table has the right shape; just needs `embedding VECTOR(1536)` + a backfill job.

**2. Hotspot → work item feedback loop** — `mem_mrr_commits_file_stats` tracks bug commits per file, but this data never surfaces to the work item classifier. A file with `hotspot_score > 0.8` should auto-suggest a "refactor" task.

**3. Context auto-compaction** — CLAUDE.md grows without bound. When it exceeds a configurable token limit (say 8000), the oldest "Recently Changed" entries should roll off automatically. Right now the user never knows when it's getting too large.

**4. Per-work-item branch awareness** — When a feature branch is checked out, automatically inject the matching `US/FE` item's summary into the Claude session. Currently requires manual `/wi` lookup.

### Medium impact

**5. Multi-repo support** — `mem_mrr_commits_code` assumes one `code_dir` per project. Monorepo or multi-service projects (e.g., `backend/` + `ui/`) need a `repo_path` column so symbol searches can distinguish modules.

**6. Embedding drift detection** — Work item embeddings are computed once on approve and never refreshed. If the summary is edited, the embedding becomes stale silently. A `last_embedded_at` column + periodic drift check would fix this.

**7. Session tagging at the prompt level** — `mem_mrr_prompts.tags` is set by hooks but relies on the user having run `/tag`. Most prompts end up with empty tags, making feature-filtered searches useless. Auto-tagging from work item name matching in the prompt text would help.

### Low impact / polish

**8. CLAUDE.md per-work-item drill-down** — Active features show name + status but not their children or recent bugs. A collapsed bullet list of child items (top 3) would make handoff context much richer.

**9. PROJECT.md conflict guard** — If the user edits a `<!-- auto-updated by /memory -->` section manually, the next `/memory` run overwrites it. A git-diff check before overwrite would prevent surprise data loss.

**10. Embedding model upgrade** — `text-embedding-3-small` (1536-dim) is used. `text-embedding-3-large` (3072-dim) gives ~10% better recall on code retrieval tasks. Worth the cost increase for a team tool.

---

## 12. Honest Assessment — Roasted Mode 🔥

**Rating: 3.5 / 5**

> _"It's not a must-have yet, but it's past the 'interesting experiment' stage."_

### What works well (earned points)

| Capability | Score | Comment |
|------------|-------|---------|
| Shared memory across tools | ✅ 4/5 | CLAUDE.md + .cursorrules genuinely auto-load in the right tools. Hook → DB → file pipeline works end to end. |
| Work item classification | ✅ 4/5 | Haiku classifier is surprisingly accurate for grouping prompts into use cases. The approve/reject UI flow is clean. |
| Commit code memory | ✅ 3.5/5 | tree-sitter symbol extraction + per-symbol Haiku summaries is smart. The "Recently Changed" section in CLAUDE.md is genuinely useful on a new session. |
| MCP live context | ✅ 3.5/5 | 18 tools is more than any competing tool. `search_memory` + `get_project_state` are the two that actually get used. |
| Multi-provider | ✅ 3/5 | Five providers with a clean adapter interface. Switching is trivial. |
| Migration discipline | ✅ 4/5 | 78 migrations with rollback paths and a proper version table. Production-grade. |

### What hurts (points deducted)

| Problem | Score | Comment |
|---------|-------|---------|
| Hook setup friction | ❌ -0.5 | 10 shell scripts, manual symlinks, JSON settings editing. First-time setup takes 30+ minutes and breaks on path changes. Should be `aicli init` with a single command. |
| No embeddings on code symbols | ❌ -0.5 | The most useful search ("find me all the places we handle auth") doesn't work because `mem_mrr_commits_code` has no embedding. The infrastructure is there. |
| Memory goes stale silently | ❌ -0.3 | If hooks aren't configured (or fail), CLAUDE.md drifts. No staleness indicator. No "last updated X hours ago" warning. |
| prompt tagging relies on user discipline | ❌ -0.2 | `/tag` must be run manually. Most prompts have empty tags. Feature-filtered history searches mostly return nothing. |

### vs. alternatives

| Tool | Memory | Code awareness | Multi-LLM | Rating |
|------|--------|---------------|-----------|--------|
| **aicli** | ✅ Persistent across sessions + tools | ✅ Symbol-level via tree-sitter | ✅ 5 providers | 3.5/5 |
| **Raw Claude Code** | ❌ Session-only | ❌ None | ❌ Claude only | 2/5 |
| **Cursor without MCP** | ❌ Session-only | ✅ Codebase index | ❌ Limited | 2.5/5 |
| **Cursor + aicli MCP** | ✅ Full persistent | ✅ Symbol + hotspot | ✅ 5 providers | 4/5 |
| **Custom CLAUDE.md only** | ⚠️ Manual maintenance | ❌ None | ❌ 1 tool | 1.5/5 |

### What would push it to 5/5

1. **`aicli init` command** that installs hooks in 60 seconds — no manual JSON editing
2. **Code symbol embeddings** — semantic search over code changes
3. **Automatic session tagging** — classify the active feature from prompt content, no `/tag` needed
4. **Context freshness indicator** in CLAUDE.md: `_Context is 4 hours old — run /memory to refresh_`
5. **Web UI onboarding** for non-Claude-Code users — Gemini/GPT users need a way to pull context without hooks

### Bottom line

If you're a solo developer using Claude Code on one project: **it works today** and the CLAUDE.md auto-inject genuinely saves 5–10 minutes of context re-explanation per session. That's real value.

If you're a team of 4+ people switching between Claude Code, Cursor, and GPT-4: **it's the best option available right now**, but plan for a half-day of setup and expect some manual hook maintenance.

If you just want to chat with an LLM about your code without building infrastructure: **use Claude Code with a hand-written CLAUDE.md**. aicli is overhead you don't need.

---

_Generated 2026-04-25. Run `/memory` on any project to regenerate CLAUDE.md, .cursorrules, and all llm_prompts files._
