# aicli Project Context

This is an AI-powered development CLI tool written in Python 3.12.

## Quick Reference

- Engine root: `/Users/user/Documents/gdrive_cellqlick/2026/aicli/`
- Workspace root: `aicli/workspace/`
- Active project workspace: `workspace/aicli/`
- Config: `aicli.yaml`

## Key File Locations

| Purpose | Path |
|---------|------|
| CLI entry point | `cli.py` |
| Provider base | `providers/base.py` |
| Claude provider | `providers/claude_agent.py` |
| Workflow runner | `workflows/runner.py` |
| Cost tracker | `core/cost_tracker.py` |
| Context builder | `core/context_builder.py` |
| Memory store | `core/memory.py` |
| This project's workspace | `workspace/aicli/` |
| Workflow definitions | `workspace/aicli/workflows/` |
| Role prompts | `workspace/aicli/prompts/roles/` |

## Environment Variables Required

- `ANTHROPIC_API_KEY` — Claude
- `OPENAI_API_KEY` — OpenAI
- `DEEPSEEK_API_KEY` — DeepSeek (optional)
- `GEMINI_API_KEY` — Gemini (optional)
- `XAI_API_KEY` — Grok (optional)
