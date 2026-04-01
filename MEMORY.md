# Project Memory — aicli
_Generated: 2026-04-01 18:06 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining Claude CLI integration with a desktop Electron UI for managing AI-augmented development workflows. It uses PostgreSQL with pgvector for semantic search, FastAPI backend with JWT auth, and async DAG-based pipeline execution with Cytoscape visualization. Current focus is on refactoring memory file generation to read feature details from planner_tags inline snapshot fields rather than separate relations tables, improving SQL cursor handling consistency, and maintaining robust data persistence across session switches.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: SQL
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude_CLI_and_LLM_platforms
- **email_verification_integration**: incremental_enhancement_to_existing_signin_register_forms
- **mcp_integration**: embedding_and_data_retrieval_for_work_item_management
- **memory_endpoint_template_variable_scoping**: code_dir_variable_fixed_at_line_1120
- **memory_management_pattern**: load_once_on_access_update_on_save
- **pending_implementation**: memory_items_and_project_facts_table_population
- **pending_issues**: project_visibility_bug_active_project_not_displaying
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
- **sql_performance_strategy**: redundant_calls_eliminated_load_once_pattern
- **stale_code_removed**: db_ensure_project_schema_call_replaced_with_ensure_shared_schema
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
- **storage_primary**: PostgreSQL 15+
- **storage_semantic**: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small)
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku), OpenAI, DeepSeek, Gemini, Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **config_management**: config.py + YAML pipelines + pyproject.toml
- **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
- **pipeline_engine**: Async DAG executor (asyncio.gather for parallel nodes) + YAML config; per-node retry/continue logic; centralized under workflows/ with pipeline_ prefix
- **pipeline_ui**: Cytoscape.js + cytoscape-dagre for graph visualization; 2-pane approval panel for chat negotiation
- **billing_storage**: data/provider_storage/ (provider_costs.json); pricing, coupons, user_logs in SQL tables
- **backend_modules**: routers/ for API endpoints, core/ for infrastructure, data/ for data access (dl_ prefix), agents/tools/ for agent implementations (tool_ prefix), agents/mcp/ for MCP server
- **dev_environment**: PyProject.toml + VS Code launch.json; PyCharm: Mark backend/ as Sources Root
- **database**: PostgreSQL 15+
- **node_modules_build**: npm 8+ with Electron-builder; Vite dev server
- **database_version**: PostgreSQL 15+
- **build_tooling**: npm 8+ with Electron-builder; Vite dev server
- **db_consolidation**: mem_ai_events (unified event table with id, project_id, session_id, session_desc, event_summary)
- **db_tables_unified**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **unified_tables**: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
- **deployment_cloud**: Railway (Dockerfile + railway.toml)
- **deployment_desktop**: Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb)
- **deployment_local**: bash start_backend.sh + ui/npm run dev

## Key Decisions

- Engine/workspace separation: aicli/ backend logic; workspace/ per-project content; _system/ project state and memory files
- Dual storage model: PostgreSQL 15+ with pgvector (1536-dim, text-embedding-3-small) for semantic search; unified mem_ai_* tables (events, tags_relations, project_facts, work_items, features)
- Electron desktop UI: Vanilla JS (no framework/bundler) + xterm.js + Monaco editor + Cytoscape.js + cytoscape-dagre; Vite dev server for local development
- JWT authentication (python-jose + bcrypt) with DEV_MODE toggle; hierarchical data model: Clients → Users with login_as_first_level_hierarchy pattern
- LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) as independent modules; Claude Haiku for dual-layer memory synthesis generating 5 output files
- Async DAG workflow executor via asyncio.gather with loop-back, max_iterations cap; Cytoscape.js visualization with 2-pane approval panel for chat negotiation
- Memory synthesis: Claude Haiku generates CLAUDE.md, MEMORY.md, context.md, rules.md, copilot.md from mem_ai_project_facts and mem_ai_work_items with timestamp tracking
- _ensure_shared_schema pattern for initialization; retry logic handles empty project list on first load
- Data persistence: load_once_on_access, update_on_save pattern; tags stored in mem_ai_tags_relations with row ID linking, not in summary arrays
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations (depends_on, relates_to, blocks, implements) via CLI/admin UI
- Backend: FastAPI + uvicorn + python-jose + bcrypt + psycopg2; routers/, core/, data/ (dl_ prefix), agents/tools/ (tool_ prefix), agents/mcp/ for MCP server
- Memory file generation reads snapshot data from inline planner_tags fields (summary, action_items, design, code_summary); mem_ai_tags_relations relations section omitted
- Per-feature CLAUDE.md auto-loaded when Claude enters features/{tag}/ directory; tag retrieval returns (id, name, status, short_desc, priority, due_date)
- Deployment: Railway (Dockerfile + railway.toml) for cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local via bash start_backend.sh + ui/npm run dev
- Config management: config.py with externalized settings; YAML for pipeline definitions; pyproject.toml for IDE support; billing storage in data/provider_storage/

## In Progress

- Memory file generation refactoring: feature_details context loaded from planner_tags inline fields; _SQL_ACTIVE_TAGS query fixed to return tag names from column index [1]; per-feature CLAUDE.md rendering improved with snapshot data integration
- Schema consolidation: mem_ai_tags_relations relations section removed from feature rendering; inline snapshot fields (summary, action_items, design, code_summary) now primary data source for feature details
- SQL cursor tuple unpacking: memory_promotion.py _SQL_GET_CURRENT_FACTS fixed to unpack 4 columns instead of 5; memory_files.py active tags query corrected to read name from proper result index
- Memory file lifecycle: get_active_feature_tags() now correctly filters active/open tags with snapshots; render_feature_claude_md() enhanced to read complete tag metadata including requirements and short_desc
- Feature details context loading: planner_tags query limits to 30 most recent tags with embedding or summary; context dict populated with id, name, short_desc, requirements, summary, action_items, design, code_summary
- Database cursor handling robustness: standardized tuple unpacking across memory_promotion.py and memory_files.py; improved documentation of SQL result column ordering in get_active_feature_tags() method

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `role` — 2026-04-01

## Output

Always output structured JSON with score (1-10), approved (bool), issues (list), summary.
Score >= 8 → approved. No critical issues → approved regardless of minor issues.


### `commit` — 2026-04-01

diff --git a/backend/memory/memory_promotion.py b/backend/memory/memory_promotion.py
index 8ef97c0..24af97f 100644
--- a/backend/memory/memory_promotion.py
+++ b/backend/memory/memory_promotion.py
@@ -290,7 +290,7 @@ class MemoryPromotion:
         with db.conn() as conn:
             with conn.cursor() as cur:
                 cur.execute(_SQL_GET_CURRENT_FACTS, (project,))
-                for f_id, f_key, f_val, _, _ in cur.fetchall():
+                for f_id, f_key, f_val, _ in cur.fetchall():
                     facts_context[f_key] = f_val
 
         # Group events by source type (all 6 batch types)


### `commit` — 2026-04-01

diff --git a/backend/memory/memory_files.py b/backend/memory/memory_files.py
index cd4ae20..3b37e5e 100644
--- a/backend/memory/memory_files.py
+++ b/backend/memory/memory_files.py
@@ -219,6 +219,29 @@ class MemoryFiles:
                     cur.execute(_SQL_BLOCKED_TAGS, (project,))
                     ctx["blocked_tags"] = [(r[1], r[3] or "") for r in cur.fetchall()]
 
+                    # Feature details: tags with embedding or summary (inline fields)
+                    cur.execute("""
+                        SELECT t.id, t.name, t.short_desc, t.requirements, t.summary,
+                               t.action_items, t.design, t.code_summary
+                        FROM planner_tags t
+                        WHERE t.project = %s
+                          AND (t.embedding IS NOT NULL OR t.summary IS NOT NULL)
+                        ORDER BY t.updated_at DESC LIMIT 30
+                    """, (project,))
+                    ctx["feature_details"] = [
+                        {
+                            "id":           str(r[0]),
+                            "name":         r[1] or "",
+                            "short_desc":   r[2] or "",
+                            "requirements": r[3] or "",
+                            "summary":      r[4] or "",
+                            "action_items": r[5] or "",
+                            "design":       r[6] or {},
+                            "code_summary": r[7] or {},
+                        }
+                        for r in cur.fetchall()
+                    ]
+
         except Exception as e:
             log.warning(f"MemoryFiles._load_context error for '{project}': {e}")
 
@@ -247,14 +270,15 @@ class MemoryFiles:
             return []
 
     def get_active_feature_tags(self, project: str) -> list[str]:
-        """Return tag names for active features that have snapshots."""
+        """Return tag names for active/open tags (active features that have snapshots)."""
         if not db.is_available():
             return []
         try:
             with db.conn() as conn:
                 with conn.cursor() as cur:
                     cur.execute(_SQL_ACTIVE_TAGS, (project,))
-                    return [r[0] for r in cur.fetchall()]
+                    # _SQL_ACTIVE_TAGS returns (id, name, status, short_desc, priority, due_date)
+                    return [r[1] for r in cur.fetchall()]
         except Exception:
             return []
 
@@ -366,36 +390,43 @@ class MemoryFiles:
         return "\n".join(lines)
 
     def render_feature_claude_md(self, project: str, tag_name: str) -> str:
-        """Render per-feature CLAUDE.md — auto-loaded when Claude enters features/{tag}/ dir."""
+        """Render per-feature CLAUDE.md — auto-loaded when Claude enters features/{tag}/ dir.
+
+        Reads snapshot data (summary, action_items, design, code_summary) from inline
+        planner_tags fields. Relations section is omitted since mem_ai_tags_relations is dropped.
+        """
         if not db.is_available():
             return f"# Feature: {tag_name}\n_No database available._\n"
 
-        snap = {}
-        relations = []
+        snap: dict = {}
         try:
             with db.conn() as conn:
                 with conn.cursor() as cur:
-                    cur.execute(_SQL_FEATURE_SNAPSHOT_BY_TAG, (project, tag_name))
+                    # Look up tag by name to get its id, then read inline snapshot fields
+                    cur.execute("""
+                        SELECT t.id, t.name, t.project, t.requirements, t.summary,
+                               t.action_items, t.design, t.code_summary, t.short_desc
+                        FROM planner_tags t
+                        WHERE t.project = %s AND t.name = %s
+                        LIMIT 1
+                    """, (project, tag_name))
                     row = cur.fetchone()
                     if row:
                         snap = {
-                            "requirements":

### `role` — 2026-04-01

## Minor Issues (note but don't block)
- Style inconsistencies with the existing codebase
- Missing type hints on new code
- Missing docstrings on public functions
- Overly verbose variable names


### `role` — 2026-04-01

## Critical Issues (block approval)
- Logic bugs that will cause incorrect behaviour
- Security vulnerabilities (shell injection, path traversal, secret exposure)
- Unhandled exceptions that will crash the program
- Breaking changes to existing interfaces


### `commit` — 2026-04-01

diff --git a/backend/agents/mcp/server.py b/backend/agents/mcp/server.py
index 1b42cd3..7c7ac1f 100644
--- a/backend/agents/mcp/server.py
+++ b/backend/agents/mcp/server.py
@@ -756,9 +756,9 @@ async def _dispatch(name: str, args: dict) -> Any:
         return {
             "naming_convention": {
                 "mng_TABLE": "Global/shared tables (users, billing, roles, tag categories, system prompts)",
-                "planner_TABLE": "Tag hierarchy tables (planner_tags, planner_tags_meta)",
-                "mem_mrr_TABLE": "Mirroring layer — raw source data as-is (prompts, commits, items, messages, tags)",
-                "mem_ai_TABLE": "AI/embedding layer — digests, embeddings, facts, features, work items",
+                "planner_TABLE": "Tag hierarchy tables (planner_tags)",
+                "mem_mrr_TABLE": "Mirroring layer — raw source data as-is (prompts, commits, items, messages)",
+                "mem_ai_TABLE": "AI/embedding layer — digests, embeddings, facts, work items",
                 "pr_TABLE": "Graph workflow tables (pr_graph_*)",
                 "filter": "All tables use client_id=1 AND project=<name> for isolation",
             },
@@ -782,23 +782,39 @@ async def _dispatch(name: str, args: dict) -> Any:
                     "purpose": "Memory pipeline prompts editable from UI (commit_digest, prompt_batch_digest, etc.)",
                     "key_columns": ["id SERIAL PK", "client_id INT", "name TEXT", "content TEXT", "is_active BOOLEAN"],
                 },
-                "mng_ai_tags_relations": {
-                    "purpose": "Directed relationships between planner_tags (depends_on, blocks, relates_to, etc.)",
-                    "key_columns": ["id UUID PK", "from_tag_id FK→planner_tags", "relation TEXT",
-                                    "to_tag_id FK→planner_tags", "note TEXT", "source (manual|ai_snapshot)"],
-                },
             },
             "tagging_tables": {
                 "planner_tags": {
-                    "purpose": "Per-project tag hierarchy (features, bugs, tasks, components)",
-                    "key_columns": ["id UUID PK", "client_id INT", "project TEXT", "name TEXT",
-                                    "description TEXT", "category_id FK→mng_tags_categories",
-                                    "parent_id FK→self", "UNIQUE(client_id, project, name)"],
+                    "purpose": "Per-project tag hierarchy (features, bugs, tasks, components) with inline metadata",
+                    "key_columns": [
+                        "id UUID PK", "client_id INT FK", "project TEXT", "name TEXT",
+                        "category_id INT FK mng_tags_categories",
+                        "parent_id UUID FK self", "merged_into UUID FK self", "seq_num INT",
+                        "source TEXT DEFAULT 'user'", "creator TEXT", "short_desc TEXT", "full_desc TEXT",
+                        "requirements TEXT", "acceptance_criteria TEXT",
+                        "status TEXT DEFAULT 'open'  -- open|active|done|archived",
+                        "priority SMALLINT DEFAULT 3", "due_date DATE", "requester TEXT", "extra JSONB",
+                        "summary TEXT", "action_items TEXT", "design JSONB", "code_summary JSONB",
+                        "is_reusable BOOLEAN", "embedding VECTOR(1536)",
+                        "created_at TIMESTAMPTZ", "updated_at TIMESTAMPTZ",
+                        "UNIQUE(client_id, project, name, category_id)",
+                    ],
                     "filter": "WHERE client_id=1 AND project=%s",
                 },
-                "planner_tags_meta": {
-                    "purpose": "Key-value metadata for planner_tags",
-                    "key_columns": ["tag_id FK→planner_tags", "meta_key TEXT", "meta_value TEXT"],
+                "mem_tags_relations": {
+                    "purpose": "Links planner_tags to raw source rows (mirror layer) or AI-inferred events",
+                    "key_columns": [
+            

## AI Synthesis

**2026-03-14** `backend/memory/memory_files.py` — Feature details context loading enhanced: planner_tags query now retrieves inline snapshot fields (summary, action_items, design, code_summary) for up to 30 most recent tags, replacing reliance on deprecated mem_ai_tags_relations relations.

**2026-03-14** `backend/memory/memory_promotion.py` — Fixed SQL cursor tuple unpacking in _SQL_GET_CURRENT_FACTS: reduced from 5 to 4 column unpack to match actual query result, preventing IndexError in facts_context population.

**2026-03-14** `backend/memory/memory_files.py` — Corrected get_active_feature_tags() method: now reads tag name from column index [1] instead of [0], properly handling result tuple structure (id, name, status, short_desc, priority, due_date).

**2026-03-14** `backend/memory/memory_files.py` — Redesigned render_feature_claude_md() to read per-feature snapshot data directly from planner_tags inline fields; mem_ai_tags_relations relations section removed from output as part of schema consolidation.

**2026-03-14** `backend/memory/memory_files.py` — Enhanced _load_context() to populate feature_details dict with complete tag metadata including id, name, short_desc, requirements, summary, action_items, design, and code_summary for use in memory file generation.

**Prior** `core architectural pattern` — Unified event table (mem_ai_events) consolidation completed; backend startup race condition resolved with retry logic; tag persistence bug fixed via mem_ai_tags_relations row ID linking and proper cache invalidation.