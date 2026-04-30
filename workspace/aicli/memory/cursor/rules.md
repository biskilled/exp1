# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-30 15:20 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-04-30_

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
- **workflow_engine**: Async DAG executor (asyncio.gather) with per-node temperature/top_p/provider/model/max_iterations overrides
- **code_parser**: tree-sitter (Python/JavaScript/TypeScript) with 180-day recency-weighted hotspot scoring
- **role_config**: YAML factory defaults (workspace/_templates/pipelines/roles/role_*.yaml) seeded ON CONFLICT DO NOTHING; mng_agent_roles DB is source-of-truth at runtime
- **system_prompts**: 3 shared canonical presets in workspace/_templates/pipelines/system_prompts.yaml (Coding—General, Design & Planning, Review & Quality)
- **mcp_transport**: Stdio MCP server with 10 MCPs; unified REST dispatch
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)

## Key Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts via /memory POST + Haiku synthesis) → approved work items (mem_work_items with wi_parent_id hierarchy); ONLY approved work items (UC/FE/BU/TA prefix) embed to pgvector
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; CLAUDE.md, CODE.md, PROJECT.md all regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Role YAML as factory defaults: workspace/_templates/pipelines/roles/*.yaml are read-only templates seeded with ON CONFLICT DO NOTHING on backend startup; mng_agent_roles DB is single source of truth at runtime; UI edits persist in DB only; base_snapshot JSONB stores pristine state for versioning and restore-to-base functionality
- System prompts: 3 shared canonical presets (Coding—General, Design & Planning, Review & Quality) in workspace/_templates/pipelines/system_prompts.yaml; all roles default to one preset; system_roles table cleaned to 3 canonical entries only
- Role parameters: system_prompt + system_prompt_preset, provider/model/temperature/top_p, tools (by category: git/files/memory), mcp (multi-select), max_iterations; base_snapshot stores pristine state for restore and versioning; all provider adapters accept temperature parameter
- Agent execution: roles define identity/behavior (system_prompt, provider/model, temperature/top_p, tools, mcp, max_iterations); pipeline nodes can override provider/model/temperature/top_p/max_iterations per stage; nodes default to role values when not overridden
- Pipeline execution: 4-agent async DAG (PM → Architect → Developer → Reviewer) triggered only on approved items under approved use cases; executed via asyncio.gather; max_iterations mandatory per node; GET /agent-roles/pipelines/{name} returns full config; POST /agents/pipeline-runs starts async execution
- Pipeline & role activation: Settings → Roles & Pipelines dual-pane shows all roles/pipelines with activation checkboxes; only activated items appear in main tabs and are executable; pipeline can only activate if all constituent roles are activated
- Tool category bundles: tool selection by category (git/files/memory) instead of individual items; categories show tool count; multi-select dropdown in role editor; MCP Catalog in main nav as dedicated card-based view showing all 10 MCPs
- Role library direct execution: Roles can be executed directly (not just within pipelines) via Role Library view; same exec bar interface (output folder, file upload, document search, prompt input) as pipeline execution; supports both file upload and document reference; history panel shows execution logs below
- Execute bar unified input: output folder combobox (default = pipeline/role name) + searchable project docs dropdown with multi-select + multi-file upload in same row; files shown as removable chips above textarea; integrated into both Pipelines tab (DAG builder) and Roles library direct execution
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech_tags from project_state.json tech_stack
- Auto-closure via commit regex: patterns ('fixes BU0012', 'closes FE0001') in commit messages auto-set score_status=5 and score_importance=5 for user approval
- Code.md generation: per-symbol diffs via tree-sitter with file coupling/hotspot tables; hotspot scores use 180-day half-life recency weighting EXP(-0.693 × age_ratio)

## Recent Context (last 5 changes)

- [2026-04-30] Why can I do the same when using role libery. I  would like to start using role (the  same way) also  on role (instead o
- [2026-04-30] the dynamic drop box (FILE &   Document) not  looks good.  it is on most  of the row. alway  shoew with  all open items.
- [2026-04-30] Not the dropbox is  not working. cannot see or choose any  files from documents. Also when I  click on a  role  - I do s
- [2026-04-30] DDropbox look better. just hight  and shape not fully align to the left text box (OUTPUT FOLDER) andd right (+files)  - 
- [2026-04-30] I am looking at my chat history - it used to be goupeed by session. I do see all prmotps and llm response in history. bu