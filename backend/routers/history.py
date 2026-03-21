"""
History router — reads the unified workspace/{project}/history/history.jsonl

All sources write to the same file:
  - "ui"         : chat.py UI exchanges (full prompt + response)
  - "claude_cli" : Claude Code UserPromptSubmit hook (prompt only, no response)
  - "workflow"   : workflow runner steps

Legacy sources still merged for backward compat:
  - {engine_root}/.aicli/prompt_log.jsonl (older hook format)
"""

import json
import csv
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from core.auth import get_optional_user
from data.database import db

router = APIRouter()

# Engine root: .../aicli/ui/backend/routers/history.py → four parents up
_ENGINE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Noise patterns — entries whose user_input contains these are internal tool noise
_NOISE_PATTERNS = ["<task-notification>", "<tool-use-id>", "<task-id>", "<parameter>"]

def _is_noisy(e: dict) -> bool:
    """True only when the entry IS a system noise message (starts with an XML tag).

    Uses startswith, not 'in', so user messages that DISCUSS these tags are kept.
    """
    txt = (e.get("user_input") or "").strip()
    return any(txt.startswith(p) for p in _NOISE_PATTERNS)


def _project_dir(project: str | None = None) -> Path:
    p = project or settings.active_project or "default"
    return Path(settings.workspace_dir) / p


def _load_unified_history(project: str | None, provider: str | None = None) -> list[dict]:
    """Read workspace/{project}/_system/history.jsonl + all archived history_*.jsonl files."""
    sys_dir = _project_dir(project) / "_system"

    # Collect all history files: current + archives (history_YYMMDDHHSS.jsonl)
    files: list[Path] = []
    main = sys_dir / "history.jsonl"
    if main.exists():
        files.append(main)
    for arch in sorted(sys_dir.glob("history_*.jsonl")):
        files.append(arch)

    entries = []
    for hist_file in files:
        try:
            with open(hist_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        if provider and e.get("provider") != provider:
                            continue
                        entries.append(e)
                    except json.JSONDecodeError:
                        pass
        except OSError:
            pass
    return entries


def _load_prompt_log_legacy() -> list[dict]:
    """Read legacy .aicli/prompt_log.jsonl — entries not already in unified history."""
    path = _ENGINE_ROOT / ".aicli" / "prompt_log.jsonl"
    if not path.exists():
        return []
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                entries.append({
                    "ts": raw.get("ts", ""),
                    "source": "claude_cli",
                    "session_id": raw.get("session", raw.get("session_id", "")),
                    "provider": raw.get("provider", "claude"),
                    "user_input": raw.get("user_input", raw.get("prompt", "")),
                    "output": raw.get("output_preview", ""),
                    "feature": raw.get("feature"),
                    "tags": [],
                    "user": None,
                })
            except json.JSONDecodeError:
                pass
    return entries


@router.get("/chat")
async def chat_history(
    project: str | None = Query(None),
    provider: str | None = Query(None),
    limit: int = Query(500),    # default 500 newest; 0 = all
    offset: int = Query(0),     # for pagination: skip first N entries
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Return unified project history — all sources, all users.

    Noise entries (user_input containing <task-notification>, <tool-use-id>, etc.)
    are filtered out before returning.
    Returns newest-first. limit+offset allow server-side pagination.
    """
    entries = _load_unified_history(project, provider)

    # Also merge legacy prompt_log.jsonl entries not yet in unified file
    if provider is None or provider == "claude":
        legacy = _load_prompt_log_legacy()
        entries.extend(legacy)

    # Deduplicate by (ts, user_input[:80])
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for e in entries:
        key = (e.get("ts", ""), e.get("user_input", "")[:80])
        if key not in seen:
            seen.add(key)
            deduped.append(e)

    total_raw = len(deduped)

    # Filter out internal noise entries
    deduped = [e for e in deduped if not _is_noisy(e)]

    deduped.sort(key=lambda x: x.get("ts", ""), reverse=True)
    total = len(deduped)
    filtered = total_raw - total

    # Apply server-side pagination
    page_entries = deduped[offset:offset + limit] if limit > 0 else deduped[offset:]
    return {
        "entries": page_entries,
        "total": total,
        "filtered": filtered,
        "offset": offset,
        "limit": limit,
        "has_more": (offset + len(page_entries)) < total,
    }


class CommitPatch(BaseModel):
    phase:   str | None = None
    feature: str | None = None
    bug_ref: str | None = None
    summary: str | None = None
    tags:    dict | None = None


@router.get("/commits")
async def commits_history(
    project: str | None = Query(None),
    limit: int = Query(100),
):
    """List commits for a project.

    If PostgreSQL is available, returns enriched rows from the `commits` table.
    Falls back to commit_log.jsonl → marks every row as untagged.
    """
    p = project or settings.active_project or "default"

    if db.is_available():
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, commit_hash, commit_msg, summary, phase,
                           feature, bug_ref, source, session_id, prompt_source_id,
                           tags, committed_at
                    FROM pr_commits
                    WHERE client_id=1 AND project=%s
                    ORDER BY committed_at DESC NULLS LAST, id DESC
                    LIMIT %s
                """, (p, limit))
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
                # Normalise types for JSON
                for r in rows:
                    if r.get("committed_at"):
                        r["committed_at"] = r["committed_at"].isoformat()
                return {"commits": rows, "project": p, "source": "db"}

    # Fallback: read commit_log.jsonl — no tag enrichment
    log_path = _project_dir(project) / "_system" / "commit_log.jsonl"
    if not log_path.exists():
        return {"commits": [], "project": p, "source": "file"}

    commits: list[dict] = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                commits.append({
                    "id": None,
                    "commit_hash": raw.get("hash", ""),
                    "commit_msg": raw.get("message", raw.get("msg", "")),
                    "summary": "",
                    "phase": None,
                    "feature": None,
                    "bug_ref": None,
                    "source": raw.get("source", "git"),
                    "session_id": raw.get("session_id"),
                    "tags": {},
                    "committed_at": raw.get("ts"),
                })
            except json.JSONDecodeError:
                pass

    commits.reverse()
    return {"commits": commits[:limit], "project": p, "source": "file"}


@router.patch("/commits/{commit_id}")
async def patch_commit(commit_id: int, body: CommitPatch, project: str | None = Query(None)):
    """Update metadata (phase, feature, bug_ref, summary, tags) for a commit row."""
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")
    p = project or settings.active_project or "default"

    updates: list[str] = []
    params: list = []

    if body.phase is not None:
        updates.append("phase = %s")
        params.append(body.phase or None)
    if body.feature is not None:
        updates.append("feature = %s")
        params.append(body.feature or None)
    if body.bug_ref is not None:
        updates.append("bug_ref = %s")
        params.append(body.bug_ref or None)
    if body.summary is not None:
        updates.append("summary = %s")
        params.append(body.summary)
    if body.tags is not None:
        updates.append("tags = %s")
        import json as _json
        params.append(_json.dumps(body.tags))

    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(commit_id)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE pr_commits SET {', '.join(updates)} WHERE id = %s AND client_id=1 RETURNING id",
                params,
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Commit not found")

    return {"ok": True, "id": commit_id}


@router.post("/commits/sync")
async def sync_commits(project: str | None = Query(None)):
    """Import commit_log.jsonl → commits table. Idempotent (UPSERT on commit_hash)."""
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

    p = project or settings.active_project or "default"
    log_path = _project_dir(project) / "_system" / "commit_log.jsonl"
    if not log_path.exists():
        return {"imported": 0, "project": p}

    inserted = 0
    with db.conn() as conn:
        with conn.cursor() as cur:
            with open(log_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        raw = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    commit_hash = raw.get("hash") or raw.get("commit_hash")
                    if not commit_hash:
                        continue

                    cur.execute("""
                        INSERT INTO pr_commits
                            (client_id, project, commit_hash, commit_msg, source, session_id, committed_at)
                        VALUES (1, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (commit_hash) DO UPDATE SET
                            session_id = CASE
                                WHEN EXCLUDED.session_id IS NOT NULL AND EXCLUDED.session_id != ''
                                THEN EXCLUDED.session_id
                                ELSE pr_commits.session_id
                            END
                    """, (
                        p,
                        commit_hash,
                        raw.get("message", raw.get("msg", "")),
                        raw.get("source", "git"),
                        raw.get("session_id"),
                        raw.get("ts"),
                    ))
                    inserted += cur.rowcount

    return {"imported": inserted, "project": p}


@router.post("/clean-noise")
async def clean_noise(project: str | None = Query(None)):
    """Remove <task-notification>/<tool-use-id> noise entries from history.jsonl.

    Safe to call repeatedly — idempotent. Also cleans history_*.jsonl archives.
    Returns counts of removed entries per file.
    """
    p     = project or settings.active_project or "default"
    sys_d = _project_dir(p) / "_system"
    result: dict = {}

    for hist in sorted(sys_d.glob("history*.jsonl")):
        lines = [l for l in hist.read_text().splitlines() if l.strip()]
        clean: list[str] = []
        removed = 0
        for line in lines:
            try:
                e   = json.loads(line)
                txt = e.get("user_input") or ""
                if _is_noisy(e) or not txt.strip():
                    removed += 1
                    continue
            except json.JSONDecodeError:
                pass
            clean.append(line)
        if removed:
            hist.write_text("\n".join(clean) + "\n")
        result[hist.name] = {"total": len(lines), "removed": removed, "kept": len(clean)}

    return {"cleaned": result, "project": p}


@router.get("/session-tags")
async def get_session_tags(project: str | None = Query(None)):
    """Get current active session tags for a project."""
    p = project or settings.active_project or "default"
    if db.is_available():
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT phase, feature, bug_ref, extra FROM mng_session_tags WHERE client_id=1 AND project=%s",
                    (p,),
                )
                row = cur.fetchone()
                if row:
                    return {"project": p, "phase": row[0], "feature": row[1],
                            "bug_ref": row[2], "extra": row[3] or {}}
    # Fallback: session_tags.json
    tags_path = _project_dir(project) / "_system" / "session_tags.json"
    if tags_path.exists():
        try:
            return {"project": p, **json.loads(tags_path.read_text())}
        except Exception:
            pass
    return {"project": p, "phase": None, "feature": None, "bug_ref": None, "extra": {}}


class SessionTagsUpdate(BaseModel):
    phase:   str | None = None
    feature: str | None = None
    bug_ref: str | None = None
    extra:   dict | None = None


@router.put("/session-tags")
async def put_session_tags(body: SessionTagsUpdate, project: str | None = Query(None)):
    """Set active session tags for a project (upsert)."""
    p = project or settings.active_project or "default"
    import json as _json

    tags = {
        "phase":   body.phase,
        "feature": body.feature,
        "bug_ref": body.bug_ref,
        "extra":   body.extra or {},
    }

    # Always write JSON file as fallback (used by Claude CLI hook)
    tags_path = _project_dir(project) / "_system" / "session_tags.json"
    tags_path.parent.mkdir(parents=True, exist_ok=True)
    tags_path.write_text(_json.dumps(tags, indent=2))

    if db.is_available():
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO mng_session_tags (client_id, project, phase, feature, bug_ref, extra, updated_at)
                    VALUES (1, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (client_id, project) DO UPDATE SET
                        phase = EXCLUDED.phase,
                        feature = EXCLUDED.feature,
                        bug_ref = EXCLUDED.bug_ref,
                        extra = EXCLUDED.extra,
                        updated_at = NOW()
                """, (p, body.phase, body.feature, body.bug_ref,
                      _json.dumps(body.extra or {})))

    return {"ok": True, **tags}


@router.get("/session-phases")
async def get_session_phases(project: str | None = Query(None)):
    """Return per-session phase overrides stored in session_phases.json.
    Used to persist phase for CLI / workflow sessions that have no JSON session file.
    """
    p = project or settings.active_project or "default"
    phases_path = _project_dir(p) / "_system" / "session_phases.json"
    if phases_path.exists():
        try:
            return json.loads(phases_path.read_text())
        except Exception:
            pass
    return {}


@router.get("/runs")
async def workflow_runs(
    project: str | None = Query(None),
    workflow: str | None = Query(None),
    limit: int = Query(50),
):
    """List workflow run logs — queries DB first (LangGraph runs), falls back to file system."""
    # Try DB first (LangGraph runs in pr_graph_runs)
    if db.is_available() and project:
        try:
            with db.conn() as conn:
                with conn.cursor() as cur:
                    if workflow:
                        cur.execute(
                            """SELECT r.id, r.status, r.user_input, r.started_at, r.finished_at,
                                      r.total_cost_usd, r.error, r.current_node, r.context,
                                      w.name AS workflow_name
                               FROM pr_graph_runs r
                               LEFT JOIN pr_graph_workflows w ON w.id = r.workflow_id
                               WHERE r.client_id=1 AND r.project=%s AND w.name=%s
                               ORDER BY r.started_at DESC LIMIT %s""",
                            (project, workflow, min(limit, 200)),
                        )
                    else:
                        cur.execute(
                            """SELECT r.id, r.status, r.user_input, r.started_at, r.finished_at,
                                      r.total_cost_usd, r.error, r.current_node, r.context,
                                      w.name AS workflow_name
                               FROM pr_graph_runs r
                               LEFT JOIN pr_graph_workflows w ON w.id = r.workflow_id
                               WHERE r.client_id=1 AND r.project=%s
                               ORDER BY r.started_at DESC LIMIT %s""",
                            (project, min(limit, 200)),
                        )
                    rows = cur.fetchall()

                    # Count node results per run
                    run_ids = [str(r[0]) for r in rows]
                    step_counts: dict = {}
                    if run_ids:
                        placeholders = ",".join(["%s"] * len(run_ids))
                        cur.execute(
                            f"SELECT run_id, COUNT(*) FROM pr_graph_node_results WHERE run_id IN ({placeholders}) GROUP BY run_id",
                            run_ids,
                        )
                        for sc_row in cur.fetchall():
                            step_counts[str(sc_row[0])] = sc_row[1]

            runs = []
            for r in rows:
                started = r[3]
                finished = r[4]
                duration_secs = 0
                if started and finished:
                    duration_secs = round((finished - started).total_seconds(), 1)
                wf_name = r[9] or "Unknown"
                if wf_name == "_work_item_pipeline":
                    wf_name = "Work Item Pipeline"
                runs.append({
                    "id": str(r[0]),
                    "file": str(r[0]),  # legacy field used by _showRunDetail click
                    "workflow": wf_name,
                    "status": r[1],
                    "user_input": (r[2] or "")[:120],
                    "started_at": started.isoformat() if started else None,
                    "finished_at": finished.isoformat() if finished else None,
                    "total_cost_usd": float(r[5] or 0),
                    "duration_secs": duration_secs,
                    "steps": step_counts.get(str(r[0]), 0),
                    "error": r[6],
                    "current_node": r[7],
                })
            return {"runs": runs}
        except Exception as _dbe:
            import logging
            logging.getLogger(__name__).warning(f"DB run query failed, falling back to files: {_dbe}")

    # Fallback: file-based run logs
    runs_dir = _project_dir(project) / "runs"
    if not runs_dir.exists():
        return {"runs": []}

    pattern = f"*_{workflow}.json" if workflow else "*.json"
    runs = []
    for path in sorted(runs_dir.glob(pattern), reverse=True)[:limit]:
        try:
            data = json.loads(path.read_text())
            runs.append({
                "file": path.name,
                "workflow": data.get("workflow"),
                "started_at": data.get("started_at"),
                "total_cost_usd": data.get("total_cost_usd"),
                "duration_secs": data.get("duration_secs"),
                "steps": len(data.get("steps", [])),
            })
        except Exception:
            pass

    return {"runs": runs}


@router.get("/runs/{filename}")
async def get_run_detail(filename: str, project: str | None = Query(None)):
    """Get full run log detail."""
    path = _project_dir(project) / "runs" / filename

    if not path.exists():
        raise HTTPException(status_code=404, detail="Run log not found")

    return json.loads(path.read_text())


@router.get("/evals")
async def prompt_evals(project: str | None = Query(None)):
    """Read prompt_evals.jsonl for a project."""
    evals_path = _project_dir(project) / "prompt_evals.jsonl"

    if not evals_path.exists():
        return {"evals": []}

    evals = []
    with open(evals_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    evals.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    return {"evals": list(reversed(evals))}


@router.get("/session-commits")
async def session_commits(
    session_id: str,
    project: str | None = Query(None),
):
    """Return commits associated with a session (UI or Claude CLI).

    For UI chat sessions (sessions/{id}.json exists):
      Matches commits by time window (created_at … updated_at) OR session_id column.

    For Claude CLI sessions (hooks write session_id to commit_log.jsonl):
      Matches commits by session_id column / JSONL field only.

    No hook changes needed — auto_commit_push.sh already stores session_id.
    """
    import yaml as _yaml

    p = project or settings.active_project or "default"

    # ── Try to resolve timestamps from a UI session file ─────────────────────
    sessions_dir = Path(settings.workspace_dir) / p / "_system" / "sessions"
    session_file = sessions_dir / f"{session_id}.json"
    created_at = updated_at = ""
    if session_file.exists():
        try:
            sess = json.loads(session_file.read_text())
            created_at = sess.get("created_at", "")
            updated_at = sess.get("updated_at", created_at)
        except Exception:
            pass
    # If no session file (Claude CLI session) — session_id match still works below

    # ── Get github_repo from project.yaml ──────────────────────────────────────
    github_repo = ""
    proj_yaml = Path(settings.workspace_dir) / p / "project.yaml"
    if proj_yaml.exists():
        try:
            cfg = _yaml.safe_load(proj_yaml.read_text()) or {}
            github_repo = cfg.get("github_repo", "")
        except Exception:
            pass

    # Normalise github_repo to base HTTPS URL (strip .git, git@ etc.)
    if github_repo:
        import re as _re
        # git@github.com:user/repo → https://github.com/user/repo
        github_repo = _re.sub(r'^git@([^:]+):', r'https://\1/', github_repo)
        github_repo = github_repo.rstrip("/").removesuffix(".git")

    # ── Query commits ──────────────────────────────────────────────────────────
    commits: list[dict] = []

    if db.is_available():
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Build query: always match by session_id; add time window if available
                if created_at and updated_at:
                    cur.execute(
                        """SELECT commit_hash, commit_msg, phase, feature, source, committed_at
                              FROM pr_commits
                             WHERE client_id=1 AND project=%s
                               AND (session_id = %s
                                OR (committed_at BETWEEN %s::timestamptz AND %s::timestamptz))
                             ORDER BY committed_at""",
                        (p, session_id, created_at, updated_at),
                    )
                else:
                    cur.execute(
                        """SELECT commit_hash, commit_msg, phase, feature, source, committed_at
                              FROM pr_commits
                             WHERE client_id=1 AND project=%s AND session_id = %s
                             ORDER BY committed_at""",
                        (p, session_id),
                    )
                cols = [d[0] for d in cur.description]
                for row in cur.fetchall():
                    r = dict(zip(cols, row))
                    if r.get("committed_at"):
                        r["committed_at"] = r["committed_at"].isoformat()
                    commits.append(r)
    else:
        # Fallback: scan commit_log.jsonl
        log_path = Path(settings.workspace_dir) / p / "_system" / "commit_log.jsonl"
        if log_path.exists():
            for line in log_path.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    c = json.loads(line)
                    ts  = c.get("ts", "")
                    sid = c.get("session_id", "")
                    if sid == session_id or (created_at and updated_at and created_at <= ts <= updated_at):
                        commits.append({
                            "commit_hash": c.get("hash", ""),
                            "commit_msg":  c.get("message", c.get("msg", "")),
                            "committed_at": ts,
                            "phase":   c.get("phase"),
                            "feature": c.get("feature"),
                            "source":  c.get("source", "git"),
                        })
                except Exception:
                    pass

    return {"commits": commits, "session_id": session_id, "github_repo": github_repo}
