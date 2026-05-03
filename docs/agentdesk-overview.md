# AgentDesk — Product Overview

---

## Slide 1 · What is AgentDesk?

**AgentDesk** is a desktop application that gives every AI coding assistant the same persistent project memory — so you can switch between Claude Code, Cursor, the CLI, or the web UI and the AI picks up exactly where you left off.

> *"One memory layer. Any AI. Every session."*

### The problem it solves

| Without AgentDesk | With AgentDesk |
|---|---|
| Re-explain architecture every session | AI has full project context on day 1 |
| Context lost when switching tools | Shared memory across all LLM clients |
| No visibility into what the AI did | Full session + commit history |
| Each tool works in isolation | Unified backlog, roles, and pipelines |

---

## Slide 2 · The Solution

AgentDesk connects your codebase, your team's decisions, and your AI tools into a single coordinated workspace.

### Three capabilities in one product

**1 · Shared AI Memory**
Every prompt, commit, and decision is stored and indexed. When you open a new session — in any tool — the AI already knows your stack, your patterns, and your open tasks.

**2 · Work Item Backlog**
AI-classified work items (features, bugs, tasks, use cases) flow through a pipeline: raw capture → AI digest → user review → approved backlog. Each item carries acceptance criteria and an implementation plan.

**3 · Multi-Agent Pipelines**
Define pipelines of specialised roles — PM, Architect, Developer, Reviewer — that execute as an async DAG. Each role uses its own LLM provider, model, and tools. Pipelines can require human approval before execution continues.

---

## Slide 3 · Architecture

```
┌─────────────────────────────────────────────────────┐
│                    AgentDesk Desktop                 │
│           Electron + Vite · Vanilla JS UI            │
└────────────────────┬────────────────────────────────┘
                     │ HTTP / REST
┌────────────────────▼────────────────────────────────┐
│                  FastAPI Backend                     │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │  Memory  │  │ Pipeline │  │   Agent Execution  │ │
│  │  Engine  │  │  Engine  │  │   (ReAct + Tools)  │ │
│  └────┬─────┘  └────┬─────┘  └─────────┬──────────┘ │
│       │              │                  │            │
│  ┌────▼──────────────▼──────────────────▼──────────┐ │
│  │          PostgreSQL 15 + pgvector               │ │
│  │   Raw events · Work items · Embeddings          │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
         │                          │
    ┌────▼────┐              ┌──────▼──────┐
    │  Claude │              │  OpenAI /   │
    │  Sonnet │              │  DeepSeek / │
    │  Haiku  │              │  Gemini /   │
    └─────────┘              │  Grok       │
                             └─────────────┘

  IDE integrations: Claude Code · Cursor · Copilot · OpenAI Codex
```

### Key layers

| Layer | Technology | Role |
|---|---|---|
| Frontend | Electron + Vite | Desktop UI, terminal, Monaco editor |
| Backend | FastAPI + uvicorn | REST API, agent orchestration |
| Memory | 3-layer pipeline | Raw → Facts → Approved work items |
| Vector search | pgvector (1536-dim) | Semantic retrieval across all context |
| Agents | ReAct loop | Thought → Tool → Observation cycles |
| Pipelines | Async DAG | Multi-role sequential execution |

---

## Slide 4 · Why AgentDesk?

### For developers

- **No more re-explaining** — the AI knows your codebase, your decisions, your open tasks
- **Any LLM, your choice** — Claude, GPT-4, DeepSeek, Gemini, Grok, all in one place
- **Traceable AI work** — every tool call, commit, and review score is logged

### For teams

- **Shared backlog** — AI-classified work items that the whole team reviews and approves
- **Reproducible pipelines** — define once, run on any item, with consistent quality gates
- **Human in the loop** — approval gates let you review the AI's plan before it writes code

### For organisations

- **Multi-provider, no lock-in** — swap models without changing workflows
- **Usage visibility** — token costs, per-run scores, per-item history
- **Extensible** — add custom agent roles, pipelines, and tool integrations via YAML

---

*AgentDesk · v2.0 · 2026*
