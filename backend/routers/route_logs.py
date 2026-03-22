"""
Log ingestion endpoint for the frontend.

The UI posts uncaught JS errors / promise rejections here so they appear
in the same log files as backend errors (error.log / app.log).

POST /logs/ui-error  — no auth required (errors happen before login too)
GET  /logs/files     — list log files (admin only)
GET  /logs/tail      — tail a log file (admin only)
"""

import os
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from core.config import settings
from core.logger import get_logger
from core.auth import get_optional_user

log = get_logger(__name__)
router = APIRouter()


class UIErrorBody(BaseModel):
    level: str = "ERROR"        # ERROR | WARNING | INFO
    message: str
    stack: str | None = None    # JS stack trace
    url: str | None = None      # page URL where error occurred
    user_agent: str | None = None
    context: dict | None = None # optional extra fields (component, action, etc.)


@router.post("/ui-error", status_code=204)
async def log_ui_error(body: UIErrorBody) -> None:
    """Accept a frontend error and write it to the backend log files."""
    prefix = f"[UI] {body.url or '?'} | {body.message}"
    extra = ""
    if body.stack:
        # Keep stack on same log line (collapsed with \n → space for grep-ability)
        extra = " | " + body.stack.replace("\n", " ← ")
    if body.context:
        extra += f" | ctx={body.context}"

    lvl = (body.level or "ERROR").upper()
    if lvl == "ERROR":
        log.error("%s%s", prefix, extra)
    elif lvl in ("WARNING", "WARN"):
        log.warning("%s%s", prefix, extra)
    else:
        log.info("%s%s", prefix, extra)


@router.get("/files")
async def list_log_files() -> list[dict]:
    """List log files in the log directory (admin only)."""
    log_dir = Path(settings.log_dir).expanduser()
    if not log_dir.exists():
        return []
    files = []
    for f in sorted(log_dir.iterdir()):
        if f.is_file():
            stat = f.stat()
            files.append({
                "name": f.name,
                "size_bytes": stat.st_size,
                "modified": stat.st_mtime,
            })
    return files


@router.get("/tail", response_class=PlainTextResponse)
async def tail_log_file(
    file: str = Query("app.log", description="Log file name (e.g. app.log, error.log)"),
    lines: int = Query(100, ge=1, le=5000),
) -> str:
    """Return the last N lines from a log file (admin only)."""
    log_dir = Path(settings.log_dir).expanduser()
    # Sanitize — only allow plain filenames, no path traversal
    safe_name = Path(file).name
    target = log_dir / safe_name
    if not target.exists():
        return f"# File not found: {safe_name}\n"
    # Read last N lines efficiently
    with open(target, "rb") as fh:
        fh.seek(0, os.SEEK_END)
        size = fh.tell()
        chunk = min(size, lines * 200)  # estimate ~200 bytes/line
        fh.seek(max(0, size - chunk))
        raw = fh.read().decode("utf-8", errors="replace")
    tail = "\n".join(raw.splitlines()[-lines:])
    return tail + "\n"
