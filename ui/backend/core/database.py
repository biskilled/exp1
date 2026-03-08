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
        _DDL_GRAPH = """
        -- Graph Workflows (DAG-based multi-LLM pipelines)
        CREATE TABLE IF NOT EXISTS graph_workflows (
            id VARCHAR(36) PRIMARY KEY, project VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL, description TEXT NOT NULL DEFAULT '',
            max_iterations INT NOT NULL DEFAULT 5,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (project, name)
        );
        CREATE INDEX IF NOT EXISTS idx_gw_project ON graph_workflows(project);

        CREATE TABLE IF NOT EXISTS graph_nodes (
            id VARCHAR(36) PRIMARY KEY,
            workflow_id VARCHAR(36) NOT NULL REFERENCES graph_workflows(id) ON DELETE CASCADE,
            name VARCHAR(255) NOT NULL,
            role_file VARCHAR(300),
            role_prompt TEXT NOT NULL DEFAULT '',
            provider VARCHAR(50) NOT NULL DEFAULT 'claude',
            model VARCHAR(100) NOT NULL DEFAULT '',
            output_schema JSONB,
            inject_context BOOLEAN NOT NULL DEFAULT TRUE,
            position_x FLOAT NOT NULL DEFAULT 100,
            position_y FLOAT NOT NULL DEFAULT 100,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_gn_workflow ON graph_nodes(workflow_id);

        CREATE TABLE IF NOT EXISTS graph_edges (
            id VARCHAR(36) PRIMARY KEY,
            workflow_id VARCHAR(36) NOT NULL REFERENCES graph_workflows(id) ON DELETE CASCADE,
            source_node_id VARCHAR(36) NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
            target_node_id VARCHAR(36) NOT NULL REFERENCES graph_nodes(id) ON DELETE CASCADE,
            condition JSONB,
            label VARCHAR(100) NOT NULL DEFAULT '',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_ge_workflow ON graph_edges(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_ge_source   ON graph_edges(source_node_id);

        CREATE TABLE IF NOT EXISTS graph_runs (
            id VARCHAR(36) PRIMARY KEY,
            workflow_id VARCHAR(36) REFERENCES graph_workflows(id) ON DELETE SET NULL,
            project VARCHAR(255) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'running',
            user_input TEXT NOT NULL DEFAULT '',
            context JSONB NOT NULL DEFAULT '{}',
            started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            finished_at TIMESTAMPTZ,
            total_cost_usd NUMERIC(12,8) NOT NULL DEFAULT 0,
            error TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_gr_workflow ON graph_runs(workflow_id);
        CREATE INDEX IF NOT EXISTS idx_gr_project  ON graph_runs(project);
        CREATE INDEX IF NOT EXISTS idx_gr_status   ON graph_runs(status);

        CREATE TABLE IF NOT EXISTS graph_node_results (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(36) NOT NULL REFERENCES graph_runs(id) ON DELETE CASCADE,
            node_id VARCHAR(36) REFERENCES graph_nodes(id) ON DELETE SET NULL,
            node_name VARCHAR(255) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'running',
            output TEXT NOT NULL DEFAULT '',
            structured JSONB,
            input_tokens INT NOT NULL DEFAULT 0,
            output_tokens INT NOT NULL DEFAULT 0,
            cost_usd NUMERIC(12,8) NOT NULL DEFAULT 0,
            started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            finished_at TIMESTAMPTZ,
            iteration INT NOT NULL DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_gnr_run ON graph_node_results(run_id);

        -- Migrations for approval workflow (idempotent)
        ALTER TABLE graph_nodes ADD COLUMN IF NOT EXISTS require_approval BOOLEAN NOT NULL DEFAULT FALSE;
        ALTER TABLE graph_nodes ADD COLUMN IF NOT EXISTS approval_msg TEXT NOT NULL DEFAULT '';
        """

        _DDL_EMBEDDINGS = """
        -- pgvector semantic embeddings (Layer 4 memory upgrade)
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS embeddings (
            id SERIAL PRIMARY KEY,
            project VARCHAR(255) NOT NULL,
            source_type VARCHAR(50) NOT NULL,
            source_id VARCHAR(255) NOT NULL,
            content TEXT NOT NULL,
            embedding vector(1536),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE (project, source_type, source_id)
        );
        CREATE INDEX IF NOT EXISTS idx_emb_project ON embeddings(project, source_type);
        """

        _DDL_ENTITIES = """
        -- Project Entities (features, tasks, bugs)
        CREATE TABLE IF NOT EXISTS features (
            id VARCHAR(36) PRIMARY KEY, project VARCHAR(255) NOT NULL,
            title VARCHAR(500) NOT NULL, description TEXT NOT NULL DEFAULT '',
            status VARCHAR(20) NOT NULL DEFAULT 'proposed',
            priority VARCHAR(10) NOT NULL DEFAULT 'medium',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id VARCHAR(36) PRIMARY KEY, project VARCHAR(255) NOT NULL,
            feature_id VARCHAR(36) REFERENCES features(id) ON DELETE SET NULL,
            title VARCHAR(500) NOT NULL, description TEXT NOT NULL DEFAULT '',
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            priority VARCHAR(10) NOT NULL DEFAULT 'medium',
            assignee VARCHAR(255),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        CREATE TABLE IF NOT EXISTS bugs (
            id VARCHAR(36) PRIMARY KEY, project VARCHAR(255) NOT NULL,
            task_id VARCHAR(36) REFERENCES tasks(id) ON DELETE SET NULL,
            title VARCHAR(500) NOT NULL, description TEXT NOT NULL DEFAULT '',
            severity VARCHAR(20) NOT NULL DEFAULT 'medium',
            status VARCHAR(20) NOT NULL DEFAULT 'open',
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
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

        # Each optional block uses its own cursor + commit so a failure in one
        # does NOT roll back other blocks (psycopg2 shares one transaction by default).
        for label, sql in [
            ("Graph workflow", _DDL_GRAPH),
            ("Embeddings (pgvector)", _DDL_EMBEDDINGS),
            ("Entity", _DDL_ENTITIES),
        ]:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                conn.commit()
                log.info(f"✅ {label} tables ready")
            except Exception as e:
                conn.rollback()
                log.warning(f"{label} DDL skipped: {e}")

        # ivfflat index requires rows to exist first — best-effort, ignore if fails
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_emb_vec ON embeddings "
                    "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
                )
            conn.commit()
        except Exception:
            conn.rollback()


# Singleton used everywhere
db = _Database()
