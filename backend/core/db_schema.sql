-- ============================================================================
-- aicli Database Schema — Canonical Latest Version
-- Updated: 2026-04-08
-- ============================================================================
-- This file is the SINGLE SOURCE OF TRUTH for all table structures.
-- Rules:
--   1. Always use CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.
--   2. Every ALTER TABLE ever applied must be merged into the CREATE TABLE here.
--   3. Schema changes update THIS file AND add a migration entry in db_migrations.py.
--   4. No raw ALTER TABLE here — fresh installs read this file; migrations handle upgrades.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- SECTION 1: mng_* — Global / Client-scoped Management Tables
-- ============================================================================

-- mng_schema_version: tracks which migrations have been applied
-- Must be created before anything else so migration checks work on first run
CREATE TABLE IF NOT EXISTS mng_schema_version (
    version    VARCHAR(100) PRIMARY KEY,
    applied_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- mng_clients: top-level tenants (local install always has id=1)
CREATE TABLE IF NOT EXISTS mng_clients (
    id                SERIAL       PRIMARY KEY,
    slug              VARCHAR(50)  UNIQUE NOT NULL,
    name              VARCHAR(255) NOT NULL DEFAULT '',
    plan              VARCHAR(20)  NOT NULL DEFAULT 'free',
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    pricing_config    JSONB        DEFAULT NULL,
    provider_costs    JSONB        DEFAULT NULL,
    provider_balances JSONB        DEFAULT NULL,
    server_api_keys   JSONB        DEFAULT NULL
);
INSERT INTO mng_clients (id, slug, name, plan)
VALUES (1, 'local', 'Local Install', 'free')
ON CONFLICT (slug) DO NOTHING;

-- mng_users: user accounts (per client)
CREATE TABLE IF NOT EXISTS mng_users (
    id                 VARCHAR(36)    PRIMARY KEY,
    client_id          INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
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
CREATE INDEX IF NOT EXISTS idx_users_email  ON mng_users(email);
CREATE INDEX IF NOT EXISTS idx_users_client ON mng_users(client_id);

-- mng_usage_logs: per-request LLM usage tracking
CREATE TABLE IF NOT EXISTS mng_usage_logs (
    id            SERIAL         PRIMARY KEY,
    user_id       VARCHAR(36)    REFERENCES mng_users(id) ON DELETE SET NULL,
    provider      VARCHAR(50),
    model         VARCHAR(100),
    input_tokens  INTEGER        NOT NULL DEFAULT 0,
    output_tokens INTEGER        NOT NULL DEFAULT 0,
    cost_usd      NUMERIC(12, 8) NOT NULL DEFAULT 0,
    charged_usd   NUMERIC(12, 8) NOT NULL DEFAULT 0,
    source        VARCHAR(50)    NOT NULL DEFAULT 'request',  -- 'request'|'workflow'|'memory'
    metadata      JSONB          DEFAULT NULL,
    period_start  TIMESTAMPTZ    DEFAULT NULL,
    period_end    TIMESTAMPTZ    DEFAULT NULL,
    created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_usage_user_id    ON mng_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_created_at ON mng_usage_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_provider   ON mng_usage_logs(provider);
CREATE INDEX IF NOT EXISTS idx_usage_source     ON mng_usage_logs(source);

-- mng_transactions: billing credit/debit events
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
CREATE INDEX IF NOT EXISTS idx_tx_user_id    ON mng_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_tx_created_at ON mng_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tx_type       ON mng_transactions(type);

-- mng_user_api_keys: per-user encrypted provider API keys
CREATE TABLE IF NOT EXISTS mng_user_api_keys (
    id         SERIAL      PRIMARY KEY,
    user_id    VARCHAR(36) NOT NULL REFERENCES mng_users(id) ON DELETE CASCADE,
    provider   VARCHAR(50) NOT NULL,
    key_enc    TEXT        NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, provider)
);
CREATE INDEX IF NOT EXISTS idx_muak_user ON mng_user_api_keys(user_id);

-- mng_coupons: discount codes (per client)
CREATE TABLE IF NOT EXISTS mng_coupons (
    id          SERIAL         PRIMARY KEY,
    client_id   INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    code        VARCHAR(50)    NOT NULL,
    amount_usd  NUMERIC(10, 4) NOT NULL DEFAULT 0,
    max_uses    INT            NOT NULL DEFAULT 1,
    used_count  INT            NOT NULL DEFAULT 0,
    used_by     JSONB          NOT NULL DEFAULT '[]',
    description TEXT           NOT NULL DEFAULT '',
    expires_at  TIMESTAMPTZ    DEFAULT NULL,
    created_by  VARCHAR(255)   NOT NULL DEFAULT 'admin',
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mcp_client_code ON mng_coupons(client_id, code);
CREATE INDEX        IF NOT EXISTS idx_mcp_client       ON mng_coupons(client_id);

-- mng_projects: one row per project — single source of truth replacing project TEXT columns
CREATE TABLE IF NOT EXISTS mng_projects (
    id                 SERIAL         PRIMARY KEY,
    client_id          INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    name               VARCHAR(255)   NOT NULL,
    description        TEXT           NOT NULL DEFAULT '',
    workspace_path     TEXT,
    code_dir           TEXT,
    default_provider   VARCHAR(50)    NOT NULL DEFAULT 'claude',
    git_branch         VARCHAR(100)   DEFAULT 'main',
    git_username       TEXT,
    git_email          TEXT,
    github_repo        TEXT,
    github_client_id   TEXT,
    auto_commit_push   BOOLEAN        NOT NULL DEFAULT FALSE,
    claude_cli_support BOOLEAN        NOT NULL DEFAULT FALSE,
    cursor_support     BOOLEAN        NOT NULL DEFAULT FALSE,
    enabled_providers  JSONB          NOT NULL DEFAULT '[]',
    active_workflows   JSONB          NOT NULL DEFAULT '[]',
    extra              JSONB          NOT NULL DEFAULT '{}',
    is_active          BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at         TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at         TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE(client_id, name)
);
INSERT INTO mng_projects (client_id, name, description)
VALUES (1, '_global', 'Global scope — agent roles and shared templates')
ON CONFLICT (client_id, name) DO NOTHING;
CREATE INDEX IF NOT EXISTS idx_mng_projects_client ON mng_projects(client_id);

-- mng_user_projects: user ↔ project membership with role (owner|editor|viewer)
CREATE TABLE IF NOT EXISTS mng_user_projects (
    user_id    VARCHAR(36) NOT NULL REFERENCES mng_users(id) ON DELETE CASCADE,
    project_id INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    role       VARCHAR(20) NOT NULL DEFAULT 'member',
    joined_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, project_id)
);
CREATE INDEX IF NOT EXISTS idx_mng_user_projects_proj ON mng_user_projects(project_id);

-- mng_session_tags: active session context tags per project (phase, feature, bug_ref)
-- One row per project; updated in-place as the user switches context.
CREATE TABLE IF NOT EXISTS mng_session_tags (
    id         SERIAL       PRIMARY KEY,
    client_id  INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id INT          NOT NULL REFERENCES mng_projects(id),
    phase      VARCHAR(50),
    feature    VARCHAR(255),
    bug_ref    VARCHAR(255),
    extra      JSONB        NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(project_id)
);
CREATE INDEX IF NOT EXISTS idx_mst_pid ON mng_session_tags(project_id);

-- mng_agent_roles: LLM agent role definitions (system_prompt + model config + tools)
-- Seeded at startup from workspace/_templates/roles/*.yaml (idempotent UPSERT).
CREATE TABLE IF NOT EXISTS mng_agent_roles (
    id            SERIAL       PRIMARY KEY,
    client_id     INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id    INT          NOT NULL REFERENCES mng_projects(id),
    name          VARCHAR(255) NOT NULL,
    description   TEXT         NOT NULL DEFAULT '',
    system_prompt TEXT         NOT NULL DEFAULT '',
    provider      VARCHAR(50)  NOT NULL DEFAULT 'claude',
    model         VARCHAR(100) NOT NULL DEFAULT '',
    tags          TEXT[]       NOT NULL DEFAULT '{}',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    inputs        JSONB        NOT NULL DEFAULT '[]',  -- expected input keys
    outputs       JSONB        NOT NULL DEFAULT '[]',  -- output keys passed to next stage
    role_type     VARCHAR(50)  NOT NULL DEFAULT 'agent',
    output_schema JSONB        DEFAULT NULL,
    auto_commit   BOOLEAN      NOT NULL DEFAULT FALSE,
    tools         JSONB        NOT NULL DEFAULT '[]',  -- tool names enabled for this role
    react         BOOLEAN      NOT NULL DEFAULT TRUE,
    max_iterations INT         NOT NULL DEFAULT 10,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mar_pid_name ON mng_agent_roles(project_id, name);
CREATE INDEX        IF NOT EXISTS idx_mar_pid       ON mng_agent_roles(project_id);

-- mng_agent_role_versions: full audit history of system_prompt edits per role
CREATE TABLE IF NOT EXISTS mng_agent_role_versions (
    id            SERIAL       PRIMARY KEY,
    role_id       INT          NOT NULL REFERENCES mng_agent_roles(id) ON DELETE CASCADE,
    system_prompt TEXT         NOT NULL DEFAULT '',
    provider      VARCHAR(50)  NOT NULL DEFAULT 'claude',
    model         VARCHAR(100) NOT NULL DEFAULT '',
    tools         JSONB        NOT NULL DEFAULT '[]',
    changed_by    VARCHAR(255),
    changed_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    note          TEXT         NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_marv_role ON mng_agent_role_versions(role_id);

-- mng_system_roles: reusable system prompt fragments (coding standards, output format, etc.)
-- Injected into agent prompts via mng_role_system_links.
CREATE TABLE IF NOT EXISTS mng_system_roles (
    id          SERIAL        PRIMARY KEY,
    client_id   INT           NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    name        VARCHAR(255)  NOT NULL,
    description TEXT          NOT NULL DEFAULT '',
    content     TEXT          NOT NULL DEFAULT '',
    category    VARCHAR(50)   NOT NULL DEFAULT 'general',
    is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE(client_id, name)
);
CREATE INDEX IF NOT EXISTS idx_msr_client ON mng_system_roles(client_id);

-- mng_role_system_links: many-to-many between agent roles and system role fragments
CREATE TABLE IF NOT EXISTS mng_role_system_links (
    id             SERIAL      PRIMARY KEY,
    role_id        INT         NOT NULL REFERENCES mng_agent_roles(id) ON DELETE CASCADE,
    system_role_id INT         NOT NULL REFERENCES mng_system_roles(id) ON DELETE CASCADE,
    order_index    INT         NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(role_id, system_role_id)
);
CREATE INDEX IF NOT EXISTS idx_mrsl_role   ON mng_role_system_links(role_id);
CREATE INDEX IF NOT EXISTS idx_mrsl_sysrol ON mng_role_system_links(system_role_id);

-- mng_tags_categories: tag type definitions (feature, bug, task, design, etc.)
-- Shared across all projects; seeded at startup.
CREATE TABLE IF NOT EXISTS mng_tags_categories (
    id          SERIAL       PRIMARY KEY,
    client_id   INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    name        VARCHAR(100) NOT NULL,
    color       VARCHAR(30)  NOT NULL DEFAULT '#4a90e2',
    icon        VARCHAR(10)  NOT NULL DEFAULT '⬡',
    description TEXT         NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(client_id, name)
);

-- mng_deliveries: global lookup table of delivery output types
-- Admin-editable; used by planner_tags.deliveries picker in the UI.
-- category: 'code' | 'document' | 'architecture_design' | 'presentation'
CREATE TABLE IF NOT EXISTS mng_deliveries (
    id          SERIAL  PRIMARY KEY,
    category    TEXT    NOT NULL,
    type        TEXT    NOT NULL,
    label       TEXT    NOT NULL,
    sort_order  INT     NOT NULL DEFAULT 0,
    UNIQUE(category, type)
);

-- ============================================================================
-- SECTION 2: planner_* — User-managed Tag Hierarchy
-- ============================================================================

-- planner_tags: features, bugs, tasks with hierarchical structure
-- Used by the Planner UI to organise and track project work items.
-- embedding is from summary + action_items (same vector space as mem_ai_work_items).
CREATE TABLE IF NOT EXISTS planner_tags (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id          INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    name                TEXT        NOT NULL,
    category_id         INT         REFERENCES mng_tags_categories(id),
    parent_id           UUID        REFERENCES planner_tags(id),      -- hierarchical parent
    merged_into         UUID        REFERENCES planner_tags(id),      -- points to merged result
    description         TEXT        NOT NULL DEFAULT '',              -- user: what this item is
    requirements        TEXT        NOT NULL DEFAULT '',              -- user: what needs to happen
    acceptance_criteria TEXT        NOT NULL DEFAULT '',              -- user: how to verify done
    action_items        TEXT        NOT NULL DEFAULT '',              -- user+AI: next steps
    deliveries          JSONB       NOT NULL DEFAULT '[]',            -- selected delivery types [{category, type}]
    status              TEXT        NOT NULL DEFAULT 'open',          -- open|active|done|archived
    priority            SMALLINT    NOT NULL DEFAULT 3,
    due_date            DATE,
    requester           TEXT,
    creator             TEXT        NOT NULL DEFAULT 'user',          -- who created (username or 'ai')
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updater             TEXT        NOT NULL DEFAULT 'user',          -- who last updated
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, name, category_id)
);
CREATE INDEX IF NOT EXISTS idx_planner_tags_pid    ON planner_tags(project_id);
CREATE INDEX IF NOT EXISTS idx_planner_tags_parent ON planner_tags(parent_id);
CREATE INDEX IF NOT EXISTS idx_planner_tags_cat    ON planner_tags(category_id);

-- ============================================================================
-- SECTION 3: mem_mrr_* — Layer 1: Raw Mirroring
-- Stores every event as it happened; no transformation, no deduplication.
-- ============================================================================

-- mem_mrr_prompts: every prompt/response pair from all providers and UIs
-- tags JSONB carries inline metadata: {source, phase, feature, bug, work-item, session_id}
-- event_id: set after prompt batch digest in mem_ai_events (back-propagated by process_prompt_batch)
CREATE TABLE IF NOT EXISTS mem_mrr_prompts (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id  INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    event_id   UUID,                            -- FK to mem_ai_events.id (set after digest)
    session_id TEXT,
    source_id  TEXT,                            -- external ID for deduplication
    prompt     TEXT        NOT NULL DEFAULT '',
    response   TEXT        NOT NULL DEFAULT '',
    tags       JSONB       NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX        IF NOT EXISTS idx_mmrr_p_pid     ON mem_mrr_prompts(project_id);
CREATE INDEX        IF NOT EXISTS idx_mmrr_p_session ON mem_mrr_prompts(session_id) WHERE session_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_mmrr_p_source  ON mem_mrr_prompts(project_id, source_id) WHERE source_id IS NOT NULL;
CREATE INDEX        IF NOT EXISTS idx_mmrr_p_created ON mem_mrr_prompts(created_at DESC);
CREATE INDEX        IF NOT EXISTS idx_mmrr_p_tags    ON mem_mrr_prompts USING gin(tags);
CREATE INDEX        IF NOT EXISTS idx_mmrr_p_event   ON mem_mrr_prompts(event_id) WHERE event_id IS NOT NULL;

-- mem_mrr_commits: git commits with AI-generated metadata
-- commit_hash is the natural PK (git SHA).
-- tags = user intent: {phase, feature, bug} — sourced from mng_session_tags at push time.
-- event_id IS NULL means process_commit_batch() has not processed this commit yet.
-- Detailed per-symbol code data lives in mem_mrr_commits_code (one row per symbol).
CREATE TABLE IF NOT EXISTS mem_mrr_commits (
    commit_hash       VARCHAR(64)  PRIMARY KEY,
    commit_hash_short VARCHAR(8)   GENERATED ALWAYS AS (LEFT(commit_hash, 8)) STORED,
    client_id         INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id        INT          NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    commit_msg        TEXT         NOT NULL DEFAULT '',
    summary           TEXT         NOT NULL DEFAULT '',
    diff_summary      TEXT         NOT NULL DEFAULT '',  -- git --stat output
    tags              JSONB        NOT NULL DEFAULT '{}',
    prompt_id         UUID         REFERENCES mem_mrr_prompts(id) ON DELETE SET NULL,
    event_id          UUID,                              -- FK to mem_ai_events.id (set after batch digest)
    session_id        VARCHAR(255),
    author            TEXT         NOT NULL DEFAULT '',
    author_email      TEXT         NOT NULL DEFAULT '',
    llm               TEXT,                              -- model name used for digest
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    committed_at      TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_mmrr_c_pid            ON mem_mrr_commits(project_id);
CREATE INDEX IF NOT EXISTS idx_mmrr_c_comm           ON mem_mrr_commits(committed_at DESC);
CREATE INDEX IF NOT EXISTS idx_mmrr_c_session        ON mem_mrr_commits(session_id) WHERE session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mmrr_c_prompt         ON mem_mrr_commits(prompt_id) WHERE prompt_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mmrr_c_tags           ON mem_mrr_commits USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_mmrr_c_event          ON mem_mrr_commits(event_id) WHERE event_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mmrrc_project_session ON mem_mrr_commits(project_id, session_id) WHERE session_id IS NOT NULL;

-- mem_mrr_commits_code: per-symbol code statistics for each commit
-- Populated by memory_code_parser.extract_commit_code() using tree-sitter AST parsing.
-- One row per (commit, file, symbol_type, class_name, method_name).
CREATE TABLE IF NOT EXISTS mem_mrr_commits_code (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id     INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id    INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    commit_hash   VARCHAR(64) NOT NULL REFERENCES mem_mrr_commits(commit_hash) ON DELETE CASCADE,
    file_path     TEXT        NOT NULL,
    file_ext      TEXT        NOT NULL DEFAULT '',
    file_language TEXT        NOT NULL DEFAULT '',
    file_change   TEXT        NOT NULL CHECK (file_change IN ('added', 'modified', 'deleted', 'renamed')),
    symbol_type   TEXT        NOT NULL CHECK (symbol_type IN ('class', 'method', 'function', 'import')),
    class_name    TEXT,
    method_name   TEXT,
    full_symbol   TEXT GENERATED ALWAYS AS (
                      CASE
                          WHEN class_name IS NOT NULL AND method_name IS NOT NULL
                              THEN class_name || '.' || method_name
                          WHEN class_name IS NOT NULL THEN class_name
                          ELSE method_name
                      END
                  ) STORED,
    symbol_change TEXT        NOT NULL CHECK (symbol_change IN ('added', 'modified', 'deleted')),
    rows_added    INT         NOT NULL DEFAULT 0,
    rows_removed  INT         NOT NULL DEFAULT 0,
    diff_snippet  TEXT,
    llm_summary   TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (commit_hash, file_path, symbol_type,
            COALESCE(class_name, ''), COALESCE(method_name, ''))
);
CREATE INDEX IF NOT EXISTS idx_mmc_code_pid  ON mem_mrr_commits_code(project_id);
CREATE INDEX IF NOT EXISTS idx_mmc_code_hash ON mem_mrr_commits_code(commit_hash);
CREATE INDEX IF NOT EXISTS idx_mmc_code_sym  ON mem_mrr_commits_code(full_symbol) WHERE full_symbol IS NOT NULL;

-- mem_mrr_items: requirements, decisions, meeting notes
CREATE TABLE IF NOT EXISTS mem_mrr_items (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id  INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    item_type  TEXT        NOT NULL,
    title      TEXT,
    meeting_at TIMESTAMPTZ,
    attendees  TEXT[],
    raw_text   TEXT        NOT NULL,
    summary    TEXT,
    tags       JSONB       NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_mmrr_items_pid  ON mem_mrr_items(project_id);
CREATE INDEX IF NOT EXISTS idx_mmrr_items_type ON mem_mrr_items(item_type);
CREATE INDEX IF NOT EXISTS idx_mmrr_i_tags     ON mem_mrr_items USING gin(tags);

-- mem_mrr_messages: chat messages from Slack, Teams, Discord
CREATE TABLE IF NOT EXISTS mem_mrr_messages (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id  INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    platform   TEXT        NOT NULL,
    channel    TEXT,
    thread_ref TEXT,
    messages   JSONB       NOT NULL,
    date_range TSTZRANGE,
    tags       JSONB       NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_mmrr_messages_pid ON mem_mrr_messages(project_id);
CREATE INDEX IF NOT EXISTS idx_mmrr_m_tags       ON mem_mrr_messages USING gin(tags);

-- ============================================================================
-- SECTION 4: mem_ai_* — Layer 2/3: AI Digests + Structured Artifacts
-- ============================================================================

-- mem_ai_events: Haiku digest + OpenAI embedding for each batch/commit/session
-- event_type: 'prompt_batch'|'commit'|'item'|'message'|'session_summary'|'workflow'
-- event_cnt: how many mirror rows this event aggregates
--   prompt_batch → number of mem_mrr_prompts in the tag group (e.g. 5)
--   commit       → number of mem_mrr_commits in the tag group (e.g. 3)
--   item/message/session_summary → 1
-- source_id semantics (m032):
--   commit batch: 'batch_{first_hash8}_{tagfp8}' — one event per tag-group of commits
--   prompt_batch: UUID of the last mem_mrr_prompts row in the tag group
--   item/session_summary: 1:1 with source record UUID
-- tags: ONLY user-intent context — {phase, feature, bug, source}; no system metadata
-- processed_at: NULL = not yet processed by work item extraction pipeline
-- Relevance ordering: pure recency EXP(-0.01 * age_days); importance lives on mem_ai_work_items
CREATE TABLE IF NOT EXISTS mem_ai_events (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id    INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id   INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    event_type   TEXT        NOT NULL,
    event_cnt    INT         NOT NULL DEFAULT 0,                 -- mirror rows aggregated
    source_id    TEXT        NOT NULL,
    work_item_id UUID,                                           -- FK to mem_ai_work_items.id
    session_id   TEXT,
    chunk        INT         NOT NULL DEFAULT 0,
    chunk_type   TEXT        NOT NULL DEFAULT 'full',
    content      TEXT        NOT NULL DEFAULT '',
    summary      TEXT,
    action_items TEXT        NOT NULL DEFAULT '',
    tags         JSONB       NOT NULL DEFAULT '{}',              -- user-intent only: phase/feature/bug/source
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,                                    -- set by extract_work_items_from_events()
    embedding    VECTOR(1536),
    UNIQUE(project_id, event_type, source_id, chunk)
);
CREATE INDEX IF NOT EXISTS idx_mae_pid            ON mem_ai_events(project_id);
CREATE INDEX IF NOT EXISTS idx_mae_session        ON mem_ai_events(session_id);
CREATE INDEX IF NOT EXISTS idx_mae_type           ON mem_ai_events(event_type);
CREATE INDEX IF NOT EXISTS idx_mae_pending        ON mem_ai_events(processed_at) WHERE processed_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_mae_tags           ON mem_ai_events USING gin(tags);
CREATE INDEX IF NOT EXISTS idx_mae_embed          ON mem_ai_events USING ivfflat(embedding vector_cosine_ops) WHERE embedding IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mae_project_session ON mem_ai_events(project_id, session_id) WHERE session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mae_project_etype   ON mem_ai_events(project_id, event_type);
CREATE INDEX IF NOT EXISTS idx_mem_ai_events_wi    ON mem_ai_events(work_item_id) WHERE work_item_id IS NOT NULL;

-- mem_ai_work_items: AI-detected actionable items (tasks, bugs, features)
-- Dual-status design:
--   status_user = user-managed lifecycle (active|in_progress|paused|done)
--   status_ai   = AI-suggested status (auto-updated by promote_work_item())
-- tag_id_user = user-confirmed link to planner_tags (drag-drop in Planner UI)
-- tag_id_ai   = AI-suggested best-match tag (confidence > 0.70)
-- tags_ai     = AI-generated metadata JSONB (populated by extract_work_item_code_summary)
-- summary_ai  = PM digest: what was done, what remains, test coverage (written by promote_work_item)
CREATE TABLE IF NOT EXISTS mem_ai_work_items (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id          INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    category_ai         TEXT        NOT NULL,                           -- 'feature'|'bug'|'task'
    name_ai             TEXT        NOT NULL,
    desc_ai             TEXT        NOT NULL DEFAULT '',
    acceptance_criteria_ai TEXT     NOT NULL DEFAULT '',
    action_items_ai     TEXT        NOT NULL DEFAULT '',
    summary_ai          TEXT        NOT NULL DEFAULT '',
    tags                JSONB       NOT NULL DEFAULT '{}',
    tags_ai             JSONB       NOT NULL DEFAULT '{}',
    tag_id_ai           UUID        REFERENCES planner_tags(id),
    tag_id_user         UUID        REFERENCES planner_tags(id),
    merged_into         UUID        REFERENCES mem_ai_work_items(id) ON DELETE SET NULL,
    status_user         VARCHAR(20) NOT NULL DEFAULT 'active',
    seq_num             INT,
    start_date          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    embedding           VECTOR(1536),
    UNIQUE(project_id, category_ai, name_ai)
);
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_pid   ON mem_ai_work_items(project_id);
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_cat   ON mem_ai_work_items(category_ai);
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_suser ON mem_ai_work_items(status_user);
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_sai   ON mem_ai_work_items(status_ai);
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_seq   ON mem_ai_work_items(project_id, seq_num) WHERE seq_num IS NOT NULL;

-- mem_ai_project_facts: durable facts extracted from project history
-- valid_until NULL = currently valid fact; set to NOW() when superseded.
CREATE TABLE IF NOT EXISTS mem_ai_project_facts (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id        INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id       INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    fact_key         TEXT        NOT NULL,
    fact_value       TEXT        NOT NULL,
    category         TEXT        DEFAULT NULL,
    valid_from       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until      TIMESTAMPTZ,
    source_memory_id UUID,
    conflict_status  TEXT        DEFAULT NULL,
    embedding        VECTOR(1536)
);
CREATE INDEX        IF NOT EXISTS idx_mem_ai_pf_pid     ON mem_ai_project_facts(project_id) WHERE valid_until IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_mem_ai_pf_current ON mem_ai_project_facts(project_id, fact_key) WHERE valid_until IS NULL;

-- mem_ai_feature_snapshot: per-tag, per-use-case feature snapshots (version='ai'|'user')
-- version='ai' is overwritten on each snapshot run; version='user' is promoted by user.
CREATE TABLE IF NOT EXISTS mem_ai_feature_snapshot (
    id                          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id                   INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id                  INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    tag_id                      UUID        NOT NULL REFERENCES planner_tags(id) ON DELETE CASCADE,
    use_case_num                INT         NOT NULL,
    -- denorm from planner_tags (same across all rows for a tag+version)
    name                        TEXT        NOT NULL DEFAULT '',
    category                    TEXT        NOT NULL DEFAULT '',
    status                      TEXT        NOT NULL DEFAULT 'open',
    priority                    SMALLINT    NOT NULL DEFAULT 3,
    due_date                    DATE,
    -- global summary (identical on all rows for same tag+version)
    summary                     TEXT        NOT NULL DEFAULT '',
    -- per-use-case fields
    use_case_summary            TEXT        NOT NULL DEFAULT '',
    use_case_type               TEXT        NOT NULL DEFAULT 'feature',
    use_case_delivery_category  TEXT        NOT NULL DEFAULT '',
    use_case_delivery_type      TEXT        NOT NULL DEFAULT '',
    -- JSONB payloads
    related_work_items          JSONB       NOT NULL DEFAULT '[]',
    requirements                JSONB       NOT NULL DEFAULT '[]',
    action_items                JSONB       NOT NULL DEFAULT '[]',
    version                     TEXT        NOT NULL DEFAULT 'ai',
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, tag_id, use_case_num, version)
);
CREATE INDEX IF NOT EXISTS idx_mafs_project     ON mem_ai_feature_snapshot(project_id);
CREATE INDEX IF NOT EXISTS idx_mafs_tag         ON mem_ai_feature_snapshot(tag_id);
CREATE INDEX IF NOT EXISTS idx_mafs_tag_version ON mem_ai_feature_snapshot(tag_id, version);

-- ============================================================================
-- SECTION 5: pr_* — Graph Workflow Engine
-- ============================================================================

-- pr_graph_workflows: named workflow definitions (DAG of LLM nodes)
CREATE TABLE IF NOT EXISTS pr_graph_workflows (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id      INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id     INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    name           VARCHAR(255) NOT NULL,
    description    TEXT         NOT NULL DEFAULT '',
    max_iterations INTEGER      NOT NULL DEFAULT 3,
    log_directory  TEXT         NOT NULL DEFAULT '',
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, name)
);
CREATE INDEX IF NOT EXISTS idx_pr_gw_pid ON pr_graph_workflows(project_id);

-- pr_graph_nodes: individual LLM steps in a workflow (scoped via workflow FK)
-- inputs/outputs: JSON arrays of key names for pipeline data flow
-- tools: list of tool names enabled for the ReAct loop
CREATE TABLE IF NOT EXISTS pr_graph_nodes (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id      UUID        NOT NULL REFERENCES pr_graph_workflows(id) ON DELETE CASCADE,
    name             VARCHAR(255) NOT NULL,
    role_id          INT         REFERENCES mng_agent_roles(id) ON DELETE SET NULL,
    role_file        VARCHAR(255),
    role_prompt      TEXT        NOT NULL DEFAULT '',
    provider         VARCHAR(50) NOT NULL DEFAULT 'claude',
    model            VARCHAR(100) NOT NULL DEFAULT '',
    output_schema    JSONB,
    inject_context   BOOLEAN     NOT NULL DEFAULT TRUE,
    require_approval BOOLEAN     NOT NULL DEFAULT FALSE,
    approval_msg     TEXT        NOT NULL DEFAULT '',
    position_x       REAL        NOT NULL DEFAULT 100,
    position_y       REAL        NOT NULL DEFAULT 100,
    inputs           JSONB       NOT NULL DEFAULT '[]',
    outputs          JSONB       NOT NULL DEFAULT '[]',
    stateless        BOOLEAN     NOT NULL DEFAULT FALSE,
    retry_config     JSONB       NOT NULL DEFAULT '{}',
    success_criteria TEXT        NOT NULL DEFAULT '',
    order_index      INT         NOT NULL DEFAULT 0,
    max_retry        INT         NOT NULL DEFAULT 3,
    continue_on_fail BOOLEAN     NOT NULL DEFAULT FALSE,
    auto_commit      BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pr_gn_workflow ON pr_graph_nodes(workflow_id);

-- pr_graph_edges: directed connections between nodes (with optional conditions)
CREATE TABLE IF NOT EXISTS pr_graph_edges (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id    UUID        NOT NULL REFERENCES pr_graph_workflows(id) ON DELETE CASCADE,
    source_node_id UUID        NOT NULL REFERENCES pr_graph_nodes(id) ON DELETE CASCADE,
    target_node_id UUID        NOT NULL REFERENCES pr_graph_nodes(id) ON DELETE CASCADE,
    condition      JSONB,
    label          VARCHAR(255) NOT NULL DEFAULT '',
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pr_ge_workflow ON pr_graph_edges(workflow_id);

-- pr_graph_runs: individual workflow execution instances
CREATE TABLE IF NOT EXISTS pr_graph_runs (
    id             UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id      INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id     INT            NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    workflow_id    UUID           NOT NULL REFERENCES pr_graph_workflows(id) ON DELETE CASCADE,
    status         VARCHAR(50)    NOT NULL DEFAULT 'running',
    user_input     TEXT           NOT NULL DEFAULT '',
    context        JSONB          NOT NULL DEFAULT '{}',
    started_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    finished_at    TIMESTAMPTZ,
    total_cost_usd NUMERIC(12, 8) NOT NULL DEFAULT 0,
    error          TEXT,
    current_node   TEXT           DEFAULT NULL,   -- node currently executing
    snapshot_id    UUID           REFERENCES mem_ai_feature_snapshot(id) ON DELETE SET NULL,
    use_case_num   INT            DEFAULT NULL    -- use case that triggered this run
);
CREATE INDEX IF NOT EXISTS idx_pr_gr_pid      ON pr_graph_runs(project_id);
CREATE INDEX IF NOT EXISTS idx_pr_gr_workflow ON pr_graph_runs(workflow_id);

-- pr_graph_node_results: per-node execution results within a run
CREATE TABLE IF NOT EXISTS pr_graph_node_results (
    id            SERIAL         PRIMARY KEY,
    run_id        UUID           NOT NULL REFERENCES pr_graph_runs(id)  ON DELETE CASCADE,
    node_id       UUID           NOT NULL REFERENCES pr_graph_nodes(id) ON DELETE CASCADE,
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
CREATE INDEX IF NOT EXISTS idx_pr_gnr_run  ON pr_graph_node_results(run_id);
CREATE INDEX IF NOT EXISTS idx_pr_gnr_node ON pr_graph_node_results(node_id);

-- mem_pipeline_runs: background task observability — tracks every pipeline invocation
-- Powers GET /memory/{project}/pipeline-status dashboard.
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
);
CREATE INDEX IF NOT EXISTS idx_mpr_project_started ON mem_pipeline_runs(project_id, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_mpr_status ON mem_pipeline_runs(status) WHERE status = 'running';

-- pr_seq_counters: atomic sequential ID generators (one row per project+category)
-- Used to give work items human-readable numbers like #10001.
CREATE TABLE IF NOT EXISTS pr_seq_counters (
    project_id INT          NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    category   VARCHAR(100) NOT NULL,
    next_val   INT          NOT NULL DEFAULT 10000,
    PRIMARY KEY (project_id, category)
);
