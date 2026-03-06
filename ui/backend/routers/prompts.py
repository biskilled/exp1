"""
Prompts router — GET/POST/PUT .md files from workspace.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from config import settings

router = APIRouter()


def _workspace_path(rel_path: str, project: str | None = None) -> Path:
    p = project or settings.active_project or "default"
    base = Path(settings.workspace_dir) / p
    full = (base / rel_path).resolve()
    # Security: prevent path traversal outside workspace
    if not str(full).startswith(str(base.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")
    return full


@router.get("/")
async def list_prompts(project: str | None = Query(None)):
    """List all .md files in the project's prompts/ directory."""
    p = project or settings.active_project or "default"
    prompts_dir = Path(settings.workspace_dir) / p / "prompts"

    if not prompts_dir.exists():
        return {"prompts": []}

    prompts = []
    for f in sorted(prompts_dir.rglob("*.md")):
        rel = str(f.relative_to(prompts_dir))
        prompts.append({"path": rel, "name": f.name, "size": f.stat().st_size})

    return {"prompts": prompts}


@router.get("/read")
async def read_prompt(path: str = Query(...), project: str | None = Query(None)):
    """Read a prompt file."""
    full_path = _workspace_path(f"prompts/{path}", project)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {path}")
    return {"path": path, "content": full_path.read_text()}


class PromptWrite(BaseModel):
    path: str
    content: str


@router.put("/")
async def write_prompt(body: PromptWrite, project: str | None = Query(None)):
    """Create or update a prompt file."""
    full_path = _workspace_path(f"prompts/{body.path}", project)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(body.content)
    return {"saved": True, "path": body.path}


@router.delete("/")
async def delete_prompt(path: str = Query(...), project: str | None = Query(None)):
    """Delete a prompt file."""
    full_path = _workspace_path(f"prompts/{path}", project)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {path}")
    full_path.unlink()
    return {"deleted": path}
