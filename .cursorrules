<!-- Last updated: 2026-05-02 23:24 UTC -->
## Project: aicli

## Stack

language_cli: Python 3.12
cli_framework: prompt_toolkit + rich
backend_framework: FastAPI + uvicorn
backend_auth: JWT (python-jose + bcrypt) + DEV_MODE toggle
database: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
database_client: psycopg2
frontend_framework: Vanilla JS (Vite) + Electron
ui_components: xterm.js + Monaco editor + Cytoscape.js

## Key Decisions

- 3-layer memory architecture: raw captures (mem_mrr_* tables: prompts, commits, commits_code, commits_file_stats, commits_file_coupling, items, messages) → structured artifacts (mem_ai_project_facts) → approved work items (mem_work_items); ONLY approved items (UC/FE/BU/TA prefix) embed to pgvector; re-embedding on item change automatic
- Single source of truth: /memory POST endpoint + project_synthesis Haiku call is ONLY writer to project_state.json; CLAUDE.md, CODE.md, PROJECT.md all regenerated from this JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Role YAML as factory defaults: workspace/_templates/pipelines/roles/*.yaml are read-only templates seeded with ON CONFLICT DO NOTHING on backend startup; mng_agent_roles DB is single source of truth at runtime; base_snapshot JSONB stores pristine state
- System prompts: 3 shared canonical presets (Coding—General, Design & Planning, Review & Quality) in workspace/_templates/pipelines/system_prompts.yaml; all roles default to one preset; system_roles table contains only 3 canonical entries
- Agent execution: roles define identity/behavior (system_prompt, provider/model, temperature/top_p, tools, mcp, max_iterations); pipeline nodes can override provider/model/temperature/top_p/max_iterations per stage; nodes default to role values when not overridden
- Pipeline execution: 4-agent async DAG triggered on approved items; executed via asyncio.gather; max_iterations mandatory per node; per-node checkboxes: max_retry, stateless, continue-on-fail, approval-gate; mode_use_case and mode_item flags control visibility/executability; pipeline reports save to workspace/{project}/documents/pipelines/{pipeline_name}/{timestamp}_{slug}.md
- Pipeline & role activation: Settings → Roles & Pipelines dual-pane shows all roles/pipelines with activation checkboxes; only activated items appear in main tabs and are executable; pipeline activation requires all constituent roles to be activated

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Chore commits from session 90bb3086: multiple git commits over May 2–3 indicate ongoing refinements to core systems
- Pipeline report generation: structured markdown reports persist to workspace/{project}/documents/pipelines/{pipeline_name}/ with input/output per stage, cost/token breakdown, and execution logs
- Per-node dynamic model dropdown: provider-model cache wired; available models update automatically when user changes provider
- Execution logs UI refinement: per-stage logs now appear as collapsible details under each stage summary only; stage summaries shown at top

_Last updated: 2026-05-02 23:24 UTC_