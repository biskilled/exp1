# Role: Developer — aicli

You are working on **aicli**.

## Key Architectural Decisions

- Memory architecture: 3 layers — raw captures (mem_mrr_* tables: prompts, commits, code diffs, file stats, coupling), structured artifacts (mem_ai_project_facts with Haiku synthesis), and work items (mem_work_items with pgvector embeddings ONLY for approved items prefixed UC/FE/BU/TA).
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; all 5 output files (CLAUDE.md, CODE.md, PROJECT.md, cursor/rules, api/) regenerated from single JSON.
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task) and wi_parent_id linking children to use_case parents; wi_id format: AI0001 (unapproved draft) → UC/FE/BU/TA0001 (approved); only approved items embed and trigger 4-agent pipeline.
- Code.md generation: per-symbol diffs via tree-sitter (Python/JS/TS) with file coupling/hotspot tables; refreshed post-commit and post-memory; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio) to prioritize recently-changed files.
- Embeddings strategy: ONLY approved work items (wi_id: UC/FE/BU/TA) embed to pgvector; code.md, project_state.json, project facts, and prompts never embed; /search/semantic searches work_items only.
- Work item re-embedding: triggered automatically on name/summary/description edits for approved items via update(); unapproved drafts (AI prefix) never embed; commit-sourced items auto-set score_status=5 and score_importance=5 via regex 'fixes BU0012' pattern for user approval.
- Prompts: all backend LLM prompts stored in YAML under backend/memory/prompts/ (command_memory.yaml, event_commit.yaml, command_work_items.yaml, mem_project_state.yaml, mem_session_tags.yaml, misc.yaml); loaded via prompt_loader utility.
- MCP server: 14 tools rewired to REST endpoints; stdio server in agents/mcp/server.py with unified dispatch pattern matching tool name to REST route; tools include search_memory, get_project_state, list_work_items, classify, approve, run_pipeline.
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract.
- 4-agent pipeline: PM (acceptance criteria) → Architect (implementation plan) → Developer (code) → Reviewer; triggered only on approved items under approved use cases; stored in mem_work_items columns acceptance_criteria, implementation_plan, pipeline_status, pipeline_run_id.
- Authentication: JWT (python-jose + bcrypt) with hierarchical Clients → Users → Projects; DEV_MODE toggle for passwordless local development.
- Code organization: memory_work_items.py split into _wi_helpers.py (225 lines), _wi_classify.py (360 lines), _wi_markdown.py (600 lines) with shared imports; all modules < 1500 lines; recursive CTEs bounded to depth < 20 with safeguards.
- Date cascade validation: _apply_date_rules() prevents re-parenting work items to use cases with earlier due_dates; depth check added when wi_parent_id changes to prevent silent data inconsistency.
- File management: backend/memory/memory.yaml is canonical single-source mapping for output files and project creation; templates/ holds seed files; memory.yaml is internal engine only, not copied to projects.
- Database optimization: batch queries replace N+1 patterns (hotspot checks use single WHERE name = ANY(%s)); token counting: len(text) // 4; recursive CTEs bounded to depth < 20; unbounded CTE depth safeguards added.

---

## Project Documentation

# aicli — Shared AI Memory Platform

_Last updated: 2026-04-28_

> **How this file works**
> - Sections marked `<!-- user-managed -->` are yours to edit freely — they feed directly into CLAUDE.md.
> - Sections marked `<!-- auto-updated by /memory -->` are refreshed automatically when you run `/memory`.
>   You can still edit them; `/memory` will merge its output in without discarding your additions.
> - `## Deprecated` — list superseded decisions here; they will be hidden from CLAUDE.md key_decisions.
> - Run `/memory` to regenerate CLAUDE.md, cursor rules, and all LLM prompt files from this document.

---

<!-- user-managed -->
## Vision

**aicli gives every LLM the same project memory.**

When you switch between Claude Code, the aicli CLI, Cursor, or the web UI, the AI picks up
exactly where you left off — same codebase context, same decisions, same feature history.
No more copy-pasting context. No more re-explaining your architecture.

---

<!-- user-managed -->
## Core Goals

| # | Goal | Status |
|---|------|--------|
| 1 | **Shared LLM memory** — Claude Code, aicli CLI, Cursor all read the same knowledge base | ✓ Implemented |
| 2 | **Backlog pipeline** — Mirror → Backlog digest → User review → Use case files | ✓ Implemented |
| 3 | **Work Items** — AI-classified backlog items (open → active → done) backed by `mem_work_items` | ✓ Implemented |
| 4 | **Auto-deploy** — Stop hook → auto_commit_push.sh after every Claude Code session | ✓ Hooks |
| 5 | **Billing & usage** — Multi-user, server keys, balance, markup, coupons | ✓ Implemented |
| 6 | **Multi-LLM workflows** — Graph DAG: design → review → develop → test | ✓ Implemented |
| 7 | **Semantic search** — pgvector cosine similarity over events | ✓ Implemented |
| 8 | **Role YAML** — All agent roles + pipelines defined in `workspace/_templates/` (no inline Python) | ✓ Refactored |
| 9 | **MCP server** — 10 tools: search_memory, get_project_state, tags, backlog | ✓ Implemented |

---

## Memory Architecture

```
Layer 1 — Raw Capture (mem_mrr_*)
  ├── mem_mrr_prompts        raw prompt/response pairs (session-tagged, all in DB)
  ├── mem_mrr_commits        git commits (hash, msg, tags, diff_summary)
  ├── mem_mrr_commits_code   per-symbol diffs (tree-sitter: class, method, file)
  ├── mem_mrr_commits_file_stats   hotspot scores per file
  ├── mem_mrr_commits_file_coupling  co-change pairs
  ├── mem_mrr_items          document/meeting items
  └── mem_mrr_messages       Slack/chat messages

Layer 2 — Structured Artifacts (mem_ai_project_facts)
  Durable facts extracted by /memory → project_state.json
  ("uses pgvector", "auth is JWT") — updated by project_synthesis Haiku call

Layer 3 — Work Items (mem_work_items)
  AI-classified + user-reviewed: wi_type (use_case/feature/bug/task/requirement)
  user_status TEXT: open → pending → in-progress → review → done


*See PROJECT.md for full documentation (334 lines total)*

## Recent Work (last 5 prompts)

- [2026-03-30] `claude_cli`: It it still balnck. the error is Uncaught SyntaxError: Identifier '_esc' has already been declared t
- [2026-03-30] `claude_cli`: Is all table strucure is implemeted properly ? I dont see the table strucure ? 
- [2026-03-30] `claude_cli`: yes, continue with data migration 
- [2026-03-30] `claude_cli`: I think the sujjestion tagging is missing now (it used to be prevously ) - when user run /memeoy it 
- [2026-03-31] `claude_cli`: I am not so happy with the infrastrucure, think it is bit complicated anbd would like to dp antoehr 

---
*Full context: see `state/CONTEXT.md` — refresh with `GET /projects/aicli/context?save=true`*