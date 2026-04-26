# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-26 23:23 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-04-26_

> **How this file works**
> - Sections marked `<!-- user-managed -->` are yours to edit freely — they feed directly into CLAUDE.md.
> - Sections marked `<!-- auto-updated by /memory -->` are refreshed automatically when you run `/memory`.
>   You can still edit them; `/memory` will merge its output in without discarding your additions.
> - Run `/memory` to regenerate CLAUDE.md, cursor rules, and all LLM prompt files from this docum

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS + Electron + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry logic
- **memory_synthesis**: Claude Haiku dual-layer + 5 output files (PROJECT.md, CODE.md, CLAUDE.md, cursorrules.md, recent_work.md) + token limits (project.yaml)
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools (broken: create_entity, sync_github_issues; working: list_work_items, run_work_item_pipeline)
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database_migrations**: PostgreSQL 15+ with m001-m079 framework; latest: m079 (user_status SMALLINT→TEXT)
- **config_management**: project.yaml (memory limits, hotspot_threshold) + memory.yaml (canonical file mapping) + YAML pipelines under pipelines/prompts

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; .ai/ and _system/ removed (replaced by cli/ structure)
- Workspace structure: cli/{claude,mcp}/ for hooks/configs; pipelines/{prompts,samples}/ for workflows; documents/ for project files; state/ for runtime state
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim) for semantic search; unified mem_mrr_* and mem_work_items tables; mem_ai_events dropped
- Memory system: /memory endpoint generates 5 files (PROJECT.md, CODE.md, CLAUDE.md, cursorrules.md, recent_work.md) from project_state.json + database; token-limited by project.yaml config
- Memory files managed by backend/memory/memory.yaml: canonical single source (not duplicated in _templates); templates in backend/memory/templates/
- Code.md structure: public symbols (classes/methods/functions) + file coupling/hotspot tables with is_latest BOOLEAN pattern; single source for all LLM context
- mem_mrr_commits_code (19 columns) with is_latest BOOLEAN: replaces need for separate code_symbols table; updated per commit; partial index optimization
- Project facts deprecated: mem_ai_project_facts no longer auto-populated during /memory; facts extracted inline from memory synthesis; conflict_detection merged into mem_project_state.yaml
- Work Items + Use Cases: items tab shows pending AI-classified items; use cases tab displays hierarchy with due dates, completion validation, auto-markdown generation
- Drag-and-drop parent-child/merge: unconditional e.preventDefault() + document.elementFromPoint() target detection (same implementation for both Work Items and Use Cases)
- Undo as persistent toolbar button: stores reverse API call closure capturing original parent_id before link modification; works for both linking and partial merge
- JWT authentication: python-jose + bcrypt with DEV_MODE toggle; hierarchical Clients → Users → Projects
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract
- Backend prompts: all LLM prompts migrated to YAML files under backend/memory/mem_*.yaml (named by table domain); templates in backend/memory/templates/
- Electron desktop UI: Vanilla JS with xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development; hardcoded localhost removed

## Recent Context (last 5 changes)

- [2026-04-26] memroy.yaml look like there are duplicate . this file suppose to use as main mapping for copy file and all managmenet do
- [2026-04-26] Let me understand again , now after all the refactor - how PROJECT.md, CODE.md , CLOUADE.md and project_fact are generrt
- [2026-04-26] the trade of is also spending more tokens as one every prompt - /memory will run ? there was config param in the aicli.y
- [2026-04-26] to create new work items - is it only by using /wi or there is something else ?
- [2026-04-26] what is create_entity used for ? was it for a use case ?