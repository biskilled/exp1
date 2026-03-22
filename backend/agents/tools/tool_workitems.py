"""
tool_workitems.py — Agent tools for reading and creating work items.

Provides direct DB access for:
  - list_work_items: query pr_work_items JOIN mng_entity_values
  - create_work_item: insert a new work item + entity value

Assigned to Product Manager and QA Engineer roles so they can triage
and capture findings without leaving the agentic loop.
"""
from __future__ import annotations

import json
import logging

log = logging.getLogger(__name__)

# ── Tool definitions (Claude tool_use JSON schema format) ─────────────────────

WORKITEM_TOOL_DEFS: list[dict] = [
    {
        "name": "list_work_items",
        "description": "List active work items (features, bugs, tasks) for the project.",
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
        "description": "Create a new work item (feature, bug, or task) for the project.",
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

# ── Handlers ──────────────────────────────────────────────────────────────────

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
                if category:
                    cur.execute(
                        """SELECT ev.name, ec.name, ev.lifecycle_status, ev.description,
                                  ev.seq_num
                           FROM pr_work_items wi
                           JOIN mng_entity_values ev ON ev.id = wi.entity_value_id
                           JOIN mng_entity_categories ec ON ec.id = ev.category_id
                           WHERE wi.client_id=1 AND wi.project=%s
                             AND ec.name ILIKE %s AND ev.status=%s
                           ORDER BY ev.seq_num DESC LIMIT 50""",
                        (project, f"%{category}%", status),
                    )
                else:
                    cur.execute(
                        """SELECT ev.name, ec.name, ev.lifecycle_status, ev.description,
                                  ev.seq_num
                           FROM pr_work_items wi
                           JOIN mng_entity_values ev ON ev.id = wi.entity_value_id
                           JOIN mng_entity_categories ec ON ec.id = ev.category_id
                           WHERE wi.client_id=1 AND wi.project=%s AND ev.status=%s
                           ORDER BY ev.seq_num DESC LIMIT 50""",
                        (project, status),
                    )
                rows = cur.fetchall()
    except Exception as e:
        return f"Error fetching work items: {e}"

    if not rows:
        return f"No {status} work items found for project '{project}'."

    lines = []
    for row in rows:
        ref  = f"#{row[4]}" if row[4] else ""
        desc = (row[3] or "")[:80]
        lines.append(f"{ref} [{row[1]}] {row[0]} ({row[2]}) — {desc}")
    return "\n".join(lines)


def _handle_create_work_item(args: dict) -> str:
    project       = args.get("project") or _get_active_project()
    name          = args.get("name", "").strip()
    category_name = args.get("category_name", "task").strip()
    description   = args.get("description", "")

    if not name:
        return "Error: 'name' is required."

    try:
        from core.database import db
        if not db.is_available():
            return "Database not available."
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Find or create category
                cur.execute(
                    """SELECT id FROM mng_entity_categories
                       WHERE client_id=1 AND name ILIKE %s LIMIT 1""",
                    (category_name,),
                )
                cat_row = cur.fetchone()
                if not cat_row:
                    cur.execute(
                        """INSERT INTO mng_entity_categories (client_id, name)
                           VALUES (1, %s) RETURNING id""",
                        (category_name,),
                    )
                    cat_row = cur.fetchone()
                category_id = cat_row[0]

                # Create entity value
                cur.execute(
                    """INSERT INTO mng_entity_values
                           (client_id, category_id, name, description, status)
                       VALUES (1, %s, %s, %s, 'active')
                       ON CONFLICT DO NOTHING
                       RETURNING id, seq_num""",
                    (category_id, name, description),
                )
                ev_row = cur.fetchone()
                if not ev_row:
                    return f"Work item '{name}' already exists."
                ev_id, seq_num = ev_row

                # Create work item link
                cur.execute(
                    """INSERT INTO pr_work_items
                           (client_id, project, entity_value_id)
                       VALUES (1, %s, %s)
                       ON CONFLICT DO NOTHING""",
                    (project, ev_id),
                )
            conn.commit()
        ref = f"#{seq_num}" if seq_num else ""
        return f"Created {category_name} {ref}: '{name}'"
    except Exception as e:
        return f"Error creating work item: {e}"


# ── Handler map ───────────────────────────────────────────────────────────────

WORKITEM_HANDLERS: dict[str, callable] = {
    "list_work_items": _handle_list_work_items,
    "create_work_item": _handle_create_work_item,
}
