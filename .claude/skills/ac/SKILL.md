---
description: Run aicli backend commands — memory, status, pipeline, search, commit, entities, agent testing
---

# aicli Command Bridge

Route the user's command to the aicli backend at `http://localhost:8000`.
The active project is `aicli` unless specified otherwise.

## Command: $ARGUMENTS

Parse the first word of `$ARGUMENTS` as the command name. Match it against the table below and execute the corresponding action.

| Command | Action |
|---------|--------|
| `/memory` | `curl -s -X POST http://localhost:8000/projects/aicli/memory` — generates and syncs all 5 memory files (CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md). Show which files were generated and any suggested tags. |
| `/status` | `curl -s http://localhost:8000/projects/aicli` — show project metadata, then also call MCP tool `get_project_state` for facts + active work items. Summarize concisely. |
| `/search <query>` | Use MCP tool `search_memory` with the remaining arguments as `query`. Show top results. |
| `/history [N]` | Use MCP tool `get_recent_history` with `limit` = N (default 10). Show entries as a compact table. |
| `/commits [N]` | Use MCP tool `get_commits` with `limit` = N (default 10). Show as compact table with tags. |
| `/items [category]` | Use MCP tool `list_work_items` with optional `category` filter (feature/bug/task). Show as table with status + seq_num. |
| `/item <number>` | Use MCP tool `get_item_by_number` with `seq_num` = the number (strip leading #). Show full details. |
| `/pipeline <id_or_name>` | Use MCP tool `run_work_item_pipeline` with `work_item_id` or `work_item_name`. Report run progress. |
| `/create <category> <name> [description]` | Use MCP tool `create_entity` with `category`, `name`, and optional `description`. Show created item with seq_num. |
| `/tags` | Use MCP tool `get_session_tags`. Show current phase + feature tags. |
| `/tag <phase> [feature]` | Use MCP tool `set_session_tags` with `phase` and optional `feature`. Confirm update. |
| `/roles` | `curl -s http://localhost:8000/agents/roles` — list all active agent roles with name, model, tools count, react flag. Format as a table. |
| `/pipelines` | `curl -s http://localhost:8000/agents/pipelines` — list available pipeline YAML definitions with stages. |
| `/context` | Use MCP tool `get_tagged_context` with any phase/feature from remaining args. Show tagged events. |
| `/commit [message]` | Use MCP tool `commit_push` with optional `message_hint`. Show result. |
| `/push [message]` | `curl -s -X POST "http://localhost:8000/git/aicli/commit-push" -H "Content-Type: application/json" -d '{"commit_message":"<message or empty string>"}'` — stage all changes, generate LLM commit message, commit and push. Show commit hash + message. |
| `/pull` | `curl -s -X POST "http://localhost:8000/git/aicli/pull"` — git pull latest from remote. Show result. |
| `/git-status` | `curl -s "http://localhost:8000/git/aicli/status"` — show staged/unstaged files and current branch. |
| `/embed [commits\|prompts]` | Without arg: both. `commits` → `POST /memory/aicli/embed-commits`. `prompts` → `POST /memory/aicli/embed-prompts`. Show events_created. |
| `/schema` | Use MCP tool `get_db_schema`. Show table structure. |
| `/sync-github <owner> <repo>` | Use MCP tool `sync_github_issues` with `owner` and `repo`. Show imported count. |
| `/rebuild [confirm]` | Rebuild all open+unlinked work items from scratch. Without `confirm`, calls `curl -s "http://localhost:8000/memory/aicli/rebuild?dry_run=true"` and shows preview (items/events that would be deleted). With `confirm`, calls with `?dry_run=false` — deletes open work items with no user tag, deletes/resets auto-generated events, resets mirror event_ids, then queues embed-prompts + embed-commits in background. |
| `/agent <role_name> <task>` | Run a single agent in pipeline mode. See **Agent Testing** below. |
| `/run <pipeline_name> <task>` | Run a full pipeline. See **Pipeline Testing** below. |
| `/help` | Show this command table to the user. |

---

## Agent Testing — `/agent <role_name> <task>`

Runs a single agent via `POST /agents/run` and shows the full ReAct trace.

**Example:** `/agent "Product Manager" "Add rate limiting to the login endpoint"`

Steps:
1. POST to `http://localhost:8000/agents/run` with body:
   ```json
   {"role": "<role_name>", "task": "<task>", "project": "aicli"}
   ```
2. Parse the JSON response and display:
   - **Role** and **Status** header
   - **ReAct Trace** — for each step show:
     ```
     Step N  ─────────────────────────────────────
     Thought: <thought text>
     Action:  <tool_name>(<args summary>)
     Observe: <first 200 chars of observation>
     [⚠ GUARD FIRED] (if hallucination_guard_fired=true)
     ```
   - **Structured Output** — pretty-print the JSON handoff
   - **Summary** — cost_usd, tokens, steps count, status

If `status` is `loop_detected` or `max_steps_reached`, show a warning with the error.

---

## Pipeline Testing — `/run <pipeline_name> <task>`

Runs a full multi-agent pipeline via `POST /agents/run-pipeline` and shows per-stage results.

**Example:** `/run standard "Add rate limiting to the login endpoint"`

Steps:
1. POST to `http://localhost:8000/agents/run-pipeline` with body:
   ```json
   {"pipeline": "<pipeline_name>", "task": "<task>", "project": "aicli"}
   ```
2. Parse JSON and display:
   - **Pipeline Summary** — run_id, verdict, total cost, total steps, duration
   - **Per-Stage Results** — for each stage:
     ```
     ── Stage: project_manager (Product Manager) — attempt 1 ──
     Status: done | Steps: 5 | Cost: $0.0012
     Thought/Action trace (first 3 steps shown)
     Structured Output: {...}
     ```
   - **Final Verdict** — "✅ approved" | "❌ rejected" | "⚠ error"
   - If rejected: show issues and suggested_fixes from reviewer

If the pipeline is not found (404), suggest running `/pipelines` to see available ones.

---

## Rules

- All MCP tools are from the `aicli_project` MCP server (already configured).
- For curl/POST commands, parse the JSON response and present it in a readable format.
- If the backend is not reachable, tell the user to start it:
  `cd /Users/user/Documents/gdrive_cellqlick/2026/aicli/backend && python3.12 -m uvicorn main:app --host 127.0.0.1 --port 8000 > /tmp/backend.log 2>&1 &`
- If `$ARGUMENTS` is empty, show the help table.
- Any extra arguments after the command name are passed as parameters to the tool/endpoint.
- For `/agent` and `/run`, these are REAL calls to a live backend — the agent will actually execute. Warn the user if the task involves writing files or git commits.
