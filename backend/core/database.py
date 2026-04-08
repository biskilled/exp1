"""
PostgreSQL connection pool — three-layer memory architecture.

Table namespaces:
  mng_         — global + client-scoped (management tables)
  planner_     — project tag hierarchy (planner_tags)
  mem_mrr_     — mirroring layer (raw source data: prompts, commits, items, messages)
  mem_ai_      — AI/embedding layer (mem_ai_events, mem_ai_work_items, mem_ai_project_facts)
    pr_          — project-scoped misc (graph_*, seq_counters)

Falls back gracefully when DATABASE_URL is not set — callers check `is_available()`.

Usage:
    from core.database import db

    cid = db.default_client_id()
    if db.is_available():
        with db.conn() as conn:
            with conn.cursor() as cur:
                project_id = db.get_project_id(project)
                cur.execute(
                    "SELECT * FROM mem_mrr_commits WHERE project_id=%s",
                    (project_id,)
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


# ─── Project ID cache ────────────────────────────────────────────────────────
_PROJECT_ID_CACHE: dict[tuple[int, str], int] = {}


def _workspace() -> Path:
    """Return absolute Path to the workspace/ directory."""
    from core.config import settings
    return Path(settings.workspace_dir)


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
INSERT INTO mng_clients (id, slug, name, plan) VALUES (1, 'local', 'Local Install', 'free')
    ON CONFLICT (slug) DO NOTHING;
"""

# ─── DDL: mng_users / usage_logs / transactions ──────────────────────────────

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
-- mng_projects: one row per project (replaces project TEXT partition key everywhere)
CREATE TABLE IF NOT EXISTS mng_projects (
    id                  SERIAL         PRIMARY KEY,
    client_id           INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    name                VARCHAR(255)   NOT NULL,
    description         TEXT           NOT NULL DEFAULT '',
    workspace_path      TEXT,
    code_dir            TEXT,
    default_provider    VARCHAR(50)    NOT NULL DEFAULT 'claude',
    git_branch          VARCHAR(100)   DEFAULT 'main',
    git_username        TEXT,
    git_email           TEXT,
    github_repo         TEXT,
    github_client_id    TEXT,
    auto_commit_push    BOOLEAN        NOT NULL DEFAULT FALSE,
    claude_cli_support  BOOLEAN        NOT NULL DEFAULT FALSE,
    cursor_support      BOOLEAN        NOT NULL DEFAULT FALSE,
    enabled_providers   JSONB          NOT NULL DEFAULT '[]',
    active_workflows    JSONB          NOT NULL DEFAULT '[]',
    extra               JSONB          NOT NULL DEFAULT '{}',
    is_active           BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE(client_id, name)
);
INSERT INTO mng_projects (client_id, name, description)
VALUES (1, '_global', 'Global scope — agent roles and shared templates')
ON CONFLICT (client_id, name) DO NOTHING;
CREATE INDEX IF NOT EXISTS idx_mng_projects_client ON mng_projects(client_id);

-- mng_user_projects: user ↔ project membership with role
CREATE TABLE IF NOT EXISTS mng_user_projects (
    user_id     VARCHAR(36)  NOT NULL REFERENCES mng_users(id) ON DELETE CASCADE,
    project_id  INT          NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    role        VARCHAR(20)  NOT NULL DEFAULT 'member',
    joined_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, project_id)
);
CREATE INDEX IF NOT EXISTS idx_mng_user_projects_proj ON mng_user_projects(project_id);

-- Session tags per project (fresh install: project_id; migration handles existing)
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

-- Agent roles per project (fresh install: project_id; migration handles existing)
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
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS inputs        JSONB        DEFAULT '[]';
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS outputs       JSONB        DEFAULT '[]';
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS role_type     VARCHAR(50)  NOT NULL DEFAULT 'agent';
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS output_schema JSONB        DEFAULT NULL;
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS auto_commit     BOOLEAN      NOT NULL DEFAULT FALSE;
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS tools           JSONB        DEFAULT '[]';
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS react           BOOLEAN      NOT NULL DEFAULT TRUE;
ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS max_iterations  INT          NOT NULL DEFAULT 10;

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
ALTER TABLE mng_agent_role_versions ADD COLUMN IF NOT EXISTS tools JSONB DEFAULT '[]';
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

-- ── Migration: mng_session_tags project TEXT → project_id INT FK ─────────────
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='mng_session_tags' AND column_name='project'
  ) THEN
    INSERT INTO mng_projects(client_id, name)
    SELECT DISTINCT client_id, project FROM mng_session_tags
    ON CONFLICT (client_id, name) DO NOTHING;
    ALTER TABLE mng_session_tags ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE mng_session_tags t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE mng_session_tags ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE mng_session_tags ADD CONSTRAINT fk_mst_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id);
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_mst_cp;
    BEGIN
      ALTER TABLE mng_session_tags DROP CONSTRAINT IF EXISTS mng_session_tags_client_id_project_key;
    EXCEPTION WHEN undefined_object THEN NULL; END;
    ALTER TABLE mng_session_tags DROP COLUMN IF EXISTS project;
    BEGIN
      ALTER TABLE mng_session_tags ADD CONSTRAINT mng_session_tags_project_id_key UNIQUE(project_id);
    EXCEPTION WHEN duplicate_object THEN NULL; END;
  END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_mst_pid ON mng_session_tags(project_id);

-- ── Migration: mng_agent_roles project TEXT → project_id INT FK ─────────────
DO $$ BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema='public' AND table_name='mng_agent_roles' AND column_name='project'
  ) THEN
    INSERT INTO mng_projects(client_id, name)
    SELECT DISTINCT client_id, project FROM mng_agent_roles
    ON CONFLICT (client_id, name) DO NOTHING;
    ALTER TABLE mng_agent_roles ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE mng_agent_roles t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE mng_agent_roles ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE mng_agent_roles ADD CONSTRAINT fk_mar_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id);
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_mar_cid_proj_name;
    DROP INDEX IF EXISTS idx_mar_cp;
    ALTER TABLE mng_agent_roles DROP COLUMN IF EXISTS project;
  END IF;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS idx_mar_pid_name ON mng_agent_roles(project_id, name);
CREATE INDEX IF NOT EXISTS idx_mar_pid ON mng_agent_roles(project_id);
"""

# ─── DDL: pr_* flat project tables (15) ──────────────────────────────────────

_DDL_PR_TABLES = """
-- pgvector extension (needed for embedding columns)
CREATE EXTENSION IF NOT EXISTS vector;

-- Mirroring: prompts (raw prompt/response log)
CREATE TABLE IF NOT EXISTS mem_mrr_prompts (
    id           UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id    INT           NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id   INT           NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    session_id   TEXT,
    source_id    TEXT,
    prompt       TEXT          NOT NULL DEFAULT '',
    response     TEXT          NOT NULL DEFAULT '',
    tags         JSONB         NOT NULL DEFAULT '{}',
    created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS        idx_mmrr_p_pid     ON mem_mrr_prompts(project_id);
CREATE INDEX IF NOT EXISTS        idx_mmrr_p_session ON mem_mrr_prompts(session_id) WHERE session_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_mmrr_p_source  ON mem_mrr_prompts(project_id, source_id) WHERE source_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS        idx_mmrr_p_created ON mem_mrr_prompts(created_at DESC);
CREATE INDEX IF NOT EXISTS        idx_mmrr_p_tags    ON mem_mrr_prompts USING gin(tags);

-- Mirroring: commits — commit_hash is the natural primary key (git hash)
CREATE TABLE IF NOT EXISTS mem_mrr_commits (
    commit_hash        VARCHAR(64)    PRIMARY KEY,
    commit_short_hash  VARCHAR(8)     GENERATED ALWAYS AS (LEFT(commit_hash,8)) STORED,
    client_id          INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id         INT            NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    commit_msg         TEXT           NOT NULL DEFAULT '',
    author             TEXT           NOT NULL DEFAULT '',
    author_email       TEXT           NOT NULL DEFAULT '',
    summary            TEXT           NOT NULL DEFAULT '',
    diff_summary       TEXT           NOT NULL DEFAULT '',
    llm                TEXT,
    exec_llm           BOOLEAN        NOT NULL DEFAULT FALSE,
    session_id         VARCHAR(255),
    prompt_id          UUID           REFERENCES mem_mrr_prompts(id) ON DELETE SET NULL,
    tags               JSONB          NOT NULL DEFAULT '{}',
    tags_ai            JSONB          NOT NULL DEFAULT '{}',
    committed_at       TIMESTAMPTZ,
    created_at         TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_mmrr_c_pid      ON mem_mrr_commits(project_id);
CREATE INDEX IF NOT EXISTS idx_mmrr_c_comm     ON mem_mrr_commits(committed_at DESC);
CREATE INDEX IF NOT EXISTS idx_mmrr_c_session  ON mem_mrr_commits(session_id) WHERE session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mmrr_c_prompt   ON mem_mrr_commits(prompt_id) WHERE prompt_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mmrr_c_tags     ON mem_mrr_commits USING gin(tags);

-- Work items (AI-detected tasks linked to planner tags)
-- status_user = user-managed lifecycle; status_ai = AI-suggested based on action_item progress
CREATE TABLE IF NOT EXISTS mem_ai_work_items (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id          INT          NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    ai_category         TEXT         NOT NULL,
    ai_name             TEXT         NOT NULL,
    ai_desc             TEXT         NOT NULL DEFAULT '',
    requirements        TEXT         NOT NULL DEFAULT '',
    acceptance_criteria TEXT         NOT NULL DEFAULT '',
    action_items        TEXT         NOT NULL DEFAULT '',
    code_summary        TEXT         NOT NULL DEFAULT '',
    summary             TEXT         NOT NULL DEFAULT '',
    tags                JSONB        NOT NULL DEFAULT '{}',
    ai_tag_id           UUID         REFERENCES planner_tags(id),
    tag_id              UUID         REFERENCES planner_tags(id),
    merged_into         UUID         REFERENCES mem_ai_work_items(id) ON DELETE SET NULL,
    status_user         VARCHAR(20)  NOT NULL DEFAULT 'active',
    status_ai           VARCHAR(20)  NOT NULL DEFAULT 'active',
    seq_num             INT,
    source_event_id     UUID,
    start_date          TIMESTAMPTZ,
    ai_tags             JSONB        NOT NULL DEFAULT '{}',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    embedding           VECTOR(1536),
    UNIQUE(project_id, ai_category, ai_name)
);
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_pid   ON mem_ai_work_items(project_id);
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_cat   ON mem_ai_work_items(ai_category);
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_suser ON mem_ai_work_items(status_user);
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_sai   ON mem_ai_work_items(status_ai);

-- Project facts (durable extracted facts; valid_until NULL = current)
CREATE TABLE IF NOT EXISTS mem_ai_project_facts (
    id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id        INT           NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id       INT           NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    fact_key         TEXT          NOT NULL,
    fact_value       TEXT          NOT NULL,
    category         TEXT          DEFAULT NULL,
    valid_from       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    valid_until      TIMESTAMPTZ,
    source_memory_id UUID,
    conflict_status  TEXT          DEFAULT NULL,
    embedding        VECTOR(1536)
);
CREATE INDEX IF NOT EXISTS        idx_mem_ai_pf_pid     ON mem_ai_project_facts(project_id) WHERE valid_until IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_mem_ai_pf_current ON mem_ai_project_facts(project_id, fact_key) WHERE valid_until IS NULL;

-- Graph workflow definitions
CREATE TABLE IF NOT EXISTS pr_graph_workflows (
    id             UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id      INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id     INT            NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    name           VARCHAR(255)   NOT NULL,
    description    TEXT           NOT NULL DEFAULT '',
    max_iterations INTEGER        NOT NULL DEFAULT 3,
    log_directory  TEXT           NOT NULL DEFAULT '',
    created_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    UNIQUE(project_id, name)
);
CREATE INDEX IF NOT EXISTS idx_pr_gw_pid ON pr_graph_workflows(project_id);

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
    inputs           JSONB          DEFAULT '[]',
    outputs          JSONB          DEFAULT '[]',
    stateless        BOOLEAN        DEFAULT FALSE,
    retry_config     JSONB          DEFAULT '{}',
    success_criteria TEXT           DEFAULT '',
    order_index      INT            NOT NULL DEFAULT 0,
    max_retry        INT            NOT NULL DEFAULT 3,
    continue_on_fail BOOLEAN        NOT NULL DEFAULT FALSE,
    auto_commit      BOOLEAN        NOT NULL DEFAULT FALSE,
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
    current_node   TEXT           DEFAULT NULL
);
CREATE INDEX IF NOT EXISTS idx_pr_gr_pid      ON pr_graph_runs(project_id);
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
    project_id INT          NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    category   VARCHAR(100) NOT NULL,
    next_val   INT          NOT NULL DEFAULT 10000,
    PRIMARY KEY (project_id, category)
);
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS seq_num INT;
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_seq ON mem_ai_work_items(project_id, seq_num) WHERE seq_num IS NOT NULL;

"""


# ─── DDL: work_items column additions (migration 017) ────────────────────────

_DDL_WORK_ITEMS_ALTERS = """
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS ai_tags JSONB NOT NULL DEFAULT '{}';
"""

# ─── DDL: mem_mrr_commits_code — per-symbol code stats for each commit ────────

_DDL_COMMIT_CODE = """
CREATE TABLE IF NOT EXISTS mem_mrr_commits_code (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id       INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id      INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    commit_hash     VARCHAR(64) NOT NULL REFERENCES mem_mrr_commits(commit_hash) ON DELETE CASCADE,
    file_path       TEXT        NOT NULL,
    file_ext        TEXT        NOT NULL DEFAULT '',
    file_language   TEXT        NOT NULL DEFAULT '',
    file_change     TEXT        NOT NULL CHECK (file_change IN ('added','modified','deleted','renamed')),
    symbol_type     TEXT        NOT NULL CHECK (symbol_type IN ('class','method','function','import')),
    class_name      TEXT,
    method_name     TEXT,
    full_symbol     TEXT GENERATED ALWAYS AS (
                        CASE WHEN class_name IS NOT NULL AND method_name IS NOT NULL
                                 THEN class_name || '.' || method_name
                             WHEN class_name IS NOT NULL THEN class_name
                             ELSE method_name END
                    ) STORED,
    symbol_change   TEXT        NOT NULL CHECK (symbol_change IN ('added','modified','deleted')),
    rows_added      INT         NOT NULL DEFAULT 0,
    rows_removed    INT         NOT NULL DEFAULT 0,
    diff_snippet    TEXT,
    llm_summary     TEXT,
    embedding       VECTOR(1536),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_mmc_code_unique
    ON mem_mrr_commits_code (commit_hash, file_path, symbol_type,
                              COALESCE(class_name,''), COALESCE(method_name,''));
CREATE INDEX IF NOT EXISTS idx_mmc_code_pid    ON mem_mrr_commits_code(project_id);
CREATE INDEX IF NOT EXISTS idx_mmc_code_hash   ON mem_mrr_commits_code(commit_hash);
CREATE INDEX IF NOT EXISTS idx_mmc_code_sym    ON mem_mrr_commits_code(full_symbol) WHERE full_symbol IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_mmc_code_embed  ON mem_mrr_commits_code USING ivfflat(embedding vector_cosine_ops) WHERE embedding IS NOT NULL;
"""


# ─── DDL: Memory Infrastructure — three-layer architecture ───────────────────

_DDL_MEMORY_INFRA = """
-- Global tag categories shared across all projects
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

-- ── Planner tag hierarchy ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS planner_tags (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id           INT         NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id          INT         NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    name                TEXT        NOT NULL,
    category_id         INT         REFERENCES mng_tags_categories(id),
    parent_id           UUID        REFERENCES planner_tags(id),
    merged_into         UUID        REFERENCES planner_tags(id),
    seq_num             INT,
    source              TEXT        NOT NULL DEFAULT 'user',
    creator             TEXT,
    short_desc          TEXT,
    full_desc           TEXT,
    requirements        TEXT,
    acceptance_criteria TEXT,
    status              TEXT        NOT NULL DEFAULT 'open',
    priority            SMALLINT    NOT NULL DEFAULT 3,
    due_date            DATE,
    requester           TEXT,
    extra               JSONB       NOT NULL DEFAULT '{}',
    summary             TEXT,
    action_items        TEXT,
    design              JSONB,
    code_summary        JSONB,
    is_reusable         BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    embedding           VECTOR(1536),
    UNIQUE(project_id, name, category_id)
);
CREATE INDEX IF NOT EXISTS idx_planner_tags_pid    ON planner_tags(project_id);
CREATE INDEX IF NOT EXISTS idx_planner_tags_parent ON planner_tags(parent_id);
CREATE INDEX IF NOT EXISTS idx_planner_tags_cat    ON planner_tags(category_id);

-- ── Mirroring: items (requirements, decisions, meetings) ─────────────────────
CREATE TABLE IF NOT EXISTS mem_mrr_items (
    id          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id   INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id  INT          NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    item_type   TEXT         NOT NULL,
    title       TEXT,
    meeting_at  TIMESTAMPTZ,
    attendees   TEXT[],
    raw_text    TEXT         NOT NULL,
    summary     TEXT,
    tags        JSONB        NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_mmrr_items_pid  ON mem_mrr_items(project_id);
CREATE INDEX IF NOT EXISTS idx_mmrr_items_type ON mem_mrr_items(item_type);
CREATE INDEX IF NOT EXISTS idx_mmrr_i_tags     ON mem_mrr_items USING gin(tags);

-- ── Mirroring: messages (Slack, Teams, Discord) ──────────────────────────────
CREATE TABLE IF NOT EXISTS mem_mrr_messages (
    id         UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id  INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id INT          NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    platform   TEXT         NOT NULL,
    channel    TEXT,
    thread_ref TEXT,
    messages   JSONB        NOT NULL,
    date_range TSTZRANGE,
    tags       JSONB        NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_mmrr_messages_pid ON mem_mrr_messages(project_id);
CREATE INDEX IF NOT EXISTS idx_mmrr_m_tags       ON mem_mrr_messages USING gin(tags);

-- ── Embedding / AI events table ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS mem_ai_events (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id    INT          NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
    project_id   INT          NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
    event_type   TEXT         NOT NULL,
    source_id    TEXT         NOT NULL,
    session_id   TEXT,
    chunk        INT          NOT NULL DEFAULT 0,
    chunk_type   TEXT         NOT NULL DEFAULT 'full',
    content      TEXT         NOT NULL,
    summary      TEXT,
    action_items TEXT         NOT NULL DEFAULT '',
    tags         JSONB        NOT NULL DEFAULT '{}',
    importance   SMALLINT     NOT NULL DEFAULT 1,
    processed_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    embedding    VECTOR(1536),
    UNIQUE(project_id, event_type, source_id, chunk)
);
CREATE INDEX IF NOT EXISTS idx_mem_ai_events_pid     ON mem_ai_events(project_id);
CREATE INDEX IF NOT EXISTS idx_mem_ai_events_session ON mem_ai_events(session_id);
CREATE INDEX IF NOT EXISTS idx_mem_ai_events_type    ON mem_ai_events(event_type);
CREATE INDEX IF NOT EXISTS idx_mem_ai_events_pending ON mem_ai_events(processed_at) WHERE processed_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_mem_ai_events_tags    ON mem_ai_events USING gin(tags);

"""

# ─── Column additions to existing tables (memory infra) ──────────────────────

_DDL_MEMORY_INFRA_ALTERS = """
-- mem_ai_events: drop legacy columns no longer in schema
ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS summary_max_resolution_hrs;
ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS summary_cnt_msg;
ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS summary_desc;
ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS summary_tags;
ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS session_desc;
ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS cnt_prompts;
-- mem_mrr_prompts: drop denormalized/redundant columns
ALTER TABLE mem_mrr_prompts DROP COLUMN IF EXISTS event_type;
ALTER TABLE mem_mrr_prompts DROP COLUMN IF EXISTS session_src_id;
ALTER TABLE mem_mrr_prompts DROP COLUMN IF EXISTS session_src_desc;
-- mem_mrr_commits: drop legacy columns
ALTER TABLE mem_mrr_commits DROP COLUMN IF EXISTS prompt_source_id;
-- mem_ai_work_items: add embedding (not in original schema; tag_id added by migration 011)
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);
-- mem_ai_project_facts: add embedding, drop unused columns
ALTER TABLE mem_ai_project_facts ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);
ALTER TABLE mem_ai_project_facts DROP COLUMN IF EXISTS conflict_with;
-- planner_tags: add all new columns (idempotent)
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS source              TEXT     NOT NULL DEFAULT 'user';
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS creator             TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS short_desc          TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS full_desc           TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS requirements        TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS acceptance_criteria TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS status_new          TEXT     NOT NULL DEFAULT 'open';
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS priority            SMALLINT NOT NULL DEFAULT 3;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS due_date            DATE;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS requester           TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS extra               JSONB    NOT NULL DEFAULT '{}';
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS summary             TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS action_items        TEXT;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS design              JSONB;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS code_summary        JSONB;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS is_reusable         BOOLEAN  NOT NULL DEFAULT FALSE;
ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS embedding           VECTOR(1536);
-- planner_tags: clean up old status/lifecycle columns (idempotent)
DO $$ BEGIN
    -- Drop status_new if status (TEXT) already exists — rename not needed
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'planner_tags' AND column_name = 'status'
        AND data_type = 'text'
    ) THEN
        ALTER TABLE planner_tags DROP COLUMN IF EXISTS status_new;
    END IF;
    -- Rename status_new → status only when status doesn't exist yet
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'planner_tags' AND column_name = 'status'
    ) AND EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'planner_tags' AND column_name = 'status_new'
    ) THEN
        ALTER TABLE planner_tags RENAME COLUMN status_new TO status;
    END IF;
END $$;
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'planner_tags' AND column_name = 'lifecycle'
    ) THEN
        ALTER TABLE planner_tags DROP COLUMN IF EXISTS lifecycle;
    END IF;
END $$;
-- planner_tags: update unique constraint to include category_id
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name   = 'planner_tags'
          AND constraint_name = 'planner_tags_client_id_project_name_key'
    ) THEN
        ALTER TABLE planner_tags DROP CONSTRAINT planner_tags_client_id_project_name_key;
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_schema = 'public'
          AND table_name   = 'planner_tags'
          AND constraint_name = 'planner_tags_project_name_cat_key'
    ) THEN
        ALTER TABLE planner_tags ADD CONSTRAINT planner_tags_project_name_cat_key
            UNIQUE(client_id, project, name, category_id);
    END IF;
END $$;
-- ── 001_consolidation: drop old junction/meta tables ────────────────────────
-- Data was migrated in previous runs; DROP IF EXISTS is idempotent and fast.
-- Note: pr_feature_snapshots was the old name for mem_ai_features
--       mng_ai_tags_relations was the old name for mem_ai_tags_relations
DROP TABLE IF EXISTS planner_tags_meta      CASCADE;
DROP TABLE IF EXISTS mem_ai_features        CASCADE;
DROP TABLE IF EXISTS pr_feature_snapshots   CASCADE;
DROP TABLE IF EXISTS mem_ai_tags            CASCADE;
DROP TABLE IF EXISTS mem_ai_tags_relations  CASCADE;
DROP TABLE IF EXISTS mng_ai_tags_relations  CASCADE;
DROP TABLE IF EXISTS mem_mrr_tags           CASCADE;
-- Drop stale tag_id FK from mem_ai_work_items (links now via mem_tags_relations)
ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS tag_id;
-- ── 002_mrr_tags_simplification: inline tags replaces mem_tags_relations ──
ALTER TABLE mem_mrr_prompts   ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '{}';
ALTER TABLE mem_mrr_commits   ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '{}';
ALTER TABLE mem_mrr_items     ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '{}';
ALTER TABLE mem_mrr_messages  ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '{}';
ALTER TABLE mem_mrr_prompts  DROP COLUMN IF EXISTS work_item_id;
ALTER TABLE mem_mrr_prompts  DROP COLUMN IF EXISTS metadata;
ALTER TABLE mem_mrr_prompts  DROP COLUMN IF EXISTS phase;
ALTER TABLE mem_mrr_prompts  DROP COLUMN IF EXISTS ai_tags;
ALTER TABLE mem_mrr_commits  DROP COLUMN IF EXISTS phase;
ALTER TABLE mem_mrr_commits  DROP COLUMN IF EXISTS feature;
ALTER TABLE mem_mrr_commits  DROP COLUMN IF EXISTS bug_ref;
ALTER TABLE mem_mrr_commits  DROP COLUMN IF EXISTS ai_tags;
ALTER TABLE mem_mrr_items    DROP COLUMN IF EXISTS ai_tags;
ALTER TABLE mem_mrr_messages DROP COLUMN IF EXISTS ai_tags;
DROP TABLE IF EXISTS mem_tags_relations CASCADE;
-- ── 003_tags_to_jsonb: TEXT[] → JSONB dict ──────────────────────────────────────────────────
-- Converts tags TEXT[] → JSONB. Must drop the TEXT[] default first, then retype, then set
-- JSONB default — all in one ALTER TABLE statement to avoid the "default cannot be cast" error.
-- If tags is already JSONB the ALTER fails — caught by fallback, logged at DEBUG, skipped.
ALTER TABLE mem_mrr_prompts   ALTER COLUMN tags DROP DEFAULT, ALTER COLUMN tags TYPE JSONB USING '{}'::jsonb, ALTER COLUMN tags SET DEFAULT '{}';
ALTER TABLE mem_mrr_commits   ALTER COLUMN tags DROP DEFAULT, ALTER COLUMN tags TYPE JSONB USING '{}'::jsonb, ALTER COLUMN tags SET DEFAULT '{}';
ALTER TABLE mem_mrr_items     ALTER COLUMN tags DROP DEFAULT, ALTER COLUMN tags TYPE JSONB USING '{}'::jsonb, ALTER COLUMN tags SET DEFAULT '{}';
ALTER TABLE mem_mrr_messages  ALTER COLUMN tags DROP DEFAULT, ALTER COLUMN tags TYPE JSONB USING '{}'::jsonb, ALTER COLUMN tags SET DEFAULT '{}';
ALTER TABLE mem_ai_events RENAME COLUMN metadata TO tags;
ALTER TABLE mem_ai_events ADD COLUMN IF NOT EXISTS tags JSONB NOT NULL DEFAULT '{}';
-- ── 004_mem_ai_events_refactor ────────────────────────────────────────────────────────────────
-- Merge open_threads into next_steps before renaming/dropping
UPDATE mem_ai_events
SET next_steps = CASE
    WHEN open_threads != '' AND next_steps != '' THEN open_threads || E'\n' || next_steps
    WHEN open_threads != ''                      THEN open_threads
    ELSE next_steps
END
WHERE open_threads IS NOT NULL AND open_threads != '';
ALTER TABLE mem_ai_events RENAME COLUMN next_steps TO session_action_items;
ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS open_threads;
-- ── 005_column_reorder ─────────────────────────────────────────────────────────
-- llm_source moved to after project; embedding moved to last column (all 4 tables).
-- PostgreSQL cannot reorder via ALTER TABLE — CREATE TABLE changes apply to clean installs only.
-- ── 006_tags_columns ───────────────────────────────────────────────────────────
-- Collapse doc_type / language / file_path into tags; rename session_action_items → action_items.
-- Data preservation: copy column values into tags before dropping.
UPDATE mem_ai_events
SET tags = tags
    || CASE WHEN doc_type  IS NOT NULL THEN jsonb_build_object('doc_type',  doc_type)  ELSE '{}'::jsonb END
    || CASE WHEN language   IS NOT NULL THEN jsonb_build_object('language',  language)  ELSE '{}'::jsonb END
    || CASE WHEN file_path  IS NOT NULL THEN jsonb_build_object('file',      file_path) ELSE '{}'::jsonb END
WHERE doc_type IS NOT NULL OR language IS NOT NULL OR file_path IS NOT NULL;
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='mem_ai_events' AND column_name='session_action_items'
    ) THEN
        ALTER TABLE mem_ai_events RENAME COLUMN session_action_items TO action_items;
    END IF;
END $$;
ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS doc_type;
ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS language;
ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS file_path;
ALTER TABLE mem_ai_events ADD COLUMN IF NOT EXISTS action_items TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_mem_ai_events_tags ON mem_ai_events USING gin(tags);
-- ── 007_source_llm_tags ──────────────────────────────────────────────────────
-- Move legacy named columns into the unified tags JSONB dict (idempotent).
UPDATE mem_mrr_prompts SET tags = tags || jsonb_build_object('source', llm_source)
 WHERE llm_source IS NOT NULL AND llm_source <> '';
ALTER TABLE mem_mrr_prompts DROP COLUMN IF EXISTS llm_source;
UPDATE mem_mrr_commits SET tags = tags || jsonb_build_object('source', source)
 WHERE source IS NOT NULL AND source <> '';
ALTER TABLE mem_mrr_commits DROP COLUMN IF EXISTS source;
UPDATE mem_ai_events SET tags = tags || jsonb_build_object('llm', llm_source)
 WHERE llm_source IS NOT NULL AND llm_source <> '';
ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS llm_source;
-- ── 008_drop_diff_details ────────────────────────────────────────────────────
-- diff_details was never populated by any code path; process_commit() fetches
-- diffs directly via git. Drop it and store file stats in tags["files"] instead.
ALTER TABLE mem_mrr_commits DROP COLUMN IF EXISTS diff_details;
-- ── 009_work_items_event_link ─────────────────────────────────────────────────
-- Link work items back to the event that generated them so the extraction
-- pipeline can avoid re-processing already-handled events.
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS source_event_id UUID;
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS source_session_id TEXT;
-- ── 010_project_ids: migrate all remaining tables project TEXT → project_id INT FK ─
-- Collects distinct (client_id, project) from each table into mng_projects,
-- then: ADD project_id, UPDATE from join, SET NOT NULL, ADD FK, DROP project.
-- Each block is wrapped in IF EXISTS so it is fully idempotent.
DO $$ DECLARE tbl TEXT;
BEGIN
  FOR tbl IN VALUES ('mem_mrr_prompts'),('mem_mrr_commits'),('mem_mrr_items'),
                    ('mem_mrr_messages'),('mem_ai_events'),('mem_ai_work_items'),
                    ('mem_ai_project_facts'),('pr_graph_workflows'),('pr_graph_runs'),
                    ('planner_tags')
  LOOP
    IF EXISTS (SELECT 1 FROM information_schema.columns
               WHERE table_schema='public' AND table_name=tbl AND column_name='project') THEN
      EXECUTE format(
        'INSERT INTO mng_projects(client_id, name)
         SELECT DISTINCT client_id, project FROM %I
         ON CONFLICT (client_id, name) DO NOTHING', tbl);
    END IF;
  END LOOP;
END $$;

-- mem_mrr_prompts
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='mem_mrr_prompts' AND column_name='project') THEN
    ALTER TABLE mem_mrr_prompts ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE mem_mrr_prompts t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE mem_mrr_prompts ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE mem_mrr_prompts ADD CONSTRAINT fk_mrr_prompts_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_mmrr_p_cp;
    DROP INDEX IF EXISTS idx_mmrr_p_source;
    ALTER TABLE mem_mrr_prompts DROP COLUMN IF EXISTS project;
    CREATE UNIQUE INDEX IF NOT EXISTS idx_mmrr_p_source ON mem_mrr_prompts(project_id, source_id) WHERE source_id IS NOT NULL;
    CREATE INDEX IF NOT EXISTS idx_mmrr_p_pid ON mem_mrr_prompts(project_id);
  END IF;
END $$;

-- mem_mrr_commits
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='mem_mrr_commits' AND column_name='project') THEN
    ALTER TABLE mem_mrr_commits ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE mem_mrr_commits t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE mem_mrr_commits ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE mem_mrr_commits ADD CONSTRAINT fk_mrr_commits_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_mmrr_c_cp;
    ALTER TABLE mem_mrr_commits DROP COLUMN IF EXISTS project;
    CREATE INDEX IF NOT EXISTS idx_mmrr_c_pid ON mem_mrr_commits(project_id);
  END IF;
END $$;

-- mem_mrr_items
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='mem_mrr_items' AND column_name='project') THEN
    ALTER TABLE mem_mrr_items ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE mem_mrr_items t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE mem_mrr_items ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE mem_mrr_items ADD CONSTRAINT fk_mrr_items_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_mmrr_items_cp;
    ALTER TABLE mem_mrr_items DROP COLUMN IF EXISTS project;
    CREATE INDEX IF NOT EXISTS idx_mmrr_items_pid ON mem_mrr_items(project_id);
  END IF;
END $$;

-- mem_mrr_messages
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='mem_mrr_messages' AND column_name='project') THEN
    ALTER TABLE mem_mrr_messages ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE mem_mrr_messages t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE mem_mrr_messages ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE mem_mrr_messages ADD CONSTRAINT fk_mrr_messages_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_mmrr_messages_cp;
    ALTER TABLE mem_mrr_messages DROP COLUMN IF EXISTS project;
    CREATE INDEX IF NOT EXISTS idx_mmrr_messages_pid ON mem_mrr_messages(project_id);
  END IF;
END $$;

-- mem_ai_events
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='mem_ai_events' AND column_name='project') THEN
    ALTER TABLE mem_ai_events ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE mem_ai_events t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE mem_ai_events ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE mem_ai_events ADD CONSTRAINT fk_ai_events_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_mem_ai_events_cp;
    BEGIN
      ALTER TABLE mem_ai_events DROP CONSTRAINT IF EXISTS mem_ai_events_client_id_project_event_type_source_id_chunk_key;
    EXCEPTION WHEN undefined_object THEN NULL; END;
    ALTER TABLE mem_ai_events DROP COLUMN IF EXISTS project;
    BEGIN
      ALTER TABLE mem_ai_events ADD CONSTRAINT mem_ai_events_pid_etype_src_chunk_key
        UNIQUE(project_id, event_type, source_id, chunk);
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    CREATE INDEX IF NOT EXISTS idx_mem_ai_events_pid ON mem_ai_events(project_id);
  END IF;
END $$;

-- mem_ai_work_items
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='mem_ai_work_items' AND column_name='project') THEN
    ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE mem_ai_work_items t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE mem_ai_work_items ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE mem_ai_work_items ADD CONSTRAINT fk_ai_wi_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_mem_ai_wi_cp;
    DROP INDEX IF EXISTS idx_mem_ai_wi_seq;
    BEGIN
      ALTER TABLE mem_ai_work_items DROP CONSTRAINT IF EXISTS mem_ai_work_items_client_id_project_category_name_name_key;
    EXCEPTION WHEN undefined_object THEN NULL; END;
    ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS project;
    BEGIN
      ALTER TABLE mem_ai_work_items ADD CONSTRAINT mem_ai_wi_pid_cat_name_key
        UNIQUE(project_id, category_name, name);
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_pid ON mem_ai_work_items(project_id);
    CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_seq ON mem_ai_work_items(project_id, seq_num) WHERE seq_num IS NOT NULL;
  END IF;
END $$;

-- mem_ai_project_facts
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='mem_ai_project_facts' AND column_name='project') THEN
    ALTER TABLE mem_ai_project_facts ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE mem_ai_project_facts t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE mem_ai_project_facts ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE mem_ai_project_facts ADD CONSTRAINT fk_ai_pf_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_mem_ai_pf_cp;
    DROP INDEX IF EXISTS idx_mem_ai_pf_current;
    ALTER TABLE mem_ai_project_facts DROP COLUMN IF EXISTS project;
    CREATE INDEX IF NOT EXISTS idx_mem_ai_pf_pid ON mem_ai_project_facts(project_id) WHERE valid_until IS NULL;
    CREATE UNIQUE INDEX IF NOT EXISTS idx_mem_ai_pf_current ON mem_ai_project_facts(project_id, fact_key) WHERE valid_until IS NULL;
  END IF;
END $$;

-- pr_graph_workflows
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='pr_graph_workflows' AND column_name='project') THEN
    ALTER TABLE pr_graph_workflows ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE pr_graph_workflows t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE pr_graph_workflows ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE pr_graph_workflows ADD CONSTRAINT fk_gw_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_pr_gw_cp;
    BEGIN
      ALTER TABLE pr_graph_workflows DROP CONSTRAINT IF EXISTS pr_graph_workflows_client_id_project_name_key;
    EXCEPTION WHEN undefined_object THEN NULL; END;
    ALTER TABLE pr_graph_workflows DROP COLUMN IF EXISTS project;
    BEGIN
      ALTER TABLE pr_graph_workflows ADD CONSTRAINT pr_gw_pid_name_key UNIQUE(project_id, name);
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    CREATE INDEX IF NOT EXISTS idx_pr_gw_pid ON pr_graph_workflows(project_id);
  END IF;
END $$;

-- pr_graph_runs
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='pr_graph_runs' AND column_name='project') THEN
    ALTER TABLE pr_graph_runs ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE pr_graph_runs t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE pr_graph_runs ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE pr_graph_runs ADD CONSTRAINT fk_gr_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_pr_gr_cp;
    ALTER TABLE pr_graph_runs DROP COLUMN IF EXISTS project;
    CREATE INDEX IF NOT EXISTS idx_pr_gr_pid ON pr_graph_runs(project_id);
  END IF;
END $$;

-- planner_tags
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='planner_tags' AND column_name='project') THEN
    ALTER TABLE planner_tags ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE planner_tags t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE planner_tags ALTER COLUMN project_id SET NOT NULL;
    BEGIN
      ALTER TABLE planner_tags ADD CONSTRAINT fk_pt_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    DROP INDEX IF EXISTS idx_planner_tags_cp;
    BEGIN
      ALTER TABLE planner_tags DROP CONSTRAINT IF EXISTS planner_tags_client_id_project_name_key;
      ALTER TABLE planner_tags DROP CONSTRAINT IF EXISTS planner_tags_project_name_cat_key;
    EXCEPTION WHEN undefined_object THEN NULL; END;
    ALTER TABLE planner_tags DROP COLUMN IF EXISTS project;
    BEGIN
      ALTER TABLE planner_tags ADD CONSTRAINT planner_tags_pid_name_cat_key
        UNIQUE(project_id, name, category_id);
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    CREATE INDEX IF NOT EXISTS idx_planner_tags_pid ON planner_tags(project_id);
  END IF;
END $$;

-- pr_seq_counters (special: PK includes project)
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema='public' AND table_name='pr_seq_counters' AND column_name='project') THEN
    -- Collect projects first
    INSERT INTO mng_projects(client_id, name)
    SELECT DISTINCT client_id, project FROM pr_seq_counters
    ON CONFLICT (client_id, name) DO NOTHING;
    ALTER TABLE pr_seq_counters ADD COLUMN IF NOT EXISTS project_id INT;
    UPDATE pr_seq_counters t SET project_id = p.id
      FROM mng_projects p WHERE p.name = t.project AND p.client_id = t.client_id
      WHERE t.project_id IS NULL;
    ALTER TABLE pr_seq_counters ALTER COLUMN project_id SET NOT NULL;
    -- Drop old PK (which included project) then drop column
    ALTER TABLE pr_seq_counters DROP CONSTRAINT IF EXISTS pr_seq_counters_pkey;
    ALTER TABLE pr_seq_counters DROP COLUMN IF EXISTS project;
    -- Add new PK and FK
    BEGIN
      ALTER TABLE pr_seq_counters ADD PRIMARY KEY (project_id, category);
    EXCEPTION WHEN duplicate_object THEN NULL; END;
    BEGIN
      ALTER TABLE pr_seq_counters ADD CONSTRAINT fk_seq_proj
        FOREIGN KEY (project_id) REFERENCES mng_projects(id) ON DELETE CASCADE;
    EXCEPTION WHEN duplicate_object THEN NULL; END;
  END IF;
END $$;
-- ── 011_work_items_refactor ───────────────────────────────────────────────────
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='mem_ai_work_items' AND column_name='category_name') THEN
    ALTER TABLE mem_ai_work_items RENAME COLUMN category_name TO ai_category;
  END IF;
END $$;
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='mem_ai_work_items' AND column_name='name') THEN
    ALTER TABLE mem_ai_work_items RENAME COLUMN name TO ai_name;
  END IF;
END $$;
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='mem_ai_work_items' AND column_name='description') THEN
    ALTER TABLE mem_ai_work_items RENAME COLUMN description TO ai_desc;
  END IF;
END $$;
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='mem_ai_work_items' AND column_name='implementation_plan') THEN
    ALTER TABLE mem_ai_work_items RENAME COLUMN implementation_plan TO action_items;
  END IF;
END $$;
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS content TEXT NOT NULL DEFAULT '';
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS summary TEXT NOT NULL DEFAULT '';
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS requirements TEXT NOT NULL DEFAULT '';
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS ai_tag_id UUID REFERENCES planner_tags(id);
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS tag_id UUID REFERENCES planner_tags(id);
-- Convert tags TEXT[] → JSONB
DO $$ BEGIN
  IF (SELECT data_type FROM information_schema.columns
      WHERE table_name='mem_ai_work_items' AND column_name='tags') = 'ARRAY' THEN
    ALTER TABLE mem_ai_work_items ALTER COLUMN tags DROP DEFAULT;
    ALTER TABLE mem_ai_work_items ALTER COLUMN tags TYPE JSONB USING '{}'::jsonb;
    ALTER TABLE mem_ai_work_items ALTER COLUMN tags SET DEFAULT '{}';
  END IF;
END $$;
ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS lifecycle_status;
ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS parent_id;
ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS due_date;
ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS agent_run_id;
ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS agent_status;
-- Update UNIQUE constraint (drop old variants, add new canonical one)
ALTER TABLE mem_ai_work_items DROP CONSTRAINT IF EXISTS mem_ai_work_items_project_id_category_name_name_key;
ALTER TABLE mem_ai_work_items DROP CONSTRAINT IF EXISTS mem_ai_wi_pid_cat_name_key;
DO $$ BEGIN
  ALTER TABLE mem_ai_work_items ADD CONSTRAINT mem_ai_work_items_proj_cat_name
    UNIQUE (project_id, ai_category, ai_name);
EXCEPTION WHEN duplicate_table THEN NULL; END $$;
-- ── 012_work_items_v2 ─────────────────────────────────────────────────────────
-- Split status → status_user (user-managed) + status_ai (AI-suggested).
-- Drop content (raw blob) and source_session_id (redundant).
-- Add code_summary (from linked commits) and source_event_id.
-- Move embedding to end of table (drop + re-add; data is regenerable).
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS status_user VARCHAR(20) NOT NULL DEFAULT 'active';
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS status_ai   VARCHAR(20) NOT NULL DEFAULT 'active';
ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS content;
ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS source_session_id;
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS source_event_id UUID;
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS code_summary TEXT NOT NULL DEFAULT '';
ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS embedding;
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);
DROP INDEX IF EXISTS idx_mem_ai_wi_status;
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_suser ON mem_ai_work_items(status_user);
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_sai   ON mem_ai_work_items(status_ai);
-- Migrate status → status_user (plain statement, no DO block needed since ADD sets DEFAULT)
UPDATE mem_ai_work_items SET status_user = status WHERE status IS NOT NULL AND status_user = 'active';
ALTER TABLE mem_ai_work_items DROP COLUMN IF EXISTS status;
-- ── 013_work_items_merge ──────────────────────────────────────────────────────
-- merged_into: when two work items are merged, both originals point to the new item.
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS merged_into UUID REFERENCES mem_ai_work_items(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_mem_ai_wi_merged ON mem_ai_work_items(merged_into) WHERE merged_into IS NOT NULL;
-- ── 014_planner_doc ──────────────────────────────────────────────────────────
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS start_date TIMESTAMPTZ;
-- ── 015_work_item_ai_tags ────────────────────────────────────────────────────
ALTER TABLE mem_ai_work_items ADD COLUMN IF NOT EXISTS ai_tags JSONB NOT NULL DEFAULT '{}';
-- ── 016_commits_refactor ─────────────────────────────────────────────────────
ALTER TABLE mem_mrr_commits ADD COLUMN IF NOT EXISTS commit_short_hash VARCHAR(8) GENERATED ALWAYS AS (LEFT(commit_hash,8)) STORED;
ALTER TABLE mem_mrr_commits ADD COLUMN IF NOT EXISTS author        TEXT NOT NULL DEFAULT '';
ALTER TABLE mem_mrr_commits ADD COLUMN IF NOT EXISTS author_email  TEXT NOT NULL DEFAULT '';
ALTER TABLE mem_mrr_commits ADD COLUMN IF NOT EXISTS llm           TEXT;
ALTER TABLE mem_mrr_commits ADD COLUMN IF NOT EXISTS exec_llm      BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE mem_mrr_commits ADD COLUMN IF NOT EXISTS tags_ai       JSONB NOT NULL DEFAULT '{}';
-- Migrate llm from tags → dedicated column; set exec_llm flag
UPDATE mem_mrr_commits SET llm = tags->>'llm', exec_llm = TRUE WHERE tags->>'llm' IS NOT NULL;
-- Strip technical keys from tags (keep: source, phase, feature, bug, work-item)
UPDATE mem_mrr_commits
   SET tags = tags - 'files' - 'languages' - 'symbols' - 'rows_changed' - 'llm'
                   - 'analysis' - 'commit_hash' - 'changed_files';
"""


# ─── DDL: schema version tracking ────────────────────────────────────────────

_DDL_SCHEMA_VERSION = """
CREATE TABLE IF NOT EXISTS mng_schema_version (
    version    VARCHAR(100) PRIMARY KEY,
    applied_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
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
            self._pool = psycopg2.pool.ThreadedConnectionPool(
                1, settings.db_pool_max, url,
                connect_timeout=10,
            )
            with self.conn() as conn:
                # lock_timeout: ALTER TABLE fails fast instead of hanging when another
                # session holds a table lock (e.g. from a previous crash mid-migration).
                # idle_in_transaction_session_timeout: auto-kills this session if it
                # goes idle mid-transaction (e.g. on kill -9), preventing zombie locks.
                with conn.cursor() as cur:
                    cur.execute("SET lock_timeout = '5s'")
                    cur.execute("SET idle_in_transaction_session_timeout = '30s'")
                conn.commit()
                self._ensure_schema(conn)
                self._ensure_shared_schema(conn)
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
    def _split_ddl(sql: str) -> list[str]:
        """Split SQL into individual statements, correctly handling DO $$ ... $$ blocks.

        Simple `;` split breaks dollar-quoted blocks (DO blocks contain internal
        semicolons). This method splits on `$$` boundaries first, keeping dollar-
        quoted content intact, then splits outer segments on `;`.
        """
        import re
        parts = re.split(r"(\$\$)", sql)
        result: list[str] = []
        current: list[str] = []
        in_quote = False
        for part in parts:
            if part == "$$":
                current.append("$$")
                in_quote = not in_quote
            elif in_quote:
                current.append(part)
            else:
                segments = part.split(";")
                current.append(segments[0])
                for seg in segments[1:]:
                    stmt = "".join(current).strip()
                    if stmt and not stmt.lstrip().startswith("--"):
                        result.append(stmt)
                    current = [seg]
        if remaining := "".join(current).strip():
            if remaining and not remaining.lstrip().startswith("--"):
                result.append(remaining)
        return result

    @staticmethod
    def _run_ddl_statements(conn, sql: str, label: str) -> None:
        """Run the entire DDL block in a single server round trip.

        All statements are sent as one string, processed server-side in one
        transaction. One COMMIT at the end. If the batch fails (rare — only on
        a fresh install with a DDL ordering bug), fall back to statement-by-statement
        so the error is isolated and progress is saved.
        """
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        except Exception:
            # Batch failed — fall back to individual statements so we don't
            # lose all progress. Per-statement commits are slow over remote DB
            # but this path is only hit on schema conflicts, not normal operation.
            conn.rollback()
            for stmt in _Database._split_ddl(sql):
                try:
                    with conn.cursor() as cur:
                        cur.execute(stmt)
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    msg = str(e).strip()
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
        _Database._seed_tag_categories(conn)

    @staticmethod
    def _migration_applied(conn, version: str) -> bool:
        """Return True if this migration version is recorded in mng_schema_version."""
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM mng_schema_version WHERE version=%s", (version,))
                return cur.fetchone() is not None
        except Exception:
            return False

    @staticmethod
    def _record_migration(conn, version: str) -> None:
        """Mark a migration version as applied."""
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO mng_schema_version (version) VALUES (%s) ON CONFLICT DO NOTHING",
                (version,),
            )
        conn.commit()

    def _ensure_shared_schema(self, conn) -> None:
        """Create all tables (mem_mrr_*, mem_ai_*, planner_*, pr_*) and run migrations.

        Uses mng_schema_version to skip migrations already applied — prevents the
        ~80-second Railway startup delay caused by re-running every ALTER TABLE on restart.
        Bump the version string (e.g. _v2 → _v3) when you add new statements to a block.
        """
        if self._shared_schema_ready:
            return

        # Schema version table must exist before we can check versions
        _Database._run_ddl_statements(conn, _DDL_SCHEMA_VERSION, "schema_version")

        _migrations = [
            ("pr_tables_v1",             _DDL_PR_TABLES,             "mem_mrr_* + mem_ai_work_items + graph tables"),
            ("memory_infra_v1",          _DDL_MEMORY_INFRA,          "planner_tags + mem_mrr_* + mem_ai_* tables"),
            ("memory_infra_alters_v2",   _DDL_MEMORY_INFRA_ALTERS,   "memory infra column alters (migration 016)"),
            ("work_items_alters_v1",     _DDL_WORK_ITEMS_ALTERS,     "mem_ai_work_items ai_tags column (migration 017)"),
            ("commit_code_v1",           _DDL_COMMIT_CODE,            "mem_mrr_commits_code"),
        ]
        for version, ddl, label in _migrations:
            if _Database._migration_applied(conn, version):
                log.debug(f"⏩ skipping {label} (already applied)")
            else:
                _Database._run_ddl_statements(conn, ddl, label)
                _Database._record_migration(conn, version)
                log.debug(f"✅ applied {label} (version={version})")

        self._shared_schema_ready = True
        log.info("✅ three-layer memory schema ready (mem_mrr_* | planner_* | mem_ai_*)")
    # ── Seeding ────────────────────────────────────────────────────────────────

    @staticmethod
    def _seed_agent_roles(conn) -> None:
        """Upsert the 10 built-in global roles (client_id=1).

        Uses DO UPDATE so improved prompts take effect on server restart.
        auto_commit=True is set on developer roles so pipeline nodes that
        link to them automatically commit+push their file changes.
        """
        # (name, description, system_prompt, provider, model, role_type, auto_commit, tools, react, max_iter)
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
                ["search_memory", "get_recent_history", "get_project_facts",
                 "list_work_items", "create_work_item", "read_file"], True, 10,
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
                ["search_memory", "get_project_facts", "read_file", "list_dir"], True, 10,
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
                ["read_file", "write_file", "list_dir", "git_status", "git_diff",
                 "git_commit", "git_push", "search_memory"], True, 15,
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
                ["read_file", "write_file", "list_dir", "git_status", "git_diff",
                 "git_commit", "git_push", "search_memory"], True, 15,
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
                ["read_file", "write_file", "list_dir", "git_status", "git_diff",
                 "git_commit", "git_push", "search_memory"], True, 15,
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
                ["read_file", "write_file", "list_dir", "git_status", "git_diff",
                 "git_commit", "git_push", "search_memory"], True, 15,
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
                ["read_file", "list_dir", "git_diff", "search_memory"], True, 10,
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
                ["read_file", "list_dir", "git_diff", "search_memory"], True, 10,
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
                ["read_file", "list_dir", "search_memory", "list_work_items"], True, 10,
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
                ["read_file", "write_file", "list_dir", "search_memory"], True, 10,
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
            "ALSO extract architectural relationships as facts using key prefix 'rel:':\n"
            '  {"key": "rel:component_a:component_b", "value": "implements|depends_on|causes|replaces|related_to", "confidence": 0.0-1.0}\n'
            "Only include relationships with confidence >= 0.75 and clear structural meaning.\n\n"
            "Good examples:\n"
            '[{"key":"auth_method","value":"JWT via python-jose + bcrypt, no passlib","confidence":0.95},\n'
            ' {"key":"vector_db","value":"pgvector cosine similarity, replaced ChromaDB","confidence":0.92},\n'
            ' {"key":"frontend_pattern","value":"Vanilla JS ES modules, no framework, no bundler","confidence":0.98},\n'
            ' {"key":"table_naming","value":"mng_ global, pr_ per-project, 25 fixed tables total","confidence":0.99},\n'
            ' {"key":"rel:auth:jwt","value":"implements","confidence":0.90},\n'
            ' {"key":"rel:vector_db:chromadb","value":"replaces","confidence":0.95}]\n\n'
            "Bad extractions — DO NOT produce:\n"
            '- {"key":"fixed_bug","value":"fixed login redirect"} — event\n'
            '- {"key":"todo","value":"add dark mode"} — task\n'
            '- {"key":"tech","value":"Python"} — too vague\n'
            '- {"key":"auth","value":"JWT"} — missing specifics'
        )

        try:
            import json as _json
            from psycopg2.extras import execute_values
            with conn.cursor() as cur:
                # Resolve _global project_id
                cur.execute(
                    "SELECT id FROM mng_projects WHERE client_id=1 AND name='_global'"
                )
                _global_row = cur.fetchone()
                if not _global_row:
                    log.warning("_global project not found — skipping agent role seed")
                    return
                global_pid = _global_row[0]

                # Batch all roles into one INSERT (single round trip)
                rows = [
                    (global_pid, name, desc, prompt, provider, model, role_type,
                     auto_commit, _json.dumps(tools), react, max_iter)
                    for (name, desc, prompt, provider, model, role_type,
                         auto_commit, tools, react, max_iter) in _ROLES
                ]
                # Append internal fact-extraction role
                rows.append((
                    global_pid, "internal_project_fact",
                    "Internal: extracts durable architectural facts from memory summaries.",
                    _INTERNAL_FACT_PROMPT, "claude", "claude-haiku-4-5-20251001",
                    "internal", False, "[]", False, 5,
                ))
                execute_values(
                    cur,
                    """INSERT INTO mng_agent_roles
                           (project_id, name, description, system_prompt,
                            provider, model, role_type, auto_commit,
                            tools, react, max_iterations)
                       VALUES %s
                       ON CONFLICT (project_id, name) DO UPDATE SET
                           description    = EXCLUDED.description,
                           system_prompt  = EXCLUDED.system_prompt,
                           provider       = EXCLUDED.provider,
                           model          = EXCLUDED.model,
                           role_type      = EXCLUDED.role_type,
                           auto_commit    = EXCLUDED.auto_commit,
                           tools          = EXCLUDED.tools,
                           react          = EXCLUDED.react,
                           max_iterations = EXCLUDED.max_iterations""",
                    rows,
                )

                # Auto-seed from workspace/_templates/roles/*.yaml
                _Database._seed_roles_from_yaml(cur)

            conn.commit()
            log.debug("✅ Agent roles seeded")
        except Exception as e:
            conn.rollback()
            log.warning(f"Agent roles seed skipped: {e}")

    @staticmethod
    def _seed_roles_from_yaml(cur) -> None:
        """Full UPSERT of agent roles from workspace/_templates/roles/*.yaml into DB.

        - Existing role (matched by client_id + project + name): ALL fields updated from YAML.
        - New role (not yet in DB): inserted fresh from YAML.

        Called after the built-in batch INSERT so YAML values take precedence.
        Roles are written to project='_global' (shared across all projects/clients).
        """
        import json as _json
        try:
            import yaml as _yaml
        except ImportError:
            log.debug("PyYAML not installed — skipping YAML role seed")
            return

        templates_dir = (
            Path(__file__).parent.parent.parent
            / "workspace" / "_templates" / "roles"
        )
        if not templates_dir.exists():
            return

        # Look up _global project_id once, before iterating YAML files
        cur.execute(
            "SELECT id FROM mng_projects WHERE client_id=1 AND name='_global'"
        )
        _row = cur.fetchone()
        if not _row:
            log.debug("_global project not found — skipping YAML role seed")
            return
        global_pid = _row[0]

        for yaml_path in sorted(templates_dir.glob("*.yaml")):
            try:
                data = _yaml.safe_load(yaml_path.read_text())
                if not data or not isinstance(data, dict) or not data.get("name"):
                    continue

                name           = data["name"]
                description    = data.get("description", "")
                system_prompt  = data.get("system_prompt", "")
                provider       = data.get("provider", "claude")
                model          = data.get("model", "")
                role_type      = data.get("role_type", "agent")
                auto_commit    = bool(data.get("auto_commit", False))
                tools          = _json.dumps(data.get("tools", []))
                react          = bool(data.get("react", True))
                max_it         = int(data.get("max_iterations", 10))
                inputs         = _json.dumps(data.get("inputs", []))
                outputs        = _json.dumps(data.get("outputs", []))

                cur.execute(
                    """INSERT INTO mng_agent_roles
                           (project_id, name, description, system_prompt,
                            provider, model, role_type, auto_commit,
                            tools, react, max_iterations, inputs, outputs)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       ON CONFLICT (project_id, name) DO UPDATE SET
                           description    = EXCLUDED.description,
                           system_prompt  = EXCLUDED.system_prompt,
                           provider       = EXCLUDED.provider,
                           model          = EXCLUDED.model,
                           role_type      = EXCLUDED.role_type,
                           auto_commit    = EXCLUDED.auto_commit,
                           tools          = EXCLUDED.tools,
                           react          = EXCLUDED.react,
                           max_iterations = EXCLUDED.max_iterations,
                           inputs         = EXCLUDED.inputs,
                           outputs        = EXCLUDED.outputs,
                           updated_at     = NOW()""",
                    (global_pid, name, description, system_prompt, provider, model,
                     role_type, auto_commit, tools, react, max_it, inputs, outputs),
                )
                log.debug(f"YAML role upserted: '{name}' ({yaml_path.name})")
            except Exception as yaml_err:
                log.warning(f"YAML role seed failed for {yaml_path.name}: {yaml_err}")

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
                "mng_ global tables, mem_mrr_/mem_ai_ memory tables, pr_ workflow tables, snake_case.",
                "## Naming Conventions\n\n"
                "Database tables:\n"
                "- Global / client-scoped: prefix `mng_` (e.g. mng_users, mng_agent_roles)\n"
                "- Memory mirror layer: prefix `mem_mrr_` (e.g. mem_mrr_prompts, mem_mrr_commits)\n"
                "- Memory AI layer: prefix `mem_ai_` (e.g. mem_ai_events, mem_ai_work_items)\n"
                "- Planner / tag hierarchy: prefix `planner_` (e.g. planner_tags)\n"
                "- Graph workflow tables: prefix `pr_` (e.g. pr_graph_workflows, pr_graph_runs)\n"
                "- Never create new tables outside these namespaces\n"
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
            from psycopg2.extras import execute_values
            with conn.cursor() as cur:
                execute_values(
                    cur,
                    """INSERT INTO mng_system_roles
                           (client_id, name, category, description, content)
                       VALUES %s
                       ON CONFLICT (client_id, name) DO UPDATE SET
                           category    = EXCLUDED.category,
                           description = EXCLUDED.description,
                           content     = EXCLUDED.content""",
                    [(1, name, category, description, content)
                     for name, category, description, content in _DEFAULT_SYSTEM_ROLES],
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
            from psycopg2.extras import execute_values
            with conn.cursor() as cur:
                # Resolve all IDs in two queries, then batch-insert links in one
                cur.execute("SELECT name, id FROM mng_agent_roles  WHERE client_id=1")
                ar_ids = {r[0]: r[1] for r in cur.fetchall()}
                cur.execute("SELECT name, id FROM mng_system_roles WHERE client_id=1")
                sr_ids = {r[0]: r[1] for r in cur.fetchall()}
                rows = [
                    (ar_ids[a], sr_ids[s], idx)
                    for a, s, idx in _LINKS
                    if a in ar_ids and s in sr_ids
                ]
                if rows:
                    execute_values(
                        cur,
                        """INSERT INTO mng_role_system_links (role_id, system_role_id, order_index)
                           VALUES %s ON CONFLICT DO NOTHING""",
                        rows,
                    )
            conn.commit()
            log.debug("✅ Role-system links seeded")
        except Exception as e:
            conn.rollback()
            log.warning(f"Role-system links seed skipped: {e}")

    @staticmethod
    def _seed_tag_categories(conn) -> None:
        """Seed default tag categories into mng_tags_categories."""
        _SEED_CATS = [
            ("feature",      "#22c55e", "⚡", "New functionality"),
            ("bug",          "#ef4444", "🐛", "Defect or unexpected behaviour"),
            ("task",         "#3b82f6", "✓",  "Process or maintenance work"),
            ("design",       "#a855f7", "◈",  "Architecture or UX design"),
            ("decision",     "#f59e0b", "⚑",  "Architectural or product decision"),
            ("meeting",      "#6b7280", "◷",  "Meeting summary"),
            ("ai_suggestion","#94a3b8", "✦",  "Auto-suggested by AI — reassign to proper category"),
        ]
        try:
            with conn.cursor() as cur:
                # Only seed if table exists (schema may not be ready on first run)
                cur.execute(
                    "SELECT 1 FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_name='mng_tags_categories'"
                )
                if not cur.fetchone():
                    return
                for name, color, icon, desc in _SEED_CATS:
                    cur.execute(
                        """INSERT INTO mng_tags_categories (client_id, name, color, icon, description)
                           VALUES (1, %s, %s, %s, %s) ON CONFLICT (client_id, name) DO NOTHING""",
                        (name, color, icon, desc),
                    )
            conn.commit()
            log.debug("✅ mng_tags_categories seeded")
        except Exception as e:
            conn.rollback()
            log.debug(f"_seed_tag_categories skipped: {e}")

    # ── Project ID helpers ─────────────────────────────────────────────────────

    def get_project_id(self, name: str, client_id: int = 1) -> int | None:
        """Resolve project name → project_id (module-level cache). Returns None if not found."""
        key = (client_id, name)
        if key in _PROJECT_ID_CACHE:
            return _PROJECT_ID_CACHE[key]
        if not self.is_available():
            return None
        try:
            with self.conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM mng_projects WHERE client_id=%s AND name=%s",
                        (client_id, name),
                    )
                    row = cur.fetchone()
            if row:
                _PROJECT_ID_CACHE[key] = row[0]
                return row[0]
        except Exception as e:
            log.debug(f"get_project_id({name!r}) failed: {e}")
        return None

    def get_or_create_project_id(
        self,
        name: str,
        client_id: int = 1,
        config: dict | None = None,
    ) -> int:
        """Resolve or create project, returning project_id.

        On first call for a name, upserts a row in mng_projects and caches the ID.
        Subsequent calls return from cache.
        """
        pid = self.get_project_id(name, client_id)
        if pid is not None:
            return pid
        cfg = config or {}
        params = {
            "client_id": client_id,
            "name": name,
            "description": cfg.get("description", ""),
            "code_dir": cfg.get("code_dir"),
            "default_provider": cfg.get("default_provider", "claude"),
            "workspace_path": str(_workspace() / name),
        }
        with self.conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO mng_projects
                           (client_id, name, description, code_dir, default_provider, workspace_path)
                       VALUES (%(client_id)s, %(name)s, %(description)s, %(code_dir)s,
                               %(default_provider)s, %(workspace_path)s)
                       ON CONFLICT (client_id, name) DO UPDATE SET
                           description      = COALESCE(EXCLUDED.description, mng_projects.description),
                           code_dir         = COALESCE(EXCLUDED.code_dir, mng_projects.code_dir),
                           updated_at       = NOW()
                       RETURNING id""",
                    params,
                )
                pid = cur.fetchone()[0]
        _PROJECT_ID_CACHE[(client_id, name)] = pid
        return pid

    def invalidate_project_cache(self, name: str, client_id: int = 1) -> None:
        """Remove a project from the cache (call after rename or delete)."""
        _PROJECT_ID_CACHE.pop((client_id, name), None)

    @staticmethod
    def _seed_client_defaults(client_id: int, conn) -> None:
        """Seed default tag categories for a new client. Idempotent."""
        _CATS = [
            ("feature", "#22c55e", "⚡", "New functionality"),
            ("bug",     "#ef4444", "🐛", "Defect or unexpected behaviour"),
            ("task",    "#3b82f6", "✓",  "Process or maintenance work"),
            ("design",  "#a855f7", "◈",  "Architecture or UX design"),
        ]
        try:
            with conn.cursor() as cur:
                for name, color, icon, desc in _CATS:
                    cur.execute(
                        """INSERT INTO mng_tags_categories (client_id, name, color, icon, description)
                           VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING""",
                        (client_id, name, color, icon, desc),
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
            f"UPDATE mng_tags_categories SET {set_clause}, updated_at=NOW() WHERE id=%s",
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
        cur.execute(f"SELECT * FROM mem_ai_work_items {where} ORDER BY created_at", params)
    """
    active = [c for c in conditions if c is not None]
    if not active:
        return "", []
    clause = "WHERE " + " AND ".join(snippet for snippet, _ in active)
    params = [val for _, val in active]
    return clause, params
