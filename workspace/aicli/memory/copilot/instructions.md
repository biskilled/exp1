<!-- Last updated: 2026-04-29 18:40 UTC -->
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
- Role YAML → DB sync: YAML files in workspace/_templates/pipelines/roles/ are read-only factory defaults; ON CONFLICT DO NOTHING seeds only new roles on startup; mng_agent_roles DB table is single source of truth for runtime; UI edits persist in DB across restarts
- Tech tag auto-detection: reads tech_stack from project_state.json instead of hardcoded regex; tags validated against actual project technologies in _build_tech_tags_block(), enabling accurate delivery_type routing to pipelines
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech tags from project_state.json tech_stack
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval
- Code.md generation: per-symbol diffs via tree-sitter with file coupling/hotspot tables; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio)

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Chore commits from Claude CLI session 1f8ecc78 (2026-04-29 16:36–18:39): multiple auto-committed changes via auto_commit_push.sh hook after each Claude Code session, indicating active development iteration
- System prompts consolidation debugging: Multiple system prompts visible in UI despite consolidation to 3 presets; investigating duplicate entries in mng_agent_roles or system_prompts.yaml
- Database schema and route entity errors: psycopg2 UndefinedColumn errors in route_entities and route_history for lifecycle (line 359) and event_type (line 228); columns removed in m080 but route code still references them
- PROJECT.md file loading performance: Timeout (>60 seconds) likely due to N+1 queries or missing database indices on mem_work_items or mem_ai_events

_Last updated: 2026-04-29 18:40 UTC_