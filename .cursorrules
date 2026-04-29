<!-- Last updated: 2026-04-29 20:09 UTC -->
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
- Role YAML factory defaults: workspace/_templates/pipelines/roles/role_*.yaml are read-only; ON CONFLICT DO NOTHING seeds only new roles on startup; mng_agent_roles DB is single source of truth at runtime; UI edits persist in DB; Refresh button re-seeds YAML; Restore button resets individual role to YAML base_snapshot
- Role base snapshot feature: POST /agent-roles/{id}/set-base snapshots current system_prompt, provider, model, tools, mcp as base_snapshot; Restore button resets role to last saved base; Save as Base button locks current state; visual status pills (BASED/UPDATED/EXTERNAL) indicate state relative to base
- Tech tag auto-detection: reads tech_stack from project_state.json instead of hardcoded regex; tags validated against actual project technologies in _build_tech_tags_block(), enabling accurate delivery_type routing to pipelines
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech tags from project_state.json tech_stack
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Role base snapshot feature: snapshots system_prompt, provider, model, tools, mcp with visual status pills (BASED/UPDATED/EXTERNAL) and Restore button functionality
- Roles UI styling: colored pill backgrounds for Provider+Model, styled reset buttons, full background shapes for model display
- MCP Catalog navigation: consolidated Roles, Pipelines, MCP Catalog under Workflows group in left nav; edit cards for all 10 MCPs with activate/deactivate
- Tool category multi-select UI: replaced individual tool checkboxes with category-based dropdowns (git, files, memory, etc.); users select entire categories

_Last updated: 2026-04-29 20:09 UTC_