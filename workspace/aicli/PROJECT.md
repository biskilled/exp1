# aicli — Project Knowledge Base

## Use Case

**Who**: Solo developer / small team building a Python project with AI assistance.
**What**: An AI-powered development CLI that lets you prompt Claude, OpenAI, DeepSeek, Gemini, or Grok from your terminal, with persistent memory, workflow automation, and a desktop Electron UI.
**Why**: Replace the cycle of copy-pasting code into chat UIs. Keep AI context close to the codebase, automate commit/push, and run multi-step AI workflows (design → implement → review) without leaving the terminal.

---

## Architecture

### Engine / Workspace Separation

```
aicli/          ← ENGINE (code only — providers, core, runner, CLI, Electron UI)
workspace/      ← CONTENT (workflows, prompts, history, PROJECT.md per project)
```

The engine knows nothing about specific prompts. Each project gets its own workspace folder (`workspace/<project>/`) containing all AI context. Templates live in `workspace/_templates/`.

### Core CLI Modules

| Module | Purpose |
|--------|---------|
| `cli.py` | Interactive REPL (prompt_toolkit + rich), all slash commands |
| `providers/base.py` | BaseProvider with retry/fallback logic |
| `providers/claude_agent.py` | Anthropic SDK: streaming, tool use, MCP |
| `providers/openai_agent.py` | OpenAI chat completions |
| `providers/deepseek_agent.py` | DeepSeek via OpenAI-compat API |
| `providers/gemini_agent.py` | Google Gemini via google-generativeai |
| `providers/grok_agent.py` | xAI Grok via OpenAI-compat API |
| `workflows/runner.py` | YAML workflow executor: file injection, retry, cost tracking |
| `core/context_builder.py` | Collects+formats files for LLM injection |
| `core/cost_tracker.py` | Token+cost per step, Rich table, JSONL log |
| `core/memory.py` | JSONL memory store: keyword/tag/feature search |
| `core/conversation.py` | JSON session persistence, feature+tag tracking |
| `core/git_supervisor.py` | Auto-commit+push via lifecycle hooks |
| `core/project_docs.py` | Reads/writes workspace PROJECT.md |
| `core/hooks.py` | Shell hook runner (pre_prompt, post_commit, etc.) |
| `core/analytics.py` | Usage stats from conversation data |
| `prompts/loader.py` | Assembles CLAUDE.md from workspace prompt modules |

### UI (Electron + FastAPI)

```
ui/
├── electron/           ← Electron shell (BrowserWindow, IPC)
│   ├── main.js         ← spawn backend, open window
│   ├── preload.js      ← window.electronAPI: readFile, writeFile, openDialog
│   └── terminal.js     ← xterm.js + node-pty: embedded Python CLI
├── frontend/           ← Vanilla JS (no framework, no bundler deps)
│   ├── main.js         ← shell: titlebar + collapsible sidebar + content area
│   ├── stores/
│   │   └── state.js    ← central reactive state (auth, nav, project, settings)
│   ├── utils/
│   │   ├── api.js      ← all HTTP calls to FastAPI backend
│   │   ├── markdown.js ← renderMd(), highlightYaml(), validateYaml() (no npm)
│   │   └── toast.js    ← toast notifications
│   └── views/
│       ├── home.js     ← project picker / recent projects
│       ├── chat.js     ← chat + SSE streaming + / commands popup
│       ├── summary.js  ← PROJECT.md markdown viewer + edit/preview toggle
│       ├── prompts.js  ← folder tree + textarea editor (save-disabled-until-changed)
│       ├── code.js     ← code folder tree + read-only file viewer
│       ├── workflow.js ← YAML editor + syntax highlight + node flow diagram
│       ├── history.js  ← chat/commits/runs/evals tabs (HistoryView class)
│       ├── settings.js ← global settings: API keys, backend URL, models
│       ├── explorer.js ← Monaco editor + file tree + prompt compare
│       └── login.js    ← JWT login/register UI
└── backend/            ← FastAPI (localhost:8000)
    ├── main.py
    ├── config.py       ← settings: workspace_dir, require_auth, secret_key
    ├── routers/
    │   ├── auth.py         ← POST /auth/register, POST /auth/login, GET /auth/me
    │   ├── chat.py         ← SSE streaming; reads per-request API key headers
    │   ├── history.py      ← GET /history/{chat,commits,runs,evals}
    │   ├── workflows.py    ← GET/PUT /workflows/{name}?project=
    │   ├── prompts.py      ← list/read/write workspace prompt files
    │   ├── files.py        ← GET /files/code (tree), GET /files/read (content)
    │   ├── projects.py     ← list/create/switch workspace projects
    │   └── config_sync.py  ← stub: future remote sync
    ├── models/
    │   └── user.py         ← file store at DATA_DIR/users.json; first = admin
    ├── core/
    │   ├── auth.py         ← JWT (python-jose) + bcrypt (direct, not passlib)
    │   └── llm_clients.py  ← per-call api_key= param, falls back to settings
    └── storage/sessions.py ← JSON session persistence
```

### UI Layout (as of 2026-02-25)

```
#titlebar  — position:fixed; top:0; left:0; right:0; height:40px; z-index:200
             backdrop-filter:blur(12px); -webkit-app-region: drag
#sidebar   — position:fixed; top:0; left:0; bottom:0; width:220px (or 48px); z-index:100
             padding-top:40px; transition: width 0.2s ease
#content   — position:fixed; top:0; left:220px; right:0; bottom:0; z-index:1
             padding-top:40px; transition: left 0.2s ease
```

- Sidebar collapses to 48px icon strip (VS Code style); CSS `body.sidebar-collapsed`
- Hover tooltips on collapsed items via CSS `::after { content: attr(data-label) }`
- Sidebar state persisted in `localStorage('aicli_sidebar_open')`

### Auth Architecture

- `REQUIRE_AUTH=false` (local dev) — no login gate
- `REQUIRE_AUTH=true` (Railway/cloud) — JWT required on all routes
- Client sends own API keys per request in headers (`X-Anthropic-Key`, etc.)
- Server never stores keys; only tracks token counts + cost
- JWT stored in `localStorage`; first registered user = admin

---

## Features

### Implemented [x]

- [x] Interactive REPL with prompt_toolkit (history, autocomplete, Ctrl+C safe)
- [x] Claude provider: Anthropic SDK, streaming, tool use (bash/file ops), MCP
- [x] OpenAI provider: chat completions, streaming
- [x] DeepSeek provider: OpenAI-compat API, streaming
- [x] Gemini provider: google-generativeai SDK, streaming
- [x] Grok provider: xAI OpenAI-compat API, streaming
- [x] BaseProvider: retry (3 attempts, 1s/3s/10s backoff), provider fallback
- [x] JSONL memory store: keyword/tag/feature search, no ML deps
- [x] JSON session persistence (conversation history, tags, features, commits)
- [x] Git supervisor: auto-commit+push, change detection
- [x] Shell lifecycle hooks (pre_prompt, post_prompt, post_commit, post_push)
- [x] PROJECT.md living doc: /docs generate, /docs todo, /docs done
- [x] /tag, /tags, /search-tag, /feature tagging system
- [x] /analytics: usage stats, cost estimate
- [x] /history: last 20 commits with feature/tag columns
- [x] Workflow runner: YAML executor, file injection, retry, cost tracking
- [x] CostTracker: per-step token+cost, Rich table, JSONL log
- [x] ContextBuilder: file injection, folder glob, auto-recent, template vars
- [x] Workspace/engine separation: workspace/_templates/, workspace/aicli/
- [x] /switch <provider>: switch LLM with autocomplete
- [x] /project new/list/switch: project management from templates
- [x] /compare <prompt.md>: multi-LLM prompt comparison, winner logged
- [x] FastAPI backend: chat SSE, history, workflows, prompts, files, projects
- [x] Electron UI: BrowserWindow, IPC, embedded xterm.js terminal
- [x] Auth: JWT login/register (bcrypt direct, python-jose), REQUIRE_AUTH toggle
- [x] Railway deployment: Dockerfile + railway.toml; SECRET_KEY+REQUIRE_AUTH as env vars
- [x] Electron-builder packaging: Mac (dmg arm64+x64), Windows (nsis x64), Linux (AppImage+deb)
- [x] UI redesign: fixed overlay layout (titlebar z-200, sidebar z-100, content)
- [x] Collapsible icon-strip sidebar (220px → 48px) with smooth CSS transition
- [x] Sidebar tooltip-on-hover when collapsed (pure CSS ::after, no JS)
- [x] Summary view: PROJECT.md rendered as markdown, edit/preview toggle
- [x] Prompts view: recursive folder tree + textarea editor, save-disabled-until-changed
- [x] Code view: code folder tree + read-only file viewer, Change Folder button
- [x] Chat commands popup: / triggers autocomplete with ↑↓ nav + Tab/Enter complete
- [x] Workflow YAML editor: split-pane (edit textarea + syntax-highlighted preview + node flow)
- [x] utils/markdown.js: renderMd(), highlightYaml(), validateYaml() — zero npm packages
- [x] History view: tabs for chat/commits/runs/evals; uses state.settings.backend_url + project param
- [x] Claude Code hooks: UserPromptSubmit → log_user_prompt.sh → .aicli/prompt_log.jsonl
- [x] History pipeline: UI chat + CLI history + Claude Code hook log all merged in /history/chat
- [x] project_state.json: static project metadata (tech stack, decisions, features, deployment)
- [x] dev_runtime_state.json: auto-updated after each exchange (session_count, last_provider, etc.)

### In Progress [ ]

- [ ] Memory auto-summarisation at token limit (compress to summary.md)
- [ ] Workflow stop_condition with loop-back tested end-to-end
- [ ] UI prompt compare split-pane view (explorer.js)
- [ ] /deploy <aws|railway> implementation (currently stub)
- [ ] Remote config sync (config_sync.py currently stub)

---

## TODO / Next Steps

1. [ ] Add memory summarisation: when history > 50k tokens, compress to summary.md
2. [ ] Test build_feature workflow end-to-end with DeepSeek review step
3. [ ] Implement /deploy stub for Railway (one-command deploy)
4. [ ] Add prompt compare split-pane in explorer.js (uses /compare CLI command)
5. [ ] Add streaming token count to CostTracker (use Anthropic token counting API)
6. [ ] Write integration tests for WorkflowRunner
7. [ ] Verify all backend endpoints respond correctly when REQUIRE_AUTH=true
8. [ ] Add per-project settings view (code_dir, default_provider, workflow params)

---

## Key Patterns

### Save-disabled-until-changed
All editors (summary.js, prompts.js, workflow.js) use the same pattern:
```js
saveBtn.disabled = true;
saveBtn.style.opacity = '0.4';
textarea.addEventListener('input', () => {
  const changed = textarea.value !== _original;
  saveBtn.disabled = !changed;
  saveBtn.style.opacity = changed ? '1' : '0.4';
});
```

### Claude Code Hooks (`.claude/settings.local.json`)
```json
{
  "hooks": {
    "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": ".aicli/scripts/log_user_prompt.sh" }] }]
  }
}
```
Hook script reads JSON from stdin, appends to `.aicli/prompt_log.jsonl`.

### Workflow YAML Structure
```yaml
name: my_workflow
description: "What this workflow does"
max_iterations: 1
steps:
  - name: design
    provider: claude
    prompt: prompts/01_design.md
    inject_files: [PROJECT.md]
  - name: review
    provider: deepseek
    prompt: prompts/02_review.md
    inject_previous_output: true
```

### API Key Flow (Cloud Mode)
- UI reads keys from localStorage
- Each `api.js` call sets `X-Anthropic-Key` / `X-OpenAI-Key` / etc. headers
- Backend `chat.py` reads headers, passes `api_key=` to llm_clients.py
- Backend only stores token counts + cost in usage log; never the key itself

---

## Recent Changes

| Date | Change |
|------|--------|
| 2026-02-23 | Engine/workspace separation: aicli/ = engine, workspace/ = content |
| 2026-02-23 | Added providers/base.py: retry, backoff, fallback |
| 2026-02-23 | Added DeepSeek, Gemini, Grok providers |
| 2026-02-23 | Added core/cost_tracker.py: per-step cost, Rich table, JSONL |
| 2026-02-23 | Added core/context_builder.py: file injection, template vars, auto |
| 2026-02-23 | Created workflows/runner.py: full YAML executor, replaces engine.py |
| 2026-02-23 | Added workspace/_templates/: blank, python_api, quant_notebook, ui_app |
| 2026-02-23 | Added /switch, /project, /compare CLI commands |
| 2026-02-23 | Electron UI: main.js, preload.js, terminal.js (xterm + node-pty) |
| 2026-02-23 | FastAPI backend: new routers for workflows, prompts, files, projects |
| 2026-02-23 | Auth: JWT + bcrypt, REQUIRE_AUTH toggle, user file store |
| 2026-02-23 | Railway: Dockerfile + railway.toml; Electron-builder: Mac/Win/Linux |
| 2026-02-25 | Full UI redesign: fixed overlay layout, collapsible icon-strip sidebar |
| 2026-02-25 | New views: summary.js (PROJECT.md), prompts.js (tree+editor), code.js (viewer) |
| 2026-02-25 | Redesigned: chat.js (/ commands popup), workflow.js (YAML split-pane + nodes) |
| 2026-02-25 | utils/markdown.js: renderMd, highlightYaml, validateYaml — no npm packages |
| 2026-02-25 | history.js: removed hardcoded API URL → uses state.settings.backend_url + project param |
| 2026-02-25 | Deleted views/project.js — navigation now driven by main.js sidebar tabs |
| 2026-02-26 | chat.py: append every UI exchange to workspace/{project}/history/history_{provider}.jsonl |
| 2026-02-26 | chat.py: update dev_runtime_state.json after each exchange (session_count, last_provider, etc.) |
| 2026-02-26 | history.py: /history/chat now merges prompt_log.jsonl (Claude Code hook entries) + deduplicates |
| 2026-02-26 | history.js: source badge (ui / claude-code), response preview with left-border styling |
| 2026-02-26 | Created workspace/aicli/project_state.json — static project metadata |
| 2026-02-26 | Created workspace/aicli/dev_runtime_state.json — auto-updated runtime state |
| 2026-02-26 | projects.py: GET /{name} now includes project_state + dev_runtime_state in response |

---

## Open Questions

- Should the Electron terminal embed the aicli REPL directly, or just a shell?
  → Decision: embed the REPL (spawn `python3.12 cli.py` via node-pty)
- Should workflow run logs be stored in workspace/ or .aicli/?
  → Decision: workspace/<project>/runs/ (portable, version-controllable)
- Should CostTracker support streaming token counting via Anthropic API?
  → Deferred: use rough estimate (len//4) for now, upgrade later
- Should the cloud deployment use Railway (current) or self-hosted VPS?
  → Undecided: Railway.toml ready; self-hosted needs nginx + systemd config
