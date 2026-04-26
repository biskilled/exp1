# Role: Developer — aicli

You are working on **aicli**.

## Key Architectural Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; .ai/ and _system/ removed (replaced by cli/ structure)
- Workspace structure: cli/{claude,mcp}/ for hooks/configs; pipelines/{prompts,samples}/ for workflows; documents/ for project files; state/ for runtime state
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim) for semantic search; unified mem_mrr_* and mem_work_items tables; mem_ai_events dropped
- Memory system: /memory endpoint generates 5 files (PROJECT.md, CODE.md, CLAUDE.md, cursorrules.md, recent_work.md) from project_state.json + database; token-limited by project.yaml config
- Memory files managed by backend/memory/memory.yaml: canonical single source (not duplicated in _templates); templates in backend/memory/templates/
- Code.md structure: public symbols (classes/methods/functions) + file coupling/hotspot tables with is_latest BOOLEAN pattern; single source for all LLM context
- mem_mrr_commits_code (19 columns) with is_latest BOOLEAN: replaces need for separate code_symbols table; updated per commit; partial index optimization
- Project facts deprecated: mem_ai_project_facts no longer auto-populated during /memory; facts extracted inline from memory synthesis; conflict_detection merged into mem_project_state.yaml
- Work Items + Use Cases: items tab shows pending AI-classified items; use cases tab displays hierarchy with due dates, completion validation, auto-markdown generation
- Drag-and-drop parent-child/merge: unconditional e.preventDefault() + document.elementFromPoint() target detection (same implementation for both Work Items and Use Cases)
- Undo as persistent toolbar button: stores reverse API call closure capturing original parent_id before link modification; works for both linking and partial merge
- JWT authentication: python-jose + bcrypt with DEV_MODE toggle; hierarchical Clients → Users → Projects
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract
- Backend prompts: all LLM prompts migrated to YAML files under backend/memory/mem_*.yaml (named by table domain); templates in backend/memory/templates/
- Electron desktop UI: Vanilla JS with xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development; hardcoded localhost removed

---

## Project Documentation

# aicli — Shared AI Memory Platform

_Last updated: 2026-04-26_

> **How this file works**
> - Sections marked `<!-- user-managed -->` are yours to edit freely — they feed directly into CLAUDE.md.
> - Sections marked `<!-- auto-updated by /memory -->` are refreshed automatically when you run `/memory`.
>   You can still edit them; `/memory` will merge its output in without discarding your additions.
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
  ├── mem_mrr_prompts        raw prompt/response pairs (session-tagged)
  ├── mem_mrr_commits        git commits (hash, msg, tags, diff_summary)
  ├── mem_mrr_commits_code   per-symbol diffs (tree-sitter: class, method, file)
  ├── mem_mrr_items          document/meeting items
  └── mem_mrr_messages       Slack/chat messages

Layer 2 — AI Events (mem_ai_events)
  Haiku digest + OpenAI embedding (text-embedding-3-small, 1536-dim)
  event_type: prompt_batch | commit | session_summary | item | workflow
  source_id: batch_{hash8}_{tagfp8} for commits; last prompt UUID for prompt batches
  Tags: only user-intent {phase, feature, bug, source} stored

Layer 3 — Structured Artifacts (mem_ai_project_facts)
  Durable facts ("uses pgvector", "auth is JWT")

Layer 4 — Work Items (mem_work_items)


*See PROJECT.md for full documentation (310 lines total)*

## Recent Work (last 5 prompts)

- [2026-03-30] `claude_cli`: It it still balnck. the error is Uncaught SyntaxError: Identifier '_esc' has already been declared t
- [2026-03-30] `claude_cli`: Is all table strucure is implemeted properly ? I dont see the table strucure ? 
- [2026-03-30] `claude_cli`: yes, continue with data migration 
- [2026-03-30] `claude_cli`: I think the sujjestion tagging is missing now (it used to be prevously ) - when user run /memeoy it 
- [2026-03-31] `claude_cli`: I am not so happy with the infrastrucure, think it is bit complicated anbd would like to dp antoehr 

---
*Full context: see `state/CONTEXT.md` — refresh with `GET /projects/aicli/context?save=true`*