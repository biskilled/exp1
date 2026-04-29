"""
agent_roles.py — Agent role library with version history.

Roles define the system prompt, provider, and model for a workflow node.
- All users: see name + description only (full definition is admin-only).
- Admin:     full CRUD including system_prompt, tools, version history.

Routes:
  GET    /agent-roles                       list roles (name+desc for users, full for admins)
  POST   /agent-roles                       create (admin only)
  PATCH  /agent-roles/{id}                  edit + validate (admin only)
  DELETE /agent-roles/{id}                  soft-delete (admin only)
  GET    /agent-roles/{id}/versions         version history (admin only)
  POST   /agent-roles/{id}/restore/{vid}    restore to previous version (admin only)
  GET    /agent-roles/providers             list LLM providers + models from providers.yaml (no auth)
  GET    /agent-roles/available-tools       list all registered tool names + categories
  POST   /agent-roles/validate-yaml         validate YAML without writing to DB (admin only)
  POST   /agent-roles/sync-yaml             validate + upsert role from YAML (admin only)
  GET    /agent-roles/{id}/export-yaml      export role to YAML (admin only)

MCP Catalog routes:
  GET    /agent-roles/mcp-catalog           read project mcp_catalog.yaml (fallback to _templates)
  PUT    /agent-roles/mcp-catalog           write project mcp_catalog.yaml
  GET    /agent-roles/mcp-active            list active MCP server names from .mcp.json
  POST   /agent-roles/mcp-activate          add/update server in .mcp.json
  DELETE /agent-roles/mcp-activate/{name}   remove server from .mcp.json
  GET    /agent-roles/mcp-usage             list roles that reference a given MCP
"""
from __future__ import annotations

import json as _json
import logging
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.auth import get_optional_user
from core.database import db, build_update
from core import project_paths

log = logging.getLogger(__name__)

_PROVIDERS_FILE = Path(__file__).parent.parent / "agents" / "yaml_config" / "providers.yaml"
_TEMPLATES_PIPELINES_DIR = Path(__file__).parent.parent.parent / "workspace" / "_templates" / "pipelines"

# ── Validation constants ──────────────────────────────────────────────────────

_KNOWN_FIELDS = {
    "name", "description", "system_prompt", "provider", "model",
    "auto_commit", "max_iterations",
    "tools", "mcp_tools", "output_schema", "tags",
}


def _load_providers() -> list[dict]:
    """Load provider list from providers.yaml. Returns list of {id, label, models} dicts."""
    try:
        import yaml as _yaml
        data = _yaml.safe_load(_PROVIDERS_FILE.read_text()) if _PROVIDERS_FILE.exists() else {}
        return data.get("providers", []) if isinstance(data, dict) else []
    except Exception as e:
        log.warning(f"providers.yaml load error: {e}")
        return []


def _valid_providers() -> set[str]:
    """Set of valid provider ids, loaded live from providers.yaml."""
    providers = _load_providers()
    if providers:
        return {p["id"] for p in providers}
    # Fallback if YAML missing
    return {"claude", "anthropic", "openai", "deepseek", "gemini", "grok", "xai", "ollama"}


def _validate_role_data(data: dict) -> list[str]:
    """Validate a role definition dict (from YAML or PATCH body).

    Returns a list of human-readable error strings. Empty list = valid.
    """
    errors: list[str] = []

    # Unknown top-level keys (catches typos like 'provder')
    unknown = set(data.keys()) - _KNOWN_FIELDS
    if unknown:
        errors.append(f"Unknown field(s): {', '.join(sorted(unknown))}. "
                      f"Known: {', '.join(sorted(_KNOWN_FIELDS))}")

    # name
    if "name" in data and not str(data.get("name", "")).strip():
        errors.append("'name' must not be empty")

    # provider — loaded live from providers.yaml
    prov = data.get("provider")
    if prov:
        valid_p = _valid_providers()
        if prov not in valid_p:
            errors.append(f"'provider' value '{prov}' is not recognised. "
                          f"Valid: {', '.join(sorted(valid_p))}")

    # max_iterations
    max_it = data.get("max_iterations")
    if max_it is not None:
        if not isinstance(max_it, int) or max_it < 1 or max_it > 100:
            errors.append("'max_iterations' must be an integer between 1 and 100")

    # tools — validate against registered AGENT_TOOLS; mcp: prefixed entries are exempt
    tools = data.get("tools")
    if tools is not None:
        if not isinstance(tools, list):
            errors.append("'tools' must be a list of tool name strings")
        else:
            builtin = [t for t in tools if not str(t).startswith("mcp:")]
            try:
                from agents.tools import AGENT_TOOLS
                unknown_tools = [t for t in builtin if t not in AGENT_TOOLS]
                if unknown_tools:
                    errors.append(
                        f"Unknown tool(s): {', '.join(unknown_tools)}. "
                        f"Registered: {', '.join(sorted(AGENT_TOOLS))}"
                    )
            except ImportError:
                pass  # tools module not available (test env)

    # mcp_tools — list of {server, tools?} or plain strings
    mcp_tools = data.get("mcp_tools")
    if mcp_tools is not None and not isinstance(mcp_tools, list):
        errors.append("'mcp_tools' must be a list")

    return errors

# ── SQL ──────────────────────────────────────────────────────────────────────

_SQL_LIST_ROLES = (
    """SELECT ar.id, p.name AS project, ar.name, ar.description, ar.system_prompt,
              ar.provider, ar.model, ar.tags, ar.is_active, ar.created_at, ar.updated_at,
              ar.output_schema, ar.auto_commit,
              COALESCE(ar.tools, '[]'::jsonb), COALESCE(ar.max_iterations, 10)
       FROM mng_agent_roles ar
       JOIN mng_projects p ON p.id = ar.project_id
       WHERE ar.is_active=TRUE AND (ar.project_id=%s OR ar.project_id=%s)
       ORDER BY ar.project_id DESC, ar.name"""
)

_SQL_GET_ROLE_BY_ID = (
    """SELECT ar.id, p.name AS project, ar.name, ar.description, ar.system_prompt,
              ar.provider, ar.model, ar.tags, ar.is_active, ar.created_at, ar.updated_at,
              ar.output_schema, ar.auto_commit,
              COALESCE(ar.tools, '[]'::jsonb), COALESCE(ar.max_iterations, 10)
       FROM mng_agent_roles ar
       JOIN mng_projects p ON p.id = ar.project_id
       WHERE ar.id=%s"""
)

_SQL_INSERT_ROLE = (
    """WITH ins AS (
       INSERT INTO mng_agent_roles
           (project_id, name, description, system_prompt, provider, model, tags,
            output_schema, auto_commit, tools, max_iterations)
       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
       RETURNING id, project_id, name, description, system_prompt,
                 provider, model, tags, is_active, created_at, updated_at,
                 output_schema, auto_commit,
                 COALESCE(tools, '[]'::jsonb), COALESCE(max_iterations, 10)
    )
    SELECT ins.id, p.name AS project, ins.name, ins.description, ins.system_prompt,
           ins.provider, ins.model, ins.tags, ins.is_active, ins.created_at, ins.updated_at,
           ins.output_schema, ins.auto_commit,
           ins.tools, ins.max_iterations
    FROM ins JOIN mng_projects p ON p.id = ins.project_id"""
)

_SQL_DELETE_ROLE = (
    "UPDATE mng_agent_roles SET is_active=FALSE, updated_at=NOW() WHERE id=%s"
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
              COALESCE(tools, '[]'::jsonb)
       FROM mng_agent_roles WHERE id=%s"""
)

_SQL_GET_VERSION_BY_ID = (
    "SELECT system_prompt, provider, model FROM mng_agent_role_versions WHERE id=%s AND role_id=%s"
)

_SQL_GET_ROLE_CURRENT_STATE = (
    "SELECT system_prompt, provider, model FROM mng_agent_roles WHERE id=%s"
)

_SQL_RESTORE_ROLE = (
    """UPDATE mng_agent_roles
       SET system_prompt=%s, provider=%s, model=%s, updated_at=NOW()
       WHERE id=%s"""
)

# ─────────────────────────────────────────────────────────────────────────────

router = APIRouter()

# Built-in fallback roles — returned when PostgreSQL is unavailable.
# Mirrors the 10 roles seeded by database._seed_agent_roles().
_BUILTIN_ROLES = [
    {"id": None, "project": "_global", "name": "Product Manager",
     "description": "Produces a concise task spec with acceptance criteria.",
     "system_prompt": "", "provider": "claude", "model": "claude-haiku-4-5-20251001",
     "tags": [], "is_active": True, "output_schema": None, "auto_commit": False,
     "tools": [], "max_iterations": 10, "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Sr. Architect",
     "description": "Produces a concise numbered implementation plan with file paths.",
     "system_prompt": "", "provider": "claude", "model": "claude-sonnet-4-6",
     "tags": [], "is_active": True, "output_schema": None, "auto_commit": False,
     "tools": [], "max_iterations": 10, "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Web Developer",
     "description": "Implements full-stack features; outputs complete files ready to commit.",
     "system_prompt": "", "provider": "claude", "model": "claude-sonnet-4-6",
     "tags": [], "is_active": True, "output_schema": None, "auto_commit": True,
     "tools": [], "max_iterations": 10, "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Backend Developer",
     "description": "Writes server-side code: APIs, DB schemas, business logic; auto-commits.",
     "system_prompt": "", "provider": "deepseek", "model": "deepseek-chat",
     "tags": [], "is_active": True, "output_schema": None, "auto_commit": True,
     "tools": [], "max_iterations": 10, "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Frontend Developer",
     "description": "Writes client-side code: UI components, styles, interactions; auto-commits.",
     "system_prompt": "", "provider": "openai", "model": "gpt-4o",
     "tags": [], "is_active": True, "output_schema": None, "auto_commit": True,
     "tools": [], "max_iterations": 10, "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "DevOps Engineer",
     "description": "Writes CI/CD configs, Dockerfiles, deployment infrastructure; auto-commits.",
     "system_prompt": "", "provider": "claude", "model": "claude-haiku-4-5-20251001",
     "tags": [], "is_active": True, "output_schema": None, "auto_commit": True,
     "tools": [], "max_iterations": 10, "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Code Reviewer",
     "description": "Reviews code quality; returns score + issues as JSON.",
     "system_prompt": "", "provider": "claude", "model": "claude-sonnet-4-6",
     "tags": [], "is_active": True, "output_schema": None, "auto_commit": False,
     "tools": [], "max_iterations": 10, "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "Security Reviewer",
     "description": "Audits code for OWASP Top 10 vulnerabilities; returns JSON.",
     "system_prompt": "", "provider": "claude", "model": "claude-haiku-4-5-20251001",
     "tags": [], "is_active": True, "output_schema": None, "auto_commit": False,
     "tools": [], "max_iterations": 10, "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "QA Engineer",
     "description": "Writes comprehensive test cases including edge cases.",
     "system_prompt": "", "provider": "openai", "model": "gpt-4o",
     "tags": [], "is_active": True, "output_schema": None, "auto_commit": False,
     "tools": [], "max_iterations": 10, "created_at": None, "updated_at": None},
    {"id": None, "project": "_global", "name": "AWS Architect",
     "description": "Designs AWS infrastructure using CDK/CloudFormation.",
     "system_prompt": "", "provider": "claude", "model": "claude-sonnet-4-6",
     "tags": [], "is_active": True, "output_schema": None, "auto_commit": True,
     "tools": [], "max_iterations": 10, "created_at": None, "updated_at": None},
]


def _require_db():
    if not db.is_available():
        raise HTTPException(503, "PostgreSQL required for agent roles")


def _is_admin(user) -> bool:
    return bool(user and (user.get("is_admin") or user.get("role") == "admin"))


def _require_admin(user):
    if not _is_admin(user):
        raise HTTPException(403, "Admin access required")


def _row_to_role(row, admin: bool = False) -> dict:
    """Serialize a DB row to a role dict.

    Non-admin users receive ONLY id / name / description — the full definition
    (system_prompt, provider, model, tools, output schema) is
    admin-only so customers cannot reverse-engineer proprietary role logic.
    """
    r = {
        "id":          row[0],
        "name":        row[2],
        "description": row[3],
        "is_active":   row[8],
    }
    if not admin:
        return r

    import json as _json
    _tools_raw = row[13] if len(row) > 13 else []
    if isinstance(_tools_raw, str):
        try:
            _tools_raw = _json.loads(_tools_raw)
        except Exception:
            _tools_raw = []

    r.update({
        "project":        row[1],
        "system_prompt":  row[4],
        "provider":       row[5],
        "model":          row[6],
        "tags":           row[7] or [],
        "created_at":     row[9].isoformat()  if row[9]  else None,
        "updated_at":     row[10].isoformat() if row[10] else None,
        "output_schema":  row[11] if len(row) > 11 else None,
        "auto_commit":    row[12] if len(row) > 12 else False,
        "tools":          _tools_raw if isinstance(_tools_raw, list) else [],
        "max_iterations": int(row[14]) if len(row) > 14 else 10,
    })
    return r


# ── Static GET routes (must come before /{role_id} to avoid 405 on parameterised match) ──

@router.get("/providers")
async def list_providers_endpoint():
    """Return LLM provider + model list from providers.yaml. No auth required.

    UI uses this to populate provider/model dropdowns without hardcoding.
    """
    providers = _load_providers()
    return {"providers": providers}


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/")
async def list_roles(
    project: str = Query("_global"),
    user=Depends(get_optional_user),
):
    admin = _is_admin(user)
    if not db.is_available():
        # Non-admins get name/description only even from fallback list
        visible = (
            _BUILTIN_ROLES if admin
            else [{"id": r["id"], "name": r["name"], "description": r["description"],
                   "is_active": r.get("is_active", True)} for r in _BUILTIN_ROLES]
        )
        return {"roles": visible, "is_admin": admin, "fallback": True}
    global_pid = db.get_project_id('_global') or 0
    project_pid = db.get_or_create_project_id(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_LIST_ROLES, (global_pid, project_pid))
            rows = cur.fetchall()
    return {
        "roles": [_row_to_role(r, admin=admin) for r in rows],
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
    output_schema:  Optional[dict] = None
    auto_commit:    bool      = False
    tools:          list[str] = []
    max_iterations: int       = 10


@router.post("/")
async def create_role(body: RoleCreate, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)
    import json as _json
    project_id = db.get_or_create_project_id(body.project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_INSERT_ROLE,
                (project_id, body.name, body.description, body.system_prompt,
                 body.provider, body.model, body.tags,
                 _json.dumps(body.output_schema) if body.output_schema else None,
                 body.auto_commit,
                 _json.dumps(body.tools), body.max_iterations),
            )
            row = cur.fetchone()
    return _row_to_role(row, admin=True)


# ── Update (auto-versions on prompt/model/provider change) ────────────────────

class RoleUpdate(BaseModel):
    name:           Optional[str]       = None
    description:    Optional[str]       = None
    system_prompt:  Optional[str]       = None
    provider:       Optional[str]       = None
    model:          Optional[str]       = None
    tags:           Optional[list[str]] = None
    output_schema:  Optional[dict]      = None
    auto_commit:    Optional[bool]      = None
    tools:          Optional[list[str]] = None
    max_iterations: Optional[int]       = None
    note:           str                 = ""


@router.patch("/{role_id}")
async def update_role(role_id: int, body: RoleUpdate, user=Depends(get_optional_user)):
    _require_db()
    _require_admin(user)

    # Validate only the fields being updated
    patch_dict = {k: v for k, v in body.model_dump(exclude={"note"}).items() if v is not None}
    errors = _validate_role_data(patch_dict)
    if errors:
        raise HTTPException(422, {"errors": errors})

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
        ("auto_commit",    body.auto_commit),
        ("max_iterations", body.max_iterations),
    ]:
        if val is not None:
            fields.append(f"{col}=%s")
            values.append(val)
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
    return _row_to_role(row, admin=True)


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
    """Return all registered agent tool names + categories (for UI category bundles)."""
    from agents.tools import AGENT_TOOLS
    tools = []
    for name, entry in AGENT_TOOLS.items():
        tools.append({
            "name":        name,
            "description": entry["definition"].get("description", ""),
            "category":    entry.get("category", "other"),
        })
    return {"tools": tools}


# ── MCP Catalog helpers ───────────────────────────────────────────────────────

def _get_project_code_dir(project: str) -> str | None:
    """Return code_dir for a project from mng_projects. None if not found or DB unavailable."""
    if not db.is_available():
        return None
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT code_dir FROM mng_projects WHERE name=%s AND client_id=1 LIMIT 1",
                    (project,),
                )
                row = cur.fetchone()
        return row[0] if row else None
    except Exception as e:
        log.warning(f"_get_project_code_dir({project}): {e}")
        return None


def _load_mcp_catalog(project: str) -> list[dict]:
    """Load mcp_catalog.yaml — project-specific first, then _templates fallback."""
    import yaml as _yaml
    # Project-specific
    proj_file = project_paths.pipelines_dir(project) / "mcp_catalog.yaml"
    if proj_file.exists():
        try:
            data = _yaml.safe_load(proj_file.read_text()) or {}
            return data.get("mcps", [])
        except Exception as e:
            log.warning(f"mcp_catalog load error ({proj_file}): {e}")
    # Template fallback
    tmpl_file = _TEMPLATES_PIPELINES_DIR / "mcp_catalog.yaml"
    if tmpl_file.exists():
        try:
            data = _yaml.safe_load(tmpl_file.read_text()) or {}
            return data.get("mcps", [])
        except Exception as e:
            log.warning(f"mcp_catalog load error ({tmpl_file}): {e}")
    return []


def _save_mcp_catalog(project: str, mcps: list[dict]) -> None:
    """Write mcp_catalog.yaml to project pipelines dir."""
    import yaml as _yaml
    out_file = project_paths.pipelines_dir(project) / "mcp_catalog.yaml"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(_yaml.dump({"mcps": mcps}, allow_unicode=True, default_flow_style=False))


def _load_mcp_json(code_dir: str) -> dict:
    """Load .mcp.json from code_dir. Returns empty mcpServers dict if missing/invalid."""
    mcp_file = Path(code_dir) / ".mcp.json"
    if mcp_file.exists():
        try:
            return _json.loads(mcp_file.read_text())
        except Exception:
            pass
    return {"mcpServers": {}}


def _save_mcp_json(code_dir: str, data: dict) -> None:
    """Write .mcp.json to code_dir."""
    mcp_file = Path(code_dir) / ".mcp.json"
    mcp_file.write_text(_json.dumps(data, indent=2))


# ── MCP Catalog endpoints ─────────────────────────────────────────────────────

@router.get("/mcp-catalog")
async def get_mcp_catalog(project: str = Query("aicli")):
    """Return mcp_catalog.yaml for the project (falls back to _templates)."""
    mcps = _load_mcp_catalog(project)
    return {"mcps": mcps}


class McpCatalogBody(BaseModel):
    mcps: list[dict[str, Any]]


@router.put("/mcp-catalog")
async def put_mcp_catalog(body: McpCatalogBody, project: str = Query("aicli"), user=Depends(get_optional_user)):
    """Write mcp_catalog.yaml to workspace/{project}/pipelines/."""
    _require_admin(user)
    _save_mcp_catalog(project, body.mcps)
    return {"ok": True, "count": len(body.mcps)}


@router.get("/mcp-active")
async def get_mcp_active(project: str = Query("aicli")):
    """Return list of active MCP server names from project code_dir/.mcp.json."""
    code_dir = _get_project_code_dir(project)
    if not code_dir:
        return {"servers": []}
    data = _load_mcp_json(code_dir)
    return {"servers": list(data.get("mcpServers", {}).keys())}


class McpActivateBody(BaseModel):
    name:    str
    command: str
    args:    list[str] = []
    env:     dict[str, str] = {}


@router.post("/mcp-activate")
async def mcp_activate(body: McpActivateBody, project: str = Query("aicli")):
    """Add or update an MCP server in project code_dir/.mcp.json."""
    code_dir = _get_project_code_dir(project)
    if not code_dir:
        raise HTTPException(404, f"code_dir not found for project '{project}'")
    data = _load_mcp_json(code_dir)
    if "mcpServers" not in data:
        data["mcpServers"] = {}
    entry: dict[str, Any] = {"command": body.command, "args": body.args}
    if body.env:
        entry["env"] = body.env
    data["mcpServers"][body.name] = entry
    _save_mcp_json(code_dir, data)
    return {"ok": True, "name": body.name}


@router.delete("/mcp-activate/{name}")
async def mcp_deactivate(name: str, project: str = Query("aicli")):
    """Remove an MCP server from project code_dir/.mcp.json."""
    code_dir = _get_project_code_dir(project)
    if not code_dir:
        raise HTTPException(404, f"code_dir not found for project '{project}'")
    data = _load_mcp_json(code_dir)
    servers = data.get("mcpServers", {})
    if name not in servers:
        raise HTTPException(404, f"MCP server '{name}' not found in .mcp.json")
    del servers[name]
    _save_mcp_json(code_dir, data)
    return {"ok": True, "name": name}


@router.get("/mcp-usage")
async def get_mcp_usage(project: str = Query("aicli"), mcp_name: str = Query(...)):
    """Return agent roles that reference mcp:{mcp_name} in their tools array."""
    if not db.is_available():
        return {"roles": []}
    project_id = db.get_project_id(project)
    global_id = db.get_project_id("_global") or 0
    mcp_key = f"mcp:{mcp_name}"
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, name FROM mng_agent_roles
                       WHERE is_active=TRUE
                         AND (project_id=%s OR project_id=%s)
                         AND tools @> %s::jsonb""",
                    (project_id or 0, global_id, _json.dumps([mcp_key])),
                )
                rows = cur.fetchall()
        return {"roles": [{"id": r[0], "name": r[1]} for r in rows]}
    except Exception as e:
        log.warning(f"mcp_usage query error: {e}")
        return {"roles": []}


@router.get("/system-prompts")
async def get_system_prompts():
    """Return shared system prompt presets from _templates/pipelines/system_prompts.yaml."""
    import yaml as _yaml
    f = _TEMPLATES_PIPELINES_DIR / "system_prompts.yaml"
    if not f.exists():
        return {"presets": []}
    try:
        with open(f) as fh:
            data = _yaml.safe_load(fh)
        return {"presets": data.get("presets", [])}
    except Exception as e:
        log.warning(f"system_prompts load error: {e}")
        return {"presets": []}


# ── Shared YAML parse helper ──────────────────────────────────────────────────

def _parse_and_validate_yaml(yaml_content: str) -> tuple[dict, list[str]]:
    """Parse YAML string and run validation. Returns (data, errors).

    On YAML parse failure, errors contains a single parse-error string and
    data is an empty dict.
    """
    try:
        import yaml as _yaml
        data = _yaml.safe_load(yaml_content)
    except Exception as e:
        return {}, [f"YAML parse error: {e}"]

    if not data or not isinstance(data, dict):
        return {}, ["YAML must be a mapping (key: value pairs)"]

    errors = _validate_role_data(data)

    # 'name' required for DB operations
    if not data.get("name", "").strip():
        errors.append("'name' field is required")

    return data, errors


# ── Sync YAML → DB ────────────────────────────────────────────────────────────

class SyncYamlBody(BaseModel):
    yaml_content: str
    project:      str = "_global"


@router.post("/validate-yaml")
async def validate_yaml(body: SyncYamlBody, user=Depends(get_optional_user)):
    """Dry-run: parse and validate a YAML role definition without writing to DB.

    Returns {valid: bool, errors: [...], name: str|null}.
    Used by UI before Save and by CLI before push.
    """
    _require_admin(user)
    data, errors = _parse_and_validate_yaml(body.yaml_content)
    return {
        "valid":  len(errors) == 0,
        "errors": errors,
        "name":   data.get("name", "").strip() or None,
    }


@router.post("/sync-yaml")
async def sync_yaml(body: SyncYamlBody, user=Depends(get_optional_user)):
    """Validate + upsert a role from YAML into the DB.

    Returns 422 with {errors: [...]} if validation fails.
    Returns {synced, name, id, tools, max_iterations, message} on success.
    """
    _require_db()
    _require_admin(user)

    import json as _json
    data, errors = _parse_and_validate_yaml(body.yaml_content)
    if errors:
        raise HTTPException(422, {"errors": errors})

    name           = data["name"].strip()
    tools          = data.get("tools", [])
    max_iterations = int(data.get("max_iterations", 10))
    provider       = data.get("provider", "claude")
    model          = data.get("model", "")
    description    = data.get("description", "")
    system_prompt  = data.get("system_prompt", "")
    auto_commit    = bool(data.get("auto_commit", False))

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO mng_agent_roles
                       (client_id, project, name, description, system_prompt,
                        provider, model, auto_commit, tools, max_iterations)
                   VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (client_id, project, name) DO UPDATE SET
                       description    = EXCLUDED.description,
                       system_prompt  = EXCLUDED.system_prompt,
                       provider       = EXCLUDED.provider,
                       model          = EXCLUDED.model,
                       auto_commit    = EXCLUDED.auto_commit,
                       tools          = EXCLUDED.tools,
                       max_iterations = EXCLUDED.max_iterations,
                       updated_at     = NOW()
                   RETURNING id""",
                (body.project, name, description, system_prompt,
                 provider, model, auto_commit,
                 _json.dumps(tools), max_iterations),
            )
            row = cur.fetchone()
    return {
        "synced":         True,
        "name":           name,
        "id":             row[0] if row else None,
        "tools":          len(tools),
        "max_iterations": max_iterations,
        "message": (
            f"Role '{name}' synced — "
            f"{len(tools)} tool(s), max_iter={max_iterations}"
        ),
    }


# ── Export YAML ───────────────────────────────────────────────────────────────

@router.get("/{role_id}/export-yaml")
async def export_yaml(role_id: int, user=Depends(get_optional_user)):
    """Serialize a DB role to YAML string. Admin only — exposes full role definition."""
    _require_db()
    _require_admin(user)
    from fastapi.responses import PlainTextResponse
    import json as _json
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(_SQL_GET_ROLE_BY_ID, (role_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Role not found")
    role = _row_to_role(row, admin=True)

    try:
        import yaml as _yaml
    except ImportError:
        raise HTTPException(500, "PyYAML not installed")

    doc = {
        "name":           role["name"],
        "description":    role.get("description", ""),
        "provider":       role.get("provider", "claude"),
        "model":          role.get("model", ""),
        "max_iterations": role.get("max_iterations", 10),
        "auto_commit":    role.get("auto_commit", False),
        "tools":          role.get("tools", []),
        "system_prompt":  role.get("system_prompt", ""),
    }
    yaml_str = _yaml.dump(doc, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return PlainTextResponse(yaml_str, media_type="text/yaml")
