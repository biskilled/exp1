"""
route_work_items.py — API endpoints for the DB-first work items pipeline.

All endpoints are registered at the /wi prefix (set in main.py).

Endpoints:
    POST  /wi/{project}/classify         — classify pending mirror rows
    GET   /wi/{project}/pending          — pending items
    GET   /wi/{project}/use-cases        — approved use cases with children + stats
    GET   /wi/{project}                  — all items (type?, level?, status?)
    GET   /wi/{project}/stats            — counts by status and type
    POST  /wi/{project}/{id}/approve     — approve → assign wi_id
    POST  /wi/{project}/{id}/reject      — reject → assign REJxxxxxx
    PATCH /wi/{project}/{id}             — update editable fields
    DELETE /wi/{project}/{id}            — delete pending item
    POST  /wi/{project}/{id}/move        — move mirror event to another item
    POST  /wi/{project}/approve-all      — approve all under parent
    POST  /wi/{project}/reset            — reset wi_id=NULL on pending rows
    POST  /wi/{project}                  — create item directly
    GET   /wi/{project}/{id}/md          — get Markdown for use_case
    POST  /wi/{project}/{id}/md          — save Markdown back to DB + file
    POST  /wi/{project}/{id}/md/refresh  — regenerate Markdown from DB
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
    user_importance:  Optional[int]   = None
    user_status:      Optional[int]   = None
    wi_type:          Optional[str]   = None
    wi_parent_id:     Optional[str]   = None


class WiMoveRequest(BaseModel):
    mrr_type:    str   # prompts | commits | messages | items
    mrr_id:      str   # UUID or commit_hash
    target_wi_id: str  # destination work item UUID


class WiApproveAllRequest(BaseModel):
    parent_id: str


class WiCreateRequest(BaseModel):
    name:             str
    wi_type:          str
    summary:          str   = ""
    wi_parent_id:     Optional[str] = None
    score_importance: int   = 2
    score_status:     int   = 0
    delivery_type:    str   = ""


class WiReorderItem(BaseModel):
    id:               str
    user_importance:  int


class WiReorderRequest(BaseModel):
    items: list[WiReorderItem]


class WiMdSaveRequest(BaseModel):
    content: str


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

@router.post("/{project}/classify")
async def classify_work_items(
    project: str,
    background_tasks: BackgroundTasks,
    background: bool = Query(False, description="Run as background task"),
    max_use_cases: int = Query(8, description="Target max use cases across all groups"),
):
    """Classify all pending mirror rows into mem_work_items via LLM.

    ?background=true returns immediately; classification runs in background.
    ?max_use_cases=N   target number of use cases (default 8).
    Default: synchronous, returns classified items immediately.
    """
    wi = _wi(project)

    if background:
        async def _run():
            try:
                result = await wi.classify(max_use_cases=max_use_cases)
                log.info(f"wi.classify background: {project} — {result.get('classified',0)} items")
            except Exception as e:
                log.warning(f"wi.classify background error: {e}")
        background_tasks.add_task(_run)
        return {"status": "started", "project": project}

    try:
        result = await wi.classify(max_use_cases=max_use_cases)
        return {"project": project, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project}/pending")
async def get_pending(project: str):
    """Return all work items pending approval (wi_id LIKE 'AI%')."""
    pid = _pid(project)
    wi  = _wi(project)
    items = wi.get_pending(pid)
    return {"project": project, "items": items, "count": len(items)}


@router.get("/{project}/pending/grouped")
async def get_pending_grouped(project: str):
    """Return pending items as use_case groups with nested children."""
    pid = _pid(project)
    wi  = _wi(project)
    groups = wi.get_pending_grouped(pid)
    total  = sum(1 + len(g.get("children", [])) for g in groups)
    return {"project": project, "groups": groups, "count": total}


@router.get("/{project}/stats")
async def get_wi_stats(project: str):
    """Return counts by status and type."""
    pid = _pid(project)
    wi  = _wi(project)
    return wi.get_stats(pid)


@router.get("/{project}/use-cases")
async def list_approved_use_cases(project: str):
    """Return approved use cases with nested children and event stats."""
    pid = _pid(project)
    wi  = _wi(project)
    ucs = wi.get_approved_use_cases(pid)
    return {"project": project, "use_cases": ucs, "count": len(ucs)}


@router.get("/{project}")
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


@router.post("/{project}/{item_id}/approve")
async def approve_work_item(project: str, item_id: str):
    """Approve a work item: assign wi_id (BU0001/FE0002/…), mark mirror rows."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.approve(item_id, pid)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/{project}/{item_id}/reject")
async def reject_work_item(project: str, item_id: str):
    """Reject a work item: assign REJxxxxxx wi_id, mark mirror rows."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.reject(item_id, pid)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.patch("/{project}/{item_id}")
async def update_work_item(project: str, item_id: str, body: WiUpdateRequest):
    """Update editable fields on a work item."""
    pid    = _pid(project)
    wi     = _wi(project)
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    result = wi.update(item_id, pid, fields)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{project}/reorder")
async def reorder_work_items(project: str, body: WiReorderRequest):
    """Bulk-update user_importance for a list of items (drag-to-reorder within UC)."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.reorder_items(pid, [i.model_dump() for i in body.items])
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.delete("/{project}/{item_id}")
async def delete_work_item(project: str, item_id: str):
    """Delete a pending work item."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.delete(item_id, pid)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{project}/{item_id}/move")
async def move_event_to_item(project: str, item_id: str, body: WiMoveRequest):
    """Move a mirror event from one work item to another."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.move_event(item_id, pid, body.mrr_type, body.mrr_id, body.target_wi_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{project}/approve-all")
async def approve_all_under(project: str, body: WiApproveAllRequest):
    """Approve all pending items under a parent work item."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.approve_all_under(body.parent_id, pid)
    return result


@router.post("/{project}/reset")
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


@router.post("/{project}")
async def create_wi(project: str, body: WiCreateRequest):
    """Create a work item directly (no LLM classification required)."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.create_item(pid, body.model_dump())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{project}/{uc_id}/versions")
async def list_uc_versions(project: str, uc_id: str):
    """List snapshot versions for a use case, newest first."""
    pid = _pid(project)
    wi  = _wi(project)
    return {"versions": wi.get_versions(uc_id, pid)}


@router.post("/{project}/{uc_id}/versions")
async def create_uc_version(project: str, uc_id: str):
    """Snapshot the current UC state as a new version."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.create_version(uc_id, pid, created_by="user")
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{project}/{uc_id}/ai-summarise")
async def ai_summarise_uc(project: str, uc_id: str):
    """Call Haiku to rewrite the UC summary and reorder items; saves as draft version."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = await wi.ai_summarise_uc(uc_id, pid)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.post("/{project}/{uc_id}/versions/{version_id}/apply")
async def apply_uc_version(project: str, uc_id: str, version_id: str):
    """Apply a version snapshot to live data (archives current state first)."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.apply_version(version_id, uc_id, pid)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/{project}/{item_id}/md")
async def get_wi_md(project: str, item_id: str):
    """Return Markdown content for a use_case work item."""
    pid     = _pid(project)
    wi      = _wi(project)
    content = wi.get_md(item_id, pid)
    return {"content": content}


@router.post("/{project}/{item_id}/md")
async def save_wi_md(project: str, item_id: str, body: WiMdSaveRequest):
    """Save edited Markdown back to DB and file."""
    pid    = _pid(project)
    wi     = _wi(project)
    result = wi.save_md(item_id, pid, body.content)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/{project}/{item_id}/md/refresh")
async def refresh_wi_md(project: str, item_id: str):
    """Regenerate Markdown from DB and write to file."""
    pid     = _pid(project)
    wi      = _wi(project)
    content = wi.refresh_md(item_id, pid)
    return {"content": content}
