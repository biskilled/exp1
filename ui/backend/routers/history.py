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

from config import settings
from core.auth import get_optional_user

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


@router.get("/commits")
async def commits_history(
    project: str | None = Query(None),
    limit: int = Query(50),
):
    """Read commits.csv for a project."""
    csv_path = _project_dir(project) / "commits.csv"

    if not csv_path.exists():
        return {"commits": [], "project": project}

    commits = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            commits.append(dict(row))

    commits.reverse()
    return {"commits": commits[:limit]}


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
