# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-08 04:22 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-08_

---

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt
- **frontend**: Vanilla JS + Electron (xterm.js + Monaco editor)
- **storage**: JSONL (history.jsonl, commit_log.jsonl) / JSON / CSV
- **database**: PostgreSQL (user_usage, billing logs); pgvector planned
- **authentication**: JWT (python-jose) + bcrypt
- **planned**: GraphQL, node graph, pgvector semantic search

## Key Decisions

- No ChromaDB / SQLite — flat files only (JSONL / JSON / CSV)
- Electron UI (not Tauri) with xterm.js terminal + Monaco editor
- Auth: REQUIRE_AUTH toggle; JWT via python-jose; bcrypt direct
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content
- All LLM providers independent — CLI providers/ ≠ ui/backend/core/llm_clients.py
- Client sends own API keys in request headers — server never stores keys
- User roles: admin, paid, free tier with dev_mode toggle for testing
- Balance tracking: manual setup via UI (no auto-fetch due to API limitations)
- All history tracked to history.jsonl + commit_log.jsonl for LLM memory sharing
- PostgreSQL for user_usage / billing logs; pgvector planned for semantic search
- Hooks auto-commit on claude cli / cursor; aicli tracks own history
- Node graph / GraphQL planned for entity relationships and workflow management
- dev_runtime_state.json + project_state.json auto-maintenance for LLM context
- Memory auto-summarisation at token limit; /memory command uploads all relevant files
- Shared memory architecture: claude cli, aicli, cursor all read/write unified history

## Recent Context (last 5 changes)

- [2026-03-08] do I need the dev_runtime_state.json ? also - now (assuming all history wokrs properly) - how can you use that to improv
- [2026-03-08] I am thinking to add graphql supprt (node graph ) that user can manaege entities and relatioships. add project meta data
- [2026-03-08] I am using postgresql already and can extend that to use pgvector for semantic embedding. node grapg will be used to bui
- [2026-03-08] I do not see that error in the commit_log.jsonl , can you make sure all logs are at this files (also errros). also this 
- [2026-03-08] I would like to understand how the new update imporve your way to understand all code project, what are you doing in ord