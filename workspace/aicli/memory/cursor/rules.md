<!-- Last updated: 2026-04-30 01:10 UTC -->
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
- Role YAML as factory defaults: workspace/_templates/pipelines/roles/role_*.yaml are read-only templates seeded with ON CONFLICT DO NOTHING; mng_agent_roles DB is single source of truth at runtime; UI edits persist in DB only; base_snapshot JSONB stores pristine state
- System prompts consolidation: 3 shared presets in workspace/_templates/pipelines/system_prompts.yaml (Coding — General, Design & Planning, Review & Quality); all roles default to canonical preset; system roles cleaned to 3 canonical entries only
- Role parameters: system_prompt + system_prompt_preset (references 3 shared presets), provider/model, temperature/top_p, tools (by category: git/files/memory), mcp (multi-select), max_iterations configured per role; base_snapshot stores pristine role state
- Agent execution: roles define identity/behavior (system_prompt, provider/model, temperature/top_p, tools, mcp, max_iterations); provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) all accept temperature parameter; pipeline stages can override temperature/top_p per node
- Pipeline execution: 4-agent async DAG (PM → Architect → Developer → Reviewer) triggered only on approved items under approved use cases; executed via asyncio.gather; GET /agent-roles/pipelines/{name} returns full config with stage role details and per-node temperature overrides

## Active Features (do not break)

Work Item UI Category Display Bug: Planner UI not displaying bug/category labels properly—only shows 'work_item' ca
Work Item Management & Metadata System: Build comprehensive work item lifecycle management with AI-generated metadata, t
MCP Configuration: Set up Model Context Protocol (MCP) configurations for multiple LLM providers an
Verify Hook-Log DB Storage After Migration: Verify that hook-log endpoint correctly stores all prompts to database after mig
Audit and clean planner_tags table schema: Review planner_tags table for redundant/unused columns: drop seq_num (always nul

## In Progress

- Post-session auto-commit: auto_commit_push.sh triggered after every Claude CLI session (5cf393d1 sessions 2026-04-29/30); commits tagged with session hash and classified automatically
- Pipeline execution UI consolidation: Pipelines tab (◆ icon) with full builder (graph_workflow.js) showing node configuration panel; left panel lists all activated pipelines/roles; right detail panel shows pipeline flow visualization and per-stage node properties
- Role activation in Settings: dual-pane dual-column view with left showing all roles/pipelines and activation checkboxes; only activated items appear in main tabs; reset-to-base and role-versioning fully wired with BASED (green), UPDATED (orange), EXTERNAL (amber) status badges
- Tool category bundles: tool selection now by category (git/files/memory) instead of individual items; MCP Catalog moved to main nav as dedicated card-based view showing all 10 MCPs with activate/deactivate/edit modals

_Last updated: 2026-04-30 01:10 UTC_