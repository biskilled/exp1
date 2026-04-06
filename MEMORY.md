# Project Memory — aicli
_Generated: 2026-04-06 17:52 UTC by aicli /memory_

> Auto-generated. CLAUDE.md references this so Claude CLI reads it at session start.

## Project Summary

aicli is a shared AI memory platform combining a FastAPI backend, PostgreSQL semantic storage (pgvector), and an Electron desktop UI for collaborative development workflows. It integrates multiple LLM providers (Claude/OpenAI/DeepSeek/Gemini/Grok) with DAG-based workflow execution, dual-status work item tracking, and unified memory synthesis. Current focus is on enhancing the UI with drag-and-drop work item repositioning and resizable pane layouts while maintaining semantic embedding consistency across project entities.

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
- Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with mem_mrr_commits table
- Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
- Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation
- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
- Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev

## In Progress

- Work item dual-status UI: implemented status_user (user dropdown) and status_ai (AI suggestion badge) with separate color indicators; updated table headers and drawer UI
- Work item schema migration: replaced single status field with status_user + status_ai; added code_summary field for semantic embedding and planner_tags matching
- Work item commits association: added /work-items/{id}/commits endpoint returning linked commits via JSONB tags filtering; integrated api.workItems.commits() client method
- Work item embedding strategy: unified embedding space for work_items + planner_tags via code_summary + requirements + summary fields for cross-table cosine-similarity matching
- Database query optimization: extended _SQL_LIST_WORK_ITEMS_BASE with commit_count subquery and status column updates; refactored _SQL_UNLINKED_WORK_ITEMS to filter by status_user != 'done'
- UI drag-and-drop feature request: user inquired about dragging work items between top/bottom screen panes and resizing bottom pane height via separator line interaction

## Active Features / Bugs / Tasks

### Ai_suggestion

- **test123** `[open]`

### Bug

- **hooks** `[open]`

### Doc_type

- **architecture-decision** `[open]`
- **customer-meeting** `[open]`
- **Test** `[open]`
- **low-level-design** `[open]`
- **high-level-design** `[open]`
- **retrospective** `[open]`

### Feature

- **UI** `[open]`
- **pagination** `[open]`
- **test-picker-feature** `[open]`
- **graph-workflow** `[open]`
- **billing** `[open]`
- **embeddings** `[open]`
- **tagging** `[open]`
- **mcp** `[open]`
- **workflow-runner** `[open]`
- **shared-memory** `[open]`
- **auth** `[open]`
- **dropbox** `[open]`

### Phase

- **prod** `[open]`
- **development** `[open]`
- **discovery** `[open]`

### Task

- **implement-projects-tab** `[open]`
- **memory** `[open]`

## Recent Memory

> Distilled summaries (Trycycle-reviewed). Feature summaries shown first.

### `prompt_batch: 04974a99-4e27-44d8-ba75-c7b9e54ba9c7` — 2026-04-06

The `source_session_id` tracks which session created/last modified each work item; `content` stores raw event data, `summary` holds the AI-generated overview, and `requirements` captures extracted needs—all three accumulate across merged sessions while `tags` consolidates tags from `mem_ai_events`. The undefined function errors were caused by a stray initialization call that was removed, allowing `window._plannerSync` to be properly assigned.

### `commit` — 2026-04-06

Commit: docs: update system context and memory after claude session 04974a99
Hash: a85bbac6
Files changed (23):
  - .ai/rules.md
  - .cursor/rules/aicli.mdrules
  - .github/copilot-instructions.md
  - CLAUDE.md
  - MEMORY.md
  - backend/core/database.py
  - backend/routers/route_work_items.py
  - ui/frontend/utils/api.js
  - ui/frontend/views/entities.js
  - workspace/aicli/PROJECT.md
  - workspace/aicli/_system/CLAUDE.md
  - workspace/aicli/_system/CONTEXT.md
  - workspace/aicli/_system/aicli/context.md
  - workspace/aicli/_system/aicli/copilot.md
  - workspace/aicli/_system/claude/CLAUDE.md
  - workspace/aicli/_system/claude/MEMORY.md
  - workspace/aicli/_system/commit_log.jsonl
  - workspace/aicli/_system/cursor/rules.md
  - workspace/aicli/_system/dev_runtime_state.json
  - workspace/aicli/_system/llm_prompts/compact.md

### `commit` — 2026-04-06

diff --git a/workspace/aicli/_system/commit_log.jsonl b/workspace/aicli/_system/commit_log.jsonl
index 0d06817..080baf8 100644
--- a/workspace/aicli/_system/commit_log.jsonl
+++ b/workspace/aicli/_system/commit_log.jsonl
@@ -715,3 +715,4 @@
 {"action": "commit_push", "source": "claude_cli", "session_id": "04974a99-4e27-44d8-ba75-c7b9e54ba9c7", "hash": "ceec428e", "message": "docs: update system context and memory files post-session", "files_count": 61, "pushed": true, "push_error": "", "branch": "master", "pull_message": "pulled: Current branch master is up to date.", "ts": "2026-04-06T17:35:51Z"}
 {"ts": "2026-04-06T17:35:21Z", "action": "commit_push", "source": "claude_cli", "session_id": "04974a99-4e27-44d8-ba75-c7b9e54ba9c7", "hash": "ceec428e", "message": "docs: update system context and memory files post-session", "pushed": true, "push_error": ""}
 {"ts": "2026-04-06T17:35:57Z", "action": "api_error", "source": "claude_cli", "session_id": "04974a99-4e27-44d8-ba75-c7b9e54ba9c7", "error": "curl failed (rc=28), backend may be unhealthy"}
+{"ts": "2026-04-06T17:35:57Z", "action": "commit_push", "source": "claude_cli_direct", "session_id": "04974a99-4e27-44d8-ba75-c7b9e54ba9c7", "hash": "dd6202f", "message": "chore(cli): auto-commit after AI session \u2014 16 file(s) \u2014 2026-04-06 17:37 UTC", "pushed": true, "push_error": ""}


### `commit` — 2026-04-06

diff --git a/.github/copilot-instructions.md b/.github/copilot-instructions.md
index d47c5dd..6cb0cab 100644
--- a/.github/copilot-instructions.md
+++ b/.github/copilot-instructions.md
@@ -1,5 +1,5 @@
 # aicli — GitHub Copilot Instructions
-> Generated by aicli 2026-04-06 14:18 UTC
+> Generated by aicli 2026-04-06 17:34 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -54,10 +54,10 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
-- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
-- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
+- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with mem_mrr_commits table
 - Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
 - Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation
+- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
\ No newline at end of file


### `commit` — 2026-04-06

Commit: chore: clean up claude cli session system files
Hash: aa720f1b
Files changed (1):
  - workspace/aicli/_system/commit_log.jsonl

### `commit` — 2026-04-06

diff --git a/.cursor/rules/aicli.mdrules b/.cursor/rules/aicli.mdrules
index e59d880..9344630 100644
--- a/.cursor/rules/aicli.mdrules
+++ b/.cursor/rules/aicli.mdrules
@@ -1,5 +1,5 @@
 # aicli — AI Coding Rules
-> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 14:18 UTC
+> Managed by aicli. Run `/memory` to refresh. Generated: 2026-04-06 17:34 UTC
 
 # aicli — Shared AI Memory Platform
 
@@ -54,12 +54,12 @@ _Last updated: 2026-03-14 | Version 2.2.0_
 - Claude Haiku dual-layer memory synthesis generating 5 files with LLM response summarization + auto-tag suggestions; timestamp tracking with tag deduplication
 - Async DAG workflow executor via asyncio.gather with loop-back and max_iterations cap; Cytoscape visualization with 2-pane approval panel
 - Data persistence: load_once_on_access, update_on_save pattern; session ordering by created_at (not updated_at) to prevent reordering on tag/phase updates
-- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Work items: dual status tracking (status_user for user control, status_ai for AI suggestions) with code_summary field for semantic embedding + planner_tags cross-matching
-- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
+- Smart chunking: per-class/function (Python/JS/TS), per-section (Markdown), per-file (diffs); manual relations via CLI/admin UI
 - Commit deduplication by hash with UNION consolidation; commits linked per-work-item via tags JSONB with mem_mrr_commits table
 - Dual-hook architecture: hook-response saves LLM responses to mem_mrr_prompts.response; session-summary hook consolidates prompt/response pairs for synthesis
 - Memory layer event-based triggering with differentiated process_item/messages handling for core memory functionality activation
+- Backend startup race condition: retry_logic_handles_empty_project_list_on_first_load; _ensure_shared_schema replaces ensure_project_schema convention
 - Deployment: Railway (Dockerfile + railway.toml) cloud; Electron-builder for desktop; local bash start_backend.sh + npm run dev
 
 ## Recent Context (last 5 changes)


## AI Synthesis

**[2026-04-06]** `claude_cli` — Completed work item dual-status UI implementation with separate status_user/status_ai tracking and visual indicators; migrated schema to support status_user + status_ai + code_summary fields for semantic embedding. **[2026-04-06]** `claude_cli` — Added /work-items/{id}/commits endpoint with JSONB tag filtering and integrated api.workItems.commits() client method for work item-commit association. **[2026-04-06]** `claude_cli` — Unified embedding strategy across work_items and planner_tags using code_summary + requirements + summary for cosine-similarity cross-table matching. **[2026-04-06]** `claude_cli` — Optimized database queries: extended _SQL_LIST_WORK_ITEMS_BASE with commit_count subquery, refactored _SQL_UNLINKED_WORK_ITEMS to filter by status_user != 'done'. **[2026-04-06]** `claude_cli_direct` — Auto-committed 16 files post-session with system context and memory consolidation; dev_runtime_state.json shows 396 sessions, latest 2026-04-06T17:34:59Z. **[2026-04-06]** `user_inquiry` — Feature request: drag-and-drop work items between top/bottom screen panes and resizable bottom pane height via separator line.