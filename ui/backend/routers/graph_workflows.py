"""
graph_workflows.py — REST API for graph-based multi-LLM workflow DAGs.

Requires PostgreSQL (returns 503 when unavailable).
Follows chat.py patterns: get_optional_user, get_key(), asyncio.create_task for side effects.

Routes:
  GET    /graph-workflows/              list for ?project=
  POST   /graph-workflows/              create
  GET    /graph-workflows/{id}          full graph (nodes + edges)
  PUT    /graph-workflows/{id}          update name/description/max_iterations
  DELETE /graph-workflows/{id}         cascade delete

  POST   /graph-workflows/{id}/nodes
  PATCH  /graph-workflows/{id}/nodes/{nid}
  DELETE /graph-workflows/{id}/nodes/{nid}

  POST   /graph-workflows/{id}/edges
  PATCH  /graph-workflows/{id}/edges/{eid}
  DELETE /graph-workflows/{id}/edges/{eid}

  POST   /graph-workflows/{id}/runs    start run (background task)
  GET    /graph-workflows/runs/{rid}   poll run status  (table: pr_graph_node_results)
  GET    /graph-workflows/{id}/runs    list runs
  DELETE /graph-workflows/runs/{rid}   cancel
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any, Optional

import yaml as _yaml_lib
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from config import settings
from core.auth import get_optional_user
from core.database import db

log = logging.getLogger(__name__)

router = APIRouter()


def _require_db():
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL required for graph workflows. Set DATABASE_URL.")


# ── Pydantic models ───────────────────────────────────────────────────────────

class WorkflowCreate(BaseModel):
    name: str
    description: str = ""
    project: str = ""
    max_iterations: int = 5


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_iterations: Optional[int] = None


class NodeCreate(BaseModel):
    name: str
    role_id: Optional[int] = None
    role_file: Optional[str] = None
    role_prompt: str = ""
    provider: str = "claude"
    model: str = ""
    output_schema: Optional[dict] = None
    inject_context: bool = True
    require_approval: bool = False
    approval_msg: str = ""
    position_x: float = 100
    position_y: float = 100
    inputs: list = []
    outputs: list = []
    stateless: bool = False
    retry_config: dict = {}
    success_criteria: str = ""


class NodeUpdate(BaseModel):
    name: Optional[str] = None
    role_id: Optional[int] = None
    role_file: Optional[str] = None
    role_prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    output_schema: Optional[dict] = None
    inject_context: Optional[bool] = None
    require_approval: Optional[bool] = None
    approval_msg: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    inputs: Optional[list] = None
    outputs: Optional[list] = None
    stateless: Optional[bool] = None
    retry_config: Optional[dict] = None
    success_criteria: Optional[str] = None


class EdgeCreate(BaseModel):
    source_node_id: str
    target_node_id: str
    condition: Optional[dict] = None
    label: str = ""


class EdgeUpdate(BaseModel):
    condition: Optional[dict] = None
    label: Optional[str] = None


class RunCreate(BaseModel):
    user_input: str = ""
    project: str = ""
    work_item_id: str | None = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row_to_workflow(row) -> dict:
    return {
        "id": row[0], "project": row[1], "name": row[2],
        "description": row[3], "max_iterations": row[4],
        "created_at": row[5].isoformat() if row[5] else None,
    }


def _row_to_node(row) -> dict:
    return {
        "id": row[0], "workflow_id": row[1], "name": row[2],
        "role_file": row[3], "role_prompt": row[4], "provider": row[5],
        "model": row[6], "output_schema": row[7], "inject_context": row[8],
        "position_x": row[9], "position_y": row[10],
        "created_at": row[11].isoformat() if row[11] else None,
        "require_approval": row[12] if len(row) > 12 else False,
        "approval_msg": row[13] if len(row) > 13 else "",
        "role_id": row[14] if len(row) > 14 else None,
        "inputs": row[15] if len(row) > 15 else [],
        "outputs": row[16] if len(row) > 16 else [],
        "stateless": row[17] if len(row) > 17 else False,
        "retry_config": row[18] if len(row) > 18 else {},
        "success_criteria": row[19] if len(row) > 19 else "",
    }


def _row_to_edge(row) -> dict:
    return {
        "id": row[0], "workflow_id": row[1], "source_node_id": row[2],
        "target_node_id": row[3], "condition": row[4], "label": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
    }


def _active_project(project: str = "") -> str:
    return project or settings.active_project or "default"


# ── Workflow CRUD ─────────────────────────────────────────────────────────────

@router.get("/")
async def list_workflows(
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, project, name, description, max_iterations, created_at "
                "FROM pr_graph_workflows WHERE client_id=1 AND project=%s ORDER BY created_at DESC",
                (p,),
            )
            rows = cur.fetchall()
    return {"workflows": [_row_to_workflow(r) for r in rows]}


@router.post("/")
async def create_workflow(body: WorkflowCreate, user=Depends(get_optional_user)):
    _require_db()
    p = _active_project(body.project)
    wf_id = str(uuid.uuid4())
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO pr_graph_workflows (id, client_id, project, name, description, max_iterations)
                   VALUES (%s, 1, %s, %s, %s, %s)
                   ON CONFLICT (client_id, project, name) DO NOTHING
                   RETURNING id, project, name, description, max_iterations, created_at""",
                (wf_id, p, body.name, body.description, body.max_iterations),
            )
            row = cur.fetchone()
    return _row_to_workflow(row)


@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, workflow_id, project, status, user_input, context, "
                "started_at, finished_at, total_cost_usd, error FROM pr_graph_runs WHERE id=%s",
                (run_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Run not found")
            run = {
                "id": row[0], "workflow_id": row[1], "project": row[2],
                "status": row[3], "user_input": row[4], "context": row[5] or {},
                "started_at": row[6].isoformat() if row[6] else None,
                "finished_at": row[7].isoformat() if row[7] else None,
                "total_cost_usd": float(row[8]),
                "error": row[9],
            }
            cur.execute(
                """SELECT id, node_id, node_name, status, output, structured,
                          input_tokens, output_tokens, cost_usd, started_at, finished_at, iteration
                   FROM pr_graph_node_results WHERE run_id=%s ORDER BY id""",
                (run_id,),
            )
            node_results = []
            for r in cur.fetchall():
                node_results.append({
                    "id": r[0], "node_id": r[1], "node_name": r[2], "status": r[3],
                    "output": r[4], "structured": r[5],
                    "input_tokens": r[6], "output_tokens": r[7], "cost_usd": float(r[8]),
                    "started_at": r[9].isoformat() if r[9] else None,
                    "finished_at": r[10].isoformat() if r[10] else None,
                    "iteration": r[11],
                })
    run["node_results"] = node_results
    return run


@router.delete("/runs/{run_id}")
async def cancel_run(
    run_id: str,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE pr_graph_runs SET status='cancelled', finished_at=NOW() WHERE id=%s AND status='running'",
                (run_id,),
            )
    return {"status": "cancelled", "run_id": run_id}


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, project, name, description, max_iterations, created_at "
                "FROM pr_graph_workflows WHERE id=%s",
                (workflow_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Workflow not found")
            wf = _row_to_workflow(row)

            cur.execute(
                """SELECT id, workflow_id, name, role_file, role_prompt, provider, model,
                          output_schema, inject_context, position_x, position_y, created_at,
                          require_approval, approval_msg, role_id,
                          inputs, outputs, stateless, retry_config, success_criteria
                   FROM pr_graph_nodes WHERE workflow_id=%s ORDER BY created_at""",
                (workflow_id,),
            )
            wf["nodes"] = [_row_to_node(r) for r in cur.fetchall()]

            cur.execute(
                """SELECT id, workflow_id, source_node_id, target_node_id, condition, label, created_at
                   FROM pr_graph_edges WHERE workflow_id=%s ORDER BY created_at""",
                (workflow_id,),
            )
            wf["edges"] = [_row_to_edge(r) for r in cur.fetchall()]

    return wf


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    body: WorkflowUpdate,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    fields = []
    values: list[Any] = []
    if body.name is not None:
        fields.append("name=%s"); values.append(body.name)
    if body.description is not None:
        fields.append("description=%s"); values.append(body.description)
    if body.max_iterations is not None:
        fields.append("max_iterations=%s"); values.append(body.max_iterations)
    if not fields:
        raise HTTPException(400, "Nothing to update")
    values.append(workflow_id)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE pr_graph_workflows SET {', '.join(fields)} WHERE id=%s",
                values,
            )
    return {"updated": True, "workflow_id": workflow_id}


@router.delete("/{workflow_id}")
async def delete_workflow(
    workflow_id: str,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM pr_graph_workflows WHERE id=%s", (workflow_id,))
    return {"deleted": True, "workflow_id": workflow_id}


# ── Node CRUD ─────────────────────────────────────────────────────────────────

@router.post("/{workflow_id}/nodes")
async def create_node(
    workflow_id: str,
    body: NodeCreate,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    node_id = str(uuid.uuid4())
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO pr_graph_nodes
                   (id, workflow_id, name, role_id, role_file, role_prompt, provider, model,
                    output_schema, inject_context, require_approval, approval_msg,
                    position_x, position_y,
                    inputs, outputs, stateless, retry_config, success_criteria)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id, workflow_id, name, role_file, role_prompt, provider, model,
                             output_schema, inject_context, position_x, position_y, created_at,
                             require_approval, approval_msg, role_id,
                             inputs, outputs, stateless, retry_config, success_criteria""",
                (
                    node_id, workflow_id, body.name, body.role_id, body.role_file,
                    body.role_prompt, body.provider, body.model,
                    json.dumps(body.output_schema) if body.output_schema else None,
                    body.inject_context, body.require_approval, body.approval_msg,
                    body.position_x, body.position_y,
                    json.dumps(body.inputs), json.dumps(body.outputs),
                    body.stateless, json.dumps(body.retry_config), body.success_criteria,
                ),
            )
            row = cur.fetchone()
    return _row_to_node(row)


@router.patch("/{workflow_id}/nodes/{node_id}")
async def update_node(
    workflow_id: str,
    node_id: str,
    body: NodeUpdate,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    fields = []
    values: list[Any] = []
    mapping = {
        "name": body.name, "role_id": body.role_id,
        "role_file": body.role_file, "role_prompt": body.role_prompt,
        "provider": body.provider, "model": body.model,
        "inject_context": body.inject_context,
        "require_approval": body.require_approval,
        "approval_msg": body.approval_msg,
        "position_x": body.position_x, "position_y": body.position_y,
        "success_criteria": body.success_criteria,
    }
    for col, val in mapping.items():
        if val is not None:
            fields.append(f"{col}=%s"); values.append(val)
    if body.output_schema is not None:
        fields.append("output_schema=%s"); values.append(json.dumps(body.output_schema))
    if body.inputs is not None:
        fields.append("inputs=%s"); values.append(json.dumps(body.inputs))
    if body.outputs is not None:
        fields.append("outputs=%s"); values.append(json.dumps(body.outputs))
    if body.stateless is not None:
        fields.append("stateless=%s"); values.append(body.stateless)
    if body.retry_config is not None:
        fields.append("retry_config=%s"); values.append(json.dumps(body.retry_config))
    if not fields:
        raise HTTPException(400, "Nothing to update")
    values.extend([node_id, workflow_id])
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE pr_graph_nodes SET {', '.join(fields)} WHERE id=%s AND workflow_id=%s",
                values,
            )
    return {"updated": True, "node_id": node_id}


@router.delete("/{workflow_id}/nodes/{node_id}")
async def delete_node(
    workflow_id: str,
    node_id: str,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM pr_graph_nodes WHERE id=%s AND workflow_id=%s",
                (node_id, workflow_id),
            )
    return {"deleted": True, "node_id": node_id}


# ── Edge CRUD ─────────────────────────────────────────────────────────────────

@router.post("/{workflow_id}/edges")
async def create_edge(
    workflow_id: str,
    body: EdgeCreate,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    edge_id = str(uuid.uuid4())
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO pr_graph_edges
                   (id, workflow_id, source_node_id, target_node_id, condition, label)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   RETURNING id, workflow_id, source_node_id, target_node_id, condition, label, created_at""",
                (
                    edge_id, workflow_id, body.source_node_id, body.target_node_id,
                    json.dumps(body.condition) if body.condition else None, body.label,
                ),
            )
            row = cur.fetchone()
    return _row_to_edge(row)


@router.patch("/{workflow_id}/edges/{edge_id}")
async def update_edge(
    workflow_id: str,
    edge_id: str,
    body: EdgeUpdate,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    fields = []
    values: list[Any] = []
    if body.label is not None:
        fields.append("label=%s"); values.append(body.label)
    if body.condition is not None:
        fields.append("condition=%s"); values.append(json.dumps(body.condition))
    if not fields:
        raise HTTPException(400, "Nothing to update")
    values.extend([edge_id, workflow_id])
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE pr_graph_edges SET {', '.join(fields)} WHERE id=%s AND workflow_id=%s",
                values,
            )
    return {"updated": True, "edge_id": edge_id}


@router.delete("/{workflow_id}/edges/{edge_id}")
async def delete_edge(
    workflow_id: str,
    edge_id: str,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM pr_graph_edges WHERE id=%s AND workflow_id=%s",
                (edge_id, workflow_id),
            )
    return {"deleted": True, "edge_id": edge_id}


# ── Runs ──────────────────────────────────────────────────────────────────────

@router.post("/{workflow_id}/runs")
async def start_run(
    workflow_id: str,
    body: RunCreate,
    user=Depends(get_optional_user),
):
    _require_db()
    from core.graph_runner import run_graph_workflow

    p = _active_project(body.project)
    run_id = str(uuid.uuid4())

    # Insert initial run record
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO pr_graph_runs (id, client_id, project, workflow_id, status, user_input)
                   VALUES (%s, 1, %s, %s, 'running', %s)""",
                (run_id, p, workflow_id, body.user_input),
            )

    # Fire-and-forget background execution
    async def _run():
        try:
            await run_graph_workflow(workflow_id, body.user_input, run_id, p,
                                     work_item_id=body.work_item_id)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Graph run {run_id} failed: {e}")
            if db.is_available():
                try:
                    with db.conn() as conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                "UPDATE pr_graph_runs SET status='error', error=%s, finished_at=NOW() WHERE id=%s",
                                (str(e), run_id),
                            )
                except Exception:
                    pass

    asyncio.create_task(_run())
    return {"run_id": run_id, "status": "running", "workflow_id": workflow_id}


class DecisionRequest(BaseModel):
    approved: bool
    next_node_id: Optional[str] = None  # override which node to run next
    retry: bool = False                  # re-run the waiting node
    reason: str = ""


@router.post("/runs/{run_id}/decision")
async def make_run_decision(
    run_id: str,
    body: DecisionRequest,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    """User approval decision for a paused run.

    approved=True  → continue to next node(s) (or to next_node_id if specified)
    retry=True     → re-run the waiting node
    approved=False → stop the run
    """
    _require_db()
    from core.graph_runner import resume_graph_workflow

    p = _active_project(project)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT workflow_id, project, context, total_cost_usd FROM pr_graph_runs WHERE id=%s AND status='waiting_approval'",
                (run_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(404, "Run not found or not in waiting_approval state")
            workflow_id, project, ctx, total_cost = row[0], row[1], row[2] or {}, float(row[3])

    waiting = ctx.get("_waiting", {})
    waiting_node_id = waiting.get("node_id")
    successors = waiting.get("successors", [])

    if not body.approved and not body.retry:
        # Stop the run
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pr_graph_runs SET status='stopped', finished_at=NOW() WHERE id=%s",
                    (run_id,),
                )
        return {"status": "stopped", "run_id": run_id}

    if body.retry and waiting_node_id:
        asyncio.create_task(
            resume_graph_workflow(run_id, workflow_id, project, ctx,
                                  start_node_ids=[waiting_node_id],
                                  approved=True, retry=True, reason=body.reason)
        )
        return {"status": "resuming", "from_node": waiting_node_id, "run_id": run_id}

    # Approved — determine next nodes
    ctx.pop("_waiting", None)
    if body.next_node_id:
        next_nodes = [body.next_node_id]
    else:
        next_nodes = successors

    if not next_nodes:
        # No successors — run is done
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pr_graph_runs SET status='done', context=%s, finished_at=NOW() WHERE id=%s",
                    (json.dumps(ctx), run_id),
                )
        return {"status": "done", "run_id": run_id}

    asyncio.create_task(
        resume_graph_workflow(run_id, workflow_id, project, ctx,
                              start_node_ids=next_nodes,
                              approved=True, retry=False, reason=body.reason)
    )
    return {"status": "resuming", "next_nodes": next_nodes, "run_id": run_id}


@router.get("/{workflow_id}/runs")
async def list_runs(
    workflow_id: str,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    _require_db()
    p = _active_project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, workflow_id, project, status, user_input,
                          started_at, finished_at, total_cost_usd, error
                   FROM pr_graph_runs WHERE client_id=1 AND project=%s AND workflow_id=%s ORDER BY started_at DESC LIMIT 50""",
                (p, workflow_id),
            )
            rows = cur.fetchall()
    runs = []
    for r in rows:
        runs.append({
            "id": r[0], "workflow_id": r[1], "project": r[2], "status": r[3],
            "user_input": r[4],
            "started_at": r[5].isoformat() if r[5] else None,
            "finished_at": r[6].isoformat() if r[6] else None,
            "total_cost_usd": float(r[7]),
            "error": r[8],
        })
    return {"runs": runs}


# ── YAML / LangGraph export & import ─────────────────────────────────────────

class YAMLImport(BaseModel):
    yaml_text: str
    project: str = ""


def _workflow_to_yaml_dict(wf: dict) -> dict:
    """Convert a DB workflow dict (with nodes/edges) to YAML-serialisable dict."""
    nodes_out = []
    for n in wf.get("nodes", []):
        nodes_out.append({
            "id": n["id"],
            "name": n["name"],
            "provider": n.get("provider", "claude"),
            "model": n.get("model", ""),
            "stateless": bool(n.get("stateless", False)),
            "role_prompt": n.get("role_prompt", ""),
            "success_criteria": n.get("success_criteria", ""),
            "retry_config": n.get("retry_config") or {},
            "inputs": n.get("inputs") or [],
            "outputs": n.get("outputs") or [],
        })
    edges_out = []
    for e in wf.get("edges", []):
        entry: dict = {"from": e["source_node_id"], "to": e["target_node_id"]}
        if e.get("condition"):
            entry["condition"] = e["condition"]
        if e.get("label"):
            entry["label"] = e["label"]
        edges_out.append(entry)
    return {
        "name": wf["name"],
        "description": wf.get("description", ""),
        "max_iterations": wf.get("max_iterations", 5),
        "nodes": nodes_out,
        "edges": edges_out,
    }


@router.get("/{workflow_id}/export-yaml", response_class=PlainTextResponse)
async def export_yaml(
    workflow_id: str,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    """Export workflow as YAML string and optionally save to workspace."""
    _require_db()
    p = _active_project(project)
    wf = await get_workflow(workflow_id, project=p, user=user)
    yaml_dict = _workflow_to_yaml_dict(wf)
    yaml_text = _yaml_lib.dump(yaml_dict, allow_unicode=True, sort_keys=False)

    # Save to workspace
    if p and p != "default":
        try:
            wf_dir = Path(settings.workspace_dir) / p / "workflows"
            wf_dir.mkdir(parents=True, exist_ok=True)
            safe = re.sub(r"[^a-z0-9_-]", "_", wf["name"].lower())
            (wf_dir / f"{safe}_graph.yaml").write_text(yaml_text)
        except Exception as _e:
            log.warning(f"Could not save YAML to workspace: {_e}")

    return yaml_text


@router.post("/import-yaml")
async def import_yaml(
    body: YAMLImport,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    """Parse YAML text and create workflow + nodes + edges in DB."""
    _require_db()
    p = _active_project(project or body.project)
    try:
        data = _yaml_lib.safe_load(body.yaml_text)
    except _yaml_lib.YAMLError as e:
        raise HTTPException(400, f"Invalid YAML: {e}")

    name = data.get("name", "Imported Workflow")
    description = data.get("description", "")
    max_iterations = int(data.get("max_iterations", 5))

    # Create workflow
    wf_body = WorkflowCreate(name=name, description=description,
                              project=p, max_iterations=max_iterations)
    wf = await create_workflow(wf_body, user=user)
    wf_id = wf["id"]

    # Create nodes, track id mapping (yaml id → db uuid)
    id_map: dict[str, str] = {}
    for nd in data.get("nodes", []):
        nc = NodeCreate(
            name=nd.get("name", "Node"),
            provider=nd.get("provider", "claude"),
            model=nd.get("model", ""),
            role_prompt=nd.get("role_prompt", ""),
            stateless=bool(nd.get("stateless", False)),
            success_criteria=nd.get("success_criteria", ""),
            retry_config=nd.get("retry_config") or {},
            inputs=nd.get("inputs") or [],
            outputs=nd.get("outputs") or [],
        )
        created = await create_node(wf_id, nc, project=p, user=user)
        yaml_id = nd.get("id", nd.get("name", ""))
        id_map[yaml_id] = created["id"]
        id_map[nd.get("name", "")] = created["id"]  # also map by name

    # Create edges
    for ed in data.get("edges", []):
        src_yaml = str(ed.get("from", ""))
        tgt_yaml = str(ed.get("to", ""))
        src_db = id_map.get(src_yaml)
        tgt_db = id_map.get(tgt_yaml)
        if not src_db or not tgt_db:
            continue
        ec = EdgeCreate(
            source_node_id=src_db,
            target_node_id=tgt_db,
            condition=ed.get("condition"),
            label=ed.get("label", ""),
        )
        await create_edge(wf_id, ec, project=p, user=user)

    return await get_workflow(wf_id, project=p, user=user)


@router.get("/{workflow_id}/export-langgraph", response_class=PlainTextResponse)
async def export_langgraph(
    workflow_id: str,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    """Generate LangGraph Python code from DB workflow."""
    _require_db()
    p = _active_project(project)
    wf = await get_workflow(workflow_id, project=p, user=user)

    lines = [
        "# Auto-generated by aicli Pipeline Designer",
        "from langgraph.graph import StateGraph, END",
        "from typing import TypedDict, Any, List",
        "",
        "",
        "class PipelineState(TypedDict):",
        "    user_input: str",
        "    context: dict",
        "    messages: list",
        "    run_id: str",
        "    project: str",
        "    total_cost: float",
        "",
        "",
    ]

    # Node id → safe function name
    def _safe(name: str) -> str:
        import re as _re
        return _re.sub(r"[^a-z0-9_]", "_", name.lower().replace(" ", "_"))

    nodes = wf.get("nodes", [])
    edges = wf.get("edges", [])
    node_map = {n["id"]: n for n in nodes}
    edges_by_src: dict[str, list] = {}
    for e in edges:
        edges_by_src.setdefault(e["source_node_id"], []).append(e)

    # Forward in-degree for entry point detection
    fwd_in: dict[str, int] = {n["id"]: 0 for n in nodes}
    for e in edges:
        if e["target_node_id"] in fwd_in:
            fwd_in[e["target_node_id"]] += 1

    for n in nodes:
        fn = _safe(n["name"])
        stateless = n.get("stateless", False)
        lines += [
            f"def {fn}(state: PipelineState) -> PipelineState:",
            f'    """Node: {n["name"]}  |  provider: {n.get("provider","claude")}  |  stateless: {stateless}"""',
            f"    # TODO: call {n.get('provider','claude')} with role_prompt",
            f"    output = ''  # replace with actual LLM call",
            f"    new_ctx = {{**state['context'], '{n['name']}': output}}",
            f"    return {{**state, 'context': new_ctx}}",
            "",
            "",
        ]

    # Router functions for nodes with conditional edges
    for n in nodes:
        out_edges = edges_by_src.get(n["id"], [])
        conditional = [e for e in out_edges if e.get("condition")]
        if len(conditional) > 1 or (len(out_edges) > 1 and conditional):
            fn = _safe(n["name"])
            lines += [
                f"def route_from_{fn}(state: PipelineState) -> str:",
            ]
            for e in out_edges:
                tgt = node_map.get(e["target_node_id"])
                tgt_fn = _safe(tgt["name"]) if tgt else "END"
                cond = e.get("condition")
                if cond:
                    field = cond.get("field", "score")
                    op = cond.get("op", "gte")
                    val = cond.get("value", 0)
                    op_map = {"gte": ">=", "gt": ">", "lt": "<", "lte": "<=",
                              "eq": "==", "neq": "!="}
                    py_op = op_map.get(op, ">=")
                    lines.append(f"    if state['context'].get('{field}', 0) {py_op} {val}:")
                    lines.append(f"        return '{tgt_fn}'")
                else:
                    lines.append(f"    return '{tgt_fn}'")
            lines += ["    return END", "", ""]

    # build_pipeline
    lines += [
        "def build_pipeline() -> StateGraph:",
        "    graph = StateGraph(PipelineState)",
        "",
    ]
    for n in nodes:
        fn = _safe(n["name"])
        lines.append(f"    graph.add_node('{fn}', {fn})")

    # Entry point
    entry_nodes = [n for n in nodes if fwd_in.get(n["id"], 0) == 0]
    if entry_nodes:
        lines.append(f"    graph.set_entry_point('{_safe(entry_nodes[0]['name'])}')")

    lines.append("")
    for n in nodes:
        fn = _safe(n["name"])
        out_edges = edges_by_src.get(n["id"], [])
        conditional = [e for e in out_edges if e.get("condition")]
        if not out_edges:
            lines.append(f"    graph.add_edge('{fn}', END)")
        elif len(out_edges) == 1 and not conditional:
            tgt = node_map.get(out_edges[0]["target_node_id"])
            tgt_fn = _safe(tgt["name"]) if tgt else "END"
            lines.append(f"    graph.add_edge('{fn}', '{tgt_fn}')")
        else:
            targets = {}
            for e in out_edges:
                tgt = node_map.get(e["target_node_id"])
                tgt_fn = _safe(tgt["name"]) if tgt else "END"
                targets[tgt_fn] = tgt_fn
            targets["END"] = "END"
            lines.append(
                f"    graph.add_conditional_edges('{fn}', route_from_{fn}, {targets})"
            )

    lines += [
        "",
        "    return graph.compile()",
        "",
        "",
        "pipeline = build_pipeline()",
    ]

    return "\n".join(lines) + "\n"


