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
from typing import Generator

import psycopg2
import psycopg2.pool

from config import settings

log = logging.getLogger(__name__)

# ─── DDL: mng_clients ────────────────────────────────────────────────────────

_DDL_CLIENTS = """
CREATE TABLE IF NOT EXISTS mng_clients (
    id         SERIAL       PRIMARY KEY,
    slug       VARCHAR(50)  UNIQUE NOT NULL,
    name       VARCHAR(255) NOT NULL DEFAULT '',
    plan       VARCHAR(20)  NOT NULL DEFAULT 'free',
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
"""

# ─── DDL: mng_users / usage_logs / transactions ───────────────────────────────

_DDL_CORE = """
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
ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS role               VARCHAR(20)    NOT NULL DEFAULT 'free';
ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS balance_added_usd  NUMERIC(14, 8) NOT NULL DEFAULT 0;
ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS balance_used_usd   NUMERIC(14, 8) NOT NULL DEFAULT 0;
ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS coupons_used       TEXT[]         NOT NULL DEFAULT '{}';
ALTER TABLE mng_users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(100)   NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_users_email ON mng_users(email);

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
CREATE INDEX IF NOT EXISTS idx_usage_user_id    ON mng_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_created_at ON mng_usage_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_provider   ON mng_usage_logs(provider);

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
            self._pool = psycopg2.pool.ThreadedConnectionPool(1, settings.db_pool_max, url)
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
    def _ensure_schema(conn) -> None:
        """Create / migrate mng_* tables. Safe to run repeatedly."""
        for label, sql in [
            ("mng_clients", _DDL_CLIENTS),
            ("mng_core (users/usage/tx)", _DDL_CORE),
            ("mng_entity+session+role tables", _DDL_MNG_TABLES),
        ]:
            try:
                with conn.cursor() as cur:
                    cur.execute(sql)
                conn.commit()
                log.debug(f"✅ {label} DDL ok")
            except Exception as e:
                conn.rollback()
                log.warning(f"{label} DDL skipped: {e}")

        # Seed built-in global agent roles (idempotent)
        _Database._seed_agent_roles(conn)

    def _ensure_shared_schema(self, conn) -> None:
        """Create all 15 pr_* flat tables. Runs once per process lifetime."""
        if self._shared_schema_ready:
            return
        try:
            with conn.cursor() as cur:
                cur.execute(_DDL_PR_TABLES)
            conn.commit()
            self._shared_schema_ready = True
            log.info("✅ pr_* flat tables ready")
        except Exception as e:
            conn.rollback()
            log.warning(f"_ensure_shared_schema failed: {e}")

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
                try:
                    cur.execute(
                        """INSERT INTO pr_work_items
                               (id, client_id, project, category_name, category_id,
                                name, description, status, lifecycle_status, due_date,
                                parent_id, acceptance_criteria, implementation_plan,
                                agent_run_id, agent_status, tags, created_at, updated_at)
                           VALUES (%s,1,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT DO NOTHING""",
                        (wi_id, proj, cat_name, new_cat, name, desc, status, lc, due, par,
                         ac, impl, run_id, a_status, tags, ts, upd),
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

        # Interaction tags (IDs preserved from work items/interactions above)
        if _exists(_tbl("interaction_tags")):
            _run(f"""
                INSERT INTO pr_interaction_tags
                    (interaction_id, work_item_id, auto_tagged, created_at)
                SELECT interaction_id, work_item_id, auto_tagged, created_at
                FROM {_tbl("interaction_tags")} ON CONFLICT DO NOTHING
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

        # Graph workflows
        if _exists(_tbl("graph_workflows")):
            _run(f"""
                INSERT INTO pr_graph_workflows
                    (id, client_id, project, name, description,
                     max_iterations, created_at, updated_at)
                SELECT id, 1, project, name, description,
                       max_iterations, created_at, updated_at
                FROM {_tbl("graph_workflows")} ON CONFLICT DO NOTHING
            """)

        # Graph nodes (role_id remapping)
        if _exists(_tbl("graph_nodes")):
            cur.execute(f"""
                SELECT id, workflow_id, name, role_id, role_file, role_prompt,
                       provider, model, output_schema, inject_context,
                       require_approval, approval_msg, position_x, position_y,
                       created_at, updated_at
                FROM {_tbl("graph_nodes")}
            """)
            for row in cur.fetchall():
                (gn_id, wf_id, name, old_rid, role_file, role_prompt, prov, model,
                 out_schema, inj, req_app, app_msg, px, py, ts, upd) = row
                new_rid = ar_id_map.get(old_rid) if old_rid else None
                try:
                    cur.execute(
                        """INSERT INTO pr_graph_nodes
                               (id, workflow_id, name, role_id, role_file, role_prompt,
                                provider, model, output_schema, inject_context,
                                require_approval, approval_msg, position_x, position_y,
                                created_at, updated_at)
                           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                           ON CONFLICT DO NOTHING""",
                        (gn_id, wf_id, name, new_rid, role_file, role_prompt, prov, model,
                         out_schema, inj, req_app, app_msg, px, py, ts, upd),
                    )
                except Exception:
                    conn.rollback()
            conn.commit()

        # Graph edges
        if _exists(_tbl("graph_edges")):
            _run(f"""
                INSERT INTO pr_graph_edges
                    (id, workflow_id, source_node_id, target_node_id,
                     condition, label, created_at, updated_at)
                SELECT id, workflow_id, source_node_id, target_node_id,
                       condition, label, created_at, updated_at
                FROM {_tbl("graph_edges")} ON CONFLICT DO NOTHING
            """)

        # Graph runs
        if _exists(_tbl("graph_runs")):
            _run(f"""
                INSERT INTO pr_graph_runs
                    (id, client_id, project, workflow_id, status, user_input,
                     context, started_at, finished_at, total_cost_usd, error)
                SELECT id, 1, project, workflow_id, status, user_input,
                       context, started_at, finished_at, total_cost_usd, error
                FROM {_tbl("graph_runs")} ON CONFLICT DO NOTHING
            """)

        # Graph node results
        if _exists(_tbl("graph_node_results")):
            _run(f"""
                INSERT INTO pr_graph_node_results
                    (id, run_id, node_id, node_name, status, output, structured,
                     input_tokens, output_tokens, cost_usd,
                     started_at, finished_at, iteration)
                SELECT id, run_id, node_id, node_name, status, output, structured,
                       input_tokens, output_tokens, cost_usd,
                       started_at, finished_at, iteration
                FROM {_tbl("graph_node_results")} ON CONFLICT DO NOTHING
            """)

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
                cur.execute(f"DROP TABLE IF EXISTS {tbl_name}")
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
        """Insert the 10 built-in global roles (client_id=1). Idempotent."""
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
                               (client_id, project, name, description, system_prompt, provider, model)
                           VALUES (1, '_global', %s, %s, %s, %s, %s)
                           ON CONFLICT (client_id, project, name) DO NOTHING""",
                        (name, desc, prompt, provider, model),
                    )
            conn.commit()
            log.debug("✅ Agent roles seeded")
        except Exception as e:
            conn.rollback()
            log.warning(f"Agent roles seed skipped: {e}")

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
