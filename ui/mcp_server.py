"""
aicli MCP Server — exposes the 5-layer project memory as LLM tools.

Run: python3.12 ui/mcp_server.py [--project aicli] [--backend http://localhost:8000]

Claude CLI, Cursor (MCP-enabled), and aicli CLI register this via aicli.yaml mcp.servers.
All tools call the FastAPI backend via HTTP — no direct DB access here.

Tools:
    search_memory        — semantic search across history + roles + node_outputs
    get_project_state    — live PROJECT.md + recent history + in_progress items
    get_roles            — list available role files with descriptions
    get_workflow_state   — current run status + node outputs for a graph run
    create_task          — create a task (for LLM to track its own work)
    get_tasks            — list open tasks
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
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    print("ERROR: mcp package not installed. Run: pip install mcp>=1.0.0", file=sys.stderr)
    sys.exit(1)

# ── Config from env / CLI args ────────────────────────────────────────────────

parser = argparse.ArgumentParser(description="aicli MCP Server")
parser.add_argument("--project", default=os.environ.get("ACTIVE_PROJECT", "aicli"))
parser.add_argument("--backend", default=os.environ.get("BACKEND_URL", "http://localhost:8000"))
args, _ = parser.parse_known_args()

BACKEND = args.backend.rstrip("/")
PROJECT = args.project

# ── HTTP helpers ──────────────────────────────────────────────────────────────

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


# ── MCP Server ────────────────────────────────────────────────────────────────

server = Server("aicli-memory")


@server.list_tools()
async def list_tools() -> list[mcp_types.Tool]:
    return [
        mcp_types.Tool(
            name="search_memory",
            description="Semantic search across project history, role files, node outputs, and decisions.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language search query"},
                    "limit": {"type": "integer", "default": 10, "description": "Max results to return"},
                    "source_types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by source: history, role, node_output, project_md, decision",
                    },
                },
                "required": ["query"],
            },
        ),
        mcp_types.Tool(
            name="get_project_state",
            description="Get the current project state: PROJECT.md content, recent history, in-progress items.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name (uses active project if omitted)"},
                },
            },
        ),
        mcp_types.Tool(
            name="get_roles",
            description="List available AI role files (agent prompts) for the project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Project name"},
                },
            },
        ),
        mcp_types.Tool(
            name="get_workflow_state",
            description="Get the current status and node outputs of a graph workflow run.",
            inputSchema={
                "type": "object",
                "properties": {
                    "run_id": {"type": "string", "description": "Graph run ID returned by startRun"},
                },
                "required": ["run_id"],
            },
        ),
        mcp_types.Tool(
            name="create_task",
            description="Create a task in the project entity tracker.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title"},
                    "description": {"type": "string", "default": "", "description": "Task details"},
                    "priority": {"type": "string", "default": "medium", "enum": ["low", "medium", "high"]},
                    "project": {"type": "string", "description": "Project name"},
                },
                "required": ["title"],
            },
        ),
        mcp_types.Tool(
            name="get_tasks",
            description="List open tasks for the project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string"},
                    "status": {"type": "string", "default": "open"},
                    "limit": {"type": "integer", "default": 20},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[mcp_types.TextContent]:
    try:
        result = await _dispatch(name, arguments)
        return [mcp_types.TextContent(type="text", text=json.dumps(result, indent=2))]
    except httpx.HTTPStatusError as e:
        error = {"error": f"Backend returned {e.response.status_code}", "detail": e.response.text}
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
        })

    elif name == "get_project_state":
        data = await _get(f"/projects/{project}")
        # Return a compact summary
        return {
            "project": project,
            "project_md": (data.get("project_md") or "")[:3000],
            "description": data.get("description", ""),
            "default_provider": data.get("default_provider", "claude"),
        }

    elif name == "get_roles":
        data = await _get("/prompts/", params={"project": project})
        prompts = data.get("prompts", [])
        roles = [p for p in prompts if p["path"].startswith("roles/")]
        return {"roles": roles, "project": project}

    elif name == "get_workflow_state":
        run_id = args["run_id"]
        return await _get(f"/graph-workflows/runs/{run_id}")

    elif name == "create_task":
        return await _post("/entities/tasks", {
            "title": args["title"],
            "description": args.get("description", ""),
            "priority": args.get("priority", "medium"),
            "project": project,
        })

    elif name == "get_tasks":
        params = {"project": project}
        if args.get("status"):
            params["status"] = args["status"]
        if args.get("limit"):
            params["limit"] = str(args["limit"])
        return await _get("/entities/tasks", params=params)

    else:
        raise ValueError(f"Unknown tool: {name}")


# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
