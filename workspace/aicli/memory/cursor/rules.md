<!-- Last updated: 2026-04-27 22:28 UTC -->
## Project: aicli

## Stack

cli: Python 3.12 + prompt_toolkit + rich
backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
frontend: Vanilla JS + Electron + Vite
ui_components: xterm.js + Monaco editor + Cytoscape.js
storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
authentication: JWT (python-jose + bcrypt) + DEV_MODE
llm_providers: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
workflow_engine: Async DAG executor (asyncio.gather) + YAML config + per-node retry + 4-agent pipeline (PM→Architect→Developer→Reviewer)

## Key Decisions

- Memory architecture: 3 layers — raw captures (mem_mrr_*: prompts, commits, code diffs, file stats, coupling), structured artifacts (mem_ai_project_facts with Haiku synthesis), and work items (mem_work_items with pgvector embeddings ONLY for approved items).
- Single source of truth: /memory POST endpoint is the ONLY writer to project_state.json via get_project_context() + Haiku synthesis; all 5 output files (CLAUDE.md, CODE.md, PROJECT.md, cursor/rules, api/) regenerated from this single JSON.
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task) and wi_parent_id linking children to use_case parents; wi_id format: AI0001 (unapproved draft) → UC/FE/BU/TA0001 (approved); only approved items embed and trigger 4-agent pipeline.
- Code.md generation: per-symbol diffs via tree-sitter (Python/JS/TS) with file coupling/hotspot tables; refreshed post-commit and post-memory via unified get_project_context() path; stores llm_summary per symbol in mem_mrr_commits_code.
- Embeddings: ONLY approved work items (wi_id: UC/FE/BU/TA) embed to pgvector (1536-dim, text-embedding-3-small); code.md, project_state.json, project facts, and prompts never embed; /search/semantic searches work_items only.
- Work item re-embedding: triggered automatically only on name/summary/description edits for approved items via update(); unapproved drafts (AI prefix) never embed; commit-sourced items auto-set score_status=5 via regex 'fixes BU0012' pattern.
- Prompts: all backend LLM prompts stored in YAML under backend/memory/prompts/ named by trigger (command_memory.yaml, event_commit.yaml, command_work_items.yaml, mem_project_state.yaml, mem_session_tags.yaml, misc.yaml); loaded via prompt_loader utility.
- MCP server: 14 tools rewired to REST endpoints (search_memory, get_project_state, tags, backlog, create_entity→POST /wi/, list_work_items, run_work_item_pipeline, update_work_item, approve_work_items, etc.); stdio server in agents/mcp/server.py.

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Rapid iteration cycle: 15 consecutive git commits in ~9 hours (2026-04-27 13:11–22:28) on session ebf898a3 indicate active refinement of core memory engine or work item pipeline.
- High-frequency chore commits: pattern suggests automated post-Claude-session hooks (auto_commit_push.sh) are working and firing regularly with minimal commit messages.
- Likely areas under development: memory synthesis, work item classification, database query optimization, or output file regeneration logic based on commit density.

_Last updated: 2026-04-27 22:28 UTC_