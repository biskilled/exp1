"""
aicli MCP Server — exposes the 5-layer project memory as LLM tools.

Run: python3.12 ui/mcp_server.py [--project aicli] [--backend http://localhost:8000]

Claude CLI and Cursor register this server via their settings files.
All tools call the FastAPI backend via HTTP — no direct DB access.

Tools:
    search_memory        — semantic search across history, roles, commits, docs
    get_project_state    — PROJECT.md + active work items + project facts
    get_recent_history   — last N prompt/response entries for the project
    get_roles            — list available AI role prompt files
    get_commits          — list commits with phase/feature tags (untagged = red flag)
    get_session_tags     — active session tags (phase, feature, bug_ref)
    set_session_tags     — update active session tags
    commit_push          — commit + push from Cursor; logs to commit_log.jsonl
    get_db_schema        — complete database schema (mem_mrr_*, mem_work_items, pr_graph_*)
    create_entity        — create a new work item (feature/bug/task/use_case) pending approval
    list_work_items      — list mem_work_items filtered by wi_type and user_status
    run_work_item_pipeline — run Haiku AI summarise on a use case (rewrites summary + reorders children)
    get_item_by_number   — resolve a wi_id ref (e.g. BU0001, FE0002) to the full work item
    search_work_items    — semantic search over embedded (approved) work items

Database:  mem_work_items — single table for use_case/feature/bug/task/requirement
  wi_type:    use_case | feature | bug | task | requirement
  user_status: open | pending | in-progress | review | blocked | done
  approved_at IS NOT NULL → item is approved (has wi_id like BU0001, FE0002)
  embedding IS NOT NULL  → item is embedded (approved items only)
  wi_parent_id           → links features/bugs/tasks to their parent use_case
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
                    "entity_name": {
                        "type": "string",
                        "description": "Restrict results to embeddings tagged with this entity value name (e.g. 'auth', 'UI dropbox'). Tags must be backfilled via /memory.",
                    },
                    "entity_category": {
                        "type": "string",
                        "description": "Restrict results to embeddings tagged with this entity category (e.g. 'bug', 'feature', 'task').",
                    },
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
                "Update the active session tags. Call this when you understand the current task "
                "to ensure prompts and commits are correctly tagged. "
                "phase is required. feature and bug_ref are optional. "
                "extra accepts any key:value pairs from: task, component, doc_type, design, decision, meeting, customer."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "phase": {
                        "type": "string",
                        "enum": _PHASES,
                        "description": "Project phase (required)",
                    },
                    "feature": {"type": "string", "description": "Feature slug being worked on (e.g. work-items-ui)"},
                    "bug_ref": {"type": "string", "description": "Bug slug if fixing a bug (e.g. login-500)"},
                    "extra": {
                        "type": "object",
                        "description": "Additional tags: {task, component, doc_type, design, decision, meeting, customer}",
                    },
                    "project": {"type": "string"},
                },
                "required": ["phase"],
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
                "Create a new work item (feature, bug, task, use_case, requirement) in mem_work_items. "
                "Created items are unapproved (no wi_id yet) until a human approves them in the UI. "
                "Approved items get a permanent ID like BU0001 (bug), FE0001 (feature), UC0001 (use_case). "
                "Link child items to a parent use_case by providing parent_id (UUID of the use_case)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "wi_type: 'feature', 'bug', 'task', 'use_case', or 'requirement'",
                    },
                    "name": {
                        "type": "string",
                        "description": "Short name for this work item (e.g. 'auth-refactor', 'login-500-error')",
                    },
                    "description": {"type": "string", "description": "Optional summary / description"},
                    "due_date":    {"type": "string", "description": "Optional due date (YYYY-MM-DD)"},
                    "parent_id":   {"type": "string", "description": "Optional UUID of parent use_case (for feature/bug/task children)"},
                    "project":     {"type": "string"},
                },
                "required": ["category", "name"],
            },
        ),
        mcp_types.Tool(
            name="list_work_items",
            description=(
                "List work items from mem_work_items for the project. "
                "Returns wi_id (e.g. BU0001), name, wi_type, user_status, is_approved, parent_wi_id, "
                "updated_at, and summary preview. "
                "Filter by category (wi_type) and status (active/done/archived). "
                "approved=True means item has been human-reviewed; embedding exists for approved items."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by wi_type: use_case, feature, bug, task, requirement"},
                    "status":   {"type": "string", "default": "active", "description": "active (not done), done, or archived (deleted)"},
                    "project":  {"type": "string"},
                },
            },
        ),
        mcp_types.Tool(
            name="run_work_item_pipeline",
            description=(
                "Run the 4-agent pipeline (PM → Architect → Developer → Reviewer) on an approved open "
                "work item (feature/bug/task) that is under an approved use case. "
                "The pipeline writes acceptance_criteria and implementation_plan back to the item. "
                "Requirements: item must be approved (has wi_id like BU0001), user_status != 'done', "
                "and parent use_case must also be approved. Pipeline runs in background."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "work_item_id":   {"type": "string", "description": "UUID of the approved open work item (feature/bug/task)"},
                    "work_item_name": {"type": "string", "description": "Name of the work item (alternative to ID)"},
                    "category":       {"type": "string", "description": "wi_type to filter by when looking up by name (default: feature)"},
                    "project":        {"type": "string"},
                },
            },
        ),
        mcp_types.Tool(
            name="get_item_by_number",
            description=(
                "Look up a work item by its approved wi_id (e.g. BU0001, FE0002, UC0001, TA0003). "
                "Use this when a user or another AI references an item by its short ID. "
                "Returns full item details: name, wi_type, user_status, is_approved, parent_wi_id, summary, due_date."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "seq_num":  {"type": "string", "description": "The wi_id string, e.g. 'BU0001' or 'FE0002' (leading # is stripped automatically)"},
                    "project":  {"type": "string"},
                },
                "required": ["seq_num"],
            },
        ),
        mcp_types.Tool(
            name="get_db_schema",
            description=(
                "Return the complete database table schema for this project. "
                "Use this when you need to write SQL queries or understand the data model. "
                "Tables follow naming convention: mng_ (global), mem_mrr_ (mirror/raw), "
                "mem_work_items (entities: use_case/feature/bug/task), pr_ (graph workflows)."
            ),
            inputSchema={
                "type": "object",
                "properties": {"project": {"type": "string"}},
            },
        ),
        mcp_types.Tool(
            name="search_facts",
            description=(
                "Semantic search over approved, embedded work items in mem_work_items. "
                "Only approved items (wi_id IS NOT NULL, embedding IS NOT NULL) are searched. "
                "For architectural facts use search_memory with doc_type='role' or source_types=['commit']."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query":   {"type": "string", "description": "Natural language query"},
                    "limit":   {"type": "integer", "default": 10},
                    "project": {"type": "string"},
                },
                "required": ["query"],
            },
        ),
        mcp_types.Tool(
            name="search_work_items",
            description=(
                "Semantic search over work items (features, bugs, tasks). "
                "Returns matching items ranked by cosine similarity to the query. "
                "Use to find relevant features/bugs before starting implementation, "
                "or to discover related work items for a given topic."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query":    {"type": "string", "description": "Natural language query"},
                    "limit":    {"type": "integer", "default": 10},
                    "category": {"type": "string", "description": "Filter by category: feature, bug, task"},
                    "project":  {"type": "string"},
                },
                "required": ["query"],
            },
        ),
        mcp_types.Tool(
            name="get_tag_context",
            description=(
                "Return comprehensive context for a specific tag (feature, bug, or task): "
                "tag properties (description, category), recent AI-layer events tagged with it, "
                "mirroring source rows (prompts/commits/items), relations to other tags, "
                "and work items referencing this tag. "
                "Use before starting work on a feature — the PM agent calls this to orient on the full history."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "tag_name": {"type": "string", "description": "Tag name, e.g. 'auth', 'retry-dashboard'"},
                    "limit":    {"type": "integer", "default": 20, "description": "Max events/sources to return"},
                    "project":  {"type": "string"},
                },
                "required": ["tag_name"],
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
            "entity_name": args.get("entity_name"),
            "entity_category": args.get("entity_category"),
        })

    elif name == "get_project_state":
        proj, tags = await asyncio.gather(
            _get(f"/projects/{project}"),
            _get("/history/session-tags", {"project": project}),
        )
        # Load work items from mem_work_items — best-effort
        work_items_data: dict = {}
        try:
            work_items_data = await _get(f"/wi/{project}")
        except Exception:
            pass

        # Build compact work items map: {wi_type: [{wi_id, name, is_approved, lifecycle, parent_wi_id, summary_preview}]}
        # Only include non-deleted, non-done items (active backlog)
        wi_map: dict = {}
        for wi in work_items_data.get("items", []):
            if wi.get("deleted_at"):
                continue
            cat = wi.get("wi_type", "other")
            wi_map.setdefault(cat, []).append({
                "wi_id": wi.get("wi_id"),          # BU0001, FE0002, or None if unapproved
                "name": wi["name"],
                "is_approved": wi.get("approved_at") is not None,
                "lifecycle": wi.get("user_status", "open"),
                "parent_wi_id": wi.get("wi_parent_wi_id"),
                "summary": (wi.get("summary") or "")[:120],
                "due_date": wi.get("due_date"),
                "updated_at": wi.get("updated_at"),
            })

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
            "work_items": wi_map,
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
        # Map category → wi_type (mem_work_items)
        _type_map = {
            "feature": "feature", "bug": "bug", "task": "task",
            "use_case": "use_case", "requirement": "requirement",
            "component": "task",   # component → task (closest match)
        }
        cat_name = args["category"]
        wi_type = _type_map.get(cat_name.lower(), cat_name.lower())
        valid_types = {"use_case", "feature", "bug", "task", "requirement"}
        if wi_type not in valid_types:
            raise ValueError(
                f"Unknown category: '{cat_name}'. Valid values: {sorted(valid_types)}"
            )
        body: dict = {
            "name": args["name"],
            "wi_type": wi_type,
            "summary": args.get("description", ""),
        }
        if args.get("wi_parent_id") or args.get("parent_id"):
            body["wi_parent_id"] = args.get("wi_parent_id") or args.get("parent_id")
        result = await _post(f"/wi/{project}", body)
        return {
            "id": result.get("id"),
            "wi_id": result.get("wi_id"),          # None until approved by human
            "name": result.get("name"),
            "category": wi_type,
            "is_approved": False,                   # new items always unapproved
            "project": project,
            "note": "Item created as unapproved. Approve in the Work Items UI to assign a wi_id (BU0001, etc.).",
        }

    elif name == "sync_github_issues":
        return {
            "error": "sync_github_issues is not implemented in the current backend.",
            "suggestion": "Import issues manually via POST /wi/{project} or use the Work Items classify pipeline.",
        }

    elif name == "list_work_items":
        # Fetch from /wi/{project} (mem_work_items table)
        params: dict = {}
        if args.get("category"):
            params["wi_type"] = args["category"]   # category → wi_type filter
        data = await _get(f"/wi/{project}", params)
        items = data.get("items", [])

        # Apply status filter client-side
        status_filter = args.get("status", "active")
        if status_filter == "active":
            items = [i for i in items if not i.get("deleted_at") and i.get("user_status") != "done"]
        elif status_filter == "done":
            items = [i for i in items if i.get("user_status") == "done" and not i.get("deleted_at")]
        elif status_filter == "archived":
            items = [i for i in items if i.get("deleted_at")]

        return {
            "count": len(items),
            "work_items": [
                {
                    "id": wi["id"],
                    "wi_id": wi.get("wi_id"),              # BU0001 / FE0002 / None
                    "name": wi["name"],
                    "category": wi.get("wi_type"),         # use_case | feature | bug | task
                    "is_approved": wi.get("approved_at") is not None,
                    "lifecycle": wi.get("user_status", "open"),
                    "parent_id": wi.get("wi_parent_id"),
                    "parent_wi_id": wi.get("wi_parent_wi_id"),
                    "due_date": wi.get("due_date"),
                    "updated_at": wi.get("updated_at"),
                    "summary": (wi.get("summary") or "")[:200],
                }
                for wi in items
            ],
        }

    elif name == "run_work_item_pipeline":
        # Triggers 4-agent pipeline (PM→Architect→Developer→Reviewer) on an approved open work item.
        # Item must be approved + open; if it has a parent use_case, that parent must also be approved.
        wi_uuid = args.get("work_item_id")
        if not wi_uuid:
            wname = args.get("work_item_name", "")
            cat = args.get("category", "feature")
            if not wname:
                raise ValueError("Provide work_item_id (UUID) or work_item_name")
            data = await _get(f"/wi/{project}", {"wi_type": cat})
            matches = [w for w in data.get("items", []) if w["name"].lower() == wname.lower()]
            if not matches:
                raise ValueError(f"Work item '{wname}' not found (wi_type={cat}). Try list_work_items first.")
            wi_uuid = matches[0]["id"]
        result = await _post(f"/wi/{project}/{wi_uuid}/run-pipeline", {})
        return {
            "work_item_id": wi_uuid,
            "wi_id": result.get("wi_id"),
            "pipeline_status": result.get("pipeline_status"),
            "message": result.get("message"),
            "project": project,
        }

    elif name == "get_item_by_number":
        # Look up by wi_id string (e.g. BU0001, FE0002, UC0001)
        ref = str(args["seq_num"]).lstrip("#").upper()
        data = await _get(f"/wi/{project}")
        items = data.get("items", [])
        # Match by wi_id (approved items) or fall back to name substring
        wi = next((i for i in items if (i.get("wi_id") or "").upper() == ref), None)
        if not wi:
            raise ValueError(
                f"Work item '{ref}' not found. "
                f"Use wi_id like BU0001, FE0002, UC0001, TA0001. "
                f"Only approved items have a wi_id — check list_work_items first."
            )
        return {
            "id": wi.get("id"),
            "wi_id": wi.get("wi_id"),
            "name": wi.get("name"),
            "category": wi.get("wi_type"),
            "is_approved": wi.get("approved_at") is not None,
            "lifecycle": wi.get("user_status", "open"),
            "parent_id": wi.get("wi_parent_id"),
            "parent_wi_id": wi.get("wi_parent_wi_id"),
            "summary": wi.get("summary", ""),
            "acceptance_criteria": wi.get("acceptance_criteria", ""),
            "implementation_plan": wi.get("implementation_plan", ""),
            "pipeline_status": wi.get("pipeline_status"),
            "due_date": wi.get("due_date"),
            "created_at": wi.get("created_at"),
            "updated_at": wi.get("updated_at"),
            "completed_at": wi.get("completed_at"),
        }

    elif name == "search_facts":
        # Semantic search over embedded (approved) work items in mem_work_items
        return await _post("/search/semantic", {
            "query": args["query"],
            "project": project,
            "limit": args.get("limit", 10),
            "source_types": ["work_item"],
        })

    elif name == "search_work_items":
        # Semantic search over approved (embedded) work items via pgvector cosine similarity
        # Note: only approved items with embedding IS NOT NULL are searchable
        result = await _post("/search/semantic", {
            "query": args["query"],
            "project": project,
            "limit": args.get("limit", 10),
            "source_types": ["work_item"],
        })
        hits = result.get("results", [])
        # Optionally filter by wi_type (category) client-side
        if args.get("category"):
            cat = args["category"]
            hits = [h for h in hits if h.get("source_type") == cat or h.get("wi_type") == cat]
        return {"results": hits, "count": len(hits), "note": "Only approved (embedded) work items are searchable."}

    elif name == "get_tag_context":
        import urllib.parse as _up
        params = {
            "tag_name": args["tag_name"],
            "project": project,
            "limit": str(args.get("limit", 20)),
        }
        qs = "&".join(f"{k}={_up.quote(str(v))}" for k, v in params.items())
        return await _get(f"/tags/context?{qs}")

    elif name == "get_db_schema":
        p = project
        return {
            "naming_convention": {
                "mng_TABLE": "Global/shared tables (users, billing, roles, system prompts)",
                "mem_mrr_TABLE": "Mirroring layer — raw source data as-is (prompts, commits, items, messages)",
                "mem_ai_TABLE": "AI/embedding layer — digests, embeddings, facts, work items",
                "mem_work_items": "Single source of truth for use cases, features, bugs, tasks",
                "pr_TABLE": "Graph workflow tables (pr_graph_*)",
                "filter": "Most tables use project_id INT FK for isolation",
            },
            "global_tables": {
                "mng_users": {
                    "purpose": "User accounts, roles, billing balances",
                    "key_columns": ["id VARCHAR(36) PK", "email UNIQUE", "role (free/paid/admin)",
                                    "balance_added_usd", "balance_used_usd"],
                },
                "mng_agent_roles": {
                    "purpose": "LLM agent role definitions (system_prompt, model, provider, tools list)",
                    "key_columns": ["id SERIAL PK", "client_id INT", "project TEXT", "name TEXT",
                                    "system_prompt TEXT", "provider TEXT", "model TEXT",
                                    "tools JSONB", "react BOOLEAN", "max_iterations INT"],
                },
                "mng_system_roles": {
                    "purpose": "Memory pipeline prompts editable from UI (commit_digest, prompt_batch_digest, etc.)",
                    "key_columns": ["id SERIAL PK", "client_id INT", "name TEXT", "content TEXT", "is_active BOOLEAN"],
                },
            },
            "work_items_table": {
                "mem_work_items": {
                    "purpose": "Single source of truth for all classified work (use cases, features, bugs, tasks, policies)",
                    "key_columns": [
                        "wi_id UUID PK", "project_id INT FK", "name TEXT", "wi_type TEXT",
                        "summary TEXT", "user_status TEXT", "wi_parent_id UUID FK self",
                        "due_date DATE", "score_importance FLOAT",
                        "completed_at TIMESTAMPTZ", "deleted_at TIMESTAMPTZ",
                        "created_at TIMESTAMPTZ", "updated_at TIMESTAMPTZ",
                    ],
                    "filter": "WHERE project_id=%s AND deleted_at IS NULL",
                },
            },
            "mirroring_tables": {
                "mem_mrr_prompts": {
                    "purpose": "Raw prompt/response log from all AI sessions (claude_cli, cursor, aicli UI)",
                    "key_columns": ["id UUID PK", "client_id INT", "project_id INT FK projects", "session_id TEXT",
                                    "prompt TEXT", "response TEXT", "phase TEXT", "source TEXT",
                                    "ai_tags TEXT (NULL|approved|ignored)", "metadata JSONB"],
                    "filter": "WHERE project_id=%s",
                },
                "mem_mrr_commits": {
                    "purpose": "Git commits with diff stats and session links",
                    "key_columns": ["commit_hash VARCHAR(40) PK", "client_id INT", "project_id INT FK projects",
                                    "commit_msg TEXT", "summary TEXT", "diff_summary TEXT",
                                    "tags JSONB", "session_id TEXT", "created_at TIMESTAMPTZ"],
                    "filter": "WHERE project_id=%s",
                },
            },
            "ai_layer_tables": {
                "mem_ai_project_facts": {
                    "purpose": "Durable extracted facts; temporal validity (valid_until NULL = current). Searchable via embedding.",
                    "key_columns": ["id UUID PK", "client_id INT", "project_id INT FK projects",
                                    "fact_key TEXT", "fact_value TEXT", "category TEXT",
                                    "embedding VECTOR(1536)", "valid_from TIMESTAMPTZ", "valid_until TIMESTAMPTZ",
                                    "UNIQUE(project_id, fact_key) WHERE valid_until IS NULL"],
                    "filter": "WHERE project_id=%s AND valid_until IS NULL",
                    "search_endpoint": "POST /search/semantic with source_types=['work_item']",
                },
            },
            "graph_tables": {
                "pr_graph_workflows": {"purpose": "DAG workflow definitions"},
                "pr_graph_nodes": {"purpose": "Steps within a workflow"},
                "pr_graph_edges": {"purpose": "Directed connections between nodes"},
                "pr_graph_runs": {"purpose": "Workflow execution instances"},
                "pr_graph_node_results": {"purpose": "Per-node output within a run"},
                "pr_seq_counters": {
                    "purpose": "Atomic sequential number counter per (project_id, category)",
                    "key_columns": ["project_id INT FK projects", "category TEXT",
                                    "next_val INT NOT NULL DEFAULT 1",
                                    "PRIMARY KEY (project_id, category)"],
                    "filter": "WHERE project_id=%s",
                },
            },
        }

    else:
        raise ValueError(f"Unknown tool: {name}")


# ── Entry point ────────────────────────────────────────────────────────────────

async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
