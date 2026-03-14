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

    def init(self) -> None:
        """Called at startup. Creates connection pool if DATABASE_URL is set."""
        url = settings.database_url
        if not url:
            log.info("DATABASE_URL not set — using file-based storage")
            return
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(1, 10, url)
            # Verify connection and create tables
            with self.conn() as conn:
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
    def project_table(base: str, project: str) -> str:
        """Return per-project table name, e.g. commits_myproject."""
        safe = re.sub(r'[^a-z0-9]', '_', project.lower())[:40].strip('_')
        return f"{base}_{safe}"

    def ensure_project_schema(self, project: str) -> None:
        """Create per-project tables if they don't exist. Safe to call repeatedly."""
        if not self._available:
            return
        tbl = self.project_table
        c   = tbl("commits",    project)
        e   = tbl("events",     project)
        emb = tbl("embeddings", project)
        et  = tbl("event_tags", project)
        el  = tbl("event_links", project)
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
        ALTER TABLE {c} ADD COLUMN IF NOT EXISTS prompt_source_id VARCHAR(255);

        CREATE TABLE IF NOT EXISTS {e} (
            id         SERIAL         PRIMARY KEY,
            event_type VARCHAR(50)    NOT NULL,
            source_id  VARCHAR(255)   NOT NULL,
            title      TEXT           NOT NULL DEFAULT '',
            content    TEXT           NOT NULL DEFAULT '',
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
            entity_value_id INT         NOT NULL REFERENCES entity_values(id) ON DELETE CASCADE,
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
        """
        try:
            with self.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(ddl)
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
    def _ensure_schema(conn) -> None:
        """Create tables and migrate missing columns — safe to run repeatedly."""

        _DDL_EMBEDDINGS = """
        -- pgvector extension (per-project embedding tables created by ensure_project_schema)
        CREATE EXTENSION IF NOT EXISTS vector;
        """


        ddl = """
        -- Users table (full schema including monetization fields)
        CREATE TABLE IF NOT EXISTS users (
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
        ALTER TABLE users ADD COLUMN IF NOT EXISTS role               VARCHAR(20)    NOT NULL DEFAULT 'free';
        ALTER TABLE users ADD COLUMN IF NOT EXISTS balance_added_usd  NUMERIC(14, 8) NOT NULL DEFAULT 0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS balance_used_usd   NUMERIC(14, 8) NOT NULL DEFAULT 0;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS coupons_used       TEXT[]         NOT NULL DEFAULT '{}';
        ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100)   NOT NULL DEFAULT '';
        CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

        -- Usage logs (real cost + charged cost)
        CREATE TABLE IF NOT EXISTS usage_logs (
            id            SERIAL         PRIMARY KEY,
            user_id       VARCHAR(36)    REFERENCES users(id) ON DELETE SET NULL,
            provider      VARCHAR(50),
            model         VARCHAR(100),
            input_tokens  INTEGER        NOT NULL DEFAULT 0,
            output_tokens INTEGER        NOT NULL DEFAULT 0,
            cost_usd      NUMERIC(12, 8) NOT NULL DEFAULT 0,
            charged_usd   NUMERIC(12, 8) NOT NULL DEFAULT 0,
            created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
        );
        ALTER TABLE usage_logs ADD COLUMN IF NOT EXISTS charged_usd NUMERIC(12, 8) NOT NULL DEFAULT 0;
        CREATE INDEX IF NOT EXISTS idx_usage_user_id    ON usage_logs (user_id);
        CREATE INDEX IF NOT EXISTS idx_usage_created_at ON usage_logs (created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_usage_provider   ON usage_logs (provider);

        -- Transactions (credits, debits, coupons)
        CREATE TABLE IF NOT EXISTS transactions (
            id            SERIAL         PRIMARY KEY,
            user_id       VARCHAR(36)    REFERENCES users(id) ON DELETE SET NULL,
            type          VARCHAR(50)    NOT NULL,
            amount_usd    NUMERIC(12, 8) NOT NULL DEFAULT 0,
            base_cost_usd NUMERIC(12, 8),
            description   TEXT           NOT NULL DEFAULT '',
            ref           VARCHAR(255)   NOT NULL DEFAULT '',
            created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_tx_user_id    ON transactions (user_id);
        CREATE INDEX IF NOT EXISTS idx_tx_created_at ON transactions (created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_tx_type       ON transactions (type);
        """
        # Core tables — always required; commit first so other blocks don't roll this back
        with conn.cursor() as cur:
            cur.execute(ddl)
        conn.commit()

        _DDL_TAGGING = """
        -- Active session tags per project (shared; commits are now per-project tables)
        CREATE TABLE IF NOT EXISTS session_tags (
            id         SERIAL         PRIMARY KEY,
            project    VARCHAR(255)   NOT NULL UNIQUE,
            phase      VARCHAR(20),
            feature    VARCHAR(255),
            bug_ref    VARCHAR(255),
            extra      JSONB          NOT NULL DEFAULT '{}',
            updated_at TIMESTAMPTZ    NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_session_tags_project ON session_tags(project);
        """

        # Each optional block uses its own cursor + commit so a failure in one
        # does NOT roll back other blocks (psycopg2 shares one transaction by default).
        _DDL_ENTITIES = """
        -- Tag categories per project (feature, bug, component, doc_type, …)
        CREATE TABLE IF NOT EXISTS entity_categories (
            id         SERIAL         PRIMARY KEY,
            project    VARCHAR(255)   NOT NULL,
            name       VARCHAR(100)   NOT NULL,
            color      VARCHAR(20)    NOT NULL DEFAULT '#4a90e2',
            icon       VARCHAR(10)    NOT NULL DEFAULT '⬡',
            created_at TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(project, name)
        );
        CREATE INDEX IF NOT EXISTS idx_ec_project ON entity_categories(project);

        -- Tag values (specific instances per category)
        CREATE TABLE IF NOT EXISTS entity_values (
            id          SERIAL         PRIMARY KEY,
            category_id INT            NOT NULL REFERENCES entity_categories(id) ON DELETE CASCADE,
            project     VARCHAR(255)   NOT NULL,
            name        VARCHAR(255)   NOT NULL,
            description TEXT           NOT NULL DEFAULT '',
            status      VARCHAR(20)    NOT NULL DEFAULT 'active',
            created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(project, category_id, name)
        );
        CREATE INDEX IF NOT EXISTS idx_ev_category ON entity_values(category_id);
        CREATE INDEX IF NOT EXISTS idx_ev_project  ON entity_values(project);
        ALTER TABLE entity_values ADD COLUMN IF NOT EXISTS due_date DATE;
        ALTER TABLE entity_values ADD COLUMN IF NOT EXISTS parent_id INTEGER REFERENCES entity_values(id) ON DELETE SET NULL;
        CREATE INDEX IF NOT EXISTS idx_ev_parent ON entity_values(parent_id);
        -- events, event_tags, event_links are now per-project tables (see ensure_project_schema)
        """

        _DDL_GRAPH = """
        -- Graph workflow definitions
        CREATE TABLE IF NOT EXISTS graph_workflows (
            id             SERIAL         PRIMARY KEY,
            project        VARCHAR(255)   NOT NULL,
            name           VARCHAR(255)   NOT NULL,
            description    TEXT           NOT NULL DEFAULT '',
            max_iterations INTEGER        NOT NULL DEFAULT 3,
            created_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(project, name)
        );
        CREATE INDEX IF NOT EXISTS idx_gw_project ON graph_workflows(project);

        -- Graph nodes (steps within a workflow)
        CREATE TABLE IF NOT EXISTS graph_nodes (
            id          SERIAL         PRIMARY KEY,
            workflow_id INT            NOT NULL REFERENCES graph_workflows(id) ON DELETE CASCADE,
            name        VARCHAR(255)   NOT NULL,
            node_type   VARCHAR(50)    NOT NULL DEFAULT 'llm',
            prompt      TEXT           NOT NULL DEFAULT '',
            provider    VARCHAR(50)    NOT NULL DEFAULT 'claude',
            model       VARCHAR(100)   NOT NULL DEFAULT '',
            pos_x       REAL           NOT NULL DEFAULT 0,
            pos_y       REAL           NOT NULL DEFAULT 0,
            config      JSONB          NOT NULL DEFAULT '{}'
        );
        CREATE INDEX IF NOT EXISTS idx_gn_workflow ON graph_nodes(workflow_id);

        -- Graph edges (connections between nodes)
        CREATE TABLE IF NOT EXISTS graph_edges (
            id            SERIAL       PRIMARY KEY,
            workflow_id   INT          NOT NULL REFERENCES graph_workflows(id) ON DELETE CASCADE,
            source_node   INT          NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
            target_node   INT          NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
            edge_type     VARCHAR(50)  NOT NULL DEFAULT 'default',
            UNIQUE(workflow_id, source_node, target_node, edge_type)
        );

        -- Workflow run instances
        CREATE TABLE IF NOT EXISTS graph_runs (
            id           SERIAL         PRIMARY KEY,
            workflow_id  INT            NOT NULL REFERENCES graph_workflows(id) ON DELETE CASCADE,
            project      VARCHAR(255)   NOT NULL,
            status       VARCHAR(50)    NOT NULL DEFAULT 'pending',
            started_at   TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            finished_at  TIMESTAMPTZ,
            total_cost   NUMERIC(12, 8) NOT NULL DEFAULT 0,
            input        TEXT           NOT NULL DEFAULT '',
            output       TEXT           NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_gr_workflow ON graph_runs(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_gr_project  ON graph_runs(project);

        -- Results per node per run
        CREATE TABLE IF NOT EXISTS graph_node_results (
            id        SERIAL         PRIMARY KEY,
            run_id    INT            NOT NULL REFERENCES graph_runs(id) ON DELETE CASCADE,
            node_id   INT            NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
            status    VARCHAR(50)    NOT NULL DEFAULT 'pending',
            output    TEXT           NOT NULL DEFAULT '',
            cost      NUMERIC(12, 8) NOT NULL DEFAULT 0,
            started_at  TIMESTAMPTZ,
            finished_at TIMESTAMPTZ
        );
        CREATE INDEX IF NOT EXISTS idx_gnr_run  ON graph_node_results(run_id);
        CREATE INDEX IF NOT EXISTS idx_gnr_node ON graph_node_results(node_id);
        """

        for label, sql in [
            ("Embeddings (pgvector)", _DDL_EMBEDDINGS),
            ("Tagging (commits + session_tags)", _DDL_TAGGING),
            ("Entities (categories + values + events + links)", _DDL_ENTITIES),
            ("Graph workflows (nodes, edges, runs, results)", _DDL_GRAPH),
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


# Singleton used everywhere
db = _Database()
