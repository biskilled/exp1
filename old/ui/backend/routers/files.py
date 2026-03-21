"""
Files router — file tree for workspace + code dirs.
Used by the Electron explorer view (left panel).
"""

import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from config import settings

router = APIRouter()

TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".md", ".yaml", ".yml",
    ".json", ".toml", ".txt", ".csv", ".sh", ".html", ".css",
    ".env.example", ".gitignore",
}
MAX_FILE_SIZE = 500_000  # 500KB cap for file reads


def _safe_path(base: Path, rel: str) -> Path:
    full = (base / rel).resolve()
    if not str(full).startswith(str(base.resolve())):
        raise HTTPException(status_code=400, detail="Invalid path")
    return full


def _tree_node(path: Path, base: Path, depth: int = 0, max_depth: int = 4) -> dict:
    rel = str(path.relative_to(base))
    node: dict = {
        "name": path.name,
        "path": rel,
        "type": "dir" if path.is_dir() else "file",
    }
    if path.is_dir():
        if depth < max_depth:
            children = []
            try:
                for child in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name)):
                    if child.name.startswith(".") or child.name == "__pycache__":
                        continue
                    children.append(_tree_node(child, base, depth + 1, max_depth))
            except PermissionError:
                pass
            node["children"] = children
    else:
        node["size"] = path.stat().st_size
        node["editable"] = path.suffix in TEXT_EXTENSIONS
    return node


@router.get("/workspace")
async def workspace_tree(project: str | None = Query(None)):
    """File tree for the active project workspace."""
    p = project or settings.active_project or "default"
    proj_dir = Path(settings.workspace_dir) / p
    if not proj_dir.exists():
        raise HTTPException(status_code=404, detail=f"Project not found: {p}")
    return _tree_node(proj_dir, proj_dir)


@router.get("/code")
async def code_tree(max_depth: int = Query(3)):
    """File tree for the code directory (read-only view)."""
    code_dir = Path(settings.code_dir) if settings.code_dir else None
    if not code_dir or not code_dir.exists():
        return {"name": "(no code_dir)", "type": "dir", "children": []}
    return _tree_node(code_dir, code_dir, max_depth=max_depth)


@router.get("/read")
async def read_file(
    path: str = Query(...),
    root: str = Query("workspace"),
    project: str | None = Query(None),
):
    """Read a file from workspace or code dir."""
    if root == "workspace":
        p = project or settings.active_project or "default"
        base = Path(settings.workspace_dir) / p
    else:
        base = Path(settings.code_dir) if settings.code_dir else None
        if not base:
            raise HTTPException(status_code=400, detail="code_dir not configured")

    full_path = _safe_path(base, path)
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    if full_path.stat().st_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large to read via API")

    if full_path.suffix not in TEXT_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Binary file — cannot display")

    return {
        "path": path,
        "content": full_path.read_text(encoding="utf-8", errors="replace"),
        "size": full_path.stat().st_size,
    }


@router.put("/write")
async def write_file(
    path: str = Query(...),
    project: str | None = Query(None),
):
    """Write to a workspace file (workspace only, not code dir)."""
    from fastapi import Request
    p = project or settings.active_project or "default"
    base = Path(settings.workspace_dir) / p
    full_path = _safe_path(base, path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    from fastapi import Body
    return {"note": "Use PUT /files/write with JSON body {content: string}"}


from fastapi import Body


@router.put("/write-content")
async def write_file_content(
    path: str = Query(...),
    content: str = Body(..., embed=True),
    project: str | None = Query(None),
):
    """Write content to a workspace file."""
    p = project or settings.active_project or "default"
    base = Path(settings.workspace_dir) / p
    full_path = _safe_path(base, path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_text(content, encoding="utf-8")
    return {"saved": True, "path": path, "size": len(content)}
