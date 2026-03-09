-- ============================================================
-- aicli — Master Schema
-- All tables defined here. Run once or apply incrementally.
-- Uses CREATE TABLE IF NOT EXISTS / ALTER TABLE ADD COLUMN IF NOT EXISTS
-- so it is fully idempotent (safe to re-run).
-- ============================================================

-- Required extension: pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- ── Core Auth / Billing ────────────────────────────────────────────────────────

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
ALTER TABLE users ADD COLUMN IF NOT EXISTS role               VARCHAR(20)    NOT NULL DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS balance_added_usd  NUMERIC(14, 8) NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS balance_used_usd   NUMERIC(14, 8) NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS coupons_used       TEXT[]         NOT NULL DEFAULT '{}';
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100)   NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

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
CREATE INDEX IF NOT EXISTS idx_usage_user_id    ON usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_created_at ON usage_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_provider   ON usage_logs(provider);

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
CREATE INDEX IF NOT EXISTS idx_tx_user_id    ON transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_tx_created_at ON transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tx_type       ON transactions(type);

-- ── Semantic Embeddings (pgvector) ────────────────────────────────────────────
-- source_type: "history" | "node_output" | "role" | "project_md" | "commit"

CREATE TABLE IF NOT EXISTS embeddings (
    id          SERIAL         PRIMARY KEY,
    project     VARCHAR(255)   NOT NULL,
    source_type VARCHAR(50)    NOT NULL,
    source_id   VARCHAR(255)   NOT NULL,
    content     TEXT           NOT NULL,
    embedding   vector(1536),
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE(project, source_type, source_id)
);
CREATE INDEX IF NOT EXISTS idx_emb_project ON embeddings(project, source_type);
-- ivfflat requires rows to exist before creation — created at runtime in database.py

-- ── Commit Metadata + Tagging ─────────────────────────────────────────────────
-- Populated by POST /history/commits/sync from commit_log.jsonl.
-- Users enrich phase/feature/bug via the Commits tab in History view.

CREATE TABLE IF NOT EXISTS commits (
    id           SERIAL         PRIMARY KEY,
    project      VARCHAR(255)   NOT NULL,
    commit_hash  VARCHAR(40)    NOT NULL,
    commit_msg   TEXT           NOT NULL DEFAULT '',
    summary      TEXT           NOT NULL DEFAULT '',
    phase        VARCHAR(20),               -- discovery | development | prod | null=untagged
    feature      VARCHAR(255),              -- free-form feature label
    bug_ref      VARCHAR(255),              -- optional bug reference
    source       VARCHAR(50)    NOT NULL DEFAULT 'git',   -- git | claude_cli | aicli
    session_id   VARCHAR(255),
    tags         JSONB          NOT NULL DEFAULT '{}',    -- extra key/value pairs
    committed_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE(project, commit_hash)
);
CREATE INDEX IF NOT EXISTS idx_commits_project     ON commits(project);
CREATE INDEX IF NOT EXISTS idx_commits_phase       ON commits(project, phase);
CREATE INDEX IF NOT EXISTS idx_commits_feature     ON commits(project, feature);
CREATE INDEX IF NOT EXISTS idx_commits_committed   ON commits(project, committed_at DESC);

-- ── Entity / Relationship Model ───────────────────────────────────────────────
-- User-defined tag taxonomy. Extensible: add Slack/CRM/Notion event_types later.

-- Tag categories: "feature", "bug", "component", "doc_type", "customer", …
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

-- Tag values: "shared-memory", "auth-loop", "trading-algo", "high-level-design", …
CREATE TABLE IF NOT EXISTS entity_values (
    id          SERIAL         PRIMARY KEY,
    category_id INT            NOT NULL REFERENCES entity_categories(id) ON DELETE CASCADE,
    project     VARCHAR(255)   NOT NULL,
    name        VARCHAR(255)   NOT NULL,
    description TEXT           NOT NULL DEFAULT '',
    status      VARCHAR(20)    NOT NULL DEFAULT 'active',  -- active | done | archived
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE(project, category_id, name)
);
CREATE INDEX IF NOT EXISTS idx_ev_category ON entity_values(category_id);
CREATE INDEX IF NOT EXISTS idx_ev_project  ON entity_values(project);

-- Raw events: every tracked item — prompt, commit, file_change, doc, meeting
-- event_type: prompt | commit | file_change | doc | meeting | slack | crm | notion
CREATE TABLE IF NOT EXISTS events (
    id         SERIAL         PRIMARY KEY,
    project    VARCHAR(255)   NOT NULL,
    event_type VARCHAR(50)    NOT NULL,
    source_id  VARCHAR(255)   NOT NULL,   -- ts, commit_hash, file_path, etc.
    title      TEXT           NOT NULL DEFAULT '',
    content    TEXT           NOT NULL DEFAULT '',
    metadata   JSONB          NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE(project, event_type, source_id)
);
CREATE INDEX IF NOT EXISTS idx_ev_project_type ON events(project, event_type);
CREATE INDEX IF NOT EXISTS idx_ev_created      ON events(project, created_at DESC);

-- Many-to-many: events ↔ entity_values
CREATE TABLE IF NOT EXISTS event_tags (
    event_id        INT         NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    entity_value_id INT         NOT NULL REFERENCES entity_values(id) ON DELETE CASCADE,
    auto_tagged     BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(event_id, entity_value_id)
);
CREATE INDEX IF NOT EXISTS idx_etag_event ON event_tags(event_id);
CREATE INDEX IF NOT EXISTS idx_etag_value ON event_tags(entity_value_id);

-- Directed relationships between events
-- link_type: implements | fixes | causes | relates_to | references | closes
CREATE TABLE IF NOT EXISTS event_links (
    from_event_id INT         NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    to_event_id   INT         NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    link_type     VARCHAR(50) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(from_event_id, to_event_id, link_type)
);
CREATE INDEX IF NOT EXISTS idx_elink_from ON event_links(from_event_id);
CREATE INDEX IF NOT EXISTS idx_elink_to   ON event_links(to_event_id);

-- ── Session Tags ──────────────────────────────────────────────────────────────
-- One row per project. Stores the currently active tags for the session.
-- Updated by the UI tag chips; injected by aicli CLI into every prompt.

CREATE TABLE IF NOT EXISTS session_tags (
    id         SERIAL         PRIMARY KEY,
    project    VARCHAR(255)   NOT NULL UNIQUE,
    phase      VARCHAR(20),               -- discovery | development | prod
    feature    VARCHAR(255),
    bug_ref    VARCHAR(255),
    extra      JSONB          NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_session_tags_project ON session_tags(project);
