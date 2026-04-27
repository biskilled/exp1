# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-27 13:30 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-04-27_

> **How this file works**
> - Sections marked `<!-- user-managed -->` are yours to edit freely — they feed directly into CLAUDE.md.
> - Sections marked `<!-- auto-updated by /memory -->` are refreshed automatically when you run `/memory`.
>   You can still edit them; `/memory` will merge its output in without discarding your additions.
> - `## Deprecated` — list superseded decisions here; they will be hidden from CLAUDE.md key_deci

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS + Electron + Vite
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js
- **storage**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry
- **memory_synthesis**: Claude Haiku (project_state.json) + 5 output files (CLAUDE.md, CODE.md, PROJECT.md, cursor/rules, api/) with token limits in project.yaml
- **chunking**: Smart: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 14 tools rewired to REST endpoints
- **deployment_backend**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database_migrations**: PostgreSQL with m001-m080 framework (m080 adds 4-agent pipeline columns)

## Key Decisions

- Workspace structure: aicli/cli/{claude,mcp}/ for hooks/configs; aicli/pipelines/{prompts,samples}/ for workflows; aicli/documents/ for project files; aicli/state/ for runtime state.
- Memory files (PROJECT.md, CODE.md, CLAUDE.md, cursor/rules, api/) generated ONLY by POST /memory endpoint from project_state.json + database queries; token-limited by project.yaml config. Not copied to projects.
- backend/memory/memory.yaml is canonical single source for file mapping; templates in backend/memory/templates/; memory.yaml itself is NOT copied to projects (internal logic only).
- code.md structure: public symbols (classes/methods/functions) with file coupling/hotspot tables; generated from mem_mrr_commits_code per commit + refreshed post-commit via sync_code_structure().
- mem_mrr_commits_code (19 columns) with is_latest BOOLEAN: per-symbol diffs tracked; replaces separate symbols table; updated per commit with depth<20 bounded recursion.
- Work Items unified hierarchy: wi_parent_id links features/bugs/tasks to use_case parents; approved items trigger 4-agent pipeline (PM→Architect→Developer→Reviewer) with acceptance_criteria, implementation_plan, pipeline_status, pipeline_run_id columns.
- Approved work items ONLY are embedded (pgvector, 1536-dim, text-embedding-3-small); code.md, project_state.json, project facts, and prompts are NOT embedded; /search/semantic searches work_items only.
- JWT authentication: python-jose + bcrypt with DEV_MODE toggle; hierarchical Clients→Users→Projects.
- LLM provider adapters: Claude/OpenAI/DeepSeek/Gemini/Grok as independent modules in agents/providers/ with send(prompt, system) → str contract.
- All backend LLM prompts in YAML files under backend/memory/prompts/: command_memory.yaml (/memory), command_work_items.yaml (/wi classify), event_commit.yaml (post-commit), event_hook_context.yaml (hook synthesis), misc.yaml (inline prompts).
- Commit-sourced work items: regex 'fixes BU0012'/'closes FE0001' in commit message auto-closes items with score_status=5, score_importance=5; user must approve to update user_status to 'done'.
- project_state.json generated ONLY by POST /memory endpoint; drives all 5 memory file outputs; no other code path writes it.
- MCP tools rewired to REST: create_entity→POST /wi/{project}, list_work_items→GET /wi/{project}, sync_github_issues→PATCH /wi/{project}, get_file_history→GET /memory/{project}/file-history.
- Memory files convergence: both /memory POST (get_project_context) and commit/work-item triggers (render_root_claude_md) use identical DB queries for in_progress items and acceptance_criteria display.
- Work item embedding refresh: re-embedding occurs only on name/summary/description edits for approved items; NOT triggered for unapproved drafts.

## Recent Context (last 5 changes)

- [2026-04-27] ok. can you fix aall remainig issues as it look small onnes
- [2026-04-27] ok. no need please fix that all
- [2026-04-27] I would like to run the last prompt again -  This time please go over on all latest changes (in the last 10-15 prompts) 
- [2026-04-27] ok. fix that
- [2026-04-27] I would like to run the last prompt again -  This time please go over on all latest changes (in the last 10-15 prompts) 