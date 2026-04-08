# Project Memory — aicli
_Generated: 2026-04-08 22:52 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python CLI backend (FastAPI + PostgreSQL + pgvector embeddings) with an Electron desktop UI (Vanilla JS + xterm.js + Cytoscape.js) for collaborative AI-assisted development. Core features include 4-layer memory synthesis (Claude Haiku dual-layer summarization), semantic search via embeddings, async DAG workflow execution with visual approval panels, MCP server integration for tool access, and billing/usage tracking across multiple LLM providers. Currently stabilizing schema management (canonical db_schema.sql + migration framework), fixing planner tag UI visibility, and optimizing work item query performance.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **code_extraction_configuration**: min_lines: 5 (per-symbol threshold), min_diff_lines: 5 (commit-level threshold), only_on_commits_with_tags: false
- **commit_processing_flag**: exec_llm boolean column replaces tags->>'llm' NULL check
- **commit_tracking_schema**: mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: PostgreSQL with SQL parameter binding
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude CLI and LLM platforms
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **known_bug_active**: planner_tag_visibility: categories upload but individual tags don't display in UI bindings
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **memory_system_update_status**: updated_with_latest_context_and_session_tags
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
- **performance_issue_active**: route_work_items latency ~60s; investigating _SQL_UNLINKED_WORK_ITEMS indexing and mem_ai_events join optimization
- **performance_optimization**: redundant_SQL_calls_eliminated
- **pipeline/auth**: Acceptance criteria:
# PM Analysis: Email Verification Feature

---

## Context Summary

The tagged context reveals this work item is an **incremental enhancement** to an existing authentication system. Sign In and Create Account forms are already live and functional. The prior PM analysis identified email verification as the missing layer—the system currently accepts any email without confirming ownership. The analys

Reviewer: ```json
{
  "passed": false,
  "score": 4,
  "issues": [
    "Implementation is incomplete — cuts off mid-file in EmailService.ts without finishing AWS SES client setup, email template loading, or the
- **prompt_loading_pattern**: core.prompt_loader._prompts.content() replaces direct mng_system_roles queries
- **rel:commit_processing:exec_llm_flag**: replaces
- **rel:memory_system:session_tags**: implements
- **rel:prompt_loader:mng_system_roles**: replaces
- **rel:route_memory:prompt_loader**: depends_on
- **rel:route_memory:sql_parameter_binding**: depends_on
- **rel:route_prompts:memory_embedding**: depends_on
- **rel:route_search:memory_embedding**: depends_on
- **rel:route_snapshots:prompt_loader**: depends_on
- **rel:route_work_items:sql_parameter_binding**: depends_on
- **route_work_items_sql_errors**: line_249_cur_execute_missing_parameter_binding_line_288_incomplete_column_selection_in_merged_query
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: git_supervisor_module_deleted_automated_git_workflow_no_longer_used
- **tagging_system**: nested_hierarchy_beyond_2_levels
- **tagging_system_hierarchy**: nested_hierarchy_beyond_2_levels_approved
- **ui_action_menu_pattern**: 3_dot_menu_for_action_visibility
- **ui_library**: 3_dot_menu_pattern
- **unimplemented_features**: memory_items_and_project_facts_tables_not_updating
- **unresolved_issues**: memory_endpoint_template_variable_scoping_and_backend_startup_race_condition

## Tech Stack

- **cli**: Python 3.12 + prompt_toolkit + rich
- **backend**: FastAPI + uvicorn + python-jose + bcrypt + psycopg2
- **frontend**: Vanilla JS (no framework, no bundler) + Electron shell + Vite dev server
- **ui_components**: xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre
- **storage_primary**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Mirror: mem_mrr_commits_code (19 columns, full_symbol generated); Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json) + SQL pricing/coupon tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+ with JSONB UNION batch upsert queries
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + npm run dev
- **prompt_management**: core.prompt_loader module with centralized prompt caching
- **schema_management**: db_schema.sql (single source of truth) + db_migrations.py (safe rename/recreate/copy pattern)

## Key Decisions

- Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files
- Dual storage: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules with send(prompt, system) → str contract
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js; Vite dev server for local development
- Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- 4-layer memory architecture: ephemeral session messages → mem_mrr_* raw capture → mem_ai_events LLM digests + embeddings → mem_ai_work_items/project_facts → user-managed planner_tags
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; mem_mrr_commits_code includes 19 columns with full_symbol as generated column
- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)
- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; routes load prompts from configuration

## In Progress

- Planner tag UI binding fix: resolved `catName` ReferenceError in _renderDrawer() (scope issue) and corrected field mismatch v.short_desc → v.desc for proper tag property display on left sidebar
- Database schema canonicalization: consolidated all DDL into db_schema.sql as single source of truth with migration framework in db_migrations.py (rename → recreate → copy pattern); legacy ALTER TABLE statements now tracked as migrations m001-m017
- Prompt loader integration: refactoring route_snapshots.py and route_memory.py to use core.prompt_loader instead of direct mng_system_roles queries to eliminate redundant database lookups
- Commit pipeline prompt discovery: tracing all LLM prompts in memory_embedding.py, agents/tools/, and routers for unified prompt management and cost tracking
- Memory endpoint data flow verification: synchronizing mirror tables (mem_mrr_commits_code) through mem_ai_events and downstream memory tables with consistent module imports
- Database query performance: investigating ~60s latency in route_work_items query (_SQL_UNLINKED_WORK_ITEMS join optimization and indexing)

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **high-level-design** `[open]`
- **architecture-decision** `[open]`
- **customer-meeting** `[open]`
- **Test** `[open]`
- **retrospective** `[open]`
- **low-level-design** `[open]`

### Feature

- **pagination**
- **graph-workflow** `[open]`
- **billing** `[open]`
- **embeddings** `[open]`
- **tagging** `[open]`
- **mcp** `[open]`
- **workflow-runner** `[open]`
- **test-picker-feature** `[open]`
- **UI** `[open]`
- **auth** `[open]`
- **dropbox** `[open]`
- **shared-memory** `[open]`

### Phase

- **discovery** `[open]`
- **prod** `[open]`
- **development** `[open]`

### Task

- **memory** `[open]`
- **implement-projects-tab** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/core/db_schema.sql b/backend/core/db_schema.sql
new file mode 100644
index 0000000..b7c4f67
--- /dev/null
+++ b/backend/core/db_schema.sql
@@ -0,0 +1,628 @@
+-- ============================================================================
+-- aicli Database Schema — Canonical Latest Version
+-- Updated: 2026-04-08
+-- ============================================================================
+-- This file is the SINGLE SOURCE OF TRUTH for all table structures.
+-- Rules:
+--   1. Always use CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.
+--   2. Every ALTER TABLE ever applied must be merged into the CREATE TABLE here.
+--   3. Schema changes update THIS file AND add a migration entry in db_migrations.py.
+--   4. No raw ALTER TABLE here — fresh installs read this file; migrations handle upgrades.
+-- ============================================================================
+
+CREATE EXTENSION IF NOT EXISTS vector;
+
+-- ============================================================================
+-- SECTION 1: mng_* — Global / Client-scoped Management Tables
+-- ============================================================================
+
+-- mng_schema_version: tracks which migrations have been applied
+-- Must be created before anything else so migration checks work on first run
+CREATE TABLE IF NOT EXISTS mng_schema_version (
+    version    VARCHAR(100) PRIMARY KEY,
+    applied_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
+);
+
+-- mng_clients: top-level tenants (local install always has id=1)
+CREATE TABLE IF NOT EXISTS mng_clients (
+    id                SERIAL       PRIMARY KEY,
+    slug              VARCHAR(50)  UNIQUE NOT NULL,
+    name              VARCHAR(255) NOT NULL DEFAULT '',
+    plan              VARCHAR(20)  NOT NULL DEFAULT 'free',
+    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
+    pricing_config    JSONB        DEFAULT NULL,
+    provider_costs    JSONB        DEFAULT NULL,
+    provider_balances JSONB        DEFAULT NULL,
+    server_api_keys   JSONB        DEFAULT NULL
+);
+INSERT INTO mng_clients (id, slug, name, plan)
+VALUES (1, 'local', 'Local Install', 'free')
+ON CONFLICT (slug) DO NOTHING;
+
+-- mng_users: user accounts (per client)
+CREATE TABLE IF NOT EXISTS mng_users (
+    id                 VARCHAR(36)    PRIMARY KEY,
+    client_id          INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
+    email              VARCHAR(255)   UNIQUE NOT NULL,
+    password_hash      TEXT           NOT NULL,
+    is_admin           BOOLEAN        NOT NULL DEFAULT FALSE,
+    is_active          BOOLEAN        NOT NULL DEFAULT TRUE,
+    created_at         TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
+    last_login         TIMESTAMPTZ,
+    role               VARCHAR(20)    NOT NULL DEFAULT 'free',
+    balance_added_usd  NUMERIC(14, 8) NOT NULL DEFAULT 0,
+    balance_used_usd   NUMERIC(14, 8) NOT NULL DEFAULT 0,
+    coupons_used       TEXT[]         NOT NULL DEFAULT '{}',
+    stripe_customer_id VARCHAR(100)   NOT NULL DEFAULT ''
+);
+CREATE INDEX IF NOT EXISTS idx_users_email  ON mng_users(email);
+CREATE INDEX IF NOT EXISTS idx_users_client ON mng_users(client_id);
+
+-- mng_usage_logs: per-request LLM usage tracking
+CREATE TABLE IF NOT EXISTS mng_usage_logs (
+    id            SERIAL         PRIMARY KEY,
+    user_id       VARCHAR(36)    REFERENCES mng_users(id) ON DELETE SET NULL,
+    provider      VARCHAR(50),
+    model         VARCHAR(100),
+    input_tokens  INTEGER        NOT NULL DEFAULT 0,
+    output_tokens INTEGER        NOT NULL DEFAULT 0,
+    cost_usd      NUMERIC(12, 8) NOT NULL DEFAULT 0,
+    charged_usd   NUMERIC(12, 8) NOT NULL DEFAULT 0,
+    source        VARCHAR(50)    NOT NULL DEFAULT 'request',  -- 'request'|'workflow'|'memory'
+    metadata      JSONB          DEFAULT NULL,
+    period_start  TIMESTAMPTZ    DEFAULT NULL,
+    period_end    TIMESTAMPTZ    DEFAULT NULL,
+    created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
+);
+CREATE INDEX IF NOT EXISTS idx_usage_user_id    ON mng_usage_logs(user_id);
+CREATE INDEX IF NOT EXISTS idx_usage_created_at ON mng_usage_logs(created_at DESC);
+CREATE INDEX IF NOT EXISTS idx_usage_provider   ON mng_usage_logs(provider);
+CREATE INDEX IF NOT EXISTS idx_usage_source     ON mng_usage_logs(source);
+
+-- mng_transactions: billing credit/debit events
+CREATE TABLE IF NOT EXISTS mng_transactions (
+    id            SERIAL         PRIMARY KEY,
+    user_id       VARCHAR(36)    REFERENCES mng_users(id) ON DELETE SET NULL,
+    type          VARCHAR(50)    NOT NULL,
+    amount_usd    NUMERIC(12, 8) NOT NULL DEFAULT 0,
+    base_cost_usd NUMERIC(12, 8),
+    description   TEXT           NOT NULL DEFAULT '',
+    ref           VARCHAR(255)   NOT NULL DEFAULT '',
+    created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
+);
+CREATE INDEX IF NOT EXISTS idx_tx_user_id    ON mng_transactions(user_id);
+CREATE INDEX IF NOT EXISTS idx_tx_created_at ON mng_transactions(created_at DESC);
+CREATE INDEX IF NOT EXISTS idx_tx_type       ON mng_transactions(type);
+
+-- mng_user_api_keys: per-user encrypted provider API keys
+CREATE TABLE IF NOT EXISTS mng_user_api_keys (
+    id         SERIAL      PRIMARY KEY,
+    user_id    VARCHAR(36) NOT NULL REFERENCES mng_users(id) ON DELETE CASCADE,
+    provider   VARCHAR(50) NOT NULL,
+    key_enc    TEXT        NOT NULL,
+    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
+    UNIQUE(user_id, provider)
+);
+CREATE INDEX IF NOT EXISTS idx_muak_user ON mng_user_api_keys(user_id);
+
+-- mng_coupons: discount codes (per client)
+CREATE TABLE IF NOT EXISTS mng_coupons (
+    id          SERIAL         PRIMARY KEY,
+    client_id   INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
+    code        VARCHAR(50)    NOT NULL,
+    amount_usd  NUMERIC(10, 4) NOT NULL DEFAULT 0,
+    max_uses    INT            NOT NULL DEFAULT 1,
+    used_count  INT            NOT NULL DEFAULT 0,
+    used_by     JSONB          NOT N

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/core/db_migrations.py b/backend/core/db_migrations.py
new file mode 100644
index 0000000..87c58a0
--- /dev/null
+++ b/backend/core/db_migrations.py
@@ -0,0 +1,118 @@
+"""
+db_migrations.py — Database migration runner for aicli.
+
+Migration philosophy
+────────────────────
+Each schema change follows a safe rename → recreate → copy pattern:
+
+    1. Rename the old table:  ALTER TABLE foo RENAME TO _bak_{version}_foo
+    2. Create the new table:  the CREATE TABLE from db_schema.sql
+    3. Copy data:             INSERT INTO foo (cols) SELECT cols FROM _bak_{version}_foo
+    4. (Optional) Drop backup after verification
+
+Benefits vs ALTER TABLE ADD COLUMN:
+  - Works for column removals, type changes, and renames (not just additions)
+  - The backup table is a free rollback path
+  - db_schema.sql always reflects the final target shape
+
+FK-dependent tables
+───────────────────
+If table B has a FK → table A, and you need to migrate A:
+    1. Drop the FK constraint from B  (ALTER TABLE B DROP CONSTRAINT fk_name)
+    2. Run migrate_table() on A
+    3. Recreate the FK on B          (ALTER TABLE B ADD CONSTRAINT ...)
+
+Helper usage example
+────────────────────
+    def m018_add_new_column(conn) -> None:
+        migrate_table(
+            conn,
+            old_table   = "mem_ai_work_items",
+            backup_name = "_bak_018_mem_ai_work_items",
+            create_sql  = '''
+                CREATE TABLE mem_ai_work_items (
+                    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
+                    project_id  INT  NOT NULL REFERENCES mng_projects(id) ON DELETE CASCADE,
+                    new_column  TEXT NOT NULL DEFAULT '',
+                    -- ... all other columns from db_schema.sql
+                )
+            ''',
+            copy_columns = [
+                "id", "client_id", "project_id", "ai_category", "ai_name",
+                # list every column that existed BEFORE this migration
+                # new columns get their DEFAULT values automatically
+            ],
+        )
+
+MIGRATIONS list
+───────────────
+Each entry: (version: str, up_fn: Callable[[conn], None])
+Versions must be unique and monotonically increasing.
+Already-applied versions are skipped (tracked in mng_schema_version).
+"""
+from __future__ import annotations
+
+import logging
+from typing import Callable
+
+log = logging.getLogger(__name__)
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# Migration helper
+# ─────────────────────────────────────────────────────────────────────────────
+
+def migrate_table(
+    conn,
+    old_table:    str,
+    backup_name:  str,
+    create_sql:   str,
+    copy_columns: list[str],
+) -> None:
+    """
+    Rename → recreate → copy pattern.
+
+    Args:
+        conn:         psycopg2 connection (autocommit=False, caller controls commit)
+        old_table:    current table name (e.g. 'mem_ai_work_items')
+        backup_name:  name for the renamed backup (e.g. '_bak_018_mem_ai_work_items')
+        create_sql:   full CREATE TABLE statement for the new schema (no IF NOT EXISTS)
+        copy_columns: columns to copy from backup → new table (omit new columns;
+                      they get their DEFAULT values)
+    """
+    cols = ", ".join(copy_columns)
+    with conn.cursor() as cur:
+        log.info(f"migrate_table: renaming {old_table} → {backup_name}")
+        cur.execute(f"ALTER TABLE {old_table} RENAME TO {backup_name}")
+        log.info(f"migrate_table: creating new {old_table}")
+        cur.execute(create_sql)
+        log.info(f"migrate_table: copying {len(copy_columns)} columns from {backup_name}")
+        cur.execute(f"INSERT INTO {old_table} ({cols}) SELECT {cols} FROM {backup_name}")
+    conn.commit()
+    log.info(f"migrate_table: {old_table} migration complete ({backup_name} kept as backup)")
+
+
+# ─────────────────────────────────────────────────────────────────────────────
+# Migration registry
+# ─────────────────────────────────────────────────────────────────────────────
+# Format: list of (version_string, callable(conn) -> None)
+# Migrations are applied in list order; already-applied versions are skipped.
+#
+# HOW TO ADD A MIGRATION:
+#   1. Update db_schema.sql with the new table structure
+#   2. Define a migration function below (name it m{NNN}_description)
+#   3. Append (version, function) to MIGRATIONS
+#   4. Bump version suffix if modifying an existing migration block in database.py
+#
+# Version naming convention: "m{NNN}_{table_slug}"
+# Examples: "m018_add_wi_priority", "m019_rename_fact_key"
+
+MIGRATIONS: list[tuple[str, Callable]] = [
+    # All migrations through m017 (ai_tags column) were applied via the legacy
+    # ALTER TABLE system in database.py and are tracked as:
+    #   pr_tables_v1, memory_infra_v1, memory_infra_alters_v2,
+    #   work_items_alters_v1, commit_code_v1
+    #
+    # Future migrations go here:
+    # ("m018_example", m018_example),
+]


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/core/database.py b/backend/core/database.py
index 130a6f7..b1e8595 100644
--- a/backend/core/database.py
+++ b/backend/core/database.py
@@ -51,1221 +51,10 @@ def _workspace() -> Path:
     return Path(settings.workspace_dir)
 
 
-# ─── DDL: mng_clients ────────────────────────────────────────────────────────
-
-_DDL_CLIENTS = """
-CREATE TABLE IF NOT EXISTS mng_clients (
-    id               SERIAL       PRIMARY KEY,
-    slug             VARCHAR(50)  UNIQUE NOT NULL,
-    name             VARCHAR(255) NOT NULL DEFAULT '',
-    plan             VARCHAR(20)  NOT NULL DEFAULT 'free',
-    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
-    pricing_config    JSONB        DEFAULT NULL,
-    provider_costs    JSONB        DEFAULT NULL,
-    provider_balances JSONB        DEFAULT NULL,
-    server_api_keys   JSONB        DEFAULT NULL
-);
-INSERT INTO mng_clients (id, slug, name, plan) VALUES (1, 'local', 'Local Install', 'free')
-    ON CONFLICT (slug) DO NOTHING;
-"""
-
-# ─── DDL: mng_users / usage_logs / transactions ──────────────────────────────
-
-_DDL_CORE = """
-CREATE TABLE IF NOT EXISTS mng_users (
-    id                 VARCHAR(36)    PRIMARY KEY,
-    client_id          INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
-    email              VARCHAR(255)   UNIQUE NOT NULL,
-    password_hash      TEXT           NOT NULL,
-    is_admin           BOOLEAN        NOT NULL DEFAULT FALSE,
-    is_active          BOOLEAN        NOT NULL DEFAULT TRUE,
-    created_at         TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
-    last_login         TIMESTAMPTZ,
-    role               VARCHAR(20)    NOT NULL DEFAULT 'free',
-    balance_added_usd  NUMERIC(14, 8) NOT NULL DEFAULT 0,
-    balance_used_usd   NUMERIC(14, 8) NOT NULL DEFAULT 0,
-    coupons_used       TEXT[]         NOT NULL DEFAULT '{}',
-    stripe_customer_id VARCHAR(100)   NOT NULL DEFAULT ''
-);
-CREATE INDEX IF NOT EXISTS idx_users_email    ON mng_users(email);
-CREATE INDEX IF NOT EXISTS idx_users_client   ON mng_users(client_id);
-
-CREATE TABLE IF NOT EXISTS mng_usage_logs (
-    id            SERIAL         PRIMARY KEY,
-    user_id       VARCHAR(36)    REFERENCES mng_users(id) ON DELETE SET NULL,
-    provider      VARCHAR(50),
-    model         VARCHAR(100),
-    input_tokens  INTEGER        NOT NULL DEFAULT 0,
-    output_tokens INTEGER        NOT NULL DEFAULT 0,
-    cost_usd      NUMERIC(12, 8) NOT NULL DEFAULT 0,
-    charged_usd   NUMERIC(12, 8) NOT NULL DEFAULT 0,
-    created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
-);
-ALTER TABLE mng_usage_logs ADD COLUMN IF NOT EXISTS source        VARCHAR(50)    NOT NULL DEFAULT 'request';
-ALTER TABLE mng_usage_logs ADD COLUMN IF NOT EXISTS metadata      JSONB          DEFAULT NULL;
-ALTER TABLE mng_usage_logs ADD COLUMN IF NOT EXISTS period_start  TIMESTAMPTZ    DEFAULT NULL;
-ALTER TABLE mng_usage_logs ADD COLUMN IF NOT EXISTS period_end    TIMESTAMPTZ    DEFAULT NULL;
-CREATE INDEX IF NOT EXISTS idx_usage_user_id    ON mng_usage_logs(user_id);
-CREATE INDEX IF NOT EXISTS idx_usage_created_at ON mng_usage_logs(created_at DESC);
-CREATE INDEX IF NOT EXISTS idx_usage_provider   ON mng_usage_logs(provider);
-CREATE INDEX IF NOT EXISTS idx_usage_source     ON mng_usage_logs(source);
-
-CREATE TABLE IF NOT EXISTS mng_transactions (
-    id            SERIAL         PRIMARY KEY,
-    user_id       VARCHAR(36)    REFERENCES mng_users(id) ON DELETE SET NULL,
-    type          VARCHAR(50)    NOT NULL,
-    amount_usd    NUMERIC(12, 8) NOT NULL DEFAULT 0,
-    base_cost_usd NUMERIC(12, 8),
-    description   TEXT           NOT NULL DEFAULT '',
-    ref           VARCHAR(255)   NOT NULL DEFAULT '',
-    created_at    TIMESTAMPTZ    NOT NULL DEFAULT NOW()
-);
-CREATE INDEX IF NOT EXISTS idx_tx_user_id    ON mng_transactions(user_id);
-CREATE INDEX IF NOT EXISTS idx_tx_created_at ON mng_transactions(created_at DESC);
-CREATE INDEX IF NOT EXISTS idx_tx_type       ON mng_transactions(type);
-"""
-
-# ─── DDL: mng_user_api_keys ──────────────────────────────────────────────────
-
-_DDL_USER_API_KEYS = """
-CREATE TABLE IF NOT EXISTS mng_user_api_keys (
-    id         SERIAL      PRIMARY KEY,
-    user_id    VARCHAR(36) NOT NULL REFERENCES mng_users(id) ON DELETE CASCADE,
-    provider   VARCHAR(50) NOT NULL,
-    key_enc    TEXT        NOT NULL,
-    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
-    UNIQUE(user_id, provider)
-);
-CREATE INDEX IF NOT EXISTS idx_muak_user ON mng_user_api_keys(user_id);
-"""
-
-# ─── DDL: mng_coupons ────────────────────────────────────────────────────────
-
-_DDL_COUPONS = """
-CREATE TABLE IF NOT EXISTS mng_coupons (
-    id          SERIAL         PRIMARY KEY,
-    client_id   INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
-    code        VARCHAR(50)    NOT NULL,
-    amount_usd  NUMERIC(10, 4) NOT NULL DEFAULT 0,
-    max_uses    INT            NOT NULL DEFAULT 1,
-    used_count  INT            NOT NULL DEFAULT 0,
-    used_by     JSONB          NOT NULL DEFAULT '[]',
-    description TEXT           NOT NULL DEFAULT '',
-    expires_at  TIMESTAMPTZ    DEFAULT NULL,
-    created_by  VARCHAR(255)   NOT NULL DEFAULT 'admin',
-    created_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW()
-);
-CREATE UNIQUE INDEX IF NOT EXISTS idx_mcp_client_code ON mng_coupons(client_id, code);
-CREATE INDEX IF NOT EXISTS idx_mcp_client ON mng_coupons(client_id);
-"""
-
-# ─── DDL: mng_* entity + session + role tables ───────────────────────────────
-
-_DDL_MNG_TABLES = """
--- mng_projects: one row per project (replaces project TEXT partition key everywhere)
-CREATE TABLE IF NOT EXISTS mng_projects (
-    id                  SERIAL         PRIMARY KEY,
-    client_id           INT            NOT NULL DEFAULT 1 REFERENCES mng_clients(id),
-    name                VARCHAR(255)   NOT NULL,
-    description         TEXT           NOT NULL DEFAULT '',
-    workspace_path      TEXT,
-    code_dir            TEXT,
-    default_p

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index bafb031..6329a63 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-08 18:31 UTC
+> Generated by aicli 2026-04-08 18:43 UTC
 
 # aicli — Shared AI Memory Platform
 


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 164f73e..ceb4548 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 18:31 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 18:43 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -65,8 +65,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-08] I do not see any update at the database
 - [2026-04-08] yes please
 - [2026-04-08] can you explain where are the  prompts that used for update new commit ?
 - [2026-04-08] Can you explain how commit data statitics are connected to work_items ? Is there is a way to know how many rows/promtps 
-- [2026-04-08] three is link from prompts to commits. each five prompts summeries to event, which meand in this action also all related
\ No newline at end of file
+- [2026-04-08] three is link from prompts to commits. each five prompts summeries to event, which meand in this action also all related
+- [2026-04-08] There is a problem to load work_items - line 331 in route_work_items -column w.ai_tags does not exist
\ No newline at end of file


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/.ai/rules.md b/.ai/rules.md
index 164f73e..ceb4548 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 18:31 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-08 18:43 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -65,8 +65,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-08] I do not see any update at the database
 - [2026-04-08] yes please
 - [2026-04-08] can you explain where are the  prompts that used for update new commit ?
 - [2026-04-08] Can you explain how commit data statitics are connected to work_items ? Is there is a way to know how many rows/promtps 
-- [2026-04-08] three is link from prompts to commits. each five prompts summeries to event, which meand in this action also all related
\ No newline at end of file
+- [2026-04-08] three is link from prompts to commits. each five prompts summeries to event, which meand in this action also all related
+- [2026-04-08] There is a problem to load work_items - line 331 in route_work_items -column w.ai_tags does not exist
\ No newline at end of file


## AI Synthesis

**[2026-04-08]** `bug-fix` — Fixed critical planner tag UI binding: `catName` reference error in `_renderDrawer()` (parameter scope issue) preventing left sidebar property display; also corrected field name `v.short_desc` → `v.desc` for proper tag metadata rendering. **[2026-04-08]** `refactor` — Established db_schema.sql as canonical single source of truth for all table structures with migration framework (db_migrations.py) using safe rename → recreate → copy pattern; consolidated legacy ALTER TABLE statements into tracked migrations m001-m017. **[2026-04-08]** `in-progress` — Refactoring routes to use centralized core.prompt_loader instead of direct mng_system_roles queries, eliminating redundant database roundtrips for prompt management. **[2026-04-08]** `infra` — Tracing all LLM prompts across commit pipeline (memory_embedding.py, agents/tools, routers) to unify prompt management and cost tracking. **[2026-04-08]** `performance` — Investigating ~60s latency in route_work_items from unlinked work items query; focusing on _SQL_UNLINKED_WORK_ITEMS join optimization and index coverage. **[2026-04-08]** `design` — Confirmed 4-layer memory architecture (session messages → raw mem_mrr → LLM digests in mem_ai → work items → user tags) with session ordering by created_at to prevent tag-update reordering.