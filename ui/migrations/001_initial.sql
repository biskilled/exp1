-- aicli — PostgreSQL schema
-- Run this once against your Railway PostgreSQL instance:
--   psql "postgresql://postgres:...@tramway.proxy.rlwy.net:35811/railway" -f 001_initial.sql
--
-- Tables are created with IF NOT EXISTS — safe to re-run.

-- ── Users ─────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
    id          VARCHAR(36)  PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT        NOT NULL,
    is_admin    BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    last_login  TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ── Usage logs ────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS usage_logs (
    id            SERIAL       PRIMARY KEY,
    user_id       VARCHAR(36)  REFERENCES users(id) ON DELETE SET NULL,
    provider      VARCHAR(50),
    model         VARCHAR(100),
    input_tokens  INTEGER      NOT NULL DEFAULT 0,
    output_tokens INTEGER      NOT NULL DEFAULT 0,
    cost_usd      NUMERIC(12, 8) NOT NULL DEFAULT 0,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_user_id    ON usage_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_usage_created_at ON usage_logs (created_at DESC);

-- ── Verify ────────────────────────────────────────────────────────────────────

SELECT 'users'      AS tbl, COUNT(*) AS rows FROM users
UNION ALL
SELECT 'usage_logs' AS tbl, COUNT(*) AS rows FROM usage_logs;
