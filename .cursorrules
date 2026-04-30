<!-- Last updated: 2026-04-30 12:51 UTC -->
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
- Work item classification pipeline: POST /wi/{project}/classify deletes AI draft rows and runs Haiku classification on raw backlog items (mem_mrr_items) to create new categorized work items
- Role YAML as factory defaults: workspace/_templates/pipelines/roles/role_*.yaml are read-only templates seeded with ON CONFLICT DO NOTHING; mng_agent_roles DB is single source of truth at runtime; UI edits persist in DB only; base_snapshot JSONB stores pristine state
- System prompts: 3 shared canonical presets (Coding—General, Design & Planning, Review & Quality) in workspace/_templates/pipelines/system_prompts.yaml; all roles default to one preset
- Role parameters: system_prompt + system_prompt_preset, provider/model, temperature/top_p, tools (by category: git/files/memory), mcp (multi-select), max_iterations; base_snapshot stores pristine state for versioning via mng_agent_role_versions
- Agent execution: roles define identity/behavior (system_prompt, provider/model, temperature/top_p, tools, mcp, max_iterations); all provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) accept temperature parameter; pipeline stages can override temperature/top_p per node

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Continuous chore commits after Claude CLI session 5cf393d1 (16+ commits from 2026-04-29 22:46 through 2026-04-30 12:51) indicating active development cycle and auto-commit hook execution
- Pipeline execution UI with node configuration panel in right detail pane showing provider/model/temperature/max_iterations per stage
- Dashboard restoration with Mirror Data cards (commits, prompts, items, messages), approved vs waiting-to-approve work items, and Pipeline Runs health tiles
- Role activation and versioning UI wiring in Settings/Roles & Pipelines with status badges (BASED/UPDATED/EXTERNAL) and reset-to-base functionality

_Last updated: 2026-04-30 12:51 UTC_