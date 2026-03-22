"""
Centralized logging for aicli backend.

Wraps Python's standard logging with:
  - Three rotating file handlers (app.log / debug.log / error.log)
  - Daily rotation via TimedRotatingFileHandler
  - Automatic cleanup of rotated files older than `retention_days`
  - Console handler at the configured level
  - Consistent timestamped format across all handlers

Log directory lives OUTSIDE backend/ — defaults to ~/.aicli/logs/
and is configurable via the LOG_DIR env var or Settings.log_dir.

Usage (any module):
    from core.logger import get_logger
    log = get_logger(__name__)
    log.info("Something happened")
    log.error("Something broke: %s", e)

Call AppLogger.setup() exactly once at backend startup (main.py).
"""

import logging
import logging.handlers
import sys
from datetime import datetime, timedelta
from pathlib import Path


_FMT = "%(asctime)s | %(levelname)-8s | %(name)-35s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


class AppLogger:
    """One-time logger bootstrap.  Call AppLogger.setup() in main.py startup."""

    _initialized: bool = False

    @classmethod
    def setup(
        cls,
        log_dir: Path,
        level: str = "info",
        retention_days: int = 30,
        debug_backup_count: int = 7,
    ) -> None:
        """Configure root logger with rotating file + console handlers.

        Args:
            log_dir:            Directory for log files (created if missing).
            level:              Console log level (debug|info|warning|error).
            retention_days:     How many days to keep app.log / error.log backups.
            debug_backup_count: How many days to keep debug.log backups (verbose).
        """
        if cls._initialized:
            return

        log_dir = Path(log_dir).expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)

        # Clean up old rotated files before adding handlers
        cls._cleanup_old_logs(log_dir, retention_days)

        formatter = logging.Formatter(_FMT, datefmt=_DATE_FMT)
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)  # capture everything; handlers filter

        # ── Console ────────────────────────────────────────────────────────────
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(getattr(logging, level.upper(), logging.INFO))
        console.setFormatter(formatter)
        root.addHandler(console)

        # ── app.log — INFO+ ────────────────────────────────────────────────────
        fh_app = logging.handlers.TimedRotatingFileHandler(
            log_dir / "app.log",
            when="midnight",
            backupCount=retention_days,
            encoding="utf-8",
        )
        fh_app.setLevel(logging.INFO)
        fh_app.setFormatter(formatter)
        root.addHandler(fh_app)

        # ── debug.log — DEBUG+ ─────────────────────────────────────────────────
        fh_debug = logging.handlers.TimedRotatingFileHandler(
            log_dir / "debug.log",
            when="midnight",
            backupCount=debug_backup_count,
            encoding="utf-8",
        )
        fh_debug.setLevel(logging.DEBUG)
        fh_debug.setFormatter(formatter)
        root.addHandler(fh_debug)

        # ── error.log — ERROR+ ─────────────────────────────────────────────────
        fh_err = logging.handlers.TimedRotatingFileHandler(
            log_dir / "error.log",
            when="midnight",
            backupCount=retention_days,
            encoding="utf-8",
        )
        fh_err.setLevel(logging.ERROR)
        fh_err.setFormatter(formatter)
        root.addHandler(fh_err)

        cls._initialized = True
        logging.getLogger(__name__).info(
            "Logger initialized — dir=%s  level=%s  retention=%dd  debug_backups=%d",
            log_dir, level, retention_days, debug_backup_count,
        )

    @classmethod
    def _cleanup_old_logs(cls, log_dir: Path, retention_days: int) -> None:
        """Delete rotated log files (*.log.*) older than retention_days."""
        cutoff = datetime.now() - timedelta(days=retention_days)
        deleted = 0
        for f in log_dir.glob("*.log.*"):
            try:
                if f.stat().st_mtime < cutoff.timestamp():
                    f.unlink()
                    deleted += 1
            except OSError:
                pass
        if deleted:
            logging.getLogger(__name__).info(
                "Cleaned up %d old rotated log files from %s", deleted, log_dir
            )


def get_logger(name: str) -> logging.Logger:
    """Return a named logger.  Equivalent to logging.getLogger(name).

    Provided as the canonical import so all modules import from one place
    and future extensions (e.g. structured logging) only need one change here.
    """
    return logging.getLogger(name)
