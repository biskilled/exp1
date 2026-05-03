# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-05-03 20:36 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-05-03_

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
- **frontend_framework**: Vanilla JS (Vite) + Electron
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) with per-node temperature/top_p/provider/model/max_iterations overrides
- **code_parser**: tree-sitter (Python/JavaScript/TypeScript) with 180-day recency-weighted hotspot scoring
- **mcp_transport**: Stdio MCP server with 10 tools; unified REST dispatch
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **pipeline_config**: YAML files (8 pipelines in workspace/_templates/pipelines/)

## Key Decisions

- Memory 3-layer architecture: raw captures (mem_mrr_* tables) → structured artifacts (mem_ai_project_facts) → approved work items (mem_work_items); ONLY approved items (UC/FE/BU/TA prefix) embed to pgvector; re-embedding on item change automatic via update() → _embed_work_item()
- Single source of truth: /memory POST endpoint is ONLY writer to project_state.json via get_project_context() + Haiku synthesis; CLAUDE.md, CODE.md, PROJECT.md all regenerated from single JSON state
- Work item hierarchy: unified mem_work_items with wi_type (use_case/feature/bug/task/requirement), user_status TEXT (open/pending/in-progress/review/done), wi_parent_id linking children to use_case parents; wi_id progression: AI#### (draft) → UC/FE/BU/TA#### (approved)
- Role YAML as factory defaults: workspace/_templates/pipelines/roles/*.yaml are read-only templates seeded with ON CONFLICT DO NOTHING on backend startup; mng_agent_roles DB is single source of truth at runtime; base_snapshot JSONB stores pristine state
- System prompts: 3 shared canonical presets (Coding—General, Design & Planning, Review & Quality) in workspace/_templates/pipelines/system_prompts.yaml; all roles default to one preset; system_roles table contains only 3 canonical entries
- Agent execution: roles define identity/behavior (system_prompt, provider/model, temperature/top_p, tools, mcp, max_iterations); pipeline nodes can override provider/model/temperature/top_p/max_iterations per stage; nodes default to role values when not overridden
- Pipeline execution: 4-agent async DAG triggered on approved items; executed via asyncio.gather; max_iterations mandatory per node; per-node checkboxes: max_retry, stateless, continue-on-fail, approval-gate; mode_use_case and mode_item flags control visibility/executability; pipeline reports save to workspace/{project}/documents/pipelines/{pipeline_name}/{ddmmyy_HHMM}_{uc_slug}.md
- Architect role mandatory research sequence: search_memory → get_project_facts → search_features → list_dir → read_file (in order); outputs file_analysis with current_state and required_changes per file; acts as information gatherer for downstream developer
- Code Reviewer role outputs structured_out JSON with per-item score (0-5) and reasoning; verdict zone displays items_reviewed table after pipeline completion with scores and brief acceptance reasoning
- Pipeline & role activation: Settings → Roles & Pipelines dual-pane shows all roles/pipelines with activation checkboxes; only activated items appear in main tabs and are executable; pipeline activation requires all constituent roles to be activated
- Tool category bundles: tool selection by category (git/files/memory) instead of individual items; categories show tool count; multi-select in role editor
- Execute bar unified input: output folder combobox + searchable project docs dropdown + multi-file upload; files shown as removable chips; supports multiple document and file selections; per-role and per-pipeline execution modes
- Pipeline execution entry points: (1) Pipelines tab with node diagram and exec bar, (2) /pipeline [name] slash command in Chat, (3) /role [name] slash command for direct role execution, (4) Use Cases section with approval gating; each mode (use_case/item) independently togglable
- Delivery type and tech tags: each work item gets delivery_type (web_ui/backend_api/infra/database) and auto-detected tech_tags from project_state.json tech_stack
- Loop detection: agent._detect_loop now requires identical tool calls (same name + args) 3× in a row to trigger, not just same tool name; fixes false positives when iterating over multiple work items with search_memory

## Recent Context (last 5 changes)

- [2026-05-02] it is not working . I dont see score by item
- [2026-05-03] I still reciave the same response - Thought: No memory found for any of the work items. Let me look at the project struc
- [2026-05-03] Still did not able to update the pipleine - that was the message in the backend - "PATCH /graph/null/nodes/developer HTT
- [2026-05-03] Can you also recheck that the previous promts was fixed - role are working as exptected on use case. Also - it is still 
- [2026-05-03] Ok. I do see now approval/reject - but there is an error - 2026-05-03 21:34:48 | ERROR    | routers.route_logs          