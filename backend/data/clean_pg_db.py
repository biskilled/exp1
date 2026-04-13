"""
clean_pg_db.py — PostgreSQL storage maintenance.

Reduces database size on disk in three passes:

  Pass 1 — Drop backup tables
    Migration scripts keep _old / _bak_NNN_ copies as rollback references.
    After verification they are dead weight. This pass drops all of them.

  Pass 2 — VACUUM FULL
    Rewrites each table into a fresh heap file, physically reclaiming all
    dead-row space that normal auto-vacuum only marks as reusable.
    Requires autocommit (cannot run inside a transaction).

  Pass 3 — REINDEX TABLE
    Rebuilds all B-tree and GIN indexes from scratch, eliminating the page
    bloat that accumulates from inserts/deletes over time.
    Also requires autocommit.

  Pass 4 — ANALYZE
    Refreshes query-planner statistics after the rewrites. No disk savings
    but prevents bad query plans after the table files move.

Usage (CLI / one-shot script):
    python3.12 -m data.clean_pg_db [--dry-run]

Usage (import):
    from data.clean_pg_db import run_maintenance
    report = run_maintenance(dry_run=False)

Usage (async wrapper — for FastAPI background tasks):
    from data.clean_pg_db import run_maintenance_async
    report = await run_maintenance_async()

VACUUM FULL and REINDEX require exclusive table locks while running — run
during low-traffic windows. They also temporarily need extra disk space equal
to the largest table being vacuumed (old + new file coexist briefly).
"""
from __future__ import annotations

import logging
import re
import sys
import time
from typing import Optional

log = logging.getLogger(__name__)

# ── Patterns ──────────────────────────────────────────────────────────────────

# Tables whose names match this pattern are treated as migration backups
_BACKUP_RE = re.compile(
    r"^(_bak_\d+_.+|.+_old)$",
    re.IGNORECASE,
)

# ── SQL ───────────────────────────────────────────────────────────────────────

_SQL_DB_SIZE       = "SELECT pg_database_size(current_database())"
_SQL_DB_SIZE_PRETTY = "SELECT pg_size_pretty(pg_database_size(current_database()))"

_SQL_ALL_TABLES = """
    SELECT relname
    FROM   pg_stat_user_tables
    WHERE  schemaname = 'public'
    ORDER  BY relname
"""

_SQL_TABLE_STATS = """
    SELECT relname,
           n_dead_tup,
           n_live_tup,
           pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
           pg_total_relation_size(relid)                 AS total_bytes
    FROM   pg_stat_user_tables
    WHERE  schemaname = 'public'
    ORDER  BY total_bytes DESC
"""

_SQL_TABLE_SIZE = "SELECT pg_size_pretty(pg_total_relation_size(%s))"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _raw_conn():
    """Open a fresh psycopg2 connection (not from the pool) using DATABASE_URL."""
    import psycopg2
    from core.config import settings
    url = settings.database_url
    if not url:
        raise RuntimeError("DATABASE_URL not configured")
    return psycopg2.connect(url, connect_timeout=30)


def _bytes_to_mb(b: int) -> float:
    return round(b / 1_048_576, 2)


# ── Main maintenance function ─────────────────────────────────────────────────

def run_maintenance(dry_run: bool = False) -> dict:
    """Run all maintenance passes. Returns a structured report dict.

    dry_run=True: collect stats and plan but execute nothing destructive.
    """
    t0 = time.monotonic()
    report: dict = {
        "dry_run":        dry_run,
        "size_before":    "",
        "size_after":     "",
        "saved_mb":       0.0,
        "tables_found":   [],
        "backup_tables":  [],
        "dropped_tables": [],
        "vacuumed":       [],
        "reindexed":      [],
        "analyzed":       [],
        "errors":         [],
        "duration_s":     0.0,
    }

    from core.database import db
    if not db.is_available():
        report["errors"].append("Database not available")
        return report

    # ── Snapshot before ───────────────────────────────────────────────────────
    try:
        conn_info = _raw_conn()
        with conn_info.cursor() as cur:
            cur.execute(_SQL_DB_SIZE)
            size_before_bytes: int = cur.fetchone()[0]
            cur.execute(_SQL_DB_SIZE_PRETTY)
            report["size_before"] = cur.fetchone()[0]

            cur.execute(_SQL_ALL_TABLES)
            all_tables: list[str] = [r[0] for r in cur.fetchall()]

            cur.execute(_SQL_TABLE_STATS)
            table_stats = [
                {
                    "table":       r[0],
                    "dead_rows":   r[1],
                    "live_rows":   r[2],
                    "total_size":  r[3],
                }
                for r in cur.fetchall()
            ]
        conn_info.close()
    except Exception as e:
        report["errors"].append(f"Pre-scan failed: {e}")
        return report

    report["tables_found"]  = all_tables
    report["table_stats"]   = table_stats

    backup_tables = [t for t in all_tables if _BACKUP_RE.match(t)]
    live_tables   = [t for t in all_tables if not _BACKUP_RE.match(t)]
    report["backup_tables"] = backup_tables

    log.info(
        f"clean_pg_db: {len(all_tables)} tables total — "
        f"{len(backup_tables)} backup, {len(live_tables)} live | "
        f"DB size before: {report['size_before']}"
    )

    # ── Pass 1: Drop backup tables ────────────────────────────────────────────
    for tbl in backup_tables:
        if dry_run:
            log.info(f"[DRY-RUN] would DROP TABLE {tbl}")
            report["dropped_tables"].append(tbl)
            continue
        try:
            conn_drop = _raw_conn()
            conn_drop.autocommit = True
            with conn_drop.cursor() as cur:
                log.info(f"clean_pg_db: DROP TABLE IF EXISTS {tbl} CASCADE")
                cur.execute(f'DROP TABLE IF EXISTS "{tbl}" CASCADE')
            conn_drop.close()
            report["dropped_tables"].append(tbl)
        except Exception as e:
            err = f"DROP {tbl}: {e}"
            log.warning(f"clean_pg_db: {err}")
            report["errors"].append(err)

    # ── Pass 2: VACUUM FULL (autocommit required) ─────────────────────────────
    for tbl in live_tables:
        if dry_run:
            log.info(f"[DRY-RUN] would VACUUM FULL {tbl}")
            report["vacuumed"].append(tbl)
            continue
        try:
            conn_vac = _raw_conn()
            conn_vac.autocommit = True
            with conn_vac.cursor() as cur:
                log.info(f"clean_pg_db: VACUUM FULL {tbl}")
                cur.execute(f'VACUUM FULL "{tbl}"')
            conn_vac.close()
            report["vacuumed"].append(tbl)
        except Exception as e:
            err = f"VACUUM FULL {tbl}: {e}"
            log.warning(f"clean_pg_db: {err}")
            report["errors"].append(err)

    # ── Pass 3: REINDEX TABLE (autocommit required) ───────────────────────────
    for tbl in live_tables:
        if dry_run:
            log.info(f"[DRY-RUN] would REINDEX TABLE {tbl}")
            report["reindexed"].append(tbl)
            continue
        try:
            conn_re = _raw_conn()
            conn_re.autocommit = True
            with conn_re.cursor() as cur:
                log.info(f"clean_pg_db: REINDEX TABLE {tbl}")
                cur.execute(f'REINDEX TABLE "{tbl}"')
            conn_re.close()
            report["reindexed"].append(tbl)
        except Exception as e:
            err = f"REINDEX {tbl}: {e}"
            log.warning(f"clean_pg_db: {err}")
            report["errors"].append(err)

    # ── Pass 4: ANALYZE (runs inside a normal transaction) ────────────────────
    try:
        conn_an = _raw_conn()
        conn_an.autocommit = True          # ANALYZE also disallowed in txn block
        with conn_an.cursor() as cur:
            for tbl in live_tables:
                if dry_run:
                    report["analyzed"].append(tbl)
                    continue
                try:
                    log.info(f"clean_pg_db: ANALYZE {tbl}")
                    cur.execute(f'ANALYZE "{tbl}"')
                    report["analyzed"].append(tbl)
                except Exception as e:
                    err = f"ANALYZE {tbl}: {e}"
                    log.warning(f"clean_pg_db: {err}")
                    report["errors"].append(err)
        conn_an.close()
    except Exception as e:
        report["errors"].append(f"ANALYZE pass failed: {e}")

    # ── Snapshot after ────────────────────────────────────────────────────────
    if not dry_run:
        try:
            conn_post = _raw_conn()
            with conn_post.cursor() as cur:
                cur.execute(_SQL_DB_SIZE)
                size_after_bytes: int = cur.fetchone()[0]
                cur.execute(_SQL_DB_SIZE_PRETTY)
                report["size_after"] = cur.fetchone()[0]
            conn_post.close()
            saved = size_before_bytes - size_after_bytes
            report["saved_mb"] = _bytes_to_mb(max(saved, 0))
        except Exception as e:
            report["errors"].append(f"Post-scan failed: {e}")
    else:
        report["size_after"] = report["size_before"]

    report["duration_s"] = round(time.monotonic() - t0, 1)
    log.info(
        f"clean_pg_db: done in {report['duration_s']}s — "
        f"saved ~{report['saved_mb']} MB "
        f"({len(report['dropped_tables'])} dropped, "
        f"{len(report['vacuumed'])} vacuumed, "
        f"{len(report['reindexed'])} reindexed)"
    )
    return report


async def run_maintenance_async(dry_run: bool = False) -> dict:
    """Async wrapper for FastAPI background tasks / endpoints."""
    import asyncio
    return await asyncio.to_thread(run_maintenance, dry_run)


# ── CLI entry point ───────────────────────────────────────────────────────────

def _cli() -> None:
    import argparse, json, os, sys
    from pathlib import Path

    # Ensure backend/ is on sys.path when run as `python3.12 -m data.clean_pg_db`
    backend_dir = Path(__file__).resolve().parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    # Bootstrap settings + DB
    os.environ.setdefault("REQUIRE_AUTH", "false")
    from core.config import settings  # noqa: F401 — triggers .env load
    from core.database import db
    db.init()

    parser = argparse.ArgumentParser(
        description="PostgreSQL maintenance — VACUUM FULL + REINDEX + drop backup tables"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Plan only — print what would be done without executing",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    report = run_maintenance(dry_run=args.dry_run)
    print(json.dumps(report, indent=2, default=str))
    if report["errors"]:
        sys.exit(1)


if __name__ == "__main__":
    _cli()
