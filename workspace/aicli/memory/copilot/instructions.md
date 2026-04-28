<!-- Last updated: 2026-04-28 19:32 UTC -->
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

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts) → work items (mem_work_items with pgvector ONLY for approved UC/FE/BU/TA items)
- Single source of truth: /memory POST endpoint is the ONLY writer to project_state.json via get_project_context() + Haiku synthesis; all 3 output files (CLAUDE.md, CODE.md, PROJECT.md) regenerated from single JSON
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement) and wi_parent_id linking children to use_case parents; wi_id: AI0001 (draft) → UC/FE/BU/TA0001 (approved); only approved items embed and trigger 4-agent pipeline
- Embeddings strategy: ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector (1536-dim, text-embedding-3-small); code.md, project_state.json, project facts, prompts, and commits never embed
- Code.md generation: per-symbol diffs via tree-sitter (Python/JS/TS) with file coupling/hotspot tables; refreshed post-commit and post-memory; hotspot scores use 180-day half-life recency: EXP(-0.693 × age_ratio)
- Work item auto-closure: regex patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval in review queue
- Prompts: all backend LLM prompts stored in YAML under backend/memory/prompts/; loaded via prompt_loader utility; no inline Python prompts
- MCP server: 10+ tools dispatched via REST endpoints with unified dispatch matching tool name to REST route; stdio transport running locally on developer machine

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Commit-sourced work items auto-closure: regex patterns ('fixes', 'closes') auto-set score_status=5 and score_importance=5; items queued for user approval in review queue
- UI transparency badges fully implemented: pending work items show ⏳ (grey/amber/red by age), approved use cases show 📂 (days since approval)
- MCP server fully operational: all 10+ tools dispatched correctly via REST endpoints; Backend db_connected: true; ready for Claude Code sessions
- Code refactoring complete: memory_work_items.py split (-49%, now 1343L); hotspot recency weighting applied; date cascade validation added; N+1 queries eliminated

_Last updated: 2026-04-28 19:32 UTC_