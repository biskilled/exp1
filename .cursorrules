<!-- Last updated: 2026-04-28 18:57 UTC -->
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

- Memory 3-layer architecture: raw captures (mem_mrr_* tables: prompts, commits, code diffs, file stats, coupling) → structured artifacts (mem_ai_project_facts) → work items (mem_work_items with pgvector ONLY for approved UC/FE/BU/TA items).
- Single source of truth: /memory POST endpoint is the ONLY writer to project_state.json via get_project_context() + Haiku synthesis; all 3 output files (CLAUDE.md, CODE.md, PROJECT.md) regenerated from single JSON.
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement) and wi_parent_id linking children to use_case parents; wi_id: AI0001 (draft) → UC/FE/BU/TA0001 (approved); only approved items embed and trigger 4-agent pipeline.
- Embeddings strategy: ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector (1536-dim, text-embedding-3-small); code.md, project_state.json, project facts, prompts, and commits never embed.
- Code.md generation: per-symbol diffs via tree-sitter (Python/JS/TS) with file coupling/hotspot tables; refreshed post-commit and post-memory; hotspot scores use 180-day half-life recency: EXP(-0.693 × age_ratio).
- Work item auto-closure: regex patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval in review queue.
- Prompts: all backend LLM prompts stored in YAML under backend/memory/prompts/ (command_memory.yaml, event_commit.yaml, command_work_items.yaml, mem_project_state.yaml, mem_session_tags.yaml, misc.yaml); loaded via prompt_loader utility.
- MCP server: 14 tools dispatched via REST endpoints in agents/mcp/server.py with unified dispatch matching tool name to REST route; stdio transport running locally on developer machine.

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Commit-sourced work items auto-closure: regex patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5; items await user approval in work item review queue before closure.
- UI transparency badges: _waitingBadge() showing '⏳ X days waiting' (grey ≤3d, amber 4–7d, red >7d) for pending items and _openDaysBadge() showing '📂 X days open' for approved use cases in Planner.
- Hotspot recency weighting: 180-day half-life formula EXP(-0.693 × age_ratio) applied in both parser and memory_files queries to deprioritize stale files and surface active development areas.
- MCP server fully operational: all 14 tools dispatched correctly via REST endpoints; Backend running db_connected: true; ready for Claude Code sessions to use shared memory and trigger 4-agent workflows.

_Last updated: 2026-04-28 18:57 UTC_