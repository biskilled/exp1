"""
PostgreSQL connection pool.

Falls back gracefully when DATABASE_URL is not set — callers check `is_available()`.

Usage:
    from core.database import db

    if db.is_available():
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT ...")
    else:
        # fall back to file-based storage
"""

from __future__ import annotations

import logging
import re
from contextlib import contextmanager
from typing import Generator

import psycopg2
import psycopg2.pool

from config import settings

log = logging.getLogger(__name__)


class _Database:
    def __init__(self) -> None:
        self._pool: psycopg2.pool.ThreadedConnectionPool | None = None
        self._available: bool = False
        # Projects whose per-project schema has been verified this process lifetime.
        # Skips all DDL/ALTER on subsequent calls — safe because CREATE/ALTER are idempotent.
        self._schema_ready: set[str] = set()

    def init(self) -> None:
        """Called at startup. Creates connection pool if DATABASE_URL is set."""
        url = settings.database_url
        if not url:
            log.info("DATABASE_URL not set — using file-based storage")
            return
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(1, settings.db_pool_max, url)
            # Verify connection and create tables
            with self.conn() as conn:
                self._rename_legacy_tables(conn)
                self._ensure_schema(conn)
            self._available = True
            log.info("✅ PostgreSQL connected — user store: database")
        except Exception as e:
            log.warning(f"PostgreSQL unavailable ({e}) — falling back to file store")
            self._pool = None
            self._available = False

    def is_available(self) -> bool:
        return self._available

    @staticmethod
    def project_table(base: str, project: str, client: str = "local") -> str:
        """Return per-project table name, e.g. pr_local_aicli_commits."""
        safe = re.sub(r'[^a-z0-9]', '_', project.lower())[:40].strip('_')
        return f"pr_{client}_{safe}_{base}"

    def ensure_project_schema(self, project: str) -> None:
        """Create per-project tables if they don't exist. Safe to call repeatedly.

        Results are cached in-process: the DDL only runs once per project per process
        lifetime, eliminating the round-trip cost on every subsequent project open.
        """
        if not self._available:
            return
        if project in self._schema_ready:
            return   # already done this process lifetime — skip all DDL
        tbl  = self.project_table
        c    = tbl("commits",          project)
        e    = tbl("events",           project)
        emb  = tbl("embeddings",       project)
        et   = tbl("event_tags",       project)
        el   = tbl("event_links",      project)
        wi   = tbl("work_items",       project)
        int_ = tbl("interactions",     project)
        itag = tbl("interaction_tags", project)
        mi   = tbl("memory_items",     project)
        pf   = tbl("project_facts",    project)
        gw   = tbl("graph_workflows",    project)
        gn   = tbl("graph_nodes",        project)
        ge   = tbl("graph_edges",        project)
        gr   = tbl("graph_runs",         project)
        gnr  = tbl("graph_node_results", project)
        ddl = f"""
        CREATE TABLE IF NOT EXISTS {c} (
            id           SERIAL         PRIMARY KEY,
            commit_hash  VARCHAR(40)    NOT NULL,
            commit_msg   TEXT           NOT NULL DEFAULT '',
            summary      TEXT           NOT NULL DEFAULT '',
            phase        VARCHAR(20),
            feature      VARCHAR(255),
            bug_ref      VARCHAR(255),
            source       VARCHAR(50)    NOT NULL DEFAULT 'git',
            session_id        VARCHAR(255),
            prompt_source_id  VARCHAR(255),
            tags              JSONB          NOT NULL DEFAULT '{{}}',
            committed_at      TIMESTAMPTZ,
            created_at        TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(commit_hash)
        );
        CREATE INDEX IF NOT EXISTS idx_{c}_committed ON {c}(committed_at DESC);

        CREATE TABLE IF NOT EXISTS {e} (
            id         SERIAL         PRIMARY KEY,
            event_type VARCHAR(50)    NOT NULL,
            source_id  VARCHAR(255)   NOT NULL,
            title      TEXT           NOT NULL DEFAULT '',
            content    TEXT           NOT NULL DEFAULT '',
            phase      VARCHAR(20),
            feature    VARCHAR(255),
            session_id VARCHAR(255),
            metadata   JSONB          NOT NULL DEFAULT '{{}}',
            created_at TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(event_type, source_id)
        );
        CREATE INDEX IF NOT EXISTS idx_{e}_type    ON {e}(event_type);
        CREATE INDEX IF NOT EXISTS idx_{e}_created ON {e}(created_at DESC);

        CREATE TABLE IF NOT EXISTS {emb} (
            id          SERIAL         PRIMARY KEY,
            source_type VARCHAR(50)    NOT NULL,
            source_id   VARCHAR(255)   NOT NULL,
            chunk_index INT            NOT NULL DEFAULT 0,
            content     TEXT           NOT NULL,
            embedding   vector(1536),
            chunk_type  VARCHAR(50)    NOT NULL DEFAULT 'full',
            doc_type    VARCHAR(50),
            language    VARCHAR(30),
            file_path   VARCHAR(500),
            metadata    JSONB          NOT NULL DEFAULT '{{}}',
            created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(source_type, source_id, chunk_index)
        );
        CREATE INDEX IF NOT EXISTS idx_{emb}_lang ON {emb}(language) WHERE language IS NOT NULL;

        CREATE TABLE IF NOT EXISTS {et} (
            event_id        INT         NOT NULL,
            entity_value_id INT         NOT NULL REFERENCES mng_entity_values(id) ON DELETE CASCADE,
            auto_tagged     BOOLEAN     NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(event_id, entity_value_id)
        );
        CREATE INDEX IF NOT EXISTS idx_{et}_event ON {et}(event_id);
        CREATE INDEX IF NOT EXISTS idx_{et}_value ON {et}(entity_value_id);

        CREATE TABLE IF NOT EXISTS {el} (
            from_event_id INT         NOT NULL,
            to_event_id   INT         NOT NULL,
            link_type     VARCHAR(50) NOT NULL,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(from_event_id, to_event_id, link_type)
        );
        CREATE INDEX IF NOT EXISTS idx_{el}_from ON {el}(from_event_id);

        -- Work items: feature/bug/task items with pipeline tracking (per-project)
        CREATE TABLE IF NOT EXISTS {wi} (
            id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
            project             TEXT          NOT NULL,
            category_name       TEXT          NOT NULL,
            category_id         INT           REFERENCES mng_entity_categories(id) ON DELETE SET NULL,
            name                TEXT          NOT NULL,
            description         TEXT          NOT NULL DEFAULT '',
            status              VARCHAR(20)   NOT NULL DEFAULT 'active',
            lifecycle_status    VARCHAR(20)   NOT NULL DEFAULT 'idea',
            due_date            DATE,
            parent_id           UUID          REFERENCES {wi}(id) ON DELETE SET NULL,
            acceptance_criteria TEXT          NOT NULL DEFAULT '',
            implementation_plan TEXT          NOT NULL DEFAULT '',
            agent_run_id        UUID,
            agent_status        VARCHAR(20),
            tags                TEXT[]        NOT NULL DEFAULT '{{}}',
            created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            UNIQUE(project, category_name, name)
        );
        CREATE INDEX IF NOT EXISTS idx_{wi}_project  ON {wi}(project);
        CREATE INDEX IF NOT EXISTS idx_{wi}_category ON {wi}(category_name);
        CREATE INDEX IF NOT EXISTS idx_{wi}_status   ON {wi}(status);

        -- Interactions: unified prompt/response log (per-project)
        CREATE TABLE IF NOT EXISTS {int_} (
            id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id          TEXT          NOT NULL,
            work_item_id        UUID          REFERENCES {wi}(id) ON DELETE SET NULL,
            session_id          TEXT,
            llm_source          TEXT,
            event_type          TEXT          NOT NULL DEFAULT 'prompt',
            source_id           TEXT,
            prompt              TEXT          NOT NULL DEFAULT '',
            response            TEXT          NOT NULL DEFAULT '',
            prompt_embedding    VECTOR(1536),
            response_embedding  VECTOR(1536),
            phase               TEXT,
            tags                TEXT[]        NOT NULL DEFAULT '{{}}',
            metadata            JSONB         NOT NULL DEFAULT '{{}}',
            created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_{int_}_project  ON {int_}(project_id);
        CREATE INDEX IF NOT EXISTS idx_{int_}_session  ON {int_}(session_id)   WHERE session_id IS NOT NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_{int_}_source ON {int_}(project_id, source_id) WHERE source_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_{int_}_created  ON {int_}(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_{int_}_workitem ON {int_}(work_item_id) WHERE work_item_id IS NOT NULL;

        -- Interaction tags: links interactions to work items (per-project)
        CREATE TABLE IF NOT EXISTS {itag} (
            interaction_id  UUID          NOT NULL REFERENCES {int_}(id)  ON DELETE CASCADE,
            work_item_id    UUID          NOT NULL REFERENCES {wi}(id)    ON DELETE CASCADE,
            auto_tagged     BOOLEAN       NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            PRIMARY KEY(interaction_id, work_item_id)
        );
        CREATE INDEX IF NOT EXISTS idx_{itag}_work ON {itag}(work_item_id);

        -- Memory items: distilled session/feature summaries (per-project)
        CREATE TABLE IF NOT EXISTS {mi} (
            id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id      TEXT          NOT NULL,
            scope           TEXT          NOT NULL,
            scope_ref       TEXT,
            content         TEXT          NOT NULL,
            embedding       VECTOR(1536),
            source_ids      UUID[]        NOT NULL DEFAULT '{{}}',
            tags            TEXT[]        NOT NULL DEFAULT '{{}}',
            reviewer_score  INT,
            reviewer_critique TEXT,
            created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_{mi}_project ON {mi}(project_id);
        CREATE INDEX IF NOT EXISTS idx_{mi}_scope   ON {mi}(project_id, scope);
        CREATE INDEX IF NOT EXISTS idx_{mi}_created ON {mi}(created_at DESC);

        -- Project facts: durable extracted facts (per-project; valid_until NULL = current)
        CREATE TABLE IF NOT EXISTS {pf} (
            id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id       TEXT          NOT NULL,
            fact_key         TEXT          NOT NULL,
            fact_value       TEXT          NOT NULL,
            valid_from       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            valid_until      TIMESTAMPTZ,
            source_memory_id UUID          REFERENCES {mi}(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS        idx_{pf}_project ON {pf}(project_id)            WHERE valid_until IS NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_{pf}_current ON {pf}(project_id, fact_key)  WHERE valid_until IS NULL;

        -- Graph workflow definitions (per-project pipelines)
        CREATE TABLE IF NOT EXISTS {gw} (
            id             UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
            project        VARCHAR(255)   NOT NULL,
            name           VARCHAR(255)   NOT NULL,
            description    TEXT           NOT NULL DEFAULT '',
            max_iterations INTEGER        NOT NULL DEFAULT 3,
            created_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(project, name)
        );
        CREATE INDEX IF NOT EXISTS idx_{gw}_project ON {gw}(project);

        -- Graph nodes (LLM steps within a workflow)
        CREATE TABLE IF NOT EXISTS {gn} (
            id               UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
            workflow_id      UUID           NOT NULL REFERENCES {gw}(id) ON DELETE CASCADE,
            name             VARCHAR(255)   NOT NULL,
            role_id          INT            REFERENCES mng_agent_roles(id) ON DELETE SET NULL,
            role_file        VARCHAR(255),
            role_prompt      TEXT           NOT NULL DEFAULT '',
            provider         VARCHAR(50)    NOT NULL DEFAULT 'claude',
            model            VARCHAR(100)   NOT NULL DEFAULT '',
            output_schema    JSONB,
            inject_context   BOOLEAN        NOT NULL DEFAULT TRUE,
            require_approval BOOLEAN        NOT NULL DEFAULT FALSE,
            approval_msg     TEXT           NOT NULL DEFAULT '',
            position_x       REAL           NOT NULL DEFAULT 100,
            position_y       REAL           NOT NULL DEFAULT 100,
            created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_{gn}_workflow ON {gn}(workflow_id);

        -- Graph edges (connections between nodes)
        CREATE TABLE IF NOT EXISTS {ge} (
            id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            workflow_id    UUID         NOT NULL REFERENCES {gw}(id) ON DELETE CASCADE,
            source_node_id UUID         NOT NULL REFERENCES {gn}(id) ON DELETE CASCADE,
            target_node_id UUID         NOT NULL REFERENCES {gn}(id) ON DELETE CASCADE,
            condition      JSONB,
            label          VARCHAR(255) NOT NULL DEFAULT '',
            created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_{ge}_workflow ON {ge}(workflow_id);

        -- Workflow run instances
        CREATE TABLE IF NOT EXISTS {gr} (
            id             UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
            workflow_id    UUID           NOT NULL REFERENCES {gw}(id) ON DELETE CASCADE,
            project        VARCHAR(255)   NOT NULL,
            status         VARCHAR(50)    NOT NULL DEFAULT 'running',
            user_input     TEXT           NOT NULL DEFAULT '',
            context        JSONB          NOT NULL DEFAULT '{{}}',
            started_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            finished_at    TIMESTAMPTZ,
            total_cost_usd NUMERIC(12, 8) NOT NULL DEFAULT 0,
            error          TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_{gr}_workflow ON {gr}(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_{gr}_project  ON {gr}(project);

        -- Results per node per run
        CREATE TABLE IF NOT EXISTS {gnr} (
            id            SERIAL         PRIMARY KEY,
            run_id        UUID           NOT NULL REFERENCES {gr}(id) ON DELETE CASCADE,
            node_id       UUID           NOT NULL REFERENCES {gn}(id) ON DELETE CASCADE,
            node_name     VARCHAR(255)   NOT NULL DEFAULT '',
            status        VARCHAR(50)    NOT NULL DEFAULT 'running',
            output        TEXT           NOT NULL DEFAULT '',
            structured    JSONB,
            input_tokens  INT            NOT NULL DEFAULT 0,
            output_tokens INT            NOT NULL DEFAULT 0,
            cost_usd      NUMERIC(12, 8) NOT NULL DEFAULT 0,
            started_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            finished_at   TIMESTAMPTZ,
            iteration     INT            NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_{gnr}_run  ON {gnr}(run_id);
        CREATE INDEX IF NOT EXISTS idx_{gnr}_node ON {gnr}(node_id);
        """
        # All DDL + migrations in a single transaction — one round-trip instead of 14.
        # Each statement is wrapped in a SAVEPOINT so a single failure (e.g. column
        # already exists on Postgres < 9.6) doesn't roll back the whole batch.
        _migrations = [
            f"ALTER TABLE {c} ADD COLUMN IF NOT EXISTS prompt_source_id VARCHAR(255)",
            f"ALTER TABLE {c} ADD COLUMN IF NOT EXISTS session_id        VARCHAR(255)",
            f"ALTER TABLE {e} ADD COLUMN IF NOT EXISTS phase             VARCHAR(20)",
            f"ALTER TABLE {e} ADD COLUMN IF NOT EXISTS feature           VARCHAR(255)",
            f"ALTER TABLE {e} ADD COLUMN IF NOT EXISTS session_id        VARCHAR(255)",
            f"CREATE INDEX IF NOT EXISTS idx_{e}_session ON {e}(session_id) WHERE session_id IS NOT NULL",
            f"CREATE INDEX IF NOT EXISTS idx_{e}_phase   ON {e}(phase)      WHERE phase IS NOT NULL",
            f"CREATE INDEX IF NOT EXISTS idx_{el}_to     ON {el}(to_event_id)",
            f"CREATE INDEX IF NOT EXISTS idx_{c}_session ON {c}(session_id) WHERE session_id IS NOT NULL",
            f"CREATE INDEX IF NOT EXISTS idx_{emb}_src   ON {emb}(source_type, source_id)",
            "ALTER TABLE mng_entity_values ADD COLUMN IF NOT EXISTS lifecycle_status VARCHAR(20) NOT NULL DEFAULT 'idea'",
            """CREATE TABLE IF NOT EXISTS mng_entity_value_links (
                from_value_id INT NOT NULL REFERENCES mng_entity_values(id) ON DELETE CASCADE,
                to_value_id   INT NOT NULL REFERENCES mng_entity_values(id) ON DELETE CASCADE,
                link_type     VARCHAR(50) NOT NULL DEFAULT 'blocks',
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY(from_value_id, to_value_id, link_type)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_evl_from ON mng_entity_value_links(from_value_id)",
            "CREATE INDEX IF NOT EXISTS idx_evl_to   ON mng_entity_value_links(to_value_id)",
        ]
        try:
            with self.conn() as conn:
                with conn.cursor() as cur:
                    # Main table DDL
                    cur.execute(ddl)
                    # Migrations — each in its own savepoint so one failure doesn't abort all
                    for i, sql in enumerate(_migrations):
                        sp = f"sp_mig_{i}"
                        try:
                            cur.execute(f"SAVEPOINT {sp}")
                            cur.execute(sql)
                            cur.execute(f"RELEASE SAVEPOINT {sp}")
                        except Exception:
                            cur.execute(f"ROLLBACK TO SAVEPOINT {sp}")
            self._schema_ready.add(project)
            log.info(f"✅ Per-project schema ready for '{project}'")
        except Exception as exc:
            log.warning(f"ensure_project_schema({project}) failed: {exc}")

    @contextmanager
    def conn(self) -> Generator:
        if not self._pool:
            raise RuntimeError("PostgreSQL not initialised")
        connection = self._pool.getconn()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            self._pool.putconn(connection)

    @staticmethod
    def _rename_legacy_tables(conn) -> None:
        """One-time migration: rename old table names to new mng_/pr_ convention.

        Idempotent — uses ALTER TABLE IF EXISTS so it's safe to run on every startup.
        Tables that have already been renamed are silently skipped.
        """
        # Global shared tables: old_name → new_name
        _GLOBAL_RENAMES = [
            ("users",               "mng_users"),
            ("usage_logs",          "mng_usage_logs"),
            ("transactions",        "mng_transactions"),
            ("session_tags",        "mng_session_tags"),
            ("entity_categories",   "mng_entity_categories"),
            ("entity_values",       "mng_entity_values"),
            ("entity_value_links",  "mng_entity_value_links"),
            ("agent_roles",         "mng_agent_roles"),
            ("agent_role_versions", "mng_agent_role_versions"),
        ]

        # Per-project table patterns: old suffix → new base name (client fixed to "local")
        # e.g. commits_aicli → pr_local_aicli_commits
        _PROJECT_BASES = ["commits", "events", "embeddings", "event_tags", "event_links"]

        renamed_count = 0
        try:
            with conn.cursor() as cur:
                # Rename global tables
                for old, new in _GLOBAL_RENAMES:
                    try:
                        cur.execute(f"ALTER TABLE IF EXISTS {old} RENAME TO {new}")
                        conn.commit()
                        renamed_count += 1
                    except Exception:
                        conn.rollback()

                # Discover and rename per-project tables
                for base in _PROJECT_BASES:
                    try:
                        cur.execute(
                            "SELECT tablename FROM pg_tables WHERE schemaname='public' "
                            "AND tablename LIKE %s AND tablename NOT LIKE 'pr_%'",
                            (f"{base}_%",),
                        )
                        rows = cur.fetchall()
                        conn.commit()
                        for (tname,) in rows:
                            # Extract project suffix: "commits_aicli" → "aicli"
                            project_suffix = tname[len(base) + 1:]
                            new_name = f"pr_local_{project_suffix}_{base}"
                            try:
                                cur.execute(f"ALTER TABLE {tname} RENAME TO {new_name}")
                                conn.commit()
                                renamed_count += 1
                                log.info(f"  Renamed {tname} → {new_name}")
                            except Exception as e:
                                conn.rollback()
                                log.debug(f"  Skip rename {tname}: {e}")
                    except Exception as e:
                        conn.rollback()
                        log.debug(f"  Skip base {base}: {e}")

            if renamed_count:
                log.info(f"✅ Legacy table rename: {renamed_count} tables renamed to mng_/pr_ convention")
        except Exception as e:
            conn.rollback()
            log.warning(f"_rename_legacy_tables skipped: {e}")

    @staticmethod
    def _ensure_schema(conn) -> None:
        """Create tables and migrate missing columns — safe to run repeatedly."""

        _DDL_EMBEDDINGS = """
        -- pgvector extension (per-project embedding tables created by ensure_project_schema)
        CREATE EXTENSION IF NOT EXISTS vector;
        """

        ddl = """
        -- Users table (full schema including monetization fields)
        CREATE TABLE IF NOT EXISTS mng_users (
            id                 VARCHAR(36)    PRIMARY KEY,
            email              VARCHAR(255)   UNIQUE NOT NULL,
            password_hash      TEXT           NOT NULL,
            is_admin           BOOLEAN        NOT NULL DEFAULT FALSE,
            is_active          BOOLEAN        NOT NULL DEFAULT TRUE,
            created_at         TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            last_login         TIMESTAMPTZ,
            role               VARCHAR(20)    NOT NULL DEFAULT 'free',
            balance_added_usd  NUMERIC(14, 8) NOT NULL DEFAULT 0,
            balance_used_usd   NUMERIC(14, 8) NOT NULL DEFAULT 0,
            coupons_used       TEXT[]         NOT NULL DEFAULT '{}',
            stripe_customer_id VARCHAR(100)   NOT NULL DEFAULT ''
        );
        -- Migrate: add monetization columns if table already exists without them
        ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS role               VARCHAR(20)    NOT NULL DEFAULT 'free';
        ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS balance_added_usd  NUMERIC(14, 8) NOT NULL DEFAULT 0;
        ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS balance_used_usd   NUMERIC(14, 8) NOT NULL DEFAULT 0;
        ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS coupons_used       TEXT[]         NOT NULL DEFAULT '{}';
        ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100)   NOT NULL DEFAULT '';
        CREATE INDEX IF NOT EXISTS idx_users_email ON mng_users (email);

        -- Usage logs (real cost + charged cost)
        CREATE TABLE IF NOT EXISTS mng_usage_logs (
            id            SERIAL         PRIMARY KEY,
            user_id       VARCHAR(36)    REFERENCES mng_users(id) ON DELETE SET NULL,
            provider      VARCHAR(50),
            model         VARCHAR(100),
            input_tokens  INTEGER        NOT NULL DEFAULT 0,
            output_tokens INTEGER        NOT NULL DEFAULT 0,
            cost_usd      NUMERIC(12, 8) NOT NULL DEFAULT 0,
            charged_usd   NUMERIC(12, 8) NOT NULL DEFAULT 0,
            created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
        );
        ALTER TABLE mng_usage_logs ADD COLUMN IF NOT EXISTS charged_usd NUMERIC(12, 8) NOT NULL DEFAULT 0;
        CREATE INDEX IF NOT EXISTS idx_usage_user_id    ON mng_usage_logs (user_id);
        CREATE INDEX IF NOT EXISTS idx_usage_created_at ON mng_usage_logs (created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_usage_provider   ON mng_usage_logs (provider);

        -- Transactions (credits, debits, coupons)
        CREATE TABLE IF NOT EXISTS mng_transactions (
            id            SERIAL         PRIMARY KEY,
            user_id       VARCHAR(36)    REFERENCES mng_users(id) ON DELETE SET NULL,
            type          VARCHAR(50)    NOT NULL,
            amount_usd    NUMERIC(12, 8) NOT NULL DEFAULT 0,
            base_cost_usd NUMERIC(12, 8),
            description   TEXT           NOT NULL DEFAULT '',
            ref           VARCHAR(255)   NOT NULL DEFAULT '',
            created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_tx_user_id    ON mng_transactions (user_id);
        CREATE INDEX IF NOT EXISTS idx_tx_created_at ON mng_transactions (created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_tx_type       ON mng_transactions (type);
        """
        # Core tables — always required; commit first so other blocks don't roll this back
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()

        _DDL_TAGGING = """
        -- Active session tags per project (shared; commits are now per-project tables)
        CREATE TABLE IF NOT EXISTS mng_session_tags (
            id         SERIAL         PRIMARY KEY,
            project    VARCHAR(255)   NOT NULL UNIQUE,
            phase      VARCHAR(20),
            feature    VARCHAR(255),
            bug_ref    VARCHAR(255),
            extra      JSONB          NOT NULL DEFAULT '{}',
            updated_at TIMESTAMPTZ    NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_session_tags_project ON mng_session_tags(project);
        """

        # Each optional block uses its own cursor + commit so a failure in one
        # does NOT roll back other blocks (psycopg2 shares one transaction by default).
        _DDL_ENTITIES = """
        -- Tag categories per project (feature, bug, component, doc_type, …)
        CREATE TABLE IF NOT EXISTS mng_entity_categories (
            id         SERIAL         PRIMARY KEY,
            project    VARCHAR(255)   NOT NULL,
            name       VARCHAR(100)   NOT NULL,
            color      VARCHAR(20)    NOT NULL DEFAULT '#4a90e2',
            icon       VARCHAR(10)    NOT NULL DEFAULT '⬡',
            created_at TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(project, name)
        );
        CREATE INDEX IF NOT EXISTS idx_ec_project ON mng_entity_categories(project);

        -- Tag values (specific instances per category)
        CREATE TABLE IF NOT EXISTS mng_entity_values (
            id          SERIAL         PRIMARY KEY,
            category_id INT            NOT NULL REFERENCES mng_entity_categories(id) ON DELETE CASCADE,
            project     VARCHAR(255)   NOT NULL,
            name        VARCHAR(255)   NOT NULL,
            description TEXT           NOT NULL DEFAULT '',
            status      VARCHAR(20)    NOT NULL DEFAULT 'active',
            created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(project, category_id, name)
        );
        CREATE INDEX IF NOT EXISTS idx_ev_category ON mng_entity_values(category_id);
        CREATE INDEX IF NOT EXISTS idx_ev_project  ON mng_entity_values(project);
        ALTER TABLE mng_entity_values ADD COLUMN IF NOT EXISTS due_date DATE;
        ALTER TABLE mng_entity_values ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES mng_entity_values(id) ON DELETE SET NULL;
        ALTER TABLE mng_entity_values ADD COLUMN IF NOT EXISTS lifecycle_status VARCHAR(20) NOT NULL DEFAULT 'idea';
        CREATE INDEX IF NOT EXISTS idx_ev_parent ON mng_entity_values(parent_id);

        -- Value-to-value dependency links (blocks, related_to, etc.)
        CREATE TABLE IF NOT EXISTS mng_entity_value_links (
            from_value_id INT NOT NULL REFERENCES mng_entity_values(id) ON DELETE CASCADE,
            to_value_id   INT NOT NULL REFERENCES mng_entity_values(id) ON DELETE CASCADE,
            link_type     VARCHAR(50) NOT NULL DEFAULT 'blocks',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(from_value_id, to_value_id, link_type)
        );
        CREATE INDEX IF NOT EXISTS idx_evl_from ON mng_entity_value_links(from_value_id);
        CREATE INDEX IF NOT EXISTS idx_evl_to   ON mng_entity_value_links(to_value_id);
        -- events, event_tags, event_links are now per-project tables (see ensure_project_schema)
        """

        _DDL_AGENT_ROLES = """
        -- Agent role library: reusable LLM personas for workflow nodes.
        -- All users see name/description; system_prompt is admin-only via the API.
        CREATE TABLE IF NOT EXISTS mng_agent_roles (
            id            SERIAL         PRIMARY KEY,
            project       TEXT           NOT NULL DEFAULT '_global',
            name          TEXT           NOT NULL,
            description   TEXT           NOT NULL DEFAULT '',
            system_prompt TEXT           NOT NULL DEFAULT '',
            provider      TEXT           NOT NULL DEFAULT 'claude',
            model         TEXT           NOT NULL DEFAULT '',
            tags          TEXT[]         NOT NULL DEFAULT '{}',
            is_active     BOOLEAN        NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(project, name)
        );
        CREATE INDEX IF NOT EXISTS idx_ar_project ON mng_agent_roles(project);

        -- Version history: written on every PATCH to system_prompt/provider/model.
        CREATE TABLE IF NOT EXISTS mng_agent_role_versions (
            id            SERIAL         PRIMARY KEY,
            role_id       INT            NOT NULL REFERENCES mng_agent_roles(id) ON DELETE CASCADE,
            system_prompt TEXT           NOT NULL,
            provider      TEXT           NOT NULL,
            model         TEXT           NOT NULL,
            changed_by    TEXT,
            changed_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            note          TEXT           NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_arv_role ON mng_agent_role_versions(role_id);
        """

        for label, sql in [
            ("Embeddings (pgvector)", _DDL_EMBEDDINGS),
            ("Tagging (commits + mng_session_tags)", _DDL_TAGGING),
            ("Entities (mng_entity_categories + mng_entity_values + links)", _DDL_ENTITIES),
            ("Agent roles (mng_agent_roles + mng_agent_role_versions)", _DDL_AGENT_ROLES),
        ]:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                conn.commit()
                log.info(f"✅ {label} tables ready")
            except Exception as e:
                conn.rollback()
                log.warning(f"{label} DDL skipped: {e}")

        # ivfflat indexes on per-project embeddings tables are added manually after rows exist

        # Seed default global roles (idempotent — skips on conflict)
        _Database._seed_agent_roles(conn)

    @staticmethod
    def _seed_agent_roles(conn) -> None:
        """Insert the 10 built-in global roles. Safe to call repeatedly."""
        _ROLES = [
            (
                "Product Manager",
                "Translates feature descriptions into acceptance criteria and user stories.",
                "You are a senior product manager. Given a feature description, write 3-8 "
                "acceptance criteria as bullet points starting with '- [ ]'. Each must be "
                "specific, measurable, and testable. Also identify 2-3 user stories in "
                "'As a [user], I want [goal]' format. Respond in plain text.",
                "claude", "claude-haiku-4-5-20251001",
            ),
            (
                "Sr. Architect",
                "Designs technical architecture and numbered implementation plans.",
                "You are a senior software architect. Given a feature and acceptance criteria, "
                "write a numbered technical implementation plan. Include: specific files to "
                "create or modify, functions/methods to add, database schema changes, and "
                "integration points. Be precise about HOW to implement, not just WHAT.",
                "claude", "claude-sonnet-4-6",
            ),
            (
                "Web Developer",
                "Implements full-stack features against a technical plan.",
                "You are a senior full-stack developer. Given an implementation plan and "
                "acceptance criteria, write the actual code. Include complete file contents "
                "or clear code diffs. Cover both frontend and backend changes. Add inline "
                "comments for non-obvious logic. Ensure all acceptance criteria are met.",
                "claude", "claude-sonnet-4-6",
            ),
            (
                "Backend Developer",
                "Writes server-side code: APIs, DB schemas, business logic.",
                "You are a senior backend developer. Implement server-side code including: "
                "REST API endpoints, database migrations, business logic, error handling, "
                "and input validation. Use the project's existing stack and patterns. "
                "Write complete, production-ready code with proper error handling.",
                "deepseek", "deepseek-chat",
            ),
            (
                "Frontend Developer",
                "Writes client-side code: UI components, styles, interactions.",
                "You are a senior frontend developer. Implement client-side code including: "
                "HTML structure, CSS styles, JavaScript logic, user interactions, and API "
                "integration. Match the existing design system and patterns. Ensure "
                "accessibility and responsiveness.",
                "openai", "gpt-4o",
            ),
            (
                "DevOps Engineer",
                "Writes CI/CD configs, Dockerfiles, and deployment infrastructure.",
                "You are a senior DevOps engineer. Write: Dockerfiles, CI/CD pipeline configs "
                "(GitHub Actions/GitLab CI), deployment scripts, environment configs, and "
                "monitoring setup. Use best practices for security, scalability, and "
                "reliability. Include health checks and rollback strategies.",
                "claude", "claude-haiku-4-5-20251001",
            ),
            (
                "Code Reviewer",
                "Reviews code quality and returns score + issues as JSON.",
                "You are a senior code reviewer. Review the provided implementation against "
                "the acceptance criteria. Evaluate: correctness, code quality, edge cases, "
                "error handling, and test coverage.\n\nReturn ONLY valid JSON:\n"
                '{"score": 1-10, "passed": true/false, "issues": ["..."], '
                '"suggestions": ["..."]}\n\nScore >= 7 means passed. Be specific.',
                "claude", "claude-sonnet-4-6",
            ),
            (
                "Security Reviewer",
                "Audits code for OWASP Top 10 vulnerabilities.",
                "You are a senior application security engineer. Review code for OWASP Top 10: "
                "injection, broken auth, sensitive data exposure, XXE, broken access control, "
                "security misconfigs, XSS, insecure deserialization, known vulnerabilities.\n\n"
                "Return ONLY valid JSON:\n"
                '{"score": 1-10, "passed": true/false, "vulnerabilities": ["..."], '
                '"recommendations": ["..."]}',
                "claude", "claude-haiku-4-5-20251001",
            ),
            (
                "QA Engineer",
                "Writes comprehensive test cases including edge cases and boundary conditions.",
                "You are a senior QA engineer. Given a feature and acceptance criteria, write "
                "a comprehensive test plan including: happy path tests, boundary conditions, "
                "error cases, edge cases, and performance considerations. For each test "
                "provide: test name, preconditions, steps, expected result.",
                "openai", "gpt-4o",
            ),
            (
                "AWS Architect",
                "Designs AWS infrastructure using CDK/CloudFormation with security best practices.",
                "You are a senior AWS solutions architect. Design and implement AWS "
                "infrastructure using CDK (TypeScript) or CloudFormation. Include: compute "
                "(ECS/Lambda/EC2), storage (S3/RDS/DynamoDB), networking (VPC/ALB/Route53), "
                "IAM roles with least-privilege, security groups, auto-scaling, and cost "
                "optimization notes.",
                "claude", "claude-sonnet-4-6",
            ),
        ]
        try:
            with conn.cursor() as cur:
                for name, desc, prompt, provider, model in _ROLES:
                    cur.execute(
                        """INSERT INTO mng_agent_roles
                               (project, name, description, system_prompt, provider, model)
                           VALUES ('_global', %s, %s, %s, %s, %s)
                           ON CONFLICT (project, name) DO NOTHING""",
                        (name, desc, prompt, provider, model),
                    )
            conn.commit()
            log.info("✅ Agent roles seeded")
        except Exception as e:
            conn.rollback()
            log.warning(f"Agent roles seed skipped: {e}")


# Singleton used everywhere
db = _Database()
