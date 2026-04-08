# Project Memory — aicli
_Generated: 2026-04-08 13:30 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python 3.12 CLI backend with FastAPI, PostgreSQL 15+ with pgvector, and a vanilla JS Electron desktop UI for managing AI-assisted project workflows. It implements a 4-layer memory architecture (ephemeral → raw capture → LLM digests → semantic work items) with async DAG workflow execution, multi-provider LLM support (Claude/OpenAI/DeepSeek/Gemini/Grok), and an MCP server for semantic search and work item management. Current focus is stabilizing commit code extraction schema and optimizing database query performance for work item retrieval.

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
- **memory_system_update_status**: updated_with_latest_context_and_session_tags
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
- **rel:memory_system:session_tags**: implements
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
- **db_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
- **authentication**: JWT (python-jose + bcrypt) + DEV_MODE toggle
- **llm_providers**: Claude (Haiku/Sonnet/Opus) + OpenAI (GPT-4/mini) + DeepSeek + Gemini + Grok
- **workflow_engine**: Async DAG executor (asyncio.gather) + YAML config + per-node retry/continue logic
- **workflow_ui**: Cytoscape.js + cytoscape-dagre; 2-pane approval panel
- **memory_synthesis**: Claude Haiku dual-layer with 5 output files + timestamp tracking + LLM response summarization
- **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
- **mcp**: Stdio MCP server with 12+ tools for semantic search and work item management
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Mirror: mem_mrr_commits, mem_mrr_commits_code; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
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
- Commit processing: mem_mrr_commits tracks exec_llm=FALSE flag for unprocessed commits; Haiku digest + embedding backpropagates summary and sets exec_llm=TRUE
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
- Stdio MCP server with 12+ tools for semantic search and work item management; embedding pipeline triggered via /memory endpoint
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag updates
- Deployment: Railway for cloud (Dockerfile + railway.toml); Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb)

## In Progress

- Commit code extraction schema finalization: mem_mrr_commits_code table with 19 columns including generated full_symbol column for semantic indexing; DDL migration applied after lock issue resolution
- Embed commits endpoint migration: switching from tags->'llm' IS NULL to exec_llm=FALSE boolean flag for tracking processed commits; backpropagating summary on mem_mrr_commits
- Database query performance optimization: route_work_items showing ~60s round-trip latency; investigating indexing strategy for _SQL_UNLINKED_WORK_ITEMS and join operations
- Commit table schema clarification: investigating mem_ai_commits columns (diff_summary, diff_details) and their usage in event linkage and embedding workflows
- Project ID resolution in embed_commits: ensuring project parameter uses project_id instead of project string in database queries
- Memory flow documentation: tracing data flow from mirror tables through mem_ai_* tables; identifying triggers and update mechanisms for each mirror table

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

diff --git a/workspace/_templates/python_api/project.yaml b/workspace/_templates/python_api/project.yaml
index 9fff36c..310d1d6 100644
--- a/workspace/_templates/python_api/project.yaml
+++ b/workspace/_templates/python_api/project.yaml
@@ -5,3 +5,6 @@ default_provider: claude
 active_workflows:
   - build_feature
   - code_review
+commit_code_extraction:
+  min_lines: 5
+  only_on_commits_with_tags: false


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/workspace/_templates/blank/project.yaml b/workspace/_templates/blank/project.yaml
index 2a79137..2b98de9 100644
--- a/workspace/_templates/blank/project.yaml
+++ b/workspace/_templates/blank/project.yaml
@@ -3,3 +3,6 @@ description: "Project created from blank template"
 code_dir: "../../{{PROJECT_NAME}}"
 default_provider: claude
 active_workflows: []
+commit_code_extraction:
+  min_lines: 5
+  only_on_commits_with_tags: false


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_memory.py b/backend/routers/route_memory.py
index ea38661..91f113b 100644
--- a/backend/routers/route_memory.py
+++ b/backend/routers/route_memory.py
@@ -375,9 +375,9 @@ async def embed_commits(
 ):
     """Run process_commit() for commits that have no Haiku digest yet.
 
-    Selects commits where tags->>'llm' IS NULL (never processed), runs Haiku
-    digest + embedding for each, back-propagates summary and llm tag to
-    mem_mrr_commits. Returns count processed.
+    Selects commits where exec_llm = FALSE (never processed), runs Haiku
+    digest + embedding for each, back-propagates summary and sets exec_llm=TRUE
+    on mem_mrr_commits. Returns count processed.
     """
     if not db.is_available():
         raise HTTPException(status_code=503, detail="PostgreSQL not available")
@@ -389,7 +389,7 @@ async def embed_commits(
                 cur.execute(
                     """SELECT commit_hash FROM mem_mrr_commits
                        WHERE project_id=%s
-                         AND (tags->>'llm') IS NULL
+                         AND exec_llm = FALSE
                        ORDER BY committed_at DESC NULLS LAST
                        LIMIT %s""",
                     (project_id, limit),


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_git.py b/backend/routers/route_git.py
index c3a990c..007fd08 100644
--- a/backend/routers/route_git.py
+++ b/backend/routers/route_git.py
@@ -26,15 +26,22 @@ log = logging.getLogger(__name__)
 
 _SQL_UPSERT_COMMIT = """
     INSERT INTO mem_mrr_commits
-            (project_id, commit_hash, session_id, commit_msg, diff_summary, committed_at, tags)
-        VALUES (%s, %s, %s, %s, %s, %s, %s)
+            (project_id, commit_hash, session_id, commit_msg, diff_summary,
+             author, author_email, committed_at, tags, tags_ai)
+        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
         ON CONFLICT (commit_hash) DO UPDATE
             SET session_id   = COALESCE(EXCLUDED.session_id,   mem_mrr_commits.session_id),
                 commit_msg   = COALESCE(EXCLUDED.commit_msg,   mem_mrr_commits.commit_msg),
                 diff_summary = COALESCE(EXCLUDED.diff_summary, mem_mrr_commits.diff_summary),
+                author       = CASE WHEN EXCLUDED.author != '' THEN EXCLUDED.author
+                                    ELSE mem_mrr_commits.author END,
+                author_email = CASE WHEN EXCLUDED.author_email != '' THEN EXCLUDED.author_email
+                                    ELSE mem_mrr_commits.author_email END,
                 committed_at = COALESCE(EXCLUDED.committed_at, mem_mrr_commits.committed_at),
-                tags         = CASE WHEN EXCLUDED.tags != \'{}\' THEN EXCLUDED.tags
-                                    ELSE mem_mrr_commits.tags END
+                tags         = CASE WHEN EXCLUDED.tags != '{}' THEN EXCLUDED.tags
+                                    ELSE mem_mrr_commits.tags END,
+                tags_ai      = CASE WHEN EXCLUDED.tags_ai != '{}' THEN EXCLUDED.tags_ai
+                                    ELSE mem_mrr_commits.tags_ai END
 """
 
 # Link commit → most-recent prompt in the same session that occurred before the commit.
@@ -158,11 +165,25 @@ async def _embed_commit_background(project: str, commit_hash: str) -> None:
         log.debug(f"_embed_commit_background error ({commit_hash[:8]}): {e}")
 
 
+def _extract_commit_code_background(project: str, commit_hash: str) -> None:
+    """Run tree-sitter symbol extraction and insert rows into mem_mrr_commits_code."""
+    import asyncio
+    loop = asyncio.new_event_loop()
+    try:
+        from memory.memory_code_parser import extract_commit_code
+        loop.run_until_complete(extract_commit_code(project, commit_hash))
+    except Exception as e:
+        log.debug(f"_extract_commit_code_background error ({commit_hash[:8]}): {e}")
+    finally:
+        loop.close()
+
+
 # ── Commit→prompt linking background task ─────────────────────────────────────
 
 def _sync_commit_and_link(project: str, commit_hash: str, session_id: str | None,
                           commit_msg: str, committed_at: str,
-                          diff_summary: str = "", analysis: dict | None = None) -> None:
+                          diff_summary: str = "", analysis: dict | None = None,
+                          author: str = "", author_email: str = "") -> None:
     """Upsert the new commit into mem_mrr_commits and link it to its triggering prompt.
 
     Linking uses mem_mrr_commits.prompt_id (UUID FK to mem_mrr_prompts) — the most recent
@@ -190,15 +211,19 @@ def _sync_commit_and_link(project: str, commit_hash: str, session_id: str | None
 
         with db.conn() as conn:
             with conn.cursor() as cur:
-                # 1. Upsert the commit (includes diff_summary + tags)
+                # 1. Upsert the commit
+                # tags: user-intent only (source, phase, feature, bug, work-item)
                 tags_dict.setdefault("source", "commit_push")
+                # analysis goes to tags_ai (AI-generated metadata), not tags
+                tags_ai_dict: dict = {}
                 if analysis:
-                    tags_dict["analysis"] = analysis
+                    tags_ai_dict["analysis"] = analysis
                 cur.execute(
                     _SQL_UPSERT_COMMIT,
                     (project_id, commit_hash, session_id, commit_msg, diff_summary or None,
+                     author, author_email,
                      committed_at or datetime.now(timezone.utc),
-                     json.dumps(tags_dict)),
+                     json.dumps(tags_dict), json.dumps(tags_ai_dict)),
                 )
 
                 # 2. Link commit → last prompt in the session (via prompt_id FK)
@@ -1002,6 +1027,17 @@ async def commit_and_push(project_name: str, body: CommitRequest, request: Reque
 
     _, commit_hash, _ = _git(["rev-parse", "HEAD"], code_dir)
 
+    # Capture author info from the just-created commit
+    commit_author = ""
+    commit_author_email = ""
+    try:
+        _, author_info, _ = _git(["log", "--format=%an\t%ae", "-1", "HEAD"], code_dir)
+        parts = author_info.split("\t", 1)
+        commit_author = parts[0].strip() if parts else ""
+        commit_author_email = parts[1].strip() if len(parts) > 1 else ""
+    except Exception:
+        pass
+
     # Determine push target: explicit > project.yaml git_branch > current local branch > "main"
     push_target = body.branch.strip()
     if not push_target:
@@ -1082,10 +1118,14 @@ async def commit_and_push(project_name: str, body: CommitRequest, request: Reque
             commit_message,
             datetime.now(timezone.utc).isoformat(),
             code_stat,          # only code file stats stored
-            commit_analysis,    # structured LLM analysis (may be {})
+            commit_analysis,    # structured LLM analysis → stored in tags_ai
+            commit_author,
+            commit_author_email,
         )
-        # Embed the commit (extracts symbols, creates mem_ai_events) in background
+        # Embed the commit (creates mem_ai_events) in background
         background.add_task(_embed_commit_background, project_name, commit_hash)
+        # Tree-sitter symbol extraction 

### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/requirements.txt b/backend/requirements.txt
index 330ea2d..0060070 100644
--- a/backend/requirements.txt
+++ b/backend/requirements.txt
@@ -14,3 +14,5 @@ httpx>=0.27.0
 pyyaml>=6.0
 python-dotenv>=1.0.0
 mcp>=1.0.0
+tree-sitter>=0.23.0
+tree-sitter-languages>=1.10.0


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/memory/memory_extraction.py b/backend/memory/memory_extraction.py
index 682040e..6699493 100644
--- a/backend/memory/memory_extraction.py
+++ b/backend/memory/memory_extraction.py
@@ -36,6 +36,15 @@ _SQL_GET_LINKED_COMMITS = """
     ORDER BY committed_at
 """
 
+_SQL_AGGREGATE_CODE = """
+    SELECT file_path, file_ext, file_language,
+           SUM(rows_added)::int   AS rows_added,
+           SUM(rows_removed)::int AS rows_removed
+    FROM mem_mrr_commits_code
+    WHERE commit_hash = ANY(%s)
+    GROUP BY file_path, file_ext, file_language
+"""
+
 _SQL_MERGE_AI_TAGS = """
     UPDATE mem_ai_work_items
     SET ai_tags = ai_tags || %s::jsonb, updated_at = NOW()
@@ -62,37 +71,74 @@ class MemoryExtraction:
     def aggregate_commits(commits: list[dict]) -> dict:
         """Aggregate file/line stats across all commits linked to a work item.
 
+        Queries mem_mrr_commits_code for structured per-symbol stats when available;
+        falls back to parsing tags["files"] / tags["rows_changed"] for older commits.
+
         Returns a dict with all_files, test_files, source_files, total_added,
         total_removed, and commit_count.
         """
-        all_files: set[str] = set()
-        test_files_seen: set[str] = set()
-        total_added = 0
-        total_removed = 0
+        commit_hashes = [c["commit_hash"] for c in commits if c.get("commit_hash")]
+
+        # Try mem_mrr_commits_code first (populated by tree-sitter parser)
+        if commit_hashes and db.is_available():
+            try:
+                with db.conn() as conn:
+                    with conn.cursor() as cur:
+                        cur.execute(_SQL_AGGREGATE_CODE, (commit_hashes,))
+                        rows = cur.fetchall()
+                if rows:
+                    all_files: set[str] = set()
+                    test_files_seen: set[str] = set()
+                    total_added = 0
+                    total_removed = 0
+                    for file_path, _ext, _lang, ra, rr in rows:
+                        all_files.add(file_path)
+                        total_added += ra or 0
+                        total_removed += rr or 0
+                        if ".test." in file_path or ".spec." in file_path or "/test" in file_path or "tests/" in file_path:
+                            test_files_seen.add(file_path)
+                    test_files = sorted(test_files_seen)
+                    source_files = sorted(all_files - test_files_seen)
+                    return {
+                        "all_files":     sorted(all_files),
+                        "test_files":    test_files,
+                        "source_files":  source_files,
+                        "total_added":   total_added,
+                        "total_removed": total_removed,
+                        "commit_count":  len(commits),
+                    }
+            except Exception as e:
+                log.debug(f"aggregate_commits code table query failed, falling back: {e}")
+
+        # Fallback: parse tags["files"] / tags["rows_changed"] (pre-016 commits)
+        all_files_fb: set[str] = set()
+        test_files_seen_fb: set[str] = set()
+        total_added_fb = 0
+        total_removed_fb = 0
 
         for c in commits:
             tags = c.get("tags") or {}
             files = tags.get("files") or {}
             names = list(files.keys()) if isinstance(files, dict) else list(files)
-            all_files.update(names)
+            all_files_fb.update(names)
 
             rc = tags.get("rows_changed") or {}
-            total_added   += rc.get("added", 0)
-            total_removed += rc.get("removed", 0)
+            total_added_fb   += rc.get("added", 0)
+            total_removed_fb += rc.get("removed", 0)
 
             for f in names:
                 if ".test." in f or ".spec." in f or "/test" in f or "tests/" in f:
-                    test_files_seen.add(f)
+                    test_files_seen_fb.add(f)
 
-        test_files   = sorted(test_files_seen)
-        source_files = sorted(all_files - test_files_seen)
+        test_files_fb   = sorted(test_files_seen_fb)
+        source_files_fb = sorted(all_files_fb - test_files_seen_fb)
 
         return {
-            "all_files":    sorted(all_files),
-            "test_files":   test_files,
-            "source_files": source_files,
-            "total_added":  total_added,
-            "total_removed": total_removed,
+            "all_files":    sorted(all_files_fb),
+            "test_files":   test_files_fb,
+            "source_files": source_files_fb,
+            "total_added":  total_added_fb,
+            "total_removed": total_removed_fb,
             "commit_count": len(commits),
         }
 


## AI Synthesis

**[2026-04-08]** `claude_cli` — Finalized commit code extraction schema: mem_mrr_commits_code table with 19 columns including generated full_symbol for semantic indexing; resolved DDL migration lock issue where generated column failed silently on first run. **[2026-04-08]** `route_memory.py` — Migrated embed_commits endpoint from tags->'llm' IS NULL to exec_llm=FALSE boolean flag for tracking processed commits; Haiku digest now backpropagates summary and sets exec_llm=TRUE on mem_mrr_commits. **[2026-03-14]** `PROJECT.md` — Project facts updated: auth_pattern confirmed as login_as_first_level_hierarchy; memory_management_pattern set to load_once_on_access_update_on_save; mcp_integration focuses on embedding and work item retrieval. **[Recent]** `schema tracking` — 4-layer memory architecture stabilized: ephemeral session → mem_mrr_* raw capture → mem_ai_* LLM digests + embeddings → work items/project facts → user planner tags. **[In progress]** Database optimization: route_work_items latency investigation (~60s round-trip); performance tuning on _SQL_UNLINKED_WORK_ITEMS joins and indexing strategy.