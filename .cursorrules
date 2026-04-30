<!-- Last updated: 2026-04-30 00:32 UTC -->
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
- Work item classification pipeline: POST /wi/{project}/classify deletes AI draft rows, runs AI classifier on backlog items, stores results with scores and evidence, user reviews and approves to finalize classification
- Role YAML factory defaults: workspace/_templates/pipelines/roles/role_*.yaml are read-only templates; ON CONFLICT DO NOTHING seeds only new roles on startup; mng_agent_roles DB is single source of truth at runtime; UI edits persist in DB only; base_snapshot JSONB stores pristine state
- System prompts consolidation: 3 shared presets in workspace/_templates/pipelines/system_prompts.yaml (Coding — General, Design & Planning, Review & Quality); all roles default to canonical preset
- Role parameters: system_prompt + system_prompt_preset (references 3 shared presets), provider/model, tools (by category: git/files/memory), mcp (multi-select), max_iterations, temperature, top_p configured per role; base_snapshot stores pristine role state for restore
- Agent execution: roles define identity/behavior (system_prompt, provider/model, tools, mcp, max_iterations, temperature, top_p); provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) all accept temperature parameter; pipeline stages can override temperature/top_p at execution time

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Repeated auto-commit patterns after Claude CLI sessions across 5cf393d1 and 45ca1683 sessions indicating chore/maintenance consolidation workflow
- Pipeline execution framework: GET /agent-roles/pipelines/{name} returns full pipeline config with stage role details; POST /agents/pipeline-runs starts async DAG execution
- Role base snapshot and versioning: POST /agent-roles/{id}/set-base snapshots current role config; POST /agent-roles/{id}/restore-base restores to snapshot; mng_agent_role_versions table tracks historical edits
- Provider model temperature injection: all 5 provider adapters accept temperature parameter; role YAML files store temperature config; pipeline stages override per-node

_Last updated: 2026-04-30 00:32 UTC_