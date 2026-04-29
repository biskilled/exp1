<!-- Last updated: 2026-04-29 09:22 UTC -->
## Project: aicli

## Stack

cli: Python 3.12 + prompt_toolkit + rich
backend_framework: FastAPI + uvicorn
backend_auth: JWT (python-jose + bcrypt) + DEV_MODE toggle
database: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
database_client: psycopg2
frontend: Vanilla JS + Electron + Vite
ui_components: xterm.js + Monaco editor + Cytoscape.js
llm_providers: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok

## Key Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts) → work items (mem_work_items with wi_parent_id hierarchy); ONLY approved items (UC/FE/BU/TA prefix) embed to pgvector
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; all 3 output files (CLAUDE.md, CODE.md, PROJECT.md) regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status (open → pending → in-progress → review → done), wi_parent_id linking children to use_case parents; wi_id: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval
- Code.md generation: per-symbol diffs via tree-sitter with file coupling/hotspot tables; hotspot scores use 180-day half-life recency weighting
- Embeddings strategy: ONLY approved work items embed to pgvector (1536-dim); code.md, project_state.json, facts, prompts, commits never embed
- MCP server: 14 tools (search_memory, get_project_state, list_work_items, etc.) dispatched via REST in agents/mcp/server.py; stdio transport, local machine only, no auth
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Multiple chore commits on 2026-04-28/29 (ebf898a3 session) — likely auto_commit_push.sh hook executions after Claude Code sessions; commit messages minimal
- Fix PROJECT.md file loading timeout (>60s) — N+1 queries or missing database indices; performance audit with single-pass reading ongoing
- Fix undefined column errors in route_entities (line 359) and route_history (line 228) referencing removed 'lifecycle' field from m080 migration
- Fix commit sync batch upsert error in /history/commits/sync API (execute_values parameter mismatch) and tag counter UI not updating

_Last updated: 2026-04-29 09:22 UTC_