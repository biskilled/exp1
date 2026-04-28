<!-- Last updated: 2026-04-28 18:38 UTC -->
## Project: aicli

## Stack

cli: Python 3.12 + prompt_toolkit + rich
backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
frontend: Vanilla JS + Electron + Vite
ui_components: xterm.js + Monaco editor + Cytoscape.js
storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
authentication: JWT (python-jose + bcrypt) + DEV_MODE
llm_providers: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
workflow_engine: Async DAG executor (asyncio.gather) + YAML config + per-node retry

## Key Decisions

- Memory architecture: 3 layers — raw captures (mem_mrr_* tables: prompts, commits, code diffs, file stats, coupling), structured artifacts (mem_ai_project_facts with Haiku synthesis), and work items (mem_work_items with pgvector embeddings ONLY for approved items UC/FE/BU/TA).
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; all output files (CLAUDE.md, CODE.md, PROJECT.md) regenerated from single JSON.
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task) and wi_parent_id linking children to use_case parents; wi_id format: AI0001 (draft) → UC/FE/BU/TA0001 (approved); only approved items embed and trigger 4-agent pipeline.
- Embeddings strategy: ONLY approved work items (wi_id: UC/FE/BU/TA) embed to pgvector; code.md, project_state.json, project facts, and prompts never embed.
- Work item re-embedding: triggered automatically on name/summary/description edits for approved items via update(); unapproved drafts (AI prefix) never embed.
- Commit-sourced items: auto-set score_status=5 and score_importance=5 via regex 'fixes BU0012'/'closes UC0001' pattern; enable auto-closure workflow.
- Prompts: all backend LLM prompts stored in YAML under backend/memory/prompts/ (command_memory.yaml, event_commit.yaml, command_work_items.yaml, mem_project_state.yaml, mem_session_tags.yaml, misc.yaml); loaded via prompt_loader utility.
- Role definitions: all agent roles and 4-agent pipeline (PM → Architect → Developer → Reviewer) defined in YAML under workspace/_templates/ (no inline Python).

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Commit-sourced work items auto-closure: regex 'fixes BU0012'/'closes UC0001' patterns auto-set score_status=5 and score_importance=5 for user approval in work item review queue.
- UI transparency badges: _waitingBadge() showing '⏳ X days waiting' for pending items and _openDaysBadge() showing '📂 X days open' for approved use cases in planner.js.
- MCP server fully operational: all 14 tools dispatched correctly via REST endpoints; backend running with db_connected: true; ready for new Claude Code sessions.
- Hotspot recency weighting: 180-day half-life formula applied in both parser and memory_files queries to prioritize recently-changed files.

_Last updated: 2026-04-28 18:38 UTC_