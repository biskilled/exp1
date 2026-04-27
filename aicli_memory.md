# aicli Memory System — Command Reference

_Last updated: 2026-04-27_

This document describes every command that manages memory, context files, and work items in aicli — what each command does, what files it writes, and which LLM calls it makes.

---

## Overview: What Gets Stored Where

| Data type | Stored in | Written by |
|-----------|-----------|------------|
| Developer prompts + responses | `mem_mrr_prompts` (DB) | Claude Code hook → `POST /history/{p}/hook-log` |
| Git commits | `mem_mrr_commits` (DB) | `POST /git/{p}/commit-push` |
| Per-symbol code changes | `mem_mrr_commits_code` (DB) | background after commit |
| File hotspot scores | `mem_mrr_commits_file_stats` (DB) | background after commit |
| Durable project facts | `mem_ai_project_facts` (DB) | `/memory` → `memory_promotion.py` |
| Work items (backlog) | `mem_work_items` (DB) | `POST /wi/{p}/classify` |
| LLM context files | `workspace/{p}/memory/` (files) | `/memory` → `memory_files.py` |

There is **no `history.jsonl`** — all history is stored in the database (`mem_mrr_prompts`).

---

## Command Index

| Command | Endpoint | LLM? | What it does |
|---------|----------|------|--------------|
| `/memory` | `POST /projects/{p}/memory` | ✓ Haiku | Synthesise project state → write all context files |
| `/push` | `POST /git/{p}/commit-push` | ✓ Haiku+Sonnet | Commit + push; extract code symbols + refresh code.md in background |
| `/wi classify` | `POST /wi/{p}/classify` | ✓ Haiku | Classify unprocessed events into work items |
| `/wi approve` | `POST /wi/{p}/{id}/approve` | ✓ OpenAI | Assign real ID + compute embedding |
| `/wi pipeline` | `POST /wi/{p}/{id}/run-pipeline` | ✓ Sonnet×4 | Run 4-agent PM→Arch→Dev→Review pipeline |
| `/embed` | `POST /memory/{p}/embed-*` | ✓ OpenAI | Embed work items for semantic search |
| `/search` | `POST /search/semantic` | — | pgvector cosine similarity search |
| `/status` | `GET /projects/{p}` | — | Show project state (cached `project_state.json`) |
| `/history` | MCP `get_recent_history` | — | Show recent prompts from `mem_mrr_prompts` |
| `/commits` | MCP `get_commits` | — | Show recent commits from `mem_mrr_commits` |
| `/items` | `GET /wi/{p}` | — | List work items from `mem_work_items` |

---

## `/memory` — Context File Synthesis

**Endpoint:** `POST /projects/{project}/memory`
**Trigger:** Manual, or automatically by the Claude Code Stop hook (`auto_commit_push.sh`)

### What it does — step by step

```
1. project_synthesis  [LLM: Claude Haiku]
   Input:  recent mem_mrr_prompts (last ~50 entries) + current project_state.json + PROJECT.md intro
   Prompt: command_memory.yaml → key: project_synthesis
   Output: project_state.json (key_decisions, in_progress, tech_stack, project_facts)

2. conflict_detection  [LLM: Claude Haiku — only if facts conflict]
   Input:  old fact value vs new fact value for same key in mem_ai_project_facts
   Prompt: command_memory.yaml → key: conflict_detection
   Output: resolution (supersede/merge/flag) → written to mem_ai_project_facts

3. write_root_files()  [NO LLM — deterministic render from DB]
   Reads: project_state.json + mem_work_items + mem_mrr_commits_file_stats
   Writes (all in workspace/{project}/memory/):
     claude/CLAUDE.md          ← main Claude context (token-limited)
     cursor/rules.md           ← Cursor IDE rules
     openai/compact.md         ← GPT-4 compact prompt
     openai/full.md            ← GPT-4 full context
     context.md                ← shared context injected by CLI
     code.md                   ← file hotspot table + coupling table
   Preambles: command_memory.yaml → keys: memory_context_compact/full/openai

4. tag_suggestion  [LLM: Claude Haiku]
   Input:  last 5 developer prompts from mem_mrr_prompts
   Prompt: command_memory.yaml → key: tag_suggestion
   Output: JSON array of 2-3 suggested phase/feature tags (shown to user, not saved)
```

### Output files

| File | Token limit (project.yaml) | Content |
|------|---------------------------|---------|
| `memory/claude/CLAUDE.md` | `claude_md_max_tokens` (default 8000) | Key decisions + in_progress + work items |
| `memory/cursor/rules.md` | `cursorrules_max_tokens` (default 2000) | Condensed cursor rules |
| `memory/openai/compact.md` | — | Compact GPT-4 system prompt |
| `memory/openai/full.md` | — | Full GPT-4 context |
| `memory/context.md` | — | Shared context block (injected by CLI) |
| `memory/code.md` | `hotspot_threshold` filter | File hotspot scores + coupling pairs |

---

## `/push` — Git Commit Processing

**Endpoint:** `POST /git/{project}/commit-push`
**Trigger:** Manual `/push` command, or Claude Code Stop hook

### What it does

```
1. git add + commit + push (shell)

2. commit_analysis  [LLM: Claude Sonnet — called once per commit]
   Input:  git diff of the commit
   Prompt: command_commits.yaml → key: commit_analysis
   Output: JSON (message, summary, key_classes, patterns, decisions)
   Written to: mem_mrr_commits.diff_summary

3. commit_message  [LLM: Claude Haiku — if no message provided]
   Input:  changed files list + diff summary
   Prompt: command_commits.yaml → key: commit_message
   Output: short git commit message string

4. Background (after response returned):
   extract_commit_code() → memory_code_parser.py
     commit_symbol  [LLM: Claude Haiku — once per changed symbol]
       Input:  single class/method/function diff
       Prompt: command_commits.yaml → key: commit_symbol
       Output: 1-sentence summary
       Written to: mem_mrr_commits_code.llm_summary
     File stats → mem_mrr_commits_file_stats (hotspot_score, bug_commit_count)
     File coupling → mem_mrr_commits_file_coupling (co_change_count)
   write_code_md()  [NO LLM — reads fresh hotspot data from DB]
     Rewrites workspace/{project}/memory/code.md immediately after symbol extraction
```

---

## `/wi classify` — Work Item Classification

**Endpoint:** `POST /wi/{project}/classify`
**Trigger:** Manual only by default; threshold-based optional via `project.yaml`

### What it does

```
1. Delete all AI draft rows from mem_work_items (wi_id LIKE 'AI%')

2. Fetch unprocessed events:
   - mem_mrr_prompts  (wi_id IS NULL) → up to 200 rows
   - mem_mrr_commits  (wi_id IS NULL) → up to 100 rows
   - mem_mrr_messages (wi_id IS NULL) → up to 50 rows
   - mem_mrr_items    (wi_id IS NULL) → up to 50 rows

3. Group into token-bounded batches (~6000 tokens each)

4. Per batch: classification  [LLM: Claude Haiku]
   Prompt: command_work_items.yaml → classification.system + classification.event_prompt
   Output: flat JSON array → use_cases first, then children with wi_parent_id
   Written to: mem_work_items (draft wi_id=AI0001, AI0002…)

5. User reviews in Planner UI:
   GET /wi/{project}/pending/grouped → use_cases + nested children

6. Approve → POST /wi/{project}/{id}/approve
   - Assigns real ID: US0001 (use_case), FE0001 (feature), BU0001 (bug), TA0001 (task)
   - Marks mem_mrr_* rows: wi_id = real ID
   - Computes OpenAI embedding → mem_work_items.embedding VECTOR(1536)
   - Writes documents/use_cases/{slug}.md for use_case items

7. Reject → wi_id = REJxxxxxx (events stay unlinked for next run)
```

### Work item ID prefixes

| Prefix | Type | Example |
|--------|------|---------|
| `AI` | Draft (temp) | AI0001 |
| `US` | Use case | US0001 |
| `FE` | Feature | FE0001 |
| `BU` | Bug | BU0001 |
| `TA` | Task | TA0001 |
| `PO` | Policy | PO0001 |
| `RE` | Requirement | RE0001 |
| `REJ` | Rejected | REJ00a3f2 |

---

## `/wi pipeline` — 4-Agent Pipeline

**Endpoint:** `POST /wi/{project}/{item_id}/run-pipeline`
**Trigger:** Manual (MCP `run_work_item_pipeline` or direct API call)

### Requirements

- Item must be approved (`wi_id` assigned — not `AI*` or `REJ*`)
- Item `user_status` must not be `done` or `deleted`
- If item has a parent use case, parent must also be approved

### What it does

```
1. Validate item (approved + open + parent approved)
2. Mark pipeline_status = 'running'
3. Background: POST /agents/run-pipeline with pipeline='standard'
   4 agents run sequentially (all Claude Sonnet):
   - Product Manager  → acceptance_criteria
   - Architect        → implementation_plan
   - Developer        → dev_implementation
   - Reviewer         → reviewer_validation + verdict
4. Save back to mem_work_items:
   - acceptance_criteria  (from PM stage)
   - implementation_plan  (from Architect stage)
   - pipeline_status = 'done' | 'error'
   - pipeline_run_id = run UUID
```

---

## `/embed` — Semantic Search Embedding

**Endpoint:** `POST /memory/{project}/embed-commits` or `POST /memory/{project}/embed-prompts`

Embeds work items for semantic search using **OpenAI text-embedding-3-small** (1536-dim).
Writes to `mem_work_items.embedding VECTOR(1536)`.
Must run before `/search` returns results for newly approved items.

---

## `/search` — Semantic Search

**Endpoint:** `POST /search/semantic`
**No LLM** — pure pgvector cosine similarity.

```json
{
  "query": "authentication bug",
  "project": "aicli",
  "source_types": ["work_item"],
  "limit": 10
}
```

---

## Session Start Hook — Context Injection

**Script:** `workspace/{project}/memory/claude/hooks/check_session_context.sh`
**Trigger:** Claude Code Start event

```
write_root_files() — NO LLM
  Reads: cached project_state.json (last /memory run)
  Writes: CLAUDE.md + .cursorrules (refreshed from cache)
  Cost: $0 — no LLM call
```

---

## Session Stop Hook — Auto Commit + Memory Sync

**Script:** `workspace/{project}/memory/claude/hooks/auto_commit_push.sh`
**Trigger:** Claude Code Stop event

```
1. POST /git/{project}/commit-push  → commit + push + commit_analysis [Sonnet]
2. Background:
   - extract_commit_code()          → commit_symbol [Haiku] per symbol
   - check_and_trigger()            → classify if threshold reached [Haiku, opt-in]
3. POST /projects/{project}/memory  → full /memory synthesis [Haiku]
```

---

## LLM Cost Summary

| Operation | Model | Calls | Approx cost |
|-----------|-------|-------|-------------|
| `/memory` project_synthesis | Haiku | 1/run | ~$0.001 |
| `/memory` tag_suggestion | Haiku | 1/run | ~$0.0002 |
| `/push` commit_analysis | Sonnet | 1/commit | ~$0.003 |
| `/push` commit_message | Haiku | 1/commit | ~$0.0001 |
| `/push` commit_symbol | Haiku | N/commit (1 per changed symbol) | ~$0.0001×N |
| `/wi classify` | Haiku | 1/batch (~6k tokens) | ~$0.001/batch |
| `/wi pipeline` | Sonnet | 4 agents | ~$0.02–0.10 |
| `/wi approve` embedding | OpenAI text-embedding-3-small | 1/item | ~$0.00002 |

All costs logged to `mng_usage_logs` with `source='memory'`.
