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


def m025_rename_work_item_ai_columns(conn) -> None:
    """Rename mem_ai_work_items columns for consistency — all AI-generated fields use _ai suffix.

    - ai_name     → name_ai       (AI-extracted slug)
    - ai_category → category_ai   (AI-extracted category)
    - ai_desc     → desc_ai       (AI-extracted description)
    - summary     → summary_ai    (PM digest, repurposed for promote_work_item output)
    """
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE mem_ai_work_items RENAME COLUMN ai_name     TO name_ai")
        cur.execute("ALTER TABLE mem_ai_work_items RENAME COLUMN ai_category TO category_ai")
        cur.execute("ALTER TABLE mem_ai_work_items RENAME COLUMN ai_desc     TO desc_ai")
        cur.execute("ALTER TABLE mem_ai_work_items RENAME COLUMN summary     TO summary_ai")
    conn.commit()
    log.info("m025_rename_work_item_ai_columns: 4 columns renamed")


def m026_planner_tags_cleanup(conn) -> None:
    """Rationalise planner_tags — clean column set, enforce creator/updater, fix order.

    DROP:   seq_num, source, full_desc, code_summary, is_reusable
    RENAME: short_desc → description
    ADD:    updater TEXT NOT NULL DEFAULT 'user'
    ALTER:  creator TEXT NOT NULL DEFAULT 'user'  (was nullable)
    ORDER:  id, client_id, project_id, name, category_id, parent_id, merged_into,
            description, requirements, acceptance_criteria, action_items,
            summary, design, status, priority, due_date, requester, extra, embedding,
            creator, created_at, updater, updated_at
    """
    with conn.cursor() as cur:
        # Drop FK constraints on mem_ai_work_items that reference planner_tags
        cur.execute("""
            SELECT conname FROM pg_constraint
            WHERE conrelid = 'mem_ai_work_items'::regclass
              AND confrelid = 'planner_tags'::regclass
        """)
        fk_names = [r[0] for r in cur.fetchall()]
        for fk in fk_names:
            cur.execute(f"ALTER TABLE mem_ai_work_items DROP CONSTRAINT IF EXISTS {fk}")

        cur.execute("ALTER TABLE planner_tags RENAME TO _bak_026_planner_tags")
        cur.execute("""
            CREATE TABLE planner_tags (
                id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id           INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
                project_id          INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                name                TEXT        NOT NULL,
                category_id         INT         REFERENCES mng_tags_categories(id),
                parent_id           UUID        REFERENCES planner_tags(id),
                merged_into         UUID        REFERENCES planner_tags(id),
                description         TEXT        NOT NULL DEFAULT '',
                requirements        TEXT        NOT NULL DEFAULT '',
                acceptance_criteria TEXT        NOT NULL DEFAULT '',
                action_items        TEXT        NOT NULL DEFAULT '',
                summary             TEXT        NOT NULL DEFAULT '',
                design              JSONB,
                status              TEXT        NOT NULL DEFAULT 'open',
                priority            SMALLINT    NOT NULL DEFAULT 3,
                due_date            DATE,
                requester           TEXT,
                extra               JSONB       NOT NULL DEFAULT '{}',
                embedding           VECTOR(1536),
                creator             TEXT        NOT NULL DEFAULT 'user',
                created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updater             TEXT        NOT NULL DEFAULT 'user',
                updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(project_id, name, category_id)
            )
        """)
        cur.execute("""
            INSERT INTO planner_tags (
                id, client_id, project_id, name, category_id, parent_id, merged_into,
                description, requirements, acceptance_criteria, action_items,
                summary, design, status, priority, due_date, requester, extra, embedding,
                creator, created_at, updated_at
            )
            SELECT
                id, client_id, project_id, name, category_id, parent_id, merged_into,
                COALESCE(short_desc, ''),
                COALESCE(requirements, ''),
                COALESCE(acceptance_criteria, ''),
                COALESCE(action_items, ''),
                COALESCE(summary, ''),
                design,
                status, priority, due_date, requester, extra, embedding,
                COALESCE(creator, 'user'),
                created_at, updated_at
            FROM _bak_026_planner_tags
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_planner_tags_pid    ON planner_tags(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_planner_tags_parent ON planner_tags(parent_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_planner_tags_cat    ON planner_tags(category_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_planner_tags_project_name ON planner_tags(project_id, name)")
        # Recreate FK constraints pointing to new planner_tags table
        cur.execute("""ALTER TABLE mem_ai_work_items
            ADD CONSTRAINT mem_ai_work_items_tag_id_ai_fkey
            FOREIGN KEY (tag_id_ai) REFERENCES planner_tags(id) ON DELETE SET NULL""")
        cur.execute("""ALTER TABLE mem_ai_work_items
            ADD CONSTRAINT mem_ai_work_items_tag_id_user_fkey
            FOREIGN KEY (tag_id_user) REFERENCES planner_tags(id) ON DELETE SET NULL""")
    conn.commit()
    log.info("m026_planner_tags_cleanup: table recreated — 5 cols dropped, short_desc→description, creator/updater enforced")


def m027_planner_tags_drop_ai_cols(conn) -> None:
    """Drop AI-generated and unused columns from planner_tags.

    summary, design, embedding → move to the future merge-layer table
    extra                      → never used, dead weight
    """
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE planner_tags DROP COLUMN IF EXISTS summary")
        cur.execute("ALTER TABLE planner_tags DROP COLUMN IF EXISTS design")
        cur.execute("ALTER TABLE planner_tags DROP COLUMN IF EXISTS embedding")
        cur.execute("ALTER TABLE planner_tags DROP COLUMN IF EXISTS extra")
    conn.commit()
    log.info("m027_planner_tags_drop_ai_cols: summary/design/embedding/extra dropped")


_DELIVERY_SEED = [
    ("code",                 "python",       "Python",           10),
    ("code",                 "javascript",   "JavaScript",       20),
    ("code",                 "typescript",   "TypeScript",       30),
    ("code",                 "csharp",       "C#",               40),
    ("code",                 "go",           "Go",               50),
    ("code",                 "rust",         "Rust",             60),
    ("code",                 "java",         "Java",             70),
    ("code",                 "bash",         "Shell / Bash",     80),
    ("code",                 "sql",          "SQL",              90),
    ("document",             "markdown",     "Markdown",         10),
    ("document",             "word",         "Word Document",    20),
    ("document",             "pdf",          "PDF",              30),
    ("document",             "html",         "HTML Page",        40),
    ("architecture_design",  "visio",        "Visio",            10),
    ("architecture_design",  "drawio",       "Draw.io",          20),
    ("architecture_design",  "mermaid",      "Mermaid Diagram",  30),
    ("architecture_design",  "excalidraw",   "Excalidraw",       40),
    ("presentation",         "powerpoint",   "PowerPoint",       10),
    ("presentation",         "google_slides","Google Slides",    20),
    ("presentation",         "keynote",      "Keynote",          30),
]


def m028_add_deliveries(conn) -> None:
    """Add mng_deliveries lookup table and planner_tags.deliveries JSONB column.

    mng_deliveries: global admin-editable list of delivery output types
    (code, document, architecture_design, presentation) seeded with 20 rows.
    planner_tags.deliveries: JSONB array of selected delivery objects per tag.
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mng_deliveries (
                id          SERIAL  PRIMARY KEY,
                category    TEXT    NOT NULL,
                type        TEXT    NOT NULL,
                label       TEXT    NOT NULL,
                sort_order  INT     NOT NULL DEFAULT 0,
                UNIQUE(category, type)
            )
        """)
        cur.executemany(
            """INSERT INTO mng_deliveries (category, type, label, sort_order)
               VALUES (%s, %s, %s, %s)
               ON CONFLICT (category, type) DO NOTHING""",
            _DELIVERY_SEED,
        )
        cur.execute(
            "ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS "
            "deliveries JSONB NOT NULL DEFAULT '[]'"
        )
    conn.commit()
    log.info("m028_add_deliveries: mng_deliveries created + seeded (20 rows); planner_tags.deliveries added")


def m029_feature_snapshot(conn) -> None:
    """Create mem_ai_feature_snapshot: per-tag, per-use-case feature snapshot rows.

    One row per (tag_id, use_case_num, version).  version='ai' is overwritten on each
    snapshot run; version='user' is promoted from AI and never overwritten by AI.
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mem_ai_feature_snapshot (
                id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id                   INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
                project_id                  INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                tag_id                      UUID        NOT NULL REFERENCES planner_tags(id) ON DELETE CASCADE,
                use_case_num                INT         NOT NULL,
                name                        TEXT        NOT NULL DEFAULT '',
                category                    TEXT        NOT NULL DEFAULT '',
                status                      TEXT        NOT NULL DEFAULT 'open',
                priority                    SMALLINT    NOT NULL DEFAULT 3,
                due_date                    DATE,
                summary                     TEXT        NOT NULL DEFAULT '',
                use_case_summary            TEXT        NOT NULL DEFAULT '',
                use_case_type               TEXT        NOT NULL DEFAULT 'feature',
                use_case_delivery_category  TEXT        NOT NULL DEFAULT '',
                use_case_delivery_type      TEXT        NOT NULL DEFAULT '',
                related_work_items          JSONB       NOT NULL DEFAULT '[]',
                requirements                JSONB       NOT NULL DEFAULT '[]',
                action_items                JSONB       NOT NULL DEFAULT '[]',
                version                     TEXT        NOT NULL DEFAULT 'ai',
                created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE(project_id, tag_id, use_case_num, version)
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mafs_project ON mem_ai_feature_snapshot(project_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mafs_tag ON mem_ai_feature_snapshot(tag_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mafs_tag_version ON mem_ai_feature_snapshot(tag_id, version)"
        )
    conn.commit()
    log.info("m029_feature_snapshot: mem_ai_feature_snapshot table + 3 indexes created")


def m030_pipeline_runs(conn) -> None:
    """Create mem_pipeline_runs table for background task observability.

    Tracks every background pipeline invocation (commit_embed, commit_store,
    commit_code_extract, session_summary, tag_match, work_item_embed) with status,
    timing, and error message. Powers GET /memory/{project}/pipeline-status.

    Also adds snapshot_id + use_case_num to pr_graph_runs for workflow-from-snapshot
    triggering (POST /tags/{id}/snapshot/{n}/run-workflow).
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mem_pipeline_runs (
                id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id   INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                pipeline     TEXT        NOT NULL,
                source_id    TEXT        NOT NULL DEFAULT '',
                status       TEXT        NOT NULL DEFAULT 'running',
                items_in     INT         NOT NULL DEFAULT 0,
                items_out    INT         NOT NULL DEFAULT 0,
                error_msg    TEXT,
                duration_ms  INT,
                started_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                finished_at  TIMESTAMPTZ
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mpr_project_started "
            "ON mem_pipeline_runs(project_id, started_at DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mpr_status "
            "ON mem_pipeline_runs(status) WHERE status = 'running'"
        )
        # Add snapshot_id and use_case_num to pr_graph_runs
        cur.execute(
            "ALTER TABLE pr_graph_runs ADD COLUMN IF NOT EXISTS snapshot_id UUID "
            "REFERENCES mem_ai_feature_snapshot(id) ON DELETE SET NULL"
        )
        cur.execute(
            "ALTER TABLE pr_graph_runs ADD COLUMN IF NOT EXISTS use_case_num INT"
        )
    conn.commit()
    log.info("m030_pipeline_runs: mem_pipeline_runs table + pr_graph_runs new cols created")


def m031_commits_cleanup(conn) -> None:
    """Simplify mem_mrr_commits: drop tags_ai + exec_llm, rename commit_short_hash → commit_hash_short.

    tags_ai was used to store AI analysis and detected languages.  That data is now
    fully covered by mem_mrr_commits_code (one row per symbol per commit) and the
    mem_ai_events commit digest summary — no need to duplicate it here.

    exec_llm tracked whether process_commit() had run; event_id IS NULL is the
    cleaner sentinel (event_id is set by process_commit() on completion).

    commit_short_hash is renamed commit_hash_short to follow consistent naming.
    """
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE mem_mrr_commits DROP COLUMN IF EXISTS tags_ai")
        cur.execute("ALTER TABLE mem_mrr_commits DROP COLUMN IF EXISTS exec_llm")
        cur.execute(
            "ALTER TABLE mem_mrr_commits RENAME COLUMN commit_short_hash TO commit_hash_short"
        )
    conn.commit()
    log.info("m031_commits_cleanup: dropped tags_ai, exec_llm; renamed commit_short_hash → commit_hash_short")


def m032_events_and_prompts_event_id(conn) -> None:
    """Add event_id to mem_mrr_prompts (back-propagation for prompt batch digest).

    Column reordering was removed — it requires a full table recreation which
    consumes double the disk space on Railway. Only the functionally necessary
    new column is added here.
    """
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE mem_mrr_prompts ADD COLUMN IF NOT EXISTS event_id UUID")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mmrr_p_event "
            "ON mem_mrr_prompts(event_id) WHERE event_id IS NOT NULL"
        )
    conn.commit()
    log.info("m032: event_id added to mem_mrr_prompts")


def m033_reorder_mem_mrr_commits(conn) -> None:
    """No-op: mem_mrr_commits column reorder was skipped (cosmetic, no new columns).

    Column reordering requires a full table recreation which doubles disk usage.
    The existing column order is functionally correct — all referenced columns exist.
    """
    conn.commit()
    log.info("m033: no-op (mem_mrr_commits column reorder skipped — cosmetic only)")


def m034_reorder_mem_ai_events(conn) -> None:
    """Add event_cnt to mem_ai_events (lightweight ADD COLUMN, no table recreation).

    Column reordering was removed — it requires double disk space on Railway.
    Only the functionally necessary new column is added here.

    event_cnt: how many mirror rows this event aggregates
    (e.g. 5 for a prompt_batch of 5 prompts, N for N commits in a tag group).
    """
    with conn.cursor() as cur:
        cur.execute(
            "ALTER TABLE mem_ai_events ADD COLUMN IF NOT EXISTS event_cnt INT NOT NULL DEFAULT 0"
        )
    conn.commit()
    log.info("m034: event_cnt added to mem_ai_events")


def m035_reorder_mem_mrr_commits(conn) -> None:
    """Reorder mem_mrr_commits columns to match db_schema.sql and drop the _old backup.

    New order:
        commit_hash, commit_hash_short (GENERATED), client_id, project_id,
        commit_msg, summary, diff_summary, tags, prompt_id, event_id,
        session_id, author, author_email, llm, created_at, committed_at

    m033 was a no-op (skipped due to disk space). This migration runs the same
    reorder now that VACUUM FULL has freed space, and drops _old at the end.
    """
    with conn.cursor() as cur:
        # 1. Drop any leftover _old from a previous attempt
        cur.execute("DROP TABLE IF EXISTS mem_mrr_commits_old CASCADE")

        # 2. Drop FK on mem_mrr_commits_code → mem_mrr_commits
        cur.execute("""
            SELECT conname FROM pg_constraint
            WHERE conrelid  = 'mem_mrr_commits_code'::regclass
              AND confrelid = 'mem_mrr_commits'::regclass
        """)
        for (fk_name,) in cur.fetchall():
            cur.execute(f'ALTER TABLE mem_mrr_commits_code DROP CONSTRAINT IF EXISTS "{fk_name}"')

        # 3. Rename current → _old
        cur.execute("ALTER TABLE mem_mrr_commits RENAME TO mem_mrr_commits_old")

        # 4. Create new table (exact column order from db_schema.sql)
        cur.execute("""
            CREATE TABLE mem_mrr_commits (
                commit_hash       VARCHAR(64)  PRIMARY KEY,
                commit_hash_short VARCHAR(8)   GENERATED ALWAYS AS (LEFT(commit_hash, 8)) STORED,
                client_id         INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
                project_id        INT          NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                commit_msg        TEXT         NOT NULL DEFAULT '',
                summary           TEXT         NOT NULL DEFAULT '',
                diff_summary      TEXT         NOT NULL DEFAULT '',
                tags              JSONB        NOT NULL DEFAULT '{}',
                prompt_id         UUID         REFERENCES mem_mrr_prompts(id) ON DELETE SET NULL,
                event_id          UUID,
                session_id        VARCHAR(255),
                author            TEXT         NOT NULL DEFAULT '',
                author_email      TEXT         NOT NULL DEFAULT '',
                llm               TEXT,
                created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                committed_at      TIMESTAMPTZ
            )
        """)

        # 5. Copy data (commit_hash_short is GENERATED — omit from list)
        _cols = (
            "commit_hash, client_id, project_id, commit_msg, summary, diff_summary, "
            "tags, prompt_id, event_id, session_id, author, author_email, llm, "
            "created_at, committed_at"
        )
        cur.execute(
            f"INSERT INTO mem_mrr_commits ({_cols}) SELECT {_cols} FROM mem_mrr_commits_old"
        )

        # 6. Recreate indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_c_pid            ON mem_mrr_commits(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_c_comm           ON mem_mrr_commits(committed_at DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_c_session        ON mem_mrr_commits(session_id) WHERE session_id IS NOT NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_c_prompt         ON mem_mrr_commits(prompt_id) WHERE prompt_id IS NOT NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_c_tags           ON mem_mrr_commits USING gin(tags)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_c_event          ON mem_mrr_commits(event_id) WHERE event_id IS NOT NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrrc_project_session ON mem_mrr_commits(project_id, session_id) WHERE session_id IS NOT NULL")

        # 7. Restore FK on mem_mrr_commits_code
        cur.execute("""
            ALTER TABLE mem_mrr_commits_code
            ADD CONSTRAINT mem_mrr_commits_code_commit_hash_fkey
            FOREIGN KEY (commit_hash) REFERENCES mem_mrr_commits(commit_hash) ON DELETE CASCADE
        """)

        # 8. Drop backup table (saves ~1 MB; data is safe in new table)
        cur.execute("DROP TABLE mem_mrr_commits_old CASCADE")

    conn.commit()
    log.info("m035: mem_mrr_commits reordered and _old dropped")


def m036_reorder_mem_ai_events(conn) -> None:
    """Reorder mem_ai_events columns to match db_schema.sql and drop the _old backup.

    New order:
        id, client_id, project_id, event_type, event_cnt, source_id,
        work_item_id, session_id, chunk, chunk_type, content, summary,
        action_items, tags, importance, created_at, processed_at, embedding

    m032/m034 added the new columns (event_id on prompts, event_cnt) but skipped
    the reorder. This migration applies the reorder and drops _old to save space.
    The _old backup is dropped immediately — 75 MB reclaimed on Railway.
    """
    with conn.cursor() as cur:
        # 1. Drop any leftover _old from a previous attempt
        cur.execute("DROP TABLE IF EXISTS mem_ai_events_old CASCADE")

        # 2. Rename current → _old
        cur.execute("ALTER TABLE mem_ai_events RENAME TO mem_ai_events_old")

        # 3. Create new table (exact column order from db_schema.sql)
        cur.execute("""
            CREATE TABLE mem_ai_events (
                id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id    INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
                project_id   INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                event_type   TEXT        NOT NULL,
                event_cnt    INT         NOT NULL DEFAULT 0,
                source_id    TEXT        NOT NULL,
                work_item_id UUID,
                session_id   TEXT,
                chunk        INT         NOT NULL DEFAULT 0,
                chunk_type   TEXT        NOT NULL DEFAULT 'full',
                content      TEXT        NOT NULL DEFAULT '',
                summary      TEXT,
                action_items TEXT        NOT NULL DEFAULT '',
                tags         JSONB       NOT NULL DEFAULT '{}',
                importance   SMALLINT    NOT NULL DEFAULT 1,
                created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                processed_at TIMESTAMPTZ,
                embedding    VECTOR(1536),
                UNIQUE(project_id, event_type, source_id, chunk)
            )
        """)

        # 4. Copy all data (event_cnt already exists in _old from m034)
        _cols = (
            "id, client_id, project_id, event_type, event_cnt, source_id, "
            "work_item_id, session_id, chunk, chunk_type, content, summary, "
            "action_items, tags, importance, created_at, processed_at, embedding"
        )
        cur.execute(
            f"INSERT INTO mem_ai_events ({_cols}) SELECT {_cols} FROM mem_ai_events_old"
        )

        # 5. Recreate indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_pid             ON mem_ai_events(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_session         ON mem_ai_events(session_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_type            ON mem_ai_events(event_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_pending         ON mem_ai_events(processed_at) WHERE processed_at IS NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_tags            ON mem_ai_events USING gin(tags)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_embed           ON mem_ai_events USING ivfflat(embedding vector_cosine_ops) WHERE embedding IS NOT NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_project_session ON mem_ai_events(project_id, session_id) WHERE session_id IS NOT NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_project_etype   ON mem_ai_events(project_id, event_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mem_ai_events_wi    ON mem_ai_events(work_item_id) WHERE work_item_id IS NOT NULL")

        # 6. Drop backup table (reclaims ~75 MB on Railway)
        cur.execute("DROP TABLE mem_ai_events_old CASCADE")

    conn.commit()
    log.info("m036: mem_ai_events reordered and _old dropped (~75 MB reclaimed)")


def m037_drop_events_importance(conn) -> None:
    """Drop importance column from mem_ai_events.

    importance is more meaningful on mem_ai_work_items where it drives prioritisation.
    For events, pure recency ordering (EXP(-0.01 * age_days)) is sufficient.
    """
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS importance")
    conn.commit()
    log.info("m037: importance dropped from mem_ai_events")


def m038_drop_commits_code_embedding(conn) -> None:
    """Drop unused embedding column from mem_mrr_commits_code.

    The embedding was written by memory_code_parser.py but never queried.
    All semantic search goes through mem_ai_events.embedding.
    Frees ~4.5 MB (88% of the table).
    """
    with conn.cursor() as cur:
        cur.execute("DROP INDEX IF EXISTS idx_mmc_code_embed")
        cur.execute("ALTER TABLE mem_mrr_commits_code DROP COLUMN IF EXISTS embedding")
    conn.commit()
    log.info("m038: embedding dropped from mem_mrr_commits_code (~4.5 MB freed)")


def m039_reorder_mem_mrr_prompts(conn) -> None:
    """Reorder mem_mrr_prompts columns — move event_id next to project_id.

    New order:
        id, client_id, project_id, event_id, session_id, source_id,
        prompt, response, tags, created_at
    """
    with conn.cursor() as cur:
        # 1. Drop any leftover _old from a previous attempt
        cur.execute("DROP TABLE IF EXISTS mem_mrr_prompts_old CASCADE")

        # 2. Drop FK on mem_mrr_commits → mem_mrr_prompts
        cur.execute("""
            SELECT conname FROM pg_constraint
            WHERE conrelid  = 'mem_mrr_commits'::regclass
              AND confrelid = 'mem_mrr_prompts'::regclass
        """)
        for (fk_name,) in cur.fetchall():
            cur.execute(f'ALTER TABLE mem_mrr_commits DROP CONSTRAINT IF EXISTS "{fk_name}"')

        # 3. Rename current → _old
        cur.execute("ALTER TABLE mem_mrr_prompts RENAME TO mem_mrr_prompts_old")

        # 4. Create new table with target column order
        cur.execute("""
            CREATE TABLE mem_mrr_prompts (
                id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id  INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
                project_id INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                event_id   UUID,
                session_id TEXT,
                source_id  TEXT,
                prompt     TEXT        NOT NULL DEFAULT '',
                response   TEXT        NOT NULL DEFAULT '',
                tags       JSONB       NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # 5. Copy data
        _cols = "id, client_id, project_id, event_id, session_id, source_id, prompt, response, tags, created_at"
        cur.execute(f"INSERT INTO mem_mrr_prompts ({_cols}) SELECT {_cols} FROM mem_mrr_prompts_old")

        # 6. Recreate indexes
        cur.execute("CREATE INDEX        IF NOT EXISTS idx_mmrr_p_pid     ON mem_mrr_prompts(project_id)")
        cur.execute("CREATE INDEX        IF NOT EXISTS idx_mmrr_p_session ON mem_mrr_prompts(session_id) WHERE session_id IS NOT NULL")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mmrr_p_source  ON mem_mrr_prompts(project_id, source_id) WHERE source_id IS NOT NULL")
        cur.execute("CREATE INDEX        IF NOT EXISTS idx_mmrr_p_created ON mem_mrr_prompts(created_at DESC)")
        cur.execute("CREATE INDEX        IF NOT EXISTS idx_mmrr_p_tags    ON mem_mrr_prompts USING gin(tags)")
        cur.execute("CREATE INDEX        IF NOT EXISTS idx_mmrr_p_event   ON mem_mrr_prompts(event_id) WHERE event_id IS NOT NULL")

        # 7. Restore FK on mem_mrr_commits
        cur.execute("""
            ALTER TABLE mem_mrr_commits
            ADD CONSTRAINT mem_mrr_commits_prompt_id_fkey
            FOREIGN KEY (prompt_id) REFERENCES mem_mrr_prompts(id) ON DELETE SET NULL
        """)

        # 8. Drop backup
        cur.execute("DROP TABLE mem_mrr_prompts_old CASCADE")

    conn.commit()
    log.info("m039: mem_mrr_prompts reordered (event_id moved after project_id) and _old dropped")


def m041_drop_diff_file_chunks(conn) -> None:
    """Delete all diff_file chunk rows from mem_ai_events.

    The old process_commit() created 1 Haiku summary row (chunk=0, chunk_type='summary')
    PLUS N raw diff-text chunks (chunk=1..N, chunk_type='diff_file') — one per changed file.
    These diff_file rows were never useful for display and are noisy for semantic search.
    Per-symbol data lives in mem_mrr_commits_code; the summary (chunk=0) is kept.

    The new process_commit_batch() never creates diff_file chunks, and the loop in
    process_commit() was removed. This migration cleans up all 2105 legacy rows.
    """
    with conn.cursor() as cur:
        cur.execute("DELETE FROM mem_ai_events WHERE chunk_type = 'diff_file'")
        deleted = cur.rowcount
    conn.commit()
    log.info(f"m041: deleted {deleted} diff_file chunk rows from mem_ai_events")


def m040_backfill_event_cnt_and_tags(conn) -> None:
    """Backfill event_cnt and tags on existing mem_ai_events rows.

    event_cnt was added (m034) with DEFAULT 0 — old rows were never updated.
    This migration sets the correct count:
      - prompt_batch (chunk=0): count of mem_mrr_prompts linked via event_id
      - commit (chunk=0, hash source_id): 1 per commit
      - commit diff_file chunks (chunk>0): 1 (sub-slice of one commit)
      - session_summary / memory_item / role: 1
      - commit batch events (batch_ prefix): already correct — skip

    Tags backfill for prompt_batch events whose tags are empty:
      source_id = last prompt UUID in the group, so we can look up that prompt's
      user-intent tags and copy them to the event.
    """
    with conn.cursor() as cur:
        # 1. prompt_batch chunk=0: count linked prompts (if any back-propagated)
        cur.execute("""
            UPDATE mem_ai_events mae
            SET event_cnt = sub.cnt
            FROM (
                SELECT p.event_id, COUNT(*) AS cnt
                FROM mem_mrr_prompts p
                WHERE p.event_id IS NOT NULL
                GROUP BY p.event_id
            ) sub
            WHERE mae.id = sub.event_id
              AND mae.event_type = 'prompt_batch'
              AND mae.chunk = 0
              AND mae.event_cnt = 0
        """)
        linked_pb = cur.rowcount

        # 2. prompt_batch chunk=0 still at 0 (old events with no back-propagation): set to 1
        cur.execute("""
            UPDATE mem_ai_events
            SET event_cnt = 1
            WHERE event_type = 'prompt_batch' AND chunk = 0 AND event_cnt = 0
        """)
        unlinked_pb = cur.rowcount

        # 3. commit chunk=0 with hash source_id (40 hex chars): set to 1
        cur.execute("""
            UPDATE mem_ai_events
            SET event_cnt = 1
            WHERE event_type = 'commit'
              AND chunk = 0
              AND source_id NOT LIKE 'batch_%'
              AND event_cnt = 0
        """)
        single_commits = cur.rowcount

        # 4. commit diff_file chunks (chunk>0): set to 1
        cur.execute("""
            UPDATE mem_ai_events
            SET event_cnt = 1
            WHERE event_type = 'commit' AND chunk > 0 AND event_cnt = 0
        """)
        diff_chunks = cur.rowcount

        # 5. session_summary / memory_item / role: set to 1
        cur.execute("""
            UPDATE mem_ai_events
            SET event_cnt = 1
            WHERE event_type IN ('session_summary', 'memory_item', 'role', 'item', 'message')
              AND event_cnt = 0
        """)
        other_types = cur.rowcount

        # 6. Tags backfill for prompt_batch events with empty tags:
        #    source_id = last prompt UUID → copy user-intent keys from that prompt
        cur.execute("""
            UPDATE mem_ai_events mae
            SET tags = (
                SELECT COALESCE(
                    jsonb_object_agg(kv.key, kv.value)
                      FILTER (WHERE kv.key = ANY(ARRAY['phase','feature','bug','source'])),
                    '{}'::jsonb
                )
                FROM jsonb_each(p.tags) AS kv
            )
            FROM mem_mrr_prompts p
            WHERE mae.event_type = 'prompt_batch'
              AND mae.chunk = 0
              AND mae.tags = '{}'::jsonb
              AND mae.source_id = p.id::text
              AND p.tags != '{}'::jsonb
        """)
        tags_backfilled = cur.rowcount

    conn.commit()
    log.info(
        f"m040: event_cnt backfilled — "
        f"prompt_batch linked={linked_pb} unlinked={unlinked_pb} "
        f"single_commits={single_commits} diff_chunks={diff_chunks} other={other_types}; "
        f"tags backfilled for {tags_backfilled} prompt_batch events"
    )


def m046_reorder_work_items(conn) -> None:
    """Reorder columns in mem_ai_work_items for logical grouping.

    New order: id, client_id, project_id, seq_num, category_ai, name_ai,
      summary_ai, acceptance_criteria_ai, action_items_ai, score_ai,
      tags, tags_ai, tag_id_ai, tag_id_user, status_user,
      merged_into, start_date, created_at, updated_at, embedding

    (desc_ai was already dropped in m044)
    """
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE mem_ai_work_items RENAME TO _bak_046_mem_ai_work_items")
        cur.execute("""
            CREATE TABLE mem_ai_work_items (
                id                     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id              INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
                project_id             INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                seq_num                INT,
                category_ai            TEXT        NOT NULL,
                name_ai                TEXT        NOT NULL,
                summary_ai             TEXT        NOT NULL DEFAULT '',
                acceptance_criteria_ai TEXT        NOT NULL DEFAULT '',
                action_items_ai        TEXT        NOT NULL DEFAULT '',
                score_ai               SMALLINT    NOT NULL DEFAULT 0,
                tags                   JSONB       NOT NULL DEFAULT '{}',
                tags_ai                JSONB       NOT NULL DEFAULT '{}',
                tag_id_ai              UUID        REFERENCES planner_tags(id),
                tag_id_user            UUID        REFERENCES planner_tags(id),
                status_user            VARCHAR(20) NOT NULL DEFAULT 'active',
                merged_into            UUID,
                start_date             TIMESTAMPTZ,
                created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                embedding              VECTOR(1536),
                UNIQUE(project_id, category_ai, name_ai)
            )
        """)
        cur.execute("""
            INSERT INTO mem_ai_work_items
              (id, client_id, project_id, seq_num, category_ai, name_ai,
               summary_ai, acceptance_criteria_ai, action_items_ai, score_ai,
               tags, tags_ai, tag_id_ai, tag_id_user, status_user,
               merged_into, start_date, created_at, updated_at, embedding)
            SELECT
              id, client_id, project_id, seq_num, category_ai, name_ai,
              summary_ai, acceptance_criteria_ai, action_items_ai, score_ai,
              tags, tags_ai, tag_id_ai, tag_id_user, status_user,
              merged_into, start_date, created_at, updated_at, embedding
            FROM _bak_046_mem_ai_work_items
        """)
        # Add self-referential FK after data is fully loaded
        cur.execute("""
            ALTER TABLE mem_ai_work_items
            ADD CONSTRAINT fk_wi_merged_into
            FOREIGN KEY (merged_into) REFERENCES mem_ai_work_items(id)
            ON DELETE SET NULL NOT VALID
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_pid   ON mem_ai_work_items(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_cat   ON mem_ai_work_items(category_ai)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_suser ON mem_ai_work_items(status_user)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_seq   ON mem_ai_work_items(project_id, seq_num) WHERE seq_num IS NOT NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_embed ON mem_ai_work_items USING ivfflat(embedding vector_cosine_ops) WHERE embedding IS NOT NULL")
    conn.commit()


def m045_add_score_ai(conn) -> None:
    """Add score_ai (0-5) to mem_ai_work_items.

    AI-calculated completion score written by promote_work_item():
      0 = not started  1 = early/unclear  2 = in progress, blockers
      3 = good progress  4 = mostly done  5 = acceptance criteria met
    """
    with conn.cursor() as cur:
        cur.execute(
            "ALTER TABLE mem_ai_work_items "
            "ADD COLUMN IF NOT EXISTS score_ai SMALLINT NOT NULL DEFAULT 0"
        )
    conn.commit()


def m044_drop_desc_ai(conn) -> None:
    """Drop desc_ai from mem_ai_work_items — merged into summary_ai.

    summary_ai now covers both definition (what the item is) and
    progress (what was done, what remains), written by promote_work_item().
    The 3 AI text columns that remain are: summary_ai, action_items_ai,
    acceptance_criteria_ai.
    """
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS desc_ai")
    conn.commit()


def m043_drop_status_ai_code_summary(conn) -> None:
    """Drop status_ai and code_summary from mem_ai_work_items.

    status_ai: AI-predicted status — stale, noisy, never used for decisions.
    code_summary TEXT: structured version lives in tags_ai.code_summary JSONB;
                       feature-level code context belongs on planner_tags snapshot.
    """
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS status_ai")
        cur.execute("ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS code_summary")
    conn.commit()


def m042_drop_source_event_id(conn) -> None:
    """Drop redundant source_event_id from mem_ai_work_items.

    The one-to-many relationship work_item → events is already captured by
    mem_ai_events.work_item_id FK.  source_event_id was only ever used to
    retrieve session_id, which can now be read directly from the linked events.
    """
    with conn.cursor() as cur:
        cur.execute(
            "ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS source_event_id"
        )
    conn.commit()


def m047_events_is_system(conn) -> None:
    """Add is_system BOOLEAN column to mem_ai_events.

    System events (e.g. PROJECT.md / CLAUDE.md / MEMORY.md auto-updates) are
    excluded from work-item extraction to avoid noise. Flagged at insert time
    by process_commit_batch() when all changed files are system-generated.
    """
    with conn.cursor() as cur:
        cur.execute(
            "ALTER TABLE mem_ai_events "
            "ADD COLUMN IF NOT EXISTS is_system BOOLEAN NOT NULL DEFAULT FALSE"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mae_system "
            "ON mem_ai_events(is_system) WHERE is_system = TRUE"
        )
    conn.commit()


def m048_user_id_mirror_tables(conn) -> None:
    """Add user_id FK to mem_mrr_* and planner_tags; seed default admin user.

    Adds user attribution to all Layer-1 mirror tables so per-user memory
    consumption can be tracked. The seeded admin user (UUID all-zeros-1) is the
    fallback for all DEV_MODE and hook-originated rows.
    """
    _ADMIN_ID = "00000000-0000-0000-0000-000000000001"
    _TABLES = [
        "mem_mrr_prompts",
        "mem_mrr_commits",
        "mem_mrr_items",
        "mem_mrr_messages",
        "planner_tags",
    ]
    with conn.cursor() as cur:
        # 1. Seed default admin user (idempotent)
        cur.execute("""
            INSERT INTO mng_users (id, client_id, email, password_hash, is_admin, role)
            VALUES (%s, 1, 'admin@local', '$2b$12$placeholder_hash_do_not_use', true, 'admin')
            ON CONFLICT DO NOTHING
        """, (_ADMIN_ID,))

        # 2. Add user_id column to each table
        for table in _TABLES:
            cur.execute(f"""
                ALTER TABLE {table}
                ADD COLUMN IF NOT EXISTS user_id VARCHAR(36)
                REFERENCES mng_users(id) ON DELETE SET NULL
            """)
            short = table[:20]
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{short}_uid ON {table}(user_id)"
            )

        # 3. Backfill existing rows with admin user
        for table in _TABLES:
            cur.execute(
                f"UPDATE {table} SET user_id=%s WHERE user_id IS NULL",
                (_ADMIN_ID,),
            )
    conn.commit()
    log.info("m048_user_id_mirror_tables: user_id added to 5 tables; admin user seeded")


def m049_work_item_quality_gate(conn) -> None:
    """Add quality gate columns to mem_ai_work_items.

    - quality_stage:  'staging' (needs review) | 'approved' | 'rejected'
    - quality_issues: JSONB dict of per-check failure reasons
    - dedup_status:   'new' | 'merged' (absorbed duplicate) | 'flagged' (similarity > 0.88)
    Existing items are backfilled as approved/new (pre-existing = already extracted).
    """
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE mem_ai_work_items
              ADD COLUMN IF NOT EXISTS quality_stage  VARCHAR(20) NOT NULL DEFAULT 'staging',
              ADD COLUMN IF NOT EXISTS quality_issues JSONB       NOT NULL DEFAULT '{}',
              ADD COLUMN IF NOT EXISTS dedup_status   VARCHAR(20) NOT NULL DEFAULT 'new'
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_wi_quality "
            "ON mem_ai_work_items(project_id, quality_stage)"
        )
        # Backfill existing items as approved (pre-existing = already extracted)
        cur.execute(
            "UPDATE mem_ai_work_items SET quality_stage='approved', dedup_status='new' "
            "WHERE quality_stage='staging'"
        )
    conn.commit()
    log.info("m049_work_item_quality_gate: quality_stage, quality_issues, dedup_status added")


def m050_prompts_source_id_index(conn) -> None:
    """Add missing unique partial index on mem_mrr_prompts(project_id, source_id).

    Required for ON CONFLICT (project_id, source_id) WHERE source_id IS NOT NULL
    in the hook-log INSERT. Without it every hook-log POST returns a DB error and
    prompts are silently dropped, causing history to stop updating.
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_mmrr_p_source
            ON mem_mrr_prompts(project_id, source_id)
            WHERE source_id IS NOT NULL
        """)
        # Also add supporting indexes if missing
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_p_pid     ON mem_mrr_prompts(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_p_session ON mem_mrr_prompts(session_id) WHERE session_id IS NOT NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_p_created ON mem_mrr_prompts(created_at DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_p_tags    ON mem_mrr_prompts USING gin(tags)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_p_event   ON mem_mrr_prompts(event_id)   WHERE event_id IS NOT NULL")
    conn.commit()
    log.info("m050_prompts_source_id_index: unique index idx_mmrr_p_source created")


def m051_schema_refactor_user_id_updated_at(conn) -> None:
    """Major schema refactor: INT user IDs, updated_at on all tables, event column renames.

    Changes applied:
      1. mng_users.id: VARCHAR(36) → SERIAL INT; old UUID kept as uuid_id VARCHAR(36) UNIQUE.
         mng_users: add updated_at TIMESTAMPTZ.
      2. Dependent tables (mng_usage_logs, mng_transactions, mng_user_api_keys,
         mng_user_projects): user_id VARCHAR(36) → INT FK to new mng_users.id.
      3. mng_clients: add updated_at TIMESTAMPTZ.
      4. Mirror tables (mem_mrr_prompts, mem_mrr_commits, mem_mrr_commits_code,
         mem_mrr_items, mem_mrr_messages): add user_id INT NULL + updated_at.
      5. mem_ai_events: rename is_system → event_system; rename processed_at → updated_at.
         Drop old index idx_mae_system, recreate as idx_mae_event_system.
         Drop old index idx_mae_pending (was on processed_at), recreate on updated_at.
      6. mem_ai_project_facts: add created_at + updated_at.
      7. mem_pipeline_runs: add user_id INT NULL + updated_at.
      8. Create set_updated_at() trigger function and triggers on all tables that have
         updated_at (excluding those that already had it before this migration).
    """
    with conn.cursor() as cur:

        # ── Step 1: Add new SERIAL column to mng_users ────────────────────────
        cur.execute("ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS new_id SERIAL")

        # ── Step 2: Drop ALL FK constraints referencing mng_users (dynamic) ────
        # Covers named FKs on mng_user_api_keys, mng_user_projects, mng_usage_logs,
        # mng_transactions, plus any mirror-table FKs added by prior migrations.
        cur.execute("""
            DO $$ DECLARE r record;
            BEGIN
                FOR r IN
                    SELECT c.conname, c.conrelid::regclass::text AS tname
                    FROM pg_constraint c
                    WHERE c.confrelid = 'mng_users'::regclass AND c.contype = 'f'
                LOOP
                    EXECUTE 'ALTER TABLE ' || r.tname ||
                            ' DROP CONSTRAINT ' || quote_ident(r.conname);
                END LOOP;
            END $$
        """)

        # ── Step 3: Swap PK on mng_users: uuid → id SERIAL ───────────────────
        # Drop existing PK dynamically — constraint name may differ from 'mng_users_pkey'
        cur.execute("""
            DO $$ DECLARE _c text;
            BEGIN
                SELECT conname INTO _c FROM pg_constraint
                WHERE conrelid = 'mng_users'::regclass AND contype = 'p';
                IF _c IS NOT NULL THEN
                    EXECUTE 'ALTER TABLE mng_users DROP CONSTRAINT ' || quote_ident(_c);
                END IF;
            END $$
        """)
        cur.execute("ALTER TABLE mng_users RENAME COLUMN id TO uuid_id")
        cur.execute("ALTER TABLE mng_users RENAME COLUMN new_id TO id")
        cur.execute("ALTER TABLE mng_users ADD PRIMARY KEY (id)")
        cur.execute("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conrelid = 'mng_users'::regclass
                      AND conname = 'mng_users_uuid_id_unique'
                ) THEN
                    ALTER TABLE mng_users
                    ADD CONSTRAINT mng_users_uuid_id_unique UNIQUE (uuid_id);
                END IF;
            END $$
        """)

        # Add updated_at to mng_users
        cur.execute("""
            ALTER TABLE mng_users
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)

        # ── Step 4a: Convert mng_usage_logs.user_id VARCHAR → INT ─────────────
        cur.execute("ALTER TABLE mng_usage_logs ADD COLUMN IF NOT EXISTS user_id_new INT")
        cur.execute("""
            UPDATE mng_usage_logs l
            SET user_id_new = u.id
            FROM mng_users u
            WHERE u.uuid_id = l.user_id
        """)
        cur.execute("ALTER TABLE mng_usage_logs DROP COLUMN IF EXISTS user_id")
        cur.execute("ALTER TABLE mng_usage_logs RENAME COLUMN user_id_new TO user_id")
        cur.execute("""
            ALTER TABLE mng_usage_logs
            ADD CONSTRAINT mng_usage_logs_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES mng_users(id) ON DELETE SET NULL
        """)

        # ── Step 4b: Convert mng_transactions.user_id VARCHAR → INT ──────────
        cur.execute("ALTER TABLE mng_transactions ADD COLUMN IF NOT EXISTS user_id_new INT")
        cur.execute("""
            UPDATE mng_transactions t
            SET user_id_new = u.id
            FROM mng_users u
            WHERE u.uuid_id = t.user_id
        """)
        cur.execute("ALTER TABLE mng_transactions DROP COLUMN IF EXISTS user_id")
        cur.execute("ALTER TABLE mng_transactions RENAME COLUMN user_id_new TO user_id")
        cur.execute("""
            ALTER TABLE mng_transactions
            ADD CONSTRAINT mng_transactions_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES mng_users(id) ON DELETE SET NULL
        """)

        # ── Step 4c: Convert mng_user_api_keys.user_id VARCHAR → INT ─────────
        # Drop any UNIQUE constraint on (user_id, provider) — name may vary
        cur.execute("""
            DO $$ DECLARE _c text;
            BEGIN
                SELECT conname INTO _c FROM pg_constraint
                WHERE conrelid = 'mng_user_api_keys'::regclass
                  AND contype = 'u'
                LIMIT 1;
                IF _c IS NOT NULL THEN
                    EXECUTE 'ALTER TABLE mng_user_api_keys DROP CONSTRAINT ' || quote_ident(_c);
                END IF;
            END $$
        """)
        cur.execute("ALTER TABLE mng_user_api_keys ADD COLUMN IF NOT EXISTS user_id_new INT")
        cur.execute("""
            UPDATE mng_user_api_keys k
            SET user_id_new = u.id
            FROM mng_users u
            WHERE u.uuid_id = k.user_id
        """)
        cur.execute("ALTER TABLE mng_user_api_keys ALTER COLUMN user_id_new SET NOT NULL")
        cur.execute("ALTER TABLE mng_user_api_keys DROP COLUMN IF EXISTS user_id")
        cur.execute("ALTER TABLE mng_user_api_keys RENAME COLUMN user_id_new TO user_id")
        cur.execute("""
            ALTER TABLE mng_user_api_keys
            ADD CONSTRAINT mng_user_api_keys_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES mng_users(id) ON DELETE CASCADE
        """)
        cur.execute("""
            ALTER TABLE mng_user_api_keys
            ADD CONSTRAINT mng_user_api_keys_user_id_provider_key
            UNIQUE (user_id, provider)
        """)

        # ── Step 4d: Convert mng_user_projects.user_id VARCHAR → INT ─────────
        cur.execute("ALTER TABLE mng_user_projects DROP CONSTRAINT IF EXISTS mng_user_projects_pkey")
        cur.execute("ALTER TABLE mng_user_projects ADD COLUMN IF NOT EXISTS user_id_new INT")
        cur.execute("""
            UPDATE mng_user_projects up
            SET user_id_new = u.id
            FROM mng_users u
            WHERE u.uuid_id = up.user_id
        """)
        cur.execute("ALTER TABLE mng_user_projects ALTER COLUMN user_id_new SET NOT NULL")
        cur.execute("ALTER TABLE mng_user_projects DROP COLUMN IF EXISTS user_id")
        cur.execute("ALTER TABLE mng_user_projects RENAME COLUMN user_id_new TO user_id")
        cur.execute("ALTER TABLE mng_user_projects ADD PRIMARY KEY (user_id, project_id)")
        cur.execute("""
            ALTER TABLE mng_user_projects
            ADD CONSTRAINT mng_user_projects_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES mng_users(id) ON DELETE CASCADE
        """)

        # ── Step 5: mng_clients — add updated_at ─────────────────────────────
        cur.execute("""
            ALTER TABLE mng_clients
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)

        # ── Step 6: Mirror tables — convert user_id VARCHAR → INT + add updated_at ──
        # mem_mrr_prompts
        cur.execute("ALTER TABLE mem_mrr_prompts ADD COLUMN IF NOT EXISTS user_id_new INT")
        cur.execute("""
            UPDATE mem_mrr_prompts p
            SET user_id_new = u.id
            FROM mng_users u
            WHERE u.uuid_id = p.user_id
        """)
        cur.execute("ALTER TABLE mem_mrr_prompts DROP COLUMN IF EXISTS user_id")
        cur.execute("ALTER TABLE mem_mrr_prompts RENAME COLUMN user_id_new TO user_id")
        cur.execute("""
            ALTER TABLE mem_mrr_prompts
            ADD CONSTRAINT mem_mrr_prompts_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES mng_users(id) ON DELETE SET NULL
        """)
        cur.execute("""
            ALTER TABLE mem_mrr_prompts
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)

        # mem_mrr_commits
        cur.execute("ALTER TABLE mem_mrr_commits ADD COLUMN IF NOT EXISTS user_id_new INT")
        cur.execute("""
            UPDATE mem_mrr_commits c
            SET user_id_new = u.id
            FROM mng_users u
            WHERE u.uuid_id = c.user_id
        """)
        cur.execute("ALTER TABLE mem_mrr_commits DROP COLUMN IF EXISTS user_id")
        cur.execute("ALTER TABLE mem_mrr_commits RENAME COLUMN user_id_new TO user_id")
        cur.execute("""
            ALTER TABLE mem_mrr_commits
            ADD CONSTRAINT mem_mrr_commits_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES mng_users(id) ON DELETE SET NULL
        """)
        cur.execute("""
            ALTER TABLE mem_mrr_commits
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)

        # mem_mrr_commits_code  (no user_id in m048, add fresh)
        cur.execute("""
            ALTER TABLE mem_mrr_commits_code
            ADD COLUMN IF NOT EXISTS user_id INT NULL REFERENCES mng_users(id) ON DELETE SET NULL
        """)
        cur.execute("""
            ALTER TABLE mem_mrr_commits_code
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)

        # mem_mrr_items
        cur.execute("ALTER TABLE mem_mrr_items ADD COLUMN IF NOT EXISTS user_id_new INT")
        cur.execute("""
            UPDATE mem_mrr_items i
            SET user_id_new = u.id
            FROM mng_users u
            WHERE u.uuid_id = i.user_id
        """)
        cur.execute("ALTER TABLE mem_mrr_items DROP COLUMN IF EXISTS user_id")
        cur.execute("ALTER TABLE mem_mrr_items RENAME COLUMN user_id_new TO user_id")
        cur.execute("""
            ALTER TABLE mem_mrr_items
            ADD CONSTRAINT mem_mrr_items_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES mng_users(id) ON DELETE SET NULL
        """)
        cur.execute("""
            ALTER TABLE mem_mrr_items
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)

        # mem_mrr_messages
        cur.execute("ALTER TABLE mem_mrr_messages ADD COLUMN IF NOT EXISTS user_id_new INT")
        cur.execute("""
            UPDATE mem_mrr_messages m
            SET user_id_new = u.id
            FROM mng_users u
            WHERE u.uuid_id = m.user_id
        """)
        cur.execute("ALTER TABLE mem_mrr_messages DROP COLUMN IF EXISTS user_id")
        cur.execute("ALTER TABLE mem_mrr_messages RENAME COLUMN user_id_new TO user_id")
        cur.execute("""
            ALTER TABLE mem_mrr_messages
            ADD CONSTRAINT mem_mrr_messages_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES mng_users(id) ON DELETE SET NULL
        """)
        cur.execute("""
            ALTER TABLE mem_mrr_messages
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)

        # ── Step 7: mem_ai_events — rename is_system → event_system, processed_at → updated_at ──
        cur.execute("""
            ALTER TABLE mem_ai_events
            RENAME COLUMN is_system TO event_system
        """)
        cur.execute("""
            ALTER TABLE mem_ai_events
            RENAME COLUMN processed_at TO updated_at
        """)
        # Drop old indexes on old column names and recreate with new names
        cur.execute("DROP INDEX IF EXISTS idx_mae_system")
        cur.execute("DROP INDEX IF EXISTS idx_mae_pending")
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_mae_event_system
            ON mem_ai_events(event_system) WHERE event_system = TRUE
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_mae_pending
            ON mem_ai_events(updated_at) WHERE updated_at IS NULL
        """)

        # ── Step 8: mem_ai_project_facts — add created_at + updated_at ───────
        cur.execute("""
            ALTER TABLE mem_ai_project_facts
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)
        cur.execute("""
            ALTER TABLE mem_ai_project_facts
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)

        # ── Step 9: mem_pipeline_runs — add user_id + updated_at ─────────────
        cur.execute("""
            ALTER TABLE mem_pipeline_runs
            ADD COLUMN IF NOT EXISTS user_id INT NULL REFERENCES mng_users(id) ON DELETE SET NULL
        """)
        cur.execute("""
            ALTER TABLE mem_pipeline_runs
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        """)

        # ── Step 10: Create set_updated_at() trigger function ─────────────────
        cur.execute("""
            CREATE OR REPLACE FUNCTION set_updated_at()
            RETURNS TRIGGER LANGUAGE plpgsql AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$
        """)

        # ── Step 11: Create triggers on all tables with updated_at ─────────────
        # Tables that already had triggers (mng_projects, planner_tags,
        # mng_agent_roles, mng_system_roles, mem_ai_work_items, mem_ai_feature_snapshot,
        # pr_graph_workflows, pr_graph_nodes, pr_graph_edges, mng_session_tags)
        # are NOT re-triggered here to avoid duplicates.
        # New tables gaining updated_at via this migration:
        _trigger_tables = [
            "mng_users",
            "mng_clients",
            "mem_mrr_prompts",
            "mem_mrr_commits",
            "mem_mrr_commits_code",
            "mem_mrr_items",
            "mem_mrr_messages",
            "mem_ai_events",
            "mem_ai_project_facts",
            "mem_pipeline_runs",
        ]
        for _tbl in _trigger_tables:
            cur.execute(f"""
                DROP TRIGGER IF EXISTS trg_updated_at_{_tbl} ON {_tbl}
            """)
            cur.execute(f"""
                CREATE TRIGGER trg_updated_at_{_tbl}
                BEFORE UPDATE ON {_tbl}
                FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """)

        # ── Step 12: Recreate idx_users_email (was on id column; now uuid_id) ─
        # The email index is fine — email column didn't change.
        # Recreate user_id indexes on dependent tables for new INT column.
        cur.execute("DROP INDEX IF EXISTS idx_usage_user_id")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_user_id ON mng_usage_logs(user_id)")
        cur.execute("DROP INDEX IF EXISTS idx_tx_user_id")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tx_user_id ON mng_transactions(user_id)")
        cur.execute("DROP INDEX IF EXISTS idx_muak_user")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_muak_user ON mng_user_api_keys(user_id)")

    conn.commit()
    log.info(
        "m051_schema_refactor_user_id_updated_at: "
        "mng_users.id → SERIAL INT, uuid_id added; "
        "user_id FK converted to INT on 4 tables; "
        "updated_at added to mng_clients, mng_users, 5 mirror tables, "
        "mem_ai_project_facts, mem_pipeline_runs; "
        "user_id INT added to 5 mirror tables + mem_pipeline_runs; "
        "mem_ai_events: is_system → event_system, processed_at → updated_at; "
        "set_updated_at() trigger created on 10 tables"
    )


def m052_column_reorder(conn) -> None:  # noqa: C901
    """Recreate 18 tables with consistent column ordering.

    Rules applied:
      id → client_id → project_id → user_id → [business cols]
      → created_at → updated_at → embedding (embedding always last)

    Additional changes:
      - mem_mrr_commits: remove committed_at (git timestamp moved into created_at)
      - planner_tags.user_id: VARCHAR(36) → INT
      - mng_users: id becomes first column (was 14th after m051)

    Pattern: drop external FKs → rename → CREATE in dep order →
             copy data → sequences → self-FKs → indexes → drop backups → commit
    """
    RECREATE = [
        "mng_clients", "mng_users", "mng_usage_logs", "mng_transactions",
        "mng_user_projects", "mng_user_api_keys", "mng_session_tags", "mng_agent_roles",
        "mem_mrr_prompts", "mem_mrr_commits", "mem_mrr_commits_code",
        "mem_mrr_items", "mem_mrr_messages",
        "mem_ai_events", "mem_ai_work_items", "mem_ai_project_facts",
        "mem_pipeline_runs", "planner_tags",
    ]

    with conn.cursor() as cur:
        # ── Phase 1: Drop external FK constraints pointing TO our tables ─────────
        # (from tables that are NOT in RECREATE — we'll recreate them at the end)
        cur.execute("""
            SELECT c.conname, c.conrelid::regclass::text AS src_tbl,
                   pg_get_constraintdef(c.oid) AS condef
            FROM pg_constraint c
            WHERE c.contype = 'f'
              AND c.confrelid::regclass::text = ANY(%s)
              AND c.conrelid::regclass::text != ALL(%s)
        """, (RECREATE, RECREATE))
        ext_fks = cur.fetchall()  # [(conname, src_tbl, condef), ...]
        for conname, src_tbl, _condef in ext_fks:
            cur.execute(f'ALTER TABLE {src_tbl} DROP CONSTRAINT IF EXISTS "{conname}"')

        # ── Phase 2: Rename all 18 tables to _bak_052_X ──────────────────────────
        for tbl in RECREATE:
            cur.execute(f"ALTER TABLE {tbl} RENAME TO _bak_052_{tbl}")

        # ── Phase 3: Create new tables in FK-dependency order ────────────────────
        # Tables may FK to mng_projects / mng_tags_categories (not in RECREATE, still exist)

        # 1. mng_clients
        cur.execute("""
            CREATE TABLE mng_clients (
                id                SERIAL        PRIMARY KEY,
                slug              VARCHAR(50)   NOT NULL UNIQUE,
                name              VARCHAR(255)  NOT NULL DEFAULT '',
                plan              VARCHAR(20)   NOT NULL DEFAULT 'free',
                pricing_config    JSONB,
                provider_costs    JSONB,
                provider_balances JSONB,
                server_api_keys   JSONB,
                created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
                updated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
            )
        """)

        # 2. mng_users  (FK → mng_clients)
        cur.execute("""
            CREATE TABLE mng_users (
                id                  SERIAL        PRIMARY KEY,
                uuid_id             VARCHAR(36)   NOT NULL UNIQUE,
                client_id           INT           NOT NULL DEFAULT 1
                                    REFERENCES mng_clients(id),
                email               VARCHAR(255)  NOT NULL UNIQUE,
                password_hash       TEXT          NOT NULL,
                is_admin            BOOLEAN       NOT NULL DEFAULT false,
                is_active           BOOLEAN       NOT NULL DEFAULT true,
                role                VARCHAR(20)   NOT NULL DEFAULT 'free',
                last_login          TIMESTAMPTZ,
                balance_added_usd   NUMERIC       NOT NULL DEFAULT 0,
                balance_used_usd    NUMERIC       NOT NULL DEFAULT 0,
                coupons_used        TEXT[]        NOT NULL DEFAULT '{}',
                stripe_customer_id  VARCHAR(100)  NOT NULL DEFAULT '',
                created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
                updated_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
            )
        """)

        # 3. mng_session_tags  (FK → mng_clients, mng_projects)
        cur.execute("""
            CREATE TABLE mng_session_tags (
                id         SERIAL       PRIMARY KEY,
                client_id  INT          NOT NULL DEFAULT 1
                           REFERENCES mng_clients(id),
                project_id INT          NOT NULL UNIQUE
                           REFERENCES mng_projects(id),
                phase      VARCHAR(20),
                feature    VARCHAR(255),
                bug_ref    VARCHAR(255),
                extra      JSONB        NOT NULL DEFAULT '{}',
                updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
        """)

        # 4. mng_agent_roles  (FK → mng_clients, mng_projects)
        cur.execute("""
            CREATE TABLE mng_agent_roles (
                id             SERIAL        PRIMARY KEY,
                client_id      INT           NOT NULL DEFAULT 1
                               REFERENCES mng_clients(id),
                project_id     INT           NOT NULL
                               REFERENCES mng_projects(id),
                name           TEXT          NOT NULL,
                description    TEXT          NOT NULL DEFAULT '',
                system_prompt  TEXT          NOT NULL DEFAULT '',
                provider       TEXT          NOT NULL DEFAULT 'claude',
                model          TEXT          NOT NULL DEFAULT '',
                role_type      VARCHAR(50)   NOT NULL DEFAULT 'agent',
                tags           TEXT[]        NOT NULL DEFAULT '{}',
                is_active      BOOLEAN       NOT NULL DEFAULT true,
                auto_commit    BOOLEAN       NOT NULL DEFAULT false,
                react          BOOLEAN       NOT NULL DEFAULT true,
                max_iterations INT           NOT NULL DEFAULT 10,
                inputs         JSONB                  DEFAULT '[]',
                outputs        JSONB                  DEFAULT '[]',
                tools          JSONB                  DEFAULT '[]',
                output_schema  JSONB,
                created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
                updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
                UNIQUE (project_id, name)
            )
        """)

        # 5. mng_usage_logs  (FK → mng_users)
        cur.execute("""
            CREATE TABLE mng_usage_logs (
                id           SERIAL        PRIMARY KEY,
                user_id      INT           REFERENCES mng_users(id) ON DELETE SET NULL,
                provider     VARCHAR(50),
                model        VARCHAR(100),
                input_tokens  INT          NOT NULL DEFAULT 0,
                output_tokens INT          NOT NULL DEFAULT 0,
                cost_usd     NUMERIC       NOT NULL DEFAULT 0,
                charged_usd  NUMERIC       NOT NULL DEFAULT 0,
                source       VARCHAR(50)   NOT NULL DEFAULT 'request',
                metadata     JSONB,
                period_start TIMESTAMPTZ,
                period_end   TIMESTAMPTZ,
                created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
            )
        """)

        # 6. mng_transactions  (FK → mng_users)
        cur.execute("""
            CREATE TABLE mng_transactions (
                id            SERIAL       PRIMARY KEY,
                user_id       INT          REFERENCES mng_users(id) ON DELETE SET NULL,
                type          VARCHAR(50)  NOT NULL,
                amount_usd    NUMERIC      NOT NULL DEFAULT 0,
                base_cost_usd NUMERIC,
                description   TEXT         NOT NULL DEFAULT '',
                ref           VARCHAR(255) NOT NULL DEFAULT '',
                created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
        """)

        # 7. mng_user_projects  (FK → mng_users, mng_projects; composite PK)
        cur.execute("""
            CREATE TABLE mng_user_projects (
                user_id    INT          NOT NULL REFERENCES mng_users(id)    ON DELETE CASCADE,
                project_id INT          NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                role       VARCHAR(20)  NOT NULL DEFAULT 'member',
                joined_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                PRIMARY KEY (user_id, project_id)
            )
        """)

        # 8. mng_user_api_keys  (FK → mng_users)
        cur.execute("""
            CREATE TABLE mng_user_api_keys (
                id         SERIAL       PRIMARY KEY,
                user_id    INT          NOT NULL REFERENCES mng_users(id) ON DELETE CASCADE,
                provider   VARCHAR(50)  NOT NULL,
                key_enc    TEXT         NOT NULL,
                updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                UNIQUE (user_id, provider)
            )
        """)

        # 9. mem_mrr_prompts  (FK → mng_clients, mng_projects, mng_users)
        cur.execute("""
            CREATE TABLE mem_mrr_prompts (
                id         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id  INT          NOT NULL DEFAULT 1
                           REFERENCES mng_clients(id),
                project_id INT          NOT NULL
                           REFERENCES mng_projects(id) ON DELETE CASCADE,
                user_id    INT          REFERENCES mng_users(id) ON DELETE SET NULL,
                event_id   UUID,
                session_id TEXT,
                source_id  TEXT,
                prompt     TEXT         NOT NULL DEFAULT '',
                response   TEXT         NOT NULL DEFAULT '',
                tags       JSONB        NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
        """)

        # 10. mem_mrr_commits  (FK → mng_clients, mng_projects, mng_users, mem_mrr_prompts)
        #     committed_at REMOVED — git timestamp is stored in created_at
        cur.execute("""
            CREATE TABLE mem_mrr_commits (
                commit_hash       VARCHAR(64)  PRIMARY KEY,
                commit_hash_short VARCHAR(8)   GENERATED ALWAYS AS (left(commit_hash, 8)) STORED,
                client_id         INT          NOT NULL DEFAULT 1
                                  REFERENCES mng_clients(id),
                project_id        INT          NOT NULL
                                  REFERENCES mng_projects(id) ON DELETE CASCADE,
                user_id           INT          REFERENCES mng_users(id) ON DELETE SET NULL,
                commit_msg        TEXT         NOT NULL DEFAULT '',
                summary           TEXT         NOT NULL DEFAULT '',
                diff_summary      TEXT         NOT NULL DEFAULT '',
                tags              JSONB        NOT NULL DEFAULT '{}',
                prompt_id         UUID         REFERENCES mem_mrr_prompts(id) ON DELETE SET NULL,
                event_id          UUID,
                session_id        VARCHAR(255),
                author            TEXT         NOT NULL DEFAULT '',
                author_email      TEXT         NOT NULL DEFAULT '',
                llm               TEXT,
                created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
            )
        """)

        # 11. mem_mrr_commits_code  (FK → mng_clients, mng_projects, mng_users, mem_mrr_commits)
        cur.execute("""
            CREATE TABLE mem_mrr_commits_code (
                id            UUID  PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id     INT   NOT NULL DEFAULT 1
                              REFERENCES mng_clients(id),
                project_id    INT   NOT NULL
                              REFERENCES mng_projects(id) ON DELETE CASCADE,
                user_id       INT   REFERENCES mng_users(id) ON DELETE SET NULL,
                commit_hash   VARCHAR(64) NOT NULL
                              REFERENCES mem_mrr_commits(commit_hash) ON DELETE CASCADE,
                file_path     TEXT  NOT NULL,
                file_ext      TEXT  NOT NULL DEFAULT '',
                file_language TEXT  NOT NULL DEFAULT '',
                file_change   TEXT  NOT NULL CHECK (file_change IN ('added','modified','deleted','renamed')),
                symbol_type   TEXT  NOT NULL CHECK (symbol_type IN ('class','method','function','import')),
                class_name    TEXT,
                method_name   TEXT,
                full_symbol   TEXT  GENERATED ALWAYS AS (
                    CASE WHEN class_name IS NOT NULL AND method_name IS NOT NULL
                         THEN class_name || '.' || method_name
                         WHEN class_name IS NOT NULL THEN class_name
                         ELSE method_name END
                ) STORED,
                symbol_change TEXT  NOT NULL CHECK (symbol_change IN ('added','modified','deleted')),
                rows_added    INT   NOT NULL DEFAULT 0,
                rows_removed  INT   NOT NULL DEFAULT 0,
                diff_snippet  TEXT,
                llm_summary   TEXT,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # 12. mem_mrr_items  (FK → mng_clients, mng_projects, mng_users)
        cur.execute("""
            CREATE TABLE mem_mrr_items (
                id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id  INT         NOT NULL DEFAULT 1
                           REFERENCES mng_clients(id),
                project_id INT         NOT NULL
                           REFERENCES mng_projects(id) ON DELETE CASCADE,
                user_id    INT         REFERENCES mng_users(id) ON DELETE SET NULL,
                item_type  TEXT        NOT NULL,
                title      TEXT,
                meeting_at TIMESTAMPTZ,
                attendees  TEXT[],
                raw_text   TEXT        NOT NULL,
                summary    TEXT,
                tags       JSONB       NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # 13. mem_mrr_messages  (FK → mng_clients, mng_projects, mng_users)
        cur.execute("""
            CREATE TABLE mem_mrr_messages (
                id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id  INT         NOT NULL DEFAULT 1
                           REFERENCES mng_clients(id),
                project_id INT         NOT NULL
                           REFERENCES mng_projects(id) ON DELETE CASCADE,
                user_id    INT         REFERENCES mng_users(id) ON DELETE SET NULL,
                platform   TEXT        NOT NULL,
                channel    TEXT,
                thread_ref TEXT,
                messages   JSONB       NOT NULL,
                date_range TSTZRANGE,
                tags       JSONB       NOT NULL DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # 14. mem_ai_events  (FK → mng_clients, mng_projects)
        #     event_system moved to after event_type
        cur.execute("""
            CREATE TABLE mem_ai_events (
                id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id    INT         NOT NULL DEFAULT 1
                             REFERENCES mng_clients(id),
                project_id   INT         NOT NULL
                             REFERENCES mng_projects(id) ON DELETE CASCADE,
                event_type   TEXT        NOT NULL,
                event_system BOOLEAN     NOT NULL DEFAULT false,
                event_cnt    INT         NOT NULL DEFAULT 0,
                source_id    TEXT        NOT NULL,
                work_item_id UUID,
                session_id   TEXT,
                chunk        INT         NOT NULL DEFAULT 0,
                chunk_type   TEXT        NOT NULL DEFAULT 'full',
                content      TEXT        NOT NULL DEFAULT '',
                summary      TEXT,
                action_items TEXT        NOT NULL DEFAULT '',
                tags         JSONB       NOT NULL DEFAULT '{}',
                created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at   TIMESTAMPTZ,
                embedding    VECTOR(1536),
                UNIQUE (project_id, event_type, source_id, chunk)
            )
        """)

        # 15. planner_tags  (FK → mng_clients, mng_projects, mng_users, mng_tags_categories)
        #     user_id: VARCHAR(36) → INT
        #     NO self-FKs yet (added after copy)
        cur.execute("""
            CREATE TABLE planner_tags (
                id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id            INT         NOT NULL DEFAULT 1
                                     REFERENCES mng_clients(id),
                project_id           INT         NOT NULL
                                     REFERENCES mng_projects(id) ON DELETE CASCADE,
                user_id              INT         REFERENCES mng_users(id) ON DELETE SET NULL,
                name                 TEXT        NOT NULL,
                category_id          INT         REFERENCES mng_tags_categories(id),
                parent_id            UUID,
                merged_into          UUID,
                description          TEXT        NOT NULL DEFAULT '',
                requirements         TEXT        NOT NULL DEFAULT '',
                acceptance_criteria  TEXT        NOT NULL DEFAULT '',
                action_items         TEXT        NOT NULL DEFAULT '',
                status               TEXT        NOT NULL DEFAULT 'open',
                priority             SMALLINT    NOT NULL DEFAULT 3,
                due_date             DATE,
                requester            TEXT,
                creator              TEXT        NOT NULL DEFAULT 'user',
                updater              TEXT        NOT NULL DEFAULT 'user',
                deliveries           JSONB       NOT NULL DEFAULT '[]',
                created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (project_id, name, category_id)
            )
        """)

        # 16. mem_ai_work_items  (FK → mng_clients, mng_projects, planner_tags)
        #     quality_stage/issues/dedup_status moved after status_user
        #     NO self-FK (merged_into) yet — added after copy
        cur.execute("""
            CREATE TABLE mem_ai_work_items (
                id                     UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id              INT         NOT NULL DEFAULT 1
                                       REFERENCES mng_clients(id),
                project_id             INT         NOT NULL
                                       REFERENCES mng_projects(id) ON DELETE CASCADE,
                seq_num                INT,
                category_ai            TEXT        NOT NULL,
                name_ai                TEXT        NOT NULL,
                summary_ai             TEXT        NOT NULL DEFAULT '',
                acceptance_criteria_ai TEXT        NOT NULL DEFAULT '',
                action_items_ai        TEXT        NOT NULL DEFAULT '',
                score_ai               SMALLINT    NOT NULL DEFAULT 0,
                tags                   JSONB       NOT NULL DEFAULT '{}',
                tags_ai                JSONB       NOT NULL DEFAULT '{}',
                tag_id_ai              UUID        REFERENCES planner_tags(id),
                tag_id_user            UUID        REFERENCES planner_tags(id),
                status_user            VARCHAR(20) NOT NULL DEFAULT 'active',
                quality_stage          VARCHAR(20) NOT NULL DEFAULT 'staging',
                quality_issues         JSONB       NOT NULL DEFAULT '{}',
                dedup_status           VARCHAR(20) NOT NULL DEFAULT 'new',
                merged_into            UUID,
                start_date             TIMESTAMPTZ,
                created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                embedding              VECTOR(1536),
                UNIQUE (project_id, category_ai, name_ai)
            )
        """)

        # 17. mem_ai_project_facts  (FK → mng_clients, mng_projects)
        #     project_id moved after client_id; embedding moved to end
        cur.execute("""
            CREATE TABLE mem_ai_project_facts (
                id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id        INT         NOT NULL DEFAULT 1
                                 REFERENCES mng_clients(id),
                project_id       INT         NOT NULL
                                 REFERENCES mng_projects(id) ON DELETE CASCADE,
                fact_key         TEXT        NOT NULL,
                fact_value       TEXT        NOT NULL,
                valid_from       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                valid_until      TIMESTAMPTZ,
                source_memory_id UUID,
                category         TEXT,
                conflict_status  TEXT,
                created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                embedding        VECTOR(1536)
            )
        """)

        # 18. mem_pipeline_runs  (FK → mng_projects, mng_users)
        cur.execute("""
            CREATE TABLE mem_pipeline_runs (
                id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id  INT         NOT NULL
                            REFERENCES mng_projects(id) ON DELETE CASCADE,
                user_id     INT         REFERENCES mng_users(id) ON DELETE SET NULL,
                pipeline    TEXT        NOT NULL,
                source_id   TEXT        NOT NULL DEFAULT '',
                status      TEXT        NOT NULL DEFAULT 'running',
                items_in    INT         NOT NULL DEFAULT 0,
                items_out   INT         NOT NULL DEFAULT 0,
                error_msg   TEXT,
                duration_ms INT,
                started_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                finished_at TIMESTAMPTZ,
                updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        # ── Phase 4: Copy data from backups ──────────────────────────────────────
        # Same dependency order as CREATE

        # mng_clients
        cur.execute("""
            INSERT INTO mng_clients
              (id, slug, name, plan, pricing_config, provider_costs,
               provider_balances, server_api_keys, created_at, updated_at)
            SELECT id, slug, name, plan, pricing_config, provider_costs,
                   provider_balances, server_api_keys, created_at, updated_at
            FROM _bak_052_mng_clients
        """)

        # mng_users
        cur.execute("""
            INSERT INTO mng_users
              (id, uuid_id, client_id, email, password_hash, is_admin, is_active,
               role, last_login, balance_added_usd, balance_used_usd,
               coupons_used, stripe_customer_id, created_at, updated_at)
            SELECT id, uuid_id, client_id, email, password_hash, is_admin, is_active,
                   role, last_login, balance_added_usd, balance_used_usd,
                   coupons_used, stripe_customer_id, created_at, updated_at
            FROM _bak_052_mng_users
        """)

        # mng_session_tags
        cur.execute("""
            INSERT INTO mng_session_tags
              (id, client_id, project_id, phase, feature, bug_ref, extra, updated_at)
            SELECT id, client_id, project_id, phase, feature, bug_ref, extra, updated_at
            FROM _bak_052_mng_session_tags
        """)

        # mng_agent_roles
        cur.execute("""
            INSERT INTO mng_agent_roles
              (id, client_id, project_id, name, description, system_prompt,
               provider, model, role_type, tags, is_active, auto_commit, react,
               max_iterations, inputs, outputs, tools, output_schema,
               created_at, updated_at)
            SELECT id, client_id, project_id, name, description, system_prompt,
                   provider, model, role_type, tags, is_active, auto_commit, react,
                   max_iterations, inputs, outputs, tools, output_schema,
                   created_at, updated_at
            FROM _bak_052_mng_agent_roles
        """)

        # mng_usage_logs
        cur.execute("""
            INSERT INTO mng_usage_logs
              (id, user_id, provider, model, input_tokens, output_tokens,
               cost_usd, charged_usd, source, metadata, period_start, period_end,
               created_at)
            SELECT id, user_id, provider, model, input_tokens, output_tokens,
                   cost_usd, charged_usd, source, metadata, period_start, period_end,
                   created_at
            FROM _bak_052_mng_usage_logs
        """)

        # mng_transactions
        cur.execute("""
            INSERT INTO mng_transactions
              (id, user_id, type, amount_usd, base_cost_usd, description, ref, created_at)
            SELECT id, user_id, type, amount_usd, base_cost_usd, description, ref, created_at
            FROM _bak_052_mng_transactions
        """)

        # mng_user_projects
        cur.execute("""
            INSERT INTO mng_user_projects (user_id, project_id, role, joined_at)
            SELECT user_id, project_id, role, joined_at
            FROM _bak_052_mng_user_projects
        """)

        # mng_user_api_keys
        cur.execute("""
            INSERT INTO mng_user_api_keys (id, user_id, provider, key_enc, updated_at)
            SELECT id, user_id, provider, key_enc, updated_at
            FROM _bak_052_mng_user_api_keys
        """)

        # mem_mrr_prompts
        cur.execute("""
            INSERT INTO mem_mrr_prompts
              (id, client_id, project_id, user_id, event_id, session_id,
               source_id, prompt, response, tags, created_at, updated_at)
            SELECT id, client_id, project_id, user_id, event_id, session_id,
                   source_id, prompt, response, tags, created_at, updated_at
            FROM _bak_052_mem_mrr_prompts
        """)

        # mem_mrr_commits — committed_at → created_at (git timestamp)
        cur.execute("""
            INSERT INTO mem_mrr_commits
              (commit_hash, client_id, project_id, user_id, commit_msg,
               summary, diff_summary, tags, prompt_id, event_id,
               session_id, author, author_email, llm,
               created_at, updated_at)
            SELECT commit_hash, client_id, project_id, user_id, commit_msg,
                   summary, diff_summary, tags, prompt_id, event_id,
                   session_id, author, author_email, llm,
                   COALESCE(committed_at, created_at),
                   updated_at
            FROM _bak_052_mem_mrr_commits
        """)

        # mem_mrr_commits_code (skip GENERATED columns: full_symbol, commit_hash_short)
        cur.execute("""
            INSERT INTO mem_mrr_commits_code
              (id, client_id, project_id, user_id, commit_hash,
               file_path, file_ext, file_language, file_change,
               symbol_type, class_name, method_name,
               symbol_change, rows_added, rows_removed,
               diff_snippet, llm_summary, created_at, updated_at)
            SELECT id, client_id, project_id, user_id, commit_hash,
                   file_path, file_ext, file_language, file_change,
                   symbol_type, class_name, method_name,
                   symbol_change, rows_added, rows_removed,
                   diff_snippet, llm_summary, created_at, updated_at
            FROM _bak_052_mem_mrr_commits_code
        """)

        # mem_mrr_items
        cur.execute("""
            INSERT INTO mem_mrr_items
              (id, client_id, project_id, user_id, item_type, title,
               meeting_at, attendees, raw_text, summary, tags, created_at, updated_at)
            SELECT id, client_id, project_id, user_id, item_type, title,
                   meeting_at, attendees, raw_text, summary, tags, created_at, updated_at
            FROM _bak_052_mem_mrr_items
        """)

        # mem_mrr_messages
        cur.execute("""
            INSERT INTO mem_mrr_messages
              (id, client_id, project_id, user_id, platform, channel,
               thread_ref, messages, date_range, tags, created_at, updated_at)
            SELECT id, client_id, project_id, user_id, platform, channel,
                   thread_ref, messages, date_range, tags, created_at, updated_at
            FROM _bak_052_mem_mrr_messages
        """)

        # mem_ai_events
        cur.execute("""
            INSERT INTO mem_ai_events
              (id, client_id, project_id, event_type, event_system, event_cnt,
               source_id, work_item_id, session_id, chunk, chunk_type,
               content, summary, action_items, tags,
               created_at, updated_at, embedding)
            SELECT id, client_id, project_id, event_type, event_system, event_cnt,
                   source_id, work_item_id, session_id, chunk, chunk_type,
                   content, summary, action_items, tags,
                   created_at, updated_at, embedding
            FROM _bak_052_mem_ai_events
        """)

        # planner_tags — user_id VARCHAR → INT via mng_users lookup
        cur.execute("""
            INSERT INTO planner_tags
              (id, client_id, project_id, user_id, name, category_id,
               parent_id, merged_into, description, requirements,
               acceptance_criteria, action_items, status, priority,
               due_date, requester, creator, updater, deliveries,
               created_at, updated_at)
            SELECT b.id, b.client_id, b.project_id,
                   u.id AS user_id,
                   b.name, b.category_id,
                   b.parent_id, b.merged_into, b.description, b.requirements,
                   b.acceptance_criteria, b.action_items, b.status, b.priority,
                   b.due_date, b.requester, b.creator, b.updater, b.deliveries,
                   b.created_at, b.updated_at
            FROM _bak_052_planner_tags b
            LEFT JOIN mng_users u ON u.uuid_id = b.user_id::text
        """)

        # mem_ai_work_items
        cur.execute("""
            INSERT INTO mem_ai_work_items
              (id, client_id, project_id, seq_num, category_ai, name_ai,
               summary_ai, acceptance_criteria_ai, action_items_ai, score_ai,
               tags, tags_ai, tag_id_ai, tag_id_user,
               status_user, quality_stage, quality_issues, dedup_status,
               merged_into, start_date, created_at, updated_at, embedding)
            SELECT id, client_id, project_id, seq_num, category_ai, name_ai,
                   summary_ai, acceptance_criteria_ai, action_items_ai, score_ai,
                   tags, tags_ai, tag_id_ai, tag_id_user,
                   status_user, quality_stage, quality_issues, dedup_status,
                   merged_into, start_date, created_at, updated_at, embedding
            FROM _bak_052_mem_ai_work_items
        """)

        # mem_ai_project_facts
        cur.execute("""
            INSERT INTO mem_ai_project_facts
              (id, client_id, project_id, fact_key, fact_value, valid_from,
               valid_until, source_memory_id, category, conflict_status,
               created_at, updated_at, embedding)
            SELECT id, client_id, project_id, fact_key, fact_value, valid_from,
                   valid_until, source_memory_id, category, conflict_status,
                   created_at, updated_at, embedding
            FROM _bak_052_mem_ai_project_facts
        """)

        # mem_pipeline_runs
        cur.execute("""
            INSERT INTO mem_pipeline_runs
              (id, project_id, user_id, pipeline, source_id, status,
               items_in, items_out, error_msg, duration_ms,
               started_at, finished_at, updated_at)
            SELECT id, project_id, user_id, pipeline, source_id, status,
                   items_in, items_out, error_msg, duration_ms,
                   started_at, finished_at, updated_at
            FROM _bak_052_mem_pipeline_runs
        """)

        # ── Phase 5: Advance sequences for SERIAL tables ──────────────────────────
        for tbl, col in [
            ("mng_clients",      "id"),
            ("mng_users",        "id"),
            ("mng_usage_logs",   "id"),
            ("mng_transactions", "id"),
            ("mng_user_api_keys","id"),
            ("mng_session_tags", "id"),
            ("mng_agent_roles",  "id"),
        ]:
            cur.execute(f"""
                SELECT setval(pg_get_serial_sequence('{tbl}', '{col}'),
                              COALESCE(MAX({col}), 1))
                FROM {tbl}
            """)

        # ── Phase 6: Add self-FK constraints ─────────────────────────────────────
        cur.execute("""
            ALTER TABLE planner_tags
              ADD CONSTRAINT planner_tags_parent_id_fkey
                FOREIGN KEY (parent_id) REFERENCES planner_tags(id),
              ADD CONSTRAINT planner_tags_merged_into_fkey
                FOREIGN KEY (merged_into) REFERENCES planner_tags(id)
        """)
        cur.execute("""
            ALTER TABLE mem_ai_work_items
              ADD CONSTRAINT fk_wi_merged_into
                FOREIGN KEY (merged_into) REFERENCES mem_ai_work_items(id)
                ON DELETE SET NULL NOT VALID
        """)

        # ── Phase 7: Recreate indexes ─────────────────────────────────────────────
        # mng_clients
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mng_clients_slug  ON mng_clients(slug)")
        # mng_users
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_client ON mng_users(client_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_users_email  ON mng_users(email)")
        # mng_usage_logs
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_created_at ON mng_usage_logs(created_at DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_provider   ON mng_usage_logs(provider)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_user_id    ON mng_usage_logs(user_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_usage_source     ON mng_usage_logs(source)")
        # mng_transactions
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tx_created_at ON mng_transactions(created_at DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tx_type       ON mng_transactions(type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tx_user_id    ON mng_transactions(user_id)")
        # mng_user_projects
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mng_user_projects_proj ON mng_user_projects(project_id)")
        # mng_user_api_keys
        cur.execute("CREATE INDEX IF NOT EXISTS idx_muak_user ON mng_user_api_keys(user_id)")
        # mng_session_tags
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mst_pid ON mng_session_tags(project_id)")
        # mng_agent_roles
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mar_pid ON mng_agent_roles(project_id)")
        # mem_mrr_prompts
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_p_pid     ON mem_mrr_prompts(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_p_session ON mem_mrr_prompts(session_id) WHERE session_id IS NOT NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_p_created ON mem_mrr_prompts(created_at DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_p_tags    ON mem_mrr_prompts USING GIN(tags)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_p_event   ON mem_mrr_prompts(event_id) WHERE event_id IS NOT NULL")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mmrr_p_source ON mem_mrr_prompts(project_id, source_id) WHERE source_id IS NOT NULL")
        # mem_mrr_commits
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_c_pid     ON mem_mrr_commits(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_c_session ON mem_mrr_commits(session_id) WHERE session_id IS NOT NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_c_created ON mem_mrr_commits(created_at DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_c_tags    ON mem_mrr_commits USING GIN(tags)")
        # mem_mrr_commits_code
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmc_code_pid  ON mem_mrr_commits_code(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmc_code_hash ON mem_mrr_commits_code(commit_hash)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmc_code_sym  ON mem_mrr_commits_code(full_symbol) WHERE full_symbol IS NOT NULL")
        cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_mmc_code_unique
            ON mem_mrr_commits_code(commit_hash, file_path, symbol_type,
               COALESCE(class_name,''), COALESCE(method_name,''))""")
        # mem_mrr_items
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_items_type ON mem_mrr_items(item_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_items_pid  ON mem_mrr_items(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_i_tags     ON mem_mrr_items USING GIN(tags)")
        # mem_mrr_messages
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_messages_pid ON mem_mrr_messages(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mmrr_m_tags       ON mem_mrr_messages USING GIN(tags)")
        # mem_ai_events
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_pid           ON mem_ai_events(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_session       ON mem_ai_events(session_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_type          ON mem_ai_events(event_type)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_tags          ON mem_ai_events USING GIN(tags)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_event_system  ON mem_ai_events(event_system) WHERE event_system = true")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_pending       ON mem_ai_events(updated_at) WHERE updated_at IS NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mae_embed         ON mem_ai_events USING ivfflat(embedding vector_cosine_ops) WHERE embedding IS NOT NULL")
        # planner_tags
        cur.execute("CREATE INDEX IF NOT EXISTS idx_planner_tags_uid  ON planner_tags(user_id)")
        # mem_ai_work_items
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_embed ON mem_ai_work_items USING ivfflat(embedding vector_cosine_ops) WHERE embedding IS NOT NULL")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_wi_quality       ON mem_ai_work_items(project_id, quality_stage)")
        # mem_ai_project_facts
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mem_ai_pf_pid ON mem_ai_project_facts(project_id) WHERE valid_until IS NULL")
        cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_mem_ai_pf_current ON mem_ai_project_facts(project_id, fact_key) WHERE valid_until IS NULL")
        # mem_pipeline_runs
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mpr_project_started ON mem_pipeline_runs(project_id, started_at DESC)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mpr_status          ON mem_pipeline_runs(status) WHERE status = 'running'")

        # ── Phase 8: Recreate updated_at triggers on rebuilt tables ──────────────
        for _tbl in RECREATE:
            cur.execute(f"DROP TRIGGER IF EXISTS trg_updated_at_{_tbl} ON {_tbl}")
            cur.execute(f"""
                CREATE TRIGGER trg_updated_at_{_tbl}
                BEFORE UPDATE ON {_tbl}
                FOR EACH ROW EXECUTE FUNCTION set_updated_at()
            """)

        # ── Phase 9: Recreate external FK constraints ─────────────────────────────
        for conname, src_tbl, condef in ext_fks:
            cur.execute(f'ALTER TABLE {src_tbl} ADD CONSTRAINT "{conname}" {condef}')

        # ── Phase 10: Drop backup tables ─────────────────────────────────────────
        for tbl in RECREATE:
            cur.execute(f"DROP TABLE IF EXISTS _bak_052_{tbl} CASCADE")

    conn.commit()
    log.info("m052_column_reorder: 18 tables rebuilt with consistent column ordering")


def m053_pr_statistics(conn) -> None:
    """Add pr_statistics aggregation cache table + performance indexes.

    Creates a per-project-per-day statistics cache (pr_statistics) to replace
    the ~15 individual COUNT queries in data_dashboard. Also fixes a stale index
    on mem_mrr_commits and adds a composite index for the ev_count CTE.
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pr_statistics (
                id                  SERIAL PRIMARY KEY,
                client_id           INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
                project_id          INT          NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                stat_date           DATE         NOT NULL DEFAULT CURRENT_DATE,
                stats               JSONB        NOT NULL DEFAULT '{}',
                last_event_run_at   TIMESTAMPTZ,
                last_fact_run_at    TIMESTAMPTZ,
                last_wi_run_at      TIMESTAMPTZ,
                created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
                UNIQUE (project_id, stat_date)
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_pr_stats_project_date "
            "ON pr_statistics(project_id, stat_date DESC)"
        )
        # Drop existing trigger first to ensure idempotency
        cur.execute("DROP TRIGGER IF EXISTS set_pr_statistics_updated_at ON pr_statistics")
        cur.execute("""
            CREATE TRIGGER set_pr_statistics_updated_at
            BEFORE UPDATE ON pr_statistics
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """)
        # Fix stale index on mem_mrr_commits referencing dropped committed_at column
        cur.execute("DROP INDEX IF EXISTS idx_mmrr_c_comm")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mmrr_c_created "
            "ON mem_mrr_commits(project_id, created_at DESC)"
        )
        # Composite index for the ev_count CTE in work items list query
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mae_pid_wi "
            "ON mem_ai_events(project_id, work_item_id) WHERE work_item_id IS NOT NULL"
        )
    conn.commit()
    log.info("m053_pr_statistics: pr_statistics table + 3 indexes created")


def m054_backlog_ref(conn) -> None:
    """Add backlog_ref column to mirror tables + file_ref to planner_tags + seed P/C/M/I sequences.

    backlog_ref TEXT: tracks which backlog.md entry this row was digested into.
    NULL = not yet processed by MemoryBacklog. Format: 'P100042', 'C200001', etc.

    file_ref TEXT on planner_tags: pointer into a use-case file section, e.g.
    'use_cases/auth-refactor.md#open-bugs'. Displayed in Planner property panel.

    pr_seq_counters seeded for 4 source-type prefixes so next_seq() returns
    predictable starting numbers (P→100000, C→200000, M→300000, I→400000).
    """
    with conn.cursor() as cur:
        for tbl in ("mem_mrr_prompts", "mem_mrr_commits", "mem_mrr_messages", "mem_mrr_items"):
            cur.execute(f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS backlog_ref TEXT")
            # Partial index: speeds up "WHERE backlog_ref IS NULL" count + fetch
            short = tbl.replace("mem_mrr_", "")[:8]
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS idx_{short}_bref "
                f"ON {tbl}(project_id) WHERE backlog_ref IS NULL"
            )
        cur.execute("ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS file_ref TEXT")
        for prefix, start in [("P", 100000), ("C", 200000), ("M", 300000), ("I", 400000)]:
            cur.execute(
                """INSERT INTO pr_seq_counters(project_id, category, next_val)
                   SELECT id, %s, %s FROM mng_projects ON CONFLICT DO NOTHING""",
                (prefix, start + 1),
            )
    conn.commit()
    log.info("m054_backlog_ref: backlog_ref + file_ref columns added; P/C/M/I seq seeds inserted")


def m055_cleanup_and_seq(conn) -> None:  # noqa: C901
    """Drop legacy tables; re-add seq_num to planner_tags; seed use_case category + seq counters.

    Legacy tables removed (all dropped in earlier migrations; safe IF NOT EXISTS):
        mem_tags_relations, pr_embeddings, pr_memory_events, pr_session_summaries,
        pr_memory_tags, pr_source_tags, pr_tags, pr_tag_meta, mng_entity_categories,
        mng_entity_values, mng_entity_value_links, pr_events, pr_prompt_tags,
        planner_tags_meta, mem_mrr_tags, mem_ai_tags, mem_ai_tags_relations, mem_ai_features

    New seq ranges (separate from work-item sequences — use prefix in category name):
        "uc"   → 10000+  (use_case planner tags)
        "feat" → 20000+  (feature  planner tags)
        "bug"  → 30000+  (bug      planner tags)

    planner_tags.seq_num INT — human-readable ID within a project (e.g. UC10001 = uc seq 10001).
    """
    _LEGACY_TABLES = [
        "mem_tags_relations",
        "pr_embeddings",
        "pr_memory_events",
        "pr_session_summaries",
        "pr_memory_tags",
        "pr_source_tags",
        "pr_tags",
        "pr_tag_meta",
        "mng_entity_categories",
        "mng_entity_values",
        "mng_entity_value_links",
        "pr_events",
        "pr_prompt_tags",
        "planner_tags_meta",
        "mem_mrr_tags",
        "mem_ai_tags",
        "mem_ai_tags_relations",
        "mem_ai_features",
    ]
    with conn.cursor() as cur:
        # 1. Drop legacy tables (CASCADE to handle any residual FK references)
        for tbl in _LEGACY_TABLES:
            cur.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE")
            log.debug(f"m055: dropped legacy table {tbl} (if existed)")

        # 2. Add seq_num back to planner_tags (was dropped in m026; now a clean human-readable ID)
        cur.execute(
            "ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS seq_num INT"
        )
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_planner_tags_seq "
            "ON planner_tags(project_id, seq_num) WHERE seq_num IS NOT NULL"
        )

        # 3. Seed "use_case" into mng_tags_categories (idempotent)
        cur.execute(
            """INSERT INTO mng_tags_categories (client_id, name, color, icon, description)
               VALUES (1, 'use_case', '#06b6d4', '◻', 'Use case — organised requirement set')
               ON CONFLICT (client_id, name) DO NOTHING"""
        )

        # 4. Seed pr_seq_counters for the three planner-tag sequences across all projects
        for cat, start in [("uc", 10000), ("feat", 20000), ("bug", 30000)]:
            cur.execute(
                """INSERT INTO pr_seq_counters (project_id, category, next_val)
                   SELECT id, %s, %s FROM mng_projects ON CONFLICT DO NOTHING""",
                (cat, start + 1),
            )

    conn.commit()
    log.info(
        "m055: %d legacy tables dropped; seq_num on planner_tags; "
        "use_case category + uc/feat/bug seq seeds added",
        len(_LEGACY_TABLES),
    )


def m056_drop_event_id_add_backlog_links(conn) -> None:
    """Drop obsolete event_id from mirror tables; create mem_backlog_links.

    event_id on mem_mrr_* was used by the old mem_ai_events digest pipeline to
    back-propagate the event UUID after a batch digest.  The new file-based
    backlog pipeline (m054) uses backlog_ref instead, so event_id is now dead
    weight.  The mem_ai_events table itself is kept for historical queries.

    mem_backlog_links is the stable DB mapping that survives .md file edits:
        ref_id (P100042)  →  tag_id (planner_tags UUID)  →  use_case_slug
    It is written when an entry is approved via run_work_items().
    The ## Internal Usage section in use_cases/*.md is regenerated from this
    table if it is ever deleted or corrupted.
    """
    with conn.cursor() as cur:
        # Drop event_id from all 4 mirror tables (no-op if already dropped)
        for tbl in ("mem_mrr_prompts", "mem_mrr_commits", "mem_mrr_messages", "mem_mrr_items"):
            cur.execute(f"ALTER TABLE {tbl} DROP COLUMN IF EXISTS event_id")
        # Drop the now-orphaned indexes that were on event_id
        for idx in (
            "idx_mmrr_p_event",
            "idx_mmrr_c_event",
        ):
            cur.execute(f"DROP INDEX IF EXISTS {idx}")

        # Create backlog linkage table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mem_backlog_links (
                id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id    INT  NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                ref_id        TEXT NOT NULL,
                tag_id        UUID REFERENCES planner_tags(id) ON DELETE SET NULL,
                use_case_slug TEXT NOT NULL,
                classify      TEXT,
                summary       TEXT,
                approved_at   TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE (project_id, ref_id)
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_backlog_links_tag  "
            "ON mem_backlog_links(tag_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_backlog_links_proj "
            "ON mem_backlog_links(project_id, use_case_slug)"
        )
    conn.commit()
    log.info(
        "m056: event_id dropped from 4 mirror tables; mem_backlog_links created"
    )


def m057_drop_events_and_work_items(conn) -> None:
    """Drop mem_ai_events and mem_ai_work_items — replaced by backlog pipeline and use case files."""
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS mem_ai_events CASCADE")
        cur.execute("DROP TABLE IF EXISTS mem_ai_work_items CASCADE")
    conn.commit()


def m058_tag_deps(conn) -> None:
    """Add planner_tag_deps table for tag-to-tag dependency links (depends_on)."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS planner_tag_deps (
                id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                project_id  INT  NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                tag_id      UUID NOT NULL REFERENCES planner_tags(id) ON DELETE CASCADE,
                depends_on  UUID NOT NULL REFERENCES planner_tags(id) ON DELETE CASCADE,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (tag_id, depends_on)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tag_deps_tag ON planner_tag_deps(tag_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_tag_deps_on  ON planner_tag_deps(depends_on)")
    conn.commit()


def m059_drop_legacy_tables(conn) -> None:
    """Drop orphaned backup table _bak_046_mem_ai_work_items (created by m046, never cleaned up)."""
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS _bak_046_mem_ai_work_items CASCADE")
    conn.commit()


def m060_drop_feature_snapshot(conn) -> None:
    """Drop mem_ai_feature_snapshot and its FK columns — feature was never completed."""
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE pr_graph_runs DROP COLUMN IF EXISTS snapshot_id")
        cur.execute("ALTER TABLE pr_graph_runs DROP COLUMN IF EXISTS use_case_num")
        cur.execute("DROP TABLE IF EXISTS mem_ai_feature_snapshot CASCADE")
    conn.commit()


def m062_rename_backlog_ref_to_wi_id(conn) -> None:
    """Rename backlog_ref → wi_id in all mem_mrr_* tables.

    wi_id replaces backlog_ref as the link from mirror rows to mem_work_items.
    All old P/C/M/I refs (pointing at the now-deleted backlog.md) are reset to
    NULL so the new classification pipeline can pick them up fresh.
    SKIP rows are preserved — they are system-generated rows that should never
    be processed.
    """
    with conn.cursor() as cur:
        for tbl in ("mem_mrr_prompts", "mem_mrr_commits", "mem_mrr_items", "mem_mrr_messages"):
            cur.execute(f"ALTER TABLE {tbl} RENAME COLUMN backlog_ref TO wi_id")
            # Reset old P/C/M/I refs — those pointed at the file-based backlog;
            # the new DB pipeline will re-classify them.
            cur.execute(
                f"UPDATE {tbl} SET wi_id = NULL "
                f"WHERE wi_id IS NOT NULL AND wi_id != 'SKIP'"
            )
            # Rename the partial index (backlog_ref IS NULL → wi_id IS NULL)
            short = tbl.replace("mem_mrr_", "")[:8]
            old_idx = f"idx_{short}_bref"
            new_idx = f"idx_{short}_wi_pending"
            cur.execute(f"DROP INDEX IF EXISTS {old_idx}")
            cur.execute(
                f"CREATE INDEX IF NOT EXISTS {new_idx} "
                f"ON {tbl}(project_id) WHERE wi_id IS NULL"
            )
    conn.commit()
    log.info(
        "m062: backlog_ref → wi_id renamed in 4 mem_mrr_* tables; "
        "non-SKIP refs reset to NULL for re-classification"
    )


def m063_create_mem_work_items(conn) -> None:
    """Create mem_work_items table — the DB-first replacement for backlog.md.

    Each row represents one classified work item (bug, feature, task, policy,
    or use_case).  Mirror rows (mem_mrr_*) link back via wi_id once approved.

    Levels:
      1 = raw event cluster (auto-generated)
      2 = bug / feature / task / policy
      3 = use_case (groups multiple level-2 items)
      4 = project (future)

    wi_id NULL means pending classification.
    wi_id 'BU0001' / 'FE0001' etc. means approved.
    wi_id starting 'REJ' means rejected.

    mrr_ids JSONB: {"prompts":["uuid1"],"commits":["hash1"],
                    "messages":["uuid2"],"items":["uuid3"]}
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mem_work_items (
                id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id        INT         REFERENCES mng_clients(id) ON DELETE CASCADE,
                project_id       INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                tags             JSONB       NOT NULL DEFAULT '{}',
                item_level       SMALLINT    NOT NULL DEFAULT 2,
                wi_id            TEXT,
                wi_type          TEXT,
                score_importance SMALLINT    DEFAULT 0
                                 CHECK (score_importance BETWEEN 0 AND 5),
                score_status     SMALLINT    DEFAULT 0
                                 CHECK (score_status BETWEEN 0 AND 5),
                name             TEXT,
                summary          TEXT,
                deliveries       TEXT,
                delivery_type    TEXT,
                mrr_ids          JSONB       NOT NULL DEFAULT '{}',
                wi_parent_id     UUID        REFERENCES mem_work_items(id) ON DELETE SET NULL,
                approved_at      TIMESTAMPTZ,
                created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                embedding        VECTOR(1536)
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_wi_project ON mem_work_items(project_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_wi_parent  ON mem_work_items(wi_parent_id)")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_wi_type ON mem_work_items(project_id, wi_type)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_wi_level ON mem_work_items(project_id, item_level)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_wi_pending "
            "ON mem_work_items(project_id, wi_id) WHERE wi_id IS NULL"
        )
        # updated_at trigger
        cur.execute("DROP TRIGGER IF EXISTS trg_updated_at_mem_work_items ON mem_work_items")
        cur.execute("""
            CREATE TRIGGER trg_updated_at_mem_work_items
            BEFORE UPDATE ON mem_work_items
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """)
        # Seed WI_* sequence counters for all existing projects
        for key, start in [
            ("WI_US", 1000),
            ("WI_FE", 2000),
            ("WI_BU", 3000),
            ("WI_TA", 4000),
            ("WI_PO", 5000),
        ]:
            # Global key (project_id=NULL via category key)
            cur.execute(
                """INSERT INTO pr_seq_counters (project_id, category, next_val)
                   SELECT id, %s, %s FROM mng_projects ON CONFLICT DO NOTHING""",
                (key, start + 1),
            )
    conn.commit()
    log.info("m063: mem_work_items table created; WI_US/FE/BU/TA/PO seq counters seeded")


def m064_add_policy_category(conn) -> None:
    """Seed the 'policy' tag category (if not already present).

    policy: mandatory rules and standards (security, auth, naming conventions).
    Sequence range PO 5000+ via WI_PO counter (seeded in m063).
    """
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO mng_tags_categories (client_id, name, color, icon, description)
               VALUES (1, 'policy', '#8b5cf6', '⚑', 'Mandatory rule or standard (PO 5000+)')
               ON CONFLICT (client_id, name) DO NOTHING"""
        )
    conn.commit()
    log.info("m064: policy tag category seeded")


def m065_add_requirement_type(conn) -> None:
    """Add requirement wi_type: seed WI_RE seq counter + tag category."""
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO pr_seq_counters (project_id, category, next_val)
               SELECT id, 'WI_RE', 6001 FROM mng_projects ON CONFLICT DO NOTHING"""
        )
        cur.execute(
            """INSERT INTO mng_tags_categories (client_id, name, color, icon, description)
               VALUES (1, 'requirement', '#f59e0b', '◎',
                       'Spec/user story not yet delivered (RE 6000+)')
               ON CONFLICT (client_id, name) DO NOTHING"""
        )
    conn.commit()
    log.info("m065: WI_RE seq counter seeded (6001) + requirement tag category added")


def m066_wi_ai_temp_ids(conn) -> None:
    """Switch pending work items to AI-temp-ID scheme.

    Deletes all wi_id=NULL rows (old pending style) from mem_work_items so
    they get re-classified as AI0001/AI0002/… on the next classify run.
    mem_mrr_* rows keep wi_id=NULL and will be re-picked up automatically.
    """
    with conn.cursor() as cur:
        cur.execute("DELETE FROM mem_work_items WHERE wi_id IS NULL")
        deleted = cur.rowcount
    conn.commit()
    log.info("m066: cleared %d pending wi_id=NULL work items (re-classify to get AI temp IDs)", deleted)


def m067_add_user_importance_status(conn) -> None:
    """Add user_importance and user_status to mem_work_items for user-controlled ordering.

    By default they mirror the AI score columns, but users can override them
    independently (drag-to-reorder updates user_importance; status popover updates
    user_status). All UI sorting and display is based on these user columns.
    """
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE mem_work_items
              ADD COLUMN IF NOT EXISTS user_importance SMALLINT,
              ADD COLUMN IF NOT EXISTS user_status     SMALLINT;
            UPDATE mem_work_items
               SET user_importance = COALESCE(score_importance, 0),
                   user_status     = COALESCE(score_status, 0)
             WHERE user_importance IS NULL OR user_status IS NULL;
        """)
    conn.commit()
    log.info("m067: added user_importance/user_status to mem_work_items")


def m068_create_wi_versions(conn) -> None:
    """Create mem_wi_versions table for use-case snapshot versioning.

    Each version stores an ordered snapshot of a use case's items
    at a point in time. Status: active (current), draft (AI-generated
    pending review), archived (older approved snapshots).
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mem_wi_versions (
              id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
              project_id  INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
              uc_id       UUID        NOT NULL REFERENCES mem_work_items(id) ON DELETE CASCADE,
              version_num SMALLINT    NOT NULL DEFAULT 1,
              name        TEXT        NOT NULL,
              summary     TEXT,
              snapshot    JSONB       NOT NULL DEFAULT '[]',
              created_by  TEXT        NOT NULL DEFAULT 'user',
              status      TEXT        NOT NULL DEFAULT 'active',
              created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              UNIQUE (uc_id, version_num)
            );
            CREATE INDEX IF NOT EXISTS idx_wi_versions_uc ON mem_wi_versions (uc_id);
        """)
    conn.commit()
    log.info("m068: created mem_wi_versions table")


def m069_src_column_and_cleanup(conn) -> None:
    """Add dedicated src column to mirror tables; remove source from JSONB tags; drop llm.

    Previously the source system (claude_cli, git, aicli…) was stored inside
    the user-facing JSONB tags column, polluting it with system metadata.
    This migration moves it to a clean TEXT column `src` on each table.

    Also drops the orphaned `llm` column from mem_mrr_commits which was never
    written to by any current code path.
    """
    with conn.cursor() as cur:
        # mem_mrr_prompts: add src, backfill from tags, strip from tags
        cur.execute("""
            ALTER TABLE mem_mrr_prompts
              ADD COLUMN IF NOT EXISTS src TEXT NOT NULL DEFAULT 'claude_cli';
        """)
        cur.execute("""
            UPDATE mem_mrr_prompts
               SET src = COALESCE(tags->>'source', 'claude_cli')
             WHERE src = 'claude_cli';
        """)
        cur.execute("""
            UPDATE mem_mrr_prompts
               SET tags = tags - 'source' - 'llm'
             WHERE tags ? 'source' OR tags ? 'llm';
        """)

        # mem_mrr_commits: add src, backfill from tags, strip from tags, drop llm column
        cur.execute("""
            ALTER TABLE mem_mrr_commits
              ADD COLUMN IF NOT EXISTS src TEXT NOT NULL DEFAULT 'git';
        """)
        cur.execute("""
            UPDATE mem_mrr_commits
               SET src = COALESCE(tags->>'source', 'git')
             WHERE src = 'git';
        """)
        cur.execute("""
            UPDATE mem_mrr_commits
               SET tags = tags - 'source' - 'llm'
             WHERE tags ? 'source' OR tags ? 'llm';
        """)
        cur.execute("ALTER TABLE mem_mrr_commits DROP COLUMN IF EXISTS llm;")

        # Index for fast src-based filtering
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prompts_src ON mem_mrr_prompts(project_id, src);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_commits_src ON mem_mrr_commits(project_id, src);")
    conn.commit()
    log.info("m069: src column added to prompts+commits; source/llm removed from tags; llm column dropped")


def m070_file_stats(conn) -> None:
    """Create mem_file_stats and mem_file_coupling for code hotspot tracking.

    mem_file_stats: per-project, per-file aggregated metrics updated after each commit.
    mem_file_coupling: co-change pairs (files committed together frequently).
    hotspot_score: computed from bug fixes, change frequency, and file size.
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mem_file_stats (
              id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
              project_id       INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
              file_path        TEXT        NOT NULL,
              change_count     INT         NOT NULL DEFAULT 0,
              commit_count     INT         NOT NULL DEFAULT 0,
              author_count     INT         NOT NULL DEFAULT 0,
              bug_commit_count INT         NOT NULL DEFAULT 0,
              lines_added      INT         NOT NULL DEFAULT 0,
              lines_removed    INT         NOT NULL DEFAULT 0,
              revert_count     INT         NOT NULL DEFAULT 0,
              current_lines    INT         NOT NULL DEFAULT 0,
              hotspot_score    FLOAT       NOT NULL DEFAULT 0.0,
              last_changed_at  TIMESTAMPTZ,
              created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              UNIQUE (project_id, file_path)
            );
            CREATE INDEX IF NOT EXISTS idx_file_stats_proj
              ON mem_file_stats (project_id);
            CREATE INDEX IF NOT EXISTS idx_file_stats_score
              ON mem_file_stats (project_id, hotspot_score DESC);
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS mem_file_coupling (
              id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
              project_id      INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
              file_a          TEXT        NOT NULL,
              file_b          TEXT        NOT NULL,
              co_change_count INT         NOT NULL DEFAULT 1,
              coupling_score  FLOAT       NOT NULL DEFAULT 0.0,
              last_co_change  TIMESTAMPTZ,
              created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              UNIQUE (project_id, file_a, file_b)
            );
            CREATE INDEX IF NOT EXISTS idx_file_coupling_proj
              ON mem_file_coupling (project_id);
            CREATE INDEX IF NOT EXISTS idx_file_coupling_a
              ON mem_file_coupling (project_id, file_a);
            CREATE INDEX IF NOT EXISTS idx_file_coupling_b
              ON mem_file_coupling (project_id, file_b);
        """)
    conn.commit()
    log.info("m070: mem_file_stats + mem_file_coupling created")


def m071_drop_score_tag(conn) -> None:
    """Drop score_tag from mem_work_items — removed as unnecessary complexity."""
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE mem_work_items DROP COLUMN IF EXISTS score_tag")
    conn.commit()
    log.info("m071: score_tag dropped from mem_work_items")


def m072_wi_dates(conn) -> None:
    """Add start_date and due_date to mem_work_items for timeline planning."""
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE mem_work_items
              ADD COLUMN IF NOT EXISTS start_date DATE,
              ADD COLUMN IF NOT EXISTS due_date   DATE;
            CREATE INDEX IF NOT EXISTS idx_wi_due_date ON mem_work_items (project_id, due_date)
              WHERE due_date IS NOT NULL;
        """)
    conn.commit()
    log.info("m072: start_date, due_date added to mem_work_items")


def m073_prompts_source_id_unique(conn) -> None:
    """Add unique partial index on mem_mrr_prompts(project_id, source_id) to fix ON CONFLICT.

    The hook-log endpoint uses ON CONFLICT (project_id, source_id) WHERE source_id IS NOT NULL
    but the matching index was never created, causing every hook call to fail with a constraint
    error and silently discard all prompts since April 15.
    """
    with conn.cursor() as cur:
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_prompts_project_source
            ON mem_mrr_prompts (project_id, source_id)
            WHERE source_id IS NOT NULL;
        """)
    conn.commit()
    log.info("m073: unique index idx_prompts_project_source created on mem_mrr_prompts")


def m074_wi_completed(conn) -> None:
    """Add completed_at to mem_work_items for use-case lifecycle tracking."""
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE mem_work_items
              ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
            CREATE INDEX IF NOT EXISTS idx_wi_completed ON mem_work_items (project_id, completed_at)
              WHERE completed_at IS NOT NULL;
        """)
    conn.commit()
    log.info("m074: completed_at added to mem_work_items")


def m075_wi_deleted(conn) -> None:
    """Soft-delete column for work items — set when user removes item from MD."""
    with conn.cursor() as cur:
        cur.execute(
            "ALTER TABLE mem_work_items ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ"
        )
    conn.commit()
    log.info("m075: deleted_at added to mem_work_items")


def m076_wi_merged_into(conn) -> None:
    """Add merged_into self-FK to mem_work_items for item merge (combine summaries)."""
    with conn.cursor() as cur:
        cur.execute(
            "ALTER TABLE mem_work_items "
            "ADD COLUMN IF NOT EXISTS merged_into UUID REFERENCES mem_work_items(id) ON DELETE SET NULL"
        )
    conn.commit()
    log.info("m076: merged_into added to mem_work_items")


def m077_commit_history(conn) -> None:
    """Rename file stats tables to mrr namespace; add is_external + commit_type to commits.

    1. Rename mem_file_stats → mem_mrr_commits_file_stats
    2. Rename mem_file_coupling → mem_mrr_commits_file_coupling
    3. Add is_external BOOLEAN to mem_mrr_commits (flags commits from external collaborators)
    4. Add commit_type TEXT to mem_mrr_commits (conventional prefix: feat/fix/chore/test/refactor)
    """
    with conn.cursor() as cur:
        # 1 & 2. Rename file stats tables to mrr namespace
        cur.execute("ALTER TABLE IF EXISTS mem_file_stats RENAME TO mem_mrr_commits_file_stats")
        cur.execute("ALTER TABLE IF EXISTS mem_file_coupling RENAME TO mem_mrr_commits_file_coupling")
        # Recreate indexes under new names
        for idx in ["idx_mfs_project_score", "idx_mfs_project_path", "idx_mfc_project_file_a"]:
            cur.execute(f"DROP INDEX IF EXISTS {idx}")
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mfs_project_score "
            "ON mem_mrr_commits_file_stats(project_id, hotspot_score DESC)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mfs_project_path "
            "ON mem_mrr_commits_file_stats(project_id, file_path)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_mfc_project_file_a "
            "ON mem_mrr_commits_file_coupling(project_id, file_a)"
        )
        # 3 & 4. New columns on mem_mrr_commits
        cur.execute(
            "ALTER TABLE mem_mrr_commits "
            "ADD COLUMN IF NOT EXISTS is_external BOOLEAN DEFAULT FALSE"
        )
        cur.execute(
            "ALTER TABLE mem_mrr_commits "
            "ADD COLUMN IF NOT EXISTS commit_type TEXT DEFAULT NULL"
        )
    conn.commit()
    log.info("m077: file stats tables renamed to mrr namespace; is_external + commit_type added to mem_mrr_commits")


def m078_drop_planner_tags(conn) -> None:
    """Drop planner_tags and all dependent tables (replaced by mem_work_items / Use Cases).

    Dropped tables (in FK dependency order):
      mem_ai_feature_snapshot  — FK to planner_tags.id
      mem_backlog_links        — FK to planner_tags.id (old file-based backlog, unused)
      planner_tag_deps         — FK to planner_tags.id (from m058)
      planner_tags             — CASCADE handles self-FKs (parent_id, merged_into)
      mng_tags_categories      — only used by planner_tags.category_id
      mng_deliveries           — only used by planner_tags.deliveries JSONB
    """
    with conn.cursor() as cur:
        # Drop any FK columns on mem_work_items that reference planner_tags
        cur.execute("ALTER TABLE mem_work_items DROP COLUMN IF EXISTS tag_id_ai")
        cur.execute("ALTER TABLE mem_work_items DROP COLUMN IF EXISTS tag_id_user")
        # Drop dependent tables
        cur.execute("DROP TABLE IF EXISTS mem_ai_feature_snapshot CASCADE")
        cur.execute("DROP TABLE IF EXISTS mem_backlog_links CASCADE")
        cur.execute("DROP TABLE IF EXISTS planner_tag_deps CASCADE")
        cur.execute("DROP TABLE IF EXISTS planner_tags CASCADE")
        cur.execute("DROP TABLE IF EXISTS mng_tags_categories CASCADE")
        cur.execute("DROP TABLE IF EXISTS mng_deliveries CASCADE")
    conn.commit()
    log.info("m078_drop_planner_tags: planner_tags and dependencies dropped")


def m061_rebuild_backlog_links(conn) -> None:
    """Rebuild mem_backlog_links with richer schema.

    New columns vs old:
      client_id     INT       — links to mng_clients
      user_id       INT       — user who approved (NULL for automated runs)
      tag_name      TEXT      — name of the linked planner_tag (avoids extra join)
      use_case_id   UUID FK   — UUID of the parent use-case planner_tag
      is_llm        BOOL      — TRUE for AI-generated delivery items (child tags);
                                FALSE for mirror-table events (P/C/M/I refs)
      created_at    TIMESTAMPTZ — replaces approved_at
      updated_at    TIMESTAMPTZ

    Distinction:
      Mirror events   → is_llm=FALSE, ref_id='P100042', tag_id=use_case_tag_id
      AI deliveries   → is_llm=TRUE,  ref_id=child_tag_uuid, tag_id=child_tag_id,
                        use_case_id=parent_use_case_tag_id
    """
    with conn.cursor() as cur:
        # Drop old table (data will be lost — re-populated on next approval run)
        cur.execute("DROP TABLE IF EXISTS mem_backlog_links CASCADE")
        cur.execute("""
            CREATE TABLE mem_backlog_links (
                id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
                client_id     INT         REFERENCES mng_clients(id) ON DELETE CASCADE,
                project_id    INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
                user_id       INT         REFERENCES mng_users(id) ON DELETE SET NULL,
                ref_id        TEXT        NOT NULL,
                tag_id        UUID        REFERENCES planner_tags(id) ON DELETE SET NULL,
                tag_name      TEXT,
                use_case_id   UUID        REFERENCES planner_tags(id) ON DELETE SET NULL,
                use_case_slug TEXT        NOT NULL,
                classify      TEXT,
                is_llm        BOOLEAN     NOT NULL DEFAULT FALSE,
                summary       TEXT,
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                UNIQUE (project_id, ref_id)
            )
        """)
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_backlog_links_tag     "
            "ON mem_backlog_links(tag_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_backlog_links_uc      "
            "ON mem_backlog_links(use_case_id)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_backlog_links_proj    "
            "ON mem_backlog_links(project_id, use_case_slug)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_backlog_links_proj_uc "
            "ON mem_backlog_links(project_id, use_case_id)"
        )
    conn.commit()
    log.info("m061: mem_backlog_links rebuilt with client_id, user_id, tag_name, use_case_id, is_llm")


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
    ("m025_rename_work_item_ai_columns", m025_rename_work_item_ai_columns),
    ("m026_planner_tags_cleanup", m026_planner_tags_cleanup),
    ("m027_planner_tags_drop_ai_cols", m027_planner_tags_drop_ai_cols),
    ("m028_add_deliveries", m028_add_deliveries),
    ("m029_feature_snapshot", m029_feature_snapshot),
    ("m030_pipeline_runs", m030_pipeline_runs),
    ("m031_commits_cleanup", m031_commits_cleanup),
    ("m032_events_and_prompts_event_id", m032_events_and_prompts_event_id),
    ("m033_reorder_mem_mrr_commits", m033_reorder_mem_mrr_commits),
    ("m034_reorder_mem_ai_events", m034_reorder_mem_ai_events),
    ("m035_reorder_mem_mrr_commits", m035_reorder_mem_mrr_commits),
    ("m036_reorder_mem_ai_events", m036_reorder_mem_ai_events),
    ("m037_drop_events_importance", m037_drop_events_importance),
    ("m038_drop_commits_code_embedding", m038_drop_commits_code_embedding),
    ("m039_reorder_mem_mrr_prompts", m039_reorder_mem_mrr_prompts),
    ("m040_backfill_event_cnt_and_tags", m040_backfill_event_cnt_and_tags),
    ("m041_drop_diff_file_chunks", m041_drop_diff_file_chunks),
    ("m042_drop_source_event_id", m042_drop_source_event_id),
    ("m043_drop_status_ai_code_summary", m043_drop_status_ai_code_summary),
    ("m044_drop_desc_ai", m044_drop_desc_ai),
    ("m045_add_score_ai", m045_add_score_ai),
    ("m046_reorder_work_items", m046_reorder_work_items),
    ("m047_events_is_system", m047_events_is_system),
    ("m048_user_id_mirror_tables", m048_user_id_mirror_tables),
    ("m049_work_item_quality_gate", m049_work_item_quality_gate),
    ("m050_prompts_source_id_index", m050_prompts_source_id_index),
    ("m051_schema_refactor_user_id_updated_at", m051_schema_refactor_user_id_updated_at),
    ("m052_column_reorder", m052_column_reorder),
    ("m053_pr_statistics", m053_pr_statistics),
    ("m054_backlog_ref", m054_backlog_ref),
    ("m055_cleanup_and_seq", m055_cleanup_and_seq),
    ("m056_drop_event_id_add_backlog_links", m056_drop_event_id_add_backlog_links),
    ("m057_drop_events_and_work_items", m057_drop_events_and_work_items),
    ("m058_tag_deps", m058_tag_deps),
    ("m059_drop_legacy_tables", m059_drop_legacy_tables),
    ("m060_drop_feature_snapshot", m060_drop_feature_snapshot),
    ("m061_rebuild_backlog_links", m061_rebuild_backlog_links),
    ("m062_rename_backlog_ref_to_wi_id", m062_rename_backlog_ref_to_wi_id),
    ("m063_create_mem_work_items", m063_create_mem_work_items),
    ("m064_add_policy_category", m064_add_policy_category),
    ("m065_add_requirement_type", m065_add_requirement_type),
    ("m066_wi_ai_temp_ids", m066_wi_ai_temp_ids),
    ("m067_add_user_importance_status", m067_add_user_importance_status),
    ("m068_create_wi_versions", m068_create_wi_versions),
    ("m069_src_column_and_cleanup", m069_src_column_and_cleanup),
    ("m070_file_stats", m070_file_stats),
    ("m071_drop_score_tag", m071_drop_score_tag),
    ("m072_wi_dates", m072_wi_dates),
    ("m073_prompts_source_id_unique", m073_prompts_source_id_unique),
    ("m074_wi_completed", m074_wi_completed),
    ("m075_wi_deleted",   m075_wi_deleted),
    ("m076_wi_merged_into", m076_wi_merged_into),
    ("m077_commit_history", m077_commit_history),
    ("m078_drop_planner_tags", m078_drop_planner_tags),
]
