# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-26 23:05 UTC

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
- **memory_synthesis**: Claude Haiku dual-layer + 5 output files + token limits (project.yaml)
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database**: PostgreSQL 15+ with pgvector + m001-m079 migration framework
- **config_management**: project.yaml (memory limits, memory.yaml (canonical file mapping), YAML pipelines

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; .ai/ removed (stale); _system/ removed (replaced by cli/ structure)
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_mrr_* and mem_work_items tables
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users → Projects
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules in agents/providers/ with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Memory synthesis: Claude Haiku dual-layer generating 5 output files (PROJECT.md, CODE.md, CLAUDE.md, cursorrules.md, recent_work.md) via /memory endpoint
- Workspace structure: cli/{claude,mcp}/ for hooks/configs; pipelines/{prompts,samples}/ for workflows; documents/ for project files; state/ for runtime state
- Memory files managed by memory.yaml: canonical single source in backend/memory/ (not duplicated); templates in backend/memory/templates/
- Token-limited memory files: project.yaml config (claude_md_max_tokens, cursorrules_max_tokens, etc.) controls /memory output sizing
- Work Items vs Use Cases: items tab shows pending AI-classified items; use cases tab displays hierarchy with due dates, completion validation, auto-markdown
- Drag-and-drop parent-child/merge in Work Items and Use Cases via unconditional e.preventDefault() + document.elementFromPoint() target detection
- Undo button as persistent toolbar button (not popup): stores reverse API call closure capturing original parent_id before link
- Code.md structure: public symbols (classes/methods/functions) + file coupling/hotspot tables; single source for all LLM context (Claude/Cursor)
- mem_mrr_commits_code (19 columns) with is_latest BOOLEAN: replaces need for mem_code_symbols; updated per commit; partial index optimization
- Project facts deprecated: mem_ai_project_facts no longer auto-populated; facts extracted inline from memory synthesis; conflict_detection merged into mem_project_state.yaml

## Recent Context (last 5 changes)

- [2026-04-26] project fact was good summery of fact on the project (language, descision I have asked .. and suppose to be part of proj
- [2026-04-26] yes
- [2026-04-26] I would like to make more meaningfull name to the prompts files. for example commit - would be mem_mrr_coomits. or memor
- [2026-04-26] memroy.yaml look like there are duplicate . this file suppose to use as main mapping for copy file and all managmenet do
- [2026-04-26] Let me understand again , now after all the refactor - how PROJECT.md, CODE.md , CLOUADE.md and project_fact are generrt