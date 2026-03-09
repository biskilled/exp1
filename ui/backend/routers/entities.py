"""
entities.py — Entity/relationship model for the aicli knowledge layer.

Manages the tag taxonomy and raw event log that links every prompt, commit,
file change, and document to named features, bugs, and components.

Requires PostgreSQL. All endpoints return 503 when the DB is unavailable.

Endpoints:
    Categories:
        GET    /entities/categories
        POST   /entities/categories
        PATCH  /entities/categories/{id}
        DELETE /entities/categories/{id}

    Values (named instances per category):
        GET    /entities/values          ?project=&category_id=
        POST   /entities/values
        PATCH  /entities/values/{id}
        DELETE /entities/values/{id}

    Events (raw event log):
        GET    /entities/events          ?project=&event_type=&value_id=&limit=
        POST   /entities/events/sync     import history.jsonl + commits (idempotent)
        POST   /entities/events/{id}/tag
        DELETE /entities/events/{id}/tag/{value_id}
        GET    /entities/values/{id}/events

    Links (event → event relationships):
        POST   /entities/events/{id}/link
        DELETE /entities/events/{id}/link/{to_id}/{link_type}
        GET    /entities/events/{id}/links
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from config import settings
from core.database import db

router = APIRouter()

# ── helpers ────────────────────────────────────────────────────────────────────

def _require_db():
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

def _project(p: str | None) -> str:
    return p or settings.active_project or "default"

def _workspace(project: str) -> Path:
    return Path(settings.workspace_dir) / project

_DEFAULT_CATEGORIES = [
    ("feature",   "#27ae60", "⬡"),
    ("bug",       "#e74c3c", "⚠"),
    ("component", "#8e44ad", "◈"),
    ("doc_type",  "#2980b9", "📄"),
    ("customer",  "#f39c12", "👤"),
    ("phase",     "#16a085", "⏱"),
]

def _seed_defaults(project: str) -> None:
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM entity_categories WHERE project=%s", (project,))
            if cur.fetchone()[0] == 0:
                for name, color, icon in _DEFAULT_CATEGORIES:
                    cur.execute(
                        "INSERT INTO entity_categories (project,name,color,icon) "
                        "VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                        (project, name, color, icon),
                    )


# ── Categories ─────────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name:    str
    color:   str = "#4a90e2"
    icon:    str = "⬡"
    project: Optional[str] = None

class CategoryPatch(BaseModel):
    name:  Optional[str] = None
    color: Optional[str] = None
    icon:  Optional[str] = None


@router.get("/categories")
async def list_categories(project: str | None = Query(None)):
    _require_db()
    p = _project(project)
    _seed_defaults(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT c.id, c.name, c.color, c.icon,
                          COUNT(v.id) AS value_count
                   FROM entity_categories c
                   LEFT JOIN entity_values v ON v.category_id = c.id
                   WHERE c.project=%s
                   GROUP BY c.id ORDER BY c.name""",
                (p,),
            )
            cols = [d[0] for d in cur.description]
            return {"categories": [dict(zip(cols, r)) for r in cur.fetchall()], "project": p}


@router.post("/categories", status_code=201)
async def create_category(body: CategoryCreate):
    _require_db()
    p = _project(body.project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO entity_categories (project,name,color,icon) "
                "VALUES (%s,%s,%s,%s) RETURNING id",
                (p, body.name, body.color, body.icon),
            )
            return {"id": cur.fetchone()[0], "name": body.name, "project": p}


@router.patch("/categories/{cat_id}")
async def patch_category(cat_id: int, body: CategoryPatch):
    _require_db()
    fields, params = [], []
    if body.name  is not None: fields.append("name=%s");  params.append(body.name)
    if body.color is not None: fields.append("color=%s"); params.append(body.color)
    if body.icon  is not None: fields.append("icon=%s");  params.append(body.icon)
    if not fields:
        raise HTTPException(400, "Nothing to update")
    params.append(cat_id)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE entity_categories SET {','.join(fields)} WHERE id=%s RETURNING id",
                params,
            )
            if not cur.fetchone():
                raise HTTPException(404, "Category not found")
    return {"ok": True}


@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: int):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM entity_categories WHERE id=%s RETURNING id", (cat_id,))
            if not cur.fetchone():
                raise HTTPException(404, "Category not found")
    return {"ok": True}


# ── Values ─────────────────────────────────────────────────────────────────────

class ValueCreate(BaseModel):
    category_id: int
    name:        str
    description: str = ""
    project:     Optional[str] = None

class ValuePatch(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    status:      Optional[str] = None


@router.get("/values")
async def list_values(
    project:     str | None = Query(None),
    category_id: int | None = Query(None),
):
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            if category_id:
                cur.execute(
                    """SELECT v.id, v.category_id, v.name, v.description, v.status,
                              v.created_at, COUNT(et.event_id) AS event_count
                       FROM entity_values v
                       LEFT JOIN event_tags et ON et.entity_value_id = v.id
                       WHERE v.project=%s AND v.category_id=%s
                       GROUP BY v.id ORDER BY v.name""",
                    (p, category_id),
                )
            else:
                cur.execute(
                    """SELECT v.id, v.category_id, v.name, v.description, v.status,
                              v.created_at, COUNT(et.event_id) AS event_count
                       FROM entity_values v
                       LEFT JOIN event_tags et ON et.entity_value_id = v.id
                       WHERE v.project=%s
                       GROUP BY v.id ORDER BY v.category_id, v.name""",
                    (p,),
                )
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                rows.append(row)
            return {"values": rows, "project": p}


@router.post("/values", status_code=201)
async def create_value(body: ValueCreate):
    _require_db()
    p = _project(body.project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM entity_categories WHERE id=%s AND project=%s",
                (body.category_id, p),
            )
            if not cur.fetchone():
                raise HTTPException(404, "Category not found")
            cur.execute(
                "INSERT INTO entity_values (category_id,project,name,description) "
                "VALUES (%s,%s,%s,%s) RETURNING id",
                (body.category_id, p, body.name, body.description),
            )
            return {"id": cur.fetchone()[0], "name": body.name, "project": p}


@router.patch("/values/{val_id}")
async def patch_value(val_id: int, body: ValuePatch):
    _require_db()
    fields, params = [], []
    if body.name        is not None: fields.append("name=%s");        params.append(body.name)
    if body.description is not None: fields.append("description=%s"); params.append(body.description)
    if body.status      is not None: fields.append("status=%s");      params.append(body.status)
    if not fields:
        raise HTTPException(400, "Nothing to update")
    params.append(val_id)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE entity_values SET {','.join(fields)} WHERE id=%s RETURNING id",
                params,
            )
            if not cur.fetchone():
                raise HTTPException(404, "Value not found")
    return {"ok": True}


@router.delete("/values/{val_id}")
async def delete_value(val_id: int):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM entity_values WHERE id=%s RETURNING id", (val_id,))
            if not cur.fetchone():
                raise HTTPException(404, "Value not found")
    return {"ok": True}


# ── Events ─────────────────────────────────────────────────────────────────────

@router.get("/events")
async def list_events(
    project:    str | None = Query(None),
    event_type: str | None = Query(None),
    value_id:   int | None = Query(None),
    limit:      int        = Query(50),
):
    _require_db()
    p = _project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            if value_id:
                cur.execute(
                    """SELECT e.id, e.event_type, e.source_id, e.title,
                              e.metadata, e.created_at
                       FROM events e
                       JOIN event_tags et ON et.event_id = e.id
                       WHERE e.project=%s AND et.entity_value_id=%s
                       ORDER BY e.created_at DESC LIMIT %s""",
                    (p, value_id, limit),
                )
            elif event_type:
                cur.execute(
                    """SELECT id, event_type, source_id, title, metadata, created_at
                       FROM events WHERE project=%s AND event_type=%s
                       ORDER BY created_at DESC LIMIT %s""",
                    (p, event_type, limit),
                )
            else:
                cur.execute(
                    """SELECT id, event_type, source_id, title, metadata, created_at
                       FROM events WHERE project=%s
                       ORDER BY created_at DESC LIMIT %s""",
                    (p, limit),
                )
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                rows.append(row)

            # Attach tags to each event
            if rows:
                ids = [r["id"] for r in rows]
                ph  = ",".join(["%s"] * len(ids))
                cur.execute(
                    f"""SELECT et.event_id, v.id, v.name, c.name AS category,
                               c.color, c.icon, et.auto_tagged
                        FROM event_tags et
                        JOIN entity_values v     ON v.id  = et.entity_value_id
                        JOIN entity_categories c ON c.id  = v.category_id
                        WHERE et.event_id IN ({ph})""",
                    ids,
                )
                tag_map: dict[int, list] = {}
                for tr in cur.fetchall():
                    tag_map.setdefault(tr[0], []).append({
                        "value_id": tr[1], "value": tr[2],
                        "category": tr[3], "color": tr[4],
                        "icon": tr[5], "auto_tagged": tr[6],
                    })
                for row in rows:
                    row["tags"] = tag_map.get(row["id"], [])

            return {"events": rows, "project": p, "total": len(rows)}


@router.post("/events/sync")
async def sync_events(project: str | None = Query(None)):
    """Import history.jsonl + commits → events table. Idempotent."""
    _require_db()
    p = _project(project)
    ws = _workspace(p)
    imported = {"prompt": 0, "commit": 0}

    with db.conn() as conn:
        with conn.cursor() as cur:

            # 1. history.jsonl → event_type="prompt"
            hist = ws / "_system" / "history.jsonl"
            if hist.exists():
                for line in hist.read_text().splitlines():
                    if not line.strip():
                        continue
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    sid = e.get("ts") or ""
                    if not sid:
                        continue
                    title = (e.get("user_input") or "")[:120] or "(no input)"
                    meta  = json.dumps({
                        "provider": e.get("provider"),
                        "source":   e.get("source"),
                        "phase":    e.get("phase"),
                        "feature":  e.get("feature"),
                    })
                    cur.execute(
                        """INSERT INTO events
                               (project, event_type, source_id, title, content, metadata, created_at)
                           VALUES (%s,'prompt',%s,%s,%s,%s,%s::timestamptz)
                           ON CONFLICT (project, event_type, source_id) DO NOTHING""",
                        (p, sid, title, (e.get("user_input") or "")[:2000], meta, sid),
                    )
                    imported["prompt"] += cur.rowcount

            # 2. commits table → event_type="commit"
            cur.execute(
                "SELECT commit_hash, commit_msg, phase, feature, source, committed_at "
                "FROM commits WHERE project=%s", (p,)
            )
            for commit_hash, msg, phase, feature, src, committed_at in cur.fetchall():
                meta = json.dumps({"phase": phase, "feature": feature, "source": src})
                cur.execute(
                    """INSERT INTO events
                           (project, event_type, source_id, title, content, metadata, created_at)
                       VALUES (%s,'commit',%s,%s,%s,%s,%s)
                       ON CONFLICT (project, event_type, source_id) DO NOTHING""",
                    (p, commit_hash, (msg or "")[:120], msg or "",
                     meta, committed_at or "2026-01-01T00:00:00+00:00"),
                )
                imported["commit"] += cur.rowcount

    return {"imported": imported, "project": p}


# ── Event tagging ──────────────────────────────────────────────────────────────

class TagAdd(BaseModel):
    entity_value_id: int
    auto_tagged:     bool = False


@router.post("/events/{event_id}/tag")
async def add_event_tag(event_id: int, body: TagAdd):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO event_tags (event_id, entity_value_id, auto_tagged) "
                "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (event_id, body.entity_value_id, body.auto_tagged),
            )
    return {"ok": True}


@router.delete("/events/{event_id}/tag/{value_id}")
async def remove_event_tag(event_id: int, value_id: int):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM event_tags WHERE event_id=%s AND entity_value_id=%s",
                (event_id, value_id),
            )
    return {"ok": True}


@router.get("/values/{val_id}/events")
async def value_events(val_id: int, project: str | None = Query(None), limit: int = Query(50)):
    return await list_events(project=project, value_id=val_id, limit=limit)


# ── Event links ────────────────────────────────────────────────────────────────

_LINK_TYPES = {"implements", "fixes", "causes", "relates_to", "references", "closes"}

class LinkCreate(BaseModel):
    to_event_id: int
    link_type:   str


@router.post("/events/{event_id}/link")
async def add_event_link(event_id: int, body: LinkCreate):
    _require_db()
    if body.link_type not in _LINK_TYPES:
        raise HTTPException(400, f"link_type must be one of: {sorted(_LINK_TYPES)}")
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO event_links (from_event_id, to_event_id, link_type) "
                "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (event_id, body.to_event_id, body.link_type),
            )
    return {"ok": True}


@router.delete("/events/{event_id}/link/{to_id}/{link_type}")
async def remove_event_link(event_id: int, to_id: int, link_type: str):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM event_links "
                "WHERE from_event_id=%s AND to_event_id=%s AND link_type=%s",
                (event_id, to_id, link_type),
            )
    return {"ok": True}


@router.get("/events/{event_id}/links")
async def get_event_links(event_id: int):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT el.to_event_id, el.link_type, e.event_type, e.title
                   FROM event_links el JOIN events e ON e.id = el.to_event_id
                   WHERE el.from_event_id=%s""",
                (event_id,),
            )
            outgoing = [
                {"to_id": r[0], "link_type": r[1], "event_type": r[2], "title": r[3]}
                for r in cur.fetchall()
            ]
            cur.execute(
                """SELECT el.from_event_id, el.link_type, e.event_type, e.title
                   FROM event_links el JOIN events e ON e.id = el.from_event_id
                   WHERE el.to_event_id=%s""",
                (event_id,),
            )
            incoming = [
                {"from_id": r[0], "link_type": r[1], "event_type": r[2], "title": r[3]}
                for r in cur.fetchall()
            ]
    return {"outgoing": outgoing, "incoming": incoming, "event_id": event_id}
