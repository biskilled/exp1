"""
pipeline_log.py — Lightweight async context manager for tracking background pipeline runs.

Every background task wraps its work in pipeline_run() or pipeline_run_sync() to
insert a mem_pipeline_runs row at start and update it with status/duration at finish.
This powers the GET /memory/{project}/pipeline-status dashboard.
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Generator

log = logging.getLogger(__name__)


def _insert_run(project_id: int, pipeline: str, source_id: str) -> str | None:
    """Insert a new pipeline run row and return its id. Returns None on failure."""
    try:
        from core.database import db
        if not db.is_available():
            return None
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO mem_pipeline_runs
                           (project_id, pipeline, source_id, status)
                       VALUES (%s, %s, %s, 'running')
                       RETURNING id::text""",
                    (project_id, pipeline, source_id or ""),
                )
                row = cur.fetchone()
                return row[0] if row else None
    except Exception as e:
        log.debug(f"pipeline_log._insert_run error: {e}")
        return None


def _finish_run(
    run_id: str,
    status: str,
    items_in: int,
    items_out: int,
    t0: float,
    error_msg: str = "",
) -> None:
    """Update the pipeline run row with final status and duration."""
    try:
        from core.database import db
        if not run_id or not db.is_available():
            return
        duration_ms = int((time.monotonic() - t0) * 1000)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE mem_pipeline_runs
                       SET status=%s, items_in=%s, items_out=%s,
                           duration_ms=%s, error_msg=%s, finished_at=NOW()
                       WHERE id=%s::uuid""",
                    (status, items_in, items_out, duration_ms, error_msg[:500] if error_msg else None, run_id),
                )
    except Exception as e:
        log.debug(f"pipeline_log._finish_run error: {e}")


@asynccontextmanager
async def pipeline_run(project_id: int, pipeline: str, source_id: str = ""):
    """Async context manager: wraps a background task with a DB run record.

    Usage:
        async with pipeline_run(p_id, "commit_embed", commit_hash) as ctx:
            ctx["items_in"] = 1
            await do_work()
            ctx["items_out"] = 1
    """
    t0 = time.monotonic()
    run_id = _insert_run(project_id, pipeline, source_id)
    ctx: dict = {"items_in": 0, "items_out": 0}
    try:
        yield ctx
        _finish_run(run_id, "ok", ctx["items_in"], ctx["items_out"], t0)
    except Exception as e:
        _finish_run(run_id, "error", ctx.get("items_in", 0), 0, t0, str(e))
        raise


def pipeline_run_sync(project_id: int, pipeline: str, source_id: str = "") -> tuple[str | None, float]:
    """Start a sync pipeline run record. Returns (run_id, t0) for use with _finish_run.

    Usage (sync background tasks with their own event loop):
        run_id, t0 = pipeline_run_sync(p_id, "commit_code_extract", commit_hash)
        try:
            do_sync_work()
            _finish_run(run_id, "ok", 1, 1, t0)
        except Exception as e:
            _finish_run(run_id, "error", 1, 0, t0, str(e))
    """
    t0 = time.monotonic()
    run_id = _insert_run(project_id, pipeline, source_id)
    return run_id, t0
