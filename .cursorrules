<!-- Last updated: 2026-04-28 19:50 UTC -->
## Project: aicli

## Stack

cli: Python 3.12 + prompt_toolkit + rich
backend_framework: FastAPI + uvicorn
backend_auth: JWT (python-jose + bcrypt) + DEV_MODE
database: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
database_client: psycopg2
frontend: Vanilla JS + Electron + Vite
ui_components: xterm.js + Monaco editor + Cytoscape.js
llm_providers: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok

## Key Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts) → work items (mem_work_items with pgvector ONLY for approved UC/FE/BU/TA items)
- Single source of truth: /memory POST endpoint synthesizes project_state.json via Haiku; all 3 output files (CLAUDE.md, CODE.md, PROJECT.md) regenerated from single JSON
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement) and wi_parent_id linking children to use_case parents; wi_id: AI0001 (draft) → UC/FE/BU/TA0001 (approved); only approved items embed and trigger 4-agent pipeline
- Embeddings strategy: ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector (1536-dim, text-embedding-3-small); code.md, project_state.json, project facts, and commits never embed
- Code.md generation: per-symbol diffs via tree-sitter (Python/JS/TS) with file coupling/hotspot tables; refreshed post-commit and post-memory; hotspot scores use 180-day half-life recency: EXP(-0.693 × age_ratio)
- Prompts: all backend LLM prompts stored in YAML under workspace/_templates/; loaded via prompt_loader utility; no inline Python prompts
- MCP server: 10 tools dispatched via REST endpoints in agents/mcp/server.py; stdio transport running locally on developer machine
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract; unified LLM abstraction layer

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Fix PROJECT.md file loading timeout (>60s) and backend startup race condition — likely N+1 queries in project context loading or missing database indices
- Fix commit sync batch upsert error in /history/commits/sync API (execute_values parameter mismatch) and tag counter not updating in Planner UI when tags added/removed
- Verify MCP server with 10 tools fully operational for Claude Code sessions with shared project memory; ensure stdio transport stability and tool dispatch correctness
- Complete production readiness: memory files (CLAUDE.md, CODE.md, PROJECT.md) provide good project structure; work items/use cases function correctly; 4-agent pipeline ready

_Last updated: 2026-04-28 19:50 UTC_