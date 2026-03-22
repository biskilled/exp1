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
from core.database import db, build_update

# ── SQL ──────────────────────────────────────────────────────────────────────

_SQL_LIST_ROLES = (
    """SELECT id, project, name, description, system_prompt,
              provider, model, tags, is_active, created_at, updated_at,
              inputs, outputs, role_type, output_schema, auto_commit,
              COALESCE(tools, '[]'::jsonb), COALESCE(react, TRUE),
              COALESCE(max_iterations, 10)
       FROM mng_agent_roles
       WHERE client_id=1 AND is_active=TRUE AND (project='_global' OR project=%s)
       ORDER BY project DESC, name"""
)

_SQL_GET_ROLE_BY_ID = (
    """SELECT id, project, name, description, system_prompt,
              provider, model, tags, is_active, created_at, updated_at,
              inputs, outputs, role_type, output_schema, auto_commit,
              COALESCE(tools, '[]'::jsonb), COALESCE(react, TRUE),
              COALESCE(max_iterations, 10)
       FROM mng_agent_roles WHERE id=%s"""
)

_SQL_INSERT_ROLE = (
    """INSERT INTO mng_agent_roles
           (client_id, project, name, description, system_prompt, provider, model, tags,
            inputs, outputs, role_type, output_schema, auto_commit,
            tools, react, max_iterations)
       VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
       RETURNING id, project, name, description, system_prompt,
                 provider, model, tags, is_active, created_at, updated_at,
                 inputs, outputs, role_type, output_schema, auto_commit,
                 COALESCE(tools, '[]'::jsonb), COALESCE(react, TRUE),
                 COALESCE(max_iterations, 10)"""
)

_SQL_DELETE_ROLE = (
    "UPDATE mng_agent_roles SET is_active=FALSE, updated_at=NOW() WHERE id=%s AND client_id=1"
)

_SQL_INSERT_ROLE_VERSION = (
    """INSERT INTO mng_agent_role_versions
           (role_id, system_prompt, provider, model, changed_by, note, tools)
       VALUES (%s, %s, %s, %s, %s, %s, %s)"""
)

_SQL_LIST_ROLE_VERSIONS = (
    """SELECT id, system_prompt, provider, model, changed_by, changed_at, note
       FROM mng_agent_role_versions WHERE role_id=%s ORDER BY changed_at DESC"""
)

_SQL_GET_ROLE_FOR_UPDATE = (
    """SELECT id, system_prompt, provider, model,
              COALESCE(tools, '[]'::jsonb), COALESCE(react, TRUE),
              COALESCE(max_iterations, 10)
       FROM mng_agent_roles WHERE id=%s AND client_id=1"""
)

_SQL_GET_VERSION_BY_ID = (
    "SELECT system_prompt, provider, model FROM mng_agent_role_versions WHERE id=%s AND role_id=%s"
)

_SQL_GET_ROLE_CURRENT_STATE = (
    "SELECT system_prompt, provider, model FROM mng_agent_roles WHERE id=%s AND client_id=1"
)

_SQL_RESTORE_ROLE = (
    """UPDATE mng_agent_roles
       SET system_prompt=%s, provider=%s, model=%s, updated_at=NOW()
       WHERE id=%s AND client_id=1"""
)

# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()

# Built-in fallback roles — returned when PostgreSQL is unavailable.
# Mirrors the 10 roles seeded by database._seed_agent_roles().
_BUILTIN_ROLES = [
    {"id": None, "project": "_global", "name": "Product Manager",
     "description": "Produces a concise task spec with acceptance criteria.",
     "provider": "claude", "model": "claude-haiku-4-5-20251001",
     "role_type": "agent", "tags": [], "is_active": True,
     "inputs": [], "outputs": [], "output_schema": None, "auto_commit": False,
     "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Sr. Architect",
     "description": "Produces a concise numbered implementation plan with file paths.",
     "provider": "claude", "model": "claude-sonnet-4-6",
     "role_type": "system_designer", "tags": [], "is_active": True,
     "inputs": [], "outputs": [], "output_schema": None, "auto_commit": False,
     "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Web Developer",
     "description": "Implements full-stack features; outputs complete files ready to commit.",
     "provider": "claude", "model": "claude-sonnet-4-6",
     "role_type": "developer", "tags": [], "is_active": True,
     "inputs": [], "outputs": [], "output_schema": None, "auto_commit": True,
     "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Backend Developer",
     "description": "Writes server-side code: APIs, DB schemas, business logic; auto-commits.",
     "provider": "deepseek", "model": "deepseek-chat",
     "role_type": "developer", "tags": [], "is_active": True,
     "inputs": [], "outputs": [], "output_schema": None, "auto_commit": True,
     "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Frontend Developer",
     "description": "Writes client-side code: UI components, styles, interactions; auto-commits.",
     "provider": "openai", "model": "gpt-4o",
     "role_type": "developer", "tags": [], "is_active": True,
     "inputs": [], "outputs": [], "output_schema": None, "auto_commit": True,
     "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "DevOps Engineer",
     "description": "Writes CI/CD configs, Dockerfiles, deployment infrastructure; auto-commits.",
     "provider": "claude", "model": "claude-haiku-4-5-20251001",
     "role_type": "developer", "tags": [], "is_active": True,
     "inputs": [], "outputs": [], "output_schema": None, "auto_commit": True,
     "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Code Reviewer",
     "description": "Reviews code quality; returns score + issues as JSON.",
     "provider": "claude", "model": "claude-sonnet-4-6",
     "role_type": "reviewer", "tags": [], "is_active": True,
     "inputs": [], "outputs": [], "output_schema": None, "auto_commit": False,
     "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Security Reviewer",
     "description": "Audits code for OWASP Top 10 vulnerabilities; returns JSON.",
     "provider": "claude", "model": "claude-haiku-4-5-20251001",
     "role_type": "reviewer", "tags": [], "is_active": True,
     "inputs": [], "outputs": [], "output_schema": None, "auto_commit": False,
     "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "QA Engineer",
     "description": "Writes comprehensive test cases including edge cases.",
     "provider": "openai", "model": "gpt-4o",
     "role_type": "agent", "tags": [], "is_active": True,
     "inputs": [], "outputs": [], "output_schema": None, "auto_commit": False,
     "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "AWS Architect",
     "description": "Designs AWS infrastructure using CDK/CloudFormation.",
     "provider": "claude", "model": "claude-sonnet-4-6",
     "role_type": "developer", "tags": [], "is_active": True,
     "inputs": [], "outputs": [], "output_schema": None, "auto_commit": True,
     "created_at": None, "updated_at": None},
]


def _require_db():
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL required for agent roles")


def _is_admin(user) -> bool:
    return bool(user and (user.get("is_admin") or user.get("role") == "admin"))


def _require_admin(user):
    if not _is_admin(user):
        raise HTTPException(403, "Admin access required")


def _row_to_role(row, include_prompt: bool = True) -> dict:
    import json as _json
    _tools_raw = row[16] if len(row) > 16 else []
    if isinstance(_tools_raw, str):
        try:
            _tools_raw = _json.loads(_tools_raw)
        except Exception:
            _tools_raw = []
    r = {
        "id":             row[0],
        "project":        row[1],
        "name":           row[2],
        "description":    row[3],
        "provider":       row[5],
        "model":          row[6],
        "tags":           row[7] or [],
        "is_active":      row[8],
        "created_at":     row[9].isoformat()  if row[9]  else None,
        "updated_at":     row[10].isoformat() if row[10] else None,
        "inputs":         row[11] if len(row) > 11 and row[11] is not None else [],
        "outputs":        row[12] if len(row) > 12 and row[12] is not None else [],
        "role_type":      row[13] if len(row) > 13 and row[13] else "agent",
        "output_schema":  row[14] if len(row) > 14 else None,
        "auto_commit":    row[15] if len(row) > 15 else False,
        "tools":          _tools_raw if isinstance(_tools_raw, list) else [],
        "react":          bool(row[17]) if len(row) > 17 else True,
        "max_iterations": int(row[18]) if len(row) > 18 else 10,
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
    admin = _is_admin(user)
    if not db.is_available():
        return {"roles": _BUILTIN_ROLES, "is_admin": admin, "fallback": True}
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_ROLES, (project,))
            rows = cur.fetchall()
    return {
        "roles": [_row_to_role(r, include_prompt=admin) for r in rows],
        "is_admin": admin,
    }


# ── Create ────────────────────────────────────────────────────────────────────

class RoleCreate(BaseModel):
    project:        str       = "_global"
    name:           str
    description:    str       = ""
    system_prompt:  str       = ""
    provider:       str       = "claude"
    model:          str       = ""
    tags:           list[str] = []
    inputs:         list      = []
    outputs:        list      = []
    role_type:      str       = "agent"
    output_schema:  Optional[dict] = None
    auto_commit:    bool      = False
    tools:          list[str] = []
    react:          bool      = True
    max_iterations: int       = 10


@router.post("/")
async def create_role(body: RoleCreate, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    import json as _json
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_INSERT_ROLE,
                (body.project, body.name, body.description, body.system_prompt,
                 body.provider, body.model, body.tags,
                 _json.dumps(body.inputs), _json.dumps(body.outputs),
                 body.role_type,
                 _json.dumps(body.output_schema) if body.output_schema else None,
                 body.auto_commit,
                 _json.dumps(body.tools), body.react, body.max_iterations),
            )
            row = cur.fetchone()
    return _row_to_role(row, include_prompt=True)


# ── Update (auto-versions on prompt/model/provider change) ────────────────────

class RoleUpdate(BaseModel):
    name:           Optional[str]       = None
    description:    Optional[str]       = None
    system_prompt:  Optional[str]       = None
    provider:       Optional[str]       = None
    model:          Optional[str]       = None
    tags:           Optional[list[str]] = None
    inputs:         Optional[list]      = None
    outputs:        Optional[list]      = None
    role_type:      Optional[str]       = None
    output_schema:  Optional[dict]      = None
    auto_commit:    Optional[bool]      = None
    tools:          Optional[list[str]] = None
    react:          Optional[bool]      = None
    max_iterations: Optional[int]       = None
    note:           str                 = ""


@router.patch("/{role_id}")
async def update_role(role_id: int, body: RoleUpdate, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)

    # Load current values for version comparison
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_ROLE_FOR_UPDATE, (role_id,))
            existing = cur.fetchone()
    if not existing:
        raise HTTPException(404, "Role not found")

    import json as _json
    versioned_changed = (
        (body.system_prompt is not None and body.system_prompt != existing[1]) or
        (body.provider      is not None and body.provider      != existing[2]) or
        (body.model         is not None and body.model         != existing[3])
    )
    existing_tools = existing[4] if len(existing) > 4 else []

    fields: list[str] = []
    values: list      = []
    for col, val in [
        ("name",           body.name),
        ("description",    body.description),
        ("system_prompt",  body.system_prompt),
        ("provider",       body.provider),
        ("model",          body.model),
        ("tags",           body.tags),
        ("role_type",      body.role_type),
        ("auto_commit",    body.auto_commit),
        ("react",          body.react),
        ("max_iterations", body.max_iterations),
    ]:
        if val is not None:
            fields.append(f"{col}=%s")
            values.append(val)
    if body.inputs is not None:
        fields.append("inputs=%s")
        values.append(_json.dumps(body.inputs))
    if body.outputs is not None:
        fields.append("outputs=%s")
        values.append(_json.dumps(body.outputs))
    if body.output_schema is not None:
        fields.append("output_schema=%s")
        values.append(_json.dumps(body.output_schema))
    if body.tools is not None:
        fields.append("tools=%s")
        values.append(_json.dumps(body.tools))
    if not fields:
        raise HTTPException(400, "Nothing to update")
    fields.append("updated_at=NOW()")
    values.append(role_id)

    with db.conn() as conn:
        with conn.cursor() as cur:
            if versioned_changed:
                cur.execute(
                    _SQL_INSERT_ROLE_VERSION,
                    (role_id, existing[1], existing[2], existing[3],
                     (user or {}).get("email", ""), body.note,
                     _json.dumps(existing_tools) if isinstance(existing_tools, list) else existing_tools),
                )
            cur.execute(
                f"UPDATE mng_agent_roles SET {', '.join(fields)} WHERE id=%s",
                values,
            )
            cur.execute(_SQL_GET_ROLE_BY_ID, (role_id,))
            row = cur.fetchone()
    return _row_to_role(row, include_prompt=True)


# ── Soft delete ───────────────────────────────────────────────────────────────

@router.delete("/{role_id}")
async def delete_role(role_id: int, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_DELETE_ROLE, (role_id,))
    return {"deleted": True, "role_id": role_id}


# ── Version history ───────────────────────────────────────────────────────────

@router.get("/{role_id}/versions")
async def get_versions(role_id: int, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_ROLE_VERSIONS, (role_id,))
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
            cur.execute(_SQL_GET_VERSION_BY_ID, (version_id, role_id))
            ver = cur.fetchone()
            if not ver:
                raise HTTPException(404, "Version not found")

            # Save current state before overwriting
            cur.execute(_SQL_GET_ROLE_CURRENT_STATE, (role_id,))
            cur_state = cur.fetchone()
            if cur_state:
                cur.execute(
                    _SQL_INSERT_ROLE_VERSION,
                    (role_id, cur_state[0], cur_state[1], cur_state[2],
                     (user or {}).get("email", ""), "before restore", "[]"),
                )
            cur.execute(_SQL_RESTORE_ROLE, (ver[0], ver[1], ver[2], role_id))
    return {"restored": True, "role_id": role_id, "version_id": version_id}


# ── Available tools registry ──────────────────────────────────────────────────

@router.get("/available-tools")
async def list_available_tools():
    """Return all registered agent tool names + descriptions (for UI checkboxes)."""
    from agents.tools import AGENT_TOOLS
    tools = []
    for name, entry in AGENT_TOOLS.items():
        defn = entry["definition"]
        # Infer category from tool name prefix
        if name.startswith("git_"):
            category = "git"
        elif name in ("read_file", "write_file", "list_dir"):
            category = "file"
        elif name in ("search_memory", "get_recent_history", "get_project_facts"):
            category = "memory"
        elif name in ("list_work_items", "create_work_item"):
            category = "work_items"
        else:
            category = "other"
        tools.append({
            "name":        name,
            "description": defn.get("description", ""),
            "category":    category,
        })
    return {"tools": tools}


# ── Sync YAML → DB ────────────────────────────────────────────────────────────

class SyncYamlBody(BaseModel):
    yaml_content: str
    project:      str = "_global"


@router.post("/sync-yaml")
async def sync_yaml(body: SyncYamlBody, user=Depends(get_optional_user)):
    """Parse a YAML role definition and upsert it into the DB."""
    _require_db()
    _require_admin(user)
    try:
        import yaml as _yaml
        import json as _json
        data = _yaml.safe_load(body.yaml_content)
    except Exception as e:
        raise HTTPException(400, f"Invalid YAML: {e}")

    if not data or not isinstance(data, dict):
        raise HTTPException(400, "YAML must be a mapping")
    name = data.get("name", "").strip()
    if not name:
        raise HTTPException(400, "YAML must have a 'name' field")

    tools          = data.get("tools", [])
    react          = bool(data.get("react", True))
    max_iterations = int(data.get("max_iterations", 10))
    provider       = data.get("provider", "claude")
    model          = data.get("model", "")
    role_type      = data.get("role_type", "agent")
    description    = data.get("description", "")
    system_prompt  = data.get("system_prompt", "")
    auto_commit    = bool(data.get("auto_commit", False))
    inputs         = data.get("inputs", [])
    outputs        = data.get("outputs", [])
    project        = body.project

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO mng_agent_roles
                       (client_id, project, name, description, system_prompt,
                        provider, model, role_type, auto_commit,
                        tools, react, max_iterations,
                        inputs, outputs)
                   VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (client_id, project, name) DO UPDATE SET
                       description    = EXCLUDED.description,
                       system_prompt  = EXCLUDED.system_prompt,
                       provider       = EXCLUDED.provider,
                       model          = EXCLUDED.model,
                       role_type      = EXCLUDED.role_type,
                       auto_commit    = EXCLUDED.auto_commit,
                       tools          = EXCLUDED.tools,
                       react          = EXCLUDED.react,
                       max_iterations = EXCLUDED.max_iterations,
                       inputs         = EXCLUDED.inputs,
                       outputs        = EXCLUDED.outputs,
                       updated_at     = NOW()
                   RETURNING id""",
                (project, name, description, system_prompt,
                 provider, model, role_type, auto_commit,
                 _json.dumps(tools), react, max_iterations,
                 _json.dumps(inputs), _json.dumps(outputs)),
            )
            row = cur.fetchone()
    return {
        "synced": True,
        "name":   name,
        "id":     row[0] if row else None,
        "tools":  len(tools),
        "react":  react,
        "max_iterations": max_iterations,
        "message": f"Role '{name}' synced ({len(tools)} tools, react={react}, max_iter={max_iterations})",
    }


# ── Export YAML ───────────────────────────────────────────────────────────────

@router.get("/{role_id}/export-yaml")
async def export_yaml(role_id: int, user=Depends(get_optional_user)):
    """Serialize a DB role to YAML string."""
    _require_db()
    from fastapi.responses import PlainTextResponse
    import json as _json
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_ROLE_BY_ID, (role_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Role not found")
    role = _row_to_role(row, include_prompt=True)

    try:
        import yaml as _yaml
    except ImportError:
        raise HTTPException(500, "PyYAML not installed")

    doc = {
        "name":           role["name"],
        "description":    role.get("description", ""),
        "provider":       role.get("provider", "claude"),
        "model":          role.get("model", ""),
        "role_type":      role.get("role_type", "agent"),
        "react":          role.get("react", True),
        "max_iterations": role.get("max_iterations", 10),
        "auto_commit":    role.get("auto_commit", False),
        "tools":          role.get("tools", []),
        "inputs":         role.get("inputs", []),
        "outputs":        role.get("outputs", []),
        "system_prompt":  role.get("system_prompt", ""),
    }
    yaml_str = _yaml.dump(doc, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return PlainTextResponse(yaml_str, media_type="text/yaml")
