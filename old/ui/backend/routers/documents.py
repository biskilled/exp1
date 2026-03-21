"""
Documents router — browse, read, write, and delete files from workspace documents/.

Mirrors prompts.py but rooted at documents/ and accepts all file types (not just .md).
No embedding on save — documents are auto-generated artifacts, not role prompts.
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
async def list_documents(project: str | None = Query(None)):
    """List all files in the project's documents/ directory."""
    p = project or settings.active_project or "default"
    docs_dir = Path(settings.workspace_dir) / p / "documents"

    if not docs_dir.exists():
        return {"documents": []}

    docs = []
    for f in sorted(docs_dir.rglob("*")):
        if f.is_file():
            rel = str(f.relative_to(docs_dir))
            docs.append({"path": rel, "name": f.name, "size": f.stat().st_size})

    return {"documents": docs}


@router.get("/read")
async def read_document(path: str = Query(...), project: str | None = Query(None)):
    """Read a document file."""
    full_path = _workspace_path(f"documents/{path}", project)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {path}")
    return {"path": path, "content": full_path.read_text()}


class DocumentWrite(BaseModel):
    path: str
    content: str


@router.put("/")
async def write_document(body: DocumentWrite, project: str | None = Query(None)):
    """Create or update a document file."""
    full_path = _workspace_path(f"documents/{body.path}", project)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(body.content)
    return {"saved": True, "path": body.path}


@router.delete("/")
async def delete_document(path: str = Query(...), project: str | None = Query(None)):
    """Delete a document file."""
    full_path = _workspace_path(f"documents/{path}", project)
    if not full_path.exists():
        raise HTTPException(status_code=404, detail=f"Not found: {path}")
    full_path.unlink()
    return {"deleted": path}
