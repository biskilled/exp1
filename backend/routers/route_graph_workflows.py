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

from core.config import settings
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
    log_directory: str = ""


class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_iterations: Optional[int] = None
    log_directory: Optional[str] = None


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
    order_index: int = 0
    max_retry: int = 3
    continue_on_fail: bool = False
    auto_commit: bool = False


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
    order_index: Optional[int] = None
    max_retry: Optional[int] = None
    continue_on_fail: Optional[bool] = None
    auto_commit: Optional[bool] = None


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
        "log_directory": row[6] if len(row) > 6 else "",
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
        "order_index": row[20] if len(row) > 20 else 0,
        "max_retry": row[21] if len(row) > 21 else 3,
        "continue_on_fail": row[22] if len(row) > 22 else False,
        "auto_commit": row[23] if len(row) > 23 else False,
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
                "SELECT id, project, name, description, max_iterations, created_at, log_directory "
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
                """INSERT INTO pr_graph_workflows (id, client_id, project, name, description, max_iterations, log_directory)
                   VALUES (%s, 1, %s, %s, %s, %s, %s)
                   ON CONFLICT (client_id, project, name) DO NOTHING
                   RETURNING id, project, name, description, max_iterations, created_at, log_directory""",
                (wf_id, p, body.name, body.description, body.max_iterations, body.log_directory),
            )
            row = cur.fetchone()
    return _row_to_workflow(row)


@router.get("/runs/recent")
async def list_recent_runs(
    project: str = Query(""),
    limit: int = Query(20),
    user=Depends(get_optional_user),
):
    """All recent runs across all workflows for a project, with workflow name."""
    _require_db()
    p = _active_project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT r.id, r.workflow_id, r.status, r.user_input,
                          r.started_at, r.finished_at, r.total_cost_usd, r.error,
                          w.name AS workflow_name
                   FROM pr_graph_runs r
                   LEFT JOIN pr_graph_workflows w ON w.id = r.workflow_id
                   WHERE r.client_id=1 AND r.project=%s
                   ORDER BY r.started_at DESC LIMIT %s""",
                (p, min(limit, 100)),
            )
            rows = cur.fetchall()
    return {"runs": [
        {
            "id": r[0], "workflow_id": str(r[1]), "status": r[2], "user_input": r[3],
            "started_at": r[4].isoformat() if r[4] else None,
            "finished_at": r[5].isoformat() if r[5] else None,
            "total_cost_usd": float(r[6] or 0),
            "error": r[7],
            "workflow_name": r[8] or "Unknown",
        }
        for r in rows
    ]}


@router.get("/runs/{run_id}/deliverables")
async def get_run_deliverables(
    run_id: str,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    """List files saved to documents/pipelines/... for this run."""
    try:
        uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(400, f"Invalid run ID: {run_id!r}")
    _require_db()
    import re as _re
    from pathlib import Path
    from core.config import settings

    p = _active_project(project)
    # Get workflow name for path resolution
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT r.id, w.name FROM pr_graph_runs r "
                "LEFT JOIN pr_graph_workflows w ON w.id=r.workflow_id WHERE r.id=%s",
                (run_id,),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Run not found")

    pipeline_name = row[1] or ""
    safe_pipeline = _re.sub(r"[^a-z0-9_-]", "_", pipeline_name.lower().replace(" ", "_"))[:40]
    run_prefix = run_id[:8]
    docs_dir = Path(settings.workspace_dir) / p / "documents" / "pipelines" / safe_pipeline / run_prefix

    files = []
    if docs_dir.exists():
        for f in sorted(docs_dir.iterdir()):
            if f.is_file():
                files.append({
                    "name": f.name,
                    "path": str(f.relative_to(Path(settings.workspace_dir) / p)),
                    "size": f.stat().st_size,
                    "node_name": f.stem.replace("_", " ").title(),
                })
    return {"files": files, "directory": f"documents/pipelines/{safe_pipeline}/{run_prefix}"}


@router.get("/runs/{run_id}")
async def get_run(
    run_id: str,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    try:
        uuid.UUID(run_id)
    except ValueError:
        raise HTTPException(400, f"Invalid run ID: {run_id!r}")
    _require_db()
    p = _active_project(project)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, workflow_id, project, status, user_input, context, "
                "started_at, finished_at, total_cost_usd, error, current_node "
                "FROM pr_graph_runs WHERE id=%s",
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
                "current_node": row[10],
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
                "SELECT id, project, name, description, max_iterations, created_at, log_directory "
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
                          inputs, outputs, stateless, retry_config, success_criteria,
                          order_index, max_retry, continue_on_fail
                   FROM pr_graph_nodes WHERE workflow_id=%s ORDER BY order_index, created_at""",
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
    if body.log_directory is not None:
        fields.append("log_directory=%s"); values.append(body.log_directory)
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
                    inputs, outputs, stateless, retry_config, success_criteria,
                    order_index, max_retry, continue_on_fail, auto_commit)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   RETURNING id, workflow_id, name, role_file, role_prompt, provider, model,
                             output_schema, inject_context, position_x, position_y, created_at,
                             require_approval, approval_msg, role_id,
                             inputs, outputs, stateless, retry_config, success_criteria,
                             order_index, max_retry, continue_on_fail, auto_commit""",
                (
                    node_id, workflow_id, body.name, body.role_id, body.role_file,
                    body.role_prompt, body.provider, body.model,
                    json.dumps(body.output_schema) if body.output_schema else None,
                    body.inject_context, body.require_approval, body.approval_msg,
                    body.position_x, body.position_y,
                    json.dumps(body.inputs), json.dumps(body.outputs),
                    body.stateless, json.dumps(body.retry_config), body.success_criteria,
                    body.order_index, body.max_retry, body.continue_on_fail, body.auto_commit,
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
    if body.order_index is not None:
        fields.append("order_index=%s"); values.append(body.order_index)
    if body.max_retry is not None:
        fields.append("max_retry=%s"); values.append(body.max_retry)
    if body.continue_on_fail is not None:
        fields.append("continue_on_fail=%s"); values.append(body.continue_on_fail)
    if body.auto_commit is not None:
        fields.append("auto_commit=%s"); values.append(body.auto_commit)
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
    from pipelines.pipeline_graph_runner import run_graph_workflow

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
    from pipelines.pipeline_graph_runner import resume_graph_workflow

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

    # Detect work-item pipeline so we can finalize the work item when done
    is_wi_pipeline = False
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM pr_graph_workflows WHERE id=%s", (workflow_id,))
                wf_row = cur.fetchone()
                is_wi_pipeline = bool(wf_row and wf_row[0] == "_work_item_pipeline")
    except Exception:
        pass

    def _try_finalize_wi(final_ctx: dict) -> None:
        """Call work-item pipeline finalization when the pipeline completes fully."""
        if not is_wi_pipeline:
            return
        try:
            work_item = final_ctx.get("_work_item")
            if not work_item:
                return
            from routers.route_work_items import _finalize_work_item_pipeline
            _finalize_work_item_pipeline(
                project, str(work_item["id"]), run_id,
                work_item.get("name", ""), final_ctx,
            )
        except Exception as _fe:
            log.warning(f"Work-item finalization failed for run {run_id}: {_fe}")

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
        # Mark running immediately so frontend stops showing the approval panel
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE pr_graph_runs SET status='running' WHERE id=%s", (run_id,))
        asyncio.create_task(
            resume_graph_workflow(run_id, workflow_id, project, ctx,
                                  start_node_ids=[waiting_node_id],
                                  approved=True, retry=True, reason=body.reason)
        )
        return {"status": "resuming", "from_node": waiting_node_id, "run_id": run_id}

    # Save approved output to documents/ with versioning (latest vs old/)
    from pipelines.pipeline_graph_runner import save_approved_output as _save_approved
    work_item = ctx.get("_work_item")
    approved_node_name = waiting.get("node_name", "")
    approved_output = str(ctx.get(approved_node_name, waiting.get("output", "")))
    if work_item and approved_node_name and approved_output:
        try:
            _save_approved(project, work_item, approved_node_name, approved_output)
        except Exception as _se:
            log.warning(f"Could not save approved output: {_se}")

    # Approved — determine next nodes
    ctx.pop("_waiting", None)
    if body.next_node_id:
        next_nodes = [body.next_node_id]
    else:
        next_nodes = successors

    if not next_nodes:
        # No successors — pipeline fully done
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE pr_graph_runs SET status='done', context=%s, finished_at=NOW() WHERE id=%s",
                    (json.dumps(ctx), run_id),
                )
        _try_finalize_wi(ctx)
        return {"status": "done", "run_id": run_id}

    # Mark as running immediately so the frontend stops showing the old approval panel
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE pr_graph_runs SET status='running', context=%s WHERE id=%s",
                (json.dumps(ctx), run_id),
            )

    async def _resume_and_finalize():
        final_ctx = await resume_graph_workflow(
            run_id, workflow_id, project, ctx,
            start_node_ids=next_nodes, approved=True, retry=False, reason=body.reason,
        )
        # If pipeline completed (no more approval waits), finalize the work item
        if not final_ctx.get("_waiting"):
            _try_finalize_wi(final_ctx)

    asyncio.create_task(_resume_and_finalize())
    return {"status": "resuming", "next_nodes": next_nodes, "run_id": run_id}


class ApprovalChatRequest(BaseModel):
    message: str
    history: list = []   # [{role: "user"|"assistant", content: str}]


@router.post("/runs/{run_id}/chat")
async def approval_chat(
    run_id: str,
    body: ApprovalChatRequest,
    project: str = Query(""),
    user=Depends(get_optional_user),
):
    """Chat with an approval-gate node to refine its output.

    The LLM replies with the COMPLETE updated document each time.
    Updates ctx[node_name] and _waiting.output in the DB so the
    next pipeline node always receives the latest agreed version.
    """
    _require_db()
    p = _active_project(project)

    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT workflow_id, project, context
                   FROM pr_graph_runs WHERE id=%s AND status='waiting_approval'""",
                (run_id,),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Run not found or not in waiting_approval state")

    workflow_id, run_project, ctx = row[0], row[1], row[2] or {}
    p = run_project or p

    waiting   = ctx.get("_waiting", {})
    node_name = waiting.get("node_name", "")
    # Current output: prefer live ctx entry (may have been refined by prior chat)
    current_output = str(ctx.get(node_name, waiting.get("output", "")))

    # ── Load node's combined system prompt ────────────────────────────────────
    node_prompt = ""
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT n.role_prompt, n.role_id, r.system_prompt
                       FROM pr_graph_nodes n
                       LEFT JOIN mng_agent_roles r ON r.id = n.role_id
                       WHERE n.workflow_id=%s AND n.name=%s""",
                    (str(workflow_id), node_name),
                )
                nrow = cur.fetchone()
                if nrow:
                    role_prompt, role_id, role_sys = nrow
                    if role_id and role_sys:
                        node_prompt = (role_sys + "\n\n---\n\n" + (role_prompt or "")).strip()
                    else:
                        node_prompt = role_prompt or ""
    except Exception as _pe:
        log.warning(f"Could not load node prompt for chat ({node_name}): {_pe}")

    # Append refinement mode instruction
    node_prompt += (
        "\n\n---\n\n"
        "## Refinement Mode\n"
        "The user wants to refine your output. When asked to change, add, or correct "
        "anything, respond with the COMPLETE updated document in the same format and "
        "structure as your original output — not just a description of changes."
    )

    # ── Build message history ─────────────────────────────────────────────────
    # Start with the current output as first assistant turn so the LLM has context
    messages: list[dict] = [{"role": "assistant", "content": current_output}]
    # Append any prior chat turns
    for turn in body.history:
        if isinstance(turn, dict) and turn.get("role") in ("user", "assistant"):
            messages.append({"role": turn["role"], "content": str(turn.get("content", ""))})
    # The new user message
    messages.append({"role": "user", "content": body.message})

    # ── Call LLM ─────────────────────────────────────────────────────────────
    from core.api_keys import get_key
    from agents.providers import call_claude
    api_key = get_key("claude")
    resp = await call_claude(messages, system=node_prompt, api_key=api_key)
    reply = resp.get("content", "")

    # ── Persist refined output into run context ───────────────────────────────
    ctx[node_name] = reply
    ctx["_waiting"] = {**waiting, "output": reply}
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE pr_graph_runs SET context=%s WHERE id=%s",
                (json.dumps(ctx), run_id),
            )

    # ── Also update the in-memory LangGraph state so the next node sees the revised output ─
    try:
        from pipelines.pipeline_graph_runner import _APP_REGISTRY
        if run_id in _APP_REGISTRY:
            app, _ = _APP_REGISTRY[run_id]
            config = {"configurable": {"thread_id": run_id}}
            snapshot = app.get_state(config)
            if snapshot.values:
                curr_ctx = dict(snapshot.values.get("context", {}))
                curr_ctx[node_name] = reply
                app.update_state(config, {"context": curr_ctx})
    except Exception as _lg_err:
        log.warning(f"Could not update LangGraph state after chat refinement: {_lg_err}")

    return {"reply": reply, "node_name": node_name}


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
    """Convert a DB workflow dict to a simplified sequential YAML format.

    YAML schema: global properties + ordered nodes list (no explicit edges needed
    for sequential pipelines — edges are implied by order_index).
    """
    nodes_out = []
    for n in sorted(wf.get("nodes", []), key=lambda x: x.get("order_index", 0)):
        node_entry: dict = {
            "name": n["name"],
            "provider": n.get("provider", "claude"),
        }
        if n.get("model"):
            node_entry["model"] = n["model"]
        if n.get("stateless"):
            node_entry["stateless"] = True
        if n.get("max_retry", 3) != 3:
            node_entry["max_retry"] = n["max_retry"]
        if n.get("continue_on_fail"):
            node_entry["continue_on_fail"] = True
        if n.get("inputs"):
            node_entry["inputs"] = n["inputs"]
        if n.get("outputs"):
            node_entry["outputs"] = n["outputs"]
        if n.get("success_criteria"):
            node_entry["success_criteria"] = n["success_criteria"]
        nodes_out.append(node_entry)
    return {
        "name": wf["name"],
        "description": wf.get("description", ""),
        "max_iterations": wf.get("max_iterations", 5),
        "log_directory": wf.get("log_directory", ""),
        "nodes": nodes_out,
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
    log_directory = data.get("log_directory", "")

    # Create workflow
    wf_body = WorkflowCreate(name=name, description=description,
                              project=p, max_iterations=max_iterations,
                              log_directory=log_directory)
    wf = await create_workflow(wf_body, user=user)
    wf_id = wf["id"]

    # Create nodes in order; sequential edges auto-generated from order_index
    prev_id: str | None = None
    for idx, nd in enumerate(data.get("nodes", [])):
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
            order_index=idx,
            max_retry=int(nd.get("max_retry", 3)),
            continue_on_fail=bool(nd.get("continue_on_fail", False)),
        )
        created = await create_node(wf_id, nc, project=p, user=user)
        # Auto-create sequential edge from previous node
        if prev_id:
            ec = EdgeCreate(source_node_id=prev_id, target_node_id=created["id"])
            await create_edge(wf_id, ec, project=p, user=user)
        prev_id = created["id"]

    return await get_workflow(wf_id, project=p, user=user)



