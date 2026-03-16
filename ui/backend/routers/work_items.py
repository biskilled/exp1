"""
work_items.py — Work item management with 4-agent pipeline support.

Replaces entity_values for feature/bug/task categories. Adds:
  - acceptance_criteria / implementation_plan fields
  - agent pipeline (PM → Architect → Developer → Reviewer) via graph DAG
  - project_facts (durable extracted facts)
  - memory_items (Trycycle-reviewed session/feature summaries)

Endpoints:
    GET    /work-items                    ?project=&category=&status=
    POST   /work-items                    {category_name, name, description, ...}
    PATCH  /work-items/{id}               {name?, description?, lifecycle_status?, ...}
    DELETE /work-items/{id}
    GET    /work-items/{id}/interactions  ?limit=20
    POST   /work-items/migrate-from-tags  ?project=
    POST   /work-items/{id}/run-pipeline  ?project=
    GET    /work-items/facts              ?project=
    GET    /work-items/memory-items       ?project=&scope=session|feature
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from config import settings
from core.database import db

router = APIRouter()
log = logging.getLogger(__name__)


def _require_db():
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")


def _project(p: str | None) -> str:
    return p or settings.active_project or "default"


# ── Models ────────────────────────────────────────────────────────────────────

class WorkItemCreate(BaseModel):
    category_name:       str
    name:                str
    description:         str = ""
    project:             Optional[str] = None
    status:              str = "active"
    lifecycle_status:    str = "idea"
    due_date:            Optional[str] = None
    acceptance_criteria: str = ""
    implementation_plan: str = ""
    tags:                list[str] = []


class WorkItemPatch(BaseModel):
    name:                Optional[str] = None
    description:         Optional[str] = None
    status:              Optional[str] = None
    lifecycle_status:    Optional[str] = None
    due_date:            Optional[str] = None
    acceptance_criteria: Optional[str] = None
    implementation_plan: Optional[str] = None
    agent_status:        Optional[str] = None
    tags:                Optional[list[str]] = None


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("")
async def list_work_items(
    project:  str | None = Query(None),
    category: str | None = Query(None),
    status:   str | None = Query(None),
    limit:    int        = Query(100),
):
    """List work items, optionally filtered by category and status."""
    _require_db()
    p = _project(project)
    where = ["w.project=%s"]
    params: list = [p]
    if category:
        where.append("w.category_name=%s"); params.append(category)
    if status:
        where.append("w.status=%s"); params.append(status)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT w.id, w.category_name, w.name, w.description,
                          w.status, w.lifecycle_status, w.due_date,
                          w.acceptance_criteria, w.implementation_plan,
                          w.agent_run_id, w.agent_status, w.tags,
                          w.created_at, w.updated_at,
                          ec.color, ec.icon,
                          (SELECT COUNT(*) FROM interaction_tags it
                           WHERE it.work_item_id = w.id) AS interaction_count
                   FROM work_items w
                   LEFT JOIN entity_categories ec ON ec.project=w.project AND ec.name=w.category_name
                   WHERE {' AND '.join(where)}
                   ORDER BY w.category_name, w.status, w.created_at DESC
                   LIMIT %s""",
                params + [limit],
            )
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                for dt_field in ("created_at", "updated_at"):
                    if row.get(dt_field):
                        row[dt_field] = row[dt_field].isoformat()
                if row.get("due_date"):
                    row["due_date"] = row["due_date"].isoformat()
                row["id"] = str(row["id"])
                if row.get("tags") is None:
                    row["tags"] = []
                rows.append(row)
    return {"work_items": rows, "project": p, "total": len(rows)}


@router.post("", status_code=201)
async def create_work_item(body: WorkItemCreate, project: str | None = Query(None)):
    """Create a new work item."""
    _require_db()
    p = _project(project or body.project)

    # Resolve category_id from entity_categories if it exists
    category_id = None
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM entity_categories WHERE project=%s AND name=%s",
                (p, body.category_name),
            )
            row = cur.fetchone()
            if row:
                category_id = row[0]

            cur.execute(
                """INSERT INTO work_items
                       (project, category_name, category_id, name, description,
                        status, lifecycle_status, due_date,
                        acceptance_criteria, implementation_plan, tags)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id, name, category_name, created_at""",
                (p, body.category_name, category_id, body.name, body.description,
                 body.status, body.lifecycle_status, body.due_date or None,
                 body.acceptance_criteria, body.implementation_plan,
                 body.tags),
            )
            r = cur.fetchone()
    return {
        "id": str(r[0]), "name": r[1], "category_name": r[2],
        "created_at": r[3].isoformat(), "project": p,
    }


@router.patch("/{item_id}")
async def patch_work_item(
    item_id: str,
    body: WorkItemPatch,
    project: str | None = Query(None),
    background: BackgroundTasks = BackgroundTasks(),
):
    """Update work item fields. Triggers feature memory synthesis when lifecycle → done."""
    _require_db()
    p = _project(project)

    fields, params = [], []
    if body.name                is not None: fields.append("name=%s");                params.append(body.name)
    if body.description         is not None: fields.append("description=%s");         params.append(body.description)
    if body.status              is not None: fields.append("status=%s");              params.append(body.status)
    if body.lifecycle_status    is not None: fields.append("lifecycle_status=%s");    params.append(body.lifecycle_status)
    if body.due_date            is not None: fields.append("due_date=%s");            params.append(body.due_date or None)
    if body.acceptance_criteria is not None: fields.append("acceptance_criteria=%s"); params.append(body.acceptance_criteria)
    if body.implementation_plan is not None: fields.append("implementation_plan=%s"); params.append(body.implementation_plan)
    if body.agent_status        is not None: fields.append("agent_status=%s");        params.append(body.agent_status)
    if body.tags                is not None: fields.append("tags=%s");                params.append(body.tags)

    if not fields:
        raise HTTPException(400, "Nothing to update")

    fields.append("updated_at=NOW()")
    params.append(item_id)
    params.append(p)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE work_items SET {','.join(fields)} WHERE id=%s::uuid AND project=%s RETURNING id",
                params,
            )
            if not cur.fetchone():
                raise HTTPException(404, "Work item not found")

    # When lifecycle → done, synthesize feature memory in background
    if body.lifecycle_status == "done":
        from routers.projects import _summarize_feature_memory
        try:
            asyncio.create_task(_summarize_feature_memory(p, item_id))
        except Exception:
            pass

    return {"ok": True, "id": item_id}


@router.delete("/{item_id}")
async def delete_work_item(item_id: str, project: str | None = Query(None)):
    """Delete a work item and all its interaction_tags."""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM work_items WHERE id=%s::uuid AND project=%s RETURNING id",
                (item_id, p),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Work item not found")
    return {"ok": True}


# ── Interactions for a work item ──────────────────────────────────────────────

@router.get("/{item_id}/interactions")
async def get_work_item_interactions(
    item_id: str,
    project: str | None = Query(None),
    limit:   int        = Query(20),
):
    """Return recent interactions tagged to this work item."""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT i.id, i.session_id, i.event_type, i.source_id,
                          i.prompt, i.response, i.phase, i.created_at
                   FROM interaction_tags it
                   JOIN interactions i ON i.id = it.interaction_id
                   WHERE it.work_item_id=%s::uuid AND i.project_id=%s
                   ORDER BY i.created_at DESC LIMIT %s""",
                (item_id, p, limit),
            )
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                row["id"] = str(row["id"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                rows.append(row)
    return {"interactions": rows, "work_item_id": item_id, "project": p}


# ── Migrate from entity_values ────────────────────────────────────────────────

@router.post("/migrate-from-tags")
async def migrate_from_tags(project: str | None = Query(None)):
    """Copy feature/bug/task entity_values → work_items. Idempotent."""
    _require_db()
    p = _project(project)
    from core.migrations.migrate_to_memory_layers import run_migration
    asyncio.create_task(run_migration(p))
    return {"status": "migration started", "project": p}


# ── Agent pipeline ────────────────────────────────────────────────────────────

@router.post("/{item_id}/run-pipeline")
async def run_pipeline(item_id: str, project: str | None = Query(None)):
    """Start the 4-agent PM→Architect→Developer→Reviewer pipeline for a work item."""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name, description, acceptance_criteria FROM work_items WHERE id=%s::uuid AND project=%s",
                (item_id, p),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Work item not found")

    name, desc, existing_ac = row

    # Mark as running
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE work_items SET agent_status='running', updated_at=NOW() WHERE id=%s::uuid",
                (item_id,),
            )

    from core.work_item_pipeline import trigger_work_item_pipeline
    asyncio.create_task(trigger_work_item_pipeline(item_id, p, name, desc, existing_ac))
    return {"status": "pipeline started", "work_item_id": item_id, "project": p}


# ── Project facts ─────────────────────────────────────────────────────────────

@router.get("/facts")
async def get_project_facts(project: str | None = Query(None)):
    """Return current (valid_until IS NULL) project facts."""
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, fact_key, fact_value, valid_from
                   FROM project_facts
                   WHERE project_id=%s AND valid_until IS NULL
                   ORDER BY fact_key""",
                (p,),
            )
            cols = [d[0] for d in cur.description]
            facts = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                row["id"] = str(row["id"])
                if row.get("valid_from"):
                    row["valid_from"] = row["valid_from"].isoformat()
                facts.append(row)
    return {"facts": facts, "project": p, "total": len(facts)}


# ── Memory items ──────────────────────────────────────────────────────────────

@router.get("/memory-items")
async def get_memory_items(
    project: str | None = Query(None),
    scope:   str | None = Query(None),   # "session" | "feature"
    limit:   int        = Query(20),
):
    """Return recent memory_items (distilled session/feature summaries)."""
    _require_db()
    p = _project(project)
    where = ["project_id=%s"]
    params: list = [p]
    if scope:
        where.append("scope=%s"); params.append(scope)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT id, scope, scope_ref, content, reviewer_score, created_at
                   FROM memory_items
                   WHERE {' AND '.join(where)}
                   ORDER BY created_at DESC LIMIT %s""",
                params + [limit],
            )
            cols = [d[0] for d in cur.description]
            items = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                row["id"] = str(row["id"])
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                items.append(row)
    return {"memory_items": items, "project": p, "total": len(items)}
