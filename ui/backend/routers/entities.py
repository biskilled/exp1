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
import logging
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from config import settings
from core.database import db

log = logging.getLogger(__name__)

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
    ("task",      "#4a90e2", "✓"),
    ("component", "#8e44ad", "◈"),
    ("doc_type",  "#2980b9", "📄"),
    ("customer",  "#f39c12", "👤"),
    ("phase",     "#16a085", "⏱"),
]

def _seed_defaults(project: str) -> None:
    """Idempotent: ensures every default category exists for the project."""
    db.ensure_project_schema(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            # Get existing names so we only insert truly missing ones
            cur.execute("SELECT name FROM entity_categories WHERE project=%s", (project,))
            existing = {r[0] for r in cur.fetchall()}
            for name, color, icon in _DEFAULT_CATEGORIES:
                if name not in existing:
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
    due_date:    Optional[str] = None
    parent_id:   Optional[int] = None

class ValuePatch(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    status:      Optional[str] = None
    due_date:    Optional[str] = None
    parent_id:   Optional[int] = None


@router.get("/values")
async def list_values(
    project:       str | None = Query(None),
    category_id:   int | None = Query(None),
    category_name: str | None = Query(None),   # e.g. "feature", "bug", "task"
    status:        str | None = Query(None),   # e.g. "active", "done", "archived"
):
    _require_db()
    p = _project(project)
    _seed_defaults(p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            # Resolve category_name → category_id if provided
            if category_name and not category_id:
                cur.execute(
                    "SELECT id FROM entity_categories WHERE project=%s AND name=%s",
                    (p, category_name),
                )
                row = cur.fetchone()
                if row:
                    category_id = row[0]

            where = ["v.project=%s"]
            params: list = [p]
            if category_id:
                where.append("v.category_id=%s"); params.append(category_id)
            if status:
                where.append("v.status=%s"); params.append(status)

            et_table = db.project_table("event_tags", p)
            cur.execute(
                f"""SELECT v.id, v.category_id, v.name, v.description, v.status,
                          v.created_at, v.due_date, v.parent_id,
                          (SELECT COUNT(*) FROM {et_table} et
                           WHERE et.entity_value_id = v.id) AS event_count,
                          c.name AS category_name, c.color, c.icon
                   FROM entity_values v
                   JOIN entity_categories c ON c.id = v.category_id
                   WHERE {' AND '.join(where)}
                   ORDER BY v.parent_id NULLS FIRST, v.status, v.name""",
                params,
            )
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                if row.get("due_date"):
                    row["due_date"] = row["due_date"].isoformat()
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
                "INSERT INTO entity_values (category_id,project,name,description,due_date,parent_id) "
                "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                (body.category_id, p, body.name, body.description, body.due_date or None, body.parent_id or None),
            )
            return {"id": cur.fetchone()[0], "name": body.name, "project": p}


@router.patch("/values/{val_id}")
async def patch_value(val_id: int, body: ValuePatch):
    _require_db()
    fields, params = [], []
    if body.name        is not None: fields.append("name=%s");        params.append(body.name)
    if body.description is not None: fields.append("description=%s"); params.append(body.description)
    if body.status      is not None: fields.append("status=%s");      params.append(body.status)
    if body.due_date    is not None: fields.append("due_date=%s");    params.append(body.due_date or None)
    if body.parent_id   is not None: fields.append("parent_id=%s");   params.append(body.parent_id or None)
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
    ev_table = db.project_table("events", p)
    et_table = db.project_table("event_tags", p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            if value_id:
                cur.execute(
                    f"""SELECT e.id, e.event_type, e.source_id, e.title,
                              e.metadata, e.created_at
                       FROM {ev_table} e
                       JOIN {et_table} et ON et.event_id = e.id
                       WHERE et.entity_value_id=%s
                       ORDER BY e.created_at DESC LIMIT %s""",
                    (value_id, limit),
                )
            elif event_type:
                cur.execute(
                    f"""SELECT id, event_type, source_id, title, metadata, created_at
                       FROM {ev_table} WHERE event_type=%s
                       ORDER BY created_at DESC LIMIT %s""",
                    (event_type, limit),
                )
            else:
                cur.execute(
                    f"""SELECT id, event_type, source_id, title, metadata, created_at
                       FROM {ev_table}
                       ORDER BY created_at DESC LIMIT %s""",
                    (limit,),
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
                        FROM {et_table} et
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


def _do_sync_events(p: str) -> dict[str, int]:
    """Core sync logic — importable by other modules (e.g. projects.py /memory).

    Imports history.jsonl + commits table into the events table. Idempotent.
    Returns {"prompt": N, "commit": N} counts of newly inserted rows.
    Requires db.is_available() to already be True; caller is responsible.
    """
    ws = _workspace(p)
    imported = {"prompt": 0, "commit": 0}
    ev_table = db.project_table("events", p)
    c_table  = db.project_table("commits", p)

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
                    meta = json.dumps({
                        "provider": e.get("provider"),
                        "source":   e.get("source"),
                        "phase":    e.get("phase"),
                        "feature":  e.get("feature"),
                    })
                    cur.execute(
                        f"""INSERT INTO {ev_table}
                               (event_type, source_id, title, content, metadata, created_at)
                           VALUES ('prompt',%s,%s,%s,%s,%s::timestamptz)
                           ON CONFLICT (event_type, source_id) DO NOTHING""",
                        (sid, title, (e.get("user_input") or "")[:2000], meta, sid),
                    )
                    imported["prompt"] += cur.rowcount

            # 2. commits_{p} table → event_type="commit"
            # Include session_id so we can propagate entity tags automatically.
            # COALESCE guards against older schema rows that lack the column.
            try:
                cur.execute(
                    f"SELECT commit_hash, commit_msg, phase, feature, source, "
                    f"       committed_at, COALESCE(session_id,'') "
                    f"FROM {c_table}"
                )
            except Exception:
                # Fallback if session_id column doesn't exist yet
                cur.execute(
                    f"SELECT commit_hash, commit_msg, phase, feature, source, "
                    f"       committed_at, '' FROM {c_table}"
                )
            for commit_hash, msg, phase, feature, src, committed_at, session_id in cur.fetchall():
                meta = json.dumps({
                    "phase": phase, "feature": feature, "source": src,
                    "session_id": session_id or None,
                })
                cur.execute(
                    f"""INSERT INTO {ev_table}
                           (event_type, source_id, title, content, metadata, created_at)
                       VALUES ('commit',%s,%s,%s,%s,%s)
                       ON CONFLICT (event_type, source_id) DO NOTHING""",
                    (commit_hash, (msg or "")[:120], msg or "",
                     meta, committed_at or "2026-01-01T00:00:00+00:00"),
                )
                imported["commit"] += cur.rowcount

            # 3. Backfill session_id into existing commit events that were imported without it
            try:
                cur.execute(
                    f"""UPDATE {ev_table} ev
                           SET metadata = ev.metadata || jsonb_build_object('session_id', c.session_id)
                          FROM {c_table} c
                         WHERE ev.source_id = c.commit_hash
                           AND ev.event_type = 'commit'
                           AND (c.session_id IS NOT NULL AND c.session_id != '')
                           AND (ev.metadata->>'session_id') IS NULL"""
                )
            except Exception:
                pass  # session_id column may not exist in old schemas

            # 4. Auto-propagate entity tags: prompt events → commit events in the same session
            #    Any entity tags applied to prompts in a session are automatically inherited
            #    by commits from that session. Runs after every sync — idempotent.
            cur.execute(
                f"""INSERT INTO {et_table} (event_id, entity_value_id, auto_tagged)
                    SELECT DISTINCT commit_ev.id, pt.entity_value_id, TRUE
                    FROM {ev_table} commit_ev
                    JOIN {ev_table} prompt_ev
                         ON prompt_ev.metadata->>'session_id' = commit_ev.metadata->>'session_id'
                        AND commit_ev.metadata->>'session_id' IS NOT NULL
                        AND commit_ev.metadata->>'session_id' NOT IN ('', 'null')
                    JOIN {et_table} pt ON pt.event_id = prompt_ev.id
                    WHERE commit_ev.event_type = 'commit'
                      AND prompt_ev.event_type  = 'prompt'
                    ON CONFLICT DO NOTHING"""
            )
            imported["tags_propagated"] = cur.rowcount

    return imported


@router.post("/events/sync")
async def sync_events(project: str | None = Query(None)):
    """Import history.jsonl + commits → events table. Idempotent."""
    _require_db()
    p = _project(project)
    imported = _do_sync_events(p)
    return {"imported": imported, "project": p}


# ── Event tagging ──────────────────────────────────────────────────────────────

class TagAdd(BaseModel):
    entity_value_id: int
    auto_tagged:     bool = False


@router.post("/events/{event_id}/tag")
async def add_event_tag(event_id: int, body: TagAdd, project: str | None = Query(None)):
    _require_db()
    p = _project(project)
    et_table = db.project_table("event_tags", p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {et_table} (event_id, entity_value_id, auto_tagged) "
                "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (event_id, body.entity_value_id, body.auto_tagged),
            )
    return {"ok": True}


@router.delete("/events/{event_id}/tag/{value_id}")
async def remove_event_tag(event_id: int, value_id: int, project: str | None = Query(None)):
    _require_db()
    p = _project(project)
    et_table = db.project_table("event_tags", p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {et_table} WHERE event_id=%s AND entity_value_id=%s",
                (event_id, value_id),
            )
    return {"ok": True}


@router.get("/values/{val_id}/events")
async def value_events(val_id: int, project: str | None = Query(None), limit: int = Query(50)):
    return await list_events(project=project, value_id=val_id, limit=limit)


# ── Auto-tag suggestions ────────────────────────────────────────────────────────

async def _auto_suggest_tags(event_id: int, project: str, content: str) -> None:
    """Use Haiku to suggest entity values for an event. Stores in metadata.tag_suggestions.

    Also immediately applies the active session tags (no LLM needed for those).
    Silent on any error — this is always fire-and-forget.
    """
    if not db.is_available():
        return
    try:
        from core.api_keys import get_key
        key = get_key("anthropic")

        # Get all active entity values for this project
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT v.id, c.name, v.name
                       FROM entity_values v
                       JOIN entity_categories c ON c.id = v.category_id
                       WHERE v.project=%s AND v.status='active'
                       ORDER BY c.name, v.name""",
                    (project,),
                )
                all_values = cur.fetchall()  # (id, category, name)

                # Get active session tags — apply immediately without LLM
                cur.execute(
                    "SELECT phase, feature, bug_ref, extra FROM session_tags WHERE project=%s",
                    (project,),
                )
                st_row = cur.fetchone()

        if not all_values:
            return

        id_to_val = {vid: (cat, name) for vid, cat, name in all_values}
        suggestions: list[dict] = []
        auto_applied: list[int] = []

        et_table = db.project_table("event_tags", project)

        # Immediately apply active session tags
        if st_row:
            phase, feature, bug_ref, extra = st_row
            for vid, cat, name in all_values:
                if (cat == "phase"   and phase   and name == phase) or \
                   (cat == "feature" and feature and name == feature) or \
                   (cat == "bug"     and bug_ref  and name == bug_ref):
                    auto_applied.append(vid)

        for vid in auto_applied:
            cat, name = id_to_val[vid]
            suggestions.append({
                "value_id": vid, "category": cat, "name": name,
                "from_session": True, "confidence": 1.0,
            })
            # Apply immediately
            try:
                with db.conn() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            f"INSERT INTO {et_table} (event_id, entity_value_id, auto_tagged) "
                            "VALUES (%s,%s,TRUE) ON CONFLICT DO NOTHING",
                            (event_id, vid),
                        )
            except Exception:
                pass

        # LLM suggestions for non-session tags (only if Anthropic key available)
        if key:
            values_list = "\n".join(
                f"  {vid}: {cat}/{name}" for vid, cat, name in all_values
                if vid not in auto_applied
            )
            prompt = (
                f"Tag this developer prompt with relevant entity values.\n\n"
                f"Prompt: {content[:600]}\n\n"
                f"Entity values (id: category/name):\n{values_list}\n\n"
                "Return a JSON array of matching value_ids (integers, up to 4 most relevant). "
                "Only include confident, specific matches. Return [] if none clearly apply.\n"
                "Example: [2, 5]"
            )
            import anthropic
            client = anthropic.AsyncAnthropic(api_key=key)
            resp = await client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=80,
                messages=[{"role": "user", "content": prompt}],
            )
            text = (resp.content[0].text if resp.content else "").strip()
            match = re.search(r'\[[\d,\s]*\]', text)
            if match:
                for vid in json.loads(match.group()):
                    try:
                        vid = int(vid)
                    except (ValueError, TypeError):
                        continue
                    if vid in id_to_val and vid not in auto_applied:
                        cat, name = id_to_val[vid]
                        suggestions.append({
                            "value_id": vid, "category": cat, "name": name,
                            "from_session": False, "confidence": 0.8,
                        })

        if not suggestions:
            return

        # Store all suggestions in event metadata (including already-applied session ones)
        ev_table = db.project_table("events", project)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE {ev_table} SET metadata = jsonb_set(metadata, '{{tag_suggestions}}', %s::jsonb, true) "
                    "WHERE id=%s",
                    (json.dumps(suggestions), event_id),
                )

    except Exception as e:
        log.debug(f"_auto_suggest_tags failed (event {event_id}): {e}")


@router.get("/suggestions")
async def get_suggestions(
    project:   str | None = Query(None),
    source_id: str | None = Query(None),
):
    """Return events with pending tag suggestions not yet dismissed.

    Pass source_id (the event ts) to get suggestions for a specific prompt event.
    """
    _require_db()
    p = _project(project)
    ev_table = db.project_table("events", p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            if source_id:
                cur.execute(
                    f"""SELECT id, event_type, source_id, title, metadata, created_at
                       FROM {ev_table}
                       WHERE source_id=%s
                         AND metadata ? 'tag_suggestions'
                         AND (metadata->>'suggestions_handled') IS DISTINCT FROM 'true'
                       LIMIT 1""",
                    (source_id,),
                )
            else:
                cur.execute(
                    f"""SELECT id, event_type, source_id, title, metadata, created_at
                       FROM {ev_table}
                       WHERE metadata ? 'tag_suggestions'
                         AND (metadata->>'suggestions_handled') IS DISTINCT FROM 'true'
                       ORDER BY created_at DESC LIMIT 10""",
                )
            cols = [d[0] for d in cur.description]
            rows = []
            for r in cur.fetchall():
                row = dict(zip(cols, r))
                if row.get("created_at"):
                    row["created_at"] = row["created_at"].isoformat()
                rows.append(row)
    return {"events": rows, "project": p}


@router.post("/suggestions/{event_id}/dismiss")
async def dismiss_suggestions(event_id: int, project: str | None = Query(None)):
    """Mark tag suggestions as handled (dismissed without applying)."""
    _require_db()
    p = _project(project)
    ev_table = db.project_table("events", p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE {ev_table} SET metadata = jsonb_set(metadata, '{{suggestions_handled}}', 'true'::jsonb, true) "
                "WHERE id=%s",
                (event_id,),
            )
    return {"ok": True}


# ── Event links ────────────────────────────────────────────────────────────────

_LINK_TYPES = {"implements", "fixes", "causes", "relates_to", "references", "closes"}

class LinkCreate(BaseModel):
    to_event_id: int
    link_type:   str


@router.post("/events/{event_id}/link")
async def add_event_link(event_id: int, body: LinkCreate, project: str | None = Query(None)):
    _require_db()
    if body.link_type not in _LINK_TYPES:
        raise HTTPException(400, f"link_type must be one of: {sorted(_LINK_TYPES)}")
    p = _project(project)
    el_table = db.project_table("event_links", p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {el_table} (from_event_id, to_event_id, link_type) "
                "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                (event_id, body.to_event_id, body.link_type),
            )
    return {"ok": True}


@router.delete("/events/{event_id}/link/{to_id}/{link_type}")
async def remove_event_link(event_id: int, to_id: int, link_type: str, project: str | None = Query(None)):
    _require_db()
    p = _project(project)
    el_table = db.project_table("event_links", p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {el_table} "
                "WHERE from_event_id=%s AND to_event_id=%s AND link_type=%s",
                (event_id, to_id, link_type),
            )
    return {"ok": True}


@router.get("/events/{event_id}/links")
async def get_event_links(event_id: int, project: str | None = Query(None)):
    _require_db()
    p = _project(project)
    ev_table = db.project_table("events", p)
    el_table = db.project_table("event_links", p)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT el.to_event_id, el.link_type, e.event_type, e.title
                   FROM {el_table} el JOIN {ev_table} e ON e.id = el.to_event_id
                   WHERE el.from_event_id=%s""",
                (event_id,),
            )
            outgoing = [
                {"to_id": r[0], "link_type": r[1], "event_type": r[2], "title": r[3]}
                for r in cur.fetchall()
            ]
            cur.execute(
                f"""SELECT el.from_event_id, el.link_type, e.event_type, e.title
                   FROM {el_table} el JOIN {ev_table} e ON e.id = el.from_event_id
                   WHERE el.to_event_id=%s""",
                (event_id,),
            )
            incoming = [
                {"from_id": r[0], "link_type": r[1], "event_type": r[2], "title": r[3]}
                for r in cur.fetchall()
            ]
    return {"outgoing": outgoing, "incoming": incoming, "event_id": event_id}


# ── Session bulk-tag ─────────────────────────────────────────────────────────────

class SessionTagBody(BaseModel):
    session_id:    str
    project:       Optional[str] = None
    value_id:      Optional[int] = None           # tag with existing value
    category_name: Optional[str] = None           # create new value in this category
    value_name:    Optional[str] = None           # new value name (used with category_name)
    description:   str = ""


@router.post("/session-tag")
async def session_bulk_tag(body: SessionTagBody):
    """Tag ALL events belonging to a session with a given entity value.

    - If value_id is provided → use it directly.
    - If category_name + value_name → find or create the entity_value first.
    - Finds events by matching metadata->>'session_id' = session_id.
    - Also sync-imports the session from history.jsonl if not yet in events table.
    Returns count of events tagged.
    """
    _require_db()
    p = _project(body.project)

    with db.conn() as conn:
        with conn.cursor() as cur:
            # Resolve or create the target value
            value_id = body.value_id
            if value_id is None:
                if not body.category_name or not body.value_name:
                    raise HTTPException(400, "Provide value_id OR category_name+value_name")
                # Get category id
                cur.execute(
                    "SELECT id FROM entity_categories WHERE project=%s AND name=%s",
                    (p, body.category_name),
                )
                cat_row = cur.fetchone()
                if not cat_row:
                    raise HTTPException(404, f"Category '{body.category_name}' not found")
                cat_id = cat_row[0]
                # Find or create value
                cur.execute(
                    "SELECT id FROM entity_values WHERE project=%s AND category_id=%s AND name=%s",
                    (p, cat_id, body.value_name),
                )
                val_row = cur.fetchone()
                if val_row:
                    value_id = val_row[0]
                else:
                    cur.execute(
                        "INSERT INTO entity_values (project, category_id, name, description) "
                        "VALUES (%s,%s,%s,%s) RETURNING id",
                        (p, cat_id, body.value_name, body.description),
                    )
                    value_id = cur.fetchone()[0]

            ev_table = db.project_table("events", p)
            et_table = db.project_table("event_tags", p)

            # Find all events for this session
            # Events created by the UI have metadata->>'session_id' = session_id
            # Events from CLI have session_id in history.jsonl metadata
            cur.execute(
                f"""SELECT id FROM {ev_table}
                   WHERE (
                       metadata->>'session_id' = %s
                       OR source_id = %s
                     )""",
                (body.session_id, body.session_id),
            )
            event_ids = [r[0] for r in cur.fetchall()]

            # Tag them all (idempotent)
            tagged = 0
            for eid in event_ids:
                cur.execute(
                    f"INSERT INTO {et_table} (event_id, entity_value_id, auto_tagged) "
                    "VALUES (%s,%s,false) ON CONFLICT DO NOTHING",
                    (eid, value_id),
                )
                tagged += cur.rowcount

    return {
        "ok": True,
        "value_id": value_id,
        "session_id": body.session_id,
        "events_tagged": tagged,
        "project": p,
    }


class TagBySourceIdBody(BaseModel):
    source_id:       str
    entity_value_id: int
    project:         Optional[str] = None


@router.post("/events/tag-by-source-id")
async def tag_event_by_source_id(body: TagBySourceIdBody):
    """Tag a single event identified by its source_id (timestamp string from history.jsonl).

    - Looks up the event by source_id in events_{project}.
    - If not found, imports it from history.jsonl (upsert) or creates a minimal record.
    - Tags the event with entity_value_id (idempotent).
    Used by the History tab per-entry ⬡ Tag button.
    """
    _require_db()
    p = _project(body.project)
    ev_table = db.project_table("events", p)
    et_table = db.project_table("event_tags", p)

    with db.conn() as conn:
        with conn.cursor() as cur:
            # Find existing event by source_id
            cur.execute(f"SELECT id FROM {ev_table} WHERE source_id=%s LIMIT 1", (body.source_id,))
            row = cur.fetchone()
            event_id: int | None = row[0] if row else None

            if event_id is None:
                # Try to import from history.jsonl
                ws = _workspace(p)
                hist = ws / "_system" / "history.jsonl"
                if hist.exists():
                    for line in hist.read_text().splitlines():
                        if not line.strip():
                            continue
                        try:
                            e = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if e.get("ts") != body.source_id:
                            continue
                        title = (e.get("user_input") or "")[:120] or "(no input)"
                        meta = json.dumps({
                            "provider":   e.get("provider"),
                            "source":     e.get("source"),
                            "phase":      e.get("phase"),
                            "feature":    e.get("feature"),
                            "session_id": e.get("session_id"),
                        })
                        cur.execute(
                            f"""INSERT INTO {ev_table}
                                   (event_type, source_id, title, content, metadata, created_at)
                               VALUES ('prompt',%s,%s,%s,%s,%s::timestamptz)
                               ON CONFLICT (event_type, source_id) DO UPDATE SET title=EXCLUDED.title
                               RETURNING id""",
                            (body.source_id, title,
                             (e.get("user_input") or "")[:2000], meta, body.source_id),
                        )
                        r2 = cur.fetchone()
                        if r2:
                            event_id = r2[0]
                        break

            if event_id is None:
                # Create minimal placeholder event
                cur.execute(
                    f"""INSERT INTO {ev_table}
                           (event_type, source_id, title, metadata, created_at)
                       VALUES ('prompt',%s,'(history entry)','{{}}',%s::timestamptz)
                       ON CONFLICT (event_type, source_id) DO NOTHING
                       RETURNING id""",
                    (body.source_id, body.source_id),
                )
                r3 = cur.fetchone()
                if r3:
                    event_id = r3[0]
                else:
                    cur.execute(f"SELECT id FROM {ev_table} WHERE source_id=%s LIMIT 1", (body.source_id,))
                    r4 = cur.fetchone()
                    if r4:
                        event_id = r4[0]

            if event_id is None:
                raise HTTPException(404, "Event not found and could not be created")

            # Verify entity value exists
            cur.execute("SELECT id FROM entity_values WHERE id=%s AND project=%s", (body.entity_value_id, p))
            if not cur.fetchone():
                raise HTTPException(404, "Entity value not found")

            # Tag (idempotent)
            cur.execute(
                f"INSERT INTO {et_table} (event_id, entity_value_id, auto_tagged) "
                "VALUES (%s,%s,false) ON CONFLICT DO NOTHING",
                (event_id, body.entity_value_id),
            )

    return {"ok": True, "event_id": event_id, "source_id": body.source_id, "project": p}


@router.get("/session-tags")
async def get_session_entity_tags(session_id: str, project: str | None = Query(None)):
    """Return all entity values tagged for events belonging to a session.

    Used by the frontend to reload the applied-tags chip bar when switching sessions.
    """
    _require_db()
    p = _project(project)
    ev_table = db.project_table("events", p)
    et_table = db.project_table("event_tags", p)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""SELECT DISTINCT v.id, v.name, v.status,
                           c.id AS category_id, c.name AS category_name, c.color, c.icon
                    FROM {et_table} et
                    JOIN {ev_table} e  ON e.id  = et.event_id
                    JOIN entity_values v      ON v.id  = et.entity_value_id
                    JOIN entity_categories c  ON c.id  = v.category_id
                   WHERE e.metadata->>'session_id' = %s
                      OR e.source_id = %s""",
                (session_id, session_id),
            )
            cols = [d[0] for d in cur.description]
            tags = [dict(zip(cols, row)) for row in cur.fetchall()]

    return {"tags": tags, "session_id": session_id, "project": p}
