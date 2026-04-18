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
    approve:  Optional[str] = None   # "x" | "-" | " "
    tag:      Optional[str] = None   # tag override (replaces TAG comment)
    classify: Optional[str] = None   # "feature" | "task" | "bug" | "use_case"
    status:   Optional[str] = None   # "in-progress" | "completed"
    summary:  Optional[str] = None   # update the item's one-line summary text


class GroupActionRequest(BaseModel):
    slug:    str
    approve: str   # "x" = approve all → merge into use case; "-" = reject all


class GroupMetaPatchRequest(BaseModel):
    new_slug:                 Optional[str]       = None   # rename the group
    summary:                  Optional[str]       = None   # update > Summary: line
    user_tags:                Optional[list[str]] = None   # replace > User tags: line
    remove_delivery_index:    Optional[int]       = None   # remove one synthesized delivery by index
    remove_ai_new_tag_index:  Optional[int]       = None   # dismiss one AI-suggested new tag
    remove_requirement_index: Optional[int]       = None   # remove one requirement bullet
    add_requirement:          Optional[str]       = None   # append a requirement (undo support)
    restore_delivery:         Optional[str]       = None   # append a delivery (undo support)
    restore_ai_new_tag:       Optional[str]       = None   # append an AI new tag (undo support)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/{project}/sync-backlog")
async def sync_backlog(
    project: str,
    background_tasks: BackgroundTasks,
    source: Optional[str] = Query(
        None,
        description="Filter to a single source: commits|prompts|messages|items. Default = all.",
    ),
    mode: Optional[str] = Query(
        None,
        description="Processing mode. 'full' = full-digest (all pending → max 7 groups, auto-approved).",
    ),
):
    """Flush pending mirror rows for a project into backlog.md.

    Modes:
      (default) — threshold-based batch processing per cnt in backlog_config.yaml
      mode=full — full-digest: ALL pending data → max 7 use-case groups, auto-approved
    """
    if mode == "full":
        from memory.memory_backlog import process_full_digest
        result = await process_full_digest(project)
        from memory.memory_backlog import MemoryBacklog
        bl = MemoryBacklog(project)
        return {
            "project":    project,
            "mode":       "full",
            "backlog_file": str(bl._backlog_path()),
            **result,
        }

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
                    # Commits: only count standalone (no prompt link) as pending
                    if src == "commits":
                        cur.execute(
                            "SELECT COUNT(*) FROM mem_mrr_commits "
                            "WHERE project_id=%s AND backlog_ref IS NULL AND prompt_id IS NULL",
                            (project_id,),
                        )
                        pending = cur.fetchone()[0] or 0
                        cur.execute(
                            "SELECT COUNT(*) FROM mem_mrr_commits "
                            "WHERE project_id=%s AND backlog_ref IS NOT NULL",
                            (project_id,),
                        )
                    else:
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
    # Support both old "\n---\n" and new "\n\n---\n\n" separators
    sep_pattern = r"\n\n?---\n\n?"
    chunks = _re.split(sep_pattern, text)

    updated = False
    new_chunks: list[str] = []
    for chunk in chunks:
        if ref_id in chunk:
            if body.approve is not None:
                val = body.approve[:1] if body.approve else " "
                # New GROUP format: item line is "  SOURCE REF_ID [APPROVE] ..."
                chunk = _re.sub(
                    rf"({_re.escape(ref_id)}\s+)\[[+ x\-]*\]",
                    rf"\1[{val}]",
                    chunk,
                )
                # Legacy format fallback
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
            if body.classify is not None:
                # Replace [classify] — 2nd bracket after ref_id (approve is 1st)
                chunk = _re.sub(
                    rf"({_re.escape(ref_id)}\s+\[[^\]]*\]\s+)\[[^\]]*\]",
                    rf"\1[{body.classify}]",
                    chunk,
                )
            if body.status is not None:
                # Replace [status] — 3rd bracket after ref_id
                chunk = _re.sub(
                    rf"({_re.escape(ref_id)}\s+\[[^\]]*\]\s+\[[^\]]*\]\s+)\[[^\]]*\]",
                    rf"\1[{body.status}]",
                    chunk,
                )
            if body.summary is not None:
                # Replace summary text after "— " on the item line
                chunk = _re.sub(
                    rf"^(  \w+\s+{_re.escape(ref_id)}\s+(?:\[[^\]]*\]\s+){{3}}\[[^\]]*\]\s*—\s+).*$",
                    lambda m, s=body.summary: m.group(1) + s,
                    chunk,
                    flags=_re.MULTILINE,
                )
            updated = True
        new_chunks.append(chunk)

    if not updated:
        raise HTTPException(status_code=404, detail=f"Ref ID '{ref_id}' not found in backlog")

    path.write_text("\n\n---\n\n".join(new_chunks))
    return {"status": "updated", "ref_id": ref_id, "project": project}


@router.post("/{project}/backlog/approve-group")
async def approve_group(project: str, body: GroupActionRequest):
    """Approve or reject all items in a backlog group at once.

    approve="x" → merge all items into use_cases/*.md + planner_tags
    approve="-"  → reject all items (move to REJECTED section)
    """
    from memory.memory_backlog import run_work_items_for_group
    try:
        result = await run_work_items_for_group(project, body.slug, body.approve)
        return {"project": project, **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{project}/backlog/group/{slug}")
async def patch_backlog_group(project: str, slug: str, body: GroupMetaPatchRequest):
    """Rename a backlog group or update its Summary line in-place.

    new_slug: renames the ## **{slug}** header to the new slug.
    summary:  replaces (or inserts) the > Summary: line in the group block.
    """
    from memory.memory_backlog import MemoryBacklog
    import re as _re

    bl = MemoryBacklog(project)
    path = bl._backlog_path()

    if not path.exists():
        raise HTTPException(status_code=404, detail="backlog.md not found")

    text = path.read_text(errors="ignore")
    sep_pattern = r"\n\n?---\n\n?"
    chunks = _re.split(sep_pattern, text)

    updated = False
    new_chunks: list[str] = []
    for chunk in chunks:
        # Identify group chunk by its header slug
        if f"## **{slug}**" not in chunk:
            new_chunks.append(chunk)
            continue

        if body.summary is not None:
            if _re.search(r"^> Summary:", chunk, _re.MULTILINE):
                chunk = _re.sub(
                    r"^> Summary:.*$",
                    f"> Summary: {body.summary}",
                    chunk,
                    flags=_re.MULTILINE,
                )
            else:
                chunk = _re.sub(
                    r"(^## \*\*.+\*\*.*$)",
                    rf"\1\n> Summary: {body.summary}",
                    chunk,
                    flags=_re.MULTILINE,
                    count=1,
                )

        if body.user_tags is not None:
            tags_val = "; ".join(body.user_tags)
            if _re.search(r"^> User tags:", chunk, _re.MULTILINE):
                chunk = _re.sub(
                    r"^> User tags:.*$",
                    f"> User tags: {tags_val}",
                    chunk,
                    flags=_re.MULTILINE,
                )
            else:
                chunk = _re.sub(
                    r"(^> Type:.*$)",
                    rf"\1\n> User tags: {tags_val}",
                    chunk,
                    flags=_re.MULTILINE,
                    count=1,
                )

        if body.remove_delivery_index is not None:
            m = _re.search(r"^> Deliveries:\s*(.+)$", chunk, _re.MULTILINE)
            if m:
                parts = [p.strip() for p in m.group(1).split(";") if p.strip()]
                idx = body.remove_delivery_index
                if 0 <= idx < len(parts):
                    parts.pop(idx)
                new_val = "; ".join(parts)
                if new_val:
                    chunk = _re.sub(
                        r"^> Deliveries:.*$",
                        f"> Deliveries: {new_val}",
                        chunk,
                        flags=_re.MULTILINE,
                    )
                else:
                    chunk = _re.sub(r"^> Deliveries:.*\n?", "", chunk, flags=_re.MULTILINE)

        if body.remove_ai_new_tag_index is not None:
            m = _re.search(r"^> AI new:\s*(.+)$", chunk, _re.MULTILINE)
            if m:
                parts = [p.strip() for p in m.group(1).split(",") if p.strip()]
                idx = body.remove_ai_new_tag_index
                if 0 <= idx < len(parts):
                    parts.pop(idx)
                new_val = ", ".join(parts)
                if new_val:
                    chunk = _re.sub(r"^> AI new:.*$", f"> AI new: {new_val}", chunk, flags=_re.MULTILINE)
                else:
                    chunk = _re.sub(r"^> AI new:.*\n?", "", chunk, flags=_re.MULTILINE)

        if body.remove_requirement_index is not None:
            m = _re.search(r"^> Requirements:\s*(.+)$", chunk, _re.MULTILINE)
            if m:
                parts = [p.strip() for p in m.group(1).split(";") if p.strip()]
                idx = body.remove_requirement_index
                if 0 <= idx < len(parts):
                    parts.pop(idx)
                new_val = "; ".join(parts)
                if new_val:
                    chunk = _re.sub(r"^> Requirements:.*$", f"> Requirements: {new_val}", chunk, flags=_re.MULTILINE)
                else:
                    chunk = _re.sub(r"^> Requirements:.*\n?", "", chunk, flags=_re.MULTILINE)

        if body.new_slug is not None:
            new_slug = body.new_slug.strip().lower()
            new_slug = _re.sub(r"[^a-z0-9\-]", "-", new_slug).strip("-") or "general"
            chunk = chunk.replace(f"## **{slug}**", f"## **{new_slug}**", 1)

        if body.add_requirement is not None and body.add_requirement.strip():
            req_val = body.add_requirement.strip()
            m = _re.search(r"^> Requirements:\s*(.+)$", chunk, _re.MULTILINE)
            if m:
                chunk = _re.sub(r"^> Requirements:.*$",
                                f"> Requirements: {m.group(1).rstrip()}; {req_val}",
                                chunk, flags=_re.MULTILINE)
            else:
                chunk = _re.sub(r"(^## \*\*.+\*\*.*$)",
                                r"\1" + "\n> Requirements: " + req_val,
                                chunk, flags=_re.MULTILINE, count=1)

        if body.restore_delivery is not None and body.restore_delivery.strip():
            d_val = body.restore_delivery.strip()
            m = _re.search(r"^> Deliveries:\s*(.+)$", chunk, _re.MULTILINE)
            if m:
                chunk = _re.sub(r"^> Deliveries:.*$",
                                f"> Deliveries: {m.group(1).rstrip()}; {d_val}",
                                chunk, flags=_re.MULTILINE)
            else:
                chunk = _re.sub(r"(^> Summary:.*$)",
                                r"\1" + "\n> Deliveries: " + d_val,
                                chunk, flags=_re.MULTILINE, count=1)

        if body.restore_ai_new_tag is not None and body.restore_ai_new_tag.strip():
            tag_val = body.restore_ai_new_tag.strip()
            m = _re.search(r"^> AI new:\s*(.*)$", chunk, _re.MULTILINE)
            if m:
                existing = m.group(1).strip()
                new_line = f"> AI new: {existing + ', ' if existing else ''}{tag_val}"
                chunk = _re.sub(r"^> AI new:.*$", new_line, chunk, flags=_re.MULTILINE)
            else:
                chunk = _re.sub(r"(^> AI existing:.*$)",
                                r"\1" + "\n> AI new: " + tag_val,
                                chunk, flags=_re.MULTILINE, count=1)

        updated = True
        new_chunks.append(chunk)

    if not updated:
        raise HTTPException(status_code=404, detail=f"Group '{slug}' not found in backlog")

    path.write_text("\n\n---\n\n".join(new_chunks))
    return {"status": "updated", "slug": slug,
            "new_slug": body.new_slug or slug, "project": project}


@router.get("/{project}/use-case-slugs")
async def get_use_case_slugs(project: str):
    """Return all known use-case slugs, separated into file-based vs backlog-only groups."""
    from memory.memory_backlog import MemoryBacklog
    bl = MemoryBacklog(project)
    uc_dir = bl._use_cases_dir()
    file_slugs: list[str] = []
    if uc_dir.exists():
        file_slugs = sorted(f.stem for f in uc_dir.glob("*.md")
                            if f.stem not in ("use_case_template",))
    groups = bl.parse_backlog()
    group_slugs = sorted({g["slug"] for g in groups if g.get("slug")} - set(file_slugs))
    all_slugs = sorted(set(file_slugs) | set(group_slugs))
    return {"project": project, "slugs": all_slugs,
            "file_slugs": file_slugs, "group_slugs": group_slugs}


@router.get("/{project}/backlog/code-stats/{slug}")
async def get_group_code_stats(project: str, slug: str):
    """Return commit code statistics for all prompts in a backlog group.

    Joins mem_mrr_prompts → mem_mrr_commits → mem_mrr_commits_code by backlog_ref.
    Returns: linked_commits, files_changed, rows_added, rows_removed, top_files.
    """
    from memory.memory_backlog import MemoryBacklog
    from core.database import db

    _empty = {"slug": slug, "linked_commits": 0, "files_changed": 0,
              "rows_added": 0, "rows_removed": 0, "top_files": []}

    if not db.is_available():
        return _empty

    bl = MemoryBacklog(project)
    groups = bl.parse_backlog()
    group = next((g for g in groups if g.get("slug") == slug), None)
    if not group:
        return _empty

    prompt_refs = [
        item["ref_id"] for item in group.get("items", [])
        if item.get("src_label") == "PROMPTS" and item.get("ref_id")
    ]
    if not prompt_refs:
        return _empty

    project_id = db.get_or_create_project_id(project)
    placeholders = ",".join(["%s"] * len(prompt_refs))

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""SELECT COUNT(DISTINCT c.commit_hash),
                               COUNT(DISTINCT cc.file_path),
                               COALESCE(SUM(cc.rows_added), 0),
                               COALESCE(SUM(cc.rows_removed), 0)
                        FROM mem_mrr_prompts p
                        JOIN mem_mrr_commits c
                             ON c.prompt_id = p.id AND c.project_id = %s
                        LEFT JOIN mem_mrr_commits_code cc
                             ON cc.commit_hash = c.commit_hash AND cc.project_id = %s
                        WHERE p.project_id = %s AND p.backlog_ref IN ({placeholders})""",
                    (project_id, project_id, project_id, *prompt_refs),
                )
                row = cur.fetchone() or (0, 0, 0, 0)
                commit_count, files_changed, rows_added, rows_removed = row

                cur.execute(
                    f"""SELECT cc.file_path,
                               COUNT(*) AS chg,
                               COALESCE(SUM(cc.rows_added), 0),
                               COALESCE(SUM(cc.rows_removed), 0)
                        FROM mem_mrr_prompts p
                        JOIN mem_mrr_commits c
                             ON c.prompt_id = p.id AND c.project_id = %s
                        JOIN mem_mrr_commits_code cc
                             ON cc.commit_hash = c.commit_hash AND cc.project_id = %s
                        WHERE p.project_id = %s AND p.backlog_ref IN ({placeholders})
                        GROUP BY cc.file_path
                        ORDER BY chg DESC, 3 DESC LIMIT 5""",
                    (project_id, project_id, project_id, *prompt_refs),
                )
                top_files = [
                    {"path": r[0], "changes": int(r[1]),
                     "added": int(r[2]), "removed": int(r[3])}
                    for r in cur.fetchall()
                ]
    except Exception as e:
        log.warning(f"get_group_code_stats({slug}): {e}")
        return _empty

    return {
        "slug":           slug,
        "linked_commits": int(commit_count or 0),
        "files_changed":  int(files_changed or 0),
        "rows_added":     int(rows_added or 0),
        "rows_removed":   int(rows_removed or 0),
        "top_files":      top_files,
    }


@router.post("/{project}/export-commit-analysis")
async def export_commit_analysis(project: str):
    """Generate a commit analysis report in workspace/{project}/logs/.

    Queries:
      1. All commits linked to prompts (via prompt_id) with commit_code symbols
      2. All standalone commits (no prompt_id) with commit_code symbols

    Writes to workspace/{project}/logs/commit_analysis.md
    Returns summary stats.
    """
    from memory.memory_backlog import MemoryBacklog
    from core.database import db
    from datetime import datetime

    if not db.is_available():
        raise HTTPException(status_code=503, detail="Database not available")

    bl = MemoryBacklog(project)
    project_id = db.get_or_create_project_id(project)

    # Ensure logs dir exists
    ws = Path(settings.workspace_dir) / project / "logs"
    ws.mkdir(parents=True, exist_ok=True)
    out_path = ws / "commit_analysis.md"

    lines: list[str] = [
        f"# Commit Analysis — {project}",
        f"_Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC_",
        "",
    ]

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # ── Summary ─────────────────────────────────────────────────
                cur.execute(
                    """SELECT
                         COUNT(*) FILTER (WHERE prompt_id IS NOT NULL)     AS linked,
                         COUNT(*) FILTER (WHERE prompt_id IS NULL)         AS standalone,
                         COUNT(*) FILTER (WHERE backlog_ref IS NULL AND prompt_id IS NULL) AS pending
                       FROM mem_mrr_commits WHERE project_id=%s""",
                    (project_id,),
                )
                tot = cur.fetchone() or (0, 0, 0)
                lines += [
                    "## Summary",
                    f"| | Count |",
                    f"|---|---|",
                    f"| Linked commits (via prompt_id) | {tot[0]} |",
                    f"| Standalone commits | {tot[1]} |",
                    f"| Pending (not yet processed) | {tot[2]} |",
                    "",
                ]

                cur.execute(
                    """SELECT
                         COUNT(DISTINCT cc.file_path),
                         COALESCE(SUM(cc.rows_added),0),
                         COALESCE(SUM(cc.rows_removed),0)
                       FROM mem_mrr_commits_code cc WHERE cc.project_id=%s""",
                    (project_id,),
                )
                code_tot = cur.fetchone() or (0, 0, 0)
                lines += [
                    f"| Unique files touched | {code_tot[0]} |",
                    f"| Total rows added | {code_tot[1]} |",
                    f"| Total rows removed | {code_tot[2]} |",
                    "",
                ]

                # ── Per use-case breakdown (linked commits via backlog_ref) ─
                cur.execute(
                    """SELECT
                         p.backlog_ref,
                         COUNT(DISTINCT c.commit_hash)  AS commits,
                         COUNT(DISTINCT cc.file_path)   AS files,
                         COALESCE(SUM(cc.rows_added),0) AS added,
                         COALESCE(SUM(cc.rows_removed),0) AS removed
                       FROM mem_mrr_prompts p
                       JOIN mem_mrr_commits c ON c.prompt_id = p.id AND c.project_id=%s
                       LEFT JOIN mem_mrr_commits_code cc ON cc.commit_hash = c.commit_hash AND cc.project_id=%s
                       WHERE p.project_id=%s AND p.backlog_ref IS NOT NULL
                       GROUP BY p.backlog_ref
                       ORDER BY commits DESC LIMIT 50""",
                    (project_id, project_id, project_id),
                )
                prows = cur.fetchall()
                if prows:
                    lines += [
                        "## Linked Commits by Prompt Ref",
                        "| Prompt | Commits | Files | +Lines | -Lines |",
                        "|--------|---------|-------|--------|--------|",
                    ]
                    for r in prows:
                        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |")
                    lines.append("")

                # ── Top files (linked commits) ──────────────────────────────
                cur.execute(
                    """SELECT cc.file_path,
                              COUNT(DISTINCT c.commit_hash),
                              COALESCE(SUM(cc.rows_added),0),
                              COALESCE(SUM(cc.rows_removed),0)
                       FROM mem_mrr_commits c
                       JOIN mem_mrr_commits_code cc ON cc.commit_hash = c.commit_hash AND cc.project_id=%s
                       WHERE c.project_id=%s AND c.prompt_id IS NOT NULL
                       GROUP BY cc.file_path
                       ORDER BY 2 DESC, 3 DESC LIMIT 30""",
                    (project_id, project_id),
                )
                frows = cur.fetchall()
                if frows:
                    lines += [
                        "## Top Files Changed (Linked Commits)",
                        "| File | Commits | +Lines | -Lines |",
                        "|------|---------|--------|--------|",
                    ]
                    for r in frows:
                        lines.append(f"| `{r[0]}` | {r[1]} | {r[2]} | {r[3]} |")
                    lines.append("")

                # ── Standalone commits ──────────────────────────────────────
                cur.execute(
                    """SELECT c.commit_hash_short, c.commit_msg,
                              COUNT(cc.file_path),
                              COALESCE(SUM(cc.rows_added),0),
                              COALESCE(SUM(cc.rows_removed),0)
                       FROM mem_mrr_commits c
                       LEFT JOIN mem_mrr_commits_code cc ON cc.commit_hash = c.commit_hash AND cc.project_id=%s
                       WHERE c.project_id=%s AND c.prompt_id IS NULL
                       GROUP BY c.commit_hash_short, c.commit_msg, c.created_at
                       ORDER BY c.created_at DESC LIMIT 100""",
                    (project_id, project_id),
                )
                srows = cur.fetchall()
                if srows:
                    lines += [
                        "## Standalone Commits (no prompt link)",
                        "| Hash | Message | Files | +Lines | -Lines |",
                        "|------|---------|-------|--------|--------|",
                    ]
                    for r in srows:
                        msg = (r[1] or "")[:60].replace("|", "\\|")
                        lines.append(f"| `{r[0]}` | {msg} | {r[2]} | {r[3]} | {r[4]} |")
                    lines.append("")

    except Exception as e:
        log.warning(f"export_commit_analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    out_path.write_text("\n".join(lines))
    return {
        "project":   project,
        "file":      str(out_path),
        "linked_commits":     int(tot[0]),
        "standalone_commits": int(tot[1]),
        "files_touched":      int(code_tot[0]),
        "rows_added":         int(code_tot[1]),
        "rows_removed":       int(code_tot[2]),
    }


@router.delete("/{project}/backlog/{ref_id}")
async def delete_backlog_entry(project: str, ref_id: str):
    """Remove a single item line (and its sub-lines) from backlog.md.

    If the group has no remaining items after removal, the whole group chunk
    is deleted too.
    """
    from memory.memory_backlog import MemoryBacklog
    import re as _re

    bl = MemoryBacklog(project)
    path = bl._backlog_path()

    if not path.exists():
        raise HTTPException(status_code=404, detail="backlog.md not found")

    text = path.read_text(errors="ignore")
    sep_pattern = r"\n\n?---\n\n?"
    chunks = _re.split(sep_pattern, text)

    updated = False
    new_chunks: list[str] = []
    for chunk in chunks:
        if ref_id not in chunk:
            new_chunks.append(chunk)
            continue

        # Remove item line(s): the "  SRC REF_ID ..." line plus any indented
        # sub-lines (Requirements: / Deliveries:) that follow it
        lines = chunk.splitlines()
        out_lines: list[str] = []
        skip = False
        for ln in lines:
            # Detect the item header line for this ref_id
            if _re.match(rf"\s+\w+\s+{_re.escape(ref_id)}\s+", ln):
                skip = True
                updated = True
                continue
            # Stop skipping at the next item or non-indented content
            if skip:
                stripped = ln.strip()
                if stripped.startswith("Requirements:") or stripped.startswith("Deliveries:"):
                    continue  # remove sub-lines too
                skip = False
            out_lines.append(ln)

        rebuilt = "\n".join(out_lines).strip()

        # Check if any item lines remain in this chunk
        from memory.memory_backlog import _ITEM_HEADER_RE
        has_items = any(_ITEM_HEADER_RE.match(ln) for ln in rebuilt.splitlines())

        if has_items or not updated:
            new_chunks.append(rebuilt)
        # else: drop the whole empty group chunk

    if not updated:
        raise HTTPException(status_code=404, detail=f"Ref ID '{ref_id}' not found in backlog")

    path.write_text("\n\n---\n\n".join(new_chunks))
    return {"status": "deleted", "ref_id": ref_id, "project": project}


@router.post("/{project}/reset-all")
async def reset_all_backlog(project: str):
    """Full backlog reset: clears all backlog_ref markers, planner_tags, backlog links,
    and removes all use_cases/*.md except discovery.md.

    Resets the system to a clean state so a fresh sync-backlog run processes everything.
    SKIP-marked commits (system-only files) are preserved.
    """
    from core.database import db
    from memory.memory_backlog import MemoryBacklog
    from pathlib import Path

    if not db.is_available():
        raise HTTPException(503, "Database not available")

    bl = MemoryBacklog(project)
    project_id = bl._get_project_id()
    if not project_id:
        raise HTTPException(404, "Project not found")

    results: dict = {}

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # 1. Reset backlog_ref on all mirror tables (keep SKIP)
                for tbl, pk in [
                    ("mem_mrr_prompts",  "id"),
                    ("mem_mrr_commits",  "commit_hash"),
                    ("mem_mrr_messages", "id"),
                    ("mem_mrr_items",    "id"),
                ]:
                    where = (
                        "WHERE project_id=%s AND backlog_ref IS NOT NULL AND backlog_ref <> 'SKIP'"
                        if tbl == "mem_mrr_commits"
                        else "WHERE project_id=%s AND backlog_ref IS NOT NULL"
                    )
                    cur.execute(
                        f"UPDATE {tbl} SET backlog_ref = NULL {where}",
                        (project_id,),
                    )
                    results[f"reset_{tbl}"] = cur.rowcount

                # 2. Delete all planner_tags for this project (categories stay)
                cur.execute("DELETE FROM planner_tags WHERE project_id=%s", (project_id,))
                results["deleted_planner_tags"] = cur.rowcount

                # 3. Delete mem_backlog_links
                cur.execute("DELETE FROM mem_backlog_links WHERE project_id=%s", (project_id,))
                results["deleted_backlog_links"] = cur.rowcount

            conn.commit()
    except Exception as e:
        raise HTTPException(500, str(e))

    # 4. Delete use_cases/*.md except discovery.md
    uc_dir = bl._use_cases_dir()
    deleted_files: list[str] = []
    if uc_dir.exists():
        for md in uc_dir.glob("*.md"):
            if md.stem not in ("discovery", "use_case_template"):
                md.unlink()
                deleted_files.append(md.name)
    results["deleted_use_case_files"] = deleted_files

    # 5. Clear backlog.md
    bl_path = bl._backlog_path()
    if bl_path.exists():
        bl_path.write_text(
            "# Backlog\n\n"
            "> Approve entries with `[+]`, reject with `[-]`.\n"
            "> Run `POST /memory/{project}/work-items` to process approved entries.\n"
        )
        results["cleared_backlog"] = True

    results["note"] = "SKIP commits preserved; discovery.md preserved"
    return {"project": project, **results}


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


@router.post("/{project}/reset-commits")
async def reset_commits_backlog(project: str):
    """Reset backlog_ref = NULL on all commits (except SKIP).

    Use before running a fresh full-digest pass to re-process all commit data.
    SKIP-marked commits (system-only file changes) are preserved.
    """
    from core.database import db
    from memory.memory_backlog import MemoryBacklog

    if not db.is_available():
        raise HTTPException(503, "Database not available")

    bl = MemoryBacklog(project)
    project_id = bl._get_project_id()
    if not project_id:
        raise HTTPException(404, "Project not found")

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE mem_mrr_commits
                       SET backlog_ref = NULL
                       WHERE project_id = %s
                         AND backlog_ref IS NOT NULL
                         AND backlog_ref <> 'SKIP'""",
                    (project_id,),
                )
                affected = cur.rowcount
            conn.commit()
        return {"project": project, "reset": affected, "note": "SKIP rows preserved"}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/{project}/reset-billing")
async def reset_billing(project: str):
    """Delete all usage_log rows to reset billing tracking from scratch.

    Called from the data dashboard when the user wants a clean billing period.
    This deletes ALL mng_usage_logs rows (they are tracking records only,
    not financial transactions which live in mng_transactions).
    """
    from core.database import db
    from core.auth import ADMIN_USER_ID

    if not db.is_available():
        raise HTTPException(503, "Database not available")

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM mng_usage_logs WHERE user_id=%s", (ADMIN_USER_ID,))
                before = cur.fetchone()[0] or 0
                cur.execute("DELETE FROM mng_usage_logs WHERE user_id=%s", (ADMIN_USER_ID,))
                deleted = cur.rowcount
            conn.commit()
        return {
            "project": project,
            "deleted": deleted,
            "before":  before,
            "note":    "mng_usage_logs cleared — billing counter reset to zero",
        }
    except Exception as e:
        raise HTTPException(500, str(e))


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
