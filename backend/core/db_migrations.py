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
]
