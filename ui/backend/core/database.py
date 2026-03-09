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

        _DDL_EMBEDDINGS = """
        -- pgvector semantic embeddings (Layer 4 memory upgrade)
        -- chunk_type: full | summary | function | class | section | file_diff
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE TABLE IF NOT EXISTS embeddings (
            id          SERIAL         PRIMARY KEY,
            project     VARCHAR(255)   NOT NULL,
            source_type VARCHAR(50)    NOT NULL,
            source_id   VARCHAR(255)   NOT NULL,
            chunk_index INT            NOT NULL DEFAULT 0,
            content     TEXT           NOT NULL,
            embedding   vector(1536),
            chunk_type  VARCHAR(50)    NOT NULL DEFAULT 'full',
            doc_type    VARCHAR(50),
            language    VARCHAR(30),
            file_path   VARCHAR(500),
            metadata    JSONB          NOT NULL DEFAULT '{}',
            created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_emb_project ON embeddings(project, source_type);
        -- Migrate: add chunking columns to existing installs (must come before indexes on new cols)
        ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS chunk_index INT NOT NULL DEFAULT 0;
        ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS chunk_type  VARCHAR(50) NOT NULL DEFAULT 'full';
        ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS doc_type    VARCHAR(50);
        ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS language    VARCHAR(30);
        ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS file_path   VARCHAR(500);
        ALTER TABLE embeddings ADD COLUMN IF NOT EXISTS metadata    JSONB NOT NULL DEFAULT '{}';
        -- Language index and unique index created AFTER columns are guaranteed to exist
        CREATE INDEX IF NOT EXISTS idx_emb_language ON embeddings(project, language)
            WHERE language IS NOT NULL;
        -- Replace 3-col unique constraint with chunk-aware 4-col index
        ALTER TABLE embeddings DROP CONSTRAINT IF EXISTS embeddings_project_source_type_source_id_key;
        CREATE UNIQUE INDEX IF NOT EXISTS embeddings_uq_chunk
            ON embeddings(project, source_type, source_id, chunk_index);
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
        -- Commit metadata + tags (populated from commit_log.jsonl via /history/commits/sync)
        CREATE TABLE IF NOT EXISTS commits (
            id           SERIAL         PRIMARY KEY,
            project      VARCHAR(255)   NOT NULL,
            commit_hash  VARCHAR(40)    NOT NULL,
            commit_msg   TEXT           NOT NULL DEFAULT '',
            summary      TEXT           NOT NULL DEFAULT '',
            phase        VARCHAR(20),
            feature      VARCHAR(255),
            bug_ref      VARCHAR(255),
            source       VARCHAR(50)    NOT NULL DEFAULT 'git',
            session_id   VARCHAR(255),
            tags         JSONB          NOT NULL DEFAULT '{}',
            committed_at TIMESTAMPTZ,
            created_at   TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(project, commit_hash)
        );
        CREATE INDEX IF NOT EXISTS idx_commits_project   ON commits(project);
        CREATE INDEX IF NOT EXISTS idx_commits_phase     ON commits(project, phase);
        CREATE INDEX IF NOT EXISTS idx_commits_feature   ON commits(project, feature);
        CREATE INDEX IF NOT EXISTS idx_commits_committed ON commits(project, committed_at DESC);

        -- Active session tags per project
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

        -- Raw event log (prompts, commits, docs, meetings, file_changes, …)
        CREATE TABLE IF NOT EXISTS events (
            id         SERIAL         PRIMARY KEY,
            project    VARCHAR(255)   NOT NULL,
            event_type VARCHAR(50)    NOT NULL,
            source_id  VARCHAR(255)   NOT NULL,
            title      TEXT           NOT NULL DEFAULT '',
            content    TEXT           NOT NULL DEFAULT '',
            metadata   JSONB          NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(project, event_type, source_id)
        );
        CREATE INDEX IF NOT EXISTS idx_events_project_type ON events(project, event_type);
        CREATE INDEX IF NOT EXISTS idx_events_created      ON events(project, created_at DESC);

        -- Events ↔ values (many-to-many)
        CREATE TABLE IF NOT EXISTS event_tags (
            event_id        INT         NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            entity_value_id INT         NOT NULL REFERENCES entity_values(id) ON DELETE CASCADE,
            auto_tagged     BOOLEAN     NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(event_id, entity_value_id)
        );
        CREATE INDEX IF NOT EXISTS idx_etag_event ON event_tags(event_id);
        CREATE INDEX IF NOT EXISTS idx_etag_value ON event_tags(entity_value_id);

        -- Directed event relationships
        CREATE TABLE IF NOT EXISTS event_links (
            from_event_id INT         NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            to_event_id   INT         NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            link_type     VARCHAR(50) NOT NULL,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(from_event_id, to_event_id, link_type)
        );
        CREATE INDEX IF NOT EXISTS idx_elink_from ON event_links(from_event_id);
        CREATE INDEX IF NOT EXISTS idx_elink_to   ON event_links(to_event_id);
        """

        for label, sql in [
            ("Embeddings (pgvector)", _DDL_EMBEDDINGS),
            ("Tagging (commits + session_tags)", _DDL_TAGGING),
            ("Entities (categories + values + events + links)", _DDL_ENTITIES),
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
