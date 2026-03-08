# aicli — AI Coding Rules
> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-08 03:08 UTC

# aicli — Shared AI Memory Platform

_Last updated: 2026-03-08_

---

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + python-jose + bcrypt
- **frontend**: Vanilla JS + Electron (no framework)
- **storage**: JSONL / JSON / CSV — no databases

## Key Decisions

- No ChromaDB / SQLite — flat files only
- Electron (not Tauri) with xterm.js terminal + Monaco editor
- Auth: REQUIRE_AUTH toggle; JWT via python-jose; bcrypt direct (not passlib)
- Engine/workspace separation: aicli/ = code, workspace/ = per-project content
- All LLM providers independent — CLI providers/ ≠ ui/backend/core/llm_clients.py
- Client sends own API keys in request headers — server never stores keys

## Recent Context (last 5 changes)

- [2026-03-08] continue
- [2026-03-08] before I continue, I would like to optimise the code - when ever possible to use config, and classes. I do see some code
- [2026-03-08] Under workspace for each project there is _system and history folder. do I need the history folder as well? I do see tha
- [2026-03-08] It is lookls like hooks are not working now as I dont see new commits into the git repo (I am currently using the claude
- [2026-03-08] do I need the dev_runtime_state.json ? also - now (assuming all history wokrs properly) - how can you use that to improv