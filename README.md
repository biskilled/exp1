# aicli

AI-powered development CLI — prompt Claude, OpenAI, DeepSeek, Gemini, or Grok from
your terminal with persistent memory, YAML workflow pipelines, git auto-commit, and
a desktop Electron UI.

---

## Prerequisites

- Python 3.12
- Node.js 20+ (Electron UI only)
- API keys for the providers you want to use

---

## Setup

```bash
pip3.12 install -r requirements.txt
cp .env.example .env   # fill in your API keys
```

`.env`:

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
GEMINI_API_KEY=AIza...
XAI_API_KEY=xai-...
```

---

## Run the CLI

```bash
python3.12 cli.py
```

```
╭─────────────────────────────────────────────────────────╮
│ aicli  branch=main  mode=CLAUDE  memory=0 entries       │
│ project=aicli                                           │
│ Type /help for commands                                 │
╰─────────────────────────────────────────────────────────╯
(CLAUDE)[aicli]>
```

---

## Basic Commands

```bash
# Ask anything — Claude streams live with tool access (bash, read_file, write_file)
(CLAUDE)[aicli]> What files should I modify to add a new provider?

# Switch provider mid-session (history carries forward)
(CLAUDE)> /switch deepseek
(DEEPSEEK)> /switch openai

# Clear conversation history
(CLAUDE)> /clear
```

---

## Workspace & Projects

AI content (prompts, workflows, history) lives separately from engine code:

```
workspace/
├── _templates/          ← project starters (blank, python_api, quant_notebook, ui_app)
└── aicli/               ← this project's workspace
    ├── PROJECT.md        ← living project doc (injected as system context)
    ├── workflows/
    └── prompts/
```

```bash
/project list
/project new myapp --template python_api
/project switch myapp
```

---

## Workflows

Multi-step LLM pipelines defined in YAML:

```yaml
name: build_feature
steps:
  - name: design
    provider: claude
    prompt: prompts/01_design.md
    inject_files: [PROJECT.md, "{{code_dir}}/providers/"]
  - name: implement
    provider: claude
    prompt: prompts/02_implement.md
    inject_previous_output: true
  - name: review
    provider: deepseek
    prompt: prompts/03_review.md
    output_format: json
    on_fail:
      loop_to: implement
stop_condition:
  field: score
  threshold: 8
```

```bash
/workflow                    # list workflows
/workflow build_feature      # run a workflow
/compare prompts/roles/architect.md --providers claude,deepseek,openai
```

---

## Memory & Tags

```bash
/tag auth-refactor           # tag current context
/search-tag auth-refactor    # retrieve tagged sessions
/feature streaming-support   # set feature context
/analytics                   # usage stats + cost summary
```

---

## Project Docs

`PROJECT.md` is injected as system context for all providers:

```bash
/docs                        # show current PROJECT.md
/docs todo "Add rate limiting"
/docs done "rate limiting"
/docs generate               # regenerate from git + memory
```

---

## Git Integration

```bash
/push       # commit + push with AI-generated commit message
/status     # git status, memory size, current mode
/history    # last 20 commits with feature/tag columns
```

Auto-commit fires after every Claude Code CLI session via the Stop hook
(`auto_commit_push: true` in `workspace/<project>/project.yaml`).

---

## Electron UI

```bash
cd ui && npm install && npm run dev
```

Set the backend URL via `BACKEND_URL` env var (default: `http://localhost:8000`).

Views: **Chat** · **Summary** · **Prompts** · **Code** · **Workflow** · **History** · **Settings**

---

## Configuration (`aicli.yaml`)

```yaml
working_folder: /path/to/your/project
active_project: aicli
workspace_dir: /path/to/workspace
backend_url: http://localhost:8000      # FastAPI backend URL

providers:
  default: claude
  claude:
    model: claude-sonnet-4-6
  deepseek:
    fallback: openai                    # auto-fallback if unavailable
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `API key not found` | Check `.env` has the key |
| `working_folder not found` | Update `working_folder` in `aicli.yaml` |
| `No active project` | Run `/project switch aicli` |
| `Workflow not found` | Check `workspace/<project>/workflows/` |
| `node-pty` errors | `cd ui && npm install` (needs Xcode tools) |
| Backend offline in UI | Ensure `uvicorn main:app` runs in `ui/backend/` |
