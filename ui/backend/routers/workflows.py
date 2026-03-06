"""
Workflows router — GET/PUT workflow YAML files from workspace.
"""

import yaml
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from config import settings

router = APIRouter()


def _wf_dir(project: str | None, workflow: str) -> Path:
    p = project or settings.active_project or "default"
    return Path(settings.workspace_dir) / p / "workflows" / workflow


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
async def update_workflow(workflow: str, body: WorkflowUpdate, project: str | None = Query(None)):
    """Update workflow YAML content."""
    wf_path = _wf_dir(project, workflow) / "workflow.yaml"
    wf_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate YAML before saving
    try:
        yaml.safe_load(body.yaml_content)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")

    wf_path.write_text(body.yaml_content)
    return {"saved": True, "workflow": workflow}


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
