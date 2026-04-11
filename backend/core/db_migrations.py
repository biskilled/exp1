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

def m018_work_items_links(conn) -> None:
    """Create mem_ai_work_items_links — comprehensive linkage table for work items."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mem_ai_work_items_links (
                id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id       INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                work_item_id     UUID        NOT NULL REFERENCES mem_ai_work_items(id) ON DELETE CASCADE,
                event_id         UUID        REFERENCES mem_ai_events(id) ON DELETE CASCADE,
                commit_hash      VARCHAR(64) REFERENCES mem_mrr_commits(commit_hash) ON DELETE CASCADE,
                prompt_source_id TEXT,
                link_type        TEXT        NOT NULL DEFAULT 'explicit',
                matched_tags     JSONB       NOT NULL DEFAULT '{}',
                matched_tags_ai  JSONB       NOT NULL DEFAULT '{}',
                created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mawi_links_pid    ON mem_ai_work_items_links(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mawi_links_wi     ON mem_ai_work_items_links(work_item_id)")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mawi_links_event  ON mem_ai_work_items_links(work_item_id, event_id)  WHERE event_id IS NOT NULL")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mawi_links_commit ON mem_ai_work_items_links(work_item_id, commit_hash) WHERE commit_hash IS NOT NULL")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mawi_links_prompt ON mem_ai_work_items_links(work_item_id, prompt_source_id) WHERE prompt_source_id IS NOT NULL")
    conn.commit()
    log.info("m018_work_items_links: mem_ai_work_items_links created")


def m019_wi_event_fk_columns(conn) -> None:
    """Replace mem_ai_work_items_links with direct FK columns on commits and events.

    - mem_mrr_commits.event_id UUID  — links commit to its mem_ai_events digest row
    - mem_ai_events.work_item_id UUID — links an event to the work item it belongs to
    Backfills work_item_id from existing mem_ai_work_items.source_event_id relations.
    """
    with conn.cursor() as cur:
        # Drop the short-lived links table (m018) if it exists
        cur.execute("DROP TABLE IF EXISTS mem_ai_work_items_links CASCADE")
        # Add event_id to commits (no FK constraint — events table created later in schema)
        cur.execute(
            "ALTER TABLE mem_mrr_commits ADD COLUMN IF NOT EXISTS event_id UUID"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mmrr_c_event ON mem_mrr_commits(event_id) WHERE event_id IS NOT NULL"
        )
        # Add work_item_id to events
        cur.execute(
            "ALTER TABLE mem_ai_events ADD COLUMN IF NOT EXISTS work_item_id UUID"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mem_ai_events_wi ON mem_ai_events(work_item_id) WHERE work_item_id IS NOT NULL"
        )
        # Backfill: set work_item_id on events that are source_event_id for a work item
        cur.execute("""
            UPDATE mem_ai_events e
               SET work_item_id = w.id
              FROM mem_ai_work_items w
             WHERE w.source_event_id = e.id
               AND e.work_item_id IS NULL
        """)
    conn.commit()
    log.info("m019_wi_event_fk_columns: event_id on commits + work_item_id on events applied")


def m020_perf_indexes(conn) -> None:
    """Add missing composite indexes for query performance.

    The work items and planner queries were doing O(N) correlated subqueries
    or full-table scans due to missing indexes on frequently-filtered columns.
    """
    with conn.cursor() as cur:
        # mem_ai_events — session_id lookups (used in _SQL_UNLINKED_WORK_ITEMS CTE)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mae_project_session "
            "ON mem_ai_events(project_id, session_id) WHERE session_id IS NOT NULL"
        )
        # mem_ai_events — event_type filter (prompt_batch/session_summary counts)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mae_project_etype "
            "ON mem_ai_events(project_id, event_type)"
        )
        # mem_mrr_commits — session_id lookups (commit count per session in work items)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mmrrc_project_session "
            "ON mem_mrr_commits(project_id, session_id) WHERE session_id IS NOT NULL"
        )
        # planner_tags — name lookups (entity/tag search)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_planner_tags_project_name "
            "ON planner_tags(project_id, name)"
        )
        # mem_ai_work_items — status_user filter (unlinked items query skips 'done')
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mawi_project_status_user "
            "ON mem_ai_work_items(project_id, status_user)"
        )
    conn.commit()
    log.info("m020_perf_indexes: composite indexes applied")



def m021_rename_work_item_columns(conn) -> None:
    """Rename mem_ai_work_items columns for consistency.

    - ai_tags     → tags_ai        (JSONB AI suggestions)
    - ai_tag_id   → tag_id_ai      (AI-suggested planner_tag FK)
    - tag_id      → tag_id_user    (User-confirmed planner_tag FK)
    - acceptance_criteria → acceptance_criteria_ai  (AI-generated)
    - action_items → action_items_ai               (AI-generated)
    - requirements → DROPPED       (belonged on planner_tags, not work items)
    """
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE mem_ai_work_items RENAME COLUMN ai_tags TO tags_ai")
        cur.execute("ALTER TABLE mem_ai_work_items RENAME COLUMN ai_tag_id TO tag_id_ai")
        cur.execute("ALTER TABLE mem_ai_work_items RENAME COLUMN tag_id TO tag_id_user")
        cur.execute("ALTER TABLE mem_ai_work_items RENAME COLUMN acceptance_criteria TO acceptance_criteria_ai")
        cur.execute("ALTER TABLE mem_ai_work_items RENAME COLUMN action_items TO action_items_ai")
        cur.execute("ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS requirements")
    conn.commit()
    log.info("m021_rename_work_item_columns: 5 renames + 1 drop applied")


def m022_backfill_event_work_item_ids(conn) -> None:
    """Backfill work_item_id on mem_ai_events for all work items with source_event_id.

    Implements proper one-to-many: one work_item → many events.
    For each work item that has a source_event_id (session-sourced), find all other
    events in the same session and set work_item_id = work_item.id on them
    (only if they don't already have a work_item_id assigned).
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE mem_ai_events e
            SET work_item_id = wi.id
            FROM mem_ai_work_items wi
            JOIN mem_ai_events src ON src.id = wi.source_event_id
            WHERE e.session_id = src.session_id
              AND e.project_id = wi.project_id
              AND e.work_item_id IS NULL
              AND wi.source_event_id IS NOT NULL
              AND src.session_id IS NOT NULL
        """)
        updated = cur.rowcount
    conn.commit()
    log.info(f"m022_backfill_event_work_item_ids: {updated} events backlinked")


def m023_work_items_tags_to_jsonb(conn) -> None:
    """Convert mem_ai_work_items.tags from TEXT[] to JSONB.

    Old design stored tags as a text array {source:claude_cli, phase:dev} — never
    populated and hard to query. New design: JSONB object {source, phase, feature, ...}
    matching the tags on mem_mrr_* tables.

    All existing rows have tags={} (empty array) so the USING clause just sets '{}'.
    """
    with conn.cursor() as cur:
        # Step 1: drop the old TEXT[] default so PostgreSQL allows the type change
        cur.execute("ALTER TABLE mem_ai_work_items ALTER COLUMN tags DROP DEFAULT")
        # Step 2: alter type with explicit USING — all existing rows are empty arrays
        cur.execute("""
            ALTER TABLE mem_ai_work_items
            ALTER COLUMN tags TYPE JSONB
            USING CASE WHEN array_length(tags, 1) IS NULL THEN '{}'::jsonb
                       ELSE array_to_json(tags)::jsonb END
        """)
        # Step 3: restore default and NOT NULL constraint for JSONB
        cur.execute("ALTER TABLE mem_ai_work_items ALTER COLUMN tags SET DEFAULT '{}'::jsonb")
        cur.execute("ALTER TABLE mem_ai_work_items ALTER COLUMN tags SET NOT NULL")
    conn.commit()
    log.info("m023_work_items_tags_to_jsonb: tags column converted TEXT[] → JSONB")


def m024_backfill_work_item_tags(conn) -> None:
    """Backfill work item tags from source event tags.

    For each work item whose tags={} and has a source_event_id,
    copies the user-intent keys (source, phase, feature, bug, component, doc_type)
    from the source event's tags JSONB into the work item.

    Handles both session events (phase/feature keys) and commit events
    (ai_phase/ai_feature keys) by using COALESCE to map ai_* variants.

    This is a one-time data migration for items created before m023/m024.
    Going forward, tags are set at extraction time in memory_promotion.py.
    """
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE mem_ai_work_items wi
            SET tags = jsonb_strip_nulls(jsonb_build_object(
                'phase',     COALESCE(e.tags->>'phase',   e.tags->>'ai_phase'),
                'feature',   COALESCE(e.tags->>'feature', e.tags->>'ai_feature'),
                'source',    e.tags->>'source',
                'bug',       e.tags->>'bug',
                'component', e.tags->>'component',
                'doc_type',  e.tags->>'doc_type'
            ))
            FROM mem_ai_events e
            WHERE e.id = wi.source_event_id
              AND wi.tags = '{}'::jsonb
              AND (
                    e.tags->>'phase'      IS NOT NULL
                 OR e.tags->>'ai_phase'   IS NOT NULL
                 OR e.tags->>'feature'    IS NOT NULL
                 OR e.tags->>'ai_feature' IS NOT NULL
                 OR e.tags->>'source'     IS NOT NULL
              )
        """)
        updated = cur.rowcount
    conn.commit()
    log.info(f"m024_backfill_work_item_tags: {updated} work items backfilled with event tags")


MIGRATIONS: list[tuple[str, Callable]] = [
    # All migrations through m017 (ai_tags column) were applied via the legacy
    # ALTER TABLE system in database.py and are tracked as:
    #   pr_tables_v1, memory_infra_v1, memory_infra_alters_v2,
    #   work_items_alters_v1, commit_code_v1
    ("m018_work_items_links", m018_work_items_links),
    ("m019_wi_event_fk_columns", m019_wi_event_fk_columns),
    ("m020_perf_indexes", m020_perf_indexes),
    ("m021_rename_work_item_columns", m021_rename_work_item_columns),
    ("m022_backfill_event_work_item_ids", m022_backfill_event_work_item_ids),
    ("m023_work_items_tags_to_jsonb", m023_work_items_tags_to_jsonb),
    ("m024_backfill_work_item_tags", m024_backfill_work_item_tags),
]
