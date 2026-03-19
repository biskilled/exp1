# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-19 14:25 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-14 | Version 2.2.0_

---

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js (embedded terminal) + Monaco editor + Cytoscape.js (graph flows) + cytoscape-dagre
- **storage_primary**: JSONL (history.jsonl with rotation to history_YYMMDDHHSS.jsonl, commit_log.jsonl), JSON, CSV
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK nesting), agent_roles, system_roles
- **authentication**: JWT (python-jose) + bcrypt + DEV_MODE toggle; 3 roles: admin/paid/free
- **llm_providers**: Claude (Haiku for synthesis), OpenAI, DeepSeek, Gemini, Grok (independent adapters)
- **workflow_engine**: Node-based async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; inline modal for pipeline creation
- **memory_synthesis**: Claude Haiku for LLM-synthesized /memory; incremental since last_memory_run; dual-layer (raw JSONL → interaction_tags → 5 output files)
- **chunking**: Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- **mcp**: Standalone stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); local: bash ui/start.sh; desktop: Electron-builder
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values (parent_id FK nesting), agent_roles, system_roles
- **config_management**: config.py with externalized backend_url, haiku_model, db_pool_max, MCP settings

## Key Decisions

- Engine/workspace separation: aicli/ = code only, workspace/ = per-project content, _system/ = project state
- Flat file primary (JSONL with rotation on /memory); PostgreSQL 15+ with pgvector for semantic search; per-project DB tables indexed on phase/feature/session_id
- Electron UI with xterm.js + Monaco editor; Vanilla JS frontend (no framework, no bundler); Vite dev server for local dev
- JWT auth via python-jose + bcrypt; DEV_MODE toggle; 3 roles: admin/paid/free; login as first-level hierarchy
- All LLM providers as independent adapters (Claude, OpenAI, DeepSeek, Gemini, Grok); server holds API keys; client sends NO keys
- Nested tags via parent_id FK: unlimited depth with tree UI; tags synced across Chat/History/Commits on save
- History rotation on /memory: configurable max_rows (default 500), creates timestamped archive (history_YYMMDDHHSS.jsonl)
- Dual-layer memory synthesis: raw JSONL → interaction_tags → 5 output files (CLAUDE.md, MEMORY.md, IDE rules, copilot rules, aicli rules)
- Smart chunking: summary + per-class/function (Python/JS/TS) + per-section (MD) + per-file (diff)
- Load-once-on-access pattern: eliminate redundant SQL; tag cache synced on explicit save
- MCP server (stdio): 12+ tools for project state, memory search, entity management, feature status tracking
- Multi-agent workflows: async DAG executor via asyncio.gather with loop-back + max_iterations cap; Cytoscape.js visualization
- Port binding safety: freePort() kills stale uvicorn; Electron cleanup via process.exit()
- Backend startup retry logic: handles empty project list on first load; prevents false 'project not found' errors
- Document folder abstraction: prompt-driven workflows instead of direct IO; role-based access (PM writes, Dev reads) via memory queries

## Recent Context (last 5 changes)

- [2026-03-19] can you update /memory as well to make sure this feature is stored
- [2026-03-19] UI improvmenet - in pipeline for each node - can you add more properties (max retry, stateless, continue on fail - so us
- [2026-03-19] UI improvement - new nodes in Pipeline we need to show more details at the node (same as it was) like model, input/outpu
- [2026-03-19] I would like to remove the IO. is it possible just to mainatin that using prompt. for example how doas prject manager wi
- [2026-03-19] I do see that when I run pipeline from work_item it is starting to run a pipeline . but I do not see any status/progress