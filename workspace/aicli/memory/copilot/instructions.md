<!-- Last updated: 2026-04-29 16:37 UTC -->
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

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts via /memory POST + Haiku synthesis) → work items (mem_work_items with wi_parent_id hierarchy); ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; CLAUDE.md, CODE.md, PROJECT.md all regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech tags from project_state.json tech_stack (no hardcoded regex), enabling intelligent pipeline routing
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval
- Code.md generation: per-symbol diffs via tree-sitter with file coupling/hotspot tables; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio)
- Embeddings strategy: ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector; code.md, project_state.json, project facts, prompts, commits never embed
- MCP server: 10 tools (search_memory, get_project_state, list_work_items, get_work_item, list_commits, search_commits, due_date filters, tags, backlog, classify_wi) dispatched via REST; stdio transport, local machine, no auth required

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Multiple chore commits after claude cli session (ebf898a3, 1f8ecc78) indicating rapid iteration on project state management
- Fix undefined column errors in route_entities and route_history: psycopg2 UndefinedColumn errors for lifecycle (line 359) and event_type (line 228); columns removed in m080 but route code still references them
- Fix PROJECT.md file loading timeout: >60 second load when opening project; likely N+1 queries or missing database indices
- Remove lifecycle tags and drag-and-drop from Planner UI: deprecated lifecycle field still active in drag-and-drop and category display; fix [object object] tag display bug

_Last updated: 2026-04-29 16:37 UTC_