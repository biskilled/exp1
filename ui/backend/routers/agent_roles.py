"""
agent_roles.py — Agent role library with version history.

Roles define the system prompt, provider, and model for a workflow node.
- All users: see name, description, provider, model (no system_prompt)
- Admin:     full CRUD including system_prompt, version history, create/edit/delete

Routes:
  GET    /agent-roles                    list active roles
  POST   /agent-roles                    create (admin only)
  PATCH  /agent-roles/{id}               edit; auto-saves version on prompt/model/provider change (admin)
  DELETE /agent-roles/{id}               soft-delete is_active=false (admin)
  GET    /agent-roles/{id}/versions      version history (admin)
  POST   /agent-roles/{id}/restore/{vid} restore to previous version (admin)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.auth import get_optional_user
from core.database import db

router = APIRouter()


def _require_db():
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL required for agent roles")


def _is_admin(user) -> bool:
    return bool(user and (user.get("is_admin") or user.get("role") == "admin"))


def _require_admin(user):
    if not _is_admin(user):
        raise HTTPException(403, "Admin access required")


def _row_to_role(row, include_prompt: bool = True) -> dict:
    r = {
        "id":          row[0],
        "project":     row[1],
        "name":        row[2],
        "description": row[3],
        "provider":    row[5],
        "model":       row[6],
        "tags":        row[7] or [],
        "is_active":   row[8],
        "created_at":  row[9].isoformat()  if row[9]  else None,
        "updated_at":  row[10].isoformat() if row[10] else None,
    }
    if include_prompt:
        r["system_prompt"] = row[4]
    return r


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/")
async def list_roles(
    project: str = Query("_global"),
    user=Depends(get_optional_user),
):
    _require_db()
    admin = _is_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, project, name, description, system_prompt,
                          provider, model, tags, is_active, created_at, updated_at
                   FROM mng_agent_roles
                   WHERE client_id=1 AND is_active=TRUE AND (project='_global' OR project=%s)
                   ORDER BY (project='_global') DESC, name""",
                (project,),
            )
            rows = cur.fetchall()
    return {
        "roles": [_row_to_role(r, include_prompt=admin) for r in rows],
        "is_admin": admin,
    }


# ── Create ────────────────────────────────────────────────────────────────────

class RoleCreate(BaseModel):
    project:       str       = "_global"
    name:          str
    description:   str       = ""
    system_prompt: str       = ""
    provider:      str       = "claude"
    model:         str       = ""
    tags:          list[str] = []


@router.post("/")
async def create_role(body: RoleCreate, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO mng_agent_roles
                       (client_id, project, name, description, system_prompt, provider, model, tags)
                   VALUES (1, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id, project, name, description, system_prompt,
                             provider, model, tags, is_active, created_at, updated_at""",
                (body.project, body.name, body.description, body.system_prompt,
                 body.provider, body.model, body.tags),
            )
            row = cur.fetchone()
    return _row_to_role(row, include_prompt=True)


# ── Update (auto-versions on prompt/model/provider change) ────────────────────

class RoleUpdate(BaseModel):
    name:          Optional[str]       = None
    description:   Optional[str]       = None
    system_prompt: Optional[str]       = None
    provider:      Optional[str]       = None
    model:         Optional[str]       = None
    tags:          Optional[list[str]] = None
    note:          str                 = ""


@router.patch("/{role_id}")
async def update_role(role_id: int, body: RoleUpdate, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)

    # Load current values for version comparison
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, system_prompt, provider, model FROM mng_agent_roles WHERE id=%s AND client_id=1",
                (role_id,),
            )
            existing = cur.fetchone()
    if not existing:
        raise HTTPException(404, "Role not found")

    versioned_changed = (
        (body.system_prompt is not None and body.system_prompt != existing[1]) or
        (body.provider      is not None and body.provider      != existing[2]) or
        (body.model         is not None and body.model         != existing[3])
    )

    fields: list[str] = []
    values: list      = []
    for col, val in [
        ("name",          body.name),
        ("description",   body.description),
        ("system_prompt", body.system_prompt),
        ("provider",      body.provider),
        ("model",         body.model),
        ("tags",          body.tags),
    ]:
        if val is not None:
            fields.append(f"{col}=%s")
            values.append(val)
    if not fields:
        raise HTTPException(400, "Nothing to update")
    fields.append("updated_at=NOW()")
    values.append(role_id)

    with db.conn() as conn:
        with conn.cursor() as cur:
            if versioned_changed:
                cur.execute(
                    """INSERT INTO mng_agent_role_versions
                           (role_id, system_prompt, provider, model, changed_by, note)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (role_id, existing[1], existing[2], existing[3],
                     (user or {}).get("email", ""), body.note),
                )
            cur.execute(
                f"UPDATE mng_agent_roles SET {', '.join(fields)} WHERE id=%s",
                values,
            )
            cur.execute(
                """SELECT id, project, name, description, system_prompt,
                          provider, model, tags, is_active, created_at, updated_at
                   FROM mng_agent_roles WHERE id=%s""",
                (role_id,),
            )
            row = cur.fetchone()
    return _row_to_role(row, include_prompt=True)


# ── Soft delete ───────────────────────────────────────────────────────────────

@router.delete("/{role_id}")
async def delete_role(role_id: int, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE mng_agent_roles SET is_active=FALSE, updated_at=NOW() WHERE id=%s AND client_id=1",
                (role_id,),
            )
    return {"deleted": True, "role_id": role_id}


# ── Version history ───────────────────────────────────────────────────────────

@router.get("/{role_id}/versions")
async def get_versions(role_id: int, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, system_prompt, provider, model, changed_by, changed_at, note
                   FROM mng_agent_role_versions WHERE role_id=%s ORDER BY changed_at DESC""",
                (role_id,),
            )
            rows = cur.fetchall()
    return {
        "versions": [
            {
                "id":           r[0],
                "system_prompt": r[1],
                "provider":     r[2],
                "model":        r[3],
                "changed_by":   r[4],
                "changed_at":   r[5].isoformat() if r[5] else None,
                "note":         r[6],
            }
            for r in rows
        ]
    }


# ── Restore ───────────────────────────────────────────────────────────────────

@router.post("/{role_id}/restore/{version_id}")
async def restore_version(role_id: int, version_id: int, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT system_prompt, provider, model FROM mng_agent_role_versions WHERE id=%s AND role_id=%s",
                (version_id, role_id),
            )
            ver = cur.fetchone()
            if not ver:
                raise HTTPException(404, "Version not found")

            # Save current state before overwriting
            cur.execute(
                "SELECT system_prompt, provider, model FROM mng_agent_roles WHERE id=%s AND client_id=1",
                (role_id,),
            )
            cur_state = cur.fetchone()
            if cur_state:
                cur.execute(
                    """INSERT INTO mng_agent_role_versions
                           (role_id, system_prompt, provider, model, changed_by, note)
                       VALUES (%s, %s, %s, %s, %s, 'before restore')""",
                    (role_id, cur_state[0], cur_state[1], cur_state[2],
                     (user or {}).get("email", "")),
                )
            cur.execute(
                """UPDATE mng_agent_roles
                   SET system_prompt=%s, provider=%s, model=%s, updated_at=NOW()
                   WHERE id=%s AND client_id=1""",
                (ver[0], ver[1], ver[2], role_id),
            )
    return {"restored": True, "role_id": role_id, "version_id": version_id}
