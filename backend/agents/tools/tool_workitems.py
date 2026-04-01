"""
tool_workitems.py — Agent tools for reading and creating work items.

Provides direct DB access for:
  - list_work_items : query mem_ai_work_items (with optional category/status filter)
  - create_work_item: insert a new work item into mem_ai_work_items

Work item → tag linking now happens automatically via match_work_item_to_tags()
in memory_tagging.py, called from route_work_items.py. This tool only inserts
the mem_ai_work_items row; planner_tags management is outside the agent loop.

Assigned to Product Manager and QA Engineer roles so they can triage and
capture findings without leaving the agentic loop.
"""
from __future__ import annotations

import json
import logging

log = logging.getLogger(__name__)

# ── Tool definitions ───────────────────────────────────────────────────────────

WORKITEM_TOOL_DEFS: list[dict] = [
    {
        "name": "list_work_items",
        "description": (
            "List work items (features, bugs, tasks) for the project. "
            "Shows name, category, lifecycle, status, and acceptance criteria preview."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project":  {"type": "string", "description": "Project name"},
                "category": {"type": "string", "description": "Filter: feature | bug | task (optional)"},
                "status":   {"type": "string", "description": "Filter: active | done | archived (default: active)"},
            },
        },
    },
    {
        "name": "create_work_item",
        "description": (
            "Create a new work item (feature, bug, or task) for the project. "
            "Inserts a row into mem_ai_work_items; tag linking is handled automatically "
            "by the memory pipeline."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project":       {"type": "string", "description": "Project name"},
                "name":          {"type": "string", "description": "Short name for the work item"},
                "category_name": {"type": "string", "description": "Category: feature | bug | task"},
                "description":   {"type": "string", "description": "Optional description"},
            },
            "required": ["name", "category_name"],
        },
    },
]

# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_active_project() -> str:
    import os
    from pathlib import Path
    project = os.environ.get("ACTIVE_PROJECT", "")
    if not project:
        state_path = Path.home() / ".aicli" / "session_state.json"
        if state_path.exists():
            try:
                project = json.loads(state_path.read_text()).get("project", "")
            except Exception:
                pass
    return project or "aicli"

# ── Handlers ───────────────────────────────────────────────────────────────────

def _handle_list_work_items(args: dict) -> str:
    project  = args.get("project") or _get_active_project()
    category = args.get("category")
    status   = args.get("status", "active")

    try:
        from core.database import db
        if not db.is_available():
            return "Database not available."
        with db.conn() as conn:
            with conn.cursor() as cur:
                where = "w.client_id=1 AND w.project=%s AND w.status=%s"
                params: list = [project, status]
                if category:
                    where += " AND w.category_name ILIKE %s"
                    params.append(f"%{category}%")
                params.append(50)
                cur.execute(
                    f"""SELECT w.seq_num, w.name, w.category_name, w.lifecycle_status,
                               w.status, w.description, w.acceptance_criteria, w.agent_status
                        FROM mem_ai_work_items w
                        WHERE {where}
                        ORDER BY w.seq_num DESC NULLS LAST, w.created_at DESC
                        LIMIT %s""",
                    params,
                )
                rows = cur.fetchall()
    except Exception as e:
        return f"Error fetching work items: {e}"

    if not rows:
        return f"No {status} work items found for project '{project}'."

    lines = []
    for r in rows:
        ref    = f"#{r[0]}" if r[0] else "   "
        desc   = (r[5] or "")[:80]
        ac     = (r[6] or "")[:100]
        agent  = f" [{r[7]}]" if r[7] else ""
        lines.append(f"{ref} [{r[2]}] {r[1]} ({r[3]}){agent}")
        if desc:
            lines.append(f"      {desc}")
        if ac:
            lines.append(f"      AC: {ac}")
    return "\n".join(lines)


def _handle_create_work_item(args: dict) -> str:
    project       = args.get("project") or _get_active_project()
    name          = args.get("name", "").strip()
    category_name = args.get("category", args.get("category_name", "task")).strip().lower()
    description   = args.get("description", "").strip()
    parent_id     = args.get("parent_id")

    if not name:
        return "Error: work item name is required"

    try:
        from core.database import db
        if not db.is_available():
            return "Database not available."
        with db.conn() as conn:
            with conn.cursor() as cur:
                # ── Insert into mem_ai_work_items (AI-generated items) ────
                cur.execute(
                    """INSERT INTO mem_ai_work_items
                           (client_id, project, name, category_name, description, status)
                       VALUES (%s, %s, %s, %s, %s, 'open')
                       RETURNING id, seq_num""",
                    (1, project, name, category_name, description or None),
                )
                row = cur.fetchone()
                wi_id  = str(row[0])
                seq_num = row[1]
                conn.commit()

        ref = f"#{seq_num}" if seq_num else ""
        return f"Created work item {ref}: {name} (id: {wi_id})"
    except Exception as e:
        return f"Error creating work item: {e}"


# ── Handler map ────────────────────────────────────────────────────────────────

WORKITEM_HANDLERS: dict[str, callable] = {
    "list_work_items":  _handle_list_work_items,
    "create_work_item": _handle_create_work_item,
}
