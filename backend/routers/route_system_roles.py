"""
system_roles.py — Reusable prompt fragments that compose onto agent roles.

System roles are admin-managed text blocks (coding standards, security rules, etc.)
that get prepended to an agent role's system_prompt when a graph node executes.

Routes:
  GET    /system-roles/                              list all
  POST   /system-roles/                              create (admin)
  POST   /system-roles/reset-defaults               delete all + seed 3 canonical ones (admin)
  PATCH  /system-roles/{id}                          update (admin)
  DELETE /system-roles/{id}                          soft-delete is_active=FALSE (admin)
  GET    /system-roles/agent-roles/{role_id}/links   list system roles linked to an agent role (includes content)
  POST   /system-roles/agent-roles/{role_id}/links   attach system role (admin)
  DELETE /system-roles/agent-roles/{role_id}/links/{system_role_id}  detach (admin)
"""
from __future__ import annotations

import pathlib
from typing import Optional

import yaml
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.auth import get_optional_user
from core.database import db, build_update

# Path to system_prompts.yaml (canonical preset definitions)
_TEMPLATES_DIR      = pathlib.Path(__file__).resolve().parent.parent.parent / "workspace" / "_templates" / "pipelines"
_SYSTEM_PROMPTS_YAML = _TEMPLATES_DIR / "system_prompts.yaml"

# ── SQL ──────────────────────────────────────────────────────────────────────

_SQL_LIST_SYSTEM_ROLES = (
    """SELECT id, name, description, content, category, is_active, created_at, updated_at
       FROM mng_system_roles
       WHERE client_id=1 AND is_active=TRUE
       ORDER BY category, name"""
)

_SQL_INSERT_SYSTEM_ROLE = (
    """INSERT INTO mng_system_roles (client_id, name, description, content, category)
       VALUES (1, %s, %s, %s, %s)
       RETURNING id, name, description, content, category, is_active, created_at, updated_at"""
)

_SQL_GET_SYSTEM_ROLE_BY_ID = (
    """SELECT id, name, description, content, category, is_active, created_at, updated_at
       FROM mng_system_roles WHERE id=%s"""
)

_SQL_DELETE_SYSTEM_ROLE = (
    "UPDATE mng_system_roles SET is_active=FALSE, updated_at=NOW() WHERE id=%s AND client_id=1"
)

_SQL_LIST_SYSTEM_ROLE_LINKS = (
    """SELECT sr.id, sr.name, sr.description, sr.category, l.order_index, sr.content
       FROM mng_role_system_links l
       JOIN mng_system_roles sr ON sr.id = l.system_role_id
       WHERE l.role_id = %s AND sr.is_active = TRUE
       ORDER BY l.order_index ASC, l.id ASC"""
)

_SQL_INSERT_ROLE_SYSTEM_LINK = (
    """INSERT INTO mng_role_system_links (role_id, system_role_id, order_index)
       VALUES (%s, %s, %s)
       ON CONFLICT (role_id, system_role_id) DO UPDATE SET order_index=EXCLUDED.order_index
       RETURNING id, role_id, system_role_id, order_index"""
)

_SQL_DELETE_ROLE_SYSTEM_LINK = (
    "DELETE FROM mng_role_system_links WHERE role_id=%s AND system_role_id=%s"
)

# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()

# Built-in fallback system roles — returned when PostgreSQL is unavailable.
# Mirrors the 7 roles seeded by database._seed_system_roles().
_BUILTIN_SYSTEM_ROLES = [
    {"id": None, "name": "coding_standards",     "category": "quality",      "is_active": True, "created_at": None, "updated_at": None,
     "description": "Clean code conventions, OOP, type hints, docstrings, DRY/SOLID principles."},
    {"id": None, "name": "output_format",        "category": "output",       "is_active": True, "created_at": None, "updated_at": None,
     "description": "Save all outputs to output/[feature]_YYMMDD_HHMMSS.md."},
    {"id": None, "name": "security_principles",  "category": "security",     "is_active": True, "created_at": None, "updated_at": None,
     "description": "OWASP Top 10, parameterised SQL, no hardcoded secrets."},
    {"id": None, "name": "reviewer_standards",   "category": "review",       "is_active": True, "created_at": None, "updated_at": None,
     "description": "Verify all ACs, list tested items, score 1-10, return JSON."},
    {"id": None, "name": "doc_output_format",    "category": "output",       "is_active": True, "created_at": None, "updated_at": None,
     "description": "Keep docs short, use bullets, include Task/Description/AC or Plan headings."},
    {"id": None, "name": "dev_code_format",      "category": "development",  "is_active": True, "created_at": None, "updated_at": None,
     "description": "Output complete files using ### File: path\\n```lang blocks; add Summary."},
    {"id": None, "name": "dev_naming_conventions","category": "development", "is_active": True, "created_at": None, "updated_at": None,
     "description": "mng_ global tables, pr_ project tables, snake_case, no abbreviations."},
]


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
    admin = _is_admin(user)
    if not db.is_available():
        return {"system_roles": _BUILTIN_SYSTEM_ROLES, "is_admin": admin, "fallback": True}
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_SYSTEM_ROLES)
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
                _SQL_INSERT_SYSTEM_ROLE,
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

    update_fields = {k: v for k, v in {
        "name":        body.name,
        "description": body.description,
        "content":     body.content,
        "category":    body.category,
    }.items() if v is not None}
    if not update_fields:
        raise HTTPException(400, "Nothing to update")
    set_clause, vals = build_update(update_fields)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE mng_system_roles SET {set_clause}, updated_at=NOW() WHERE id=%s AND client_id=1",
                vals + [system_role_id],
            )
            cur.execute(_SQL_GET_SYSTEM_ROLE_BY_ID, (system_role_id,))
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
            cur.execute(_SQL_DELETE_SYSTEM_ROLE, (system_role_id,))
    return {"deleted": True, "system_role_id": system_role_id}


# ── Links: list ───────────────────────────────────────────────────────────────

@router.get("/agent-roles/{role_id}/links")
async def list_links(role_id: int, user=Depends(get_optional_user)):
    _require_db()
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_SYSTEM_ROLE_LINKS, (role_id,))
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
                "content":     r[5] or "",
            }
            for r in rows
        ],
    }


# ── Reset to canonical defaults ───────────────────────────────────────────────

@router.post("/reset-defaults")
async def reset_system_role_defaults(user=Depends(get_optional_user)):
    """Delete all system roles and re-seed the 3 canonical ones from system_prompts.yaml."""
    _require_db()
    _require_admin(user)

    # Load presets from YAML
    presets: list[dict] = []
    if _SYSTEM_PROMPTS_YAML.exists():
        with open(_SYSTEM_PROMPTS_YAML) as f:
            data = yaml.safe_load(f) or {}
        presets = data.get("presets", [])

    if not presets:
        raise HTTPException(400, "system_prompts.yaml not found or has no presets")

    # Map preset category names to system role categories
    _cat_map = {
        "coding_general":    "quality",
        "design_and_planning": "general",
        "review_and_quality":  "review",
    }

    with db.conn() as conn:
        with conn.cursor() as cur:
            # Soft-delete all existing system roles
            cur.execute("UPDATE mng_system_roles SET is_active=FALSE, updated_at=NOW() WHERE client_id=1")
            deleted = cur.rowcount

            # Insert 3 canonical ones
            created = 0
            for p in presets:
                name     = p.get("name", "")
                label    = p.get("label", name)
                content  = p.get("content", "").strip()
                desc     = p.get("description", label)
                category = _cat_map.get(name, "general")
                if not name or not content:
                    continue
                cur.execute(
                    _SQL_INSERT_SYSTEM_ROLE,
                    (label, desc, content, category),
                )
                created += 1

    return {"ok": True, "deleted": deleted, "created": created}


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
                _SQL_INSERT_ROLE_SYSTEM_LINK,
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
            cur.execute(_SQL_DELETE_ROLE_SYSTEM_LINK, (role_id, system_role_id))
    return {"detached": True, "role_id": role_id, "system_role_id": system_role_id}
