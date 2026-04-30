<!-- Last updated: 2026-04-30 13:20 UTC -->
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

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts via /memory POST + Haiku synthesis) → approved work items (mem_work_items with wi_parent_id hierarchy); ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; CLAUDE.md, CODE.md, PROJECT.md all regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Work item classification pipeline: POST /wi/{project}/classify deletes AI draft rows, synthesizes Haiku facts, classifies backlog items by type, user reviews and approves to assign UC/FE/BU/TA IDs
- Role YAML as factory defaults: workspace/_templates/pipelines/roles/role_*.yaml are read-only templates seeded with ON CONFLICT DO NOTHING on backend startup; mng_agent_roles DB is single source of truth at runtime; UI edits persist in DB only; base_snapshot JSONB stores pristine state; POST /agent-roles/{id}/refresh reloads YAML and updates DB
- System prompts: 3 shared canonical presets (Coding—General, Design & Planning, Review & Quality) in workspace/_templates/pipelines/system_prompts.yaml; all roles default to one preset; system roles table cleaned to 3 canonical entries only
- Role parameters: system_prompt + system_prompt_preset (references shared preset), provider/model/temperature/top_p, tools (by category: git/files/memory), mcp (multi-select), max_iterations; base_snapshot stores pristine state for restore and versioning via mng_agent_role_versions
- Agent execution: roles define identity/behavior (system_prompt, provider/model, temperature/top_p, tools, mcp, max_iterations); all provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) accept temperature parameter; pipeline stages can override temperature/top_p per node

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Chore commits automated after Claude CLI sessions (5cf393d1 session branch) — auto_commit_push.sh hook integration with 15+ commits since 2026-04-29
- Pipeline execution UI: Pipelines tab (◇ icon) shows full builder (graph_workflow.js) with node configuration panel; left panel lists all activated pipelines/roles; right detail panel shows pipeline flow visualization and per-stage node properties
- Execute bar unified input: output folder combobox (default = pipeline name) + searchable project docs dropdown + multi-file upload in same row; files shown as removable chips above textarea
- Dashboard restoration: Dashboard tab (◇ icon) with Mirror Data cards (commits, prompts, items, messages—total + 24h), approved vs waiting-to-approve work items/use cases, total embeddings, Pipeline Runs health tiles

_Last updated: 2026-04-30 13:20 UTC_