# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-29 16:06 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-04-29_

> **How this file works**
> - Sections marked `<!-- user-managed -->` are yours to edit freely — they feed directly into CLAUDE.md.
> - Sections marked `<!-- auto-updated by /memory -->` are refreshed automatically when you run `/memory`.
>   You can still edit them; `/memory` will merge its output in without discarding your additions.
> - `## Deprecated` — list superseded decisions here; they will be hidden from CLAUDE.md key_deci

## Tech Stack

- **language_cli**: Python 3.12
- **cli_framework**: prompt_toolkit + rich
- **backend_framework**: FastAPI + uvicorn
- **backend_auth**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **database**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **database_client**: psycopg2
- **frontend_framework**: Vanilla JS + Electron + Vite
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML role + pipeline config + per-node retry
- **code_parser**: tree-sitter (Python/JavaScript/TypeScript) with 180-day recency-weighted hotspot scoring
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **mcp_transport**: Stdio MCP server with 10 tools; unified REST dispatch

## Key Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts via /memory POST + Haiku synthesis) → work items (mem_work_items with wi_parent_id hierarchy); ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; CLAUDE.md, CODE.md, PROJECT.md all regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech tags from project_state.json tech_stack (no hardcoded regex), enabling intelligent pipeline routing
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval
- Code.md generation: per-symbol diffs via tree-sitter with file coupling/hotspot tables; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio)
- Embeddings strategy: ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector; code.md, project_state.json, project facts, prompts, commits never embed
- MCP server: 10 tools (search_memory, get_project_state, list_work_items, get_work_item, list_commits, search_commits, due_date filters, tags, backlog, classify_wi) dispatched via REST; stdio transport, local machine, no auth required
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract; temperature, max_tokens, model configurable per role YAML
- 4-agent pipeline: PM (acceptance criteria) → Architect (implementation) → Developer (code) → Reviewer (QA); triggered only on approved items under approved use cases; async DAG executor via asyncio.gather
- Authentication: JWT (python-jose + bcrypt) with hierarchical Clients → Users → Projects; DEV_MODE toggle for passwordless local development; MCP runs with no auth (stdio-only, local)
- Role YAML consolidation: all roles stored in workspace/_templates/pipelines/roles/role_*.yaml with system_prompt, model, provider, temperature, max_tokens, max_iterations; no inline Python definitions
- Pipeline YAML structure: pl_*.yaml files in workspace/_templates/pipelines/ reference roles only (no embedded task_prompt); pipeline stages execute role-based agents; user-specific context in workspace/aicli/pipelines/system/
- Unified prompt storage: backend/memory/yaml_config/ stores memory command prompts (project_synthesis, conflict_detection, fact_extraction, commit_analysis, feature_detect); backend/agents/yaml_config/ stores agent/pipeline prompts (agent_react, event_tag_detection)
- Recursive CTE safety: all bounded to depth < 20 with safeguards; date cascade validation prevents re-parenting children to use cases with earlier due_dates

## Recent Context (last 5 changes)

- [2026-04-29] I mention that have added all yaml related to pipeline under the pipeline folder (and remove prompt folder) - but I do n
- [2026-04-29] I do 2 folder - documents and features under the project root. are they needed. is it possible to remove them ?
- [2026-04-29] under aiCli root folder there are 2 folders  aicli/documents and aicli/features not related to backed or  ui folders. ar
- [2026-04-29] What about cli folder - is it in used (it used to be old version running claude cli behind.. not sure it is still releva
- [2026-04-29] pelae run the /momory to update all changes