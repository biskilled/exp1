"""
route_backlog.py — API endpoints for the file-based backlog pipeline.

Endpoints:
    POST /memory/{project}/sync-backlog          — flush pending rows → backlog.md
    POST /memory/{project}/work-items            — full run_work_items() pipeline
    GET  /memory/{project}/backlog               — parsed backlog entries as JSON
    PATCH /memory/{project}/backlog/{ref_id}     — approve/reject/retag single entry
    GET  /memory/{project}/use-case-section      — read a section from a use case file
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from core.config import settings

log = logging.getLogger(__name__)
router = APIRouter()


# ── Models ────────────────────────────────────────────────────────────────────

class BacklogPatchRequest(BaseModel):
    approve: Optional[str] = None    # "x" | "-" | " "
    tag:     Optional[str] = None    # tag override (replaces TAG comment)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/{project}/sync-backlog")
async def sync_backlog(
    project: str,
    background_tasks: BackgroundTasks,
    source: Optional[str] = Query(
        None,
        description="Filter to a single source: commits|prompts|messages|items. Default = all.",
    ),
):
    """Flush pending mirror rows for a project into backlog.md.

    Threshold check is bypassed — all pending rows are processed regardless
    of the count threshold in backlog_config.yaml.
    """
    from memory.memory_backlog import MemoryBacklog
    bl = MemoryBacklog(project)

    if source:
        valid = {"commits", "prompts", "messages", "items"}
        if source not in valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source '{source}'. Must be one of: {', '.join(sorted(valid))}",
            )
        n = await bl.process_pending(source)
        results = {source: n}
    else:
        results = await bl.process_all_pending()

    total = sum(results.values())
    return {
        "project":       project,
        "appended":      total,
        "by_source":     results,
        "backlog_file":  str(bl._backlog_path()),
    }


@router.post("/{project}/work-items")
async def run_work_items_endpoint(
    project: str,
    background_tasks: BackgroundTasks,
):
    """Run full work-items pipeline as a background task.

    Pipeline:
        1. Flush all unprocessed mirror rows → backlog.md
        2. Approve all entries with APPROVE: x
        3. Create/merge into use_cases/{slug}.md
        4. Rewrite backlog.md (pending stays, processed/rejected archived)
    """
    async def _run():
        from memory.memory_backlog import run_work_items
        try:
            result = await run_work_items(project)
            log.info(f"work_items: {project} — {result}")
        except Exception as e:
            log.warning(f"work_items background error: {e}")

    background_tasks.add_task(_run)
    return {"status": "started", "project": project}


@router.post("/{project}/work-items/sync")
async def run_work_items_sync(project: str):
    """Run work-items pipeline synchronously and return results immediately."""
    from memory.memory_backlog import run_work_items
    try:
        result = await run_work_items(project)
        return {"project": project, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project}/backlog-stats")
async def get_backlog_stats(project: str):
    """Return counters for the Backlog tab header.

    Returns per-source-type counts of:
      - pending:   rows with backlog_ref IS NULL (not yet digested)
      - processed: rows with backlog_ref IS NOT NULL (already in backlog.md)
      - batches:   processed / cnt (how many Haiku batch calls were made)

    Also returns the current cnt threshold per source from backlog_config.yaml.
    """
    from memory.memory_backlog import MemoryBacklog, _TABLE
    from core.database import db

    bl = MemoryBacklog(project)

    if not db.is_available():
        raise HTTPException(status_code=503, detail="Database not available")

    project_id = db.get_or_create_project_id(project)
    cfg = bl._config().get("mirroring_event_summary", {})

    stats: dict = {}
    sources = ["prompts", "commits", "messages", "items"]
    pk = {"commits": "commit_hash"}

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                for src in sources:
                    tbl = _TABLE[src]
                    cur.execute(
                        f"SELECT COUNT(*) FROM {tbl} WHERE project_id=%s AND backlog_ref IS NULL",
                        (project_id,),
                    )
                    pending = cur.fetchone()[0] or 0

                    cur.execute(
                        f"SELECT COUNT(*) FROM {tbl} WHERE project_id=%s AND backlog_ref IS NOT NULL",
                        (project_id,),
                    )
                    processed = cur.fetchone()[0] or 0

                    cnt = int(cfg.get(src, {}).get("cnt", 5))
                    batches = processed // cnt if cnt > 0 else 0

                    stats[src] = {
                        "pending":   pending,
                        "processed": processed,
                        "batches":   batches,
                        "cnt":       cnt,
                    }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Totals
    total_pending   = sum(s["pending"]   for s in stats.values())
    total_processed = sum(s["processed"] for s in stats.values())
    total_batches   = sum(s["batches"]   for s in stats.values())

    return {
        "project":         project,
        "by_source":       stats,
        "total_pending":   total_pending,
        "total_processed": total_processed,
        "total_batches":   total_batches,
    }


@router.get("/{project}/backlog")
async def get_backlog(project: str):
    """Return all parsed backlog entries as JSON for the UI."""
    from memory.memory_backlog import MemoryBacklog
    bl = MemoryBacklog(project)
    entries = bl.parse_backlog()
    return {
        "project": project,
        "total":   len(entries),
        "entries": entries,
    }


@router.patch("/{project}/backlog/{ref_id}")
async def patch_backlog_entry(
    project: str,
    ref_id:  str,
    body:    BacklogPatchRequest,
):
    """Approve, reject, or retag a single backlog entry in-place.

    Updates the inline HTML comment markers directly in backlog.md.
    """
    from memory.memory_backlog import MemoryBacklog
    bl = MemoryBacklog(project)
    path = bl._backlog_path()

    if not path.exists():
        raise HTTPException(status_code=404, detail="backlog.md not found")

    text = path.read_text(errors="ignore")

    # Find the chunk containing this ref_id
    import re as _re
    chunks = _re.split(r"\n---\n", text)

    updated = False
    new_chunks: list[str] = []
    for chunk in chunks:
        if ref_id in chunk and f"### {ref_id} " in chunk:
            if body.approve is not None:
                val = body.approve[:1] if body.approve else " "
                # Replace APPROVE comment value
                chunk = _re.sub(
                    r"<!--\s*APPROVE:\s*\[[ x\-]\]\s*-->",
                    f"<!-- APPROVE: [{val}] -->",
                    chunk,
                )
            if body.tag is not None:
                chunk = _re.sub(
                    r"<!--\s*TAG:\s*.*?-->",
                    f"<!-- TAG: {body.tag} -->",
                    chunk,
                )
            updated = True
        new_chunks.append(chunk)

    if not updated:
        raise HTTPException(status_code=404, detail=f"Ref ID '{ref_id}' not found in backlog")

    path.write_text("\n---\n".join(new_chunks))
    return {"status": "updated", "ref_id": ref_id, "project": project}


@router.get("/{project}/use-case-events")
async def get_use_case_events(
    project: str,
    tag_id: Optional[str] = Query(None, description="planner_tags UUID"),
    slug: Optional[str]   = Query(None, description="use_case_slug (alternative to tag_id)"),
):
    """Return all backlog refs linked to a use case, with their source row details.

    Queries mem_backlog_links then joins back to mem_mrr_* tables so the UI
    can show a full audit trail of which raw prompts/commits contributed to
    a use case — even if the .md file is edited or deleted.

    At least one of tag_id or slug must be supplied.
    """
    if not tag_id and not slug:
        raise HTTPException(status_code=400, detail="Provide tag_id or slug")

    from memory.memory_backlog import MemoryBacklog
    from core.database import db

    if not db.is_available():
        raise HTTPException(status_code=503, detail="Database not available")

    bl = MemoryBacklog(project)
    project_id = bl._get_project_id()
    if not project_id:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Resolve slug from tag_id if needed
                if tag_id and not slug:
                    cur.execute(
                        "SELECT use_case_slug FROM mem_backlog_links "
                        "WHERE project_id=%s AND tag_id=%s::uuid LIMIT 1",
                        (project_id, tag_id),
                    )
                    row = cur.fetchone()
                    slug = row[0] if row else None

                if not slug:
                    return {"project": project, "slug": slug, "events": []}

                # Fetch all links for this slug
                cur.execute(
                    """SELECT ref_id, classify, summary, approved_at, tag_id::text
                       FROM mem_backlog_links
                       WHERE project_id=%s AND use_case_slug=%s
                       ORDER BY approved_at""",
                    (project_id, slug),
                )
                links = cur.fetchall()

                events = []
                for ref_id, classify, summary, approved_at, t_id in links:
                    # Determine source type from prefix letter
                    prefix = ref_id[0] if ref_id else ""
                    src_map = {"P": "prompts", "C": "commits", "M": "messages", "I": "items"}
                    src_type = src_map.get(prefix)

                    source_row: dict = {}
                    if src_type == "prompts":
                        cur.execute(
                            "SELECT id::text, left(prompt,200), created_at FROM mem_mrr_prompts "
                            "WHERE project_id=%s AND backlog_ref=%s LIMIT 5",
                            (project_id, ref_id),
                        )
                        source_row = [
                            {"id": r[0], "prompt_preview": r[1], "created_at": str(r[2])}
                            for r in cur.fetchall()
                        ]
                    elif src_type == "commits":
                        cur.execute(
                            "SELECT commit_hash_short, commit_msg, created_at FROM mem_mrr_commits "
                            "WHERE project_id=%s AND backlog_ref=%s LIMIT 5",
                            (project_id, ref_id),
                        )
                        source_row = [
                            {"hash": r[0], "msg": r[1], "created_at": str(r[2])}
                            for r in cur.fetchall()
                        ]
                    elif src_type == "items":
                        cur.execute(
                            "SELECT id::text, title, item_type, created_at FROM mem_mrr_items "
                            "WHERE project_id=%s AND backlog_ref=%s LIMIT 5",
                            (project_id, ref_id),
                        )
                        source_row = [
                            {"id": r[0], "title": r[1], "type": r[2], "created_at": str(r[3])}
                            for r in cur.fetchall()
                        ]

                    events.append({
                        "ref_id":      ref_id,
                        "source_type": src_type,
                        "classify":    classify,
                        "summary":     summary,
                        "approved_at": str(approved_at) if approved_at else None,
                        "tag_id":      t_id,
                        "source_rows": source_row,
                    })

                return {
                    "project":  project,
                    "slug":     slug,
                    "tag_id":   tag_id,
                    "total":    len(events),
                    "events":   events,
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{project}/regenerate-use-case")
async def regenerate_use_case(
    project: str,
    slug: str = Query(..., description="use_case slug to regenerate Internal Usage for"),
):
    """Rebuild the ## Internal Usage section of a use case file from mem_backlog_links.

    Use this if the section was accidentally deleted or edited by a user.
    """
    from memory.memory_backlog import MemoryBacklog, _regenerate_internal_usage

    bl = MemoryBacklog(project)
    project_id = bl._get_project_id()
    if not project_id:
        raise HTTPException(status_code=404, detail="Project not found")

    uc_dir = bl._use_cases_dir()
    path = uc_dir / f"{slug}.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"use_cases/{slug}.md not found")

    _regenerate_internal_usage(uc_dir, slug, project_id)
    return {"status": "regenerated", "slug": slug, "project": project}


@router.get("/{project}/use-case-section")
async def get_use_case_section(
    project: str,
    ref: str = Query(..., description="Relative path with optional anchor: use_cases/auth.md#open-bugs"),
):
    """Return the content of a section within a use case file.

    The `ref` parameter follows the format `use_cases/{slug}.md[#{anchor}]`.
    If no anchor is given, returns the full file content.
    """
    from memory.memory_backlog import MemoryBacklog
    bl = MemoryBacklog(project)

    code_dir = bl._use_cases_dir().parent.parent  # documents/../  = code_dir
    # _use_cases_dir returns {code_dir}/documents/use_cases
    # so parent.parent is code_dir
    base_dir = bl._use_cases_dir().parent.parent

    # Split ref into path + anchor
    if "#" in ref:
        file_part, anchor = ref.split("#", 1)
    else:
        file_part, anchor = ref, ""

    target = (base_dir / file_part).resolve()

    # Safety: must stay inside base_dir
    try:
        target.relative_to(base_dir.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Path traversal not allowed")

    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_part}")

    full_text = target.read_text(errors="ignore")

    if not anchor:
        return {"ref": ref, "content": full_text}

    # Extract section by heading anchor (normalise: lowercase, spaces→hyphens)
    def _norm(h: str) -> str:
        return re.sub(r"[^a-z0-9\-]", "", h.lower().replace(" ", "-"))

    lines = full_text.splitlines()
    section_lines: list[str] = []
    in_section = False
    section_level = 0

    for line in lines:
        heading_m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_m:
            level = len(heading_m.group(1))
            heading_text = heading_m.group(2)
            if _norm(heading_text) == _norm(anchor):
                in_section = True
                section_level = level
                section_lines.append(line)
                continue
            if in_section and level <= section_level:
                break
        if in_section:
            section_lines.append(line)

    if not section_lines:
        raise HTTPException(status_code=404, detail=f"Section '#{anchor}' not found in {file_part}")

    return {"ref": ref, "content": "\n".join(section_lines)}
