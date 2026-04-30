<!-- Last updated: 2026-04-30 21:37 UTC -->
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

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts via /memory POST + Haiku synthesis) → approved work items (mem_work_items with wi_parent_id hierarchy); ONLY approved items (UC/FE/BU/TA prefix) embed to pgvector
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; CLAUDE.md, CODE.md, PROJECT.md all regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Role YAML as factory defaults: workspace/_templates/pipelines/roles/*.yaml are read-only templates seeded with ON CONFLICT DO NOTHING on backend startup; mng_agent_roles DB is single source of truth at runtime; UI edits persist in DB only; base_snapshot JSONB stores pristine state for versioning
- System prompts: 3 shared canonical presets (Coding—General, Design & Planning, Review & Quality) in workspace/_templates/pipelines/system_prompts.yaml; all roles default to one preset; system_roles table contains only 3 canonical entries
- Agent execution: roles define identity/behavior (system_prompt, provider/model, temperature/top_p, tools, mcp, max_iterations); pipeline nodes can override provider/model/temperature/top_p/max_iterations per stage; nodes default to role values when not overridden
- Pipeline execution: 4-agent async DAG triggered only on approved items under approved use cases; executed via asyncio.gather; max_iterations mandatory per node; per-node checkboxes: max_retry, stateless, continue-on-fail, approval-gate
- Pipeline & role activation: Settings → Roles & Pipelines dual-pane shows all roles/pipelines with activation checkboxes; only activated items appear in main tabs and are executable; pipeline activation requires all constituent roles to be activated; mode_use_case and mode_item flags control visibility

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Auto-deploy workflow: stop hook integration with auto_commit_push.sh triggers after every Claude Code session to sync memory and work items back to central repo
- Settings/pipeline UI mode filtering: mode_use_case and mode_item checkboxes (m087 migration) control pipeline visibility in use case vs item execution contexts
- DOM update optimization in settings: in-place DOM patches on checkbox toggles instead of full page reloads; _toggleRoleActivated/_togglePipelineActivated now patch UI without renderAgentRoles refresh
- Dashboard restoration: Mirror Data cards, Work Items/Use Cases sections, Pipeline Runs health tiles for last 24h

_Last updated: 2026-04-30 21:37 UTC_