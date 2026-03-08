"""
entities.py — CRUD for project entities: features, tasks, bugs.

Requires PostgreSQL (returns 503 when unavailable — schema created in Phase 1).
All entities are scoped to a project.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from config import settings
from core.auth import get_optional_user
from core.database import db

router = APIRouter()


def _require_db():
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL required for entity tracking. Set DATABASE_URL.")


def _proj(project: str = "") -> str:
    return project or settings.active_project or "default"


# ── Pydantic models ───────────────────────────────────────────────────────────

class FeatureCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "proposed"
    priority: str = "medium"
    project: str = ""


class FeatureUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class TaskCreate(BaseModel):
    title: str
    description: str = ""
    status: str = "open"
    priority: str = "medium"
    feature_id: Optional[str] = None
    assignee: Optional[str] = None
    project: str = ""


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    feature_id: Optional[str] = None
    assignee: Optional[str] = None


class BugCreate(BaseModel):
    title: str
    description: str = ""
    severity: str = "medium"
    status: str = "open"
    task_id: Optional[str] = None
    project: str = ""


class BugUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    task_id: Optional[str] = None


# ── Features ──────────────────────────────────────────────────────────────────

@router.get("/features")
async def list_features(
    project: str = Query(""),
    status: Optional[str] = Query(None),
    limit: int = Query(100),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _proj(project)
    sql = "SELECT id, project, title, description, status, priority, created_at, updated_at FROM features WHERE project=%s"
    params = [p]
    if status:
        sql += " AND status=%s"; params.append(status)
    sql += " ORDER BY created_at DESC LIMIT %s"; params.append(limit)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return {"features": [_feat_row(r) for r in rows]}


@router.post("/features")
async def create_feature(body: FeatureCreate, user=Depends(get_optional_user)):
    _require_db()
    fid = str(uuid.uuid4())
    p = _proj(body.project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO features (id, project, title, description, status, priority)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   RETURNING id, project, title, description, status, priority, created_at, updated_at""",
                (fid, p, body.title, body.description, body.status, body.priority),
            )
            row = cur.fetchone()
    return _feat_row(row)


@router.patch("/features/{fid}")
async def update_feature(fid: str, body: FeatureUpdate, user=Depends(get_optional_user)):
    _require_db()
    fields, values = _build_update({"title": body.title, "description": body.description,
                                    "status": body.status, "priority": body.priority})
    if not fields:
        raise HTTPException(400, "Nothing to update")
    values.extend([fid])
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE features SET {', '.join(fields)}, updated_at=NOW() WHERE id=%s", values
            )
    return {"updated": True, "id": fid}


@router.delete("/features/{fid}")
async def delete_feature(fid: str, user=Depends(get_optional_user)):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM features WHERE id=%s", (fid,))
    return {"deleted": True, "id": fid}


# ── Tasks ─────────────────────────────────────────────────────────────────────

@router.get("/tasks")
async def list_tasks(
    project: str = Query(""),
    status: Optional[str] = Query(None),
    feature_id: Optional[str] = Query(None),
    limit: int = Query(100),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _proj(project)
    sql = """SELECT id, project, feature_id, title, description, status, priority, assignee,
                    created_at, updated_at FROM tasks WHERE project=%s"""
    params: list = [p]
    if status:
        sql += " AND status=%s"; params.append(status)
    if feature_id:
        sql += " AND feature_id=%s"; params.append(feature_id)
    sql += " ORDER BY created_at DESC LIMIT %s"; params.append(limit)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return {"tasks": [_task_row(r) for r in rows]}


@router.post("/tasks")
async def create_task(body: TaskCreate, user=Depends(get_optional_user)):
    _require_db()
    tid = str(uuid.uuid4())
    p = _proj(body.project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO tasks (id, project, feature_id, title, description, status, priority, assignee)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id, project, feature_id, title, description, status, priority, assignee,
                             created_at, updated_at""",
                (tid, p, body.feature_id or None, body.title, body.description,
                 body.status, body.priority, body.assignee or None),
            )
            row = cur.fetchone()
    return _task_row(row)


@router.patch("/tasks/{tid}")
async def update_task(tid: str, body: TaskUpdate, user=Depends(get_optional_user)):
    _require_db()
    fields, values = _build_update({
        "title": body.title, "description": body.description,
        "status": body.status, "priority": body.priority,
        "feature_id": body.feature_id, "assignee": body.assignee,
    })
    if not fields:
        raise HTTPException(400, "Nothing to update")
    values.append(tid)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE tasks SET {', '.join(fields)}, updated_at=NOW() WHERE id=%s", values
            )
    return {"updated": True, "id": tid}


@router.delete("/tasks/{tid}")
async def delete_task(tid: str, user=Depends(get_optional_user)):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id=%s", (tid,))
    return {"deleted": True, "id": tid}


# ── Bugs ──────────────────────────────────────────────────────────────────────

@router.get("/bugs")
async def list_bugs(
    project: str = Query(""),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _proj(project)
    sql = """SELECT id, project, task_id, title, description, severity, status, created_at
             FROM bugs WHERE project=%s"""
    params: list = [p]
    if status:
        sql += " AND status=%s"; params.append(status)
    if severity:
        sql += " AND severity=%s"; params.append(severity)
    sql += " ORDER BY created_at DESC LIMIT %s"; params.append(limit)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return {"bugs": [_bug_row(r) for r in rows]}


@router.post("/bugs")
async def create_bug(body: BugCreate, user=Depends(get_optional_user)):
    _require_db()
    bid = str(uuid.uuid4())
    p = _proj(body.project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO bugs (id, project, task_id, title, description, severity, status)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id, project, task_id, title, description, severity, status, created_at""",
                (bid, p, body.task_id or None, body.title, body.description, body.severity, body.status),
            )
            row = cur.fetchone()
    return _bug_row(row)


@router.patch("/bugs/{bid}")
async def update_bug(bid: str, body: BugUpdate, user=Depends(get_optional_user)):
    _require_db()
    fields, values = _build_update({
        "title": body.title, "description": body.description,
        "severity": body.severity, "status": body.status, "task_id": body.task_id,
    })
    if not fields:
        raise HTTPException(400, "Nothing to update")
    values.append(bid)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE bugs SET {', '.join(fields)} WHERE id=%s", values)
    return {"updated": True, "id": bid}


@router.delete("/bugs/{bid}")
async def delete_bug(bid: str, user=Depends(get_optional_user)):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM bugs WHERE id=%s", (bid,))
    return {"deleted": True, "id": bid}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _feat_row(r) -> dict:
    return {"id": r[0], "project": r[1], "title": r[2], "description": r[3],
            "status": r[4], "priority": r[5],
            "created_at": r[6].isoformat() if r[6] else None,
            "updated_at": r[7].isoformat() if r[7] else None}


def _task_row(r) -> dict:
    return {"id": r[0], "project": r[1], "feature_id": r[2], "title": r[3],
            "description": r[4], "status": r[5], "priority": r[6], "assignee": r[7],
            "created_at": r[8].isoformat() if r[8] else None,
            "updated_at": r[9].isoformat() if r[9] else None}


def _bug_row(r) -> dict:
    return {"id": r[0], "project": r[1], "task_id": r[2], "title": r[3],
            "description": r[4], "severity": r[5], "status": r[6],
            "created_at": r[7].isoformat() if r[7] else None}


def _build_update(mapping: dict) -> tuple[list[str], list]:
    fields, values = [], []
    for col, val in mapping.items():
        if val is not None:
            fields.append(f"{col}=%s")
            values.append(val)
    return fields, values
