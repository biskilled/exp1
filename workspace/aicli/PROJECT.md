# aicli — Shared AI Memory Platform

_Last updated: 2026-03-08_

---

## Vision

**aicli gives every LLM the same project memory.**

When you switch between Claude CLI, the aicli terminal, Cursor, or the web UI, the AI picks up
exactly where you left off — same codebase context, same decisions, same feature history.
No more copy-pasting context. No more re-explaining your architecture.

---

## Core Goals

| # | Goal | Status |
|---|------|--------|
| 1 | **Shared LLM memory** — Claude CLI, aicli CLI, Cursor, UI all read the same knowledge base | ✓ Implemented |
| 2 | **Prompt management** — Role-based agents (architect, developer, reviewer, QA, security, devops) | ✓ Foundation done |
| 3 | **5-layer memory** — Immediate → Working → Project → Historical → Global | ✓ Architecture in place |
| 4 | **Auto-deploy** — pull → commit → push after every AI session | ✓ Hooks + git.py |
| 5 | **Billing & usage** — Multi-user, server keys, balance, markup, coupons | ✓ Implemented |
| 6 | **Multi-LLM workflows** — YAML chains: design → review → develop → test | ✓ Runner done |

---

## 5-Layer Memory Architecture

```
Layer 1 — Immediate Context
  └── providers/{claude,openai,...}.messages  (in-memory, not persisted)
      Live conversation: current prompt chain within the session

Layer 2 — Working Memory
  └── {cli_data_dir}/sessions/{provider}_messages.json
  └── {cli_data_dir}/session_state.json
      Short-term task state: active feature, tag, last commit, cross-provider handoff

Layer 3 — Project Knowledge
  └── workspace/{project}/PROJECT.md          — living project doc (this file)
  └── workspace/{project}/project_state.json  — structured metadata: tech stack, modules, APIs
  └── workspace/{project}/_system/CLAUDE.md   — synced to code_dir/CLAUDE.md for Claude Code
      Architecture, decisions, coding standards, data models

Layer 4 — Historical Knowledge
  └── workspace/{project}/_system/history.jsonl    — all interactions (UI + CLI + workflow + Cursor)
  └── {cli_data_dir}/memory.jsonl                  — tagged/featured entries, keyword-searchable
      Past decisions, design discussions, feature history, bug postmortems, refactor notes

Layer 5 — Global Knowledge
  └── workspace/_templates/hooks/                  — canonical hook scripts for all projects
  └── workspace/_templates/{blank,python_api,...}  — project starter templates
  └── workspace/_templates/roles/                  — shared AI role prompts (TODO: create)
      Company coding standards, security policies, AI role prompts, architecture templates
```

### How `/memory` syncs layers 3–5 to every LLM tool:

```
_system/claude/CLAUDE.md   →  {code_dir}/CLAUDE.md          ← Claude Code reads at session start
_system/claude/MEMORY.md   →  {code_dir}/MEMORY.md          ← referenced inside CLAUDE.md
_system/cursor/rules.md    →  {code_dir}/.cursor/rules/aicli.mdrules  ← Cursor reads on open
_system/aicli/context.md   →  prepended to every aicli CLI prompt
```

---

## Prompt Management — Roles & Agents

Roles live in `workspace/{project}/prompts/roles/`. Each is a Markdown system prompt.

| Role file | Use case | Provider preference |
|-----------|----------|-------------------|
| `architect.md` | System design, API contracts, tech decisions | Claude (reasoning) |
| `developer.md` | Code implementation, refactoring | Claude / DeepSeek |
| `reviewer.md` | Code review, quality feedback | OpenAI / Gemini |
| `qa.md` | Test design, edge cases, regression | DeepSeek / Claude |
| `security.md` | OWASP checks, auth review, secrets audit | Claude |
| `devops.md` | CI/CD, AWS, Railway, Docker, nginx | GPT-4.1 |
| `summariser.md` | Compress long sessions → summary | Gemini Flash (cheap) |

**Workflow example** (multi-role YAML):
```yaml
name: feature_cycle
steps:
  - name: design
    provider: claude
    role_prompt: prompts/roles/architect.md
    prompt: prompts/01_design.md
  - name: implement
    provider: deepseek
    role_prompt: prompts/roles/developer.md
    prompt: prompts/02_implement.md
    inject_previous_output: true
  - name: review
    provider: openai
    role_prompt: prompts/roles/reviewer.md
    prompt: prompts/03_review.md
    inject_previous_output: true
  - name: tests
    provider: deepseek
    role_prompt: prompts/roles/qa.md
    prompt: prompts/04_tests.md
    inject_previous_output: true
```

---

## Architecture

### Engine / Workspace Separation

```
aicli/                     ← ENGINE — code only, no project-specific content
├── cli.py                 ← Interactive REPL (prompt_toolkit + rich)
├── providers/             ← LLM adapters (Claude, OpenAI, DeepSeek, Gemini, Grok)
├── core/                  ← Memory, session, git, hooks, analytics, cost tracking
├── workflows/             ← YAML workflow executor
├── prompts/               ← Prompt loader (reads from workspace)
└── ui/
    ├── electron/          ← Electron shell (BrowserWindow, xterm.js, Monaco)
    ├── frontend/          ← Vanilla JS UI (no framework, no bundler)
    └── backend/           ← FastAPI (localhost:8000)
        ├── routers/       ← auth, chat, projects, admin, billing, git, history, workflows
        ├── core/          ← auth, pricing, api_keys, llm_clients, provider_costs
        └── data/          ← ALL server data (api_keys.json, users.json, pricing.json...)

workspace/                 ← CONTENT — portable, per-project, version-controllable
├── _templates/
│   ├── hooks/             ← Canonical hook scripts (log_user_prompt, auto_commit_push...)
│   └── {blank,python_api,quant_notebook,ui_app}/
└── {project}/
    ├── PROJECT.md         ← Living project doc (this file)
    ├── project.yaml       ← Project config (code_dir, provider, git settings)
    ├── prompts/
    │   ├── roles/         ← Agent role system prompts
    │   └── {feature}/     ← Feature-specific prompts
    ├── workflows/         ← YAML workflow definitions
    └── _system/
        ├── history.jsonl      ← ALL interactions (all LLMs, all tools)
        ├── CONTEXT.md         ← Auto-generated project overview
        ├── claude/CLAUDE.md   ← Claude Code system prompt (synced to code_dir)
        ├── claude/MEMORY.md   ← Distilled history (synced to code_dir)
        ├── cursor/rules.md    ← Cursor AI rules (synced to .cursor/rules/)
        └── aicli/context.md   ← Compact CLI injection block
```

### Key Config Files

| File | Purpose |
|------|---------|
| `aicli.yaml` | CLI config: workspace_dir, providers, hooks, cli_data_dir |
| `workspace/{project}/project.yaml` | Per-project: code_dir, default_provider, git settings, claude_cli_support |
| `ui/backend/config.py` | Backend: data_dir=ui/backend/data/, require_auth, dev_mode |
| `ui/backend/data/provider_costs.json` | **Single source of truth** for LLM per-token pricing (used by CLI + backend) |
| `ui/backend/data/pricing.json` | Free tier limits, markup %, free-tier model list |
| `ui/backend/data/api_keys.json` | Server-managed LLM API keys (admin-set, never in client requests) |

---

## Features

### Implemented ✓

**Memory & Context**
- [x] 5-layer memory architecture (immediate, working, project, historical, global)
- [x] Unified history.jsonl: all sources (UI, Claude CLI, aicli CLI, workflow) → single file
- [x] Per-LLM output: `_system/claude/`, `_system/cursor/`, `_system/aicli/` subdirs
- [x] `POST /projects/{name}/memory` — regenerates all LLM files + copies to code_dir
- [x] JSONL keyword/tag/feature memory search (no ML deps, instant startup)
- [x] Cross-provider session handoff: save/restore messages between CLI sessions
- [x] `_system/aicli/context.md` prepended to every CLI prompt automatically

**Prompt Management**
- [x] Workspace prompt folders: `prompts/roles/`, `prompts/{feature}/`
- [x] Role-based system prompts loaded per provider
- [x] Prompts UI: recursive folder tree + textarea editor
- [x] `/compare <prompt.md>` — multi-LLM prompt comparison, winner logged

**Providers (CLI)**
- [x] Claude: Anthropic SDK, streaming, tool use (bash/read/write/ls), MCP
- [x] OpenAI: chat completions, streaming
- [x] DeepSeek: OpenAI-compat API, streaming
- [x] Gemini: google-generativeai SDK, streaming
- [x] Grok: xAI OpenAI-compat API, streaming
- [x] BaseProvider: retry (3 attempts, 1s/3s/10s backoff), provider fallback

**Auto-Deploy / Git**
- [x] Claude Code Stop hook → auto_commit_push.sh after every response
- [x] Git supervisor: auto-commit + push from CLI after AI responses
- [x] Backend `POST /git/{project}/commit-push`: LLM-generated commit messages
- [x] Git OAuth device flow + Personal Access Token setup
- [x] Auto-pull before commit; conflict detection
- [x] Credentials stored in `_system/.git_token` (gitignored)

**Multi-LLM Workflows**
- [x] YAML workflow executor: file injection, retry, cost tracking per step
- [x] CostTracker reads from `ui/backend/data/provider_costs.json` (single source)
- [x] Workflow runs logged to `workspace/{project}/runs/`
- [x] `inject_files`, `inject_previous_output`, `stop_condition` support

**UI (Electron + FastAPI)**
- [x] Electron shell: BrowserWindow, IPC, embedded xterm.js terminal (node-pty)
- [x] Vanilla JS frontend (no framework, no build step, no npm bundler)
- [x] 4-step project creation wizard (Basics → Git → IDE Support → Review)
- [x] Chat: SSE streaming, session list (UI+CLI+WF unified), source badges
- [x] Summary: PROJECT.md viewer + edit/preview toggle
- [x] Prompts: recursive tree + textarea editor, save-disabled-until-changed
- [x] Workflow: YAML editor + syntax highlight + node flow diagram
- [x] History: unified chat tabs (all sources)
- [x] Code: folder tree + read-only file viewer

**Billing & Usage**
- [x] Multi-user roles: admin / paid / free
- [x] Server-managed API keys (admin panel → api_keys.json; client sends no keys)
- [x] Per-user balance: `balance_added_usd − balance_used_usd`
- [x] Markup pricing per provider; free-tier limit + model restrictions
- [x] Coupons (AICLI=$10 pre-seeded); apply at register or from Billing tab
- [x] Transaction log: `{DATA_DIR}/transactions/{user_id}.jsonl`
- [x] Provider usage fetch from Anthropic + OpenAI APIs
- [x] Manual provider balance tracking (`provider_balances.json`)
- [x] Railway deployment: Dockerfile + railway.toml

### In Progress ◷

- [ ] Global knowledge layer: `workspace/_templates/roles/` shared role library
- [ ] Memory auto-compaction at token limit (compress old entries → summary)
- [ ] `/deploy <aws|railway>` — one-command deploy from CLI
- [ ] Remote config sync (`config_sync.py` currently stub)
- [ ] UI prompt compare split-pane (explorer.js)

### Planned ○

- [ ] Stripe real payment integration (placeholder returning "coming soon")
- [ ] MCP server: expose memory query endpoint so any LLM can pull context on-demand
- [ ] Semantic search over history.jsonl (pgvector, Phase 2)
- [ ] Admin dashboard: revenue summary, top users by spend, model cost breakdown
- [ ] Workflow `stop_condition` with loop-back (retry if review fails)
- [ ] Agent-to-agent communication in workflows (output routed to specific next agent)

---

## Key Patterns

### Single Pricing Source
`ui/backend/data/provider_costs.json` is the single source of truth for all LLM pricing.
- `core/cost_tracker.py` reads it (with fallback to defaults if backend not set up)
- `ui/backend/core/provider_costs.py` manages it (load/save/estimate)
- `ui/backend/core/pricing.py` reads it for markup calculation

### Configurable cli_data_dir
All CLI core modules use `config.get("cli_data_dir", ".aicli")` — never hardcode `.aicli/`.
Set in `aicli.yaml` as `cli_data_dir: .aicli`.

### Hook Architecture
```
workspace/_templates/hooks/   ← canonical scripts (version-controlled)
{code_dir}/.aicli/scripts/    ← project copy (installed by wizard or /memory)
.claude/settings.local.json   ← registers hooks with Claude Code
```

### Provider Contract
```python
class BaseProvider:
    def send(self, prompt: str, system: str = "") -> str: ...
    def stream(self, prompt: str, system: str = "") -> Generator[str, None, None]: ...
    def clear_history(self) -> None: ...
    def reload_system_prompt(self) -> None: ...
```

### Save-Disabled-Until-Changed (UI editors)
```js
saveBtn.disabled = true;
textarea.addEventListener('input', () => {
  saveBtn.disabled = textarea.value === _original;
});
```

### Auth Architecture
- `REQUIRE_AUTH=false` (local dev) — no login gate
- `REQUIRE_AUTH=true` (Railway/cloud) — JWT required on all routes
- `DEV_MODE=true` — synthetic admin user, no balance deduction
- JWT stored in `localStorage`; first registered user = admin
- Role system: `admin | paid | free`

---

## Open Questions

- Should `workspace/_templates/roles/` be a built-in global roles library?
  → Proposal: yes — ship 6 default roles with installation, user extends in project-level roles/
- Should MCP server be a separate process or embedded in FastAPI?
  → Leaning: separate process, so Claude Code can connect directly without backend running
- Should workflow results feed back into historical memory automatically?
  → Proposal: yes — WorkflowRunner appends to history.jsonl with `source: workflow`
- Should the Electron app ship with `python3.12` bundled, or require system install?
  → Current: requires system python3.12. Bundling adds ~50MB but removes user friction.

## Recent Work

- Fix hooks integration — commits not working from claude cli; history.jsonl captures prompts but not responses; ensure all sources write to commit_log.jsonl
- Balance persistence on refresh — manual balance entry saves but doesn't persist on UI refresh; admin sees total, users see own balance
- PostgreSQL usage_logs population — table created but entries not populating; ensure all providers log usage and refresh UI displays totals
- Consolidate workflow/entity management — 'flows' tab created but 'workflow' tab exists; clarify distinction; build node graph UI instead of separate tabs
- Memory system optimization — commit_log.jsonl not capturing all errors/logs from claude cli, aicli, cursor; ensure unified history across all sources
- Shared memory architecture for LLM context — define how /memory command reads/compresses history files; establish memory digest strategy for project understanding
