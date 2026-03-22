"""
PostgreSQL connection pool — flat table architecture.

Two table namespaces only:
  mng_  — global + client-scoped (10 tables, client_id FK)
  pr_   — project-scoped (15 tables, client_id + project columns)

Total: 25 fixed tables regardless of client or project count.

Falls back gracefully when DATABASE_URL is not set — callers check `is_available()`.

Usage:
    from core.database import db

    cid = db.default_client_id()
    if db.is_available():
        with db.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM pr_commits WHERE client_id=%s AND project=%s",
                    (cid, project)
                )
    else:
        # fall back to file-based storage
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import psycopg2
import psycopg2.pool

from core.config import settings

log = logging.getLogger(__name__)

# ─── DDL: mng_clients ────────────────────────────────────────────────────────

_DDL_CLIENTS = """
CREATE TABLE IF NOT EXISTS mng_clients (
    id               SERIAL       PRIMARY KEY,
    slug             VARCHAR(50)  UNIQUE NOT NULL,
    name             VARCHAR(255) NOT NULL DEFAULT '',
    plan             VARCHAR(20)  NOT NULL DEFAULT 'free',
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    pricing_config    JSONB        DEFAULT NULL,
    provider_costs    JSONB        DEFAULT NULL,
    provider_balances JSONB        DEFAULT NULL,
    server_api_keys   JSONB        DEFAULT NULL
);
ALTER TABLE mng_clients ADD COLUMN IF NOT EXISTS pricing_config    JSONB DEFAULT NULL;
ALTER TABLE mng_clients ADD COLUMN IF NOT EXISTS provider_costs    JSONB DEFAULT NULL;
ALTER TABLE mng_clients ADD COLUMN IF NOT EXISTS provider_balances JSONB DEFAULT NULL;
ALTER TABLE mng_clients ADD COLUMN IF NOT EXISTS server_api_keys   JSONB DEFAULT NULL;
INSERT INTO mng_clients (id, slug, name, plan) VALUES (1, 'local', 'Local Install', 'free')
    ON CONFLICT (slug) DO NOTHING;
"""

# ─── DDL: mng_users / usage_logs / transactions ───────────────────────────────

_DDL_CORE = """
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
ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS client_id          INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id);
ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS role               VARCHAR(20)    NOT NULL DEFAULT 'free';
ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS balance_added_usd  NUMERIC(14, 8) NOT NULL DEFAULT 0;
ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS balance_used_usd   NUMERIC(14, 8) NOT NULL DEFAULT 0;
ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS coupons_used       TEXT[]         NOT NULL DEFAULT '{}';
ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100)   NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_users_email    ON mng_users(email);
CREATE INDEX IF NOT EXISTS idx_users_client   ON mng_users(client_id);

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
ALTER TABLE mng_usage_logs ADD COLUMN IF NOT EXISTS charged_usd   NUMERIC(12, 8) NOT NULL DEFAULT 0;
ALTER TABLE mng_usage_logs ADD COLUMN IF NOT EXISTS source        VARCHAR(50)    NOT NULL DEFAULT 'request';
ALTER TABLE mng_usage_logs ADD COLUMN IF NOT EXISTS metadata      JSONB          DEFAULT NULL;
ALTER TABLE mng_usage_logs ADD COLUMN IF NOT EXISTS period_start  TIMESTAMPTZ    DEFAULT NULL;
ALTER TABLE mng_usage_logs ADD COLUMN IF NOT EXISTS period_end    TIMESTAMPTZ    DEFAULT NULL;
CREATE INDEX IF NOT EXISTS idx_usage_user_id    ON mng_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_created_at ON mng_usage_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_provider   ON mng_usage_logs(provider);
CREATE INDEX IF NOT EXISTS idx_usage_source     ON mng_usage_logs(source);

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
"""

# ─── DDL: mng_user_api_keys ──────────────────────────────────────────────────

_DDL_USER_API_KEYS = """
CREATE TABLE IF NOT EXISTS mng_user_api_keys (
    id         SERIAL      PRIMARY KEY,
    user_id    VARCHAR(36) NOT NULL REFERENCES mng_users(id) ON DELETE CASCADE,
    provider   VARCHAR(50) NOT NULL,
    key_enc    TEXT        NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, provider)
);
CREATE INDEX IF NOT EXISTS idx_muak_user ON mng_user_api_keys(user_id);
"""

# ─── DDL: mng_coupons ────────────────────────────────────────────────────────

_DDL_COUPONS = """
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
CREATE INDEX IF NOT EXISTS idx_mcp_client ON mng_coupons(client_id);
"""

# ─── DDL: mng_* entity + session + role tables ───────────────────────────────

_DDL_MNG_TABLES = """
-- Session tags per client+project
CREATE TABLE IF NOT EXISTS mng_session_tags (
    id         SERIAL       PRIMARY KEY,
    client_id  INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project    VARCHAR(255) NOT NULL,
    phase      VARCHAR(50),
    feature    VARCHAR(255),
    bug_ref    VARCHAR(255),
    extra      JSONB        NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE(client_id, project)
);
ALTER TABLE mng_session_tags ADD COLUMN IF NOT EXISTS
    client_id INT NOT NULL DEFAULT 1 REFERENCES mng_clients(id);
CREATE INDEX IF NOT EXISTS idx_mst_cp ON mng_session_tags(client_id, project);

-- Entity categories per client+project
CREATE TABLE IF NOT EXISTS mng_entity_categories (
    id         SERIAL       PRIMARY KEY,
    client_id  INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project    VARCHAR(255) NOT NULL,
    name       VARCHAR(100) NOT NULL,
    color      VARCHAR(30)  NOT NULL DEFAULT '#4a90e2',
    icon       VARCHAR(10)  NOT NULL DEFAULT '⬡',
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
ALTER TABLE mng_entity_categories ADD COLUMN IF NOT EXISTS
    client_id INT NOT NULL DEFAULT 1 REFERENCES mng_clients(id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mec_cid_proj_name
    ON mng_entity_categories(client_id, project, name);
CREATE INDEX IF NOT EXISTS idx_mec_cp ON mng_entity_categories(client_id, project);

-- Entity values (features, bugs, tasks, docs)
CREATE TABLE IF NOT EXISTS mng_entity_values (
    id               SERIAL       PRIMARY KEY,
    client_id        INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    category_id      INT          REFERENCES mng_entity_categories(id) ON DELETE CASCADE,
    project          VARCHAR(255) NOT NULL,
    name             VARCHAR(255) NOT NULL,
    description      TEXT         NOT NULL DEFAULT '',
    status           VARCHAR(20)  NOT NULL DEFAULT 'active',
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    due_date         DATE,
    parent_id        INT          REFERENCES mng_entity_values(id) ON DELETE SET NULL,
    lifecycle_status VARCHAR(20)  NOT NULL DEFAULT 'idea',
    UNIQUE(client_id, project, name)
);
ALTER TABLE mng_entity_values ADD COLUMN IF NOT EXISTS
    client_id INT NOT NULL DEFAULT 1 REFERENCES mng_clients(id);
CREATE INDEX IF NOT EXISTS idx_mev_cp  ON mng_entity_values(client_id, project);
CREATE INDEX IF NOT EXISTS idx_mev_cat ON mng_entity_values(category_id);
CREATE INDEX IF NOT EXISTS idx_mev_par ON mng_entity_values(parent_id);

-- Entity value dependency links
CREATE TABLE IF NOT EXISTS mng_entity_value_links (
    from_value_id INT         NOT NULL REFERENCES mng_entity_values(id) ON DELETE CASCADE,
    to_value_id   INT         NOT NULL REFERENCES mng_entity_values(id) ON DELETE CASCADE,
    link_type     VARCHAR(50) NOT NULL DEFAULT 'blocks',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(from_value_id, to_value_id, link_type)
);
CREATE INDEX IF NOT EXISTS idx_mevl_from ON mng_entity_value_links(from_value_id);
CREATE INDEX IF NOT EXISTS idx_mevl_to   ON mng_entity_value_links(to_value_id);

-- Agent roles per client+project (templates + custom)
CREATE TABLE IF NOT EXISTS mng_agent_roles (
    id            SERIAL       PRIMARY KEY,
    client_id     INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project       VARCHAR(100) NOT NULL DEFAULT '_global',
    name          VARCHAR(255) NOT NULL,
    description   TEXT         NOT NULL DEFAULT '',
    system_prompt TEXT         NOT NULL DEFAULT '',
    provider      VARCHAR(50)  NOT NULL DEFAULT 'claude',
    model         VARCHAR(100) NOT NULL DEFAULT '',
    tags          TEXT[]       NOT NULL DEFAULT '{}',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS
    client_id INT NOT NULL DEFAULT 1 REFERENCES mng_clients(id);
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS inputs        JSONB        DEFAULT '[]';
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS outputs       JSONB        DEFAULT '[]';
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS role_type     VARCHAR(50)  NOT NULL DEFAULT 'agent';
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS output_schema JSONB        DEFAULT NULL;
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS auto_commit   BOOLEAN      NOT NULL DEFAULT FALSE;
CREATE UNIQUE INDEX IF NOT EXISTS idx_mar_cid_proj_name
    ON mng_agent_roles(client_id, project, name);
CREATE INDEX IF NOT EXISTS idx_mar_cp ON mng_agent_roles(client_id, project);

-- Agent role version history
CREATE TABLE IF NOT EXISTS mng_agent_role_versions (
    id            SERIAL       PRIMARY KEY,
    role_id       INT          NOT NULL REFERENCES mng_agent_roles(id) ON DELETE CASCADE,
    system_prompt TEXT         NOT NULL DEFAULT '',
    provider      VARCHAR(50)  NOT NULL DEFAULT 'claude',
    model         VARCHAR(100) NOT NULL DEFAULT '',
    changed_by    VARCHAR(255),
    changed_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    note          TEXT         NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_marv_role ON mng_agent_role_versions(role_id);

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
"""

# ─── DDL: pr_* flat project tables (15) ──────────────────────────────────────

_DDL_PR_TABLES = """
-- pgvector extension (needed for embedding columns)
CREATE EXTENSION IF NOT EXISTS vector;

-- Commits
CREATE TABLE IF NOT EXISTS pr_commits (
    id               SERIAL         PRIMARY KEY,
    client_id        INT            NOT NULL REFERENCES mng_clients(id),
    project          VARCHAR(255)   NOT NULL,
    commit_hash      VARCHAR(64)    NOT NULL,
    commit_msg       TEXT           NOT NULL DEFAULT '',
    summary          TEXT           NOT NULL DEFAULT '',
    phase            VARCHAR(20),
    feature          VARCHAR(255),
    bug_ref          VARCHAR(255),
    source           VARCHAR(50)    NOT NULL DEFAULT 'git',
    session_id       VARCHAR(255),
    prompt_source_id VARCHAR(255),
    tags             JSONB          NOT NULL DEFAULT '{}',
    committed_at     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE(commit_hash)
);
CREATE INDEX IF NOT EXISTS idx_pr_c_cp       ON pr_commits(client_id, project);
CREATE INDEX IF NOT EXISTS idx_pr_c_comm     ON pr_commits(committed_at DESC);
CREATE INDEX IF NOT EXISTS idx_pr_c_session  ON pr_commits(session_id) WHERE session_id IS NOT NULL;

-- Events (prompt/response log entries)
CREATE TABLE IF NOT EXISTS pr_events (
    id         SERIAL         PRIMARY KEY,
    client_id  INT            NOT NULL REFERENCES mng_clients(id),
    project    VARCHAR(255)   NOT NULL,
    event_type VARCHAR(50)    NOT NULL,
    source_id  VARCHAR(255)   NOT NULL,
    title      TEXT           NOT NULL DEFAULT '',
    content    TEXT           NOT NULL DEFAULT '',
    phase      VARCHAR(20),
    feature    VARCHAR(255),
    session_id VARCHAR(255),
    metadata   JSONB          NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE(client_id, project, event_type, source_id)
);
CREATE INDEX IF NOT EXISTS idx_pr_e_cp      ON pr_events(client_id, project);
CREATE INDEX IF NOT EXISTS idx_pr_e_type    ON pr_events(event_type);
CREATE INDEX IF NOT EXISTS idx_pr_e_created ON pr_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pr_e_session ON pr_events(session_id)   WHERE session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_pr_e_phase   ON pr_events(phase)        WHERE phase IS NOT NULL;

-- Embeddings (pgvector)
CREATE TABLE IF NOT EXISTS pr_embeddings (
    id          SERIAL         PRIMARY KEY,
    client_id   INT            NOT NULL REFERENCES mng_clients(id),
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
    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE(client_id, project, source_type, source_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_pr_emb_cp   ON pr_embeddings(client_id, project);
CREATE INDEX IF NOT EXISTS idx_pr_emb_lang ON pr_embeddings(language) WHERE language IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_pr_emb_src  ON pr_embeddings(source_type, source_id);

-- Event tags (links events to entity values; scoped via event FK)
CREATE TABLE IF NOT EXISTS pr_event_tags (
    event_id        INT         NOT NULL,
    entity_value_id INT         NOT NULL REFERENCES mng_entity_values(id) ON DELETE CASCADE,
    auto_tagged     BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(event_id, entity_value_id)
);
CREATE INDEX IF NOT EXISTS idx_pr_et_event ON pr_event_tags(event_id);
CREATE INDEX IF NOT EXISTS idx_pr_et_value ON pr_event_tags(entity_value_id);

-- Event links (connections between events; scoped via event FKs)
CREATE TABLE IF NOT EXISTS pr_event_links (
    from_event_id INT         NOT NULL,
    to_event_id   INT         NOT NULL,
    link_type     VARCHAR(50) NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(from_event_id, to_event_id, link_type)
);
CREATE INDEX IF NOT EXISTS idx_pr_el_from ON pr_event_links(from_event_id);
CREATE INDEX IF NOT EXISTS idx_pr_el_to   ON pr_event_links(to_event_id);

-- Work items (feature/bug/task pipeline tracking)
CREATE TABLE IF NOT EXISTS pr_work_items (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           INT           NOT NULL REFERENCES mng_clients(id),
    project             VARCHAR(255)  NOT NULL,
    category_name       TEXT          NOT NULL,
    category_id         INT           REFERENCES mng_entity_categories(id) ON DELETE SET NULL,
    name                TEXT          NOT NULL,
    description         TEXT          NOT NULL DEFAULT '',
    status              VARCHAR(20)   NOT NULL DEFAULT 'active',
    lifecycle_status    VARCHAR(20)   NOT NULL DEFAULT 'idea',
    due_date            DATE,
    parent_id           UUID          REFERENCES pr_work_items(id) ON DELETE SET NULL,
    acceptance_criteria TEXT          NOT NULL DEFAULT '',
    implementation_plan TEXT          NOT NULL DEFAULT '',
    agent_run_id        UUID,
    agent_status        VARCHAR(20),
    tags                TEXT[]        NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE(client_id, project, category_name, name)
);
CREATE INDEX IF NOT EXISTS idx_pr_wi_cp     ON pr_work_items(client_id, project);
CREATE INDEX IF NOT EXISTS idx_pr_wi_cat    ON pr_work_items(category_name);
CREATE INDEX IF NOT EXISTS idx_pr_wi_status ON pr_work_items(status);

-- Interactions (unified prompt/response log)
CREATE TABLE IF NOT EXISTS pr_interactions (
    id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           INT           NOT NULL REFERENCES mng_clients(id),
    project             VARCHAR(255)  NOT NULL,
    work_item_id        UUID          REFERENCES pr_work_items(id) ON DELETE SET NULL,
    session_id          TEXT,
    llm_source          TEXT,
    event_type          TEXT          NOT NULL DEFAULT 'prompt',
    source_id           TEXT,
    prompt              TEXT          NOT NULL DEFAULT '',
    response            TEXT          NOT NULL DEFAULT '',
    prompt_embedding    VECTOR(1536),
    response_embedding  VECTOR(1536),
    phase               TEXT,
    tags                TEXT[]        NOT NULL DEFAULT '{}',
    metadata            JSONB         NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS        idx_pr_i_cp      ON pr_interactions(client_id, project);
CREATE INDEX IF NOT EXISTS        idx_pr_i_session ON pr_interactions(session_id) WHERE session_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_pr_i_source  ON pr_interactions(client_id, project, source_id) WHERE source_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS        idx_pr_i_created ON pr_interactions(created_at DESC);
CREATE INDEX IF NOT EXISTS        idx_pr_i_wi      ON pr_interactions(work_item_id) WHERE work_item_id IS NOT NULL;

-- Interaction tags (links interactions to work items; scoped via interaction FK)
CREATE TABLE IF NOT EXISTS pr_interaction_tags (
    interaction_id  UUID          NOT NULL REFERENCES pr_interactions(id)  ON DELETE CASCADE,
    work_item_id    UUID          NOT NULL REFERENCES pr_work_items(id)     ON DELETE CASCADE,
    auto_tagged     BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    PRIMARY KEY(interaction_id, work_item_id)
);
CREATE INDEX IF NOT EXISTS idx_pr_itag_work ON pr_interaction_tags(work_item_id);

-- Memory items (distilled session/feature summaries)
CREATE TABLE IF NOT EXISTS pr_memory_items (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id        INT           NOT NULL REFERENCES mng_clients(id),
    project          VARCHAR(255)  NOT NULL,
    scope            TEXT          NOT NULL,
    scope_ref        TEXT,
    content          TEXT          NOT NULL,
    embedding        VECTOR(1536),
    source_ids       UUID[]        NOT NULL DEFAULT '{}',
    tags             TEXT[]        NOT NULL DEFAULT '{}',
    reviewer_score   INT,
    reviewer_critique TEXT,
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pr_mi_cp      ON pr_memory_items(client_id, project);
CREATE INDEX IF NOT EXISTS idx_pr_mi_scope   ON pr_memory_items(client_id, project, scope);
CREATE INDEX IF NOT EXISTS idx_pr_mi_created ON pr_memory_items(created_at DESC);

-- Project facts (durable extracted facts; valid_until NULL = current)
CREATE TABLE IF NOT EXISTS pr_project_facts (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id        INT           NOT NULL REFERENCES mng_clients(id),
    project          VARCHAR(255)  NOT NULL,
    fact_key         TEXT          NOT NULL,
    fact_value       TEXT          NOT NULL,
    valid_from       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    valid_until      TIMESTAMPTZ,
    source_memory_id UUID          REFERENCES pr_memory_items(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS        idx_pr_pf_cp      ON pr_project_facts(client_id, project) WHERE valid_until IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_pr_pf_current ON pr_project_facts(client_id, project, fact_key) WHERE valid_until IS NULL;

-- Graph workflow definitions
CREATE TABLE IF NOT EXISTS pr_graph_workflows (
    id             UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id      INT            NOT NULL REFERENCES mng_clients(id),
    project        VARCHAR(255)   NOT NULL,
    name           VARCHAR(255)   NOT NULL,
    description    TEXT           NOT NULL DEFAULT '',
    max_iterations INTEGER        NOT NULL DEFAULT 3,
    created_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE(client_id, project, name)
);
ALTER TABLE pr_graph_workflows ADD COLUMN IF NOT EXISTS log_directory TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_pr_gw_cp ON pr_graph_workflows(client_id, project);

-- Graph nodes (LLM steps; scoped via workflow FK)
CREATE TABLE IF NOT EXISTS pr_graph_nodes (
    id               UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id      UUID           NOT NULL REFERENCES pr_graph_workflows(id) ON DELETE CASCADE,
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
CREATE INDEX IF NOT EXISTS idx_pr_gn_workflow ON pr_graph_nodes(workflow_id);
ALTER TABLE pr_graph_nodes ADD COLUMN IF NOT EXISTS inputs           JSONB   DEFAULT '[]';
ALTER TABLE pr_graph_nodes ADD COLUMN IF NOT EXISTS outputs          JSONB   DEFAULT '[]';
ALTER TABLE pr_graph_nodes ADD COLUMN IF NOT EXISTS stateless        BOOLEAN DEFAULT FALSE;
ALTER TABLE pr_graph_nodes ADD COLUMN IF NOT EXISTS retry_config     JSONB   DEFAULT '{}';
ALTER TABLE pr_graph_nodes ADD COLUMN IF NOT EXISTS success_criteria TEXT    DEFAULT '';
ALTER TABLE pr_graph_nodes ADD COLUMN IF NOT EXISTS order_index      INT     NOT NULL DEFAULT 0;
ALTER TABLE pr_graph_nodes ADD COLUMN IF NOT EXISTS max_retry        INT     NOT NULL DEFAULT 3;
ALTER TABLE pr_graph_nodes ADD COLUMN IF NOT EXISTS continue_on_fail BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE pr_graph_nodes ADD COLUMN IF NOT EXISTS auto_commit      BOOLEAN NOT NULL DEFAULT FALSE;

-- Graph edges (scoped via workflow FK)
CREATE TABLE IF NOT EXISTS pr_graph_edges (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    workflow_id    UUID         NOT NULL REFERENCES pr_graph_workflows(id) ON DELETE CASCADE,
    source_node_id UUID         NOT NULL REFERENCES pr_graph_nodes(id) ON DELETE CASCADE,
    target_node_id UUID         NOT NULL REFERENCES pr_graph_nodes(id) ON DELETE CASCADE,
    condition      JSONB,
    label          VARCHAR(255) NOT NULL DEFAULT '',
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_pr_ge_workflow ON pr_graph_edges(workflow_id);

-- Workflow run instances
CREATE TABLE IF NOT EXISTS pr_graph_runs (
    id             UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id      INT            NOT NULL REFERENCES mng_clients(id),
    project        VARCHAR(255)   NOT NULL,
    workflow_id    UUID           NOT NULL REFERENCES pr_graph_workflows(id) ON DELETE CASCADE,
    status         VARCHAR(50)    NOT NULL DEFAULT 'running',
    user_input     TEXT           NOT NULL DEFAULT '',
    context        JSONB          NOT NULL DEFAULT '{}',
    started_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    finished_at    TIMESTAMPTZ,
    total_cost_usd NUMERIC(12, 8) NOT NULL DEFAULT 0,
    error          TEXT
);
CREATE INDEX IF NOT EXISTS idx_pr_gr_cp       ON pr_graph_runs(client_id, project);
CREATE INDEX IF NOT EXISTS idx_pr_gr_workflow ON pr_graph_runs(workflow_id);
ALTER TABLE pr_graph_runs ADD COLUMN IF NOT EXISTS current_node TEXT DEFAULT NULL;

-- Node results per run (scoped via run FK)
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

-- Sequential ID counters (atomic per project+category)
CREATE TABLE IF NOT EXISTS pr_seq_counters (
    client_id INT          NOT NULL REFERENCES mng_clients(id),
    project   VARCHAR(255) NOT NULL,
    category  VARCHAR(100) NOT NULL,
    next_val  INT          NOT NULL DEFAULT 10000,
    PRIMARY KEY (client_id, project, category)
);
ALTER TABLE pr_work_items     ADD COLUMN IF NOT EXISTS seq_num         INT;
ALTER TABLE mng_entity_values ADD COLUMN IF NOT EXISTS seq_num         INT;
ALTER TABLE pr_work_items     ADD COLUMN IF NOT EXISTS entity_value_id INT REFERENCES mng_entity_values(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_pr_wi_seq   ON pr_work_items(client_id, project, seq_num) WHERE seq_num IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mev_seq     ON mng_entity_values(client_id, project, seq_num) WHERE seq_num IS NOT NULL;
"""


# ─── Database class ───────────────────────────────────────────────────────────

class _Database:
    def __init__(self) -> None:
        self._pool: psycopg2.pool.ThreadedConnectionPool | None = None
        self._available: bool = False
        self._shared_schema_ready: bool = False
        self._client_id_cache: dict[str, int] = {}

    def init(self) -> None:
        """Called at startup. Creates connection pool and runs all schema migrations."""
        url = settings.database_url
        if not url:
            log.info("DATABASE_URL not set — using file-based storage")
            return
        try:
            import socket as _socket
            # socket.setdefaulttimeout covers TCP + SSL + PostgreSQL handshake.
            # connect_timeout only covers the TCP SYN, so we need both.
            _old_timeout = _socket.getdefaulttimeout()
            _socket.setdefaulttimeout(10.0)
            try:
                self._pool = psycopg2.pool.ThreadedConnectionPool(1, settings.db_pool_max, url)
            finally:
                _socket.setdefaulttimeout(_old_timeout)
            with self.conn() as conn:
                self._rename_legacy_tables(conn)
                self._ensure_schema(conn)
                self._ensure_shared_schema(conn)
                self._migrate_to_flat_tables(conn)
                # Populate client_id cache
                with conn.cursor() as cur:
                    cur.execute("SELECT slug, id FROM mng_clients")
                    for slug, cid in cur.fetchall():
                        self._client_id_cache[slug] = cid
            self._available = True
            log.info("✅ PostgreSQL connected — flat table architecture (mng_ + pr_)")
        except Exception as e:
            log.warning(f"PostgreSQL unavailable ({e}) — falling back to file store")
            self._pool = None
            self._available = False

    def is_available(self) -> bool:
        return self._available

    def default_client_id(self) -> int:
        """Return the client_id for the local installation (always 1)."""
        return self._client_id_cache.get("local", 1)

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

    # ── Schema creation ────────────────────────────────────────────────────────

    @staticmethod
    def _run_ddl_statements(conn, sql: str, label: str) -> None:
        """Run each semicolon-separated SQL statement individually.

        This prevents a single failed statement (e.g. CREATE INDEX on a column
        that doesn't exist yet) from rolling back an entire DDL block.
        """
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if not stmt or stmt.startswith("--"):
                continue
            try:
                with conn.cursor() as cur:
                    cur.execute(stmt)
                conn.commit()
            except Exception as e:
                conn.rollback()
                msg = str(e).strip()
                # Silence noise for expected "already exists" situations
                if "already exists" not in msg.lower():
                    log.debug(f"{label} stmt skipped: {msg[:120]}")

    @staticmethod
    def _ensure_schema(conn) -> None:
        """Create / migrate mng_* tables. Safe to run repeatedly."""
        # Run each DDL block statement-by-statement so one failure doesn't
        # roll back the entire block (e.g. CREATE INDEX after ALTER TABLE ADD COLUMN).
        for label, sql in [
            ("mng_clients", _DDL_CLIENTS),
            ("mng_core (users/usage/tx)", _DDL_CORE),
            ("mng_user_api_keys", _DDL_USER_API_KEYS),
            ("mng_coupons", _DDL_COUPONS),
            ("mng_entity+session+role tables", _DDL_MNG_TABLES),
        ]:
            _Database._run_ddl_statements(conn, sql, label)
            log.debug(f"✅ {label} DDL done")

        # Seed built-in global agent roles + system roles + links (idempotent)
        _Database._seed_agent_roles(conn)
        _Database._seed_system_roles(conn)
        _Database._seed_role_system_links(conn)

    def _ensure_shared_schema(self, conn) -> None:
        """Create all 15 pr_* flat tables. Runs once per process lifetime.

        Uses statement-by-statement execution so one failed ALTER TABLE
        (e.g. on an already-migrated DB) doesn't roll back all table creation.
        """
        if self._shared_schema_ready:
            return
        _Database._run_ddl_statements(conn, _DDL_PR_TABLES, "pr_* flat tables")
        self._shared_schema_ready = True
        log.info("✅ pr_* flat tables ready")

    # ── One-time data migration ────────────────────────────────────────────────

    @staticmethod
    def _migrate_to_flat_tables(conn) -> None:
        """Idempotent: cl_local_* + pr_local_* → flat mng_/pr_ tables, then DROP old tables."""

        def _tbl_exists(cur, name: str) -> bool:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name=%s",
                (name,),
            )
            return cur.fetchone() is not None

        try:
            with conn.cursor() as cur:

                # ── Step 1: seed mng_clients ──────────────────────────────────
                cur.execute(
                    """INSERT INTO mng_clients (slug, name, plan)
                       VALUES ('local', 'Local Install', 'free')
                       ON CONFLICT (slug) DO NOTHING"""
                )
                conn.commit()

                # ── Step 2: cl_local_entity_categories → mng_entity_categories ─
                cat_id_map: dict[int, int] = {}
                if _tbl_exists(cur, "cl_local_entity_categories"):
                    cur.execute(
                        "SELECT id, project, name, color, icon, created_at "
                        "FROM cl_local_entity_categories"
                    )
                    old_cats = cur.fetchall()
                    for (old_id, proj, name, color, icon, ts) in old_cats:
                        cur.execute(
                            """INSERT INTO mng_entity_categories
                                   (client_id, project, name, color, icon, created_at)
                               VALUES (1, %s, %s, %s, %s, %s)
                               ON CONFLICT (client_id, project, name) DO NOTHING
                               RETURNING id""",
                            (proj, name, color, icon, ts),
                        )
                        row = cur.fetchone()
                        if row:
                            cat_id_map[old_id] = row[0]
                        else:
                            cur.execute(
                                "SELECT id FROM mng_entity_categories "
                                "WHERE client_id=1 AND project=%s AND name=%s",
                                (proj, name),
                            )
                            r = cur.fetchone()
                            if r:
                                cat_id_map[old_id] = r[0]
                    conn.commit()
                    cur.execute("DROP TABLE IF EXISTS cl_local_entity_categories CASCADE")
                    conn.commit()
                    log.info(f"Migrated {len(old_cats)} entity categories cl_local→mng")

                # ── Step 3: cl_local_entity_values → mng_entity_values ────────
                ev_id_map: dict[int, int] = {}
                if _tbl_exists(cur, "cl_local_entity_values"):
                    cur.execute(
                        "SELECT id, category_id, project, name, description, status, "
                        "created_at, due_date, parent_id, lifecycle_status "
                        "FROM cl_local_entity_values ORDER BY id"
                    )
                    old_evs = cur.fetchall()
                    for (old_id, old_cat, proj, name, desc, status,
                         ts, due, old_par, lc) in old_evs:
                        new_cat = cat_id_map.get(old_cat) if old_cat else None
                        cur.execute(
                            """INSERT INTO mng_entity_values
                                   (client_id, category_id, project, name, description,
                                    status, created_at, due_date, lifecycle_status)
                               VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s)
                               ON CONFLICT DO NOTHING
                               RETURNING id""",
                            (new_cat, proj, name, desc or "", status or "active",
                             ts, due, lc or "idea"),
                        )
                        row = cur.fetchone()
                        if row:
                            ev_id_map[old_id] = row[0]
                        else:
                            cur.execute(
                                "SELECT id FROM mng_entity_values "
                                "WHERE client_id=1 AND project=%s AND name=%s "
                                "AND COALESCE(category_id,0)=%s LIMIT 1",
                                (proj, name, new_cat or 0),
                            )
                            r = cur.fetchone()
                            if r:
                                ev_id_map[old_id] = r[0]
                    # Second pass: fix parent_id refs
                    for (old_id, _, _, _, _, _, _, _, old_par, _) in old_evs:
                        if old_par and old_id in ev_id_map and old_par in ev_id_map:
                            cur.execute(
                                "UPDATE mng_entity_values SET parent_id=%s "
                                "WHERE id=%s AND parent_id IS NULL",
                                (ev_id_map[old_par], ev_id_map[old_id]),
                            )
                    conn.commit()
                    cur.execute("DROP TABLE IF EXISTS cl_local_entity_values CASCADE")
                    conn.commit()
                    log.info(f"Migrated {len(old_evs)} entity values cl_local→mng")

                # ── Step 4: cl_local_entity_value_links → mng_entity_value_links
                if _tbl_exists(cur, "cl_local_entity_value_links"):
                    cur.execute(
                        "SELECT from_value_id, to_value_id, link_type, created_at "
                        "FROM cl_local_entity_value_links"
                    )
                    for (f_id, t_id, lt, ts) in cur.fetchall():
                        nf, nt = ev_id_map.get(f_id), ev_id_map.get(t_id)
                        if nf and nt:
                            cur.execute(
                                """INSERT INTO mng_entity_value_links
                                       (from_value_id, to_value_id, link_type, created_at)
                                   VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                                (nf, nt, lt, ts),
                            )
                    conn.commit()
                    cur.execute("DROP TABLE IF EXISTS cl_local_entity_value_links")
                    conn.commit()

                # ── Step 5: cl_local_session_tags → mng_session_tags ──────────
                if _tbl_exists(cur, "cl_local_session_tags"):
                    cur.execute(
                        "SELECT project, phase, feature, bug_ref, extra, updated_at "
                        "FROM cl_local_session_tags"
                    )
                    for row in cur.fetchall():
                        cur.execute(
                            """INSERT INTO mng_session_tags
                                   (client_id, project, phase, feature, bug_ref, extra, updated_at)
                               VALUES (1, %s, %s, %s, %s, %s, %s)
                               ON CONFLICT (client_id, project) DO NOTHING""",
                            (row[0], row[1], row[2], row[3], row[4], row[5]),
                        )
                    conn.commit()
                    cur.execute("DROP TABLE IF EXISTS cl_local_session_tags")
                    conn.commit()

                # ── Step 6: cl_local_agent_roles → mng_agent_roles ────────────
                ar_id_map: dict[int, int] = {}
                if _tbl_exists(cur, "cl_local_agent_roles"):
                    cur.execute(
                        "SELECT id, project, name, description, system_prompt, "
                        "provider, model, tags, is_active, created_at, updated_at "
                        "FROM cl_local_agent_roles"
                    )
                    old_ars = cur.fetchall()
                    for (old_id, proj, name, desc, prompt, prov,
                         model, tags, active, ts, upd) in old_ars:
                        cur.execute(
                            """INSERT INTO mng_agent_roles
                                   (client_id, project, name, description, system_prompt,
                                    provider, model, tags, is_active, created_at, updated_at)
                               VALUES (1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                               ON CONFLICT (client_id, project, name) DO NOTHING
                               RETURNING id""",
                            (proj, name, desc or "", prompt or "", prov,
                             model, tags, active, ts, upd),
                        )
                        row = cur.fetchone()
                        if row:
                            ar_id_map[old_id] = row[0]
                        else:
                            cur.execute(
                                "SELECT id FROM mng_agent_roles "
                                "WHERE client_id=1 AND project=%s AND name=%s",
                                (proj, name),
                            )
                            r = cur.fetchone()
                            if r:
                                ar_id_map[old_id] = r[0]
                    conn.commit()
                    cur.execute("DROP TABLE IF EXISTS cl_local_agent_roles CASCADE")
                    conn.commit()
                    log.info(f"Migrated {len(old_ars)} agent roles cl_local→mng")

                # ── Step 7: cl_local_agent_role_versions → mng_agent_role_versions
                if _tbl_exists(cur, "cl_local_agent_role_versions"):
                    cur.execute(
                        "SELECT role_id, system_prompt, provider, model, "
                        "changed_by, changed_at, note FROM cl_local_agent_role_versions"
                    )
                    for (old_rid, prompt, prov, model, chby, chat, note) in cur.fetchall():
                        new_rid = ar_id_map.get(old_rid)
                        if new_rid:
                            cur.execute(
                                """INSERT INTO mng_agent_role_versions
                                       (role_id, system_prompt, provider, model,
                                        changed_by, changed_at, note)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                                   ON CONFLICT DO NOTHING""",
                                (new_rid, prompt, prov, model, chby, chat, note),
                            )
                    conn.commit()
                    cur.execute("DROP TABLE IF EXISTS cl_local_agent_role_versions")
                    conn.commit()

                # ── Step 8: discover + migrate pr_local_{p}_* tables ──────────
                cur.execute(
                    "SELECT tablename FROM pg_tables "
                    "WHERE schemaname='public' AND tablename LIKE 'pr_local_%_commits'"
                )
                project_slugs = [
                    row[0][len("pr_local_"):-len("_commits")]
                    for row in cur.fetchall()
                ]
                conn.commit()

                for p in project_slugs:
                    _Database._migrate_project_tables(
                        cur, conn, p, cat_id_map, ev_id_map, ar_id_map
                    )
                    log.info(f"✅ Migrated per-project tables for '{p}'")

        except Exception as exc:
            conn.rollback()
            log.warning(f"_migrate_to_flat_tables failed: {exc}")

    @staticmethod
    def _migrate_project_tables(
        cur,
        conn,
        p: str,
        cat_id_map: dict[int, int],
        ev_id_map: dict[int, int],
        ar_id_map: dict[int, int],
    ) -> None:
        """Migrate all pr_local_{p}_* tables into flat pr_* tables for project p."""

        def _tbl(base: str) -> str:
            return f"pr_local_{p}_{base}"

        def _exists(name: str) -> bool:
            cur.execute(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name=%s",
                (name,),
            )
            return cur.fetchone() is not None

        def _run(sql: str) -> None:
            try:
                cur.execute(sql)
                conn.commit()
            except Exception as e:
                conn.rollback()
                log.warning(f"  migrate pr/{p}: {e}")

        # Commits
        if _exists(_tbl("commits")):
            _run(f"""
                INSERT INTO pr_commits
                    (client_id, project, commit_hash, commit_msg, summary,
                     phase, feature, bug_ref, source, session_id, prompt_source_id,
                     tags, committed_at, created_at)
                SELECT 1, '{p}', commit_hash, commit_msg, summary,
                       phase, feature, bug_ref, source, session_id, prompt_source_id,
                       tags, committed_at, created_at
                FROM {_tbl("commits")} ON CONFLICT DO NOTHING
            """)

        # Events
        if _exists(_tbl("events")):
            _run(f"""
                INSERT INTO pr_events
                    (client_id, project, event_type, source_id, title, content,
                     phase, feature, session_id, metadata, created_at)
                SELECT 1, '{p}', event_type, source_id, title, content,
                       phase, feature, session_id, metadata, created_at
                FROM {_tbl("events")} ON CONFLICT DO NOTHING
            """)

        # Embeddings
        if _exists(_tbl("embeddings")):
            _run(f"""
                INSERT INTO pr_embeddings
                    (client_id, project, source_type, source_id, chunk_index, content,
                     embedding, chunk_type, doc_type, language, file_path, metadata, created_at)
                SELECT 1, '{p}', source_type, source_id, chunk_index, content,
                       embedding, chunk_type, doc_type, language, file_path, metadata, created_at
                FROM {_tbl("embeddings")} ON CONFLICT DO NOTHING
            """)

        # Event tags (need entity_value_id remapping via event source_id join)
        if _exists(_tbl("event_tags")) and _exists(_tbl("events")):
            cur.execute(f"""
                SELECT et.event_id, et.entity_value_id, et.auto_tagged, et.created_at,
                       e.event_type, e.source_id
                FROM {_tbl("event_tags")} et
                JOIN {_tbl("events")} e ON e.id = et.event_id
            """)
            for (old_eid, old_evid, auto, ts, etype, src_id) in cur.fetchall():
                # Look up new event id in pr_events
                cur.execute(
                    "SELECT id FROM pr_events WHERE client_id=1 AND project=%s "
                    "AND event_type=%s AND source_id=%s LIMIT 1",
                    (p, etype, src_id),
                )
                new_ev = cur.fetchone()
                new_evid = ev_id_map.get(old_evid)
                if new_ev and new_evid:
                    try:
                        cur.execute(
                            """INSERT INTO pr_event_tags (event_id, entity_value_id, auto_tagged, created_at)
                               VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                            (new_ev[0], new_evid, auto, ts),
                        )
                    except Exception:
                        conn.rollback()
            conn.commit()

        # Work items (category_id remapping)
        if _exists(_tbl("work_items")):
            cur.execute(f"""
                SELECT id, project, category_name, category_id, name, description,
                       status, lifecycle_status, due_date, parent_id,
                       acceptance_criteria, implementation_plan,
                       agent_run_id, agent_status, tags, created_at, updated_at
                FROM {_tbl("work_items")}
            """)
            for row in cur.fetchall():
                (wi_id, proj, cat_name, old_cat, name, desc, status, lc, due, par,
                 ac, impl, run_id, a_status, tags, ts, upd) = row
                new_cat = cat_id_map.get(old_cat) if old_cat else None
                # agent_run_id changed from int → uuid; pass NULL to avoid type errors
                try:
                    cur.execute(
                        """INSERT INTO pr_work_items
                               (id, client_id, project, category_name, category_id,
                                name, description, status, lifecycle_status, due_date,
                                parent_id, acceptance_criteria, implementation_plan,
                                agent_status, tags, created_at, updated_at)
                           VALUES (%s,1,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT DO NOTHING""",
                        (wi_id, proj, cat_name, new_cat, name, desc, status, lc, due, par,
                         ac, impl, a_status, tags, ts, upd),
                    )
                except Exception:
                    conn.rollback()
            conn.commit()

        # Interactions (project_id → project)
        if _exists(_tbl("interactions")):
            cur.execute(f"""
                SELECT id, project_id, work_item_id, session_id, llm_source,
                       event_type, source_id, prompt, response, phase,
                       tags, metadata, created_at
                FROM {_tbl("interactions")}
            """)
            for row in cur.fetchall():
                (iid, proj_id, wi_id, sess, llm, etype, src,
                 prompt, resp, phase, tags, meta, ts) = row
                try:
                    cur.execute(
                        """INSERT INTO pr_interactions
                               (id, client_id, project, work_item_id, session_id,
                                llm_source, event_type, source_id, prompt, response,
                                phase, tags, metadata, created_at)
                           VALUES (%s,1,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT DO NOTHING""",
                        (iid, proj_id or p, wi_id, sess, llm, etype, src,
                         prompt, resp, phase, tags, meta, ts),
                    )
                except Exception:
                    conn.rollback()
            conn.commit()

        # Interaction tags — only copy rows whose interaction_id exists in pr_interactions
        if _exists(_tbl("interaction_tags")):
            _run(f"""
                INSERT INTO pr_interaction_tags
                    (interaction_id, work_item_id, auto_tagged, created_at)
                SELECT it.interaction_id, it.work_item_id, it.auto_tagged, it.created_at
                FROM {_tbl("interaction_tags")} it
                WHERE EXISTS (
                    SELECT 1 FROM pr_interactions i WHERE i.id = it.interaction_id
                )
                ON CONFLICT DO NOTHING
            """)

        # Memory items (project_id → project)
        if _exists(_tbl("memory_items")):
            _run(f"""
                INSERT INTO pr_memory_items
                    (id, client_id, project, scope, scope_ref, content,
                     source_ids, tags, reviewer_score, reviewer_critique,
                     created_at, updated_at)
                SELECT id, 1, project_id, scope, scope_ref, content,
                       source_ids, tags, reviewer_score, reviewer_critique,
                       created_at, updated_at
                FROM {_tbl("memory_items")} ON CONFLICT DO NOTHING
            """)

        # Project facts (project_id → project)
        if _exists(_tbl("project_facts")):
            _run(f"""
                INSERT INTO pr_project_facts
                    (id, client_id, project, fact_key, fact_value,
                     valid_from, valid_until, source_memory_id)
                SELECT id, 1, project_id, fact_key, fact_value,
                       valid_from, valid_until, source_memory_id
                FROM {_tbl("project_facts")} ON CONFLICT DO NOTHING
            """)

        # Backfill pr_interactions from history.jsonl if table is empty
        # (handles the case where old interactions table was empty or failed migration)
        cur.execute(
            "SELECT 1 FROM pr_interactions WHERE client_id=1 AND project=%s LIMIT 1",
            (p,),
        )
        if not cur.fetchone():
            import json as _json
            hist_file = Path(settings.workspace_dir) / p / "_system" / "history.jsonl"
            if hist_file.exists():
                for line in hist_file.read_text().splitlines():
                    if not line.strip():
                        continue
                    try:
                        e = _json.loads(line)
                    except Exception:
                        continue
                    ts = e.get("ts")
                    if not ts or not e.get("user_input"):
                        continue
                    try:
                        cur.execute(
                            """INSERT INTO pr_interactions
                                   (client_id, project, session_id, llm_source, event_type,
                                    source_id, prompt, response, phase, metadata, created_at)
                               VALUES (1,%s,%s,%s,'prompt',%s,%s,%s,%s,%s::jsonb,%s::timestamptz)
                               ON CONFLICT (client_id, project, source_id)
                               WHERE source_id IS NOT NULL DO NOTHING""",
                            (p, e.get("session_id"), e.get("provider", "claude"), ts,
                             (e.get("user_input") or "")[:4000],
                             (e.get("output") or "")[:8000],
                             e.get("phase"),
                             _json.dumps({"user": e.get("user"), "source": e.get("source"),
                                          "feature": e.get("feature")}),
                             ts),
                        )
                    except Exception:
                        conn.rollback()
                conn.commit()
                log.info(f"Backfilled pr_interactions for '{p}' from history.jsonl")

        # Graph tables: schema changed too significantly (int → uuid IDs, column renames).
        # Skip data migration — just drop the old tables below.

        # DROP per-project tables (children before parents)
        _drop_order = [
            _tbl("graph_node_results"),
            _tbl("graph_edges"),
            _tbl("graph_nodes"),
            _tbl("graph_runs"),
            _tbl("graph_workflows"),
            _tbl("interaction_tags"),
            _tbl("project_facts"),
            _tbl("memory_items"),
            _tbl("interactions"),
            _tbl("work_items"),
            _tbl("event_links"),
            _tbl("event_tags"),
            _tbl("embeddings"),
            _tbl("events"),
            _tbl("commits"),
        ]
        for tbl_name in _drop_order:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {tbl_name} CASCADE")
                conn.commit()
            except Exception:
                conn.rollback()

    # ── Legacy table renames ───────────────────────────────────────────────────

    @staticmethod
    def _rename_legacy_tables(conn) -> None:
        """One-time rename: old bare names → mng_ prefix.

        Phase 1 only (bare → mng_). Phase 2 (mng_ → cl_local_) removed —
        data migration handled by _migrate_to_flat_tables().
        """
        _RENAMES = [
            # Phase 1: bare names → mng_ prefix
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
        # Phase 3: old per-project bare names → pr_local_ convention
        _PROJECT_BASES = ["commits", "events", "embeddings", "event_tags", "event_links"]

        renamed = 0
        try:
            with conn.cursor() as cur:
                for old, new in _RENAMES:
                    try:
                        cur.execute(f"ALTER TABLE IF EXISTS {old} RENAME TO {new}")
                        conn.commit()
                        renamed += 1
                    except Exception:
                        conn.rollback()

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
                            suffix = tname[len(base) + 1:]
                            new_name = f"pr_local_{suffix}_{base}"
                            try:
                                cur.execute(f"ALTER TABLE {tname} RENAME TO {new_name}")
                                conn.commit()
                                renamed += 1
                            except Exception:
                                conn.rollback()
                    except Exception:
                        conn.rollback()

            if renamed:
                log.info(f"✅ Legacy renames: {renamed} tables → mng_/pr_ convention")
        except Exception as e:
            conn.rollback()
            log.warning(f"_rename_legacy_tables skipped: {e}")

    # ── Seeding ────────────────────────────────────────────────────────────────

    @staticmethod
    def _seed_agent_roles(conn) -> None:
        """Upsert the 10 built-in global roles (client_id=1).

        Uses DO UPDATE so improved prompts take effect on server restart.
        auto_commit=True is set on developer roles so pipeline nodes that
        link to them automatically commit+push their file changes.
        """
        # (name, description, system_prompt, provider, model, role_type, auto_commit)
        _ROLES = [
            (
                "Product Manager",
                "Produces a concise task spec with acceptance criteria.",
                "You are a senior product manager. Given a work item, produce ONLY:\n\n"
                "## Task\n<one-sentence task statement>\n\n"
                "## Description\n<2-3 sentences: goal, user value, scope>\n\n"
                "## Acceptance Criteria\n"
                "- [ ] <specific, testable criterion 1>\n"
                "- [ ] <specific, testable criterion 2>\n"
                "- [ ] <specific, testable criterion 3 (max 5 total)>\n\n"
                "Rules: under 250 words total. No preamble. No user stories unless asked.",
                "claude", "claude-haiku-4-5-20251001", "agent", False,
            ),
            (
                "Sr. Architect",
                "Produces a concise numbered implementation plan with file paths.",
                "You are a senior software architect. Given a task and acceptance criteria, "
                "produce ONLY:\n\n"
                "## Plan\n1. <concrete step>\n2. <concrete step>\n...(max 6 steps)\n\n"
                "## Files to Change\n"
                "- `path/to/file.py` — <what to add/modify>\n\n"
                "## Notes\n<2-3 sentences: key decisions, patterns to follow, risks>\n\n"
                "Rules: under 300 words. Be precise about file paths and function names. "
                "No lengthy prose.",
                "claude", "claude-sonnet-4-6", "system_designer", False,
            ),
            (
                "Web Developer",
                "Implements full-stack features; outputs complete files ready to commit.",
                "You are a senior full-stack developer. Given an implementation plan and "
                "acceptance criteria, write the actual code changes.\n\n"
                "For EACH file you create or modify, use this EXACT format:\n\n"
                "### File: path/to/file.ext\n```language\n<complete file content>\n```\n\n"
                "After all files, add:\n"
                "## Summary\n- <bullet: what changed>\n- <bullet: why>\n\n"
                "Rules:\n"
                "- Write COMPLETE file content (not partial diffs)\n"
                "- Cover both frontend and backend if needed\n"
                "- All acceptance criteria must be met\n"
                "- Add inline comments for non-obvious logic",
                "claude", "claude-sonnet-4-6", "developer", True,
            ),
            (
                "Backend Developer",
                "Writes server-side code: APIs, DB schemas, business logic; auto-commits.",
                "You are a senior backend developer. Implement server-side code.\n\n"
                "For EACH file you create or modify, use this EXACT format:\n\n"
                "### File: path/to/file.ext\n```language\n<complete file content>\n```\n\n"
                "After all files, add:\n"
                "## Summary\n- <bullet: what changed>\n- <bullet: why>\n\n"
                "Rules:\n"
                "- Write COMPLETE file content (not partial diffs)\n"
                "- REST API endpoints, DB migrations, business logic, error handling\n"
                "- Use the project's existing stack and patterns\n"
                "- Add input validation at all system boundaries",
                "deepseek", "deepseek-chat", "developer", True,
            ),
            (
                "Frontend Developer",
                "Writes client-side code: UI components, styles, interactions; auto-commits.",
                "You are a senior frontend developer. Implement client-side code.\n\n"
                "For EACH file you create or modify, use this EXACT format:\n\n"
                "### File: path/to/file.ext\n```language\n<complete file content>\n```\n\n"
                "After all files, add:\n"
                "## Summary\n- <bullet: what changed>\n- <bullet: why>\n\n"
                "Rules:\n"
                "- Write COMPLETE file content (not partial diffs)\n"
                "- Match the existing design system and naming conventions\n"
                "- Ensure accessibility (ARIA, keyboard nav) and responsiveness",
                "openai", "gpt-4o", "developer", True,
            ),
            (
                "DevOps Engineer",
                "Writes CI/CD configs, Dockerfiles, deployment infrastructure; auto-commits.",
                "You are a senior DevOps engineer. Write infrastructure-as-code.\n\n"
                "For EACH file you create or modify, use this EXACT format:\n\n"
                "### File: path/to/file.ext\n```language\n<complete file content>\n```\n\n"
                "After all files, add:\n"
                "## Summary\n- <bullet: what changed>\n- <bullet: why>\n\n"
                "Rules:\n"
                "- Dockerfiles, CI/CD (GitHub Actions/GitLab CI), deployment scripts\n"
                "- Include health checks, rollback strategy, and env var docs\n"
                "- Security: no hardcoded secrets, least-privilege IAM",
                "claude", "claude-haiku-4-5-20251001", "developer", True,
            ),
            (
                "Code Reviewer",
                "Reviews code quality; returns score + issues as JSON.",
                "You are a senior code reviewer. Review the implementation against "
                "the acceptance criteria.\n\n"
                "Return ONLY valid JSON (no markdown fences, no preamble):\n"
                '{"score": <1-10>, "passed": <true|false>, '
                '"ac_results": [{"criterion": "...", "status": "PASS|FAIL"}], '
                '"issues": ["..."], "suggestions": ["..."]}\n\n'
                "Score >= 7 means passed. Be specific and actionable.",
                "claude", "claude-sonnet-4-6", "reviewer", False,
            ),
            (
                "Security Reviewer",
                "Audits code for OWASP Top 10 vulnerabilities; returns JSON.",
                "You are a senior application security engineer. Review code for:\n"
                "injection, broken auth, sensitive data exposure, XSS, CSRF, "
                "insecure deserialization, broken access control, security misconfigs.\n\n"
                "Return ONLY valid JSON:\n"
                '{"score": <1-10>, "passed": <true|false>, '
                '"vulnerabilities": ["..."], "recommendations": ["..."]}',
                "claude", "claude-haiku-4-5-20251001", "reviewer", False,
            ),
            (
                "QA Engineer",
                "Writes comprehensive test cases including edge cases.",
                "You are a senior QA engineer. Given a feature and acceptance criteria, "
                "produce a test plan.\n\n"
                "## Test Cases\n"
                "For each test: **Name** | Preconditions | Steps | Expected Result\n\n"
                "Cover: happy path, boundary conditions, error cases, edge cases.\n"
                "Keep each test case to 3-5 lines. Max 10 test cases.",
                "openai", "gpt-4o", "agent", False,
            ),
            (
                "AWS Architect",
                "Designs AWS infrastructure using CDK/CloudFormation.",
                "You are a senior AWS solutions architect. Design AWS infrastructure.\n\n"
                "For EACH infrastructure file, use this EXACT format:\n\n"
                "### File: path/to/file.ts\n```typescript\n<complete CDK/CFN content>\n```\n\n"
                "After all files, add:\n"
                "## Summary\n- <resource created/modified>\n- <key decision>\n\n"
                "Include: compute, storage, networking, IAM (least-privilege), "
                "auto-scaling, cost notes.",
                "claude", "claude-sonnet-4-6", "developer", True,
            ),
        ]
        _INTERNAL_FACT_PROMPT = (
            "You are a precise technical fact extractor. Your job is to identify DURABLE "
            "architectural facts from software development notes.\n\n"
            "EXTRACTION RULES:\n"
            "1. Only extract facts that will STILL BE TRUE in 3+ months\n"
            "2. Only extract facts that CONSTRAIN future development decisions\n"
            "3. Be SPECIFIC — 'pgvector cosine similarity, no ChromaDB' not 'uses a vector db'\n"
            "4. Only include facts where confidence >= 0.7\n\n"
            "INCLUDE: tech stack choices, architectural patterns, auth methods, DB schema "
            "conventions, naming rules, API style, deployment targets, SDK choices.\n\n"
            "EXCLUDE (these pollute facts and go stale fast): bugs fixed, one-off decisions, "
            "user preferences, tasks/TODOs, events that happened, temporary workarounds.\n\n"
            "OUTPUT: Valid JSON array ONLY. No preamble, no markdown fences, no explanation.\n\n"
            'Format: [{"key": "snake_case_id", "value": "specific concrete value", "confidence": 0.0-1.0}]\n\n'
            "Good examples:\n"
            '[{"key":"auth_method","value":"JWT via python-jose + bcrypt, no passlib","confidence":0.95},\n'
            ' {"key":"vector_db","value":"pgvector cosine similarity, replaced ChromaDB","confidence":0.92},\n'
            ' {"key":"frontend_pattern","value":"Vanilla JS ES modules, no framework, no bundler","confidence":0.98},\n'
            ' {"key":"table_naming","value":"mng_ global, pr_ per-project, 25 fixed tables total","confidence":0.99}]\n\n'
            "Bad extractions — DO NOT produce:\n"
            '- {"key":"fixed_bug","value":"fixed login redirect"} — event\n'
            '- {"key":"todo","value":"add dark mode"} — task\n'
            '- {"key":"tech","value":"Python"} — too vague\n'
            '- {"key":"auth","value":"JWT"} — missing specifics'
        )

        try:
            with conn.cursor() as cur:
                for name, desc, prompt, provider, model, role_type, auto_commit in _ROLES:
                    cur.execute(
                        """INSERT INTO mng_agent_roles
                               (client_id, project, name, description, system_prompt,
                                provider, model, role_type, auto_commit)
                           VALUES (1, '_global', %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (client_id, project, name) DO UPDATE SET
                               description   = EXCLUDED.description,
                               system_prompt = EXCLUDED.system_prompt,
                               provider      = EXCLUDED.provider,
                               model         = EXCLUDED.model,
                               role_type     = EXCLUDED.role_type,
                               auto_commit   = EXCLUDED.auto_commit""",
                        (name, desc, prompt, provider, model, role_type, auto_commit),
                    )
                # Seed the internal fact-extraction prompt (role_type='internal')
                cur.execute(
                    """INSERT INTO mng_agent_roles
                           (client_id, project, name, description, system_prompt,
                            provider, model, role_type)
                       VALUES (1, '_global',
                               'internal_project_fact',
                               'Internal: extracts durable architectural facts from memory summaries. '
                               'Used automatically by /memory, session-end, and workflow-end triggers.',
                               %s, 'claude', 'claude-haiku-4-5-20251001', 'internal')
                       ON CONFLICT (client_id, project, name) DO UPDATE SET
                           system_prompt = EXCLUDED.system_prompt""",
                    (_INTERNAL_FACT_PROMPT,),
                )
            conn.commit()
            log.debug("✅ Agent roles seeded")
        except Exception as e:
            conn.rollback()
            log.warning(f"Agent roles seed skipped: {e}")

    @staticmethod
    def _seed_system_roles(conn) -> None:
        """Upsert 7 built-in system roles (client_id=1).

        Uses DO UPDATE so improved content takes effect on server restart.
        """
        _DEFAULT_SYSTEM_ROLES = [
            (
                "coding_standards",
                "quality",
                "Clean code conventions, OOP, type hints, docstrings, DRY/SOLID principles.",
                "## Coding Standards\n\n"
                "- Follow clean code principles: meaningful names, small focused functions, "
                "no magic numbers\n"
                "- Apply OOP where appropriate: encapsulation, inheritance, polymorphism\n"
                "- Add type hints to all functions and methods\n"
                "- Write docstrings for all public classes and functions\n"
                "- Apply DRY (Don't Repeat Yourself) and SOLID principles\n"
                "- Keep functions under 30 lines; break complex logic into helpers\n"
                "- Prefer composition over inheritance\n"
                "- Use descriptive variable names that reveal intent",
            ),
            (
                "output_format",
                "output",
                "Save all outputs to output/[feature]_YYMMDD_HHMMSS.md.",
                "## Output Format\n\n"
                "- Save all generated outputs to a file named: "
                "`output/[feature]_YYMMDD_HHMMSS.md` where YYMMDD_HHMMSS is the current "
                "timestamp\n"
                "- Use clear Markdown headings (##, ###) to structure the output\n"
                "- Include a brief summary at the top\n"
                "- List all files created or modified with their full paths\n"
                "- End with a 'Next Steps' section if applicable",
            ),
            (
                "security_principles",
                "security",
                "OWASP Top 10, parameterised SQL, no hardcoded secrets.",
                "## Security Principles\n\n"
                "- Guard against OWASP Top 10: injection, broken auth, XSS, CSRF, "
                "insecure direct object references, security misconfiguration, "
                "sensitive data exposure, XXE, broken access control, "
                "using components with known vulnerabilities\n"
                "- Always use parameterised queries — never string-interpolate SQL\n"
                "- Never hardcode secrets, API keys, or passwords in code\n"
                "- Use environment variables or a secrets manager for all credentials\n"
                "- Validate and sanitize all user inputs at system boundaries\n"
                "- Apply principle of least privilege to all access controls\n"
                "- Use HTTPS everywhere; set secure, httpOnly, sameSite cookie flags",
            ),
            (
                "reviewer_standards",
                "review",
                "Verify all ACs, list tested items, score 1-10, return JSON.",
                "## Reviewer Standards\n\n"
                "- Verify every acceptance criterion is met — list each with PASS/FAIL\n"
                "- Check for edge cases, error handling, and boundary conditions\n"
                "- Assess code quality: readability, maintainability, test coverage\n"
                "- Provide a score from 1–10 (>= 7 means passed)\n"
                "- Return ONLY valid JSON in this exact format:\n"
                '{"score": <1-10>, "passed": <true|false>, '
                '"ac_results": [{"criterion": "...", "status": "PASS|FAIL", "note": "..."}], '
                '"issues": ["..."], "suggestions": ["..."]}',
            ),
            (
                "doc_output_format",
                "output",
                "Keep docs short, use bullets, include Task/Description/AC or Plan headings.",
                "## Document Output Rules\n\n"
                "- Keep the total output under 300 words\n"
                "- Use bullet points instead of paragraphs wherever possible\n"
                "- Use standard section headings: ## Task, ## Description, "
                "## Acceptance Criteria, ## Plan, ## Files to Change, ## Notes\n"
                "- Each acceptance criterion or plan step must be a single concise line\n"
                "- No preamble, no 'Sure, here is...', no repeating the prompt back\n"
                "- No filler phrases: skip 'it is important to', 'please note that', etc.",
            ),
            (
                "dev_code_format",
                "development",
                "Output complete files using ### File: path\\n```lang blocks; add Summary.",
                "## Developer Output Format\n\n"
                "For EACH file you create or modify, use this EXACT format:\n\n"
                "### File: path/to/file.ext\n```language\n<complete file content>\n```\n\n"
                "Rules:\n"
                "- Always write COMPLETE file content, not partial snippets or diffs\n"
                "- Include all imports, all existing functions — not just the changed part\n"
                "- After all files, add a ## Summary section with bullet points:\n"
                "  - What was changed and in which file\n"
                "  - Why the change was needed\n"
                "  - Any migration steps or env vars required\n"
                "- If no files were modified, explain why in plain text",
            ),
            (
                "dev_naming_conventions",
                "development",
                "mng_ global tables, pr_ project tables, snake_case, no abbreviations.",
                "## Naming Conventions\n\n"
                "Database tables:\n"
                "- Global / client-scoped tables: prefix `mng_` (e.g. mng_users, mng_agent_roles)\n"
                "- Project-scoped tables: prefix `pr_` (e.g. pr_commits, pr_graph_runs)\n"
                "- Never create new tables outside these two namespaces\n"
                "- Always include `client_id INT` FK on every table\n"
                "- Project-scoped tables also have a `project VARCHAR(100)` column\n\n"
                "Python:\n"
                "- snake_case for variables, functions, modules\n"
                "- PascalCase for classes\n"
                "- ALL_CAPS for module-level constants\n"
                "- No abbreviations: use `connection` not `conn`, `error` not `err`\n\n"
                "JavaScript:\n"
                "- camelCase for variables and functions\n"
                "- PascalCase for classes and components\n"
                "- UPPER_SNAKE_CASE for constants",
            ),
        ]
        try:
            with conn.cursor() as cur:
                for name, category, description, content in _DEFAULT_SYSTEM_ROLES:
                    cur.execute(
                        """INSERT INTO mng_system_roles
                               (client_id, name, category, description, content)
                           VALUES (1, %s, %s, %s, %s)
                           ON CONFLICT (client_id, name) DO UPDATE SET
                               category    = EXCLUDED.category,
                               description = EXCLUDED.description,
                               content     = EXCLUDED.content""",
                        (name, category, description, content),
                    )
            conn.commit()
            log.debug("✅ System roles seeded")
        except Exception as e:
            conn.rollback()
            log.warning(f"System roles seed skipped: {e}")

    @staticmethod
    def _seed_role_system_links(conn) -> None:
        """Link agent roles to system roles. Idempotent — uses ON CONFLICT DO NOTHING."""
        # (agent_role_name, system_role_name, order_index)
        _LINKS = [
            # Document-producing roles → doc output format
            ("Product Manager",      "doc_output_format",      0),
            ("Sr. Architect",        "doc_output_format",      0),
            ("QA Engineer",          "doc_output_format",      0),
            # Developer roles → code format + naming conventions + coding standards
            ("Web Developer",        "dev_code_format",        0),
            ("Web Developer",        "dev_naming_conventions", 1),
            ("Web Developer",        "coding_standards",       2),
            ("Backend Developer",    "dev_code_format",        0),
            ("Backend Developer",    "dev_naming_conventions", 1),
            ("Backend Developer",    "coding_standards",       2),
            ("Backend Developer",    "security_principles",    3),
            ("Frontend Developer",   "dev_code_format",        0),
            ("Frontend Developer",   "dev_naming_conventions", 1),
            ("Frontend Developer",   "coding_standards",       2),
            ("DevOps Engineer",      "dev_code_format",        0),
            ("DevOps Engineer",      "security_principles",    1),
            ("AWS Architect",        "dev_code_format",        0),
            ("AWS Architect",        "coding_standards",       1),
            ("AWS Architect",        "security_principles",    2),
            # Reviewer roles → reviewer standards + security
            ("Code Reviewer",        "reviewer_standards",     0),
            ("Code Reviewer",        "coding_standards",       1),
            ("Security Reviewer",    "reviewer_standards",     0),
            ("Security Reviewer",    "security_principles",    1),
        ]
        try:
            with conn.cursor() as cur:
                for agent_name, system_name, order_idx in _LINKS:
                    cur.execute(
                        """INSERT INTO mng_role_system_links
                               (role_id, system_role_id, order_index)
                           SELECT ar.id, sr.id, %s
                           FROM   mng_agent_roles  ar
                           JOIN   mng_system_roles sr ON sr.name = %s AND sr.client_id = 1
                           WHERE  ar.name = %s AND ar.client_id = 1
                           ON CONFLICT DO NOTHING""",
                        (order_idx, system_name, agent_name),
                    )
            conn.commit()
            log.debug("✅ Role-system links seeded")
        except Exception as e:
            conn.rollback()
            log.warning(f"Role-system links seed skipped: {e}")

    @staticmethod
    def _seed_client_defaults(client_id: int, conn) -> None:
        """Seed default entity categories for a new client. Idempotent."""
        _CATS = [
            ("_global", "feature", "#3b82f6", "★"),
            ("_global", "bug",     "#ef4444", "🐛"),
            ("_global", "task",    "#8b5cf6", "✓"),
            ("_global", "doc",     "#10b981", "📄"),
        ]
        try:
            with conn.cursor() as cur:
                for proj, name, color, icon in _CATS:
                    cur.execute(
                        """INSERT INTO mng_entity_categories (client_id, project, name, color, icon)
                           VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                        (client_id, proj, name, color, icon),
                    )
            conn.commit()
        except Exception as e:
            conn.rollback()
            log.warning(f"_seed_client_defaults({client_id}) failed: {e}")


# Singleton used everywhere
db = _Database()


# ─── Dynamic query helpers ────────────────────────────────────────────────────

def build_update(fields: dict) -> tuple[str, list]:
    """Build a SET clause for UPDATE from a dict, skipping None values.

    Returns (set_clause, values) — append your WHERE values after.

    Usage::
        set_clause, vals = build_update({"name": body.name, "color": body.color})
        cur.execute(
            f"UPDATE mng_entity_categories SET {set_clause}, updated_at=NOW() WHERE id=%s",
            vals + [row_id],
        )
    """
    items = [(k, v) for k, v in fields.items() if v is not None]
    if not items:
        raise ValueError("build_update: no non-None fields provided")
    clause = ", ".join(f"{k} = %s" for k, _ in items)
    return clause, [v for _, v in items]


def build_where(*conditions: tuple[str, any] | None) -> tuple[str, list]:
    """Build a WHERE clause from (snippet, value) pairs, skipping None entries.

    Returns ('WHERE cond1 AND cond2 ...', [val1, val2, ...]).
    Pass ``None`` for optional conditions to skip them cleanly.

    Usage::
        where, params = build_where(
            ("client_id = %s", 1),
            ("project = %s", project),
            ("status = %s", status) if status else None,
        )
        cur.execute(f"SELECT * FROM pr_work_items {where} ORDER BY created_at", params)
    """
    active = [c for c in conditions if c is not None]
    if not active:
        return "", []
    clause = "WHERE " + " AND ".join(snippet for snippet, _ in active)
    params = [val for _, val in active]
    return clause, params
