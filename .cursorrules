<!-- Last updated: 2026-04-29 22:35 UTC -->
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
- Role YAML factory defaults: workspace/_templates/pipelines/roles/role_*.yaml are read-only templates; ON CONFLICT DO NOTHING seeds only new roles on startup; mng_agent_roles DB is single source of truth at runtime; UI edits persist in DB only
- Role parameters: system_prompt + system_prompt_preset (references 3 shared presets from system_prompts.yaml), provider/model, tools (by category: git/files/memory), mcp (multi-select), max_iterations, temperature, top_p configured per role; pipeline can override temperature/top_p per stage; base_snapshot stores pristine role state for restore
- System prompts consolidation: 3 shared system prompt presets in workspace/_templates/pipelines/system_prompts.yaml (Coding—General, Design & Planning, Review & Quality); all roles default to canonical preset on creation
- Tech tag auto-detection: reads tech_stack from project_state.json instead of hardcoded regex; tags validated against actual project technologies in _build_tech_tags_block()
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech_tags from project_state.json tech_stack

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Multi-session auto-commit workflow: chore commits after each Claude CLI session (1f8ecc78 and 45ca1683) indicate active session-based commit hook integration
- Role UI and system prompts finalization: 3 canonical presets (Coding—General, Design & Planning, Review & Quality) mapped to all 10 roles with status badges (BASED/UPDATED/EXTERNAL)
- Temperature/top_p parameter support: implemented in mng_agent_roles DB schema (migration m082) and provider adapters; pipeline stage-level override ready for execution phase
- Navigation structure finalized: Roles, Pipelines, MCP Catalog unified under Workflows group; MCP Catalog wired with activate/deactivate/edit modals; role library shows provider+model pills

_Last updated: 2026-04-29 22:35 UTC_