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
        # Projects whose per-project schema has been verified this process lifetime.
        # Skips all DDL/ALTER on subsequent calls — safe because CREATE/ALTER are idempotent.
        self._schema_ready: set[str] = set()

    def init(self) -> None:
        """Called at startup. Creates connection pool if DATABASE_URL is set."""
        url = settings.database_url
        if not url:
            log.info("DATABASE_URL not set — using file-based storage")
            return
        try:
            self._pool = psycopg2.pool.ThreadedConnectionPool(1, settings.db_pool_max, url)
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
        """Create per-project tables if they don't exist. Safe to call repeatedly.

        Results are cached in-process: the DDL only runs once per project per process
        lifetime, eliminating the round-trip cost on every subsequent project open.
        """
        if not self._available:
            return
        if project in self._schema_ready:
            return   # already done this process lifetime — skip all DDL
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

        CREATE TABLE IF NOT EXISTS {e} (
            id         SERIAL         PRIMARY KEY,
            event_type VARCHAR(50)    NOT NULL,
            source_id  VARCHAR(255)   NOT NULL,
            title      TEXT           NOT NULL DEFAULT '',
            content    TEXT           NOT NULL DEFAULT '',
            phase      VARCHAR(20),
            feature    VARCHAR(255),
            session_id VARCHAR(255),
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
        # All DDL + migrations in a single transaction — one round-trip instead of 14.
        # Each statement is wrapped in a SAVEPOINT so a single failure (e.g. column
        # already exists on Postgres < 9.6) doesn't roll back the whole batch.
        _migrations = [
            f"ALTER TABLE {c} ADD COLUMN IF NOT EXISTS prompt_source_id VARCHAR(255)",
            f"ALTER TABLE {c} ADD COLUMN IF NOT EXISTS session_id        VARCHAR(255)",
            f"ALTER TABLE {e} ADD COLUMN IF NOT EXISTS phase             VARCHAR(20)",
            f"ALTER TABLE {e} ADD COLUMN IF NOT EXISTS feature           VARCHAR(255)",
            f"ALTER TABLE {e} ADD COLUMN IF NOT EXISTS session_id        VARCHAR(255)",
            f"CREATE INDEX IF NOT EXISTS idx_{e}_session ON {e}(session_id) WHERE session_id IS NOT NULL",
            f"CREATE INDEX IF NOT EXISTS idx_{e}_phase   ON {e}(phase)      WHERE phase IS NOT NULL",
            f"CREATE INDEX IF NOT EXISTS idx_{el}_to     ON {el}(to_event_id)",
            f"CREATE INDEX IF NOT EXISTS idx_{c}_session ON {c}(session_id) WHERE session_id IS NOT NULL",
            f"CREATE INDEX IF NOT EXISTS idx_{emb}_src   ON {emb}(source_type, source_id)",
            "ALTER TABLE entity_values ADD COLUMN IF NOT EXISTS lifecycle_status VARCHAR(20) NOT NULL DEFAULT 'idea'",
            """CREATE TABLE IF NOT EXISTS entity_value_links (
                from_value_id INT NOT NULL REFERENCES entity_values(id) ON DELETE CASCADE,
                to_value_id   INT NOT NULL REFERENCES entity_values(id) ON DELETE CASCADE,
                link_type     VARCHAR(50) NOT NULL DEFAULT 'blocks',
                created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY(from_value_id, to_value_id, link_type)
            )""",
            "CREATE INDEX IF NOT EXISTS idx_evl_from ON entity_value_links(from_value_id)",
            "CREATE INDEX IF NOT EXISTS idx_evl_to   ON entity_value_links(to_value_id)",
        ]
        try:
            with self.conn() as conn:
                with conn.cursor() as cur:
                    # Main table DDL
                    cur.execute(ddl)
                    # Migrations — each in its own savepoint so one failure doesn't abort all
                    for i, sql in enumerate(_migrations):
                        sp = f"sp_mig_{i}"
                        try:
                            cur.execute(f"SAVEPOINT {sp}")
                            cur.execute(sql)
                            cur.execute(f"RELEASE SAVEPOINT {sp}")
                        except Exception:
                            cur.execute(f"ROLLBACK TO SAVEPOINT {sp}")
            self._schema_ready.add(project)
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
        ALTER TABLE entity_values ADD COLUMN IF NOT EXISTS lifecycle_status VARCHAR(20) NOT NULL DEFAULT 'idea';
        CREATE INDEX IF NOT EXISTS idx_ev_parent ON entity_values(parent_id);

        -- Value-to-value dependency links (blocks, related_to, etc.)
        CREATE TABLE IF NOT EXISTS entity_value_links (
            from_value_id INT NOT NULL REFERENCES entity_values(id) ON DELETE CASCADE,
            to_value_id   INT NOT NULL REFERENCES entity_values(id) ON DELETE CASCADE,
            link_type     VARCHAR(50) NOT NULL DEFAULT 'blocks',
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY(from_value_id, to_value_id, link_type)
        );
        CREATE INDEX IF NOT EXISTS idx_evl_from ON entity_value_links(from_value_id);
        CREATE INDEX IF NOT EXISTS idx_evl_to   ON entity_value_links(to_value_id);
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
            id              SERIAL         PRIMARY KEY,
            workflow_id     INT            NOT NULL REFERENCES graph_workflows(id) ON DELETE CASCADE,
            project         VARCHAR(255)   NOT NULL,
            status          VARCHAR(50)    NOT NULL DEFAULT 'pending',
            started_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            finished_at     TIMESTAMPTZ,
            total_cost_usd  NUMERIC(12, 8) NOT NULL DEFAULT 0,
            context         JSONB          NOT NULL DEFAULT '{}',
            input           TEXT           NOT NULL DEFAULT '',
            output          TEXT           NOT NULL DEFAULT ''
        );
        ALTER TABLE graph_runs ADD COLUMN IF NOT EXISTS total_cost_usd NUMERIC(12, 8) NOT NULL DEFAULT 0;
        ALTER TABLE graph_runs ADD COLUMN IF NOT EXISTS context        JSONB          NOT NULL DEFAULT '{}';
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

        _DDL_MEMORY_LAYERS = """
        -- Work items: replaces entity_values for feature/bug/task categories.
        -- Adds acceptance_criteria, implementation_plan, and agent pipeline tracking.
        CREATE TABLE IF NOT EXISTS work_items (
            id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
            project             TEXT          NOT NULL,
            category_name       TEXT          NOT NULL,
            category_id         INT           REFERENCES entity_categories(id) ON DELETE SET NULL,
            name                TEXT          NOT NULL,
            description         TEXT          NOT NULL DEFAULT '',
            status              VARCHAR(20)   NOT NULL DEFAULT 'active',
            lifecycle_status    VARCHAR(20)   NOT NULL DEFAULT 'idea',
            due_date            DATE,
            parent_id           UUID          REFERENCES work_items(id) ON DELETE SET NULL,
            acceptance_criteria TEXT          NOT NULL DEFAULT '',
            implementation_plan TEXT          NOT NULL DEFAULT '',
            agent_run_id        INT           REFERENCES graph_runs(id) ON DELETE SET NULL,
            agent_status        VARCHAR(20),
            tags                TEXT[]        NOT NULL DEFAULT '{}',
            created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            UNIQUE(project, category_name, name)
        );
        CREATE INDEX IF NOT EXISTS idx_wi_project  ON work_items(project);
        CREATE INDEX IF NOT EXISTS idx_wi_category ON work_items(category_name);
        CREATE INDEX IF NOT EXISTS idx_wi_status   ON work_items(status);

        -- Interactions: unified shared table replacing per-project events_{p}.
        -- project_id is TEXT so no per-project schema migration is needed.
        CREATE TABLE IF NOT EXISTS interactions (
            id                  UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id          TEXT          NOT NULL,
            work_item_id        UUID          REFERENCES work_items(id) ON DELETE SET NULL,
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
        CREATE INDEX IF NOT EXISTS idx_int_project  ON interactions(project_id);
        CREATE INDEX IF NOT EXISTS idx_int_session  ON interactions(session_id)   WHERE session_id IS NOT NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_int_source ON interactions(project_id, source_id) WHERE source_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_int_created  ON interactions(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_int_workitem ON interactions(work_item_id) WHERE work_item_id IS NOT NULL;

        -- Interaction tags: replaces per-project event_tags_{p}.
        CREATE TABLE IF NOT EXISTS interaction_tags (
            interaction_id  UUID          NOT NULL REFERENCES interactions(id)  ON DELETE CASCADE,
            work_item_id    UUID          NOT NULL REFERENCES work_items(id)    ON DELETE CASCADE,
            auto_tagged     BOOLEAN       NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            PRIMARY KEY(interaction_id, work_item_id)
        );
        CREATE INDEX IF NOT EXISTS idx_itag_work ON interaction_tags(work_item_id);

        -- Memory items: Trycycle-reviewed session/feature summaries (distilled memory layer).
        CREATE TABLE IF NOT EXISTS memory_items (
            id              UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id      TEXT          NOT NULL,
            scope           TEXT          NOT NULL,
            scope_ref       TEXT,
            content         TEXT          NOT NULL,
            embedding       VECTOR(1536),
            source_ids      UUID[]        NOT NULL DEFAULT '{}',
            tags            TEXT[]        NOT NULL DEFAULT '{}',
            reviewer_score  INT,
            reviewer_critique TEXT,
            created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
        );
        CREATE INDEX IF NOT EXISTS idx_mi_project ON memory_items(project_id);
        CREATE INDEX IF NOT EXISTS idx_mi_scope   ON memory_items(project_id, scope);
        CREATE INDEX IF NOT EXISTS idx_mi_created ON memory_items(created_at DESC);

        -- Project facts: durable single facts extracted from memory ("we use pgvector", etc.).
        -- valid_until IS NULL = currently valid; set to NOW() to invalidate on conflict.
        CREATE TABLE IF NOT EXISTS project_facts (
            id               UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
            project_id       TEXT          NOT NULL,
            fact_key         TEXT          NOT NULL,
            fact_value       TEXT          NOT NULL,
            valid_from       TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
            valid_until      TIMESTAMPTZ,
            source_memory_id UUID          REFERENCES memory_items(id) ON DELETE SET NULL
        );
        CREATE INDEX IF NOT EXISTS        idx_pf_project ON project_facts(project_id)            WHERE valid_until IS NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_pf_current ON project_facts(project_id, fact_key)  WHERE valid_until IS NULL;
        """

        _DDL_AGENT_ROLES = """
        -- Agent role library: reusable LLM personas for workflow nodes.
        -- All users see name/description; system_prompt is admin-only via the API.
        CREATE TABLE IF NOT EXISTS agent_roles (
            id            SERIAL         PRIMARY KEY,
            project       TEXT           NOT NULL DEFAULT '_global',
            name          TEXT           NOT NULL,
            description   TEXT           NOT NULL DEFAULT '',
            system_prompt TEXT           NOT NULL DEFAULT '',
            provider      TEXT           NOT NULL DEFAULT 'claude',
            model         TEXT           NOT NULL DEFAULT '',
            tags          TEXT[]         NOT NULL DEFAULT '{}',
            is_active     BOOLEAN        NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            UNIQUE(project, name)
        );
        CREATE INDEX IF NOT EXISTS idx_ar_project ON agent_roles(project);

        -- Version history: written on every PATCH to system_prompt/provider/model.
        CREATE TABLE IF NOT EXISTS agent_role_versions (
            id            SERIAL         PRIMARY KEY,
            role_id       INT            NOT NULL REFERENCES agent_roles(id) ON DELETE CASCADE,
            system_prompt TEXT           NOT NULL,
            provider      TEXT           NOT NULL,
            model         TEXT           NOT NULL,
            changed_by    TEXT,
            changed_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
            note          TEXT           NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_arv_role ON agent_role_versions(role_id);

        -- Link graph_nodes to a reusable role (prompt loaded from agent_roles at run time).
        ALTER TABLE graph_nodes ADD COLUMN IF NOT EXISTS role_id INT REFERENCES agent_roles(id) ON DELETE SET NULL;
        """

        for label, sql in [
            ("Embeddings (pgvector)", _DDL_EMBEDDINGS),
            ("Tagging (commits + session_tags)", _DDL_TAGGING),
            ("Entities (categories + values + events + links)", _DDL_ENTITIES),
            ("Graph workflows (nodes, edges, runs, results)", _DDL_GRAPH),
            ("Memory layers (work_items, interactions, memory_items, project_facts)", _DDL_MEMORY_LAYERS),
            ("Agent roles (library + version history)", _DDL_AGENT_ROLES),
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

        # Seed default global roles (idempotent — skips on conflict)
        _Database._seed_agent_roles(conn)

    @staticmethod
    def _seed_agent_roles(conn) -> None:
        """Insert the 10 built-in global roles. Safe to call repeatedly."""
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
                        """INSERT INTO agent_roles
                               (project, name, description, system_prompt, provider, model)
                           VALUES ('_global', %s, %s, %s, %s, %s)
                           ON CONFLICT (project, name) DO NOTHING""",
                        (name, desc, prompt, provider, model),
                    )
            conn.commit()
            log.info("✅ Agent roles seeded")
        except Exception as e:
            conn.rollback()
            log.warning(f"Agent roles seed skipped: {e}")


# Singleton used everywhere
db = _Database()
