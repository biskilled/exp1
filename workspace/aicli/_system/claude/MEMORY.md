# Project Memory — aicli
_Generated: 2026-04-06 22:55 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a Python FastAPI backend with a desktop Electron UI and CLI, using PostgreSQL+pgvector for semantic search and multiple LLM providers (Claude/OpenAI/DeepSeek/Gemini/Grok). It provides unified project memory management, work item tracking with dual-status (user/AI), async DAG workflow execution, and session-based tagging/phase management. Current focus is on resolving work item persistence bugs in tag-linking and improving UI for drag-drop interactions between panes.

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
- **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local bash/npm
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
- Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
- Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
- Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
- Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with per-prompt inline display
- Tag filtering in work item list: ai_category must match tag's category, not work item's own category (fixed regression in _loadTagLinkedWorkItems)
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev
- Session-level UI consolidation: Planner tab unified for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created
- Work item persistence across navigation: drag-drop linkage saves correctly to DB; reload of project/page maintains linked work items in list display

## In Progress

- Work item tag-linking persistence and display: fixed _loadTagLinkedWorkItems filter logic where ai_category was incorrectly matching work item's category instead of tag's category; work items now persist and display correctly after drag-drop linkage and page reload
- Work item dual-status UI implementation: status_user dropdown for user control + status_ai badge for AI suggestions with separate color indicators; integrated into table headers and item drawer
- Work item embedding strategy: unified embedding space via code_summary + requirements + summary fields for cross-table cosine-similarity matching with planner_tags
- Work item commits association: /work-items/{id}/commits endpoint returning linked commits via JSONB tags filtering; commit-per-prompt inline display with accent left-border
- Tag deduplication across views: 149 tags total (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously
- UI drag-and-drop work item feature: user can drag work items between panes with visual feedback; investigating pane resizing via separator line interaction

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **retrospective** `[open]`
- **Test** `[open]`
- **architecture-decision** `[open]`
- **customer-meeting** `[open]`
- **high-level-design** `[open]`
- **low-level-design** `[open]`

### Feature

- **pagination**
- **test-picker-feature** `[open]`
- **graph-workflow** `[open]`
- **billing** `[open]`
- **embeddings** `[open]`
- **tagging** `[open]`
- **mcp** `[open]`
- **workflow-runner** `[open]`
- **shared-memory** `[open]`
- **UI** `[open]`
- **auth** `[open]`
- **dropbox** `[open]`

### Phase

- **development** `[open]`
- **discovery** `[open]`
- **prod** `[open]`

### Task

- **memory** `[open]`
- **implement-projects-tab** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/project_state.json b/workspace/aicli/_system/project_state.json
index 5017cd6..f76ad53 100644
--- a/workspace/aicli/_system/project_state.json
+++ b/workspace/aicli/_system/project_state.json
@@ -19,7 +19,7 @@
     "chunking": "Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)",
     "mcp": "Stdio MCP server with 12+ tools",
     "deployment": "Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev",
-    "database_schema": "Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features",
+    "database_schema": "Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles",
     "config_management": "config.py + YAML pipelines + pyproject.toml",
     "db_tables": "Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles",
     "llm_provider_adapters": "agents/providers/ with pr_ prefix for pricing and provider implementations",
@@ -51,9 +51,9 @@
     "Data persistence: load_once_on_access, update_on_save pattern; tags in mem_ai_tags_relations with row ID linking",
     "Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI",
     "Backend: FastAPI + uvicorn; routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for access, agents/ for tools and MCP",
-    "UI/UX consolidated: Planner tab unified for tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created tags",
+    "UI unified: Planner tab for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created tags",
     "Session ordering by created_at (not updated_at) to prevent tag/phase updates from reordering session list",
-    "Memory synthesis improved: summaries of LLM responses instead of full output; suggested tags auto-saved to session via _acceptSuggestedTag",
+    "Memory synthesis: summaries of LLM responses instead of full output; suggested tags auto-saved to session via _acceptSuggestedTag",
     "Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev"
   ],
   "implemented_features": [
@@ -83,12 +83,12 @@
     "config.py reads ~/.aicli/config.json for WORKSPACE_DIR at startup"
   ],
   "in_progress": [
-    "Session ordering fixed: sessions now order by created_at instead of updated_at to prevent phase/tag updates from reordering list (2026-03-15)",
-    "Phase persistence enhanced: loads from DB on init, PATCH /chat/sessions/{id}/tags saves phase, red \u26a0 badge for missing phase across UI/CLI/WF (2026-03-15)",
-    "Commit-per-prompt inline display: replaced session-level strip with commits at bottom of each prompt entry (accent left-border, hash \u2197 link showing only that prompt's commits) (2026-03-15)",
-    "Tag deduplication and cross-view sync: 149 tags total (0 duplicates); removal via \u2715 buttons propagates across Chat/History/Commits simultaneously (2026-03-15)",
-    "AI suggestion auto-save with tag management: suggestions create tags in proper category via _acceptSuggestedTag; suggested tags marked with distinct color/mark; tags appear immediately in Planner (2026-03-15)",
-    "Planner tab unified redesign: consolidated tag management into single tags view with category, active/inactive status, short description, created date; removed Feature/Bugs/Tags split (2026-03-15)"
+    "Session ordering fixed: sessions now order by created_at instead of updated_at to prevent phase/tag updates from reordering list",
+    "Phase persistence enhanced: loads from DB on init, PATCH /chat/sessions/{id}/tags saves phase, red \u26a0 badge for missing phase across UI/CLI/WF",
+    "Commit-per-prompt inline display: replaced session-level strip with commits at bottom of each prompt entry (accent left-border, hash \u2197 link showing only that prompt's commits)",
+    "Tag deduplication and cross-view sync: 149 tags total (0 duplicates); removal via \u2715 buttons propagates across Chat/History/Commits simultaneously",
+    "AI suggestion auto-save with tag management: suggestions create tags in proper category via _acceptSuggestedTag; suggested tags marked with distinct color/mark; tags appear immediately in Planner",
+    "Planner tab unified redesign: consolidated tag management into single tags view with category, active/inactive status, short description, created date; removed Feature/Bugs/Tags split"
   ],
   "next_phase_plan": {
     "project_management_page": [
@@ -120,7 +120,7 @@
     "cloud": "Railway (Dockerfile + railway.toml)",
     "desktop": "Electron-builder: Mac dmg (arm64+x64), Windows nsis, Linux AppImage+deb"
   },
-  "last_memory_run": "2026-04-05T16:26:57Z",
+  "last_memory_run": "2026-04-05T17:07:11Z",
   "_synthesis_cache": {
     "key_decisions": [
       "Engine/workspace separation: aicli/ backend + CLI; workspace/ per-project content; _system/ stores project state and memory files",
@@ -134,18 +134,18 @@
       "Data persistence: load_once_on_access, update_on_save pattern; tags i

### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/dev_runtime_state.json b/workspace/aicli/_system/dev_runtime_state.json
index a17d289..4cc52f4 100644
--- a/workspace/aicli/_system/dev_runtime_state.json
+++ b/workspace/aicli/_system/dev_runtime_state.json
@@ -1,8 +1,8 @@
 {
-  "last_updated": "2026-04-05T17:06:45Z",
-  "last_session_id": "04d3b8ba-c786-4b24-b0d6-ed49009f369d",
-  "last_session_ts": "2026-04-05T17:06:45Z",
-  "session_count": 349,
+  "last_updated": "2026-04-05T17:23:39Z",
+  "last_session_id": "1780c17d-dfad-46ce-8a6b-26dc60511e55",
+  "last_session_ts": "2026-04-05T17:23:39Z",
+  "session_count": 350,
   "last_provider": "claude",
   "last_prompt_preview": "hellow, how are you ?",
   "source": "claude_cli"


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/cursor/rules.md b/workspace/aicli/_system/cursor/rules.md
index 2bfa5fd..6e7b294 100644
--- a/workspace/aicli/_system/cursor/rules.md
+++ b/workspace/aicli/_system/cursor/rules.md
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-05 16:26 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-05 17:06 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -24,7 +24,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
 - **mcp**: Stdio MCP server with 12+ tools
 - **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
-- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
+- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **config_management**: config.py + YAML pipelines + pyproject.toml
 - **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
@@ -57,7 +57,7 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Data persistence: load_once_on_access, update_on_save pattern; tags in mem_ai_tags_relations with row ID linking
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Backend: FastAPI + uvicorn; routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for access, agents/ for tools and MCP
-- UI/UX consolidated: Planner tab unified for tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created tags
+- UI unified: Planner tab for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created tags
 - Session ordering by created_at (not updated_at) to prevent tag/phase updates from reordering session list
-- Memory synthesis improved: summaries of LLM responses instead of full output; suggested tags auto-saved to session via _acceptSuggestedTag
+- Memory synthesis: summaries of LLM responses instead of full output; suggested tags auto-saved to session via _acceptSuggestedTag
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index dc9a26a..251a98e 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -613,3 +613,6 @@
 {"ts": "2026-04-05T12:40:02Z", "action": "commit_push", "source": "claude_cli", "session_id": "6ffb562b-40dd-4aea-80a1-408ce5204f03", "hash": "0477b67b", "message": "docs: update memory, rules, and project docs after claude session", "pushed": true, "push_error": ""}
 {"action": "commit_push", "source": "claude_cli", "session_id": "6ffb562b-40dd-4aea-80a1-408ce5204f03", "hash": "cf4a7845", "message": "chore: update system files and memory after claude session 6ffb562b", "files_count": 40, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-05T16:26:40Z"}
 {"ts": "2026-04-05T16:26:32Z", "action": "commit_push", "source": "claude_cli", "session_id": "6ffb562b-40dd-4aea-80a1-408ce5204f03", "hash": "cf4a7845", "message": "chore: update system files and memory after claude session 6ffb562b", "pushed": true, "push_error": ""}
+{"action": "commit_push", "source": "claude_cli", "session_id": "04d3b8ba-c786-4b24-b0d6-ed49009f369d", "hash": "4d63fb40", "message": "chore: update system files and memory after claude session 04d3b8ba", "files_count": 37, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-05T17:06:53Z"}
+{"ts": "2026-04-05T17:06:44Z", "action": "commit_push", "source": "claude_cli", "session_id": "04d3b8ba-c786-4b24-b0d6-ed49009f369d", "hash": "4d63fb40", "message": "chore: update system files and memory after claude session 04d3b8ba", "pushed": true, "push_error": ""}
+{"ts": "2026-04-05T17:23:39Z", "action": "api_error", "source": "claude_cli", "session_id": "1780c17d-dfad-46ce-8a6b-26dc60511e55", "error": "curl failed (rc=28), backend may be unhealthy"}


### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/claude/MEMORY.md b/workspace/aicli/_system/claude/MEMORY.md
index 16026ec..b9747f5 100644
--- a/workspace/aicli/_system/claude/MEMORY.md
+++ b/workspace/aicli/_system/claude/MEMORY.md
@@ -1,11 +1,11 @@
 # Project Memory — aicli
-_Generated: 2026-04-05 16:26 UTC by aicli /memory_
+_Generated: 2026-04-05 17:06 UTC by aicli /memory_
 
 > Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.
 
 ## Project Summary
 
-aicli is a shared AI memory platform combining a Python CLI backend (FastAPI + PostgreSQL + pgvector), desktop Electron UI, and LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok) to enable multi-modal project management with intelligent memory synthesis. Recent focus has been on UI consolidation (unified Planner tab for tag management), session ordering fixes to prevent list reordering, and enhanced AI suggestion system with auto-saved tags marked distinctly from user-created ones; session count now at 99 with stable core features for phase persistence, commit tracking, and cross-view tag synchronization.
+aicli is a shared AI memory platform combining a Python 3.12 CLI, FastAPI backend, and Electron desktop UI with PostgreSQL + pgvector for semantic search. The project provides unified session/tag management, LLM provider adapters (Claude/OpenAI/DeepSeek/Gemini/Grok), workflow automation via async DAG execution, and comprehensive memory synthesis—currently focused on UI consolidation (Planner tab), session persistence, and memory response summarization.
 
 ## Project Facts
 
@@ -64,7 +64,7 @@ Reviewer: ```json
 - **chunking**: Smart chunking: per-class/function (Python/JS/TS) + per-section (Markdown) + per-file (diffs)
 - **mcp**: Stdio MCP server with 12+ tools
 - **deployment**: Railway (Dockerfile + railway.toml); Electron-builder; local: bash start_backend.sh + ui/npm run dev
-- **database_schema**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles; unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features
+- **database_schema**: Unified: mem_ai_events, mem_ai_tags_relations, mem_ai_project_facts, mem_ai_work_items, mem_ai_features; Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; Shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **config_management**: config.py + YAML pipelines + pyproject.toml
 - **db_tables**: Per-project: commits_{p}, events_{p}, embeddings_{p}, event_tags_{p}, event_links_{p}, memory_items_{p}, project_facts_{p}, pr_graph_runs; shared: users, usage_logs, transactions, session_tags, entity_categories, entity_values, agent_roles, system_roles
 - **llm_provider_adapters**: agents/providers/ with pr_ prefix for pricing and provider implementations
@@ -97,19 +97,19 @@ Reviewer: ```json
 - Data persistence: load_once_on_access, update_on_save pattern; tags in mem_ai_tags_relations with row ID linking
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Backend: FastAPI + uvicorn; routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for access, agents/ for tools and MCP
-- UI/UX consolidated: Planner tab unified for tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created tags
+- UI unified: Planner tab for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created tags
 - Session ordering by created_at (not updated_at) to prevent tag/phase updates from reordering session list
-- Memory synthesis improved: summaries of LLM responses instead of full output; suggested tags auto-saved to session via _acceptSuggestedTag
+- Memory synthesis: summaries of LLM responses instead of full output; suggested tags auto-saved to session via _acceptSuggestedTag
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev
 
 ## In Progress
 
-- Session ordering fixed: sessions now order by created_at instead of updated_at to prevent phase/tag updates from reordering list (2026-03-15)
-- Phase persistence enhanced: loads from DB on init, PATCH /chat/sessions/{id}/tags saves phase, red ⚠ badge for missing phase across UI/CLI/WF (2026-03-15)
-- Commit-per-prompt inline display: replaced session-level strip with commits at bottom of each prompt entry (accent left-border, hash ↗ link showing only that prompt's commits) (2026-03-15)
-- Tag deduplication and cross-view sync: 149 tags total (0 duplicates); removal via ✕ buttons propagates across Chat/History/Commits simultaneously (2026-03-15)
-- AI suggestion auto-save with tag management: suggestions create tags in proper category via _acceptSuggestedTag; suggested tags marked with distinct color/mark; tags appear immediately in Planner (2026-03-15)
-- Planner tab unified redesign: consolidated tag management into single tags view with category, active/inactive status, short description, created date; removed Feature/Bugs/Tags split (2026-03-15)
+- Session ordering fixed: sessions now order by created_at instead of updated_at to prevent phase/tag updates from reordering list
+- Phase persistence enhanced: loads from DB on init, PATCH /chat/sessions/{id}/tags saves phase, red ⚠ badge for missing phase across UI/CLI/WF
+- Commit-per-prompt inline display: replaced session-level strip with commits at bottom of each prompt entry (accent left-border, hash ↗ link showing only that prompt's commits)
+- Tag deduplication and cross-view sync: 149 

### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/claude/CLAUDE.md b/workspace/aicli/_system/claude/CLAUDE.md
index 352196a..3b2e26d 100644
--- a/workspace/aicli/_system/claude/CLAUDE.md
+++ b/workspace/aicli/_system/claude/CLAUDE.md
@@ -37,9 +37,9 @@ You are a senior Python software architect with deep expertise in:
 - Data persistence: load_once_on_access, update_on_save pattern; tags in mem_ai_tags_relations with row ID linking
 - Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Backend: FastAPI + uvicorn; routers/ for API, core/ for infrastructure, data/ (dl_ prefix) for access, agents/ for tools and MCP
-- UI/UX consolidated: Planner tab unified for tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created tags
+- UI unified: Planner tab for all tag management (single tags view with category/status/properties); suggested tags marked distinctly from user-created tags
 - Session ordering by created_at (not updated_at) to prevent tag/phase updates from reordering session list
-- Memory synthesis improved: summaries of LLM responses instead of full output; suggested tags auto-saved to session via _acceptSuggestedTag
+- Memory synthesis: summaries of LLM responses instead of full output; suggested tags auto-saved to session via _acceptSuggestedTag
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop (Mac dmg, Windows nsis, Linux AppImage+deb); local bash start_backend.sh + npm run dev
 
 ---


## AI Synthesis

**[2026-04-06]** `claude_cli` — Fixed work item tag-linking persistence: ai_category filter in _loadTagLinkedWorkItems was incorrectly matching work item's own category instead of the tag's category, preventing linked items from appearing in list after drag-drop. Root cause identified and corrected to check tag's category; linked work items now persist across page reloads.

**[2026-04-05]** `claude_cli` — Completed work item dual-status UI: implemented status_user dropdown + status_ai suggestion badge with distinct color indicators in table headers and drawer; unified embedding strategy via code_summary + requirements + summary for cross-table semantic matching with planner_tags.

**[2026-04-05]** `claude_cli` — Work item commits association endpoint: added /work-items/{id}/commits returning linked commits via JSONB tags filtering; replaced session-level commit strip with per-prompt inline display (accent left-border, hash link showing only that prompt's commits).

**[2026-04-05]** `claude_cli` — Tag deduplication and cross-view sync: verified 149 total tags with 0 duplicates; tag removal via ✕ buttons now propagates across Chat/History/Commits views simultaneously without duplication.

**[2026-04-05]** `claude_cli` — AI suggestion auto-save with tag management: suggestions now create tags in proper category via _acceptSuggestedTag; suggested tags marked with distinct color/mark; tags appear immediately in Planner tab.

**[2026-04-05]** `claude_cli` — Planner tab redesign: consolidated tag management into single tags view with category, active/inactive status, short description, created date; removed Feature/Bugs/Tasks split view; session ordering fixed to use created_at instead of updated_at to prevent tag/phase updates from reordering list.