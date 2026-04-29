# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-29 19:23 UTC

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
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML pipeline + per-node retry
- **code_parser**: tree-sitter (Python/JavaScript/TypeScript) with 180-day recency-weighted hotspot scoring
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **mcp_transport**: Stdio MCP server with 10 tools; unified REST dispatch
- **role_storage**: mng_agent_roles table with YAML seed defaults

## Key Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts via /memory POST + Haiku synthesis) → work items (mem_work_items with wi_parent_id hierarchy); ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; CLAUDE.md, CODE.md, PROJECT.md all regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Role YAML → DB sync: workspace/_templates/pipelines/roles/*.yaml are read-only factory defaults; ON CONFLICT DO NOTHING seeds only new roles on startup; mng_agent_roles DB table is single source of truth for runtime; UI edits persist in DB across restarts; Refresh button re-seeds YAML; Restore button resets individual role to YAML defaults
- Tech tag auto-detection: reads tech_stack from project_state.json instead of hardcoded regex; tags validated against actual project technologies in _build_tech_tags_block(), enabling accurate delivery_type routing to pipelines
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech tags from project_state.json tech_stack
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval
- Code.md generation: per-symbol diffs via tree-sitter with file coupling/hotspot tables; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio)
- Embeddings strategy: ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector; code.md, project_state.json, project facts, prompts, commits never embed
- MCP server: 10 tools (search_memory, get_project_state, list_work_items, get_work_item, list_commits, search_commits, due_date filters, tags, backlog, classify_wi) dispatched via REST; stdio transport, local machine, no auth required
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract; temperature, max_tokens, model configurable per role YAML
- 4-agent async DAG pipeline: PM (acceptance criteria) → Architect (implementation) → Developer (code) → Reviewer (QA); triggered only on approved items under approved use cases; executed via asyncio.gather
- Authentication: JWT (python-jose + bcrypt) with hierarchical Clients → Users → Projects; DEV_MODE toggle for passwordless local development; MCP runs with no auth (stdio-only, local)
- System prompts consolidation: 3 shared system prompt presets in system_prompts.yaml (coding_general, design_and_planning, review_and_quality); mng_agent_roles.system_prompt_preset references presets by ID; eliminates duplicate prompt definitions
- Tool and MCP management: tools grouped by category (files, git, bash, etc.) with multi-select category dropdowns per role in UI; MCPs stored in mng_mcp_servers table; MCP Catalog accessible from main left nav under Workflows section

## Recent Context (last 5 changes)

- [2026-04-29] backedn wont sto and start in relatiy. I would like to have refresh above at the role section (on top) that will upload 
- [2026-04-29] Why do I see lots of system prompts . didnt you fix that ?
- [2026-04-29] I think there is bit of a mess in SYSTEM PROMOTS. I do see quite lots of system promot whci are probable lots of old one
- [2026-04-29] I have got the following error - ReferenceError: _sysRolesResetDefaults is not defined | ctx={'stack': 'ReferenceError: 
- [2026-04-29] Can you summersie the work for today - I did worked on agent is there is anything I missed (next step is to work on pipe