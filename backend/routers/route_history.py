"""
History router — reads the unified workspace/{project}/history/history.jsonl

All sources write to the same file:
  - "ui"         : chat.py UI exchanges (full prompt + response)
  - "claude_cli" : Claude Code UserPromptSubmit hook (prompt only, no response)
  - "workflow"   : workflow runner steps

Legacy sources still merged for backward compat:
  - {engine_root}/.aicli/prompt_log.jsonl (older hook format)
"""

import asyncio
import json
import csv
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from psycopg2.extras import execute_values

from core.config import settings
from core.auth import get_optional_user
from core.database import db
from core.tags import tags_to_list, parse_tag

# ── SQL ────────────────────────────────────────────────────────────────────────

_SQL_LIST_COMMITS = """
    SELECT c.commit_hash, c.commit_msg, c.summary, c.tags,
           c.tags->>'source' AS source, c.session_id, c.committed_at,
           p.source_id AS prompt_source_id
    FROM mem_mrr_commits c
    LEFT JOIN mem_mrr_prompts p ON p.id = c.prompt_id
    WHERE c.project_id=%s
    ORDER BY c.committed_at DESC NULLS LAST, c.created_at DESC
    LIMIT %s
"""

_SQL_UPSERT_COMMIT_FROM_LOG = """
    INSERT INTO mem_mrr_commits
        (project_id, commit_hash, commit_msg, session_id, committed_at,
         tags)
    VALUES (%s, %s, %s, %s, %s,
            jsonb_build_object('source', %s))
    ON CONFLICT (commit_hash) DO UPDATE SET
        session_id = CASE
            WHEN EXCLUDED.session_id IS NOT NULL AND EXCLUDED.session_id != ''
            THEN EXCLUDED.session_id
            ELSE mem_mrr_commits.session_id
        END,
        tags = mem_mrr_commits.tags || EXCLUDED.tags
"""

_SQL_UPDATE_COMMIT_META = (
    "UPDATE mem_mrr_commits SET {set_clause} WHERE commit_hash = %s AND client_id=1 RETURNING commit_hash"
)

# Dynamic WHERE variant: add time-window filter when session timestamps are available.
# Base form matches by session_id only; extended form adds a committed_at range.
# Build dynamically in the handler; see session_commits() below.
_SQL_SESSION_COMMITS_BASE = """
    SELECT commit_hash, commit_msg, tags, tags->>'source' AS source, committed_at
          FROM mem_mrr_commits
         WHERE project_id=%s AND session_id = %s
         ORDER BY committed_at
"""

_SQL_SESSION_COMMITS_WITH_WINDOW = """
    SELECT commit_hash, commit_msg, tags, tags->>'source' AS source, committed_at
          FROM mem_mrr_commits
         WHERE project_id=%s
           AND (session_id = %s
            OR (committed_at BETWEEN %s::timestamptz AND %s::timestamptz))
         ORDER BY committed_at
"""

_SQL_GET_SESSION_TAGS = (
    "SELECT phase, feature, bug_ref, extra FROM mng_session_tags WHERE project_id=%s"
)

_SQL_UPSERT_SESSION_TAGS = """
    INSERT INTO mng_session_tags (project_id, phase, feature, bug_ref, extra, updated_at)
    VALUES (%s, %s, %s, %s, %s, NOW())
    ON CONFLICT (project_id) DO UPDATE SET
        phase = EXCLUDED.phase,
        feature = EXCLUDED.feature,
        bug_ref = EXCLUDED.bug_ref,
        extra = EXCLUDED.extra,
        updated_at = NOW()
"""

# Workflow run queries — dynamic: with or without a workflow name filter.
# Build the variant conditionally in workflow_runs(); constants cover both shapes.
_SQL_LIST_RUNS_BASE = """
    SELECT r.id, r.status, r.user_input, r.started_at, r.finished_at,
           r.total_cost_usd, r.error, r.current_node, r.context,
           w.name AS workflow_name
    FROM pr_graph_runs r
    LEFT JOIN pr_graph_workflows w ON w.id = r.workflow_id
    WHERE r.project_id=%s
    ORDER BY r.started_at DESC LIMIT %s
"""

_SQL_LIST_RUNS_BY_WORKFLOW = """
    SELECT r.id, r.status, r.user_input, r.started_at, r.finished_at,
           r.total_cost_usd, r.error, r.current_node, r.context,
           w.name AS workflow_name
    FROM pr_graph_runs r
    LEFT JOIN pr_graph_workflows w ON w.id = r.workflow_id
    WHERE r.project_id=%s AND w.name=%s
    ORDER BY r.started_at DESC LIMIT %s
"""

# IN-list placeholder built dynamically; template documents intent.
# Usage: f"SELECT run_id, COUNT(*) FROM pr_graph_node_results WHERE run_id IN ({placeholders}) GROUP BY run_id"
_SQL_COUNT_NODE_RESULTS_TEMPLATE = (
    "SELECT run_id, COUNT(*) FROM pr_graph_node_results "
    "WHERE run_id IN ({placeholders}) GROUP BY run_id"
)

# ── Router definition ─────────────────────────────────────────────────────────

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
    limit: int = Query(500),
    offset: int = Query(0),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    """Return unified project history from mem_mrr_prompts (DB-primary).

    Falls back to history.jsonl when DB is unavailable.
    Noise entries are filtered. Returns newest-first with pagination.
    """
    p = project or settings.active_project or "default"

    if db.is_available():
        try:
            project_id = db.get_or_create_project_id(p)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Total count (excluding noise)
                    noise_filter = " AND NOT (" + " OR ".join(
                        f"prompt LIKE %s" for _ in range(4)
                    ) + ")"
                    noise_args = tuple(f"{pat}%" for pat in _NOISE_PATTERNS)

                    provider_filter = " AND tags->>'source' = %s" if provider else ""
                    provider_arg    = (provider,) if provider else ()

                    cur.execute(
                        f"""SELECT COUNT(*) FROM mem_mrr_prompts
                            WHERE project_id=%s
                              AND prompt IS NOT NULL AND prompt != ''
                              {noise_filter}{provider_filter}""",
                        (project_id,) + noise_args + provider_arg,
                    )
                    total = cur.fetchone()[0]

                    cur.execute(
                        f"""SELECT source_id, session_id, tags->>'source' AS source, prompt,
                                   response, tags, created_at
                            FROM mem_mrr_prompts
                            WHERE project_id=%s
                              AND prompt IS NOT NULL AND prompt != ''
                              {noise_filter}{provider_filter}
                            ORDER BY created_at DESC
                            LIMIT %s OFFSET %s""",
                        (project_id,) + noise_args + provider_arg + (limit if limit > 0 else 10000, offset),
                    )
                    rows = cur.fetchall()

            entries = [
                {
                    "ts":         r[0] or (r[6].strftime("%Y-%m-%dT%H:%M:%SZ") if r[6] else ""),
                    "source":     r[2] or "ui",
                    "session_id": r[1],
                    "provider":   r[2] or "unknown",
                    "user_input": r[3],
                    "output":     r[4] or "",
                    "tags":       tags_to_list(r[5] or {}),
                }
                for r in rows
            ]
            return {
                "entries": entries,
                "total": total,
                "filtered": 0,
                "offset": offset,
                "limit": limit,
                "has_more": (offset + len(entries)) < total,
            }
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("chat_history DB read failed, falling back to JSONL: %s", e)

    # Fallback: JSONL (when DB unavailable)
    entries = _load_unified_history(project, provider)
    if provider is None or provider == "claude":
        entries.extend(_load_prompt_log_legacy())
    seen: set[tuple] = set()
    deduped: list[dict] = []
    for e in entries:
        key = (e.get("ts", ""), e.get("user_input", "")[:80])
        if key not in seen:
            seen.add(key)
            if not _is_noisy(e):
                deduped.append(e)
    deduped.sort(key=lambda x: x.get("ts", ""), reverse=True)
    total = len(deduped)
    page = deduped[offset:offset + limit] if limit > 0 else deduped[offset:]
    return {"entries": page, "total": total, "filtered": 0,
            "offset": offset, "limit": limit, "has_more": (offset + len(page)) < total}


class CommitPatch(BaseModel):
    add_tag:  str | None = None   # e.g. "phase:discovery" — appended to tags[]
    remove_tag: str | None = None  # e.g. "phase:discovery" — removed from tags[]
    summary: str | None = None


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
        project_id = db.get_or_create_project_id(p)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_LIST_COMMITS, (project_id, limit))
                cols = [d[0] for d in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
                # Normalise types for JSON
                for r in rows:
                    if r.get("committed_at"):
                        r["committed_at"] = r["committed_at"].isoformat()
                    if isinstance(r.get("tags"), dict):
                        r["tags"] = tags_to_list(r["tags"])
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
                    "source": raw.get("source", "git"),
                    "session_id": raw.get("session_id"),
                    "tags": [],
                    "committed_at": raw.get("ts"),
                })
            except json.JSONDecodeError:
                pass

    commits.reverse()
    return {"commits": commits[:limit], "project": p, "source": "file"}


@router.patch("/commits/{commit_hash}")
async def patch_commit(commit_hash: str, body: CommitPatch, project: str | None = Query(None)):
    """Update metadata (add_tag, remove_tag, summary) for a commit row."""
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")
    p = project or settings.active_project or "default"

    updates: list[str] = []
    params: list = []

    if body.add_tag is not None:
        _k, _v = parse_tag(body.add_tag)
        updates.append("tags = tags || %s::jsonb")
        params.append(json.dumps({_k: _v}))
    if body.remove_tag is not None:
        _k, _ = parse_tag(body.remove_tag)
        updates.append("tags = tags - %s")
        params.append(_k)
    if body.summary is not None:
        updates.append("summary = %s")
        params.append(body.summary)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(commit_hash)
    with db.conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                _SQL_UPDATE_COMMIT_META.format(set_clause=", ".join(updates)),
                params,
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Commit not found")

    return {"ok": True, "commit_hash": commit_hash}


async def _embed_commits_background(project: str, commit_hashes: list[str]) -> None:
    """Fire-and-forget: run process_commit() for each hash. Silent on error."""
    try:
        from memory.memory_embedding import MemoryEmbedding
        emb = MemoryEmbedding()
        for h in commit_hashes:
            try:
                await emb.process_commit(project, h)
            except Exception as e:
                import logging
                logging.getLogger(__name__).debug(f"_embed_commits_background {h}: {e}")
    except Exception:
        pass


@router.post("/commits/sync")
async def sync_commits(project: str | None = Query(None)):
    """Import commit_log.jsonl → commits table. Idempotent (UPSERT on commit_hash)."""
    if not db.is_available():
        raise HTTPException(status_code=503, detail="PostgreSQL not available")

    p = project or settings.active_project or "default"
    project_id = db.get_or_create_project_id(p)
    log_path = _project_dir(project) / "_system" / "commit_log.jsonl"
    if not log_path.exists():
        return {"imported": 0, "project": p}

    # Parse all valid rows first, then batch-upsert in one round-trip
    rows: list[tuple] = []
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
            source_val = raw.get("source", "git")
            rows.append((
                project_id,
                commit_hash,
                raw.get("message", raw.get("msg", "")),
                raw.get("session_id"),
                raw.get("ts"),
                json.dumps({"source": source_val}),
            ))

    if not rows:
        return {"imported": 0, "project": p}

    _SQL_BATCH_UPSERT = """
        INSERT INTO mem_mrr_commits
            (project_id, commit_hash, commit_msg, session_id, committed_at, tags)
        VALUES %s
        ON CONFLICT (commit_hash) DO UPDATE SET
            session_id = CASE
                WHEN EXCLUDED.session_id IS NOT NULL AND EXCLUDED.session_id != ''
                THEN EXCLUDED.session_id
                ELSE mem_mrr_commits.session_id
            END,
            tags = mem_mrr_commits.tags || EXCLUDED.tags
    """
    with db.conn() as conn:
        with conn.cursor() as cur:
            execute_values(cur, _SQL_BATCH_UPSERT, rows)
            inserted = cur.rowcount

    # Fire process_commit() for each new commit (fire-and-forget background tasks)
    hashes = [r[2] for r in rows]  # commit_hash is index 2 in each tuple
    asyncio.create_task(_embed_commits_background(p, hashes))

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
        project_id = db.get_or_create_project_id(p)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_SQL_GET_SESSION_TAGS, (project_id,))
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
        project_id = db.get_or_create_project_id(p)
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    _SQL_UPSERT_SESSION_TAGS,
                    (project_id, body.phase, body.feature, body.bug_ref,
                     _json.dumps(body.extra or {})),
                )

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
            project_id = db.get_or_create_project_id(project)
            with db.conn() as conn:
                with conn.cursor() as cur:
                    # Use the workflow-filtered variant when a name is provided;
                    # otherwise use the base query (_SQL_LIST_RUNS_BY_WORKFLOW / _SQL_LIST_RUNS_BASE).
                    if workflow:
                        cur.execute(
                            _SQL_LIST_RUNS_BY_WORKFLOW,
                            (project_id, workflow, min(limit, 200)),
                        )
                    else:
                        cur.execute(
                            _SQL_LIST_RUNS_BASE,
                            (project_id, min(limit, 200)),
                        )
                    rows = cur.fetchall()

                    # Count node results per run
                    run_ids = [str(r[0]) for r in rows]
                    step_counts: dict = {}
                    if run_ids:
                        placeholders = ",".join(["%s"] * len(run_ids))
                        cur.execute(
                            _SQL_COUNT_NODE_RESULTS_TEMPLATE.format(placeholders=placeholders),
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
        project_id = db.get_or_create_project_id(p)
        with db.conn() as conn:
            with conn.cursor() as cur:
                # Use the time-window variant when session timestamps are available
                # (_SQL_SESSION_COMMITS_WITH_WINDOW), otherwise fall back to the
                # session_id-only query (_SQL_SESSION_COMMITS_BASE).
                if created_at and updated_at:
                    cur.execute(
                        _SQL_SESSION_COMMITS_WITH_WINDOW,
                        (project_id, session_id, created_at, updated_at),
                    )
                else:
                    cur.execute(_SQL_SESSION_COMMITS_BASE, (project_id, session_id))
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
                            "tags":   c.get("tags", []),
                            "source": c.get("source", "git"),
                        })
                except Exception:
                    pass

    return {"commits": commits, "session_id": session_id, "github_repo": github_repo}
