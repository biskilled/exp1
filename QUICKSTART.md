# aicli — Quick Start Guide

## 1. Prerequisites

- Python 3.12
- Node.js 20+ (for the Electron UI only)
- API keys for the providers you want to use

---

## 2. Setup

```bash
cd /Users/user/Documents/gdrive_cellqlick/2026/aicli

# Install Python dependencies
pip3.12 install -r requirements.txt

# Copy and fill in your API keys
cp .env.example .env   # (or create .env manually — see below)
```

`.env` file — add whichever keys you have:

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
DEEPSEEK_API_KEY=sk-...
GEMINI_API_KEY=AIza...
XAI_API_KEY=xai-...
```

---

## 3. Run the CLI

```bash
python3.12 cli.py
```

You'll see the startup panel:
```
╭─────────────────────────────────────────────────────────╮
│ aicli  branch=main  mode=CLAUDE  memory=0 entries       │
│ project=aicli                                           │
│ Type /help for commands                                 │
╰─────────────────────────────────────────────────────────╯
(CLAUDE)[aicli]>
```

---

## 4. Basic Commands

### Ask Claude anything
```
(CLAUDE)[aicli]> What files should I modify to add a new provider?
```
Claude streams the response live as it's generated. It has tool access (bash, read_file,
write_file, list_directory) — it can read your code and make changes directly.

### Switch provider mid-session
```
(CLAUDE)> /switch deepseek
(DEEPSEEK)> Now I'm on DeepSeek — same memory context carries forward
(DEEPSEEK)> /switch openai
(OPENAI)> /switch claude
```

All providers maintain conversation history within the session.

### Clear conversation history
```
(CLAUDE)> /clear
```
Clears history for ALL active providers (fresh start).

---

## 5. Workspace & Projects

Your AI content (prompts, workflows, history) lives separately from the engine code:

```
workspace/
├── _templates/          ← project starters
│   ├── blank/
│   ├── python_api/
│   ├── quant_notebook/
│   └── ui_app/
└── aicli/               ← this project's workspace (already set up)
    ├── PROJECT.md
    ├── CLAUDE.md
    ├── workflows/
    └── prompts/
```

### List projects
```
(CLAUDE)> /project list
```

### Create a new project from template
```
(CLAUDE)> /project new myapp --template python_api
(CLAUDE)> /project new trading_bot --template quant_notebook
```

### Switch active project
```
(CLAUDE)> /project switch myapp
```

---

## 6. Workflows

Workflows are multi-step LLM pipelines defined in YAML.

### List available workflows (for current project)
```
(CLAUDE)> /workflow
  build_feature
  code_review
  update_docs
```

### Run a workflow
```
(CLAUDE)> /workflow build_feature
Workflow input: Add streaming support to the DeepSeek provider
```

The runner will:
1. Inject context (PROJECT.md, relevant code files)
2. Run each step (Claude → Claude → DeepSeek review)
3. Loop back if the review score is below threshold
4. Print a cost table at the end
5. Save a run log to `workspace/aicli/runs/`

### What a workflow YAML looks like
```yaml
# workspace/aicli/workflows/build_feature/workflow.yaml
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
    output_format: json       # expects {"score": N, "approved": bool}
    on_fail:
      loop_to: implement      # feed issues back if score < 8
stop_condition:
  field: score
  threshold: 8
```

---

## 7. Compare Prompts Across LLMs

Run the same prompt against multiple providers simultaneously and pick the winner:

```
(CLAUDE)> /compare prompts/roles/architect.md --providers claude,deepseek,openai
```

- Results shown side-by-side
- You pick the winner (1/2/3)
- Result logged to `workspace/aicli/prompt_evals.jsonl` for future reference

---

## 8. Memory & Context

Every turn is saved to `.aicli/memory.jsonl`. Memory is automatically searched and
injected as context for ALL providers (Claude and non-Claude alike).

### Tag your work
```
(CLAUDE)> /tag auth-refactor
(CLAUDE)> Tell me how to improve the session handling
(CLAUDE)> /tag payments
```

### Search by tag
```
(CLAUDE)> /search-tag auth-refactor
```

### Feature tracking
```
(CLAUDE)> /feature streaming-support
(CLAUDE)> How should I implement streaming for Gemini?
```

---

## 9. Project Docs

`PROJECT.md` is the living document for your project. It's injected into the system
prompt so all providers have project context from the start.

```bash
# Show current PROJECT.md
/docs

# Add a TODO item (no LLM call)
/docs todo "Add rate limiting to providers"

# Mark a TODO done
/docs done "rate limiting"

# Regenerate PROJECT.md from git history + memory (uses OpenAI)
/docs generate
```

---

## 10. Git Integration

```bash
# Commit + push with AI-generated commit message
/push

# Check git status, memory size, current mode
/status

# Last 20 commits with feature/tag columns
/history
```

---

## 11. Run Tests

```bash
python3.12 -m pytest tests/ -v
```

Or from within the CLI:
```
(CLAUDE)> /qa
```

---

## 12. Run the Electron UI

```bash
cd ui
npm install
npm run dev    # starts Vite + Electron with hot reload
```

The UI connects to the FastAPI backend (auto-started by Electron) at `localhost:8000`.

Features:
- **Chat** tab — streaming chat with any provider
- **Explorer** tab — Monaco editor + file tree for workspace + code
- **History** tab — chat logs, git commits, workflow run logs, prompt evals
- **Workflow** tab — YAML workflow editor
- **Settings** tab — configure workspace_dir, active project, API key status

---

## 13. Configuration (`aicli.yaml`)

Key settings you may want to change:

```yaml
working_folder: /path/to/your/project    # git project Claude works on
module: ui                               # which prompts/module/ to load
active_project: aicli                   # active workspace project
workspace_dir: /path/to/workspace       # where workspaces live

providers:
  default: claude
  claude:
    model: claude-sonnet-4-6
  deepseek:
    fallback: openai    # auto-fallback if DeepSeek is unavailable
```

---

## 14. Switching from `claude` CLI to aicli

If you've been using the `claude` CLI directly in your project folder:

1. The `UserPromptSubmit` hook is now configured in `.claude/settings.local.json`
   so every `claude` CLI prompt is logged to `.aicli/prompt_log.jsonl`.
   This means **your existing `claude` session history is being tracked**.

2. To start using `aicli`, just run it from your project folder:
   ```bash
   cd /path/to/your/project
   python3.12 /Users/user/Documents/gdrive_cellqlick/2026/aicli/cli.py
   ```
   Or add an alias to `~/.zshrc`:
   ```bash
   alias aicli='python3.12 /Users/user/Documents/gdrive_cellqlick/2026/aicli/cli.py'
   ```

3. Update `aicli.yaml` to point to your project:
   ```yaml
   working_folder: /path/to/your/project
   active_project: your_project_name
   ```

4. aicli starts with the same `CLAUDE.md` awareness as the `claude` CLI, plus:
   - Full conversation history that persists across sessions
   - Memory search and injection for all providers
   - Multi-provider switching with shared context
   - Workflow runner, cost tracking, project templates

---

## 15. Cross-LLM Handoff — How It Works

Every turn is preserved across sessions and across providers through 5 layers:

### Layer 1: `session_state.json` — the "sticky note"
Updated after every turn. Contains: last provider, feature, tag, last Q&A preview.
Injected as `[PREVIOUS SESSION]` into the **first prompt of every new session**,
for **every provider**. When you restart and switch to DeepSeek, it sees this:
```
[PREVIOUS SESSION — 2026-02-23]
Provider: claude  Project: aicli
Feature in progress: streaming-support
Last question: How do I add streaming to Gemini?
Last answer: Use model.generate_content(stream=True)...
(session #14)
```

### Layer 2: Provider message history — persisted across sessions
Each provider saves its conversation `messages` to `.aicli/sessions/<provider>_messages.json`
after every turn. On next startup, history is reloaded. Claude, OpenAI, DeepSeek,
Grok, and Gemini all resume their own full conversation thread automatically.

### Layer 3: `memory.jsonl` — permanent knowledge base
Every Q&A pair from all providers. Searched by keyword at each turn and injected
as `[RELEVANT PAST CONTEXT]`. Auto-compacted to `memory_summary.md` after 200 entries.

### Layer 4: `memory_summary.md` — long-term project knowledge
When memory exceeds 200 entries, the oldest are summarised by LLM and stored here.
Injected as `[HISTORICAL CONTEXT]` in every prompt — even after `memory.jsonl` is trimmed.
This means project knowledge persists indefinitely.

### Layer 5: `CLAUDE.md` + `PROJECT.md` — static project context
The assembled system prompt. Both `claude` CLI and aicli read this.
Update with `/docs generate` after major work sessions.

---

**Recommended handoff pattern:**
```bash
# LLM A (Claude) finishes a chunk of work
/docs todo "Next: add rate limiting middleware"
/push                                              # commit + saves session state

# Restart aicli, switch to LLM B
/switch deepseek

# DeepSeek automatically sees the [PREVIOUS SESSION] block.
# Just ask:
What was the last thing worked on? Continue with the next TODO.
```

**To start completely fresh:**
```
/clear    # clears all message histories + session files (memory.jsonl preserved)
```

---

## 16. Do I Need ChromaDB?

**No.** Here's why file-based storage is sufficient for this use case:

| Concern | Reality |
|---------|---------|
| Search speed | JSONL keyword search over 200 entries takes < 1ms |
| "Semantic" recall | Covered by CLAUDE.md + memory_summary.md context injection |
| History volume | 5 turns/day × 365 days = 1,825 entries → compacts to ~50 + summary |
| Startup time | Instant (no model download, no vector index build) |
| Dependencies | Zero ML packages needed |

ChromaDB would only be worth it if you had **50k+ entries** and needed
**semantic similarity** ("find work similar to X" when you don't know the keywords).
For a personal dev tool used by one developer on focused projects, JSONL + keyword
search + memory compaction covers 100% of practical recall needs.

The `memory_summary.md` compaction layer specifically closes the one gap that
pure keyword search has: it distils old work into a human-readable summary that
any LLM can reason about, even without knowing the exact keywords used months ago.

---

## 17. Troubleshooting

| Problem | Fix |
|---------|-----|
| `API key not found in env var` | Check `.env` has the key, and it's loaded |
| `ModuleNotFoundError: google.generativeai` | `pip3.12 install google-generativeai` |
| `working_folder not found` | Update `working_folder` in `aicli.yaml` to a real path |
| `No active project` | Run `/project switch aicli` |
| `Workflow not found` | Check workflow exists in `workspace/<project>/workflows/` |
| `node-pty` errors in Electron | `cd ui && npm install` (needs node-gyp + Xcode tools) |
