<!-- Last updated: 2026-04-28 11:47 UTC -->
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

- Memory architecture: 3 layers — raw captures (mem_mrr_* tables: prompts, commits, code diffs, file stats, coupling), structured artifacts (mem_ai_project_facts with Haiku synthesis), and work items (mem_work_items with pgvector embeddings ONLY for approved items prefixed UC/FE/BU/TA).
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; all 5 output files (CLAUDE.md, CODE.md, PROJECT.md, cursor/rules, api/) regenerated from single JSON.
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task) and wi_parent_id linking children to use_case parents; wi_id format: AI0001 (unapproved draft) → UC/FE/BU/TA0001 (approved); only approved items embed and trigger 4-agent pipeline.
- Code.md generation: per-symbol diffs via tree-sitter (Python/JS/TS) with file coupling/hotspot tables; refreshed post-commit and post-memory; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio) to prioritize recently-changed files.
- Embeddings strategy: ONLY approved work items (wi_id: UC/FE/BU/TA) embed to pgvector; code.md, project_state.json, project facts, and prompts never embed; /search/semantic searches work_items only.
- Work item re-embedding: triggered automatically on name/summary/description edits for approved items via update(); unapproved drafts (AI prefix) never embed; commit-sourced items auto-set score_status=5 and score_importance=5 via regex 'fixes BU0012' pattern for user approval.
- Prompts: all backend LLM prompts stored in YAML under backend/memory/prompts/ (command_memory.yaml, event_commit.yaml, command_work_items.yaml, mem_project_state.yaml, mem_session_tags.yaml, misc.yaml); loaded via prompt_loader utility.
- MCP server: 10 tools (search_memory, get_project_state, list_work_items, classify, approve, run_pipeline, tags, backlog, etc.) dispatched via REST endpoints; stdio server in agents/mcp/server.py with unified dispatch pattern matching tool name to route.

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Auto-commit-push hook integration: chore commits after every Claude CLI session (ebf898a3, d113294c) indicating post-session state capture and memory sync working.
- MCP server fully operational: 10 tools dispatched correctly via REST endpoints; Backend running with db_connected status; ready for Claude Code sessions.
- Commit-sourced work items auto-closure: regex 'fixes BU0012'/'closes FE0001' patterns auto-set score_status=5 and score_importance=5 for user approval in work item review queue.
- Hotspot recency weighting: 180-day half-life formula EXP(-0.693 × age_ratio) applied in memory_files queries to prioritize recently-changed files in CODE.md rankings.

_Last updated: 2026-04-28 11:47 UTC_