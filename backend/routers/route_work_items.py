"""
route_work_items.py — API endpoints for the DB-first work items pipeline.

All endpoints are registered at the /memory prefix (set in main.py).

Endpoints:
    POST  /memory/{project}/wi/classify         — classify pending mirror rows
    GET   /memory/{project}/wi/pending          — pending items
    GET   /memory/{project}/wi                  — all items (type?, level?, status?)
    GET   /memory/{project}/wi/stats            — counts by status and type
    POST  /memory/{project}/wi/{id}/approve     — approve → assign wi_id
    POST  /memory/{project}/wi/{id}/reject      — reject → assign REJxxxxxx
    PATCH /memory/{project}/wi/{id}             — update editable fields
    DELETE /memory/{project}/wi/{id}            — delete pending item
    POST  /memory/{project}/wi/{id}/move        — move mirror event to another item
    POST  /memory/{project}/wi/approve-all      — approve all under parent
    POST  /memory/{project}/wi/reset            — reset wi_id=NULL on pending rows

Kept from old route_backlog.py:
    POST  /memory/{project}/reset-commits       — (in route_memory.py)
    POST  /memory/{project}/reset-billing       — (in route_memory.py)
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from core.database import db

log = logging.getLogger(__name__)
router = APIRouter()


# ── Request models ─────────────────────────────────────────────────────────────

class WiUpdateRequest(BaseModel):
    name:             Optional[str]   = None
    summary:          Optional[str]   = None
    deliveries:       Optional[str]   = None
    delivery_type:    Optional[str]   = None
    score_importance: Optional[int]   = None
    score_status:     Optional[int]   = None
    wi_type:          Optional[str]   = None
    wi_parent_id:     Optional[str]   = None


class WiMoveRequest(BaseModel):
    mrr_type:    str   # prompts | commits | messages | items
    mrr_id:      str   # UUID or commit_hash
    target_wi_id: str  # destination work item UUID


class WiApproveAllRequest(BaseModel):
    parent_id: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _wi(project: str):
    from memory.memory_work_items import MemoryWorkItems
    return MemoryWorkItems(project)


def _pid(project: str) -> int:
    if not db.is_available():
        raise HTTPException(status_code=503, detail="Database not available")
    pid = db.get_or_create_project_id(project)
    if not pid:
        raise HTTPException(status_code=404, detail=f"Project '{project}' not found")
    return pid


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/{project}/wi/classify")
async def classify_work_items(
    project: str,
    background_tasks: BackgroundTasks,
    background: bool = Query(False, description="Run as background task"),
):
    """Classify all pending mirror rows into mem_work_items via LLM.

    ?background=true returns immediately; classification runs in background.
    Default: synchronous, returns classified items immediately.
    """
    wi = _wi(project)

    if background:
        async def _run():
            try:
                result = await wi.classify()
                log.info(f"wi.classify background: {project} — {result.get('classified',0)} items")
            except Exception as e:
                log.warning(f"wi.classify background error: {e}")
        background_tasks.add_task(_run)
        return {"status": "started", "project": project}

    try:
        result = await wi.classify()
        return {"project": project, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project}/wi/pending")
async def get_pending(project: str):
    """Return all work items pending approval (wi_id IS NULL)."""
    pid = _pid(project)
    wi  = _wi(project)
    items = wi.get_pending(pid)
    return {"project": project, "items": items, "count": len(items)}


@router.get("/{project}/wi/stats")
async def get_wi_stats(project: str):
    """Return counts by status and type."""
    pid = _pid(project)
    wi  = _wi(project)
    return wi.get_stats(pid)


@router.get("/{project}/wi")
async def list_work_items(
    project: str,
    wi_type:    Optional[str] = Query(None),
    item_level: Optional[int] = Query(None),
):
    """Return all work items, optionally filtered by wi_type or item_level."""
    pid = _pid(project)
    wi  = _wi(project)
    items = wi.get_all(pid, wi_type=wi_type, item_level=item_level)
    return {"project": project, "items": items, "count": len(items)}


@router.post("/{project}/wi/{item_id}/approve")
async def approve_work_item(project: str, item_id: str):
    """Approve a work item: assign wi_id (BU0001/FE0002/…), mark mirror rows."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.approve(item_id, pid)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/{project}/wi/{item_id}/reject")
async def reject_work_item(project: str, item_id: str):
    """Reject a work item: assign REJxxxxxx wi_id, mark mirror rows."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.reject(item_id, pid)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.patch("/{project}/wi/{item_id}")
async def update_work_item(project: str, item_id: str, body: WiUpdateRequest):
    """Update editable fields on a work item."""
    pid    = _pid(project)
    wi     = _wi(project)
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    result = wi.update(item_id, pid, fields)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/{project}/wi/{item_id}")
async def delete_work_item(project: str, item_id: str):
    """Delete a pending work item."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.delete(item_id, pid)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{project}/wi/{item_id}/move")
async def move_event_to_item(project: str, item_id: str, body: WiMoveRequest):
    """Move a mirror event from one work item to another."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.move_event(item_id, pid, body.mrr_type, body.mrr_id, body.target_wi_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{project}/wi/approve-all")
async def approve_all_under(project: str, body: WiApproveAllRequest):
    """Approve all pending items under a parent work item."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.approve_all_under(body.parent_id, pid)
    return result


@router.post("/{project}/wi/reset")
async def reset_wi_pending(project: str):
    """Reset wi_id=NULL on all non-SKIP, non-approved mirror rows.

    Useful when re-running classification after tuning the prompt.
    Only affects rows that haven't been explicitly approved (REJ* is cleared too).
    """
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.reset_pending(pid)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result
