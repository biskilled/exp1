"""
aicli MCP Server — exposes the 5-layer project memory as LLM tools.

Run: python3.12 ui/mcp_server.py [--project aicli] [--backend http://localhost:8000]

Claude CLI and Cursor register this server via their settings files.
All tools call the FastAPI backend via HTTP — no direct DB access.

Tools:
    search_memory        — semantic search across history, roles, commits, docs
    get_project_state    — PROJECT.md + in_progress items + tech stack
    get_recent_history   — last N prompt/response entries for the project
    get_roles            — list available AI role prompt files
    get_commits          — list commits with phase/feature tags (untagged = red flag)
    get_session_tags     — active session tags (phase, feature, bug_ref)
    set_session_tags     — update active session tags
    commit_push          — commit + push from Cursor; logs to commit_log.jsonl
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any

import httpx

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp import types as mcp_types
except ImportError:
    print("ERROR: mcp package not installed. Run: pip install mcp>=1.0.0", file=sys.stderr)
    sys.exit(1)

# ── Config ─────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="aicli MCP Server")
parser.add_argument("--project", default=os.environ.get("ACTIVE_PROJECT", "aicli"))
parser.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
args, _ = parser.parse_known_args()

BACKEND = args.backend.rstrip("/")
PROJECT = args.project

# ── HTTP helpers ───────────────────────────────────────────────────────────────

async def _get(path: str, params: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(BACKEND + path, params=params or {})
        r.raise_for_status()
        return r.json()


async def _post(path: str, body: dict) -> Any:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(BACKEND + path, json=body)
        r.raise_for_status()
        return r.json()


async def _put(path: str, body: dict) -> Any:
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.put(BACKEND + path, json=body)
        r.raise_for_status()
        return r.json()


# ── MCP Server ─────────────────────────────────────────────────────────────────

server = Server("aicli-memory")


@server.list_tools()
async def list_tools() -> list[mcp_types.Tool]:
    _PHASES = ["discovery", "development", "testing", "review", "production", "maintenance", "bugfix"]

    return [
        mcp_types.Tool(
            name="search_memory",
            description=(
                "Semantic search across the project's full knowledge base: "
                "chat history, role prompts, commit summaries, code chunks, and design docs. "
                "Optionally filter by phase or feature tag to scope the search. "
                "Use this when you need to recall past decisions, understand a feature history, "
                "or find relevant context before starting work."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "limit": {"type": "integer", "default": 10},
                    "source_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by source: history, role, commit, doc, node_output",
                    },
                    "language": {"type": "string", "description": "Filter by language: python, javascript, …"},
                    "doc_type": {"type": "string", "description": "Filter by doc type: role, commit, …"},
                    "file_path": {"type": "string", "description": "Filter to a specific file path (substring)"},
                    "chunk_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by chunk type: summary, function, class, section, file_diff, full",
                    },
                    "phase": {
                        "type": "string",
                        "enum": _PHASES,
                        "description": "Restrict results to history recorded during this phase",
                    },
                    "feature": {"type": "string", "description": "Restrict results to a specific feature tag"},
                    "project": {"type": "string"},
                },
                "required": ["query"],
            },
        ),
        mcp_types.Tool(
            name="get_project_state",
            description=(
                "Get the live project state: PROJECT.md, tech stack, in-progress items, "
                "current session tags, and ALL active project entities (features, bugs, tasks, components). "
                "Call this at the start of a session to orient yourself and understand what is being built."
            ),
            inputSchema={
                "type": "object",
                "properties": {"project": {"type": "string"}},
            },
        ),
        mcp_types.Tool(
            name="get_recent_history",
            description=(
                "Return the last N prompt/response entries from the project's unified history. "
                "Filter by phase or feature to retrieve context for a specific area of work."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20, "description": "Max entries"},
                    "provider": {"type": "string", "description": "Filter by provider (claude, openai, …)"},
                    "phase": {"type": "string", "enum": _PHASES, "description": "Filter by phase"},
                    "feature": {"type": "string", "description": "Filter by feature tag"},
                    "project": {"type": "string"},
                },
            },
        ),
        mcp_types.Tool(
            name="get_roles",
            description="List available AI role prompt files for the project (architect, developer, QA, etc.).",
            inputSchema={
                "type": "object",
                "properties": {"project": {"type": "string"}},
            },
        ),
        mcp_types.Tool(
            name="get_commits",
            description=(
                "List recent commits with phase, feature, bug_ref metadata. "
                "Filter by phase or feature to see what changed for a specific area. "
                "Untagged commits (no phase) are marked as red flags."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 30},
                    "phase": {"type": "string", "enum": _PHASES, "description": "Filter commits by phase"},
                    "feature": {"type": "string", "description": "Filter commits by feature tag"},
                    "project": {"type": "string"},
                },
            },
        ),
        mcp_types.Tool(
            name="get_tagged_context",
            description=(
                "Return all events (prompts + commits) tagged with a specific phase or feature. "
                "Use this to get a complete picture of everything that happened during a phase "
                "or for a feature: decisions made, code committed, problems encountered. "
                "More precise than search_memory when you know the exact tag."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "phase": {"type": "string", "enum": _PHASES, "description": "Phase to retrieve context for"},
                    "feature": {"type": "string", "description": "Feature name to retrieve context for"},
                    "limit": {"type": "integer", "default": 30},
                    "project": {"type": "string"},
                },
            },
        ),
        mcp_types.Tool(
            name="get_session_tags",
            description=(
                "Get the currently active session tags: phase, feature, bug_ref. "
                "These are injected into every prompt as context. "
                "Use to understand what the user is currently working on."
            ),
            inputSchema={
                "type": "object",
                "properties": {"project": {"type": "string"}},
            },
        ),
        mcp_types.Tool(
            name="set_session_tags",
            description=(
                "Update the active session tags (phase, feature, bug_ref). "
                "Call this when you understand the current task to ensure proper tracking."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "enum": _PHASES,
                        "description": "Project phase",
                    },
                    "feature": {"type": "string", "description": "Feature name being worked on"},
                    "bug_ref": {"type": "string", "description": "Bug reference if fixing a bug"},
                    "project": {"type": "string"},
                },
            },
        ),
        mcp_types.Tool(
            name="commit_push",
            description=(
                "Commit all changed files and push to remote. "
                "Call at the end of a Cursor session to persist work. "
                "Auto-generates commit message. Logs to commit_log.jsonl with source='cursor_mcp'."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "message_hint": {"type": "string", "default": ""},
                    "project": {"type": "string"},
                },
            },
        ),
        mcp_types.Tool(
            name="create_entity",
            description=(
                "Create a new entity value (feature, bug, task, etc.) in the project's knowledge graph. "
                "Use this to track a new feature you are about to implement, a bug you discovered, "
                "or a task that needs to be done. The entity will appear in the Planner tab."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Category name: 'feature', 'bug', 'task', 'component', etc.",
                    },
                    "name": {
                        "type": "string",
                        "description": "Short name for this entity (e.g. 'auth-refactor', 'login-500-error')",
                    },
                    "description": {"type": "string", "description": "Optional description"},
                    "due_date":    {"type": "string", "description": "Optional due date (YYYY-MM-DD)"},
                    "project":     {"type": "string"},
                },
                "required": ["category", "name"],
            },
        ),
        mcp_types.Tool(
            name="sync_github_issues",
            description=(
                "Import GitHub issues as entity values into the project's Planner. "
                "Bug-labelled issues → bug category; enhancement/feature → feature; others → task. "
                "Idempotent: safe to run repeatedly."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "owner":   {"type": "string", "description": "GitHub repo owner (org or user)"},
                    "repo":    {"type": "string", "description": "GitHub repository name"},
                    "token":   {"type": "string", "description": "Optional GitHub personal access token"},
                    "state":   {"type": "string", "default": "open", "description": "Issue state: open, closed, all"},
                    "project": {"type": "string"},
                },
                "required": ["owner", "repo"],
            },
        ),
        mcp_types.Tool(
            name="list_work_items",
            description=(
                "List work items (features, bugs, tasks) for the project. "
                "Returns name, lifecycle_status, agent_status, acceptance_criteria preview, and due_date. "
                "Filter by category (feature/bug/task) and status (active/done/archived)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by category: feature, bug, task"},
                    "status":   {"type": "string", "default": "active", "description": "active, done, or archived"},
                    "project":  {"type": "string"},
                },
            },
        ),
        mcp_types.Tool(
            name="run_work_item_pipeline",
            description=(
                "Trigger the 4-agent pipeline (PM → Architect → Developer → Reviewer) for a work item. "
                "The pipeline writes acceptance_criteria and implementation_plan to the work item. "
                "Provide either work_item_id (UUID) or work_item_name + category to look it up. "
                "Returns the agent_status after triggering (pipeline runs in background)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "work_item_id":   {"type": "string", "description": "UUID of the work item"},
                    "work_item_name": {"type": "string", "description": "Name of the work item (alternative to ID)"},
                    "category":       {"type": "string", "description": "Category needed if using work_item_name"},
                    "project":        {"type": "string"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[mcp_types.TextContent]:
    try:
        result = await _dispatch(name, arguments)
        return [mcp_types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
    except httpx.HTTPStatusError as e:
        error = {"error": f"Backend {e.response.status_code}", "detail": e.response.text[:500]}
        return [mcp_types.TextContent(type="text", text=json.dumps(error))]
    except Exception as e:
        return [mcp_types.TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def _dispatch(name: str, args: dict) -> Any:
    project = args.get("project") or PROJECT

    if name == "search_memory":
        return await _post("/search/semantic", {
            "query": args["query"],
            "project": project,
            "limit": args.get("limit", 10),
            "source_types": args.get("source_types"),
            "language": args.get("language"),
            "doc_type": args.get("doc_type"),
            "file_path": args.get("file_path"),
            "chunk_types": args.get("chunk_types"),
            "phase": args.get("phase"),
            "feature": args.get("feature"),
        })

    elif name == "get_project_state":
        proj, tags = await asyncio.gather(
            _get(f"/projects/{project}"),
            _get("/history/session-tags", {"project": project}),
        )
        # Load entity summary, project facts, recent memory — each best-effort
        entities: dict = {}
        facts_data: dict = {}
        memory_data: dict = {}
        try:
            entities = await _get("/entities/summary", {"project": project})
        except Exception:
            pass
        try:
            facts_data = await _get("/work-items/facts", {"project": project})
        except Exception:
            pass
        try:
            memory_data = await _get("/work-items/memory-items", {"project": project, "scope": "session"})
        except Exception:
            pass

        # Build compact entity map: {category: [{name, status, event_count, commit_count, description, due_date}]}
        entity_map: dict = {}
        for cat in entities.get("summary", []):
            entity_map[cat["name"]] = [
                {
                    "name": v["name"],
                    "status": v["status"],
                    "description": v["description"],
                    "due_date": v["due_date"],
                    "event_count": v["event_count"],
                    "commit_count": v["commit_count"],
                }
                for v in cat.get("values", [])
            ]

        return {
            "project": project,
            "project_md": (proj.get("project_md") or "")[:3000],
            "description": proj.get("description", ""),
            "default_provider": proj.get("default_provider", "claude"),
            "active_tags": {
                "phase": tags.get("phase"),
                "feature": tags.get("feature"),
                "bug_ref": tags.get("bug_ref"),
            },
            "entities": entity_map,
            "project_facts": {
                f["fact_key"]: f["fact_value"]
                for f in facts_data.get("facts", [])
            },
            "recent_memory": [
                {
                    "scope": m["scope"],
                    "ref": m.get("scope_ref"),
                    "summary": (m.get("content") or "")[:500],
                }
                for m in memory_data.get("memory_items", [])[:3]
            ],
        }

    elif name == "get_recent_history":
        params: dict = {"project": project, "limit": str(args.get("limit", 20))}
        if args.get("provider"):
            params["provider"] = args["provider"]
        data = await _get("/history/chat", params)
        entries = data.get("entries", [])
        # Apply phase/feature filters client-side (history API doesn't support them yet)
        if args.get("phase"):
            entries = [e for e in entries if e.get("phase") == args["phase"]]
        if args.get("feature"):
            entries = [e for e in entries if e.get("feature") == args["feature"]]
        return {
            "entries": [
                {
                    "ts": e.get("ts", "")[:16],
                    "source": e.get("source", ""),
                    "provider": e.get("provider", ""),
                    "phase": e.get("phase"),
                    "feature": e.get("feature"),
                    "prompt": (e.get("user_input") or "")[:300],
                    "response_preview": (e.get("output") or "")[:200],
                }
                for e in entries
            ],
            "total": len(entries),
        }

    elif name == "get_roles":
        data = await _get("/prompts/", params={"project": project})
        prompts = data.get("prompts", [])
        roles = [p for p in prompts if "roles/" in p.get("path", "")]
        return {"roles": roles, "project": project}

    elif name == "get_commits":
        data = await _get("/history/commits", {
            "project": project,
            "limit": str(args.get("limit", 30)),
        })
        commits = data.get("commits", [])
        # Apply phase/feature filters
        if args.get("phase"):
            commits = [c for c in commits if c.get("phase") == args["phase"]]
        if args.get("feature"):
            commits = [c for c in commits if c.get("feature") == args["feature"]]
        untagged = [c for c in commits if not c.get("phase")]
        return {
            "commits": commits,
            "untagged_count": len(untagged),
            "source": data.get("source", "file"),
        }

    elif name == "get_tagged_context":
        params: dict = {"project": project, "limit": str(args.get("limit", 30))}
        if args.get("phase"):
            params["phase"] = args["phase"]
        if args.get("feature"):
            params["feature"] = args["feature"]
        return await _get("/search/tagged", params)

    elif name == "get_session_tags":
        return await _get("/history/session-tags", {"project": project})

    elif name == "set_session_tags":
        body = {
            "phase": args.get("phase") or None,
            "feature": args.get("feature") or None,
            "bug_ref": args.get("bug_ref") or None,
        }
        return await _put(f"/history/session-tags?project={project}", body)

    elif name == "commit_push":
        return await _post(f"/git/{project}/commit-push", {
            "message_hint": args.get("message_hint", "cursor session"),
            "provider": "claude",
            "skip_pull": False,
            "source": "cursor_mcp",
        })

    elif name == "create_entity":
        # Resolve category name → id via the categories list
        cats_data = await _get("/entities/categories", {"project": project})
        cat_name = args["category"]
        cat = next(
            (c for c in cats_data.get("categories", []) if c["name"] == cat_name),
            None,
        )
        if not cat:
            raise ValueError(
                f"Unknown category: '{cat_name}'. "
                f"Available: {[c['name'] for c in cats_data.get('categories', [])]}"
            )
        body: dict = {
            "category_id": cat["id"],
            "project": project,
            "name": args["name"],
            "description": args.get("description", ""),
        }
        if args.get("due_date"):
            body["due_date"] = args["due_date"]
        result = await _post("/entities/values", body)
        return {
            "id": result.get("id"),
            "name": result.get("name"),
            "category": cat_name,
            "project": project,
        }

    elif name == "sync_github_issues":
        import urllib.parse
        params = {
            "project": project,
            "owner": args["owner"],
            "repo": args["repo"],
        }
        if args.get("token"):
            params["token"] = args["token"]
        if args.get("state"):
            params["state"] = args["state"]
        qs = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
        return await _post(f"/entities/github-sync?{qs}", {})

    elif name == "list_work_items":
        import urllib.parse as _up
        params: dict = {"project": project}
        if args.get("category"):
            params["category"] = args["category"]
        if args.get("status"):
            params["status"] = args["status"]
        qs = "&".join(f"{k}={_up.quote(str(v))}" for k, v in params.items())
        data = await _get(f"/work-items?{qs}")
        items = data.get("work_items", [])
        return {
            "count": len(items),
            "work_items": [
                {
                    "id": wi["id"],
                    "name": wi["name"],
                    "category": wi.get("category_name"),
                    "lifecycle": wi.get("lifecycle_status", "idea"),
                    "status": wi.get("status", "active"),
                    "agent_status": wi.get("agent_status"),
                    "due_date": wi.get("due_date"),
                    "criteria_preview": (wi.get("acceptance_criteria") or "")[:120],
                }
                for wi in items
            ],
        }

    elif name == "run_work_item_pipeline":
        import urllib.parse as _up
        wi_id = args.get("work_item_id")
        if not wi_id:
            # Look up by name + category
            cat = args.get("category", "feature")
            wname = args.get("work_item_name", "")
            if not wname:
                raise ValueError("Provide work_item_id or work_item_name + category")
            data = await _get(f"/work-items?project={_up.quote(project)}&category={_up.quote(cat)}")
            matches = [w for w in data.get("work_items", []) if w["name"].lower() == wname.lower()]
            if not matches:
                raise ValueError(f"Work item '{wname}' not found in {cat}")
            wi_id = matches[0]["id"]
        result = await _post(f"/work-items/{wi_id}/run-pipeline?project={_up.quote(project)}", {})
        return {"work_item_id": wi_id, "status": result.get("status"), "project": project}

    else:
        raise ValueError(f"Unknown tool: {name}")


# ── Entry point ────────────────────────────────────────────────────────────────

async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
