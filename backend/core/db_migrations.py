"""
db_migrations.py — Database migration runner for aicli.

Migration philosophy
────────────────────
Each schema change follows a safe rename → recreate → copy pattern:

    1. Rename the old table:  ALTER TABLE foo RENAME TO _bak_{version}_foo
    2. Create the new table:  the CREATE TABLE from db_schema.sql
    3. Copy data:             INSERT INTO foo (cols) SELECT cols FROM _bak_{version}_foo
    4. (Optional) Drop backup after verification

Benefits vs ALTER TABLE ADD COLUMN:
  - Works for column removals, type changes, and renames (not just additions)
  - The backup table is a free rollback path
  - db_schema.sql always reflects the final target shape

FK-dependent tables
───────────────────
If table B has a FK → table A, and you need to migrate A:
    1. Drop the FK constraint from B  (ALTER TABLE B DROP CONSTRAINT fk_name)
    2. Run migrate_table() on A
    3. Recreate the FK on B          (ALTER TABLE B ADD CONSTRAINT ...)

Helper usage example
────────────────────
    def m018_add_new_column(conn) -> None:
        migrate_table(
            conn,
            old_table   = "mem_ai_work_items",
            backup_name = "_bak_018_mem_ai_work_items",
            create_sql  = '''
                CREATE TABLE mem_ai_work_items (
                    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    project_id  INT  NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                    new_column  TEXT NOT NULL DEFAULT '',
                    -- ... all other columns from db_schema.sql
                )
            ''',
            copy_columns = [
                "id", "client_id", "project_id", "ai_category", "ai_name",
                # list every column that existed BEFORE this migration
                # new columns get their DEFAULT values automatically
            ],
        )

MIGRATIONS list
───────────────
Each entry: (version: str, up_fn: Callable[[conn], None])
Versions must be unique and monotonically increasing.
Already-applied versions are skipped (tracked in mng_schema_version).
"""
from __future__ import annotations

import logging
from typing import Callable

log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Migration helper
# ─────────────────────────────────────────────────────────────────────────────

def migrate_table(
    conn,
    old_table:    str,
    backup_name:  str,
    create_sql:   str,
    copy_columns: list[str],
) -> None:
    """
    Rename → recreate → copy pattern.

    Args:
        conn:         psycopg2 connection (autocommit=False, caller controls commit)
        old_table:    current table name (e.g. 'mem_ai_work_items')
        backup_name:  name for the renamed backup (e.g. '_bak_018_mem_ai_work_items')
        create_sql:   full CREATE TABLE statement for the new schema (no IF NOT EXISTS)
        copy_columns: columns to copy from backup → new table (omit new columns;
                      they get their DEFAULT values)
    """
    cols = ", ".join(copy_columns)
    with conn.cursor() as cur:
        log.info(f"migrate_table: renaming {old_table} → {backup_name}")
        cur.execute(f"ALTER TABLE {old_table} RENAME TO {backup_name}")
        log.info(f"migrate_table: creating new {old_table}")
        cur.execute(create_sql)
        log.info(f"migrate_table: copying {len(copy_columns)} columns from {backup_name}")
        cur.execute(f"INSERT INTO {old_table} ({cols}) SELECT {cols} FROM {backup_name}")
    conn.commit()
    log.info(f"migrate_table: {old_table} migration complete ({backup_name} kept as backup)")


# ─────────────────────────────────────────────────────────────────────────────
# Migration registry
# ─────────────────────────────────────────────────────────────────────────────
# Format: list of (version_string, callable(conn) -> None)
# Migrations are applied in list order; already-applied versions are skipped.
#
# HOW TO ADD A MIGRATION:
#   1. Update db_schema.sql with the new table structure
#   2. Define a migration function below (name it m{NNN}_description)
#   3. Append (version, function) to MIGRATIONS
#   4. Bump version suffix if modifying an existing migration block in database.py
#
# Version naming convention: "m{NNN}_{table_slug}"
# Examples: "m018_add_wi_priority", "m019_rename_fact_key"

MIGRATIONS: list[tuple[str, Callable]] = [
    # All migrations through m017 (ai_tags column) were applied via the legacy
    # ALTER TABLE system in database.py and are tracked as:
    #   pr_tables_v1, memory_infra_v1, memory_infra_alters_v2,
    #   work_items_alters_v1, commit_code_v1
    #
    # Future migrations go here:
    # ("m018_example", m018_example),
]
