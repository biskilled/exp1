---
description: Run aicli backend commands — memory, status, pipeline, search, commit, entities
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
| `/roles` | Use MCP tool `get_roles`. List available AI roles. |
| `/context` | Use MCP tool `get_tagged_context` with any phase/feature from remaining args. Show tagged events. |
| `/commit [message]` | Use MCP tool `commit_push` with optional `message_hint`. Show result. |
| `/schema` | Use MCP tool `get_db_schema`. Show table structure. |
| `/sync-github <owner> <repo>` | Use MCP tool `sync_github_issues` with `owner` and `repo`. Show imported count. |
| `/help` | Show this command table to the user. |

## Rules

- All MCP tools are from the `aicli_project` MCP server (already configured).
- For curl commands, parse the JSON response and present it in a readable format.
- If the backend is not reachable, tell the user to start it: `cd backend && python3.12 -m uvicorn main:app --host 127.0.0.1 --port 8000 &`
- If `$ARGUMENTS` is empty, show the help table.
- Any extra arguments after the command name are passed as parameters to the tool/endpoint.
