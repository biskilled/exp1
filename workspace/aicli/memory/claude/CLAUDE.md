# Role: Developer — aicli

You are working on **aicli**.

## Key Architectural Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts via /memory POST + Haiku synthesis) → approved work items (mem_work_items with wi_parent_id hierarchy); ONLY approved items (UC/FE/BU/TA prefix) embed to pgvector
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; CLAUDE.md, CODE.md, PROJECT.md all regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Role YAML as factory defaults: workspace/_templates/pipelines/roles/*.yaml are read-only templates seeded with ON CONFLICT DO NOTHING on backend startup; mng_agent_roles DB is single source of truth at runtime; base_snapshot JSONB stores pristine state for versioning; edit/reset/set-as-base workflow preserves template integrity
- System prompts: 3 shared canonical presets (Coding — General, Design & Planning, Review & Quality) in workspace/_templates/pipelines/system_prompts.yaml; all roles default to one preset; system_roles table contains only 3 canonical entries; old presets soft-deleted
- Agent execution: roles define identity/behavior (system_prompt, provider/model, temperature/top_p, tools, mcp, max_iterations); pipeline nodes can override provider/model/temperature/top_p/max_iterations per stage; nodes default to role values when not overridden; ToolUseBlock handling via getattr(tc, 'input') with fallback
- Pipeline execution: 4-agent async DAG triggered on approved items; executed via asyncio.gather; max_iterations mandatory per node; per-node checkboxes: max_retry, stateless, continue-on-fail, approval-gate; mode_use_case and mode_item flags control visibility/executability in UC vs item contexts; each stage captures steps_json (ReAct trace) and input_snapshot (handoff dict) to pr_pipeline_run_stages
- Pipeline & role activation: Settings → Roles & Pipelines dual-pane shows all roles/pipelines with activation checkboxes; only activated items appear in main tabs and are executable; pipeline activation requires all constituent roles to be activated; DOM updates are in-place (no full page reload) on checkbox changes
- Tool category bundles: tool selection by category (git/files/memory) instead of individual items; categories show tool count; multi-select in role editor
- Execute bar unified input: output folder combobox + searchable project docs dropdown + multi-file upload in same row; files shown as removable chips; supports multiple document and file selections; integrated into pipeline, role, and use-case execution
- Pipeline execution entry points: (1) Pipelines tab with node diagram and exec bar, (2) /pipeline [name] slash command in Chat using all preceding prompts as context, (3) /role [name] slash command for direct role execution, (4) Use Cases section with approval gating and pipeline selection per item (filtered by mode_use_case and mode_item flags)
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech_tags from project_state.json tech_stack
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval
- Auto-deploy workflow: stop hook integration with auto_commit_push.sh to sync memory and work items back to central repo after Claude Code sessions
- Stage execution logging: steps_json captures ReAct iteration trace (tool_name, tool_args, observation) and score_dots display (●●●●○ visual indicator of completion 0-5); input_snapshot preserves handoff context; stage detail panels show input summary and output artifacts (files, code changes, text)

---

## Project Documentation

# aicli — Shared AI Memory Platform

_Last updated: 2026-05-02_

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