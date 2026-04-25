# aicli Memory System — Reference Guide

_Last updated: 2026-04-25 (m077 — commit history enrichment)_

This document is the single authoritative reference for how aicli stores, updates, and serves project memory across every supported LLM tool. It covers output files, prompt locations, data flow, and MCP integration.

---

## 1. Output Files

Every time `/memory` runs, `memory_files.py` (no LLM) renders and writes these files for the active project:

| File | Path | Consumed by |
|------|------|-------------|
| `CLAUDE.md` | `{code_dir}/CLAUDE.md` | **Claude Code** (auto-loaded) |
| `CLAUDE.md` | `{workspace}/_system/claude/CLAUDE.md` | Archive copy |
| `.cursorrules` | `{code_dir}/.cursorrules` | **Cursor** (auto-loaded) |
| `rules.md` | `{workspace}/_system/cursor/rules.md` | Archive copy |
| `compact.md` | `{workspace}/_system/llm_prompts/compact.md` | GPT-4/small-window models (≤2000 tokens) |
| `full.md` | `{workspace}/_system/llm_prompts/full.md` | Claude CLI / DeepSeek / Grok (large context) |
| `gemini_context.md` | `{workspace}/_system/llm_prompts/gemini_context.md` | **Gemini** Files API upload |
| `openai.md` | `{workspace}/_system/llm_prompts/openai.md` | **OpenAI API** system prompt |
| `system_prompt.md` | `{workspace}/_system/openai/system_prompt.md` | **Codex CLI** (`--system-prompt` flag) |
| `CLAUDE.md` (feature) | `{code_dir}/features/{tag}/CLAUDE.md` | Claude Code per-feature context |

### How to use each file

**Claude Code (claude.ai/claude-code):**
`CLAUDE.md` is auto-loaded from your `code_dir`. No extra steps.

**Claude CLI:**
```bash
cat workspace/aicli/_system/llm_prompts/full.md | claude -
```

**Cursor:**
`.cursorrules` is auto-loaded. Keep it under 2000 tokens (enforced by the renderer).

**OpenAI API / ChatGPT:**
```python
with open("workspace/aicli/_system/llm_prompts/openai.md") as f:
    system = f.read()
client.chat.completions.create(model="gpt-4o", messages=[
    {"role": "system", "content": system}, ...
])
```

**Codex CLI:**
```bash
codex --system-prompt "$(cat workspace/aicli/_system/openai/system_prompt.md)"
```

**Gemini:**
Upload `gemini_context.md` via the Files API, then reference the file URI in your request. The file contains all facts, tags, and recent work.

**DeepSeek / Grok / Any OpenAI-compatible API:**
Use `llm_prompts/full.md` as the system prompt — it's plain text and provider-agnostic.

**MCP (Claude Code, Cursor):**
The MCP server exposes tools (`search_memory`, `get_project_state`) that query the live DB in real-time. No file needed — context is pulled dynamically.

---

## 2. All Prompts

All LLM prompts live under `backend/prompts/`. They are hot-reloadable (changes take effect without restart).

### Loaded via `core/prompt_loader.py` (YAML format)

| File | Keys | Used in | Trigger | Model |
|------|------|---------|---------|-------|
| `commit.yaml` | `commit_analysis` | `route_git.py` | `POST /git/commit-store` | Sonnet |
| `commit.yaml` | `commit_symbol` | `memory_code_parser.py` | Per modified symbol after commit | Haiku |
| `work_items.yaml` | `classification.system` | `memory_work_items.py` | `POST /wi/{p}/classify` | Haiku |
| `work_items.yaml` | `summarise.system` | `memory_work_items.py` | `POST /wi/{p}/summarize` | Haiku |
| `conflict_detection.yaml` | `conflict_detection` | `memory_promotion.py` | When a new fact contradicts existing | Haiku |

### Loaded directly (YAML with `prompt:` field)

| File | Used in | Trigger | Model |
|------|---------|---------|-------|
| `memory_synthesis.yaml` | `route_projects.py` | `POST /projects/{p}/memory` | Haiku |

### Prompts stored in work_items.yaml (inline in YAML, not via prompt_loader)

`work_items.yaml` is parsed directly by `memory_work_items.py` using PyYAML (not `prompt_loader`). This lets the file serve double duty: LLM prompts **and** category config (colors, seq prefixes).

---

## 3. All LLM Call Sites

Every place in the codebase that calls an LLM:

| # | Where | What | Prompt Source | When Triggered |
|---|-------|------|---------------|----------------|
| 1 | `route_projects.py:_synthesize_with_llm()` | Memory synthesis → `key_decisions`, `in_progress`, `tech_stack` | `prompts/memory_synthesis.yaml` | `POST /projects/{p}/memory` (manual) |
| 2 | `memory_work_items.py:classify()` | Classify mirror rows into use cases + children | `work_items.yaml:classification.system` | Manual: `POST /wi/{p}/classify`; Auto: threshold mode |
| 3 | `memory_work_items.py:summarize_use_case()` | Reorder + rescore items under a use case | `work_items.yaml:summarise.system` | `POST /wi/{p}/summarize/{id}` |
| 4 | `route_git.py` | Commit analysis → structured JSON record | `commit.yaml:commit_analysis` | `POST /git/commit-store` |
| 5 | `memory_code_parser.py:_haiku()` | Per-symbol diff summary | `commit.yaml:commit_symbol` | After each commit, for symbols above `min_lines` threshold |
| 6 | `memory_promotion.py:_call_llm()` | Fact conflict resolution | `conflict_detection.yaml` | When `save_fact()` sees a contradicting value for same key |
| 7 | `agents/agent.py` | ReAct agent loop | Agent role's `system_prompt` from `mng_agent_roles` DB table | `POST /agents/run` |
| 8 | `pipelines/pipeline_runner.py` | YAML pipeline step | Each step's `prompt:` field from the pipeline YAML | `POST /agents/run-pipeline` |
| 9 | `pipelines/pipeline_graph_runner.py` | DAG node execution | Node's agent role system_prompt | `POST /graph-workflows/{id}/run` |

**Embedding calls (OpenAI `text-embedding-3-small`, 1536-dim):**

| Where | When |
|-------|------|
| `tool_memory.py:_embed_sync()` | On work item approval, and in `POST /search/semantic` |
| `route_search.py` | On every semantic search query |

---

## 4. Data Flow

### 4a. Prompts/Commits → Memory

```
Developer works in Claude Code
  ↓ (Stop hook or /memory)
POST /projects/{p}/memory
  ├── Fetch recent history from mem_mrr_prompts + mem_mrr_commits
  ├── _synthesize_with_llm()           ← Haiku (memory_synthesis.yaml)
  │     → key_decisions[], in_progress[], tech_stack{}, project_summary
  ├── Save state → workspace/aicli/project_state.json
  ├── Update PROJECT.md sections: "Key Decisions" + "Recent Work"
  └── write_root_files()               ← No LLM
        → CLAUDE.md, .cursorrules, llm_prompts/*, openai/*
```

**Staleness check**: if `PROJECT.md` `_Last updated` is > 7 days old and there are recent events, `/memory` will refresh it.

### 4b. Commits → Code Memory

```
git push (or POST /git/commit-store)
  ├── call_claude(commit_analysis)     ← Sonnet
  │     → structured JSON: key_classes, decisions, summary
  ├── INSERT mem_mrr_commits (backlog_ref=NULL)
  ├── tree-sitter parse per modified file
  │   → INSERT mem_mrr_commits_code per symbol
  └── For each symbol > min_lines:
        _haiku(commit_symbol)          ← Haiku
          → 1-sentence diff summary
```

### 4c. Raw Mirror → Work Items

```
mem_mrr_prompts / mem_mrr_commits (wi_id IS NULL)
  ↓
POST /wi/{p}/classify
  ├── Fetch unprocessed mirror rows (max 200 prompts / 100 commits / 50 messages)
  ├── Group into token-bounded batches (~6000 tokens each)
  └── For each batch:
        _call_haiku(work_items classification prompt)  ← Haiku
          → flat JSON array: use_cases + children

        INSERT mem_work_items (wi_id=AI0001…, draft)

User reviews in Work Items tab (GET /wi/{p}/pending/grouped)
  ↓ approve
  ├── Assign real ID (US0001, FE0002, BU0003…)
  ├── SET mem_mrr_*.wi_id = real ID (marks row as processed)
  ├── Upsert planner_tags (name, category, parent_id)
  ├── _embed_sync(summary + name)      ← OpenAI text-embedding-3-small
  │     → UPDATE mem_work_items.embedding
  └── Write/refresh documents/use_cases/{slug}.md
```

### 4d. Fact Conflict Detection

```
Any code calls save_fact(project, key, value)
  ├── SELECT existing fact for same key (valid_until IS NULL)
  └── If exists AND different value:
        _call_llm(conflict_detection prompt)  ← Haiku
          → { resolution: "supersede|merge|flag", merged_value }
        UPDATE mem_ai_project_facts based on resolution
```

---

## 5. What Triggers What (Summary)

| Event | Immediate triggers | Background tasks |
|-------|-------------------|-----------------|
| `POST /git/commit-store` | commit_analysis (Sonnet), tree-sitter parse | Per-symbol Haiku summaries, `_check_backlog_threshold` |
| `POST /chat` (hook-log) | INSERT mem_mrr_prompts | `_check_backlog_threshold("prompts")` |
| `POST /wi/{p}/classify` | Work item classification (Haiku) | — |
| `POST /wi/{p}/approve/{id}` | Embedding (OpenAI), use case MD write | — |
| `POST /projects/{p}/memory` | Memory synthesis (Haiku), write_root_files | PROJECT.md update |
| Tag create/update | `write_root_files()` (sync, no LLM) | — |
| `POST /agents/run` | Full ReAct loop (any provider) | Usage logging |

---

## 6. MCP Integration

The MCP server exposes 10 tools that Claude Code / Cursor can call during a session:

| Tool | Endpoint | What it returns |
|------|----------|-----------------|
| `search_memory` | `POST /search/semantic` | Top-K events by cosine similarity (pgvector) |
| `get_project_state` | DB + `project_state.json` | tech_stack, key_decisions, in_progress, entities |
| `get_recent_history` | `GET /history/{p}?limit=N` | Recent prompt/response pairs |
| `get_commits` | `GET /history/{p}/commits` | Recent commits with tags |
| `get_session_tags` | `GET /entities/{p}/session-tags` | Active phase/feature/bug tags |
| `set_session_tags` | `PUT /entities/{p}/session-tags` | Update active tags |
| `get_tagged_context` | DB query by phase/feature | All events tagged with given phase/feature |
| `list_work_items` | `GET /wi/{p}?category=…` | Active use cases + work items |
| `create_entity` | `POST /wi/{p}` | Create new work item |
| `commit_push` | `POST /git/commit-push` | Stage, commit, push |

**Why MCP matters**: static files (CLAUDE.md) reflect the state at the last `/memory` run. MCP gives Claude **live** access to the database — most recent events, semantic search over all history, and the ability to tag work mid-session. The combination gives the best of both: fast startup (static file) + live context (MCP).

---

## 7. Memory System Assessment (after 2026-04-25 refactor)

### Before

| Problem | Impact |
|---------|--------|
| MEMORY.md generated alongside CLAUDE.md — duplicate, stale, grew to 30+ duplicate tech_stack keys | Confusing; wasted context tokens |
| `tech_stack.update()` never reset | Keys accumulated across runs |
| LLM synthesis prompt hardcoded in route_projects.py | Required restart for prompt tweaks |
| `planner_tags.embedding` + `code_summary` referenced in tool_memory.py but dropped in m027 | MCP search_features crashed |
| `/search/semantic` endpoint didn't exist | MCP `search_memory` always returned 404 |
| No OpenAI/Codex output file | OpenAI users had no memory file |
| PROJECT.md never updated by `/memory` | Went stale permanently |

### After

| Fix | Result |
|-----|--------|
| MEMORY.md removed — content flows through PROJECT.md `Key Decisions` + `Recent Work` | Single source of truth |
| `tech_stack = synthesis["tech_stack"]` (replace, not update) | Clean 15-entry canonical set |
| Synthesis prompt in `backend/prompts/memory_synthesis.yaml` | Hot-reloadable |
| `search_features()` replaced with text ILIKE search on surviving columns | MCP search works |
| `/search/semantic` implemented with pgvector cosine similarity | MCP `search_memory` functional |
| `render_openai_system()` + `_system/openai/system_prompt.md` | OpenAI/Codex supported |
| `_project_md_age_days()` + `_Last updated` bump in `_update_project_md_section()` | PROJECT.md stays current |

### Remaining gaps

- `mem_ai_project_facts` is long and contains stale entries — no curation endpoint or automatic expiry yet
- Commit embeddings are not stored (commits in `mem_ai_events` via the old embedding pipeline may be stale)
- No auto-compaction when context files exceed token limits
- `planner_tags` text search is weak (ILIKE) — a proper embedding column would make feature discovery much better

---

## 9. Commit History Enrichment (m077 — 2026-04-25)

### New DB columns (mem_mrr_commits)

| Column | Type | Purpose |
|--------|------|---------|
| `commit_type` | `TEXT` | Conventional prefix hint: `feat`→feature, `fix`→bug, `chore`/`refactor`/`test`→task |
| `is_external` | `BOOLEAN DEFAULT FALSE` | Marks commits from external collaborators (not pushed via aicli) |

### Renamed tables

| Old name | New name (m077) |
|----------|-----------------|
| `mem_file_stats` | `mem_mrr_commits_file_stats` |
| `mem_file_coupling` | `mem_mrr_commits_file_coupling` |

These renames align the hotspot/coupling tables with the `mem_mrr_*` namespace used by all mirror tables.

### New endpoint: `POST /git/{project}/sync-commits`

Ingests git commits that exist locally but are not yet stored in `mem_mrr_commits`. Useful when:
- External collaborators push commits directly (no aicli)
- You import an existing repo with commit history
- The backend was offline when commits were pushed

**Response:**
```json
{
  "synced": 12,
  "skipped": 0,
  "already_known": 5,
  "latest_hash": "abc12345..."
}
```

All synced commits are stored with `is_external=true` and `commit_type` derived from the conventional prefix. Tree-sitter symbol extraction is queued in the background.

### commit_type in classification

The `commit_type` column is included in the `[COMMIT ...]` block sent to the work item classification LLM:

```
[COMMIT abc12345 2026-04-25 type=bug (linked to prompt def67890)]
  fix: null pointer in session refresh
```

This gives the classifier an explicit type hint instead of requiring it to infer from free text, improving bug/feature/task classification accuracy.

### CLAUDE.md enhanced sections (memory_files.py)

The rendered `CLAUDE.md` now includes:

```markdown
# aicli
aicli gives every LLM the same project memory...

## Structure
- backend/
- cli/
- ui/
- workspace/

## Active Features
- `auth-refactor` [active] — JWT token refresh

## Recently Changed (last commits)
- `AuthService.refresh_token` — modified in abc12345 — refreshes JWT silently
- `route_git.sync_missing_commits` — added in def67890
(+ 3 more — see git log)

## Conventions & Decisions
...
```

### Memory quality rating (0–5 scale)

| Capability | Before m077 | After m077 |
|------------|-------------|------------|
| Code structure visible to LLM | 0 — no dirs/modules shown | 3 — top dirs + recently changed symbols |
| Commit classification quality | 2 — LLM infers type from free text | 4 — `commit_type` hint pre-categorizes |
| External commit ingestion | 0 — no sync mechanism | 4 — `sync-commits` endpoint |
| Memory freshness for new CLIs | 2 — CLAUDE.md has tags + facts | 3.5 — + structure + recent changes |
| MCP semantic search | 3 — works on events | 3 — unchanged |

**Overall rating: 3.5/5**

What's needed for 5/5:
1. Embedding over `mem_mrr_commits_code` symbols (cosine search for "show me auth code")
2. Per-module summary refresh (only regenerate when module hash changes)
3. Design document extraction from commit diffs (docstrings, ADRs)
4. Cross-repo memory (multiple repos per project)
5. Auto-compaction when context window fills

---

## 8. File Locations Quick Reference

```
backend/
  prompts/
    commit.yaml            ← commit_analysis + commit_symbol prompts
    work_items.yaml        ← classification + summarise prompts + category config
    conflict_detection.yaml ← fact conflict resolution prompt
    memory_synthesis.yaml  ← /memory LLM synthesis prompt

workspace/{project}/
  PROJECT.md               ← User-maintained; Key Decisions + Recent Work auto-updated
  _system/
    CLAUDE.md              ← Full context (archive)
    claude/CLAUDE.md       ← Full context (primary)
    cursor/rules.md        ← Compact Cursor rules
    llm_prompts/
      compact.md           ← GPT-4 / small models
      full.md              ← Claude CLI / DeepSeek / Grok
      gemini_context.md    ← Gemini Files API
      openai.md            ← OpenAI API system prompt
    openai/
      system_prompt.md     ← Codex CLI --system-prompt

{code_dir}/
  CLAUDE.md               ← Auto-loaded by Claude Code
  .cursorrules            ← Auto-loaded by Cursor
  features/{tag}/CLAUDE.md ← Per-feature context for Claude Code
```
