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
                        """SELECT t.name, tc.name AS cat_name, t.lifecycle, tm.description, t.seq_num
                           FROM pr_work_items wi
                           JOIN planner_tags t ON t.id = wi.tag_id
                           LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
                           LEFT JOIN planner_tags_meta tm ON tm.tag_id = t.id
                           WHERE wi.client_id=1 AND wi.project=%s
                             AND tc.name ILIKE %s AND t.status=%s
                           ORDER BY t.seq_num DESC NULLS LAST LIMIT 50""",
                        (project, f"%{category}%", status),
                    )
                else:
                    cur.execute(
                        """SELECT t.name, tc.name AS cat_name, t.lifecycle, tm.description, t.seq_num
                           FROM pr_work_items wi
                           JOIN planner_tags t ON t.id = wi.tag_id
                           LEFT JOIN mng_tags_categories tc ON tc.id = t.category_id
                           LEFT JOIN planner_tags_meta tm ON tm.tag_id = t.id
                           WHERE wi.client_id=1 AND wi.project=%s AND t.status=%s
                           ORDER BY t.seq_num DESC NULLS LAST LIMIT 50""",
                        (project, status),
                    )
                # Fallback: also query work items using category_name if tag_id is null
                rows = cur.fetchall()
                if not rows:
                    if category:
                        cur.execute(
                            """SELECT w.name, w.category_name, w.lifecycle_status, w.description, w.seq_num
                               FROM pr_work_items w
                               WHERE w.client_id=1 AND w.project=%s
                                 AND w.category_name ILIKE %s AND w.status=%s
                               ORDER BY w.seq_num DESC NULLS LAST LIMIT 50""",
                            (project, f"%{category}%", status),
                        )
                    else:
                        cur.execute(
                            """SELECT w.name, w.category_name, w.lifecycle_status, w.description, w.seq_num
                               FROM pr_work_items w
                               WHERE w.client_id=1 AND w.project=%s AND w.status=%s
                               ORDER BY w.seq_num DESC NULLS LAST LIMIT 50""",
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
                # Find or create global tag category
                cur.execute(
                    """SELECT id FROM mng_tags_categories
                       WHERE client_id=1 AND name ILIKE %s LIMIT 1""",
                    (category_name,),
                )
                cat_row = cur.fetchone()
                if not cat_row:
                    cur.execute(
                        """INSERT INTO mng_tags_categories (client_id, name)
                           VALUES (1, %s)
                           ON CONFLICT (client_id, name) DO NOTHING
                           RETURNING id""",
                        (category_name,),
                    )
                    cat_row = cur.fetchone()
                    if not cat_row:
                        cur.execute(
                            "SELECT id FROM mng_tags_categories WHERE client_id=1 AND name ILIKE %s LIMIT 1",
                            (category_name,),
                        )
                        cat_row = cur.fetchone()
                category_id = cat_row[0] if cat_row else None

                # Create planner_tags row
                cur.execute(
                    """INSERT INTO planner_tags (client_id, project, name, category_id, status)
                       VALUES (1, %s, %s, %s, 'active')
                       ON CONFLICT (client_id, project, name) DO NOTHING
                       RETURNING id, seq_num""",
                    (project, name, category_id),
                )
                tag_row = cur.fetchone()
                if not tag_row:
                    return f"Work item '{name}' already exists."
                tag_id, seq_num = tag_row

                # Insert tag_meta with description
                if description:
                    cur.execute(
                        """INSERT INTO planner_tags_meta (tag_id, client_id, project, description)
                           VALUES (%s::uuid, 1, %s, %s)
                           ON CONFLICT (tag_id) DO NOTHING""",
                        (tag_id, project, description),
                    )

                # Create work item linked to tag
                cur.execute(
                    """INSERT INTO pr_work_items
                           (client_id, project, category_name, name, description, tag_id)
                       VALUES (1, %s, %s, %s, %s, %s::uuid)
                       ON CONFLICT DO NOTHING""",
                    (project, category_name, name, description, tag_id),
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
