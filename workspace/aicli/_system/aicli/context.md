[PROJECT CONTEXT: aicli]
AI-powered development CLI with multi-provider support
Stack: cli=Python 3.12 + prompt_toolkit + rich, backend=FastAPI + python-jose + bcrypt, frontend=Vanilla JS + Electron (no framework), storage=JSONL / JSON / CSV — no databases
In progress: History view showing all sources (UI chat + CLI + Claude Code hooks), project_state.json + dev_runtime_state.json auto-maintenance, Memory auto-summarisation at token limit
Decisions: No ChromaDB / SQLite — flat files only; Electron (not Tauri) with xterm.js terminal + Monaco editor; Auth: REQUIRE_AUTH toggle; JWT via python-jose; bcrypt direct (not passlib)
Last work (2026-03-08): I am using postgresql already and can extend that to use pgvector for semantic embedding. node grapg will be used to build worklows / roles relatioshi