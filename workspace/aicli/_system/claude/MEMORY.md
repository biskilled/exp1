# Project Memory — aicli
_Generated: 2026-04-08 17:19 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend with PostgreSQL+pgvector semantic storage, a Python 3.12 CLI (prompt_toolkit + rich), and an Electron desktop UI (Vanilla JS + xterm.js + Monaco + Cytoscape). It implements a 4-layer memory architecture (sessions → raw capture → LLM digests → work items/facts → user tags) with async DAG workflow execution, multi-provider LLM support (Claude/OpenAI/DeepSeek), and dual deployment (Railway cloud + Electron desktop). Current focus is prompt loader consolidation, memory endpoint synchronization, and performance optimization for work item queries.

## Project Facts

- **auth_pattern**: login_as_first_level_hierarchy
- **backend_startup_race_condition_fix**: retry_logic_handles_empty_project_list_on_first_load
- **code_extraction_configuration**: min_lines: 5, only_on_commits_with_tags: false in project.yaml templates
- **commit_processing_flag**: exec_llm boolean column replaces tags->>'llm' NULL check
- **commit_tracking_schema**: mem_mrr_commits_code table with 19 columns including commit_short_hash and full_symbol as generated column
- **data_model_hierarchy**: clients_contain_multiple_users
- **data_persistence_issue**: tags_disappear_on_session_switch
- **db_engine**: PostgreSQL with SQL parameter binding
- **db_schema_method_convention**: _ensure_shared_schema_replaces_ensure_project_schema
- **deployment_target**: Claude CLI and LLM platforms
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
- **rel:commit_processing:exec_llm_flag**: replaces
- **rel:memory_system:session_tags**: implements
- **rel:route_memory:sql_parameter_binding**: depends_on
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
- Prompt centralization via core.prompt_loader; system roles (mng_system_roles) replaced with prompt cache; eliminates redundant database lookups

## In Progress

- Prompt loader integration: refactoring route_snapshots.py and route_memory.py to use core.prompt_loader._prompts.content() instead of direct mng_system_roles queries for performance and consistency
- Commit pipeline prompt discovery: tracing all LLM prompts in memory_embedding.py, agents/tools/, and route_snapshots.py to establish comprehensive prompt inventory
- Memory endpoint data flow synchronization: verifying cascade from mirror tables (mem_mrr_commits_code) through mem_ai_events and downstream tables; completed import migration to memory_embedding module
- Module restructuring: consolidating embedding/ingestion logic into memory_embedding.py; updating imports across route_snapshots.py, route_search.py, route_prompts.py for consistency
- Database query performance optimization: investigating ~60s latency in route_work_items; indexing strategy for _SQL_UNLINKED_WORK_ITEMS and join optimization on mem_ai_events
- Planner tag visibility debugging: resolving issue where categories upload correctly but individual tags don't display in UI bindings; verifying router mapping and category query logic

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

diff --git a/workspace/aicli/PROJECT.md b/workspace/aicli/PROJECT.md
index 7951bce..5810212 100644
--- a/workspace/aicli/PROJECT.md
+++ b/workspace/aicli/PROJECT.md
@@ -375,9 +375,9 @@ All tables follow a structured naming convention:
 
 ## Recent Work
 
-- Commit pipeline prompt discovery: tracing all LLM prompts used in commit processing (code extraction, summarization, embedding); located in memory/memory_embedding.py, agents/tools/, and routers/route_snapshots.py
+- Prompt loader integration: refactoring route_snapshots.py and route_memory.py to use core.prompt_loader._prompts.content() instead of direct mng_system_roles queries; eliminates redundant database lookups
+- Commit pipeline prompt discovery: tracing all LLM prompts used in commit processing (code extraction, summarization, embedding) located in memory/memory_embedding.py, agents/tools/, and routers/route_snapshots.py
 - Memory endpoint data flow: verifying synchronization from mirror tables (mem_mrr_commits_code) through mem_ai_events and downstream memory tables; identified import migration from mem_embeddings to memory_embedding module
 - Module restructuring: consolidating embedding/ingestion logic into memory_embedding.py; updating imports across route_snapshots.py, route_search.py, route_prompts.py for consistent module paths
-- Database query performance: route_work_items showing ~60s latency; investigating indexing for _SQL_UNLINKED_WORK_ITEMS and join optimization on mem_ai_events
-- Planner tag visibility: debugging category upload and tag binding visibility in UI; verifying router mapping and category query logic
-- DDL runner robustness: investigating silent failures during initial migration caused by table locks; post-creation DDL for generated columns now handled separately from base table creation
+- Database query performance optimization: route_work_items showing ~60s latency; investigating indexing for _SQL_UNLINKED_WORK_ITEMS and join optimization on mem_ai_events
+- Planner tag visibility debugging: categories upload but individual tags don't display in UI bindings; verifying router mapping and category query logic


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/workspace/_templates/python_api/project.yaml b/workspace/_templates/python_api/project.yaml
index 310d1d6..771a0fe 100644
--- a/workspace/_templates/python_api/project.yaml
+++ b/workspace/_templates/python_api/project.yaml
@@ -6,5 +6,6 @@ active_workflows:
   - build_feature
   - code_review
 commit_code_extraction:
-  min_lines: 5
+  min_lines: 5              # per-symbol llm_summary threshold (rows_added+rows_removed)
+  min_diff_lines: 5         # commit-level threshold: skip all LLM calls if diff < this
   only_on_commits_with_tags: false


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/workspace/_templates/blank/project.yaml b/workspace/_templates/blank/project.yaml
index 2b98de9..2156a73 100644
--- a/workspace/_templates/blank/project.yaml
+++ b/workspace/_templates/blank/project.yaml
@@ -4,5 +4,6 @@ code_dir: "../../{{PROJECT_NAME}}"
 default_provider: claude
 active_workflows: []
 commit_code_extraction:
-  min_lines: 5
+  min_lines: 5              # per-symbol llm_summary threshold (rows_added+rows_removed)
+  min_diff_lines: 5         # commit-level threshold: skip all LLM calls if diff < this
   only_on_commits_with_tags: false


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_git.py b/backend/routers/route_git.py
index 7513630..dd18344 100644
--- a/backend/routers/route_git.py
+++ b/backend/routers/route_git.py
@@ -1006,17 +1006,42 @@ async def commit_and_push(project_name: str, body: CommitRequest, request: Reque
     _, staged_diff, _ = _git(["diff", "--cached"], code_dir)
     staged_diff = (staged_diff or "")[:8000]
 
+    # Count meaningful diff lines (added + removed, excluding file headers)
+    _diff_line_count = sum(
+        1 for ln in staged_diff.splitlines()
+        if ln.startswith(("+", "-")) and not ln.startswith(("+++", "---"))
+    )
+
+    # Read min_diff_lines from project.yaml (default 5)
+    _min_diff_lines = 5
+    try:
+        _pcfg = yaml.safe_load((_proj_dir(project_name) / "project.yaml").read_text()) or {}
+        _min_diff_lines = int(_pcfg.get("commit_code_extraction", {}).get("min_diff_lines", 5))
+    except Exception:
+        pass
+
     # Resolve API key: body field takes priority, then request header
     api_key = body.api_key or request.headers.get("X-Anthropic-Key") or None
 
     # Generate commit message (+ optional structured analysis)
-    commit_message, commit_analysis = await _generate_commit_message(
-        hint=body.message_hint,
-        diff_stat=diff_stat,
-        changed_files=changed,
-        staged_diff=staged_diff,
-        api_key=api_key,
-    )
+    # Skip LLM for tiny commits (below min_diff_lines threshold)
+    if _diff_line_count < _min_diff_lines:
+        if body.message_hint:
+            commit_message = body.message_hint[:72]
+        elif len(changed) == 1:
+            commit_message = f"chore: update {changed[0]}"
+        else:
+            commit_message = f"chore: update {len(changed)} files"
+        commit_analysis = {}
+        log.debug(f"Skipping LLM commit analysis: diff_lines={_diff_line_count} < min={_min_diff_lines}")
+    else:
+        commit_message, commit_analysis = await _generate_commit_message(
+            hint=body.message_hint,
+            diff_stat=diff_stat,
+            changed_files=changed,
+            staged_diff=staged_diff,
+            api_key=api_key,
+        )
 
     # Stage all changed files
     _git(["add", "--"] + changed, code_dir)


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/routers/route_chat.py b/backend/routers/route_chat.py
index 5336538..5f3f09a 100644
--- a/backend/routers/route_chat.py
+++ b/backend/routers/route_chat.py
@@ -75,12 +75,12 @@ _SQL_INSERT_GRAPH_RUN = """
     VALUES (%s, %s, %s, 'running', %s)
 """
 
-_SQL_UPDATE_COMMIT_PHASE = """
+_SQL_UPDATE_COMMIT_TAGS = """
     UPDATE mem_mrr_commits
-    SET tags = CASE
-        WHEN %s IS NOT NULL THEN (tags - 'phase') || jsonb_build_object('phase', %s)
-        ELSE tags - 'phase'
-    END
+    SET tags = (tags - 'phase' - 'feature' - 'bug')
+        || CASE WHEN %s::text IS NOT NULL THEN jsonb_build_object('phase',   %s::text) ELSE '{}'::jsonb END
+        || CASE WHEN %s::text IS NOT NULL THEN jsonb_build_object('feature', %s::text) ELSE '{}'::jsonb END
+        || CASE WHEN %s::text IS NOT NULL THEN jsonb_build_object('bug',     %s::text) ELSE '{}'::jsonb END
     WHERE project_id=%s AND session_id=%s
 """
 
@@ -778,11 +778,17 @@ class SessionTagsPatch(BaseModel):
     bug_ref: Optional[str] = None
 
 
-def _backfill_session_phase(project: str, session_id: str, phase: Optional[str]) -> None:
-    """Retroactively set phase on all history.jsonl entries + DB rows for a session.
+def _backfill_session_tags(
+    project: str, session_id: str,
+    phase: Optional[str] = None,
+    feature: Optional[str] = None,
+    bug_ref: Optional[str] = None,
+) -> None:
+    """Retroactively set phase/feature/bug tags on all history.jsonl entries + DB commits.
 
-    Called whenever a session's phase tag is changed so that all prompts and commits
-    linked to that session become filterable by the new phase.
+    Called whenever any session tag is changed via PATCH /sessions/{id}/tags so that
+    all prompts and commits linked to that session become filterable by the new tags.
+    Only keys explicitly passed (not None) are updated; None-valued keys are removed.
     """
     # 1. Rewrite matching entries in history.jsonl
     hist_path = Path(settings.workspace_dir) / project / "_system" / "history.jsonl"
@@ -796,7 +802,9 @@ def _backfill_session_phase(project: str, session_id: str, phase: Optional[str])
                 try:
                     entry = json.loads(line)
                     if entry.get("session_id") == session_id:
-                        entry["phase"] = phase
+                        if phase   is not None: entry["phase"]   = phase   or None
+                        if feature is not None: entry["feature"] = feature or None
+                        if bug_ref is not None: entry["bug_ref"] = bug_ref or None
                     updated.append(json.dumps(entry, ensure_ascii=False))
                 except Exception:
                     updated.append(line)
@@ -804,7 +812,7 @@ def _backfill_session_phase(project: str, session_id: str, phase: Optional[str])
         except Exception:
             pass  # read-only filesystem or concurrent write — best-effort
 
-    # 2. Update commits table tags[] (phase column dropped — tags[] used instead)
+    # 2. Update mem_mrr_commits.tags for all commits in this session
     if db.is_available():
         import logging as _log
         _logger = _log.getLogger(__name__)
@@ -812,14 +820,17 @@ def _backfill_session_phase(project: str, session_id: str, phase: Optional[str])
             project_id = db.get_or_create_project_id(project)
             with db.conn() as conn:
                 with conn.cursor() as cur:
-                    cur.execute(_SQL_UPDATE_COMMIT_PHASE, (phase, phase, project_id, session_id))
+                    cur.execute(
+                        _SQL_UPDATE_COMMIT_TAGS,
+                        (phase, phase, feature, feature, bug_ref, bug_ref, project_id, session_id),
+                    )
                     c_rows = cur.rowcount
             _logger.info(
-                f"backfill_session_phase: project={project} session={session_id[:8]} "
-                f"phase={phase!r} → commits={c_rows}"
+                f"backfill_session_tags: project={project} session={session_id[:8]} "
+                f"phase={phase!r} feature={feature!r} bug={bug_ref!r} → commits={c_rows}"
             )
         except Exception as exc:
-            _logger.warning(f"backfill_session_phase DB failed: {exc}")
+            _logger.warning(f"backfill_session_tags DB failed: {exc}")
 
 
 @router.patch("/sessions/{session_id}/tags")
@@ -847,8 +858,9 @@ async def patch_session_tags(
         if body.bug_ref is not None: tags["bug_ref"] = body.bug_ref or None
         # Do NOT update updated_at — tag edits shouldn't change session sort order
         store._save(session)
-        if body.phase is not None:
-            _backfill_session_phase(p, session_id, body.phase or None)
+        if body.phase is not None or body.feature is not None or body.bug_ref is not None:
+            _backfill_session_tags(p, session_id,
+                                   phase=body.phase, feature=body.feature, bug_ref=body.bug_ref)
         return {"ok": True, "tags": tags}
 
     # CLI / workflow session — persist in session_phases.json
@@ -863,6 +875,7 @@ async def patch_session_tags(
     if body.feature is not None: entry["feature"] = body.feature or None
     if body.bug_ref is not None: entry["bug_ref"] = body.bug_ref or None
     phases_path.write_text(json.dumps(existing, indent=2))
-    if body.phase is not None:
-        _backfill_session_phase(p, session_id, body.phase or None)
+    if body.phase is not None or body.feature is not None or body.bug_ref is not None:
+        _backfill_session_tags(p, session_id,
+                               phase=body.phase, feature=body.feature, bug_ref=body.bug_ref)
     return {"ok": True, "tags": entry}


### `commit: 9315de75-b88b-4961-b13b-7acb9f07af17` — 2026-04-08

diff --git a/backend/memory/memory_embedding.py b/backend/memory/memory_embedding.py
index becb413..fd7a46b 100644
--- a/backend/memory/memory_embedding.py
+++ b/backend/memory/memory_embedding.py
@@ -75,7 +75,7 @@ _SQL_UPSERT_EVENT = """
 """
 
 _SQL_GET_COMMIT = """
-    SELECT commit_hash, commit_msg, summary, tags, session_id
+    SELECT commit_hash, commit_msg, summary, tags, session_id, diff_summary
     FROM mem_mrr_commits
     WHERE project_id=%s AND commit_hash=%s
 """
@@ -255,6 +255,33 @@ def _upsert_event(
         return None
 
 
+def _read_commit_min_diff_lines(project: str) -> int:
+    """Read commit_code_extraction.min_diff_lines from project.yaml (default 5)."""
+    try:
+        import yaml as _yaml
+        from pathlib import Path as _Path
+        proj_yaml = _Path(settings.workspace_dir) / project / "project.yaml"
+        if proj_yaml.exists():
+            cfg = _yaml.safe_load(proj_yaml.read_text()) or {}
+            return int(cfg.get("commit_code_extraction", {}).get("min_diff_lines", 5))
+    except Exception:
+        pass
+    return 5
+
+
+def _count_diff_stat_lines(diff_summary: str) -> int:
+    """Parse total changed lines from git --stat output.
+
+    e.g. '3 files changed, 10 insertions(+), 5 deletions(-)' → 15
+    Returns 0 if summary is missing/unparseable.
+    """
+    import re as _re
+    total = 0
+    for count, _ in _re.findall(r"(\d+) (insertion|deletion)", diff_summary):
+        total += int(count)
+    return total
+
+
 class MemoryEmbedding:
     """Embeds and stores content in mem_ai_events; provides semantic search."""
 
@@ -368,12 +395,20 @@ class MemoryEmbedding:
             if not row:
                 return None
 
-            commit_hash_val, commit_msg, existing_summary, mrr_tags, session_id = row
+            commit_hash_val, commit_msg, existing_summary, mrr_tags, session_id, diff_summary = row
             mrr_tags = mrr_tags or {}
         except Exception as e:
             log.debug(f"process_commit DB error: {e}")
             return None
 
+        # Guard: skip LLM if diff is below min_diff_lines threshold
+        _min_diff = _read_commit_min_diff_lines(project)
+        _diff_lines = _count_diff_stat_lines(diff_summary or "")
+        if _diff_lines > 0 and _diff_lines < _min_diff:
+            log.debug(f"process_commit: skipping LLM for {commit_hash[:8]} "
+                      f"(diff_lines={_diff_lines} < min={_min_diff})")
+            return None
+
         user_content = f"Commit: {commit_hash_val[:8]}\n{commit_msg}"
         if existing_summary:
             user_content += f"\nSummary: {existing_summary}"


## AI Synthesis

**[2026-03-14]** `core.prompt_loader` — Replaced mng_system_roles database queries with centralized prompt_loader._prompts.content() to eliminate redundant lookups; refactoring route_snapshots.py and route_memory.py to use new pattern. **[2026-03-14]** `memory_embedding.py` — Consolidated embedding/ingestion logic and completed module restructuring; established import consistency across route_snapshots.py, route_search.py, and route_prompts.py. **[2026-03-14]** `mem_mrr_commits_code` — Verified 4-layer memory architecture data flow from mirror tables through mem_ai_events to downstream mem_ai_work_items/project_facts; confirmed full_symbol as generated column and 19-column schema. **[2026-03-14]** `commit_code_extraction config` — Added min_diff_lines threshold (5) for commit-level skip logic; per-symbol llm_summary now conditional on min_lines threshold. **[2026-03-14]** `route_work_items` — Identified ~60s latency in _SQL_UNLINKED_WORK_ITEMS join; investigation underway for indexing strategy on mem_ai_events. **[2026-03-14]** `planner_tags visibility` — Debugging category upload success but individual tag non-display in UI bindings; router mapping and category query logic verification in progress.