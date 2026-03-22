"""
system_roles.py — Reusable prompt fragments that compose onto agent roles.

System roles are admin-managed text blocks (coding standards, security rules, etc.)
that get prepended to an agent role's system_prompt when a graph node executes.

Routes:
  GET    /system-roles/                              list (content only for admin)
  POST   /system-roles/                              create (admin)
  PATCH  /system-roles/{id}                          update (admin)
  DELETE /system-roles/{id}                          soft-delete is_active=FALSE (admin)
  GET    /system-roles/agent-roles/{role_id}/links   list system roles linked to an agent role
  POST   /system-roles/agent-roles/{role_id}/links   attach system role (admin)
  DELETE /system-roles/agent-roles/{role_id}/links/{system_role_id}  detach (admin)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import get_optional_user
from core.database import db

router = APIRouter()


def _require_db():
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL required for system roles")


def _is_admin(user) -> bool:
    return bool(user and (user.get("is_admin") or user.get("role") == "admin"))


def _require_admin(user):
    if not _is_admin(user):
        raise HTTPException(403, "Admin access required")


def _row_to_dict(row, include_content: bool = True) -> dict:
    d = {
        "id":          row[0],
        "name":        row[1],
        "description": row[2],
        "category":    row[4],
        "is_active":   row[5],
        "created_at":  row[6].isoformat() if row[6] else None,
        "updated_at":  row[7].isoformat() if row[7] else None,
    }
    if include_content:
        d["content"] = row[3]
    return d


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/")
async def list_system_roles(user=Depends(get_optional_user)):
    _require_db()
    admin = _is_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, name, description, content, category, is_active, created_at, updated_at
                   FROM mng_system_roles
                   WHERE client_id=1 AND is_active=TRUE
                   ORDER BY category, name""",
            )
            rows = cur.fetchall()
    return {
        "system_roles": [_row_to_dict(r, include_content=admin) for r in rows],
        "is_admin": admin,
    }


# ── Create ────────────────────────────────────────────────────────────────────

class SystemRoleCreate(BaseModel):
    name:        str
    description: str = ""
    content:     str = ""
    category:    str = "general"


@router.post("/")
async def create_system_role(body: SystemRoleCreate, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO mng_system_roles (client_id, name, description, content, category)
                   VALUES (1, %s, %s, %s, %s)
                   RETURNING id, name, description, content, category, is_active, created_at, updated_at""",
                (body.name, body.description, body.content, body.category),
            )
            row = cur.fetchone()
    return _row_to_dict(row, include_content=True)


# ── Update ────────────────────────────────────────────────────────────────────

class SystemRoleUpdate(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    content:     Optional[str] = None
    category:    Optional[str] = None


@router.patch("/{system_role_id}")
async def update_system_role(
    system_role_id: int, body: SystemRoleUpdate, user=Depends(get_optional_user)
):
    _require_db()
    _require_admin(user)

    fields: list[str] = []
    values: list      = []
    for col, val in [
        ("name",        body.name),
        ("description", body.description),
        ("content",     body.content),
        ("category",    body.category),
    ]:
        if val is not None:
            fields.append(f"{col}=%s")
            values.append(val)
    if not fields:
        raise HTTPException(400, "Nothing to update")
    fields.append("updated_at=NOW()")
    values.append(system_role_id)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE mng_system_roles SET {', '.join(fields)} WHERE id=%s AND client_id=1",
                values,
            )
            cur.execute(
                """SELECT id, name, description, content, category, is_active, created_at, updated_at
                   FROM mng_system_roles WHERE id=%s""",
                (system_role_id,),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "System role not found")
    return _row_to_dict(row, include_content=True)


# ── Soft delete ───────────────────────────────────────────────────────────────

@router.delete("/{system_role_id}")
async def delete_system_role(system_role_id: int, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE mng_system_roles SET is_active=FALSE, updated_at=NOW() WHERE id=%s AND client_id=1",
                (system_role_id,),
            )
    return {"deleted": True, "system_role_id": system_role_id}


# ── Links: list ───────────────────────────────────────────────────────────────

@router.get("/agent-roles/{role_id}/links")
async def list_links(role_id: int, user=Depends(get_optional_user)):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT sr.id, sr.name, sr.description, sr.category, l.order_index
                   FROM mng_role_system_links l
                   JOIN mng_system_roles sr ON sr.id = l.system_role_id
                   WHERE l.role_id = %s AND sr.is_active = TRUE
                   ORDER BY l.order_index ASC, l.id ASC""",
                (role_id,),
            )
            rows = cur.fetchall()
    return {
        "role_id": role_id,
        "links": [
            {
                "id":          r[0],
                "name":        r[1],
                "description": r[2],
                "category":    r[3],
                "order_index": r[4],
            }
            for r in rows
        ],
    }


# ── Links: attach ─────────────────────────────────────────────────────────────

class LinkCreate(BaseModel):
    system_role_id: int
    order_index:    int = 0


@router.post("/agent-roles/{role_id}/links")
async def attach_link(role_id: int, body: LinkCreate, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO mng_role_system_links (role_id, system_role_id, order_index)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (role_id, system_role_id) DO UPDATE SET order_index=EXCLUDED.order_index
                   RETURNING id, role_id, system_role_id, order_index""",
                (role_id, body.system_role_id, body.order_index),
            )
            row = cur.fetchone()
    return {"id": row[0], "role_id": row[1], "system_role_id": row[2], "order_index": row[3]}


# ── Links: detach ─────────────────────────────────────────────────────────────

@router.delete("/agent-roles/{role_id}/links/{system_role_id}")
async def detach_link(role_id: int, system_role_id: int, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM mng_role_system_links WHERE role_id=%s AND system_role_id=%s",
                (role_id, system_role_id),
            )
    return {"detached": True, "role_id": role_id, "system_role_id": system_role_id}
