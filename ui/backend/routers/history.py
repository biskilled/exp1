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

from config import settings
from core.auth import get_optional_user
from core.database import db

router = APIRouter()

# Engine root: .../aicli/ui/backend/routers/history.py → four parents up
_ENGINE_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _project_dir(project: str | None = None) -> Path:
    p = project or settings.active_project or "default"
    return Path(settings.workspace_dir) / p


def _load_unified_history(project: str | None, provider: str | None = None) -> list[dict]:
    """Read workspace/{project}/_system/history.jsonl."""
    hist_file = _project_dir(project) / "_system" / "history.jsonl"
    if not hist_file.exists():
        return []

    entries = []
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
    limit: int = Query(100),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Return unified project history — all sources, all users."""
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

    deduped.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return {"entries": deduped[:limit], "total": len(deduped)}


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
                           feature, bug_ref, source, session_id, tags, committed_at
                    FROM commits
                    WHERE project = %s
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
async def patch_commit(commit_id: int, body: CommitPatch):
    """Update metadata (phase, feature, bug_ref, summary, tags) for a commit row."""
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

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
                f"UPDATE commits SET {', '.join(updates)} WHERE id = %s RETURNING id",
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
                        INSERT INTO commits
                            (project, commit_hash, commit_msg, source, session_id, committed_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (project, commit_hash) DO NOTHING
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


@router.get("/session-tags")
async def get_session_tags(project: str | None = Query(None)):
    """Get current active session tags for a project."""
    p = project or settings.active_project or "default"
    if db.is_available():
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT phase, feature, bug_ref, extra FROM session_tags WHERE project=%s",
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
                    INSERT INTO session_tags (project, phase, feature, bug_ref, extra, updated_at)
                    VALUES (%s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (project) DO UPDATE SET
                        phase = EXCLUDED.phase,
                        feature = EXCLUDED.feature,
                        bug_ref = EXCLUDED.bug_ref,
                        extra = EXCLUDED.extra,
                        updated_at = NOW()
                """, (p, body.phase, body.feature, body.bug_ref,
                      _json.dumps(body.extra or {})))

    return {"ok": True, **tags}


@router.get("/runs")
async def workflow_runs(
    project: str | None = Query(None),
    workflow: str | None = Query(None),
    limit: int = Query(20),
):
    """List workflow run logs."""
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
