<!-- Last updated: 2026-04-29 15:36 UTC -->
## Project: aicli

## Stack

language_cli: Python 3.12
cli_framework: prompt_toolkit + rich
backend_framework: FastAPI + uvicorn
backend_auth: JWT (python-jose + bcrypt) + DEV_MODE toggle
database: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
database_client: psycopg2
frontend_framework: Vanilla JS + Electron + Vite
ui_components: xterm.js + Monaco editor + Cytoscape.js

## Key Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts via /memory POST + Haiku synthesis) → work items (mem_work_items with wi_parent_id hierarchy); ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector (1536-dim, text-embedding-3-small)
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; all 3 output files (CLAUDE.md, CODE.md, PROJECT.md) regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001', 'resolve TA0003') in commit messages auto-set score_status=5 and score_importance=5 for user approval in review queue
- Code.md generation: per-symbol diffs via tree-sitter with file coupling/hotspot tables; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio) to prioritize recent changes
- Embeddings strategy: ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector; code.md, project_state.json, project facts, prompts, and commits never embed
- MCP server: 10 tools (search_memory, get_project_state, list_work_items, get_work_item, list_commits, search_commits, due_date_before filter, etc.) dispatched via REST endpoints in agents/mcp/server.py; stdio transport running locally on developer machine with no auth
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract; temperature, max_tokens, model configurable per role

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Fix undefined column errors in route_entities and route_history: columns removed in migration m080 (lifecycle, event_type) but route code not yet updated — causing UndefinedColumn psycopg2 errors on startup; audit all column references
- Fix backend startup race condition and project selector: active project not displayed in project selector after startup; recent projects list missing aiCli project; likely init sequencing issue in project loader or database connection timing
- Remove lifecycle tags and drag-and-drop issues from Planner UI: lifecycle field deprecated but active references remain in drag-and-drop, category display, and tagging UI; also fix [object object] display bug in tag additions
- Optimize PROJECT.md file loading: currently >60s timeout when opening project; performance audit needed for database indices on project, wi_type, user_status or single-pass read refactoring

_Last updated: 2026-04-29 15:36 UTC_