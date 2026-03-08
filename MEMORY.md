# Project Memory — aicli
_Generated: 2026-03-08 03:08 UTC by aicli /memory command_

> This file is auto-generated. Reference it in CLAUDE.md so Claude reads it at session start.

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

## In Progress

- History view showing all sources (UI chat + CLI + Claude Code hooks)
- project_state.json + dev_runtime_state.json auto-maintenance
- Memory auto-summarisation at token limit

## Recent Work (last 10 exchanges)

**[2026-03-08 03:07]** `claude_cli/claude`
Q: do I need the dev_runtime_state.json ? also - now (assuming all history wokrs properly) - how can you use that to improve your ability to understand the porject better ?

**[2026-03-08 02:51]** `claude_cli/claude`
Q: It is lookls like hooks are not working now as I dont see new commits into the git repo (I am currently using the claude cli, so it is supposed to run by the hooks) also history.jsonl - I do see that 

**[2026-03-08 02:29]** `claude_cli/claude`
Q: Under workspace for each project there is _system and history folder. do I need the history folder as well? I do see that all history is stored under _system. also why there is another folder .aicli (

**[2026-03-08 02:09]** `claude_cli/claude`
Q: before I continue, I would like to optimise the code - when ever possible to use config, and classes. I do see some code that I am not sure is used. for example in core folder - I do see cost_tracker 

**[2026-03-08 01:30]** `claude_cli/claude`
Q: continue

**[2026-03-08 01:18]** `claude_cli/claude`
Q: Lets start to fix that , as this is the major goal of this project - shared memory between diffrent llm, so I can use claude cli, or my aicli (that connect to diffrent llm model) or cursor. I would li

**[2026-03-08 00:53]** `claude_cli/claude`
Q: Would using vectordb and enabling you reading the data from vectordb will make that more easy for you (or other llm) to understand the project more ? I am using you, but can use also my aicli which mu

**[2026-03-08 00:44]** `claude_cli/claude`
Q: The main goal of this project is to be able for you and other llm to share memory. I have started to do that, and I do see that all session are written to .aicli/proivder_usage by the hooks. are you u

**[2026-03-08 00:40]** `claude_cli/claude`
Q: Can you explain how you get all project info, I do see that sometime you compress the history. and start loading a new session, where do you get all the history of the project ?

**[2026-03-08 00:30]** `claude_cli/claude`
Q: It is manage to save balance, but I dont see that when I am rephresh (top right corenr). also on users tab - I dont see total balance uodated. I would except that on any refresh - all calculation will
