<!-- Last updated: 2026-04-27 22:39 UTC -->
## Project: aicli

## Stack

cli: Python 3.12 + prompt_toolkit + rich
backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
frontend: Vanilla JS + Electron + Vite
ui_components: xterm.js + Monaco editor + Cytoscape.js
storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
authentication: JWT (python-jose + bcrypt) + DEV_MODE
llm_providers: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
workflow_engine: Async DAG executor (asyncio.gather) + YAML config + per-node retry + 4-agent pipeline

## Key Decisions

- Memory architecture: 3 layers — raw captures (mem_mrr_*: prompts, commits, code diffs, file stats, coupling), structured artifacts (mem_ai_project_facts with Haiku synthesis), and work items (mem_work_items with pgvector embeddings ONLY for approved items prefixed UC/FE/BU/TA).
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; all 5 output files (CLAUDE.md, CODE.md, PROJECT.md, cursor/rules, api/) regenerated from single JSON.
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task) and wi_parent_id linking children to use_case parents; wi_id format: AI0001 (unapproved draft) → UC/FE/BU/TA0001 (approved); only approved items embed and trigger 4-agent pipeline.
- Work item classification pipeline: POST /wi/{project}/classify deletes AI draft rows, calls Claude to tag/classify remaining items, then user explicitly approves drafts to convert to UC/FE/BU/TA0001 prefixes.
- Code.md generation: per-symbol diffs via tree-sitter (Python/JS/TS) with file coupling/hotspot tables; refreshed post-commit and post-memory; hotspot scores recency-weighted (180-day half-life).
- Embeddings strategy: ONLY approved work items (wi_id: UC/FE/BU/TA) embed to pgvector; code.md, project_state.json, project facts, and prompts never embed; /search/semantic searches work_items only.
- Work item re-embedding: triggered automatically on name/summary/description edits for approved items via update(); unapproved drafts (AI prefix) never embed; commit-sourced items auto-set score_status=5 via regex 'fixes BU0012' pattern.
- Prompts: all backend LLM prompts stored in YAML under backend/memory/prompts/ (command_memory.yaml, event_commit.yaml, command_work_items.yaml, mem_project_state.yaml, mem_session_tags.yaml, misc.yaml); loaded via prompt_loader utility.

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Commit chore cycles (2026-04-27 13:25–22:38): 15 sequential auto-commits from Claude CLI session ebf898a3, indicating rapid development iteration with incremental memory/state updates.
- Code audit cycle (sessions 35-40): fresh aicli_memory.md audit reviewing all changes from last 10-15 prompts for optimization, SQL efficiency, code duplication, and file length reasonableness; 4 parallel audit agents verifying memory files, work items, code quality, and production readiness.
- Production readiness assessment: verified memory files provide good project structure view, work items/use cases function correctly, code quality acceptable, no stale/unused data remains.
- Memory file convergence: unified get_project_context() path eliminates double file-reads; _load_context() now splits DB queries and PROJECT.md parsing; all 5 output files regenerate from single DB source.

_Last updated: 2026-04-27 22:39 UTC_