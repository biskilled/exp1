"""
route_work_items.py — API endpoints for the DB-first work items pipeline.

All endpoints are registered at the /wi prefix (set in main.py).

Endpoints:
    POST  /wi/{project}/classify         — classify pending mirror rows
    GET   /wi/{project}/classify-status  — is classify running? + pending mrr counts
    GET   /wi/{project}/pending          — pending items
    GET   /wi/{project}/use-cases        — approved use cases with children + stats
    GET   /wi/{project}/file-hotspots   — file-level code hotspot metrics
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

# ── Process-level classify state ──────────────────────────────────────────────
# Keyed by project name → True while classify() is running in this process.
_classify_running: dict[str, bool] = {}


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
    due_date:         Optional[str]   = None   # ISO date "YYYY-MM-DD" or null to clear
    start_date:       Optional[str]   = None   # set by server; rarely passed directly


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
    max_use_cases: int = Query(0, description="Target max use cases (0 = read from work_items.yaml)"),
):
    """Classify all pending mirror rows into mem_work_items via LLM.

    ?background=true returns immediately; classification runs in background.
    ?max_use_cases=N   override max use cases (0 = use YAML default).
    Default: synchronous, returns classified items immediately.
    """
    if _classify_running.get(project):
        return {"status": "already_running", "project": project}

    wi = _wi(project)

    if background:
        async def _run():
            _classify_running[project] = True
            try:
                result = await wi.classify(max_use_cases=max_use_cases or None)
                log.info(f"wi.classify background: {project} — {result.get('classified',0)} items")
            except Exception as e:
                log.warning(f"wi.classify background error: {e}")
            finally:
                _classify_running.pop(project, None)
        background_tasks.add_task(_run)
        return {"status": "started", "project": project}

    _classify_running[project] = True
    try:
        result = await wi.classify(max_use_cases=max_use_cases or None)
        return {"project": project, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        _classify_running.pop(project, None)


@router.get("/{project}/classify-status")
async def classify_status(project: str):
    """Return whether a classify job is currently running for this project."""
    pid = _pid(project)
    wi  = _wi(project)
    # Also return pending mrr counts so the UI can show them without a separate stats call
    pending_mrr = wi.get_pending_mrr_counts(pid)
    return {
        "running":  _classify_running.get(project, False),
        "project":  project,
        **pending_mrr,
    }


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


@router.get("/{project}/file-hotspots")
async def list_file_hotspots(
    project: str,
    min_score: float = Query(1.0, description="Minimum hotspot score"),
    limit: int = Query(30, description="Max results"),
    file_path: Optional[str] = Query(None, description="Filter to specific file path"),
):
    """Return file-level code hotspot metrics for project planning insight."""
    from memory.memory_code_parser import get_file_hotspots, get_coupled_files
    pid = _pid(project)
    if file_path:
        hotspots = get_file_hotspots(pid, file_paths=[file_path])
        coupled = get_coupled_files(pid, file_path) if hotspots else []
        return {
            "project": project,
            "file": hotspots[0] if hotspots else None,
            "coupled_files": coupled,
        }
    hotspots = get_file_hotspots(pid, min_score=min_score, limit=limit)
    return {"project": project, "hotspots": hotspots, "count": len(hotspots)}


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
    # Use exclude_unset so we can distinguish "not provided" from explicit null.
    # Allow explicit null for date fields (to clear them); filter None for everything else.
    _nullable = {"due_date", "start_date"}
    dumped = body.model_dump(exclude_unset=True)
    fields = {k: v for k, v in dumped.items() if v is not None or k in _nullable}
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


@router.get("/{project}/completed")
async def list_completed_use_cases(project: str):
    """Return all completed use cases with summary, dates, and total_days."""
    pid = _pid(project)
    wi  = _wi(project)
    return {"use_cases": wi.get_completed_use_cases(pid)}


@router.post("/{project}/{item_id}/complete")
async def complete_use_case(project: str, item_id: str):
    """Mark a use case as completed (validates all items done first)."""
    pid = _pid(project)
    wi  = _wi(project)
    return wi.complete_use_case(item_id, pid)


@router.post("/{project}/{item_id}/reopen")
async def reopen_use_case(project: str, item_id: str):
    """Reopen a completed use case."""
    pid = _pid(project)
    wi  = _wi(project)
    return wi.reopen_use_case(item_id, pid)
