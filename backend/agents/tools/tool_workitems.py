"""
tool_workitems.py — Agent tools for reading and creating work items.

Provides direct DB access for:
  - list_work_items : query mem_ai_work_items (with optional category/status filter)
  - create_work_item: insert a new work item into mem_ai_work_items + planner_tags

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
            "Also creates a matching planner_tag so the item appears in the Planner tab."
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
                # ── Find or create tag category ───────────────────────────
                cur.execute(
                    "SELECT id FROM mng_tags_categories WHERE client_id=1 AND name ILIKE %s LIMIT 1",
                    (category_name,),
                )
                cat_row = cur.fetchone()
                if not cat_row:
                    cur.execute(
                        """INSERT INTO mng_tags_categories (client_id, name)
                           VALUES (1, %s) ON CONFLICT (client_id, name) DO NOTHING RETURNING id""",
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

                # ── Create planner_tags entry (visible in Planner) ────────
                cur.execute(
                    """INSERT INTO planner_tags (client_id, project, name, category_id, status)
                       VALUES (1, %s, %s, %s, 'active')
                       ON CONFLICT (client_id, project, name) DO NOTHING
                       RETURNING id""",
                    (project, name, category_id),
                )
                tag_row = cur.fetchone()
                tag_id = str(tag_row[0]) if tag_row else None

                # If tag existed already, look it up
                if not tag_id:
                    cur.execute(
                        "SELECT id FROM planner_tags WHERE client_id=1 AND project=%s AND name=%s LIMIT 1",
                        (project, name),
                    )
                    existing = cur.fetchone()
                    tag_id = str(existing[0]) if existing else None

                # ── Create planner_tags_meta with description ─────────────
                if tag_id and description:
                    cur.execute(
                        """INSERT INTO planner_tags_meta (tag_id, client_id, project, description)
                           VALUES (%s::uuid, 1, %s, %s)
                           ON CONFLICT (tag_id) DO UPDATE SET description=EXCLUDED.description""",
                        (tag_id, project, description),
                    )

                # ── Assign seq_num ────────────────────────────────────────
                try:
                    from data.dl_seq import next_seq
                    seq = next_seq(cur, project, category_name)
                except Exception:
                    seq = None

                # ── Insert mem_ai_work_items ──────────────────────────────
                cur.execute(
                    """INSERT INTO mem_ai_work_items
                           (client_id, project, category_name, name, description,
                            status, lifecycle_status, tag_id, seq_num)
                       VALUES (1, %s, %s, %s, %s, 'active', 'idea', %s::uuid, %s)
                       ON CONFLICT (client_id, project, category_name, name) DO NOTHING
                       RETURNING id, seq_num""",
                    (project, category_name, name, description, tag_id, seq),
                )
                wi_row = cur.fetchone()

        if wi_row:
            ref = f"#{wi_row[1]}" if wi_row[1] else ""
            return f"Created {category_name} {ref}: '{name}' (id={wi_row[0]})"
        return f"Work item '{name}' already exists in category '{category_name}'."
    except Exception as e:
        return f"Error creating work item: {e}"


# ── Handler map ────────────────────────────────────────────────────────────────

WORKITEM_HANDLERS: dict[str, callable] = {
    "list_work_items":  _handle_list_work_items,
    "create_work_item": _handle_create_work_item,
}
