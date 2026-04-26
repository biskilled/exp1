"""
PostgreSQL connection pool — three-layer memory architecture.

Table namespaces:
  mng_         — global + client-scoped (management tables)
  mem_mrr_     — mirroring layer (raw source data: prompts, commits, items, messages)
  mem_ai_      — AI/embedding layer (mem_ai_project_facts, mem_work_items)
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


# ─── Schema SQL ─────────────────────────────────────────────────────────────────
# db_schema.sql: canonical latest table definitions — the single source of truth.
# db_migrations.py: rename → recreate → copy migrations applied at startup.
_SCHEMA_SQL_PATH = Path(__file__).parent / "db_schema.sql"


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
        # Test the connection; if stale, discard and get a fresh one
        try:
            connection.cursor().execute("SELECT 1")
        except Exception:
            try:
                self._pool.putconn(connection, close=True)
            except Exception:
                pass
            connection = self._pool.getconn()
        try:
            yield connection
            connection.commit()
        except Exception:
            try:
                connection.rollback()
            except Exception:
                pass
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
        """Apply db_schema.sql on fresh installs; detect existing installs and skip.

        Flow:
          1. Create mng_schema_version (tiny table, fast, idempotent).
          2. Check if any tables already exist (existing install detection).
          3. Fresh install → apply db_schema.sql (all IF NOT EXISTS, ordered correctly).
          4. Existing install → mark schema_base_v1 done without re-running DDL.
          5. Seed built-in data (agent roles, system roles, tag categories).
        """
        # Step 1: create version tracking table (prerequisite for all checks)
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS mng_schema_version (
                    version    VARCHAR(100) PRIMARY KEY,
                    applied_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
                )
            """)
        conn.commit()

        # Step 2: check if this is a fresh install or an existing one
        if not _Database._migration_applied(conn, "schema_base_v1"):
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'public' AND table_name = 'mng_clients'
                    )
                """)
                existing_install = cur.fetchone()[0]

            if existing_install:
                # Existing install — tables already in place; just mark the base done
                _Database._record_migration(conn, "schema_base_v1")
                log.debug("⏩ existing install — schema_base_v1 pre-marked, skipping DDL")
            else:
                # Fresh install — apply the full canonical schema
                _Database._run_ddl_statements(conn, _SCHEMA_SQL_PATH.read_text(), "db_schema.sql")
                _Database._record_migration(conn, "schema_base_v1")
                log.info("✅ fresh install — db_schema.sql applied")

        # Step 5: seed built-in data (idempotent ON CONFLICT DO NOTHING/UPDATE)
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
        """Apply pending data migrations from db_migrations.py.

        Called after _ensure_schema(). Applies only migrations whose version
        strings are not yet recorded in mng_schema_version — so each migration
        runs exactly once regardless of how many times the backend restarts.

        To add a migration: define a function in db_migrations.py and append
        it to the MIGRATIONS list with a unique version string.
        """
        if self._shared_schema_ready:
            return

        from core.db_migrations import MIGRATIONS
        for version, up_fn in MIGRATIONS:
            if _Database._migration_applied(conn, version):
                log.debug(f"⏩ skipping migration {version} (already applied)")
            else:
                log.info(f"▶  applying migration {version}")
                try:
                    up_fn(conn)
                    _Database._record_migration(conn, version)
                    log.info(f"✅ migration {version} applied")
                except Exception as mig_err:
                    # Roll back the failed migration transaction so the DB stays clean.
                    # Do NOT re-raise — DB remains fully available and the migration
                    # will be retried on next restart (it won't be recorded as applied).
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                    log.warning(
                        f"⚠  migration {version} failed (will retry on next restart): "
                        f"{mig_err!s:.200}"
                    )

        self._shared_schema_ready = True
        log.info("✅ schema ready (mem_mrr_* | planner_* | mem_ai_* | pr_*)")
    # ── Seeding ────────────────────────────────────────────────────────────────

    @staticmethod
    def _seed_agent_roles(conn) -> None:
        """Upsert all agent roles from workspace/_templates/pipelines/roles/*.yaml.

        Uses DO UPDATE so improved prompts take effect on server restart.
        """
        try:
            with conn.cursor() as cur:
                _Database._seed_roles_from_yaml(cur)
            conn.commit()
            log.debug("✅ Agent roles seeded")
        except Exception as e:
            conn.rollback()
            log.warning(f"Agent roles seed skipped: {e}")

    @staticmethod
    def _seed_roles_from_yaml(cur) -> None:
        """Full UPSERT of agent roles from workspace/_templates/pipelines/roles/*.yaml into DB.

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
            / "workspace" / "_templates" / "pipelines" / "roles"
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
                "- Memory AI layer: prefix `mem_ai_` (e.g. mem_ai_project_facts)\n"
                "- Work items (use cases, features, bugs): table `mem_work_items`\n"
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
            ("use_case",     "#06b6d4", "◻",  "Use case — organised requirement set (UC 10000+)"),
            ("feature",      "#22c55e", "⚡", "New functionality (F 20000+)"),
            ("bug",          "#ef4444", "🐛", "Defect or unexpected behaviour (B 30000+)"),
            ("task",         "#3b82f6", "✓",  "Process or maintenance work"),
            ("design",       "#a855f7", "◈",  "Architecture or UX design"),
            ("decision",     "#f59e0b", "⚑",  "Architectural or product decision"),
            ("meeting",      "#6b7280", "◷",  "Meeting summary"),
            ("policy",       "#8b5cf6", "⚑",  "Mandatory rule or standard (PO 5000+)"),
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


