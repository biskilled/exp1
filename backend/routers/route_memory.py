"""
route_memory.py — Memory file generation endpoints.

Endpoints:
    POST /memory/{project}/regenerate           — regenerate context files from DB
    GET  /memory/{project}/llm-prompt           — get rendered system prompt (compact|full|gemini)
    POST /memory/{project}/prune-tags           — delete planner_tags except keep_ids list
    GET  /memory/{project}/pipeline-status      — pipeline health dashboard
    GET  /memory/{project}/data-dashboard       — aggregated statistics (uses pr_statistics cache)
"""
from __future__ import annotations

import asyncio
import json
import logging
import re

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from core.database import db

log = logging.getLogger(__name__)
router = APIRouter()

# ── SQL ────────────────────────────────────────────────────────────────────────

# ── Helpers ───────────────────────────────────────────────────────────────────

def _require_db():
    if not db.is_available():
        raise HTTPException(status_code=503, detail="Database not available")


# ── Statistics cache helpers ───────────────────────────────────────────────────

_SQL_STATS_COUNTS = """
    SELECT
      (SELECT COUNT(*) FROM mem_mrr_prompts WHERE project_id=%s) AS prompts_total,
      (SELECT COUNT(*) FROM mem_mrr_prompts WHERE project_id=%s AND backlog_ref IS NULL) AS prompts_pending,
      (SELECT COUNT(*) FROM mem_mrr_commits WHERE project_id=%s) AS commits_total,
      (SELECT COUNT(*) FROM mem_mrr_commits WHERE project_id=%s AND backlog_ref IS NULL) AS commits_pending,
      (SELECT COUNT(*) FROM planner_tags WHERE project_id=%s) AS tags_total,
      (SELECT COUNT(*) FROM planner_tags WHERE project_id=%s AND status IN ('open','active')) AS tags_active,
      (SELECT COUNT(*) FROM mem_mrr_prompts WHERE project_id=%s AND backlog_ref IS NOT NULL) AS prompts_processed,
      (SELECT COUNT(*) FROM mem_mrr_commits WHERE project_id=%s AND backlog_ref IS NOT NULL) AS commits_processed
"""

_SQL_GET_CACHED_STATS = """
    SELECT stats, updated_at FROM pr_statistics
    WHERE project_id=%s AND stat_date=CURRENT_DATE
"""

_SQL_UPSERT_STATS = """
    INSERT INTO pr_statistics (project_id, stat_date, stats)
    VALUES (%s, CURRENT_DATE, %s::jsonb)
    ON CONFLICT (project_id, stat_date)
    DO UPDATE SET stats=EXCLUDED.stats, updated_at=NOW()
"""

_SQL_RECORD_PIPELINE_RUN = """
    INSERT INTO pr_statistics (project_id, stat_date, {col})
    VALUES (%s, CURRENT_DATE, NOW())
    ON CONFLICT (project_id, stat_date)
    DO UPDATE SET {col}=NOW(), updated_at=NOW()
"""

_STAGE_COL = {"event": "last_event_run_at", "fact": "last_fact_run_at", "wi": "last_wi_run_at"}


def _get_stats(project_id: int) -> dict:
    """Read cached stats for today from pr_statistics. Returns {} on miss."""
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_CACHED_STATS, (project_id,))
                row = cur.fetchone()
        return row[0] if row else {}
    except Exception as e:
        log.debug(f"_get_stats error: {e}")
        return {}


def _refresh_stats(project_id: int) -> dict:
    """Recompute aggregated counts + KPIs and upsert into pr_statistics. Returns computed stats."""
    import datetime, json as _json
    try:
        pid = project_id
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_STATS_COUNTS, (pid,) * 8)
                r = cur.fetchone()
                if not r:
                    return {}

                # Preserve existing last_rebuild block — don't overwrite it here
                cur.execute(
                    "SELECT stats->'last_rebuild' FROM pr_statistics "
                    "WHERE project_id=%s AND stat_date=CURRENT_DATE",
                    (pid,),
                )
                existing_rb = cur.fetchone()
                last_rebuild = (existing_rb[0] if existing_rb else None) or {}

        p_total      = r[0] or 0
        p_processed  = r[6] or 0
        c_total      = r[2] or 0
        c_processed  = r[7] or 0

        # KPI: % of mirror rows processed through backlog pipeline
        prompt_backlog_pct = round(p_processed / p_total * 100, 1) if p_total else 0.0
        commit_backlog_pct = round(c_processed / c_total * 100, 1) if c_total else 0.0

        stats: dict = {
            "prompts_total":           p_total,
            "prompts_pending":         r[1] or 0,
            "prompts_processed":       p_processed,
            "commits_total":           c_total,
            "commits_pending":         r[3] or 0,
            "commits_processed":       c_processed,
            "planner_tags_total":      r[4] or 0,
            "planner_tags_active":     r[5] or 0,
            # KPIs
            "prompt_backlog_pct":      prompt_backlog_pct,
            "commit_backlog_pct":      commit_backlog_pct,
            "updated_at":              datetime.datetime.utcnow().isoformat() + "Z",
            # Preserve last_rebuild block
            "last_rebuild":            last_rebuild,
        }

        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_UPSERT_STATS, (pid, _json.dumps(stats)))
        return stats
    except Exception as e:
        log.warning(f"_refresh_stats error: {e}")
        return {}


def _record_pipeline_run(project_id: int, stage: str) -> None:
    """Record the timestamp of a completed pipeline stage in pr_statistics.

    stage: 'event' | 'fact' | 'wi'
    """
    col = _STAGE_COL.get(stage)
    if not col:
        return
    try:
        sql = _SQL_RECORD_PIPELINE_RUN.format(col=col)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (project_id,))
    except Exception as e:
        log.debug(f"_record_pipeline_run({stage}) error: {e}")


async def _call_haiku(system_prompt: str, user_message: str, max_tokens: int = 600) -> str:
    try:
        from data.dl_api_keys import get_key
        api_key = get_key("claude") or get_key("anthropic")
        if not api_key:
            return ""
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=api_key)
        resp = await client.messages.create(
            model=getattr(settings, "claude_haiku_model", "claude-haiku-4-5-20251001"),
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return resp.content[0].text if resp.content else ""
    except Exception as e:
        log.warning(f"_call_haiku error: {e}")
        return ""


def _parse_json(text: str) -> dict:
    clean = re.sub(r"```(?:json)?\s*", "", text).strip().rstrip("`")
    m = re.search(r"\{[\s\S]*\}", clean)
    if not m:
        return {}
    try:
        return json.loads(m.group())
    except Exception:
        return {}


async def _trigger_root_regen(project: str) -> None:
    """Background task: regenerate root context files."""
    try:
        from memory.memory_files import MemoryFiles
        await asyncio.get_event_loop().run_in_executor(
            None, MemoryFiles().write_root_files, project
        )
        log.debug(f"Root files regenerated for '{project}'")
    except Exception as e:
        log.debug(f"_trigger_root_regen error: {e}")


async def _trigger_feature_regen(project: str, tag_name: str) -> None:
    """Background task: regenerate a feature CLAUDE.md."""
    try:
        from memory.memory_files import MemoryFiles
        await asyncio.get_event_loop().run_in_executor(
            None, MemoryFiles().write_feature_files, project, tag_name
        )
        log.debug(f"Feature files regenerated for '{project}/{tag_name}'")
    except Exception as e:
        log.debug(f"_trigger_feature_regen error: {e}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/{project}/regenerate")
async def regenerate_memory_files(
    project: str,
    scope:    str        = Query("root", pattern="^(root|feature|all)$"),
    tag_name: str | None = Query(None),
):
    """
    Regenerate context files from DB tables.

    scope=root    → CLAUDE.md, .cursorrules, system prompts, top_events.md
    scope=feature → features/{tag_name}/CLAUDE.md  (tag_name required)
    scope=all     → root + all active feature files
    """
    from memory.memory_files import MemoryFiles
    mf = MemoryFiles()
    written: list[str] = []

    if scope == "root":
        written = await asyncio.get_event_loop().run_in_executor(
            None, mf.write_root_files, project
        )
    elif scope == "feature":
        if not tag_name:
            raise HTTPException(400, "tag_name is required for scope=feature")
        written = await asyncio.get_event_loop().run_in_executor(
            None, mf.write_feature_files, project, tag_name
        )
    elif scope == "all":
        written = await asyncio.get_event_loop().run_in_executor(
            None, mf.write_all_files, project
        )

    return {
        "status":  "ok",
        "project": project,
        "scope":   scope,
        "written": [p.split("/workspace/")[-1] if "/workspace/" in p else p for p in written],
        "count":   len(written),
    }


@router.get("/{project}/llm-prompt")
async def get_llm_prompt(
    project: str,
    variant: str = Query("compact", pattern="^(compact|full|gemini)$"),
):
    """Return a rendered LLM system prompt. Useful for copy-paste into claude.ai, ChatGPT, etc."""
    from memory.memory_files import MemoryFiles
    mf = MemoryFiles()
    ctx = mf._load_context(project)

    if variant == "compact":
        content = mf.render_system_compact(ctx)
    elif variant == "full":
        content = mf.render_system_full(ctx)
    else:
        content = mf.render_gemini_context(ctx)

    return {"variant": variant, "project": project, "content": content}


class PruneTagsBody(BaseModel):
    keep_ids: list[str]  # UUIDs to keep; all others will be deleted


@router.post("/{project}/prune-tags")
async def prune_tags(project: str, body: PruneTagsBody):
    """Delete all planner_tags for this project EXCEPT those in keep_ids.

    Use this to reset the tag taxonomy to a curated set before a full rebuild.
    Returns {deleted, kept}.
    """
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")
    if not body.keep_ids:
        raise HTTPException(status_code=400, detail="keep_ids must not be empty — pass the UUIDs to keep")

    project_id = db.get_or_create_project_id(project)
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Count total before deletion
                cur.execute("SELECT COUNT(*) FROM planner_tags WHERE project_id=%s", (project_id,))
                total_before = cur.fetchone()[0] or 0

                # Delete all except keep_ids
                import psycopg2.extras
                cur.execute(
                    "DELETE FROM planner_tags WHERE project_id=%s AND id != ALL(%s::uuid[])",
                    (project_id, body.keep_ids),
                )
                deleted = cur.rowcount
        kept = total_before - deleted
        log.info(f"prune_tags: deleted={deleted} kept={kept} for '{project}'")
        return {"project": project, "deleted": deleted, "kept": kept}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project}/pipeline-status")
async def get_pipeline_status(project: str):
    """Return pipeline health dashboard: last-24h stats per pipeline, pending counts, recent errors."""
    if not db.is_available():
        return {"last_24h": {}, "pending": {}, "recent_errors": []}

    project_id = db.get_or_create_project_id(project)

    pipelines = ["commit_embed", "commit_store", "commit_code_extract",
                 "session_summary", "tag_match", "work_item_embed", "work_item_promote"]
    last_24h: dict = {}

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Per-pipeline counts in last 24h
                cur.execute(
                    """SELECT pipeline, status, COUNT(*) AS cnt,
                              MAX(started_at) AS last_run
                       FROM mem_pipeline_runs
                       WHERE project_id = %s
                         AND started_at > NOW() - INTERVAL '24 hours'
                       GROUP BY pipeline, status""",
                    (project_id,),
                )
                rows = cur.fetchall()
                # Aggregate
                agg: dict = {}
                for pl, st, cnt, last_run in rows:
                    if pl not in agg:
                        agg[pl] = {"ok": 0, "error": 0, "skipped": 0, "last_run": None}
                    key = st if st in ("ok", "error", "skipped") else "error"
                    agg[pl][key] += cnt
                    if last_run:
                        existing = agg[pl]["last_run"]
                        if not existing or last_run.isoformat() > existing:
                            agg[pl]["last_run"] = last_run.isoformat()

                for pl in pipelines:
                    last_24h[pl] = agg.get(pl, {"ok": 0, "error": 0, "skipped": 0, "last_run": None})

                # Pending commits (not yet processed into backlog)
                cur.execute(
                    "SELECT COUNT(*) FROM mem_mrr_commits WHERE project_id=%s AND backlog_ref IS NULL",
                    (project_id,),
                )
                commits_not_embedded = cur.fetchone()[0] or 0

                # Pending prompts (not yet processed into backlog)
                cur.execute(
                    "SELECT COUNT(*) FROM mem_mrr_prompts WHERE project_id=%s AND backlog_ref IS NULL",
                    (project_id,),
                )
                work_items_unmatched = cur.fetchone()[0] or 0  # reuse field name for compat

                # Recent errors (last 10)
                cur.execute(
                    """SELECT pipeline, source_id, error_msg, started_at
                       FROM mem_pipeline_runs
                       WHERE project_id=%s AND status='error'
                       ORDER BY started_at DESC LIMIT 10""",
                    (project_id,),
                )
                recent_errors = [
                    {
                        "pipeline": r[0],
                        "source_id": r[1] or "",
                        "error_msg": r[2] or "",
                        "at": r[3].isoformat() if r[3] else None,
                    }
                    for r in cur.fetchall()
                ]

    except Exception as e:
        log.warning(f"get_pipeline_status error: {e}")
        return {"last_24h": {pl: {"ok": 0, "error": 0, "skipped": 0, "last_run": None} for pl in pipelines},
                "pending": {}, "recent_errors": []}

    return {
        "last_24h": last_24h,
        "pending": {
            "commits_not_embedded": commits_not_embedded,
            "work_items_unmatched": work_items_unmatched,
        },
        "recent_errors": recent_errors,
    }


@router.get("/{project}/data-dashboard")
async def get_data_dashboard(
    project: str,
    use_cache: bool = Query(False, description="Return cached stats if refreshed within 30 min"),
):
    """Data Dashboard: mirror layer counts, AI layer counts, pipeline health, pending.

    Pass ?use_cache=true to serve today's pr_statistics row when it was computed
    within the last 30 minutes instead of recomputing all counts from scratch.
    """
    if not db.is_available():
        return {"mirror": {}, "ai": {}, "pipeline": {}, "pending": {}, "recent_errors": [], "fallback": True}

    project_id = db.get_or_create_project_id(project)

    # ── Fast path: return cached stats if fresh enough ────────────────────────
    if use_cache:
        try:
            import datetime
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT stats, updated_at FROM pr_statistics "
                        "WHERE project_id=%s AND stat_date=CURRENT_DATE",
                        (project_id,),
                    )
                    row = cur.fetchone()
            if row and row[0] and row[1]:
                age = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc) - row[1].replace(tzinfo=datetime.timezone.utc)
                if age.total_seconds() < 1800:  # 30 minutes
                    s = row[0]
                    cached_kpis = {
                        "prompt_backlog_pct": s.get("prompt_backlog_pct"),
                        "commit_backlog_pct": s.get("commit_backlog_pct"),
                    }
                    cached_rebuild = s.get("last_rebuild", {})
                    return {"cached": True, "project": project, **s,
                            "kpis": cached_kpis, "rebuild_history": cached_rebuild}
        except Exception as _e:
            log.debug(f"data-dashboard cache lookup error: {_e}")
    mirror: dict = {}
    ai: dict = {}
    pipeline: dict = {}
    pending: dict = {}
    health: dict = {}
    recent_errors: list = []

    try:
        with db.conn() as conn:
            with conn.cursor() as cur:

                # ── Mirror layer ──────────────────────────────────────────
                for table, key in [
                    ("mem_mrr_commits",  "commits"),
                    ("mem_mrr_prompts",  "prompts"),
                    ("mem_mrr_items",    "items"),
                    ("mem_mrr_messages", "messages"),
                ]:
                    try:
                        cur.execute(
                            f"""SELECT COUNT(*),
                                       COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours'),
                                       MAX(created_at)
                                FROM {table} WHERE project_id = %s""",
                            (project_id,),
                        )
                        r = cur.fetchone()
                        mirror[key] = {
                            "total": r[0] or 0,
                            "last_24h": r[1] or 0,
                            "last_at": r[2].isoformat() if r[2] else None,
                        }
                    except Exception:
                        conn.rollback()
                        mirror[key] = {"total": 0, "last_24h": 0, "last_at": None}

                # Commits: pending backlog processing
                try:
                    cur.execute(
                        "SELECT COUNT(*) FROM mem_mrr_commits WHERE project_id=%s AND backlog_ref IS NULL",
                        (project_id,),
                    )
                    mirror["commits"]["pending_backlog"] = cur.fetchone()[0] or 0
                except Exception:
                    conn.rollback()
                    mirror["commits"]["pending_backlog"] = 0

                # Prompts: pending backlog processing
                try:
                    cur.execute(
                        "SELECT COUNT(*) FROM mem_mrr_prompts WHERE project_id=%s AND backlog_ref IS NULL",
                        (project_id,),
                    )
                    mirror["prompts"]["pending_backlog"] = cur.fetchone()[0] or 0
                except Exception:
                    conn.rollback()
                    mirror["prompts"]["pending_backlog"] = 0

                # ── AI layer ──────────────────────────────────────────────
                # Planner tags
                try:
                    cur.execute(
                        """SELECT COUNT(*),
                                  COUNT(*) FILTER (WHERE status IN ('open','active')),
                                  COUNT(*) FILTER (WHERE status = 'done'),
                                  COUNT(*) FILTER (WHERE updated_at > NOW() - INTERVAL '24 hours'),
                                  MAX(updated_at)
                           FROM planner_tags WHERE project_id = %s""",
                        (project_id,),
                    )
                    r = cur.fetchone()
                    ai["planner_tags"] = {
                        "total":      r[0] or 0,
                        "active":     r[1] or 0,
                        "done":       r[2] or 0,
                        "last_24h":   r[3] or 0,
                        "last_at":    r[4].isoformat() if r[4] else None,
                    }
                except Exception:
                    conn.rollback()
                    ai["planner_tags"] = {"total": 0, "active": 0, "done": 0, "last_24h": 0, "last_at": None}

                # Backlog stats
                try:
                    cur.execute(
                        """SELECT
                             COUNT(*) FILTER (WHERE backlog_ref IS NULL) AS prompts_pending,
                             COUNT(*) FILTER (WHERE backlog_ref IS NOT NULL) AS prompts_processed
                           FROM mem_mrr_prompts WHERE project_id = %s""",
                        (project_id,),
                    )
                    r = cur.fetchone()
                    ai["backlog"] = {
                        "prompts_pending":   r[0] or 0,
                        "prompts_processed": r[1] or 0,
                    }
                    cur.execute(
                        """SELECT
                             COUNT(*) FILTER (WHERE backlog_ref IS NULL) AS commits_pending,
                             COUNT(*) FILTER (WHERE backlog_ref IS NOT NULL) AS commits_processed
                           FROM mem_mrr_commits WHERE project_id = %s""",
                        (project_id,),
                    )
                    r = cur.fetchone()
                    ai["backlog"]["commits_pending"]   = r[0] or 0
                    ai["backlog"]["commits_processed"] = r[1] or 0
                except Exception:
                    conn.rollback()
                    ai["backlog"] = {"prompts_pending": 0, "prompts_processed": 0,
                                     "commits_pending": 0, "commits_processed": 0}

                # Feature snapshots (planner_tags with AI content)
                try:
                    cur.execute(
                        """SELECT COUNT(*),
                                  COUNT(*) FILTER (WHERE updated_at > NOW() - INTERVAL '24 hours'),
                                  MAX(updated_at)
                           FROM planner_tags
                           WHERE project_id = %s
                             AND (description IS NOT NULL OR acceptance_criteria IS NOT NULL)""",
                        (project_id,),
                    )
                    r = cur.fetchone()
                    ai["feature_snapshots"] = {
                        "total": r[0] or 0,
                        "last_24h": r[1] or 0,
                        "last_at": r[2].isoformat() if r[2] else None,
                    }
                except Exception:
                    conn.rollback()
                    ai["feature_snapshots"] = {"total": 0, "last_24h": 0, "last_at": None}

                # ── Pipeline runs (last 24h) ───────────────────────────────
                pl_keys = ["commit_embed", "commit_store", "commit_code_extract",
                           "session_summary", "tag_match", "work_item_embed",
                           "work_item_promote"]
                try:
                    cur.execute(
                        """SELECT pipeline, status, COUNT(*), MAX(started_at)
                           FROM mem_pipeline_runs
                           WHERE project_id = %s AND started_at > NOW() - INTERVAL '24 hours'
                           GROUP BY pipeline, status""",
                        (project_id,),
                    )
                    agg: dict = {}
                    for pl, st, cnt, last_run in cur.fetchall():
                        if pl not in agg:
                            agg[pl] = {"ok": 0, "error": 0, "skipped": 0, "last_run": None}
                        key = st if st in ("ok", "error", "skipped") else "error"
                        agg[pl][key] += cnt
                        if last_run:
                            ex = agg[pl]["last_run"]
                            if not ex or last_run.isoformat() > ex:
                                agg[pl]["last_run"] = last_run.isoformat()
                    for pl in pl_keys:
                        pipeline[pl] = agg.get(pl, {"ok": 0, "error": 0, "skipped": 0, "last_run": None})
                except Exception:
                    conn.rollback()
                    for pl in pl_keys:
                        pipeline[pl] = {"ok": 0, "error": 0, "skipped": 0, "last_run": None}

                # ── Pending ───────────────────────────────────────────────
                try:
                    cur.execute(
                        "SELECT COUNT(*) FROM mem_mrr_commits WHERE project_id=%s AND backlog_ref IS NULL",
                        (project_id,),
                    )
                    pending["commits_pending_backlog"] = cur.fetchone()[0] or 0
                except Exception:
                    conn.rollback()
                    pending["commits_pending_backlog"] = 0

                try:
                    cur.execute(
                        "SELECT COUNT(*) FROM mem_mrr_prompts WHERE project_id=%s AND backlog_ref IS NULL",
                        (project_id,),
                    )
                    pending["prompts_pending_backlog"] = cur.fetchone()[0] or 0
                except Exception:
                    conn.rollback()
                    pending["prompts_pending_backlog"] = 0

                # ── Health KPIs ───────────────────────────────────────────
                health: dict = {}
                try:
                    # Total active planner tags
                    cur.execute(
                        "SELECT COUNT(*) FROM planner_tags WHERE project_id=%s AND status NOT IN ('archived','done')",
                        (project_id,),
                    )
                    total_tags = cur.fetchone()[0] or 0

                    # Tags with file_ref (linked to use case files)
                    cur.execute(
                        "SELECT COUNT(*) FROM planner_tags WHERE project_id=%s AND file_ref IS NOT NULL",
                        (project_id,),
                    )
                    tags_with_use_case = cur.fetchone()[0] or 0

                    # Backlog coverage
                    _bl = ai.get("backlog", {})
                    total_p = (_bl.get("prompts_pending", 0) + _bl.get("prompts_processed", 0))
                    total_c = (_bl.get("commits_pending", 0) + _bl.get("commits_processed", 0))
                    prompt_coverage = round(_bl.get("prompts_processed", 0) / max(total_p, 1) * 100, 1)
                    commit_coverage = round(_bl.get("commits_processed", 0) / max(total_c, 1) * 100, 1)

                    health = {
                        "total_planner_tags":    total_tags,
                        "tags_with_use_case":    tags_with_use_case,
                        "use_case_coverage_pct": round(tags_with_use_case / max(total_tags, 1) * 100, 1),
                        "prompt_backlog_pct":    prompt_coverage,
                        "commit_backlog_pct":    commit_coverage,
                    }
                except Exception:
                    conn.rollback()
                    health = {
                        "total_planner_tags": 0, "tags_with_use_case": 0,
                        "use_case_coverage_pct": 0, "prompt_backlog_pct": 0,
                        "commit_backlog_pct": 0,
                    }

                # ── Recent errors ─────────────────────────────────────────
                try:
                    cur.execute(
                        """SELECT pipeline, source_id, error_msg, started_at
                           FROM mem_pipeline_runs
                           WHERE project_id=%s AND status='error'
                           ORDER BY started_at DESC LIMIT 5""",
                        (project_id,),
                    )
                    recent_errors = [
                        {"pipeline": r[0], "source_id": r[1] or "",
                         "error_msg": r[2] or "", "at": r[3].isoformat() if r[3] else None}
                        for r in cur.fetchall()
                    ]
                except Exception:
                    conn.rollback()

    except Exception as e:
        log.warning(f"get_data_dashboard error: {e}")
        return {"mirror": mirror, "ai": ai, "pipeline": pipeline,
                "pending": pending, "health": health, "recent_errors": recent_errors, "error": str(e)}

    # ── KPIs + rebuild history from pr_statistics ─────────────────────────────
    kpis: dict = {}
    rebuild_history: dict = {}
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT stats FROM pr_statistics "
                    "WHERE project_id=%s ORDER BY stat_date DESC LIMIT 1",
                    (project_id,),
                )
                row = cur.fetchone()
        if row and row[0]:
            s = row[0]
            kpis = {
                "prompt_backlog_pct": s.get("prompt_backlog_pct"),
                "commit_backlog_pct": s.get("commit_backlog_pct"),
            }
            rebuild_history = s.get("last_rebuild") or {}
    except Exception:
        pass

    # Recompute KPIs inline if not cached yet
    if not kpis.get("prompt_backlog_pct") and kpis.get("prompt_backlog_pct") != 0:
        try:
            s = _refresh_stats(project_id)
            kpis = {
                "prompt_backlog_pct": s.get("prompt_backlog_pct", 0),
                "commit_backlog_pct": s.get("commit_backlog_pct", 0),
            }
            rebuild_history = s.get("last_rebuild") or {}
        except Exception:
            pass

    return {
        "mirror":          mirror,
        "ai":              ai,
        "pipeline":        pipeline,
        "pending":         pending,
        "recent_errors":   recent_errors,
        "health":          health,
        "kpis":            kpis,
        "rebuild_history": rebuild_history,
    }


@router.get("/{project}/llm-costs")
async def llm_costs(project: str):
    """Return LLM cost breakdown for memory pipeline calls (last 24h + all time).

    Queries mng_usage_logs WHERE source='memory', grouped by provider and model.
    Does NOT filter by project — pipeline costs are system-wide.
    """
    if not db.is_available():
        return {"last_24h": {"total_calls": 0, "total_cost_usd": 0, "by_model": []},
                "all_time":  {"total_calls": 0, "total_cost_usd": 0, "by_model": []}}
    try:
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        provider, model,
                        COUNT(*) AS calls,
                        SUM(cost_usd) AS cost_usd,
                        SUM(input_tokens) AS input_tokens,
                        SUM(output_tokens) AS output_tokens,
                        (created_at > NOW() - INTERVAL '24 hours') AS is_24h
                    FROM mng_usage_logs
                    WHERE source = 'memory'
                    GROUP BY provider, model, (created_at > NOW() - INTERVAL '24 hours')
                    ORDER BY cost_usd DESC
                """)
                rows = cur.fetchall()

        def _build(is_24h_flag: bool) -> dict:
            models = [
                {
                    "provider": r[0], "model": r[1],
                    "calls": r[2], "cost_usd": float(r[3] or 0),
                    "input_tokens": r[4] or 0, "output_tokens": r[5] or 0,
                }
                for r in rows if r[6] == is_24h_flag
            ]
            return {
                "total_calls":    sum(m["calls"] for m in models),
                "total_cost_usd": round(sum(m["cost_usd"] for m in models), 6),
                "by_model":       models,
            }

        return {"last_24h": _build(True), "all_time": _build(False), "project": project}
    except Exception as e:
        log.warning(f"llm_costs error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project}/workflow-templates")
async def get_workflow_templates(project: str):
    """Return delivery-type → workflow mapping + available workflows for this project."""
    from pathlib import Path
    import yaml as _yaml

    templates_path = Path(__file__).parent.parent.parent / "workspace" / "_templates" / "workflows" / "templates.yaml"
    templates: dict = {}
    if templates_path.exists():
        try:
            data = _yaml.safe_load(templates_path.read_text()) or {}
            templates = data.get("templates", {})
        except Exception:
            pass

    workflows: list = []
    if db.is_available():
        project_id = db.get_or_create_project_id(project)
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT w.id::text, w.name,
                                  COUNT(n.id) AS node_count
                           FROM pr_graph_workflows w
                           LEFT JOIN pr_graph_nodes n ON n.workflow_id = w.id
                           WHERE w.project_id = %s
                           GROUP BY w.id, w.name
                           ORDER BY w.name""",
                        (project_id,),
                    )
                    for r in cur.fetchall():
                        workflows.append({"id": r[0], "name": r[1], "node_count": r[2] or 0})
        except Exception as e:
            log.debug(f"get_workflow_templates workflows query error: {e}")

    return {"templates": templates, "workflows": workflows}
