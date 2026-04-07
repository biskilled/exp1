# Project Memory — aicli
_Generated: 2026-04-07 22:39 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

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
- **mcp**: Stdio MCP server with 12+ tools
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder (Mac dmg, Windows nsis, Linux AppImage+deb); local bash/npm
- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
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
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- 4-layer memory architecture: Layer 0 (ephemeral session messages) → Layer 1 (mem_mrr_* raw capture) → Layer 2 (mem_ai_events LLM digests + embeddings) → Layer 3 (mem_ai_work_items, mem_ai_project_facts) → Layer 4 (user-managed planner_tags)
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
- Tag filtering in work item list: ai_category must match tag's category, not work item's own category
- Session-level UI consolidation: Planner tab unified for all tag management with category/status/properties; suggested tags marked distinctly
- Memory synthesis triggered from session data via /memory endpoint → Claude Haiku processes commits/events → outputs to mem_ai_events/project_facts tables

## In Progress

- Commit table schema verification: confirmed diff_summary (TEXT) stays as human-readable git --stat output; diff_details (JSONB) was dropped and cleaned from mcp/server.py and memory_mirroring.py
- Backend data loading optimization: route_work_items line 249 (_SQL_UNLINKED_WORK_ITEMS) and line 288 (merged_into/start_date alignment) under investigation; Railway migrations functional but slow (~60s per round-trip, 0.9s per query)
- Work item drag-and-drop UI refinement: fixing hover state propagation for target tag highlights; ensuring dropped work items persist in correct parent and disappear from source after page reload
- Frontend reference error resolution: fixing _plannerSelectAiSubtype undefined error in routers.route_logs; ensuring all planner helper functions properly scoped and exported to global scope
- Memory endpoint data population: running /memory to sync session data into memory_items and ensure mem_ai_* tables properly reflect latest project state with correct event linkage
- Mirror table architecture investigation: understanding trigger mechanisms for mem_ai_events and mem_ai_project_facts, LLM prompts used in synthesis, and data flow from session commits/events

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

### `commit: fa708653-5003-4882-8b5c-07ef4d0d32e5` — 2026-04-07

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index 144dcc9..d3ab483 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-22 02:30 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-22 02:37 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -55,8 +55,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-22] I have created pyproject.toml manualy. can you update that file again ? also I do see error in stop hook which preventin
 - [2026-03-22] I do see that backend is failing to start (it also take quite a while to load )
 - [2026-03-22] looks better. planner is loading well. Also there is an issue with Roles (PostgreSQL required agent roles) Also Pipeline
 - [2026-03-22] I still do not see All Planner tags (categroeis, existing tags...) also Pipelines are not loading
-- [2026-03-22] PostgreSql is up and running, why do you build a workaround. it looks like router mappig not query the proper tables
\ No newline at end of file
+- [2026-03-22] PostgreSql is up and running, why do you build a workaround. it looks like router mappig not query the proper tables
+- [2026-03-22] I do see categroeis uploaded in Planner tab, but I do not see all the tags in each categroy. Also I do got an error when
\ No newline at end of file


### `commit: dca94c94-c618-4866-89ce-7a3178adc777` — 2026-04-07

diff --git a/backend/routers/route_git.py b/backend/routers/route_git.py
index e071bfd..f7bde33 100644
--- a/backend/routers/route_git.py
+++ b/backend/routers/route_git.py
@@ -121,6 +121,43 @@ def _write_commit_log(project_name: str, entry: dict) -> None:
         pass  # never break git operations because of logging
 
 
+# ── Generated-file filter ──────────────────────────────────────────────────────
+
+import re as _re
+_GEN_FILE_PAT = _re.compile(
+    r'^\s*(CLAUDE\.md|\.cursorrules|MEMORY\.md|\.ai/|\.cursor/|\.github/copilot|'
+    r'workspace/.*/_system/|history\.jsonl|.*\.claude/memory)',
+    _re.IGNORECASE,
+)
+
+def _filter_diff_stat(diff_stat: str) -> tuple[str, str]:
+    """Return (code_stat, gen_stat) — split diff --stat by generated vs code files."""
+    code_lines, gen_lines = [], []
+    for line in (diff_stat or "").splitlines():
+        if _GEN_FILE_PAT.match(line):
+            gen_lines.append(line)
+        else:
+            code_lines.append(line)
+    # Keep summary line (last line, has "N files changed") in both
+    if code_lines or gen_lines:
+        summary = (diff_stat or "").splitlines()[-1] if diff_stat else ""
+        if summary and not _re.match(r'^\s*\w', summary.lstrip()):
+            code_lines.append(summary)
+    return "\n".join(code_lines), "\n".join(gen_lines)
+
+
+# ── Commit embedding background task ───────────────────────────────────────────
+
+async def _embed_commit_background(project: str, commit_hash: str) -> None:
+    """Run process_commit() to embed + extract symbols after commit is stored."""
+    try:
+        from memory.memory_embedding import MemoryEmbedding
+        await MemoryEmbedding().process_commit(project, commit_hash)
+        log.info(f"_embed_commit_background: embedded {commit_hash[:8]} for {project}")
+    except Exception as e:
+        log.debug(f"_embed_commit_background error ({commit_hash[:8]}): {e}")
+
+
 # ── Commit→prompt linking background task ─────────────────────────────────────
 
 def _sync_commit_and_link(project: str, commit_hash: str, session_id: str | None,
@@ -1028,15 +1065,19 @@ async def commit_and_push(project_name: str, body: CommitRequest, request: Reque
 
     # Immediately link this commit to its triggering prompt in the background
     if commit_hash and background is not None:
+        # Filter generated/memory files from diff_summary so code stats are clean
+        code_stat, _ = _filter_diff_stat(diff_stat or "")
         background.add_task(
             _sync_commit_and_link,
             project_name,
-            commit_hash[:8],
+            commit_hash,        # full 40-char hash (not truncated)
             body.session_id or None,
             commit_message,
             datetime.now(timezone.utc).isoformat(),
-            diff_stat or "",   # stored as diff_summary on mem_mrr_commits
+            code_stat,          # only code file stats stored
         )
+        # Embed the commit (extracts symbols, creates mem_ai_events) in background
+        background.add_task(_embed_commit_background, project_name, commit_hash)
 
     return {
         "committed": True,


### `commit: dca94c94-c618-4866-89ce-7a3178adc777` — 2026-04-07

diff --git a/backend/memory/memory_embedding.py b/backend/memory/memory_embedding.py
index 5410f7e..4364a62 100644
--- a/backend/memory/memory_embedding.py
+++ b/backend/memory/memory_embedding.py
@@ -425,7 +425,20 @@ class MemoryEmbedding:
 
         # Per-file diff chunks (raw embed, no llm tag) + back-propagate file stats to mrr
         try:
+            # Prefer project-specific code_dir from DB; fall back to settings.code_dir
             code_dir = settings.code_dir
+            try:
+                with db.conn() as conn:
+                    with conn.cursor() as cur:
+                        cur.execute(
+                            "SELECT code_dir FROM mng_projects WHERE name=%s AND code_dir IS NOT NULL LIMIT 1",
+                            (project,),
+                        )
+                        prow = cur.fetchone()
+                        if prow and prow[0]:
+                            code_dir = prow[0]
+            except Exception:
+                pass
             if code_dir:
                 result = subprocess.run(
                     ["git", "show", "--format=%B%n---DIFF---", commit_hash_val],
@@ -438,13 +451,15 @@ class MemoryEmbedding:
                         diff_chunks = MemoryEmbedding.smart_chunk_diff(
                             diff_text, commit_hash_val, {"commit_msg": commit_msg}
                         )
-                        # Back-propagate file/language stats from summary chunk to mrr
+                        # Back-propagate file/language/symbol stats from summary chunk to mrr
                         summary_chunk_tags = diff_chunks[0].get("tags", {}) if diff_chunks else {}
                         mrr_stat_update: dict = {}
                         if summary_chunk_tags.get("files"):
                             mrr_stat_update["files"] = summary_chunk_tags["files"]
                         if summary_chunk_tags.get("languages"):
                             mrr_stat_update["languages"] = summary_chunk_tags["languages"]
+                        if summary_chunk_tags.get("symbols"):
+                            mrr_stat_update["symbols"] = summary_chunk_tags["symbols"]
                         if mrr_stat_update:
                             with db.conn() as conn:
                                 with conn.cursor() as cur:


### `commit: fa708653-5003-4882-8b5c-07ef4d0d32e5` — 2026-04-07

diff --git a/.ai/rules.md b/.ai/rules.md
index 144dcc9..d3ab483 100644
--- a/.ai/rules.md
+++ b/.ai/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-22 02:30 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-03-22 02:37 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -55,8 +55,8 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 
 ## Recent Context (last 5 changes)
 
-- [2026-03-22] I have created pyproject.toml manualy. can you update that file again ? also I do see error in stop hook which preventin
 - [2026-03-22] I do see that backend is failing to start (it also take quite a while to load )
 - [2026-03-22] looks better. planner is loading well. Also there is an issue with Roles (PostgreSQL required agent roles) Also Pipeline
 - [2026-03-22] I still do not see All Planner tags (categroeis, existing tags...) also Pipelines are not loading
-- [2026-03-22] PostgreSql is up and running, why do you build a workaround. it looks like router mappig not query the proper tables
\ No newline at end of file
+- [2026-03-22] PostgreSql is up and running, why do you build a workaround. it looks like router mappig not query the proper tables
+- [2026-03-22] I do see categroeis uploaded in Planner tab, but I do not see all the tags in each categroy. Also I do got an error when
\ No newline at end of file


### `commit: dca94c94-c618-4866-89ce-7a3178adc777` — 2026-04-07

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index e756479..b5b1abd 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-07 16:48 UTC
+> Generated by aicli 2026-04-07 17:12 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -54,10 +54,10 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
+- 4-layer memory architecture: Layer 0 (ephemeral session messages) → Layer 1 (mem_mrr_* raw capture) → Layer 2 (mem_ai_events LLM digests + embeddings) → Layer 3 (mem_ai_work_items, mem_ai_project_facts) → Layer 4 (user-managed planner_tags)
 - Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
 - Tag filtering in work item list: ai_category must match tag's category, not work item's own category
 - Session-level UI consolidation: Planner tab unified for all tag management with category/status/properties; suggested tags marked distinctly
-- Memory synthesis triggered from session data via /memory endpoint → Claude Haiku processes commits/events → outputs to mem_ai_events/project_facts tables
-- Project facts generated via LLM prompt analyzing session events and commits; stored in mem_ai_project_facts with event_id linkage for traceability
\ No newline at end of file
+- Memory synthesis triggered from session data via /memory endpoint → Claude Haiku processes commits/events → outputs to mem_ai_events/project_facts tables
\ No newline at end of file


### `commit: dca94c94-c618-4866-89ce-7a3178adc777` — 2026-04-07

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index ce342af..0d6ba29 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-07 16:48 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-07 17:12 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -54,18 +54,18 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Claude Haiku dual-layer memory synthesis generating 5 output files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
+- 4-layer memory architecture: Layer 0 (ephemeral session messages) → Layer 1 (mem_mrr_* raw capture) → Layer 2 (mem_ai_events LLM digests + embeddings) → Layer 3 (mem_ai_work_items, mem_ai_project_facts) → Layer 4 (user-managed planner_tags)
 - Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
 - Tag filtering in work item list: ai_category must match tag's category, not work item's own category
 - Session-level UI consolidation: Planner tab unified for all tag management with category/status/properties; suggested tags marked distinctly
 - Memory synthesis triggered from session data via /memory endpoint → Claude Haiku processes commits/events → outputs to mem_ai_events/project_facts tables
-- Project facts generated via LLM prompt analyzing session events and commits; stored in mem_ai_project_facts with event_id linkage for traceability
 
 ## Recent Context (last 5 changes)
 
-- [2026-04-07] I do have some errors loading data - route_work_items line 249 - cur.execute(_SQL_UNLINKED_WORK_ITEMS, (p_id,)) and line
 - [2026-04-07] Can you use aiCli_memeory to describe the followng : how flow works from mirror. each mirrr table - what is the trigeer,
 - [2026-04-07] Can you use aiCli_memeory to describe the followng : how flow works from mirror. each mirrr table - what is the trigeer,
 - [2026-04-07] In addtion to your reccomendation, I would like to check the following -  mem_ai_coomits -  what is diff_details is used
-- [2026-04-07] dont you have any moemry, did you see the previous file you din - aicli_memoy.md under the project root ?
\ No newline at end of file
+- [2026-04-07] dont you have any moemry, did you see the previous file you din - aicli_memoy.md under the project root ?
+- [2026-04-07] I still see the columns in commit table - diif_summery and diff_details . is it suppose to be ?
\ No newline at end of file

