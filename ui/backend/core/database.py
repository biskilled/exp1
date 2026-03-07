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
        with conn.cursor() as cur:
            cur.execute(ddl)


# Singleton used everywhere
db = _Database()
