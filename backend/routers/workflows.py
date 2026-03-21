"""
Workflows router — YAML workflow files + interactive run execution.

Run endpoints (note: /runs/* routes must appear BEFORE /{workflow} to avoid
FastAPI matching "runs" as a workflow name):

  POST /workflows/{name}/runs          start a run
  GET  /workflows/runs                 list recent runs for ?project=
  GET  /workflows/runs/{run_id}        get run state (poll for status)
  POST /workflows/runs/{run_id}/decision   continue | retry | stop
"""

import yaml
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from workflow.workflow_runner import (
    start_run, decide, load_run, list_runs,
)

router = APIRouter()


def _wf_dir(project: str | None, workflow: str) -> Path:
    p = project or settings.active_project or "default"
    return Path(settings.workspace_dir) / p / "workflows" / workflow


# ── Run endpoints (MUST be before /{workflow} to avoid route conflict) ─────────

class RunStart(BaseModel):
    user_input: str = ""


class RunDecision(BaseModel):
    action: str           # "continue" | "retry" | "stop"
    next_step: int | None = None   # for "continue" with explicit target step


@router.post("/runs/{run_id}/decision")
async def run_decision(run_id: str, body: RunDecision, project: str | None = Query(None)):
    """User approves, retries, or stops a paused run."""
    p = project or settings.active_project or "default"
    if body.action not in ("continue", "retry", "stop"):
        raise HTTPException(status_code=400, detail="action must be continue|retry|stop")
    try:
        await decide(run_id, p, body.action, body.next_step)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"ok": True, "action": body.action}


@router.get("/runs/{run_id}")
async def get_run(run_id: str, project: str | None = Query(None)):
    """Get current run state — poll this every 2 s while status is 'running'."""
    p = project or settings.active_project or "default"
    try:
        return load_run(p, run_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/runs")
async def list_runs_ep(project: str | None = Query(None), limit: int = 30):
    """List recent runs for a project."""
    p = project or settings.active_project or "default"
    return {"runs": list_runs(p, limit), "project": p}


# ── Workflow YAML CRUD ─────────────────────────────────────────────────────────

@router.get("/")
async def list_workflows(project: str | None = Query(None)):
    """List available workflows for a project."""
    p = project or settings.active_project or "default"
    wf_base = Path(settings.workspace_dir) / p / "workflows"

    if not wf_base.exists():
        return {"workflows": [], "project": p}

    workflows = []
    for d in sorted(wf_base.iterdir()):
        if d.is_dir() and (d / "workflow.yaml").exists():
            try:
                data = yaml.safe_load((d / "workflow.yaml").read_text())
                workflows.append({
                    "name": d.name,
                    "description": data.get("description", ""),
                    "steps": len(data.get("steps", [])),
                })
            except Exception:
                workflows.append({"name": d.name})

    return {"workflows": workflows, "project": p}


@router.get("/{workflow}")
async def get_workflow(workflow: str, project: str | None = Query(None)):
    """Get workflow YAML content."""
    wf_path = _wf_dir(project, workflow) / "workflow.yaml"
    if not wf_path.exists():
        raise HTTPException(status_code=404, detail=f"Workflow not found: {workflow}")

    return {
        "workflow": workflow,
        "yaml": wf_path.read_text(),
        "parsed": yaml.safe_load(wf_path.read_text()),
    }


class WorkflowUpdate(BaseModel):
    yaml_content: str


@router.put("/{workflow}")
async def update_workflow(workflow: str, body: WorkflowUpdate,
                          project: str | None = Query(None)):
    """Save workflow YAML content."""
    wf_path = _wf_dir(project, workflow) / "workflow.yaml"
    wf_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        yaml.safe_load(body.yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")

    wf_path.write_text(body.yaml_content)
    return {"saved": True, "workflow": workflow}


@router.post("/{workflow}/runs")
async def start_workflow_run(workflow: str, body: RunStart,
                             project: str | None = Query(None)):
    """Start a workflow run. Returns run_id — poll GET /runs/{run_id} for status."""
    p = project or settings.active_project or "default"
    try:
        run_id = await start_run(workflow, body.user_input, p)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"run_id": run_id, "status": "running"}


@router.get("/{workflow}/prompts")
async def list_workflow_prompts(workflow: str, project: str | None = Query(None)):
    """List prompt files in a workflow."""
    prompts_dir = _wf_dir(project, workflow) / "prompts"
    if not prompts_dir.exists():
        return {"prompts": []}

    return {
        "prompts": [
            {"name": f.name, "path": str(f.relative_to(Path(settings.workspace_dir)))}
            for f in sorted(prompts_dir.glob("*.md"))
        ]
    }
